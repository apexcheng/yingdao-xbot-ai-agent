"""天猫库存监控：通过千牛消息页网络响应发现 SKU 卖空预警并自动加库存。

主流程见 process_shop：打开千牛浏览器 → 扫描库存卖空消息 → 逐条在库存管理页
查询 ERP 库存、计算目标库存并提交，结果写回 SQLite 用于跨轮次去重和重试。
"""

import json
import math
import re
import time
import traceback
from datetime import datetime

from xbot import web, win32, sleep, print
from xbot.app.dialog import show_notifycation
from xbot_extensions.iframe2 import api as iframe2

from . import database
from .config import ERP_MIN_QTY, STOCK_UPDATE_MAX_ATTEMPTS, TARGET_DIVISOR, TARGET_MAX, TMALL_EXISTING_MESSAGE_STOP_COUNT, TMALL_SCROLL_REQUEST_ATTEMPTS, TMALL_SCROLL_UNITS
from .utils import ContextLogger, ErpStockDataError, get_erp_available_qty, get_or_create_single_page, is_sku_ignored


class NonRetryableStockError(RuntimeError):
    """当前 SKU 属于业务性终态失败，不再自动重试。"""


def process_shop(platform, shop_config):
    """处理单个天猫店铺的主流程。"""
    success_records = []
    failed_records = []
    skipped_records = []
    retry_unfound_count = 0
    step = "打开店铺浏览器"
    page = None
    network_monitoring = False
    shop_logger = ContextLogger(platform, shop_config["name"])

    try:
        # 店铺必须配置独立 Chrome Profile，复用千牛现有登录态
        profile = str(shop_config.get("profile", "")).strip()
        if not profile:
            raise RuntimeError(f"店铺 {shop_config['name']} 尚未配置 Chrome Profile")

        # 切换店铺环境，复用或新建千牛页并最大化浏览器
        page = get_or_create_single_page(platform, profile)
        shop_logger.flow("店铺浏览器已打开")

        step = "检查登录状态"
        # 千牛跳转到 login 页面即表示当前登录态已失效，复现“增强工具2026”千牛登录源码完成账密登录
        if "login" in page.get_url().lower():
            shop_logger.flow("登录态已失效，开始重新登录")
            username = str(shop_config.get("username", "")).strip()
            password = str(shop_config.get("password", ""))
            if not username or not password:
                raise RuntimeError("当前店铺登录态已失效，且店铺配置中缺少登录账号或密码")

            iframe_page = iframe2.init_iframe(page)
            login_iframe = iframe2.to_iframe(iframe_instance=iframe_page, iframe_xpath="//iframe[contains(@id, 'login')]", current_global=False, timeout=5)
            iframe2.click_by_xpath(iframe_instance=login_iframe, xpath="//div[contains(@class, 'login')]//a[contains(text(), '密码登录')]", current_global=False, delay_after=0, timeout=10)
            iframe2.input_by_xpath(iframe_instance=login_iframe, xpath="//form[contains(@class, 'login-form')]//input[contains(@id, 'login-id')]", text=username, current_global=False, focus_timeout=5, timeout=10)
            iframe2.input_by_xpath(iframe_instance=login_iframe, xpath="//form[contains(@class, 'login-form')]//input[contains(@id, 'password')]", text=password, current_global=False, focus_timeout=5, timeout=10)
            iframe2.click_by_xpath(iframe_instance=login_iframe, xpath="//form[contains(@class, 'login-form')]//button[contains(text(), '登录')]", current_global=False, delay_after=0, timeout=10)
            page.wait_load_completed(timeout=60 * 2)
            sleep(2)
            if "login" in page.get_url().lower():
                raise RuntimeError("千牛店铺登录失败，提交账号密码后仍停留在登录页")
            shop_logger.flow("重新登录成功")
        else:
            shop_logger.flow("登录状态正常")

        step = "打开千牛店铺消息"
        page.find_by_xpath("//div[contains(@class, 'bg')]//div[contains(@class, 'MessageIcon_container')][.//*[text()='消息']]", timeout=20).click(delay_after=0.1)

        # 首批消息：监听覆盖「店铺」加载直到进入「库存卖空通知」，避免提前结束漏掉响应
        page.start_monitor_network(url="*mtop.taobao.wireless.amp.imba.message.session.list*", use_wildcard=True, resource_type="XHR|Fetch|Script")
        network_monitoring = True
        page.find_by_xpath("//div[contains(@class, 'SysMessage_drawerContainer')]//ul/li[contains(., '店铺')]", timeout=10).click(delay_after=0.1)
        page.find_by_xpath("//div[contains(@class, 'SysMessage_drawerContainer')]//div[contains(@class, 'tabs-content')]//div[@data-msgid and contains(., '库存卖空通知')]", timeout=10).click(delay_after=0.1)
        page.find_by_xpath("//div[contains(@class, 'SysMessage_drawerContainer')]//*[contains(@class, 'drawer-header')][contains(., '库存卖空通知')]", timeout=10)
        # TODO 首次实测时用 F12 对照请求数量；如果 F12 有而影刀没抓到，说明这里结束监听太早，需要继续等响应完整后再停止。
        current_responses = page.get_responses()
        page.stop_monitor_network()
        network_monitoring = False
        if not current_responses:
            raise RuntimeError("进入库存卖空通知后未捕获到 message.session.list 响应")
        shop_logger.flow("已进入库存卖空通知")

        step = "扫描库存卖空消息"
        seen_message_ids = set()
        retry_alert_ids = database.get_retry_alert_ids(platform, shop_config["name"])
        consecutive_existing = 0
        batch_no = 1
        stop_reason = None
        shop_logger.flow("开始扫描库存卖空消息", f"待重试商品={len(retry_alert_ids)}")

        while True:
            stock_messages = _parse_stock_messages(current_responses)
            shop_logger.flow(f"扫描第{batch_no}批消息", f"商品预警数={len(stock_messages)}")
            for alert_data in stock_messages:
                if alert_data["message_id"] in seen_message_ids:
                    continue
                seen_message_ids.add(alert_data["message_id"])

                sku_key = alert_data["spec_name"].strip()
                alert = database.get_or_create_alert(
                    platform,
                    shop_config["name"],
                    alert_data["notification_time"],
                    alert_data["message_type"],
                    alert_data["product_id"],
                    sku_key,
                )
                retry_alert_ids.discard(alert["id"])
                if alert["status"] in ("success", "skipped", "failed_final"):
                    shop_logger.product("跳过处理，已有终态结果", alert_data["product_id"], sku_key, f"状态={alert['status']}")
                    consecutive_existing += 1
                    if consecutive_existing >= TMALL_EXISTING_MESSAGE_STOP_COUNT and not retry_alert_ids:
                        stop_reason = f"连续{TMALL_EXISTING_MESSAGE_STOP_COUNT}条预警已终态"
                        break
                    continue
                if alert["attempt_count"] >= STOCK_UPDATE_MAX_ATTEMPTS:
                    shop_logger.product("跳过处理，已达到最大尝试次数", alert_data["product_id"], sku_key, f"状态={alert['status']}")
                    consecutive_existing += 1
                    if consecutive_existing >= TMALL_EXISTING_MESSAGE_STOP_COUNT and not retry_alert_ids:
                        stop_reason = f"连续{TMALL_EXISTING_MESSAGE_STOP_COUNT}条预警已终态"
                        break
                    continue

                consecutive_existing = 0
                attempt_count = alert["attempt_count"] + 1
                shop_logger.product(f"开始第{attempt_count}次库存处理", alert_data["product_id"], sku_key)

                try:
                    result = _process_stock_alert(page, alert_data, platform, shop_logger)
                    result["attempt_count"] = attempt_count
                    result["updated_at"] = database.save_alert_result(
                        alert["id"],
                        result.get("sku_id"),
                        result.get("erp_code"),
                        alert_data["spec_name"],
                        attempt_count,
                        result["status"],
                        result.get("erp_available_qty"),
                        result.get("stock_before"),
                        result.get("added_qty"),
                        result.get("stock_after"),
                        result.get("result_note"),
                    )
                    if result.get("skip_reason") == "stock_at_target":
                        result_text = "当前库存已达到目标，未补库存"
                        result_details = ()
                    elif result.get("skip_reason") == "erp_stock_below_threshold":
                        result_text = "ERP库存不高于阈值，未补库存"
                        result_details = ()
                    elif result.get("skip_reason") == "sku_not_online":
                        result_text = "SKU未上架，未补库存"
                        result_details = ()
                    elif result.get("skip_reason") == "sku_ignored":
                        result_text = "SKU在忽略名单中，未补库存"
                        result_details = ()
                    else:
                        result_text = "库存更新成功"
                        result_details = (f"库存={result.get('stock_before')}→{result.get('stock_after')}", f"增加={result.get('added_qty')}")
                    shop_logger.product(result_text, alert_data["product_id"], sku_key, *result_details)
                    show_notifycation(f"天猫库存处理完成\n商品ID：{alert_data['product_id']}\nSKU ID：{result.get('sku_id') or '无'}\n状态：{result['status']}\n结果：{'｜'.join((result_text, *result_details))}", placement="top")

                    if result["status"] == "success":
                        success_records.append(result)
                    elif result["status"] == "skipped":
                        skipped_records.append(result)
                except Exception as exc:
                    status = "failed_final" if isinstance(exc, NonRetryableStockError) or attempt_count >= STOCK_UPDATE_MAX_ATTEMPTS else "failed"
                    updated_at = database.save_alert_result(
                        alert["id"],
                        alert_data.get("sku_id"),
                        None,
                        alert_data["spec_name"],
                        attempt_count,
                        status,
                        result_note=str(exc),
                    )
                    failed_record = dict(alert_data)
                    failed_record.update({"attempt_count": attempt_count, "status": status, "result_note": str(exc), "updated_at": updated_at})
                    failed_records.append(failed_record)
                    shop_logger.product_error("处理失败", alert_data["product_id"], sku_key, f"状态={status}", f"原因={exc}", traceback_text=traceback.format_exc())
                    show_notifycation(f"天猫库存处理失败\n商品ID：{alert_data['product_id']}\n规格：{sku_key}\n原因：{exc}", placement="top", level="error")

            if stop_reason:
                break

            page.start_monitor_network(url="*mtop.taobao.wireless.amp.imba.message.session.list*", use_wildcard=True, resource_type="XHR|Fetch|Script")
            network_monitoring = True
            next_responses = []
            for scroll_no in range(1, TMALL_SCROLL_REQUEST_ATTEMPTS + 1):
                page.find_by_xpath("//div[contains(@class, 'SysMessage_drawerContainer')]//div[contains(@class, 'tabs-content')]", timeout=5).hover(simulative=True, delay_after=0.1)
                win32.mouse_wheel(wheel_direction="down", wheel_times=TMALL_SCROLL_UNITS, delay_after=1)
                sleep(2)
                next_responses = page.get_responses()
                if next_responses:
                    break

            page.stop_monitor_network()
            network_monitoring = False
            if not next_responses:
                if retry_alert_ids:
                    stop_reason = (
                        f"连续{TMALL_SCROLL_REQUEST_ATTEMPTS}次滚动未触发新消息请求，已到底，"
                        f"仍有{len(retry_alert_ids)}条待重试预警未在消息列表中找到"
                    )
                    retry_unfound_count = len(retry_alert_ids)
                else:
                    stop_reason = f"连续{TMALL_SCROLL_REQUEST_ATTEMPTS}次滚动未触发新消息请求，已到底"
                break

            current_responses = next_responses
            batch_no += 1

        shop_logger.flow("停止扫描", f"原因={stop_reason}")

        return {
            "success": success_records,
            "failed": failed_records,
            "skipped": skipped_records,
            "retry_unfound_count": retry_unfound_count,
            "program_error": None,
        }
    except Exception as exc:
        if network_monitoring and page is not None:
            try:
                page.stop_monitor_network()
            except Exception as stop_exc:
                shop_logger.error("停止网络监听失败", f"原因={stop_exc}")
        return {
            "success": success_records,
            "failed": failed_records,
            "skipped": skipped_records,
            "retry_unfound_count": retry_unfound_count,
            "program_error": {"step": step, "error": str(exc), "traceback": traceback.format_exc()},
        }


def _parse_stock_messages(responses):
    """解析千牛 message.session.list 响应中的 SKU 卖空消息。"""
    messages = []

    for response in responses:
        body = response.get("body")
        if not body:
            continue

        if isinstance(body, str):
            start = body.find("(")
            end = body.rfind(")")
            if start < 0 or end <= start:
                raise RuntimeError("message.session.list 响应不是可识别的 JSONP")
            try:
                payload = json.loads(body[start + 1:end])
            except json.JSONDecodeError as exc:
                raise RuntimeError("message.session.list JSONP 解析失败") from exc
        elif isinstance(body, dict):
            payload = body
        else:
            raise RuntimeError(f"message.session.list 响应 body 类型未适配：{type(body).__name__}")

        for protocol in payload.get("data", {}).get("dataProtocols", []):
            template_text = protocol.get("body", {}).get("templateData")
            if not template_text:
                continue
            try:
                template_data = json.loads(template_text) if isinstance(template_text, str) else template_text
                msg_text = template_data.get("msg")
                msg = json.loads(msg_text) if isinstance(msg_text, str) else msg_text
            except (json.JSONDecodeError, AttributeError) as exc:
                raise RuntimeError("message.session.list templateData.msg 解析失败") from exc
            if not isinstance(msg, dict):
                continue
            if msg.get("status") != "ItemSkuZeroStock":
                continue
            if msg.get("title") == "热销SKU售罄提醒":
                continue

            content_list = msg.get("content")
            content = content_list[0].strip() if isinstance(content_list, list) and content_list else ""
            # TODO 用真实复杂规格继续验证解析：规格内可能包含 /、-、丨、【】、()，商品标题本身也可能带括号，不能出现截断或串位。
            match = re.match(r"^(?P<product_name>.+?)\(商品ID[:：]\s*(?P<product_id>\d+)\)\s*(?P<spec_name>.+?)\s+已售罄(?:，|,)", content)
            if not match:
                raise RuntimeError(f"SKU卖空消息正文格式未适配：{content}")
            if not msg.get("gmtModified"):
                raise RuntimeError(f"SKU卖空消息缺少 gmtModified：商品ID={match.group('product_id')}")
            if not msg.get("id"):
                raise RuntimeError(f"SKU卖空消息缺少 id：商品ID={match.group('product_id')}")

            messages.append(
                {
                    "message_id": str(msg["id"]),
                    "message_type": str(msg.get("cnName") or "商品卖空（SKU）"),
                    # TODO 首次实机核对该时间与千牛页面一致；这里使用运行机器本地时区，机器时区配置错误会导致通知时间偏移。
                    "notification_time": datetime.fromtimestamp(int(msg["gmtModified"]) / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                    "product_id": match.group("product_id"),
                    "product_name": match.group("product_name").strip(),
                    "sku_id": None,
                    "spec_name": match.group("spec_name").strip(),
                }
            )

    return messages


def _find_unique_sku_row(iframe_page, spec_name, error_prefix=""):
    """按规格名搜索并定位唯一 SKU 行，多行时优先唯一上架行。"""
    iframe2.input_by_xpath(iframe_instance=iframe_page, xpath="//input[@uitype='search' or contains(@placeholder, '搜索')]", text=spec_name, current_global=False, focus_timeout=5, timeout=10, send_key_delay=10)
    win32.send_keys("{ENTER}")
    sleep(1.5)

    rows = iframe2.find_all_ele(iframe_instance=iframe_page, xpath='//tbody//tr[.//*[@class="sku-name"]]', current_global=False, timeout=5)
    target_spec_name = re.sub(r"[\s\u200b\u200c\u200d\u2060\ufeff]+", "", spec_name)
    rows = [
        row
        for row in rows
        if re.sub(
            r"[\s\u200b\u200c\u200d\u2060\ufeff]+",
            "",
            row.find_by_xpath(".//*[@class='sku-name']", timeout=2).get_text(),
        )
        == target_spec_name
    ]

    if len(rows) == 1:
        return rows[0]
    if not rows:
        raise RuntimeError(f"{error_prefix}未找到匹配的SKU行：{spec_name}")

    online_rows = []
    for candidate_row in rows:
        sku_tag_elements = candidate_row.find_all_by_xpath(".//div[@class='sku-tag']", timeout=2)
        if sku_tag_elements and "上架" in sku_tag_elements[0].get_text().strip():
            online_rows.append(candidate_row)

    if len(online_rows) == 1:
        return online_rows[0]
    if online_rows:
        raise RuntimeError(f"{error_prefix}SKU行匹配到 {len(rows)} 行，其中 {len(online_rows)} 行上架，无法唯一确定：{spec_name}")
    raise RuntimeError(f"{error_prefix}SKU行匹配到 {len(rows)} 行，但均未上架，无法确定目标SKU：{spec_name}")


def _process_stock_alert(message_page, alert_data, platform, shop_logger):
    """在加库存页上执行单条预警的加库存操作。"""
    stock_page = None
    iframe_page = None
    try:
        stock_page = web.create(
            url=f"https://inventorymanage.tmall.com/qn/inventory/inventoryWarningSetting?current=1&pageSize=10&itemIds={alert_data['product_id']}",
            mode="chrome",
            load_timeout=20,
        )
        stock_page.wait_load_completed()

        stock_page.find_by_xpath("//tbody//tr[contains(@class, 'first ')]/td//button[contains(., '编辑库存')]", timeout=10).click(delay_after=0.5)
        iframe_page = iframe2.to_iframe(
            iframe_instance=stock_page,
            iframe_xpath="//iframe[@class='inventory-drawer-iframe-content']",
            current_global=False,
            timeout=5
        )

        spec_name = alert_data["spec_name"].strip()
        row = _find_unique_sku_row(iframe_page, spec_name)

        sku_tag_elements = row.find_all_by_xpath(".//div[@class='sku-tag']", timeout=2)
        is_online = "上架" in sku_tag_elements[0].get_text().strip() if sku_tag_elements else False
        if not is_online:
            return {
                **alert_data,
                "status": "skipped",
                "skip_reason": "sku_not_online",
                "added_qty": 0,
                "result_note": "SKU未上架，跳过补库存",
            }

        erp_code = ""
        sku_id = ""
        erp_code_elements = row.find_all_by_xpath(".//*[contains(@class, 'sku-serial-number')]", timeout=2)
        if erp_code_elements:
            serial_text = erp_code_elements[0].get_text().strip()
            erp_match = re.search(r"商家编码\s*[:：]\s*(\S+)", serial_text)
            erp_code = erp_match.group(1).strip() if erp_match else ""

        sku_id_elements = row.find_all_by_xpath(".//*[contains(@class, 'sku-id')]", timeout=2)
        if sku_id_elements:
            sku_id_text = sku_id_elements[0].get_text().strip()
            sku_match = re.search(r"skuId\s*[:：]\s*(\d+)", sku_id_text)
            sku_id = sku_match.group(1).strip() if sku_match else ""

        if is_sku_ignored(platform, sku_id):
            return {
                **alert_data,
                "status": "skipped",
                "skip_reason": "sku_ignored",
                "sku_id": sku_id,
                "added_qty": 0,
                "result_note": "SKU在忽略名单中，跳过补库存",
            }

        if not erp_code:
            if not sku_id:
                raise NonRetryableStockError("SKU 未关联商家编码，且页面无法取得 SKU ID，请运营检查商品 SKU 的 ERP 代码关联")
            erp_codes = database.get_erp_codes(platform, alert_data["product_id"], sku_id)
            if len(erp_codes) != 1:
                raise NonRetryableStockError(
                    f"SKU 未关联商家编码，ERP铺货按商品ID+SKU ID匹配到 {len(erp_codes)} 条，无法唯一取得ERP代码，请运营检查商品 SKU 的 ERP 代码关联：SKU ID={sku_id}"
                )
            erp_mapping = erp_codes[0]
            erp_code = erp_mapping["system_sku_code"] or erp_mapping["system_item_code"]
            if not erp_code:
                raise NonRetryableStockError(
                    f"ERP铺货匹配到的系统商品代码与系统规格代码均为空：商品ID={alert_data['product_id']}，SKU ID={sku_id}"
                )

        try:
            erp_available_qty, erp_item_code, erp_spec_name = get_erp_available_qty(erp_code)
        except ErpStockDataError as exc:
            raise NonRetryableStockError(str(exc)) from exc

        headers = iframe2.find_all_ele(
            iframe_instance=iframe_page,
            xpath="//thead//th",
            current_global=False,
            timeout=5,
        )
        header_texts = [header.get_text().strip() for header in headers]
        if "改后可售库存" not in header_texts or "库存增减" not in header_texts or "预扣库存" not in header_texts:
            raise RuntimeError(f"库存编辑表头异常：{header_texts}")

        sellable_col = header_texts.index("改后可售库存") + 1
        change_col = header_texts.index("库存增减") + 1
        reserved_col = header_texts.index("预扣库存") + 1

        sellable_text = row.find_by_xpath(f".//td[{sellable_col}]//input", timeout=3).get_attribute("value").strip()
        sellable_match = re.search(r"-?\d+", sellable_text)
        if not sellable_match:
            raise RuntimeError(f"无法读取改后可售库存：{sellable_text}")
        current_sellable = int(sellable_match.group())
        reserved_text = row.find_by_xpath(f".//td[{reserved_col}]", timeout=3).get_text().strip()
        reserved_match = re.search(r"-?\d+", reserved_text)
        if not reserved_match:
            raise RuntimeError(f"无法读取预扣库存：{reserved_text}")
        reserved_qty = int(reserved_match.group())
        stock_before = current_sellable + reserved_qty

        if erp_available_qty <= ERP_MIN_QTY:
            return {
                **alert_data,
                "status": "skipped",
                "skip_reason": "erp_stock_below_threshold",
                "sku_id": sku_id,
                "erp_code": erp_code,
                "erp_item_code": erp_item_code,
                "erp_spec_name": erp_spec_name,
                "erp_available_qty": erp_available_qty,
                "stock_before": stock_before,
                "added_qty": 0,
                "stock_after": stock_before,
                "result_note": f"ERP可售库存({erp_available_qty})不高于阈值({ERP_MIN_QTY})，跳过补库存",
            }

        target_stock = min(math.ceil(erp_available_qty / TARGET_DIVISOR), TARGET_MAX)
        added_qty = max(target_stock - stock_before, 0)
        if added_qty <= 0:
            return {
                **alert_data,
                "status": "skipped",
                "skip_reason": "stock_at_target",
                "sku_id": sku_id,
                "erp_code": erp_code,
                "erp_item_code": erp_item_code,
                "erp_spec_name": erp_spec_name,
                "erp_available_qty": erp_available_qty,
                "stock_before": stock_before,
                "added_qty": 0,
                "stock_after": stock_before,
                "result_note": f"当前库存({stock_before})已达目标({target_stock})，无需补库存",
            }

        row.find_by_xpath(f".//td[{change_col}]//div[contains(@class, 'button') and contains(text(), '增加')]", timeout=3).click(delay_after=0.2)
        stock_input = row.find_by_xpath(f".//td[{change_col}]//input", timeout=3)
        stock_input.set_value("")
        stock_input.input(str(added_qty))
        iframe2.find_ele(
            iframe_instance=iframe_page,
            xpath="//div[contains(@class, 'footer')]//button[contains(., '提交')]",
            current_global=False,
            timeout=5,
        ).click(delay_after=0.1)

        drawer_gone = False
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if not stock_page.find_all_by_xpath("//iframe[@class='inventory-drawer-iframe-content']", timeout=0.5):
                drawer_gone = True
                break
            sleep(0.1)
        if not drawer_gone:
            raise RuntimeError("点击提交后库存编辑抽屉未关闭")

        reopen_deadline = time.monotonic() + 5
        reopen_error = None
        while time.monotonic() < reopen_deadline:
            try:
                stock_page.find_by_xpath("//tbody//tr[contains(@class, 'first ')]/td//button[contains(., '编辑库存')]", timeout=0.5).click(delay_after=0.1)
                break
            except Exception as exc:
                reopen_error = exc
                sleep(0.1)
        else:
            raise RuntimeError("提交后 5 秒内未能重新打开库存编辑抽屉") from reopen_error

        iframe_page = iframe2.to_iframe(
            iframe_instance=stock_page,
            iframe_xpath="//iframe[@class='inventory-drawer-iframe-content']",
            current_global=False,
            timeout=5
        )
        sleep(3)
        verify_row = _find_unique_sku_row(iframe_page, spec_name, "二次校验时")

        verify_sellable_text = verify_row.find_by_xpath(f".//td[{sellable_col}]//input", timeout=3).get_attribute("value").strip()
        verify_sellable_match = re.search(r"-?\d+", verify_sellable_text)
        if not verify_sellable_match:
            raise RuntimeError(f"二次校验无法读取改后可售库存：{verify_sellable_text}")
        verify_sellable = int(verify_sellable_match.group())

        verify_reserved_text = verify_row.find_by_xpath(f".//td[{reserved_col}]", timeout=3).get_text().strip()
        verify_reserved_match = re.search(r"-?\d+", verify_reserved_text)
        if not verify_reserved_match:
            raise RuntimeError(f"二次校验无法读取预扣库存：{verify_reserved_text}")
        verify_reserved = int(verify_reserved_match.group())
        stock_after = verify_sellable + verify_reserved

        if stock_after <= stock_before:
            raise RuntimeError(f"二次校验加后库存未高于加前库存：加前={stock_before}，加后={stock_after}")
        sleep(1.5)

        return {
            **alert_data,
            "status": "success",
            "sku_id": sku_id,
            "erp_code": erp_code,
            "erp_item_code": erp_item_code,
            "erp_spec_name": erp_spec_name,
            "erp_available_qty": erp_available_qty,
            "stock_before": stock_before,
            "added_qty": added_qty,
            "stock_after": stock_after,
            "result_note": f"成功补库存：{stock_before}→{stock_after}(+{added_qty})，ERP可售={erp_available_qty}",
        }
    finally:
        if stock_page is not None:
            try:
                stock_page.close()
            except Exception as exc:
                shop_logger.product_error("关闭加库存页失败", alert_data["product_id"], alert_data["spec_name"].strip(), f"原因={exc}")
        try:
            message_page.activate()
        except Exception as exc:
            shop_logger.product_error("返回千牛消息页失败", alert_data["product_id"], alert_data["spec_name"].strip(), f"原因={exc}")
