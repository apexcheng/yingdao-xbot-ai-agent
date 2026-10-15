"""发送本轮表格更新结果。"""

import datetime

from xbot_extensions.xbot_enhance_tools.dingtalk_message import send_dingtalk_group

from .config import DINGTALK_OPERATOR_MOBILES, DINGTALK_SECRET, DINGTALK_WEBHOOK, ERP_SHOP_NAME, TARGET_FILE


def send_results(sheet_results, saved, errors, product_library_id_events=None, purchase_changed_ids=None):
    skipped_count = sum(row[1] == "今日跳过" for row in sheet_results)
    success_count = sum(row[1] == "成功" for row in sheet_results)
    failure_count = sum(row[1] == "失败" for row in sheet_results)
    incomplete_count = len(sheet_results) - success_count - skipped_count - failure_count
    product_warnings = any(
        row[0] == "【基源】产品库" and row[1] == "成功" and "未找到商品" in row[4]
        for row in sheet_results
    )
    needs_attention = bool(errors or failure_count or incomplete_count or not saved or product_warnings)
    title = f"{ERP_SHOP_NAME}｜经营报表{'更新需关注⚠️' if needs_attention else '更新完成✅'}"
    summary = f"📊 成功：**{success_count}**　⏭️ 跳过：**{skipped_count}**　❌ 失败：**{failure_count}**"
    if incomplete_count:
        summary += f"　⏳ 未完成：**{incomplete_count}**"
    message = [
        f"### {title}",
        "",
        f"> {summary}",
    ]
    if purchase_changed_ids:
        message.extend([
            "",
            f"**采购成本：更新了 {len(purchase_changed_ids)} 个ID**",
            f"> 规格代码：{'、'.join(purchase_changed_ids[:5])}" + (" 等" if len(purchase_changed_ids) > 5 else ""),
        ])
    status_sections = (
        ("失败", "❌ 处理失败"),
        ("未实现", "⏳ 未完成"),
        ("未执行", "⏳ 未执行"),
        ("成功", "✅ 本次更新"),
        ("今日跳过", "⏭️ 今日已完成，自动跳过"),
    )
    for status, heading in status_sections:
        rows = [row for row in sheet_results if row[1] == status]
        if not rows:
            continue
        message.extend(["", f"#### {heading}（{len(rows)}）"])
        for row in rows:
            if status == "失败":
                message.append(f"- **{row[0]}**\n> ❌ **失败原因**：{row[4]}")
            elif status in ("成功", "今日跳过"):
                message.append(f"- {row[0]}")
                if row[0] == "【基源】产品库" and status == "成功" and row[4]:
                    message.append(f"> {row[4]}")
            else:
                message.append(f"- **{row[0]}**｜{row[4]}")
    if errors:
        message.extend(["", "#### 🚨 程序异常"])
        message.extend(f"> {error}" for error in errors)
    message.extend([
        "", f"💾 **表格保存**：{'已保存' if saved else '未保存成功'}",
        "---", f"🕒 **通知时间**：{datetime.datetime.now():%Y-%m-%d %H:%M:%S}",
        "",
        f"📁 **文件位置**：`{TARGET_FILE}`",
    ])

    if product_library_id_events:
        if any(event["kind"] in ("filled_time", "added") for event in product_library_id_events):
            message.extend(["", "---", "", "#### ✅ 产品库成功变更 ID"])
            for kind, label in (("filled_time", "补齐创建时间"), ("added", "新增商品")):
                ids = "、".join(f"`{event['id']}`" for event in product_library_id_events if event["kind"] == kind)
                if ids:
                    message.append(f"- {label}：{ids}")
        if any(event["kind"] in ("not_found", "failed") for event in product_library_id_events):
            message.extend(["", "#### ⚠️ 产品库未完成 ID"])
            message.extend(
                f"- `{event['id']}`：{event['reason']}"
                for event in product_library_id_events
                if event["kind"] in ("not_found", "failed")
            )

    # 群机器人 Markdown 通知；Webhook/Secret 为地址与加签密钥，title 为标题，at_mobiles 为需关注时的运营手机号。
    send_dingtalk_group(
        "markdown", "\n".join(message), webhook_url=DINGTALK_WEBHOOK,
        webhook_secret=DINGTALK_SECRET, title=title,
        at_mobiles=DINGTALK_OPERATOR_MOBILES if needs_attention else [],
    )
