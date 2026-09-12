# iframe2 扩展指令说明

> 保留的 Python 片段依赖当前流程已取得的对象、输入数据和项目已确认的参数。片段不是独立脚本；[示例边界](../AGENTS.md)。

> 来源目录：`xbot_extensions/iframe2`
> 当前核验版本：市场指令「XPath跨域获取网页元素」`25.12.0`，`activity_code=iframe2`
> 结论依据：实际项目中的市场指令副本 `package.json`、`prototype.block.json`、`__init__.py`、`api.py`、各 Visual 包装流程和 `_core.py`
> 最近核验：2026-09-11

---

## 1. 定位

`iframe2` 是一个面向跨 `iframe` / `frame` 场景的**市场扩展指令集**，不是原生 `xbot.web` API。

当前安装的原生 `xbot.web` 源码虽然会导入内部辅助函数 `is_cross_frame_element`，但这只是 selector 内部能力，不能据此推断存在公开的 `switch_to_frame()`、`frame_locator()` 或同类 iframe API。需要按 XPath 跨 iframe 查找时，应以本市场指令的公开入口为准。

它的核心能力是：

- 用 `IframePage` 保存「原始 `web_page` + 当前 iframe 上下文 + selector path」
- 在当前 document / iframe 中执行 XPath，再把得到的元素路径转换成影刀 selector，最终仍通过原生 `web_page.find(...)` 取得真实 `WebElement`
- 按 XPath 切换 iframe、查找元素、点击、输入、等待、读取文本或属性
- 编码版直接调用 `xbot_extensions.iframe2.api`；除 `init_iframe()` 外的主要 API 都会自动把普通 `web_page` 包装成 `IframePage`

它适合这些场景：

- 原生元素库不方便直接覆盖多层 iframe
- 页面结构变化不大，但需要按 XPath 精确切入某一层 iframe
- 已有 `web_page`，希望继续用 `xbot.web` / `WebElement` 能力完成后续操作

因此编码版的默认用法不是“必须先初始化 IFrame”，而是**能直接传 `web_page` 就直接传**；只有需要先切入某个 iframe，并在后续多次操作里复用这个上下文时，才保存 `to_iframe()` 返回的 `iframe_instance`。

Shadow Root、隐藏块和不同浏览器下的真实稳定性仍需按具体项目运行验证，不要直接当成稳定结论。

---

## 2. 调用方式

### 2.1 可视化指令入口

| 分组 | 指令名 | function | 主要出参 |
|---|---|---|---|
| A0 | `A0-初始化IFrame` | `xbot_extensions.iframe2.init_iframe` | `iframe_instance` |
| A1 | `A1-切换IFrame` | `xbot_extensions.iframe2.to_iframe` | `new_iframe_instance` |
| B1 | `B1-获取元素对象` | `xbot_extensions.iframe2.find_ele` | `web_element` |
| B2 | `B2-获取相似元素` | `xbot_extensions.iframe2.find_all_ele` | `web_element_list` |
| C1 | `C1-点击元素` | `xbot_extensions.iframe2.click_by_xpath` | — |
| C2 | `C2-填写输入框` | `xbot_extensions.iframe2.input_by_xpath` | — |
| C3 | `C3-等待元素` | `xbot_extensions.iframe2.wait_by_xpath` | `wait_result` |
| D1 | `D1-获取元素信息` | `xbot_extensions.iframe2.process2` | `attribute` |
| D2 | `D2-获取元素属性` | `xbot_extensions.iframe2.process3` | `attribute` |

说明：

- `A2-切换至父IFrame` 在 `prototype.block.json` 中存在，但 `hidden=true`，不作为当前稳定公开入口。
- `main`、`_core`、`api`、`js_code`、`测试` 这些 flow 也存在，但不是面向业务开发的主要指令入口。

### 2.2 Python 直接调用入口

编码版推荐直接调用 `xbot_extensions.iframe2.api`，不要绕过到 `_core.py`。

当前 `api.py` 的调用契约：

| 方法 | 主要参数 | 返回值 | 说明 |
|---|---|---|---|
| `init_iframe(web_page)` | `web_page` | `IframePage` | 仅做包装；编码版通常可省略 |
| `to_iframe(...)` | `iframe_instance`, `iframe_xpath`, `current_global`, `timeout` | `IframePage` | 切入目标 iframe |
| `find_ele(...)` | `iframe_instance`, `xpath`, `current_global`, `timeout` | `WebElement` | 找唯一元素 |
| `find_all_ele(...)` | `iframe_instance`, `xpath`, `current_global=False`, `timeout=10` | `list[WebElement]` | 找相似元素 |
| `click_by_xpath(...)` | 见下文 | `None` | 查找后点击 |
| `input_by_xpath(...)` | 见下文 | `None` | 查找后输入 |
| `wait(...)` | `iframe_instance`, `xpath`, `state="appear"`, `current_global=False`, `timeout=20` | `bool` | 等待出现 / 消失 |
| `get_elem_info(...)` | `iframe_instance`, `xpath`, `op`, `attr_name=None`, `current_global=False`, `timeout=20` | 取决于 `op` | 读取文本 / HTML / value / 位置 / 属性 |

源码声明签名如下；`*` 后面的参数都是关键字参数：

```text
init_iframe(web_page)
to_iframe(*, iframe_instance, iframe_xpath, current_global, timeout)
find_ele(*, iframe_instance, xpath, current_global, timeout)
find_all_ele(*, iframe_instance, xpath, current_global=False, timeout=10)
click_by_xpath(*, iframe_instance, xpath, current_global=False, button="left", simulative=True, keys="none", move_mouse=False, clicks="单击", delay_after=1, timeout=5)
input_by_xpath(*, iframe_instance, xpath, text, current_global=False, simulative=True, append=False, contains_hotkey=False, force_ime_ENG=False, send_key_delay=50, focus_timeout=1000, delay_after=1, click_before_input=True, timeout=5)
wait(*, iframe_instance, xpath, state="appear", current_global=False, timeout=20)
get_elem_info(*, iframe_instance, xpath, op, attr_name=None, current_global=False, timeout=20)
```

除 `init_iframe()` 外，公开函数都通过 `@check_obj` 读取关键字参数 `iframe_instance`。编码版应统一使用**关键字参数**调用，不要依赖位置参数。

该装饰器没有使用 `functools.wraps` 保留原函数签名，因此某些运行环境里直接 `inspect.signature()` 可能只能看到包装层的 `(*args, **kwargs)`；遇到这种情况应以当前版本 `api.py` 的公开函数声明和 Visual 包装参数为准。

`api.py` 还暴露了 `parent(iframe_instance)`，但当前 `25.12.0` 的 `_core.IframePage` 并没有实现 `parent()`；对应 Visual block 也为 `hidden=true`。因此当前版本不要把“切换至父 IFrame”当作可用稳定接口。

---

## 3. 参数规律

### 3.1 通用入参

| 源码名 | 可视化含义 | 说明 |
|---|---|---|
| `web_page` | 网页对象 | 仅初始化时使用 |
| `iframe_instance` | IFrame 上下文 | 可以直接传原生 `web_page`；`check_obj` 会自动包装成 `IframePage` |
| `iframe_xpath` / `xpath` | XPath / IFrame_XPath | 支持单个 XPath，也支持数组形式逐层切入 |
| `current_global` | 基于当前 IFrame 全局查找 | `True` 时会遍历当前 iframe 树做全局查找 |
| `timeout` | 超时时间 | `to_iframe` / 查找 / 点击 / 输入默认单位是秒 |

`IframePage` 不是原生 `WebBrowser` 子类。市场指令内部会把原始 `web_page` 的方法反射到包装对象上，因此使用体验很像网页对象，但文档和业务代码不要把两者当成同一种类型。

### 3.2 XPath 数组规则

- `find_ele()` / `find_all_ele()` 传 `list`：前面的每一段都是 iframe XPath，最后一段是目标元素 XPath。
- `to_iframe()` 传 `list`：**数组中的每一段都是 iframe XPath**，最后一段仍然是要切入的 iframe，不是普通目标元素。
- 传数组时内部固定按层级精确切入，不走 `current_global=True` 的全局遍历逻辑。

查找元素时可理解为：

```python
[
    '//iframe[@id="outer"]',
    '//iframe[@id="inner"]',
    '//button[contains(., "查询")]',
]
```

切换多层 iframe 时则是：

```python
[
    '//iframe[@id="outer"]',
    '//iframe[@id="inner"]',
]
```

### 3.3 `current_global` 的真实语义

`current_global=True` 不是“拿第一个匹配项”。底层会从当前 `IframePage` 开始递归遍历 `iframe` / `frame` 树：

- `find_ele()`：要求最终只能在一个 iframe 上得到唯一目标；多个 iframe 都命中时会报“无法唯一确定”。
- `find_all_ele()`：允许在**同一个 iframe**中得到多个相似元素；如果多个 iframe 都各自存在匹配结果，会报“在多个iframe中找到相似元素，无法唯一确定”。
- 已知明确层级时，优先传 XPath 数组，比全局遍历更确定。

### 3.4 点击与输入的关键枚举

`click_by_xpath()`：

- `clicks` / `点击方式`：`"单击"`、`"双击"`
- `button` / `鼠标按键`：`"left"`、`"right"`
- `keys` / `辅助按键`：`"none"`、`"alt"`、`"ctrl"`、`"shift"`、`"win"`

`input_by_xpath()`：

- `simulative` / `输入方式` 在可视化层实际有 3 种：
  - `模拟人工输入`
  - `剪贴板输入`
  - `自动化接口输入`
- `append`：是否追加输入
- `contains_hotkey`：输入内容是否包含快捷键
- `force_ime_ENG`：是否强制加载美式键盘
- `send_key_delay`、`focus_timeout`：单位是毫秒
- `delay_after`：单位是秒
- `click_before_input`：输入前是否先点击元素

这里有一个容易踩坑的实现细节：编码版要选择“自动化接口输入”，必须传 `simulative="自动化接口输入"`。传 Python 布尔值 `False` 不会等价于自动化接口输入，底层反而会落到模拟人工输入分支。

### 3.5 超时与等待规则

Direct Python 与 Visual 默认值并不完全一致：

| 能力 | Direct Python | Visual 默认值 |
|---|---:|---:|
| `to_iframe` | `timeout` 必传 | `5` 秒 |
| `find_ele` | `timeout` 必传 | `5` 秒 |
| `find_all_ele` | `10` 秒 | `5` 秒 |
| `click_by_xpath` | `5` 秒 | `5` 秒 |
| `input_by_xpath` | `5` 秒 | `5` 秒 |
| `wait` | `20` 秒 | 空值，表示一直等待 |
| `get_elem_info` | `20` 秒 | D1 / D2 为 `5` 秒 |

普通查找路径会把 `timeout` 转成 `int`，业务代码优先传整数秒。

`wait()` / `C3-等待元素`：

- `state` / `等待状态` 只写两种稳定枚举：
  - `appear`
  - `disappear`
- 返回值是 `bool`
- `timeout=""` 或 `None` 时，底层会按无限等待处理

### 3.6 读取元素信息规则

`get_elem_info()` / `D1-获取元素信息` 当前映射到这些操作：

- `获取元素文本内容` -> `get_text()`
- `获取元素源代码` -> `get_html()`
- `获取元素值` -> `get_value()`
- `获取元素位置` -> `get_bounding()`

`D2-获取元素属性` 本质上也是查到元素后调用 `get_attribute(attr_name)`。

Direct Python 的 `get_elem_info()` 本身也接受 `op="获取元素属性"` + `attr_name=...`；只是 Visual 层把“获取元素信息”和“获取元素属性”拆成了 D1 / D2 两个 block。

---

## 4. 最小示例

### 4.1 编码版：直接从 `web_page` 查跨 iframe 元素

```python
from xbot_extensions.iframe2.api import find_ele

element = find_ele(
    iframe_instance=web_page,
    xpath='//button[contains(., "查询")]',
    current_global=True,
    timeout=5,
)
```

这是编码版最短路径：`find_ele()` 会自动把 `web_page` 包装成 `IframePage`。

### 4.2 先切入 iframe，再复用当前上下文

```python
from xbot_extensions.iframe2.api import to_iframe, find_ele

detail_iframe = to_iframe(
    iframe_instance=web_page,
    iframe_xpath='//iframe[@id="detail-frame"]',
    current_global=True,
    timeout=5,
)

element = find_ele(
    iframe_instance=detail_iframe,
    xpath='//button[contains(., "保存")]',
    current_global=False,
    timeout=5,
)
```

### 4.3 按数组 XPath 精确切入多层 iframe 后查元素

```text
非执行调用说明（不可直接运行）：

from xbot_extensions.iframe2.api import find_ele

submit_btn = find_ele(
    iframe_instance=web_page,
    xpath=[
        '//iframe[@id="outer"]',
        '//iframe[@id="inner"]',
        '//button[contains(., "提交")]',
    ],
    current_global=False,
    timeout=5,
)
submit_btn.click()
```

### 4.4 跨 iframe 点击

```text
非执行调用说明（不可直接运行）：

from xbot_extensions.iframe2.api import click_by_xpath

click_by_xpath(
    iframe_instance=web_page,
    xpath='//button[contains(., "查询")]',
    current_global=True,
    simulative=True,
    move_mouse=False,
    button='left',
    keys='none',
    clicks='单击',
    delay_after=1,
    timeout=5,
)
```

### 4.5 跨 iframe 输入

```text
非执行调用说明（不可直接运行）：

from xbot_extensions.iframe2.api import input_by_xpath

input_by_xpath(
    iframe_instance=web_page,
    xpath='//input[@placeholder="请输入关键词"]',
    text='影刀',
    current_global=True,
    simulative='剪贴板输入',
    append=False,
    contains_hotkey=False,
    force_ime_ENG=False,
    send_key_delay=50,
    focus_timeout=1000,
    delay_after=1,
    click_before_input=True,
    timeout=5,
)
```

### 4.6 等待元素出现 / 消失

```python
from xbot_extensions.iframe2.api import wait

ok = wait(
    iframe_instance=web_page,
    xpath='//div[@class="loading-mask"]',
    state='disappear',
    current_global=True,
    timeout=20,
)
if not ok:
    raise RuntimeError("loading 未消失")
```

### 4.7 读取文本和属性

```python
from xbot_extensions.iframe2.api import get_elem_info

text = get_elem_info(
    iframe_instance=web_page,
    xpath='//span[@class="shop-name"]',
    op='获取元素文本内容',
    current_global=True,
    timeout=5,
)

placeholder = get_elem_info(
    iframe_instance=web_page,
    xpath='//input[@name="keyword"]',
    op='获取元素属性',
    attr_name='placeholder',
    current_global=True,
    timeout=5,
)
```

---

## 5. 注意事项

- 这是市场指令 `iframe2`，不是原生 `xbot.web` 的 iframe API。
- 编码版通常直接把 `web_page` 传给 `find_ele()` / `find_all_ele()` / `click_by_xpath()` 等，不需要为了“初始化”单独调用一次 `init_iframe()`。
- `current_global=True` 会遍历当前 iframe 树；多个 iframe 同时命中时不是任选一个，而是报无法唯一确定。
- 多层 iframe 路径已知时优先传 XPath 数组；`find_*` 的最后一段是目标元素，而 `to_iframe()` 的最后一段仍是 iframe。
- `find_ele()` 返回的是影刀原生 `WebElement`，后续可以继续调用 `.click()`、`.get_text()`、`.get_attribute()` 等原生元素方法。
- `wait()` 的返回值是布尔值，不直接返回元素对象。
- `input_by_xpath()` 要使用自动化接口输入时传字符串 `"自动化接口输入"`，不要用 `False` 代替；非剪贴板输入分支还会尝试额外触发一次 `input` 事件。
- `A2-切换至父IFrame` 当前版本不要使用：Visual block 已隐藏，而且 `IframePage` 没有对应 `parent()` 实现。
- 本文只沉淀源码已确认的接口行为；Shadow Root 路径、浏览器兼容性、页面未完全加载时的真实重试表现，仍需运行验证。

---

## 6. 关联文档

- [市场指令入口与签名核验](extension-instructions.md)
