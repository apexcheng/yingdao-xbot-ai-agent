# 钉钉｜群 Webhook 文本或 Markdown 通知

适用范围：已由用户确认群机器人 Webhook 地址、鉴权方式，且当前业务只需向**指定群**发送文本/Markdown。使用 Python 标准库，不依赖「增强工具2026」；**不能替代**企业机器人私聊、群图片上传、基于 userId 的发送等能力。

## 最小 Markdown 发送

```python
import json
from urllib.request import Request, urlopen

# webhook_url 来自本地 config.py，不要输出到日志。
payload = {
    "msgtype": "markdown",
    "markdown": {"title": "执行结果", "text": "### 报表更新完成\n> 本轮已保存"},
}
request = Request(
    webhook_url,
    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urlopen(request, timeout=15) as response:
    result = json.loads(response.read().decode("utf-8"))
if result.get("errcode") != 0:
    raise RuntimeError(f"钉钉 Webhook 发送失败：{result.get('errmsg')}")
```

## 已开启加签安全时

使用用户提供的 Secret（不写进知识库）。生成签名后，将 `timestamp` 和 `sign` 附加到原有 Webhook 查询参数；业务应沿用已经确认的钉钉机器人安全设置。

```python
import base64
import hashlib
import hmac
import time
from urllib.parse import quote_plus

timestamp = str(int(time.time() * 1000))
string_to_sign = f"{timestamp}\n{webhook_secret}"
signature = base64.b64encode(
    hmac.new(webhook_secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha256).digest()
).decode("ascii")
webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={quote_plus(signature)}"
```

发送结果须检查接口业务错误码；不能以 HTTP 200 断言对方已接收或读到。发送正文的业务汇总与异常追溯规则见 [钉钉通知实践](../dingtalk.md)；不要因为迁移工具而改变通知状态口径。

证据：既有知识库的群机器人 Webhook 场景和标准 HTTP/加签协议；未对真实机器人发消息验收。企业机器人发送所需的授权、Token、会话/用户 ID API 尚无独立已验模板，遇到该需求先查正式接口并补知识，不能改用群 Webhook 代替。
