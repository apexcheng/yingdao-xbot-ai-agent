"""SHOPEE SKU 映射数据源：按地区导出已批准商品并写回 RAW 区。"""

import re
import time
from datetime import datetime, timedelta
from pathlib import Path

from xbot import web
from xbot.app import logging
from xbot_extensions.xbot_enhance_tools.browser_utils import wait_download_file

from .config import BROWSER_PROFILE
from .update_shopee_warehouse import _login_shopee
from .utils import clean_text, get_shop_credential, load_excel_matrix, replace_raw_area

SHEET_NAME = "SHOPEE SKU映射"
RAW_LAYOUT = {
    "start_col": "F",
    "header_rows": 1,
    "expected_headers": [(0, 3, "店铺SKU ID"), (0, 4, "仓库SKU ID"), (0, 5, "外部SKU ID")],
}

PRODUCT_URL = "https://seller.shopee.cn/portal/fbs/product/approved?cnsc_shop_id=EXAMPLE_MY_SHOP_ID"
REGION_SHOPS = (("马来西亚", "EXAMPLE_MY_SHOP_ID"), ("菲律宾", "EXAMPLE_PH_PRODUCT_SHOP_ID"))
TASK_TIME = re.compile(r"20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}")


def prepare():
    """
    下载 MY / PH 已批准商品文件并拼接 SKU 映射。

    :return: 含二维数据的 payload
    """
    web.set_user_environment(
        mode="chrome", profile_name=BROWSER_PROFILE,
        specifield_userdata=False, user_data_dir=None,
    )
    browser = web.create(url=PRODUCT_URL, mode="chrome", load_timeout=60)
    try:
        browser.wait_load_completed(timeout=60)

        # 登录态失效时复用官方仓模块的 Shopee 登录能力
        if "account/signin" in browser.get_url():
            credentials = get_shop_credential("shopee")
            browser.close()
            browser = _login_shopee(credentials["username"], credentials["password"])
            browser.navigate(PRODUCT_URL, load_timeout=60)
            browser.wait_load_completed(timeout=60)
        if "/portal/fbs/product/" not in browser.get_url():
            raise RuntimeError("Shopee SKU 映射未进入商品管理页，请确认登录状态")

        # 两个地区分别导出，保留第一份表头拼接其它地区的数据
        matrices = []
        for region, shop_id in REGION_SHOPS:
            browser.find_by_xpath(
                "//div[contains(@class,'eds-selector--label')][.//div[contains(@class,'eds-selector__label--text') and contains(.,'仓库所在地区')]]",
                timeout=15,
            ).click(delay_after=0.2)
            browser.find_by_xpath(
                f"//div[contains(@class,'eds-select__options')]//div[contains(@class,'eds-option') and normalize-space()='{region}']",
                timeout=10,
            ).click(delay_after=0.3)

            # 下拉显示的地区和 URL 中的店铺 ID 都更新，才算切换成功
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                region_labels = browser.find_all_by_xpath(
                    "//div[contains(@class,'eds-selector--label')][.//div[contains(@class,'eds-selector__label--text') and contains(.,'仓库所在地区')]]/div[contains(@class,'eds-selector__inner')]",
                    timeout=1,
                )
                if region_labels and clean_text(region_labels[0].get_text()) == region and f"cnsc_shop_id={shop_id}" in browser.get_url():
                    browser.find_by_xpath(
                        "//div[contains(@class,'eds-tabs__nav-tab') and contains(.,'已批准')]",
                        timeout=15,
                    )
                    break
                time.sleep(1)
            else:
                raise RuntimeError(f"Shopee 仓库地区切换失败：{region}，当前网址 {browser.get_url()}")

            # 导出前记录当前地区任务，避免本轮时间窗口内误下载历史任务
            browser.find_by_xpath(
                "//span[contains(@class,'task-center-text') and normalize-space()='任务中心']",
                timeout=15,
            ).click(delay_after=0.2)
            browser.find_by_xpath(
                "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//div[contains(@class,'eds-tabs__nav-tab')][normalize-space()='商品管理']",
                timeout=10,
            ).click(delay_after=0.2)
            tasks = []
            for row in browser.find_all_by_xpath(
                "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//tr[contains(@class,'eds-table__row')]",
                timeout=1,
            ):
                cells = row.find_all_by_xpath("./td", timeout=1)
                if len(cells) < 4:
                    continue
                name = clean_text(cells[0].get_text())
                match = TASK_TIME.search(clean_text(cells[1].get_text()))
                if not name.startswith("FBS_Products_") or not name.endswith(".xlsx") or not match:
                    continue
                tasks.append({
                    "name": name,
                    "submitted_at": datetime.strptime(match.group(), "%Y-%m-%d %H:%M:%S"),
                    "status": clean_text(cells[2].get_text()),
                    "row": row,
                })
            existing = {(task["name"], task["submitted_at"]) for task in tasks}
            browser.find_by_xpath(
                "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//i[contains(@class,'eds-modal__close')]",
                timeout=10,
            ).click(delay_after=0.2)

            # 从商品管理“已批准”页面导出全部商品
            browser.find_by_xpath(
                "//button[.//span[normalize-space()='导出']]",
                timeout=15,
            ).click(delay_after=0.2)
            started_at = datetime.now()
            browser.find_by_xpath(
                "//li[@role='menuitem' and contains(.,'导出全部') and @aria-disabled='false']",
                timeout=10,
            ).click(delay_after=0.2)

            # 任务中心“商品管理”中按提交时间和新增记录识别本轮任务
            browser.find_by_xpath(
                "//span[contains(@class,'task-center-text') and normalize-space()='任务中心']",
                timeout=15,
            ).click(delay_after=0.2)
            browser.find_by_xpath(
                "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//div[contains(@class,'eds-tabs__nav-tab')][normalize-space()='商品管理']",
                timeout=10,
            ).click(delay_after=0.2)
            deadline = time.monotonic() + 180
            selected = None
            while time.monotonic() < deadline:
                tasks = []
                for row in browser.find_all_by_xpath(
                    "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//tr[contains(@class,'eds-table__row')]",
                    timeout=1,
                ):
                    cells = row.find_all_by_xpath("./td", timeout=1)
                    if len(cells) < 4:
                        continue
                    name = clean_text(cells[0].get_text())
                    match = TASK_TIME.search(clean_text(cells[1].get_text()))
                    if not name.startswith("FBS_Products_") or not name.endswith(".xlsx") or not match:
                        continue
                    tasks.append({
                        "name": name,
                        "submitted_at": datetime.strptime(match.group(), "%Y-%m-%d %H:%M:%S"),
                        "status": clean_text(cells[2].get_text()),
                        "row": row,
                    })
                candidates = [
                    task for task in tasks
                    if (task["name"], task["submitted_at"]) not in existing
                    and task["submitted_at"] >= started_at - timedelta(seconds=5)
                ]
                if len(candidates) > 1:
                    raise RuntimeError(f"Shopee {region} 同时发现多个新导出任务，无法安全识别本轮下载")
                if candidates:
                    selected = candidates[0]
                    if "失败" in selected["status"]:
                        raise RuntimeError(f"Shopee {region} 商品导出失败：{selected['name']}")
                    if selected["status"] == "成功":
                        break

                # 重新切换任务分类使异步导出列表刷新，不根据历史成功行下载
                browser.find_by_xpath(
                    "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//div[contains(@class,'eds-tabs__nav-tab')][normalize-space()='概览']",
                    timeout=5,
                ).click(delay_after=0.1)
                browser.find_by_xpath(
                    "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//div[contains(@class,'eds-tabs__nav-tab')][normalize-space()='商品管理']",
                    timeout=5,
                ).click(delay_after=0.1)
                time.sleep(2)
            if selected is None or selected["status"] != "成功":
                raise RuntimeError(f"Shopee {region} 等待本轮商品导出成功超时")

            # 在精确任务行内下载，匹配文件名确保拿到本轮文件
            start_time = time.time()
            selected["row"].find_by_xpath(".//button[contains(@class,'download')]", timeout=10).click(delay_after=0.2)
            # 增强工具2026 wait_download_file：filename_pattern=任务文件名 glob；
            # download_dir=当前用户下载目录；timeout=下载等待上限；start_time=点击前的时间。
            downloaded = wait_download_file(
                download_dir=str(Path.home() / "Downloads"),
                filename_pattern=Path(selected["name"]).stem + "*.xlsx",
                timeout=120,
                start_time=start_time,
            )
            logging.info(f"[{SHEET_NAME}] {region} 导出完成：{selected['name']}，提交时间 {selected['submitted_at']:%Y-%m-%d %H:%M:%S}")
            browser.find_by_xpath(
                "//div[contains(concat(' ',normalize-space(@class),' '),' eds-modal ')][.//div[contains(@class,'eds-modal__title') and normalize-space()='任务中心']]//i[contains(@class,'eds-modal__close')]",
                timeout=10,
            ).click(delay_after=0.2)

            data = load_excel_matrix(downloaded)
            if not any(clean_text(row[4]) for row in data[1:]):
                raise RuntimeError(f"Shopee {region} SKU 映射导出没有有效数据行")
            matrices.append(data)

        # 两地区表头一致才可拼接，避免列错位
        if [clean_text(v) for v in matrices[0][0]] != [clean_text(v) for v in matrices[1][0]]:
            raise RuntimeError("Shopee 两个地区商品导出表头不同，停止拼接")
        return {"data": matrices[0] + matrices[1][1:]}
    finally:
        if browser is not None:
            browser.close()


def apply_update(workbook, payload):
    """
    更新 Shopee SKU 映射原始区。

    :param workbook: 已打开的目标工作簿
    :param payload: ``prepare`` 返回的数据
    :return: 写入结果描述文本
    """
    return replace_raw_area(workbook, SHEET_NAME, payload["data"], RAW_LAYOUT)
