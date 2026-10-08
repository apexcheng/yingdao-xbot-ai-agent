---
name: rpa-practices
description: Apply proven ShadowBot/Yingdao RPA development workflows and templates. Use for multi-source or multi-Sheet Excel/WPS automation, asynchronous web export task identification, DingTalk business notification content, and cross-layer troubleshooting. For API signatures use the official xbot API docs; for code style follow project AGENTS.md.
---

# 影刀开发经验与模板

本 Skill 汇总原 `docs/` 的实际开发经验、专项流程与示例。**先按任务类型读取相应的完整参考文件**，不要为简单改动加载全部内容；参考文件保留原有详细判断、风险边界及示例，不用本目录替代正式 xbot API 文档或当前项目 `AGENTS.md`。

## 按场景读取

| 场景 | 必须按需阅读的材料 |
| --- | --- |
| 多个数据源、多 Sheet 共享工作簿、统一或逐任务保存、失败隔离、状态与数据写入安全 | [多数据源报表安全边界](references/multi-source-report-safety.md) |
| 点击导出后在后台任务中心等待并下载，多地区、多分类任务、SPA 动态元素失效 | [网页后台异步导出任务绑定](references/async-export-task-binding.md) |
| 钉钉机器人业务通知的标题、数字汇总、状态、分组、@ 规则及真实文案示例 | [钉钉通知文案与排版偏好](references/dingtalk-notification-style.md) |
| 跨数据、网页、Excel / WPS、接口或环境的复杂故障，需要最小复现和分层排查 | [影刀编码版通用排错](references/troubleshooting.md) |

## 使用边界

- 多数据源的业务失败策略与工作簿保存策略需要分别按业务确定，不默认逐任务保存，也不默认全部成功才能继续。
- 识别后台导出任务时以本轮唯一性为准；已有可靠身份特征就不额外建立历史任务快照。
- 钉钉通知的文案与排版从上述经验页读取；发送消息的函数、参数、返回值仍查 `xbot-api-docs/` 的对应正式事实页。
- 通用排错只在局部 API 排错不足以解决或故障跨层时使用，不把全部检查清单强加给普通小改。
- 复杂项目完整落地可查看知识库 `reference-projects/` 中经筛选的冻结案例，它们是参考代码，不覆盖当前业务规则或正式 API。
