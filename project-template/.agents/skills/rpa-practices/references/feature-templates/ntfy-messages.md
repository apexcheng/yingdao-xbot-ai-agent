# ntfy｜标准库发送与轮询接收

适用于影刀项目已配置 ntfy 服务和私有 topic 的通知/短信转发；不依赖 `xbot_enhance_tools`、`requests`。接口基于已核实的 `POST /<topic>` 与 `GET /<topic>/json?since=10m&poll=1`。消息可能被缓存，**获取消息不代表只会返回本次发送的数据**。

## 发送文本

```python
from urllib.parse import quote
from urllib.request import Request, urlopen

# topic 和 server 来自本项目的 config.py，不要在源码中写真实私有 topic。
url = f"{server.rstrip('/')}/{quote(topic, safe='')}"
request = Request(url, data=message.encode("utf-8"), headers={"Content-Type": "text/plain"}, method="POST")
with urlopen(request, timeout=15) as response:
    if response.status != 200:
        raise RuntimeError(f"ntfy 发送失败：HTTP {response.status}")
```

## 读取最近 10 分钟的消息

```python
import json
from urllib.parse import quote
from urllib.request import urlopen

url = f"{server.rstrip('/')}/{quote(topic, safe='')}/json?since=10m&poll=1"
with urlopen(url, timeout=15) as response:
    messages = [
        json.loads(line)
        for line in response.read().decode("utf-8").splitlines()
        if line.strip()
    ]
messages = sorted(
    (message for message in messages if message.get("event") == "message"),
    key=lambda message: message.get("time") or 0,
    reverse=True,
)
```

验证码登录需要**在点击「获取验证码」前**记下 `requested_at=int(time.time())`，之后循环读取，按 `message["time"] >= requested_at` 与业务特定发送方、短信正文正则共同匹配，并设置总超时。ntfy 的消息时间戳是整秒，无法严格区别同一秒内两条验证码；多个账号共用 topic 时应再确认接收策略。

`poll=1` 是一次性轮询，不是长连接；`since=10m` 是取消息范围，不是服务器保留期限。ntfy 读取不删除已读消息。网络/HTTP 异常让其如实抛出，由业务调用方处理。使用公共 `ntfy.sh` 时 topic 应足够难猜，不传账号密码等高敏感信息，验证码不打印至日志。

**证据**：2026-10-29 核对已安装 `xbot_enhance_tools/ntfy_message.py` 的协议调用并用 Python 标准库替代。此模板未独立做真实 ntfy 请求测试。
