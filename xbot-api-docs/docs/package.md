# 影刀基础对象与全局变量

> 保留的 Python 片段依赖当前影刀项目的 `package`，资源名、变量名和对象由项目确认。片段不是独立脚本；[示例边界](../AGENTS.md)。

> 定位：影刀 RPA Python 编码版里的 `package` 运行时辅助对象。
> 说明：以下内容结合官方接口文档笔记整理，当前仓库未直接提取到 `package` 源码实现；若客户端版本不一致，以影刀客户端内置提示或官方文档为准。

---

## 1. 作用

`package` 主要用于访问当前应用中的：

- 图像库选择器
- 资源文件
- 全局变量

常见写法：

```python
from . import package
```

---

## 2. `package.image_selector(name)`

### 作用

按图像库名称获取图像选择器。

### 常用场景

- 等待图像出现
- 点击图像
- 校验图像是否存在

### 示例

```python
from . import package

logo = package.image_selector("登录成功标志")
```

### Agent 常见场景

```python
from . import package

captcha_image = package.image_selector("验证码区域")
success_logo = package.image_selector("登录成功标记")
```

### 注意事项

- 配合 `xbot.win32.image` 图像识别 API 使用，不要把图片选择器传给 `Win32Window.find()`。
- 图像选择器的稳定性依赖截图质量和页面状态。
- 图像选择器更适合兜底，不要优先替代能稳定定位的网页元素。

---

## 3. `package.resources`

### 作用

访问应用资源文件。

本页按本机可见 ShadowBot 6.3.13 内置 `xbot/primitives.py` 的 `ResourceReader` 公开方法核对；与 6.3.12 对应源码哈希一致。安装目录随版本变化，不固定绝对路径，也不推断未确认行为。

### 常用场景

- 读取模板 Excel
- 读取配置文件
- 读取图片或临时数据文件

### 当前可见方法

- `get_path(filename) -> str`：获取资源文件路径
- `get_text(filename, encoding='utf-8') -> str`：读取资源文件文本内容
- `get_bytes(filename) -> bytes`：读取资源文件二进制内容
- `copy_to(filename, dest_filename)`：复制资源文件到指定路径
- `copy_to_clipboard(filenames)`：将资源文件加入剪贴板

### `get_path()`

```python
from . import package

file_path = package.resources.get_path("模板.xlsx")
```

### `get_text()`

```python
from . import package

config_text = package.resources.get_text("config.json")
```

### `get_bytes()`

```python
from . import package

logo_bytes = package.resources.get_bytes("logo.png")
```

### `copy_to()`

```text
非执行调用说明（不可直接运行）：

from . import package

package.resources.copy_to("模板.xlsx", r"D:\temp\模板.xlsx")
```

### `copy_to_clipboard()`

```text
非执行调用说明（不可直接运行）：

from . import package

package.resources.copy_to_clipboard(["模板.xlsx", "logo.png"])
```

### 典型场景

- Excel 模板路径传给 `xbot.excel.open()`
- 配置文件文本内容传给 JSON / 文本读取逻辑
- 图片二进制内容或路径传给上传、比对或通知逻辑

### 注意事项

- `package.resources` 更适合读“跟项目一起打包”的固定文件，不适合存运行时动态生成内容。
- 当前知识库以本机可见 `ResourceReader` 方法为准，`package.resources["xxx"]` 不应再作为可用写法保留。
- 当前可见源码没有确认 `package.resources` 支持下标访问，不要把它当成字典使用。
- 若运行结果与当前版本不一致，以当前版本实际行为为准。

---

## 4. `package.variables`

### 作用

读写影刀应用运行时的全局变量。

### 常用场景

- 保存浏览器对象
- 保存账号、店铺、任务状态
- 在多个流程间传递数据
- 存储密钥、凭证等敏感配置

### 示例

```text
非执行调用说明（不可直接运行）：

from . import package

package.variables["web_page"] = browser
web_page = package.variables["web_page"]
```

### Agent 最常见用法

#### 1. 保存网页对象供后续流程继续使用

```text
非执行调用说明（不可直接运行）：

from . import package

package.variables["web_page"] = browser
web_page = package.variables["web_page"]
```

#### 2. 读取账号、店铺、时间范围等运行参数

```python
from . import package

shop_name = package.variables["shop_name"]
start_date = package.variables["start_date"]
end_date = package.variables["end_date"]
```

#### 3. 读取接口凭证或配置

```python
from . import package

app_key = package.variables["APP_KEY"]
session_key = package.variables["SESSION_KEY"]
secret = package.variables["SECRET"]
```

#### 4. 回写流程结果

```text
非执行调用说明（不可直接运行）：

from . import package

package.variables["collect_status"] = "success"
package.variables["collect_count"] = 20
```

### 注意事项

- 使用前要在影刀编辑器中先创建对应变量名。
- 脚本结束后变量通常不会长期保留。
- 敏感信息优先放到全局变量，不建议硬编码。
- 读变量前，先确认变量名是否由当前项目约定好，不要凭感觉新造名字。
- 浏览器对象、列表、字典等运行时对象可以放进去，但前提是后续流程确实会继续消费这些对象。
- 确需用 `package.variables` 保存任务级缓存时，在每轮任务开始时显式初始化或清空该缓存，避免复用上一轮结果；不要清空其他流程仍需使用的全局变量。
- 任务级缓存只保存本轮可复用的页面数据、接口响应或解析结果；账号密码、Token、Cookie 等由项目既有凭证配置管理，不复制到业务缓存中。

---

## 5. 组合用法

### 5.1 元素库 + 全局变量

```text
非执行调用说明（不可直接运行）：

from . import package

web_page = package.variables["web_page"]

web_page.wait_load_completed(timeout=30)
query_btn = web_page.find("按钮_查询", timeout=10)
query_btn.click()
```

### 5.2 资源文件 + 全局变量

```text
非执行调用说明（不可直接运行）：

from . import package

template_file = package.resources.get_path("模板.xlsx")
package.variables["template_file"] = template_file
```

## 6. 低频：显式获取 `Selector` 对象

普通 Win32 / Web / Mobile 元素定位直接把元素库名称传给对应原生 API，不需要显式获取 `Selector` 对象。

调用的 API 要求传入 Selector 对象时，使用 `package.selector(name)` 从元素库名称获取对象；需要读取选择器元数据时也使用此方法。例如，广告杀手 `close_ads_win()` 要求 Win32 Selector 对象列表，详见[广告杀手事实页](extensions/ad-killer.md)：

```python
from . import package

selector = package.selector("目标元素")
framework = selector.framework()
xpath = selector.xpath()
```
