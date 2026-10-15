"""使用主流程已初始化的 ERP 页面更新发货商品明细。"""

import datetime

from xbot.app import logging
from xbot_extensions.activity_a90a8311.download_delivery_item_details import download_delivery_item_details

from .config import ERP_SHOP_NAME
from .utils import open_source_workbook, replace_fact_area


def download(erp_page):
    today = datetime.date.today()
    start_date = (today - datetime.timedelta(days=30)).strftime("%Y/%m/%d")
    end_date = today.strftime("%Y/%m/%d")
    # ERP 发货商品明细下载；page 为已登录页面，shop_name 为店铺，start_date/end_date 为起止日期。
    file_path = download_delivery_item_details(page=erp_page, shop_name=ERP_SHOP_NAME, start_date=start_date, end_date=end_date)
    logging.info(f"【ERP发货详情】下载完成｜文件={file_path}")
    return file_path


def update(target_workbook, erp_page):
    source_workbook = open_source_workbook(download(erp_page))
    replace_fact_area(target_workbook, source_workbook, "【基源】ERP发货详情")
    return True
