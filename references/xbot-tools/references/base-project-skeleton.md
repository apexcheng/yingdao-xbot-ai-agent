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

## 新建应用与项目路径定位

新建应用前先按当前 CLI 帮助核对创建命令；`studio create` 与 `studio open` 的已知差异及打开已有应用的限制，见 [CLI 的 Studio 操作](../guide.md#studio-operations)，不要在这里另存一份版本规则。

创建后以唯一的临时应用名称按[应用与项目定位步骤](../guide.md#find-shadowbot-appsprojects)查找 App ID，具备对应的本机源码目录后再合并模板。

## 需要复制的文件

将 `project-template/` 中缺失的文件复制到已存在 `package.json` 的真实项目根目录。目标已有同名文件时，先保留原文件和用户改动，再按当前需求最小合并；不得整份覆盖已有 `run.py`、`config.py` 或 `.gitignore`。其中的 base 代码是：

- `run.py`：通过 `main(args)` 进入业务，按真实业务顺序编写主流程。
- `config.py`：集中定义当前项目实际需要的配置变量，业务模块直接导入所需值。
- `.gitignore`：按项目已有配置作最小合并。

在已有应用中，检查 Visual `main` 是否已调用 `run.py` 的 `main(args)`。空白应用复制文件或登记 Code Flow 后，还需要由用户在影刀 Studio 的 Visual `main` 中补上调用。已有调用时沿用。部署和单独 Git push 见 [应用开发闭环](../guide.md#应用开发闭环)。

模板不预设业务字段，也不创建影刀“运行应用时需要传入的参数”。配置归属、凭据管理及配置变更验收统一遵守 [编码标准的文件职责](../../code-quality/references/coding-style.md#2-文件职责)，不另设配置来源。

## Agent 实现规则

开发约束遵守[项目开发规则](../../../SKILL.md)，不在骨架文档重复规定。

## 最小验收

按实际改动做必要验证。涉及新增或删除 Code Flow 时确认注册一致，按需检查 Python 语法。新建应用另核对 `startup` 指向 Visual `main`，并从已有流程或用户的 Studio 核对确认调用已接通。未实际发布或运行的内容，不得宣称已通过对应验证。

**验收证据分级：** 语法与静态检查只证明代码形式、配置及注册核对结果；使用模拟 Page / 假 API 的离线测试只证明被模拟的逻辑；真实浏览器探测只证明当前网页交互和响应可用，**不能代替影刀 `xbot.web` 实机运行**；Studio / Console 中实际执行成功才可称影刀实机验收通过；发布后实际任务和数据写入经核验，才可称正式运行验收通过。报告必须注明已到达的级别和未验证的级别，不得用较低级别的结果代替较高级别。
