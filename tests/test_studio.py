import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "wechat-mp-studio", "scripts")
EXAMPLE = os.path.join(ROOT, "examples", "hello", "article.md")
sys.path.insert(0, SCRIPTS)

from convert import convert  # noqa: E402
from presets import PRESETS, contrast, palette  # noqa: E402
from themes import BUILTIN  # noqa: E402

VARIANTS = [(t, None) for t in BUILTIN] + [(t, s) for t, p in PRESETS.items() for s in p["schemes"]]


@pytest.mark.parametrize("theme,scheme", VARIANTS)
def test_every_theme_renders_wechat_safe_html(theme, scheme):
    html, meta = convert(EXAMPLE, theme, None, False, scheme)
    assert meta["title"].startswith("示例")
    assert "\n" not in html, "标签间换行会在微信里变成空行"
    for bad in ("<ul", "<ol", "<li", "<style", "class=", "background-clip", ":::"):
        assert bad not in html, f"{theme}/{scheme} 含有 {bad}"
    assert "参考资料" in html  # 外链转脚注


def test_components_rendered():
    html, _ = convert(EXAMPLE, "friendly", None, False, "松绿")
    for text in ("15", "初始化工作区", "复制粘贴丢样式", "内容归你，样式归主题", "✓"):
        assert text in html


@pytest.mark.parametrize("name", list(PRESETS))
def test_palette_ink_is_readable(name):
    for primary, secondary in PRESETS[name]["schemes"].values():
        pal = palette(primary, secondary)
        assert contrast(pal["primary-ink"]) >= 4.5
        assert contrast(pal["primary-fill"]) >= 3.0


def test_front_matter_roundtrip(tmp_path):
    from preview import set_front_matter
    md = tmp_path / "a.md"
    md.write_text("---\ntitle: T\ntheme: tech-blue\n---\n\n正文\n", encoding="utf-8")
    set_front_matter(str(md), {"theme": "bookish", "scheme": "黛蓝"})
    text = md.read_text(encoding="utf-8")
    assert "theme: bookish" in text and "scheme: 黛蓝" in text and text.endswith("正文\n")
    set_front_matter(str(md), {"scheme": ""})
    assert "scheme" not in md.read_text(encoding="utf-8")


def test_init_workspace(tmp_path):
    ws = tmp_path / "ws"
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "init_workspace.py"), str(ws)], check=True,
                   capture_output=True)
    cfg = json.loads((ws / "config.json").read_text(encoding="utf-8"))
    assert "accounts" in cfg and (ws / "articles").is_dir() and (ws / "style" / "profile.md").is_file()


def test_ip_whitelist_hint(capsys):
    import publish
    with pytest.raises(SystemExit) as e:
        publish.check({"errcode": 40164, "errmsg": "invalid ip 1.2.3.4 ipv6 ::ffff:1.2.3.4, not in whitelist"})
    assert "1.2.3.4" in str(e.value)
