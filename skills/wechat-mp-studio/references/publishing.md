# 发布到公众号

## 前置条件
- 认证的订阅号或服务号才有草稿箱接口；部分账号有草稿权限但没有 `freepublish`（发布）权限（48001）。
- 公众平台 → 设置与开发 → 基本配置：AppID、AppSecret（只显示一次）、IP 白名单。
- **在用户自己的电脑上运行**：接口校验 IP 白名单，云端环境出口 IP 不固定。

## 配置
工作区 `config.json` 的 `accounts.<名>.appid/appsecret`，或环境变量 `WECHAT_APPID` / `WECHAT_APPSECRET`。
绝不让用户把 AppSecret 粘贴进对话；绝不在对话中输出 config.json。

```bash
python3 scripts/publish.py myip     # 本机出口 IP（仅供参考）
python3 scripts/publish.py check    # 校验凭证
```
IP 以 40164 报错里微信看到的为准（代理/分流时与 myip 不同），脚本会直接提示。

## 推草稿
```bash
python3 scripts/convert.py articles/<dir>/article.md --theme <主题> [--scheme <配色>]
python3 scripts/publish.py draft articles/<dir>/article_build --cover articles/<dir>/cover.jpg [--comment] [--account main]
```
- 正文图片自动上传（≤1MB，超出自动压缩；webp/gif 转 jpg；按内容哈希缓存在 `.cache/images.json`）。
- 封面上传为永久素材；未指定封面时用正文第一张图。
- 草稿 media_id 和临时预览链接（`draft_url`，https://mp.weixin.qq.com/…）写回 `meta.json` 并打印出来，把链接给用户在微信里查看。每次 draft 都会新建草稿，提醒用户删掉旧版本。
- 临时链接只用于预览，会过期，不要当正式链接分享；正式链接在群发/发布后获得。

## 直接发布（需用户明确确认）
```bash
python3 scripts/publish.py publish <draft_media_id> --yes
python3 scripts/publish.py status <publish_id>
```
发布成功后 `status` 打印正式文章链接（https://mp.weixin.qq.com/s/…），把它给用户。
`freepublish` 发布的文章**不推送给粉丝**、不进订阅消息，只出现在主页，可分享链接；不可撤回，只能删除。要推送粉丝请在后台手动群发。

## 错误码
| 码 | 含义 / 处理 |
|---|---|
| 40164 | IP 不在白名单，按报错里的 IP 添加 |
| 48001 | 无接口权限（未认证，或无发布权限 → 后台手动群发） |
| 40001 / 40125 / 40013 | AppSecret / AppID 错误 |
| 40007 | media_id 无效（草稿已被删除或修改） |
| 45002 / 45003 / 45004 | 正文 / 标题 / 摘要过长 |
| 53503 | 未通过发布检查，去后台查看 |
