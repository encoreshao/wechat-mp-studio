#!/usr/bin/env python3
"""本地实时预览：启动一个只监听本机的小服务器，浏览器里手机宽度预览文章。

用法:
  python3 preview.py articles/<dir>/article.md [--theme tech-blue] [--scheme 黛蓝] [--port 8765] [--no-open]

功能:
  - 左侧栏勾选主题（最多 4 个并排对比），每个主题可单独选配色
  - 保存 article.md 后自动刷新（无需重新运行）
  - 「复制到公众号」：复制带内联样式的富文本，可直接粘贴进公众号编辑器
    （本地图片粘贴后需在编辑器里重新上传；用 publish.py draft 推草稿会自动上传）
  - 「推草稿箱」：用该主题/配色排版并推送到公众号草稿箱
  - 「设为本文主题」：把该主题/配色写回 article.md 的 front matter
仅依赖标准库 + convert.py 的依赖（markdown、beautifulsoup4）。
"""
import argparse
import html
import json
import mimetypes
import os
import re
import subprocess
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

REPO_URL = "https://github.com/encoreshao/wechat-mp-studio"

PAGE = r"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>预览 · __TITLE__</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#ececef;font-family:-apple-system,'PingFang SC',sans-serif;color:#222}
.layout{display:flex;min-height:100vh}
.sidebar{position:sticky;top:0;height:100vh;width:300px;flex:none;overflow-y:auto;background:#fff;border-right:1px solid #ddd;
 padding:18px 16px 24px;font-size:13px}
.sidebar h3{margin:0 0 4px;font-size:15px}
.sidebar h4{margin:20px 0 8px;font-size:12px;color:#888;font-weight:500;display:flex;justify-content:space-between}
select,button{font-size:13px;padding:5px 9px;border:1px solid #ccc;border-radius:8px;background:#fff;cursor:pointer}
button.primary{background:#07c160;border-color:#07c160;color:#fff}
select:disabled{opacity:.5;cursor:default}
.info{color:#888;line-height:1.6}
.warn{color:#b26b00;line-height:1.6;margin-top:6px}
.wxlink{margin-top:6px;line-height:1.6}.wxlink a{color:#07c160}
.themes{display:flex;flex-direction:column;gap:2px}
.trow{display:flex;align-items:center;gap:8px;padding:5px 6px;border-radius:8px}
.trow:hover{background:#f5f5f7}
.trow.on{background:#eef8f1}
.trow label{flex:1;display:flex;align-items:center;gap:8px;cursor:pointer}
.trow.off label{color:#aaa;cursor:not-allowed}
.trow select{padding:3px 6px;font-size:12px;max-width:96px}
.seg{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px}
.seg button{padding:3px 8px;font-size:12px;border-radius:6px}
.gh{display:flex;gap:8px;margin-top:16px;padding-top:14px;border-top:1px solid #eee}
.gh a{flex:1;text-align:center;font-size:12px;color:#333;text-decoration:none;border:1px solid #ddd;border-radius:8px;padding:6px 0}
.gh a:hover{background:#f5f5f7}
.seg button.on{background:#222;border-color:#222;color:#fff}
.stage{background:#ededed;border-radius:10px;padding:12px}
.clamp{display:-webkit-box;-webkit-box-orient:vertical;overflow:hidden}
.cover{display:block;object-fit:cover;background:#ccc}
.v-feed{background:#fff;border-radius:8px;overflow:hidden}
.v-feed .acct{display:flex;align-items:center;gap:6px;padding:10px 12px 8px;font-size:12px;color:#555}
.v-feed .acct i{width:20px;height:20px;border-radius:50%;background:#07c160;display:inline-block}
.v-feed .cover{width:100%;aspect-ratio:2.35/1}
.v-feed .t{padding:10px 12px 12px;font-size:15px;font-weight:600;line-height:1.4;-webkit-line-clamp:2}
.v-list{background:#fff;border-radius:8px;padding:12px;display:flex;gap:10px;align-items:flex-start}
.v-list .t{flex:1;font-size:15px;line-height:1.45;-webkit-line-clamp:2}
.v-list .cover{width:56px;height:56px;flex:none;border-radius:4px}
.v-chat{display:flex;gap:8px;align-items:flex-start;justify-content:flex-end}
.v-chat .bub{width:220px;background:#fff;border-radius:6px;padding:10px 12px}
.v-chat .t{font-size:14px;line-height:1.4;-webkit-line-clamp:2;margin-bottom:6px}
.v-chat .row{display:flex;gap:8px}
.v-chat .d{flex:1;font-size:12px;color:#999;line-height:1.45;-webkit-line-clamp:3}
.v-chat .cover{width:44px;height:44px;flex:none}
.v-chat .src{border-top:1px solid #f0f0f0;margin-top:8px;padding-top:6px;font-size:11px;color:#aaa}
.v-chat .me{width:32px;height:32px;border-radius:4px;background:#9bb;flex:none}
.v-moments{display:flex;gap:8px}
.v-moments .me{width:36px;height:36px;border-radius:4px;background:#9bb;flex:none}
.v-moments .nm{font-size:13px;color:#576b95;font-weight:600;margin-bottom:6px}
.v-moments .box{background:#f3f3f5;display:flex;gap:8px;padding:6px;align-items:center}
.v-moments .cover{width:40px;height:40px;flex:none}
.v-moments .t{font-size:13px;line-height:1.4;-webkit-line-clamp:2}
.main{flex:1;min-width:0;overflow-x:auto}
.phones{display:flex;gap:24px;padding:24px;align-items:flex-start;width:max-content;margin:0 auto}
.col{display:flex;flex-direction:column;gap:10px}
.head{display:flex;align-items:center;gap:8px;font-size:13px}
.head b{flex:1;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.head button{padding:4px 9px;font-size:12px}
button:disabled{opacity:.6;cursor:wait}
.phone{width:390px;background:#fff;border-radius:28px;border:10px solid #1c1c1e;box-shadow:0 6px 30px rgba(0,0,0,.12);overflow:hidden}
.top{height:44px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:600;border-bottom:1px solid #f0f0f0}
.body{padding:20px 16px 40px}
.body h1.ti{font-size:22px;line-height:1.4;margin:0 0 10px;color:#111}
.meta{font-size:14px;color:#576b95;margin:0 0 22px}
.empty{padding:80px 24px;color:#888;font-size:14px}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#111;color:#fff;padding:10px 16px;border-radius:8px;
 font-size:13px;opacity:0;transition:opacity .2s;pointer-events:none;z-index:9}
.toast.on{opacity:.92}
.err{color:#e5484d;white-space:pre-wrap;font-size:13px}
@media(max-width:820px){.layout{flex-direction:column}.sidebar{position:static;height:auto;width:100%;border-right:0;border-bottom:1px solid #ddd}
 .phone{width:min(390px,calc(100vw - 32px))}.phones{padding:16px}}
</style></head><body>
<div class="layout">
<aside class="sidebar">
  <h3>__TITLE__</h3>
  <div class="info" id="info"></div>
  <div class="warn" id="warn"></div>
  <div class="wxlink" id="wxlink"></div>
  <h4><span>主题（最多 4 个并排对比）</span><span id="count"></span></h4>
  <div class="themes" id="themes"></div>
  <h4><span>消息卡片样式</span></h4>
  <div class="seg" id="cardseg"></div>
  <div class="stage" id="cardstage"></div>
  <p class="info" id="cardnote" style="margin:8px 0 0;font-size:12px"></p>
  <p class="info" style="margin-top:14px">保存 article.md 后页面会自动刷新。<br>
  「复制」后在公众号编辑器里粘贴即可，本地图片需要重新上传。<br>「设为本文主题」写回 article.md 的 front matter。<br>「推草稿箱」用该主题排版并推送到公众号草稿箱（需已配置凭证和 IP 白名单），成功后显示 mp.weixin.qq.com 预览链接。</p>
  <div class="gh"><a href="__REPO__" target="_blank" rel="noopener">⭐ Star on GitHub</a>
  <a href="__REPO__/issues/new" target="_blank" rel="noopener">反馈问题</a></div>
</aside>
<main class="main"><div class="phones" id="phones"></div></main>
</div>
<div class="toast" id="toast"></div>
<script>
const MAX=4, $=id=>document.getElementById(id);
let THEMES={}, CURRENT={}, picks=[], mtime=0;
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function toast(t){const e=$('toast');e.textContent=t;e.classList.add('on');setTimeout(()=>e.classList.remove('on'),1800)}
function store(){try{localStorage.setItem('wmp-picks',JSON.stringify(picks))}catch(e){}}
function restore(){try{const v=JSON.parse(localStorage.getItem('wmp-picks')||'null');
  if(Array.isArray(v)) return v.filter(p=>THEMES[p.theme]).slice(0,MAX)}catch(e){} return null}
function schemeOf(theme){const p=picks.find(x=>x.theme===theme); return p?p.scheme:''}
function drawList(){
  const box=$('themes'); box.innerHTML='';
  for(const [k,v] of Object.entries(THEMES)){
    const on=picks.some(p=>p.theme===k), full=!on&&picks.length>=MAX;
    const row=document.createElement('div'); row.className='trow'+(on?' on':'')+(full?' off':'');
    row.innerHTML='<label><input type="checkbox"'+(on?' checked':'')+(full?' disabled':'')+'>'+esc(v.label)+'</label>';
    row.querySelector('input').onchange=e=>toggle(k,e.target.checked);
    if(v.schemes.length){const s=document.createElement('select'); s.disabled=!on;
      v.schemes.forEach(x=>{const o=document.createElement('option');o.value=o.textContent=x;s.appendChild(o)});
      s.value=schemeOf(k)||v.schemes[0]; s.onchange=()=>{const p=picks.find(x=>x.theme===k); if(p){p.scheme=s.value;store();renderOne(p)}};
      row.appendChild(s)}
    box.appendChild(row)}
  $('count').textContent=picks.length+' / '+MAX;
}
function toggle(theme,on){
  if(on){if(picks.length>=MAX) return; picks.push({theme,scheme:(THEMES[theme].schemes[0]||'')})}
  else picks=picks.filter(p=>p.theme!==theme);
  store(); drawList(); drawPhones();
}
function drawPhones(){
  const box=$('phones'); box.innerHTML='';
  if(!picks.length){box.innerHTML='<div class="empty">在左侧勾选主题开始预览</div>';return}
  picks.forEach(p=>{
    const col=document.createElement('div'); col.className='col';
    col.innerHTML='<div class="head"><b></b><button data-a="save">设为本文主题</button><button data-a="copy">复制</button><button data-a="draft" class="primary">推草稿箱</button></div>'+
      '<div class="phone"><div class="top">公众号文章</div><div class="body"><h1 class="ti"></h1><p class="meta"></p><div class="art"></div></div></div>';
    col.querySelector('[data-a=save]').onclick=()=>save(p);
    col.querySelector('[data-a=copy]').onclick=()=>copy(col.querySelector('.art'));
    col.querySelector('[data-a=draft]').onclick=e=>draft(p,e.target);
    p.el=col; box.appendChild(col); renderOne(p)});
}
async function renderOne(p){
  const col=p.el; if(!col) return;
  const v=THEMES[p.theme]; col.querySelector('.head b').textContent=v.label+(p.scheme?' · '+p.scheme:'');
  const isCur=p.theme===CURRENT.theme&&(p.scheme||'')===(CURRENT.scheme||'');
  col.querySelector('[data-a=save]').textContent=isCur?'✓ 本文主题':'设为本文主题';
  const j=await (await fetch('/render?'+new URLSearchParams({theme:p.theme,scheme:p.scheme}))).json();
  const art=col.querySelector('.art');
  if(j.error){art.innerHTML='<p class="err">'+esc(j.error)+'</p>';return}
  art.innerHTML=j.html; col.querySelector('.ti').textContent=j.meta.title||''; col.querySelector('.meta').textContent=j.meta.author||'';
  if(p===picks[0]){
    CARD={title:j.meta.title||'',digest:j.meta.digest||'',author:j.meta.author||'',
      cover:j.meta.cover?('/files/'+encodeURI(j.meta.cover)+'?t='+Date.now()):''}; drawCard();
    $('info').textContent=(j.meta.word_count||0)+' 字';
    $('warn').textContent=j.warnings&&j.warnings.length?'⚠ '+j.warnings.join('；'):'';
  }
  mtime=j.mtime;
}
async function copy(el){
  try{await navigator.clipboard.write([new ClipboardItem({'text/html':new Blob([el.innerHTML],{type:'text/html'}),'text/plain':new Blob([el.innerText],{type:'text/plain'})})]);toast('已复制，去公众号编辑器粘贴')}
  catch(e){const r=document.createRange();r.selectNodeContents(el);const s=getSelection();s.removeAllRanges();s.addRange(r);document.execCommand('copy');s.removeAllRanges();toast('已复制')}
}
async function save(p){
  const r=await fetch('/save',{method:'POST',body:JSON.stringify({theme:p.theme,scheme:p.scheme})});
  if(!(await r.json()).ok) return toast('保存失败');
  CURRENT={theme:p.theme,scheme:p.scheme}; toast('已写入 article.md 的 front matter'); picks.forEach(renderOne);
}
const CARD_STYLES={
  feed:{label:'大图',note:'订阅号头条：封面按 2.35:1 裁切，标题最多两行'},
  list:{label:'小图',note:'订阅号次条/列表：封面按 1:1 居中裁切'},
  chat:{label:'聊天',note:'转发给好友：显示摘要，封面 1:1'},
  moments:{label:'朋友圈',note:'分享到朋友圈：只显示标题，封面 1:1'}};
let CARD={title:'',digest:'',author:'',cover:''}, cardStyle='feed';
try{const v=localStorage.getItem('wmp-card'); if(CARD_STYLES[v]) cardStyle=v}catch(e){}
function drawCard(){
  const seg=$('cardseg'); seg.innerHTML='';
  for(const [k,v] of Object.entries(CARD_STYLES)){const b=document.createElement('button');b.textContent=v.label;
    if(k===cardStyle) b.className='on'; b.onclick=()=>{cardStyle=k;try{localStorage.setItem('wmp-card',k)}catch(e){};drawCard()}; seg.appendChild(b)}
  const img='<img class="cover" alt=""'+(CARD.cover?' src="'+esc(CARD.cover)+'"':'')+'>';
  const t=esc(CARD.title), d=esc(CARD.digest), a=esc(CARD.author||'公众号');
  $('cardstage').innerHTML={
    feed:'<div class="v-feed"><div class="acct"><i></i>'+a+'</div>'+img+'<div class="t clamp">'+t+'</div></div>',
    list:'<div class="v-list"><div class="t clamp">'+t+'</div>'+img+'</div>',
    chat:'<div class="v-chat"><div class="bub"><div class="t clamp">'+t+'</div><div class="row"><div class="d clamp">'+d+'</div>'+img+'</div><div class="src">'+a+'</div></div><div class="me"></div></div>',
    moments:'<div class="v-moments"><div class="me"></div><div style="flex:1"><div class="nm">我</div><div class="box">'+img+'<div class="t clamp">'+t+'</div></div></div></div>'
  }[cardStyle];
  $('cardnote').textContent=CARD_STYLES[cardStyle].note;
}
async function draft(p,btn){
  btn.disabled=true; const old=btn.textContent; btn.textContent='推送中…';
  try{const j=await (await fetch('/draft',{method:'POST',body:JSON.stringify({theme:p.theme,scheme:p.scheme})})).json();
    toast(j.ok?'✅ 已推送到草稿箱':'推送失败');
    if(j.ok&&j.url){const a=document.createElement('a');a.href=j.url;a.target='_blank';a.rel='noopener';
      a.textContent='在微信中查看草稿（临时链接）↗';$('wxlink').replaceChildren(a)}
    $('warn').textContent=j.ok?'':'⚠ '+(j.error||'').trim().split('\n').slice(-3).join(' ');
  }catch(e){toast('推送失败')}
  btn.disabled=false; btn.textContent=old;
}
async function init(){
  const j=await (await fetch('/themes')).json(); THEMES=j.themes; CURRENT=j.current;
  picks=restore()||[];
  if(!picks.length&&THEMES[CURRENT.theme]) picks=[{theme:CURRENT.theme,scheme:CURRENT.scheme||(THEMES[CURRENT.theme].schemes[0]||'')}];
  drawList(); drawPhones();
  setInterval(async()=>{try{const m=(await (await fetch('/mtime')).json()).mtime; if(m!==mtime) picks.forEach(renderOne)}catch(e){}},1000);
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


def push_draft(md_path, ws, theme, scheme):
    here = os.path.dirname(os.path.abspath(__file__))
    wsargs = ["--workspace", ws] if ws else []
    build = os.path.splitext(md_path)[0] + "_build"
    conv = [sys.executable, os.path.join(here, "convert.py"), md_path, "--out", build, *wsargs]
    if theme:
        conv += ["--theme", theme]
    if scheme:
        conv += ["--scheme", scheme]
    steps = [conv, [sys.executable, os.path.join(here, "publish.py"), *wsargs, "draft", build]]
    for cmd in steps:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            return {"ok": False, "error": (r.stderr or r.stdout).strip()}
    try:
        with open(os.path.join(build, "meta.json"), encoding="utf-8") as fh:
            url = json.load(fh).get("draft_url", "")
    except (OSError, ValueError):
        url = ""
    return {"ok": True, "log": r.stdout, "url": url if url.startswith("https://mp.weixin.qq.com/") else ""}


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
                return self._send(200, PAGE.replace("__TITLE__", html.escape(os.path.basename(base))).replace("__REPO__", REPO_URL),
                                  "text/html; charset=utf-8")
            if u.path == "/themes":
                return self._send(200, json.dumps({"themes": theme_catalog(ws), "current": state}, ensure_ascii=False))
            if u.path == "/mtime":
                return self._send(200, json.dumps({"mtime": os.path.getmtime(md_path)}))
            if u.path == "/render":
                theme = q.get("theme") or state["theme"]
                scheme = q.get("scheme") or None
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
                state.update(theme=d.get("theme") or state["theme"], scheme=d.get("scheme") or "")
                return self._send(200, json.dumps({"ok": True}))
            if self.path == "/draft":
                n = int(self.headers.get("Content-Length", 0))
                d = json.loads(self.rfile.read(n) or b"{}")
                return self._send(200, json.dumps(push_draft(md_path, ws, d.get("theme"), d.get("scheme")),
                                                  ensure_ascii=False))
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
