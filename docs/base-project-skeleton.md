# 影刀编码版最小 base 骨架

本骨架用于新建或补全真实影刀 xbot 编码版项目。流程结构依据维护者提供的真实项目于 2026-09-01 核验。不记录本机用户 ID、应用 ID 和业务凭据。

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

- `run.py`：通过 `main(args)` 进入业务，按真实业务顺序编写主流程。
- `config.py`：集中定义当前项目实际需要的配置变量，业务模块直接导入所需值。
- `.agents/skills/xbot-app-lifecycle/scripts/sync_codeflows.py`：仅在新增 / 删除项目根目录 `.py` 时使用，用于同步 Code Flow 注册并编译当前项目 Python 文件；普通已有文件修改不需要执行。
- `.agents/skills/xbot-app-lifecycle/scripts/publish_app.py`：发布外部修改后的已有应用，统一执行打开应用、重新载入磁盘、保存编译、同步、发布和线上版本校验；不负责 Code Flow 注册。

模板不预设业务字段，也不创建影刀“运行应用时需要传入的参数”。在真实项目的 `config.py` 中按需求定义配置；凭据等敏感值从本地安全来源读取，不在 Git 中保存明文。需要交互式配置或加密持久化的项目，可按[增强工具2026](../xbot-api-docs/docs/extensions/xbot-enhance-tools.md)的已核验 API 单独实现。

## Agent 实现规则

入口、参数、敏感信息与同步遵守[项目开发规则](../project-template/AGENTS.md)；过程式主流程、`run.py / config.py / tool.py（或 utils.py）` 职责、变量内联和函数边界的详细判断见[编程风格详解](coding-style.md)。`main(args)` 是影刀调用 Code 流的入口约定；其他 Python 文件按正常 Python 语法导入和调用，无需都定义 `main(args)`。

涉及多个更新模块共同处理一份 Excel，优先参考[跨境补货表真实实现案例](../reference-projects/cross-border-replenishment/README.md)的固定业务编排、独立保存与失败隔离；仅需“整轮统一保存”的最小代码时再看 [多 Sheet 工作簿教学 Demo](examples/multi-sheet-workbook/README.md)。二者都不是要整体复制的项目模板；提交策略先根据实际业务在 [多数据源报表安全边界](multi-source-report-safety.md) 确认。

## 最小验收

1. 仅新增缺失文件；已有入口、配置与用户改动保留。按项目规则需要同步时，先备份 `package.json`，再确认新增 Code 流已登记；用户要求暂不同步时记录未执行。
2. 真实项目的配置变量已在 `config.py` 定义，业务模块只导入所需值；敏感值没有以明文提交。
3. 默认执行语法检查及与改动风险匹配的针对性验证；仅在用户明确要求时才发布或运行影刀应用。执行后须确认生效的是最终代码版本，主要业务路径符合当前需求。
