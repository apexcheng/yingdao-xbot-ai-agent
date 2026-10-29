# 影刀功能模板｜面向 AI 直接编写业务代码

本目录是**跨项目操作知识**，不是新的 Python 工具包。按所需功能读取一页即可写入当前 RPA；优先影刀原生 API、Python 标准库，未来新项目**不使用「增强工具2026」**。完整应用与业务口径仍属于真实项目。

## 按需求直达

| 需求 | 位置 | 当前证据 |
| --- | --- | --- |
| 抖店（抖音电商）手机号 + ntfy 验证码登录 | [抖店](site-logins/douyin-shop.md) | 2026-10-29 用户确认 XPath、短信格式；经营报表 `91acca7` / V34 发布，未实机登录验收；新项目模板改用原生 HTTP 接码 |
| 拼多多商家账密登录 | [拼多多](site-logins/pdd.md) | 旧市场指令已核源码，XPath 需按当前页面核实 |
| 京麦账密登录 | [京麦](site-logins/jingmai.md) | 同上 |
| 千牛账密登录 | [千牛](site-logins/qianniu.md) | 同上；需独立 iframe2 市场指令，不依赖增强工具2026 |
| 支付宝账密登录 | [支付宝](site-logins/alipay.md) | 同上；不含风控、短信二次验证 |
| 本轮文件下载完成 | [下载等待](download-wait.md) | 基于现有市场指令能力/行为提炼，需按浏览器与目录实测 |
| ntfy 发送、轮询接收、短信时间过滤 | [ntfy 消息](ntfy-messages.md) | ntfy JSON 轮询接口与现有已核实现；标准库写法待新项目实测 |
| 钉钉群 Webhook 发送 | [钉钉 Webhook](dingtalk-webhook.md) | 标准 HTTP 写法；企业机器人私聊等不在此模板内 |
| XPath 等待、异常堆栈、文件占用等 | [原生简写与功能边界](native-shortcuts.md) | 已核原生 API / 标准库能力与尚不具备的能力 |

## 「增强工具2026」公开能力处置清单

| 旧入口 | 新项目处理 | 边界 |
| --- | --- | --- |
| `login_pdd_seller / login_qianniu / login_jingmai / login_alipay / login_douyin_seller` | 站点登录模板 | 抖店默认手机号；旧邮箱登录留在旧 API 事实页供维护 |
| `wait_appear_by_xpath` | 原生 `find_by_xpath`；多命中允许时用 `find_all_by_xpath` | 避免新增等价等待封装 |
| `wait_download_file` | 下载等待模板 | 需绑定本轮下载时间；本轮业务任务唯一性由调用方负责 |
| `format_exception_detail` | 标准库 `traceback.format_exc()` | 不额外包装同一异常 |
| `send_ntfy_message / receive_ntfy_message` | ntfy 模板 | topic、消息格式和消费边界由业务确定 |
| `send_dingtalk_group` | 简单群 Webhook 用钉钉模板 | 企业机器人群图片、会话 API 不与 Webhook 等价 |
| `send_dingtalk_private` | **尚无同能力的已核原生模板** | 需要企业应用鉴权、用户 ID 与发送 API 的独立核验；不能使用 Webhook 冒充私聊 |
| `to_markdown_table` | Python 内联格式化 | 只需当前数据列，不机械照搬通用表格封装 |
| `is_win_element_clickable` | 原生属性检查；见原生简写 | 屏幕坐标/遮挡判断不能仅凭 visible 代替 |
| `get_wps_lock_user` | 原生 `ReadOnly` 判断只读状态 | **锁文件中解析占用者用户名尚无等价模板**，不可声称已迁移 |
| `dialog_result_to_dict` | 优先项目 `config.py`；特殊对话框依原生 API 结果处理 | 不自动猜返回对象类型/字段转换 |
| `save_secret_config / load_secret_config` | 默认按项目规则用本地 Git 忽略的 `config.py` | **DPAPI 加密持久化尚无等价已验模板**；确有用户级持久化需求时专项核实 |

**迁移状态**：已建立常用功能的无「增强工具2026」模板；上表标明的复杂能力**不是已完成一比一替换**。新项目不安装旧工具；确需尚未覆盖的能力时，先核实原生 API / 标准接口并补对应功能模板，不能静默降级。旧项目保持原有依赖，不能因本目录建立就直接批量删指令。

## 维护原则

- 单站点一篇；不同登录方式在同一篇中标记当前推荐与历史模式。
- 每个示例注明适用条件、源版本/来源、未验证步骤；只放示例账号/主题，不包含密钥或用户数据。
- 登录中遇到验证码、人机风控、子账号选择等，不能把 URL 离开 `login` 单独等同于全部业务权限已可用。
- 站点 XPath 经实际运行失效，更新此处对应模板，不新建「某站点登录增强工具」。
- 本目录不是对未来页面永久有效的承诺；如果没有可信 XPath，标注缺口，不臆造。
