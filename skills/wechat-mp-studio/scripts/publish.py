#!/usr/bin/env python3
"""微信公众号发布：上传图片 → 创建草稿 →（可选）发布。仅用 Python 标准库（压缩图片时用 Pillow）。

命令:
  python3 publish.py myip                         查看本机出口 IP（需加入公众号 IP 白名单）
  python3 publish.py check   [--account main]     校验 AppID/AppSecret 能否拿到 access_token
  python3 publish.py draft   <build_dir> [--cover cover.jpg] [--account main] [--comment]
  python3 publish.py publish <draft_media_id> --yes    提交发布（freepublish，不群发推送）
  python3 publish.py status  <publish_id>               查询发布状态与文章链接

凭证读取顺序: 环境变量 WECHAT_APPID / WECHAT_APPSECRET > <workspace>/config.json 的 accounts
workspace 由 --workspace、环境变量 WECHAT_MP_WORKSPACE 或当前目录向上查找确定。
"""
import argparse
import hashlib
import io
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import find_workspace  # noqa: E402

API = os.environ.get("WECHAT_API_BASE", "https://api.weixin.qq.com")

ERR_HINTS = {
    40001: "AppSecret 错误或 access_token 失效",
    40013: "AppID 无效",
    40125: "AppSecret 无效",
    40164: "调用 IP 不在白名单：到 公众平台 → 设置与开发 → 基本配置 → IP白名单 添加本机出口 IP（运行 myip 查看）",
    41001: "缺少 access_token",
    42001: "access_token 过期，重试即可",
    44002: "POST 数据为空",
    45009: "接口调用超过每日上限",
    48001: "公众号没有该接口权限（草稿/发布接口需认证的订阅号或服务号）",
    40007: "media_id 无效（封面需先上传为永久素材）",
    45002: "正文内容过长（限 2 万字符 / 1MB）",
    45003: "标题过长",
    45004: "摘要过长",
    53503: "该草稿未通过发布检查（可能含违规内容或格式问题），请在后台查看",
}


# ---------------- 基础 ----------------
def ws_path(ws, *p):
    return os.path.join(ws, *p) if ws else None


def load_cfg(ws):
    p = ws_path(ws, "config.json")
    if p and os.path.isfile(p):
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def creds(ws, account):
    if os.environ.get("WECHAT_APPID") and os.environ.get("WECHAT_APPSECRET"):
        return os.environ["WECHAT_APPID"], os.environ["WECHAT_APPSECRET"]
    cfg = load_cfg(ws)
    accts = cfg.get("accounts", {})
    name = account or cfg.get("default_account") or (next(iter(accts)) if accts else None)
    a = accts.get(name or "", {})
    if not a.get("appid") or not a.get("appsecret"):
        sys.exit("未配置凭证：设置环境变量 WECHAT_APPID/WECHAT_APPSECRET，或在 config.json 的 accounts 中填写 appid/appsecret")
    return a["appid"], a["appsecret"]


def http(method, url, data=None, headers=None, timeout=60):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"❌ HTTP {e.code} {url.split('?')[0]}")
    except urllib.error.URLError as e:
        sys.exit(f"❌ 网络错误 {url.split('?')[0]}：{e.reason}（检查网络/代理；若在受限环境，请在本机终端运行）")


def check(resp):
    if isinstance(resp, (bytes, bytearray)):
        resp = json.loads(resp.decode("utf-8"))
    code = resp.get("errcode", 0)
    if code:
        hint = ERR_HINTS.get(code, "")
        if code == 40164:
            m = re.search(r"invalid ip ([\d.]+)", resp.get("errmsg", ""))
            if m:
                hint = f"微信看到的调用 IP 是 {m.group(1)}（以此为准，可能与 myip 不同）→ 公众平台 → 设置与开发 → 基本配置 → IP白名单 添加它"
        sys.exit(f"❌ 微信接口错误 {code}: {resp.get('errmsg')}\n   {hint}")
    return resp


def post_json(url, obj):
    body = json.dumps(obj, ensure_ascii=False).encode("utf-8")  # 必须 ensure_ascii=False，否则中文变 \\u
    return check(http("POST", url, body, {"Content-Type": "application/json; charset=utf-8"}))


def multipart(url, field, filename, content, ctype):
    boundary = "----wx" + uuid.uuid4().hex
    head = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode()
    body = head + content + f"\r\n--{boundary}--\r\n".encode()
    return check(http("POST", url, body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}))


def token(ws, account, force=False):
    appid, secret = creds(ws, account)
    cache = ws_path(ws, ".cache", f"token_{appid}.json")
    if cache and not force and os.path.isfile(cache):
        with open(cache) as fh:
            t = json.load(fh)
        if t["expires_at"] > time.time() + 120:
            return t["access_token"]
    r = post_json(f"{API}/cgi-bin/stable_token",
                  {"grant_type": "client_credential", "appid": appid, "secret": secret, "force_refresh": False})
    if cache:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, "w") as fh:
            json.dump({"access_token": r["access_token"], "expires_at": time.time() + r["expires_in"]}, fh)
        os.chmod(cache, 0o600)
    return r["access_token"]


# ---------------- 图片 ----------------
def read_image(src, base_dir):
    if re.match(r"https?://", src):
        data = http("GET", src, headers={"User-Agent": "Mozilla/5.0"})
        name = os.path.basename(urllib.parse.urlparse(src).path) or "img.jpg"
    else:
        src = os.path.expanduser(src)
        p = src if os.path.isabs(src) else os.path.join(base_dir, src)
        p = urllib.parse.unquote(p)
        with open(p, "rb") as fh:
            data = fh.read()
        name = os.path.basename(p)
    return data, name


def shrink(data, name, limit, force=False):
    """超出体积上限（或 force）时转为 JPEG（宽 ≤1080）。"""
    if not force and len(data) <= limit:
        return data, name
    try:
        from PIL import Image
    except ImportError:
        sys.exit(f"图片 {name} 超过 {limit // 1024}KB，需要 pip install pillow 自动压缩")
    im = Image.open(io.BytesIO(data)).convert("RGB")
    if im.width > 1080:
        im = im.resize((1080, int(im.height * 1080 / im.width)))
    q = 88
    while True:
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True)
        if buf.tell() <= limit or q <= 40:
            return buf.getvalue(), os.path.splitext(name)[0] + ".jpg"
        q -= 8


def ctype_of(name):
    return mimetypes.guess_type(name)[0] or "image/jpeg"


def upload_content_image(tk, data, name):
    # uploadimg 仅支持 jpg/png 且 ≤1MB；其他格式（webp/gif 等）转 JPEG（GIF 会丢动画）
    if not name.lower().endswith((".jpg", ".jpeg", ".png")):
        data, name = shrink(data, name, 1024 * 1024 - 1024, force=True)
    else:
        data, name = shrink(data, name, 1024 * 1024 - 1024)
    return multipart(f"{API}/cgi-bin/media/uploadimg?access_token={tk}", "media", name, data, ctype_of(name))["url"]


def upload_cover(tk, data, name):
    data, name = shrink(data, name, 9 * 1024 * 1024)  # 永久图片素材限 10MB
    r = multipart(f"{API}/cgi-bin/material/add_material?access_token={tk}&type=image",
                  "media", name, data, ctype_of(name))
    return r["media_id"], r.get("url")


def replace_images(html_str, tk, base_dir, cache_file):
    cache = {}
    if cache_file and os.path.isfile(cache_file):
        with open(cache_file) as fh:
            cache = json.load(fh)
    first = None

    def sub(m):
        nonlocal first
        src = m.group(2)
        if "mmbiz.qpic.cn" in src or src.startswith("data:"):
            first = first or (src, None)
            return m.group(0)
        data, name = read_image(src, base_dir)
        key = hashlib.sha1(data).hexdigest()
        if key not in cache:
            print(f"  ↑ 上传图片 {name}")
            cache[key] = upload_content_image(tk, data, name)
        first = first or (src, data)
        return f'{m.group(1)}{cache[key]}{m.group(3)}'

    out = re.sub(r'(<img[^>]*?\ssrc=")([^"]+)(")', sub, html_str)
    if cache_file:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, "w") as fh:
            json.dump(cache, fh)
    return out, first


# ---------------- 命令 ----------------
def cmd_myip(_a):
    ip = http("GET", "https://api.ipify.org").decode().strip()
    print(f"出口 IP：{ip}\n请在 公众平台 → 设置与开发 → 基本配置 → IP白名单 中添加它。")


def cmd_check(a):
    tk = token(a.workspace, a.account, force=True)
    print(f"✅ 凭证有效，access_token 获取成功（{tk[:8]}…）")


def cmd_draft(a):
    build = a.build_dir
    with open(os.path.join(build, "meta.json"), encoding="utf-8") as fh:
        meta = json.load(fh)
    with open(os.path.join(build, "article.html"), encoding="utf-8") as fh:
        html_str = fh.read()
    md_dir = os.path.dirname(meta.get("source_md", "")) or build
    tk = token(a.workspace, a.account)

    print("① 上传正文图片")
    html_str, first = replace_images(html_str, tk, md_dir, ws_path(a.workspace, ".cache", "images.json"))

    print("② 上传封面")
    if a.cover:
        cdata, cname = read_image(os.path.abspath(a.cover), md_dir)
    elif meta.get("cover"):
        cdata, cname = read_image(meta["cover"], md_dir)
    elif first and first[1]:
        cdata, cname = first[1], "cover.jpg"
        print("  （未指定封面，使用正文第一张图）")
    else:
        sys.exit("没有封面：用 --cover 指定，或先运行 cover.py 生成")
    thumb_id, _ = upload_cover(tk, cdata, cname)

    title = meta.get("title", "").strip()
    if not title:
        sys.exit("meta.json 缺少 title")
    art = {
        "title": title[:64],
        "author": (a.author or meta.get("author") or "")[:16],
        "digest": (meta.get("digest") or "")[:120],
        "content": html_str,
        "content_source_url": meta.get("source_url", ""),
        "thumb_media_id": thumb_id,
        "need_open_comment": 1 if a.comment else 0,
        "only_fans_can_comment": 0,
    }
    print("③ 创建草稿")
    r = post_json(f"{API}/cgi-bin/draft/add?access_token={tk}", {"articles": [art]})
    media_id = r["media_id"]
    meta["draft_media_id"] = media_id
    with open(os.path.join(build, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    print(f"✅ 草稿已创建 media_id={media_id}\n   到 公众平台 → 内容与互动 → 草稿箱 预览/群发。")
    if a.publish:
        cmd_publish(argparse.Namespace(**{**vars(a), "media_id": media_id}))


def cmd_publish(a):
    if not a.yes:
        sys.exit("发布不可撤回（只能删除）。确认后加 --yes 再运行。")
    tk = token(a.workspace, a.account)
    r = post_json(f"{API}/cgi-bin/freepublish/submit?access_token={tk}", {"media_id": a.media_id})
    pid = r["publish_id"]
    print(f"已提交发布 publish_id={pid}，等待审核…")
    for _ in range(12):
        time.sleep(5)
        if cmd_status(argparse.Namespace(**{**vars(a), "publish_id": pid}), quiet=True):
            return
    print(f"仍在处理中，稍后运行：python3 publish.py status {pid}")


def cmd_status(a, quiet=False):
    tk = token(a.workspace, a.account)
    r = post_json(f"{API}/cgi-bin/freepublish/get?access_token={tk}", {"publish_id": str(a.publish_id)})
    st = r.get("publish_status")
    names = {0: "发布成功", 1: "发布中", 2: "原创声明失败", 3: "常规失败", 4: "平台审核不通过",
             5: "成功后用户删除", 6: "成功后系统封禁"}
    if st == 1 and quiet:
        return False
    print(f"状态：{names.get(st, st)}")
    for item in (r.get("article_detail") or {}).get("item", []):
        print(f"  文章链接：{item.get('article_url')}")
    if r.get("fail_idx"):
        print(f"  失败文章序号：{r['fail_idx']}")
    return st != 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", help="工作区目录（默认 $WECHAT_MP_WORKSPACE 或自动向上查找）")
    ap.add_argument("--account")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("myip").set_defaults(fn=cmd_myip)
    sp.add_parser("check").set_defaults(fn=cmd_check)
    d = sp.add_parser("draft")
    d.add_argument("build_dir")
    d.add_argument("--cover")
    d.add_argument("--author")
    d.add_argument("--comment", action="store_true", help="打开留言")
    d.add_argument("--publish", action="store_true", help="创建草稿后立即提交发布（需同时 --yes）")
    d.add_argument("--yes", action="store_true")
    d.set_defaults(fn=cmd_draft)
    p = sp.add_parser("publish")
    p.add_argument("media_id")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(fn=cmd_publish)
    s = sp.add_parser("status")
    s.add_argument("publish_id")
    s.set_defaults(fn=cmd_status)
    a = ap.parse_args()
    a.workspace = find_workspace(a.workspace)
    a.fn(a)


if __name__ == "__main__":
    main()
