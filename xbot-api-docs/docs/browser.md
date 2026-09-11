# 影刀浏览器操作方法整理

> 保留的 Python 片段依赖当前流程已取得的 `browser`、`page` 或 `element`，定位值和页面状态由项目确认。片段不是独立脚本；[示例边界](../AGENTS.md)。

> 定位：影刀 / xbot 操作浏览器的开发者参数手册。
> 重点：把 `xbot.web` 常用方法、参数、默认值、可选值写清楚。
> 规则：字符串参数必须按文档中的值原样传入，例如 `mode="chrome"`，不是 `Chrome` / `CHROME`。

网页实现路线及 HTTP 例外统一遵守[项目开发规则](../../project-template/AGENTS.md)：默认使用 `xbot.web` 和浏览器对象能力；用户明确要求接口方式，或项目已有稳定接口实现时，沿用对应路线。

---

## 0. 相关基础文档

| 文档 | 说明 |
|---|---|
| [`package.md`](package.md) | 元素库、图像库、资源文件、全局变量 |
| [`notification.md`](notification.md) | 桌面通知和对话框 |
| [`logging.md`](logging.md) | 日志记录 |
| [`win32.md`](win32.md) | Windows 桌面自动化 |

---

## 1. 核验来源

本页按本机可见 ShadowBot 6.3.13 内置 `xbot/web/__init__.py`、`browser.py` 和 `element.py` 核对；与 6.3.12 对应源码哈希一致。安装目录随版本变化；其他版本用 `inspect.getfile(xbot.web)` 定位当前实现，不复制固定绝对路径。

---

## 2. 参数传值总规则

### 2.1 字符串可选值区分大小写

```python
mode="chrome"
mode="cef"
button="left"
simulative=True
```

错误：

```python
mode="Chrome"
mode="CHROME"
button="Left"
simulative="True"
```

### 2.2 布尔值必须传 Python 布尔值

```python
visible=True
wait_complete=True
ignore_beforeunload=False
```

### 2.3 路径建议使用原始字符串

```python
file_folder = r"C:\Downloads"
file_name = r"C:\test.txt"
```

### 2.4 元素库与 XPath / CSS

项目已有元素库名称时，可直接使用 `browser.find("元素名")`。没有可复用元素时，再按真实 DOM 使用 XPath / CSS；不要自行猜测或转换选择器。

```python
element = browser.find("搜索框", timeout=10)
element = browser.find_by_xpath('//div[@class="item"]', timeout=10)
element = browser.find_by_css('.item', timeout=10)
```

### 2.5 运行日志

```python
from xbot.app import logging

logging.info("第1页采集中...")
```

真实影刀项目里的运行日志优先使用 `xbot.app.logging`，不要使用 Python 内置 `print()`。`xbot.print()` 属于历史兼容写法，普通新代码不再优先推荐。

### 2.6 全局变量 `package.variables`

更完整的 `package` 用法见 [`package.md`](package.md)。

```text
非执行调用说明（不可直接运行）：

from .package import variables as glv
client_id = glv['client_id']
glv['my_var'] = 'value'
```

---

## 3. 原生与可视化能力分工

| 层级 | 推荐使用场景 | 返回对象 |
|---|---|---|
| `xbot.web` | 普通网页自动化主线 | 原生 `WebBrowser` / `WebElement` |
| `xbot_visual.web` | 影刀可视化组件内部 | 多数为原生对象 |

重点：不要默认把 `xbot.web` 理解成带有 `wait_for_element` 一类的等待元素能力。单次等待元素出现可直接使用原生 `find_by_xpath(..., timeout=...)`；项目已安装“增强工具2026”、且需要等待 XPath 出现 / 消失或下载完成时，再按 [增强工具 2026](extensions/xbot-enhance-tools.md) 使用对应公开函数，不要仅因为文档示例给项目新增未安装依赖。

---

## 4. 浏览器类型 `mode`

| 浏览器 | 正确写法 | 说明 |
|---|---|---|
| 自动选择 | `mode="auto"` | 自动选择浏览器类型 |
| 影刀内置浏览器 | `mode="cef"` | 影刀内置浏览器 |
| 谷歌浏览器 | `mode="chrome"` | Google Chrome |
| Edge 浏览器 | `mode="edge"` | Microsoft Edge |
| IE 浏览器 | `mode="ie"` | Internet Explorer |
| 360 安全浏览器 | `mode="360se"` | 360 安全浏览器 |
| 火狐浏览器 | `mode="firefox"` | Firefox |

---

## 5. 打开网页：`xbot.web.create()`

```text
非执行调用说明（不可直接运行）：

from xbot import web

browser = web.create(
    url="https://example.com",
    mode="chrome",
    load_timeout=20,
    stop_if_timeout=False,
    silent_running=False,
    executable_path=None,
    arguments=None,
)
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---:|---|---|
| `url` | `str` | 是 | 无 | 要打开的网页地址 |
| `mode` | `str` | 否 | `"cef"` | 浏览器类型，必须小写 |
| `load_timeout` | `int` / `float` | 否 | `20` | `0` 不等待；`-1` 无限等待 |
| `stop_if_timeout` | `bool` | 否 | `False` | 页面加载超时后是否停止加载 |
| `silent_running` | `bool` | 否 | `False` | 是否静默运行 |
| `executable_path` | `str` / `None` | 否 | `None` | 自定义浏览器路径 |
| `arguments` | `list` / `str` / `None` | 否 | `None` | 启动参数 |

---

## 6. 获取网页：`get()` / `get_active()` / `get_all()`

```python
browser = web.get(title="订单")
browser = web.get_active(mode="chrome")
browsers = web.get_all(mode="chrome")
```

注意：`web.get_active()` 依赖浏览器已经启动；如果当前还没有启动浏览器，这里会获取失败。初始化浏览器时建议直接用 `web.create('')`，再按业务需要传入 `mode` 和 `url`。

多 Chrome Profile 场景要特别注意：`web.get_all(mode="chrome")` 受当前用户环境影响。要获取或关闭某个 Profile 下的页面，必须先用 `web.set_user_environment(...)` 切换到该 Profile，再调用 `web.get_all(...)`；不要在一个 Profile 环境下直接假设能拿到其它 Profile 的页面。

长期运行的多 Profile 自动化通常还需要在收尾时清理残留页面。清理某个 Profile 前同样先切换用户环境；日常目标如果只是防止页面越积越多，应保留该 Profile 的最后一个页面，避免把对应 Chrome 实例一起完全关闭，影响后续复用登录状态：

下例仅适用于对应 Profile 的全部页面已由当前流程接管的情况。Profile 中混有用户工作页时，不能直接按 `get_all()[:-1]` 清理，应只关闭当前流程已确认接管的页面。

```text
非执行调用说明（不可直接运行）：

for profile in dict.fromkeys(profiles):
    profile = str(profile or "Default").strip() or "Default"
    web.set_user_environment(mode="chrome", profile_name=profile, specifield_userdata=False, user_data_dir=None)
    for page in web.get_all(mode="chrome")[:-1]:
        page.close()
```

这里的 `[:-1]` 是有意保留最后一个页面，不是遗漏。只有业务明确要求完全退出浏览器时，才关闭全部页面或使用 `web.close_all()`。页面清理还要遵守所有权边界：只清理由当前自动化流程接管的页面，不要因为 `get_all()` 能获取到就关闭用户手工保留的工作页。

复用 Profile 登录态时，优先先检查当前目标站点是否已经登录，再决定是否进入登录流程；登录态判断必须以该站点真实页面、URL、元素或已验证 Cookie 规则为准，不要把一个站点的判断方式泛化到其它平台。

| 方法 | 主要参数 | 说明 |
|---|---|---|
| `get(title=None, url=None, mode='cef', ...)` | `title` / `url` / `mode` / `open_page` / `page_url` | 按标题或网址匹配已打开网页 |
| `get_active(mode='cef', ...)` | `mode` | 获取当前激活网页 |
| `get_all(mode='cef', ...)` | `title` / `url` / `use_wildcard` | 获取所有网页 |

---

## 7. 关闭网页：`close()` / `close_all()`

```text
非执行调用说明（不可直接运行）：

browser.close(ignore_beforeunload=False)
web.close_all(mode="chrome", task_kill=False, ignore_beforeunload=False)
```

网页关闭及异常收尾统一遵守[项目开发规则](../../project-template/AGENTS.md)；关闭范围仍须符合本页的页面所有权和 Profile 边界。

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `ignore_beforeunload` | `bool` | `False` | 是否忽略“确认离开页面”弹窗 |
| `mode` | `str` | `"cef"` | 要关闭的浏览器类型 |
| `task_kill` | `bool` | `False` | 是否强制结束浏览器进程 |

---

## 8. `Browser` 常用方法

`xbot.web.Browser` 是网页对象。

| 方法 | 作用 |
|---|---|
| `get_url()` | 获取当前网页地址 |
| `get_title()` | 获取当前网页标题 |
| `get_text()` | 获取页面文本 |
| `get_html()` | 获取页面 HTML |
| `activate()` | 激活网页 |
| `activateTab()` | 激活标签页 |
| `close(ignore_beforeunload=False)` | 关闭当前网页 |
| `navigate(url, load_timeout=20)` | 跳转网址 |
| `go_back(load_timeout=20)` | 后退 |
| `go_forward(load_timeout=20)` | 前进 |
| `reload(ignore_cache=False, load_timeout=20)` | 刷新页面 |
| `stop_load()` | 停止加载 |
| `wait_load_completed(timeout=20)` | 等待页面加载完成 |
| `find(selector, timeout=20)` | 查找单个元素 |
| `find_all(selector, timeout=20)` | 查找多个元素 |
| `find_by_css(css_selector, timeout=20)` | 按 CSS 查找单个元素 |
| `find_all_by_css(css_selector, timeout=20)` | 按 CSS 查找多个元素 |
| `find_by_xpath(xpath_selector, timeout=20)` | 按 XPath 查找单个元素 |
| `find_all_by_xpath(xpath_selector, timeout=20)` | 按 XPath 查找多个元素 |
| `scroll_to(location, ...)` | 滚动页面 |
| `execute_javascript(code, argument=None, execution_world="ISOLATED")` | 执行 JavaScript |
| `handle_javascript_dialog(dialog_result, text=None, wait_appear_timeout=20)` | 处理 JS 弹窗 |
| `get_javascript_dialog_text(wait_appear_timeout=20)` | 获取 JS 弹窗文本 |
| `start_monitor_network(...)` | 开始网络监听 |
| `get_responses(...)` | 获取已监听响应 |
| `stop_monitor_network()` | 停止网络监听 |
| `http_request(...)` | 发起网页 HTTP 请求 |
| `screenshot(...)` | 截图 |

---

## 9. 页面基础信息和加载控制

```text
非执行调用说明（不可直接运行）：

url = browser.get_url()
title = browser.get_title()
text = browser.get_text()
html = browser.get_html()

browser.activate()
browser.activateTab()
browser.navigate("https://example.com/list", load_timeout=20)
browser.go_back(load_timeout=20)
browser.go_forward(load_timeout=20)
browser.reload(ignore_cache=False, load_timeout=20)
browser.stop_load()
browser.wait_load_completed(timeout=20)
```

| 方法 | 参数 | 说明 |
|---|---|---|
| `navigate(url, load_timeout=20)` | `url: str` | 跳转网址 |
| `go_back(load_timeout=20)` | `load_timeout` | 后退 |
| `go_forward(load_timeout=20)` | `load_timeout` | 前进 |
| `reload(ignore_cache=False, load_timeout=20)` | `ignore_cache: bool` | 是否忽略缓存刷新 |
| `wait_load_completed(timeout=20)` | `timeout` | `-1` 无限等待，正数为秒 |

---

## 10. 查找元素

```python
element = browser.find("按钮_查询", timeout=10)
elements = browser.find_all("商品列表项", timeout=10)
element = browser.find_by_css("#kw", timeout=10)
elements = browser.find_all_by_css(".item", timeout=10)
element = browser.find_by_xpath('//input[@name="q"]', timeout=10)
elements = browser.find_all_by_xpath('//div[@class="item"]', timeout=10)
```

从已找到的元素内部继续查找时，直接对元素调用同名方法，并使用以 `.//` 开头的相对 XPath：

```python
row = browser.find_by_xpath('//div[@role="row"]', timeout=10)
name_element = row.find_by_xpath('.//div[@aria-colindex="2"]', timeout=2)
buttons = row.find_all_by_xpath('.//button[contains(@class, "action")]', timeout=2)
```

注意：元素内部查找必须使用 `.//` 表示“从当前元素向下查找”。写成 `//` 会从整个页面根节点开始查找，可能匹配到其他行中的元素。

定位规则应以当前真实 DOM 为准。优先选择稳定文本、稳定属性、父子关系、元素语义或项目已有元素库；不要只依赖明显随机生成的 class，也不要因为按钮文案相同就假设 DOM 结构相同。已有 XPath / CSS 失效时，优先重新确认页面结构并修正定位规则，不要在业务代码里堆多个未经验证的候选 XPath 作为兜底，否则容易在页面变化后静默点错元素。

| 方法 | 参数 | 类型 |
|---|---|---|
| `find` | `selector` | `str`（元素库名称） |
| `find_all` | `selector` | `str`（元素库名称） |
| `find_by_css` | `css_selector` | `str` |
| `find_all_by_css` | `css_selector` | `str` |
| `find_by_xpath` | `xpath_selector` | `str` |
| `find_all_by_xpath` | `xpath_selector` | `str` |
| 所有查找方法 | `timeout` | `int` / `float` |

| 方法 | 未找到 | 匹配多个 |
|---|---|---|
| `find()` | 抛异常 | 抛异常 |
| `find_all()` | 返回空列表 | 返回列表 |
| `find_by_css()` | 抛异常 | 抛异常 |
| `find_all_by_css()` | 返回空列表 | 返回列表 |
| `find_by_xpath()` | 抛异常 | 抛异常 |
| `find_all_by_xpath()` | 返回空列表 | 返回列表 |

---

## 11. 等待元素

```python
element = browser.find_by_xpath('//button[contains(., "查询")]', timeout=10)
```

`find_by_xpath()` 自带超时等待，适合一次性等待并获取单个元素。需要“等待 XPath 出现 / 消失”“循环刷新直到总超时”这类复用能力时，如果当前项目已安装“增强工具2026”，直接使用其 `wait_appear_by_xpath()` / `wait_disappear_by_xpath()`；准确签名、返回值和循环等待约定只在 [增强工具 2026](extensions/xbot-enhance-tools.md) 维护。

---

## 12. `Element` 常用方法

`xbot.web.Element` 用于处理网页元素。

| 方法 | 作用 |
|---|---|
| `click()` | 点击元素 |
| `dblclick()` | 双击元素 |
| `hover()` | 鼠标悬停 |
| `focus()` | 聚焦元素 |
| `input(text)` | 输入文本 |
| `clipboard_input(text)` | 剪切板输入文本 |
| `get_text()` | 获取元素文本 |
| `get_html()` | 获取元素 HTML |
| `get_value()` | 获取元素值 |
| `set_value(value)` | 设置元素值 |
| `get_attribute(name)` | 获取元素属性 |
| `get_all_attributes()` | 获取全部属性 |
| `set_attribute(name, value)` | 设置属性 |
| `parent()` | 获取父元素 |
| `children()` | 获取子元素列表 |
| `check(mode)` | 复选框选中 / 取消 |
| `select(item, mode)` | 下拉框选择 |
| `select_by_index(index)` | 按下标选择 |
| `select_multiple(items, mode, append=False)` | 多选下拉选择 |
| `select_multiple_by_index(indexes, append=False)` | 按下标多选 |
| `is_displayed()` | 判断是否显示 |
| `is_enabled()` | 判断是否可用 |
| `is_checked()` | 判断是否选中 |
| `get_bounding(to96dpi=True, relative_to="screen")` | 获取元素矩形 |
| `scroll_to(location, behavior="instant", search_up=False)` | 滚动元素 |
| `execute_javascript(code, argument=None, execution_world="ISOLATED")` | 执行 JavaScript |
| `upload(file_path)` | 上传文件 |
| `download(file_folder, ...)` | 下载文件 |
| `drag_to(...)` | 拖拽元素 |
| `drag_to_by_cdp(...)` | 用 CDP 拖拽 |

---

## 13. 点击、双击、悬停、聚焦

```text
非执行调用说明（不可直接运行）：

element.click(button="left", simulative=True, keys="none", delay_after=0.3)
element.dblclick(simulative=True, delay_after=0.3)
element.hover(simulative=True, delay_after=0.3)
element.hover(simulative=True, delay_after=0.3, anchor=("middleCenter", -100, 0))
element.focus()
```

### 13.1 `click()` 参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `button` | `str` | `"left"` | 鼠标左键 / 右键，必须小写 |
| `simulative` | `bool` | `True` | 是否模拟人工点击 |
| `keys` | `str` | `"none"` | 辅助键，必须小写 |
| `delay_after` | `int` / `float` | `1` | 操作后等待 |
| `move_mouse` | `bool` | `False` | 是否显示鼠标轨迹 |
| `anchor` | `tuple` / `None` | `None` | 点击位置和偏移 |

### 13.2 `anchor` 可选值

`anchor` 参数结构为 `(sudoku_part, offset_x, offset_y)`：

- `sudoku_part`：元素内的锚点位置。
- `offset_x`：相对锚点的水平偏移量，负数向左，正数向右。
- `offset_y`：相对锚点的垂直偏移量，负数向上，正数向下。

| 第一项 | 说明 |
|---|---|
| `"topLeft"` | 左上 |
| `"topCenter"` | 上中 |
| `"topRight"` | 右上 |
| `"middleLeft"` | 左中 |
| `"middleCenter"` | 中心 |
| `"middleRight"` | 右中 |
| `"bottomLeft"` | 左下 |
| `"bottomCenter"` | 下中 |
| `"bottomRight"` | 右下 |
| `"random"` | 随机位置 |

### 13.3 `hover()` 参数

```text
非执行调用说明（不可直接运行）：

element.hover(simulative=True, delay_after=1, anchor=None)
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `simulative` | `bool` | `True` | 是否模拟人工移动（鼠标轨迹） |
| `delay_after` | `int` / `float` | `1` | 操作后等待 |
| `anchor` | `tuple` / `None` | `None` | 悬停位置和偏移，结构为 `(sudoku_part, offset_x, offset_y)`；为 `None` 时悬停在元素中心且无偏移 |

示例：悬停在元素中心左侧 100px：

```text
非执行调用说明（不可直接运行）：

element.hover(anchor=("middleCenter", -100, 0))
```

---

## 14. 输入文本

### 14.1 普通输入

```text
非执行调用说明（不可直接运行）：

element.input(
    text="测试内容",
    simulative=True,
    cdp_input=False,
    driver_input=False,
    append=False,
    contains_hotkey=False,
    force_ime_ENG=False,
    send_key_delay=50,
    focus_timeout=1000,
    delay_after=0.3,
    click_before_input=True,
    input_check=False,
    retry_times=3,
    check_value="",
)
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `text` | `str` | 必填 | 要输入的内容 |
| `simulative` | `bool` | `True` | 是否模拟人工输入 |
| `cdp_input` | `bool` | `False` | 极速直写输入 |
| `driver_input` | `bool` | `False` | 驱动输入，非静默模式下生效 |
| `append` | `bool` | `False` | 是否追加输入 |
| `contains_hotkey` | `bool` | `False` | 输入内容是否包含快捷键 |
| `force_ime_ENG` | `bool` | `False` | 是否强制英文输入法 |
| `send_key_delay` | `int` | `50` | 按键间隔（毫秒） |
| `focus_timeout` | `int` | `1000` | 获取焦点超时（毫秒） |
| `delay_after` | `int` / `float` | `1` | 操作后等待 |
| `click_before_input` | `bool` | `True` | 输入前是否点击元素 |
| `input_check` | `bool` | `False` | 是否开启输入校验 |
| `retry_times` | `int` | `3` | 校验失败重试次数 |
| `check_value` | `str` | `""` | 校验目标值 |

### 14.2 剪切板输入

```text
非执行调用说明（不可直接运行）：

element.clipboard_input(
    "中文内容",
    append=False,
    focus_timeout=1000,
    delay_after=0.3,
    send_key_delay=50,
    click_before_input=True,
)
```

推荐：中文、长文本、输入法不稳定时，优先用 `clipboard_input()`。

---

## 15. 文本、源码、属性和值

```text
非执行调用说明（不可直接运行）：

text = element.get_text()
html = element.get_html()
value = element.get_value()
element.set_value("新值")
href = element.get_attribute("href")
url = element.get_attribute("absoluteUrl")
attrs = element.get_all_attributes()
element.set_attribute("data-id", "123")
```

| 方法 | 参数 | 说明 |
|---|---|---|
| `get_text()` | 无 | 获取元素文本 |
| `get_html()` | 无 | 获取元素 HTML |
| `get_value()` | 无 | 获取元素值 |
| `set_value(value)` | `value: str` | 设置元素值 |
| `get_attribute(name)` | `name: str` | 获取属性；`"absoluteUrl"` 可取绝对链接 |
| `get_all_attributes()` | 无 | 获取全部属性 |
| `set_attribute(name, value)` | `str, str` | 设置属性 |

### 15.1 `get_text()` 暂时读取不到动态渲染文本

动态页面中，元素已经可以定位时，`get_text()` 仍可能拿不到完整业务文本。先区分两种情况：

1. 文本只是尚未加载完成：继续用“短间隔轮询 + 总超时”，每轮重新定位元素并读取。
2. 页面视觉上已经显示值，但 `get_text()` / `get_html()` 始终缺少动态渲染内容：不要继续重复 `get_text()`；改从真实 DOM 的 `textContent` 读取，再按业务格式判断。

```python
import re
import time

deadline = time.monotonic() + 3

while True:
    text = page.find_by_xpath(value_xpath, timeout=1).get_text()

    if re.fullmatch(r"\d+", text.strip()):
        break

    if time.monotonic() >= deadline:
        raise RuntimeError(f"动态文本加载超时：{text}")

    time.sleep(0.2)
```

正则应替换为当前业务值最终应满足的格式。

如果页面已经能看到动态数字，但 `get_text()` / `get_html()` 仍持续缺失这些值，可直接对当前元素读取 DOM `textContent`：

```python
element = page.find_by_xpath(countdown_xpath, timeout=1)
text = element.execute_javascript(
    """
    function (element, args) {
        return element.textContent;
    }
    """
)
```

真实案例中，倒计时视觉显示 `06 分 08 秒 后结束`，但 `get_text()` 只能得到 `分 秒 后结束`；此时继续轮询 `get_text()` 不会补出数字，应改读 `textContent` 后再用正则解析。动态内容本身仍可能延迟出现，因此 `textContent` 也应按“短间隔轮询 + 总超时”控制，不要无限等待。

---

## 16. 复选框和下拉框

```text
非执行调用说明（不可直接运行）：

element.check("check")
element.check("uncheck")
element.check("toggle")
checked = element.is_checked()

element.select("选项文本", mode="fuzzy")
element.select_by_index(0)
element.select_multiple(["选项1", "选项2"], mode="fuzzy", append=False)
element.select_multiple_by_index([0, 2], append=False)
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `mode` | `str` | `"fuzzy"` | 下拉框匹配模式 |
| `append` | `bool` | `False` | 是否追加选择 |
| `item` | `str` | 必填 | 单选文本 |
| `items` | `list[str]` | 必填 | 多选文本 |
| `index` | `int` | 必填 | 单选下标 |
| `indexes` | `list[int]` | 必填 | 多选下标 |

---

## 17. 状态、坐标、滚动

```python
visible = element.is_displayed()
enabled = element.is_enabled()
checked = element.is_checked()
x, y, width, height = element.get_bounding(to96dpi=True, relative_to="screen")
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `to96dpi` | `bool` | `True` | 是否转换为 96 DPI |
| `relative_to` | `str` | `"screen"` | 相对屏幕或窗口客户区 |

```text
非执行调用说明（不可直接运行）：

browser.scroll_to(location="bottom", behavior="smooth")
browser.scroll_to(location="point", top=500, left=0)
element.scroll_to(location="bottom", behavior="instant", search_up=True)
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `location` | `str` | `"bottom"` | `"bottom"` / `"top"` / `"point"` / `"oneScreen"` |
| `behavior` | `str` | `"instant"` / 页面常见 `"smooth"` | 滚动效果 |
| `top` | `int` | `0` | 指定纵坐标 |
| `left` | `int` | `0` | 指定横坐标 |
| `search_up` | `bool` | `False` | 无滚动条时是否向上找可滚动父级 |

处理懒加载、无限滚动或内部滚动容器时，不能只执行滚动动作。至少要确认实际滚动对象是整页还是内部容器，并在每轮滚动后检查数据量是否增长、是否出现“查看更多”入口、是否已经到底以及结果是否需要去重。连续滚动后数据量不再变化时，应按当前业务规则结束或报错，不要无限滚动。

---

## 18. 执行 JavaScript

```python
result = browser.execute_javascript(
    """
    function (element, args) {
        return document.title;
    }
    """,
    argument=None,
    execution_world="ISOLATED",
)

result = element.execute_javascript(
    """
    function (element, args) {
        return element.innerText;
    }
    """,
    argument=None,
    execution_world="ISOLATED",
)
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `code` | `str` | 必填 | JS 函数字符串，必须是函数形式 |
| `argument` | `str` / `None` | `None` | 传给 JS 的参数，复杂对象建议转 JSON 字符串 |
| `execution_world` | `str` | `"ISOLATED"` | `"ISOLATED"` / `"MAIN"` |

注意：

- `execution_world` 建议按文档中的大写值传入，不要自行改成小写
- 需要隔离执行时优先用 `"ISOLATED"`
- 需要直接访问页面主环境对象时再考虑 `"MAIN"`

---

## 19. 网页弹窗

```text
非执行调用说明（不可直接运行）：

browser.handle_javascript_dialog("ok", text=None, wait_appear_timeout=20)
browser.handle_javascript_dialog("cancel", wait_appear_timeout=20)
text = browser.get_javascript_dialog_text(wait_appear_timeout=20)
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `dialog_result` | `str` | `"ok"` | `"ok"` / `"cancel"` |
| `text` | `str` / `None` | `None` | prompt 输入内容 |
| `wait_appear_timeout` | `int` / `float` | `20` | 等待弹窗出现 |

---

## 20. Cookie

```text
非执行调用说明（不可直接运行）：

cookies = web.get_cookies("https://example.com", mode="chrome")
cookie = web.get_cookie("https://example.com", mode="chrome", name="token")
web.set_cookie("https://example.com", mode="chrome", name="token", value="abc")
web.remove_cookie("https://example.com", "token", mode="chrome")
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `url` | `str` | 必填 | Cookie 对应网址 |
| `mode` | `str` | `"cef"` | 浏览器类型 |
| `name` | `str` / `None` | `None` | Cookie 名称 |
| `value` | `str` / `None` | `None` | Cookie 值 |
| `domain` | `str` / `None` | `None` | 域名 |
| `path` | `str` / `None` | `None` | 路径 |
| `secure` | `bool` / `None` | `None` | 是否 secure |
| `session` | `bool` / `None` | `None` | 是否会话 Cookie |
| `sessionCookie` | `bool` | `True` | `set_cookie` 中是否为会话 Cookie |
| `expires` | `int` | `100` | 持久化 Cookie 有效秒数 |
| `httpOnly` | `bool` | `False` | 是否 HttpOnly |

---

## 21. 上传和下载

```text
非执行调用说明（不可直接运行）：

web.handle_upload_dialog(
    filenames=[r"C:\test.txt"],
    dialog_result="ok",
    mode="chrome",
    simulative=False,
    clipboard_input=True,
    wait_appear_timeout=20,
)

file_path = web.handle_save_dialog(
    file_folder=r"C:\Downloads",
    dialog_result="ok",
    mode="chrome",
    file_name="demo.xlsx",
    overwrite=True,
    wait_complete=True,
    wait_complete_timeout=300,
)

element.upload(r"C:\test.txt")
file_path = element.download(r"C:\Downloads", file_name="result.xlsx", wait_complete=True)
file_path = browser.dowload_url(
    "https://example.com/demo.xlsx",
    r"C:\Downloads",
    file_name="demo.xlsx",
    overwrite=True,
    wait_complete=True,
)
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `filenames` | `str` / `list[str]` | 必填 | 单文件或多文件 |
| `dialog_result` | `str` | `"ok"` | `"ok"` / `"cancel"` |
| `file_folder` | `str` | 必填 | 保存目录 |
| `file_name` | `str` / `None` | `None` | 保存文件名 |
| `overwrite` | `bool` | `True` | 同名是否覆盖 |
| `wait_complete` | `bool` | `False` | 是否等待下载完成 |
| `wait_complete_timeout` | `int` / `float` | `300` | 下载完成超时 |

注意：方法名是 `dowload_url`，不是 `download_url`。

项目已安装“增强工具2026”时，下载文件后等待结果优先按 [增强工具 2026](extensions/xbot-enhance-tools.md) 使用 `wait_download_file()`；未安装时继续使用本节原生下载接口的 `wait_complete` / `wait_complete_timeout`，不要仅为复用示例新增市场指令依赖。

---

## 22. 截图

```text
非执行调用说明（不可直接运行）：

browser.screenshot(
    folder_path=r"C:\screenshots",
    file_name="page.png",
    full_size=True,
    piece_height=0,
    height=0,
)

path = element.screenshot(
    folder_path=r"C:\screenshots",
    filename="button.png",
)
```

| 参数 | 类型 | 默认值 |
|---|---|---|
| `folder_path` | `str` | 必填 |
| `file_name` / `filename` | `str` / `None` | `None` |
| `full_size` | `bool` | `True` |
| `piece_height` | `int` | `0` |
| `height` | `int` | `0` |

---

## 23. 网络监听和请求

```text
非执行调用说明（不可直接运行）：

# 开始监听必须放在触发页面请求之前；URL 不需要写完整，尽量用通配符提高命中率
browser.start_monitor_network(url="*client.action*", use_wildcard=True, resource_type="XHR|Fetch")

# 已在 start_monitor_network 里限定采集范围，直接读取当前监听结果
responses = browser.get_responses()
browser.stop_monitor_network()

result = browser.http_request(
    url="https://example.com/api/list",
    method="GET",
    headers={"token": "abc"},
    body=None,
    save_filename=None,
    connect_timeout=30,
    dowload_timeout=300,
)
```

`stop_monitor_network()` 和 `stop_load()` 的异常收尾方式遵守[项目开发规则](../../project-template/AGENTS.md)。

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `url` | `str` | `""` | 过滤请求 URL |
| `use_wildcard` | `bool` | `False` | 是否通配符匹配 |
| `resource_type` | `str` | `"All"` | `"All"` / `"XHR"` / `"Fetch"` / `"Script"` / `"Image"` 等 |
| `method` | `str` | `"GET"` | 请求方法 |
| `headers` | `dict` / `None` | `None` | 请求头 |
| `body` | 任意 / `None` | `None` | 请求体 |
| `save_filename` | `str` / `None` | `None` | 保存响应文件路径 |
| `connect_timeout` | `int` | `30` | 连接超时秒数 |
| `dowload_timeout` | `int` | `300` | 等待下载/响应超时秒数；源码拼写是 `dowload_timeout` |

`start_monitor_network()` / `get_responses()` 说明：

- 两个方法都支持 `url`、`use_wildcard`、`resource_type` 过滤；`resource_type` 可用 `|` 连接多个类型，例如 `"XHR|Fetch"`。
- 监听要在点击、刷新、滚动、加载更多等触发请求动作之前开启。
- 指定 URL 时优先使用通配符，例如 `url="*client.action*", use_wildcard=True`；不要强依赖完整 URL，避免查询参数或域名变化导致匹配不到。
- `start_monitor_network()` 用于确定本次采集范围。已经在开始监听时限定目标 URL 和资源类型时，后续直接调用 `get_responses()` 读取当前监听结果。
- 只有开始监听时有意保留较宽范围，并且读取阶段需要进一步划分结果时，才给 `get_responses()` 传入过滤参数。
- `get_responses()` 返回 `list[dict]`。单条记录常见键包括：`url`、`type`、`headers`、`body`、`base64Encoded`、`status`、`requestHeaders`、`requestBody`、`method`，读取方式如 `item["body"]`。
- `body` 的具体内容形态、非 JSON 响应和异常请求表现，仍建议以真实运行日志为准，需运行验证。

---

## 24. 拖拽

```text
非执行调用说明（不可直接运行）：

element.drag_to(top=100, left=0, simulative=True, move_speed="middle")
element.drag_to_by_cdp(targetX=500, targetY=300, targetType="viewport", move_speed="middle")
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `top` / `left` | `int` | `0` | 相对位移 |
| `targetX` / `targetY` | `int` | `0` | 目标坐标 |
| `targetType` | `str` | `"viewport"` | `"viewport"` / `"screen"` |
| `move_speed` | `str` | `"middle"` | `"instant"` / `"fast"` / `"middle"` / `"slow"` |

---

## 25. 自动处理弹窗和用户环境

```text
非执行调用说明（不可直接运行）：

web.auto_handle_popup(
    handle_method="close_dialog",
    close_button=close_button_selector,
)

web.auto_handle_popup(
    handle_method="execute_process",
    element_selector=target_selector,
    process="流程名",
    package=__name__,
)

web.set_user_environment(
    mode="chrome",
    profile_name="Profile 1",
    specifield_userdata=False,
    user_data_dir=None,
)
```

| 参数 | 可选值 | 说明 |
|---|---|---|
| `handle_method` | `"close_dialog"` / `"execute_process"` | 自动关闭弹窗 / 执行指定流程 |
| `close_button` | `Selector` | 关闭按钮选择器 |
| `element_selector` | `Selector` | 触发流程的目标元素 |
| `process` | `str` | 流程名，不要带 `.py` |
| `package` | `str` | 一般传 `__name__` |
| `mode` | `str` | 通常 `"chrome"` / `"edge"` |
| `profile_name` | `str` | 浏览器 Profile 名 |
| `specifield_userdata` | `bool` | 是否指定用户数据目录 |
| `user_data_dir` | `str` / `None` | `specifield_userdata=True` 时使用的用户数据目录 |

---

## 26. 排错速查

| 报错 / 现象 | 常见原因 | 处理 |
|---|---|---|
| `ChromiumBrowser` 没有 `wait_for_element` | 当前对象没有该方法，不代表 `get_active_page()` 入口不存在 | 单次等待用原生 `find_by_xpath(..., timeout=...)`；项目已有增强工具时再用其 XPath 等待能力 |
| `mode="Chrome"` 不稳定或报错 | 字符串大小写错误 | 改成 `mode="chrome"` |
| `download_url` 不存在 | 源码拼写是 `dowload_url` | 调用 `browser.dowload_url(...)` |
| `dowload_timeout` 拼写奇怪 | 源码就是这个拼写 | 按源码传 `dowload_timeout` |
| 元素匹配多个 | 单元素查找要求唯一 | 改选择器，或用 `find_all*` 后自己取 |
| 中文输入异常 | 输入法干扰 | 改用 `clipboard_input()` |
| 下载后文件还没生成 | 没等下载完成 | 先使用原生下载等待参数；项目已有增强工具时可按其事实页使用 `wait_download_file()` |
| `dialog_result="OK"` 不确定 | 源码注释是小写 `ok` / `cancel` | 建议传 `"ok"` / `"cancel"` |
