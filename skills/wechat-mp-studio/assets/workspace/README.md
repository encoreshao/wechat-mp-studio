# 公众号工作区（wechat-mp-studio）

这是你的个人数据目录，skill 代码不在这里。

```
config.json            账号、作者、默认主题、页脚（含 AppSecret，已在 .gitignore 中）
articles/<日期-slug>/  每篇文章：article.md、图片、cover.jpg、构建产物
templates/structures/  自定义文章结构模版
templates/themes/      自定义主题 *.json（参考 my-brand.json.example）
templates/components/  自定义组件 *.html|*.md，正文用 {{名称}} 引用
style/profile.md       写作风格档案；style/samples/ 放样本文章
```

设置 `export WECHAT_MP_WORKSPACE=$(pwd)` 或在本目录内运行脚本即可自动识别。
