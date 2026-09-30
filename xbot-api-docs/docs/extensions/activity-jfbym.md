# 云码验证码识别 (activity_jfbym)

> 调用类型：`Direct`  
> 主要入口：Code 型直接调用各验证码模块的 main(args)；本页只核验 `std_alphanum_captcha`（通用数英验证码）。  
> 证据边界：args 结构与行为按 2026-10 安装版本 26.5.0 源码确认；`captcha_type` 编号来自真实项目稳定调用，未独立运行验证。  
> 返回：[市场指令索引](../extension-instructions.md)

---

**目录/指令名：** `activity_jfbym` / 云码验证码识别（jfbym）

**调用方式：** Direct Python

**用途：** 对网页元素截图后调用云端识别，返回验证码文本；扩展内覆盖数英、滑块、点选、九宫格等多类验证码。本页仅核验通用数英入口。

**调用入口：**
- Direct：`std_alphanum_captcha.main(args)`（通用数英验证码识别）

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
- 扩展内滑块、点选、九宫格等其他验证码模块本页未核验，不要按 `std_alphanum_captcha` 的 args 结构套用。

---
