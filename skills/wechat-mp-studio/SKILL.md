---
name: wechat-mp-studio
description: 微信公众号文章的创作、排版与发布：选题→按结构模版写作→审校→选主题排版（15 套主题、本地实时预览）→封面→推送草稿箱/发布。用户提到公众号、微信文章、公众号排版、推草稿箱、发公众号时使用。
---

# wechat-mp-studio

流程：**选题 → 大纲 → 写作 → 审校 → 排版与本地预览 → 封面 → 草稿箱 →（可选）发布**。
每个阶段结束停下来让用户确认；用户可直接跳到任一阶段（如"把这篇 md 推到草稿箱"）。

## 0. 环境

- **SKILL_DIR**：本文件所在目录，脚本在 `SKILL_DIR/scripts/`。若只有 SKILL.md 没有 scripts/，在用户电脑上找 `wechat-mp-studio` 仓库，找不到就让用户 `git clone https://github.com/encoreshao/wechat-mp-studio`。
- **工作区**（用户数据，与 skill 代码分离）：含 `config.json` + `articles/` 的目录。按顺序确定：`$WECHAT_MP_WORKSPACE` → 当前目录向上查找 → 询问用户。没有就创建：`python3 SKILL_DIR/scripts/init_workspace.py <目录>`。
- **所有命令都在用户电脑上运行**（本地生成、本地预览）；发布必须在用户电脑上，因为微信校验 IP 白名单。
- 依赖：`pip3 install markdown beautifulsoup4 pillow`。
- 下文 `$S` = `SKILL_DIR/scripts`，命令在工作区目录内执行（或设 `WECHAT_MP_WORKSPACE`）。

## 1. 选题与大纲

- 只有方向时给 3-5 个选题卡（标题 / 读者 / 核心观点 / 推荐结构）；需要时先联网查资料。
- 让用户选结构模版：`SKILL_DIR/assets/structures/` + 工作区 `templates/structures/`。
- 产出大纲（各节要点 + 计划配图）→ **等用户确认**。

## 2. 写作

写到工作区 `articles/<YYYY-MM-DD-slug>/article.md`。先读工作区 `style/profile.md`（如已生成则严格遵循）。
文件头字段、写作规范、标题公式见 `references/writing.md`；可用组件（提示框、数据卡、金句卡、对比、步骤、清单、作者卡、页脚）见 `references/components.md`。

## 3. 审校

写完自动按 `references/writing.md` 的审校清单检查，把问题和建议列给用户；代写的第一人称经历、资料冲突要特别标出。用户确认后再排版。

## 4. 排版与本地预览

```bash
python3 $S/convert.py --list-themes                                  # 15 套主题及适用场景
python3 $S/preview.py articles/<dir>/article.md [--theme X --scheme Y]  # 本地实时预览（推荐）
python3 $S/convert.py articles/<dir>/article.md --theme X [--scheme Y]  # 生成 article_build/
python3 $S/gallery.py [article.md] --out gallery.html                 # 全部主题对比页
```
- 按文章类型推荐 2-3 套主题（见 `references/themes.md`），让用户在 `preview.py` 打开的浏览器页里切换主题/配色；页面会随 article.md 保存自动刷新，「保存为本文主题」写回 front matter，「复制到公众号」可直接粘贴进公众号编辑器。
- `preview.py` 是常驻进程：让用户在自己的终端运行（或用后台方式启动并告诉用户地址），Claude 继续改 article.md，用户浏览器会自动刷新。
- 产物 `article_build/`：`article.html`（发布用）、`preview.html`（静态预览，可直接双击打开）、`meta.json`。
- 用户要品牌色/新风格 → 在工作区 `templates/themes/` 建 JSON（格式见 `references/themes.md`）。改样式前读 `references/wechat-html.md`。

## 5. 封面

用户有图就用（900×383，2.35:1）。否则：
```bash
python3 $S/cover.py --title '主标题\n副标题' --subtitle "栏目" --theme X --out articles/<dir>/cover.jpg
```
给用户看过再继续。

## 6. 发布

细节、前置条件、错误码见 `references/publishing.md`。
```bash
python3 $S/publish.py check
python3 $S/publish.py draft articles/<dir>/article_build --cover articles/<dir>/cover.jpg [--comment]
```
- 默认只推草稿箱，告诉用户 media_id，并提醒删除旧版本草稿、在后台预览后群发。
- `publish <media_id> --yes` 直接发布前**必须明确征得用户同意**，并说明不会推送给粉丝、不可撤回。
- 不让用户把 AppSecret 贴进对话；不在对话中输出 config.json。

## 收尾

告诉用户：文章目录、结构模版/主题/配色、预览方式、草稿 media_id 或发布链接。
