#!/usr/bin/env bash
# 打包 skill，用于上传到 Claude App（claude.ai / 桌面版：Customize → Skills → Upload a skill）。
# 产物：dist/wechat-mp-studio.zip，zip 顶层是 wechat-mp-studio/ 文件夹。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HERE/dist"
OUT="$HERE/dist/wechat-mp-studio.zip"
rm -f "$OUT"
cd "$HERE/skills"
zip -qr "$OUT" wechat-mp-studio -x '*/__pycache__/*' '*.pyc' '*/.DS_Store'
echo "已生成 $OUT"
