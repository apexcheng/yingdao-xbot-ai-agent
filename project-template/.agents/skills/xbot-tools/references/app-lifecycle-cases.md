# 影刀应用生命周期：低频验证记录

以下是特定版本与环境下的实测结论，供启动入口和整应用复制任务参考，不应当推断为所有影刀版本的固定行为。

## Code Flow 直接作为发布应用启动入口

只有隔离验证 Code 流可作为 `startup`，且 Studio 保存、同步、发布及 Console CLI 运行都成功，并由任务状态 / 日志确认发布任务实际执行了 `run.py`，才可把应用入口改为 `run.py`。仅修改 `package.json.startup` 或看到发布成功不等于业务流程已执行。

需要核对服务器是否收到当前本地 manifest 时，可比较 ShadowBot 主日志中的 `packageJsonMd5` 与本地 `package.json` 的 MD5。

2026-09-27 在 ShadowBot 6.3.22 隔离临时应用中的实验：

- `run` Code flow 可在 Studio 内直接运行，日志出现探针；本地与上传的 `package.json` MD5 也一致。
- 将 `package.json.startup="run"` 后，执行 `studio app reload`、`studio app save`、`studio current sync` 并发布，`console task run` 仍以 `completed` 结束，日志只出现“开始执行 / 执行结束”，没有 `run.py` 的探针。
- 把 `run.py` 改为抛出唯一异常后再次发布，任务日志仍未出现该异常。

本次**不能证明直接 Code startup 已正常工作**，但也不据此断定产品不支持。未完成新的发布运行验证之前，沿用已验证的 Visual 启动流。

## 复制整个应用的已知限制

复制应用前先核对当前 CLI 帮助。ShadowBot 6.3.22 实测没有可直接等价完成“复制整个 developed app”的应用级 copy / clone / duplicate 命令；`studio flow copy` 仅复制单个 Flow，不能替代复制整应用。

如果确需通过“新建应用 + 复制本地项目文件”制作副本，必须保留新应用自己的身份信息。直接复制或改写 `package.json` 可能导致 `package.sigstore` 校验失败或出现“应用文件已损坏”；遇到此类问题参见 [项目诊断与迁移](project-diagnostics.md)，不要靠反复运行应用排查。
