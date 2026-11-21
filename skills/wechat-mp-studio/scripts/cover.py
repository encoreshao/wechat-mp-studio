#!/usr/bin/env python3
"""生成文字型封面图（无需 AI 绘图）。

用法:
  python3 cover.py --title "标题" [--subtitle "副标题/栏目名"] [--theme tech-blue]
                   [--bg 背景图.jpg] [--out cover.jpg] [--square]
默认 900x383（2.35:1 头图）；--square 同时生成 500x500 分享缩略图 <out>_square.jpg
依赖: pip install pillow
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from themes import BUILTIN, _hex_to_rgb  # noqa: E402

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:
    sys.exit("缺少依赖：pip install pillow")

FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/msyh.ttc",
]


def find_font(custom=None):
    for p in ([custom] if custom else []) + FONT_CANDIDATES:
        if p and os.path.isfile(p):
            return p
    sys.exit("未找到中文字体，请用 --font 指定 .ttf/.ttc 路径")


NO_LINE_START = "，。、：；！？）」』】》,.:;!?)"


def wrap(draw, text, font, max_w):
    """按宽度折行；支持 \\n 手动换行；标点不出现在行首。"""
    lines = []
    for para in text.replace("\\n", "\n").split("\n"):
        cur = ""
        for ch in para:
            if draw.textlength(cur + ch, font=font) <= max_w or not cur:
                cur += ch
            elif ch in NO_LINE_START and len(cur) > 1:
                lines.append(cur[:-1])
                cur = cur[-1] + ch
            else:
                lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
    return lines


def make(title, subtitle, primary, size, bg_path, font_path, out):
    W, H = size
    r, g, b = _hex_to_rgb(primary)
    if bg_path:
        img = Image.open(bg_path).convert("RGB")
        scale = max(W / img.width, H / img.height)
        img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1))
        l, t = (img.width - W) // 2, (img.height - H) // 2
        img = img.crop((l, t, l + W, t + H)).filter(ImageFilter.GaussianBlur(2))
        overlay = Image.new("RGB", (W, H), (r // 3, g // 3, b // 3))
        img = Image.blend(img, overlay, 0.55)
    else:
        img = Image.new("RGB", (W, H))
        px = img.load()
        dark = (int(r * 0.55), int(g * 0.55), int(b * 0.55))
        for x in range(W):
            for y in range(H):
                k = (x / W * 0.7 + y / H * 0.3)
                px[x, y] = tuple(int(c1 * (1 - k) + c2 * k) for c1, c2 in zip((r, g, b), dark))
    d = ImageDraw.Draw(img)
    # 装饰：右上圆、左下细线
    d.ellipse((W - H * 0.55, -H * 0.25, W + H * 0.25, H * 0.55), outline=(255, 255, 255), width=2)
    pad = int(W * 0.07)
    title_size = int(H * (0.16 if W > H else 0.10))
    font = ImageFont.truetype(font_path, title_size)
    lines = wrap(d, title, font, W - pad * 2)
    while len(lines) > 3 and title_size > 18:
        title_size -= 2
        font = ImageFont.truetype(font_path, title_size)
        lines = wrap(d, title, font, W - pad * 2)
    sub_font = ImageFont.truetype(font_path, int(title_size * 0.45))
    lh = int(title_size * 1.3)
    block_h = lh * len(lines) + (int(title_size * 1.2) if subtitle else 0)
    y = (H - block_h) // 2
    for ln in lines:
        d.text((pad, y), ln, font=font, fill=(255, 255, 255))
        y += lh
    if subtitle:
        y += int(title_size * 0.55)
        d.line((pad, y, pad + 40, y), fill=(255, 255, 255), width=3)
        d.text((pad + 52, y - int(title_size * 0.27)), subtitle, font=sub_font, fill=(235, 235, 235))
    img.save(out, "JPEG", quality=90)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True, help="可用 \\n 手动换行")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--theme", default="tech-blue")
    ap.add_argument("--color", help="覆盖主题主色，如 #1e6fff")
    ap.add_argument("--bg", help="可选背景图")
    ap.add_argument("--font")
    ap.add_argument("--out", default="cover.jpg")
    ap.add_argument("--square", action="store_true")
    a = ap.parse_args()
    primary = a.color or BUILTIN.get(a.theme, BUILTIN["tech-blue"])["primary"]
    fp = find_font(a.font)
    print(make(a.title, a.subtitle, primary, (900, 383), a.bg, fp, a.out))
    if a.square:
        sq = os.path.splitext(a.out)[0] + "_square.jpg"
        print(make(a.title, a.subtitle, primary, (500, 500), a.bg, fp, sq))


if __name__ == "__main__":
    main()
