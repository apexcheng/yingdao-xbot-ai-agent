# 影刀工具：CLI、应用生命周期与项目诊断

Operate ShadowBot/Yingdao Studio editor (xbot-bash) and CLI, inspect apps or flows, develop and publish xbot Code apps, synchronize flows, and diagnose project metadata and Sigstore problems. Read only the task-relevant section; execution, publication, and repair require the user's explicit intent.

本专题汇总影刀工具与项目级操作，**不是普通代码开发任务的默认执行清单**。默认仅编写代码和静态检查；仅在用户明确要求查询影刀状态、运行、部署或操作 Studio 等具体事项时，按需进入「CLI 操作」「应用开发闭环」或「项目诊断」。Visual Flow 编辑及市场指令 / 项目 Python 包安装默认交由用户；职责边界以全局影刀开发规则为准。

新建或补全影刀编码版项目时，按需先阅读 [最小 base 项目骨架与验收说明](references/base-project-skeleton.md)。模板文件仍位于本 Skill 根目录的 `project-template/`，不使用参考文档替代真实项目文件。普通 CLI 账户 / 任务查询无需加载骨架说明。

## Studio 与 CLI 操作

影刀 6.4.14 中，CLI 负责打开应用、同步关闭、发布、版本与正式任务管理。当前 Studio 应用的识别、重载、保存和流程检查走新版 `xbot-bash`。需要直接操作编辑器时先读 [Studio 6.4.14 的命令与验证范围](references/studio-copilot.md)。普通源码、配置与业务分析直接在项目工作区完成。

### Executable

Prefer the stable launcher path:

`C:\Program Files\ShadowBot\shadowbot.shell-cli.exe`

Do not pin commands to versioned directories such as `shadowbot-6.x.x`; ShadowBot updates can change those folders.

### 按需检查与命令帮助

- CLI 连接或服务可用性不明时查 `system health`；涉及模式或任务状态时查 `system state`；需要当前账号身份时查 `auth current`。已掌握所需信息时不重复预检。
- 不熟悉命令或参数时，对目标子命令运行 `-h` 查看当前支持的用法；不要猜 ID、参数或执行顺序。

### Find ShadowBot apps/projects

已有可信项目路径或 App ID 时直接使用。需要发现时用 `console app` 搜索（自主开发应用为 `--app-type developed`，订阅应用为 `subscribed`）；以返回的 `appId` 为准，多条匹配时核对元数据，再根据当前子命令帮助查看详情或定位项目目录。

### Run and inspect tasks

**只有用户明确要求运行时才启动应用或任务。** 运行不是只读检查；不能为了查看配置、字段、凭证等就实际执行。运行前按需核实应用和输入参数，再使用 `console task run`；默认同步执行并输出日志，仅在业务明确需要时使用 `--async`。任务查询与停止按需使用 `console task status/history/logs/stop`，参数以当前帮助为准。

项目任务触发失败按全局影刀开发规则停止并报告，即使报错为每日额度耗尽。Windows 全局说明中的桌面备用运行只适用于允许桌面回退的任务。

### Studio operations

仅用户明确要求操作 Studio，或已明确授权部署且发布流程需要时才使用以下命令；不得为验证代码自行打开 Studio。这里的 Code Flow 登记不等于编辑 Visual Flow。

ShadowBot 6.3.22 已验证：`studio create` **新建**应用后同步关闭，且不返回 App ID；`studio open` **不带 `--app-id`** 时新建应用并保持 Studio 打开。要打开**已有应用**，在当前 PowerShell 进程设置 `SWITCH_STUDIO_MCP_CLI_SUPPORT=1`，通过 `studio open -h` 确认支持 `--app-id` 后执行 `studio open --app-id <uuid>`。不同版本先以当前 CLI 帮助为准，不要把不带 ID 的 `studio open` 误用为打开已有项目。

当前使用 `xbot-bash app info` 读取 `app.app_id`，核对它与目标项目 `package.json` 的 `uuid` 一致。若当前打开的是其它应用，停止并提示处理。`studio current get` 可用于读取 Studio 状态；在 6.4.14 上，旧的 `studio app get/reload` 会调用已返回 404 的旧接口。

### Runtime modes

The CLI supports `console` and `assistant` mode switching:

```powershell
& 'C:\Program Files\ShadowBot\shadowbot.shell-cli.exe' mode switch --to console
& 'C:\Program Files\ShadowBot\shadowbot.shell-cli.exe' mode switch --to assistant
```

Console-only operations can return `not_supported` in Assistant mode. Check `system state` before switching. Do not use `--force` to switch to Console while a task is running unless the user explicitly wants that interruption/risk.

### 低频配置、UI 与连接排错

涉及影刀配置、窗口 UI 操作或 CLI 本地 REST 连接异常时，按需阅读 [CLI 辅助命令与连接排错](references/cli-auxiliary-commands.md)。

### Safety and modification rules

- Use ordinary project workspace capabilities for source inspection, file operations, project-local commands, and temporary diagnostic or migration scripts. Use this CLI only when a ShadowBot-specific capability is actually needed.
- Treat `console app recycle`, permanent delete, publish, collaborator changes, `config set`, task stop, forced mode switches, and similar state-changing operations as explicit user-intent actions.
- Never invent an app UUID or silently pick the first search result when multiple apps match. Use names and returned metadata to disambiguate.
- Prefer CLI outputs as the source of truth for current ShadowBot app IDs, task state, account state, and supported command parameters.

## 应用开发闭环

**仅用户明确要求部署时执行本节发布流程。**普通开发任务写完代码、完成静态检查即交付，不因项目尚未发布而自行启动 Studio、登记 Flow、同步或运行任务。按需读取全局影刀开发规则与相关正式知识；CLI 操作按上方章节及本机帮助执行。新建应用及模板合并步骤见 [最小 base 项目骨架](references/base-project-skeleton.md)。

市场指令或依赖未安装时的编码与交付边界，遵守全局影刀开发规则中“xbot 与知识库”的规则；不将安装排查提前为编码前置步骤。

1. 用户说 **“push”** 时，Agent 正常调用 Git 完成 commit 和 push，不运行影刀部署。用户说 **“部署”** 或 **“push 并部署”** 时，在 PowerShell 中只执行一次 `python "$HOME/.agents/skills/shadowbot-development/scripts/deploy_app.py" --project-dir <项目目录> --commit-message "<提交说明>" --update-log "<发布说明>"`，由脚本自动完成必要的 Code Flow 元数据登记、Git 提交（无改动不产生空提交）和 push、Studio 重载/保存/同步、发布与线上版本校验；**不编辑 Visual Flow，不自动执行发布后的业务任务**。Agent 不再单独调用 Git、同步、发布和版本查询。
   **部署内容以当前项目工作区的完整代码状态为准。** 用户明确要求部署时，不因存在其他已完成但尚未提交的代码修改而自动 stash、隔离、恢复或拆分部署范围；这些已有修改允许随本次部署一起提交、push、同步和发布。只需避免把明显的临时文件、备份文件等无关新增文件纳入提交。
2. 新增根目录 `.py` 会自动纳入 Git；其余已有跟踪文件的修改自动提交。为了防止将备份、临时文件等误推送，**其它新增文件默认不提交**，需在同一次部署命令中通过可重复的 `--add <相对路径>` 明确纳入。请在部署结果中关注 `untracked_skipped`。`--commit-message` 可指定 Git 提交信息；不传时使用发布说明生成。
3. Git 为可选步骤：缺少 Git、仓库或远程仓库，以及 Git 操作失败时，记录 `git_error` 并继续部署；根据 `git_pushed` 和 `git_commit` 报告实际结果。影刀同步、发布或线上版本校验失败时返回 `status=failed` 与非零退出码；新版本成为线上版本并通过 `versionId` 校验后返回 `status=success`。若 Git 已推送但发布失败，必须报告部分完成，不能称为部署成功。
4. 仅保留 `deploy_app.py` 一个部署脚本。脚本先核对登录账号对应的开发目录、影刀任务状态和已打开应用的保存状态，再变更 Code Flow 或推送 Git。`_Release` 和其它副本不能用来发起部署。到发布阶段，经 `xbot-bash` 重核目标应用及保存状态、从磁盘重载并保存编译，再用 CLI 同步关闭、发布并核对线上版本 ID。
5. 脚本成功后 Agent **无需再次调用 `console app versions` 重复校验版本**；直接汇报版本和 Git 提交信息。线上 `versionId` 变化不等于已证明业务运行正确；只有用户明确要求实际运行时才再按任务状态与日志验收。
6. 未经发布运行验证，不得假定 Code flow 可以直接作为应用的 `startup`；历史实验和验证边界见 [应用生命周期特殊案例](references/app-lifecycle-cases.md)。整应用复制的已知限制也在该参考文档中。

## 项目诊断

排查应用文件损坏、Sigstore 校验失败、Flow 重名时，按需阅读 [项目诊断](references/project-diagnostics.md)。普通业务代码问题不触发该流程。
