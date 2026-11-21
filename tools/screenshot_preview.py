#!/usr/bin/env python3
"""Regenerate docs/images/preview.png from examples/hello with the live preview server.

Usage: python3 tools/screenshot_preview.py
Requires: pip install playwright pillow && playwright install chromium
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "wechat-mp-studio", "scripts")
OUT = os.path.join(ROOT, "docs", "images", "preview.png")
PICKS = [{"theme": "friendly", "scheme": "松绿"}, {"theme": "bookish", "scheme": "朱砂"}, {"theme": "tech-blue", "scheme": ""}]
VIEWPORT = {"width": 1620, "height": 1000}

sys.path.insert(0, SCRIPTS)
from preview import set_front_matter  # noqa: E402


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_up(url, timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except OSError:
            time.sleep(0.2)
    sys.exit(f"preview server did not start: {url}")


def main():
    from playwright.sync_api import sync_playwright

    root_tmp = tempfile.mkdtemp()
    tmp = os.path.join(root_tmp, "2026-11-21-hello")
    os.makedirs(tmp)
    try:
        md = os.path.join(tmp, "article.md")
        shutil.copy(os.path.join(ROOT, "examples", "hello", "article.md"), md)
        subprocess.run([sys.executable, os.path.join(SCRIPTS, "cover.py"), "--title", "把写作和排版分开",
                        "--subtitle", "wechat-mp-studio", "--theme", "tech-blue",
                        "--out", os.path.join(tmp, "cover.jpg")], check=True, capture_output=True)
        set_front_matter(md, {"cover": "cover.jpg", "author": "wechat-mp-studio"})

        port = free_port()
        srv = subprocess.Popen([sys.executable, os.path.join(SCRIPTS, "preview.py"), md, "--port", str(port),
                                "--no-open"], cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            url = f"http://127.0.0.1:{port}/"
            wait_up(url)
            with sync_playwright() as p:
                b = p.chromium.launch()
                pg = b.new_page(viewport=VIEWPORT, device_scale_factor=1.5)
                pg.add_init_script(f"localStorage.setItem('wmp-picks', {json.dumps(json.dumps(PICKS))});"
                                   "localStorage.setItem('wmp-card', 'feed');")
                pg.goto(url)
                pg.wait_for_function(f"document.querySelectorAll('.art').length === {len(PICKS)} && "
                                     "[...document.querySelectorAll('.art')].every(a => a.children.length)")
                pg.wait_for_function("[...document.images].every(i => i.complete)")
                pg.wait_for_timeout(300)
                pg.screenshot(path=OUT)
                b.close()
        finally:
            srv.terminate()
    finally:
        shutil.rmtree(root_tmp, ignore_errors=True)

    try:
        from PIL import Image
        Image.open(OUT).convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT).save(OUT, optimize=True)
    except ImportError:
        pass
    print(f"wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
