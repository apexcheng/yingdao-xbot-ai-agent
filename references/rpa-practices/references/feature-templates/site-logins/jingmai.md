# 京麦商家工作台｜账号密码登录

登录入口：`https://passport.shop.jd.com/login/index.action/jdm`。前提：项目已有可用的 Chrome Profile 与账号密码。

证据：2026-10-29 核对已安装「增强工具2026」中 `login_jingmai` 的页面入口和 XPath；尚未对当前京麦页面运行验收。不调用旧市场指令。

```python
import time
from xbot import web

web.set_user_environment(mode="chrome", profile_name=profile)
page = web.create("https://passport.shop.jd.com/login/index.action/jdm", mode="chrome", load_timeout=20)
page.wait_load_completed(timeout=20)
time.sleep(1)
page.find_by_xpath("//div[contains(@class, 'login')]//*[contains(text(), '密码登录')]", timeout=10).click(delay_after=0.3)
page.find_by_xpath("//div[contains(@class, 'login')]//input[contains(@id, 'loginname')]", timeout=10).input(account, delay_after=0.3)
page.find_by_xpath("//div[contains(@class, 'login')]//input[contains(@type, 'password')]", timeout=10).input(password, delay_after=0.3)
page.find_by_xpath("//div[contains(@class, 'login')]//button[contains(., '立即登录')]", timeout=10).click(delay_after=0.3)

deadline = time.monotonic() + 30
while time.monotonic() < deadline:
    if "login" not in page.get_url().lower():
        break
    time.sleep(0.3)
else:
    raise TimeoutError("京麦登录后仍停留在登录页")
```

离开登录页不保证店铺授权完整；风险验证由实际项目按页面事实处理。
