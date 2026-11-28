# 影刀 xbot AI Agent 开发指南

> 面向影刀 xbot / 编码版、RPA 自动化和 AI 编程 Agent 的中文开发知识库。

[![GitHub stars](https://img.shields.io/github/stars/apexcheng/yingdao-xbot-ai-agent?style=social)](https://github.com/apexcheng/yingdao-xbot-ai-agent/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/apexcheng/yingdao-xbot-ai-agent?style=social)](https://github.com/apexcheng/yingdao-xbot-ai-agent/network/members)
[![AI Agent](https://img.shields.io/badge/AI-Agent-blue)](AGENTS.md)
[![RPA](https://img.shields.io/badge/RPA-Automation-green)](xbot-api-docs/docs/browser.md)
[![xbot](https://img.shields.io/badge/xbot-Yingdao-orange)](llms.txt)

## 关于这个项目

这是我在实际开发和维护影刀自动化项目时，为个人 AI 辅助开发流程持续整理的知识库。它首先服务于我自己的项目，同时公开出来，希望给同样使用 Codex、Claude Code、Cursor 等工具开发影刀编码版的开发者一些参考。

本仓库不是影刀官方文档，也不追求覆盖所有 API。其中的内容主要来自个人项目中的真实调用、源码核验和可复现问题。开发时按正式事实页使用影刀 API 与市场指令；若项目安装版本缺少文档中的入口，请检查更新状态，并反馈尚未发布或文档需要修订的情况。

这个仓库解决的是“如何开发、维护和排查影刀项目”，不是“AI Agent 应该如何操作电脑或选择宿主工具”。用于访问 Windows / macOS、执行代码、连接设备或编排外部能力的 ChatGPT、Codex、Claude Code 等宿主侧插件、MCP、DevSpace、Computer Use 和工具路由不属于本项目维护范围；只有与影刀自身直接相关的 CLI、API、项目格式和运行机制属于本知识库。

## 为什么整理这个知识库

通用代码模型通常熟悉 Python、Selenium、Playwright、pandas 或 openpyxl，但并不天然了解影刀项目中的：

- xbot 对象、元素库、图像库和资源文件的真实用法。
- 浏览器、Excel / WPS、Windows 自动化之间的 API 边界。
- 市场指令在可视化界面和编码版中的参数映射。
- 影刀真实项目目录、`package.json` 和同步流程的关系。
- 哪些结论已验证，哪些仍需要在当前环境运行确认。

这个仓库的目标不是让 AI “记住更多文档”，而是让它在不确定时能找到正确入口，少猜 API，少复制过时经验。

## 仓库包含什么

### AI Agent 开发规则

- [AGENTS.md](AGENTS.md)：知识库自身的维护规则；真实项目的常驻开发规则见 [SKILL.md](SKILL.md)。
- [llms.txt](llms.txt)：给 AI Agent 使用的精简文档导航。
- [project-template](project-template/)：可按需合并到真实影刀项目的 `run.py`、`config.py` 和 `.gitignore`。

### 专项参考与完整开发经验

- [网页操作流程与 XPath 探测](references/web-workflow-extraction/guide.md)：复用已确认的定位并在需要时探测真实网页。

- [代码质量专题](references/code-quality/guide.md)：一致性、简化、审查。
- [影刀工具专题](references/xbot-tools/guide.md)：CLI、项目创建、同步、发布、项目诊断。
- [开发经验专题](references/rpa-practices/guide.md)：网页、钉钉通知、跨轮状态及通用排错。
- [功能模板索引](references/rpa-practices/references/feature-templates/README.md)提供站点登录、ntfy、下载等待、钉钉 Webhook 和常用原生写法。
- [表格操作专题](references/spreadsheet-operations/guide.md)：Excel/CSV 用 WPS 打开、更新、保存和关闭。

- [影刀编码版编程风格详解](references/code-quality/references/coding-style.md)
- [最小 base 骨架](references/xbot-tools/references/base-project-skeleton.md)
- [网页自动化实践](references/rpa-practices/references/web.md)
- [钉钉通知实践](references/rpa-practices/references/dingtalk.md)
- [项目参考案例库](reference-projects/README.md)：抖音经营报表和库存监控的本地冻结源码案例。
- [抖音经营报表真实案例（内置源码快照）](reference-projects/douyin-operating-report/README.md)
- [影刀编码版通用排错](references/rpa-practices/references/troubleshooting.md)

### xbot API 与自动化文档

- [基础对象、元素库与资源](xbot-api-docs/docs/package.md)
- [浏览器与网页元素](xbot-api-docs/docs/browser.md)
- [Excel / WPS 工作簿与数据读写](xbot-api-docs/docs/excel.md)
- [Windows 窗口、键盘与鼠标](xbot-api-docs/docs/win32.md)
- [影刀日志](xbot-api-docs/docs/logging.md)
- [通知与对话框](xbot-api-docs/docs/notification.md)
- [压缩与解压](xbot-api-docs/docs/xzip.md)
- [iframe2 扩展](xbot-api-docs/docs/iframe2-extension.md)

### 市场指令事实

[市场指令索引](xbot-api-docs/docs/extension-instructions.md) 用于查找各指令的正式调用事实页，目前包括：

- 钉钉 AI 表格。
- Excel 扩展操作、离线 OCR、广告处理和网页增强。
- C-ERP 开发项目内 Python 报表下载模块、ERP 订单查询与字段翻译。
- 登录扩展、iframe 和其他已核验扩展能力。

## 快速开始

### 安装与更新

在 Windows PowerShell 将这个独立 Git 仓库直接克隆到共享 Skill 目录：

```powershell
git clone https://github.com/apexcheng/yingdao-xbot-ai-agent.git "$HOME/.agents/skills/shadowbot-development"
```

更新时在同一个仓库执行 `git pull --ff-only`。Windows DevSpace 和本机 Codex 都从共享目录发现 [shadowbot-development](SKILL.md)。打开任意工作区后，说明影刀应用名称、App ID 或已知项目路径即可。需要修改业务代码时，先定位到有 `package.json` 的真实影刀目录。知识库自己的 [AGENTS.md](AGENTS.md) 用于维护本仓库。

新应用按 [base 骨架](references/xbot-tools/references/base-project-skeleton.md) 合并缺失的模板文件，已有同名文件按需最小合并。公共开发规则、专题正文和部署脚本都从本 Skill 读取。项目的 PRD、运行交接和业务配置仍随项目维护。

### 查找知识与使用工具

旧项目或历史交接文档里的入口可按下表定位。右列路径相对于全局 Skill 根目录。

| 旧入口 | 全局位置或用途 |
| --- | --- |
| 项目根 `AGENTS.md` 的公共开发规则 | [SKILL.md](SKILL.md) |
| 项目 `.agents/skills/<专题>/SKILL.md` | `references/<专题>/guide.md`，原专项资料仍在同专题的 `references/` 下 |
| 项目 `.agents/skills/xbot-tools/scripts/` | [scripts/](scripts/)，运行时指定真实项目目录 |
| 知识库的 API、完整案例 | [xbot-api-docs/docs/](xbot-api-docs/docs/) 和 [reference-projects/](reference-projects/) |
| 模板中的 QMD 与 Codex 配置 | [integrations/](integrations/) 中保留可选接入样例 |
| 跨项目规则同步脚本 | 更新这个独立仓库，各工作区从同一份 Skill 读取 |

[核心开发规则](SKILL.md) 与 [任务导航](llms.txt) 提供直达入口。也可在全局 Skill 根目录使用 QMD，首次安装或知识更新后执行 `qmd update`，再运行 `qmd search "Sigstore" -c yingdao-skills --full-path`。可选 QMD 接入样例和已有只读审查角色配置见 `integrations/`，使用样例时按实际安装位置设置路径。

影刀官方 CLI 的账户、控制台及任务查询由独立 `shadowbot-cli` 提供。[影刀工具指南](references/xbot-tools/guide.md) 记录 Studio 的版本差异、项目定位、诊断和部署。单独 “push” 时只提交推送 Git；要求影刀部署时，从全局脚本传入真实项目路径，单次完成 Git、必要的 Code Flow 登记、Studio 同步、发布及线上版本核验。

## 开发与维护风格

这是一个个人持续维护的实用型知识库，优先保留长期、稳定、能反复帮助真实项目的内容：

- 业务流程优先直接、可读，不追求复杂架构。
- API 结论需要有当前版本源码、真实调用或可追溯代码作为依据。
- 项目专用的页面字段、业务口径和临时 workaround 不上升为公共规则。
- 文档尽量链接到唯一事实页，不为了“看起来完整”重复同一段内容。

如果你发现文档与当前版本不一致，欢迎提交 Issue 或 Pull Request。贡献前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，并确保账号、Token、Webhook、客户数据和本机路径已脱敏。

## 目录结构

```text
SKILL.md                     # Windows DevSpace / Codex 共享的影刀开发入口
AGENTS.md                    # 知识库维护规则
llms.txt                     # AI / LLM 文档索引
README.md                    # 项目介绍与使用入口
CONTRIBUTING.md              # 事实证据、内容边界与脱敏规则
project-template/            # run.py、config.py、.gitignore
references/                  # 五个按需读取的专题，各自从 guide.md 进入
  code-quality/              # 代码规范、简化与审查
  xbot-tools/                # CLI、应用生命周期、诊断、项目骨架
  rpa-practices/             # Web、日志、钉钉、跨轮状态、排错与功能模板
  spreadsheet-operations/    # 影刀运行时 WPS 表格操作
  web-workflow-extraction/   # 网页流程与 XPath 探测
scripts/                     # 部署、Sigstore 诊断与 QMD 入口
integrations/                # 可选工具配置示例
reference-projects/          # 真实项目参考案例：固定 Git commit 或脱敏冻结源码
xbot-api-docs/
  AGENTS.md                  # API 文档维护边界
  docs/                      # xbot API 和市场指令事实页
```

## 搜索关键词

影刀、影刀编码版、影刀 xbot、影刀 API、影刀 RPA、浏览器自动化、Excel 自动化、WPS 自动化、Windows 自动化、钉钉 AI 表格、市场指令、AI Agent、Codex、Claude Code、Cursor、Yingdao、xbot API、RPA automation、Python automation。

## 联系作者

如果你在使用过程中遇到问题，或有影刀 RPA、AI 编码相关的交流需求：

- QQ：`1677880403`
- 邮箱：`apexc@qq.com`
- 技术问题 / Bug：请优先提交 GitHub Issue

## 许可证

本项目采用 [MIT License](LICENSE)。
