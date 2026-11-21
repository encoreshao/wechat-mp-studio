#!/usr/bin/env python3
"""本地实时预览：启动一个只监听本机的小服务器，浏览器里手机宽度预览文章。

用法:
  python3 preview.py articles/<dir>/article.md [--theme tech-blue] [--scheme 黛蓝] [--port 8765] [--no-open]

功能:
  - 顶部切换主题 / 配色，即时重新排版
  - 保存 article.md 后自动刷新（无需重新运行）
  - 「复制到公众号」：复制带内联样式的富文本，可直接粘贴进公众号编辑器
    （本地图片粘贴后需在编辑器里重新上传；用 publish.py draft 推草稿会自动上传）
  - 「保存为主题」：把当前主题/配色写回 article.md 的 front matter
仅依赖标准库 + convert.py 的依赖（markdown、beautifulsoup4）。
"""
import argparse
import html
import json
import mimetypes
import os
import re
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import find_workspace  # noqa: E402
from convert import convert  # noqa: E402
from presets import PRESETS  # noqa: E402
from themes import list_themes  # noqa: E402

PAGE = r"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>预览 · __TITLE__</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#ececef;font-family:-apple-system,'PingFang SC',sans-serif;color:#222}
.bar{position:sticky;top:0;z-index:5;background:rgba(255,255,255,.95);backdrop-filter:blur(8px);border-bottom:1px solid #ddd;
 padding:10px 16px;display:flex;gap:10px;align-items:center;justify-content:center;flex-wrap:wrap;font-size:13px}
select,button{font-size:13px;padding:6px 10px;border:1px solid #ccc;border-radius:8px;background:#fff;cursor:pointer}
button.primary{background:#07c160;border-color:#07c160;color:#fff}
.info{color:#888}
.wrap{display:flex;gap:28px;justify-content:center;align-items:flex-start;padding:24px 12px 80px;flex-wrap:wrap}
.card{width:320px;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.08)}
.card img{width:100%;display:block;aspect-ratio:2.35/1;object-fit:cover;background:#ddd}
.card .t{padding:10px 12px 4px;font-size:16px;font-weight:600;line-height:1.4}
.card .d{padding:0 12px 12px;font-size:12.5px;color:#888;line-height:1.5}
.side h4{margin:0 0 8px;font-size:13px;color:#666;font-weight:500}
.phone{width:390px;background:#fff;border-radius:28px;border:10px solid #1c1c1e;box-shadow:0 6px 30px rgba(0,0,0,.12);overflow:hidden}
.top{height:44px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:600;border-bottom:1px solid #f0f0f0}
.body{padding:20px 16px 40px}
.body h1.ti{font-size:22px;line-height:1.4;margin:0 0 10px;color:#111}
.meta{font-size:14px;color:#576b95;margin:0 0 22px}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#111;color:#fff;padding:10px 16px;border-radius:8px;
 font-size:13px;opacity:0;transition:opacity .2s;pointer-events:none}
.toast.on{opacity:.92}
.err{color:#e5484d;white-space:pre-wrap;font-size:13px}
@media(max-width:820px){.side{display:none}}
</style></head><body>
<div class="bar">
  <label>主题 <select id="theme"></select></label>
  <label>配色 <select id="scheme"></select></label>
  <button id="save">保存为本文主题</button>
  <button id="copy" class="primary">复制到公众号</button>
  <span class="info" id="info"></span>
</div>
<div class="wrap">
  <div class="side"><h4>订阅消息卡片</h4>
    <div class="card"><img id="cover" alt=""><div class="t" id="ctitle"></div><div class="d" id="cdigest"></div></div>
    <p class="info" style="margin-top:12px;max-width:320px;line-height:1.6">保存 article.md 后页面会自动刷新。<br>
    「复制到公众号」后在公众号编辑器里粘贴即可，本地图片需要重新上传。</p>
  </div>
  <div class="phone"><div class="top">公众号文章</div>
    <div class="body"><h1 class="ti" id="title"></h1><p class="meta" id="author"></p><div id="article"></div></div>
  </div>
</div>
<div class="toast" id="toast"></div>
<script>
const $=id=>document.getElementById(id);
let THEMES={}, mtime=0;
function toast(t){const e=$('toast');e.textContent=t;e.classList.add('on');setTimeout(()=>e.classList.remove('on'),1800)}
function fillSchemes(){const t=$('theme').value, s=$('scheme'); s.innerHTML='';
  const list=(THEMES[t]||{}).schemes||[]; s.disabled=!list.length;
  (list.length?list:['—']).forEach(x=>{const o=document.createElement('option');o.value=list.length?x:'';o.textContent=x;s.appendChild(o)});}
async function render(){
  const q=new URLSearchParams({theme:$('theme').value,scheme:$('scheme').value});
  const r=await fetch('/render?'+q); const j=await r.json();
  if(j.error){$('article').innerHTML='<p class="err">'+j.error+'</p>';return}
  $('article').innerHTML=j.html; $('title').textContent=j.meta.title||''; $('ctitle').textContent=j.meta.title||'';
  $('cdigest').textContent=j.meta.digest||''; $('author').textContent=j.meta.author||'';
  $('cover').src=j.meta.cover?('/files/'+encodeURI(j.meta.cover)+'?t='+Date.now()):'';
  $('info').textContent=(j.meta.word_count||0)+' 字'+(j.warnings&&j.warnings.length?' · ⚠ '+j.warnings.join('；'):'');
  mtime=j.mtime;
}
async function init(){
  const j=await (await fetch('/themes')).json(); THEMES=j.themes;
  for(const [k,v] of Object.entries(THEMES)){const o=document.createElement('option');o.value=k;o.textContent=v.label;$('theme').appendChild(o)}
  $('theme').value=j.current.theme; fillSchemes(); if(j.current.scheme) $('scheme').value=j.current.scheme;
  $('theme').onchange=()=>{fillSchemes();render()}; $('scheme').onchange=render;
  $('copy').onclick=async()=>{const h=$('article').innerHTML;
    try{await navigator.clipboard.write([new ClipboardItem({'text/html':new Blob([h],{type:'text/html'}),'text/plain':new Blob([$('article').innerText],{type:'text/plain'})})]);toast('已复制，去公众号编辑器粘贴')}
    catch(e){const r=document.createRange();r.selectNodeContents($('article'));const s=getSelection();s.removeAllRanges();s.addRange(r);document.execCommand('copy');s.removeAllRanges();toast('已复制')}};
  $('save').onclick=async()=>{const r=await fetch('/save',{method:'POST',body:JSON.stringify({theme:$('theme').value,scheme:$('scheme').value})});
    toast((await r.json()).ok?'已写入 article.md 的 front matter':'保存失败')};
  await render();
  setInterval(async()=>{try{const m=(await (await fetch('/mtime')).json()).mtime; if(m!==mtime) render()}catch(e){}},1000);
}
init();
</script></body></html>"""


def theme_catalog(ws):
    out = {}
    for k, label in list_themes(ws).items():
        if k in PRESETS:
            out[k] = {"label": PRESETS[k]["label"] + "（风格）", "schemes": list(PRESETS[k]["schemes"])}
        else:
            out[k] = {"label": label.split("（")[0], "schemes": []}
    return out


def set_front_matter(md_path, updates):
    with open(md_path, encoding="utf-8") as fh:
        text = fh.read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    lines = m.group(1).splitlines() if m else []
    body = text[m.end():] if m else text
    keys = {ln.split(":", 1)[0].strip(): i for i, ln in enumerate(lines) if ":" in ln}
    for k, v in updates.items():
        if v in (None, ""):
            if k in keys:
                lines[keys[k]] = None
            continue
        if k in keys:
            lines[keys[k]] = f"{k}: {v}"
        else:
            lines.append(f"{k}: {v}")
    lines = [ln for ln in lines if ln is not None]
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("---\n" + "\n".join(lines) + "\n---\n" + body)


def make_handler(md_path, ws, state):
    base = os.path.dirname(md_path)

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype="application/json; charset=utf-8"):
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            q = dict(urllib.parse.parse_qsl(u.query))
            if u.path == "/":
                return self._send(200, PAGE.replace("__TITLE__", html.escape(os.path.basename(base))),
                                  "text/html; charset=utf-8")
            if u.path == "/themes":
                return self._send(200, json.dumps({"themes": theme_catalog(ws), "current": state}, ensure_ascii=False))
            if u.path == "/mtime":
                return self._send(200, json.dumps({"mtime": os.path.getmtime(md_path)}))
            if u.path == "/render":
                theme = q.get("theme") or state["theme"]
                scheme = q.get("scheme") or None
                state.update(theme=theme, scheme=scheme or "")
                warnings = []
                try:
                    import io
                    import contextlib
                    err = io.StringIO()
                    with contextlib.redirect_stderr(err):
                        art, meta = convert(md_path, theme, ws, False, scheme)
                    warnings = [ln.strip("⚠️ ").strip() for ln in err.getvalue().splitlines() if ln.strip()]
                except SystemExit as e:
                    return self._send(200, json.dumps({"error": str(e)}, ensure_ascii=False))
                except Exception as e:  # noqa: BLE001
                    return self._send(200, json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False))

                def fix(m):
                    src = m.group(2)
                    if re.match(r"(https?:|data:)", src):
                        return m.group(0)
                    p = src if os.path.isabs(src) else os.path.join(base, src)
                    return f'{m.group(1)}/abs{urllib.parse.quote(os.path.abspath(p))}{m.group(3)}'
                art = re.sub(r'(<img[^>]*?\ssrc=")([^"]+)(")', fix, art)
                return self._send(200, json.dumps({"html": art, "meta": meta, "warnings": warnings,
                                                   "mtime": os.path.getmtime(md_path)}, ensure_ascii=False))
            if u.path.startswith("/files/") or u.path.startswith("/abs/"):
                if u.path.startswith("/files/"):
                    p = os.path.normpath(os.path.join(base, urllib.parse.unquote(u.path[len("/files/"):])))
                else:
                    p = os.path.normpath(urllib.parse.unquote(u.path[len("/abs"):]))
                allowed = [os.path.abspath(base)] + ([os.path.abspath(ws)] if ws else [])
                if not any(p.startswith(a + os.sep) for a in allowed) or not os.path.isfile(p):
                    return self._send(404, "not found", "text/plain")
                with open(p, "rb") as fh:
                    return self._send(200, fh.read(), mimetypes.guess_type(p)[0] or "application/octet-stream")
            return self._send(404, "not found", "text/plain")

        def do_POST(self):
            if self.path == "/save":
                n = int(self.headers.get("Content-Length", 0))
                d = json.loads(self.rfile.read(n) or b"{}")
                set_front_matter(md_path, {"theme": d.get("theme"), "scheme": d.get("scheme")})
                return self._send(200, json.dumps({"ok": True}))
            return self._send(404, "not found", "text/plain")

    return H


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("md")
    ap.add_argument("--theme")
    ap.add_argument("--scheme")
    ap.add_argument("--workspace")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args()
    ws = find_workspace(a.workspace)
    md = os.path.abspath(a.md)
    _, meta = convert(md, a.theme, ws, False, a.scheme)
    state = {"theme": meta["theme"], "scheme": meta.get("scheme", "")}
    srv = None
    for port in range(a.port, a.port + 20):
        try:
            srv = ThreadingHTTPServer((a.host, port), make_handler(md, ws, state))
            break
        except OSError:
            continue
    if not srv:
        sys.exit("没有可用端口")
    url = f"http://{a.host}:{srv.server_address[1]}/"
    print(f"预览地址：{url}\n文章：{md}\n保存文件后浏览器会自动刷新，Ctrl+C 退出。")
    if not a.no_open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已退出")


if __name__ == "__main__":
    main()
