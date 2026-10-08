"""跨模块公共能力：文本/日期/列号转换、下载文件读取、RAW 区写入、钉钉凭证读取。"""

import time
from datetime import datetime, timedelta
from pathlib import Path

import xbot.excel
from xbot.app import logging

from .config import (
    DINGTALK_BASE_ID,
    DINGTALK_CLIENT_ID,
    DINGTALK_CLIENT_SECRET,
    DINGTALK_USER_ID,
    SHEET_ID_SEAYA_CRED,
    SHEET_ID_SHOPEE_CRED,
)


def parse_time(value):
    """
    把配置区的时间值统一转换为 ``datetime``。

    :param value: 工作簿单元格值或文本
    :return: 解析后的 ``datetime``，无法识别时返回 ``None``
    """
    if isinstance(value, datetime):
        return value
    if value in (None, ""):
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def column_number(name):
    """
    把 Excel 列名转换成从 1 开始的列号。

    :param name: Excel 列名，例如 ``F``、``AA``
    :return: 从 1 开始的列号
    """
    result = 0
    for char in str(name).upper():
        if not "A" <= char <= "Z":
            raise ValueError(f"无效列名：{name}")
        result = result * 26 + ord(char) - ord("A") + 1
    return result


def column_name(number):
    """
    把从 1 开始的列号转换成 Excel 列名。

    :param number: 从 1 开始的列号
    :return: Excel 列名，例如 ``F``、``AA``
    """
    if number <= 0:
        raise ValueError(f"无效列号：{number}")
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def clean_text(value):
    """
    把外部数据字段转换成去除首尾空白的文本。

    :param value: 任意单元格值
    :return: 清理后的文本
    """
    return str(value or "").replace("\u00a0", " ").strip()


def preserve_excel_scalar(value):
    """
    避免超长数字 ID 写回 Excel 后发生 15 位精度截断。

    :param value: 原始单元格值
    :return: 需要保护时返回带前导 ``'`` 的文本，否则原样返回
    """
    # 超 15 位整数写回 Excel 会精度截断，加前导引号转文本
    if isinstance(value, int) and abs(value) >= 10 ** 15:
        return "'" + str(value)
    # 16 位以上纯数字文本同样加前导引号保护
    if isinstance(value, str):
        normalized = value.strip()
        digits = normalized[1:] if normalized[:1] in ("+", "-") else normalized
        if len(digits) >= 16 and digits.isdigit():
            return "'" + value
    return value


def normalize_date(value):
    """
    把 Excel / 文本日期转换成 ``date``。

    :param value: 单元格值或日期文本
    :return: 归一化后的 ``date``，空值返回 ``None``
    """
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
        return value
    if isinstance(value, (int, float)):
        # Excel 序列号日期从 1899-12-30 起算
        return (datetime(1899, 12, 30) + timedelta(days=float(value))).date()
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"无法识别日期：{value}")


def load_excel_matrix(file_path):
    """
    读取下载 Excel 的首个工作表并返回完整二维数据。

    :param file_path: 下载文件路径
    :return: 补齐宽度后的二维数据矩阵
    """
    # 打开下载文件读取首个工作表的完整数据
    workbook = xbot.excel.open(
        file_name=str(file_path),
        kind="openpyxl",
        visible=False,
        ignore_formula=False,
        update_links=False,
    )
    try:
        data = workbook.get_sheet_by_index(1).get_used_range()
    finally:
        workbook.close()

    if not data or not data[0]:
        raise RuntimeError(f"下载文件为空：{Path(file_path).name}")

    # 补齐每行宽度，避免后续按列索引访问越界
    width = max(len(row) for row in data)
    return [
        [preserve_excel_scalar(value) for value in row] + [None] * (width - len(row))
        for row in data
    ]


def validate_headers(data, required_headers, header_rows=1):
    """
    校验下载文件前若干表头行包含当前业务所需字段。

    :param data: 下载文件二维数据
    :param required_headers: 必须出现的字段名列表
    :param header_rows: 表头占用的行数
    """
    header_text = {clean_text(value) for row in data[:header_rows] for value in row if clean_text(value)}
    missing = [header for header in required_headers if header not in header_text]
    if missing:
        raise RuntimeError(f"下载文件缺少必要字段：{'、'.join(missing)}")


def validate_raw_layout(sheet_name, data, layout):
    """
    校验 RAW 关键列仍处于左侧公式所依赖的固定位置。

    :param sheet_name: 目标工作簿 Sheet 名
    :param data: 下载文件二维数据
    :param layout: 该 Sheet 的 RAW 布局配置
    """
    for row_index, column_index, expected in layout["expected_headers"]:
        if row_index >= len(data) or column_index >= len(data[row_index]):
            raise RuntimeError(f"{sheet_name} 原始导出列结构不完整：缺少 {expected}")
        actual = clean_text(data[row_index][column_index])
        if actual != expected:
            raise RuntimeError(
                f"{sheet_name} 原始导出列结构已变化：第 {column_index + 1} 列应为“{expected}”，实际为“{actual or '空'}”"
            )


def replace_raw_area(workbook, sheet_name, data, layout):
    """
    清空指定 Sheet 右侧旧 RAW 区，再完整写入本轮数据。

    :param workbook: 已打开的目标工作簿
    :param sheet_name: 目标工作簿 Sheet 名
    :param data: 下载文件二维数据
    :param layout: 该 Sheet 的 RAW 布局配置
    :return: 写入结果描述文本
    """
    validate_raw_layout(sheet_name, data, layout)
    sheet = workbook.get_sheet_by_name(sheet_name)
    start_col = layout["start_col"]
    start_number = column_number(start_col)

    # 计算本轮数据右侧边界，清空范围取旧 RAW 区与新区的外沿
    new_width = max(len(row) for row in data)
    new_end_col = column_name(start_number + new_width - 1)
    current_last_col = sheet.get_last_column() or start_col
    clear_end_col = (
        current_last_col
        if column_number(current_last_col) >= column_number(new_end_col)
        else new_end_col
    )
    clear_end_row = max(sheet.get_first_free_row(), len(data) + 1)

    # 清空旧内容后分批写入本轮完整数据
    sheet.clear_range(1, start_col, clear_end_row, clear_end_col, target="content")
    for start in range(0, len(data), 500):
        sheet.set_range(1 + start, start_col, data[start:start + 500])

    # 数据行数按去掉表头行统计
    data_rows = max(len(data) - layout["header_rows"], 0)
    return f"写入 {data_rows} 条，{new_width} 列"


def fetch_ai_table_records(sheet_id):
    """
    从现有钉钉 AI 表格凭证表读取全部记录。

    :param sheet_id: 凭证数据表 ID
    :return: 记录字段字典列表
    """
    # 市场指令依赖缺失时直接给出明确提示
    try:
        from xbot_extensions.activity_5b77c4ce.croe import yd_ai_table_action
    except ImportError as exc:
        raise RuntimeError("当前应用缺少钉钉 AI 表格市场指令依赖 activity_5b77c4ce") from exc

    # 读取失败最多重试 4 次，每次间隔 5 秒
    result = None
    for attempt in range(4):
        try:
            # 钉钉 AI 表格市场指令：分页读取指定凭证表。
            # action=读取动作；client_id/client_secret=应用凭证；base_id=Base；
            # user_id=操作者；sheet=数据表；params=分页大小与页数上限。
            result = yd_ai_table_action(
                action="获取多行记录分页",
                client_id=DINGTALK_CLIENT_ID,
                client_secret=DINGTALK_CLIENT_SECRET,
                base_id=DINGTALK_BASE_ID,
                user_id=DINGTALK_USER_ID,
                sheet=sheet_id,
                params={"page_size": 100, "max_pages": 20},
            )
        except Exception as exc:
            result = {"ok": False, "error": exc}

        if result.get("ok"):
            break
        if attempt < 3:
            logging.warning(f"读取凭证表失败，第 {attempt + 1} 次重试")
            time.sleep(5)

    if not result.get("ok"):
        raise RuntimeError(f"读取钉钉 AI 表格凭证失败：{result.get('error')}")
    # 分页未读完时直接失败，避免使用不完整的凭证数据
    if result["data"].get("hasMore"):
        raise RuntimeError("读取钉钉 AI 表格凭证分页未完成")
    return [record.get("fields", {}) for record in result["data"].get("records", [])]


def get_shop_credential(platform):
    """
    按平台独立读取现有钉钉凭证表，避免一个凭证源故障阻塞其它任务。

    :param platform: 凭证平台，``seaya`` 或 ``shopee``
    :return: 含 ``username`` / ``password`` 的凭证字典
    """
    # 按平台选择对应凭证表和账号字段名
    if platform == "seaya":
        records = fetch_ai_table_records(SHEET_ID_SEAYA_CRED)
        username_field, password_field = "ACCOUNT", "PASSWORD"
    elif platform == "shopee":
        records = fetch_ai_table_records(SHEET_ID_SHOPEE_CRED)
        username_field, password_field = "USERNAME", "PASSWORD"
    else:
        raise ValueError(f"不支持的凭证平台：{platform}")

    # 取首条记录作为当前账号，并校验账号密码完整
    if not records:
        raise RuntimeError(f"{platform} 凭证表为空")
    credential = {
        "username": clean_text(records[0].get(username_field)),
        "password": clean_text(records[0].get(password_field)),
    }
    if not credential["username"] or not credential["password"]:
        raise RuntimeError(f"{platform} 凭证缺少账号或密码")
    return credential
