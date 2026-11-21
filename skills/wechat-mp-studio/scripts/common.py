"""工作区定位：skill 代码与用户数据（config.json、文章、自定义模版）分离。"""
import os

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(SKILL_DIR, "assets")


def _is_workspace(d):
    return os.path.isfile(os.path.join(d, "config.json")) and os.path.isdir(os.path.join(d, "articles"))


def find_workspace(explicit=None):
    """--workspace > $WECHAT_MP_WORKSPACE > $WECHAT_STUDIO(旧) > 当前目录及其上级中含 config.json + articles/ 的目录。"""
    for cand in (explicit, os.environ.get("WECHAT_MP_WORKSPACE"), os.environ.get("WECHAT_STUDIO")):
        if cand:
            return os.path.abspath(os.path.expanduser(cand))
    d = os.getcwd()
    while True:
        if _is_workspace(d):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent
