"""各数据源共用的事实层写入及订单短信读取。"""

import datetime
import re
import time

from xbot import excel, win32
from xbot.app import logging
from xbot_extensions.xbot_enhance_tools.ntfy_message import receive_ntfy_message

from .config import FACT_AREAS, NTFY_SERVER, NTFY_TOPIC


def parse_datetime(value):
    """解析常见日期时间值；忽略时区标记但保留原始时钟时间。"""
    if isinstance(value, datetime.datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, datetime.date):
        return datetime.datetime.combine(value, datetime.time())
    if not isinstance(value, str) or not value.strip():
        return None

    value = value.strip()
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"
    try:
        return datetime.datetime.fromisoformat(value).replace(tzinfo=None)
    except ValueError:
        for date_format in (
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d",
        ):
            try:
                return datetime.datetime.strptime(value, date_format)
            except ValueError:
                continue
    return None


def _read_displayed_calendar_months(page):
    calendar_years = page.find_all_by_xpath("//button[contains(@class, 'auxo-picker-year-btn')]", timeout=5)
    calendar_months = page.find_all_by_xpath("//button[contains(@class, 'auxo-picker-month-btn')]", timeout=5)
    if len(calendar_years) != len(calendar_months):
        raise RuntimeError("日期选择器年月显示数量不一致")
    displayed_months = [
        (int(re.search(r"\d{4}", year.get_text()).group()), int(re.search(r"\d{1,2}", month.get_text()).group()))
        for year, month in zip(calendar_years, calendar_months)
    ]
    if not displayed_months:
        raise RuntimeError("未读取到日期选择器当前年月")
    return displayed_months


def _select_calendar_date(page, target_date):
    target_month = (target_date.year, target_date.month)
    while True:
        displayed_months = _read_displayed_calendar_months(page)
        if target_month < min(displayed_months):
            previous_months = displayed_months
            page.find_by_xpath("//button[contains(@class, 'auxo-picker-header-prev-btn') and not(contains(@style, 'hidden'))]", timeout=5).click(delay_after=0.2)
        elif target_month > max(displayed_months):
            previous_months = displayed_months
            page.find_by_xpath("//button[contains(@class, 'auxo-picker-header-next-btn') and not(contains(@style, 'hidden'))]", timeout=5).click(delay_after=0.2)
        else:
            break

        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if _read_displayed_calendar_months(page) != previous_months:
                break
            time.sleep(0.2)
        else:
            raise TimeoutError("日期选择器切换月份后年月未更新")

    page.find_by_xpath(
        f"//td[@title='{target_date:%Y-%m-%d}' and contains(@class, 'auxo-picker-cell-in-view') and not(contains(@class, 'auxo-picker-cell-disabled'))]",
        timeout=5,
    ).click(delay_after=0.2)


def select_date_range(page, start_date, end_date, start_placeholder, end_placeholder):
    """通过双月日历设置并验证完整自然日日期范围。"""
    if start_date > end_date:
        raise ValueError(f"开始日期晚于结束日期｜{start_date} > {end_date}")

    page.find_by_xpath(
        f"//div[contains(@class, 'sp-range-picker-join')]//input[@placeholder='{start_placeholder}']",
        timeout=5,
    ).click(delay_after=0.2)
    _select_calendar_date(page, start_date)
    _select_calendar_date(page, end_date)
    page.find_by_xpath("//button[contains(@class, 'sp-picker-range-ok-btn')][.//span[normalize-space()='确定']]", timeout=5).click(delay_after=0.2)

    actual_start = datetime.datetime.strptime(
        page.find_by_xpath(
            f"//div[contains(@class, 'sp-range-picker-join')]//input[@placeholder='{start_placeholder}']",
            timeout=5,
        ).get_value(),
        "%Y/%m/%d %H:%M:%S",
    )
    actual_end = datetime.datetime.strptime(
        page.find_by_xpath(
            f"//div[contains(@class, 'sp-range-picker-join')]//input[@placeholder='{end_placeholder}']",
            timeout=5,
        ).get_value(),
        "%Y/%m/%d %H:%M:%S",
    )
    if actual_start != datetime.datetime.combine(start_date, datetime.time.min):
        raise RuntimeError(f"日期开始时间校验失败｜预期={start_date:%Y/%m/%d} 00:00:00｜实际={actual_start}")
    if actual_end != datetime.datetime.combine(end_date, datetime.time(23, 59, 59)):
        raise RuntimeError(f"日期结束时间校验失败｜预期={end_date:%Y/%m/%d} 23:59:59｜实际={actual_end}")
    return actual_start, actual_end


def open_source_workbook(file_path):
    source_workbook = excel.open(file_name=str(file_path), kind="wps", visible=True, update_links=False)
    source_workbook.workbook.Activate()
    source_workbook.workbook.Application.WindowState = -4137
    return source_workbook


def replace_fact_area(target_workbook, source_workbook, sheet_name):
    """按固定列覆盖事实层；订单列索引从 0 开始，其它数据保持原类型。"""
    begin_column, end_column, source_end_column, order_column_indexes = FACT_AREAS[sheet_name]
    target_sheet = target_workbook.get_sheet_by_name(sheet_name)
    target_sheet.clear_range(1, begin_column, target_sheet.get_first_free_row() - 1, end_column, target="content")

    source_sheet = source_workbook.get_sheet_by_index(1)
    source_rows = source_sheet.get_range(1, "A", source_sheet.get_first_free_row() - 1, source_end_column)
    for row in source_rows[1:]:
        for index in order_column_indexes:
            value = row[index]
            if value is not None and value != "":
                row[index] = "'" + (str(int(value)) if isinstance(value, float) and value.is_integer() else str(value))
    target_sheet.set_range(1, begin_column, source_rows)
    logging.info(f"【{sheet_name}】事实层写入完成｜区域={begin_column}:{end_column}｜数据行数={len(source_rows) - 1}")


def fetch_ntfy_code(code_kind, after_time):
    """在约定的五分钟内提取本次下载之后的验证码或解压密码。"""
    pattern = re.compile(r"【抖店】验证码(\d{4})" if code_kind == "verification" else r"【抖音商城】订单导出文件已加密，解压密码为(\S+?)，")
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        # 拉取短信缓存；topic 为短信主题，server 为 ntfy 地址，timeout 为单次请求超时秒数。
        messages = receive_ntfy_message(topic=NTFY_TOPIC, server=NTFY_SERVER, timeout=15)
        for message in messages:
            if message["time"] < after_time:
                continue
            match = pattern.search(message["message"])
            if match:
                logging.info(f"【【基源】平台订单明细】短信提取成功｜类型={code_kind}")
                return match.group(1)
        time.sleep(3)
    raise TimeoutError(f"【基源】平台订单明细：300秒内未收到{code_kind}短信")
