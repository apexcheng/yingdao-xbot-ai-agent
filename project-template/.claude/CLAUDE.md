# CLAUDE.md

@../AGENTS.md

以上 `AGENTS.md` 是当前影刀项目的唯一主规则入口。Claude Code 执行生成、修改、审查和排错时必须遵守，不得以通用工程化、模块化或抽象化偏好覆盖其中的代码结构规则；不在这里复制另一套规则。

知识库固定路径为 `C:\Users\Administrator\Desktop\影刀xAI开发指南`。需要确认 xbot API、市场指令、base 骨架或排错资料时，优先检查该目录，再按其 `llms.txt` 直达对应页面；目录不存在时立即停止并要求用户提供正确路径，不自行猜测其它位置。

读取 / 迁移旧版影刀可视化项目，或排查“应用文件已损坏”、flow 文件缺失、`package.sigstore` 等项目级问题时，使用 `.claude/skills/xbot-project-diagnostics/SKILL.md`；普通 Python 业务 bug 不触发该 Skill。

影刀同步的触发条件、执行方式及验证边界统一遵守当前项目的 [AGENTS.md](../AGENTS.md)。
