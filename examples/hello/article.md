---
title: 示例：用 wechat-mp-studio 写一篇公众号
digest: 演示结构、组件和主题效果的示例文章。
theme: friendly
scheme: 松绿
---

::: lead
这是一篇示例文章，用来演示 **wechat-mp-studio** 的排版效果。用 `preview.py` 打开它，在浏览器里切换主题看看。
:::

## 为什么要把写作和排版分开

公众号编辑器对 Markdown 不友好，复制粘贴经常丢样式。把内容写成 Markdown，样式交给主题，换风格只需要换一个参数。

::: stat 一个示例数字块
15 | 套主题
31 | 种配色组合
:::

## 三步上手

::: steps
初始化工作区 | init_workspace.py ~/wechat-mp-workspace
本地预览 | preview.py articles/x/article.md
推送草稿箱 | publish.py draft articles/x/article_build
:::

::: compare 以前 / 现在
复制粘贴丢样式 | 内联样式一次成型
外链点不开 | 自动转成文末脚注
:::

> 引用块：别人说过的话放这里。

- 列表项会被转成带主题色符号的段落
- 第二项稍长一些，用来观察折行后的缩进是否对齐到文字
  - 嵌套子项

::: quote-card wechat-mp-studio
内容归你，样式归主题。
:::

::: checklist 发文前检查
done | 跑一遍审校
todo | 手机上预览封面
warn | 外链会变成脚注
:::

了解更多可以看 [项目主页](https://github.com/encoreshao/wechat-mp-studio)。
