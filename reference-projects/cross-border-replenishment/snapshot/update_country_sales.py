"""国家日销量：直接使用妙手历史订单原始导出，三国作为一个更新任务。"""

import re
from collections import defaultdict
from datetime import datetime

from xbot.app import logging

from .utils import clean_text, column_name, column_number, normalize_date


COUNTRIES = (
    ("【跨镜】非律宾", "PH"),
    ("【跨镜】马来西亚", "MY"),
    ("【跨镜】泰国", "TH"),
)
VALID_STATUSES = {"已发货", "已完成", "交运成功", "已退款"}


def update_all(workbook, results, states, set_state, prepare):
    """
    基于本轮妙手原始文件独立重算三国销量，全部成功后由调用方保存。

    :param workbook: 已打开的目标工作簿
    :param results: 本轮执行结果列表
    :param states: 原有更新状态
    :param set_state: 在当前工作簿写入更新状态的函数
    :param prepare: 获取本轮妙手原始导出数据的函数
    :return: 是否有需要保存的修改
    """
    # 三国视为一个任务；全部今天成功才整体跳过
    if all(
        states.get(name, {}).get("last_success")
        and states[name]["last_success"].date() == datetime.now().date()
        for name, _ in COUNTRIES
    ):
        for name, _ in COUNTRIES:
            results.append({"sheet": name, "status": "skipped", "last_success": states[name]["last_success"]})
        return False

    logging.info("[国家销量更新] 开始更新菲律宾、马来西亚、泰国")
    try:
        payload = prepare()
    except Exception as exc:
        detail = f"妙手历史订单原始文件获取失败：{exc}"
        for name, _ in COUNTRIES:
            results.append({"sheet": name, "status": "failed", "detail": detail,
                            "last_success": states.get(name, {}).get("last_success")})
        for name, _ in COUNTRIES:
            set_state(workbook, name, "失败", detail)
        logging.error(f"[国家销量更新] {detail}")
        return True

    try:
        # 原始文件列位置由妙手导出模块校验；此处直接使用原始字段计算
        sales = defaultdict(int)
        source_dates = set()
        for row in payload["data"][1:]:
            if clean_text(row[6]) not in VALID_STATUSES:
                continue
            site = clean_text(row[1])
            site_code = (
                "PH" if "菲律宾" in site else
                "MY" if "马来" in site else
                "TH" if "泰国" in site else None
            )
            if site_code is None:
                continue
            platform = clean_text(row[0])
            pay_time = row[76]
            date_value = pay_time if pay_time not in (None, "") else (
                row[75] if platform == "Lazada" else None
            )
            sale_date = normalize_date(date_value)
            if sale_date is None:
                continue
            source_dates.add(sale_date)
            spec_code = clean_text(row[92])
            if not spec_code:
                continue
            try:
                quantity = int(float(row[98] or 0))
            except (TypeError, ValueError) as exc:
                raise RuntimeError(f"妙手销量数量无法转换：站点={site_code} 规格={spec_code} 值={row[98]}") from exc
            sales[(site_code, sale_date, spec_code)] += quantity

        if not source_dates:
            raise RuntimeError("妙手历史订单没有有效销售日期")

        # 先校验全部国家的日期表头和 SKU 清单，再修改任何业务单元格
        updates = []
        for sheet_name, site_code in COUNTRIES:
            target = workbook.get_sheet_by_name(sheet_name)
            last_column = target.get_last_column()
            date_headers = target.get_range(1, "H", 1, last_column)[0]
            header_map = {
                normalize_date(value): column_name(column_number("H") + offset)
                for offset, value in enumerate(date_headers) if value not in (None, "")
            }
            missing_dates = sorted(source_dates - header_map.keys())
            if missing_dates:
                raise RuntimeError(
                    f"{sheet_name} 缺少日期列：" + "、".join(date.isoformat() for date in missing_dates[:10])
                )
            last_sku_row = target.get_first_free_row_on_column("B") - 1
            if last_sku_row < 2:
                raise RuntimeError(f"{sheet_name} 没有商品规格清单")
            spec_codes = [clean_text(row[0]) for row in target.get_range(2, "B", last_sku_row, "B")]
            target_specs = set(spec_codes)
            matched_sales = defaultdict(int)
            missing_specs = set()
            missing_qty = 0
            for (sales_site, sale_date, source_spec), quantity in sales.items():
                if sales_site != site_code:
                    continue
                matched_spec = source_spec if source_spec in target_specs else None
                if matched_spec is None:
                    code_match = re.search(r"69\d{11,12}", source_spec)
                    if code_match and code_match.group() in target_specs:
                        matched_spec = code_match.group()
                if matched_spec is None:
                    missing_specs.add(source_spec)
                    missing_qty += quantity
                    continue
                matched_sales[(sale_date, matched_spec)] += quantity

            columns = [
                (header_map[sale_date], [[matched_sales.get((sale_date, code), 0)] for code in spec_codes])
                for sale_date in sorted(source_dates)
            ]
            detail = f"重算 {len(source_dates)} 天，{len(spec_codes)} 个 SKU"
            if missing_specs:
                detail += (
                    f"；未匹配规格 {len(missing_specs)} 个 / 销量 {missing_qty} 已跳过"
                    f"（{'、'.join(sorted(missing_specs)[:3])}）"
                )
            updates.append((sheet_name, target, columns, detail))

        # 三国销量和三条成功状态写入同一工作簿，仅在全部成功后保存
        success_time = datetime.now()
        for sheet_name, target, columns, detail in updates:
            for column, values in columns:
                target.set_range(2, column, values)
            set_state(workbook, sheet_name, "成功", detail, success_time=success_time)
            logging.info(f"[{sheet_name}] 更新完成（待保存）：{detail}")
    except Exception as exc:
        detail = f"三国销量整体更新失败：{exc}"
        for name, _ in COUNTRIES:
            results.append({"sheet": name, "status": "failed", "detail": detail,
                            "last_success": states.get(name, {}).get("last_success")})
        raise RuntimeError(detail) from exc

    for sheet_name, _, _, detail in updates:
        results.append({"sheet": sheet_name, "status": "success", "success_time": success_time, "detail": detail})
    return True
