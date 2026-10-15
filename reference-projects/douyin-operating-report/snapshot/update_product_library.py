"""按创建时间补齐并更新基源产品库。"""

import json
import re
import time
import traceback

from xbot import web
from xbot.app import logging

from .config import DOUYIN_PROFILE, ERP_SHOP_NAME
from .utils import parse_datetime


def extract_product_code(product_name):
    """去掉 BOW 品牌名后，提取标题开头的型号。"""
    product_name = re.sub(r"B\.?O\.?W\.?", "", product_name, flags=re.IGNORECASE).strip()
    match = re.match(r"([A-Za-z]+\d[A-Za-z0-9]*(?:[-_][A-Za-z0-9]+)*(?:\s+Pro)?)", product_name, flags=re.IGNORECASE)
    return " ".join(match.group(1).split()) if match else "未维护"


def get_product_list(page, action):
    """通过 DOM 触发列表请求，从响应中读取当页商品。"""
    page.start_monitor_network(url="*/product/tproduct/list*", use_wildcard=True, resource_type="XHR|Fetch")
    try:
        action()
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            responses = page.get_responses()
            if responses:
                response = responses[0]
                product_list = json.loads(response["body"])
                if response["status"] != 200 or product_list["code"] != 0:
                    raise RuntimeError(f"商品列表请求失败：HTTP={response['status']}，原因={product_list['msg']}")
                break
            time.sleep(0.2)
        else:
            raise TimeoutError("等待本次商品列表请求完成超时")
    except Exception:
        try:
            page.stop_monitor_network()
        except Exception:
            logging.error(f"【产品库】停止网络监听失败：异常={traceback.format_exc()}")
        raise
    else:
        page.stop_monitor_network()

    products = []
    for item in product_list["data"]:
        created_value = item["create_time"]
        created_at = parse_datetime(created_value)
        if created_at is None:
            raise ValueError(f"商品创建时间无法解析：商品ID={item['product_id']}，时间={created_value}")
        products.append({"product_id": str(item["product_id"]), "name": item["name"], "created_at": created_at})
    return products


def find_new_products(max_created_at, existing_ids):
    """按创建时间降序遍历列表响应，到达时间边界时结束。"""
    # 打开“全部”商品列表，等页面加载后处理可能挡住操作的提示弹窗。
    page = web.create("https://fxg.jinritemai.com/ffa/g/list?tab=all", "chrome", load_timeout=20)
    page.wait_load_completed(timeout=20)
    time.sleep(2)
    if page.find_all_by_xpath("//div[@role='dialog']//button[normalize-space()='知道了']", timeout=0.5):
        page.find_by_xpath("//div[@role='dialog']//button[normalize-space()='知道了']", timeout=2).click(delay_after=0.2)
    # 清除搜索条件，并把创建时间切换到降序，再查询第一页。
    page.find_by_xpath("//button[@type='reset'][.//span[normalize-space()='重置']]", timeout=20).click(delay_after=0.2)

    while page.find_by_xpath("//th[contains(@class, 'timeSortTitle')]", timeout=20).get_attribute("aria-sort") != "descending":
        page.find_by_xpath("//th[contains(@class, 'timeSortTitle')][.//span[normalize-space()='创建时间']]", timeout=20).click(delay_after=0.2)

    # 表头排序也会触发列表请求；等 1 秒后再监听查询，避免混入排序请求响应。
    time.sleep(1)
    products = get_product_list(page, lambda: page.find_by_xpath("//button[@type='submit'][.//span[normalize-space()='查询']]", timeout=20).click(delay_after=0.2))

    new_rows = []
    seen_ids = set(existing_ids)
    reached_boundary = False
    page_number = 1
    while products:
        for product in products:
            if product["created_at"] <= max_created_at:
                # 降序列表到达 MAX，后续商品都不属于新增范围。
                reached_boundary = True
                break
            if product["product_id"] not in seen_ids:
                new_rows.append([ERP_SHOP_NAME, "'" + product["product_id"], extract_product_code(product["name"]), product["created_at"].strftime("%Y/%m/%d %H:%M:%S")])
                seen_ids.add(product["product_id"])

        logging.info(f"【产品库】商品页检查完成：页码={page_number}，累计新增={len(new_rows)}，已到时间边界={reached_boundary}")
        if reached_boundary or page.find_all_by_xpath("//li[@title='下一页' and @aria-disabled='true']", timeout=0.5):
            break
        products = get_product_list(page, lambda: page.find_by_xpath("//li[@title='下一页' and @aria-disabled='false']//button", timeout=20).click(delay_after=0.2))
        page_number += 1

    page.close()
    return new_rows


def update(target_workbook, id_events=None):
    """先补齐缺失时间，再按补齐后的 MAX 追加新商品。"""
    if id_events is None:
        id_events = []
    else:
        id_events.clear()
    # 读取第 2 行起的 F:I，记录已有商品 ID 和最后一条有内容的行，用于补时间及末尾追加。
    target_sheet = target_workbook.get_sheet_by_name("【基源】产品库")
    product_rows = target_sheet.get_range(2, "F", target_sheet.get_first_free_row() - 1, "I")
    existing_ids = {str(row[1]).strip() for row in product_rows if row[1] is not None and row[1] != ""}
    if not existing_ids:
        raise ValueError("产品库没有商品ID，无法执行增量更新")
    last_data_row = max(index + 2 for index, row in enumerate(product_rows) if any(value is not None and value != "" for value in row))
    phase_errors = []
    current_product_id = None
    web.set_user_environment(mode="chrome", profile_name=DOUYIN_PROFILE)

    try:
        # 第一阶段：按 ID 查询缺少时间的商品，只回填对应行的 I 列。
        page = web.create("https://fxg.jinritemai.com/ffa/g/list?tab=all", "chrome", load_timeout=20)
        page.wait_load_completed(timeout=20)
        time.sleep(2)
        if page.find_all_by_xpath("//div[@role='dialog']//button[normalize-space()='知道了']", timeout=0.3):
            page.find_by_xpath("//div[@role='dialog']//button[normalize-space()='知道了']", timeout=2).click(delay_after=0.2)
        for index, row in enumerate(product_rows):
            current_product_id = None
            if row[1] is None or row[1] == "":
                continue
            product_id = str(row[1]).strip()
            if row[3] is not None and row[3] != "":
                continue
            current_product_id = product_id
            # 查询后只接受 ID 完全匹配的商品行；未找到时保留空白并记录通知提示。
            page.find_by_xpath("//input[@placeholder='请输入商品名称/商品ID/商家编码，多条可用逗号隔开']", timeout=20).input(product_id, append=False, delay_after=0.2, send_key_delay=10)
            products = get_product_list(page, lambda: page.find_by_xpath("//button[@type='submit'][.//span[normalize-space()='查询']]", timeout=20).click(delay_after=0.2))
            matching_rows = [item for item in products if item["product_id"] == product_id]
            if not matching_rows:
                id_events.append({"id": product_id, "kind": "not_found", "reason": "未找到商品，创建时间未补齐"})
                current_product_id = None
                logging.warning(f"【产品库】未找到商品，时间留空：商品ID={product_id}")
                continue
            formatted_time = matching_rows[0]["created_at"].strftime("%Y/%m/%d %H:%M:%S")
            target_sheet.set_range(index + 2, "I", [[formatted_time]])
            row[3] = formatted_time
            id_events.append({"id": product_id, "kind": "filled_time"})
            current_product_id = None
            logging.info(f"【产品库】创建时间已补齐：商品ID={product_id}，创建时间={formatted_time}")
        page.close()
    except Exception as error:
        if current_product_id is not None:
            id_events.append({"id": current_product_id, "kind": "failed", "reason": str(error)})
        phase_errors.append(f"补齐创建时间失败：{error}")
        logging.error(f"【产品库】补齐时间失败，继续检查新商品：异常={traceback.format_exc()}")

    try:
        # 第二阶段：使用补齐后的时间计算 MAX，扫描更新商品；该阶段在第一阶段失败时仍会执行。
        parsed_times = [parse_datetime(row[3]) for row in product_rows]
        max_created_at = max(value for value in parsed_times if value is not None)
        logging.info(f"【产品库】开始检查新商品：创建时间MAX={max_created_at:%Y/%m/%d %H:%M:%S}")
        new_rows = find_new_products(max_created_at, existing_ids)
        if new_rows:
            # 新商品按扫描得到的降序写到最后一条有内容记录之后，中间空行不作为追加位置。
            target_sheet.set_range(last_data_row + 1, "F", new_rows)
            id_events.extend({"id": row[1][1:], "kind": "added"} for row in new_rows)
    except Exception as error:
        phase_errors.append(f"追加新商品失败：{error}")
        logging.error(f"【产品库】追加新商品失败，保留已完成数据：异常={traceback.format_exc()}")

    filled_count = sum(event["kind"] == "filled_time" for event in id_events)
    added_count = sum(event["kind"] == "added" for event in id_events)
    not_found = [event["id"] for event in id_events if event["kind"] == "not_found"]
    detail = f"补齐创建时间{filled_count}条；新增商品{added_count}条"
    if not_found:
        detail += f"；⚠️ 未找到商品（时间留空）：{'、'.join(not_found)}"
    if phase_errors:
        raise RuntimeError("；".join([*phase_errors, detail]))
    return detail
