# 增强工具2026 (xbot_enhance_tools)

> 保留的 Python 片段依赖当前流程已取得的对象、输入数据和项目已确认的参数。片段不是独立脚本；[示例边界](../../AGENTS.md)。

> 调用类型：`direct python`  
> 主要入口：直接调用 browser_utils.py、exception_utils.py、shop_utils.py、win_utils.py、excel_utils.py、ntfy_message.py、market_config.py 中的公开函数；__init__.py 不提供 processN 包装入口。
> 证据边界：入口以当前安装版本公开模块为准；网页登录和下载等待需运行验证。
> 返回：[市场指令索引](../extension-instructions.md)

---

**目录/指令名：** `xbot_enhance_tools` / 增强工具2026

**调用方式：** direct python

**用途：** 面向 `xbot` 的增强工具包。当前已收录浏览器 XPath 等待、下载等待、异常详情格式化、商家后台登录辅助、Windows 元素可点击判断、Excel / WPS 共享文件占用者识别、ntfy 消息发送与接收，以及影刀自定义对话框初始化配置的 DPAPI 加密持久化。

**调用入口：**
- `from xbot_extensions.xbot_enhance_tools import exception_utils, browser_utils, shop_utils, win_utils, ntfy_message`
- `from xbot_extensions.xbot_enhance_tools.browser_utils import wait_appear_by_xpath`
- `from xbot_extensions.xbot_enhance_tools.browser_utils import wait_disappear_by_xpath`
- `from xbot_extensions.xbot_enhance_tools.browser_utils import wait_download_file`
- `from xbot_extensions.xbot_enhance_tools.exception_utils import format_exception_detail`
- `from xbot_extensions.xbot_enhance_tools.shop_utils import login_pdd_seller`
- `from xbot_extensions.xbot_enhance_tools.shop_utils import login_qianniu`
- `from xbot_extensions.xbot_enhance_tools.shop_utils import login_jingmai`
- `from xbot_extensions.xbot_enhance_tools.shop_utils import login_alipay`
- `from xbot_extensions.xbot_enhance_tools.shop_utils import login_douyin_seller`
- `from xbot_extensions.xbot_enhance_tools.win_utils import is_win_element_clickable`
- `from xbot_extensions.xbot_enhance_tools.excel_utils import get_wps_lock_user`
- `from xbot_extensions.xbot_enhance_tools.ntfy_message import send_ntfy_message`
- `from xbot_extensions.xbot_enhance_tools.ntfy_message import receive_ntfy_message`
- `from xbot_extensions.xbot_enhance_tools.market_config import dialog_result_to_dict`
- `from xbot_extensions.xbot_enhance_tools.market_config import save_secret_config`
- `from xbot_extensions.xbot_enhance_tools.market_config import load_secret_config`

**当前能力：**
- `wait_appear_by_xpath(page, xpath, timeout=20)`：循环调用 `page.find_all_by_xpath(xpath, timeout=1)`，匹配到一个及以上元素即返回第一个元素，超时返回 `None`
- `wait_disappear_by_xpath(page, xpath, timeout=20)`：循环调用 `page.find_all_by_xpath(xpath, timeout=1)`，返回空列表即视为已消失，返回 `True`；超时返回 `False`
- `wait_download_file(download_dir=None, filename_pattern=None, timeout=300, start_time=None)`：等待下载目录中的文件下载完成；成功返回 `pathlib.Path`；超时抛出 `TimeoutError`。`download_dir` 不传时默认使用当前用户下载目录，不存在则回退到 `~/下载`；`filename_pattern` 可选，传了按指定文件名关键词或 glob 表达式匹配，不传按本次新出现并稳定的文件判断；`start_time` 建议在点击下载前用 `time.time()` 记录
- `format_exception_detail(e)`：返回错误信息、报错位置、当前时间、函数名、代码行，适合通知或日志汇总
- `login_pdd_seller(account, password, profile=None)`：打开拼多多商家中心登录页，登录后按 URL 是否离开 `login` 判断结果
- `login_qianniu(account, password, profile=None)`：打开千牛商家工作台登录页，登录后按 URL 是否离开 `login` 判断结果
- `login_jingmai(account, password, profile=None)`：打开京麦商家工作台登录页，登录后按 URL 是否离开 `login` 判断结果
- `login_alipay(account, password, profile=None)`：打开支付宝登录页，切到“账密登录”，输入账号密码并提交，等待页面跳转后按 URL 是否仍包含 `login` 判断结果
- `login_douyin_seller(account, password, profile=None)`：打开抖音电商后台 `https://fxg.jinritemai.com/login`，切换到邮箱登录，输入邮箱和密码，必要时勾选协议并提交；按 URL 是否离开 `login` 判断结果
- `is_win_element_clickable(element)`：判断 `Win32Window.find()` / `find_all()` 返回的 Win 元素是否显示、可用、矩形有效，且中心点落在当前屏幕范围内；满足时返回 `True`，否则返回 `False`
- `get_wps_lock_user(workbook)`：判断影刀 Excel 工作簿是否因共享文件占用而只读，并读取同目录的 `~$` 锁文件解析当前占用者用户名。仅接收影刀 Excel workbook 对象
- `send_ntfy_message(message, topic, server="https://ntfy.sh")`：向指定 ntfy topic 发送纯文本消息；成功返回 `True`，失败抛出异常
- `receive_ntfy_message(topic, server="https://ntfy.sh", since="10m", timeout=15)`：从指定 ntfy topic 拉取 `since` 范围内的缓存消息，按 `time` 从新到旧返回包含 `id`、`time`、`message` 的字典列表；无消息时返回空列表
- `dialog_result_to_dict(dialog_result, ignore_attr=None)`：将 `xbot.app.dialog.show_custom_dialog()` 的返回对象转换为普通 `dict`；字符串值会尽量还原为 bool、数字、list、dict 等 Python 基础对象
- `save_secret_config(json_path, config_obj, entropy="", description="my_app")`：使用当前 Windows 用户的 DPAPI 加密配置，并以 `{"token": "..."}` 形式持久化到磁盘；父目录不存在时自动创建
- `load_secret_config(json_path, entropy="")`：读取并解密配置；成功返回 `dict`，文件不存在、格式错误、token 无效或解密失败时返回 `None`

**适用场景：**
- Agent 编码场景里只有 XPath 字符串，没有元素库选择器
- XPath 字符串等待优先使用本扩展里的等待方法
- 下载文件业务需要统一等待下载完成
- 需要把异常对象整理成更易读的文本内容
- 需要在编码版里直接调用商家后台登录辅助函数，并复用指定 Chrome profile
- 点击 Windows 元素前，需要先判断元素当前是否适合直接点击
- 共享 Excel / WPS 文件保存失败或只读打开时，需要识别当前占用者用户名
- 需要在 iOS 快捷指令与影刀 RPA 之间传递短信、验证码或其他文本消息
- 机器人首次运行时通过 `show_custom_dialog()` 收集账号、路径、开关等初始化参数，并希望后续启动时直接读取，而不是每次重新填写
- 初始化配置包含账号、密码或其他不适合明文写入 JSON 的敏感字段，需要使用 Windows 当前用户凭证保护后再落盘

**最小示例：**

```text
非执行调用说明（不可直接运行）：

import time

from xbot_extensions.xbot_enhance_tools.browser_utils import (
    wait_appear_by_xpath,
    wait_disappear_by_xpath,
    wait_download_file,
)
from xbot_extensions.xbot_enhance_tools.exception_utils import format_exception_detail
from xbot.app import logging


element = wait_appear_by_xpath(page, '//button[contains(., "查询")]', timeout=10)
if not element:
    raise RuntimeError("查询按钮等待超时")
element.click()

if not wait_disappear_by_xpath(page, '//div[@class="loading"]', timeout=20):
    raise RuntimeError("loading 未消失")

start_time = time.time()
file_path = wait_download_file(filename_pattern="result.xlsx", timeout=300, start_time=start_time)
file_path = str(file_path)

try:
    page.find_by_xpath('//input[@name="keyword"]', timeout=3).input("影刀")
except Exception as e:
    detail = format_exception_detail(e)
    logging.error(detail)
    raise
```

**商家后台登录示例：**

```text
非执行调用说明（不可直接运行）：

from xbot_extensions.xbot_enhance_tools import shop_utils


ok = shop_utils.login_pdd_seller("账号", "密码", profile="Default")
if not ok:
    raise RuntimeError("拼多多商家中心登录失败")

ok = shop_utils.login_alipay("账号", "密码", profile="Default")
if not ok:
    raise RuntimeError("支付宝登录失败")

ok = shop_utils.login_douyin_seller("邮箱账号", "密码", profile="Default")
if not ok:
    raise RuntimeError("抖音店铺登录失败")
```

**Windows 元素可点击判断示例：**

```text
非执行调用说明（不可直接运行）：

from xbot_extensions.xbot_enhance_tools.win_utils import is_win_element_clickable


element = window.find("确定", timeout=3)
if not is_win_element_clickable(element):
    raise RuntimeError("确定按钮当前不可点击")
element.click()
```

**Excel / WPS 共享文件占用者识别示例：**

```python
from xbot.app import logging
from xbot_extensions.xbot_enhance_tools.excel_utils import get_wps_lock_user


# 传影刀 Excel 工作簿对象
user = get_wps_lock_user(workbook)

if user:
    logging.info(f"文件正在被【{user}】占用")
```

**ntfy 消息发送与接收示例：**

```text
非执行调用说明（不可直接运行）：

发送：send_ntfy_message(已确认的消息内容, topic=已确认的目标主题)
接收：receive_ntfy_message(topic=同一已确认主题, timeout=15)
按真实返回消息处理结果；示例不发送验证码或使用固定公共主题。
```

**初始化配置加密持久化示例：**

```text
非执行调用说明（不可直接运行）：

from xbot.app.dialog import show_custom_dialog
from xbot_extensions.xbot_enhance_tools.market_config import (
    dialog_result_to_dict,
    load_secret_config,
    save_secret_config,
)


config_path = r"C:\RobotData\my_robot_config.json"

config = load_secret_config(config_path)
if config is None:
    dialog_result = show_custom_dialog(dialog_settings)
    config = dialog_result_to_dict(dialog_result)
    save_secret_config(config_path, config)

username = config["username"]
```

`market_config.py` 对外只约定以上 3 个公开方法。DPAPI 加解密、字符串自动转换和底层 Windows CryptoAPI 处理均为 `_` 开头的内部方法，不应由业务项目直接依赖。

**`show_custom_dialog()` 常用写法：**

- 不要使用 `{"title": ..., "fields": ...}` 这种简化结构。
- 推荐使用 `dialog_settings` 结构，通过 `dialogTitle`、`settings.editors`、`settings.buttons` 定义。
- 输入控件使用 `VariableName` 作为返回字段名，之后通过 `dialog_result_to_dict()` 转换。
- 用户点击的按钮在返回结果中以 `pressed_button` 作为 key，不是 `button`；经 `dialog_result_to_dict()` 转换后的 dict 同样按 `pressed_button` 读取。
- 初始化配置场景通常流程：`load_secret_config()` → 无配置时 `show_custom_dialog(dialog_settings)` → `dialog_result_to_dict()` → `save_secret_config()`。
- 加密保存也可以由 `CheckBox` 编辑器控制：底部保留“启动 / 取消”按钮，用户勾选“持久化加密”后再调用 `save_secret_config()`。
- 原生“记住内容”与“持久化加密”可以同时提供，但两者职责不同：前者通过 `canRememberContent + storage_key` 在下次打开对话框时回填输入，不能视为加密；后者由业务代码调用 DPAPI 保存。具体控件配置见[对话框与通知](../notification.md)。
- 对话框包含密码、Token 等敏感输入时，应提示用户不要勾选原生“记住内容”；勾选“持久化加密”不影响原生记忆功能，也不会把原生记忆产生的副本改为密文。

示例：

```text
非执行调用说明（不可直接运行）：

saved_config = load_secret_config(str(project_config.CONFIG_PATH)) or {}

dialog_settings = {
    "dialogTitle": "初始化配置",
    "canRememberContent": True,
    "settings": {
        "editors": [
            {
                "type": "TextArea",
                "label": "平台店铺配置",
                "VariableName": "platform_configs",
                "value": saved_config.get("platform_configs"),
                "nullText": "请输入平台店铺配置 JSON",
                "height": 300,
            },
            {
                "type": "CheckBox",
                "content": "持久化加密",
                "VariableName": "persist_encrypted",
                "value": False,
            },
        ],
        "buttons": [
            {
                "type": "Button",
                "label": "启动",
                "theme": "red",
            },
            {
                "type": "Button",
                "label": "取消",
                "theme": "white",
            },
        ],
    },
}

dialog_result = show_custom_dialog(dialog_settings, storage_key="platform_config_dialog")
config = dialog_result_to_dict(dialog_result)

# 用户点击的按钮 key 是 pressed_button，不是 button
pressed_button = config.pop("pressed_button")
persist_encrypted = config.pop("persist_encrypted", False)

if pressed_button != "取消" and persist_encrypted:
    save_secret_config(str(project_config.CONFIG_PATH), config)
```

**注意事项：**
- 这是市场扩展能力，不是原生 `xbot` 内置 API
- `wait_appear_by_xpath()` / `wait_disappear_by_xpath()` 面向 XPath 字符串，不是元素库选择器
- 需要循环刷新等待元素时，优先让 `wait_appear_by_xpath()` 负责单轮短时等待，并在循环顶部统一判断总超时；不要再用 `find_by_xpath()` 配合 `try / except` 轮询
- `wait_disappear_by_xpath()` 的判定依据是"`find_all_by_xpath()` 返回空列表即视为已消失"
- 两个等待方法内部都用 `find_all_by_xpath()` 判断，XPath 匹配到多个元素时也能正常工作；不要改回 `find_by_xpath()`（它匹配到多个元素会抛异常，会让"等待出现"误判为失败、"等待消失"误判为已消失）
- 下载文件业务统一优先使用 `wait_download_file()`，不要再为同类业务单独维护旧下载等待封装
- `wait_download_file()` 成功返回 `Path`；需要传给只接受字符串路径的市场指令或旧代码时，可显式转换为 `str(file_path)`
- `wait_download_file()` 超时会抛出 `TimeoutError`，不要把超时误判为返回 `None`
- `shop_utils` 中的登录 XPath 会随平台页面变化，当前页面行为需运行验证
- 商家后台登录只处理账号密码输入和提交，不处理验证码、扫码、安全验证、短信验证、人机验证等复杂分支
- 抖音登录使用邮箱账号；协议勾选仅在页面显示未勾选状态时处理，登录后的跳转和风控页面仍需在实际环境确认
- 当前 `__init__.py` 仅做模块导入，不建议把隐藏的 Visual block 当作主要调用方式
- `is_win_element_clickable()` 只判断元素当前状态和中心点是否在屏幕范围内，不会自动滚动、激活窗口或处理遮挡；复杂窗口状态仍需运行验证
- `excel_utils.py` 是增强工具2026新增文件；`get_wps_lock_user()` 只接收影刀工作簿对象，并通过 `workbook.get_full_name()` 获取正式文件路径
- `get_wps_lock_user()` 会先检查 `workbook.workbook.ReadOnly`：`False` 时直接返回 `None`，即使目录里有残留 `~$` 文件也不判定为占用；`True` 时才继续检查锁文件
- `get_wps_lock_user()` 不通过普通 Python `open()` 读取锁文件，而是使用 Windows `CreateFileW` 并允许 `FILE_SHARE_READ / FILE_SHARE_WRITE / FILE_SHARE_DELETE` 后读取；这是为兼容 WPS 占用期间普通读取可能出现 `PermissionError` 的情况
- 当前实测 WPS 锁文件会在同目录生成 `~$原文件名.xlsx/xlsm`，用户名优先从 UTF-16LE 区域解析，兼容 ANSI / GBK 回退；`ReadOnly=True` 但未发现锁文件时返回 `None`，锁文件存在但无法解析用户名时返回 `"未知用户"`
- 该能力依赖 Windows / WPS 当前锁文件格式，已在当前 WPS 环境验证可读取中文用户名；WPS 后续版本若调整锁文件格式，需要重新验证解析偏移
- `ntfy_message.py` 依赖 `requests`，当前市场指令项目已登记该依赖
- 使用公共 `ntfy.sh` 时，topic 即消息地址的一部分，应使用难以猜测的私有 topic，避免传递账号密码等高敏感信息
- `receive_ntfy_message()` 使用 `poll=1` 一次读取当前缓存消息，不会在无消息时保持长连接等待；返回结果按消息时间从新到旧排序
- `since` 表示本次查询从什么时间点开始读取，例如 `10m` 是最近 10 分钟、`1m` 是最近 1 分钟；它不是 ntfy 的消息保存时长
- `receive_ntfy_message()` 的 `since` 默认值已经是 `"10m"`；业务没有特殊时间范围要求时不要显式传入，也不要额外改成更短或更长的值
- ntfy 拉取不会删除服务端消息；是否需要去重或持久化消费进度由调用方处理
- `market_config.py` 是增强工具2026的 Direct Python 能力，不是 `show_custom_dialog()` 本身；对话框仍由调用方负责创建和展示
- `market_config.py` 公开 API 仅有 `dialog_result_to_dict()`、`save_secret_config()`、`load_secret_config()`；其余 `_` 开头方法均视为内部实现，不要在业务项目中直接调用
- `save_secret_config()` 使用 Windows DPAPI。默认情况下，密文与执行加密的 Windows 用户安全上下文绑定，不能把该文件当作跨用户、跨机器通用的加密配置文件
- `entropy` 是可选附加熵；如果保存时传入，读取时必须传入完全相同的值，否则无法解密
- `load_secret_config()` 把文件不存在、JSON 无效、token 缺失和解密失败统一处理为 `None`，调用方可据此决定是否重新展示初始化对话框
- 配置文件磁盘格式固定为 `{"token": "<Base64 DPAPI 密文>"}`，不要再额外把明文账号、密码写入同一文件
- 后续如果该扩展新增能力，应按源码实际接口继续补充，不要提前推断

---
