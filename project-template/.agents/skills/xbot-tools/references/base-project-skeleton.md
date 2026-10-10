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

新建应用前先按当前 CLI 帮助核对创建命令；`studio create` 与 `studio open` 的已知差异及打开已有应用的限制，见 [CLI 的 Studio 操作](../SKILL.md#studio-operations)，不要在这里另存一份版本规则。

创建后以唯一的临时应用名称执行 `console app --search <name>`，取得 `appId` / `versionId`；通过 `auth current` 获取 `userId`，定位 `%LOCALAPPDATA%\ShadowBot\users\<userId>\apps\<appId>\xbot_robot`。核对该目录 `package.json.uuid == appId` 后才认定为项目根，不仅凭应用名称猜目录。

## 需要复制的文件

将 `project-template/` 中缺失的文件复制到已存在 `package.json` 的真实项目根目录。目标已有同名文件时，先保留原文件和用户改动，再按当前需求最小合并；不得整份覆盖已有 `run.py`、`config.py`、`.gitignore` 或规则文件。其中的 base 代码是：

- `run.py`：通过 `main(args)` 进入业务，按真实业务顺序编写主流程。
- `config.py`：集中定义当前项目实际需要的配置变量，业务模块直接导入所需值。
- `.agents/skills/xbot-tools/scripts/sync_codeflows.py`：仅在新增 / 删除项目根目录 `.py` 时使用，用于同步 Code Flow 注册并编译当前项目 Python 文件；普通已有文件修改不需要执行。
- `.agents/skills/xbot-tools/scripts/publish_app.py`：发布外部修改后的已有应用，统一执行打开应用、重新载入磁盘、保存编译、同步、发布和线上版本校验；不负责 Code Flow 注册。

模板不预设业务字段，也不创建影刀“运行应用时需要传入的参数”。在真实项目的 `config.py` 中按需求定义配置；凭据等敏感值从本地安全来源读取，不在 Git 中保存明文。

## Agent 实现规则

开发约束遵守[项目开发规则](../../../../AGENTS.md)，不在骨架文档重复规定。

## 最小验收

按实际改动做必要验证：涉及新增或删除 Code Flow 时确认注册一致，按需检查 Python 语法。未实际发布或运行的内容，不得宣称已通过对应验证。
