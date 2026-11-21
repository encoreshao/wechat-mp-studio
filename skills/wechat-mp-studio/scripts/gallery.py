#!/usr/bin/env python3
"""主题画廊：把一篇 markdown 用所有主题（及每套的全部配色）渲染进一个可切换的 HTML 页面。

用法:
  python3 gallery.py [article.md] [--workspace DIR] [--out gallery.html] [--themes a,b,c]
不传 md 时使用内置示例（含全部组件）。图片会内嵌为 data URI，页面可单独打开/分享。
"""
import argparse
import base64
import html
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import find_workspace  # noqa: E402
from convert import convert  # noqa: E402
from presets import PRESETS  # noqa: E402
from themes import BUILTIN, list_themes  # noqa: E402

SAMPLE = """---
title: 主题画廊示例
---

::: lead
这是一段**导语**：两三句话说清这篇讲什么、为什么值得读。
:::

## 二级标题：章节开始

正文段落包含**加粗强调**、*斜体强调*、`行内代码`，以及一个[外部链接](https://example.com)（会转成文末脚注）。手机上每段不超过四行最舒服。

### 三级标题：小节

> 引用块：别人说过的话，或需要读者停一下的句子。

- 无序列表第一项
- 第二项稍微长一点，看看折行之后缩进是否对齐到文字而不是符号
  - 嵌套的子项

1. 有序列表
2. 第二步

::: stat 核心数字
98% | 运行成功率
$0.36 | 平均每次成本
:::

::: quote-card 出处
人负责判断，AI 负责循环。
:::

::: compare 以前 / 现在
手动分拣 | 自动处理
邮件被淹没 | 自动起草回复
:::

::: steps 上手步骤
安装 | brew install xxx
自检 | xxx doctor
:::

::: checklist 发文前检查
done | 敏感词过一遍
todo | 封面在信息流尺寸下可读
warn | 外链会触发安全提示
:::

::: tip 小贴士
提示框组件：tip / note / warning / danger。
:::

| 方案 | 成本 | 速度 |
|---|---|---|
| A | 低 | 慢 |
| B | 高 | 快 |

```python
def hello():
    print("代码块")
```

---

结尾段落。
"""


def inline_images(h, base):
    def sub(m):
        src = m.group(2)
        if src.startswith(("data:", "http")):
            return m.group(0)
        p = src if os.path.isabs(src) else os.path.join(base, src)
        if not os.path.isfile(p):
            return m.group(0)
        mt = "png" if p.lower().endswith(".png") else "jpeg"
        with open(p, "rb") as fh:
            return f'{m.group(1)}data:image/{mt};base64,{base64.b64encode(fh.read()).decode()}{m.group(3)}'
    return re.sub(r'(<img[^>]*?\ssrc=")([^"]+)(")', sub, h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md", nargs="?")
    ap.add_argument("--workspace", help="工作区目录（默认 $WECHAT_MP_WORKSPACE 或自动向上查找）")
    ap.add_argument("--out", default="gallery.html")
    ap.add_argument("--themes", help="逗号分隔，只渲染这些主题")
    a = ap.parse_args()
    a.workspace = find_workspace(a.workspace)

    md = a.md
    if not md:
        md = os.path.join(tempfile.mkdtemp(), "sample.md")
        with open(md, "w", encoding="utf-8") as fh:
            fh.write(SAMPLE)
    base = os.path.dirname(os.path.abspath(md))
    names = a.themes.split(",") if a.themes else list(list_themes(a.workspace))

    variants = []  # (key, theme_label, scheme, html)
    title = ""
    for n in names:
        schemes = list(PRESETS[n]["schemes"]) if n in PRESETS else [None]
        for s in schemes:
            art, meta = convert(md, n, a.workspace, False, s)
            title = meta.get("title", "")
            label = PRESETS[n]["label"] if n in PRESETS else BUILTIN.get(n, {}).get("label", n)
            variants.append((f"{n}--{s or 'default'}", n, label, s, inline_images(art, base)))

    groups = {}
    for key, n, label, s, _ in variants:
        groups.setdefault((n, label), []).append((key, s))
    tabs = "".join(
        f'<button class="t" data-theme="{n}">{html.escape(label.split("（")[0])}</button>' for (n, label) in groups)
    scheme_bars = "".join(
        f'<div class="sb" data-theme="{n}">' + "".join(
            f'<button class="s" data-k="{k}">{html.escape(s or "默认")}</button>' for k, s in lst) + "</div>"
        for (n, _), lst in groups.items())
    panes = "".join(f'<div class="pane" id="{k}">{h}</div>' for k, _, _, _, h in variants)
    descs = {n: (PRESETS[n]["desc"] + "｜适合：" + PRESETS[n]["fit"]) if n in PRESETS else "" for (n, _) in groups}
    import json
    page = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>主题画廊 · {html.escape(title)}</title>
<style>
body{{margin:0;background:#ececef;font-family:-apple-system,'PingFang SC',sans-serif}}
.bar{{position:sticky;top:0;z-index:5;background:rgba(255,255,255,.95);border-bottom:1px solid #ddd;padding:10px 12px 6px;text-align:center}}
.t,.s{{border:1px solid #ccc;background:#fff;border-radius:16px;padding:5px 12px;margin:3px;font-size:13px;cursor:pointer}}
.t.on{{background:#111;color:#fff;border-color:#111}} .s.on{{background:#576b95;color:#fff;border-color:#576b95}}
.sb{{display:none;margin-top:4px}} .sb.on{{display:block}}
.desc{{font-size:12px;color:#777;margin:6px 0 2px;min-height:16px}}
.phone{{width:390px;margin:20px auto 60px;background:#fff;border-radius:24px;border:10px solid #1c1c1e;padding:20px 16px 40px}}
.phone h1.ti{{font-size:22px;line-height:1.4;margin:0 0 20px;color:#111}}
.pane{{display:none}} .pane.on{{display:block}}
</style></head><body>
<div class="bar"><div>{tabs}</div>{scheme_bars}<div class="desc" id="desc"></div></div>
<div class="phone"><h1 class="ti">{html.escape(title)}</h1>{panes}</div>
<script>
const D={json.dumps(descs, ensure_ascii=False)};
function showTheme(n){{document.querySelectorAll('.t').forEach(b=>b.classList.toggle('on',b.dataset.theme===n));
document.querySelectorAll('.sb').forEach(b=>b.classList.toggle('on',b.dataset.theme===n));
document.getElementById('desc').textContent=D[n]||'';
const first=document.querySelector('.sb[data-theme="'+n+'"] .s');showVar(first.dataset.k);}}
function showVar(k){{document.querySelectorAll('.s').forEach(b=>b.classList.toggle('on',b.dataset.k===k));
document.querySelectorAll('.pane').forEach(p=>p.classList.toggle('on',p.id===k));}}
document.querySelectorAll('.t').forEach(b=>b.onclick=()=>showTheme(b.dataset.theme));
document.querySelectorAll('.s').forEach(b=>b.onclick=()=>showVar(b.dataset.k));
showTheme(document.querySelector('.t').dataset.theme);
</script></body></html>"""
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"{a.out}  （{len(groups)} 套主题，{len(variants)} 个配色变体）")


if __name__ == "__main__":
    main()
