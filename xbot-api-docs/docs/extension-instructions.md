# 影刀市场指令索引

本页导航到各市场指令的正式事实页。日常开发直接按事实页使用入口、参数和返回值；本页的安装检查只用于处理版本不匹配。

## 日常使用顺序

1. 从知识库 `llms.txt` 定位本页，再打开下方对应指令的正式事实页。
2. 按事实页给出的公开入口、参数、返回值和适用条件编写调用；无需每次读取项目的 `xbot_extensions` 安装副本。
3. 知识页缺少所需事实时说明缺口，不猜测，也不自动转查源码。项目报缺少模块或入口时，提示检查、更新或重新安装对应指令；如果市场尚无包含该能力的版本，说明发布缺口。

## 调查版本差异或维护事实页

仅当用户要求调查版本差异、维护文档，或升级后仍异常时，按任务范围核对实际安装情况：

1. `package.json` 的 `flows` 确认 `filename`、`kind` 和流程名。
2. `prototype.block.json` 只查看 `hidden=false` 的公开 block；`inputs[].name` 是编码参数名，`outputs[].name` 是输出名。
3. Visual 流程查看 `__init__.py` 的公开包装函数，确认实际参数和输出。
4. Code 流程查看 `filename.py` 的 `main(args)`；这里的 `args` 是流程初始化参数字典，不等同于 `package.variables`。
5. Direct Python 入口直接查看被导入模块的公开函数，并用 `inspect.signature()` 核对当前版本。

```text
Visual:
package.json → prototype.block.json → __init__.py 包装函数 → xbot_visual.process.run()

Code:
package.json → prototype.block.json → filename.py 的 main(args)

Direct Python:
直接 import 公开模块或函数，不经过 xbot_visual.process.run()
```

界面中文标签、默认显示值和其他扩展的返回结构，都不能代替上述证据。找不到明确依据时不要写成稳定事实。

### 需要核验公开签名时

仅检查当前安装版本的公开模块和公开函数：

```text
非执行调用说明（不可直接运行）：

import inspect
from xbot_extensions import your_extension_module

print(inspect.getfile(your_extension_module))
print(inspect.signature(your_extension_module.some_function))
```

`inspect.getfile()` 用于定位当前应用实际安装的扩展，`inspect.signature()` 用于调查其公开入口参数。核验结果用于修正文档或确认版本差异，不要求每个业务项目重复此步骤。业务代码不应直接导入 `_core` 等私有入口，知识库也不复制扩展内部源码。

## 项目内 `xbot_extensions` 只是安装副本

真实影刀应用目录中的 `xbot_extensions/<市场指令目录>` 是该应用从市场安装 / 拉取后的**项目副本**，可能落后于正式事实页所描述的能力。日常用法以事实页为准；仅在调查版本差异时查看这个副本。

如果需要给市场指令新增能力、修复实现或发布给其它机器使用：

1. 先找到该市场指令对应的真实开发项目 / 源仓库，在那里修改并发布。
2. 目标影刀应用再通过正常的市场指令安装、更新或重新拉取流程取得新版本。
3. 不要只修改某个业务项目下的 `xbot_extensions/<市场指令目录>` 并认为改动已经进入市场指令；这种本地副本修改不会自动传播到其它机器，应用重新拉取市场指令时也可能被覆盖。

调查升级后仍存在的版本异常时，可以读取项目内 `xbot_extensions` 作为安装状态证据；开发市场指令本身时必须回到其真实项目目录。不要直接修改已安装的市场指令副本。

## 指令事实页

| 指令目录 | 主要调用类型 | 事实页 |
|---|---|---|
| `activity_47680f64` | Visual / Code | [小工具指令集](extensions/activity-47680f64.md) |
| `activity_5b77c4ce` | Direct Python | [钉钉 AI 表格](extensions/activity-5b77c4ce.md) |
| `activity_7bca6d` | Visual / Code | [登录扩展操作](extensions/activity-7bca6d.md) |
| `guanyi_erp_api` | Direct Python | [C-ERP API](extensions/guanyi-erp-api.md) |
| `activity_a90a8311` | Code（项目内模块） | [C-ERP 报表下载 Python 版](extensions/c-erp-python.md) |
| `activity_df0688e4` | Direct Python | [ERP 订单详情与字段翻译](extensions/activity-df0688e4.md) |
| `activity_179ea575` | Flow | [离线 OCR](extensions/activity-179ea575.md) |
| `iframe2` | Visual / Direct Python | [iframe2](iframe2-extension.md) |
| `ad_killer` | Visual / Direct Python | [广告杀手](extensions/ad-killer.md) |
| `web_action` | Visual / Direct Python | [网页扩展操作](extensions/web-action.md) |
| `xbot_enhance_tools` | Direct Python | [增强工具 2026（含钉钉机器人）](extensions/xbot-enhance-tools.md) |
| `activity_excel_v2` | Flow | [Excel 扩展操作](extensions/activity-excel-v2.md) |

## 相近能力如何选

- 普通网页打开、元素查找、点击、输入、Cookie、下载和网络监听先用原生 [`xbot.web`](browser.md)；只有目标能力属于扩展特性时，再进入 `web_action`、`iframe2` 或增强工具事实页。
- `iframe2` 是市场指令「XPath跨域获取网页元素」，不是原生 `xbot.web` 的 iframe API。原生源码中的 `is_cross_frame_element` 属于内部 selector 辅助能力，不能当作公开调用入口；跨 iframe XPath 操作按 [`iframe2`](iframe2-extension.md) 正式事实页处理。
- `activity_7bca6d` 是完整登录扩展，包含多平台 Visual 登录、验证码和滑块等入口；`xbot_enhance_tools.shop_utils` 是轻量商家后台登录辅助，是否适用以其 [事实页](extensions/xbot-enhance-tools.md) 的能力边界为准，不要把两者当成同一套登录 API。
- `guanyi_erp_api` 面向 C-ERP Direct Python 查询；`activity_a90a8311` 面向 ERP 初始化和报表下载，以项目内 Code flow Python 模块实现（项目内模块导入或 Studio 执行 Code flow）。需要查询接口数据时看 [C-ERP API](extensions/guanyi-erp-api.md)，需要下载 ERP 报表时看 [C-ERP 报表下载 Python 版](extensions/c-erp-python.md)。
- 普通工作簿、Sheet、区域读写和格式先查原生 [`xbot.excel`](excel.md)；只有原生能力不足、且项目已安装 Excel 扩展操作时，再查 [`activity_excel_v2`](extensions/activity-excel-v2.md)。

正式事实页仍缺参数，或升级后可视化可运行但编码版失败时，按本页的调查方法核验当前安装版本并补充事实页。
