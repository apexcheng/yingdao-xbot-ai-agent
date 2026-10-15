"""影刀编码版业务入口（模板示例）。

真实项目应将本文件复制或合并到已有 ``package.json`` 的影刀项目根目录。
现有 Visual 启动流调用本模块的 ``main(args)``；业务配置从 ``config.py`` 导入。
"""
r"""
TODO 不要删除此注释，方便用户复盘
    准备开发本程序，你先看以下信息，再向我确认细节。每个细节我都要知道/确认，你不能自动帮我做了
    流程其它细节需要参考知识库「表格更新」demo
    
    配置变量统一放在config.py
    每个sheet的更新try2次，若失败不阻塞下一个sheet更新
    
    最终需要发送钉钉通知
    若今天已经更新过，就不需要再更新

    需要：ERP 账号、密码、ERP所在的浏览器profile 及实现自动登录（这个在市场指令已经有了，所以不用封装）
    需要：抖店 账号、密码、所在的浏览器Profile 及实现自动登录（这个在市场指令已经有了，所以不用封装）

    stpe 0
    kill wps

    step 1
    读取「经营看板」sheet的 C11单元格，得到这样的字符串：'数据更新日期：08月07日 09:59  （也可能为空）
    提取日期，转换成标准日期 --> 这是上后更新完成的时候，如果是今天，说明今天已经更新了，本次程序就可以结束不更新了。（也无需发钉钉通知）

    step2
    更新各数据源
    各数据源的左边是计算层、右边是事实层，左右两边的分隔条件是 中间有一列是空的。
    更新的做法是：下载数据源表格文件 -> 清除目标sheet右边的事实层数据clear_range -> 读取 数据源表格数据 -> 写入事实层 -> OK 完成更新

    更新「【基源】ERP退货明细」和「【基源】ERP发货详情」
        这两个都来自ERP，对应的都有封装。
        使用init erp就可以实现初始化、拿到page、自动登录实现
        然后再调对应的指令下载

    更新「【基源】平台订单明细」
    xpath参考：〔历史本机路径已脱敏〕
    注意只参考xpath和必须的解压、获取密码及相关步骤，代码风格、框架和本项目统一

    更新「【基源】全域投放」
    同样参考：〔历史本机路径已脱敏〕


    更新「【基源】直播链接数据」
    先写框架，xpath-浏览器下载步骤先pass

    更新「【基源】达人佣金」
    同样参考：〔历史本机路径已脱敏〕

    更新「【基源】团长服务费」# TODO
    先写框架，xpath-浏览器下载步骤先pass
    补充：它和达人佣金一样，都是打开「https://buyin.jinritemai.com/dashboard/data/financial/list」
    

    更新「【基源】达人投流」
    先写框架，xpath-浏览器下载步骤先pass

    step3
    关闭多余浏览器、保存表格、kill wps，发送钉钉通知

"""

import datetime
import time
import traceback

from xbot import excel, web
from xbot.app import logging
from xbot_extensions.activity_a90a8311.init_erp import init
from xbot_extensions.ad_killer import close_ads_win
from xbot_extensions.xbot_enhance_tools.shop_utils import login_douyin_seller

from . import package
from . import update_erp_deliveries, update_erp_returns, update_global_promotion
from . import update_influencer_promotion, update_leader_fee, update_live_links
from . import update_order_data, update_product_library, update_selected_alliance, update_purchase_cost
from .config import (
    DOUYIN_ACCOUNT, DOUYIN_PASSWORD, DOUYIN_PROFILE, ERP_ACCOUNT,
    ERP_CAPTCHA_TOKEN, ERP_PASSWORD, ERP_PROFILE, NTFY_TOPIC, SHEET_ATTEMPTS,
    STATUS_BEGIN_COLUMN, STATUS_END_COLUMN, TARGET_FILE, UPDATE_TIME_FORMAT,
)
from .notify import send_results
from .utils import parse_datetime


def update_sheet(sheet_name, update_action):
    """每个 Sheet 总共尝试两次，返回用于看板和通知的本轮结果。"""
    for attempt in range(1, SHEET_ATTEMPTS + 1):
        try:
            if attempt == 1:
                logging.info(f"【{sheet_name}】开始更新")
            else:
                logging.info(f"【{sheet_name}】第{attempt}次尝试更新")
            completed = update_action()
        except Exception as error:
            if attempt < SHEET_ATTEMPTS:
                logging.warning(f"【{sheet_name}】第{attempt}次失败，准备重试｜原因={error}")
            else:
                logging.error(f"【{sheet_name}】最终失败，继续下一项｜已尝试{attempt}次｜原因={error}\n{traceback.format_exc()}")
                return [sheet_name, "失败", attempt, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(error)]
        else:
            if completed is None:
                logging.info(f"【{sheet_name}】下载步骤尚未实现，本轮未执行")
                return [sheet_name, "未实现", 0, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "下载步骤待开发"]
            detail = f"｜{completed}" if isinstance(completed, str) and completed else ""
            logging.info(f"【{sheet_name}】写入完成，等待统一保存{detail}")
            return [sheet_name, "成功", attempt, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), completed if isinstance(completed, str) else ""]


def main(args):
    """更新九个日常 Sheet 与每次必同步的采购成本，统一保存并通知。"""
    logging.info("【经营报表】开始执行")
    # 每行依次为：Sheet 名、状态、尝试次数、处理时间、说明。
    sheet_results = [
        ["【基源】ERP退货明细", "未执行", 0, "", ""],
        ["【基源】ERP发货详情", "未执行", 0, "", ""],
        ["【基源】平台订单明细", "未执行", 0, "", ""],
        ["【基源】全域投放", "未执行", 0, "", ""],
        ["【基源】直播链接数据", "未执行", 0, "", ""],
        ["【基源】达人佣金", "未执行", 0, "", ""],
        ["【基源】团长服务费", "未执行", 0, "", ""],
        ["【基源】达人投流", "未执行", 0, "", ""],
        ["【基源】产品库", "未执行", 0, "", ""],
        ["【基源】采购成本", "未执行", 0, "", ""],
    ]
    errors = []
    saved = False
    product_library_id_events = []
    purchase_changed_ids = []
    try:
        excel.kill_excel_process("wps", True)
        target_workbook = excel.open(file_name=TARGET_FILE, kind="wps", visible=True, update_links=False)
        target_workbook.workbook.Activate()
        target_workbook.workbook.Application.WindowState = -4137
        logging.info("【经营报表】目标工作簿已打开并最大化")

        dashboard = target_workbook.get_sheet_by_name("经营看板")
        today = datetime.date.today()
        try:
            status_rows = dashboard.get_range(1, STATUS_BEGIN_COLUMN, len(sheet_results) + 1, STATUS_END_COLUMN)
            # 读取当天成功记录，在本轮状态中标记为“今日跳过”，保留原尝试次数、时间和说明。
            for previous_row in status_rows[1:]:
                try:
                    if not isinstance(previous_row, (list, tuple)) or len(previous_row) < 5:
                        logging.warning(f"【经营看板】状态行格式错误，忽略今日跳过判断｜内容={previous_row}")
                        continue
                    sheet_name, status, attempts, processed_at, detail = previous_row[:5]
                    if status != "成功" or not processed_at:
                        continue
                    processed_time = parse_datetime(processed_at)
                    if processed_time is None:
                        logging.warning(f"【{sheet_name}】处理时间为空或格式错误，忽略今日跳过判断｜处理时间={processed_at}")
                        continue
                    for sheet_result in sheet_results:
                        if sheet_result[0] == sheet_name and sheet_name != "【基源】采购成本" and processed_time.date() == today:
                            normalized_processed_at = processed_time.strftime("%Y-%m-%d %H:%M:%S")
                            sheet_result[:] = [sheet_name, "今日跳过", attempts, normalized_processed_at, detail or ""]
                            logging.info(f"【{sheet_name}】今天已成功，跳过更新｜处理时间={normalized_processed_at}")
                except Exception as error:
                    logging.warning(f"【经营看板】状态行读取或解析失败，继续执行｜内容={previous_row}｜原因={error}")
        except Exception as error:
            logging.warning(f"【经营看板】读取状态区失败，继续执行报表更新｜原因={error}")

        def sync_purchase():
            changes = update_purchase_cost.update(target_workbook)
            purchase_changed_ids[:] = changes
            return f"更新{len(changes)}个ID"

        sheet_results[9] = update_sheet("【基源】采购成本", sync_purchase)
        if all(row[1] == "今日跳过" for row in sheet_results[:9]):
            logging.info("【经营报表】9个日常 Sheet 今日全部成功，跳过平台初始化，仅同步采购成本")
            dashboard.clear_range(1, STATUS_BEGIN_COLUMN, len(sheet_results) + 1, STATUS_END_COLUMN, target="content")
            dashboard.set_range(1, STATUS_BEGIN_COLUMN, [
                ["Sheet", "结果", "尝试次数", "处理时间", "说明"],
                *[[row[0], "成功" if row[1] == "今日跳过" else row[1], *row[2:]] for row in sheet_results],
            ])
            try:
                target_workbook.save()
                saved = True
            except Exception as error:
                errors.append(f"表格保存失败：{error}")
                logging.error(f"【经营报表】保存失败｜异常={traceback.format_exc()}")
        else:
            # 广告杀手后台监测 Win32 弹窗；参数为 Selector 对象列表，通过元素库名称获取 Selector，检测到“chrome最近下载列表”时自动关闭。
            close_ads_win([package.selector("chrome最近下载列表")])

            # 仅当仍有未执行的 ERP Sheet 时才初始化 ERP。
            if sheet_results[0][1] == "未执行" or sheet_results[1][1] == "未执行":
                web.set_user_environment(mode="chrome", profile_name=ERP_PROFILE)
                for page in web.get_all(mode="chrome")[:-1]:
                    page.close()

                try:
                    # ERP 初始化及自动登录；传入账号、密码、Chrome Profile、图形验证码 Token 和短信主题。
                    erp_page = init(username=ERP_ACCOUNT, password=ERP_PASSWORD, browser_profile=ERP_PROFILE, captcha_token=ERP_CAPTCHA_TOKEN, ntfy_topic=NTFY_TOPIC)
                    erp_page.wait_load_completed(timeout=20)
                    time.sleep(2)
                    logging.info("【ERP】初始化登录成功")
                except Exception as error:
                    logging.error(f"【ERP】初始化失败，继续抖店阶段｜异常={traceback.format_exc()}")
                    for row in sheet_results[:2]:
                        if row[1] == "未执行":
                            row[1:] = ["失败", 0, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"ERP 初始化失败：{error}"]
                else:
                    if sheet_results[0][1] == "未执行":
                        sheet_results[0] = update_sheet("【基源】ERP退货明细", lambda: update_erp_returns.update(target_workbook, erp_page))
                    if sheet_results[1][1] == "未执行":
                        sheet_results[1] = update_sheet("【基源】ERP发货详情", lambda: update_erp_deliveries.update(target_workbook, erp_page))
            else:
                logging.info("【ERP】退货明细与发货详情今日均已成功，跳过初始化")

            # 仅当仍有未执行的抖店 Sheet 时才初始化抖店；采购成本此时已完成，不会是“未执行”。
            if any(row[1] == "未执行" for row in sheet_results[2:]):
                web.set_user_environment(mode="chrome", profile_name=DOUYIN_PROFILE)
                for page in web.get_all(mode="chrome")[:-1]:
                    page.close()

                try:
                    douyin_check_page = web.create(
                        "https://fxg.jinritemai.com/ffa/mshop/homepage/index",
                        "chrome",
                        load_timeout=20,
                    )
                    douyin_check_page.wait_load_completed(timeout=20)
                    time.sleep(2)
                    douyin_url = douyin_check_page.get_url()
                    if "login" in douyin_url:
                        # 抖店自动登录；account/password 为邮箱账号和密码，profile 为共用的 Chrome Profile，返回是否登录成功。
                        logged_in = login_douyin_seller(account=DOUYIN_ACCOUNT, password=DOUYIN_PASSWORD, profile=DOUYIN_PROFILE)
                        if not logged_in:
                            raise RuntimeError("抖店自动登录失败")
                        login_page = web.get_active(mode="chrome")
                        login_page.wait_load_completed(timeout=20)
                        time.sleep(2)
                        logging.info("【抖店】自动登录成功")
                    else:
                        logging.info(f"【抖店】已登录，跳过登录｜当前 URL={douyin_url}")
                except Exception as error:
                    logging.error(f"【抖店】初始化失败，进入统一收尾｜异常={traceback.format_exc()}")
                    for row in sheet_results[2:]:
                        if row[1] == "未执行":
                            row[1:] = ["失败", 0, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"抖店初始化失败：{error}"]
                else:
                    if sheet_results[2][1] == "未执行":
                        sheet_results[2] = update_sheet("【基源】平台订单明细", lambda: update_order_data.update(target_workbook))
                    if sheet_results[3][1] == "未执行":
                        sheet_results[3] = update_sheet("【基源】全域投放", lambda: update_global_promotion.update(target_workbook))
                    if sheet_results[4][1] == "未执行":
                        sheet_results[4] = update_sheet("【基源】直播链接数据", lambda: update_live_links.update(target_workbook))
                    if sheet_results[5][1] == "未执行":
                        sheet_results[5] = update_sheet("【基源】达人佣金", lambda: update_selected_alliance.update(target_workbook))
                    if sheet_results[6][1] == "未执行":
                        sheet_results[6] = update_sheet("【基源】团长服务费", lambda: update_leader_fee.update(target_workbook))
                    if sheet_results[7][1] == "未执行":
                        sheet_results[7] = update_sheet("【基源】达人投流", lambda: update_influencer_promotion.update(target_workbook))
                    if sheet_results[8][1] == "未执行":
                        sheet_results[8] = update_sheet(
                            "【基源】产品库",
                            lambda: update_product_library.update(target_workbook, product_library_id_events),
                        )
            else:
                logging.info("【抖店】相关 Sheet 今日均已成功，跳过初始化")

            all_succeeded = all(row[1] in ("成功", "今日跳过") for row in sheet_results[:9])
            # 全部正常完成时按 Profile 保留最后一个 Page；清理失败不阻断保存。
            if all_succeeded:
                try:
                    for profile in dict.fromkeys((ERP_PROFILE, DOUYIN_PROFILE)):
                        web.set_user_environment(mode="chrome", profile_name=profile)
                        for page in web.get_all(mode="chrome")[:-1]:
                            page.close()
                except Exception as error:
                    errors.append(f"浏览器清理失败：{error}")
                    logging.error(f"【浏览器】清理失败｜异常={traceback.format_exc()}")

            dashboard.clear_range(1, STATUS_BEGIN_COLUMN, len(sheet_results) + 1, STATUS_END_COLUMN, target="content")
            # 看板保留原成功状态；通知直接使用 sheet_results 中的“今日跳过”状态。
            dashboard.set_range(1, STATUS_BEGIN_COLUMN, [
                ["Sheet", "结果", "尝试次数", "处理时间", "说明"],
                *[[row[0], "成功" if row[1] == "今日跳过" else row[1], *row[2:]] for row in sheet_results],
            ])
            if all_succeeded:
                dashboard.set_cell(11, "C", datetime.datetime.now().strftime(UPDATE_TIME_FORMAT))
            try:
                logging.info("【经营报表】开始统一保存")
                target_workbook.save()
                saved = True
                logging.info(f"【经营报表】统一保存完成｜文件={TARGET_FILE}")
            except Exception as error:
                errors.append(f"表格保存失败：{error}")
                logging.error(f"【经营报表】保存失败｜异常={traceback.format_exc()}")
    except Exception as error:
        errors.append(f"程序中断：{error}")
        logging.error(f"【经营报表】程序中断｜异常={traceback.format_exc()}")
    finally:
        try:
            excel.kill_excel_process("wps", True)
        except Exception as error:
            errors.append(f"结束 WPS 失败：{error}")
            logging.error(f"【经营报表】结束 WPS 失败｜异常={traceback.format_exc()}")
        skipped_count = sum(row[1] == "今日跳过" for row in sheet_results)
        success_count = sum(row[1] == "成功" for row in sheet_results)
        failure_count = sum(row[1] == "失败" for row in sheet_results)
        unimplemented_count = sum(row[1] == "未实现" for row in sheet_results)
        unexecuted_count = sum(row[1] == "未执行" for row in sheet_results)
        logging.info(
            f"【经营报表】本轮结果｜成功={success_count}｜今日已完成跳过={skipped_count}｜失败={failure_count}｜"
            f"未实现={unimplemented_count}｜未执行={unexecuted_count}｜保存={'成功' if saved else '未成功'}"
        )
        if any(row[1] != "今日跳过" for row in sheet_results[:9]) or purchase_changed_ids or sheet_results[9][1] != "成功" or errors:
            try:
                send_results(sheet_results, saved, errors, product_library_id_events, purchase_changed_ids if saved else [])
                logging.info("【钉钉】经营报表结果通知发送完成")
            except Exception as error:
                errors.append(f"钉钉通知失败：{error}")
                logging.error(f"【经营报表】钉钉通知失败｜异常={traceback.format_exc()}")
        else:
            logging.info("【钉钉】日常 Sheet 均已跳过且采购成本无变更，本次不发送通知")

    if errors:
        raise RuntimeError("；".join(errors))
    if any(row[1] == "失败" for row in sheet_results):
        raise RuntimeError("经营报表部分 Sheet 更新失败，已完成其余更新与收尾，详情见状态区及钉钉通知")
