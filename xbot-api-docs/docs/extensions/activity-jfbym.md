# 云码验证码识别 (activity_jfbym)

> 调用类型：`Direct`  
> 主要入口：Code 型直接调用各验证码模块的 `main(args)`；本页核验 `std_alphanum_captcha`（通用数英）和 `std_slider_captcha`（通用单图滑块）。
> 证据边界：数英参数按 2026-10 安装版本 26.5.0 源码确认；滑块参数按 **26.10.9** 安装源码及真实 RPA 项目集成代码确认。数英 `captcha_type` 编号来自稳定项目调用，未逐一实机验证；滑块识别**尚未在对应项目真实验证码现场验收通过**。
> 返回：[市场指令索引](../extension-instructions.md)

---

**目录/指令名：** `activity_jfbym` / 云码验证码识别（jfbym）

**调用方式：** Direct Python

**用途：** 对网页验证码元素截图后调用识别服务；数英入口写回文本，滑块入口识别距离并尝试拖动。扩展还包含点选、九宫格等模块，但本页未核验其接口。

**调用入口：**
- Direct：`std_alphanum_captcha.main(args)`（通用数英验证码识别）
- Direct：`std_slider_captcha.main(args)`（通用单图滑块识别与拖动）

**args 参数：**

| 键 | 类型 | 含义 |
|---|---|---|
| `web_page` | 网页对象 | 验证码所在页面 |
| `ele` | 元素库元素 | 验证码图片元素；传 `package.selector("元素名")`，内部通过 `web_page.find()` 定位 |
| `token` | str | 云码 code；**留空时自动改用影刀免费识别** |
| `captcha_type` | str | 验证码类型编号，见下表 |
| `is_trim` | bool | 可选；`True` 时要求识别结果区分大小写 |
| `timeout` | int | 可选；识别请求超时秒数，默认 20 |

**返回值：** 函数无返回值；识别结果写回 `args["data"]`。

**captcha_type 速查（稳定项目使用，未逐一运行验证）：**

| 显示名 | captcha_type |
|---|---:|
| 通用数英（≤5位） | `10110` |
| 通用数英plus（≤5位） | `10103` |
| 通用数英plus（≤6位） | `10104` |
| 通用数英5-8位 | `10111` |
| 通用数英9~11位 | `10112` |
| 数英定制4 | `15294` |
| 通用数英12位及以上 | `10113` |

**典型调用方式：**
```text
非执行调用说明（不可直接运行）：

from xbot_extensions.activity_jfbym import std_alphanum_captcha

args = {
    "web_page": page,                     # 前置：已打开验证码所在页面
    "ele": package.selector("验证码图片"),  # 必须是元素库元素，见注意事项
    "token": "<token>",                   # 云码 code；留空走影刀免费识别
    "captcha_type": "10110",
}
std_alphanum_captcha.main(args=args)
code = args.get("data")
```

**注意事项：**
- `ele` 不能传裸 XPath 字符串或 `find_by_xpath` 得到的元素对象：原生 `web_page.find()` 只支持元素名（`str`）与 `Selector` 对象（参数契约见 [browser.md](../browser.md)）。真实项目中曾因该限制必须改用元素库元素。
- 识别原理是对 `ele` 元素整体截图后送云端识别，元素库选择器应对准验证码图片本身。
- 各验证码入口参数结构不通用，滑块见下节；点选、九宫格等其他模块尚未核验，不要套用数英入口的 `args`。

## 通用单图滑块：`std_slider_captcha`

已安装 **activity_jfbym 26.10.9** 源码核对：入口 `std_slider_captcha.main(args)`；内部截图背景、调用识别类型 **22222**、计算横向距离并拖动滑块。它不是拼多多旋转验证码入口 `pdd_rotate_captcha`。

| `args` 键 | 值/用途 | 已核实的行为 |
|---|---|---|
| `web_page` | 已打开验证码的影刀 Chrome Page | 在该 Page 查找元素；不负责创建新 Page |
| `background_ele` | 元素库中**完整验证码背景**的选择器 | 对其显示区域截图 |
| `slider_ele` | 元素库中的滑块拖动按钮选择器 | 识别距离后由指令移动 |
| `refresh_elem` | 元素库中的验证码刷新按钮选择器 | 重试时按指令实现尝试刷新 |
| `retry_count` | 单次调用内尝试上限，整数 | 示例设 `2`；源码未传/假值时按 `5` 处理 |
| `offset` | 对识别距离追加的偏移量 | 示例为 `0` |
| `speed` | 距离缩放除数 | 默认 `1` |
| `ym_token` | 云码识别 Token | 留空走影刀侧识别路径；有值走独立云码接口 |

三个 `*_ele` 传**元素库 `Selector` 对象**，例如 `package.selector("滑块背景")`，不能直接用裸 XPath 代替。元素名与实际 XPath 由每个业务项目的真实页面决定，不由该市场指令统一规定。

**调用形态：**

```text
非执行调用说明（不可直接运行）：

from xbot_extensions.activity_jfbym import std_slider_captcha

# 前置：page 已定位到显示拼图验证码的 Chrome Page；
# 三个元素已在当前项目元素库中创建，token 来自未入库的本地配置。
args = {
    "web_page": page,
    "background_ele": package.selector("滑块背景"),
    "slider_ele": package.selector("滑块按钮"),
    "refresh_elem": package.selector("刷新验证码"),
    "retry_count": 2,
    "offset": 0,
    "speed": 1,
    "ym_token": token,
}
std_slider_captcha.main(args=args)
# 调用完成后仍需在业务页面检查验证码是否消失、目标数据是否正常返回。
```

**结果判定与限制：**
- 该入口没有可靠的业务验证成功返回值；调用结束只代表指令流程执行过。调用方应检查**当前页面验证码状态及原业务数据**，不得仅凭无异常就宣称验证成功。
- 单次调用可能包含内部识别重试；业务想统计「遇到验证码几次」时，应在**实际发现验证码**的外层计数，不能把内部识别重试数直接当作遇到次数。
- 有 Token 时安装版本走独立接口；敏感 Token 应留在项目被 Git 忽略的本地配置，不出现在代码样例、日志或 Git。该版本独立云码请求使用未加密 HTTP，存在凭据/图片传输风险；使用前须评估网络和服务可信度。
- **验收范围（2026-11-03）**：正式 RPA 已集成此入口并发布，但当日线上成功采集4条订单时验证码出现 **0次**；已确认业务流程运行成功，**不能据此认定滑块识别已实机验证成功**。

---
