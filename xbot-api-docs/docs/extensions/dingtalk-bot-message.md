# 钉钉企业机器人消息_v2 (dingtalk_bot_message)

> 调用类型：`direct python` 为主，保留 flow 包装兼容。
> 主要入口：`py_api.py` 的 `send_dingtalk_group()` / `send_dingtalk_private()`；`to_markdown_table.py` 可直接调用。
> 证据边界：入口、参数和返回值以当前安装版本源码或实测为准。
> 返回：[市场指令索引](../extension-instructions.md)

---

**目录/指令名：** `dingtalk_bot_message` / 钉钉企业机器人消息_v2

**调用方式：** direct python 优先

**用途：** 发送钉钉私聊消息、群聊消息、生成 markdown 表格

**调用入口：**
- Direct：`xbot_extensions.dingtalk_bot_message.py_api.send_dingtalk_group(...)`
- Direct：`xbot_extensions.dingtalk_bot_message.py_api.send_dingtalk_private(...)`
- Direct：`xbot_extensions.dingtalk_bot_message.to_table_format.to_markdown_table(data, max_cell_length)`
- Flow 兼容入口：`process1(...)` / `process2(...)`

**参数说明：**
- `message_type`：消息类型（`text` / `markdown` / `image`）
- `content`：文本/markdown内容 或 图片路径
- `user_mobiles`：接收人手机号列表（私聊，自动换取 userId）
- `webhook_url` / `webhook_secret`：自定义机器人 webhook
- `at_mobiles` / `at_all`：@ 相关

**返回值：** 钉钉接口返回结果。发送失败会抛出异常，不要按返回 `False` 处理。

**注意事项：**
- 群聊图片需要 `app_key` + `app_secret` + `open_conversation_id`
- 群聊文本/Markdown 可以用 webhook 机器人
- `to_table_format.py` 可直接调用生成 markdown 表格
- 新代码优先使用 `py_api.py`，不要再优先套 `process1()` / `process2()` 的 Visual flow

## Direct Python 参数

```text
非执行调用说明（不可直接运行）：

send_dingtalk_group(
    message_type,
    content,
    *,
    app_key=None,
    app_secret=None,
    robot_code=None,
    open_conversation_id=None,
    webhook_url=None,
    webhook_secret=None,
    title=None,
    at_mobiles=None,
    at_all=None,
    timeout=10.0,
)
```

群消息支持 `text`、`markdown`、`image`。文本和 Markdown 可走 webhook；图片通常需要应用机器人参数。

私聊入口使用相同的消息类型与内容参数，并通过 `user_ids` 或 `user_mobiles` 指定接收人。账号、密钥、webhook 等敏感信息应从项目参数或安全配置中读取，不要写入知识库或提交到 Git。

**典型调用方式：**
```text
非执行调用说明（不可直接运行）：

from xbot_extensions.dingtalk_bot_message.py_api import (
    send_dingtalk_group,
    send_dingtalk_private,
)

# 发送群 Markdown
result = send_dingtalk_group(
    "markdown",
    "## 数据更新完成\n\n报表已写入。",
    title="数据更新完成",
    webhook_url=webhook_url,
    webhook_secret=webhook_secret,
    at_mobiles=[],
    at_all=False,
)

# 发送私聊文本
result = send_dingtalk_private(
    "text",
    "任务执行完成",
    app_key=app_key,
    app_secret=app_secret,
    user_mobiles=[mobile],
)

# 生成 markdown 表格
from xbot_extensions.dingtalk_bot_message.to_table_format import to_markdown_table
md = to_markdown_table(data=[["a", "b"], ["1", "2"]], max_cell_length=100)
```

**项目里的 Markdown 群通知模式：**

```text
非执行调用说明（不可直接运行）：

from xbot_extensions.dingtalk_bot_message.py_api import send_dingtalk_group
from xbot.app import logging

try:
    send_dingtalk_group(
        "markdown",
        content,
        title="商品链接价格监测完成",
        webhook_url="",
        webhook_secret="",
        at_mobiles=[],
        at_all=False,
    )
except Exception as e:
    logging.error(f"钉钉群通知发送失败：{e}")
```

补充约定：

- 群通知里更推荐 `title` 和 `content` 分离，正文统一传 Markdown。
- 如果通知失败只影响提醒链路，不影响主业务，可只记录日志，不中断主流程。
- 老项目继续使用 `process1()` / `process2()` 时无需强制改造；新增代码直接使用 `py_api`，调用链更短、参数更明确。
- 业务通知的标题、状态 emoji、信息层级、@ 人策略和 Markdown 排版偏好见 [钉钉通知文案与排版偏好](../../../docs/dingtalk-notification-style.md)。本页只维护市场指令调用事实，不重复维护文案规范。

---
