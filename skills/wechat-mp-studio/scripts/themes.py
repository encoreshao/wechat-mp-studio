"""排版主题。每个主题 = 主色 + 风格变体，生成每个标签的内联样式。
自定义主题：在 <workspace>/templates/themes/<name>.json 写
  {"label": "我的主题", "extends": "tech-blue", "primary": "#0a84ff",
   "font": "serif", "overrides": {"h2": "...css..."}}
"""
import json
import os

SANS = ("-apple-system,BlinkMacSystemFont,'Helvetica Neue','PingFang SC',"
        "'Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif")
SERIF = "'Songti SC','Noto Serif CJK SC','Source Han Serif SC',STSong,SimSun,serif"
MONO = "Menlo,Monaco,Consolas,'Courier New',monospace"


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def tint(h, a):
    """主色叠白底，a=主色占比(0-1)，返回实色（微信对 rgba 支持不稳定）。"""
    r, g, b = _hex_to_rgb(h)
    mix = lambda c: round(c * a + 255 * (1 - a))
    return "#%02x%02x%02x" % (mix(r), mix(g), mix(b))


def build(primary, h2_variant="bar", font="sans", text="#333333", code_dark=False):
    ff = SERIF if font == "serif" else SANS
    light = tint(primary, 0.08)
    mid = tint(primary, 0.35)
    h2 = {
        "bar": f"font-size:20px;font-weight:bold;color:{text};margin:36px 0 18px;padding-left:12px;"
               f"border-left:4px solid {primary};line-height:1.4;",
        "underline": f"font-size:20px;font-weight:bold;color:{text};margin:36px 0 18px;padding-bottom:8px;"
                     f"border-bottom:2px solid {primary};line-height:1.4;",
        "pill": f"display:table;font-size:18px;font-weight:bold;color:#fff;background:{primary};"
                f"margin:36px auto 18px;padding:6px 18px;border-radius:20px;line-height:1.4;",
        "center": f"font-size:20px;font-weight:bold;color:{primary};text-align:center;margin:40px 0 20px;"
                  f"line-height:1.4;letter-spacing:2px;",
        "block": f"font-size:18px;font-weight:bold;color:#fff;background:{primary};margin:36px 0 18px;"
                 f"padding:8px 14px;line-height:1.4;",
    }[h2_variant]
    pre_bg, pre_fg = ("#282c34", "#abb2bf") if code_dark else ("#f6f8fa", "#24292e")
    return {
        "_primary": primary,
        "_h2_variant": h2_variant,
        "wrapper": f"font-family:{ff};font-size:15px;color:{text};line-height:1.8;letter-spacing:0.5px;"
                   f"word-break:break-word;padding:0 4px;",
        "h1": f"font-size:24px;font-weight:bold;color:{text};text-align:center;margin:28px 0 24px;line-height:1.4;",
        "h2": h2,
        "h3": f"font-size:17px;font-weight:bold;color:{primary};margin:28px 0 14px;line-height:1.5;",
        "h4": f"font-size:16px;font-weight:bold;color:{text};margin:22px 0 12px;line-height:1.5;",
        "p": "margin:0 0 18px;text-align:justify;",
        "strong": f"font-weight:bold;color:{primary};",
        "em": "font-style:italic;",
        "del": "text-decoration:line-through;color:#999;",
        "a": f"color:{primary};text-decoration:none;border-bottom:1px solid {mid};",
        "sup": f"color:{primary};font-size:11px;",
        "blockquote": f"margin:20px 0;padding:12px 16px;background:{light};border-left:4px solid {mid};"
                      f"color:#555;font-size:14px;border-radius:2px;",
        "code": f"font-family:{MONO};font-size:13px;color:{primary};background:{light};padding:2px 5px;"
                f"border-radius:3px;margin:0 2px;",
        "pre": f"font-family:{MONO};font-size:12.5px;line-height:1.6;color:{pre_fg};background:{pre_bg};"
               f"padding:14px 16px;border-radius:6px;margin:20px 0;overflow-x:auto;white-space:nowrap;"
               f"letter-spacing:0;text-align:left;",
        "ul": "margin:0 0 18px;padding-left:22px;list-style-type:disc;",
        "ol": "margin:0 0 18px;padding-left:22px;list-style-type:decimal;",
        "li": "margin:6px 0;line-height:1.8;",
        "img": "display:block;max-width:100%;height:auto;margin:20px auto 8px;border-radius:4px;",
        "figcaption": "text-align:center;font-size:12px;color:#999;margin:0 0 20px;",
        "hr": f"border:none;border-top:1px solid {mid};margin:32px 0;",
        "table_wrap": "overflow-x:auto;margin:20px 0;",
        "table": "border-collapse:collapse;width:100%;font-size:13px;",
        "th": f"background:{light};color:{text};font-weight:bold;border:1px solid #e1e4e8;padding:8px 10px;text-align:left;",
        "td": "border:1px solid #e1e4e8;padding:8px 10px;",
        "refs_title": f"font-size:14px;font-weight:bold;color:{text};margin:32px 0 8px;",
        "refs_item": "font-size:12px;color:#888;margin:2px 0;word-break:break-all;line-height:1.6;",
        # 容器组件 :::tip / :::note / :::warning / :::quote
        "box_tip": ("#e8f7ee", "#07c160"),
        "box_note": (light, primary),
        "box_warning": ("#fff4e5", "#f57c00"),
        "box_danger": ("#fdecea", "#e5484d"),
        "box_quote": ("#fafafa", "#cccccc"),
    }


BUILTIN = {
    "tech-blue":      {"label": "科技蓝", "primary": "#1e6fff", "h2": "bar", "font": "sans", "code_dark": True},
    "minimal-black":  {"label": "极简黑", "primary": "#222222", "h2": "underline", "font": "sans", "code_dark": False},
    "warm-orange":    {"label": "暖橙", "primary": "#f0712c", "h2": "pill", "font": "sans", "code_dark": False},
    "elegant-purple": {"label": "优雅紫", "primary": "#7b4fd6", "h2": "center", "font": "sans", "code_dark": False},
    "fresh-green":    {"label": "清新绿", "primary": "#07a35a", "h2": "bar", "font": "sans", "code_dark": False},
    "business-navy":  {"label": "商务藏青", "primary": "#1f3a5f", "h2": "block", "font": "sans", "code_dark": True},
    "ink-red":        {"label": "墨韵红（衬线·人文）", "primary": "#b5342b", "h2": "center", "font": "serif", "code_dark": False},
}


def _presets():
    from presets import PRESETS
    return PRESETS


def resolve_name(name):
    """支持用中文名（如「书卷」「科技蓝」）指定主题。"""
    if name in BUILTIN or name in _presets():
        return name
    for k, v in BUILTIN.items():
        if v["label"].split("（")[0] == name:
            return k
    for k, v in _presets().items():
        if v["label"] == name:
            return k
    return name


def list_themes(workspace=None, detail=False):
    out = {k: v["label"] for k, v in BUILTIN.items()}
    for k, v in _presets().items():
        out[k] = (f"{v['label']}｜配色：{'、'.join(v['schemes'])}（默认 {v['default']}）"
                  + (f"\n{'':17s}{v['desc']}；适合 {v['fit']}；不适合 {v['avoid']}" if detail else ""))
    d = os.path.join(workspace or "", "templates", "themes")
    if workspace and os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".json"):
                with open(os.path.join(d, f), encoding="utf-8") as fh:
                    out[f[:-5]] = json.load(fh).get("label", f[:-5]) + "（自定义）"
    return out


def get_theme(name, workspace=None, scheme=None):
    name = resolve_name(name)
    custom = os.path.join(workspace or "", "templates", "themes", f"{name}.json")
    if workspace and os.path.isfile(custom):
        with open(custom, encoding="utf-8") as fh:
            spec = json.load(fh)
        if spec.get("extends") in _presets():
            from presets import build_preset
            sch = scheme or spec.get("scheme")
            t = build_preset(spec["extends"], sch, spec.get("overrides"))
            if spec.get("primary"):  # 自定义主色：替换整套派生色
                from presets import PRESETS, palette, fill
                p = PRESETS[spec["extends"]]
                pal = palette(spec["primary"], spec.get("secondary"), p.get("text", "#1F1F1F"), p.get("muted", "#8A8F98"))
                for k, v in {**p["styles"], **spec.get("overrides", {})}.items():
                    t[k] = fill(v, pal)
                t["_primary"] = pal["primary-ink"]
            return t
        base = dict(BUILTIN.get(spec.get("extends", "tech-blue"), BUILTIN["tech-blue"]))
        base.update({k: spec[k] for k in ("primary", "h2", "font", "code_dark") if k in spec})
        t = build(base["primary"], base["h2"], base["font"], spec.get("text", "#333333"), base["code_dark"])
        t.update(spec.get("overrides", {}))
        return t
    if name in _presets():
        from presets import build_preset
        return build_preset(name, scheme)
    if name not in BUILTIN:
        raise SystemExit(f"未知主题 {name}，可选：{', '.join(list_themes(workspace))}")
    b = BUILTIN[name]
    return build(b["primary"], b["h2"], b["font"], code_dark=b["code_dark"])
