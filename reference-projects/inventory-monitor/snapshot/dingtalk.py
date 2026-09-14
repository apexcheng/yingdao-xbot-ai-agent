from datetime import datetime

from xbot_extensions.dingtalk_bot_message.py_api import send_dingtalk_group

from .config import DINGTALK_WEBHOOK_URL, DINGTALK_WEBHOOK_SECRET, OPS_MOBILES, STOCK_UPDATE_MAX_ATTEMPTS
from .utils import ContextLogger


def _product_link(platform, product_id, product_name):
    """生成平台商品详情链接；未知平台只显示商品名称。"""
    product_name = product_name or "未命名商品"
    if not product_id:
        return product_name
    if platform == "拼多多":
        url = f"https://mobile.yangkeduo.com/goods.html?goods_id={product_id}"
    elif platform == "天猫":
        url = f"https://detail.tmall.com/item.htm?id={product_id}"
    else:
        return product_name
    return f"[{product_name}]({url})"


def send_notification(title, content, at_mobiles=None):
    """发送通用钉钉 Markdown 通知，失败只记日志不抛出。"""
    try:
        send_dingtalk_group(
            "markdown",
            content,
            title=title,
            webhook_url=DINGTALK_WEBHOOK_URL,
            webhook_secret=DINGTALK_WEBHOOK_SECRET,
            at_mobiles=at_mobiles or [],
            at_all=False,
        )
        return True
    except Exception as exc:
        ContextLogger("通知", "钉钉").error("发送失败", f"原因={exc}")
        return False


def send_stock_shop_result(platform, shop_name, success_records, failed_records, skipped_records, retry_unfound_count, manager_mobiles, interrupted=False):
    """合并发送单个店铺的库存处理结果。"""
    low_erp_records = [record for record in skipped_records if record.get("skip_reason") == "erp_stock_below_threshold"]
    sku_not_online_records = [record for record in skipped_records if record.get("skip_reason") == "sku_not_online"]
    if not success_records and not failed_records and not low_erp_records and not sku_not_online_records and not retry_unfound_count:
        return False

    status_emoji = "⚠️" if interrupted or failed_records or low_erp_records or retry_unfound_count else "✅"
    status_text = "库存处理中断" if interrupted else "库存处理完成"
    lines = [
        f"### {platform} / {shop_name}｜{status_text}{status_emoji}",
        "",
        f"> 🎉 补库存成功：**{len(success_records)} 个 SKU**　❌ 处理失败：**{len(failed_records)}**  ",
        f"> ⚠️ ERP库存不足：**{len(low_erp_records)}**　ℹ️ SKU未上架：**{len(sku_not_online_records)}**　🔁 待重试未找到：**{retry_unfound_count}**",
    ]
    if success_records:
        lines.extend(["", "#### ✅ 补库存完成"])
        for index, record in enumerate(success_records, start=1):
            product_id = record.get("product_id") or ""
            product_link = _product_link(platform, product_id, record.get("product_name"))
            stock_after = record.get("stock_after") if record.get("stock_after") is not None else "校验失败 / 未取得"
            lines.extend(
                [
                    "",
                    f"**{index}. 📦 {product_link}**  ",
                    f"🏷️ 规格：{record.get('spec_name') or '未命名SKU'}  ",
                    f"🔢 商品ID：{product_id or '未取得'}  ",
                    f"🆔 规格ID：{record.get('sku_id') or '未取得'}  ",
                    f"🕒 操作时间：{record.get('updated_at') or '未记录'}  ",
                    "",
                    f"🧩 ERP商品：{record.get('erp_item_code') or '未取得'}  ",
                    f"🏷️ ERP规格：{record.get('erp_code') or '未取得'}｜{record.get('erp_spec_name') or '未取得名称'}  ",
                    "",
                    f"📊 库存：**{record.get('stock_before')} → {stock_after}**　➕ **+{record.get('added_qty')}**　🏭 ERP：{record.get('erp_available_qty')}",
                ]
            )
    if failed_records:
        lines.extend(["", "#### ❌ 处理失败"])
        for index, record in enumerate(failed_records, start=1):
            attempt_count = record.get("attempt_count")
            if attempt_count is None:
                retry_text = "未关联到预警记录，下轮重新扫描"
            elif record.get("status") == "failed_final" or attempt_count >= STOCK_UPDATE_MAX_ATTEMPTS:
                retry_text = "已终止自动重试"
            else:
                retry_text = f"下轮继续重试（{attempt_count}/{STOCK_UPDATE_MAX_ATTEMPTS}）"
            product_id = record.get("product_id") or ""
            product_link = _product_link(platform, product_id, record.get("product_name"))
            lines.extend(
                [
                    "",
                    f"**{index}. 📦 {product_link}**  ",
                    f"🏷️ 规格：{record.get('spec_name') or '未知SKU'}  ",
                    f"🔢 商品ID：{product_id or '未知'}  ",
                    f"🆔 规格ID：{record.get('sku_id') or '未取得'}  ",
                    f"🕒 操作时间：{record.get('updated_at') or '未记录'}",
                    "",
                    f"> ❌ **失败原因**：{record.get('result_note') or '未知原因'}",
                    f"🔁 {retry_text}",
                ]
            )
    if low_erp_records:
        lines.extend(["", "#### ⚠️ ERP库存不足"])
        for index, record in enumerate(low_erp_records, start=1):
            product_id = record.get("product_id") or ""
            product_link = _product_link(platform, product_id, record.get("product_name"))
            lines.extend(
                [
                    "",
                    f"**{index}. 📦 {product_link}**  ",
                    f"🏷️ 规格：{record.get('spec_name') or '未命名SKU'}  ",
                    f"🔢 商品ID：{product_id or '未取得'}　🆔 规格ID：{record.get('sku_id') or '未取得'}  ",
                    f"🕒 操作时间：{record.get('updated_at') or '未记录'}  ",
                    f"🧩 ERP商品：{record.get('erp_item_code') or '未取得'}  ",
                    f"🏷️ ERP规格：{record.get('erp_code') or '未取得'}｜{record.get('erp_spec_name') or '未取得名称'}  ",
                    f"📊 平台库存：{record.get('stock_before')}　🏭 ERP可售：{record.get('erp_available_qty')}　未补库存",
                ]
            )
    if sku_not_online_records:
        lines.extend(["", "#### ℹ️ SKU未上架"])
        for index, record in enumerate(sku_not_online_records, start=1):
            product_id = record.get("product_id") or ""
            product_link = _product_link(platform, product_id, record.get("product_name"))
            lines.extend(
                [
                    "",
                    f"**{index}. 📦 {product_link}**  ",
                    f"🏷️ 规格：{record.get('spec_name') or '未命名SKU'}  ",
                    f"🔢 商品ID：{product_id or '未取得'}　🆔 规格ID：{record.get('sku_id') or '未取得'}  ",
                    f"🕒 操作时间：{record.get('updated_at') or '未记录'}  ",
                    "ℹ️ 当前 SKU 未上架，未补库存",
                ]
            )
    if retry_unfound_count:
        lines.extend(
            [
                "",
                "#### 🔁 待重试提醒",
                "",
                f"> ⚠️ 已翻到消息列表底部，仍有 **{retry_unfound_count} 条**待重试预警未找到。",
            ]
        )
    lines.extend(["", "---", f"🕒 **通知时间**：{datetime.now():%Y-%m-%d %H:%M:%S}"])

    return send_notification(
        f"{platform}库存处理结果｜{shop_name}",
        "\n".join(lines),
        manager_mobiles if failed_records or low_erp_records or retry_unfound_count else [],
    )


def send_run_summary(started_at, finished_at, alert_records):
    """发送一个汇总窗口内的 SKU 最终处理结果；无有效内容时返回 None。"""
    def count_records(records):
        success = sum(record["status"] == "success" for record in records)
        retrying_failed = sum(record["status"] == "failed" for record in records)
        final_failed = sum(record["status"] == "failed_final" for record in records)
        low_erp = sum(record["status"] == "skipped" and (record.get("result_note") or "").startswith("ERP可售库存(") for record in records)
        at_target = sum(record["status"] == "skipped" and "已达目标" in (record.get("result_note") or "") for record in records)
        sku_not_online = sum(record["status"] == "skipped" and (record.get("result_note") or "").startswith("SKU未上架") for record in records)
        return success, retrying_failed, final_failed, low_erp, at_target, sku_not_online

    success_count, retrying_failed_count, final_failed_count, low_erp_count, at_target_count, sku_not_online_count = count_records(alert_records)
    if not (success_count or retrying_failed_count or final_failed_count or low_erp_count or sku_not_online_count):
        return None

    shop_lines = []
    shop_keys = sorted({(record["platform"], record["shop_name"]) for record in alert_records})
    for platform, shop_name in shop_keys:
        shop_records = [record for record in alert_records if record["platform"] == platform and record["shop_name"] == shop_name]
        shop_success, shop_retrying_failed, shop_final_failed, shop_low_erp, shop_at_target, shop_sku_not_online = count_records(shop_records)
        if not (shop_success or shop_retrying_failed or shop_final_failed or shop_low_erp or shop_sku_not_online):
            continue
        shop_lines.extend(
            [
                f"**{platform} / {shop_name}**  ",
                f"✅ 成功：**{shop_success}**　🔁 待重试失败：**{shop_retrying_failed}**　❌ 最终失败：**{shop_final_failed}**  ",
                f"⚠️ ERP库存不足：**{shop_low_erp}**　ℹ️ SKU未上架：**{shop_sku_not_online}**　🎯 已达目标：**{shop_at_target}**",
                "",
            ]
        )

    content = "\n".join(
        [
            f"### 库存监控阶段汇总{'⚠️' if retrying_failed_count or final_failed_count or low_erp_count else '✅'}",
            "",
            f"🕒 **统计区间**：{started_at:%Y-%m-%d %H:%M:%S} ～ {finished_at:%Y-%m-%d %H:%M:%S}",
            "",
            f"> 🎉 补库存成功：**{success_count} 个 SKU**　🔁 待重试失败：**{retrying_failed_count}**　❌ 最终失败：**{final_failed_count}**  ",
            f"> ⚠️ ERP库存不足：**{low_erp_count}**　ℹ️ SKU未上架：**{sku_not_online_count}**　🎯 库存已达目标：**{at_target_count}**",
            "",
            "#### 🏪 店铺汇总",
            "",
            "\n".join(shop_lines),
            "---",
            f"🕒 **汇总时间**：{finished_at:%Y-%m-%d %H:%M:%S}",
        ]
    )
    return send_notification("库存监控阶段汇总", content)


def send_program_error(platform, shop_name, step, error, product_id="", sku_id=""):
    """发送店铺级程序异常通知，并 @ 运维人员。"""
    product_line = f"**商品**：{_product_link(platform, product_id, product_id)}" if product_id else "**商品**："
    content = "\n".join(
        [
            f"### {platform} / {shop_name}｜程序异常🚨",
            "",
            f"🛒 **平台**：{platform}  ",
            f"🏪 **店铺**：{shop_name}  ",
            f"🧭 **步骤**：{step}  ",
            f"🔗 {product_line}  ",
            f"🆔 **SKU ID**：{sku_id or '未取得'}",
            "",
            f"> ❌ **异常原因**：{error}",
            "",
            "👉 **处理建议**：请检查对应步骤、商品和 SKU 后重新运行。",
            "",
            "---",
            f"🕒 **异常时间**：{datetime.now():%Y-%m-%d %H:%M:%S}",
        ]
    )
    return send_notification(f"{platform}库存监控程序异常", content, OPS_MOBILES)


def send_erp_refresh_error(platform, error, loaded_at, action):
    """发送 ERP 铺货数据刷新失败通知，并 @ 运维人员。"""
    content = "\n".join(
        [
            f"### {platform}｜ERP铺货刷新失败🔄⚠️",
            "",
            f"🛒 **平台**：{platform}  ",
            f"🗂️ **当前数据**：{loaded_at or '无可用旧数据'}  ",
            f"🧭 **后续处理**：{action}",
            "",
            f"> ❌ **失败原因**：{error}",
            "",
            "👉 **处理建议**：请检查 ERP 登录状态、铺货导出和数据导入流程。",
            "",
            "---",
            f"🕒 **异常时间**：{datetime.now():%Y-%m-%d %H:%M:%S}",
        ]
    )
    return send_notification("ERP铺货数据刷新失败", content, OPS_MOBILES)
