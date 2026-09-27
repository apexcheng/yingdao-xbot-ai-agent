---
name: xbot-app-lifecycle
description: Develop, publish, trial-run, and debug a ShadowBot xbot Code app with the CLI in a real project. Use for the full app workflow, not for a one-off CLI account or console command.
---

# 影刀编码版应用开发闭环

先读真实项目 `AGENTS.md`。项目结构和 API 事实按知识库 `llms.txt` 查找；CLI 命令、参数和登录恢复按 `.agents/skills/shadowbot-cli/SKILL.md` 执行，以本机帮助和实际返回为准。

1. 新建应用时，先核对 CLI 的 `studio create -h` / `studio open -h`。ShadowBot 6.3.22 实测中，`studio create` 创建并同步关闭应用，但返回结果不含应用 ID；随后用唯一临时应用名执行 `console app --search <name>` 可取得 `appId` / `versionId`。再用 `auth current` 返回的 `userId` 组合本机目录 `%LOCALAPPDATA%\ShadowBot\users\<userId>\apps\<appId>\xbot_robot`，并以该目录 `package.json.uuid == appId` 作为项目根确认，不凭应用名猜目录。
2. 重新打开已有应用与创建新应用必须分开。ShadowBot 6.3.22 实测需要在当前 PowerShell 进程设置 `SWITCH_STUDIO_MCP_CLI_SUPPORT=1` 后重新查看 `studio open -h`；此时帮助会正式列出 `--app-id`。使用 `studio open --app-id <uuid>` 可重新打开已有 developed app；不传 `--app-id` 的 `studio open` 仍是创建新应用。保存已有应用可用 `studio current save`，同步并关闭用 `studio current sync`。若先在项目目录外部修改了 `package.json` / Code flow，先执行 `studio app reload` 让 Studio 重新载入磁盘状态，再执行 `studio app save`（保存并编译），最后 `studio current sync`；本机实测直接对外部改动执行旧的 `studio current save` / `sync` 曾返回 `apiCode=4091, message=\"sync close canceled\"`。
3. 将模板中缺失的文件合并到真实项目，保留影刀生成的文件和已有业务改动。配置变量由 `config.py` 管理，默认不新增影刀运行输入参数；`run.py` 的 `main(args)` 是 Code 流入口，其他模块正常导入调用。新增或删除项目根目录的 `.py` 文件后，运行本 Skill 内置 helper：`python .agents/skills/xbot-app-lifecycle/scripts/sync_codeflows.py`。它只负责扫描顶层 Python 文件、同步 Code flow 注册和使用目标应用 Python 环境做编译检查；不是独立产品能力，也不代表 Studio 已保存、同步或运行成功。随后按第 2 条执行 `studio app reload → studio app save → studio current sync` 并检查实际结果。ShadowBot 6.3.22 实测 `studio flow create --kind code --name run` 返回 HTTP 400：`Invalid params ... $.flows is required.`；该错误只说明这条创建命令本次未成功，不据此判断 Code flow 不受支持。
4. 开发完成后记录原发布版本。涉及真实业务写入时先确认试运行的数据范围及重复运行影响。发布后用 CLI 试运行，保存任务 ID，并结合运行结果、状态与日志判断业务是否成功；默认不传运行输入参数。编译、保存、发布和实际运行分别验证。
5. 排错时在相关步骤临时加日志，不记录凭据或敏感数据；根据日志修复并重试。测试与验收后删除临时日志，重新保存 / 同步，**最后再次发布**，确认发布版本对应清理后的代码。
6. 只有隔离验证 Code 流可作为 `startup`，且 Studio 保存、同步、发布与 Console CLI 运行都成功，并能由任务状态 / 日志证明发布任务实际执行了 `run.py`，才把应用入口改为 `run.py`。需要证明服务器收到的 manifest 就是当前本地版本时，可对比 ShadowBot 主日志中的 `packageJsonMd5` 与本地 `package.json` 的 MD5。2026-09-27 在 ShadowBot 6.3.22 的隔离临时应用中，`run` Code flow 可在 Studio 内直接运行且日志出现探针，本地与上传的 `package.json` MD5 也一致；但即使 `package.json.startup=\"run\"`、`studio app reload`、`studio app save`、`studio current sync`、发布均成功，`console task run` 任务仍以 `completed` 结束且任务日志只出现“开始执行 / 执行结束”；将 `run.py` 改为抛出唯一异常后，发布任务仍未出现该异常。因此当前只记录“直接 Code startup 未通过本次发布运行验证”，不推断为产品不支持；此前继续保留 Visual 启动流，不单凭修改 `package.json` 宣称入口已经生效。
