---
name: rpa-practices
description: Apply proven ShadowBot/Yingdao RPA practices for Web automation, Excel/WPS, Chinese business-context logs, DingTalk notifications, cross-run state and retries, and troubleshooting. Includes a real spreadsheet-update workflow-composition example. For API signatures use official xbot API docs; for code style follow project AGENTS.md.
---

# 影刀开发经验与模板

本 Skill 汇总影刀实际开发经验，分技术专题与跨领域专项。**按任务需要读取对应参考文件**，不要求简单改动加载全部内容；API 签名仍查正式 xbot API 文档，常驻开发约束仍以当前项目 `AGENTS.md` 为准。

## 按场景读取

| 场景 | 必须按需阅读的材料 |
| --- | --- |
| Web 自动化：后台异步导出任务绑定、SPA 动态元素失效 | [网页实践](references/web.md) |
| Excel / WPS：多数据源、多 Sheet、工作簿使用和写入边界 | [表格实践](references/excel-wps.md) |
| 中文业务上下文日志：输出格式、关键节点、异常记录与示例 | [日志实践](references/logging.md) |
| 钉钉机器人业务通知：排版、分组、@ 规则及真实示例 | [钉钉通知实践](references/dingtalk.md) |
| 跨技术业务流程组合：多平台来源 → 同一 WPS 工作簿 → 日志与钉钉的真实「表格更新」案例 | [业务流程组合](references/workflow-composition.md) |
| 跨轮次状态示例、失败重试判断、业务结果与通知结果区分 | [跨轮次处理状态与重试](references/cross-run-state-and-retries.md) |
| 跨数据、网页、Excel / WPS、接口或环境的复杂故障，按实际证据分层排查 | [影刀编码版通用排错](references/troubleshooting.md) |

## 使用边界

- 数据源失败是否继续、工作簿何时保存，按当前业务分别判断。
- 钉钉通知的文案与排版从上述经验页读取；发送消息的函数、参数、返回值仍查 `xbot-api-docs/` 的对应正式事实页。
- 通用排错只在局部 API 排错不足以解决或故障跨层时使用，不把全部检查清单强加给普通小改。
