"""风格化主题预设（每套含多档配色）。

8 套风格的版式与配色改编自 aiworkskills/wechat-article-skills
(https://github.com/aiworkskills/wechat-article-skills, Apache-2.0)，
已按微信编辑器的兼容性调整：去掉 background-clip:text 渐变字（微信会剥掉导致文字不可见）、
补齐依赖骨架装饰的 h2 样式、列表改由 convert.py 统一渲染。

样式字符串里的 {变量} 由 palette() 从主色/次色派生：
  primary-color 原色（装饰面积） primary-fill 压白字的实心块 primary-ink 白底上的文字色
  bg-accent-soft / bg-accent-color 两档浅底  highlight-pen / highlight-soft 两档高亮笔
  secondary-color 次色  text-color 正文色  text-muted 辅助文字色
"""

SANS = ("-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',"
        "'Helvetica Neue',Arial,sans-serif")
SERIF_W = "Baskerville,Georgia,'Times New Roman','Songti SC','Noto Serif CJK SC',serif"
MONO = "Menlo,Consolas,'SF Mono',monospace"


# ---------- 颜色工具（保证可读性） ----------
def _rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(c))) for c in rgb)


def _lum(h):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b="#FFFFFF"):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def darken_to(h, target=4.5):
    rgb = _rgb(h)
    for _ in range(40):
        if contrast(_hex(rgb)) >= target:
            break
        rgb = tuple(c * 0.94 for c in rgb)
    return _hex(rgb)


def mix_white(h, ratio):
    return _hex(tuple(c + (255 - c) * ratio for c in _rgb(h)))


def palette(primary, secondary=None, text="#1F1F1F", muted="#8A8F98"):
    fill = primary if contrast(primary) >= 3.0 else darken_to(primary, 3.0)
    return {
        "primary-color": primary,
        "primary-fill": fill,
        "primary-ink": darken_to(primary),
        "bg-accent-soft": mix_white(primary, 0.96),
        "bg-accent-color": mix_white(primary, 0.92),
        "highlight-pen": mix_white(primary, 0.74),
        "highlight-soft": mix_white(primary, 0.84),
        "secondary-color": secondary or primary,
        "secondary-ink": darken_to(secondary or primary),
        "secondary-soft": mix_white(secondary or primary, 0.88),
        "text-color": text,
        "text-muted": muted,
    }


# ---------- 预设 ----------
# 每套: label, desc, fit, avoid, text, muted, schemes(名称→(主色, 次色)), default, code_dark, styles
PRESETS = {
    "friendly": {
        "label": "亲和", "desc": "圆润友好：实心胶囊标题、灰底圆角引用、高亮笔加粗",
        "fit": "教程、职场、面向新手的解释性长文", "avoid": "严肃议题、财报解读",
        "schemes": {"黛紫": ("#6B5B95", None), "松绿": ("#4E7D6B", None), "靛蓝": ("#3F5F9E", None)},
        "default": "黛紫", "code_dark": False,
        "styles": {
            "wrapper": f"font-family:{SANS};font-size:16px;color:{{text-color}};line-height:1.95;letter-spacing:0.5px;word-break:break-word;",
            "p": "margin:0 0 24px;",
            "strong": "color:{text-color};font-weight:700;background:linear-gradient(transparent 70%,{highlight-soft} 70%);",
            "em": "font-style:normal;color:{primary-ink};font-weight:600;",
            "a": "color:{primary-ink};text-decoration:none;font-weight:500;",
            "h1": "font-size:24px;font-weight:800;color:{text-color};line-height:1.4;margin:0 0 28px;",
            "h2": "font-size:18px;font-weight:700;color:#FFFFFF;line-height:1.5;text-align:center;margin:48px auto 24px;padding:10px 22px;background:{primary-fill};border-radius:999px;display:table;",
            "h3": "font-size:16px;font-weight:700;color:{primary-ink};line-height:1.6;margin:32px 0 12px;padding:4px 14px;background:{bg-accent-color};border-radius:999px;display:inline-block;",
            "blockquote": "color:{text-color};font-size:15px;line-height:1.85;padding:16px 18px;margin:0 0 26px;background:#F5F6F8;border-left:5px solid {highlight-pen};border-radius:0 16px 16px 0;",
            "img": "display:block;width:100%;height:auto;border-radius:16px;margin:20px auto 8px;",
            "code": f"font-family:{MONO};font-size:13.5px;background:#F2F3F5;color:{{text-color}};padding:1px 6px;border-radius:6px;",
            "th": "color:#FFFFFF;font-size:13px;font-weight:700;padding:10px 12px;background:{primary-fill};text-align:left;",
            "td": "color:{text-color};padding:11px 12px;border-bottom:1px solid #EEF0F2;",
            "hr": "border:none;height:6px;width:48px;background:{highlight-pen};border-radius:3px;margin:48px auto;",
        },
    },
    "notebook": {
        "label": "手账", "desc": "手作笔记：荧光笔加粗、虚线引用、笔记本质感",
        "fit": "个人笔记、复盘、学习记录、第一人称", "avoid": "官方公告、白皮书",
        "text": "#2A2622", "muted": "#8A7F76",
        "schemes": {"朱红·黄笔": ("#C8553D", "#FFE066"), "墨蓝·粉笔": ("#2C4A7A", "#FFC2D9"),
                    "深绿·薄荷笔": ("#2F6B4F", "#C6F0C2")},
        "default": "朱红·黄笔", "code_dark": False,
        "styles": {
            "wrapper": f"font-family:{SANS};font-size:16px;color:{{text-color}};line-height:2.0;letter-spacing:0.4px;word-break:break-word;",
            "p": "margin:0 0 24px;",
            "strong": "color:{text-color};font-weight:700;background:linear-gradient(transparent 65%,{secondary-color} 65%);",
            "em": "font-style:normal;color:{primary-ink};font-weight:700;",
            "a": "color:{primary-ink};text-decoration:none;border-bottom:2px dotted {primary-ink};",
            "h1": "font-size:25px;font-weight:800;color:{text-color};line-height:1.4;margin:0 0 28px;",
            "h2": "font-size:20px;font-weight:800;color:{text-color};line-height:1.4;margin:44px 0 20px;padding:0 4px 6px;display:inline-block;background:linear-gradient(transparent 62%,{secondary-color} 62%);",
            "h3": "font-size:17px;font-weight:800;color:{primary-ink};margin:32px 0 12px;",
            "blockquote": "color:#5A524B;font-size:15.5px;line-height:1.9;padding:2px 0 2px 18px;margin:0 0 26px;border-left:3px dotted {primary-ink};",
            "img": "display:block;width:100%;height:auto;border-radius:4px;margin:20px auto 8px;box-shadow:0 2px 0 #E9E2D6;",
            "figcaption": "font-size:13px;color:{text-muted};margin:8px 0 28px;text-align:center;",
            "th": "color:{text-color};font-size:13px;font-weight:800;text-align:left;padding:10px 8px;border-bottom:2px dotted {primary-ink};",
            "td": "color:{text-color};padding:10px 8px;border-bottom:1px dotted #D9D2C8;",
            "hr": "border:none;border-top:2px dashed #D9D2C8;margin:44px 0;",
        },
    },
    "bookish": {
        "label": "书卷", "desc": "纸书感：衬线正文、标题居中、表格书线、慢阅读",
        "fit": "人文、读书、历史、深度长文", "avoid": "工程文档、数据密集评测",
        "text": "#1F1F1F", "muted": "#8A8F98",
        "schemes": {"朱砂": ("#9E3D30", None), "黛蓝": ("#2F4A6D", None), "苍绿": ("#3F5E4A", None)},
        "default": "朱砂", "code_dark": False,
        "styles": {
            "wrapper": f"font-family:{SERIF_W};font-size:15.5px;color:#222222;line-height:1.95;letter-spacing:0.3px;word-break:break-word;",
            "p": "margin:0 0 20px;",
            "strong": "color:{primary-ink};font-weight:900;",
            "em": "font-style:normal;color:{primary-ink};",
            "a": "color:{text-color};text-decoration:none;border-bottom:1px solid #B9BEC4;",
            "h1": "font-size:24px;font-weight:700;color:#111111;line-height:1.5;text-align:center;margin:0 0 28px;",
            "h2": "font-size:20px;font-weight:700;color:#111111;line-height:1.55;letter-spacing:1px;text-align:center;margin:48px 0 22px;padding-top:16px;border-top:3px solid {primary-color};display:table;margin-left:auto;margin-right:auto;",
            "h3": "font-size:16px;font-weight:700;color:{primary-ink};letter-spacing:1.5px;text-align:center;margin:32px 0 12px;",
            "blockquote": "color:#555555;font-size:15.5px;line-height:1.95;padding:0 22px;margin:8px 0 24px;text-align:center;",
            "figcaption": "text-align:center;font-size:12.5px;letter-spacing:1px;color:{text-muted};margin:10px 0 28px;",
            "img": "display:block;width:100%;height:auto;margin:20px auto 8px;padding:8px 0;border-top:1px solid #D9DDE1;border-bottom:1px solid #D9DDE1;",
            "th": "color:#111111;font-size:13px;font-weight:700;text-align:left;padding:8px;border-top:2px solid #111111;border-bottom:1px solid #111111;",
            "td": "color:#222222;padding:9px 8px;border-bottom:1px solid #E6E8EB;",
            "hr": "border:none;height:1px;background:#D9DDE1;margin:44px 0;",
        },
    },
    "magazine": {
        "label": "杂志", "desc": "编辑部气质：窄栏松行距、细线引用、大写小字图注",
        "fit": "品牌故事、人物访谈、生活方式、图多的稿子", "avoid": "纯文字信息型短文",
        "text": "#1F1F1F", "muted": "#8A8A8A",
        "schemes": {"石青": ("#4A5D6E", None), "驼褐": ("#8A6A4B", None), "铁锈": ("#9C4F3B", None)},
        "default": "石青", "code_dark": False,
        "styles": {
            "wrapper": f"font-family:{SANS};font-size:15px;color:#2A2A2A;line-height:2.0;letter-spacing:0.4px;padding:0 10px;word-break:break-word;",
            "p": "margin:0 0 24px;",
            "strong": "color:{primary-ink};font-weight:600;",
            "em": "font-style:normal;color:{primary-ink};",
            "a": "color:{text-color};text-decoration:none;border-bottom:1px solid #C9CED3;",
            "h1": "font-size:24px;font-weight:600;letter-spacing:1px;color:{text-color};line-height:1.5;margin:0 0 24px;",
            "h2": "font-size:19px;font-weight:600;letter-spacing:1px;color:{text-color};line-height:1.55;margin:52px 0 20px;padding-top:14px;border-top:1px solid {text-color};",
            "h3": "font-size:15px;font-weight:600;letter-spacing:2.5px;color:{primary-ink};margin:34px 0 12px;",
            "blockquote": "color:#555555;font-size:15px;line-height:2.0;letter-spacing:0.3px;padding:0 0 0 16px;margin:8px 0 28px;border-left:1px solid #C9CED3;",
            "figcaption": "font-size:11px;letter-spacing:2px;color:{text-muted};margin:12px 0 36px;text-transform:uppercase;",
            "img": "display:block;width:100%;height:auto;margin:24px auto 8px;",
            "th": "padding:10px 8px;text-align:left;font-weight:600;letter-spacing:2px;font-size:11px;color:{text-muted};border-bottom:1px solid #C9CED3;",
            "td": "padding:10px 8px;color:#2A2A2A;line-height:1.7;border-bottom:1px solid #EEF0F2;",
            "hr": "border:none;height:1px;background:#D9DDE1;margin:52px 0;",
        },
    },
    "news": {
        "label": "资讯", "desc": "媒体号语法：17px 大字、松字距、彩色粗体、只用发丝线",
        "fit": "快讯、评测、行业观察", "avoid": "抒情散文、碎片短文",
        "text": "#111111", "muted": "#8A8F98",
        "schemes": {"墨绿": ("#1F6F5F", None), "绛红": ("#9B2D30", None), "藏青": ("#24406B", None)},
        "default": "墨绿", "code_dark": True,
        "styles": {
            "wrapper": f"font-family:{SANS};font-size:17px;color:{{text-color}};line-height:2.0;letter-spacing:0.8px;word-break:break-word;",
            "p": "margin:0 0 28px;",
            "strong": "color:{primary-ink};font-weight:700;",
            "em": "font-style:normal;font-weight:700;color:{text-color};",
            "a": "color:{primary-ink};text-decoration:none;border-bottom:1px solid {primary-ink};",
            "h1": "font-size:26px;font-weight:800;color:{text-color};line-height:1.4;margin:0 0 28px;",
            "h2": "font-size:21px;font-weight:800;color:{text-color};line-height:1.5;letter-spacing:0.8px;margin:56px 0 24px;padding-bottom:14px;border-bottom:1px solid #E3E6EA;",
            "h3": "font-size:18px;font-weight:800;color:{text-color};line-height:1.6;margin:36px 0 14px;",
            "blockquote": "color:#555555;font-size:16px;line-height:1.95;letter-spacing:0.6px;padding:18px 20px;margin:0 0 28px;background:#F4F5F7;border-radius:12px;",
            "code": f"font-family:{MONO};font-size:14px;background:#F4F5F7;color:{{text-color}};padding:1px 6px;border-radius:4px;",
            "th": "color:{text-muted};font-size:13px;font-weight:700;letter-spacing:1px;text-align:left;padding:10px 8px;border-bottom:1px solid #C9CED3;",
            "td": "color:{text-color};padding:11px 8px;border-bottom:1px solid #E3E6EA;",
            "hr": "border:none;height:1px;background:#E3E6EA;margin:48px 0;",
        },
    },
    "docs": {
        "label": "文档", "desc": "开发者文档感：发丝线、等宽小标签、冷静的单一强调色（类 Stripe/Linear 博客）",
        "fit": "工程实践、技术文档、代码讲解", "avoid": "情绪向、故事向内容",
        "text": "#111827", "muted": "#6B7280",
        "schemes": {"蓝": ("#2563EB", None), "紫": ("#7C3AED", None), "绿": ("#047857", None)},
        "default": "蓝", "code_dark": True,
        "styles": {
            "wrapper": f"font-family:{SANS};font-size:16px;color:{{text-color}};line-height:1.95;letter-spacing:0.2px;word-break:break-word;",
            "p": "margin:0 0 24px;",
            "strong": "color:{primary-ink};font-weight:800;",
            "em": "font-style:normal;color:{primary-ink};font-weight:600;",
            "a": "color:{primary-ink};text-decoration:none;border-bottom:1px solid {primary-ink};",
            "h1": "font-size:25px;font-weight:700;color:{text-color};line-height:1.4;margin:0 0 28px;",
            "h2": "font-size:20px;font-weight:700;color:{text-color};line-height:1.5;margin:48px 0 20px;padding-top:12px;border-top:1px solid #E5E7EB;",
            "h3": "font-size:16px;font-weight:700;color:{text-color};margin:32px 0 12px;",
            "blockquote": "color:{text-muted};font-size:15.5px;line-height:1.9;padding:2px 0 2px 18px;margin:0 0 26px;border-left:2px solid {primary-ink};",
            "figcaption": f"font-family:{MONO};font-size:11px;letter-spacing:1.5px;color:{{text-muted}};margin:10px 0 30px;text-align:center;",
            "img": "display:block;width:100%;height:auto;border:1px solid #E5E7EB;border-radius:6px;margin:20px auto 8px;",
            "code": f"font-family:{MONO};font-size:13.5px;background:#F6F8FA;color:{{text-color}};padding:1px 6px;border-radius:4px;",
            "th": f"font-family:{MONO};font-size:11px;letter-spacing:1.5px;color:{{text-muted}};font-weight:600;text-align:left;padding:10px 8px;border-bottom:1px solid {{text-color}};",
            "td": "color:{text-color};padding:10px 8px;border-bottom:1px solid #E5E7EB;",
            "hr": "border:none;height:1px;background:#E5E7EB;margin:48px 0;",
        },
    },
    "vivid": {
        "label": "活力", "desc": "外向醒目：渐变色条标题、渐变淡底引用、双色强调",
        "fit": "产品发布、增长复盘、面向年轻读者", "avoid": "严肃议题、超长深度稿",
        "text": "#1F1F1F", "muted": "#8A8F98",
        "schemes": {"靛青": ("#5B4BFF", "#17A398"), "玫紫": ("#B83280", "#6B46C1"), "暮橙": ("#D9480F", "#A61E4D")},
        "default": "靛青", "code_dark": True,
        "styles": {
            "wrapper": f"font-family:{SANS};font-size:16px;color:{{text-color}};line-height:1.95;letter-spacing:0.4px;word-break:break-word;",
            "p": "margin:0 0 24px;",
            "strong": "color:{primary-ink};font-weight:800;",
            "em": "font-style:normal;color:{secondary-ink};font-weight:700;",
            "a": "color:{primary-ink};text-decoration:none;border-bottom:2px solid {secondary-color};",
            "h1": "font-size:25px;font-weight:800;color:{text-color};line-height:1.4;margin:0 0 28px;",
            "h2": "font-size:20px;font-weight:900;color:#FFFFFF;line-height:1.4;margin:48px 0 22px;padding:10px 16px;border-radius:8px;background:linear-gradient(90deg,{primary-fill},{secondary-color});",
            "h3": "font-size:17px;font-weight:800;color:{primary-ink};margin:32px 0 12px;",
            "blockquote": "color:#3A3F47;font-size:15.5px;line-height:1.85;padding:14px 18px;margin:0 0 26px;background:linear-gradient(90deg,{bg-accent-color},{secondary-soft});border-left:4px solid {secondary-color};border-radius:0 10px 10px 0;",
            "img": "display:block;width:100%;height:auto;border-radius:10px;margin:20px auto 8px;",
            "th": "color:#FFFFFF;font-size:13px;font-weight:700;padding:10px 8px;background:{primary-fill};text-align:left;",
            "td": "color:{text-color};padding:10px 8px;border-bottom:1px solid #E6E8EB;",
            "hr": "border:none;height:3px;background:linear-gradient(90deg,{primary-color},{secondary-color},#FFFFFF);margin:48px 0;",
        },
    },
    "bauhaus": {
        "label": "硬朗", "desc": "包豪斯：粗黑线、色块编号感标题、三色几何、主张鲜明",
        "fit": "观点、宣言、立场鲜明的内容", "avoid": "温和科普、需要亲和力的品牌内容",
        "text": "#111111", "muted": "#6B7078",
        "schemes": {"蓝黄": ("#1F4FD6", "#F2C230"), "赤黑": ("#C0392B", "#1A1A1A"), "绿橙": ("#2A9D8F", "#E76F51")},
        "default": "蓝黄", "code_dark": True,
        "styles": {
            "wrapper": f"font-family:{SANS};font-size:16px;color:#111111;line-height:1.95;letter-spacing:0.4px;word-break:break-word;",
            "p": "margin:0 0 24px;",
            "strong": "color:#111111;font-weight:900;border-bottom:3px solid {primary-fill};",
            "em": "font-style:normal;color:{primary-ink};font-weight:700;",
            "a": "color:{primary-ink};text-decoration:none;font-weight:700;",
            "h1": "font-size:26px;font-weight:900;color:#111111;line-height:1.35;margin:0 0 28px;",
            "h2": "font-size:21px;font-weight:900;color:#111111;line-height:1.35;margin:48px 0 20px;padding:6px 0 6px 14px;border-left:14px solid {primary-fill};box-shadow:inset 0 -6px 0 {secondary-color};display:inline-block;",
            "h3": "font-size:17px;font-weight:800;color:#111111;margin:32px 0 12px;padding-left:12px;border-left:8px solid {secondary-color};",
            "blockquote": "color:#111111;font-size:16px;line-height:1.85;padding:12px 0 12px 18px;margin:0 0 26px;border-left:8px solid #111111;",
            "figcaption": "font-size:11px;letter-spacing:2px;color:{text-muted};margin:8px 0 28px;text-align:center;",
            "img": "display:block;width:100%;height:auto;border:3px solid #111111;margin:20px auto 8px;",
            "th": "color:#111111;font-size:12px;letter-spacing:1.5px;font-weight:700;text-align:left;padding:10px 8px;border-top:6px solid #111111;border-bottom:1px solid #111111;",
            "td": "color:#111111;padding:10px 8px;border-bottom:1px solid #E3E6EA;",
            "hr": "border:none;height:6px;background:#111111;margin:48px 0;",
        },
    },
}


def fill(s, pal):
    for k, v in pal.items():
        s = s.replace("{" + k + "}", v)
    return s


def build_preset(name, scheme=None, overrides=None):
    """返回与 themes.build() 同结构的样式字典。"""
    from themes import build  # 复用默认键（pre、提示框、参考资料等）
    spec = PRESETS[name]
    scheme = scheme or spec["default"]
    if scheme not in spec["schemes"]:
        raise SystemExit(f"主题 {name} 没有配色「{scheme}」，可选：{'、'.join(spec['schemes'])}")
    primary, secondary = spec["schemes"][scheme]
    pal = palette(primary, secondary, spec.get("text", "#1F1F1F"), spec.get("muted", "#8A8F98"))
    t = build(pal["primary-ink"], "bar", "sans", pal["text-color"], spec.get("code_dark", False))
    for k, v in spec["styles"].items():
        t[k] = fill(v, pal)
    for k, v in (overrides or {}).items():
        t[k] = fill(v, pal)
    t["_primary"] = pal["primary-ink"]
    t["_palette"] = pal
    t["_scheme"] = scheme
    t["box_note"] = (pal["bg-accent-color"], pal["primary-fill"])
    return t
