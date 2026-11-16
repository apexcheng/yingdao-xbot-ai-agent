# Excel扩展操作 (activity_excel_v2)

> 调用类型：`flow`  
> 主要入口：主要通过 __init__.py 包装入口调用 Visual / Code flow；refresh_pivot_table 为模块导入入口。  
> 核验来源：2026-09-01 按本机 2026-07-13 版本的 `__init__.py` 与 `prototype.block.json` 核对；其他版本调用前用 `inspect.signature()` 复核。
> 返回：[市场指令索引](../extension-instructions.md)

---

**目录/指令名：** `activity_excel_v2` / Excel扩展操作

**调用方式：** flow

**用途：** 补充原生 Excel 指令没有覆盖的高级表格处理能力，如公式填充、筛选、文本数字转换、图片操作、工作表处理、透视表刷新等。

## 与原生 Excel 指令边界

- 普通读取、写入、清空、复制等基础操作优先使用原生 Excel 指令。
- 复杂筛选、公式批量填充、图片处理、工作表扩展操作使用 `activity_excel_v2`。
- `activity_excel_v2` 不替代原生 Excel 指令。

## 参数规范

公开 API 常见参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| excel_instance | 影刀工作簿对象 | None | `prototype.block.json` 的类型标签为 `openpyxl.Workbook`，实际传入影刀 Excel 工作簿对象 |
| sheet_name | str | 当前 Sheet | 指定 Sheet |
| row / begin_row / end_row | str/int | 按指令定义 | 行范围 |
| column / begin_column / end_column | str | 按指令定义 | 列范围 |

主要返回类型：

| 类型 | 场景 |
| --- | --- |
| None | 修改类操作 |
| str/path | 文件、图片等结果 |
| list/dict | 数据读取、聚合类结果 |

完整参数以当前版本 `prototype.block.json` 定义为准。

## API 分类索引

以下为正式公开 API，不包含 `test_*` 等内部测试 flow。

### A 单元格填充

- 公式向下填充
- 公式向右填充
- 自动向下填充
- 空白单元格填充

主要入口：

- `fill_down_formula`
- `fill_right_formula`
- `process31`
- `process36`

### B 单元格操作

- 文本/数字格式转换
- 分列
- 内容替换
- 自动换行
- 超链接
- 注释
- 图片导入导出删除
- WPS 图片内嵌参见 [WPS 图片嵌入单元格](../excel.md#165-wps-图片嵌入单元格)。

主要入口：

- `text_format_to_num`
- `num_format_to_text`
- `process19`
- `process26`
- `process32`
- `process33`
- `process37`
- `process42`
- `process45`
- `process55`

### C 筛选

- 筛选
- 清除筛选

主要入口：

- `filter`
- `process16`
- `process20`
- `process21`
- `process38`
- 读取筛选内容
- 删除筛选内容
- 颜色筛选

### D 其它

- 查找数据所在行/列
- 合成字典
- 工作表隐藏管理
- 合并计算
- 密码设置
- 透视表刷新

其它公开入口：

- `process23` 数字列名转换
- `process27` 查找数据所在列
- `process28` 查找数据所在行
- `process29` 生成字典(数值累加)
- `process30` 生成字典(列表拼接)
- `process44` 删除所有图片
- `process46` 隐藏/取消隐藏 Sheet
- `process47` 获取隐藏 Sheet
- `process48` 合并计算
- `process49` 设置/取消密码
- `process56` 冻结首行
- `process57` 设置切片器
- `process58` 执行文本宏

**调用入口：**
- Visual flow 包装入口：`xbot_extensions.activity_excel_v2.<入口函数>(...)`
- Code flow 模块入口：`xbot_extensions.activity_excel_v2.refresh_pivot_table.main(args)`
- 常用入口：`fill_down_formula()`、`fill_right_formula()`、`filter()`、`text_format_to_num()`、`num_format_to_text()`、`process16()` 等
- 区域截图入口：`process24(excel_instance, begin_row, begin_column, end_row, end_column, save_path, sheet_name)`

**参数说明：**
- `excel_instance` / `Excel对象`：待处理 Excel 对象。
- `sheet_name` / `Sheet页名称`：Sheet 名称；多数指令可选，通常默认当前激活 Sheet。
- 行列参数按指令定义传入，如 `row`、`begin_row`、`end_row`、`column`、`column_name`、`begin_column`、`end_column`。
- 具体入口函数、参数顺序和返回值以 `prototype.block.json` 与 `__init__.py` 为准，不根据可视化中文界面猜测编码版参数。

**典型调用方式：**
```text
非执行调用说明（不可直接运行）：

from xbot_extensions.activity_excel_v2 import (
    fill_down_formula,
    filter,
    process21,
    process24,
    process56,
)

# 向下填充公式
fill_down_formula(
    excel_instance=workbook,
    formula_content="=A2+B2",
    column="C",
    begin_row="2",
    end_row="-1",
    sheet_name="",
    数组公式=False,
)

# 按内容筛选后读取筛选结果
filter(
    excel_instance=workbook,
    row="1",
    column="A",
    select_content="已完成",
    select_type="={0}",
    sheet_name="",
    operator="7",
    select_content2="",
    select_type2="",
)

filter_content = process21(
    excel_instance=workbook,
    begin_row="2",
    sheet_name="",
    content_type="data",
    using_text=True,
    using_text_cols="",
    data_columns="",
)

# 冻结首行
process56(
    excel_instance=workbook,
    sheet_name="",
    kind="ROW",
    area="1",
)

# 把指定区域保存为图片
result = process24(
    excel_instance=workbook,
    begin_row=1,
    begin_column="E",
    end_row=last_row,
    end_column=last_column,
    save_path=image_path,
    sheet_name="每日报表",
)
if isinstance(result, dict):
    image_path = result.get("image_save_path", image_path)
```

### 区域截图 `process24()`

```text
非执行调用说明（不可直接运行）：

result = process24(excel_instance, begin_row, begin_column, end_row, end_column, save_path, sheet_name)
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `excel_instance` | 工作簿对象 | 已打开的 Excel / WPS 工作簿 |
| `begin_row` | `int` | 起始行 |
| `begin_column` | `str` | 起始列，如 `"E"` |
| `end_row` | `int` | 结束行 |
| `end_column` | `str` | 结束列，如 `"T"` |
| `save_path` | `str` | 图片保存路径 |
| `sheet_name` | `str` | 要截图的 Sheet 名称 |

输出名为 `image_save_path`。当前真实项目中包装入口可能直接返回路径，也可能返回包含 `image_save_path` 的字典，因此调用方可按上例兼容读取。该能力没有发现等价的原生 `xbot.excel` 区域截图接口，适合保留为市场指令用法。

**注意事项：**
- 这是市场扩展能力，不是原生 `xbot.excel` 内置 API；能用原生 `xbot.excel` 清晰完成的任务仍优先查 [`excel.md`](../excel.md)。
- 普通读写、清空、复制优先使用原生 `xbot.excel`；只有区域截图等原生 API 缺失的能力才使用本扩展。
- 该扩展大多数编码版入口是 `__init__.py` 中的包装函数，调用后进入 Visual flow；`refresh_pivot_table` 是 Code flow 模块入口；不要把内部工具模块或测试模块当作公开调用入口。
- `process45`、`process46`、`process47` 等入口在源码中使用中文参数名，编码版调用前建议按当前安装版本再次用 `inspect.signature()` 核对。
- 本节仅根据源码结构和 block 元数据整理，未在影刀编辑器内运行验证。

## API Reference（参数索引）

公开指令参数来源于 `prototype.block.json`，隐藏测试 flow 不纳入。

| 指令 | function | 参数 | 类型 | 默认值 | 输出 |
| --- | --- | --- | --- | --- | --- |
| 批量向下填充(公式) | `fill_down_formula` | excel_instance, formula_content, column, begin_row, end_row, sheet_name, 数组公式 | Workbook / str / bool | None/空/False | 无 |
| 批量向右填充(公式) | `fill_right_formula` | excel_instance, formula_content, row, begin_column, end_column, sheet_name, array_formula_mode | Workbook / str / bool | None/空/False | 无 |
| 筛选 | `filter` | excel_instance, row, column, select_content, select_type, sheet_name, operator, select_content2, select_type2 | Workbook / str | None | 无 |
| 区域文本转数字 | `text_format_to_num` | excel_instance, begin_row, begin_column, end_row, end_column, sheet_name | Workbook / str | None | 无 |
| 区域数字转文本 | `num_format_to_text` | excel_instance, begin_row, begin_column, end_row, end_column, sheet_name | Workbook / str | None | 无 |
| 区域截图 | `process24` | excel_instance, begin_row, begin_column, end_row, end_column, save_path, sheet_name | Workbook / int / str | None | 图片路径 |
| 读取筛选内容 | `process21` | excel_instance, begin_row, sheet_name, content_type, using_text, using_text_cols, data_columns | Workbook / bool | None | 数据列表 |
| 获取合并单元格区域 | `process55` | excel_instance, row, column, sheet_name | Workbook / str | None | 合并状态、区域 |
| 冻结首行 | `process56` | excel_instance, sheet_name, kind, area | Workbook / str | None | 无 |
| 设置切片器 | `process57` | excel_instance, slicercache_name, item_name, selected | Workbook / str / bool | True | 无 |
| 刷新透视表 | `refresh_pivot_table.main` | args（含 excel_instance、sheet_name） | dict | None | 无 |

完整参数仍以当前安装版本 `prototype.block.json` 为准。

---
