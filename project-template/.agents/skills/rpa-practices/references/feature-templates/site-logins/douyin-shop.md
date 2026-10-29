# 抖店（抖音电商）商家后台｜手机号 + ntfy 短信验证码登录（当前推荐）

入口：`https://fxg.jinritemai.com/login/common`。适用于抖店已退出登录、持有合法手机号并已建立短信 → 私有 ntfy topic 转发的项目。若原 Chrome Profile 仍有登录态，优先进入业务页确认，不应为了登录而主动退出。

**证据边界（2026-10-29）**：用户提供登录 URL、所有步骤及 XPath，并确认短信格式为 `【抖店】验证码<六位数字>，用于手机验证码登录...`。真实实现来自 [抖店经营报表 `run.py`，提交 `91acca7`](https://github.com/apexcheng/douyin-bow-profit-report-rpa/commit/91acca7)，影刀应用已发布 **V34**；**尚未进行真实短信登录端到端验收**。下方是根据该版本提炼、使用 `xbot.web` 和 Python 标准库的**新项目模板**，不依赖「增强工具2026」，并非已部署 V34 的逐字源码。登录 UI 更新后必须重新核 XPath。

## 已实现流程与边界

1. 复用指定 Chrome Profile，先打开业务页检查 URL；已登录时不执行登录。
2. 未登录时在原 Page 导航到 `/login/common`，等待页面加载后等待 1 秒。
3. 尝试点击 `//div[contains(@class, '--qr')]`，查找最多 3 秒，未找到不阻塞。
4. 切换「手机登录」、填手机号、点击「验证码」（完整 XPath 在下方代码）。
5. 从点击前记录的本轮时间开始匹配 ntfy 短信，最长等待 300 秒；本轮确认的正文为 `【抖店】验证码123456，用于手机验证码登录，5分钟内有效。`（数字仅为虚构示例）。
6. 输入验证码；仅在服务协议未勾选时点击勾选框；点击登录。
7. 10 秒内检测到 URL 不再包含 `/login` 即返回同一 Page；否则报错。此条件**不等于已验证业务权限**。

**与已部署 V34 的区别**：V34 接码仍调用 `xbot_extensions.xbot_enhance_tools.ntfy_message.receive_ntfy_message`；此模板将接码改为 ntfy JSON HTTP 轮询，供**未来新项目**摆脱「增强工具2026」。V34 未修改、未因这份文档重新发布。

必需项目配置（位于 Git 忽略的 `config.py`）：`DOUYIN_PHONE`、`DOUYIN_PROFILE`、`NTFY_TOPIC`；`NTFY_SERVER` 默认 `https://ntfy.sh`，以真实项目配置为准。不要把真实手机号、验证码、topic 写进知识库或日志。

## 复制到业务代码的登录函数

```python
import json
import re
import time
from urllib.parse import quote
from urllib.request import urlopen

from xbot import web
from .config import DOUYIN_PHONE, DOUYIN_PROFILE, NTFY_TOPIC, NTFY_SERVER


def login_douyin_phone(page):
    """在调用方已经选择 Chrome Profile 的现有 Page 上执行抖店手机号登录。"""
    if not DOUYIN_PHONE or not NTFY_TOPIC:
        raise ValueError("抖店手机号或 ntfy topic 未配置")

    page.navigate("https://fxg.jinritemai.com/login/common", load_timeout=20)
    page.wait_load_completed(timeout=20)
    time.sleep(1)

    qr_buttons = page.find_all_by_xpath("//div[contains(@class, '--qr')]", timeout=3)
    if qr_buttons:
        qr_buttons[0].click(delay_after=0.3)
    page.find_by_xpath("//div[contains(@class, 'daren-login-container')]//*[contains(text(), '手机登录')]", timeout=5).click(delay_after=0.3)
    page.find_by_xpath("//div[contains(@class, 'daren-login-container')]//input[@title='手机号码']", timeout=5).input(str(DOUYIN_PHONE), delay_after=0.3)

    requested_at = int(time.time())
    page.find_by_xpath("//div[contains(@class, 'login-custom')]//div[contains(@class, 'input-row')]//div[contains(text(), '验证码')]", timeout=5).click(delay_after=0.3)

    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        # ntfy JSON 轮询协议；与旧增强工具无关。每次重新读取近 10 分钟的缓存消息。
        url = f"{NTFY_SERVER.rstrip('/')}/{quote(NTFY_TOPIC, safe='')}/json?since=10m&poll=1"
        with urlopen(url, timeout=15) as response:
            messages = [
                json.loads(line)
                for line in response.read().decode("utf-8").splitlines()
                if line.strip()
            ]
        for message in messages:
            if message.get("event") != "message" or (message.get("time") or 0) < requested_at:
                continue
            match = re.search(r"【(?:抖店|抖音电商)】验证码\s*([0-9]{6})", message.get("message") or "")
            if match:
                code = match.group(1)
                break
        else:
            time.sleep(3)
            continue
        break
    else:
        raise TimeoutError("300 秒内未收到本次抖店登录验证码")

    page.find_by_xpath("//div[contains(@class, 'login-custom')]//div[contains(@class, 'input-row')]//input[@placeholder='验证码']", timeout=5).input(code, delay_after=0.3)
    if not page.find_all_by_xpath("//div[contains(@class,'policyWrapper')]//span[contains(@class, 'checkbox-checked')]", timeout=1):
        page.find_by_xpath("//div[contains(@class,'policyWrapper')]//span[contains(@class, 'checkbox')]//input", timeout=3).click(delay_after=0.3)
    page.find_by_xpath("//div[contains(@class, 'login-custom')]//button[contains(., '登录')]", timeout=5).click(delay_after=0.3)

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if "/login" not in page.get_url().lower():
            return page
        time.sleep(0.2)
    raise RuntimeError("抖店登录后 10 秒仍停留在登录页")
```

已有项目调用方式：先 `web.set_user_environment(mode="chrome", profile_name=DOUYIN_PROFILE)`，打开目标业务页，`wait_load_completed()` 后确认 URL 是否包含 `login`；仅未登录时调用 `login_douyin_phone(page)`。登录函数返回同一 Page；后续业务页另行确认登录态和授权。无需新增通用 LoginService、扫码 fallback、跨轮验证码缓存。

**验证码过滤边界**：ntfy 的 `time` 只有秒精度，`requested_at=int(time.time())` 并使用 `<` 排除旧秒消息，仍可能匹配本秒内的先前消息；若同一 topic 多账号并发接码，必须依据业务确认更严格的关联规则，不能默默把第一条当作本次验证码。登录前不要将验证码写日志。

旧邮箱登录 `login_douyin_seller(account, password, profile)` 仅保留在历史市场 API 文档，**不作为新项目默认实现**。
