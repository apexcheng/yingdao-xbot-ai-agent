"""SQLite 数据库层：负责预警去重与处理结果、ERP 铺货映射和运行状态的持久化。"""

import csv
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from .config import PROJECT_DIR, STOCK_UPDATE_MAX_ATTEMPTS

DATABASE_PATH = PROJECT_DIR / "inventory_monitor.db"


def init_database():
    """初始化 SQLite 表结构（已存在则跳过）。"""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                shop_name TEXT NOT NULL,
                notification_time TEXT NOT NULL,
                message_type TEXT NOT NULL,
                product_id TEXT NOT NULL,
                sku_key TEXT NOT NULL,
                sku_id TEXT,
                erp_code TEXT,
                spec_name TEXT,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                erp_available_qty INTEGER,
                stock_before INTEGER,
                added_qty INTEGER,
                stock_after INTEGER,
                result_note TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(platform, shop_name, notification_time, product_id, sku_key)
            )
            """
        )
        cursor = conn.execute("PRAGMA table_info(alerts)")
        columns = [row[1] for row in cursor.fetchall()]
        if "last_error" in columns and "result_note" not in columns:
            conn.execute("ALTER TABLE alerts RENAME COLUMN last_error TO result_note")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS erp_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                platform_product_id TEXT NOT NULL,
                platform_sku_id TEXT NOT NULL,
                system_item_code TEXT NOT NULL,
                system_sku_code TEXT NOT NULL,
                source_file TEXT NOT NULL,
                source_updated_at TEXT NOT NULL,
                loaded_at TEXT NOT NULL,
                raw_data TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_erp_inventory_lookup "
            "ON erp_inventory(platform, platform_product_id, platform_sku_id)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )


def get_last_cleanup_at():
    """查询上次 SQLite 历史清理时间。"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        row = conn.execute("SELECT value FROM system_state WHERE key = 'last_cleanup_at'").fetchone()
    return row[0] if row else None


def get_last_run_summary_at():
    """查询上次全局运行汇总窗口结束时间。"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        row = conn.execute("SELECT value FROM system_state WHERE key = 'last_run_summary_at'").fetchone()
    return row[0] if row else None


def set_last_run_summary_at(summary_at):
    """保存全局运行汇总窗口结束时间。"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO system_state (key, value) VALUES ('last_run_summary_at', ?)",
            (summary_at,),
        )


def get_alert_results_between(started_at, finished_at):
    """读取汇总时间窗口内最后一次更新的 SKU 处理事实。"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT platform, shop_name, status, result_note, updated_at
            FROM alerts
            WHERE updated_at > ? AND updated_at <= ?
            ORDER BY platform, shop_name, updated_at
            """,
            (started_at, finished_at),
        ).fetchall()
    return [dict(row) for row in rows]


def cleanup_history(retention_days):
    """删除保留天数之外的预警及处理结果历史。"""
    now = datetime.now()
    cutoff = (now - timedelta(days=retention_days)).strftime("%Y-%m-%d %H:%M:%S")
    cleaned_at = now.strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("DELETE FROM alerts WHERE created_at < ?", (cutoff,))
        conn.execute(
            "INSERT OR REPLACE INTO system_state (key, value) VALUES ('last_cleanup_at', ?)",
            (cleaned_at,),
        )


def get_erp_inventory_state(platform):
    """查询平台 ERP 铺货数据的记录数与最后导入时间。"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        row = conn.execute(
            "SELECT COUNT(*), MAX(loaded_at) FROM erp_inventory WHERE platform = ?",
            (platform,),
        ).fetchone()
    return {"row_count": row[0], "loaded_at": row[1]}


def replace_erp_inventory_from_csv(platform, csv_path):
    """用铺货 CSV 全量替换指定平台的 ERP 库存数据。"""
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"ERP铺货CSV不存在：{path}")

    rows = None
    last_decode_error = None
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            with path.open("r", encoding=encoding, newline="") as file:
                reader = csv.DictReader(file)
                if reader.fieldnames:
                    reader.fieldnames = [field.strip() for field in reader.fieldnames]
                field_aliases = {
                    "平台商品ID": ("平台商品ID", "商品编号"),
                    "平台规格ID": ("平台规格ID", "平台规格Id"),
                    "系统商品代码": ("系统商品代码",),
                    "系统规格代码": ("系统规格代码",),
                }
                resolved_fields = {
                    field: next((alias for alias in aliases if alias in (reader.fieldnames or [])), None)
                    for field, aliases in field_aliases.items()
                }
                missing_fields = [field for field, actual_field in resolved_fields.items() if actual_field is None]
                if missing_fields:
                    raise RuntimeError(f"ERP铺货CSV缺少必要字段：{', '.join(missing_fields)}")
                rows = list(reader)
            break
        except UnicodeDecodeError as exc:
            last_decode_error = exc

    if rows is None:
        raise RuntimeError("ERP铺货CSV编码无法识别") from last_decode_error
    if not rows:
        raise RuntimeError("ERP铺货CSV没有可导入数据")

    source_updated_at = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    loaded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records = []
    for row in rows:
        product_id = str(row.get(resolved_fields["平台商品ID"], "")).strip()
        sku_id = str(row.get(resolved_fields["平台规格ID"], "")).strip()
        item_code = str(row.get(resolved_fields["系统商品代码"], "")).strip()
        sku_code = str(row.get(resolved_fields["系统规格代码"], "")).strip()
        item_code = "" if item_code.lower() == "null" else item_code
        sku_code = "" if sku_code.lower() == "null" else sku_code
        if not product_id or not sku_id or (not item_code and not sku_code):
            continue
        records.append(
            (
                platform,
                product_id,
                sku_id,
                item_code,
                sku_code,
                path.name,
                source_updated_at,
                loaded_at,
                json.dumps(row, ensure_ascii=False),
            )
        )
    if not records:
        raise RuntimeError("ERP铺货CSV没有完整的商品ID / 规格ID / 系统商品代码 / 系统规格代码记录")

    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("DELETE FROM erp_inventory WHERE platform = ?", (platform,))
        conn.executemany(
            """
            INSERT INTO erp_inventory (
                platform, platform_product_id, platform_sku_id,
                system_item_code, system_sku_code, source_file,
                source_updated_at, loaded_at, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            records,
        )
    return len(records)


def get_erp_codes(platform, product_id, sku_id):
    """按平台商品ID + 规格ID 查询系统商品代码与系统规格代码。"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT system_item_code, system_sku_code
            FROM erp_inventory
            WHERE platform = ? AND platform_product_id = ? AND platform_sku_id = ?
            """,
            (platform, str(product_id), str(sku_id)),
        ).fetchall()
    return [dict(row) for row in rows]


def get_or_create_alert(platform, shop_name, notification_time, message_type, product_id, sku_key):
    """按唯一键取预警，不存在则新建 pending 记录。"""
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute(
            """
            INSERT OR IGNORE INTO alerts (
                platform, shop_name, notification_time, message_type,
                product_id, sku_key, attempt_count, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 0, 'pending', ?, ?)
            """,
            (platform, shop_name, notification_time, message_type, str(product_id), str(sku_key), created_at, created_at),
        )
        row = conn.execute(
            """
            SELECT * FROM alerts
            WHERE platform = ? AND shop_name = ? AND notification_time = ?
              AND product_id = ? AND sku_key = ?
            """,
            (platform, shop_name, notification_time, str(product_id), str(sku_key)),
        ).fetchone()
    return dict(row)


def get_alert(platform, shop_name, notification_time, product_id, sku_key):
    """按预警唯一键查询现有记录，不存在时返回 None。"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT * FROM alerts
            WHERE platform = ? AND shop_name = ? AND notification_time = ?
              AND product_id = ? AND sku_key = ?
            """,
            (platform, shop_name, notification_time, str(product_id), str(sku_key)),
        ).fetchone()
    return dict(row) if row else None


def get_retry_alert_ids(platform, shop_name):
    """读取当前店铺本轮需要继续在消息列表中查找的预警记录ID。"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        rows = conn.execute(
            """
            SELECT id
            FROM alerts
            WHERE platform = ? AND shop_name = ?
              AND status IN ('pending', 'failed') AND attempt_count < ?
            """,
            (platform, shop_name, STOCK_UPDATE_MAX_ATTEMPTS),
        ).fetchall()
    return {row[0] for row in rows}


def save_alert_result(
    alert_id,
    sku_id,
    erp_code,
    spec_name,
    attempt_count,
    status,
    erp_available_qty=None,
    stock_before=None,
    added_qty=None,
    stock_after=None,
    result_note=None,
):
    """将本次 SKU 处理结果整体覆盖写回对应预警行。"""
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            UPDATE alerts SET
                sku_id = ?, erp_code = ?, spec_name = ?,
                attempt_count = ?, status = ?,
                erp_available_qty = ?, stock_before = ?,
                added_qty = ?, stock_after = ?, result_note = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                str(sku_id) if sku_id else None,
                str(erp_code) if erp_code else None,
                spec_name,
                attempt_count,
                status,
                erp_available_qty,
                stock_before,
                added_qty,
                stock_after,
                result_note,
                updated_at,
                alert_id,
            ),
        )
    return updated_at
