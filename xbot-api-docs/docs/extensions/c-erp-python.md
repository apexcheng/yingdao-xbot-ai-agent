# C-ERP 报表下载 Python 版

> 来源：C-ERP 项目源码（GitHub：`apexcheng/shadowbot-c-erp`），业务决策记录见项目内 `docs/erp-visual-python-migration.md`。  
> 调用类型：项目内 Code flow 模块（Python 源码），不经过 `xbot_extensions` 市场指令包装。  
> 记录原则：接口事实以项目源码为证据（2026-10 核对）；全链路已于 2026-10-01 在真实 ERP 环境运行 `test.py` 验证通过；页面行为类结论按需标注需运行验证。

---

## 1. 定位与调用方式

这些模块是 C-ERP 项目内的 Code flow 模块，不是市场指令扩展。使用方式有两种：

1. **项目内模块导入**：在项目的其他 Code flow 模块中 `from .xxx import ...` 直接调用函数，`test.py` 是完整调用示例。
2. **Studio 执行 Code flow**：每个模块同时定义 `main(args)` 作为影刀 Code flow 入口，`args` 是流程初始化参数字典。

`page`（ERP 网页对象）由 `init()` 返回，作为每个函数的第一个参数显式传递；不使用 `package.variables` 全局变量。

模块依赖市场指令 `iframe2` 做 iframe 内二段 XPath 定位（用法见 [iframe2](iframe2-extension.md)）；日期翻页、任务中心轮询等待均为明确条件等待，不依赖固定 `sleep`。

```text
非执行调用说明（不可直接运行）：

from .init import init
from .download_stock import download_stock
from .download_delivery_orders import download_delivery_orders
from .download_return_details import download_return_details

# 初始化并登录 ERP；browser_profile 是 Chrome Profile 名称，refresh 表示复用已有页面时是否刷新
page = init("<username>", "<password>", "Default")

# 库存下载：空字符串表示不过滤对应条件
stock_path = download_stock(page, item_code="", spec_code="", warehouse_name="正品仓")

# 报表下载：日期格式 yyyy/mm/dd，三个报表统一筛选「发货时间」字段
orders_path = download_delivery_orders(page, shop_name="<shop_name>", start_date="2026/09/01", end_date="2026/09/30")
return_path = download_return_details(page, shop_name="<shop_name>", start_date="2026/09/01", end_date="2026/09/30")
```

---

## 2. 模块与函数

| 模块 | 函数 | 入参 | 返回 | 说明 |
|---|---|---|---|---|
| `init.py` | `init(username, password, browser_profile, refresh=False)` | 账号 `str`、密码 `str`、Chrome Profile 名 `str`、复用页面时是否刷新 `bool` | ERP 网页对象 | 复用已有 ERP 页面并登录；登录失败关闭页面并抛 `RuntimeError` |
| `enter_tab.py` | `enter_tab(page, menu_name)` | 菜单 / Tab 名称 `str` | 无 | 顶部已有同名 Tab 直接切换；否则经「全部功能菜单」搜索第一条结果进入 |
| `get_download_file.py` | `get_download_file(page, file_keyword, export_time, timeout_seconds)` | 任务关键词 `str`、本次点击导出的时间（`datetime` 或 `%Y-%m-%d %H:%M:%S` 字符串）、等待秒数 | CSV 文件路径 `str` | 在任务中心等待导出任务完成并下载，见第 4 节 |
| `date_picker.py` | `select_date(page, iframe_xpath, date_label, placeholder, target_date)` | iframe XPath、日期字段标签（如 发货时间）、占位符（开始日期 / 结束日期）、目标日期 `datetime.date` | 无 | 报表 iframe 内打开日期选择器，按与今天的年月差翻页后点击目标日期 |
| `download_stock.py` | `download_stock(page, item_code, spec_code, warehouse_name)` | 商品代码 / 规格代码 / 仓库名称 `str`，空表示不过滤 | CSV 路径 `str` | 库存统计 Tab；仓库名称输入后点击「全 选」 |
| `download_platform_distribution.py` | `download_platform_distribution(page, platform_type, shop_name, platform_item_id)` | 平台类型 / 店铺名称（空表示不过滤）、平台商品 ID `str` | CSV 路径 `str` | 平台铺货 Tab；下拉输入后回车确认，见第 3 节 |
| `download_delivery_summary.py` | `download_delivery_summary(page, shop_name, start_date, end_date, group_by_shop)` | 店铺名称 `str`、起止日期 `yyyy/mm/dd` 字符串、是否按店铺汇总 `bool` | CSV 路径 `str` | 发货商品汇总 Tab；含「店铺汇总」对称勾选 |
| `download_delivery_orders.py` | `download_delivery_orders(page, shop_name, start_date, end_date)` | 店铺名称 `str`、起止日期 `yyyy/mm/dd` 字符串 | CSV 路径 `str` | 发货订单明细 Tab |
| `download_return_details.py` | `download_return_details(page, shop_name, start_date, end_date)` | 店铺名称 `str`、起止日期 `yyyy/mm/dd` 字符串 | CSV 路径 `str` | 退货商品明细 Tab |

---

## 3. 已确认业务规则

以下规则由用户确认并在源码中落地（2026-10-01 真实 ERP 运行验证通过）：

1. **任务关键词按包含匹配**：库存下载用「库存」，平台铺货下载用「铺货」，发货商品汇总与发货订单明细用「发货」，退货商品明细用「退货」。
2. **查询完成判断**：点击「查 询」后，iframe 内未禁用的查询按钮 `//div[@class='gy-split-pane-content']//button[not(@disabled)]/span[contains(text(), '查 询')]` 再次出现即视为查询完成，全部指令统一最长 40 秒。
3. **报表日期字段**：三个报表（发货汇总 / 发货明细 / 退货明细）统一筛选「发货时间」字段（开始日期 / 结束日期），日期格式 `yyyy/mm/dd`。
4. **店铺汇总对称处理**：`group_by_shop` 为真且未勾选时点击勾选，为假且已勾选时点击取消。
5. **铺货下拉回车确认**：平台类型 / 店铺名称下拉输入后输入框保持焦点，用 `xbot.win32.send_keys("{ENTER}")` 向当前激活的 ERP 窗口发送回车确认选择。
6. **报表店铺选项匹配**：下拉选项使用大小写不敏感的精确匹配（XPath `translate()` 比较）。

---

## 4. 任务中心下载机制

ERP 的报表导出在点击导出按钮后先创建后台导出任务，不会立即生成文件；`get_download_file` 负责等待任务完成并下载，不能替换为固定 `sleep` 后扫描下载目录：

1. 进入任务中心（顶栏图标 → 帮助 Popover 内「任务中心」链接）。
2. 切到「执行中」，循环点击刷新，读取任务名称与任务时间两个并行列表；**任务名称包含关键词**且**任务时间 ≥ 传入的导出时间**的行即本次任务，锁定其完整任务名称（如 `发货商品明细--2026-07-29 19:51:09`）。
3. 切到「已完成」，持续刷新，在已完成任务名称列表中找到与锁定的完整任务名称**完全一致**的行，用同一行索引在下载链接列表中取对应元素。
4. 下载到用户 `Downloads` 目录：文件名 `{关键词}-{导出时间:yyyyMMdd_HHmmss}.tmp`，`overwrite=True`、`wait_complete=True`、`wait_complete_timeout=3600`；完成后改名为同名 `.csv` 并返回路径。先写 `.tmp` 再改名是为了避免 CSV 在下载阶段被 Chrome 按类型自动打开。
5. 超时基准是**传入的导出时间**（不是进入任务中心的时刻）：`deadline = 导出时间 + timeout_seconds`，「执行中」找不到任务或「已完成」未生成都抛 `TimeoutError`；各下载指令统一传 600 秒。

任务中心 iframe 内关键 XPath（与 iframe2 配合时作为第二段）：

| 元素 | XPath |
|---|---|
| 任务中心 iframe（第一段） | `//iframe[contains(@src, "/task/task_center")]` |
| 执行中 / 已完成 Tab | `//span[@class='x-tab-inner x-tab-inner-center'][contains(text(), '执行中')]`（已完成同理） |
| 执行中 / 已完成刷新 | `//div[@id='detailTab-body']//div[@id='running']//span[text()='刷新']`（已完成把 `running` 换成 `finished`） |
| 任务名称 / 任务时间列表 | `//div[@id='running']//table[@role='presentation'][contains(@id, 'gridview')]//tr/td[2]`（时间为 `td[3]`，已完成把 `running` 换成 `finished`） |
| 已完成下载链接 | `//div[@id='finished']//table[@role='presentation'][contains(@id, 'gridview')]//tr/td[last()]//a` |

---

## 5. 页面 iframe 定位清单

各页面业务元素都位于内容 iframe 内，统一用 iframe2 二段 XPath（第一段为下表 iframe、第二段为 iframe 内元素，`current_global=False`）：

| 页面 | iframe XPath |
|---|---|
| 库存统计 | `//div[@role="tabpanel"]/iframe[contains(@src, "/stock/message/stock_tenant")]` |
| 平台铺货 | `//div[@role="tabpanel"]/iframe[contains(@src, "/Platformweb/platformweb/erp/info/platformItem")]` |
| 发货商品汇总 | `//div[@role="tabpanel"]/iframe[contains(@src, "/report/report/trade_delivery_item_collect_report")]` |
| 发货订单明细 | `//div[@role="tabpanel"]/iframe[contains(@src, "/report/report/trade_delivery_order_detail_report")]` |
| 退货商品明细 | `//div[@role="tabpanel"]/iframe[contains(@src, "/report/report/trade_return_order_detail_report")]` |
| 任务中心 | `//iframe[contains(@src, "/task/task_center")]` |

iframe 内其余元素 XPath（重置、查询、导出按钮、筛选输入框、日期选择器、店铺汇总 checkbox 等）以项目各 `download_*.py` 源码中的调用点注释为准，不在本页复制第二份。

---

## 6. 需运行验证

以下页面行为只能从源码确认，未做过专项运行验证，不要写成稳定结论：

- `platform_type` 除常见平台外的完整可选值列表。
- `start_date` 与 `end_date` 同日或相邻边界时，ERP 对起止日期的包含语义。
- 下载改名（`os.rename`）在目标同名文件已存在 / 被占用时的失败表现。
- `enter_tab` 的 `menu_name` 支持的完整菜单名称列表。

---

## 7. 证据

| 结论 | 证据 |
|---|---|
| 模块划分、函数签名、参数、返回值 | 项目源码 `init.py`、`enter_tab.py`、`get_download_file.py`、`date_picker.py`、`download_*.py` |
| 完整调用方式 | 项目源码 `test.py`（依次初始化并执行全部五个下载指令） |
| 业务决策（关键词、40 秒查询等待、发货时间字段、店铺汇总对称、回车确认） | 项目内 `docs/erp-visual-python-migration.md`「用户已确认的实现决策」 |
| 全链路运行结果 | 2026-10-01 用户在真实 ERP 环境完整执行 `test.py` 通过 |

示例中的账号、密码、店铺名称均为占位符；不要把真实凭据写入代码、日志或文档。
