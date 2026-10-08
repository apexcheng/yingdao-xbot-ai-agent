"""雅仓库存数据源：登录雅仓、导出下载库存文件并写回 RAW 区。"""

import re
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from xbot import web
from xbot_extensions.xbot_enhance_tools.browser_utils import wait_download_file

from . import package
from .config import BROWSER_PROFILE
from .utils import clean_text, get_shop_credential, load_excel_matrix, replace_raw_area, validate_headers

SHEET_NAME = "雅仓库存"
RAW_LAYOUT = {
    "start_col": "F",
    "header_rows": 1,
    "expected_headers": [(0, 1, "SKU"), (0, 4, "仓库"), (0, 10, "在途数量"), (0, 12, "可用库存")],
}


def _login_seaya(username, password):
    """
    使用现有账号和验证码能力登录雅仓并返回已登录页面。

    :param username: 雅仓登录手机号
    :param password: 雅仓登录密码
    :return: 已完成登录的页面对象
    """
    try:
        from xbot_extensions.activity_jfbym import std_alphanum_captcha
    except ImportError as exc:
        raise RuntimeError("当前应用缺少雅仓验证码市场指令依赖 activity_jfbym") from exc

    web.set_user_environment(
        mode="chrome",
        profile_name=BROWSER_PROFILE,
        specifield_userdata=False,
        user_data_dir=None,
    )
    # 打开登录页并填入手机号和密码
    browser = web.create(url="https://m.seaya.cn/login", mode="chrome", load_timeout=60)
    browser.wait_load_completed(timeout=60)
    browser.find_by_xpath("//div[@placeholder='请输入手机号']//input[@class='el-input__inner']", timeout=20).input(username)
    browser.find_by_xpath("//div[@placeholder='请输入密码']//input[@class='el-input__inner']", timeout=20).input(password)

    # 从元素库读取验证码图片位置，缺失时说明编辑器尚未同步
    try:
        captcha_selector = package.selector("seaya_captcha_img")
    except Exception as exc:
        raise RuntimeError(
            "雅仓登录需要元素库 seaya_captcha_img；参考项目已有该 selector，当前应用尚未通过影刀编辑器同步"
        ) from exc

    # 调用云码识别验证码并回填
    captcha_args = {
        "web_page": browser,
        "ele": captcha_selector,
        "token": "",
        "captcha_type": "10110",
    }
    # 云码验证码识别市场指令：web_page=验证码页面；ele=验证码图片 Selector；
    # token=云码 code（空值使用影刀免费识别）；captcha_type=通用数英≤5位。
    std_alphanum_captcha.main(args=captcha_args)
    verify_code = clean_text(captcha_args.get("data"))
    if not verify_code:
        raise RuntimeError("雅仓验证码识别结果为空")

    # 提交登录并校验已离开登录页
    browser.find_by_xpath("//div[@placeholder='请输入验证码']//input", timeout=10).input(verify_code)
    browser.find_by_xpath("//button[contains(., '登录')]", timeout=10).click(delay_after=0.3)
    browser.wait_load_completed(timeout=60)
    if "login" in browser.get_url():
        raise RuntimeError("雅仓自动登录失败，提交后仍停留在登录页")
    return browser


def prepare():
    """
    登录雅仓、导出下载库存文件，并校验库存数据。

    :return: 含二维数据和来源文件路径的 payload
    """
    web.set_user_environment(
        mode="chrome",
        profile_name=BROWSER_PROFILE,
        specifield_userdata=False,
        user_data_dir=None,
    )
    url = "https://m.seaya.cn/warehouse/inventoryManagement/stockWarehouse"
    browser = web.create(url=url, mode="chrome", load_timeout=60)
    browser.wait_load_completed(timeout=60)

    # 登录态失效时用现有凭证重新登录再回到库存页
    if "login" in browser.get_url():
        credentials = get_shop_credential("seaya")
        browser.close()
        browser = _login_seaya(credentials["username"], credentials["password"])
        browser.navigate(url, load_timeout=60)
        browser.wait_load_completed(timeout=60)

    # 关闭可能遮挡下载按钮的提醒弹窗
    for xpath in (
        '//div[contains(@aria-label, "提醒")]//button[@aria-label="关闭此对话框"]',
        '//div[@class="el-overlay"]//span[@title="关闭"]',
    ):
        elements = browser.find_all_by_xpath(xpath, timeout=1)
        if elements:
            elements[0].click(delay_after=0.2)

    # 触发右上角库存导出
    download_buttons = browser.find_all_by_xpath(
        "//div[contains(@class, 'right-view')]//button[.//*[name()='path' and contains(@d, 'M160 832h704')]]",
        timeout=5,
    )
    if not download_buttons:
        browser.reload(ignore_cache=True, load_timeout=60)
        download_buttons = browser.find_all_by_xpath(
            "//div[contains(@class, 'right-view')]//button[.//*[name()='path' and contains(@d, 'M160 832h704')]]",
            timeout=5,
        )
    if not download_buttons:
        raise RuntimeError("雅仓库存页刷新后仍未找到右上角下载按钮")

    existing_export_counts = defaultdict(int)
    for row in browser.find_all_by_xpath("//div[@class='item-view'][contains(., '库存导出')]", timeout=1):
        existing_export_counts[clean_text(row.get_text())] += 1

    # 提交导出请求并记录请求时间，用于识别新生成的导出记录
    request_started = datetime.now()
    download_buttons[0].click(delay_after=0.3)
    notification_close = browser.find_all_by_xpath(
        "//div[contains(@id, 'notification')]//i[contains(@class, 'closeBtn')]",
        timeout=1,
    )
    if notification_close:
        notification_close[0].click(delay_after=0.2)

    # 在下载管理中轮询等待本轮导出记录生成
    browser.find_by_xpath("//div[@class='fixed-header']//div[@content='下载管理']", timeout=10).click(delay_after=0.3)
    deadline = time.monotonic() + 90
    export_row = None
    while time.monotonic() < deadline:
        seen_counts = defaultdict(int)
        for row in browser.find_all_by_xpath("//div[@class='item-view'][contains(., '库存导出')]", timeout=1):
            row_text = clean_text(row.get_text())
            seen_counts[row_text] += 1
            timestamp_match = re.search(r"20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?", row_text)
            if not timestamp_match:
                continue
            timestamp_text = timestamp_match.group()
            timestamp_format = "%Y-%m-%d %H:%M:%S" if timestamp_text.count(":") == 2 else "%Y-%m-%d %H:%M"
            created_at = datetime.strptime(timestamp_text, timestamp_format)
            threshold = request_started - timedelta(seconds=5) if timestamp_format.endswith("%S") else request_started.replace(second=0, microsecond=0)
            is_new_row = seen_counts[row_text] > existing_export_counts.get(row_text, 0)
            if is_new_row and created_at >= threshold:
                export_row = row
                break
        if export_row is not None:
            break
        generating = browser.find_all_by_xpath(
            "//div[@class='item-view'][contains(., '文件生成中')]//div[@class='btn']",
            timeout=1,
        )
        if generating:
            generating[0].click(delay_after=0.3)
        time.sleep(1)
    if export_row is None:
        raise RuntimeError(f"雅仓库存导出在 90 秒内未生成完成：请求时间 {request_started:%Y-%m-%d %H:%M:%S}")

    # 下载本轮导出文件并等待落盘完成
    start_time = time.time()
    export_row.find_by_xpath(".//div[@class='btn']", timeout=5).click(delay_after=0.3)
    # 增强工具2026 wait_download_file：download_dir=用户下载目录；filename_pattern=库存导出；
    # timeout=下载等待上限；start_time=点击下载前时间，用于排除旧文件。
    downloaded = wait_download_file(
        download_dir=str(Path.home() / "Downloads"),
        filename_pattern="库存导出",
        timeout=120,
        start_time=start_time,
    )
    # 读取并校验本轮下载的库存数据
    data = load_excel_matrix(downloaded)
    validate_headers(data, ["SKU", "仓库", "可用库存"], header_rows=1)

    # 校验至少一行同时有 SKU 和仓库的有效库存数据
    headers = [clean_text(value) for value in data[0]]
    sku_index = headers.index("SKU")
    warehouse_index = headers.index("仓库")
    if not any(
        clean_text(row[sku_index]) and clean_text(row[warehouse_index])
        for row in data[1:]
    ):
        raise RuntimeError("雅仓库存导出只有表头或没有有效库存数据行")
    return {"data": data, "source_file": str(downloaded)}


def apply_update(workbook, payload):
    """
    把雅仓库存原始数据写入右侧数据源区域。

    :param workbook: 已打开的目标工作簿
    :param payload: ``prepare`` 返回的数据
    :return: 写入结果描述文本
    """
    detail = replace_raw_area(workbook, SHEET_NAME, payload["data"], RAW_LAYOUT)
    return f"{detail}；来源 {Path(payload['source_file']).name}"
