# 影刀桌面对话框与通知方法

> 定位：影刀 / xbot 桌面端对话框、通知、选择器交互接口。
> 说明：本页基于 `xbot.app.dialog` 源码整理，优先按源码参数和返回值描述；旧文档若有冲突，以源码为准。

---

## 1. 核验来源

本页按本机可见 ShadowBot 6.3.13 内置 `xbot/app/dialog.py` 核对；与 6.3.12 对应源码哈希一致。安装目录随版本变化；其他版本用 `inspect.getfile(xbot.app.dialog)` 定位当前实现。

---

## 2. `show_alert(message, title=...)`

### 作用

打开消息提示框。

### 返回值

无。

### 注意事项

- `title` 默认值来自 `strings.Dialog_Alter_Title`，源码未直接展开字符串内容。

---

## 3. `show_confirm(message, title=...) -> bool`

### 作用

打开确认对话框，返回用户是否确认。

### 返回值

- `True`：确认
- `False`：取消

---

## 4. `show_custom_dialog(settings, *, storage_key=None) -> dict`

### 作用

打开自定义对话框。

### 常用场景

- 组合输入框、按钮、选择框
- 复杂参数收集
- 需要记住用户输入时

### 参数

| 参数名 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| `settings` | `dict` / `json串` | 是 | 对话框配置 |
| `storage_key` | `str` / `None` | 否 | 记忆输入内容的存储键 |

### 返回值

- 成功时返回对话框数据字典
- 失败时抛异常

### 注意事项

- `storage_key` 不为空时，源码会尝试读取/保存历史输入。
- 对话框配置结构较复杂，建议按源码注释逐项填写。
- 下拉/列表控件的 `options` 结构存在版本差异：6.3.12 / 6.3.13 的 Python 存根仍给出字符串数组示例，而部分运行时版本使用 `{"value": ..., "display": ...}` 对象数组。不能把任一写法泛化为所有版本；按当前客户端做最小运行验证。

### `File` 文件选择编辑器

自定义对话框需要用户选择一个已存在的本地文件时，应使用 `File` 编辑器，不要用 `TextBox` 要求用户手工填写文件路径。`TextBox` 只用于普通文本输入。

当前真实项目已确认的文件选择配置如下：

```text
非执行调用说明（不可直接运行）：

{
    "type": "File",
    "label": "订单表格",
    "VariableName": "table_path",
    "kind": 0,  # 选择文件
    "filter": "Excel文件|*.xlsx;*.xlsm;*.xls;*.et|所有文件|*.*",
    "value": None,
    "nullText": "请选择订单表格文件",
}
```

- `kind=0` 表示选择文件；其他 `kind` 值未在本页确认，不应推断。
- `filter` 使用“说明|扩展名列表”的格式，并按业务允许的文件类型设置。
- `value` 可以传入之前保存的文件路径，用于再次打开对话框时回显。
- 用户选择的路径通过结果字典中的 `VariableName` 获取，例如 `result["table_path"]`。
- 文件选择控件不能替代业务校验；使用前仍应确认路径指向实际存在的文件。
- 需要与其他配置项一起收集时使用本节的 `File` 编辑器；只需要单独选择文件时，也可以使用本页的 `show_select_file_dialog()`。

### 示例

当前运行时要求对象数组时，可使用以下写法；其他版本需运行验证：

```text
非执行调用说明（不可直接运行）：

from xbot.app.dialog import show_custom_dialog

dialog_settings = {
    "dialogTitle": "采集参数",
    "settings": {
        "editors": [
            {"type": "TextBox", "label": "链接", "VariableName": "url",
             "value": None, "nullText": "请输入链接"},
            {"type": "Select", "label": "浏览器类型", "VariableName": "browser_type",
             "value": "chrome",  # 必须等于某个选项的 value
             "options": [{"value": "chrome", "display": "chrome"},
                         {"value": "edge", "display": "edge"}]},
        ],
        "buttons": [
            {"type": "Button", "label": "确定", "theme": "red", "hotkey": "Enter"},
            {"type": "Button", "label": "取消", "theme": "white", "hotkey": "Esc"},
        ],
    },
}
result = show_custom_dialog(dialog_settings)
# result["browser_type"] 取到选项的 value（如 "chrome"）
```

---

## 5. `show_message_box(title, message, button='ok', *, timeout=-1, default_button=None) -> str`

### 作用

打开消息对话框，支持单按钮或多按钮选择。

### 参数

| 参数名 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| `title` | `str` | 是 | 标题 |
| `message` | `str` | 是 | 消息内容 |
| `button` | `str` | 否 | 按钮组合，如 `ok`、`okcancel`、`yesno`、`yesnocancel` |
| `timeout` | `int` | 否 | 超时时间，`-1` 一直等，`0` 不等 |
| `default_button` | `str` / `None` | 否 | 默认按钮；不传时按源码规则自动推断 |

### 返回值

返回用户点击的按钮名。

### 注意事项

- 按钮名应传小写，源码按小写判断。
- `default_button` 不传时，源码会根据 `button` 自动选择。

---

## 6. `show_workbook_dialog(title, message) -> str`

### 作用

打开数据表格对话框。

### 返回值

返回用户点击的按钮名。

---

## 7. `show_input_dialog(title, label, typestr, *, value=None, storage_key=None) -> dict`

### 作用

打开输入对话框。

### `typestr` 可选值

- `input`
- `password`
- `multiInput`

### 返回值

对话框结果字典。

### 注意事项

- `multiInput` 会被构造成多行输入框。
- 其他类型会走单行输入或密码框。

---

## 8. `show_datetime_dialog(title, label, kind, formatstr, *, begin_date=None, end_date=None, storage_key=None) -> dict`

### 作用

打开日期/时间选择对话框。

### `kind` 可选值

- `date`
- `dateRange`

### `formatstr` 常见值

- `yyyy-MM-dd`
- `yyyy-MM-dd HH:mm:ss`
- `yyyy/MM/dd`
- `yyyy/MM/dd HH:mm:ss`

### 返回值

对话框结果字典。

---

## 9. `show_select_dialog(title, label, select_type, select_model, *, values=None, is_selected_first=True, storage_key=None) -> dict`

### 作用

打开单选/多选选择对话框。

### `select_type`

- `combobox`
- `list`

### `select_model`

- `single`
- `multi`

### `values`

可传 `list[str]` 或按换行分隔的字符串。

### 返回值

对话框结果字典。

### 注意事项

- `values` 不能为空，否则会报类型错误。
- `is_selected_first=True` 时会默认选中第一项。

---

## 10. `show_select_file_dialog(title, *, folder=None, filter=..., is_multi=False, is_checked_exists=False) -> dict`

### 作用

打开文件选择对话框。

### 返回值

对话框结果字典。

---

## 11. `show_select_folder_dialog(title, *, folder=None) -> dict`

### 作用

打开文件夹选择对话框。

### 返回值

对话框结果字典。

---

## 12. `show_notifycation(message, *, placement='rightbottom', level='info', timeout=3)`

### 作用

发送桌面通知。

### 参数

| 参数名 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| `message` | `str` | 是 | 通知内容 |
| `placement` | `str` | 否 | `top` / `bottom` / `rightbottom`，默认 `rightbottom` |
| `level` | `str` | 否 | `info` / `warning` / `error` |
| `timeout` | `int` / `float` | 否 | 显示时长，默认 3 秒 |

### 返回值

无。

### 注意事项

- `placement` 和 `level` 的可选值已按 ShadowBot 6.3.13 存根核对；与 6.3.12 对应源码一致，其他版本应复核当前实现。

### 示例

```text
非执行调用说明（不可直接运行）：

from xbot.app.dialog import show_notifycation

show_notifycation("✅ 完成", placement="rightbottom", level="info")
```

---

## 13. `close_notifycation()`

### 作用

关闭桌面通知框。

方法名中的 `notifycation` 是当前公开 API 的实际拼写，不要改成 `notification`。

### 返回值

无。

---

## 14. 推荐用法

- 运行中提示：`show_notifycation()`
- 用户确认：`show_confirm()`
- 单次提示：`show_alert()` 或 `show_message_box()`
- 复杂参数输入：`show_custom_dialog()`
- 文件/文件夹选择：`show_select_file_dialog()` / `show_select_folder_dialog()`
