from xbot import web, win32
from xbot.app import logging
from xbot_extensions.guanyi_erp_api import select_combine_item, select_stock

from .config import COMBINE_IGNORE_ITEM_CODES, SKU_IGNORE_LIST

PLATFORM_ENTRY_URLS = {
    "拼多多": "https://mms.pinduoduo.com/",
    "天猫": "https://qn.taobao.com/home.htm/",
}

PLATFORM_ENTRY_URLS = {
    "拼多多": "https://mms.pinduoduo.com/",
    "天猫": "https://qn.taobao.com/home.htm/",
}


class ContextLogger:
    """绑定日志业务域和执行主体，统一输出流程与商品日志。"""

    def __init__(self, platform, shop_name):
        self._prefix = f"【{platform}】{shop_name}"

    def flow(self, event, *details):
        logging.info(self._format(event, details))

    def error(self, event, *details, traceback_text=None):
        logging.error(self._format(event, details, traceback_text))

    def product(self, event, product_id, sku=None, *details):
        logging.info(self._format_product(event, product_id, sku, details))

    def product_error(self, event, product_id, sku=None, *details, traceback_text=None):
        logging.error(self._format_product(event, product_id, sku, details, traceback_text))

    def _format_product(self, event, product_id, sku, details, traceback_text=None):
        product_details = [f"商品ID={product_id}"]
        if sku is not None and str(sku).strip():
            product_details.append(f"SKU={sku}")
        product_details.extend(details)
        return self._format(event, product_details, traceback_text)

    def _format(self, event, details, traceback_text=None):
        message = f"{self._prefix}：{event}{''.join(f'｜{detail}' for detail in details if detail is not None and str(detail))}"
        if traceback_text:
            message += f"\n异常堆栈：\n{traceback_text}"
        return message


def get_or_create_single_page(platform, profile):
    web.set_user_environment(
        mode="chrome",
        profile_name=profile,
        specifield_userdata=False,
        user_data_dir=None
    )

    target_url = PLATFORM_ENTRY_URLS[platform]
    all_page = web.get_all(mode="chrome")
    platform_pages = {}
    fallback_page = None

    for page in all_page:
        current_url = page.get_url() or ""
        matched_platform = None
        for name, entry_url in PLATFORM_ENTRY_URLS.items():
            if entry_url in current_url:
                matched_platform = name
                break
        if matched_platform:
            if matched_platform in platform_pages:
                page.close()
            else:
                platform_pages[matched_platform] = page
        else:
            if fallback_page is None:
                fallback_page = page
            else:
                page.close()

    if platform in platform_pages:
        target_page = platform_pages[platform]
    elif fallback_page:
        target_page = fallback_page
    elif platform_pages:
        target_page = next(iter(platform_pages.values()))
    else:
        target_page = web.create(url=target_url, mode="chrome")
        target_page.wait_load_completed()
        return target_page

    target_page.navigate(target_url, load_timeout=20)
    return target_page


class ErpStockDataError(RuntimeError):
    """ERP 商品结构或仓库关系已明确异常，由业务调用方决定失败策略。"""


def is_sku_ignored(platform, sku_id):
    """判断平台 SKU ID 是否在不补库存名单中。"""
    return bool(sku_id) and str(sku_id).strip() in {str(item).strip() for item in SKU_IGNORE_LIST.get(platform, [])}


def get_erp_available_qty(erp_code):
    """按已确定的 ERP 代码查询可售库存（69 单码或组合商品代码）。"""
    if erp_code.startswith("69"):
        return _query_sku_stock(erp_code)

    params = {"code": erp_code}
    select_combine_item.main(params)
    context = params.get("context", {})
    items = params.get("items", [])
    if not items:
        raise RuntimeError(f"CREP-API 未返回组合商品 {erp_code} 的子件明细")

    participating_items = []
    for item in items:
        item_code = str(item.get("item_code", "")).strip()
        if item_code in COMBINE_IGNORE_ITEM_CODES:
            continue
        participating_items.append(item)
    if not participating_items:
        participating_items = items

    min_qty = None
    for item in participating_items:
        item_code = str(item.get("item_code", "")).strip()
        child_sku_code = str(item.get("item_sku_code", "")).strip()
        if not child_sku_code.startswith("69"):
            raise ErpStockDataError(
                f"组合商品 {erp_code} 子件 {item_code} 的规格代码缺失或非69码：{child_sku_code or '无'}"
            )
        child_qty, _, _ = _query_sku_stock(child_sku_code)
        min_qty = child_qty if min_qty is None else min(min_qty, child_qty)
    return min_qty, str(context.get("code", "")).strip() or erp_code, str(context.get("name", "")).strip()


def _query_sku_stock(item_sku_code):
    """按 69 规格代码查询 ERP 参与仓库的可售库存。"""
    params = {"max_page_no": 10, "item_sku_code": item_sku_code}
    select_stock.main(params)
    stocks = params.get("stocks", [])
    if not stocks:
        raise RuntimeError(f"CREP-API 未返回规格代码 {item_sku_code} 的库存记录")
    warehouse_stocks = [stock for stock in stocks if str(stock.get("warehouse_name", "")).strip() == "正品仓"]
    if not warehouse_stocks:
        raise ErpStockDataError(f"CREP-API 已返回规格代码 {item_sku_code} 的库存，但没有 正品仓 记录")
    erp_available_qty = sum(int(float(stock.get("salable_qty", 0) or 0)) for stock in warehouse_stocks) # TODO 理论上这里只会去有一条len(warehouse_stocks)=1，待跑测试确认。
    stock = warehouse_stocks[0]
    return erp_available_qty, str(stock.get("item_code", "")).strip(), str(stock.get("item_sku_name", "")).strip()
