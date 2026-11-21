#!/usr/bin/env bash
# 安装 wechat-mp-studio skill：链接到 Claude Code 的 skills 目录，并安装 Python 依赖。
# 用法: ./install.sh [--copy] [--target ~/.claude/skills] [--workspace ~/wechat-mp-workspace]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/skills/wechat-mp-studio"
TARGET="$HOME/.claude/skills"
WORKSPACE=""
MODE="link"
while [ $# -gt 0 ]; do
  case "$1" in
    --copy) MODE="copy" ;;
    --target) TARGET="$2"; shift ;;
    --workspace) WORKSPACE="$2"; shift ;;
    *) echo "未知参数 $1"; exit 1 ;;
  esac
  shift
done
mkdir -p "$TARGET"
DEST="$TARGET/wechat-mp-studio"
if [ -e "$DEST" ] || [ -L "$DEST" ]; then
  echo "已存在：$DEST（如需重装请先手动移除）"
else
  if [ "$MODE" = "copy" ]; then cp -R "$SRC" "$DEST"; else ln -s "$SRC" "$DEST"; fi
  echo "已安装 skill → $DEST ($MODE)"
fi
python3 -m pip install -q -r "$HERE/requirements.txt" || python3 -m pip install -q --user -r "$HERE/requirements.txt" \
  || echo "⚠ 依赖安装失败，请手动执行: pip3 install -r requirements.txt"
if [ -n "$WORKSPACE" ]; then
  python3 "$SRC/scripts/init_workspace.py" "$WORKSPACE"
fi
echo "完成。新建工作区: python3 $SRC/scripts/init_workspace.py ~/wechat-mp-workspace"
