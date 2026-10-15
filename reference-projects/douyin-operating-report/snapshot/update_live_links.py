"""按日补齐直播链接数据，合并后追加到固定 J:AC 事实层。"""

import datetime
from pathlib import Path
import re
import time

from xbot import web
from xbot.app import logging
from xbot_extensions.xbot_enhance_tools.browser_utils import wait_download_file

from .config import DOWNLOAD_DIR, DOUYIN_PROFILE, FACT_AREAS, LIVE_LINK_DOWNLOAD_TIMEOUT
from .utils import open_source_workbook


def to_date(value):
    """读取 WPS 日期对象、Excel 日期序列号或常见字符串日期。"""
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, (int, float)):
        return (datetime.datetime(1899, 12, 30) + datetime.timedelta(days=value)).date()
    date_text = str(value).strip().split()[0].split("T")[0]
    date_text = date_text.replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-").replace(".", "-")
    date_format = "%Y%m%d" if len(date_text) == 8 and date_text.isdigit() else "%Y-%m-%d"
    return datetime.datetime.strptime(date_text, date_format).date()


def download(target_date):
    """用 DOM 选择自然日和直播渠道，等待两秒后下载当前明细。"""
    web.set_user_environment(mode="chrome", profile_name=DOUYIN_PROFILE)
    page = web.create("https://compass.jinritemai.com/shop/commodity/product-list", "chrome", load_timeout=20)
    page.wait_load_completed(timeout=20)
    time.sleep(2)
    page.find_by_xpath("//*[@id='rc-tabs-2-tab-day']", timeout=20).click(delay_after=0.2)

    while True:
        calendar_year = int(re.search(r"\d+", page.find_by_xpath("//button[@aria-label='选择年份']", timeout=20).get_text()).group())
        calendar_month = int(re.search(r"\d+", page.find_by_xpath("//button[@aria-label='选择月份']", timeout=20).get_text()).group())
        if (calendar_year, calendar_month) == (target_date.year, target_date.month):
            break
        if (calendar_year, calendar_month) > (target_date.year, target_date.month):
            page.find_by_xpath("//button[contains(@class, 'aurora-picker-header-prev-btn')]", timeout=20).click(delay_after=0.3)
        else:
            page.find_by_xpath("//button[contains(@class, 'aurora-picker-header-next-btn')]", timeout=20).click(delay_after=0.3)

    date_text = target_date.strftime("%Y-%m-%d")
    page.find_by_xpath(f"//td[@title='{date_text}' and not(contains(@class, 'disabled'))]", timeout=20).click(delay_after=0.2)
    page.find_by_xpath(f"//div[contains(@class, 'aurora-dorami-date-picker-picker-display')]/span[normalize-space()='{date_text}']", timeout=20)
    page.find_by_xpath("//label[contains(@class, 'aurora-radio-button-wrapper')][.//span[normalize-space()='直播']]", timeout=20).click(button='right', simulative=True, delay_after=0.2, anchor=('middleLeft', -500,0))
    page.find_by_xpath("//label[contains(@class, 'aurora-radio-button-wrapper')][.//span[normalize-space()='直播']]", timeout=2).click(delay_after=0.2)
    page.find_by_xpath("//label[contains(@class, 'aurora-radio-button-wrapper')][.//span[normalize-space()='直播']][contains(@class, 'aurora-radio-button-wrapper-checked')]", timeout=20)
    # 用户确认：切换直播后固定等待两秒，不监听请求，也不判断商品列表空数据状态。
    time.sleep(2)

    page.find_by_xpath("//button[contains(., '下载明细')]", timeout=20).click(delay_after=0.2)
    download_started = time.time()
    page.find_by_xpath("//li[@role='menuitem'][.//span[normalize-space()='下载当前明细']]", timeout=20).click(delay_after=0.2)
    # 等待本次点击产生的新文件；download_dir 为目录，timeout 为下载上限秒数，start_time 为点击前时间戳。
    file_path = wait_download_file(download_dir=DOWNLOAD_DIR, timeout=LIVE_LINK_DOWNLOAD_TIMEOUT, start_time=download_started)
    if Path(file_path).stat().st_size == 0:
        raise RuntimeError(f"【基源】直播链接数据：{date_text}下载文件为空｜文件={file_path}")
    logging.info(f"【【基源】直播链接数据】逐日下载完成｜日期={date_text}｜文件={file_path}")
    page.close()
    return open_source_workbook(file_path)


def update(target_workbook):
    target_sheet = target_workbook.get_sheet_by_name("【基源】直播链接数据")
    begin_column, _, source_end_column, _ = FACT_AREAS["【基源】直播链接数据"]
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    start_date = today - datetime.timedelta(days=30)
    last_data_row = 1
    last_used_row = target_sheet.get_first_free_row() - 1
    if last_used_row >= 2:
        date_rows = target_sheet.get_range(2, begin_column, last_used_row, begin_column)
        for index in range(len(date_rows) - 1, -1, -1):
            value = date_rows[index][0]
            if value is not None and value != "":
                last_data_row = index + 2
                start_date = to_date(value) + datetime.timedelta(days=1)
                break

    if start_date > yesterday:
        logging.info(f"【【基源】直播链接数据】已更新到昨天或更晚，无需补下载")
        return True

    logging.info(f"【【基源】直播链接数据】开始补齐｜日期={start_date}～{yesterday}｜天数={(yesterday - start_date).days + 1}")
    appended_rows = []
    target_date = start_date
    while target_date <= yesterday:
        source_workbook = download(target_date)
        source_sheet = source_workbook.get_sheet_by_index(1)
        source_rows = source_sheet.get_range(1, "A", source_sheet.get_first_free_row() - 1, source_end_column)
        appended_rows.extend(source_rows[1:])
        target_date += datetime.timedelta(days=1)

    # 全部缺失日期下载、读取完成后一次追加；下载失败时目标数据不变，下一次尝试重新补整个区间。
    if appended_rows:
        target_sheet.set_range(last_data_row + 1, begin_column, appended_rows)
    logging.info(f"【【基源】直播链接数据】补齐完成｜新增行数={len(appended_rows)}｜固定区域=J:AC")
    return True
