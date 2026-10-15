"""更新 ERP 退货明细；页面保留到 ERP 发货详情下载完成。"""

import datetime

from xbot.app import logging
from xbot_extensions.activity_a90a8311.download_return_details import download_return_details

from .config import ERP_SHOP_NAME
from .utils import open_source_workbook, replace_fact_area


def download(erp_page):
    today = datetime.date.today()
    inbound_time = ((today - datetime.timedelta(days=50)).strftime("%Y/%m/%d"), today.strftime("%Y/%m/%d"))
    creation_time = ((today - datetime.timedelta(days=60)).strftime("%Y/%m/%d"), today.strftime("%Y/%m/%d"))
    # ERP 退货商品明细下载；page 为已登录页面，shop_name 为店铺，两个日期元组分别筛选入库和制单时间。
    file_path = download_return_details(page=erp_page, shop_name=ERP_SHOP_NAME, inbound_time=inbound_time, creation_time=creation_time)
    logging.info(f"【ERP退货明细】下载完成｜文件={file_path}")
    return file_path


def update(target_workbook, erp_page):
    source_workbook = open_source_workbook(download(erp_page))
    replace_fact_area(target_workbook, source_workbook, "【基源】ERP退货明细")
    return True
