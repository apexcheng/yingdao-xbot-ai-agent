# C-ERP可视化版（activity_a90a8311）

> 调用类型：影刀市场指令 Visual Flow，通过 `xbot_extensions.activity_a90a8311.processN(...)` 公开包装函数调用；不是 `guanyi_erp_api` 直接查询接口。
>
> 证据：2026-10-13 核对本机「C-ERP可视化版」市场指令开发项目（`activity_code=activity_a90a8311`）的 `package.json`、`prototype.block.json`、`__init__.py` 及项目内 Code Flow 源码。`package.json` 登记了 13 个 Visual Flow 和 13 个 Code Flow；其中 9 个 Visual Flow 为公开入口。`package_version=8` 是项目元数据，不等于市场线上发布版本；未验证市场线上最新版本。
>
> [市场指令索引](../extension-instructions.md)

## 公开入口

先在目标影刀应用中安装或更新「C-ERP可视化版」，再从 `xbot_extensions` 调用；使用登录/初始化入口建立 ERP 会话，其他入口在相应会话和页面条件满足时执行。

| 入口 | 指令 | 位置参数（按公开包装函数顺序） | 公开输出 |
|---|---|---|---|
| `process10` | init初始化ERP | `username`、`password`、`ERP浏览器标识` | `ERP网页对象` |
| `process13` | init_v2（已有网页时可复用） | `username`、`password`、`ERP浏览器标识`、`refresh` | `ERP网页对象` |
| `process4` | 库存下载 | `商品代码`、`规格代码`、`仓库名称` | `file_path` |
| `process11` | 平台铺货下载 | `平台类型`、`店铺名称`、`平台商品ID` | `file_path` |
| `process12` | 发货商品汇总下载 | `店铺名称`、`发货时间start`、`发货时间end`、`店铺汇总` | `file_path` |
| `process14` | 发货订单明细下载 | `店铺名称`、`发货时间start`、`发货时间end` | `file_path` |
| `process15` | 退货商品明细下载 | `店铺名称`、`发货时间start`、`发货时间end` | `file_path` |
| `process5` | 进入选项卡 | `菜单项Name`、`web` | 无 |
| `process8` | 获取下载文件 | `文件关键词`、`下载时间`、`等待超时` | `file_path` |

### 参数与使用边界

- `username`、`password` 是 ERP 登录凭据；`ERP浏览器标识` 是浏览器 Profile 标识（字符串），示例值 `Default`。不得在知识库或日志中填写真实凭据。
- `process13` 的 `refresh` 为布尔值：已有网页时决定是否刷新。Visual 指令元数据默认 `False`，但 Python 包装函数**仍要求传入第四个参数**。旧的 `process10` 不提供该参数。
- `process4` 的 `商品代码`、`规格代码`、`仓库名称` 为字符串筛选条件；Visual 界面的仓库名称默认显示「正品仓」。`process11` 的 `平台类型`、`店铺名称`、`平台商品ID` 也是字符串筛选条件；Visual 界面平台类型默认显示「淘宝」。**编码调用仍须传入全部位置参数**，不能省略界面有默认值的参数。
- 报表类入口的 `店铺名称` 是字符串筛选条件；`发货时间start` / `发货时间end` 使用 `yyyy/mm/dd` 字符串。
- `process15` 虽然叫「退货商品明细下载」，当前**公开包装**中的两个日期参数仍命名为 `发货时间start`、`发货时间end`。不要根据项目内部的退货下载 Python 模块改写其位置参数或推断日期筛选的实际业务含义。
- `process12` 的 `店铺汇总` 是布尔值。Visual 元数据默认 `False`，但 Python 包装函数**仍要求显式传入**。
- `process5` 的 `web` 对应 ERP 网页对象；Visual 元数据允许 `None`，但 Python 包装函数仍有必填位置参数。它只负责进入 Tab，不返回下载路径。
- `process8` 的 `下载时间` 为 `datetime` 对象，`等待超时` 为以秒为单位的整数；Visual 元数据默认 600 秒，但 Python 包装函数仍要求传入。该入口用于获取后台导出任务的结果，不应与发起导出混为一谈。
- `file_path` 表示下载文件路径（字符串）；`ERP网页对象` 表示网页对象。这里列出的是指令公开的**输出字段名及类型**，业务代码应按当前安装版本核对实际包装返回形态。
- 其余隐藏 Visual Flow 和 Code Flow 也在下方列出，供维护市场指令开发项目时查询。它们未出现在 `__init__.py` 的公开包装方法中，**不能直接等同于已发布市场指令的公开 API**。

## 最小调用形态

```text
非执行调用说明（不可直接运行；凭据和业务范围均为占位符）：

from xbot_extensions import activity_a90a8311 as cerp

# 初始化；已有页面可复用，refresh=False 表示不主动刷新
erp_page = cerp.process13("ERP账号", "ERP密码", "Default", False)

# 库存与平台铺货下载
stock_path = cerp.process4("指定商品代码", "指定规格代码", "正品仓")
distribution_path = cerp.process11("淘宝", "指定店铺", "指定平台商品ID")

# 获取发货商品汇总；日期格式 yyyy/mm/dd
file_path = cerp.process12("指定店铺", "2026/10/01", "2026/10/07", False)

# 发货订单明细（安装副本必须包含 process14）
orders_path = cerp.process14("指定店铺", "2026/10/01", "2026/10/07")

# 退货商品明细；参数名以公开包装为准，不能换成内部 Python 模块的参数
returns_path = cerp.process15("指定店铺", "2026/10/01", "2026/10/07")

# 进入已有 ERP 页面的指定 Tab；使用初始化返回的网页对象
cerp.process5("库存统计", erp_page)

# 仅在已触发后台导出、且明确知道任务关键词与提交时间时单独获取文件
# download_time 由调用方在实际提交导出前记录，为 datetime 对象；此处省略导出过程
# 超时单位为秒
download_path = cerp.process8("指定导出任务关键词", download_time, 600)
```

以上示例只表达包装函数的调用顺序及参数位置，不证明账号、ERP 页面、下载权限或业务数据当前可用。调用市场指令时，真实项目代码还需遵守 `project-template/AGENTS.md` 的调用点功能与参数注释要求。

## 项目内其他 Visual Flow（非公开）

这些 Flow 存在于当前 `package.json`，但 `prototype.block.json` 中标记 `hidden=true`，且 `__init__.py` 没有对应公开包装函数。它们用于理解开发项目结构，不作为业务应用的调用入口。

| Flow 文件名 | 项目名称 | 作用与状态 |
|---|---|---|
| `main` | 主流程 | Visual 启动流，不是公开 API |
| `process1` | 登陆C-ERP | 初始化流程所依赖的登录子流程 |
| `process2` | 子流程1 | 隐藏的历史子流程，具体用途未在本次核验中确认 |
| `process7` | 进入任务中心X(废弃) | 已标为废弃，不应作为新开发入口 |

## 项目内 Python Code Flow（非公开）

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

`start_date`、`end_date` 及两个日期元组内的日期字符串使用 `yyyy/mm/dd`。**特别注意：** `download_return_details.py` 的双时间范围是 Code Flow 的内部接口，不是公开 Visual `process15` 的参数，也不能把 `download_delivery_item_details.py` 误认为已存在同名公开 `processN`。

### 配置与测试模块

| 模块文件 | 角色与使用边界 |
|---|---|
| `config.example.py` | 登录验证码配置模板，声明 `CAPTCHA_TOKEN`、`NTFY_TOPIC` 两项配置；不提供 `main(args)` |
| `config.py` | 开发项目自身的私有登录验证码配置，由 `init_erp.py` 在未显式传值时读取；不提供 `main(args)`，不得复制其中任何真实配置到知识库 |
| `test.py` | 项目内测试 Code Flow，`main(args)` 依次下载退货商品明细与发货商品明细，写入 `args["return_details_file_path"]`、`args["delivery_item_details_file_path"]`；使用项目内测试配置及固定测试条件，**不作为通用业务入口** |

还有三个不在 `package.json` 的 `flows` 列表中、但存在于项目根目录的 Python 支撑文件：`__init__.py` 定义上述九个公开 `processN` 包装函数，`package.py` 提供项目变量与资源访问，`test_config.py` 是测试用的私有配置文件。它们不是另三个 Code Flow；配置内容不在此记录。

### Code Flow 与公开市场 API 的区别

- **其他业务影刀项目**：使用上方 `processN(...)` 公开包装函数；按目标应用实际安装的市场指令版本确认是否具备对应入口。
- **维护当前市场指令开发项目**：可以依据上表的内部 Python 函数和 `main(args)` 字段维护自身 Code Flow。`hidden=true` 并不意味着源码不存在，但也不自动产生对外 Python 包装签名。
- **来源差异**：当前项目同时保留 Visual 下载流程和 Python 实现，它们并非自动互相替换。例如退货报表 Python 实现使用两个时间范围，而公开 `process15` 仍是三个位置参数，不能混用。

## 安装版本差异

- 已检查的部分较旧应用副本只公开 `process4/5/8/10/11/12/13`。
- 另一些安装副本还公开 `process14/15`；使用发货订单明细、退货商品明细下载时，目标应用必须安装包含这两个入口的版本。
- 如目标应用出现 `AttributeError`、无法导入入口或指令缺失，先检查或更新**该项目实际安装的市场指令**；不得直接修改 `xbot_extensions` 安装副本，也不要改为调用来源项目的 `download_*.py` 来绕过。
- 未检查市场线上当前发布版本，也未运行真实 ERP 下载。本页核验范围为上述本机市场指令项目的公开调用契约，不宣称业务实机验收通过。

如果需要用 C-ERP API 查询数据而不是在网页导出报表，应查 [C-ERP API](guanyi-erp-api.md)，不要混用两个扩展。
