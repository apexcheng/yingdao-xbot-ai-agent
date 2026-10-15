"""下载【基源】全域投放的推商品、分日、近 30 天报表。"""

import time

from xbot import web
from xbot.app import logging

from .config import DOWNLOAD_DIR, DOUYIN_PROFILE
from .utils import open_source_workbook, replace_fact_area


def download():
    web.set_user_environment(mode="chrome", profile_name=DOUYIN_PROFILE)
    page = web.create("https://qianchuan.jinritemai.com/dataV2/bidding/site-promotion?aavid=EXAMPLE_ACCOUNT_ID", "chrome", load_timeout=20)
    page.wait_load_completed(timeout=20)
    time.sleep(2)

    page.find_by_xpath("//div[@class='ovui-tabs__nav']//div[@data-auto-id='oc-new-badge'][text()='推商品']", timeout=5).click(delay_after=0.3)
    page.find_by_xpath("//div[@class='header-right-container']//div[@class='ovui-input__after']").click(delay_after=0.3)
    page.find_by_xpath("//span[@class='oc-typography-value-int'][text()='分日']").click(delay_after=0.3)
    page.find_by_xpath("//input[@class='ovui-input'][@placeholder='开始日期']").click(delay_after=0.3)
    page.find_by_xpath("//div[@class='ovui-shortcut oc-range-picker-shortcut-item'][contains(., '30天')]", timeout=20).click(delay_after=0.3)
    time.sleep(3)

    file_path = page.find_by_xpath("//button[contains(@class, 'ovui-button--fill')]//iconpark-icon[contains(@name, 'download')]").download(file_folder=DOWNLOAD_DIR, wait_complete=True, wait_complete_timeout=120)
    logging.info(f"【【基源】全域投放】下载完成｜文件={file_path}")
    page.close()

    return open_source_workbook(file_path)


def update(target_workbook):
    source_workbook = download()
    replace_fact_area(target_workbook, source_workbook, "【基源】全域投放")
    return True
