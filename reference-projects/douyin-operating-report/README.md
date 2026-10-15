# 抖音经营报表｜表格更新真实案例

> **定位**：影刀编码版多来源、多 Sheet 表格更新的**唯一项目级参考案例**；是实际实现的固定版本记录，**不是可直接运行的项目模板**。具体 API 和通用编码规范以知识库正式文档为准。

## 来源与使用范围

- 项目：`douyin-bow-profit-report-rpa`；[固定源码提交 `7cb4751`](https://github.com/apexcheng/douyin-bow-profit-report-rpa/tree/7cb4751675d9b062b30527bcc15320a34579ffc1)（2026-10-15）。
- 当前案例只以此 Git 提交为准，不自动追随本机未提交修改或之后的业务更新。资料审查不等于整项目的实机验收；不能据此承诺网页、外部服务或 WPS 在其它机器上直接运行成功。
- 适合参考：一个目标 WPS 工作簿、多来源文件导出、网页网络响应、独立 HTTP API、全量覆盖和增量/差异更新、跨日跳过、逐 Sheet 结果、统一保存及钉钉通知。
- 源码中涉及未跟踪的私有 `config.py`、影刀应用资源、账号授权和已安装市场指令；**Git 固定源码本身不是完整可部署应用**。只学习结构与数据交接，不复制真实配置、店铺路径、授权信息或专有字段值。

## 主流程：9 个日常 Sheet + 每轮采购成本

```text
run.main(args)
  → kill 残留 WPS → 打开并最大化目标工作簿（本轮仅一次）
  → 从「经营看板」读取各 Sheet 上次成功状态
  → 每轮都执行「采购成本」：航桥 API → 比对 → 按需写入
  → 判断其余 9 个日常 Sheet 是否全部「今日跳过」
      ├─ 是：不初始化 ERP/抖店、不处理日常 Sheet；回写状态并保存本轮结果
      └─ 否：启动广告弹窗处理
             → ERP 有未执行 Sheet：切换 ERP Profile、清理该 Profile 历史 Page
               → 初始化 ERP → 仅更新未执行的 ERP 退货、ERP 发货（复用同一 Page）
             → 抖店有未执行 Sheet：切换抖店 Profile、清理该 Profile 历史 Page
               → 初始化抖店 → 仅更新未执行的 7 个抖店相关 Sheet
             → 某平台的 Sheet 均已完成：跳过该平台初始化及启动清理
             → 日常任务全部成功时按 Profile 清理多余 Page
  → 经营看板写入各 Sheet 状态 / 按条件更新完成时间
  → 统一保存目标工作簿
  → finally 结束 WPS → 统计结果 → 按条件发送钉钉
```

- 10 个 `update_*.py` 对应 **10 个被跟踪的 Sheet**：ERP 2 个，抖店相关 7 个，以及采购成本 1 个。
- 主流程直接以明确的业务顺序调用各 `update_xxx.update(...)`，共享已打开的目标 `target_workbook`；不为了展示而增加任务框架或重复打开目标文件。
- **每轮采购成本都检查**：即使其余 9 个 Sheet 今天已成功，也会先执行成本同步，随后保存本轮结果；这不是“10 个全部完成便退出”的旧模式。
- 日常 Sheet 仅在历史状态为「成功」且处理日期为今天时标记「今日跳过」；不重复下载、写入。采购成本特意不套用这一跳过条件。状态读取失败时此项目会记录警告并继续更新，这个容错决定不适用于所有有副作用的业务。
- **平台初始化由待执行任务决定**：先检查 ERP 的 2 个 Sheet、抖店的 7 个 Sheet 是否仍有「未执行」，再分别决定是否初始化平台与清理该 Profile 的启动 Page。不能把「仍有日常任务需要执行」等同于「两个平台都必须登录」。这属于任务依赖驱动的初始化，保存和收尾仍照常执行。

## 十个模块：按数据获取与更新模式寻找源码

| Sheet / 模块 | 数据来源与操作 | 更新方式 |
| --- | --- | --- |
| ERP 退货｜[update_erp_returns.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/update_erp_returns.py) | 复用主流程的 ERP Page，调用市场指令下载退货明细 | 文件经 WPS 读取，覆盖事实层 |
| ERP 发货｜[update_erp_deliveries.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/update_erp_deliveries.py) | 同一个 ERP Page，市场指令下载发货明细 | 文件经 WPS 读取，覆盖事实层 |
| 平台订单｜[update_order_data.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/update_order_data.py) | 抖店页面导出、短信验证码及加密 ZIP 解压 | 文件经 WPS 读取，覆盖事实层 |
| 全域投放｜[update_global_promotion.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/update_global_promotion.py) | 网页筛选、导出投放报表 | 文件经 WPS 读取，覆盖事实层 |
| 直播链接｜[update_live_links.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/update_live_links.py) | 逐日网页导出直播商品数据 | 按已有日期向后追加 |
| 达人佣金｜[update_selected_alliance.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/update_selected_alliance.py) | 联盟财务页查询、等待导出任务 | 文件经 WPS 读取，覆盖事实层 |
| 团长服务费｜[update_leader_fee.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/update_leader_fee.py) | 联盟财务页查询、等待导出任务 | 文件经 WPS 读取，覆盖事实层 |
| 达人投流｜[update_influencer_promotion.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/update_influencer_promotion.py) | 多账户网页下载投放数据并合并 | 合并后覆盖事实层 |
| 产品库｜[update_product_library.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/update_product_library.py) | DOM 负责查询/排序/翻页，网络响应提供商品数据 | 补齐旧商品时间，再按创建时间降序增量追加 |
| 采购成本｜[update_purchase_cost.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/update_purchase_cost.py) | `urllib.request` 使用只读 Token 分页请求航桥 API | 全量读取并比较规格代码；有变化才覆盖成本区域 |

### 模式一：文件导出 → WPS 事实层覆盖

- `download()` 获取文件或已打开的源工作簿；`update(target_workbook, ...)` 只处理自己负责的 Sheet。复用的 ERP Page 从主流程传入，避免重复初始化。
- [utils.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/utils.py) 中的 `open_source_workbook()` 使用 WPS 打开来源文件；`replace_fact_area()` 只清空约定事实层，读取来源二维矩阵并批量写入目标。订单号等长标识在写入前按当前业务需求保留文本形态。
- 某些业务是多来源合并或按日追加，**不是所有 Sheet 都适合无条件覆盖**；例如直播链接按日期追加。固定列坐标和业务字段映射来自项目配置，不应被提升为通用规则。

### 模式二：网页操作触发请求 → 读取响应 → 增量补录

以 [update_product_library.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/update_product_library.py) 为代表：

1. 从目标产品库读取已有商品 ID 和时间。对于时间缺失的 ID，通过输入商品 ID、点击查询触发 `/product/tproduct/list` 请求；监听响应、按 ID 精确匹配后补齐时间；找不到时保留空值并记录业务提示。
2. 以补齐后的最大创建时间为下界，网页按创建时间降序排序；依次通过查询、下一页动作触发网络请求，解析响应中的商品列表。
3. 到达时间边界停止，追加未见过的较新 ID，商品 ID 保留文本形态；变更及未找到 ID 供钉钉通知使用。

**真实边界**：增量扫描在 `created_at <= MAX` 时结束，同一时间或更早但缺失的商品不会被扫描补齐；监听读取第一个匹配响应，尚不能称为经过查询条件校验的严格请求唯一关联。第一阶段失败仍尝试第二阶段，结果按模块现有异常语义处理。用户提供用于取业务数据的 XPath 时，优先遵循正式 [Web 规则](../../project-template/.agents/skills/rpa-practices/references/web.md)，不要从示例推导为必须做 DOM 取数。

### 模式三：HTTP API → 完整读取 → 差异写入

以 [update_purchase_cost.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/update_purchase_cost.py) 为代表：

1. 直接通过 HTTP API 分页读取航桥采购成本，使用私有配置中的只读 Token；核对接口返回、分页完整性、记录与规格代码，并按业务口径转换成本数值。
2. 从目标表读取当前成本区，以规格代码为键对比旧值、新值（含新增、修改、删除）。
3. **无差异：不写成本区**；有差异：写入前得到完整来源，再覆盖约定成本列；保留目标表其它公式及区域。
4. 返回本轮变更规格代码，供主流程在保存成功后最多展示 5 个 ID 的钉钉摘要。

写入过程中出现异常会**尝试**恢复本轮旧值，但 WPS 写入不具备数据库事务保证；恢复再次失败可能覆盖原异常，不应把此实现介绍为可靠回滚。来源数据核对是采购成本**已确认的业务要求**，不是要求所有表格下载都增加同类校验。

## 状态、重试、保存与通知的真实边界

- [run.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/run.py) 的 `update_sheet()` 按源码注释约定，对**整个 Sheet 的下载、读取、写入操作最多尝试 2 次（首次执行 + 失败后重试 1 次）**，最终失败记状态并继续处理独立 Sheet；实际次数由未收录在固定提交中的私有配置 `SHEET_ATTEMPTS` 决定。ERP 或抖店初始化失败则按来源分组标记受影响任务。存在依赖时遵守当前项目的实际失败分组，而不是假定所有任务独立。
- 看板的记录包含 Sheet、结果、尝试次数、处理时间、说明；「今日跳过」在本轮结果中保留原成功时间，写回看板时仍记「成功」。单个 Sheet 的「成功」表示业务写入步骤已完成，**不意味着统一保存已经成功**。
- 普通事实层可能先清空再写入；如果中途失败且主流程最终保存，可能保留部分修改，**不是原子更新**。产品库以 ID 事件辅助通知，不是完整的持久化审计：失败重试时可能清空前次尝试的事件。
- **日常任务完成后的收尾浏览器清理**与 `target_workbook.save()` 由独立的 `try/except` 处理，保持清理在保存之前的业务顺序；这次收尾清理仍遍历两个 Profile，即使某个平台本轮未初始化；清理异常不会阻止保存，两个失败分别记错误。**启动阶段只清理需要初始化的平台的历史 Page**，该清理未单独捕获异常，失败会中断本轮并跳过保存。程序 `finally` 仍会结束 WPS，即使保存失败也不保留 WPS 现场。
- [notify.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/notify.py) 按 Sheet 结果分组显示本轮更新、今日跳过和失败；额外列出产品库 ID 变化或异常、采购成本变更摘要，以及独立的「表格是否已保存」状态。采购成本没有变化且全部日常 Sheet 今日跳过、无异常时不发送通知；通知失败不会反向修改已保存的 Sheet 结果。

## 文件职责与按需阅读路径

| 首先读 | 需要回答的问题 |
| --- | --- |
| [run.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/run.py) | 十项任务顺序、ERP/抖店初始化、跨日跳过、最多两次尝试、统一保存和异常收尾 |
| [utils.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/utils.py) | 多来源文件如何用 WPS 读取、复用对象、写入约定事实层 |
| [update_product_library.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/update_product_library.py) | 怎样从页面操作和网络响应获取业务数据并增量写入 |
| [update_purchase_cost.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/update_purchase_cost.py) | 怎样将直接 HTTP API 与差异对比、WPS 写入结合 |
| [notify.py](https://github.com/apexcheng/douyin-bow-profit-report-rpa/blob/7cb4751675d9b062b30527bcc15320a34579ffc1/notify.py) | Sheet 结果、产品 ID 事件和采购成本差异怎样进入通知 |

其它业务模块从上方十项清单按需打开 1～2 个即可。不单独维护 XPath 清单、可复制的业务账号、配置内容或完整源码快照。

**规范边界**：这是来源提交当时的运行事实。影刀 Page、网络监听、Excel/WPS、钉钉等 API 优先查 [正式 API 文档](../../xbot-api-docs/docs/browser.md)、[表格操作 Skill](../../project-template/.agents/skills/spreadsheet-operations/SKILL.md) 与 [Web 实践](../../project-template/.agents/skills/rpa-practices/references/web.md)；案例中的日期边界、状态字段、写入区域、外部接口、通知阈值不能自动套给其它项目。固定版本的达人投流页面有特定的右键交互与 `time.sleep(3)`，属于项目实现差异，不替代模板中加载完成后等待 2 秒的通用规则。
