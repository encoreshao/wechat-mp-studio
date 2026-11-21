# 主题与配色

`python3 scripts/convert.py --list-themes` 输出最新列表与适用场景。`--theme` 同时接受英文 key 和中文名。

## 基础主题（7 套，单一主色）

| key | 名称 | 特征 |
|---|---|---|
| tech-blue | 科技蓝 | 左侧色条 h2、深色代码块 |
| minimal-black | 极简黑 | 下划线 h2、黑白 |
| warm-orange | 暖橙 | 胶囊 h2 |
| elegant-purple | 优雅紫 | 居中 h2 |
| fresh-green | 清新绿 | 左侧色条 h2 |
| business-navy | 商务藏青 | 色块 h2、深色代码块 |
| ink-red | 墨韵红 | 衬线、居中 h2 |

## 风格主题（8 套 × 3 档配色，`--scheme` 选择）

| key | 名称 | 配色 | 适合 | 不适合 |
|---|---|---|---|---|
| friendly | 亲和 | 黛紫 / 松绿 / 靛蓝 | 教程、职场、新手向 | 严肃议题、财报 |
| notebook | 手账 | 朱红·黄笔 / 墨蓝·粉笔 / 深绿·薄荷笔 | 个人笔记、复盘、第一人称 | 官方公告 |
| bookish | 书卷 | 朱砂 / 黛蓝 / 苍绿 | 人文、读书、深度长文 | 代码、数据密集 |
| magazine | 杂志 | 石青 / 驼褐 / 铁锈 | 品牌故事、访谈、图多 | 纯文字短文 |
| news | 资讯 | 墨绿 / 绛红 / 藏青 | 快讯、评测、行业观察 | 抒情散文 |
| docs | 文档 | 蓝 / 紫 / 绿 | 工程实践、代码讲解 | 情绪向内容 |
| vivid | 活力 | 靛青 / 玫紫 / 暮橙 | 产品发布、年轻读者 | 严肃议题、超长稿 |
| bauhaus | 硬朗 | 蓝黄 / 赤黑 / 绿橙 | 观点、宣言 | 温和科普 |

推荐时：读文章类型 → 选 2-3 套 → 用 `preview.py` 让用户在浏览器里切换确认，或 `gallery.py` 出对比页。

## 自定义主题

在工作区 `templates/themes/<名称>.json`：

```json
{
  "label": "我的品牌",
  "extends": "friendly",
  "primary": "#E4572E",
  "secondary": "#FFD166",
  "scheme": "松绿",
  "overrides": { "h2": "font-size:20px;color:#fff;background:{primary-fill};padding:8px 16px;border-radius:999px;display:table;margin:40px auto 20px;" }
}
```

- `extends`：任一内置主题。基础主题另可用 `"h2": "bar|underline|pill|center|block"`、`"font": "sans|serif"`、`"code_dark": true`。
- 可覆盖键：`wrapper h1 h2 h3 h4 p strong em a blockquote code pre img figcaption hr table th td`。
- 继承风格主题时可用派生色变量：`{primary-color}`（原色，装饰）`{primary-fill}`（压白字的实心块，对比 ≥3）`{primary-ink}`（白底文字，对比 ≥4.5）`{bg-accent-soft}` `{bg-accent-color}`（两档浅底）`{highlight-pen}` `{highlight-soft}`（高亮笔）`{secondary-color}` `{secondary-ink}` `{secondary-soft}` `{text-color}` `{text-muted}`。
