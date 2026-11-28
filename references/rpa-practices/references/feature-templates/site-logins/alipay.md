# 支付宝｜账密登录

入口：`https://auth.alipay.com/login/index.htm`。涉及支付宝敏感登录，遇到风控、短信或扫码步骤必须按当前页面真实状态处理，不默认绕过。

证据：2026-10-29 核对已安装「增强工具2026」中 `login_alipay` 的入口和 XPath；以下代码按原生 Web API 简化，未进行实时页面验证。不照搬旧指令中的不明确二次点击循环。

```python
import time
from xbot import web

web.set_user_environment(mode="chrome", profile_name=profile)
page = web.create("https://auth.alipay.com/login/index.htm", mode="chrome", load_timeout=20)
page.wait_load_completed(timeout=20)
time.sleep(1)
page.find_by_xpath("//div[contains(@class, ' authcenter-body-login')]//li[contains(text(), '账密登录')]", timeout=20).click(delay_after=0.3)
page.find_by_xpath("//div[contains(@class, ' authcenter-body-login')]//input[contains(@id, 'user')]", timeout=10).clipboard_input(account, delay_after=0.3)
page.find_by_xpath("//div[contains(@class, ' authcenter-body-login')]//span[contains(@id, 'password')]/input", timeout=10).input(password, delay_after=0.3)
page.find_by_xpath("//div[contains(@class, ' authcenter-body-login')]//input[contains(@id, 'login-simulate-btn')]", timeout=10).click(delay_after=0.3)

deadline = time.monotonic() + 30
while time.monotonic() < deadline:
    if "login" not in page.get_url().lower():
        break
    time.sleep(0.3)
else:
    raise TimeoutError("支付宝账密登录未完成；检查是否需要安全验证")
```

此代码只实现基础账密流程；登录后的业务访问权限、二次验证均不在成功条件内。
