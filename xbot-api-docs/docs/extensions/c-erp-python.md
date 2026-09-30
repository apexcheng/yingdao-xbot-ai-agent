# C-ERP 报表下载 Python 版

> 来源：C-ERP 项目源码（GitHub：`apexcheng/shadowbot-c-erp`），业务决策记录见项目内 `docs/erp-visual-python-migration.md`。  
> 调用类型：项目内 Code flow 模块（Python 源码），不经过 `xbot_extensions` 市场指令包装。  
> 记录原则：接口事实以项目源码为证据（2026-10-01 核对至 GitHub main `a1c4b0e`，另含项目工作区未提交的日期选择器与发货汇总 iframe 调整）；此前报表全链路已于 2026-10-01 在真实 ERP 环境运行 `test.py` 验证通过；验证码登录接口（`80b1f8d0` 起，及其后的登录等待、错误提示与短信提取修正）按源码静态核对，未专项运行验证。

---

## 1. 定位与调用方式

这些模块是 C-ERP 项目内的 Code flow 模块，不是市场指令扩展。市场指令「C-ERP可视化版」自 26.10.6 起也把这些 Python 模块作为隐藏的内部 Code flow 打包发布，但公开入口仍是原有的 `processN(...)` 包装函数（`__init__.py` 与 26.9.3 完全一致），编码版调用方式未变；本文按项目内模块用法记录。使用方式有两种：

1. **项目内模块导入**：在项目的其他 Code flow 模块中 `from .xxx import ...` 直接调用函数，`test.py` 是完整调用示例。
2. **Studio 执行 Code flow**：每个模块同时定义 `main(args)` 作为影刀 Code flow 入口，`args` 是流程初始化参数字典。

`page`（ERP 网页对象）由 `init()` 返回，作为每个函数的第一个参数显式传递；不使用 `package.variables` 全局变量。

模块依赖市场指令 `iframe2` 做 iframe 内二段 XPath 定位（用法见 [iframe2](../iframe2-extension.md)）；日期翻页、任务中心轮询等待均为明确条件等待，不依赖固定 `sleep`。

```text
非执行调用说明（不可直接运行）：

from .init_erp import init
from .download_stock import download_stock
from .download_delivery_orders import download_delivery_orders
from .download_return_details import download_return_details

# 初始化并登录 ERP；验证码配置默认从项目 config.py 读取，详见第 2.1 节
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
| `init_erp.py` | `init(username, password, browser_profile, captcha_token="", ntfy_topic="", refresh=False)` | 账号、密码、Chrome Profile 名、云码 token、ntfy 主题均为 `str`；复用页面时是否刷新 `bool` | ERP 网页对象 | 复用已有 ERP 页面并登录；登录结果为失败时关闭页面并抛 `RuntimeError`，登录过程中的配置缺失、验证码识别或短信接收异常统一包装为 `RuntimeError` 后传播 |
| `init_erp.py` | `login_c_erp(login_web, username, password, captcha_token, ntfy_topic)` | 登录网页对象、账号、密码、云码 token、ntfy 主题 | 登录结果 `bool` | 当前 URL 已离开登录域时直接返回 `True`；处理协议勾选、账号密码、图形验证码与短信验证码，提交后检测登录错误提示 |
| `init_erp.py` | `wait_sms_code(ntfy_topic, requested_at)` | ntfy 主题 `str`、本次请求时间戳 `float` | 验证码 `str` | 轮询缓存消息，只处理 `time > requested_at` 的消息，按「验证码是：」文案后的 4～6 位数字匹配返回；超时抛 `TimeoutError` |
| `enter_tab.py` | `enter_tab(page, menu_name)` | 菜单 / Tab 名称 `str` | 无 | 顶部已有同名 Tab 直接切换；否则经「全部功能菜单」搜索第一条结果进入 |
| `get_download_file.py` | `get_download_file(page, file_keyword, export_time, timeout_seconds)` | 任务关键词 `str`、本次点击导出的时间（`datetime` 或 `%Y-%m-%d %H:%M:%S` 字符串）、等待秒数 | CSV 文件路径 `str` | 在任务中心等待导出任务完成并下载，见第 4 节 |
| `date_picker.py` | `select_date(page, iframe_xpath, date_label, placeholder, target_date)` | iframe XPath、日期字段标签（如 发货时间）、占位符（开始日期 / 结束日期）、目标日期 `datetime.date` | 无 | 报表 iframe 内读取输入框当前日期（格式 `yyyy-mm-dd HH:MM:SS`），已等于目标日期时跳过；否则打开日期选择器，按输入框实际日期逐次校准年份、月份后点击目标日期 |
| `download_stock.py` | `download_stock(page, item_code, spec_code, warehouse_name)` | 商品代码 / 规格代码 / 仓库名称 `str`，空表示不过滤 | CSV 路径 `str` | 库存统计 Tab；仓库名称输入后点击「全 选」 |
| `download_platform_distribution.py` | `download_platform_distribution(page, platform_type, shop_name, platform_item_id)` | 平台类型 / 店铺名称（空表示不过滤）、平台商品 ID `str` | CSV 路径 `str` | 平台铺货 Tab；下拉输入后回车确认，见第 3 节 |
| `download_delivery_summary.py` | `download_delivery_summary(page, shop_name, start_date, end_date, group_by_shop)` | 店铺名称 `str`、起止日期 `yyyy/mm/dd` 字符串、是否按店铺汇总 `bool` | CSV 路径 `str` | 发货商品汇总 Tab；含「店铺汇总」对称勾选 |
| `download_delivery_orders.py` | `download_delivery_orders(page, shop_name, start_date, end_date)` | 店铺名称 `str`、起止日期 `yyyy/mm/dd` 字符串 | CSV 路径 `str` | 发货订单明细 Tab |
| `download_return_details.py` | `download_return_details(page, shop_name, start_date, end_date)` | 店铺名称 `str`、起止日期 `yyyy/mm/dd` 字符串 | CSV 路径 `str` | 退货商品明细 Tab |

### 2.1 初始化与验证码登录契约

以下行为来自 GitHub main（`80b1f8d0` 至 `a1c4b0e`）的 `init_erp.py`，属于项目接口的当前实现，验证码登录相关分支尚未专项运行验证：

- `main(args)` 必填 `username`、`password`、`browser_profile`；可选 `captcha_token`、`ntfy_topic`（默认空字符串）及 `refresh`（默认 `False`）；成功返回网页对象，并写入 `args["page"]`。
- `init()` 对空的 `captcha_token` / `ntfy_topic` 分别使用 `config.CAPTCHA_TOKEN` / `config.NTFY_TOPIC`。`config.example.py` 提供空值模板，须复制为本地 `config.py` 并按需配置；真实配置已被项目 `.gitignore` 排除，不写入知识库。
- 签名在 `refresh` 前新增了两个参数。需要刷新时使用 `refresh=True` 关键字；旧调用若把第 4 个位置参数作为 `refresh`，必须随签名调整。
- 提交登录前若协议 checkbox 未勾选会自动点击勾选；图形验证码区域与短信验证码输入框均在点击登录后的 2 秒检测窗口内判断，两类验证码可能先后出现。
- 图形验证码分支使用元素库中的 `ERP验证码图片` 选择器，调用[云码通用数英入口](activity-jfbym.md)，类型编号为 `10110`，从调用参数字典的 `data` 字段读取结果后填入并再次登录。扩展参数契约以云码事实页为准。
- 当前登录代码在有效云码 token 为空时先抛 `ValueError`，因此不会进入扩展自身的空 token 免费识别分支；模板注释中的“留空时走影刀免费识别”并不等于当前项目的实际行为。
- 短信验证码分支要求有效 ntfy 主题非空，否则抛 `ValueError`；调用方需将手机短信转发到该主题。点击获取验证码并确认提示后记录时间戳，再调用 `wait_sms_code()`；消息获取使用[增强工具的 ntfy 接口](xbot-enhance-tools.md)，缓存范围沿用接口默认值。
- `wait_sms_code()` 以 300 秒为轮询截止时间，单次请求超时 15 秒，本轮无匹配结果时等待 1 秒再请求；只过滤消息时间，并按正则提取短信文案「验证码是：」后的 4～6 位数字（负向断言排除更长数字串），不校验短信发送方或业务归属。单次请求可能使实际结束时间超过截止时间。
- 提交后最多轮询 10 秒等待 URL 离开登录域，每 0.5 秒检测登录错误提示；检测到含「错误」的提示时将账号、密码、token、主题脱敏后记录日志并返回 `False`。未跳转时等待 ERP 页头（`.cerp-header`）就绪 5 秒，再重新取得 ERP 页面判断登录结果。返回 `False` 时由 `init()` 关闭本次页面并抛 `RuntimeError`；验证码配置缺失、识别或短信接收异常不经过这一失败返回分支，而是由 `login_c_erp` 统一包装为 `RuntimeError`（附阶段上下文与原始异常）后传播。

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
5. 超时基准是**传入的导出时间**（不是进入任务中心的时刻）：`deadline = 导出时间 + timeout_seconds`，「执行中」找不到任务或「已完成」未生成抛 `TimeoutError`，并统一被 `get_download_file` 包装为 `RuntimeError`（附阶段上下文与原始异常）后传播；各下载指令统一传 600 秒。

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
| 发货商品汇总 | `//div[@role="tabpanel"]/iframe[contains(@src, "/report/report/oms_delivery_item_count_report")]` |
| 发货订单明细 | `//div[@role="tabpanel"]/iframe[contains(@src, "/report/report/trade_delivery_order_detail_report")]` |
| 退货商品明细 | `//div[@role="tabpanel"]/iframe[contains(@src, "/report/report/trade_return_order_detail_report")]` |
| 任务中心 | `//iframe[contains(@src, "/task/task_center")]` |

iframe 内其余元素 XPath（重置、查询、导出按钮、筛选输入框、日期选择器、店铺汇总 checkbox 等）以项目各 `download_*.py` 源码中的调用点注释为准，不在本页复制第二份。发货商品汇总的 iframe 地址是项目工作区未提交调整（2026-10-01），尚未推送到 GitHub main。

---

## 6. 需运行验证

以下页面行为只能从源码确认，未做过专项运行验证，不要写成稳定结论：

- `platform_type` 除常见平台外的完整可选值列表。
- `start_date` 与 `end_date` 同日或相邻边界时，ERP 对起止日期的包含语义。
- 下载改名（`os.rename`）在目标同名文件已存在 / 被占用时的失败表现。
- `enter_tab` 的 `menu_name` 支持的完整菜单名称列表。
- 新增图形验证码与短信验证码分支的页面检测、输入、提交及登录跳转；此前报表全链路验证不能替代这些分支的专项验证。
- 短信文案是否固定为「验证码是：」格式：当前正则按该文案匹配（不校验发送方），转发短信模板变更会直接导致取不到验证码。
- ntfy 消息时间与确认提示后记录的浮点时间戳在同秒、时钟偏差或短信极快到达时的边界。
- 日期选择器「按输入框实际日期逐次校准翻页」逻辑来自用户 Visual Flow 截图校正（静态依据）；日期已一致时的跳过分支，以及其他报表与发货汇总分支的一致性，未专项运行验证。

---

## 7. 证据

| 结论 | 证据 |
|---|---|
| 模块划分、函数签名、参数、返回值 | 项目源码 `init_erp.py`、`enter_tab.py`、`get_download_file.py`、`date_picker.py`、`download_*.py` |
| 验证码登录接口、配置默认值与失败行为 | GitHub main 提交 `80b1f8d0cc42196b76f735863d1bac96f9d757af` 至 `a1c4b0e` 的 `init_erp.py`、`config.example.py`；静态代码依据，未专项运行验证 |
| 日期选择器翻页基准、发货商品汇总 iframe 地址 | 项目工作区未提交改动（2026-10-01）及项目内 `docs/erp-visual-python-migration.md` 的截图校正记录；未专项运行验证 |
| 完整调用方式 | 项目源码 `test.py`（依次初始化并执行全部下载指令；已停止纳入 git 跟踪，凭据只保留在本地） |
| 业务决策（关键词、40 秒查询等待、发货时间字段、店铺汇总对称、回车确认） | 项目内 `docs/erp-visual-python-migration.md`「用户已确认的实现决策」 |
| 此前报表全链路运行结果 | 2026-10-01 用户在真实 ERP 环境完整执行 `test.py` 通过；不据此确认新增验证码分支 |

示例中的账号、密码、店铺名称均为占位符；不要把真实凭据写入代码、日志或文档。
