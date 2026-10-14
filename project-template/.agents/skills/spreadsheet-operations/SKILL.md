---
name: spreadsheet-operations
description: 影刀编码版使用 WPS 更新 Excel/CSV 表格的固定操作规范，包括打开、最大化、区域读写、多 Sheet 更新、保存与关闭。
---

# 表格操作（影刀 WPS）

开发影刀表格更新程序时遵守本页。API 参数和返回值查 [xbot.excel 正式文档](../../../../xbot-api-docs/docs/excel.md)；业务模块命名与函数边界见 [编程风格](../code-quality/references/coding-style.md)。不重复加载其它表格操作规范。

## 打开与使用工作簿

1. 本轮程序第一次打开 WPS 前，直接调用 `xbot.excel.kill_excel_process("wps", True)` 结束残留进程；不判断其他 WPS 文件是否正在编辑。本轮已经打开目标工作簿后，不在打开源文件前再次结束 WPS。
2. **所有表格文件，包括 Excel 和 CSV，都使用 `xbot.excel.open()` 的 WPS 驱动打开**，不改用 `openpyxl`、`pandas` 或其它方式加载。
3. 统一使用 `workbook = xbot.excel.open(file_name=str(target), kind="wps", visible=True, update_links=False)`；不使用 `visible=False`。
4. 每次打开工作簿后，立即激活并最大化：

   ```python
   workbook.workbook.Activate()
   workbook.workbook.Application.WindowState = -4137
   ```

5. 每个 Sheet 的数据源更新使用 `get_range()` 读取 → 按需清洗或计算 → `set_range()` 写入。已有二维数据直接 `set_range()`，不创建临时工作簿中转。
   覆盖旧数据时只清空当前业务约定的数据区域，不整表 `clear()` 影响公式和格式。写入原始数据后确实要立即使用公式计算结果时，按实际 WPS 计算结果处理，不能用 Python 模拟计算代替。
6. 表格下载后不验证表头、第一行是否有数据或文件是否存在；需要什么数据就直接按业务流程读取处理。
7. 表格处理函数直接接收已经打开的 `workbook`；禁止 `load_excel_matrix` 及同类再次加载工作簿的封装。多个函数需要同一对象时由主流程局部变量持有、传递。

## 多 Sheet 更新与收尾

1. 主流程直接写明下载、打开、写入、计算、保存和关闭的先后顺序。目标工作簿一轮只打开一次，各业务模块接收该对象。
2. 不在每个 Sheet 更新后保存。A Sheet 成功、B Sheet 失败时记录 B 的错误，继续更新独立的 C Sheet；存在前置依赖的 Sheet 则按当前业务确认的依赖关系及失败策略处理，不机械套用独立任务的继续规则。各 Sheet 处理完后统一 `workbook.save()` 一次。
3. 下载函数供后续步骤直接处理表格时，返回已经打开的源 `workbook`，由主流程持有并传递；如果另一个业务需要复用前一个业务下载的文件，则前一个业务返回 `filepath`，后一个业务接收该路径。不重复下载或重新加载已打开的工作簿。
4. 完成本轮处理后，**先保存目标工作簿，再统一关闭全部 WPS 表格**，不额外维护逐工作簿关闭清单。异常时按原业务异常处理未保存内容；清理失败不能覆盖原来的业务异常。
5. 表格更新业务各自放在 `update_xxx.py` 中，例如 `update_erp_date.py` 和 `update_sales.py`。同一业务的下载和更新放在一起，不因读取 C-ERP 数据就把其它业务的函数放入 C-ERP 模块；多个业务确实复用相同且完整的技术操作时才提取公共函数。

不为了潜在需求新增跨轮下载缓存、重复状态源、补跑开关、历史兼容和复杂恢复分支。
