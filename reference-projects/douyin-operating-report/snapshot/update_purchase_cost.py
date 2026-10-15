"""从航桥读取采购成本，按规格代码比较后同步 Excel 原始数据区域。"""

import json
from decimal import Decimal, InvalidOperation
from urllib import request

from xbot.app import logging

from .config import PURCHASE_COST_API_TOKEN, PURCHASE_COST_API_URL


FIELDS = ("商品代码", "规格代码", "规格名称", "成本（未税）")
PAGE_SIZE = 1000
DIRECT_HTTP = request.build_opener(request.ProxyHandler({}))


def _load_rows():
    if not PURCHASE_COST_API_TOKEN:
        raise RuntimeError("未配置航桥采购成本只读 Token")
    records = []
    total = None
    page = 1
    while True:
        payload = json.dumps({"page": page, "page_size": PAGE_SIZE, "sort": [{"field": "id", "direction": "asc"}]}).encode("utf-8")
        req = request.Request(
            PURCHASE_COST_API_URL,
            data=payload,
            headers={"Authorization": f"Bearer {PURCHASE_COST_API_TOKEN}", "Content-Type": "application/json"},
            method="POST",
        )
        with DIRECT_HTTP.open(req, timeout=30) as response:
            result = json.load(response)
        if "error" in result:
            raise RuntimeError(f"航桥采购成本查询失败：{result.get('error')}")
        if "data" not in result:
            raise RuntimeError("航桥采购成本返回格式无效")
        data = result["data"]
        paging = data["pagination"]
        if paging["page"] != page or paging["page_size"] != PAGE_SIZE:
            raise RuntimeError("航桥采购成本分页参数不一致")
        if total is None:
            total = paging["total"]
        if paging["total"] != total:
            raise RuntimeError("航桥采购成本同步期间数据总量发生变化")
        records.extend(data["records"])
        if len(records) >= total:
            break
        if not data["records"]:
            raise RuntimeError("航桥采购成本分页提前结束")
        page += 1

    if not records or len(records) != total:
        raise RuntimeError("航桥采购成本返回记录不完整或为空")
    rows = []
    spec_codes = set()
    record_ids = set()
    for item in records:
        if item["id"] in record_ids:
            raise RuntimeError("航桥采购成本分页出现重复记录")
        record_ids.add(item["id"])
        values = [item[field] for field in FIELDS]
        if any(value is None or value == "" for value in values):
            raise ValueError(f"航桥采购成本存在空字段：记录ID={item['id']}")
        spec = str(values[1]).strip()
        if spec in spec_codes:
            raise ValueError(f"航桥采购成本规格代码重复：{spec}")
        spec_codes.add(spec)
        try:
            cost = Decimal(str(values[3]))
        except InvalidOperation as exc:
            raise ValueError(f"航桥采购成本不是数字：{spec}") from exc
        if not cost.is_finite():
            raise ValueError(f"航桥采购成本数值无效：{spec}")
        rows.append([str(values[0]).strip(), spec, str(values[2]).strip(), float(cost)])
    return rows


def _compare_value(row):
    """比较原始内容；不要把文本类型的规格代码转为数字。"""
    return (
        str(row[0] or "").strip().lstrip("'"),
        str(row[1] or "").strip().lstrip("'"),
        str(row[2] or "").strip(),
        Decimal(str(row[3])) if row[3] is not None and row[3] != "" else None,
    )


def changed_codes(old_rows, new_rows):
    old = {_compare_value(row)[1]: _compare_value(row) for row in old_rows if row[1] is not None and row[1] != ""}
    new = {_compare_value(row)[1]: _compare_value(row) for row in new_rows}
    return sorted(key for key in old.keys() | new.keys() if old.get(key) != new.get(key))


def update(target_workbook):
    new_rows = _load_rows()  # 全量获取、校验后才允许动 Excel。
    sheet = target_workbook.get_sheet_by_name("【基源】采购成本")
    last_row = sheet.get_first_free_row() - 1
    old_rows = sheet.get_range(2, "D", last_row, "G") if last_row >= 2 else []
    changes = changed_codes(old_rows, new_rows)
    if not changes:
        logging.info(f"【采购成本】{len(new_rows)}条已核对，没有变化")
        return []

    # 仅同步 D:G 的内容，保留 D1:G1 表头、A:C 的公式接口和格式。
    # 规格代码为文本，写入前加单引号以防 WPS 将数字样式的代码自动转换为数值。
    write_rows = [["'" + row[0], "'" + row[1], row[2], row[3]] for row in new_rows]
    try:
        if last_row >= 2:
            sheet.clear_range(2, "D", last_row, "G", target="content")
        sheet.set_range(2, "D", write_rows)
    except Exception:
        # 如果 WPS 写入异常，恢复本轮改写前的内容，避免主流程统一保存半成品。
        sheet.clear_range(2, "D", max(last_row, len(write_rows) + 1), "G", target="content")
        if old_rows:
            sheet.set_range(2, "D", old_rows)
        raise
    logging.info(f"【采购成本】同步完成｜总行数={len(new_rows)}｜变更规格代码={len(changes)}")
    return changes
