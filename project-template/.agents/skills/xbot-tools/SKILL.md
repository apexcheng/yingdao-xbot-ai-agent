---
name: xbot-tools
description: Operate ShadowBot/Yingdao CLI, develop and publish xbot Code apps, synchronize flows, and diagnose or repair project metadata and Sigstore problems. Read only the task-relevant section; execution, publication, and repair require the user's explicit intent.
---

# 影刀工具：CLI、应用生命周期与项目诊断

该 Skill 汇总影刀工具与项目级操作。根据任务进入「CLI 操作」「应用开发闭环」或「项目诊断」，不要求执行无关流程。默认先只读；启动任务、同步发布、改写项目文件和修复签名都要遵守各部分原有的执行边界。

新建或补全影刀编码版项目时，按需先阅读 [最小 base 项目骨架与验收说明](references/base-project-skeleton.md)。模板文件仍位于当前项目的 `project-template/`，不使用参考文档替代真实项目文件。普通 CLI 账户 / 任务查询无需加载骨架说明。

## CLI 操作

ShadowBot CLI 只用于影刀自身运行和生命周期操作；普通源码、配置与业务分析直接在项目工作区完成。

### Executable

Prefer the stable launcher path:

`C:\Program Files\ShadowBot\shadowbot.shell-cli.exe`

Do not pin commands to versioned directories such as `shadowbot-6.x.x`; ShadowBot updates can change those folders.

### 按需检查与命令帮助

- CLI 连接或服务可用性不明时查 `system health`；涉及模式或任务状态时查 `system state`；需要当前账号身份时查 `auth current`。已掌握所需信息时不重复预检。
- 遇到不熟悉的命令或不确定的参数，先运行 `"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" <command> -h`；不要猜命令标志、ID、参数取值或执行顺序。

### Find ShadowBot apps/projects

For user-developed apps:

`"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" console app --app-type developed --search "<keyword>"`

For subscribed apps, use `--app-type subscribed`.

Use the returned `appId` as the canonical app identifier. To inspect one app and its runtime input parameters:

`"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" console app detail --app-id <UUID> --app-type developed`

已有可信项目路径或 App ID 时直接使用，不重复搜索；需要发现应用身份时再用 `console app` 搜索，多个结果必须核对元数据后确定目标。需定位源码时据此确认对应项目目录，不按目录顺序猜测。

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

ShadowBot 6.3.22 已验证：`studio create` **新建**应用后同步关闭；`studio open` **不带 `--app-id`** 时新建应用并保持 Studio 打开。要打开**已有应用**，在当前 PowerShell 进程设置 `SWITCH_STUDIO_MCP_CLI_SUPPORT=1`，通过 `studio open -h` 确认支持 `--app-id` 后执行 `studio open --app-id <uuid>`。不同版本先以当前 CLI 帮助为准，不要把不带 ID 的 `studio open` 误用为打开已有项目。

### Runtime modes

The CLI supports `console` and `assistant` mode switching:

`"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" mode switch --to console`
`"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe" mode switch --to assistant`

Console-only operations can return `not_supported` in Assistant mode. Check `system state` before switching. Do not use `--force` to switch to Console while a task is running unless the user explicitly wants that interruption/risk.

### 低频配置、UI 与连接排错

涉及影刀配置、窗口 UI 操作或 CLI 本地 REST 连接异常时，按需阅读 [CLI 辅助命令与连接排错](references/cli-auxiliary-commands.md)。

### Safety and modification rules

- Read/query operations are safe defaults.
- Use ordinary project workspace capabilities for source inspection, file operations, project-local commands, and temporary diagnostic or migration scripts. Use this CLI only when a ShadowBot-specific capability is actually needed.
- Treat `console app recycle`, permanent delete, publish, collaborator changes, `config set`, task stop, forced mode switches, and similar state-changing operations as explicit user-intent actions.
- Treat all app/task execution commands as real execution with possible business side effects. Only execute when the user explicitly requests a run; do not make app execution a default development, verification, or completion step.
- Never invent an app UUID or silently pick the first search result when multiple apps match. Use names and returned metadata to disambiguate.
- Prefer CLI outputs as the source of truth for current ShadowBot app IDs, task state, account state, and supported command parameters.

## 应用开发闭环

按需读取真实项目 `AGENTS.md` 与相关正式知识；CLI 操作按上方章节及本机帮助执行。新建应用及模板合并步骤见 [最小 base 项目骨架](references/base-project-skeleton.md)。

1. 保存已有应用可使用 `studio current save`，同步并关闭使用 `studio current sync`。若在项目目录外部修改了 `package.json` / Code flow，必须让 Studio 重新载入磁盘状态后再保存、同步；不能仅凭 `console app publish` 成功认定磁盘改动已发布。
2. **只有新增或删除项目根目录 `.py` 文件时**才运行 `python .agents/skills/xbot-tools/scripts/sync_codeflows.py` 同步 Code flow 注册并编译；只修改已有 `.py` 不运行。该工具不负责保存、同步或发布。
3. 可选发布 helper：`python .agents/skills/xbot-tools/scripts/publish_app.py --project-dir <项目目录> --update-log "<发布说明>"`。负责重新加载、保存、同步、发布并检查线上版本，不负责 Code flow 注册。
4. 实际发布后核实线上版本对应本次代码；如已按用户要求运行，再根据任务状态与日志确认实际结果，未运行不得宣称业务已验证。
5. 未经发布运行验证，不得假定 Code flow 可以直接作为应用的 `startup`；历史实验和验证边界见 [应用生命周期特殊案例](references/app-lifecycle-cases.md)。整应用复制的已知限制也在该参考文档中。

## 项目诊断

排查应用文件损坏、Sigstore 校验失败、Flow 重名时，按需阅读 [项目诊断](references/project-diagnostics.md)。普通业务代码问题不触发该流程。
