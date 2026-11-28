# 拼多多商家中心｜账号密码登录

登录入口：`https://mms.pinduoduo.com/login/`。已有 Chrome Profile 可先打开目标业务页判断是否需要登录；以下示例只负责**需要登录时的操作**，不是无条件清空登录状态。

证据：2026-10-29 核对已安装「增强工具2026」中 `login_pdd_seller` 的页面入口及 XPath；未对当前拼多多 DOM 或登录成功进行实测。此示例不依赖该市场指令。

```python
import time
from xbot import web

web.set_user_environment(mode="chrome", profile_name=profile)
page = web.create("https://mms.pinduoduo.com/login/", mode="chrome", load_timeout=20)
page.wait_load_completed(timeout=20)
time.sleep(1)
page.find_by_xpath("//div[contains(@class, 'info-part')]//div[contains(text(), '账号登录')]", timeout=10).click(delay_after=0.3)
page.find_by_xpath("//div[contains(@class, 'info-part')]//input[contains(@id, 'username')]", timeout=10).input(account, delay_after=0.3)
page.find_by_xpath("//div[contains(@class, 'info-part')]//input[contains(@id, 'password')]", timeout=10).input(password, delay_after=0.3)
page.find_by_xpath("//div[contains(@class, 'info-part')]//button[contains(., '登录')]/span", timeout=10).click(delay_after=0.3)

deadline = time.monotonic() + 30
while time.monotonic() < deadline:
    if "login" not in page.get_url().lower():
        break
    time.sleep(0.3)
else:
    raise TimeoutError("拼多多商家登录后仍停留在登录页")
```

`profile`、`account`、`password` 来自项目已确认配置。离开登录页只是初步登录判断，具体店铺权限应在业务页验证。扫码、短信及人机验证不包含在此流程。
