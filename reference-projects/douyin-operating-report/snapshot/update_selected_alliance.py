"""下载精选联盟佣金订单明细并更新达人佣金事实层。"""

import datetime
import json
import time

from xbot import web
from xbot.app import logging
from xbot_extensions.xbot_enhance_tools.browser_utils import wait_appear_by_xpath

from .config import DOWNLOAD_DIR, DOUYIN_PROFILE
from .utils import open_source_workbook, replace_fact_area, select_date_range


def download():
    web.set_user_environment(mode="chrome", profile_name=DOUYIN_PROFILE)
    page = web.create("https://buyin.jinritemai.com/dashboard/data/financial/list", "chrome", load_timeout=20)
    page.wait_load_completed(timeout=20)
    time.sleep(2)

    page.find_by_xpath("//div[@class='auxo-tabs-nav-wrap']//div[@class='auxo-tabs-tab-btn'][contains(., '联盟订单')]", timeout=5).click(delay_after=0.2)
    page.find_by_xpath("//div[contains(@class, 'form-content')]//div[contains(@class, 'label-wrapper')]//span[contains(text(),'付款时间')]", timeout=5).click(delay_after=0.2)
    page.find_by_xpath("//div[@title='付款时间']/div[@class='auxo-select-item-option-content']", timeout=5).click(delay_after=0.2)
    time.sleep(2)
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=30)
    actual_start, actual_end = select_date_range(page, start_date, end_date, "开始日期", "结束日期")
    logging.info(f"【达人佣金】付款时间筛选完成｜{actual_start}～{actual_end}")
    page.find_by_xpath("//div[contains(@class, 'button')]//button[contains(., '导出数据')]", timeout=5).click(delay_after=0.2)
    export_time = datetime.datetime.now().replace(microsecond=0)
    page.find_by_xpath("//div[@class='auxo-modal-confirm-btns']/button[contains(., '导出')]", timeout=5).click(delay_after=0.2)
    time.sleep(5)
    page.reload(ignore_cache=True, load_timeout=20)
    page.wait_load_completed(timeout=20)
    time.sleep(2)

    task_time = None
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        records = json.loads(page.execute_javascript("""
            function () {
                return JSON.stringify(Array.from(document.querySelectorAll('div.export-list-item')).map(function (card) {
                    return {
                        type: card.querySelector('.export-list-item-header-title > span').textContent.trim(),
                        time: card.querySelector('.export-list-item-header-time').textContent.trim()
                    };
                }));
            }
        """))
        if task_time is None:
            candidates = [record for record in records if record["type"] == "佣金订单明细导出" and datetime.datetime.strptime(record["time"].removeprefix("导出时间：").strip(), "%Y-%m-%d %H:%M:%S") >= export_time]
        else:
            candidates = [record for record in records if record["type"] == "佣金订单明细导出" and record["time"] == task_time]
        if len(candidates) > 1:
            raise RuntimeError("达人佣金：本轮导出任务不唯一，停止下载")
        if candidates:
            task_time = candidates[0]["time"]
            download_xpath = f"//div[@class='export-list-item'][.//div[@class='export-list-item-header-title']/span[normalize-space(.)='佣金订单明细导出'] and .//div[@class='export-list-item-header-time'][normalize-space(.)='{task_time}']]//button[contains(., '下载')]"
            # 等待本轮佣金报表按钮；page 为当前页面，xpath 绑定导出类型与时间，timeout 为单轮等待秒数。
            if wait_appear_by_xpath(page, download_xpath, timeout=5):
                break
        page.reload(ignore_cache=True, load_timeout=20)
        page.wait_load_completed(timeout=20)
        time.sleep(2)
    else:
        raise TimeoutError("达人佣金：120秒内本轮报表未生成")

    file_path = page.find_by_xpath(download_xpath, timeout=5).download(file_folder=DOWNLOAD_DIR, wait_complete=True, wait_complete_timeout=120)
    logging.info(f"【达人佣金】下载完成｜{task_time}｜文件={file_path}")
    page.close()
    return open_source_workbook(file_path)


def update(target_workbook):
    source_workbook = download()
    replace_fact_area(target_workbook, source_workbook, "【基源】达人佣金")
    return True
