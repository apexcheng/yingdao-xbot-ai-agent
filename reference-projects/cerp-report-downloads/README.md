# C-ERP 商品明细报表下载｜Python 实现参考

本案例记录退货商品明细统计和发货商品明细统计两个项目内 Python 模块，以及它们共用的日期选择、Tab 导航和下载中心流程。实现只维护在来源项目，本页引用固定提交，不复制业务源码。

## 来源与证据

- 来源项目：C-ERP可视化版的 Python 迁移项目，[GitHub 固定版本 `1f50f25`](https://github.com/yingdao-workspace/shadowbot-c-erp/tree/1f50f251ccccb364fdc292e15cfdd59ce8794e16)，记录日期 2026-10-13。
- 证据等级：稳定代码依据，以及用户确认的筛选字段、发货报表 iframe 路径、状态框要求和空日期处理方式；本页未独立运行真实 ERP 下载，不宣称实机验收通过。
- 两个模块是来源项目内部函数及 Code Flow。已安装市场指令的公开包装接口仍查 [C-ERP可视化版](../../xbot-api-docs/docs/extensions/activity-a90a8311.md)；本案例不证明市场线上版本已经公开同名函数，也不改变旧 `process15` 的参数契约。
- 适合参考：在报表 iframe 内筛选日期和店铺、设置三态复选框、提交 CSV 异步导出，再通过下载中心返回文件路径。

## 模块与参数

| 模块与固定源码 | 项目内函数签名 | 输入含义 |
| --- | --- | --- |
| [download_return_details.py](https://github.com/yingdao-workspace/shadowbot-c-erp/blob/1f50f251ccccb364fdc292e15cfdd59ce8794e16/download_return_details.py) | `download_return_details(page, shop_name, inbound_time, creation_time)` | `page` 为已初始化的 ERP Page；`shop_name` 为空时不过滤店铺；两个时间范围分别为入库时间和制单时间，各接收 `(开始日期, 结束日期)`，日期字符串为 `yyyy/mm/dd` |
| [download_delivery_item_details.py](https://github.com/yingdao-workspace/shadowbot-c-erp/blob/1f50f251ccccb364fdc292e15cfdd59ce8794e16/download_delivery_item_details.py) | `download_delivery_item_details(page, shop_name, start_date, end_date)` | `page` 和 `shop_name` 同上；`start_date`、`end_date` 为发货时间开始、结束日期，字符串为 `yyyy/mm/dd` |

两个函数成功时均返回 CSV 文件路径字符串；异常记录当前阶段及完整堆栈，并继续向调用方传播。它们不负责初始化 ERP 或提供登录凭据。

各文件的 `main(args)` 为 Code Flow 入口：退货模块从 `args` 读取 `page`、`shop_name`、`inbound_time`、`creation_time`；发货模块读取 `page`、`shop_name`、`start_date`、`end_date`。两者都把成功路径写入 `args["file_path"]` 并返回该路径。店铺虽允许空值，调用入口仍要求提供 `shop_name` 字段。

## 退货商品明细统计流程

1. `enter_tab(page, "退货商品明细统计")` 进入外层 Tab；后续报表操作通过 `iframe2` 的 `[iframe XPath, 元素 XPath]` 在对应 iframe 完成。
2. 解析入库、制单两个时间范围，重置报表筛选。店铺非空时输入店铺搜索框，并选择大小写不敏感的精确匹配选项。
3. 使用 `select_date` 设置入库时间的开始和结束日期。
4. 按来源项目当前流程，先提交一次入库时间查询以关闭日期窗口；等待未禁用的查询按钮再次出现，最长 40 秒，然后设置制单时间的开始和结束日期。该中间查询是本案例的流程事实，不作为其它报表的通用要求。
5. 对「同意、入库、外仓单据、作废、商品换出」逐一检查 indeterminate 标记；缺少标记时点击对应 input。
6. 提交最终查询，等待未禁用的查询按钮再次出现，最长 40 秒。
7. 记录导出时间，点击「CSV导出」和确认弹窗的「确定」。调用 `get_download_file(page, "退货", export_time, 600)`，从下载中心取得本次导出的 CSV 路径。

报表 iframe 的来源实现定位：`//div[@role="tabpanel"]/iframe[contains(@src, "/report/report/trade_return_order_detail_report")]`。

## 发货商品明细统计流程

1. `enter_tab(page, "发货商品明细统计")` 进入外层 Tab；后续报表筛选、查询和导出在 iframe 完成。
2. 解析发货时间开始、结束日期，重置筛选。店铺非空时搜索并选择大小写不敏感的精确匹配选项。
3. 使用 `select_date` 设置发货时间的开始和结束日期。
4. 对「赠品、货到付款、包材」逐一检查 indeterminate 标记；缺少标记时点击对应 input。
5. 提交查询，等待未禁用的查询按钮再次出现，最长 40 秒。
6. 记录导出时间，点击「CSV导出」和确认弹窗的「确定」。调用 `get_download_file(page, "发货商品明细", export_time, 600)`，从下载中心返回本次 CSV 路径。

用户确认的 iframe src 为 `/report/report/oms_delivery_item_collect_report`；来源实现定位：`//div[@role="tabpanel"]/iframe[contains(@src, "/report/report/oms_delivery_item_collect_report")]`。

## 共用能力与实现边界

| 共用模块与固定源码 | 在本案例中的职责 |
| --- | --- |
| [date_picker.py](https://github.com/yingdao-workspace/shadowbot-c-erp/blob/1f50f251ccccb364fdc292e15cfdd59ce8794e16/date_picker.py) | 精确定位日期字段；空值时先选择今天；依据输入框反馈的日期校准年月，再点击目标日期 |
| [enter_tab.py](https://github.com/yingdao-workspace/shadowbot-c-erp/blob/1f50f251ccccb364fdc292e15cfdd59ce8794e16/enter_tab.py) | 进入指定报表 Tab |
| [get_download_file.py](https://github.com/yingdao-workspace/shadowbot-c-erp/blob/1f50f251ccccb364fdc292e15cfdd59ce8794e16/get_download_file.py) | 按导出关键词和时间进入任务中心，等待导出任务并下载文件，返回实际路径 |

- 日期输入框按标签精确匹配：`(//label[text()='{date_label}']/parent::*/following-sibling::div)//input[@placeholder='{placeholder}']`，用于区别含有相同词语的其它日期字段；占位符为「开始日期」或「结束日期」。
- 输入框 `value` 为空时，先点击输入框，再点击可见日期弹窗中的「今天」按钮；弹窗关闭后重新读取 `value`。来源实现的按钮 XPath 为 `//div[contains(@class, 'ant-picker-dropdown-placement-bottomLeft') and not(contains(@class, 'ant-picker-dropdown-hidden'))]//button[contains(., '今 天')]`。
- `select_date` 按 `%Y-%m-%d %H:%M:%S` 解析输入框值；已有日期与目标相同时跳过，否则打开日历，反复读取输入框值来决定年月翻页方向，然后点击 `td[@title='目标日期']`。其它格式或翻页不更新输入框值的组件，不在本实现的已确认条件内。
- 三态筛选使用 0.1 秒查找当前条件下的 `span[contains(@class,'checkbox-indeterminate')]`；查不到时点击同一条件下的 input。固定提交未增加循环点击或点击后的再次核验。
- 当前查询完成判据是「未禁用的查询按钮再次出现」，不是结果行数或数据完整性核验。报表导出与下载完成是两个阶段；导出时间在点击导出前记录，下载等待上限为 600 秒。
- 下载中心的外层菜单和任务 iframe 由 `get_download_file` 自行处理；报表模块只传入 Page、关键词、导出时间及等待上限。
- 日志采用中文报表上下文，包含店铺、时间范围、当前阶段和下载结果；中间入库时间查询也单独记录提交、等待和完成。

具体 XPath 和流程是固定来源版本的项目事实。复用时以目标项目当前页面和用户确认要求为准，不把它们升级为所有 ERP 页面通用的规则。`iframe2` 调用契约查 [正式事实页](../../xbot-api-docs/docs/iframe2-extension.md)，原生 Page / WebElement 能力查 [browser.md](../../xbot-api-docs/docs/browser.md)。
