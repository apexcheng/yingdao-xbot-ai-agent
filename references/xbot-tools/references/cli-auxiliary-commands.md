# ShadowBot CLI 辅助命令与连接排错

仅在调整影刀配置、操作影刀窗口或排查 CLI 本地 REST 连接异常时读取；常规项目源码分析无需执行这些命令。命令参数以本机 `-h` 帮助为准。

## 配置

按需求使用：

```text
config list
config describe --key <key>
config get --key <key>
config set --key <key> --value <value>
```

`config set` 会修改影刀设置，只有用户明确要求时才执行。有的设置变更需重启 ShadowBot 才生效，修改后按实际需求验证。

## 影刀窗口 UI

通过 `ui --exec <action>` 执行，先运行 `ui -h` 确认当前支持的动作。已核验的动作类别包括 Studio / Console 窗口最小化、最大化，以及切换计划 / 助手 / 控制台界面；具体动作名称以本机帮助为准。

## CLI 本地 REST 连接异常

只有命令因本地 REST API 不可用而失败时，才按需检查 `system health`、ShadowBot 进程与运行状态、认证状态，然后判断是否需要其它方法。不要把这些检查变成每次 CLI 操作的固定前置步骤，也不要未经用户允许启动影刀主程序。
