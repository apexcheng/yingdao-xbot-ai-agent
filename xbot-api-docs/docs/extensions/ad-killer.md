# 广告杀手 (ad_killer)

> 调用类型：`Visual / Direct Python`
> 公开入口：`close_ads()` / `close_ads_win()`
> 证据边界：`close_type` 等枚举以当前安装版本为准。
> 返回：[市场指令索引](../extension-instructions.md)

## 用途与入口

- `xbot_extensions.ad_killer.close_ads(网页对象, 广告Xpath, 使用内置广告Xpath, 关闭方式)`：异步处理网页广告。
- `xbot_extensions.ad_killer.close_ads_win(元素选择器列表)`：后台监测 Win32 弹窗。

| 参数 | 说明 |
|---|---|
| `广告Xpath` | 自定义广告元素 XPath |
| `使用内置广告Xpath` | 是否同时使用扩展内置名单，默认 `False` |
| `关闭方式` | `"hidden"` 隐藏元素（默认），或 `"click"` 点击关闭元素 |
| `元素选择器列表` | Win32 Selector 对象列表，不是元素库名称字符串；通过元素库名称获取对象时，使用 `package.selector(name)` |

当前核对的 `ad_killer==25.12.2` 会读取列表成员的 `value`：传入字符串会报 `AttributeError`，传入 Web 选择器会报 `ValueError`。

`"hidden"` 不依赖广告存在可点击的关闭按钮；`"click"` 只适用于 XPath 能定位真实关闭元素的情况。网页刷新后需重新调用 `close_ads()`；Win32 监测随主流程结束。

## 网页端持续监听风险与推荐替代

已核对的网页端实现会通过 `execute_javascript()` 注入 `MutationObserver`，持续监听页面及子节点的新增变化；每次触发检查时重新查询 XPath / CSS，并点击或隐藏匹配元素。源码未主动调用 `observer.disconnect()`。**即使当前 XPath 没有匹配元素，监听仍会继续**。这在动态网页中可能造成额外查询负担或干扰交互，但不能仅凭源码断言所有网页都会受影响。

**已观察案例（2026-10-28，千牛商家后台）：** RPA 打开页面后，「批量导出」「消息」等按钮显示正常却点击无反应；手动刷新可恢复，注释 `close_ads()` 后业务可正常执行。已证实该指令调用与故障有关，但尚未证实具体是高频查询还是自动关闭弹窗导致；不应据此推断网站反自动化拦截。

普通弹窗处理优先使用原生 `xbot.web` **单次定位、按需操作**，无需长期 DOM 监听。以下示例要求 `web_page` 为已打开的 Page，`xpath` 为经过确认的目标元素 XPath：

```text
非执行调用说明（不可直接运行）：

# 点击关闭
for element in web_page.find_all_by_xpath(xpath, timeout=0.5):
    element.click()

# 隐藏元素
for element in web_page.find_all_by_xpath(xpath, timeout=0.5):
    element.set_attribute("hidden", "")
```

单次检查只处理当前已出现的元素；较晚出现的弹窗应根据实际出现时机在对应步骤再次检查，而非默认引入持续监听。HTML 的 `hidden` 属性通常可隐藏元素，但效果可能受网页 CSS 影响。XPath 也应限定到目标弹窗，避免误操作正常业务元素。

仅当业务确实需要持续监测、且已验证不会影响目标页面时，才考虑网页端 `close_ads()`。上述风险和替代方式**不适用于 Win32 的 `close_ads_win()`**。

## 网页端持续监听调用（非默认推荐）

```text
非执行调用说明（不可直接运行）：

from xbot_extensions.ad_killer import close_ads

close_ads(
    网页对象=web_page,
    广告Xpath="//button[@class='close-btn']",
    使用内置广告Xpath=False,
    关闭方式="click",
)
```

`close_ads_win()` 接收 Win32 Selector 对象列表。下面示例通过已有元素库名称获取 Selector 对象：

```text
非执行调用说明（不可直接运行）：

from . import package
from xbot_extensions.ad_killer import close_ads_win

close_ads_win([
    package.selector("chrome最近下载列表"),
])
```

业务代码只使用公开入口，不直接导入扩展的私有实现模块。
