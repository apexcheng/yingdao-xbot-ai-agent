"""SHOPEE 官方仓库存数据源：登录卖家中心、下载双地区报告并写入 RAW 区。"""

import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from xbot import web
from xbot.app import logging
from xbot_extensions.xbot_enhance_tools.browser_utils import wait_download_file

from .config import BROWSER_PROFILE, SHOPEE_OFFICIAL_WAREHOUSE_URLS
from .utils import clean_text, get_shop_credential, load_excel_matrix, replace_raw_area

SHEET_NAME = "SHOPEE官方仓库存"
RAW_LAYOUT = {
    "start_col": "H",
    "header_rows": 2,
    "expected_headers": [
        (1, 2, "仓库SKU ID"),
        (0, 6, "仓库"),
        (0, 7, "可售数量"),
        (1, 15, "待处理的IR已到达"),
        (1, 16, "待上架库存"),
    ],
}

REGIONS = ("马来西亚", "菲律宾")
TASK_TIME = re.compile(r"20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}")


def _login_shopee(username, password):
    """
    复用卖家中心的登录能力并返回已登录页面，供库存和 SKU 映射共用。

    :param username: Shopee 卖家中心账号
    :param password: Shopee 卖家中心密码
    :return: 已完成登录的页面对象
    """
    try:
        from xbot_extensions.activity_shopee_seller import account_login
    except ImportError as exc:
        raise RuntimeError("当前应用缺少 Shopee 登录市场指令依赖 activity_shopee_seller") from exc

    web.set_user_environment(
        mode="chrome",
        profile_name=BROWSER_PROFILE,
        specifield_userdata=False,
        user_data_dir=None,
    )
    # 打开卖家中心登录页并等待就绪
    browser = web.create(url="https://seller.shopee.cn/account/signin", mode="chrome", load_timeout=60)
    browser.wait_load_completed(timeout=60)

    # Shopee 卖家中心登录市场指令：account=账号；password=密码；web_page=当前登录页。
    account_login.main(args={"account": username, "password": password, "web_page": browser})

    # 校验登录后已离开登录页
    if "account/signin" in browser.get_url():
        raise RuntimeError("Shopee 自动登录失败，当前仍停留在登录页")
    return browser


def prepare():
    """
    在同一个 Shopee 页面依次导出两地区库存，并校验双表头、纵向合并。

    :return: 含合并后二维数据和各地区行数的 payload
    """
    # 校验两个地区的库存管理 URL
    urls = [str(url or "").strip() for url in SHOPEE_OFFICIAL_WAREHOUSE_URLS]
    if len(urls) != 2 or not all(urls) or urls[0] == urls[1]:
        raise RuntimeError("Shopee 官方仓两个地区库存管理 URL 配置错误")
    shop_ids = [parse_qs(urlsplit(url).query).get("cnsc_shop_id", [""])[0] for url in urls]
    if not all("/portal/fbs/inventory/current/v2" in url for url in urls) or not all(shop_ids):
        raise RuntimeError("Shopee 官方仓 URL 必须指向对应地区的现有库存页面")

    web.set_user_environment(
        mode="chrome", profile_name=BROWSER_PROFILE,
        specifield_userdata=False, user_data_dir=None,
    )
    browser = web.create(url=urls[0], mode="chrome", load_timeout=60)
    try:
        browser.wait_load_completed(timeout=60)

        # 登录失效时使用已有共享登录能力，回到库存页面
        if "account/signin" in browser.get_url():
            credentials = get_shop_credential("shopee")
            browser.close()
            browser = None
            browser = _login_shopee(credentials["username"], credentials["password"])
            browser.navigate(urls[0], load_timeout=60)
            browser.wait_load_completed(timeout=60)
        if "/portal/fbs/inventory/current/v2" not in browser.get_url():
            raise RuntimeError("Shopee 官方仓没有进入现有库存页面，请确认登录状态")

        # 按地区依次完成切换、导出、等待和下载，任一失败都不提交该 Sheet
        merged = []
        first_headers = None
        counts = {}
        for region, shop_id in zip(REGIONS, shop_ids):
            logging.info(f"[{SHEET_NAME}] {region} 开始下载")

            # 切换地区，等待地区标签、店铺 ID 和现有库存页面全部就绪
            browser.find_by_xpath(
                "//div[contains(@class,'eds-selector--label')][.//div[contains(@class,'eds-selector__label--text') and contains(.,'仓库所在地区')]]",
                timeout=15,
            ).click(delay_after=0.2)
            browser.find_by_xpath(
                f"//div[contains(@class,'eds-select__options')]//div[contains(@class,'eds-option') and normalize-space()='{region}']",
                timeout=10,
            ).click(delay_after=0.3)

            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                labels = browser.find_all_by_xpath(
                    "//div[contains(@class,'eds-selector--label')][.//div[contains(@class,'eds-selector__label--text') and contains(.,'仓库所在地区')]]/div[contains(@class,'eds-selector__inner')]",
                    timeout=1,
                )
                if (
                    labels
                    and clean_text(labels[0].get_text()) == region
                    and f"cnsc_shop_id={shop_id}" in browser.get_url()
                ):
                    browser.find_by_xpath(
                        "//span[contains(@class,'sc-ssc-react-dropdown-reference')]//button[.//span[normalize-space()='导出']]",
                        timeout=15,
                    )
                    break
                time.sleep(1)
            else:
                raise RuntimeError(f"Shopee 官方仓切换至 {region} 失败，当前网址 {browser.get_url()}")

            # 打开任务中心，选库存管理，记录触发导出前已有的库存报告
            browser.find_by_xpath(
                "//span[contains(@class,'task-center-text') and normalize-space()='任务中心']",
                timeout=15,
            ).click(delay_after=0.2)
            browser.find_by_xpath(
                "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//div[contains(@class,'eds-tabs__nav-tab')][normalize-space()='库存管理']",
                timeout=10,
            ).click(delay_after=0.2)

            existing = set()
            for row in browser.find_all_by_xpath(
                "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//tr[contains(@class,'eds-table__row')]",
                timeout=1,
            ):
                cells = row.find_all_by_xpath("./td", timeout=1)
                if len(cells) < 4:
                    continue
                name = clean_text(cells[0].get_text())
                matched = TASK_TIME.search(clean_text(cells[1].get_text()))
                if name.startswith("Current Inventory Report") and name.endswith(".xlsx") and matched:
                    existing.add((name, datetime.strptime(matched.group(), "%Y-%m-%d %H:%M:%S")))

            browser.find_by_xpath(
                "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//i[contains(@class,'eds-modal__close')]",
                timeout=10,
            ).click(delay_after=0.2)

            # 从现有库存页面发起“导出全部”，记录本轮提交时间
            browser.find_by_xpath(
                "//span[contains(@class,'sc-ssc-react-dropdown-reference')]//button[.//span[normalize-space()='导出']]",
                timeout=15,
            ).click(delay_after=0.2)
            requested_at = datetime.now()
            browser.find_by_xpath(
                "//li[@role='menuitem' and contains(.,'导出全部') and @aria-disabled='false']",
                timeout=10,
            ).click(delay_after=0.2)

            # 再次打开任务中心，等待明确属于本轮的库存报告生成
            browser.find_by_xpath(
                "//span[contains(@class,'task-center-text') and normalize-space()='任务中心']",
                timeout=15,
            ).click(delay_after=0.2)
            browser.find_by_xpath(
                "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//div[contains(@class,'eds-tabs__nav-tab')][normalize-space()='库存管理']",
                timeout=10,
            ).click(delay_after=0.2)

            deadline = time.monotonic() + 180
            selected = None
            while time.monotonic() < deadline:
                new_tasks = []
                for row in browser.find_all_by_xpath(
                    "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//tr[contains(@class,'eds-table__row')]",
                    timeout=1,
                ):
                    cells = row.find_all_by_xpath("./td", timeout=1)
                    if len(cells) < 4:
                        continue
                    name = clean_text(cells[0].get_text())
                    matched = TASK_TIME.search(clean_text(cells[1].get_text()))
                    if not name.startswith("Current Inventory Report") or not name.endswith(".xlsx") or not matched:
                        continue
                    submitted_at = datetime.strptime(matched.group(), "%Y-%m-%d %H:%M:%S")
                    if (name, submitted_at) not in existing and submitted_at >= requested_at - timedelta(seconds=5):
                        new_tasks.append({
                            "name": name,
                            "submitted_at": submitted_at,
                            "status": clean_text(cells[2].get_text()),
                            "row": row,
                        })
                if len(new_tasks) > 1:
                    raise RuntimeError(f"Shopee {region} 同时出现多条新库存导出任务，无法安全区分")
                if new_tasks:
                    selected = new_tasks[0]
                    if "失败" in selected["status"]:
                        raise RuntimeError(f"Shopee {region} 库存导出失败：{selected['name']}")
                    if selected["status"] == "成功":
                        break

                # 通过切换页签触发后台刷新
                browser.find_by_xpath(
                    "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//div[contains(@class,'eds-tabs__nav-tab')][normalize-space()='概览']",
                    timeout=5,
                ).click(delay_after=0.1)
                browser.find_by_xpath(
                    "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//div[contains(@class,'eds-tabs__nav-tab')][normalize-space()='库存管理']",
                    timeout=5,
                ).click(delay_after=0.1)
                time.sleep(2)
            if selected is None or selected["status"] != "成功":
                raise RuntimeError(f"Shopee {region} 本轮库存导出等待超时")

            # 只下载本轮确定的任务行，完成后读取该地区文件
            started_at = time.time()
            selected["row"].find_by_xpath(
                ".//button[contains(@class,'download')]", timeout=10
            ).click(delay_after=0.2)
            # 增强工具2026 wait_download_file：download_dir=用户下载目录；
            # filename_pattern=本轮文件名；timeout=等待秒数；start_time=点击下载前的时间。
            downloaded = wait_download_file(
                download_dir=str(Path.home() / "Downloads"),
                filename_pattern=Path(selected["name"]).stem + "*.xlsx",
                timeout=120,
                start_time=started_at,
            )
            logging.info(
                f"[{SHEET_NAME}] {region} 下载完成：{selected['name']}，"
                f"提交时间 {selected['submitted_at']:%Y-%m-%d %H:%M:%S}"
            )
            browser.find_by_xpath(
                "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//i[contains(@class,'eds-modal__close')]",
                timeout=10,
            ).click(delay_after=0.2)

            data = load_excel_matrix(downloaded)
            if not any(clean_text(row[2]) for row in data[2:]):
                raise RuntimeError(f"Shopee {region} 官方仓库存导出没有有效仓库 SKU 数据")
            counts[region] = len(data) - 2

            # 两个地区双表头必须一致，仅保留首份表头
            headers = [[clean_text(value) for value in row] for row in data[:2]]
            if first_headers is None:
                first_headers = headers
                merged = data[:]
            else:
                if headers != first_headers:
                    raise RuntimeError("Shopee 官方仓第 2 个文件表头与第 1 个文件不一致")
                merged.extend(data[2:])

        return {"data": merged, "counts": counts}
    finally:
        if browser is not None:
            browser.close()


def apply_update(workbook, payload):
    """
    将 Shopee 官方仓双地区原始数据写入目标 Sheet 的 RAW 区。

    :param workbook: 已打开的目标工作簿
    :param payload: ``prepare`` 返回的数据
    :return: 写入结果描述文本
    """
    detail = replace_raw_area(workbook, SHEET_NAME, payload["data"], RAW_LAYOUT)
    return f"{detail}；马来西亚 {payload['counts']['马来西亚']} 条，菲律宾 {payload['counts']['菲律宾']} 条"
