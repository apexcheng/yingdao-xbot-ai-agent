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

## 验证码接收

点击「获取验证码」前，先轮询同一 topic，记录已有消息的 `id`；点击后轮询，跳过这些 ID，再按业务确认的发送方和短信正文格式匹配新消息。等待时限用 `time.monotonic()` 计算，避免系统校时影响等待。完整登录示例见[抖店手机号登录](site-logins/douyin-shop.md)。

不要用本机 `time.time()` 与 ntfy 的 `message["time"]` 比较来决定消息是否属于本次请求：运行机和 ntfy 服务的时钟可能不同步。实测目标机快约 76 秒时，手机收到并成功转发的新短信被判为旧消息，最终等待超时；反向时差也可能让旧消息被误用。消息 ID 基线不依赖两端时钟一致，也避免按整秒时间戳判断的歧义。

ID 基线只能区分基线读取前后看到的消息，不能证明新消息由本次点击产生：基线读取结束到点击之间到达的消息、之前短信的延迟转发以及同一 topic 的并发请求都可能混入。多账号共用或并发接码时，必须按实际业务确认能区分接收者和请求的关联方式，不能把任意新消息认定为本次验证码。基线和轮询须使用同一 topic，消息 ID 与缓存范围须由所用服务支持；网络或解析失败如实抛出，不回退到旧时间过滤。验证码不写入日志。

`poll=1` 是一次性轮询，不是长连接；`since=10m` 是取消息范围，不是服务器保留期限。ntfy 读取不删除已读消息。网络/HTTP 异常让其如实抛出，由业务调用方处理。使用公共 `ntfy.sh` 时 topic 应足够难猜，不传账号密码等高敏感信息，验证码不打印至日志。

**证据**：2026-10-29 核对 ntfy 协议调用；2026-11-10 实际只读查询确认 JSON 消息含 ID，目标机时间偏差与过滤失败的时间线吻合。ID 基线筛选已做离线模拟验证，尚未完成真实短信登录端到端验收。
