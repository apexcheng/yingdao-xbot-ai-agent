# C-ERP API (guanyi_erp_api)

> 调用类型：`direct python`  
> 主要入口：直接调用 `__init__.py` 已导入的各业务模块 `.main(args)`；`core.py` 属于共享实现，不作为业务代码默认入口。
> 证据边界：本页公开入口已按当前安装版本源码核对；接口凭证和服务可用性仍需按当前项目验证。
> 返回：[市场指令索引](../extension-instructions.md)

---

**目录/指令名：** `guanyi_erp_api` / C-ERP API

**调用方式：** direct python

**用途：** 管易 ERP / C-ERP 的库存、商品、订单、发货、退货、仓库查询，以及商品 / SKU / 条码新增

**调用入口：**
- `xbot_extensions.guanyi_erp_api.select_stock.main(args)`
- `xbot_extensions.guanyi_erp_api.select_item.main(args)`
- `xbot_extensions.guanyi_erp_api.select_order_list.main(args)`
- `xbot_extensions.guanyi_erp_api.select_order_dteail.main(args)`
- `xbot_extensions.guanyi_erp_api.select_combine_item.main(args)`
- `xbot_extensions.guanyi_erp_api.select_item_by_sku_code.main(args)`
- `xbot_extensions.guanyi_erp_api.select_delivery.main(args)`
- `xbot_extensions.guanyi_erp_api.select_return.main(args)`
- `xbot_extensions.guanyi_erp_api.select_warehouse.main(args)`
- `xbot_extensions.guanyi_erp_api.add_item.main(args)`
- `xbot_extensions.guanyi_erp_api.add_item_sku.main(args)`
- `xbot_extensions.guanyi_erp_api.add_item_barcode.main(args)`

**公开入口参数速查：**

| 入口 | 用途 | 主要入参 | 主要输出 |
|---|---|---|---|
| `select_stock.main(args)` | 查询库存 | `max_page_no`、`item_code`、`item_sku_code`、`warehouse_code` | 写入 `args['stocks']`；无显式返回值 |
| `select_item.main(args)` | 查询商品 | `max_page_no`、`code`、`combine` | 写入 `args['items']`；无显式返回值 |
| `select_combine_item.main(args)` | 查询组合商品 | `code` | 写入 `args['context']`、`args['items']`；无显式返回值 |
| `translation.main(args)` | 翻译 Dict | `record` | 写入 `args['new_record']`，并返回翻译结果 |
| `select_order_dteail.main(args)` | 查询订单详情 | `code`、`platform_code` | 写入 `args['order_detail']`，并返回订单详情 |
| `select_order_list.main(args)` | 查询订单列表 | `date_type`、`shop_code`、`code`、`has_cancel_data`、`start_date`、`end_date` | 写入 `args['orders']`；无显式返回值 |
| `select_item_by_sku_code.main(args)` | 按商品条码查询商品 | `商品条码` | 写入 `args['items']`；无显式返回值 |
| `select_delivery.main(args)` | 查询发货单 / 销售出库单 | `page_no`、`page_size`、`code`、`outer_code`、`warehouse_code`、`shop_code`、`mail_no`、创建 / 发货 / 修改时间范围、`del`、`delivery`、`wms` | 写入 `args['result']`、`args['deliverys']`，并返回原始响应 |
| `select_return.main(args)` | 查询退货单 | `page_no`、`page_size`、`code`、`platform_code`、`shop_code`、`return_type`、`express_no`、`warehousein_code`、`warehouseout_code`、创建 / 入库 / 修改时间范围等 | 写入 `args['result']`，并返回原始响应；退货列表字段为 `tradeReturns` |
| `select_warehouse.main(args)` | 查询仓库 | `page_no`、`page_size`、`start_date`、`end_date`、`date_type`、`has_del_data`、`code` | 写入 `args['result']`，并返回原始响应；仓库列表字段为 `warehouses` |
| `add_item.main(args)` | 新增商品，可同时带 `skus` 新增规格 | `code`、`name`、品牌 / 类目 / 供应商 / 税务 / 尺寸 / 价格 / 库存状态字段、`skus` 等 | 写入 `args['result']`，并返回原始响应 |
| `add_item_sku.main(args)` | 给已有商品新增规格 | `item_id` 或 `item_code` 二选一，另有 `code`、`name`、库存状态、重量、价格、备注等 | 写入 `args['result']`，并返回原始响应 |
| `add_item_barcode.main(args)` | 给商品或规格新增条码 | `item_code`、`sku_code`、`barcode` | 写入 `args['result']`，并返回原始响应 |

**参数说明：**
- `APP_KEY`、`SESSION_KEY`、`SECRET`：当前扩展业务模块在导入时从自身 `package.variables` 读取，不是上述 `main(args)` 的调用参数。不要把凭证塞进 `args` 期待覆盖模块级配置。
- `code`：商品编码 / 订单编号
- `platform_code`：平台代码
- `start_date`、`end_date`：日期范围
- `max_page_no`：最大页码
- `outer_code`：发货查询中的平台单号
- `mail_no`：发货查询中的物流单号
- `warehouse_code`：仓库代码
- `item_id` / `item_code`：`add_item_sku` 用于定位已有商品；真实接口验证表明二者必须至少传一项
- `barcode`：`add_item_barcode` 的必填条码字段

不同入口的参数并不通用。例如库存查询有 `item_code` / `item_sku_code` / `warehouse_code`，订单列表有 `date_type` / `shop_code` / `has_cancel_data`。调用时按目标入口的真实参数使用，不要把上面的概括参数列表当成所有函数都支持的公共参数集。

**返回值约定：** 旧入口多数 Code 流通过修改传入的 `args` 写回输出；`translation.main(args)`、`select_order_dteail.main(args)` 以及本次新增的 `select_delivery`、`select_return`、`select_warehouse`、`add_item`、`add_item_sku`、`add_item_barcode` 都有显式 `return`。查询类新增入口返回 C-ERP 原始响应 Dict，不直接返回列表；列表需从 `deliverys`、`tradeReturns`、`warehouses` 等字段读取。

**真实请求核验（2026-09-12）：**
- `gy.erp.warehouse.get`：真实请求成功，返回 `success=true`、`warehouses`，当次返回 `total=20`。
- `gy.erp.trade.deliverys.get`：真实请求成功，返回 `success=true`、`deliverys`。
- `gy.erp.trade.return.get`：真实请求成功，返回 `success=true`、`tradeReturns`。
- `gy.erp.item.add`：为避免制造测试商品，真实请求故意不传必填业务字段；服务端返回 `PARAM ERR / 商品CODE必填`，确认鉴权、签名、方法名和接口路由可达。
- `gy.erp.item.sku.add`：同样采用无落库校验请求；服务端返回 `PARAM ERR / 商品ID和商品CODE必填一项`，据此确认 `item_id` / `item_code` 的定位规则。
- `gy.erp.item.barcode.add`：同样采用无落库校验请求；服务端返回 `PARAM ERR / 商品barcode必填`，确认接口可达且 `barcode` 为必填字段。

**注意事项：**
- `core.py` 提供共享 API 签名和请求封装，但当前 `__init__.py` 没有把它作为业务入口导出；业务代码默认调用上表模块，不直接绕到 `core.py`。
- `select_item.main(args)` 当前源码虽然读取了 `item_sku_code`，但没有把它传给实际商品查询函数，因此本页不把它列为有效筛选参数；不要因为看到局部变量就假定该筛选已生效。
- `select_order_list` 的底层查询函数支持更多筛选条件，包括 `platform_code`，但当前 `main(args)` 没有向下传递这些额外参数；调用 `main(args)` 时只按上表已确认参数使用。
- 模块文件名 `select_order_dteail` 是扩展现有拼写，调用时不要自行改成 `detail`。
- `select_delivery.main(args)` 的接口字段名确实包含 `del`；Python 调用层通过 Dict 展开传递该字段，业务侧传参键仍使用字符串 `"del"`。
- `add_item`、`add_item_sku`、`add_item_barcode` 会真实写入 ERP。知识库只记录入口和参数契约，不提供可直接运行的新增脚本；运行验证优先使用不会落库的参数校验请求。

**典型调用方式：**
```text
非执行调用说明（不可直接运行）：

from xbot_extensions.guanyi_erp_api import select_stock

params = {
    "max_page_no": 10,
    "warehouse_code": "WH001",
}
select_stock.main(params)
stocks = params["stocks"]
```

---
