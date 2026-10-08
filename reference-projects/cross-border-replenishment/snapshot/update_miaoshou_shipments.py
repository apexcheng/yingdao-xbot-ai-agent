"""妙手 ERP 发货商品明细数据源：下载发货明细并写回 RAW 区。"""

import time
from pathlib import Path

from xbot import web
from xbot.app import logging
from xbot_extensions.xbot_enhance_tools.browser_utils import wait_download_file

from .config import BROWSER_PROFILE
from .utils import clean_text, load_excel_matrix, replace_raw_area, validate_raw_layout

SHEET_NAME = "妙手ERP发货商品明细"
RAW_LAYOUT = {
    "start_col": "K",
    "header_rows": 1,
    "expected_headers": [
        (0, 0, "平台"),
        (0, 1, "国家/地区(站点)"),
        (0, 6, "订单状态"),
        (0, 75, "下单时间"),
        (0, 76, "付款时间"),
        (0, 92, "平台SKU"),
        (0, 98, "产品数量"),
    ],
}


def prepare():
    """
    从妙手历史订单下载最近 30 天的子商品明细（每个产品一行）。

    :return: 含二维数据的 payload
    """
    web.set_user_environment(
        mode="chrome", profile_name=BROWSER_PROFILE,
        specifield_userdata=False, user_data_dir=None,
    )
    browser = web.create(
        url="https://erp.91miaoshou.com/order/package/all?appPackageTab=all",
        mode="chrome", load_timeout=60,
    )
    try:
        browser.wait_load_completed(timeout=60)
        if "/order/package/all" not in browser.get_url():
            raise RuntimeError("妙手 ERP 未进入历史订单页，请先确认 Chrome 登录状态")

        # 先点击左侧历史订单；页面由 Vue 动态渲染，使用实际 DOM 中验证过的菜单结构。
        browser.find_by_xpath(
            "//li[@role='menuitem' and contains(concat(' ',normalize-space(@class),' '),' jx-menu-item ')][.//span[normalize-space()='历史订单']]",
            timeout=20,
        ).click(delay_after=0.2)

        # 平台与订单状态均选择“全部”，只按下单时间筛选近 30 天。
        browser.find_by_xpath("//label[contains(@class,'J_orderPackageQueryPlatformAll')]", timeout=10).click(delay_after=0.1)
        browser.find_by_xpath(
            "//div[contains(@class,'pro-radio-group')]//label[.//input[@value='all']]",
            timeout=10,
        ).click(delay_after=0.1)
        browser.find_by_xpath(
            "//div[contains(@class,'jx-form-item')][.//label[contains(normalize-space(.),'下单时间')]]//div[contains(@class,'jx-date-editor')]",
            timeout=10,
        ).click(delay_after=0.2)
        browser.find_by_xpath(
            "//div[contains(@class,'jx-picker__popper') and @aria-hidden='false']//button[contains(@class,'jx-picker-panel__shortcut') and normalize-space()='近30天']",
            timeout=10,
        ).click(delay_after=0.2)
        browser.find_by_xpath("//button[contains(@class,'J_queryFormSearch')]", timeout=10).click(delay_after=0.5)

        # 通过“导入/导出 → 按当前查询导出”发起导出，不导出未过滤的全部历史订单。
        browser.find_by_xpath("//button[contains(@class,'J_orderPackageExport')]", timeout=15).click(delay_after=0.2)
        browser.find_by_xpath(
            "//li[@role='menuitem' and contains(@class,'J_exportOpOrderBySearchCondition')]",
            timeout=10,
        ).click(delay_after=0.2)
        browser.find_by_xpath("//div[@role='dialog' and @aria-label='导出订单']", timeout=15)

        # 设置已有 EXAMPLE_EXPORT_TEMPLATE 模板对应的列布局：明细、子商品、按产品显示。
        for value in ("order_detail", "sub_bundle", "1"):
            browser.find_by_xpath(
                f"//div[@role='dialog' and @aria-label='导出订单']//label[.//input[@value='{value}']]",
                timeout=10,
            ).click(delay_after=0.1)
        template = browser.find_by_xpath(
            "//div[@role='dialog' and @aria-label='导出订单']//div[contains(@class,'order-package_export-order-template-select')]//div[contains(@class,'jx-select__placeholder')][normalize-space(.)='EXAMPLE_EXPORT_TEMPLATE']",
            timeout=10,
        )
        if not template.is_displayed():
            raise RuntimeError("妙手 ERP 导出模板 EXAMPLE_EXPORT_TEMPLATE 未处于选中状态")

        # 导出可能先显示进度弹窗，再由浏览器自动下载；仅接受本轮新文件。
        started_at = time.time()
        browser.find_by_xpath(
            "//div[@role='dialog' and @aria-label='导出订单']//button[contains(@class,'J_orderPackageExportDialogExport')]",
            timeout=10,
        ).click(delay_after=0.2)
        browser.find_by_xpath("//div[@role='dialog' and @aria-label='正在导出']", timeout=15)

        # 增强工具2026 下载等待：download_dir=当前用户下载目录；
        # filename_pattern=Excel 导出文件；timeout=大批量导出上限秒数；
        # start_time=点击最终导出前时间，防止取到历史文件。
        downloaded = wait_download_file(
            download_dir=str(Path.home() / "Downloads"),
            filename_pattern="*.xls*",
            timeout=1200,
            start_time=started_at,
        )
        data = load_excel_matrix(downloaded)
        validate_raw_layout(SHEET_NAME, data, RAW_LAYOUT)
        if len(data) < 2 or not any(clean_text(row[92]) for row in data[1:]):
            raise RuntimeError("妙手 ERP 本轮导出没有有效平台 SKU 数据")
        logging.info(f"[{SHEET_NAME}] 本轮下载完成：{Path(downloaded).name}，{len(data)-1} 行")
        return {"data": data}
    finally:
        browser.close()


def apply_update(workbook, payload):
    """
    更新妙手 ERP 发货商品明细原始区。

    :param workbook: 已打开的目标工作簿
    :param payload: ``prepare`` 返回的数据
    :return: 写入结果描述文本
    """
    return replace_raw_area(workbook, SHEET_NAME, payload["data"], RAW_LAYOUT)
