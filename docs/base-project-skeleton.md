# 影刀编码版最小 base 骨架

本骨架用于新建或补全真实影刀 xbot 编码版项目。流程结构和配置 API 依据维护者提供的真实项目于 2026-09-01 核验；项目内配置路径的运行验证边界见下文。不记录本机用户 ID、应用 ID 和业务凭据。

## 经过核验的结构

参考项目的 `package.json` 包含三个流程：

```text
main     Visual   项目启动流
run      Code     编码版业务入口
config   Code     配置路径
```

`startup` 指向 `main`。`main.pybx`、`package.json`、`package.py`、`selectorsV2.xml` 和 `imagesV2.xml` 由影刀维护，不从知识库模板覆盖。

## 需要复制的文件

将 `project-template/` 中缺失的文件复制到已存在 `package.json` 的真实项目根目录。目标已有同名文件时，先保留原文件和用户改动，再按当前需求最小合并；不得整份覆盖已有 `run.py`、`config.py`、`.gitignore` 或规则文件。其中的 base 代码是：

- `run.py`：通过 `main(args)` 进入业务，首次运行显示配置对话框。
- `config.py`：保存当前项目的加密配置路径；默认放在当前 Windows 用户目录下的 `.xbot/<项目功能名>/project_config.json`。
- `shadowbot_sync_tool.py`：登记和编译新增 Code 流。

`run.py` 依赖项目已安装“增强工具2026”市场指令，使用其公开 `market_config` 能力：

```text
load_secret_config()
→ 无配置时 show_custom_dialog()
→ dialog_result_to_dict()
→ 用户选择保存时 save_secret_config()
→ 进入业务流程
```

模板使用 `Path.home() / ".xbot" / "<项目功能名>" / "project_config.json"` 定位配置。复制到真实项目时，必须把 `<项目功能名>` 换成能直接识别当前项目用途的目录名，例如 `拼多多库存监控`；不要直接使用项目文件夹名、应用 ID 或所有项目共用的固定目录。不同项目功能使用不同目录，避免配置串用。新位置没有配置时，沿用初始化流程。

配置加密仍使用与当前 Windows 用户绑定的 DPAPI，更换用户或机器后不能直接复用配置。详细 API 事实见 [增强工具2026](../xbot-api-docs/docs/extensions/xbot-enhance-tools.md)。

## Agent 实现规则

入口、参数、敏感信息与同步遵守[项目开发规则](../project-template/AGENTS.md)；过程式主流程、`run.py / config.py / tool.py（或 utils.py）` 职责、变量内联和函数边界的详细判断见[编程风格详解](coding-style.md)。本模板只补充以下约定：

- `args` 是流程初始化参数字典，不等于 `package.variables`。
- 修改 `dialog_settings` 时，`VariableName` 是转换后的配置字段名，按钮结果从 `pressed_button` 读取。

## 最小验收

1. 仅新增缺失文件；已有入口、配置与用户改动保留。按项目规则需要同步时，先备份 `package.json`，再确认新增 Code 流已登记；用户要求暂不同步时记录未执行。
2. 在影刀 Code 流中确认配置实际位于当前 Windows 用户目录的 `.xbot/<项目功能名>/project_config.json`，且目录名能明确对应当前项目功能，不与其他项目共用。
3. 首次运行显示初始化对话框，取消时流程正常结束；保存后再次运行能加载本项目配置。
4. 同一 Windows 用户下两个项目互不串用配置。
