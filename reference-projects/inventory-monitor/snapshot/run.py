"""影刀项目入口。"""

import traceback
from datetime import datetime, timedelta

from xbot.app.dialog import show_notifycation

from . import config as project_config
from . import database, dingtalk, pdd
from .utils import ContextLogger


def main(args):
    """库存监控主流程。

    按平台分发处理库存预警。存在业务结果的店铺各发送一条合并通知，店铺级程序异常即时
    通知运维，全部平台结束后再发送一条运行汇总。

    :param args: 影刀流程入参，当前未使用。
    """
    run_started_at = datetime.now()
    system_logger = ContextLogger("系统", "库存监控")
    try:
        # 初始化配置、数据库和历史数据
        platform_configs = project_config.PLATFORM_CONFIGS
        system_logger.flow("开始执行", f"平台数={len(platform_configs)}")
        database.init_database()
        last_cleanup_at_text = database.get_last_cleanup_at()
        last_cleanup_at = datetime.strptime(last_cleanup_at_text, "%Y-%m-%d %H:%M:%S") if last_cleanup_at_text else None
        need_cleanup = last_cleanup_at is None or (datetime.now() - last_cleanup_at).total_seconds() >= 24 * 3600
        if need_cleanup:
            database.cleanup_history(project_config.SQLITE_RETENTION_DAYS)
        system_logger.flow("配置和数据库初始化完成")
    except Exception as exc:
        system_logger.error("初始化失败", f"原因={exc}", traceback_text=traceback.format_exc())
        dingtalk.send_program_error("全平台", "程序", "初始化", str(exc))
        raise

    shop_results = []
    run_issues = []

    for platform_name, shop_configs in platform_configs.items():
        platform_logger = ContextLogger(platform_name, "全部店铺")
        if not shop_configs:
            platform_logger.flow("未配置店铺，跳过执行")
            continue
        platform_logger.flow("开始执行", f"店铺数={len(shop_configs)}")

        if platform_name in ("拼多多", "天猫"):
            # 查询铺货数据状态，无数据或超过 6 小时则刷新
            try:
                erp_state = database.get_erp_inventory_state(platform_name)
                loaded_at = datetime.strptime(erp_state["loaded_at"], "%Y-%m-%d %H:%M:%S") if erp_state["loaded_at"] else None
                need_refresh = loaded_at is None or (datetime.now() - loaded_at).total_seconds() >= 6 * 3600
            except Exception as exc:
                platform_logger.error("ERP铺货状态读取失败", f"原因={exc}")
                dingtalk.send_program_error(platform_name, "全部店铺", "读取ERP铺货状态", str(exc))
                run_issues.append(f"{platform_name}：ERP铺货状态读取失败，已跳过平台处理")
                continue

            if need_refresh:
                try:
                    # ERP 账号必须已配置，否则无法登录导出
                    if not project_config.ERP_USERNAME or not project_config.ERP_PASSWORD:
                        raise RuntimeError("ERP账号或密码尚未配置")
                    from xbot_extensions import activity_a90a8311

                    # process13 初始化 ERP 网页（已打开则刷新登录态）
                    platform_logger.flow("开始刷新ERP铺货数据")
                    activity_a90a8311.process13(
                        username=project_config.ERP_USERNAME,
                        password=project_config.ERP_PASSWORD,
                        ERP浏览器标识=project_config.ERP_PROFILE,
                        refresh=True,
                    )
                    # process11(平台类型, 店铺名称, 平台商品ID)：过滤式下载平台铺货；天猫在 ERP 中使用淘宝类型，
                    # 店铺名称 / 平台商品ID 传空表示不过滤，返回导出 CSV 路径
                    csv_path = activity_a90a8311.process11("淘宝" if platform_name == "天猫" else "拼多多", "", "")
                    if not csv_path:
                        raise RuntimeError("ERP平台铺货下载未返回CSV路径")
                    # CSV 全量替换当前平台的铺货数据
                    imported_count = database.replace_erp_inventory_from_csv(platform_name, csv_path)
                    platform_logger.flow("ERP铺货数据刷新完成", f"导入记录数={imported_count}")
                except Exception as exc:
                    # 刷新失败：通知运维；无旧数据跳过该平台，有旧数据继续使用
                    action = "已跳过该平台全部店铺" if erp_state["row_count"] == 0 else "继续使用现有旧数据"
                    dingtalk.send_erp_refresh_error(platform_name, str(exc), erp_state["loaded_at"], action)
                    show_notifycation(f"ERP铺货刷新失败\n平台：{platform_name}\n当前数据：{erp_state['loaded_at'] or '无可用旧数据'}\n失败原因：{exc}", level="error")
                    if erp_state["row_count"] == 0:
                        platform_logger.error("ERP铺货数据不可用，跳过平台处理", f"原因={exc}")
                        run_issues.append(f"{platform_name}：ERP铺货不可用，已跳过平台处理")
                        continue
                    platform_logger.error("ERP铺货数据刷新失败，继续使用旧数据", f"最后导入={erp_state['loaded_at']}", f"原因={exc}")
                    run_issues.append(f"{platform_name}：ERP刷新失败，继续使用 {erp_state['loaded_at']} 的旧数据")
            else:
                platform_logger.flow("ERP铺货数据有效，无需刷新", f"记录数={erp_state['row_count']}", f"最后导入={erp_state['loaded_at']}")

        if platform_name == "拼多多":
            process_shop = pdd.process_shop
        elif platform_name == "天猫":
            from . import tmall

            process_shop = tmall.process_shop
        else:
            error = f"暂未实现平台：{platform_name}"
            platform_logger.error(error)
            dingtalk.send_program_error(platform_name, "全部店铺", "平台分发", error)
            run_issues.append(error)
            continue

        for shop_config in shop_configs:
            shop_logger = ContextLogger(platform_name, shop_config["name"])
            try:
                shop_logger.flow("开始执行")
                # 处理店铺，并由钉钉模块统一汇总本轮统计
                result = process_shop(platform_name, shop_config)
                shop_results.append((platform_name, shop_config["name"], result))
                if result["program_error"]:
                    # 店铺中途异常时，先发送异常发生前已经完成的 SKU 处理结果，避免业务结果只落库但通知层丢失
                    dingtalk.send_stock_shop_result(
                        platform_name,
                        shop_config["name"],
                        result["success"],
                        result["failed"],
                        result["skipped"],
                        result["retry_unfound_count"],
                        shop_config.get("manager_mobiles", []),
                        interrupted=True,
                    )
                    shop_logger.error("执行中止", f"步骤={result['program_error']['step']}", f"原因={result['program_error']['error']}", traceback_text=result["program_error"]["traceback"])
                    dingtalk.send_program_error(
                        platform_name,
                        shop_config["name"],
                        result["program_error"]["step"],
                        result["program_error"]["error"],
                    )
                    run_issues.append(f"{platform_name} / {shop_config['name']}：{result['program_error']['step']}异常")
                    show_notifycation(f"店铺处理异常\n平台：{platform_name}\n店铺：{shop_config['name']}\n步骤：{result['program_error']['step']}\n原因：{result['program_error']['error']}", level="error")
                    continue
                shop_logger.flow(
                    "执行完成",
                    f"成功={len(result['success'])}",
                    f"失败={len(result['failed'])}",
                    f"跳过={len(result['skipped'])}",
                    f"待重试未找到={result['retry_unfound_count']}",
                )
                dingtalk.send_stock_shop_result(
                    platform_name,
                    shop_config["name"],
                    result["success"],
                    result["failed"],
                    result["skipped"],
                    result["retry_unfound_count"],
                    shop_config.get("manager_mobiles", []),
                )
            except Exception as exc:
                shop_logger.error("店铺主流程异常", f"原因={exc}", traceback_text=traceback.format_exc())
                dingtalk.send_program_error(platform_name, shop_config["name"], "店铺主流程", str(exc))
                run_issues.append(f"{platform_name} / {shop_config['name']}：店铺主流程异常={exc}")
                show_notifycation(f"店铺处理异常\n平台：{platform_name}\n店铺：{shop_config['name']}\n步骤：店铺主流程\n原因：{exc}", level="error")

        platform_logger.flow("执行完成")

    # SKU 与程序异常保持实时通知；跨过 08:00 / 13:30 / 18:00 后的首次运行才发送阶段汇总
    run_finished_at = datetime.now()
    summary_text = "\n".join(run_issues) or "所有店铺处理完成"
    summary_times = getattr(project_config, "RUN_SUMMARY_TIMES", ("08:00", "13:30", "18:00"))
    last_summary_at = database.get_last_run_summary_at()
    if last_summary_at is None:
        database.set_last_run_summary_at((run_started_at - timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S"))
    else:
        summary_started_at = datetime.strptime(last_summary_at, "%Y-%m-%d %H:%M:%S")
        trigger_times = sorted(datetime.strptime(value, "%H:%M").time() for value in summary_times)
        next_trigger_at = next(
            (datetime.combine(summary_started_at.date(), value) for value in trigger_times if datetime.combine(summary_started_at.date(), value) > summary_started_at),
            datetime.combine(summary_started_at.date() + timedelta(days=1), trigger_times[0]),
        )
        if run_finished_at >= next_trigger_at:
            summary_records = database.get_alert_results_between(last_summary_at, run_finished_at.strftime("%Y-%m-%d %H:%M:%S"))
            summary_result = dingtalk.send_run_summary(summary_started_at, run_finished_at, summary_records)
            # 无可汇总内容时推进时间窗口；有内容但发送失败时保留旧窗口，下轮继续尝试发送
            if summary_result is not False:
                database.set_last_run_summary_at(run_finished_at.strftime("%Y-%m-%d %H:%M:%S"))
    system_logger.flow("执行结束", f"运行异常={len(run_issues)}", f"运行汇总=\n{summary_text}")
    show_notifycation(f"库存监控完成\n{summary_text}")
