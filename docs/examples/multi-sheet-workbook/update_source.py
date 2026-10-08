"""示例数据源：准备 CSV，写入专用订单 RAW Sheet。"""

import csv
from datetime import datetime
from pathlib import Path

from .config import SOURCE_CSV_PATH


def prepare():
    """
    读取并校验本轮来源 CSV，返回完整表头和数据。

    :return: 可写入订单数据 Sheet 的二维列表
    """
    with Path(SOURCE_CSV_PATH).open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))

    if not rows or rows[0] != ["日期", "地区", "销量"] or len(rows) < 2:
        raise RuntimeError("CSV 必须包含日期、地区、销量表头和至少一条数据")

    # 先完成全部源数据校验；不允许写入一半才发现非法数量
    for index, row in enumerate(rows[1:], start=2):
        if len(row) != 3 or row[1] not in ("北区", "南区"):
            raise RuntimeError(f"CSV 第 {index} 行地区或列数异常")
        datetime.strptime(row[0], "%Y-%m-%d")
        if not row[2].isdigit():
            raise RuntimeError(f"CSV 第 {index} 行销量必须为非负整数")
        row[2] = int(row[2])
    return rows


def apply_update(workbook, rows):
    """
    覆盖订单数据 Sheet 的 A:C RAW 区，保留其它区域。

    :param workbook: 主流程已经打开的共享工作簿
    :param rows: 已完整校验的来源二维数据
    :return: 实际写入的订单行数说明
    """
    sheet = workbook.get_sheet_by_name("订单数据")
    last_row = sheet.get_first_free_row() - 1
    if last_row >= 2:
        sheet.clear_range(2, "A", last_row, "C", target="content")
    sheet.set_range(1, "A", rows)
    return f"写入 {len(rows) - 1} 条订单"
