# 跨境补货表：多数据源、单 Page 过程式更新真实实现参考

这是当前跨境补货影刀编码版项目的**脱敏、冻结源码快照**。需要理解多 Sheet WPS 更新、固定任务顺序、网页后台导出和逐任务保存时，优先参考本案例，而不是将“整轮统一保存”的旧教学 Demo 当作通用默认写法。

## 来源与状态

- 来源项目：跨境补货表自动更新（影刀编码版）
- 来源 Git 仓库：`apexcheng/cross-border-replenishment-rpa`
- 来源 Git commit：`4038cea4913a5f8c7deade977179bde94f8074a7`
- **历史实现提示**：后续真实项目 `6356d6f` 已删除 `_discard_unsaved_and_reopen()` 及写入失败后重开继续机制，状态判断改为只读任务名与最近成功时间；Shopee 导出任务不再默认预扫描历史列表，C-ERP 删除了加权匹配。冻结源码保留旧实现供历史问题复现，**这些部分不再是推荐写法**。后续进一步修复以真实项目当前代码为准。
- 快照日期：2026-10-08
- 快照性质：冻结，不随实际项目自动更新；未来需对照新 commit 明确更新
- 收录范围：`run.py`、六个 `update_*.py` 业务模块、`utils.py` 和脱敏配置字段示例
- 验证边界：来源项目在该版本完成 13 项离线测试和 7 个业务 Python 模块编译检查；**不能据此声称所有平台在 Windows 影刀中完成真实执行验收**

## 推荐按问题读取

| 需要参考的能力 | 优先阅读 |
| --- | --- |
| 固定业务任务显式调用、状态读取、单任务保存、统一快照和通知（失败重开属旧实现） | [`snapshot/run.py`](snapshot/run.py) |
| 一个 Page 一个主函数、地区切换、任务中心按本轮记录匹配 | [`snapshot/update_shopee_warehouse.py`](snapshot/update_shopee_warehouse.py) |
| 与上面同类的商品管理双地区导出；不同业务各自匹配任务 | [`snapshot/update_shopee_sku_mapping.py`](snapshot/update_shopee_sku_mapping.py) |
| 登录验证码作为独立能力，其余下载动作顺序放在 `prepare()` | [`snapshot/update_seaya_stock.py`](snapshot/update_seaya_stock.py) |
| C-ERP 的 Page 获取、同一主函数操作 iframe/任务中心；CSV 解码单独处理 | [`snapshot/update_cerp_products.py`](snapshot/update_cerp_products.py) |
| 从历史订单筛选、导出、等待本轮文件下载 | [`snapshot/update_miaoshou_shipments.py`](snapshot/update_miaoshou_shipments.py) |
| 原始数据直接计算三国销量；先校验三张表，再统一保存 | [`snapshot/update_country_sales.py`](snapshot/update_country_sales.py) |
| RAW 区固定列校验、限制覆盖范围、超长数字保护与通用文件读取 | [`snapshot/utils.py`](snapshot/utils.py) |
| 配置类别、依赖字段与脱敏占位符 | [`snapshot/config.py.template`](snapshot/config.py.template) |

## 值得借鉴的流程边界

1. `main(args)` **显式按固定顺序**调用五个 `_update_data_source(...)`，而不是先拼任务元组再循环；业务模块独立命名为 `update_xxxx.py`。
2. `_update_data_source()` 处理一个 Sheet 的今日跳过、下载、数据写入、失败状态和独立保存。此快照还带有已废弃的“失败重新打开工作簿并继续”逻辑；新项目不要照搬，按业务要求决定失败是否中断。
3. 妙手历史订单**一轮只下载一次**，供明细与三国销量共享原始结果；明细 Sheet 是否成功保存，不决定三国销量能否使用已下载数据。
4. 三国销量是一个业务任务，全部数据先校验后写入，**三张表全部成功才保存**；不从妙手明细 Sheet 的公式区再读取数据。
5. 同一个 Page 的地区切换、导出、任务中心、等待、下载在 `prepare()` 自上而下展开。独立登录、页面就绪及较复杂的数据解析才封装辅助函数。
6. 快照旧代码用提交时间、导出前历史任务快照、文件名和状态识别本轮任务。新版允许直接使用提交时间 + 文件名 + 唯一任务绑定，不要求每次预扫描；仍不能下载历史成功任务。
7. 快照中 WPS 的 `set_saved(True)` + 重新打开是在**放弃未保存内存修改**，不是数据库级事务，也已从新版删去；自动保存、保存失败或磁盘部分写入都不能仅靠该流程保证回滚。

## 脱敏和使用限制

- 仅复制业务源码中能代表实现方式的内容；**未收录**真实 `config.py`、凭据、Webhook、业务工作簿、下载数据、项目运行环境、PRD、`.dev/` 测试目录、IDE/影刀自动生成的项目文件。
- 商品管理站点 ID、个人导出模板名称已经替换为 `EXAMPLE_...` 占位符；`config.py.template` 中站点 ID、文件路径、凭据也只是占位，不是来源 commit 原样文件。其他选取的源码按来源版本保留业务步骤，不为适配教学用途重写流程。
- **本快照不能直接投入生产运行**：缺少影刀项目包、真实业务配置、模板和凭据；页面 XPath、下载命名及业务列规则只对原项目场景有参考意义。
- 跨项目开发时，当前用户要求、项目正式规范、[项目模板规则](../../project-template/AGENTS.md)、[编程风格](../../docs/coding-style.md) 和 [API 文档](../../xbot-api-docs/) 优先于此快照。具体保存模式及失败边界另见 [多数据源安全规范](../../docs/multi-source-report-safety.md)。

### 与原教学 Demo 的区别

[多 Sheet 工作簿教学 Demo](../../docs/examples/multi-sheet-workbook/README.md) 专门演示“一次打开、整轮统一保存”的简单场景；是否逐任务或整轮保存始终由业务要求决定，不以冻结案例的失败恢复实现作为默认规则。
