"""下载千川多账户抖音号明细，全部读取合并后覆盖达人投流事实层。"""

import datetime
from pathlib import Path
import re
import time

from xbot import web
from xbot.app import logging
from xbot_extensions.ad_killer import close_ads
from xbot_extensions.xbot_enhance_tools.browser_utils import wait_download_file
from xbot_extensions.ad_killer import close_ads_win

from . import package
from .config import DOWNLOAD_DIR, DOUYIN_PROFILE, FACT_AREAS, INFLUENCER_DISABLED_ACCOUNT_IDS
from .utils import open_source_workbook



def download():
    """每次尝试按账户 ID 遍历，返回本轮下载文件和账户汇总；失败直接传播。"""
    web.set_user_environment(mode="chrome", profile_name=DOUYIN_PROFILE)
    page = web.create("https://qianchuan.jinritemai.com/home?aavid=EXAMPLE_ACCOUNT_ID", "chrome", load_timeout=20)
    page.wait_load_completed(timeout=20)
    time.sleep(3)
    # 广告杀手使用自定义关闭按钮 XPath；使用 click 点击匹配的广告关闭元素，不启用内置 XPath。
    close_ads(page, "//*[contains(@class, 'close-button')]|//div[contains(@class, 'close-icon')]|//*[@class='close']", False, "click")
    close_ads(page, "//popup-shell[contains(@id, 'popup-shell')]", False, "hidden")

    page.find_by_xpath("//div[contains(@class, 'account-info-container')]", timeout=5).click(button='right', delay_after=0.2, anchor=('middleLeft', -600, 0))
    page.find_by_xpath("//div[contains(@class, 'account-info-container')]", timeout=5).hover()
    page.find_by_xpath("//div[contains(@class, 'checkout-account')][normalize-space()='切换']", timeout=20).click(delay_after=0.2)

    accounts = {}
    for account_id_element in page.find_all_by_xpath("//div[contains(@class, 'account-id')]", timeout=5):
        account_id = re.search(r"\d+", account_id_element.get_text()).group()
        account_item = account_id_element.find_by_xpath("ancestor::div[contains(@class, 'qc-ui-navigator-account-item')][1]", timeout=5)
        account_name = account_item.find_by_xpath(".//div[contains(@class, 'account-name')]", timeout=5).get_text().strip()
        if account_id not in accounts:
            accounts[account_id] = account_name
    if not accounts:
        raise RuntimeError("达人投流：未读取到账户列表")

    downloaded_files = []
    account_results = []
    empty_count = 0
    disabled_count = 0
    for account_id, account_name in accounts.items():
        if account_id in INFLUENCER_DISABLED_ACCOUNT_IDS:
            disabled_count += 1
            account_results.append(f"{account_name}（{account_id}）｜已停用跳过｜日期与数据未查询")
            continue
        # 广告杀手后台监测 Win32 弹窗；参数为 Selector 对象列表，通过元素库名称获取 Selector，检测到“chrome最近下载列表”时自动关闭。
        close_ads_win([package.selector("chrome最近下载列表")])

        date_range = "未确认"
        failure_status = "页面异常"
        try:
            page.navigate(f"https://qianchuan.jinritemai.com/home?aavid={account_id}", load_timeout=20)
            page.wait_load_completed(timeout=20)
            time.sleep(2)
            # 广告杀手使用自定义关闭按钮 XPath；使用 click 点击匹配的广告关闭元素，不启用内置 XPath。
            close_ads(page, "//*[contains(@class, 'close-button')]|//div[contains(@class, 'close-icon')]|//*[@class='close']", False, "click")
            close_ads(page, "//popup-shell[contains(@id, 'popup-shell')]", False, "hidden")
            page.find_by_xpath(f"//div[contains(@class, 'account-info-container')]//div[@title='{account_id}']", timeout=5)

            page.find_by_xpath("//*[@id='firstTitle_data']", timeout=5).click(delay_after=0.2)
            page.find_by_xpath("//span[contains(@class, 'ocean-vmok-plugin-oc-typography-value-slot')][normalize-space()='乘方数据']", timeout=5).click(delay_after=0.2)
            page = web.get_active(mode="chrome", load_timeout=20)
            page.wait_load_completed(timeout=20)
            time.sleep(2)
            # 广告杀手使用自定义关闭按钮 XPath；使用 click 点击匹配的广告关闭元素，不启用内置 XPath。
            close_ads(page, "//div[contains(@class, 'launcher_popupSlot')]", False, "hidden")

            page.find_by_xpath("//div[contains(concat(' ', normalize-space(@class), ' '), ' ovui-tabs__tab ')][.//*[normalize-space()='抖音号数据明细']]", timeout=5).click(delay_after=0.2)
            page.find_by_xpath("//div[contains(@class, 'ovui-tabs__tab--active')][.//*[normalize-space()='抖音号数据明细']]", timeout=5)

            page.find_by_xpath("//div[@data-auto-id='oc-select' and not(contains(@class, 'report-shortcuts-datepicker-prefix-selection'))]//div[contains(@class, 'ovui-select--fill')]", timeout=5).click(delay_after=0.2)
            page.find_by_xpath("//div[contains(concat(' ', normalize-space(@class), ' '), ' ovui-option ')][.//span[normalize-space()='整体数据']]", timeout=5).click(delay_after=0.2)
            data_type = page.find_by_xpath("//div[contains(@class, 'date')]//div[@data-auto-id='oc-select' and not(contains(@class, 'report-shortcuts-datepicker-prefix-selection'))]//input", timeout=5).get_value()
            if data_type != "整体数据":
                raise RuntimeError(f"数据类型未切换为整体数据，实际为{data_type}")

            page.find_by_xpath("//input[@placeholder='开始日期']", timeout=5).click(delay_after=0.2)
            page.find_by_xpath("//div[contains(@class, 'oc-range-picker-shortcut-item')][normalize-space()='最近30天']", timeout=5).click(delay_after=0.2)
            start_date = datetime.date.fromisoformat(page.find_by_xpath("//input[@placeholder='开始日期']", timeout=5).get_value())
            end_date = datetime.date.fromisoformat(page.find_by_xpath("//input[@placeholder='结束日期']", timeout=5).get_value())
            date_range = f"{start_date}～{end_date}"
            today = datetime.date.today()
            if (start_date, end_date) != (today - datetime.timedelta(days=29), today):
                raise RuntimeError(f"日期范围未更新为最近30天，实际为{date_range}")
            # 用户确认：选好整体数据与最近30天后固定等三秒，再判断有无数据，不监听请求。
            time.sleep(3)

            empty_elements = page.find_all_by_xpath("//div[@data-auto-id='oc-empty' and contains(@data-e2e, 'ocTable')]//span[normalize-space()='暂无数据']", timeout=1)
            if any(element.is_displayed() for element in empty_elements):
                empty_count += 1
                account_results.append(f"{account_name}（{account_id}）｜无数据跳过｜日期={date_range}｜有数据=否｜下载=否")
                continue
            data_rows = page.find_all_by_xpath("//table[contains(@class, 'ovui-table')]//tbody/tr[td]", timeout=1)
            if not any(row.is_displayed() for row in data_rows):
                raise RuntimeError("等待三秒后既无可见数据行，也未显示暂无数据，无法确认明细状态")

            failure_status = "下载失败"
            download_started = time.time()
            page.find_by_xpath("//div[contains(@class, 'download-btn')]//button[.//iconpark-icon[@name='oc-icon-download']]", timeout=5).click(delay_after=0.2)
            # 等待当前账户的新下载完成；download_dir 为目录，timeout 为上限秒数，start_time 为点击前时间戳。
            file_path = Path(wait_download_file(download_dir=DOWNLOAD_DIR, timeout=120, start_time=download_started))
            if file_path.stat().st_size == 0:
                raise RuntimeError(f"下载文件为空：{file_path}")
            named_path = file_path.with_name(f"qianchuan_{account_id}_{start_date}_{end_date}_{time.time_ns()}{file_path.suffix}")
            file_path.rename(named_path)
            downloaded_files.append((account_name, account_id, date_range, named_path))
            account_results.append(f"{account_name}（{account_id}）｜下载成功｜日期={date_range}｜有数据=是｜文件={named_path}")
        except Exception as error:
            account_results.append(f"{account_name}（{account_id}）｜{failure_status}｜日期={date_range}｜原因={error}")
            details = "\n".join(account_results)
            logging.info(f"【达人投流】本次账户处理已中断｜\n{details}")
            raise RuntimeError(f"达人投流：{account_name}（{account_id}）{failure_status}｜日期={date_range}｜原因={error}") from error

    page.close()
    details = "\n".join(account_results)
    summary = f"账户{len(accounts)}个；下载{len(downloaded_files)}个；无数据跳过{empty_count}个；停用跳过{disabled_count}个"
    logging.info(f"【达人投流】账户结果汇总｜{summary}\n{details}")
    return downloaded_files, summary


def update(target_workbook):
    """全部下载、读取合并完成后才清空写入，返回状态区和通知使用的摘要。"""
    downloaded_files, summary = download()
    begin_column, end_column, source_end_column, _ = FACT_AREAS["【基源】达人投流"]
    merged_rows = []
    for account_name, account_id, date_range, file_path in downloaded_files:
        try:
            source_workbook = open_source_workbook(file_path)
            source_sheet = source_workbook.get_sheet_by_index(1)
            source_rows = source_sheet.get_range(1, "A", source_sheet.get_first_free_row() - 1, source_end_column)
            merged_rows.extend(source_rows if not merged_rows else source_rows[1:])
        except Exception as error:
            raise RuntimeError(f"达人投流：{account_name}（{account_id}）文件读取失败｜日期={date_range}｜文件={file_path}｜原因={error}") from error

    target_sheet = target_workbook.get_sheet_by_name("【基源】达人投流")
    if not downloaded_files:
        merged_rows = target_sheet.get_range(1, begin_column, 1, end_column)
    target_sheet.clear_range(1, begin_column, target_sheet.get_first_free_row() - 1, end_column, target="content")
    target_sheet.set_range(1, begin_column, merged_rows)
    logging.info(f"【达人投流】多账户合并写入完成｜区域={begin_column}:{end_column}｜数据行数={len(merged_rows) - 1}")
    return f"{summary}；合并{len(merged_rows) - 1}行"
