# C-ERP可视化版（activity_a90a8311）

> 调用类型：影刀市场指令 Visual Flow，通过 `xbot_extensions.activity_a90a8311.processN(...)` 公开包装函数调用；不是 C-ERP 项目内部 Python 模块，也不是 `guanyi_erp_api` 直接查询接口。
>
> 证据：Windows 本机已安装扩展的 `package.json`、`prototype.block.json`（仅公开的 `hidden=false` block）和 `__init__.py` 公开包装签名。核对到扩展包版本字段 `26.5.8`，但不同应用的安装副本所含入口不完全一致；这里描述实际检查到的九个公开入口，不将其等同于市场线上最新版本。
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
- 下载指令中的商品代码、规格代码、店铺名称、平台类型及平台商品 ID 均为字符串筛选条件。报表的 `发货时间start` / `发货时间end` 使用 `yyyy/mm/dd` 字符串。
- `process12` 的 `店铺汇总` 是布尔值。Visual 元数据默认 `False`，但 Python 包装函数**仍要求显式传入**。
- `process5` 的 `web` 对应 ERP 网页对象；Visual 元数据允许 `None`，但 Python 包装函数仍有必填位置参数。它只负责进入 Tab，不返回下载路径。
- `process8` 的 `下载时间` 为 `datetime` 对象，`等待超时` 为以秒为单位的整数；Visual 元数据默认 600 秒，但 Python 包装函数仍要求传入。该入口用于获取后台导出任务的结果，不应与发起导出混为一谈。
- `file_path` 表示下载文件路径（字符串）；`ERP网页对象` 表示网页对象。这里列出的是指令公开的**输出字段名及类型**，业务代码应按当前安装版本核对实际包装返回形态。

## 最小调用形态

```text
非执行调用说明（不可直接运行；凭据和业务范围均为占位符）：

from xbot_extensions import activity_a90a8311 as cerp

# 初始化；已有页面可复用，refresh=False 表示不主动刷新
erp_page = cerp.process13("ERP账号", "ERP密码", "Default", False)

# 获取发货商品汇总；日期格式 yyyy/mm/dd
file_path = cerp.process12("指定店铺", "2026/10/01", "2026/10/07", False)

# 发货订单明细（安装副本必须包含 process14）
orders_path = cerp.process14("指定店铺", "2026/10/01", "2026/10/07")
```

以上示例只表达包装函数的调用顺序及参数位置，不证明账号、ERP 页面、下载权限或业务数据当前可用。调用市场指令时，真实项目代码还需遵守 `project-template/AGENTS.md` 的调用点功能与参数注释要求。

## 安装版本差异

- 已检查的部分较旧应用副本只公开 `process4/5/8/10/11/12/13`。
- 另一些安装副本还公开 `process14/15`；使用发货订单明细、退货商品明细下载时，目标应用必须安装包含这两个入口的版本。
- 如目标应用出现 `AttributeError`、无法导入入口或指令缺失，先检查或更新**该项目实际安装的市场指令**；不得直接修改 `xbot_extensions` 安装副本，也不要改为调用来源项目的 `download_*.py` 来绕过。
- 未检查市场线上当前发布版本，也未运行真实 ERP 下载。本页核验范围为本机安装副本的公开调用契约，不宣称业务实机验收通过。

如果需要用 C-ERP API 查询数据而不是在网页导出报表，应查 [C-ERP API](guanyi-erp-api.md)，不要混用两个扩展。
