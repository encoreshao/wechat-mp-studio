# 正文组件

所有组件都是 Markdown 里的 `:::` 块或 `{{名称}}` 占位，转换时生成纯内联样式 HTML。

## 提示框
```
::: tip 标题        （tip / note / warning / danger / quote，标题可省略）
内容，支持 **Markdown**
:::
```

## 信息图（每篇 1-3 个，别堆砌）

| 语法 | 用途 | 规则 |
|---|---|---|
| `::: lead` | 开篇导语 | 只放开头，≤4 行；不要写成"本文将从三方面…" |
| `::: stat 标题` 每行 `数字 \| 说明` | 核心数字 | 2-4 行；第一列只放数字+短单位；只放核实过的数字 |
| `::: quote-card 出处` | 金句卡 | 全篇最多 1 张，≤40 字，脱离上下文仍成立 |
| `::: compare 左 / 右` 每行 `左 \| 右` | 两栏对比 | ≤6 行，每格 ≤20 字，左右是同一维度 |
| `::: steps 标题` 每行 `步骤名 \| 补充` | 有序流程 | ≤6 步；序号自动生成，不要手写"1." |
| `::: checklist 标题` 每行 `done\|todo\|warn \| 事项` | 无序要点 | 状态只认 done/todo/warn |

## 占位组件
- `{{divider}}` 分隔点
- `{{author}}` 作者卡（config: author、author_bio）
- `{{footer}}` 关注引导 + 二维码（config: footer.text、footer.qr_image）；`auto_footer: true` 时自动追加
- `{{名称}}` 工作区 `templates/components/<名称>.html|.md`

## 其他自动处理
- 外链 → 文末「参考资料」脚注（微信内外链不可点）；`mp.weixin.qq.com` 链接保留。`--keep-links` 关闭。
- `![图注](x.png)` → 居中图片 + 灰色图注。
- 列表 → 带主题色符号的悬挂缩进段落（微信对 ul/ol 支持差）。
- 代码块 → 保留缩进的等宽块，可横向滚动。
