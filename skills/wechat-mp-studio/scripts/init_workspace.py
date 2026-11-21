#!/usr/bin/env python3
"""初始化公众号工作区（用户数据目录）。已存在的文件不会被覆盖。

用法: python3 init_workspace.py [目录，默认 ~/wechat-mp-workspace]
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ASSETS  # noqa: E402


def main():
    target = os.path.abspath(os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/wechat-mp-workspace"))
    src = os.path.join(ASSETS, "workspace")
    created = []
    for root, _dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        dst_dir = os.path.join(target, rel) if rel != "." else target
        os.makedirs(dst_dir, exist_ok=True)
        for f in files:
            dst = os.path.join(dst_dir, f)
            if not os.path.exists(dst):
                shutil.copy2(os.path.join(root, f), dst)
                created.append(os.path.relpath(dst, target))
    cfg = os.path.join(target, "config.json")
    if not os.path.exists(cfg):
        shutil.copy2(os.path.join(ASSETS, "config.example.json"), cfg)
        os.chmod(cfg, 0o600)
        created.append("config.json")
    print(f"工作区：{target}")
    for c in created:
        print(f"  + {c}")
    if not created:
        print("  （已是完整工作区，未改动）")
    print(f"\n下一步：编辑 {cfg} 填写公众号名称与 AppID/AppSecret，然后\n"
          f"  export WECHAT_MP_WORKSPACE={target}")


if __name__ == "__main__":
    main()
