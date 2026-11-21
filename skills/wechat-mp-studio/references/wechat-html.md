# 微信公众号 HTML 约束（改脚本或写自定义组件前读）

- 只认内联 `style`：`<style>`、class、id 选择器、外部 CSS/JS 全部被过滤。
- 不支持/不可靠：`position`、`background-clip:text`（渐变字会变透明不可见）、`rgba` 在部分客户端、动画、`@media`、自定义字体。
- 可用：`display:flex`（简单布局）、`linear-gradient` 背景、`border-radius`、`box-shadow`。
- 标签之间的换行会被当成空行或空列表项 → 输出前去掉所有 `\n`。
- `<ul>/<ol>` 缩进和符号不稳定 → 用 `<p>` + 手动符号 + 悬挂缩进。
- 外链不可点击（mp.weixin.qq.com 除外）→ 转脚注。
- 图片必须是微信域名（mmbiz.qpic.cn）：发布时上传并替换 src；`uploadimg` 仅 jpg/png ≤1MB。
- 代码块：空格转 `&nbsp;`、换行转 `<br>`，`white-space:nowrap` + `overflow-x:auto`。
- 正文 ≤2 万字符 / 1MB；标题 ≤64 字；摘要 ≤120 字。
- 草稿 JSON 必须 `ensure_ascii=False` 发送，否则中文会变成 \u 转义。
