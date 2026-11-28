# 钉钉｜企业机器人互动卡片群告警与 @

适用范围：企业内部应用机器人已安装到目标群，且应用已获得机器人发消息、按手机号查询用户和读取成员信息的权限。群会话 ID、机器人凭据及手机号由调用项目配置；不要记录凭据或成员数据。无需自定义机器人 Webhook。

## 已验证流程

2026-11-13 在抖音直播巡检项目的影刀环境中，由用户确认测试卡片能收到 @ 提醒：从配置手机号查询 userId，再查询成员姓名；卡片正文包含 `@姓名`，发送选项包含对应 userId 和姓名。群截图使用影刀页面截图，上传钉钉取得 media_id，放入卡片图片组件。调用成功仅表示接口接收，实际提醒及图片显示须以客户端验收为准；多成员场景尚未单独验证。

1. 使用企业应用凭据获取旧版 access_token，通过 `POST /topapi/v2/user/getbymobile` 以手机号查询 `result.userid`；再调用 `POST /topapi/v2/user/get`（请求体 `userid`）取得 `result.name`。
2. 如需现场图，通过 `POST /media/upload?type=image` 上传截图并取得 `media_id`。截图来源和业务条件由具体项目决定。
3. 获取新版 accessToken，通过 `POST /v1.0/im/v1.0/robot/interactiveCards/send` 发送 `StandardCard`。`cardData` 和 `sendOptions.atUserListJson` 均为 JSON 字符串；`cardBizId` 每条消息唯一。

```text
非执行调用说明（不可直接运行）：
cardData = JSON字符串({
  "config": {"autoLayout": true},
  "header": {"title": {"type": "text", "text": "<告警标题>"}},
  "contents": [
    {"type": "markdown", "id": "content", "text": "<告警内容>\n\n@<成员姓名>"},
    {"type": "image", "id": "screenshot", "image": "<图片media_id>"}
  ]
})
sendOptions = {"atUserListJson": JSON字符串([{"userId": "<用户ID>", "nickName": "<成员姓名>"}])}
```

测试中正文不包含 `@姓名` 时未收到 @ 提醒；不能把正文中的文字本身等同于已触发提醒。用户 ID、群成员资格、请求权限和卡片展示效果都需在目标环境核实。失败应如实报告，不把发送请求成功当作已读。

正式接口参见钉钉[机器人发送互动卡片](https://open.dingtalk.com/document/orgapp/robots-send-interactive-cards)、[获取用户详情](https://dingtalk.apifox.cn/api-139715614)。通知内容的业务规则见[钉钉通知实践](../dingtalk.md)。
