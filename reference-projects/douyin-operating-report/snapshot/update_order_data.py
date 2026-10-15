"""导出抖店标准订单报表，获取短信密码并更新【基源】平台订单明细。"""

import datetime
import json
from pathlib import Path
import time
import zipfile

from xbot import web, win32
from xbot.app import logging
from xbot_extensions.xbot_enhance_tools.browser_utils import wait_appear_by_xpath, wait_download_file
import pyzipper

from .config import DOWNLOAD_DIR, DOUYIN_PROFILE
from .utils import fetch_ntfy_code, open_source_workbook, replace_fact_area, select_date_range


def download():
    web.set_user_environment(mode="chrome", profile_name=DOUYIN_PROFILE)
    page = web.create("https://fxg.jinritemai.com/ffa/morder/order/list", "chrome", load_timeout=20)
    page.wait_load_completed(timeout=20)
    time.sleep(2)

    win32.mouse_wheel('down',2,delay_after=0.2)
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=30)
    if page.find_all_by_xpath("//button[.//span[starts-with(normalize-space(.), '展开')]]", timeout=1):
        page.find_by_xpath("//button[.//span[starts-with(normalize-space(.), '展开')]]", timeout=5).click(delay_after=0.2)
    actual_start, actual_end = select_date_range(page, start_date, end_date, "开始范围", "结束范围")
    logging.info(f"【【基源】平台订单明细】下单时间筛选完成｜{actual_start}～{actual_end}")

    page.find_by_xpath("//div[@id='search-form-container']//button[contains(., '导出')]", timeout=5).click(delay_after=0.2)
    page.find_by_xpath("//div[contains(@class, 'dropdown')]//ul/li[contains(., '导出订单')]", timeout=5).click(delay_after=0.2)
    page.find_by_xpath("//div[contains(@class, 'drawer-body')]//div/span[contains(text(), '标准报表')]", timeout=5).click(delay_after=0.2)
    page.find_by_xpath("//div[contains(@class, 'drawer-content-footer')]//button[contains(., '导出')]", timeout=5).click(delay_after=0.2)
    export_time = datetime.datetime.now().replace(microsecond=0)
    page.find_by_xpath("//div[contains(@class, 'modal-body')]//button[contains(., '确认')]", timeout=5).click(delay_after=0.2)
    page = web.get_active(mode="chrome", load_timeout=20)
    page.wait_load_completed(timeout=20)
    time.sleep(2)

    report_id = None
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        # 从用户提供的 DOM 读取普通数据；每轮重新定位，避免页面刷新后继续使用失效元素。
        records = json.loads(page.execute_javascript("""
            function () {
                return JSON.stringify(Array.from(document.querySelectorAll('div[class*="ListWithPagination"] div[class*="RecordCard"]')).map(function (card) {
                    const header = card.querySelector('div[class*="header"]');
                    return {
                        id: header.querySelector('.auxo-col-7 div[data-foobar] span').textContent.trim(),
                        time: header.querySelector('.auxo-col-8 > span:last-child').textContent.trim(),
                        type: header.querySelector(':scope > span').textContent.trim()
                    };
                }));
            }
        """))
        if report_id is None:
            candidates = [record for record in records if record["type"] == "标准报表" and datetime.datetime.strptime(record["time"], "%Y/%m/%d %H:%M:%S") >= export_time]
        else:
            candidates = [record for record in records if record["id"] == report_id]
        if len(candidates) > 1:
            raise RuntimeError("【基源】平台订单明细：本轮导出任务不唯一，停止下载")
        if candidates:
            report_id = candidates[0]["id"]
            download_xpath = f"//div[contains(@class, 'ListWithPagination')]//div[contains(@class, 'RecordCard')][.//span[normalize-space(.)='报表ID']/following-sibling::div//span[normalize-space(.)='{report_id}']]//button[contains(., '下载报表')]"
            # 等待本轮报表的下载按钮；page 为当前页面，xpath 为指定报表 ID 的按钮，timeout 为单轮等待秒数。
            if wait_appear_by_xpath(page, download_xpath, timeout=5):
                break
        page.reload(load_timeout=20)
        page.wait_load_completed(timeout=20)
        time.sleep(2)
    else:
        raise TimeoutError("【基源】平台订单明细：300秒内本轮报表未生成")

    logging.info(f"【【基源】平台订单明细】本轮报表已生成｜报表ID={report_id}")
    download_started = time.time()
    page.find_by_xpath(download_xpath, timeout=5).click(delay_after=0.2)
    # 检查下载验证码弹窗；page 为当前页面，xpath 为获取验证码入口，timeout 为检查秒数。
    if wait_appear_by_xpath(page, "//div[@class='auxo-modal']//span[contains(text(), '获取验证码')]", timeout=3):
        page.find_by_xpath("//div[@class='auxo-modal']//span[contains(text(), '获取验证码')]", timeout=5).click(delay_after=0.2)
        verification_code = fetch_ntfy_code("verification", int(download_started))
        page.find_by_xpath("//div[@class='auxo-modal']//span[contains(@class, 'sp-input')]//input", timeout=5).input(verification_code)
        time.sleep(3)
        page.find_by_xpath("//div[@class='auxo-modal']//button[contains(., '确定')]", timeout=5).click(delay_after=0.2)

    # 等待本次点击产生的下载完成；download_dir 为目录，timeout 为上限秒数，start_time 为点击前的时间戳。
    zip_path = wait_download_file(download_dir=DOWNLOAD_DIR, timeout=180, start_time=download_started)
    logging.info(f"【【基源】平台订单明细】下载完成｜文件={zip_path}")
    page.close()

    unzip_password = fetch_ntfy_code("password", int(download_started))
    extract_dir = Path(DOWNLOAD_DIR) / f"order_data_{time.time_ns()}"
    extract_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_dir, pwd=unzip_password.encode("utf-8"))
    except (NotImplementedError, RuntimeError, zipfile.BadZipFile) as error:
        logging.warning(f"【【基源】平台订单明细】标准库解压失败，使用 pyzipper｜原因={error}")
        with pyzipper.AESZipFile(zip_path) as archive:
            archive.extractall(extract_dir, pwd=unzip_password.encode("utf-8"))

    source_files = [path for path in extract_dir.iterdir() if path.is_file() and path.suffix.lower() in (".xlsx", ".xls", ".xlsm", ".csv")]
    if len(source_files) != 1:
        raise RuntimeError(f"【基源】平台订单明细：解压后应有一个表格文件，实际找到{len(source_files)}个｜目录={extract_dir}")
    return open_source_workbook(source_files[0])


def update(target_workbook):
    source_workbook = download()
    replace_fact_area(target_workbook, source_workbook, "【基源】平台订单明细")
    return True
