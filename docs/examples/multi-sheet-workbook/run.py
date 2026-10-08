"""教学示例：共享一个 Excel 工作簿，按业务顺序更新后统一保存。"""

import traceback
from datetime import datetime
from pathlib import Path

import xbot.excel
from xbot.app import logging

from . import update_country_sales, update_source
from .config import TARGET_WORKBOOK_PATH


STATUS_NAMES = ("订单数据", "地区销量")
STATUS_HEADERS = ["更新对象", "最近成功时间", "最近尝试时间", "最近结果", "最近说明"]


def _read_status_table(workbook):
    """
    一次读取整张示例状态表，并按更新对象转换完整的五字段状态。

    :param workbook: 本轮共享的 Excel 工作簿
    :return: 以更新对象名称为键的状态字典
    """
    sheet = workbook.get_sheet_by_name("RPA配置区")
    table = sheet.get_range(1, "A", 4, "E")
    if table[0][0] != "RPA更新状态" or table[1] != STATUS_HEADERS:
        raise RuntimeError("RPA 更新状态表标题或五列表头不匹配")

    states = {}
    for name, row in zip(STATUS_NAMES, table[2:]):
        if row[0] != name:
            raise RuntimeError(f"RPA 更新状态表行身份不匹配：应为 {name}，实际 {row[0]}")

        # 日期字段转换为 datetime；其余字段也完整保留，不因当前未用而丢弃
        last_success = row[1] if isinstance(row[1], datetime) else (
            datetime.strptime(str(row[1]), "%Y-%m-%d %H:%M:%S") if row[1] not in (None, "") else None
        )
        last_attempt = row[2] if isinstance(row[2], datetime) else (
            datetime.strptime(str(row[2]), "%Y-%m-%d %H:%M:%S") if row[2] not in (None, "") else None
        )
        states[name] = {
            "sheet_name": name,
            "last_success": last_success,
            "last_attempt": last_attempt,
            "last_result": str(row[3] or "").strip(),
            "last_detail": str(row[4] or "").strip(),
        }
    return states


def _set_status(workbook, name, result, detail, success_time=None):
    """
    在本轮工作簿中更新一个任务的状态，不提前保存。

    :param workbook: 本轮共享的 Excel 工作簿
    :param name: 已配置的更新对象名称
    :param result: 成功、失败或未执行
    :param detail: 本轮结果说明
    :param success_time: 本次真正成功写入业务数据的时间
    """
    sheet = workbook.get_sheet_by_name("RPA配置区")
    row = 3 + STATUS_NAMES.index(name)
    if success_time is not None:
        sheet.set_cell(row, "B", success_time.strftime("%Y-%m-%d %H:%M:%S"))
    sheet.set_cell(row, "C", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    sheet.set_cell(row, "D", result)
    sheet.set_cell(row, "E", str(detail)[:500])


def main(args):
    """直接打开正式工作簿，按固定业务流程更新两个 Sheet 并统一保存。"""
    results = []
    target = Path(TARGET_WORKBOOK_PATH)
    workbook = None
    committed = False

    try:
        # 打开正式工作簿前检查一次占用
        if target.with_name(f"~${target.name}").exists():
            raise RuntimeError("正式 Excel 正在被编辑，本轮不打开")

        # WPS 直接打开正式文件，所有业务模块共享同一个 workbook
        workbook = xbot.excel.open(file_name=str(target), kind="wps", visible=True, update_links=False)
        states = _read_status_table(workbook)

        # 来源数据：准备阶段失败不接触 RAW 区，写入阶段失败则整轮回滚
        old_success = states["订单数据"]["last_success"]
        source_updated = False
        if not (old_success and old_success.date() == datetime.now().date()):
            try:
                rows = update_source.prepare()
            except Exception as exc:
                results.append(("订单数据", "失败", str(exc)))
                _set_status(workbook, "订单数据", "失败", str(exc))
                logging.error(f"订单数据准备失败：{exc}\n{traceback.format_exc()}")
            else:
                try:
                    detail = update_source.apply_update(workbook, rows)
                    _set_status(workbook, "订单数据", "成功", detail, datetime.now())
                except Exception as exc:
                    results.append(("订单数据", "失败", str(exc)))
                    raise RuntimeError("订单数据 RAW 写入失败") from exc
                source_updated = True
                results.append(("订单数据", "成功", detail))
        else:
            results.append(("订单数据", "跳过", "今天已成功"))

        # 依赖更新：来源刚更新或今天已有有效数据时才允许重新计算
        source_ready = source_updated or (old_success and old_success.date() == datetime.now().date())
        country_success = states["地区销量"]["last_success"]
        if not source_ready:
            _set_status(workbook, "地区销量", "未执行", "来源今天未成功")
            results.append(("地区销量", "未执行", "来源今天未成功"))
        elif source_updated or not (country_success and country_success.date() == datetime.now().date()):
            try:
                detail = update_country_sales.update_all(workbook)
                _set_status(workbook, "地区销量", "成功", detail, datetime.now())
            except Exception as exc:
                results.append(("地区销量", "失败", str(exc)))
                raise RuntimeError("地区销量汇总写入失败") from exc
            results.append(("地区销量", "成功", detail))
        else:
            results.append(("地区销量", "跳过", "今天已成功且来源未变化"))

        # 不论本轮更新结果，直接保存正式文件一次
        workbook.save()
        committed = True
        workbook.close()
        workbook = None
    except Exception as exc:
        # 未保存的任务不能对外称成功；异常链包含具体业务上下文
        logging.error(f"本轮 Excel 更新失败：{exc}\n{traceback.format_exc()}")
        if not committed:
            results = [
                (name, "失败", f"整轮未保存：{exc}") if status == "成功" else (name, status, detail)
                for name, status, detail in results
            ]
        results.append(("整轮提交", "失败", str(exc)))
    finally:
        if workbook is not None:
            try:
                workbook.set_saved(True)
                workbook.close()
            except Exception as exc:
                logging.error(f"关闭 Excel 失败：{exc}\n{traceback.format_exc()}")

    # 只在业务完整结束后输出一次汇总；实际项目可对接已核验的通知能力
    logging.info(f"工作簿提交={'成功' if committed else '失败'}，更新结果={results}")
    return results
