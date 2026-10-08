"""跨境补货工作簿自动更新入口：逐 Sheet 编排任务、维护更新状态并统一通知。"""

import shutil
import traceback
from datetime import datetime
from pathlib import Path

import xbot.excel
from xbot.app import logging
from xbot_extensions.xbot_enhance_tools.dingtalk_message import send_dingtalk_group

from . import (
    update_cerp_products,
    update_country_sales,
    update_miaoshou_shipments,
    update_seaya_stock,
    update_shopee_sku_mapping,
    update_shopee_warehouse,
)
from .config import (
    DINGTALK_WEBHOOK_SECRET,
    DINGTALK_WEBHOOK_URL,
    SNAPSHOT_DIR,
    SNAPSHOT_KEEP_COUNT,
    STATUS_SHEET,
    TARGET_WORKBOOK_PATH,
)
from .utils import parse_time


STATUS_TITLE_ROW = 16
STATUS_HEADER_ROW = 17
STATUS_START_ROW = 18
TRACKED_SHEETS = [
    "雅仓库存",
    "SHOPEE官方仓库存",
    "妙手ERP发货商品明细",
    "C-ERP库存(产品库)",
    "SHOPEE SKU映射",
    "【跨镜】非律宾",
    "【跨镜】马来西亚",
    "【跨镜】泰国",
]


def _read_states(workbook):
    """
    一次读取并检查完整的 RPA 更新状态表，转换为各 Sheet 的五字段状态。

    :param workbook: 本轮已打开的工作簿对象
    :return: 以更新对象为键、包含五个状态字段的字典
    """
    sheet = workbook.get_sheet_by_name(STATUS_SHEET)
    headers = ["更新对象", "最近成功时间", "最近尝试时间", "最近结果", "最近说明"]

    # 连同标题、五列表头和全部任务数据，一次读取 A16:E25
    table = sheet.get_range(STATUS_TITLE_ROW, "A", STATUS_START_ROW + len(TRACKED_SHEETS) - 1, "E")
    title = str(table[0][0] or "").strip()
    if title and title != "RPA更新状态":
        raise RuntimeError(f"RPA 更新状态表标题异常：{title}")
    if not title:
        sheet.set_cell(STATUS_TITLE_ROW, "A", "RPA更新状态")

    actual_headers = [str(value or "").strip() for value in table[1]]
    if any(actual_headers) and actual_headers != headers:
        raise RuntimeError(f"RPA 更新状态表表头不匹配：{actual_headers}")
    if not any(actual_headers):
        sheet.set_range(STATUS_HEADER_ROW, "A", [headers])

    # 完整转换五个字段；即使当前只按最近成功时间判断，也保留其它字段供业务使用
    states = {}
    for row_index, sheet_name in enumerate(TRACKED_SHEETS, start=STATUS_START_ROW):
        row = table[row_index - STATUS_TITLE_ROW]
        actual_name = str(row[0] or "").strip()
        if actual_name and actual_name != sheet_name:
            raise RuntimeError(f"RPA 更新状态表第 {row_index} 行更新对象不匹配：{actual_name}，应为 {sheet_name}")
        if not actual_name:
            if any(value not in (None, "") for value in row[1:]):
                raise RuntimeError(f"RPA 更新状态表第 {row_index} 行缺少更新对象，但已存在状态值")
            sheet.set_cell(row_index, "A", sheet_name)

        last_success = parse_time(row[1])
        last_attempt = parse_time(row[2])
        if row[1] not in (None, "") and last_success is None:
            raise RuntimeError(f"RPA 更新状态表第 {row_index} 行最近成功时间无效：{row[1]}")
        if row[2] not in (None, "") and last_attempt is None:
            raise RuntimeError(f"RPA 更新状态表第 {row_index} 行最近尝试时间无效：{row[2]}")
        states[sheet_name] = {
            "sheet_name": sheet_name,
            "last_success": last_success,
            "last_attempt": last_attempt,
            "last_result": str(row[3] or "").strip(),
            "last_detail": str(row[4] or "").strip(),
        }
    return states


def _set_state(workbook, sheet_name, result, detail, success_time=None):
    """
    在当前工作簿记录某个 Sheet 的本次结果。

    :param workbook: 已打开的目标工作簿
    :param sheet_name: 更新对象 Sheet 名
    :param result: 结果文案，例如 ``成功``、``失败``
    :param detail: 结果说明文本
    :param success_time: 成功时的成功时间
    """
    sheet = workbook.get_sheet_by_name(STATUS_SHEET)
    row = STATUS_START_ROW + TRACKED_SHEETS.index(sheet_name)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 成功时才刷新最近成功时间，其余结果只更新尝试时间和说明
    if success_time is not None:
        sheet.set_cell(row, "B", success_time.strftime("%Y-%m-%d %H:%M:%S"))
    sheet.set_cell(row, "C", now)
    sheet.set_cell(row, "D", result)
    sheet.set_cell(row, "E", str(detail or "")[:500])


def _create_snapshot():
    """
    生成最终工作簿快照，并只保留最近指定数量。

    :return: 快照文件路径
    """
    snapshot_dir = Path(SNAPSHOT_DIR)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    source = Path(TARGET_WORKBOOK_PATH)
    # 按时间戳命名复制一份当前工作簿快照
    snapshot_path = snapshot_dir / f"{source.stem}-{datetime.now():%Y%m%d-%H%M%S}{source.suffix}"
    shutil.copy2(str(source), str(snapshot_path))

    # 按修改时间只保留最近指定数量的快照，删除更早的
    snapshots = sorted(
        snapshot_dir.glob(f"{source.stem}-*{source.suffix}"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for old_path in snapshots[SNAPSHOT_KEEP_COUNT:]:
        old_path.unlink()
    return str(snapshot_path)


def _send_summary(results, snapshot_path, snapshot_error, started_at):
    """
    通过钉钉 Webhook 发送一次最终 Markdown 汇总。

    :param results: 各 Sheet 的执行结果列表
    :param snapshot_path: 快照文件路径，失败时为 ``None``
    :param snapshot_error: 快照失败原因，成功时为 ``None``
    :param started_at: 本次运行开始时间
    """
    if not DINGTALK_WEBHOOK_URL:
        logging.warning("未配置 DINGTALK_WEBHOOK_URL，本次不发送钉钉通知")
        return

    # 统计各状态数量并据此确定汇总标题
    success_count = sum(item["status"] == "success" for item in results)
    skipped_count = sum(item["status"] == "skipped" for item in results)
    failed_count = sum(item["status"] == "failed" for item in results)
    blocked_count = sum(item["status"] == "blocked" for item in results)
    title = "跨境补货数据更新｜完成✅" if not failed_count and not blocked_count else "跨境补货数据更新｜部分异常⚠️"

    lines = [
        f"### {title}",
        "",
        f"> ✅ 成功：**{success_count}**　⏭ 今日已更新：**{skipped_count}**　❌ 失败：**{failed_count}**　⚠️ 未执行：**{blocked_count}**",
        "",
        "#### Sheet 更新结果",
    ]
    # 按状态拼接每个 Sheet 的结果行，失败项附失败原因
    for item in results:
        if item["status"] == "success":
            lines.append(f"✅ **{item['sheet']}**｜成功｜{item['success_time']:%Y-%m-%d %H:%M:%S}｜{item.get('detail') or '已更新'}")
        elif item["status"] == "skipped":
            last_success = item.get("last_success")
            when = last_success.strftime("%Y-%m-%d %H:%M:%S") if last_success else "未知"
            lines.append(f"⏭ **{item['sheet']}**｜今日已更新，跳过｜最近成功：{when}")
        elif item["status"] == "blocked":
            last_success = item.get("last_success")
            success_text = last_success.strftime("%Y-%m-%d %H:%M:%S") if last_success else "无"
            lines.append(f"⚠️ **{item['sheet']}**｜未执行｜最近成功：{success_text}｜{item.get('detail') or '依赖未就绪'}")
        else:
            last_success = item.get("last_success")
            success_text = last_success.strftime("%Y-%m-%d %H:%M:%S") if last_success else "无"
            lines.append(f"❌ **{item['sheet']}**｜失败｜上次成功：{success_text}")
            lines.append(f"> ❌ **失败原因**：{item.get('detail') or '未知错误'}")

    # 附加快照结果和本次运行区间
    if snapshot_path:
        lines.extend(["", f"📁 **快照**：`{snapshot_path}`"])
    elif snapshot_error:
        lines.extend(["", f"> ⚠️ **快照生成失败**：{snapshot_error}"])
    lines.extend([
        "",
        "---",
        f"🕒 **运行区间**：{started_at:%Y-%m-%d %H:%M:%S} ～ {datetime.now():%Y-%m-%d %H:%M:%S}",
    ])

    # 增强工具2026 / dingtalk_message.send_dingtalk_group：
    # 业务功能：通过群机器人 Webhook 发送 Markdown；message_type=消息类型，content=正文，
    # title=Markdown 标题，webhook_url=机器人地址，webhook_secret=可选加签密钥。
    send_dingtalk_group(
        "markdown",
        "\n".join(lines),
        title=title,
        webhook_url=DINGTALK_WEBHOOK_URL,
        webhook_secret=DINGTALK_WEBHOOK_SECRET or None,
    )


def _update_data_source(workbook, results, states, sheet_name, prepare, apply_update):
    """
    独立完成一个 Sheet 的数据准备、写入、保存和失败恢复。

    :param workbook: 本轮共享的工作簿，异常时可能被重新打开
    :param results: 各 Sheet 的执行结果列表
    :param states: 状态区各 Sheet 的状态字典
    :param sheet_name: 更新对象 Sheet 名
    :param prepare: 下载并准备数据的函数
    :param apply_update: 写入目标工作簿的函数
    :return: 当前可继续使用的工作簿对象
    """
    state = states.get(sheet_name, {})
    last_success = state.get("last_success")
    if last_success and last_success.date() == datetime.now().date():
        results.append({"sheet": sheet_name, "status": "skipped", "last_success": last_success})
        return workbook

    try:
        # 下载失败只记录该任务失败，继续保存失败状态
        try:
            logging.info(f"[{sheet_name}] 开始更新")
            payload = prepare()
        except Exception as exc:
            detail = str(exc).strip() or exc.__class__.__name__
            logging.error(f"[{sheet_name}] 下载失败：{detail}\n{traceback.format_exc()}")
            results.append({"sheet": sheet_name, "status": "failed", "detail": detail, "last_success": last_success})
            try:
                _set_state(workbook, sheet_name, "失败", detail)
            except Exception as state_exc:
                raise RuntimeError(f"{sheet_name} 失败状态写入失败") from state_exc
        else:
            # 原始数据及成功状态在本任务的一次保存中落盘
            try:
                detail = apply_update(workbook, payload)
                success_time = datetime.now()
                _set_state(workbook, sheet_name, "成功", detail, success_time=success_time)
            except Exception as exc:
                results.append({
                    "sheet": sheet_name, "status": "failed", "detail": f"{sheet_name} 写入失败：{exc}",
                    "last_success": last_success,
                })
                raise RuntimeError(f"{sheet_name} 写入失败") from exc
            results.append({"sheet": sheet_name, "status": "success", "success_time": success_time, "detail": detail})
            logging.info(f"[{sheet_name}] 更新完成（待保存）：{detail}")
    except Exception as exc:
        # 写入中途失败时放弃当前未保存修改，恢复上一个已保存版本
        logging.error(f"[{sheet_name}] 写入失败，丢弃本任务未保存改动：{exc}\n{traceback.format_exc()}")
        workbook = _discard_unsaved_and_reopen(workbook, Path(TARGET_WORKBOOK_PATH))
        try:
            _set_state(workbook, sheet_name, "失败", str(exc))
            workbook.save()
        except Exception as save_exc:
            # 避免恢复后打开的新工作簿因保存失败遗留后台占用
            try:
                workbook.set_saved(True)
                workbook.close()
            except Exception as close_exc:
                logging.error(f"[{sheet_name}] 恢复工作簿关闭失败：{close_exc}")
            raise RuntimeError(f"{sheet_name} 失败状态保存失败，正式文件状态待核实") from save_exc
        return workbook

    # 无论是成功数据还是下载失败状态，都在当前任务结束时持久化
    try:
        workbook.save()
    except Exception as exc:
        for item in results:
            if item["sheet"] == sheet_name and item["status"] == "success":
                item.update(
                    status="failed", detail=f"保存失败，正式文件状态待核实：{exc}",
                    last_success=last_success,
                )
        raise RuntimeError(f"{sheet_name} 保存失败，正式文件状态待核实") from exc
    if results[-1]["status"] == "success":
        logging.info(f"[{sheet_name}] 已独立保存")
    return workbook


def _discard_unsaved_and_reopen(workbook, target):
    """
    丢弃失败任务在内存中未保存的写入，重新打开上次已保存的工作簿。

    :param workbook: 当前工作簿
    :param target: 正式文件路径
    :return: 重新打开的工作簿
    """
    workbook.set_saved(True)
    workbook.close()
    return xbot.excel.open(file_name=str(target), kind="wps", visible=False, update_links=False)


def main(args):
    """共用一个工作簿会话，普通 Sheet 独立保存，三国销量整体保存。"""
    started_at = datetime.now()
    results = []
    target = Path(TARGET_WORKBOOK_PATH)
    workbook = None
    states = {}
    miaoshou_payload = None
    miaoshou_error = None

    def get_miaoshou_payload():
        """本轮只下载一次妙手历史订单，供明细和国家销量独立使用。"""
        nonlocal miaoshou_payload, miaoshou_error
        if miaoshou_payload is None and miaoshou_error is None:
            try:
                miaoshou_payload = update_miaoshou_shipments.prepare()
            except Exception as exc:
                miaoshou_error = exc
        if miaoshou_error is not None:
            raise RuntimeError(f"妙手历史订单下载失败：{miaoshou_error}") from miaoshou_error
        return miaoshou_payload

    try:
        # 打开正式工作簿前检查占用，避免影响人工编辑
        if target.with_name(f"~${target.name}").exists():
            raise RuntimeError(f"目标工作簿正在被占用，请先关闭：{target.name}")

        # WPS 直接打开正式文件，所有模块共享同一个工作簿对象
        workbook = xbot.excel.open(file_name=str(target), kind="wps", visible=False, update_links=False)
        states = _read_states(workbook)

        # 五个普通 Sheet 按固定业务顺序执行；各任务内部独立保存并恢复写入失败
        workbook = _update_data_source(workbook, results, states, "雅仓库存", update_seaya_stock.prepare, update_seaya_stock.apply_update)
        workbook = _update_data_source(workbook, results, states, "SHOPEE官方仓库存", update_shopee_warehouse.prepare, update_shopee_warehouse.apply_update)
        workbook = _update_data_source(workbook, results, states, "妙手ERP发货商品明细", get_miaoshou_payload, update_miaoshou_shipments.apply_update)
        workbook = _update_data_source(workbook, results, states, "C-ERP库存(产品库)", update_cerp_products.prepare, update_cerp_products.apply_update)
        workbook = _update_data_source(workbook, results, states, "SHOPEE SKU映射", update_shopee_sku_mapping.prepare, update_shopee_sku_mapping.apply_update)

        # 三国作为一个任务：直接使用妙手原始文件，全部写入成功才保存
        try:
            changed = update_country_sales.update_all(workbook, results, states, _set_state, get_miaoshou_payload)
        except Exception as exc:
            logging.error(f"[国家销量更新] 三国未保存，丢弃本任务修改：{exc}\n{traceback.format_exc()}")
            workbook = _discard_unsaved_and_reopen(workbook, target)
            for name, _ in update_country_sales.COUNTRIES:
                _set_state(workbook, name, "失败", str(exc))
            try:
                workbook.save()
            except Exception as save_exc:
                raise RuntimeError("三国销量失败状态保存失败，正式文件状态待核实") from save_exc
        else:
            if changed:
                try:
                    workbook.save()
                except Exception as exc:
                    for item in results:
                        if item["sheet"] in dict(update_country_sales.COUNTRIES) and item["status"] == "success":
                            item.update(status="failed", detail=f"保存失败，正式文件状态待核实：{exc}",
                                        last_success=states.get(item["sheet"], {}).get("last_success"))
                    raise RuntimeError("三国销量整体保存失败，正式文件状态待核实") from exc
                logging.info("[国家销量更新] 三国已统一保存")

        # 所有任务已独立保存，关闭工作簿
        workbook.close()
        workbook = None
    except Exception as exc:
        detail = str(exc).strip() or exc.__class__.__name__
        logging.error(f"工作簿更新中断（已保存任务保留）：{detail}\n{traceback.format_exc()}")
        completed = {item["sheet"] for item in results}
        results.extend(
            {"sheet": name, "status": "blocked", "detail": f"整轮中断，未执行：{detail}", "last_success": states.get(name, {}).get("last_success")}
            for name in TRACKED_SHEETS if name not in completed
        )
        results.append({"sheet": "整轮更新", "status": "failed", "detail": detail, "last_success": None})
    finally:
        # 异常路径关闭工作簿，不保存当前任务未完成的写入
        if workbook is not None:
            try:
                workbook.set_saved(True)
                workbook.close()
            except Exception as exc:
                logging.error(f"关闭 Excel 失败：{exc}\n{traceback.format_exc()}")

    snapshot_path = None
    snapshot_error = None
    # 本轮有成功更新时生成历史快照，失败只记录不影响结果
    if any(item["status"] == "success" for item in results):
        try:
            snapshot_path = _create_snapshot()
        except Exception as exc:
            snapshot_error = str(exc).strip() or exc.__class__.__name__
            logging.error(f"生成历史快照失败：{exc}\n{traceback.format_exc()}")

    # 发送最终钉钉汇总，通知失败也不影响已完成的更新结果
    try:
        _send_summary(results, snapshot_path, snapshot_error, started_at)
    except Exception as exc:
        logging.error(f"钉钉通知发送失败：{exc}\n{traceback.format_exc()}")

    return results
