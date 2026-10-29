# 千牛商家工作台｜密码登录（iframe）

入口：`https://loginmyseller.taobao.com/`。已核实原登录控件位于 `//iframe[contains(@id, 'login')]` 内。**不能直接把框内 XPath 交给外层 `page.find_by_xpath()`**。

证据：2026-10-29 核对已安装「增强工具2026」中 `login_qianniu` 的 iframe XPath；影刀知识库 [iframe2 接口事实](../../../../../../../xbot-api-docs/docs/iframe2-extension.md) 核验版本为 25.12.0。当前页面及登录状态尚未实测。

此站点的跨 iframe 操作**仍依赖独立的 `iframe2` 市场指令**，但不需要「增强工具2026」；当前知识库没有可替代它的已确认原生 `xbot.web` 跨 iframe 公开接口。

```python
import time
from xbot import web
from xbot_extensions.iframe2.api import find_ele

web.set_user_environment(mode="chrome", profile_name=profile)
page = web.create("https://loginmyseller.taobao.com/", mode="chrome", load_timeout=20)
page.wait_load_completed(timeout=20)
time.sleep(1)

find_ele(iframe_instance=page, xpath=["//iframe[contains(@id, 'login')]", "//div[contains(@class, 'login')]//a[contains(text(), '密码登录')]"], timeout=10, current_global=False).click(delay_after=0.3)
find_ele(iframe_instance=page, xpath=["//iframe[contains(@id, 'login')]", "//form[contains(@class, 'login-form')]//input[contains(@id, 'login-id')]"], timeout=10, current_global=False).input(account, delay_after=0.3)
find_ele(iframe_instance=page, xpath=["//iframe[contains(@id, 'login')]", "//form[contains(@class, 'login-form')]//input[contains(@id, 'password')]"], timeout=10, current_global=False).input(password, delay_after=0.3)
find_ele(iframe_instance=page, xpath=["//iframe[contains(@id, 'login')]", "//form[contains(@class, 'login-form')]//button[contains(text(), '登录')]"], timeout=10, current_global=False).click(delay_after=0.3)

deadline = time.monotonic() + 30
while time.monotonic() < deadline:
    if "login" not in page.get_url().lower():
        break
    time.sleep(0.3)
else:
    raise TimeoutError("千牛登录后仍停留在登录页")
```

前提：`iframe2` 已安装，且当前 iframe 与控件 XPath 未变化；未解决扫码、短信二次验证和风控弹窗。离开登录页后应检查目标业务页面权限。
