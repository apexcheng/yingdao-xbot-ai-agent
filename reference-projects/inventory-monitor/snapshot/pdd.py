"""拼多多库存监控：扫描商家后台「商品动态」售罄预警并自动加库存。

主流程见 process_shop：打开店铺浏览器 → 登录 → 进入商品动态 → 分页扫描
预警消息 → 逐条在加库存页查询 ERP 库存、计算目标库存并提交，结果写回
SQLite 用于跨轮次去重和重试。
"""

import math
import re
import time
import traceback
from datetime import datetime, timedelta

from xbot import sleep, web, win32
from xbot.app.dialog import show_notifycation
from xbot_extensions.ad_killer import close_ads

from . import database
from .config import ERP_MIN_QTY, PDD_SCROLL_UNITS, STOCK_UPDATE_MAX_ATTEMPTS, TARGET_DIVISOR, TARGET_MAX
from .utils import ContextLogger, ErpStockDataError, get_erp_available_qty, get_or_create_single_page, is_sku_ignored


class NonRetryableStockError(RuntimeError):
    """当前 SKU 属于业务性终态失败，不再自动重试。"""


def process_shop(platform, shop_config):
    """处理单个拼多多店铺的主流程。"""
    success_records = []
    failed_records = []
    skipped_records = []
    retry_unfound_count = 0
    step = "打开店铺浏览器"
    shop_logger = ContextLogger(platform, shop_config["name"])

    try:
        # 店铺必须配置独立的 Chrome Profile，保证各店铺浏览器环境和登录态隔离
        profile = str(shop_config.get("profile", "")).strip()
        if not profile:
            raise RuntimeError(f"店铺 {shop_config['name']} 尚未配置 Chrome Profile")

        # 切换店铺环境，复用或新建后台页并最大化浏览器
        page = get_or_create_single_page(platform, profile)
        shop_logger.flow("店铺浏览器已打开")
        # sleep(3)
        step = "检查登录状态"
        # URL 已进入 login 页面时，用店铺配置的账号密码重新登录
        is_login_page = "login" in page.get_url().lower()
        if is_login_page:
            shop_logger.flow("登录态已失效，开始重新登录")
            username = str(shop_config.get("username", "")).strip()
            password = str(shop_config.get("password", ""))
            if not username or not password:
                raise RuntimeError("当前店铺登录态已失效，且店铺配置中缺少登录账号或密码")
            # 复现“增强工具2026”拼多多登录源码：切账号登录、填写账号密码并提交
            page.find_by_xpath("//div[contains(@class, 'info-part')]//div[contains(text(), '账号登录')]", timeout=10).click(delay_after=0.3)
            page.find_by_xpath("//div[contains(@class, 'info-part')]//input[contains(@id, 'username')]", timeout=10).input(username, delay_after=0.3)
            page.find_by_xpath("//div[contains(@class, 'info-part')]//input[contains(@id, 'password')]", timeout=10).input(password, delay_after=0.3)
            page.find_by_xpath("//div[contains(@class, 'info-part')]//button[contains(., '登录')]/span", timeout=10).click(delay_after=0.5)
            page.wait_load_completed(timeout=60 * 2)
            sleep(2)
            if "login" in page.get_url().lower():
                raise RuntimeError("拼多多店铺登录失败，提交账号密码后仍停留在登录页")
            shop_logger.flow("重新登录成功")
        else:
            shop_logger.flow("登录状态正常")

        # sleep(4) # 等待js加载 / 广告加载
        close_ads(网页对象=page, 广告Xpath="//div[contains(@data-testid, 'modal-innerWrapper')]//*[local-name()='svg' and contains(@data-testid, 'icon-close')]|//div[contains(@class, 'outerWrapper')]//*[local-name()='svg' and contains(@data-testid, 'icon-close')]", 使用内置广告Xpath=False, 关闭方式="click")
        close_ads(网页对象=page, 广告Xpath="//div[contains(@class, 'outerWrapper')]//div[./*[contains(@data-testid, 'icon-close')]]", 使用内置广告Xpath=False, 关闭方式="click")

        step = "进入商品动态"
        # 从首页进「消息」再点「商品动态」，随后校验菜单已处于选中状态
        page.find_by_xpath("//div[@id='umd_kits_home_entry_wrapper']//div[contains(text(), '消息')]", timeout=10).click(delay_after=0.1)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            product_dynamic_entries = page.find_all_by_xpath(
                "//ul[contains(@class, 'NavList_nav-wrapper')]//li[contains(., '商品动态')]",
                timeout=0.1,
            )
            if product_dynamic_entries:
                product_dynamic_entries[0].click(delay_after=0.1)
            if page.find_all_by_xpath(
                "//ul[contains(@class, 'NavList_nav-wrapper')]//li[contains(., '商品动态') and contains(@class, 'NavList_nav-item-active')]",
                timeout=0.1,
            ):
                break
        else:
            raise RuntimeError("商品动态未进入选中状态，可能存在广告或蒙层阻挡")
        shop_logger.flow("已进入商品动态")
        step = "扫描商品动态消息"
        retry_alert_ids = database.get_retry_alert_ids(platform, shop_config["name"])
        shop_logger.flow("开始扫描商品动态", f"待重试商品={len(retry_alert_ids)}")
        page_no = 1
        while True:
            # 扫描当前页面全部消息条，逐条识别售罄预警
            messages = page.find_all_by_xpath("//section[contains(@class, 'detail-wrapper')]//div[contains(@class, 'msg-item')]", timeout=10)
            shop_logger.flow(f"扫描第{page_no}页", f"消息数={len(messages)}")
            for message in messages:
                # 只处理两类已确认的库存预警标题，发现新标题按程序异常通知运维适配
                title = message.find_by_xpath(".//div[contains(@class, 'title-content')]", timeout=2).get_text().strip()
                if title not in ("【库存预警】您有热卖商品今天即将售罄", "【SKU库存预警】SKU即将售罄"):
                    if title == "店铺商品库存预警":
                        message.find_by_xpath(".//button[contains(., '售罄转预售')]", timeout=3).click()
                        web.get_active(mode="chrome").close()
                        shop_logger.flow("店铺商品库存预警已转为预售，跳转页已关闭")
                        continue
                    elif title == "商品编辑驳回通知":
                        message.find_by_xpath(".//button[contains(., '去处理')]", timeout=3).click()
                        web.get_active(mode="chrome").close()
                        shop_logger.flow("商品编辑驳回通知已点击去处理，跳转页已关闭")
                        continue
                    shop_logger.error("发现未适配的商品动态消息", f"消息类型={title}")
                    raise RuntimeError(f"发现未适配的商品动态消息标题，请运维适配：{title}")

                alert_data = None
                try:
                    # 读取正文与消息时间后解析预警数据
                    body = message.find_by_xpath(".//p[contains(@class, 'MsgItem_info')]", timeout=2).get_text().strip()
                    time_text = message.find_by_xpath(".//span[contains(@class, 'title-time')]", timeout=2).get_text().strip()
                    alert_data = _parse_alert_message(title, body, time_text, datetime.now())

                    sku_key = alert_data["sku_id"] or alert_data["spec_name"].strip()
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
                        continue
                    if alert["attempt_count"] >= STOCK_UPDATE_MAX_ATTEMPTS:
                        shop_logger.product("跳过处理，已达到最大尝试次数", alert_data["product_id"], sku_key, f"状态={alert['status']}")
                        continue

                    attempt_count = alert["attempt_count"] + 1
                    shop_logger.product(f"开始第{attempt_count}次库存处理", alert_data["product_id"], sku_key)
                    message.find_by_xpath(".//button[contains(., '补库存')]", timeout=3).click()
                    stock_page = web.get_active(mode="chrome")
                    result = _process_stock_alert(page, stock_page, alert_data, platform, shop_logger)
                    result["attempt_count"] = attempt_count
                    result["updated_at"] = database.save_alert_result(
                        alert["id"],
                        result.get("sku_id") or alert_data["sku_id"],
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
                    elif result.get("skip_reason") == "sku_ignored":
                        result_text = "SKU在忽略名单中，未补库存"
                        result_details = ()
                    else:
                        result_text = "库存更新成功"
                        result_details = (f"库存={result.get('stock_before')}→{result.get('stock_after')}", f"增加={result.get('added_qty')}")
                    shop_logger.product(result_text, alert_data["product_id"], sku_key, *result_details)
                    show_notifycation(f"拼多多库存处理完成\n商品ID：{alert_data['product_id']}\nSKU ID：{result.get('sku_id') or alert_data['sku_id'] or '无'}\n状态：{result['status']}\n结果：{'｜'.join((result_text, *result_details))}", placement="top")

                    if result["status"] == "success":
                        success_records.append(result)
                    elif result["status"] == "skipped":
                        skipped_records.append(result)
                except Exception as exc:
                    if not alert_data:
                        shop_logger.error("商品预警解析失败", f"原因={exc}", traceback_text=traceback.format_exc())
                        failed_records.append({"result_note": str(exc)})
                        continue

                    sku_key = alert_data["sku_id"] or alert_data["spec_name"].strip()
                    alert = database.get_or_create_alert(
                        platform,
                        shop_config["name"],
                        alert_data["notification_time"],
                        alert_data["message_type"],
                        alert_data["product_id"],
                        sku_key,
                    )
                    attempt_count = alert["attempt_count"] + 1
                    status = "failed_final" if isinstance(exc, NonRetryableStockError) or attempt_count >= STOCK_UPDATE_MAX_ATTEMPTS else "failed"
                    updated_at = database.save_alert_result(
                        alert["id"],
                        alert_data["sku_id"],
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
                    show_notifycation(f"拼多多库存处理失败\n商品ID：{alert_data['product_id']}\nSKU ID：{alert_data['sku_id'] or '无'}\n原因：{exc}", placement="top", level="error")

            has_unread = bool(page.find_all_by_xpath(
                "//ul[contains(@class, 'NavList_nav-wrapper')]//li[contains(., '商品动态')]/span[contains(@class, 'unread')]",
                timeout=0.2,
            ))
            if not has_unread and not retry_alert_ids:
                shop_logger.flow("停止翻页", "原因=当前无未读消息且无待重试商品")
                break
            next_buttons = page.find_all_by_xpath(
                "//li[contains(@class, 'pagination-next') and not(contains(@class, 'disabled'))]",
                timeout=0.2,
            )
            if len(next_buttons) > 1:
                raise RuntimeError(f"商品动态可用下一页按钮数量异常：{len(next_buttons)}")
            if not next_buttons:
                if has_unread:
                    raise RuntimeError("商品动态仍有未读消息，但未找到可用下一页按钮")
                retry_unfound_count = len(retry_alert_ids)
                shop_logger.flow("停止翻页", f"原因=已到最后一页，仍有{retry_unfound_count}条待重试商品未找到")
                break
            next_buttons[0].click(delay_after=0.1)
            page_no += 1
            shop_logger.flow(f"翻到第{page_no}页继续扫描")

        return {
            "success": success_records,
            "failed": failed_records,
            "skipped": skipped_records,
            "retry_unfound_count": retry_unfound_count,
            "program_error": None,
        }
    except Exception as exc:
        return {
            "success": success_records,
            "failed": failed_records,
            "skipped": skipped_records,
            "retry_unfound_count": retry_unfound_count,
            "program_error": {"step": step, "error": str(exc), "traceback": traceback.format_exc()},
        }


def _parse_alert_message(title, body, time_text, now):
    """解析单条售罄预警消息文本为预警数据。"""
    label_matches = list(
        re.finditer(r"(?P<label>商品标题|商品(?:id|ID)|商品规格|规格(?:id|ID)|仅剩库存|规格)\s*[:：]?\s*", body)
    )
    fields = {}
    for index, match in enumerate(label_matches):
        value_end = label_matches[index + 1].start() if index + 1 < len(label_matches) else len(body)
        fields[match.group("label").lower()] = body[match.end():value_end].strip()

    product_id = fields.get("商品id", "")
    current_stock = fields.get("仅剩库存", "")
    current_stock_match = re.match(r"\d+", current_stock)
    if not product_id.isdigit() or not current_stock_match:
        raise RuntimeError(f"库存预警正文无法解析商品ID或当前库存：{body}")
    current_stock = current_stock_match.group()

    sku_id = ""
    if title == "【库存预警】您有热卖商品今天即将售罄":
        sku_id = fields.get("规格id", "")
        spec_name = fields.get("规格", "")
        if not sku_id.isdigit() or not spec_name:
            raise RuntimeError(f"热卖商品库存预警正文无法解析规格或规格ID：{body}")
    else:
        spec_text = fields.get("商品规格", "")
        if not spec_text:
            raise RuntimeError(f"SKU库存预警正文无法解析商品规格：{body}")
        spec_name = spec_text.strip()

    if re.fullmatch(r"\d{1,2}:\d{2}", time_text):
        alert_date = now.date()
        clock_text = time_text
    elif re.fullmatch(r"昨天\s+\d{1,2}:\d{2}", time_text):
        alert_date = (now - timedelta(days=1)).date()
        clock_text = time_text.split()[-1]
    elif re.fullmatch(r"前天\s+\d{1,2}:\d{2}", time_text):
        alert_date = (now - timedelta(days=2)).date()
        clock_text = time_text.split()[-1]
    elif re.fullmatch(r"三天前\s+\d{1,2}:\d{2}", time_text):
        alert_date = (now - timedelta(days=3)).date()
        clock_text = time_text.split()[-1]
    else:
        raise RuntimeError(f"库存预警时间格式未确认：{time_text}")

    notification_time = datetime.strptime(f"{alert_date:%Y-%m-%d} {clock_text}", "%Y-%m-%d %H:%M").strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    return {
        "message_type": title,
        "product_id": product_id,
        "product_name": fields.get("商品标题", ""),
        "sku_id": sku_id,
        "spec_name": spec_name,
        "current_stock": int(current_stock),
        "notification_time": notification_time,
    }


def _process_stock_alert(message_page, stock_page, alert_data, platform, shop_logger):
    """在点击「加库存」跳转后的加库存页上执行单条预警的加库存操作。"""
    message_url = message_page.get_url()
    try:
        stock_page.find_by_xpath("//div[contains(@class, 'innerWrapper')][contains(., '修改库存')]", timeout=10)
        low_stock_filters = stock_page.find_all_by_xpath("//div[contains(@class, 'filter-sku')]//label[contains(., '低库存规格')][@data-checked='true']//input/following-sibling::div[1]", timeout=2)
        if low_stock_filters:
            low_stock_filters[0].click(delay_after=0.1)

        headers = stock_page.find_all_by_xpath("//div[contains(@class, 'innerWrapper')][contains(., '修改库存')]//table[contains(@class, 'tableWrapper')][contains(., '规格信息')]//tr/th", timeout=5)
        header_texts = [header.get_text().strip() for header in headers]
        if header_texts.count("当前库存") != 1 or header_texts.count("改后库存") != 1:
            raise RuntimeError(f"修改库存表头异常：{header_texts}")
        current_stock_col = header_texts.index("当前库存") + 1
        changed_stock_col = header_texts.index("改后库存") + 1

        row = _find_unique_sku_row(stock_page, alert_data["sku_id"], alert_data["spec_name"].strip())

        sku_id = alert_data["sku_id"]
        if not sku_id:
            sku_id_elements = row.find_all_by_xpath(".//td[1]//div[contains(text(), '规格 ID')]", timeout=2)
            if sku_id_elements:
                sku_id_match = re.search(r"规格\s*ID\s*[:：]\s*(\d+)", sku_id_elements[0].get_text())
                sku_id = sku_id_match.group(1) if sku_id_match else ""
        if is_sku_ignored(platform, sku_id):
            return {
                **alert_data,
                "status": "skipped",
                "skip_reason": "sku_ignored",
                "sku_id": sku_id,
                "added_qty": 0,
                "result_note": "SKU在忽略名单中，跳过补库存",
            }

        erp_code = ""
        erp_code_elements = row.find_all_by_xpath(".//td[1]//div[contains(text(), '规格编码')]", timeout=2)
        if erp_code_elements:
            erp_code_match = re.search(r"规格编码\s*[:：]\s*(\S+)", erp_code_elements[0].get_text())
            erp_code = erp_code_match.group(1).strip() if erp_code_match else ""

        if not erp_code:
            if not sku_id:
                raise NonRetryableStockError("SKU 未关联规格编码，且加库存页无法取得规格 ID，请运营检查商品 SKU 的 ERP 代码关联")
            erp_codes = database.get_erp_codes(platform, alert_data["product_id"], sku_id)
            if len(erp_codes) != 1:
                raise NonRetryableStockError(
                    f"SKU 未关联规格编码，ERP铺货按商品ID+SKU ID匹配到 {len(erp_codes)} 条，无法唯一取得ERP代码，请运营检查商品 SKU 的 ERP 代码关联：SKU ID={sku_id}"
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

        stock_text = row.find_by_xpath(f".//td[{current_stock_col}]", timeout=3).get_text()
        stock_match = re.search(r"-?\d+", stock_text)
        if not stock_match:
            raise RuntimeError(f"无法读取当前拼多多库存：{stock_text}")
        stock_before = int(stock_match.group())

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

        stock_input = row.find_by_xpath(f".//td[{changed_stock_col}]//input", timeout=3)
        stock_input.set_value("")
        stock_input.input(str(target_stock))
        stock_page.find_by_xpath("//div[contains(@class, 'innerWrapper')][contains(., '修改库存')]//button[contains(., '提交')]", timeout=5).click(delay_after=0.1)

        stock_dialog_gone = False
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if not stock_page.find_all_by_xpath("//div[contains(@class, 'innerWrapper')][contains(., '修改库存')]", timeout=0.5):
                stock_dialog_gone = True
                break
            sleep(0.1)
        if not stock_dialog_gone:
            raise RuntimeError("点击提交后修改库存弹层未关闭")

        stock_page.find_by_xpath(
            f"//table[contains(@class, 'tableWrapper')]//tr[contains(., '{alert_data['product_id']}')]//a[@data-tracking-viewid='changestock']",
            timeout=10,
        ).execute_javascript(
            """
            function (element, args) {
                element.click();
            }
            """
        )
        stock_page.find_by_xpath("//div[contains(@class, 'innerWrapper')][contains(., '修改库存')]", timeout=10)
        low_stock_filters = stock_page.find_all_by_xpath("//div[contains(@class, 'filter-sku')]//label[contains(., '低库存规格')][@data-checked='true']//input/following-sibling::div[1]", timeout=2)
        if low_stock_filters:
            low_stock_filters[0].click(delay_after=0.1)
        verify_row = _find_unique_sku_row(stock_page, sku_id, alert_data["spec_name"].strip())
        verify_text = verify_row.find_by_xpath(f".//td[{current_stock_col}]", timeout=3).get_text()
        verify_match = re.search(r"-?\d+", verify_text)
        if not verify_match:
            raise RuntimeError(f"二次校验库存无法解析：{verify_text}")
        stock_after = int(verify_match.group())
        if stock_after <= stock_before:
            raise RuntimeError(f"二次校验加后库存未高于加前库存：加前={stock_before}，加后={stock_after}")

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
        try:
            if stock_page.get_url() != message_url:
                stock_page.close()
        except Exception as exc:
            shop_logger.product_error("关闭加库存页失败", alert_data["product_id"], alert_data["sku_id"] or alert_data["spec_name"].strip(), f"原因={exc}")
        try:
            message_page.activate()
        except Exception as exc:
            shop_logger.product_error("返回商品动态消息页失败", alert_data["product_id"], alert_data["sku_id"] or alert_data["spec_name"].strip(), f"原因={exc}")


def _find_unique_sku_row(stock_page, sku_id, message_spec_text):
    """在加库存页 SKU 表格中优先按消息规格、再按规格ID定位行。"""
    stock_list = stock_page.find_by_xpath("//div[contains(@id, 'goods-list') and contains(@class, 'quantity')]", timeout=5)
    # stock_list.hover(simulative=True, delay_after=0.1)
    # stock_list.scroll_to(location="top", behavior="instant", search_up=True)
    previous_row_texts = None
    message_spec_text = message_spec_text.replace(" ", "")
    while True:
        rows = stock_page.find_all_by_xpath("//div[contains(@id, 'goods-list') and contains(@class, 'quantity')]//tr[@data-testid='beast-core-table-body-tr']", timeout=5)
        for row in rows:
            page_sku_values = [value.strip().replace(" ", "") for value in row.find_by_xpath(".//div[@class='sku-name']", timeout=3).get_text().strip().split(",")]
            pattern = "".join(rf"[^\s-]+-{re.escape(value)}" for value in page_sku_values)
            if all(page_sku_values) and re.fullmatch(pattern, message_spec_text):
                return row
            if sku_id and row.find_all_by_xpath(f".//div[@class='sku-id' and contains(., '{sku_id}')]", timeout=0.1):
                return row

        row_texts = tuple(row.get_text().strip() for row in rows)
        if row_texts == previous_row_texts:
            break
        previous_row_texts = row_texts
        stock_list.hover(simulative=True, delay_after=0)
        win32.mouse_wheel(wheel_direction="down", wheel_times=PDD_SCROLL_UNITS, delay_after=0)
        sleep(1)

    raise RuntimeError(f"未找到目标SKU行：{sku_id or message_spec_text}")
