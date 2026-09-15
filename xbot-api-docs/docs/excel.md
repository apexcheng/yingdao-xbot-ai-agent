# 影刀表格操作方法整理

> 保留的 Python 片段依赖当前流程已取得的 `workbook`、`sheet` 或待处理数据，Sheet 名和区域由项目确认。片段不是独立脚本；[示例边界](../AGENTS.md)。

> 定位：影刀 / xbot 操作 Excel 的开发者参数手册。  
> 重点：用户写代码时看不到源码，所以本文尽量把**参数名、默认值、可选值、大小写、传参示例**写清楚。  
> 规则：字符串参数必须按文档中的值原样传入，例如 `kind="wps"`，不是 `WPS`，也不是 `PWS`。

---

## 1. 核验来源

本页按本机可见 ShadowBot 6.3.13 内置 `xbot/excel/` 与 `xbot_visual/excel.py` 核对；与 6.3.12 对应源码哈希一致。安装目录随版本变化；其他版本用 `inspect.getfile(xbot.excel)` 定位当前实现。基础对象见 [`package.md`](package.md)。

---

新增影刀 Excel / WPS 操作默认优先使用 `xbot.excel`。涉及公式刷新、界面交互、宏、格式或文件占用时，不为了图快改用其他后台读写库；项目已有稳定实现路线时遵守[项目开发规则](../../project-template/AGENTS.md)。真实 Office / WPS 行为需要对应环境运行证据，静态检查不能代替。

## 2. 参数传值总规则

### 2.1 字符串可选值区分大小写

正确：

```python
kind="wps"
kind="office"
kind="openpyxl"
```

错误：

```python
kind="WPS"      # 错
kind="PWS"      # 错
kind="Office"   # 错
kind="OPENPYXL" # 错
```

### 2.2 布尔值必须传 Python 布尔值

正确：

```python
visible=True
ignore_formula=False
update_links=False
```

不建议：

```python
visible="True"   # 字符串，不建议
visible="False"  # 字符串，不建议
```

### 2.3 路径建议使用原始字符串

```python
file_name = r"C:\path\demo.xlsx"
```

或者使用双反斜杠：

```python
file_name = "C:\\path\\demo.xlsx"
```

---

## 3. Excel 驱动类型 `kind`

`kind` 是最容易传错的参数，必须使用下面这些**小写字符串**：

| 传参值 | 正确写法 | 说明 | 常见错误 |
|---|---|---|---|
| Office | `kind="office"` | 使用 Microsoft Excel / Office | `"Office"`、`"OFFICE"` |
| WPS | `kind="wps"` | 使用 WPS 表格 | `"WPS"`、`"pws"`、`"PWS"` |
| OpenPyXL | `kind="openpyxl"` | 后台读写 `.xlsx`，不打开界面 | `"openPyXL"`、`"OpenPyxl"` |
| 自动检查 | `kind="auto_check"` | 优先 Office，失败再尝试 WPS | `"auto"`、`"autoCheck"` |
| WPS 插件 | `kind="wps_addon"` | WPS 插件方式 | `"wpsAddon"`、`"wps-addon"` |

推荐选择：

| 场景 | 推荐 |
|---|---|
| 只读写 `.xlsx`，不需要界面 | `kind="openpyxl"` |
| 需要宏、公式刷新、复制粘贴、真实 Excel 行为 | `kind="office"` |
| 公司电脑主要装 WPS | `kind="wps"` |
| 不确定装了 Office 还是 WPS | `kind="auto_check"` |

---

## 4. 创建 Excel：`xbot.excel.create()`

### 4.1 方法签名

```text
非执行调用说明（不可直接运行）：

workbook = xbot.excel.create(
    kind="office",
    visible=True,
    original_file="",
)
```

### 4.2 参数说明

| 参数 | 类型 | 必填 | 默认值 | 可选值 | 说明 |
|---|---|---:|---|---|---|
| `kind` | `str` | 否 | `"office"` | `"office"` / `"wps"` / `"openpyxl"` / `"auto_check"` / `"wps_addon"` | 创建方式，必须小写 |
| `visible` | `bool` | 否 | `True` | `True` / `False` | 是否显示 Excel/WPS 窗口；主要对 `office`、`wps` 有效 |
| `original_file` | `str` | 否 | `""` | 文件路径字符串 | 原始文件路径；通常可不传 |

### 4.3 示例

```text
非执行调用说明（不可直接运行）：

import xbot.excel

# 用 Office 新建
workbook = xbot.excel.create(kind="office", visible=True)

# 用 WPS 新建
workbook = xbot.excel.create(kind="wps", visible=True)

# 用 openpyxl 后台新建
workbook = xbot.excel.create(kind="openpyxl")
```

---

## 5. 打开 Excel：`xbot.excel.open()`

### 5.1 方法签名

```text
非执行调用说明（不可直接运行）：

workbook = xbot.excel.open(
    file_name=r"C:\path\demo.xlsx",
    kind="office",
    visible=True,
    password="",
    write_password="",
    ignore_formula=False,
    update_links=False,
)
```

### 5.2 参数说明

| 参数 | 类型 | 必填 | 默认值 | 可选值 | 说明 |
|---|---|---:|---|---|---|
| `file_name` | `str` | 是 | 无 | Excel 文件路径 | 要打开的文件路径 |
| `kind` | `str` | 否 | `"office"` | `"office"` / `"wps"` / `"openpyxl"` / `"auto_check"` / `"wps_addon"` | 打开方式，必须小写 |
| `visible` | `bool` | 否 | `True` | `True` / `False` | 是否显示窗口；主要对 `office`、`wps` 有效 |
| `password` | `str` | 否 | `""` | 密码字符串 | 打开密码；主要对 `office`、`wps` 有效 |
| `write_password` | `str` | 否 | `""` | 密码字符串 | 编辑密码；主要对 `office`、`wps` 有效 |
| `ignore_formula` | `bool` | 否 | `False` | `True` / `False` | `openpyxl` 下会传给 `data_only`；`True` 倾向读取公式结果，`False` 倾向保留公式 |
| `update_links` | `bool` | 否 | `False` | `True` / `False` | 是否更新外部链接；主要对 `office`、`wps` 有效 |

### 5.3 正确示例

```text
非执行调用说明（不可直接运行）：

import xbot.excel

# Office 打开
workbook = xbot.excel.open(
    file_name=r"C:\path\demo.xlsx",
    kind="office",
    visible=False,
)

# WPS 打开：注意是小写 wps
workbook = xbot.excel.open(
    file_name=r"C:\path\demo.xlsx",
    kind="wps",
    visible=True,
)

# openpyxl 后台打开
workbook = xbot.excel.open(
    file_name=r"C:\path\demo.xlsx",
    kind="openpyxl",
    ignore_formula=True,
)
```

### 5.4 常见错误

```python
kind="WPS"       # 错，应该是 kind="wps"
kind="PWS"       # 错，拼写错误
kind="xlsx"      # 错，kind 不是文件类型
visible="False"  # 不建议，应该用 visible=False
```

---

## 6. 获取当前工作簿：`xbot.excel.get_active_workbook()`

```python
workbook = xbot.excel.get_active_workbook()
```

| 参数 | 说明 |
|---|---|
| 无 | 获取当前激活的 Excel / WPS 工作簿 |

注意：当前无法从参数里指定 `kind`，源码会按运行环境尝试获取当前激活工作簿。

---

## 7. 关闭 Excel 进程：`xbot.excel.kill_excel_process()`

```text
非执行调用说明（不可直接运行）：

xbot.excel.kill_excel_process("office", False)
xbot.excel.kill_excel_process("wps", True)
```

`xbot.excel.kill_excel_process()` 直接调用即可，不需要为了关闭进程单独套 `try / except`。

| 参数 | 类型 | 必填 | 可选值 | 说明 |
|---|---|---:|---|---|
| `close_process` | `str` | 是 | `"office"` / `"wps"` | 关闭 Office Excel 或 WPS 表格进程，必须小写 |
| `kill_task` | `bool` | 是 | `True` / `False` | 是否强制结束进程 |

---

## 8. 工作簿常用方法

### 8.1 保存 / 另存 / 关闭

```text
非执行调用说明（不可直接运行）：

workbook.save()
workbook.save_as(r"C:\path\new.xlsx")
workbook.close()
file_path = workbook.get_full_name()
```

| 方法 | 参数 | 说明 |
|---|---|---|
| `save()` | 无 | 保存当前文件 |
| `save_as(filename)` | `filename: str` | 另存为指定路径 |
| `close()` | 无 | 关闭工作簿 |
| `is_closed()` | 无 | 判断工作簿对象是否已关闭 |
| `set_saved(True)` | `True` / `False` | 标记保存状态；常用于不保存关闭 |

工作簿关闭及异常收尾统一遵守[项目开发规则](../../project-template/AGENTS.md)。以下为读取后关闭工作簿的非执行调用说明：

```text
非执行调用说明（不可直接运行）：

workbook = xbot.excel.open(file_name=file_path, kind="wps", visible=True)
try:
    sheet = workbook.get_active_sheet()
    data = sheet.get_used_range()
finally:
    workbook.close()
```
| `get_full_name()` | 无 | 获取当前工作簿的完整文件路径 |

---

## 9. Sheet 操作

### 9.1 获取 Sheet

```python
sheet = workbook.get_active_sheet()
sheet = workbook.get_sheet_by_name("Sheet1")
sheet = workbook.get_sheet_by_index(1)
sheets = workbook.get_all_sheets()
sheet_name = sheet.get_name()
```

| 方法 | 参数 | 参数说明 | 返回 |
|---|---|---|---|
| `get_active_sheet()` | 无 | 当前激活 Sheet | `WorkSheet` |
| `get_sheet_by_name(name)` | `name: str` | Sheet 名称 | `WorkSheet` |
| `get_sheet_by_index(index)` | `index: int` | Sheet 位置，通常从 `1` 开始 | `WorkSheet` |
| `get_all_sheets()` | 无 | 获取全部 Sheet | Sheet 列表 |
| `sheet.get_name()` | 无 | 获取当前 Sheet 名称 | `str` |

### 9.2 激活 / 创建 / 删除 / 重命名

```text
非执行调用说明（不可直接运行）：

workbook.active_sheet_by_name("Sheet1")
workbook.active_sheet_by_index(1)
workbook.create_sheet("新Sheet", "last")
workbook.rename_sheet("旧名称", "新名称")
workbook.delete_sheet("Sheet1")
```

| 方法 | 参数 | 可选值 / 说明 |
|---|---|---|
| `active_sheet_by_name(name)` | `name: str` | Sheet 名称 |
| `active_sheet_by_index(index)` | `index: int` | Sheet 位置 |
| `create_sheet(name, create_way)` | `create_way: str` | `"first"` / `"last"`，必须小写 |
| `rename_sheet(name, new_name)` | `name/new_name: str` | 旧名称 / 新名称 |
| `delete_sheet(name)` | `name: str` | 要删除的 Sheet 名称 |
| `copy_sheet(name, new_name, is_cover)` | `is_cover: bool` | 是否覆盖同名 Sheet |
| `copy_sheet_to_workbook(name, workbook, new_name, is_cover)` | `workbook` | 复制到另一个工作簿 |

---

## 10. 读取数据

### 10.1 原生 Sheet 方法

```python
value = sheet.get_cell(1, "A")
row_data = sheet.get_row(1)
col_data = sheet.get_column("A")
data = sheet.get_range(1, "A", 10, "D")
data = sheet.get_used_range()
```

| 方法 | 参数 | 参数说明 | 返回 |
|---|---|---|---|
| `get_cell(row, column)` | `row: int`, `column: str` | 行号从 `1` 开始；列名如 `"A"` | 单元格值 |
| `get_row(row)` | `row: int` | 行号从 `1` 开始 | 一维列表 |
| `get_column(column)` | `column: str` | 列名如 `"A"` | 一维列表 |
| `get_range(start_row, start_col, end_row, end_col)` | `int/str` | 起止行列 | 二维列表 |
| `get_used_range()` | 无 | 已使用区域 | 二维列表 |

### 10.2 可视化封装读数据：`read_data_from_workbook`

常见 `read_way` 可选值：

| `read_way` | 说明 | 需要的关键参数 |
|---|---|---|
| `"cell"` | 读取单元格 | `cell_row_num`、`cell_column_name` |
| `"range"` | 读取区域 | `area_begin_row_num`、`area_begin_column_name`、`area_end_row_num`、`area_end_column_name` |
| `"row"` | 读取整行 | `row_row_num` |
| `"column"` | 读取整列 | `column_column_name` |
| `"used_range"` | 读取已使用区域 | 无关键行列参数 |

其它参数：

| 参数 | 类型 | 默认值 | 可选值 | 说明 |
|---|---|---|---|---|
| `has_header_row` | `bool` | 视调用传入 | `True` / `False` | 读取区域时是否跳过首行表头 |
| `using_text` | `bool` | `False` | `True` / `False` | 是否读取显示文本；`openpyxl` 不支持 |
| `text_cols` | `str` | `""` | 如 `"C,F"` | 指定按文本读取的列 |
| `clear_space` | `bool` | `False` | `True` / `False` | 是否清理前后空白 |

---

## 11. 写入数据

### 11.1 原生 Sheet 方法

```text
非执行调用说明（不可直接运行）：

sheet.set_cell(1, "A", "hello")
sheet.set_cell(row_num=2, col_name="A", value="2026/08/05")
sheet.set_row(1, ["姓名", "年龄"], begin_column_name="A")
sheet.append_row(["张三", 18], begin_column_name="A")
sheet.insert_row(2, ["李四", 20], begin_column_name="A")
sheet.set_column("A", ["姓名", "张三"], begin_row_num=1)
sheet.set_range(1, "A", [["姓名", "年龄"], ["张三", 18]])
sheet.set_range(row_num=3, col_name="A", values=[["李四", 20]])
```

| 方法 | 参数 | 参数说明 |
|---|---|---|
| `set_cell(row_num, col_name, value)` | `row_num: int`, `col_name: str`, `value` | 写入单元格；也可按位置传参 |
| `set_row(row, values, begin_column_name="A")` | `values: list` | 覆盖一行 |
| `append_row(values, begin_column_name="A")` | `values: list` | 追加一行 |
| `insert_row(row, values, begin_column_name="A")` | `row: int` | 插入一行 |
| `set_column(column, values, begin_row_num=1)` | `values: list` | 覆盖一列 |
| `set_range(row_num, col_name, values)` | `values: list[list]` | 从指定位置写入二维数组；也可按位置传参 |

### 11.2 可视化封装写数据：`write_data_to_workbook`

`write_range` 可选值：

| `write_range` | 说明 | 常用关键参数 |
|---|---|---|
| `"cell"` | 写单元格 | `row_num`、`column_name`、`content` |
| `"row"` | 写一行 | `write_way`、`row_num`、`begin_column_name`、`content` |
| `"column"` | 写一列 | `write_column_way`、`column_name`、`begin_row_num`、`content` |
| `"area"` | 写区域 | `row_num`、`column_name`、`content` |

`write_way` 可选值：

| 值 | 说明 |
|---|---|
| `"append"` | 追加 |
| `"insert"` | 插入 |
| `"override"` | 覆盖 |

`write_column_way` 可选值：

| 值 | 说明 |
|---|---|
| `"append"` | 追加列 |
| `"insert"` | 插入列 |
| `"override"` | 覆盖列 |

其它参数：

| 参数 | 类型 | 示例 | 说明 |
|---|---|---|---|
| `write_as_text_cols` | `str` | `"C,F"` | 指定哪些列按文本写入，避免数字字符串被转成数字 |
| `content` | 任意 / `list` / `list[list]` | `"hello"`、`[1,2]`、`[[1,2]]` | 写入内容 |

### 11.3 WPS 批量写入以 `=` 开头的文本

通过 `kind="wps"` 调用 `sheet.set_range()` 写入二维数组时，字符串只要以 `=` 开头，WPS 就可能把它当成公式解析。内容不是合法公式时，影刀侧可能只得到没有明确字段信息的 COM 异常：

```text
pywintypes.com_error: (-2147352567, '发生意外。', ..., -1880948725)
```

这种问题有以下特征：

- 同一份数据总是在包含异常文本的固定批次失败。
- 延迟写入、重新打开 WPS、换新工作簿和连续重试都不能解决。
- 把失败批次单独写入仍然失败。
- 即使用 `csv.reader` 把全部值读取为字符串，只要原值仍以 `=` 开头，WPS 依然会尝试按公式处理。

写入前应把**本来就是业务文本、但以 `=` 开头**的值加上英文单引号：

```text
非执行调用说明（不可直接运行）：

cleaned_data = []
for row in data:
    cleaned_row = []
    for value in row:
        if isinstance(value, str) and value.startswith("="):
            value = "'" + value
        cleaned_row.append(value)
    cleaned_data.append(cleaned_row)

sheet.set_range(1, "A", cleaned_data)
```

本次在影刀 + WPS 环境实测，增加英文单引号后可一次性写入数千行数据，单元格显示内容仍以 `=` 开头，不会把英文单引号显示出来。

注意：只处理确定属于文本的字段。真正需要执行的 Excel / WPS 公式不能加英文单引号，否则会按普通文本保存。

---

## 12. 行列和区域操作

```python
row_count = sheet.get_row_count()
column_count = sheet.get_column_count()
first_free_row = sheet.get_first_free_row()
first_free_column = sheet.get_first_free_column()
last_column = sheet.get_last_column()
row_num = sheet.get_first_free_row_on_column("A")
```

当前真实项目已确认可用 `sheet.get_last_column()` 获取最后使用列，返回列字母，例如 `"BA"`。当前未确认对应的原生“最后数据行”方法，最后数据行通常仍使用 `sheet.get_first_free_row() - 1`。

普通的数据区域读取、复制或清空场景中，即使结束边界多包含一个空行或空列通常也没有影响，可以直接把 `get_first_free_row()` / `get_first_free_column()` 的结果当作区域结束位置使用。不要仅为把“第一个空行 / 空列”换算成“最后数据行 / 列”而新增复杂封装；需要准确最后列时直接调用 `get_last_column()`。

只有业务明确要求精确行数、精确列数或严格边界时，才在当前代码中直接做简单换算，例如最后数据行为 `sheet.get_first_free_row() - 1`。

```text
非执行调用说明（不可直接运行）：

sheet.remove_row(2)
sheet.remove_column("C")
sheet.insert_blank_row(2, amount=1)
sheet.insert_blank_column("B", amount=1)
sheet.clear()
sheet.clear_range(begin_row_num=1, begin_column_name="E", end_row_num=first_free_row, end_column_name=first_free_column, target="content")
```

`clear_range()` 用于清空指定区域，真实项目已确认的参数如下：

| 参数 | 类型 | 示例 | 说明 |
|---|---|---|---|
| `begin_row_num` | `int` | `1` | 起始行 |
| `begin_column_name` | `str` | `"E"` | 起始列 |
| `end_row_num` | `int` | `20000` | 结束行 |
| `end_column_name` | `str` | `"AA"` | 结束列 |
| `target` | `str` | `"content"` | 清空目标；清数据时使用 `"content"` |

也可按位置传参：

```text
非执行调用说明（不可直接运行）：

sheet.clear_range(1, "E", 20000, "AA")
```

清空或覆盖目标数据前，先成功读取本次写入所需的源数据，并按当前业务契约确认必需字段、数据范围、目标区域及空结果是否允许覆盖；不满足约定时停止写入，不清空旧数据。只检查本次真实路径所需内容，不重复读取或校验已由正常流程确认的结果。

清空旧数据是后续写入正确性的前提时，不要静默忽略 `clear_range()` 异常。

常见参数：

| 参数 | 类型 | 可选值 / 示例 | 说明 |
|---|---|---|---|
| `row_num` | `int` / `str` | `1`、`"1:3"`、`"1,3,5"` | 行号或行范围；部分封装支持范围字符串 |
| `column_name` | `str` / `int` | `"A"`、`"A:C"`、`"A,C"`、`1` | 列名或列范围；部分封装支持数字列 |
| `amount` | `int` | `1`、`2` | 插入空行/空列数量，必须大于 0 |

---

## 13. 清空、复制、粘贴、选择

### 13.1 复制区域

原生区域复制：

```text
非执行调用说明（不可直接运行）：

source_sheet.copy_range(begin_row_num=1, begin_column_name="A", end_row_num=end_row, end_column_name="BA")
target_sheet.paste_range_ex(row_num=1, column_name="G")
```

纯数据搬运优先使用 `get_range()` + `set_range()`；需要同时保留公式或格式时，再使用 `copy_range()` + `paste_range_ex()`。

`copy_range()` 参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `begin_row_num` | `int` | 起始行 |
| `begin_column_name` | `str` | 起始列 |
| `end_row_num` | `int` | 结束行 |
| `end_column_name` | `str` | 结束列 |

可视化复制封装的 `copy_way` 可选值：

`copy_way` 可选值：

| 值 | 说明 |
|---|---|
| `"cell"` | 复制单元格 |
| `"range"` | 复制区域 |
| `"row"` | 复制行 |
| `"column"` | 复制列 |
| `"used_range"` | 复制已使用区域 |

### 13.2 粘贴区域

```text
非执行调用说明（不可直接运行）：

sheet.paste_range_ex(
    row_num=1,
    column_name="A",
    paste_type=-4104,
    paste_special_operation=-4142,
    skip_blanks=False,
    transpose=False,
)
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `row_num` | `int` | 无 | 粘贴起始行 |
| `column_name` | `str` | 无 | 粘贴起始列 |
| `paste_type` | `int` | `-4104` | Excel 粘贴类型常量 |
| `paste_special_operation` | `int` | `-4142` | Excel 特殊粘贴操作常量 |
| `skip_blanks` | `bool` | `False` | 是否跳过空白 |
| `transpose` | `bool` | `False` | 是否转置 |

### 13.3 选择多行

```text
非执行调用说明（不可直接运行）：

sheet.select_rows(list(range(2, 11)))
```

`select_rows(rows)` 接收行号列表，用于在 Excel / WPS 界面中选中多行。该操作依赖真实 Office / WPS 界面，需在影刀运行环境验证。

---

## 14. 格式设置

### 14.1 获取区域对象

```python
cell_range = sheet.cell("A", 1)
row_range = sheet.row(1)
column_range = sheet.column("A")
area_range = sheet.range("A1:D10")
used_range = sheet.used_range()
```

### 14.2 区域格式方法

| 方法 | 参数 | 可选值 / 示例 | 说明 |
|---|---|---|---|
| `set_format(setting)` | `dict` | 格式字典 | 设置完整格式 |
| `set_number_format(number_format)` | `str` | `"0.00"`、`"yyyy-mm-dd"` | 设置数字格式 |
| `set_alignment(setting)` | `dict` | 对齐设置 | 设置对齐 |
| `set_border(setting)` | `dict` | 边框设置 | 设置边框 |
| `set_font(setting)` | `dict` | 字体设置 | 设置字体 |
| `set_background(setting)` | `dict` | 背景设置 | 设置背景色 |
| `set_protection(locked=True, formula_hidden=None)` | `bool` | `True` / `False` | 设置保护 |
| `clear_format()` | 无 | 无 | 清空格式 |
| `set_column_width(mode, value=None)` | `mode: str` | `"autoFit"` 或指定宽度 | 设置列宽 |
| `set_row_height(mode, value=None)` | `mode: str` | `"autoFit"` 或指定高度 | 设置行高 |
| `add_validation(setting)` | `dict` | 数据验证设置 | 添加数据验证 |

注意：`autoFit` 大小写按源码注释写法，建议原样传 `"autoFit"`。

---

## 15. 高级功能

```text
非执行调用说明（不可直接运行）：

workbook.execute_macro("宏名称")
workbook.refresh_data()
workbook.export_to_pdf(r"C:\path\demo.pdf", sheet_name="Sheet1", all_sheets=False, override=True)
```

| 方法 | 关键参数 | 可选值 / 说明 |
|---|---|---|
| `execute_macro(macro)` | `macro: str` | 宏名称 |
| `refresh_data()` | 无 | 刷新数据 |
| `create_pivot_table(setting, source, sheet_name=None, pivot_name=None)` | `dict/str` | 创建数据透视表 |
| `refresh_pivot_table(name_or_index, sheet_name, refresh_all)` | `refresh_all: bool` | 刷新透视表 |
| `filter_pivot_table(sheet_name, name_or_index, field_name, select_type, filter_value_list)` | `select_type` | 常见 `"partial"` |
| `export_to_pdf(pdf_name, sheet_name=None, all_sheets=False, override=True)` | `all_sheets/override: bool` | 导出 PDF |

---

## 16. 推荐模板

### 16.1 只读数据

```text
非执行调用说明（不可直接运行）：

import xbot.excel

workbook = xbot.excel.open(
    file_name=r"C:\path\demo.xlsx",
    kind="openpyxl",
    ignore_formula=True,
)

sheet = workbook.get_active_sheet()
data = sheet.get_used_range()
workbook.close()
```

### 16.2 写入数据并保存

```text
非执行调用说明（不可直接运行）：

import xbot.excel

workbook = xbot.excel.open(
    file_name=r"C:\path\demo.xlsx",
    kind="office",
    visible=False,
)

sheet = workbook.get_sheet_by_name("Sheet1")
sheet.set_range(1, "A", [["姓名", "年龄"], ["张三", 18]])

workbook.save()
workbook.close()
```

### 16.3 WPS 打开文件

```text
非执行调用说明（不可直接运行）：

import xbot.excel

workbook = xbot.excel.open(
    file_name=r"C:\path\demo.xlsx",
    kind="wps",  # 必须是小写 wps
    visible=True,
)
```

### 16.4 WPS 主窗口获取与最大化

WPS 表格的可见 UI 主窗口由 `wps.exe` 承载，不要只按 `et.exe` 查找表格窗口。`et.exe` 可存在于 WPS 表格运行过程中，但不能据此判断拿到的是用户当前看到的主窗口。

WPS 窗口标题也不是稳定定位条件。打开或创建 WPS 工作簿后，如果下一步就是操作刚出现的表格窗口，优先使用 `win32.get_active()` 获取当前激活窗口，并校验其进程确实为 `wps.exe`，再执行窗口操作。

```text
非执行调用说明（不可直接运行）：

from xbot import win32
import xbot.excel


workbook = xbot.excel.open(
    file_name=r"C:\path\demo.xlsx",
    kind="wps",
    visible=True,
)

wps_window = win32.get_active(timeout=5)
process_name = str(wps_window.get_detail("process_name") or "").lower()
if process_name not in ("wps", "wps.exe"):
    raise RuntimeError("当前激活窗口不是 WPS 表格窗口")

wps_window.set_state("maximize")
```

这里 `set_state("maximize")` 本身就是正确的最大化调用；如果调用后没有视觉效果，应先确认取得的是否是真正的 WPS 可见主窗口，而不是辅助进程窗口或其他前台窗口。`get_active()` 与 `set_state()` 的窗口 API 事实见 [Win32 自动化](win32.md)。

如果业务允许清理本机残留 WPS 进程，可在打开工作簿前使用 `xbot.excel.kill_excel_process("wps", True)` 清场；它不是“最大化 WPS”的必要步骤，不应为了最大化窗口默认强制关闭用户现有的 WPS 进程。

---

## 17. 排错速查

解压后的报表包含多个 Excel 文件时，目标工作簿的识别规则见 [ZIP 使用建议](xzip.md#5-使用建议)。

### 17.1 长数字已经丢失精度时不能靠格式恢复

订单号、商品 ID、链接 ID 等长数字应在进入 Excel / WPS 前就按文本保护。如果原始文件已经把长数字按数值保存并发生精度丢失，之后再设置文本格式、科学计数法显示格式或给当前错误值加单引号，都不能恢复原始数字；这时必须回到未丢失精度的数据源重新读取。

### 17.2 WPS / Excel 只读与文件占用

真实工作簿以只读方式打开时，不要直接把原因判定为“他人占用”。常见排查顺序是：

1. 先检查 `workbook.workbook.ReadOnly`。
2. 如果业务允许清理本机残留进程，先关闭当前工作簿，再按驱动使用 `xbot.excel.kill_excel_process("wps", True)` 或 `xbot.excel.kill_excel_process("office", True)` 清理本机残留进程并重新打开一次。
3. 二次打开仍为只读时，再结合 `xbot_enhance_tools.excel_utils.get_wps_lock_user(workbook)` 检查共享文件锁和占用者。

不要在共享办公场景下未经确认就强制结束他人的 Office / WPS 进程。`get_wps_lock_user()` 的返回与锁文件边界见 [增强工具 2026](extensions/xbot-enhance-tools.md)。

| 现象 | 常见原因 | 处理 |
|---|---|---|
| `kind="WPS"` 打不开 | 参数值大小写错误 | 改成 `kind="wps"` |
| `kind="PWS"` 报错 | 拼写错误 | 改成 `kind="wps"` |
| `openpyxl` 读取不到显示文本 | `openpyxl` 不支持 `using_text=True` | 改用 `office` / `wps` |
| 写入数字字符串变成数字 | Excel 自动识别类型 | 用 `write_as_text_cols="C,F"` 或写入前加文本标记 |
| 大量写入很慢 | 循环逐单元格写入 | 改用 `set_range()` 一次性写二维数组 |
| WPS `set_range()` 固定批次报 `发生意外` / `-1880948725` | 某个业务文本以 `=` 开头，被 WPS 当成非法公式 | 二分定位到具体单元格；确认是文本后改为 `"'" + value` 再一次性写入 |
| 宏无法执行 | `openpyxl` 不支持宏执行 | 改用 `office` 或 `wps` |
