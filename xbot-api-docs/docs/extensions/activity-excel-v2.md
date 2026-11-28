# Excel 扩展操作（activity_excel_v2）

> 安装版本 `26.10.5` · 核验日期 2026-11-16
> 返回 [市场指令索引](../extension-instructions.md)

本页依据影刀应用安装的「Excel 扩展操作」`26.10.5` 版。共核对 **40 条公开指令**，其中 **39 条可视化流程**、**1 条编码流程**。以下行为来自安装副本的静态核对，Excel、WPS 的具体运行结果需在实际软件版本验证。

## 公开指令总表

| 界面名称 | 编码入口 | 流程类型 | 声明输出 |
| --- | --- | --- | --- |
| 批量向下填充(公式) | `fill_down_formula` | 可视化 | — |
| 批量向右填充(公式) | `fill_right_formula` | 可视化 | — |
| 自动向下填充 | `process31` | 可视化 | — |
| 单元格填充图片 | `process18` | 可视化 | — |
| 空白单元格填充(向上填充) | `process36` | 可视化 | — |
| 公式转换成值 | `process52` | 可视化 | — |
| 新建注释 | `process53` | 可视化 | — |
| 分列 | `process19` | 可视化 | — |
| 内容替换 | `process26` | 可视化 | — |
| 区域截图 | `process24` | 可视化 | `image_save_path` |
| 区域文本转数字 | `text_format_to_num` | 可视化 | — |
| 区域数字转文本 | `num_format_to_text` | 可视化 | — |
| 读取单元格注释 | `process37` | 可视化 | `comment` |
| 合并单元格 / 取消单元格合并 | `process34` | 可视化 | — |
| 设置单元格超链接 | `process33` | 可视化 | — |
| 获取单元格超链接 | `process32` | 可视化 | `hyperlink` |
| 导出单元格的图片 | `process42` | 可视化 | `pic_path` |
| 删除单元格的图片 | `process45` | 可视化 | — |
| 获取背景色 | `process54` | 可视化 | `background_color` |
| 获取合并单元格区域 | `process55` | 可视化 | `is_merge`、`merge_range` |
| 筛选 | `filter` | 可视化 | — |
| 筛选颜色 | `process38` | 可视化 | — |
| 清除筛选 | `process16` | 可视化 | — |
| 读取筛选内容 | `process21` | 可视化 | `filter_content` |
| 删除筛选内容 | `process20` | 可视化 | — |
| 数字列名转换 | `process23` | 可视化 | `convert_result` |
| 查找数据所在列 | `process27` | 可视化 | `column_name` |
| 查找数据所在行 | `process28` | 可视化 | `查找结果` |
| 生成字典(列表拼接) | `process30` | 可视化 | `result_dict` |
| 生成字典(数值累加) | `process29` | 可视化 | `result_dict` |
| 删除所有图片 | `process44` | 可视化 | — |
| 隐藏 / 取消隐藏 Sheet 页 | `process46` | 可视化 | — |
| 获取隐藏的 Sheet 页 | `process47` | 可视化 | `隐藏的工作表名列表` |
| 合并计算 | `process48` | 可视化 | — |
| 设置/取消密码 | `process49` | 可视化 | — |
| 自动换行 | `process51` | 可视化 | — |
| 冻结首行 | `process56` | 可视化 | — |
| 设置切片器 | `process57` | 可视化 | — |
| 执行文本宏 | `process58` | 可视化 | — |
| 刷新透视表 | `refresh_pivot_table.main` | 编码 | — |

## 调用方式

- 在影刀编码版，从 `xbot_extensions.activity_excel_v2` 导入可视化指令的包装函数，例如 `process18`。包装函数会通过影刀流程运行器执行对应流程，公开调用需要影刀运行环境。
- 刷新透视表是编码流程，模块是 `xbot_extensions.activity_excel_v2.refresh_pivot_table`，其中的 `main` 接收参数字典。
- 表格指令通常使用已打开的影刀 Office/WPS 工作簿。多数实现会检查关闭状态和对象类型。可视化参数将不少工作簿标为 `openpyxl.Workbook`，本版校验实际接受 `OfficeWorkBook`、`WpsWorkBook`，并拒绝影刀的 `OpenPyxlWorkBook`。普通单元格读写可继续使用 [影刀原生 Excel 指令](../excel.md)。
- 参数表按**编码版调用顺序**排列，签名按源码原样列出。参数表的「流程默认」是缺失字段时流程采用的初始值。39 个 Python 包装函数的签名中均没有可省略的默认参数，有空值的参数也按签名传入 `''` 或对应布尔值。中文参数名应原样保留。
- 行列通常从 `1` 开始，列通常接受 `A` 或数字形式。采用通用坐标解析的指令中，`-1` 代表已使用区域的最后一行或最后一列，`-2` 代表倒数第二项。单条指令可以另有限制。`sheet_name=''` 通常取当前活动 Sheet，隐藏或显示工作表必须给出名称。
- 文档的「输出」是流程声明的字段及实现产生的数据。可视化包装函数直接返回影刀运行器的结果。旧知识页记录区域截图在真实项目中可得到路径本身或以 `image_save_path` 为键的字典。本次未运行 `26.10.5` 验证包装层的返回容器。

## 常用指令速查

| 任务 | 公开入口 | 调用要点 |
| --- | --- | --- |
| 插入浮动图片 | `process18` | `lockaspectratio`、`placement` 传明确枚举值。 |
| 导出或删除同一位置的图片 | `process42`、`process45` | 按图片左上角对应的格子定位。 |
| 区域截图 | `process24` | 依赖 Windows 剪贴板，输出路径字段为 `image_save_path`。 |
| 筛选后读取 | `filter`、`process21` | 读取模式支持数据、首个可见行和全部可见行号。 |
| 区域公式转换成值 | `process52` | 会覆盖公式，区域在 `set_range` 中指定。 |
| 刷新透视表 | `refresh_pivot_table.main` | `args` 传字段字典，指定 Sheet 时会激活该页。 |

### 调用示意

以下示意中的 `workbook` 指已用影刀以 Office/WPS 方式打开的工作簿。

```text
非执行调用说明（不可直接运行）

from xbot_extensions.activity_excel_v2 import process18

process18(excel_instance=workbook, image_path=r'D:\images\example.png',
          row_num='2', column_name='E', row_height='', colnum_width='',
          lockaspectratio='-1', placement='1', sheet_name='评价',
          compress=False, is_insert_only=True)
```

这会插入一张随格移动和缩放的浮动图片。需要将图片写成单元格内容时，参见 [WPS 图片嵌入单元格](../excel.md#165-wps-图片嵌入单元格)。

```text
非执行调用说明（不可直接运行）

from xbot_extensions.activity_excel_v2 import filter, process21

filter(excel_instance=workbook, row='1', column='C',
       select_content='已完成', select_type='={0}', sheet_name='明细',
       operator='7', select_content2='', select_type2='')

result = process21(excel_instance=workbook, begin_row='2', sheet_name='明细',
                   content_type='data', using_text=True,
                   using_text_cols='A', data_columns='A,C')
```

```text
非执行调用说明（不可直接运行）

from xbot_extensions.activity_excel_v2 import process24, refresh_pivot_table

result = process24(excel_instance=workbook, begin_row='2', begin_column='E',
                   end_row='20', end_column='T', save_path=r'D:\images\report.png',
                   sheet_name='每日报表')

refresh_pivot_table.main({'excel_instance': workbook, 'sheet_name': '汇总'})
```

## A 单元格填充

### 批量向下填充(公式) — `fill_down_formula`

**签名** `fill_down_formula(excel_instance, formula_content, column, begin_row, end_row, sheet_name, 数组公式, is_cover_format)`

在单列中从起始行往下写公式。`end_row=''` 按 `-1` 处理。`数组公式=True` 时优先尝试 `Formula2`，失败后尝试 `FormulaArray`。`is_cover_format=True` 用表格应用的向下填充，`False` 直接给区间赋同一公式字符串。当前实现先定位可见起始行，随后操作连续区域，筛选状态下也可能写到中间隐藏行。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `formula_content` | 填充内容(公式) | str | `''` | 输入起始单元格的公式内容 |
| `column` | 列名 | str | `''` | 待填充区域的列号 |
| `begin_row` | 开始行号 | str | `''` | 待填充区域起始单元格行号 |
| `end_row` | 结束行号 | str | `''` | 待填充区域结束单元格行号 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `数组公式` | 数组公式 | bool | `False` | — |
| `is_cover_format` | 覆盖原单元格格式 | bool | `True` | 默认覆盖原格式 |

**输出** 无声明输出。

### 批量向右填充(公式) — `fill_right_formula`

**签名** `fill_right_formula(excel_instance, formula_content, row, begin_column, end_column, sheet_name, array_formula_mode)`

从一行的起始列向右填充公式。`end_column=''` 按 `-1` 处理。`array_formula_mode=True` 时优先尝试 `Formula2`，失败后尝试 `FormulaArray`。写起始格后按连续范围执行向右填充。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `formula_content` | 填充内容(公式) | str | `''` | 输入起始单元格的公式内容 |
| `row` | 行号 | str | `''` | 待填充区域的行号 |
| `begin_column` | 开始列名 | str | `''` | 待填充区域起始单元格列号 |
| `end_column` | 结束列名 | str | `''` | 待填充区域结束单元格列号, 默认填写最后一列 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `array_formula_mode` | 数组公式 | bool | `False` | 数组公式 |

**输出** 无声明输出。

### 自动向下填充 — `process31`

**签名** `process31(excel_instance, begin_column, begin_row, end_column, end_row, sheet_name, 填充类型)`

以给定范围的首行为填充起点，支持多列。开始行和结束行相同会直接退出。`填充类型` 是公开参数的原名，枚举值采用字符串。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `begin_column` | 开始列号 | str | `''` | 待填充区域起始单元格列名 |
| `begin_row` | 开始行号 | str | `''` | 待填充区域起始单元格行号 |
| `end_column` | 结束列号 | str | `''` | 待填充区域结束单元格列名 |
| `end_row` | 结束行号 | str | `''` | 填充的结束行。 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `填充类型` | 填充类型 | str | `''` | 待填充的类型。`'0'` 默认填充、`'1'` 拷贝填充、`'2'` 序列填充、`'11'` 快速填充 |

**输出** 无声明输出。

### 单元格填充图片 — `process18`

**签名** `process18(excel_instance, image_path, row_num, column_name, row_height, colnum_width, lockaspectratio, placement, sheet_name, compress, is_insert_only)`

插入的是浮动图片对象，图片以单元格左上角定位。`placement='1'` 会随单元格移动和缩放，保存后仍是浮动对象。`lockaspectratio`、`placement` 在外层留空时是 `''`，底层直接转整数，调用时应传明确值。图片先插入，再设置纵横比和定位，后续参数报错时可能已插入图片。只有同时设置 `row_height` 和 `colnum_width` 才调整行高、列宽并按单元格尺寸设置图片，建议两项都传整数文本；两项未同时设置时，合并格分支会调整图片高度。网络地址交给表格应用尝试加载，源码也提示网络图片失败时可先下载到本地。`compress=True` 走 `Shapes.AddPicture2`，否则走 `Shapes.AddPicture`。`is_insert_only=True` 关闭源文件链接。此安装副本的公开入口及源码均未发现 `InsertCellPicture`。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `image_path` | 图片路径 | str | `''` | 插入单元格图片的路径, 本地地址或网络地址 |
| `row_num` | 行号 | str | `''` | 插入单元格图片的行号 |
| `column_name` | 列名 | str | `''` | 插入单元格图片的列名 |
| `row_height` | 行高 | str | `''` | 插入单元格图片的行高 |
| `colnum_width` | 列宽 | str | `''` | 插入单元格图片的列宽 |
| `lockaspectratio` | 锁定纵横比 | str | `''` | 是否锁定图片纵横比。`'0'` 取消、`'-1'` 锁定 |
| `placement` | 图片属性 | str | `''` | 图片与单元格的关系。`'2'` 随单元格改变位置，但不改变大小、`'3'` 不随单元格改变位置和大小、`'1'` 随单元格改变位置和大小 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `compress` | compress | bool | `False` | 是否压缩插入的图片 |
| `is_insert_only` | is_insert_only | bool | `False` | 是否只插入图片而不链接 |

**输出** 无声明输出。

### 空白单元格填充(向上填充) — `process36`

**签名** `process36(excel_instance, sheet_name, begin_row, begin_column, end_row, end_column)`

在指定区域的空白格写入引用正上方单元格的公式。连续空白格会沿着上方引用链得到值。显示为空、但已经有公式的格子会保留其公式。结束行、列留空按 `-1` 处理。单格范围直接退出。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `begin_row` | 开始行号 | str | `''` | 待填充区域起始单元格行号 |
| `begin_column` | 开始列名 | str | `''` | 待填充区域起始单元格列名 |
| `end_row` | 结束行号 | str | `''` | 待填充区域结束单元格行号 |
| `end_column` | 结束列名 | str | `''` | 待填充区域结束单元格列名 |

**输出** 无声明输出。

### 公式转换成值 — `process52`

**签名** `process52(excel_instance, sheet_name, set_range, dim)`

把范围里的公式替换为当前计算值。`COLUMN` 支持逗号分隔的多列，`ROW` 传单行，`CELL` 传如 `A1`，`RANGE` 传如 `A1:D20`，`USEDRANGE` 使用当前工作表已用区域。转换后对应单元格原公式会被覆盖。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `set_range` | 转换区域 | str | `''` | 公式转换成值的区域 |
| `dim` | 转换范围 | str | `''` | 公式转换成值的范围。`'COLUMN'` 列、`'ROW'` 行、`'RANGE'` 区域、`'CELL'` 单元格、`'USEDRANGE'` 已使用区域 |

**输出** 无声明输出。

### 新建注释 — `process53`

**签名** `process53(excel_instance, sheet_name, row_num, column_name, comment)`

在指定格添加传统注释。已有注释时更新正文。用 `comment` 传文本，行和列按单元格坐标传入。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `row_num` | 行号 | str | `''` | 待新建注释单元格的行号 |
| `column_name` | 列名 | str | `''` | 待新建注释单元格的列名 |
| `comment` | 注释 | str | `''` | 注释的内容 |

**输出** 无声明输出。

## B 单元格操作

### 分列 — `process19`

**签名** `process19(excel_instance, column, tab, semicolon, comma, space, otherchar, row_start, row_end, column_num, sheet_name, destination_column, field_info, consecutive_delimiter)`

按分隔符将一列拆为多列。起止行留空取 `1`、`-1`，目标列留空从原列开始。`field_info` 会直接转整数，应明确选择类型。填 `column_num` 时会在源列右边插入所需列，已有列可能右移；留空时分列结果可能覆盖后方数据。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `column` | 列号 | str | `''` | 待分列列名 |
| `tab` | tab | bool | `True` | — |
| `semicolon` | semicolon | bool | `False` | — |
| `comma` | comma | bool | `False` | — |
| `space` | space | bool | `False` | — |
| `otherchar` | 其他字符 | str | `''` | 其它分隔符，例如竖线。 |
| `row_start` | 开始行号 | str | `''` | 分列开始行号 |
| `row_end` | 结束行号 | str | `''` | 分列结束行号 |
| `column_num` | 列数 | str | `''` | 拆分后的目标列数。留空可能覆盖后方数据。 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `destination_column` | 目标区域 | str | `''` | 分列后的目标区域 |
| `field_info` | 列数据格式 | str | `''` | 分列后的字段类型。`'1'` 常规、`'2'` 文本、`'3'` 日期MDY、`'5'` 日期YMD |
| `consecutive_delimiter` | consecutive_delimiter | bool | `False` | 连续分隔符号视为单个处理(R) |

**输出** 无声明输出。

### 内容替换 — `process26`

**签名** `process26(excel_instance, search_text, replace_text, 替换区域, lookat, sheet_name, 替换范围, case_sensitive)`

只接受字符串查找值和替换值。`替换范围='SHEET'` 作用于工作表已使用区域，`COLUMN` 支持逗号分隔的列名，`ROW` 使用行号，`RANGE` 使用如 `A1:D20` 的区域地址。`替换范围`、`替换区域` 是原样使用的 Python 参数名。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel 对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `search_text` | 查找内容 | str | `''` | 输入查找内容 |
| `replace_text` | 替换文本 | str | `''` | 输入替换内容 |
| `替换区域` | 替换区域 | str | `''` | 替换范围为Sheet页, 不填; 替换范围为列, 填写对应列名; 替换范围为行, 填写对应行号 |
| `lookat` | 匹配方式 | str | `''` | `'1'` 相等、`'2'` 包含 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `替换范围` | 替换范围 | str | `''` | 指定待替换区域维度。`'SHEET'` Sheet页、`'COLUMN'` 列、`'ROW'` 行、`'RANGE'` 区域 |
| `case_sensitive` |  | bool | `False` | 是否区分大小写 |

**输出** 无声明输出。

### 区域截图 — `process24`

**签名** `process24(excel_instance, begin_row, begin_column, end_row, end_column, save_path, sheet_name)`

对指定区域截图。会尝试激活目标 Sheet 并使用 Windows 剪贴板，流程会清理剪贴板。`end_row=''` 按 `-1` 处理，结束列需填写。`save_path` 推荐填写带目录的文件路径或目录路径：有文件扩展名时按文件名保存，无扩展名时在指定目录生成 PNG。流程输出 `image_save_path` 是保存路径。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `begin_row` | 开始行号 | str | `''` | 待截取区域起始单元格行号 |
| `begin_column` | 开始列名 | str | `''` | 待截取区域起始单元格（左上角）列名 |
| `end_row` | 结束行号 | str | `''` | 待截取区域结束单元格行号 |
| `end_column` | 结束列名 | str | `''` | 待截取区域结束单元格（右下角）列名 |
| `save_path` | 保存路径 | str | `''` | 图片文件路径或目录路径。 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |

**输出** `image_save_path`。图片保存路径 `str`。

### 区域文本转数字 — `text_format_to_num`

**签名** `text_format_to_num(excel_instance, begin_row, begin_column, end_row, end_column, sheet_name)`

按通用格式重写范围的值。起始行、列留空取 `1`、`A`，结束行和列留空都取 `-1`。界面的结束行提示写成了 `1`，当前实现取最后一行。范围内的公式也会被重写为值。大范围会一次读取和写回数据。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `begin_row` | 开始行号 | str | `''` | 待转换区域起始单元格行号 |
| `begin_column` | 开始列名 | str | `''` | 待转换区域起始单元格列名 |
| `end_row` | 结束行号 | str | `''` | 转换的结束行。留空按最后一行。 |
| `end_column` | 结束列名 | str | `''` | 待转换区域结束单元格列名 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |

**输出** 无声明输出。

### 区域数字转文本 — `num_format_to_text`

**签名** `num_format_to_text(excel_instance, begin_row, begin_column, end_row, end_column, sheet_name)`

逐列执行文本转换。起始行、列留空取 `1`、`A`，结束行和列留空取 `-1`。WPS 分支会把涉及的整列设为文本格式，因此格式变化可超出指定行范围。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `begin_row` | 开始行号 | str | `''` | 待转换区域起始单元格行号 |
| `begin_column` | 开始列名 | str | `''` | 待转换区域起始单元格列名 |
| `end_row` | 结束行号 | str | `''` | 待转换区域结束单元格行号 |
| `end_column` | 结束列名 | str | `''` | 待转换区域结束单元格列名 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |

**输出** 无声明输出。

### 读取单元格注释 — `process37`

**签名** `process37(excel_instance, row, column, sheet_name)`

读取传统单元格注释的正文。没有注释时实现返回 `None`。接口读取的是表格应用的 `Comment` 对象。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `row` | 单元格行号 | str | `''` | 待提取备注单元格行号 |
| `column` | 单元格列名 | str | `''` | 待提取备注单元格列名 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |

**输出** `comment`。注释正文 `str` 或 `None`。

### 合并单元格 / 取消单元格合并 — `process34`

**签名** `process34(excel_instance, sheet_name, begin_row, begin_column, end_row, end_column, is_merge)`

按矩形范围合并或取消合并。结束行、列留空按 `-1` 处理。通过 `is_merge='1'` 合并，传 `'0'` 取消。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `begin_row` | 开始行号 | str | `''` | 待合并单元格开始行号 |
| `begin_column` | 开始列名 | str | `''` | 待合并单元格开始列名 |
| `end_row` | 结束行号 | str | `''` | 待合并单元格结束行号 |
| `end_column` | 结束列名 | str | `''` | 待合并单元格结束列名 |
| `is_merge` | 操作 | str | `''` | 合并操作。`'1'` 合并单元格、`'0'` 取消单元格合并 |

**输出** 无声明输出。

### 设置单元格超链接 — `process33`

**签名** `process33(excel_instance, sheet_name, row_num, col_name, address, subaddress, screentip, texttodisplay)`

为单元格设置超链接。`address` 用于外部地址，`subaddress` 用于工作簿内的跳转位置。`texttodisplay=''` 时会优先取现有单元格值作为显示文本。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `row_num` | 行号 | str | `''` | 设置单元格超链接的行号 |
| `col_name` | 列名 | str | `''` | 设置单元格超链接的列名 |
| `address` | 超链接地址 | str | `''` | 超链接地址 |
| `subaddress` | 超链接子地址 | str | `''` | 超链接子地址 |
| `screentip` | 屏幕提示 | str | `''` | 屏幕提醒 |
| `texttodisplay` | 超链接显示文本 | str | `''` | 数据展示 |

**输出** 无声明输出。

### 获取单元格超链接 — `process32`

**签名** `process32(excel_instance, row_num, col_name, sheet_name)`

读取单元格的首个超链接。有子地址时返回 `地址#子地址`，无超链接时返回 `None`。可以用于读取表格里的跳转链接。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `row_num` | 单元格行号 | str | `''` | 获取单元格超链接的行号 |
| `col_name` | 单元格列名 | str | `''` | 获取单元格超链接的列名 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |

**输出** `hyperlink`。链接文本 `str` 或 `None`。

### 导出单元格的图片 — `process42`

**签名** `process42(excel_instance, sheet_name, column_name, folder_path, row_number)`

按图片左上角所在的单元格匹配浮动图片，将图片写入已存在的 `folder_path` 目录，输出 PNG。没有匹配返回 `None`，单张是路径字符串，多张是路径列表，界面只标注了 `str`。会操作 Windows 剪贴板，部分图片在导出过程中会临时调整缩放。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel 对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `sheet_name` | Sheet 页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `column_name` | 列名 | str | `''` | 待导出单元格列名 |
| `folder_path` | 保存在文件夹 | str | `''` | 图片保存文件夹 |
| `row_number` | 行号 | str | `''` | 待导出单元格行号 |

**输出** `pic_path`。路径 `str`、路径列表，或 `None`。

### 删除单元格的图片 — `process45`

**签名** `process45(Excel对象, Sheet页名称, 行号, 列名)`

按图片左上角所在的单元格匹配，删除该位置所有符合类型条件的浮动图形。该筛选还包含类型 `1` 的自选图形。未匹配时返回。参数名 `Excel对象`、`Sheet页名称`、`行号`、`列名` 要原样使用。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `Excel对象` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `Sheet页名称` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `行号` | 行号 | str | `''` | — |
| `列名` | 列名 | str | `''` | — |

**输出** 无声明输出。

### 获取背景色 — `process54`

**签名** `process54(excel_instance, dim, target_range, sheet_name)`

取区域的 `Interior.Color` 并换算为 `(R, G, B)` 元组。界面标注 `list`，并描述无填充时返回 `None`；当前实现没有无填充专门分支，不能据此判断未填色。`ROW` 分支校验行号后仍将原传参交给表格应用，负数行号不宜据此视为已支持。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel 对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `dim` | 获取范围 | str | `''` | 获取范围。`'RANGE'` 区域、`'ROW'` 行、`'COLUMN'` 列 |
| `target_range` | 获取区域 | str | `''` | 获取区域 |
| `sheet_name` | Sheet 页名称 | str | `''` | 留空取当前活动 Sheet。 |

**输出** `background_color`。三个整数构成的 RGB 元组。

### 获取合并单元格区域 — `process55`

**签名** `process55(excel_instance, row, column, sheet_name)`

流程声明两个输出 `is_merge`、`merge_range`。范围字符串会去掉 `$`，普通未合并格也会按 `MergeArea` 取地址，使用时先看 `is_merge`。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel 对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `row` | 行号 | str | `''` | 合并单元格的行 |
| `column` | 列名 | str | `''` | 合并单元格的列 |
| `sheet_name` | Sheet 页名称 | str | `''` | 留空取当前活动 Sheet。 |

**输出** `is_merge`（`bool`）和 `merge_range`（`str`）。

## C 筛选

### 筛选 — `filter`

**签名** `filter(excel_instance, row, column, select_content, select_type, sheet_name, operator, select_content2, select_type2)`

按列筛选工作表。`row=''` 使用第 1 行。条件模板里的 `{0}` 由筛选值填入。条件值可传字符串或数字。`select_content` 是列表时只实现等于或不等于，且不能与 `operator='1'` 或 `'2'` 配合；处理列表里的 `None` 时会原地改变传入的列表。列表类型虽未体现在界面声明中，当前实现有明确的分支。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `row` | 筛选行号 | str | `''` | 待筛选的行号 |
| `column` | 筛选列号 | str | `''` | 待筛选的列号 |
| `select_content` | 筛选内容 | str | `''` | 要筛选的内容 |
| `select_type` | 筛选类型 | str | `''` | 选择筛选类型相等/不相等/包含/不包含。`'={0}'` 等于、`'<>{0}'` 不等于、`'=*{0}*'` 包含、`'<>*{0}*'` 不包含、`'={0}*'` 开头是、`'<>{0}*'` 开头不是、`'=*{0}'` 结尾是、`'<>*{0}'` 结尾不是、`'>{0}'` 大于、`'>={0}'` 大于或等于、`'<{0}'` 小于、`'<={0}'` 小于或等于 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `operator` | 筛选关系 | str | `''` | 筛选运算符。`'7'` 不使用条件2、`'2'` 或、`'1'` 且 |
| `select_content2` | 筛选内容2 | str | `''` | 第二个条件的比较值。 |
| `select_type2` | 筛选类型2 | str | `''` | 第二个条件的比较模板，取值与 `select_type` 相同。`'={0}'` 等于、`'<>{0}'` 不等于、`'=*{0}*'` 包含、`'<>*{0}*'` 不包含、`'={0}*'` 开头是、`'<>{0}*'` 开头不是、`'=*{0}'` 结尾是、`'<>*{0}'` 结尾不是、`'>{0}'` 大于、`'>={0}'` 大于或等于、`'<{0}'` 小于、`'<={0}'` 小于或等于 |

**输出** 无声明输出。

### 筛选颜色 — `process38`

**签名** `process38(excel_instance, sheet_name, row_num, column_name, xl_filter, rgb)`

`xl_filter='8'` 按填充颜色筛选，`'9'` 按字体颜色筛选，`'12'` 筛选无填充。前两种传入 RGB 文本如 `'(255,255,0)'`。当前实现会把 RGB 文本作为 Python 表达式求值，因此仅应传脚本内固定的 RGB 常量，或由校验过的三个整数生成的字面量。WPS 分支遇到不支持无填充筛选时会报错。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `row_num` | 筛选行号 | str | `''` | 待筛选的行号 |
| `column_name` | 筛选列名 | str | `''` | 待筛选的列名 |
| `xl_filter` | 筛选类型 | str | `''` | 筛选类型。`'8'` 填充颜色、`'9'` 字体颜色、`'12'` 无填充 |
| `rgb` | RGB颜色 | str | `''` | RGB 文本，例如 `'(255,255,0)'`。 |

**输出** 无声明输出。

### 清除筛选 — `process16`

**签名** `process16(excel_instance, sheet_name, column_name)`

清除工作表筛选。`column_name=''` 关闭整表筛选；填列名时先按该列清除普通筛选。若使用区域识别到结构化表格，另有整表筛选处理，指定列也可能影响该表格的其他列和筛选下拉。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `column_name` | 列名 | str | `''` | 不填, 清除全部筛选 |

**输出** 无声明输出。

### 读取筛选内容 — `process21`

**签名** `process21(excel_instance, begin_row, sheet_name, content_type, using_text, using_text_cols, data_columns)`

`begin_row=''` 从第 2 行开始。`data` 返回行数据，设置 `data_columns` 时实现可能给出由元组组成的列表。`first_row` 返回首个可见的行号或 `None`，`all_row` 返回可见行号列表，部分无结果或调用失败的分支可能返回 `None`。`using_text=True` 按指定列读取显示值，`using_text_cols=''` 按所有列处理。`data` 分支会使用剪贴板、创建并删除临时 Sheet，再激活原 Sheet。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `begin_row` | 开始行号 | str | `''` | 筛选结果开始的行号, 选填, 默认为 2 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `content_type` | 读取类型 | str | `''` | 读取数据的类型。`'data'` 筛选数据、`'first_row'` 筛选区域首行、`'all_row'` 筛选区域全部行号 |
| `using_text` | 读取单元格显示的内容 | bool | `False` | 读取单元格显示的内容 |
| `using_text_cols` | 显示内容的列 | str | `''` | 多个列名以,分割,若空表示所有列, 但读取速度会较慢 |
| `data_columns` | 读取指定列数据 | str | `''` | 用于读取指定列的内容 |

**输出** `filter_content`。根据模式得到行数据、行号或行号列表。

### 删除筛选内容 — `process20`

**签名** `process20(excel_instance, begin_row, end_row, removefiltermode, sheet_name)`

删除指定行范围内的可见行。开始、结束留空取 `2`、`-1`。如果没有有效筛选，范围内所有可见行均可能被删除。删除操作异常被内部捕获，`removefiltermode=True` 仍可能关闭筛选，调用返回本身无法证明删除成功。源码未验证结构化表格与各软件版本的表现。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `begin_row` | 开始行号 | str | `''` | 删除筛选内容开始行号 |
| `end_row` | 结束行号 | str | `''` | 删除筛选内容结束行号 |
| `removefiltermode` | null | bool | `True` | 清除筛选状态 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |

**输出** 无声明输出。

## D 其他

### 数字列名转换 — `process23`

**签名** `process23(text_input, convert_type)`

转换单个列标。`column2num` 输入单个字母列名，例如 `AA`，返回整数 `27`。`num2column` 输入单个正整数或其文本，例如 `'27'`，返回 `'AA'`。界面把输出标为 `str`，实际方向决定其类型。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `text_input` | 转换内容 | str | `''` | 转换内容 |
| `convert_type` | 转换方式 | str | `''` | 转换方式。`'column2num'` 列名转数字、`'num2column'` 数字转列名 |

**输出** `convert_result`。列号 `int` 或列标 `str`。

### 查找数据所在列 — `process27`

**签名** `process27(excel_instance, search_text, lookat, sheet_name, find_all, row, look_in, num_flag)`

在指定行查找列位置。`row` 支持逗号分隔的行号，传多行时实现从首个行号到最后一个行号按连续矩形搜索。`find_all='True'` 返回排序后的结果列表，`'False'` 返回第一项或 `None`。`num_flag=True` 返回列号，`False` 返回列字母。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel 对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `search_text` | 查找内容 | str | `''` | 待查找的文本 |
| `lookat` | 匹配方式 | str | `''` | 对查找内容整体还是对查找内容的部分进行匹配。`'1'` 相等、`'2'` 包含 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `find_all` | 查找范围 | str | `''` | 找到第一个还是找到全部位置。`'False'` 第一个、`'True'` 全部 |
| `row` | 查找行号 | str | `''` | 待查找的行号 |
| `look_in` | 查找类型 | str | `'-4123'` | 查找值或公式。`'-4123'` 公式、`'-4163'` 值 |
| `num_flag` | num_flag | bool | `False` | 是否返回数字列号。 |

**输出** `column_name`。列字母 `str`、数字列号 `int`、列表，或 `None`。

### 查找数据所在行 — `process28`

**签名** `process28(excel_instance, search_text, lookat, sheet_name, find_all, column, look_in)`

在指定列查找行位置。`column` 可传单列，或逗号分隔的列名；多列时按首尾列包围的矩形查找。`find_all='False'` 返回单个行号或 `None`，`'True'` 返回排序后的行号列表。`find_all` 请传字符串，以匹配实现的分支。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel 对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `search_text` | 查找内容 | str | `''` | 待查找的文本 |
| `lookat` | 匹配方式 | str | `''` | 对查找内容整体还是对查找内容的部分进行匹配。`'1'` 相等、`'2'` 包含 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `find_all` | 查找范围 | str | `''` | 找到第一个还是找到全部位置。`'False'` 第一个、`'True'` 全部 |
| `column` | 查找列名 | str | `''` | 待查找的列名 |
| `look_in` | 查找类型 | str | `'-4123'` | 查找值或公式。`'-4123'` 公式、`'-4163'` 值 |

**输出** `查找结果`。行号 `int`、行号列表，或 `None`。

### 生成字典(列表拼接) — `process30`

**签名** `process30(excel_instance, begin_row, key_column, value_column, end_row, sheet_name)`

按键列分组，按原始行次序收集各行的值。`begin_row=''` 取 `2`，`end_row=''` 取 `-1`。单值列得到如 `{'A': [10, 20]}`，多值列得到如 `{'A': [[10, '甲'], [20, '乙']]}`。元数据将输出标为 `str`，实现产生字典。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `begin_row` | 开始行号 | str | `''` | 开始行号 |
| `key_column` | 键列名 | str | `''` | 键对应的列 |
| `value_column` | 值列名 | str | `''` | 值对应的列 |
| `end_row` | 结束行号 | str | `''` | 结束行号 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |

**输出** `result_dict`。以键对应多行值的字典。

### 生成字典(数值累加) — `process29`

**签名** `process29(excel_instance, begin_row, key_column, value_column, sheet_name, end_row)`

按键列分组，把同键的值相加。`begin_row=''` 取 `2`，`end_row=''` 取 `-1`。值列要求数值，空值按 `0` 参与运算，结果值为浮点数。元数据将输出标为 `str`，实现产生字典。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `begin_row` | 开始行号 | str | `''` | 开始行号 |
| `key_column` | 键列名 | str | `''` | 键对应的列 |
| `value_column` | 值列名 | str | `''` | 值对应的列 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `end_row` | 结束行号 | str | `''` | 结束行号 |

**输出** `result_dict`。以键对应累加值的字典。

### 删除所有图片 — `process44`

**签名** `process44(excel_instance, sheet_name)`

删除指定工作表内符合实现图形类型筛选条件的对象，整张 Sheet 生效。该筛选还包含类型 `1` 的自选图形，目标 Sheet 上用于展示的图形也可能被删。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel 对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `sheet_name` | Sheet 页 | str | `''` | 留空取当前活动 Sheet。 |

**输出** 无声明输出。

### 隐藏 / 取消隐藏 Sheet 页 — `process46`

**签名** `process46(Excel对象, Sheet页名称, 设置为)`

隐藏或显示一张已存在的 Sheet。必须传入 `Sheet页名称`，`设置为` 用 `'隐藏'` 或 `'显示'`。实现只把精确的 `'隐藏'` 当作隐藏，其它值走显示分支。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `Excel对象` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `Sheet页名称` | Sheet页名称 | str | `''` | — |
| `设置为` | 设置为 | str | `''` | `'隐藏'` 隐藏、`'显示'` 显示 |

**输出** 无声明输出。

### 获取隐藏的 Sheet 页 — `process47`

**签名** `process47(Excel对象)`

返回实现判定为隐藏的工作表名列表。判断条件是工作表的 `Visible` 值为假。返回非零 `Visible` 值的隐藏状态不会被这个判断收录。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `Excel对象` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |

**输出** `隐藏的工作表名列表`。工作表名称列表。

### 合并计算 — `process48`

**签名** `process48(Excel对象, Sheet页名称, 行号, 列名, 所引用的位置, 函数, 首列, 最左侧, 创建指向数据源的链接)`

把多个区域按指定函数汇总到目标单元格。`所引用的位置` 为字符串，每项采用 `源表!$A$2:$D$20` 这样的形式，多项用 `\r\n` 分隔。当前实现解析了源区域起始行，但随后取目标 `行号` 作为源起始行。源起始行与目标行不同时，实际汇总范围可能偏移，使用前应针对同版确认结果。`首列` 实际传给表格应用的顶行标签参数，`最左侧` 传给左列标签参数。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `Excel对象` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `Sheet页名称` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `行号` | 行号 | str | `''` | 汇总结果存放位置的行号 |
| `列名` | 列名 | str | `''` | 汇总结果存放位置的列名 |
| `所引用的位置` | 所引用的位置 | str | `''` | 引用数据的表格区域 |
| `函数` | 函数 | str | `''` | 合并计算应用的公式。`'-4157'` 求和、`'-4112'` 计数、`'-4106'` 平均值、`'-4136'` 最大值、`'-4139'` 最小值、`'-4149'` 乘积、`'-4113'` 数值计数、`'-4155'` 标准偏差、`'-4156'` 总体标准偏差、`'-4164'` 方差、`'-4165'` 总体方差 |
| `首列` | 首行 | bool | `False` | 是否使用顶行作为标签。 |
| `最左侧` | 最左列 | bool | `True` | 是否使用左列作为标签。 |
| `创建指向数据源的链接` | 创建指向数据源的链接 | bool | `False` | 创建指向数据源的链接 |

**输出** 无声明输出。

### 设置/取消密码 — `process49`

**签名** `process49(Excel对象, 打开密码, 编辑密码)`

设置打开密码和编辑密码，空字符串用于取消对应密码。会按当前文件名和原格式直接保存，WPS 还会额外尝试设置属性并保存。源码备注 WPS 设置编辑密码有限制，是否生效需按实际版本核对。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `Excel对象` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `打开密码` | 打开密码 | str | `''` | 打开Excel文件的密码, 设置空字符串表示取消密码 |
| `编辑密码` | 编辑密码 | str | `''` | 编辑Excel文件的密码, 设置空字符串表示取消密码 |

**输出** 无声明输出。

### 自动换行 — `process51`

**签名** `process51(Excel对象, Sheet页名称, 自动换行范围, 自动换行区域, operation)`

在指定范围启用或取消自动换行。`自动换行范围` 决定选区类型，`自动换行区域` 填对应地址。行和列模式的实现按单个行号或列名解析，界面示例里逗号分隔的多行多列写法不宜当作已支持。`operation` 使用字符串 `'TRUE'` 或 `'FALSE'`。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `Excel对象` | Excel对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `Sheet页名称` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `自动换行范围` | 范围 | str | `''` | 自动换行的范围, 如已使用区域, 行, 列, 单元格。`'USEDRANGE'` 已使用区域、`'COLUMN'` 列、`'ROW'` 行、`'CELL'` 单元格、`'RANGE'` 区域 |
| `自动换行区域` | 区域 | str | `''` | 自动换行的具体位置 |
| `operation` | 操作 | str | `''` | `'TRUE'` 自动换行、`'FALSE'` 取消换行 |

**输出** 无声明输出。

### 冻结首行 — `process56`

**签名** `process56(excel_instance, sheet_name, kind, area)`

按行、列、区域冻结，或解除冻结。`ROW` 传一个行号，`COLUMN` 传一个列名，`RANGE` 传如 `A1:B2`，按尾格设置冻结的行列数，`UNFREEZE` 的 `area` 传空字符串。修改的是表格程序的活动窗口，`sheet_name` 在此用于位置解析，代码没有通过它切换活动 Sheet。调用前先确认要冻结的是当前活动页。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel 对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `sheet_name` | Sheet 页名称 | str | `''` | 留空取当前活动 Sheet。 |
| `kind` | 冻结范围 | str | `''` | 冻结范围。`'ROW'` 行、`'COLUMN'` 列、`'RANGE'` 区域、`'UNFREEZE'` 取消冻结 |
| `area` | 冻结区域 | str | `''` | 一个行号、一个列名或矩形范围地址，由 `kind` 决定。 |

**输出** 无声明输出。

### 设置切片器 — `process57`

**签名** `process57(excel_instance, slicercache_name, item_name, selected)`

按切片器缓存名称定位切片器，`item_name` 可传单个字符串或列表。`selected=True` 选择匹配项并尝试取消其它项，`False` 取消匹配项。使用当前活动工作簿的切片器缓存。找不到项只记日志，部分表格应用调用异常会被内部捕获，流程返回不能证明筛选已生效。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel 对象 | 影刀工作簿 | `None` | 传入已打开的影刀 Office/WPS 工作簿。 |
| `slicercache_name` | 切片器名称 | str | `''` | 切片器的名称 |
| `item_name` | 项名称 | str | `''` | 要选中或取消选中的项，可传名称字符串或名称列表。 |
| `selected` |  | bool | `True` | 勾选或者取消勾选 |

**输出** 无声明输出。

### 执行文本宏 — `process58`

**签名** `process58(excel_instance, macro_string, macro_name)`

在目标工作簿的 VBA 工程中创建临时模块并执行，再尝试删除临时模块。`macro_string` 传过程体，`macro_name` 传过程名，流程会自行组装 `Sub ... End Sub`。界面将 `excel_instance` 标为 `str`，实现却直接使用工作簿的 `workbook` 和 `xlApp` 属性，应传影刀工作簿对象。是否可调用由宿主的 VBA 和工程访问权限决定，本次未运行宏。

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel 对象 | 影刀工作簿 | `''` | 供 VBA 操作的实际工作簿。 |
| `macro_string` | 宏文本 | str | `''` | 宏过程体。 |
| `macro_name` | 宏名称 | str | `''` | 宏过程名。 |

**输出** 无声明输出。

### 刷新透视表 — `refresh_pivot_table`

**签名** `main(args)`

通过模块的 `main(args)` 接收字典。会激活指定 Sheet，然后逐个刷新其中透视表的数据缓存。`sheet_name=''` 作用于该工作簿当前页。`main` 源码把 `get_active_workbook()` 直接写在字典默认值里，因此即使传入 `excel_instance`，也会先求值一次，运行前仍需存在可获取的活动工作簿。编码版元数据也暴露了模块内的 `refresh(excel_instance, sheet_name)`，其调用使用显式工作簿和 Sheet 参数。

`args` 的字段如下。

**模块签名** `refresh(excel_instance, sheet_name)` 和 `main(args)`

| 参数 | 界面含义 | 类型 | 流程默认 | 说明 |
| --- | --- | --- | --- | --- |
| `excel_instance` | Excel 对象 | 影刀工作簿 | 当前活动工作簿 | 传入已打开的影刀 Office/WPS 工作簿。显式传入 `None` 不会触发默认值。 |
| `sheet_name` | Sheet页名称 | str | `''` | 留空取当前活动 Sheet。 |

**输出** 无声明输出。

## 安装副本文件索引

| 文件 | 用途 |
| --- | --- |
| `package.json` | 扩展版本、流程清单、流程分组以及 Visual / Code 类型。 |
| `prototype.block.json` | 可视化指令标题、公开状态、参数、选项、输出。以 `hidden=false` 认定公开指令。 |
| `prototype.activity.xml` | 编码版发现的调用入口。透视表模块内列出 `main` 和 `refresh`。 |
| `__init__.py` | 39 个公开可视化流程的包装函数、参数和声明输出。 |
| 40 个同名流程 `.py` | 包装函数下游的公开流程定义，对照上方总表的入口名查找。 |
| `invoke_modules.py`、`utils.py`、`validators.py` | 主要实现、超链接读取及通用校验，用于核实行为和限制。 |
| `main.py`、`filldown.py`、`iexcel.py`、`tmp.py`、`process50.py` | 隐藏流程。旧自动换行的 `process50` 隐藏，公开自动换行使用 `process51`。 |
| `test_*.py` | 20 个隐藏测试流程，本次未执行。 |
| `package.py`、`settings.json`、`package.sigstore` | 运行时的包定义、配置和包签名文件。 |
| `selectors*.xml`、`images*.xml` | 影刀选择器、图片资源定义。 |
| `__pycache__`、`logs` | 运行产生的缓存和日志。 |

### 隐藏流程清单

- 内部流程 `main.py`、`utils.py`、`validators.py`、`invoke_modules.py`、`tmp.py`、`process50.py`、`iexcel.py`、`filldown.py`。
- 测试流程 `test_utils.py`、`test_invoke_modules.py`、`test_excel_get_filter_content.py`、`test_gen_dict_for_key_columns_and_value_columns_combined.py`、`test_excel_range_screenshot.py`、`test_excel_filldown.py`、`test_excel_autofilter.py`、`test_excel_auto_filldown.py`、`test_excel_remove_filtermode.py`、`test_gen_dict_from_two_column_and_value_sum.py`、`test_execl_export_cell_picture.py`、`test_delete_cell_picture.py`、`test_excel_filter_and_delete.py`、`test_excel_add_picture.py`、`test_excel_get_range_background_color.py`、`test_excel_get_merge_cell.py`、`test_excel_replace.py`、`test_excel_freeze.py`、`test_excel_autofilter_color.py`、`test_excel_get_content_column_in_row.py`。

## 核验记录

- `package.json`、`prototype.block.json` 声明的流程总数均为 68。40 条公开指令都在编码元数据中找到对应入口。其余为 28 条隐藏流程，其中 20 条是测试流程。
- 公开指令的参数名、顺序、枚举和声明输出已逐项与当前安装副本核对。主要行为及界面标注差异通过流程代码和实现交叉验证。
- 旧版知识页依据 2026-07-13 版，本页依据 `package.json` 明确声明的 `26.10.5`。向下公式填充签名包含 `is_cover_format`，本版横向填充仍使用 `array_formula_mode`。使用其它安装版本时可用 `inspect.signature()` 对照公开包装函数。
- 证据指纹（SHA-256）
  - `package.json` `331607ac0696eb392e2fd74b867a7765116bf044408213679eca98993f5dc2b9`
  - `prototype.block.json` `fedadfcab8eda6e37da8e19d5c60aa65b8c5db250fd2d12597e33ba42431d270`
  - `__init__.py` `567fb39fa26cb267e9fd64f321d77d4ac79ba37031d0813649dfab722cc8dd47`
  - `prototype.activity.xml` `5a976fdecab0c1995afc580630d779c3e54d915c6934703f86a32da62e5ff178`
- 未执行插图、删除、另存、宏与其它表格操作。
