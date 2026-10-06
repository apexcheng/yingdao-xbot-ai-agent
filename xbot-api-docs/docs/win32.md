# 影刀 Windows 自动化方法

> 保留的 Python 片段依赖当前流程已取得的窗口、元素和已确认的定位值。片段不是独立脚本；[示例边界](../AGENTS.md)。

> 定位：影刀 / xbot 的 Windows 桌面自动化接口。
> 说明：本页整理 `xbot.win32` 模块常用公开方法，重点覆盖窗口、鼠标、键盘、锁屏、输入法相关能力。

---

## 1. 核验来源

本页按本机可见 ShadowBot 6.3.13 内置 `xbot/win32/__init__.py`、`window.py`、`element.py` 和 `image.py` 核对；与 6.3.12 对应源码哈希一致。安装目录随版本变化；其他版本用 `inspect.getfile(xbot.win32)` 定位当前实现，不复制固定绝对路径。

2026-10 复核 6.3.13 / 6.3.21 / 6.3.22 运行时 `Win32Element` 方法：`is_displayed()` / `is_enabled()` 不存在，已从本页移除；`get_bounding` / `get_anchor_position` 签名见 7.5，滚动容器可见性判断见 7.6，其中矩形包含写法已在真实桌面流程验证。

---

## 2. 使用范围说明

- 本页重点整理 **模块级公开方法**。
- `Win32Window`、`Win32Element`、`Image` 等对象的实例方法，若源码未在本次范围内确认，不在本页展开猜测。
- 对锁屏、RDP、CredentialProvider 等系统依赖，建议按源码条件判断；不确定时不要写成稳定事实。

---

## 3. 窗口查找

### 3.1 `get(title=None, class_name=None, use_wildcard=False, *, timeout=5)`

按标题或类名获取单个窗口。

| 参数名 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| `title` | `str` / `None` | 否 | 窗口标题 |
| `class_name` | `str` / `None` | 否 | 窗口类名 |
| `use_wildcard` | `bool` | 否 | 是否使用通配符匹配 |
| `timeout` | `int` / `float` | 否 | 超时时间，`0` 不等，`-1` 一直等 |

### 3.2 `get_list(title=None, *, use_wildcard=False, timeout=5)`

获取所有匹配窗口。

### 3.3 `get_by_handle(handle=None, *, timeout=5)`

按窗口句柄获取窗口。

### 3.4 `get_by_selector(selector=None, *, timeout=5)`

根据元素库中的窗口选择器名称获取窗口，返回 `Win32Window`。

当前存根明确：超时未找到窗口时抛出 `xbot.errors.UIAError`。需要把“窗口不存在”作为业务分支时，只捕获该异常，不要用裸 `except Exception` 把其它 Win32 / 引擎异常也误判成“窗口不存在”。

普通业务代码直接传窗口选择器名称字符串：

```python
window = win32.get_by_selector("ERP主窗口", timeout=10)
```

获取窗口后，通过窗口对象查找其内部元素。窗口和内部元素分别使用各自的元素库名称：

```text
非执行调用说明（不可直接运行）：

window = win32.get_by_selector("ERP主窗口", timeout=10)
query_button = window.find("按钮_查询", timeout=10)
query_button.click()
```

如果调用方只需要窗口对象，可以直接返回 `get_by_selector()` 的结果：

```python
def get_window(name, timeout):
    return win32.get_by_selector(name, timeout=timeout)
```

普通窗口和元素定位直接传元素库名称字符串，不需要调用 `package.selector()`；`package.selector()` 仅用于读取或处理选择器对象本身的元数据。

### 3.5 `get_by_element(element)`

由元素对象反查所属窗口。

### 3.6 `get_desktop(timeout=5)`

获取桌面窗口对象。

### 3.7 `get_active(timeout=5)`

获取当前激活窗口。

### 3.8 `exists(window) -> bool`

判断窗口对象是否仍然存在。

---

## 4. 鼠标与键盘

### 4.1 `manual_motion_on(...)` / `manual_motion_off()`

开启或关闭模拟真人操作。

- `motion_move`：随机路线和速度移动鼠标
- `motion_click`：随机位置点击
- `motion_delay`：操作间随机停顿
- `min_time` / `max_time`：随机停顿区间

### 4.2 `minimize_all()`

最小化全部窗口。

### 4.3 `mouse_move(point_x, point_y, relative_to='screen', move_speed='instant', delay_after=1)`

移动鼠标到指定位置。

- `relative_to`：`screen`、`window`、`position`。
- `move_speed`：`instant`、`fast`、`middle`、`slow`。

### 4.4 `mouse_move_by_anchor(rectangle, anchor=None, relative_to='screen', move_speed='instant', delay_after=1)`

按矩形范围和锚点移动鼠标。

### 4.5 `send_keys(keys='', send_key_delay=50, hardware_driver_input=False, delay_after=1, contains_hotkey=True, force_ime_eng=False)`

向当前激活窗口发送按键或文本。

**注意事项**：
- 特殊符号和快捷键输入要按源码约定处理。
- `force_ime_eng=True` 时会尝试切到英文输入。
- `hardware_driver_input=True` 只支持键盘可见字符，不用于 `Tab`、`Ctrl`、`Enter`、`Shift` 等特殊按键。
- `send_keys()` 发送给当前激活窗口，执行前必须确认目标窗口已激活、目标输入框已有焦点且没有弹窗遮挡；拿得到元素时优先使用元素级 `input()` / `clipboard_input()`。

### 4.6 `mouse_click(button='left', click_type='click', hardware_driver_click=False, keys='none', delay_after=1)`

鼠标点击。

- `button`：`left`、`right`。
- `click_type`：`click`、`dbclick`、`down`、`up`。
- `keys`：`none`、`alt`、`ctrl`、`shift`、`win`。

### 4.7 `mouse_click_by_anchor(rectangle, anchor=None, button='left', click_type='click', keys='none', hardware_driver_click=False, delay_after=1, move_mouse=True)`

按锚点和矩形范围点击。

### 4.8 `mouse_wheel(wheel_direction='down', wheel_times=1, keys='none', delay_after=1)`

鼠标滚轮滚动。

滚轮作用位置依赖当前鼠标所在区域。页面或软件存在内部滚动容器时，先把鼠标移到目标区域再滚动；否则 API 调用成功也可能滚动了错误容器。坐标类操作还会受系统缩放、分辨率、窗口位置和远程桌面状态影响。

### 4.9 `get_mouse_position(relative_to='screen') -> tuple`

获取鼠标当前位置。

### 4.10 `get_selected_text(wait_time=0, **kwargs) -> str`

获取当前激活窗口中选中的文本。

---

## 5. 屏幕与系统控制

### 5.1 `get_real_resolution()`

获取真实分辨率。

### 5.2 `get_screen_size()`

获取缩放后的分辨率。

### 5.3 `lock_screen()`

锁屏。

### 5.4 `rdp_lock_screen(user_name, password)`

通过 ShadowBotRDP 执行 RDP 锁屏。

**注意事项**：
- 当前目录需存在 `ShadowBotRDP.exe`。
- 用户名必须与当前登录用户匹配。
- 若返回码异常，源码会抛出对应 `EngineError`。

### 5.5 `unlock_screen(user_name, password)`

解锁屏幕。

**注意事项**：
- 依赖 CredentialProvider 安装文件。
- 需要先确认当前处于锁屏或远程状态。
- 若版本文件不存在或版本过低，会直接报错。

### 5.6 `is_os_64bit()`

判断系统是否为 64 位。

### 5.7 `set_ime(lang)`

设置激活窗口输入法。

| 参数名 | 类型 | 说明 |
|---|---|---|
| `lang` | `str` | 仅支持 `"chinese"` 或 `"english"` |

### 5.8 `get_ime() -> str`

获取激活窗口输入法状态。

返回值：`"chinese"` / `"english"` / `"unknow"`（源码拼写如此，未修正）。

---

## 6. Win32Window 常用方法

`xbot.win32.get()` / `get_active()` / `get_list()` 返回的都是 `Win32Window`。

| 方法 | 作用 |
|---|---|
| `get_detail(operation)` | 获取窗口标题、内容或进程名 |
| `activate()` | 激活窗口 |
| `set_state(flag)` | 设置窗口状态（隐藏、显示、最小化、最大化、还原） |
| `move(x=0, y=0)` | 移动窗口 |
| `resize(width=1, height=1)` | 调整窗口大小 |
| `close()` | 关闭窗口 |
| `is_active()` | 判断窗口是否激活 |
| `wait_active(timeout=20)` | 等待窗口激活 |
| `wait_close(timeout=20)` | 等待窗口关闭 |
| `find(selector, timeout=20)` | 查找单个元素 |
| `find_all(selector, timeout=20)` | 查找多个元素 |
| `wait_appear(selector_or_element, timeout=20)` | 等待元素出现 |
| `wait_disappear(selector_or_element, timeout=20)` | 等待元素消失 |

### 6.1 `get_detail(operation)`

获取窗口信息，常见 `operation`：

- `title`：窗口标题
- `text`：窗口内容
- `process_name`：进程名

### 6.2 `activate()`

激活窗口。

### 6.3 `set_state(flag)`

设置窗口状态：

- `hide`
- `show`
- `minimize`
- `maximize`
- `restore`

### 6.4 `move(x=0, y=0)` / `resize(width=1, height=1)`

移动或调整窗口大小。

### 6.5 `close()` / `is_active()` / `wait_active()` / `wait_close()`

关闭窗口、判断激活状态、等待激活、等待关闭。

窗口关闭及异常收尾统一遵守[项目开发规则](../../project-template/AGENTS.md)。

### 6.6 `find()` / `find_all()` / `wait_appear()` / `wait_disappear()`

在窗口内查找元素、等待元素出现或消失。

`Win32Window.find(selector, timeout=20)` 返回 `Win32Element`。普通业务代码直接传元素库选择器名称字符串。

推荐保留“先找窗口，再在窗口内找元素”的对象层级：

```text
非执行调用说明（不可直接运行）：

window = win32.get_by_selector("ERP主窗口", timeout=10)

query_btn = window.find("按钮_查询", timeout=10)
query_btn.click()

search_input = window.find("输入框_关键词", timeout=10)
search_input.input("影刀")
```

窗口选择器用于取得 `Win32Window`，元素选择器用于在该窗口中取得 `Win32Element`；两者分别使用各自的元素库名称。

### 6.7 推荐代码结构

Windows 自动化优先让代码直接对应真实操作路径：先获取真正要操作的业务窗口；只有业务窗口不存在时，才进入主程序并打开该业务窗口。

```text
非执行调用说明（不可直接运行）：

from xbot.errors import UIAError

try:
    target_window = win32.get_by_selector("目标业务窗口", timeout=2)
except UIAError:
    target_window = None

if not target_window:
    main_window = win32.get_by_selector("主程序窗口", timeout=10)
    main_window.find("进入业务窗口按钮", timeout=10).click()
    target_window = win32.get_by_selector("目标业务窗口", timeout=20)

target_window.find("搜索框", timeout=10).clipboard_input("关键词", append=False)
target_window.find("查询按钮", timeout=10).click()
```

这种结构重点表达三层语义：

1. 先复用目标业务窗口，不无条件启动或切换主程序。
2. 主程序只是目标窗口不存在时的兜底入口。
3. 获取目标窗口后，后续元素查找和操作都围绕该窗口对象展开。

元素只使用一次并立即执行操作时，可以直接链式调用：

```text
非执行调用说明（不可直接运行）：

window.find("输入框", timeout=10).clipboard_input(text, append=False)
window.find("查询按钮", timeout=10).click()
```

元素后续还需要读取、判断或重复使用时，保留变量：

```text
非执行调用说明（不可直接运行）：

result = window.find("结果文本", timeout=10)
if "成功" in str(result.get_text() or ""):
    result.click()
```

---

## 7. Win32Element 常用方法

`Win32Window.find()` / `find_all()` 返回的元素对象，常用方法包括：

| 方法 | 作用 |
|---|---|
| `click(button='left', simulative=True, keys='none', delay_after=1, move_mouse=True, anchor=None)` | 点击元素 |
| `dblclick(simulative=True, delay_after=1, move_mouse=True, anchor=None)` | 双击元素 |
| `input(text, simulative=True, append=False, contains_hotkey=False, send_key_delay=50, focus_timeout=1000, delay_after=1, click_before_input=True, anchor=None, force_ime_ENG=False)` | 输入文本 |
| `clipboard_input(text, append=False, focus_timeout=1000, delay_after=1, send_key_delay=50, click_before_input=True, anchor=None)` | 剪切板输入 |
| `hover(simulative=True, delay_after=1, anchor=None)` | 悬停 |
| `check(mode='check', delay_after=1)` | 复选框选中 / 取消 / 取反 |
| `select(item, mode='fuzzy', delay_after=1)` | 下拉框选择 |
| `find_related_element(selector, timeout=20)` | 查找当前元素内部的相关元素 |
| `get_text()` | 获取文本 |
| `get_value()` | 获取值 |
| `get_bounding(to96dpi=True, relative_to='screen')` | 获取元素矩形，返回 `(x, y, width, height)` |
| `get_anchor_position(anchor=None, to96dpi=True)` | 获取元素锚点坐标，默认中心点，返回 `(x, y)` |

### 7.1 点击与悬停

- `click(button='left', simulative=True, keys='none', delay_after=1, move_mouse=True, anchor=None)`
- `dblclick(simulative=True, delay_after=1, move_mouse=True, anchor=None)`
- `hover(simulative=True, delay_after=1, anchor=None)`

### 7.2 输入

- `input(text, simulative=True, append=False, contains_hotkey=False, send_key_delay=50, focus_timeout=1000, delay_after=1, click_before_input=True, anchor=None, force_ime_ENG=False)`
- `clipboard_input(text, append=False, focus_timeout=1000, delay_after=1, send_key_delay=50, click_before_input=True, anchor=None)`

### 7.3 状态与选择

- `check(mode='check', delay_after=1)`
- `select(item, mode='fuzzy', delay_after=1)`

### 7.4 相关元素

- `find_related_element(selector, timeout=20)`：在当前元素内部继续找子元素

### 7.5 位置与矩形

- `get_bounding(to96dpi=True, relative_to='screen') -> tuple`：返回元素矩形 `(x, y, width, height)`。
    - `relative_to`：`'screen'` 相对屏幕左上角（默认），`'window'` 相对元素所在窗口左上角。
    - `to96dpi`：是否把矩形转换为 96dpi 下的值，默认 `True`。比较两个元素的矩形时保持同一默认值即可，DPI 口径自动一致。
- `get_anchor_position(anchor=None, to96dpi=True) -> tuple`：返回元素锚点坐标 `(x, y)`，`anchor=None` 时默认取元素中心点。

以上签名与返回结构按 6.3.13 / 6.3.21 / 6.3.22 内置运行时源码核对一致。`Win32Element` **没有** `is_displayed()` / `is_enabled()` 方法（三个版本源码均无），不要照网页元素的习惯调用。

### 7.6 判断元素是否在滚动容器可见范围内

适用场景：元素能通过 `find()` 定位到，但位于滚动容器（表单、列表、面板）的可见范围之外；此时直接 `click()` 可能无效或点到错误位置，且不一定抛错。

可见性用矩形包含判断：把目标元素的 `get_bounding()` 矩形与滚动容器元素的矩形比较，不在范围内时先用容器元素 `hover()` 把鼠标移入滚动区域，再 `win32.mouse_wheel()` 滚动后重查，滚动次数要有上限：

```text
非执行调用说明（不可直接运行）：

window = win32.get_active()
element = window.find("目标元素", timeout=10)
container = window.find("滚动容器元素", timeout=10)

for _ in range(5):
    _, c_y, _, c_h = container.get_bounding()
    _, e_y, _, e_h = element.get_bounding()
    if c_y <= e_y and e_y + e_h <= c_y + c_h:
        break
    container.hover(delay_after=0.1)
    win32.mouse_wheel(wheel_direction="down", wheel_times=1, delay_after=0.2)
else:
    raise RuntimeError("滚动后仍看不到目标元素")
element.click(delay_after=0.1)
```

要点：

- 滚轮作用于鼠标当前位置（见 4.8），滚动前先 `hover()` 容器元素，避免滚动落到错误容器。
- 例子只比较纵向；横向溢出按同样方式扩展 x 轴比较。
- 该写法已在真实桌面流程中验证（2026-10，影刀 6.3.x）。矩形包含只能说明元素在容器可见范围内，不能保证没有被弹窗、遮罩或其他窗口覆盖；遮挡场景仍需结合实际页面状态处理。

---

## 8. Image 常用方法

`xbot.win32.image` 负责图像识别，常用公开能力包括：

| 方法 | 作用 |
|---|---|
| `wait_appear(image_selectors, wait_all=False, timeout=20)` | 等待图像在全屏出现 |
| `wait_appear_from_window(hWnd, image_selectors, wait_all=False, timeout=20)` | 等待图像在指定窗口出现 |
| `wait_disappear(image_selectors, wait_all=False, timeout=20)` | 等待图像在全屏消失 |
| `wait_disappear_from_window(hWnd, image_selectors, wait_all=False, timeout=20)` | 等待图像在指定窗口消失 |
| `hover(image_selectors, anchor=None, timeout=5, delay_after=1)` | 全屏悬停到图像 |
| `hover_on_window(hWnd, image_selectors, anchor=None, timeout=5, delay_after=1)` | 指定窗口内悬停到图像 |
| `click(image_selectors, anchor=None, button='left', keys='none', move_mouse=True, timeout=5, delay_after=1)` | 全屏点击图像 |
| `click_on_window(hWnd, image_selectors, anchor=None, button='left', keys='none', move_mouse=True, timeout=5, delay_after=1)` | 指定窗口内点击图像 |
| `dblclick(image_selectors, anchor=None, move_mouse=True, timeout=5, delay_after=1)` | 全屏双击图像 |
| `dblclick_on_window(hWnd, image_selectors, anchor=None, move_mouse=True, timeout=5, delay_after=1)` | 指定窗口内双击图像 |

### 注意事项

- 图像选择器可来自 `package.image_selector()`。
- 当前已有网页元素/桌面元素时，优先用元素，不优先图像。

---

## 9. 常用建议

- 已有窗口元素库名称时使用 `get_by_selector()`；只有目标由标题、类名或当前激活状态确定时才使用 `get()` / `get_active()`，不要猜句柄。
- 需要模拟人工操作时，再开启 `manual_motion_on()`。
- 锁屏和解锁相关方法有明显系统依赖，建议先运行验证再写入正式流程。
