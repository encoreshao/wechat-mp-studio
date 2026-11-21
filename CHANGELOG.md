# Changelog

## 0.1.1 — 2026-11-21

- 中文 README 设为默认（英文版改为 README.en.md）
- 新增 Claude Code 插件清单：`/plugin marketplace add encoreshao/wechat-mp-studio` 一键安装
- 新增 `package.sh`：打包上传到 Claude App 的 zip

## 0.1.0 — 2026-11-21

首个公开版本。

- 写作：7 套文章结构模版、写作风格档案、审校清单
- 排版：Markdown → 公众号内联样式 HTML；15 套主题（7 基础 + 8 风格 × 3 配色）
- 组件：提示框、导语、数据卡、金句卡、对比、步骤、清单、作者卡、页脚二维码
- 本地实时预览 `preview.py`：切换主题/配色、保存自动刷新、一键复制到公众号编辑器
- 主题画廊 `gallery.py`、文字封面 `cover.py`
- 发布 `publish.py`：图片自动上传压缩、草稿箱、freepublish、多账号
- 微信兼容：列表转段落、去除标签间换行、外链转脚注
