# 影刀 Studio 6.4.14 的命令与验证范围

以下基于 Windows 客户端 6.4.14、2026-11-24 的本机检查。影刀运行时 Python API（如 `xbot.web`）仍以对应 API 事实页为准。

| 操作 | 当前入口 | 验证情况 |
| --- | --- | --- |
| 打开指定应用、同步关闭、发布、查询线上版本 | 官方 CLI | 已在本机完成一次真实发布并核对新版本上线 |
| 查询当前应用、从磁盘重载、保存编译 | `xbot-bash app info/reload/save` | 已在本机实测；重载会丢弃未保存编辑，开始前必须核对目标应用和未保存状态 |
| 应用名称、说明与设置 | `xbot-bash app update` | 本机帮助确认；社区实测了名称和说明修改 |
| 编码与可视化流程、流程参数 | `xbot-bash flow` | 帮助提供列出、创建、读写、编辑、复制、改名、删除和参数管理；社区实测了可视化子流程搭建和传参调用 |
| 静态检查和 Studio 调试 | `diagnostics snapshot`、`run start/wait/stop/logs/result/variables` | 帮助提供检查、调试、日志、结果与指令输入输出快照；社区实测了检查、运行、日志和结果 |
| 元素、资源、图片、全局变量、内置数据表和 Python 依赖 | `selector`、`resource`、`images/image`、`variable`、`datatable`、`python package` | 本机帮助确认。元素命令为列出、查询与删除；资源可列出、添加、改名与删除；图片可列出及查看；变量可列出、设置和删除；数据表可读和清空；Python 包可列出、安装和卸载 |
| API 与自定义指令 | `api get`、`custom` | 本机帮助确认精确 API 查询及自定义指令的搜索、详情、包、连接列表、参数解析和依赖准备 |
| 网页探索 | `execute_cell` | 本机工具清单确认有入口，网页操作未逐项实测，按项目现有浏览器规则使用 |

这些命令描述的是客户端能力。Visual Flow 编辑、依赖安装、元素库改动和实际执行仍遵循项目 `AGENTS.md` 的授权边界。正式任务、触发器、登录、账户和客户端配置走 CLI。

## 从 Windows DevSpace 查当前应用

`xbot-bash` 是 Studio 接口中的工具名。先用 CLI `system state` 确认编辑器已打开；用户指定已有应用且当前没有打开应用时，用 CLI `studio open --app-id <UUID>` 打开。只读查询可复用部署脚本中的客户端，从真实项目根目录运行：

```powershell
python -c "import json,runpy; studio=runpy.run_path('.agents/skills/xbot-tools/scripts/deploy_app.py')['StudioClient'](); print(json.dumps(studio.command('app info','查看当前应用'),ensure_ascii=False))"
```

把 `app info` 换成 `--help` 或对应子命令的 `--help` 可以读取本机命令说明。读取指定应用的信息时，核对返回的 `app.app_id`。有其它应用打开时，保留现场。

客户端根据当前 Windows 会话的 `%TEMP%\shadowbot.cli.<会话编号>.port` 读取本机端口，向 `127.0.0.1` 上的 `/api/v1/copilot-mcp/mcp` 发请求。6.4.14 本机验证旧 CLI 列出的 `/api/v1/mcp` 返回 404，新地址返回成功。升级后先核对实际运行版本和接口，用测试应用复验重载、保存、同步、发布及线上版本。CLI 帮助仍列出旧命令时，以实际调用为准。

- [影刀 6.4 官方更新说明](https://www.yingdao.com/community/detaildiscuss?id=1019415212110471168)
- [影刀 6.4.14 开发者社区实测记录](https://www.yingdao.com/community/detaildiscuss?id=1019898659614580736)
