# 影刀市场指令索引

本页只说明如何确认市场指令的编码入口，并导航到各指令事实页。参数、返回值和示例不在这里重复维护。

## 如何确认调用入口

以真实项目当前安装的扩展版本为准，按以下顺序核对：

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

### 参数不明确时

只检查当前安装版本的公开模块和公开函数：

```text
非执行调用说明（不可直接运行）：

import inspect
from xbot_extensions import your_extension_module

print(inspect.getfile(your_extension_module))
print(inspect.signature(your_extension_module.some_function))
```

`inspect.getfile()` 用于定位当前应用实际安装的扩展，`inspect.signature()` 用于确认公开入口参数。如公开入口只是转发层，再对照 `package.json`、`prototype.block.json`、包装函数和真实实现确认默认值、枚举和返回结构。业务代码不应直接导入 `_core` 等私有入口，知识库也不复制扩展内部源码。

## 指令事实页

| 指令目录 | 主要调用类型 | 事实页 |
|---|---|---|
| `activity_47680f64` | Visual / Code | [小工具指令集](extensions/activity-47680f64.md) |
| `activity_5b77c4ce` | Direct Python | [钉钉 AI 表格](extensions/activity-5b77c4ce.md) |
| `dingtalk_bot_message` | Direct Python | [钉钉企业机器人消息](extensions/dingtalk-bot-message.md) |
| `activity_7bca6d` | Visual / Code | [登录扩展操作](extensions/activity-7bca6d.md) |
| `guanyi_erp_api` | Direct Python | [C-ERP API](extensions/guanyi-erp-api.md) |
| `activity_a90a8311` | Flow | [C-ERP 市场指令](extensions/activity-a90a8311-cerp-visual.md) |
| `activity_df0688e4` | Direct Python | [ERP 订单详情与字段翻译](extensions/activity-df0688e4.md) |
| `activity_179ea575` | Flow | [离线 OCR](extensions/activity-179ea575.md) |
| `iframe2` | Visual / Direct Python | [iframe2](iframe2-extension.md) |
| `ad_killer` | Visual / Direct Python | [广告杀手](extensions/ad-killer.md) |
| `web_action` | Visual / Direct Python | [网页扩展操作](extensions/web-action.md) |
| `xbot_enhance_tools` | Direct Python | [增强工具 2026](extensions/xbot-enhance-tools.md) |
| `activity_excel_v2` | Flow | [Excel 扩展操作](extensions/activity-excel-v2.md) |

## 相近能力如何选

- 普通网页打开、元素查找、点击、输入、Cookie、下载和网络监听先用原生 [`xbot.web`](browser.md)；只有目标能力属于扩展特性时，再进入 `web_action`、`iframe2` 或增强工具事实页。
- `iframe2` 是市场指令「XPath跨域获取网页元素」，不是原生 `xbot.web` 的 iframe API。原生源码中的 `is_cross_frame_element` 属于内部 selector 辅助能力，不能当作公开调用入口；跨 iframe XPath 操作按 [`iframe2`](iframe2-extension.md) 的当前安装版本事实页处理。
- `activity_7bca6d` 是完整登录扩展，包含多平台 Visual 登录、验证码和滑块等入口；`xbot_enhance_tools.shop_utils` 是轻量商家后台登录辅助，是否适用以其 [事实页](extensions/xbot-enhance-tools.md) 的能力边界为准，不要把两者当成同一套登录 API。
- `guanyi_erp_api` 面向 C-ERP Direct Python 查询；`activity_a90a8311` 面向 ERP 初始化和报表下载等 Flow 能力。需要查询接口数据时看 [C-ERP API](extensions/guanyi-erp-api.md)，需要下载 ERP 报表时看 [C-ERP 市场指令](extensions/activity-a90a8311-cerp-visual.md)。
- 普通工作簿、Sheet、区域读写和格式先查原生 [`xbot.excel`](excel.md)；只有原生能力不足、且项目已安装 Excel 扩展操作时，再查 [`activity_excel_v2`](extensions/activity-excel-v2.md)。

参数不明确、可视化可运行但编码版失败时，按本页的入口与签名核验方法检查当前安装版本。
