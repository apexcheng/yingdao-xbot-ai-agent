# xbot 项目诊断与迁移

本文处理普通业务代码之外的**项目级问题**。当前包含两条工作流：

1. 旧版可视化项目解析 / 迁移。
2. 影刀应用“应用文件已损坏”等项目完整性问题排查与修复。

先根据用户症状选择对应工作流，不把两套步骤机械地全部执行。普通 Python 业务 bug、网页元素问题、Excel / WPS 问题仍按项目 `AGENTS.md` 和知识库对应事实页处理。

### 工作流 A：可视化项目解析与迁移

#### 1. 先做只读项目盘点

直接读取真实项目的 `package.json`、相关 Code flow 源码以及资源清单，**只读核对结构元数据**；不要输出 `package.json` 中的变量值，也不尝试解码 `.pybx`。根据文件确认：

- `startup` 和所有 flow 的 `name` / `filename` / `kind` / `groupName`。
- Visual flow 对应 `.pybx`、Code flow 对应 `.py` 是否实际存在。
- Code flow 的公开函数、参数和 import 关系。
- 全局变量名称、元素库和图像库条目数。

#### 2. 证据顺序

1. `package.json`：启动流、flow 类型和文件映射。
2. Code flow `.py`：`main(args)`、公开函数、参数与调用边界。
3. `selectorsV2.xml` / `imagesV2.xml` / `package.py`：资源名称和对象来源。
4. Visual flow `.pybx`：影刀维护的二进制流程文件，不把它当文本、JSON 或 Python 猜内部步骤。
5. 需要步骤级逻辑时，使用当前环境可用的影刀 Studio、截图或可读导出作为证据；先从已安装工具的 help 发现真实命令，不编造命令、标志或流程 ID。

无法确认 Visual flow 内部步骤时，明确标记“未确认”，不要根据流程名补全业务逻辑。

#### 3. 迁移到编码版

迁移前先整理每个待迁移流程的真实业务顺序、输入输出、分支 / 循环、异常路径、页面定位、全局变量、元素 / 图像资源和市场指令调用。只迁移已有证据确认的行为。

迁移时：

- 保留用户已确认的 XPath、字段名、参数名、按钮文案和业务口径，不顺带重写业务。
- 主流程按真实业务顺序自上而下展开，遵守项目 `AGENTS.md` 的代码结构规则。
- 一次迁移一个可验证的业务边界；不要先删除原 Visual flow 再尝试复原。
- 新增 `.py` flow 后按项目同步规则更新 `package.json` 并编译；资源仍被使用时不要删除元素库、图像库或全局变量。

迁移完成至少验证：新 Code flow 已登记、Python 编译通过、必要的影刀同步完成、关键业务路径与旧流程证据一致。没有实际运行过的步骤不得写成“已验证运行”。

### 工作流 B：应用文件损坏排查

典型界面提示：

```text
加载失败
应用文件已损坏，是否获取云端备份为副本？
```

不要只根据这个弹窗猜 Python 代码坏了。**先看影刀日志，确认失败层级。**

#### 1. 先查真实错误

优先读取失败时间附近的影刀日志：

```text
%LOCALAPPDATA%\ShadowBot\log\YYYYMMDD.log
```

按当前应用 UUID 和以下关键词缩小范围：

```text
OpenStudio
PackageUnreadableException
[Sigstore]
package sigstore check failed
```

如果日志明确出现：

```text
[Sigstore] package sigstore check failed
ShadowBot.Common.PackageUnreadableException: 应用文件已损坏
```

则当前已确认的是**项目完整性签名校验失败**，不是 Python 语法错误的同义词。

#### 2. Sigstore 修复顺序

`package.sigstore` 与影刀项目文件内容有关。外部工具修改 `run.py`、其他 flow、`package.json` 等文件后，如果没有由影刀重新生成签名，就可能出现 Studio 拒绝打开。

修复时严格按这个顺序：

1. 确认影刀当前没有正在运行该应用，也没有打开该项目 Studio。
2. 保留现场；不要先删除 `package.sigstore`。
3. 先核对 Code flow 注册与实际文件是否一致；仅在项目根目录新增 / 删除了 `.py` 文件、需要同步注册时，按 [应用开发闭环](../SKILL.md#应用开发闭环) 规则执行 `python .agents/skills/xbot-tools/scripts/sync_codeflows.py`。只修改已有文件或仅排查签名时不运行同步 helper；如需检查 Python 语法则单独检查，不为此改写 flow 注册。
4. 先只校验，不写入：

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/xbot-tools/scripts/repair_package_sigstore.ps1 -ProjectRoot .
```

5. 只有输出 `before=False` 且用户要求修复时，才重新生成签名：

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/xbot-tools/scripts/repair_package_sigstore.ps1 -ProjectRoot . -Write
```

6. 必须看到 `after=True` 才能把 Sigstore 修复标记为成功，然后重新打开 Studio 验证。

脚本调用**本机已安装影刀 Runtime 自己的 `PackageHelper.TestPackageSigstore()` / `WritePackageSigstore()`**，并在写入前把旧 `package.sigstore` 备份到项目 `.dev/repair-backups/`。它不是手工计算或伪造签名。

#### 3. 不要把所有“损坏”都归因于 Sigstore

如果日志没有 Sigstore 失败，或者校验结果已经是 `before=True`，不要重签名碰运气。继续按日志证据检查：

- `package.json` 是否可解析，`startup` 是否对应真实 flow。
- `package.json` 中 Visual / Code flow 是否存在对应 `.pybx` / `.py` 文件。
- package version / feature 是否被当前影刀版本支持。
- 元素库、图像库或其他项目资源是否缺失或格式损坏。

flow / 文件映射异常时，直接对照 `package.json` 中的 flow 注册、实际 `.py` / `.pybx` 文件与启动流，不需要另行执行项目结构扫描脚本。

如果修了 `package.json`、flow 文件或其他参与完整性校验的项目文件，**最后再重新做 Sigstore 校验 / 写入**；不要先重签名、再继续改文件，否则签名会再次失效。

#### 4. flow 重名导致的假“损坏”

日志没有 Sigstore 失败、校验 `before=True`，但出现以下错误时，是流程重名，不是签名问题（运行验证：影刀 Studio，2026-10）：

```text
Failed to load app
System.ArgumentException: An item with the same key has already been added. Key: <活动代码>.<流程名>
   at ShadowBot.Runtime.Development.FlowCollection..ctor(...)
```

Studio 按 `<活动代码>.<流程名>` 建 flow 字典，`package.json` 的 `flows` 中只要有两个同名 flow，加载即崩溃，界面就弹“应用文件已损坏”。常见来源：`sync_codeflows.py` 登记新 `.py` 时 flow 名 = 文件名去扩展名，与已有 Visual flow 名撞车，例如项目已有名为 `init` 的 Visual flow 时新建了 `init.py`。

指令项目（`robot_type: "activity"`）还要同时检查 `prototype.block.json`：其 `blocks[].name` 同样是 `<活动代码>.<流程名>`、`function` 指向流程文件名；影刀打开项目时只重写 `package.json`，不会自动修复重复的 block。

修复顺序：

1. `git mv` 重命名撞名的 `.py`（不要改 Visual flow 的名字），并更新引用它的 import。
2. 运行 `sync_codeflows.py`，让 `package.json` 移除旧注册、登记新文件名。
3. 把 `prototype.block.json` 中对应 block 的 `name`、`function`、`title` 一并改为新名。
4. 最后做 Sigstore 只读校验；`before=True` 则无需重签。
5. 重新打开 Studio 验证日志中不再出现 `Failed to load app`。

预防：新增项目根目录 `.py` 前，先确认文件名去扩展名后不与 `package.json` 中任何已有 flow 的 `name` 重复；不要新建 `init.py` 这类与既有 Visual flow 名相同的文件。

### 安全与输出

- 排查默认先只读。只有用户明确要求修复 / 迁移时才修改项目文件。
- 不泄露账号、密码、Token、Cookie、Webhook、客户数据或 `package.json` 的变量值。
- 不把“Python 编译通过”“Sigstore 校验通过”“Studio 可以打开”“业务实际运行成功”混成同一个验证等级。
- 汇报时区分：已确认根因、实际修改、实际验证、仍未验证的部分。
