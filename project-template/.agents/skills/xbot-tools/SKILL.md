---
name: xbot-tools
description: Operate ShadowBot/Yingdao CLI, develop and publish xbot Code apps, synchronize flows, analyze legacy Visual projects, and diagnose or repair project metadata and Sigstore problems. Read only the task-relevant section; execution, publication, and repair require the user's explicit intent.
---

# 影刀工具：CLI、应用生命周期与项目诊断

该 Skill 汇总影刀工具与项目级操作。根据任务进入「CLI 操作」「应用开发闭环」或「项目诊断与迁移」，不要求执行无关流程。默认先只读；启动任务、同步发布、改写项目文件和修复签名都要遵守各部分原有的执行边界。

新建或补全影刀编码版项目时，按需先阅读 [最小 base 项目骨架与验收说明](references/base-project-skeleton.md)。模板文件仍位于当前项目的 `project-template/`，不使用参考文档替代真实项目文件。普通 CLI 账户 / 任务查询无需加载骨架说明。

## CLI 操作

Use the installed ShadowBot agent-oriented CLI for ShadowBot-specific app lifecycle and runtime operations instead of guessing internal APIs or manually automating the ShadowBot UI.

This CLI is a **supplementary ShadowBot tool, not the default way to inspect or develop project source**. Read and analyze the actual project directly for source files, configuration tracing, code search, temporary scripts, and ordinary project commands. Do not use CLI flow/block inspection as a substitute for source analysis when the project can answer the question directly.

### Executable

Prefer the stable launcher path:

`C:\Program Files\ShadowBot\shadowbot.shell-cli.exe`

Do not pin commands to versioned directories such as `shadowbot-6.x.x`; ShadowBot updates can change those folders.

### Core workflow

1. Check availability first:
   `"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" system health`
2. Inspect runtime state when mode/UI/task state matters:
   `"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" system state`
3. Inspect the current account when authentication matters:
   `"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" auth current`
4. The CLI is self-documenting for LLM agents. Before any unfamiliar or parameterized action, run:
   `"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" <command> -h`
   Do not guess flags, IDs, accepted values, or workflow ordering.

### Find ShadowBot apps/projects

For user-developed apps:

`"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" console app --app-type developed --search "<keyword>"`

For subscribed apps, use `--app-type subscribed`.

Use the returned `appId` as the canonical app identifier. To inspect one app and its runtime input parameters:

`"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" console app detail --app-id <UUID> --app-type developed`

When the user asks which ShadowBot project contains a feature, webhook, task, or automation, search app names first with `console app`. If source-level inspection is then required, use the discovered app identity to locate the corresponding local ShadowBot project rather than guessing from directory order.

### Run and inspect tasks

Before running, discover the app and inspect its detail when inputs may be required.

Starting an app or task is a real business execution, not a read-only inspection technique. Do not start a workflow merely to discover runtime variables, configuration values, Sheet names, credentials, account lists, or other data that can be obtained by static source analysis or a direct minimal API request. **Only run an app or task when the user explicitly asks to run it.** Do not infer permission to run from “development completed”, “ready for testing”, “needs verification”, or similar states.

Help:
`"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" console task run -h`

Typical default-parameter run:
`"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" console task run --app-id <UUID> --app-type developed`

The default task run is synchronous and streams logs. Use `--async` only when the user explicitly wants immediate return or the workflow specifically requires it.

Useful task commands:
- `console task status`
- `console task history`
- `console task logs`
- `console task stop`

Run `-h` on the exact subcommand before supplying parameters.

### Studio operations

Useful commands:
- `studio current get`
- `studio current save`
- `studio current sync`
- `studio current update-info`
- `studio create`
- `studio open`

`studio create` creates a PC automation app and sync-closes it. `studio open` creates a PC automation app and keeps Studio open. Do not assume either command opens an existing app; inspect help and current CLI capabilities instead.

### Runtime modes

The CLI supports `console` and `assistant` mode switching:

`"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" mode switch --to console`
`"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" mode switch --to assistant`

Console-only operations can return `not_supported` in Assistant mode. Check `system state` before switching. Do not use `--force` to switch to Console while a task is running unless the user explicitly wants that interruption/risk.

### Settings and UI

Configuration workflow:
1. `config list`
2. `config describe --key <key>`
3. `config get --key <key>`
4. `config set --key <key> --value <value>`

Some settings require a ShadowBot restart. Verify after changes.

UI actions are exposed through:
`ui --exec <action>`

Run `ui -h` before use. Supported actions include Studio/Console minimize/maximize and switching to schedule/assistant/console.

### Safety and modification rules

- Read/query operations are safe defaults.
- Use ordinary project workspace capabilities for source inspection, file operations, project-local commands, and temporary diagnostic or migration scripts. Use this CLI only when a ShadowBot-specific capability is actually needed.
- Treat `console app recycle`, permanent delete, publish, collaborator changes, `config set`, task stop, forced mode switches, and similar state-changing operations as explicit user-intent actions.
- Treat all app/task execution commands as real execution with possible business side effects. Only execute when the user explicitly requests a run; do not make app execution a default development, verification, or completion step.
- Never invent an app UUID or silently pick the first search result when multiple apps match. Use names and returned metadata to disambiguate.
- Prefer CLI outputs as the source of truth for current ShadowBot app IDs, task state, account state, and supported command parameters.
- If a command fails because the local REST API is unavailable, verify `system health`, ShadowBot process/runtime state, and authentication before attempting alternate methods.

## 应用开发闭环

先读真实项目 `AGENTS.md`。项目结构和 API 事实按知识库 `llms.txt` 查找；CLI 命令、参数和登录恢复按 `本 Skill 的「CLI 操作」部分` 执行，以本机帮助和实际返回为准。

源码读取、代码修改、配置追踪和临时脚本直接在真实项目工作区完成；本 Skill 中的 ShadowBot CLI 只承担创建 / 打开 / 保存 / 同步 / 发布 / 运行等应用生命周期动作，不把 CLI 当成源码分析器。

1. 新建应用时，先核对 CLI 的 `studio create -h` / `studio open -h`。ShadowBot 6.3.22 实测中，`studio create` 创建并同步关闭应用，但返回结果不含应用 ID；随后用唯一临时应用名执行 `console app --search <name>` 可取得 `appId` / `versionId`。再用 `auth current` 返回的 `userId` 组合本机目录 `%LOCALAPPDATA%\ShadowBot\users\<userId>\apps\<appId>\xbot_robot`，并以该目录 `package.json.uuid == appId` 作为项目根确认，不凭应用名猜目录。
2. 重新打开已有应用与创建新应用必须分开。ShadowBot 6.3.22 实测需要在当前 PowerShell 进程设置 `SWITCH_STUDIO_MCP_CLI_SUPPORT=1` 后重新查看 `studio open -h`；此时帮助会正式列出 `--app-id`。使用 `studio open --app-id <uuid>` 可重新打开已有 developed app；不传 `--app-id` 的 `studio open` 仍是创建新应用。保存已有应用可用 `studio current save`，同步并关闭用 `studio current sync`。若先在项目目录外部修改了 `package.json` / Code flow，必须让 Studio 重新载入磁盘状态后再保存、同步；不要把 `console app publish` 的成功返回当作磁盘改动已经进入新版本。
3. 将模板中缺失的文件合并到真实项目，保留影刀生成的文件和已有业务改动。配置变量由 `config.py` 管理，默认不新增影刀运行输入参数；`run.py` 的 `main(args)` 是 Code 流入口，其他模块正常导入调用。只有新增或删除项目根目录 `.py` 文件时才运行本 Skill 内置 helper：`python .agents/skills/xbot-tools/scripts/sync_codeflows.py`；只修改已有 `.py` 文件时不要运行。该 helper 只同步 Code flow 注册并做编译检查，不承担保存、同步或发布。
4. 用户明确要求发布外部修改后的应用时，优先运行本 Skill 内置 helper：`python .agents/skills/xbot-tools/scripts/publish_app.py --project-dir <项目目录> --update-log \"<发布说明>\"`。它从目标项目 `package.json.uuid` 读取 App ID，统一执行 `studio open → studio app reload → studio app save → studio current sync → console app publish`，并在发布前后读取线上版本；只有线上 `versionId` 真正变化才判定发布成功。该 helper 不调用 `sync_codeflows.py`，新增 / 删除 `.py` 时应先单独执行 Code flow 同步。发布和运行都不是默认开发收尾动作，只有用户明确要求时才执行。
5. 排错时在相关步骤临时加日志，不记录凭据或敏感数据；根据日志修复并重试。完成后删除临时日志并重新保存 / 同步。若本次任务由用户明确要求发布，再确认发布版本对应清理后的代码；若用户明确要求运行，再单独确认运行范围、副作用，并结合任务状态与日志验收。
6. 只有隔离验证 Code 流可作为 `startup`，且 Studio 保存、同步、发布与 Console CLI 运行都成功，并能由任务状态 / 日志证明发布任务实际执行了 `run.py`，才把应用入口改为 `run.py`。需要证明服务器收到的 manifest 就是当前本地版本时，可对比 ShadowBot 主日志中的 `packageJsonMd5` 与本地 `package.json` 的 MD5。2026-09-27 在 ShadowBot 6.3.22 的隔离临时应用中，`run` Code flow 可在 Studio 内直接运行且日志出现探针，本地与上传的 `package.json` MD5 也一致；但即使 `package.json.startup=\"run\"`、`studio app reload`、`studio app save`、`studio current sync`、发布均成功，`console task run` 任务仍以 `completed` 结束且任务日志只出现“开始执行 / 执行结束”；将 `run.py` 改为抛出唯一异常后，发布任务仍未出现该异常。因此当前只记录“直接 Code startup 未通过本次发布运行验证”，不推断为产品不支持；此前继续保留 Visual 启动流，不单凭修改 `package.json` 宣称入口已经生效。
7. 复制整个应用前必须先核对当前 CLI 帮助，不把流程级命令误认为应用级命令。ShadowBot 6.3.22 实测没有可直接等价完成“复制整个 developed app”的应用级 copy / clone / duplicate 命令；`studio flow copy` 只复制 Flow，不能替代整应用复制。若确需通过“新建应用 + 复制本地项目文件”实现整应用副本，必须保留新应用自己的身份信息，并意识到直接复制 / 改写 `package.json` 可能造成 `package.sigstore` 校验失败或“应用文件已损坏”；出现此类问题按 [项目诊断与迁移](references/project-diagnostics.md) 处理，而不是反复运行应用验证。

## 项目诊断与迁移

读取 / 迁移旧版可视化项目，或排查应用文件损坏、Sigstore 校验失败、Flow 重名时，按需阅读 [项目诊断与迁移](references/project-diagnostics.md)。普通业务代码问题不触发该流程。
