#!/usr/bin/env python3
"""Markdown → 微信公众号 HTML（全部内联样式）。

用法:
  python3 convert.py article.md [--theme tech-blue] [--workspace DIR] [--out DIR] [--keep-links]
  python3 convert.py --list-themes [--workspace DIR]

输出 (--out，默认与 md 同目录下 <文件名>_build/):
  article.html  只含正文的 HTML 片段（发布用）
  preview.html  手机宽度预览页（浏览器打开查看）
  meta.json     标题/作者/摘要/封面/主题等元数据

Markdown 扩展:
  文件头 front matter（--- 包裹，key: value）：title author digest cover theme source_url
  ::: tip 标题 / ::: note / ::: warning / ::: danger / ::: quote  ...  :::   提示框
  {{footer}} {{divider}} {{author}} 以及 templates/components/<名称>.md|.html 自定义组件
依赖: pip install markdown beautifulsoup4
"""
import argparse
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import find_workspace  # noqa: E402
from themes import get_theme, list_themes, resolve_name  # noqa: E402

try:
    import markdown
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("缺少依赖：pip install markdown beautifulsoup4")

MD_EXT = ["extra", "sane_lists"]


def load_config(ws):
    p = os.path.join(ws or "", "config.json")
    if ws and os.path.isfile(p):
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def parse_front_matter(text):
    meta = {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"').strip("'")
        text = text[m.end():]
    return meta, text


LIST_RE = re.compile(r"^( +)([-*+]|\d+[.)]) ", re.M)


def normalize_list_indent(text):
    """python-markdown 要求嵌套列表缩进 4 空格；把 2/3 空格缩进统一放大到 4 的倍数。"""
    indents = [len(m.group(1)) for m in LIST_RE.finditer(text)]
    if not indents:
        return text
    unit = min(indents)
    if unit >= 4:
        return text
    return LIST_RE.sub(lambda m: " " * (4 * max(1, round(len(m.group(1)) / unit))) + m.group(2) + " ", text)


def md_to_html(text):
    return markdown.markdown(normalize_list_indent(text), extensions=MD_EXT)


# ---------- 组件 ----------
def resolve_asset(path, ws):
    """config 里的图片路径：支持绝对路径、~/、以及相对工作区的路径。"""
    if not path or re.match(r"https?://", path):
        return path
    cands = [os.path.expanduser(path)]
    if ws:
        cands.append(os.path.join(ws, re.sub(r"^~/", "", path)))
    for c in cands:
        if os.path.isfile(c):
            return os.path.abspath(c)
    print(f"⚠️ 找不到图片 {path}", file=sys.stderr)
    return path


def builtin_component(name, cfg, theme):
    p = theme["_primary"]
    acct = cfg.get("account_name", "")
    if name == "divider":
        dot = (f'<span style="display:inline-block;width:6px;height:6px;border-radius:50%;'
               f'background:{p};margin:0 8px;vertical-align:middle;"></span>')
        return f'<section style="text-align:center;margin:32px 0;line-height:1;">{dot * 3}</section>'
    if name == "author":
        a = cfg.get("author", "")
        bio = cfg.get("author_bio", "")
        if bio == "一句话作者简介":  # config.example 的占位文字
            bio = ""
        return (f'<section style="margin:28px 0;padding:14px 16px;border:1px solid #eee;border-radius:6px;">'
                f'<p style="margin:0;font-weight:bold;color:{p};">作者 · {html.escape(a)}</p>'
                + (f'<p style="margin:6px 0 0;font-size:13px;color:#888;">{html.escape(bio)}</p>' if bio else "")
                + '</section>')
    if name == "footer":
        f = cfg.get("footer", {})
        text = f.get("text", f"喜欢这篇文章？点个「在看」，关注「{acct}」获取更多内容。" if acct else "")
        qr = resolve_asset(f.get("qr_image", ""), cfg.get("_workspace"))
        parts = [f'<section style="margin:40px 0 10px;padding:20px 16px;background:#fafafa;'
                 f'border-top:2px solid {p};text-align:center;">']
        if text:
            parts.append(f'<p style="margin:0 0 10px;font-size:14px;color:#555;">{html.escape(text)}</p>')
        if qr:
            parts.append(f'<img src="{html.escape(qr)}" alt="" style="width:140px;height:140px;'
                         f'display:block;margin:10px auto 0;" />')
        parts.append("</section>")
        return "".join(parts)
    return None


def _inline_md(s):
    """单行 markdown（加粗/行内代码等）转 HTML，去掉外层 <p>。"""
    h = md_to_html(s.strip())
    return re.sub(r"^<p>(.*)</p>$", r"\1", h, flags=re.S)


def _rows(body, ncol=2):
    rows = []
    for ln in body.strip().splitlines():
        if not ln.strip():
            continue
        parts = [p.strip() for p in ln.split("|")]
        parts += [""] * (ncol - len(parts))
        rows.append(parts[:ncol])
    return rows


def rich_component(kind, arg, body, theme):
    """信息图组件（借鉴 aiworkskills/wechat-article-skills 的组件设计）。
    ::: stat 标题        每行「数字 | 说明」
    ::: quote-card 出处  金句正文
    ::: compare 左 / 右  每行「左 | 右」
    ::: steps 标题       每行「步骤名 | 补充说明」
    ::: checklist 标题   每行「done|todo|warn | 事项」
    ::: lead             开篇导语
    """
    pal = theme.get("_palette") or {}
    ink = theme["_primary"]
    fillc = pal.get("primary-fill", ink)
    soft = pal.get("bg-accent-color", theme["box_note"][0])
    text = pal.get("text-color", "#333333")
    muted = pal.get("text-muted", "#8A8F98")
    title = (f'<section style="font-size:13px;letter-spacing:1px;color:{muted};margin-bottom:12px;">'
             f'{html.escape(arg)}</section>') if arg else ""
    if kind == "lead":
        return (f'<section style="margin:0 0 32px;"><section style="width:36px;height:4px;background:{fillc};'
                f'margin-bottom:14px;"></section><section style="font-size:17px;line-height:1.85;font-weight:500;'
                f'color:{text};">{md_to_html(body)}</section></section>')
    if kind == "quote-card":
        src = (f'<section style="margin-top:14px;font-size:13px;letter-spacing:1px;color:{ink};">— {html.escape(arg)}'
               f'</section>') if arg else ""
        return (f'<section style="margin:32px 0;background:{soft};border-radius:14px;padding:24px 22px;">'
                f'<section style="font-size:44px;line-height:0.8;font-weight:800;color:{ink};margin-bottom:6px;">&#8220;</section>'
                f'<section style="font-size:18px;line-height:1.7;font-weight:600;color:{text};">{_inline_md(body)}</section>{src}</section>')
    rows = _rows(body)
    if kind == "stat":
        items = "".join(
            f'<section style="display:flex;align-items:baseline;padding:0 0 14px;">'
            f'<section style="flex:0 0 auto;min-width:96px;font-size:30px;font-weight:800;line-height:1.1;'
            f'color:{ink};">{_inline_md(a)}</section>'
            f'<section style="flex:1;padding-left:14px;font-size:14px;line-height:1.6;color:{muted};">{_inline_md(b)}</section>'
            f'</section>' for a, b in rows)
        return f'<section style="margin:28px 0;">{title}{items}</section>'
    if kind == "compare":
        left, _, right = arg.partition("/")
        head = (f'<section style="display:flex;margin-bottom:8px;font-size:13px;letter-spacing:1px;">'
                f'<section style="flex:1;color:{muted};">{html.escape(left.strip())}</section><section style="width:10px;"></section>'
                f'<section style="flex:1;color:{ink};font-weight:600;">{html.escape(right.strip())}</section></section>')
        items = "".join(
            f'<section style="display:flex;margin-bottom:8px;font-size:14px;line-height:1.6;">'
            f'<section style="flex:1;padding:10px 12px;background:#F5F6F8;border-radius:8px;color:{muted};">{_inline_md(a)}</section>'
            f'<section style="width:10px;"></section>'
            f'<section style="flex:1;padding:10px 12px;background:{soft};border-radius:8px;color:{text};">{_inline_md(b)}</section>'
            f'</section>' for a, b in rows)
        return f'<section style="margin:28px 0;">{head}{items}</section>'
    if kind == "steps":
        items = "".join(
            f'<section style="display:flex;align-items:flex-start;margin-bottom:14px;">'
            f'<section style="flex:0 0 26px;width:26px;height:26px;line-height:26px;border-radius:50%;background:{fillc};'
            f'color:#FFFFFF;text-align:center;font-size:13px;font-weight:700;">{i}</section>'
            f'<section style="flex:1;padding-left:12px;line-height:1.6;"><section style="font-size:15px;font-weight:700;'
            f'color:{text};">{_inline_md(a)}</section>'
            + (f'<section style="font-size:13.5px;color:{muted};margin-top:2px;">{_inline_md(b)}</section>' if b else "")
            + '</section></section>' for i, (a, b) in enumerate(rows, 1))
        return f'<section style="margin:28px 0;">{title}{items}</section>'
    if kind == "checklist":
        sym = {"done": ("&#10003;", "#07A35A"), "todo": ("&#9675;", muted), "warn": ("!", "#E5484D")}
        items = ""
        for a, b in rows:
            if a.lower() not in sym:  # 漏写状态列
                a, b = "todo", f"{a} {b}".strip()
            s, col = sym[a.lower()]
            items += (f'<section style="display:flex;align-items:baseline;padding:8px 0;border-bottom:1px solid #EEF0F2;">'
                      f'<section style="flex:0 0 22px;color:{col};font-weight:800;font-size:15px;">{s}</section>'
                      f'<section style="flex:1;font-size:15px;line-height:1.6;color:{text};">{_inline_md(b)}</section></section>')
        return f'<section style="margin:28px 0;padding:16px 18px;background:#FAFAFB;border-radius:10px;">{title}{items}</section>'
    return body


def custom_component(name, ws):
    if not ws:
        return None
    base = os.path.join(ws, "templates", "components", name)
    for ext, is_md in ((".html", False), (".md", True)):
        if os.path.isfile(base + ext):
            with open(base + ext, encoding="utf-8") as fh:
                c = fh.read()
            return md_to_html(c) if is_md else c
    return None


def preprocess(text, cfg, theme, ws):
    """把 ::: 容器和 {{组件}} 换成占位符，转换后再替换回 HTML。"""
    blocks = {}

    def stash(html_str):
        key = f"WXBLOCK{len(blocks)}X"
        blocks[key] = html_str
        return f"\n\n{key}\n\n"

    box_re = re.compile(r"^:::[ \t]*(tip|note|warning|danger|quote)(?![\w-])[ \t]*([^\n]*)\n(.*?)\n:::[ \t]*$", re.S | re.M)

    def box(m):
        kind, title, body = m.group(1), m.group(2).strip(), m.group(3)
        bg, bd = theme[f"box_{kind}"]
        default_title = {"tip": "小贴士", "note": "说明", "warning": "注意", "danger": "警告", "quote": ""}[kind]
        title = title or default_title
        inner = md_to_html(body)
        head = (f'<p style="margin:0 0 6px;font-weight:bold;color:{bd};font-size:14px;">'
                f'{html.escape(title)}</p>') if title else ""
        return stash(f'<section data-wx="box" style="margin:20px 0;padding:12px 16px;background:{bg};'
                     f'border-left:4px solid {bd};border-radius:4px;font-size:14px;">{head}{inner}</section>')

    text = box_re.sub(box, text)

    comp_re = re.compile(r"^:::[ \t]*(stat|quote-card|compare|steps|checklist|lead)(?![\w-])[ \t]*([^\n]*)\n(.*?)\n:::[ \t]*$",
                         re.S | re.M)
    text = comp_re.sub(lambda m: stash(rich_component(m.group(1), m.group(2).strip(), m.group(3), theme)), text)

    def comp(m):
        name = m.group(1)
        c = custom_component(name, ws) or builtin_component(name, cfg, theme)
        if c is None:
            print(f"⚠️ 未找到组件 {{{{{name}}}}}，已原样保留", file=sys.stderr)
            return m.group(0)
        return stash(c)

    text = re.sub(r"^\{\{\s*([\w-]+)\s*\}\}\s*$", comp, text, flags=re.M)
    return text, blocks


# ---------- 样式化 ----------
def style_tag(tag, css):
    old = tag.get("style", "")
    tag["style"] = css + old


def is_wechat_link(href):
    return bool(re.match(r"https?://mp\.weixin\.qq\.com/", href or ""))


def render_code_block(soup, pre, theme):
    code = pre.find("code")
    raw = code.get_text() if code else pre.get_text()
    raw = raw.rstrip("\n")
    lines = []
    for ln in raw.split("\n"):
        esc = html.escape(ln).replace("\t", "    ")
        # 前导空格转 &nbsp; 保留缩进；行内多空格也保留
        esc = re.sub(r" {2,}", lambda m: "&nbsp;" * len(m.group(0)), esc)
        esc = re.sub(r"^ ", "&nbsp;", esc)
        lines.append(esc or "&nbsp;")
    new = BeautifulSoup(
        f'<section style="{theme["pre"]}"><code style="font-family:inherit;white-space:nowrap;">'
        + "<br>".join(lines) + "</code></section>", "html.parser")
    pre.replace_with(new)


def render_lists(soup, theme):
    """微信对 <ul>/<ol> 支持差（空项目符号、缩进错乱），统一改为带手动符号的悬挂缩进段落。"""
    p = theme["_primary"]

    def render(lst, level):
        out = []
        ordered = lst.name == "ol"
        start = int(lst.get("start", 1)) if ordered else 1
        for i, li in enumerate(lst.find_all("li", recursive=False)):
            nested = [x.extract() for x in li.find_all(["ul", "ol"], recursive=False)]
            marker = f"{start + i}." if ordered else ("•" if level == 0 else "◦")
            w = 1.6 if ordered else 1.1
            pad = level * 1.2 + w
            para = soup.new_tag("p", style=(
                f"margin:6px 0;line-height:1.8;padding-left:{pad}em;text-indent:-{w}em;text-align:left;"))
            m = soup.new_tag("span", style=(
                f"display:inline-block;width:{w}em;text-indent:0;color:{p};"
                + ("font-weight:bold;" if ordered else "")))
            m.string = marker
            para.append(m)
            for child in list(li.contents):
                para.append(child.extract())
            out.append(para)
            for n in nested:
                out.extend(render(n, level + 1))
        return out

    for lst in soup.find_all(["ul", "ol"]):
        if lst.find_parent(["ul", "ol"]) or lst.parent is None:
            continue
        wrap = soup.new_tag("section", style="margin:0 0 18px;")
        for para in render(lst, 0):
            wrap.append(para)
        lst.replace_with(wrap)


def apply_styles(body_html, theme, keep_links=False):
    soup = BeautifulSoup(body_html, "html.parser")
    refs = []

    for pre in soup.find_all("pre"):
        render_code_block(soup, pre, theme)

    simple = ["h1", "h2", "h3", "h4", "p", "blockquote", "strong", "em", "del", "hr", "sup"]
    for name in simple:
        for t in soup.find_all(name):
            if name == "p" and t.find_parent("section", attrs={"data-wx": "box"}):
                style_tag(t, "margin:0 0 8px;")
                continue
            if name == "p" and t.find_parent("blockquote"):
                style_tag(t, "margin:0 0 6px;")
                continue
            style_tag(t, theme[name])
    for t in soup.find_all(["h5", "h6"]):
        t.name = "h4"
        style_tag(t, theme["h4"])
    for t in soup.find_all("b"):
        style_tag(t, theme["strong"])

    # 列表项里的 <p> 去掉，再把列表转成段落
    for li in soup.find_all("li"):
        for p in li.find_all("p", recursive=False):
            p.unwrap()

    # 行内 code（代码块已转为 section）
    for c in soup.find_all("code"):
        if c.find_parent("section") and "white-space:nowrap" in (c.get("style") or ""):
            continue
        style_tag(c, theme["code"])

    # 图片：独占段落时加图注
    for img in soup.find_all("img"):
        style_tag(img, theme["img"])
        alt = img.get("alt", "").strip()
        parent = img.parent
        if parent and parent.name == "p" and len([c for c in parent.contents if str(c).strip()]) == 1:
            parent.name = "section"
            parent["style"] = "margin:0;"
            if alt:
                cap = soup.new_tag("p", style=theme["figcaption"])
                cap.string = alt
                parent.insert_after(cap)

    # 表格
    for tb in soup.find_all("table"):
        style_tag(tb, theme["table"])
        wrap = soup.new_tag("section", style=theme["table_wrap"])
        tb.wrap(wrap)
    for t in soup.find_all("th"):
        style_tag(t, theme["th"])
    for t in soup.find_all("td"):
        style_tag(t, theme["td"])

    # 链接：微信不允许外链跳转 → 转为脚注
    for a in soup.find_all("a"):
        href = a.get("href", "")
        if keep_links or is_wechat_link(href) or href.startswith("#"):
            style_tag(a, theme["a"])
            continue
        text = a.get_text()
        refs.append((text, href))
        n = len(refs)
        span = soup.new_tag("span", style=f"color:{theme['_primary']};")
        span.string = text
        sup = soup.new_tag("sup", style=theme["sup"])
        sup.string = f"[{n}]"
        a.replace_with(span)
        span.insert_after(sup)

    render_lists(soup, theme)
    out = str(soup)
    if refs:
        items = "".join(
            f'<p style="{theme["refs_item"]}">[{i}] {html.escape(t)}：{html.escape(h)}</p>'
            for i, (t, h) in enumerate(refs, 1))
        out += f'<p style="{theme["refs_title"]}">参考资料</p>{items}'
    return out


def convert(md_path, theme_name=None, ws=None, keep_links=False, scheme=None):
    with open(md_path, encoding="utf-8") as fh:
        raw = fh.read()
    cfg = load_config(ws)
    cfg["_workspace"] = ws
    meta, text = parse_front_matter(raw)
    theme_name = resolve_name(theme_name or meta.get("theme") or cfg.get("default_theme", "tech-blue"))
    scheme = scheme or meta.get("scheme") or cfg.get("default_scheme")
    theme = get_theme(theme_name, ws, scheme)

    # 标题：front matter 优先，否则取第一个 # 标题并从正文移除（微信标题单独显示）
    m = re.search(r"^#\s+(.+)$", text, re.M)
    if m and (not meta.get("title") or m.group(1).strip() == meta["title"]):
        meta["title"] = m.group(1).strip()
        text = text[:m.start()] + text[m.end():]

    digest_src = re.sub(r"^:::.*$|^\{\{.*\}\}\s*$", "", text, flags=re.M)
    if cfg.get("auto_footer") and "{{footer}}" not in raw:
        text = text.rstrip() + "\n\n{{footer}}\n"
    text, blocks = preprocess(text, cfg, theme, ws)

    body = md_to_html(text)
    for k, v in blocks.items():
        body = body.replace(f"<p>{k}</p>", v).replace(k, v)

    styled = apply_styles(body, theme, keep_links)
    styled = re.sub(r">\s*\n\s*<", "><", styled)          # 标签间换行在微信里会变成空行/空项目
    styled = re.sub(r"(?<=[\u4e00-\u9fff，。、：；！？])\n(?=[\u4e00-\u9fff])", "", styled)
    styled = styled.replace("\n", " ")
    article = f'<section style="{theme["wrapper"]}">{styled}</section>'

    plain = re.sub(r"<[^>]+>", "", styled)
    plain = re.sub(r"\s+", " ", html.unescape(plain)).strip()
    meta.setdefault("author", cfg.get("author", ""))
    dh = re.sub(r"<(h[1-6]|pre)[^>]*>.*?</\1>", " ", md_to_html(digest_src), flags=re.S)
    dh = re.sub(r"</(p|li|blockquote|td|th|tr)>", " ", dh)
    dplain = re.sub(r"<[^>]+>", "", dh)
    dplain = re.sub(r"\s+", " ", html.unescape(dplain)).strip()
    meta.setdefault("digest", dplain[:110])
    meta["theme"] = theme_name
    if theme.get("_scheme"):
        meta["scheme"] = theme["_scheme"]
    meta["word_count"] = len(re.sub(r"\s", "", plain))
    return article, meta


PREVIEW_TPL = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><base href="{base}"><title>{title} · 预览</title></head>
<body style="margin:0;background:#ededed;">
<div style="max-width:414px;margin:24px auto;background:#fff;padding:20px 16px 40px;box-shadow:0 2px 12px rgba(0,0,0,.08);">
<h1 style="font-size:22px;line-height:1.4;margin:0 0 10px;color:#111;font-family:-apple-system,'PingFang SC',sans-serif;">{title}</h1>
<p style="font-size:14px;color:#576b95;margin:0 0 24px;font-family:-apple-system,'PingFang SC',sans-serif;">{author}<span style="color:#999;margin-left:10px;">主题：{theme} · {words} 字</span></p>
{article}
</div></body></html>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("md", nargs="?")
    ap.add_argument("--theme")
    ap.add_argument("--workspace", help="工作区目录（默认 $WECHAT_MP_WORKSPACE 或自动向上查找）")
    ap.add_argument("--out")
    ap.add_argument("--scheme", help="主题配色档，如 书卷 的 朱砂/黛蓝/苍绿")
    ap.add_argument("--keep-links", action="store_true", help="保留外链（默认转为文末脚注）")
    ap.add_argument("--list-themes", action="store_true")
    a = ap.parse_args()
    a.workspace = find_workspace(a.workspace)

    if a.list_themes:
        for k, v in list_themes(a.workspace, detail=True).items():
            print(f"{k:16s} {v}")
        return
    if not a.md:
        ap.error("需要 markdown 文件路径")

    article, meta = convert(a.md, a.theme, a.workspace, a.keep_links, a.scheme)
    out = a.out or os.path.splitext(a.md)[0] + "_build"
    os.makedirs(out, exist_ok=True)
    meta["source_md"] = os.path.abspath(a.md)
    with open(os.path.join(out, "article.html"), "w", encoding="utf-8") as fh:
        fh.write(article)
    with open(os.path.join(out, "preview.html"), "w", encoding="utf-8") as fh:
        base = "file://" + os.path.dirname(os.path.abspath(a.md)) + "/"
        fh.write(PREVIEW_TPL.format(base=html.escape(base), title=html.escape(meta.get("title", "")),
                                    author=html.escape(meta.get("author", "")),
                                    theme=meta["theme"], words=meta["word_count"], article=article))
    with open(os.path.join(out, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    print(json.dumps({"out": out, **meta}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
