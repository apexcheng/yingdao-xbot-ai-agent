# C-ERP可视化版｜Python 模块（activity_a90a8311）

> 本页仅记录「C-ERP可视化版」市场指令开发项目中的 Python Code Flow 及支撑文件，不记录可视化流程。它不是 `guanyi_erp_api` 直接查询接口文档，也不意味着以下内部函数已经作为市场指令的公开 API 发布。
>
> 证据：2026-10-13 核对本机市场指令开发项目（`activity_code=activity_a90a8311`）的 `package.json`、`prototype.block.json` 和 Python 源码；`package.json` 登记了 13 个 Code Flow。未验证市场线上发布版本或真实 ERP 下载。
>
> [市场指令索引](../extension-instructions.md)

## Python Code Flow

以下 **13 个 Code Flow 均登记在 `package.json`**，其 block 为 `hidden=true`。表中的 Python 函数签名、`main(args)` 字段来自本机源文件，适用于**维护这个市场指令开发项目时**查阅；它们不代表其他影刀业务应用可以通过 `from xbot_extensions import activity_a90a8311` 直接调用同名函数。

### 初始化与共用模块

| 模块文件 | Python 函数或入口 | 功能、输入与结果 |
|---|---|---|
| `init_erp.py` | `init(username, password, browser_profile, captcha_token="", ntfy_topic="", refresh=False)` | 初始化浏览器环境、复用或新建 ERP 页面并登录；可选图形验证码 Token、短信接收主题与刷新选项；返回 ERP Page。`main(args)` 必需 `username`、`password`、`browser_profile`，可选 `captcha_token`、`ntfy_topic`、`refresh`，将 Page 写入 `args["page"]` |
| `enter_tab.py` | `enter_tab(page, menu_name)` | 切换已存在的 ERP Tab，或搜索进入指定菜单；`main(args)` 读取 `page`、`menu_name`，不返回下载文件 |
| `date_picker.py` | `select_date(page, iframe_xpath, date_label, placeholder, target_date)` | 在报表 iframe 中定位日期输入框并选择 `datetime.date` 目标日期；空日期先选择今天。**该文件没有 `main(args)`**，虽然登记为 Code Flow，当前是内部 Python 辅助函数 |
| `get_download_file.py` | `get_download_file(page, file_keyword, export_time, timeout_seconds)` | 到 ERP 任务中心按任务关键词及导出时间等待、下载 CSV；`export_time` 为 `datetime` 或 `%Y-%m-%d %H:%M:%S` 字符串，超时单位秒；`main(args)` 读取同名四个字段，输出 `args["file_path"]` |

### 报表下载模块

以下模块在开发项目内部接收已经初始化的 ERP `page`，自行切换 Tab、设置筛选、触发导出并调用 `get_download_file` 获取 CSV；成功时返回文件路径，`main(args)` 也写入 `args["file_path"]`。

| 模块文件 | Python 函数签名 | `main(args)` 必需字段和用途 |
|---|---|---|
| `download_stock.py` | `download_stock(page, item_code, spec_code, warehouse_name)` | `page`、`item_code`、`spec_code`、`warehouse_name`；按商品代码、规格代码、仓库筛选库存 |
| `download_platform_distribution.py` | `download_platform_distribution(page, platform_type, shop_name, platform_item_id)` | `page`、`platform_type`、`shop_name`、`platform_item_id`；筛选平台铺货数据 |
| `download_delivery_summary.py` | `download_delivery_summary(page, shop_name, start_date, end_date, group_by_shop)` | `page`、`shop_name`、`start_date`、`end_date`、`group_by_shop`；发货商品汇总，可按店铺汇总 |
| `download_delivery_orders.py` | `download_delivery_orders(page, shop_name, start_date, end_date)` | `page`、`shop_name`、`start_date`、`end_date`；发货订单明细 |
| `download_return_details.py` | `download_return_details(page, shop_name, inbound_time, creation_time)` | `page`、`shop_name`、`inbound_time`、`creation_time`；退货商品明细，后两项各为 `(开始日期, 结束日期)` 元组，分别表示入库与制单时间 |
| `download_delivery_item_details.py` | `download_delivery_item_details(page, shop_name, start_date, end_date)` | `page`、`shop_name`、`start_date`、`end_date`；发货商品明细统计 |

`start_date`、`end_date` 及两个日期元组内的日期字符串使用 `yyyy/mm/dd`。退货明细的入库时间与制单时间分别传入日期元组，不能混用其他报表的起止日期参数。

### 配置与测试模块

| 模块文件 | 角色与使用边界 |
|---|---|
| `config.example.py` | 登录验证码配置模板，声明 `CAPTCHA_TOKEN`、`NTFY_TOPIC` 两项配置；不提供 `main(args)` |
| `config.py` | 开发项目自身的私有登录验证码配置，由 `init_erp.py` 在未显式传值时读取；不提供 `main(args)`，不得复制其中任何真实配置到知识库 |
| `test.py` | 项目内测试 Code Flow，`main(args)` 依次下载退货商品明细与发货商品明细，写入 `args["return_details_file_path"]`、`args["delivery_item_details_file_path"]`；使用项目内测试配置及固定测试条件，**不作为通用业务入口** |

还有三个不在 `package.json` 的 `flows` 列表中、但存在于项目根目录的 Python 支撑文件：`__init__.py` 是扩展包入口，`package.py` 提供项目变量与资源访问，`test_config.py` 是测试用的私有配置文件。它们不是另三个 Code Flow；配置内容不在此记录。

### 使用边界

- **维护当前市场指令开发项目**：依据上表的 Python 函数签名和 `main(args)` 字段维护自身模块；已初始化的 ERP Page 由调用方传入。
- **其他影刀业务项目**：本页的 Code Flow 标记为 `hidden=true`，不代表它们可作为市场指令公开 API 直接调用。应按实际安装版本核实可用入口，不复制内部实现来绕过安装差异。
- 下载函数的成功结果是 CSV 路径；本页核验的是源码接口，不代表 ERP 页面或下载权限当前可用。

如果需要用 C-ERP API 查询数据而不是在网页导出报表，应查 [C-ERP API](guanyi-erp-api.md)，不要混用两个扩展。
