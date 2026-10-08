"""C-ERP 库存统计数据源：导出商品库存 CSV，写回 RAW 并同步规格配置。"""

import csv
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from xbot import web
from xbot.app import logging
from xbot_extensions.iframe2 import api as iframe_api

from .config import BROWSER_PROFILE, STATUS_SHEET
from .utils import clean_text, preserve_excel_scalar, replace_raw_area, validate_headers, validate_raw_layout

SHEET_NAME = "C-ERP库存(产品库)"
RAW_LAYOUT = {
    "start_col": "G",
    "header_rows": 1,
    "expected_headers": [
        (0, 0, "商品代码"),
        (0, 2, "商品规格代码"),
        (0, 3, "商品规格名称"),
        (0, 24, "商品分类"),
        (0, 30, "商品建档日期"),
    ],
}


def _get_erp_page():
    """取得已登录的 C-ERP 网页会话，不启动整套参考 RPA。"""
    web.set_user_environment(
        mode="chrome", profile_name=BROWSER_PROFILE,
        specifield_userdata=False, user_data_dir=None,
    )
    try:
        page = web.get(url="www.guanyierp.com/index", mode="chrome", load_timeout=3)
    except Exception:
        page = web.create(
            url="https://www.guanyierp.com/index",
            mode="chrome",
            load_timeout=20,
            stop_if_timeout=False,
        )
    if "login.guanyierp.com" in page.get_url():
        raise RuntimeError("C-ERP 登录会话已失效，请先在影刀 Chrome 登录 ERP 后重试该 Sheet")
    page.find_by_xpath("//div[@class='cerp-header']", timeout=20)
    return page


def prepare():
    """
    在一个 C-ERP 页面完成库存统计、查询、导出、任务中心下载并解析 CSV。

    :return: 含二维数据的 payload
    """
    page = _get_erp_page()

    # 进入库存统计；已经打开则直接切换对应 Tab
    opened = page.find_all_by_xpath(
        "//div[@class='ant-tabs-nav-list']//div[contains(@class, 'ant-tabs-tab')]//span[contains(text(), '库存统计')]",
        timeout=0.2,
    )
    if opened:
        opened[0].click(delay_after=0.1)
    else:
        # 复用 C-ERP 已验证的“全部功能菜单 → 搜索菜单 → 进入 Tab”路径
        page.find_by_xpath('//div[@class="cerp-header"]//div[@class="menu-entry-icon"]', timeout=10).click(delay_after=0.1)
        page.find_by_xpath('//div[@class="menu-panel-entry"][normalize-space(.)="全部功能菜单"]', timeout=10).click(delay_after=0.1)
        page.find_by_xpath(
            '//div[contains(@class, "shortcut-search-select")]//span[contains(@class, "ant-select-selection-item")]',
            timeout=10,
        ).click(delay_after=0.1)
        page.find_by_xpath(
            '//div[contains(@class, "shortcut-search-select")]//span[contains(@class, "ant-select-selection-search")]//input',
            timeout=10,
        ).input("库存统计", append=False, send_key_delay=10, delay_after=0.1)
        page.find_by_xpath(
            '//div[@class="rc-virtual-list-holder-inner"]/div[1][contains(@class, "ant-select-item")]',
            timeout=10,
        ).click(delay_after=0.1)
        page.find_by_xpath(
            "//div[@class='ant-tabs-nav-list']//div[contains(@class, 'ant-tabs-tab')]//span[contains(text(), '库存统计')]",
            timeout=20,
        ).click(delay_after=0.1)

    # iframe2 市场指令：库存统计 iframe 内重置筛选；iframe_instance=页面对象，
    # xpath=[业务 iframe, 重置按钮]；current_global=False；timeout=10 秒。
    iframe_api.click_by_xpath(
        iframe_instance=page,
        xpath=[
            '//div[@role="tabpanel"]/iframe[contains(@src, "/stock/message/stock_tenant")]',
            "//div[@class='ant-tabs-extra-content']//button[contains(., '重 置')]",
        ],
        current_global=False, timeout=10,
    )
    # iframe2 市场指令：点击库存统计查询；iframe_instance=页面对象，
    # xpath=[业务 iframe, 查询按钮]；current_global=False；timeout=10 秒。
    iframe_api.find_ele(
        iframe_instance=page,
        xpath=[
            '//div[@role="tabpanel"]/iframe[contains(@src, "/stock/message/stock_tenant")]',
            "//div[@class='gy-split-pane-content']//button[not(@disabled)]/span[contains(text(), '查 询')]",
        ],
        current_global=False, timeout=10,
    ).click(delay_after=1)
    # iframe2 市场指令：等待查询按钮重新启用，确认查询完成；
    # iframe_instance=页面对象，xpath=[业务 iframe, 查询按钮]；current_global=False；timeout=40 秒。
    iframe_api.find_ele(
        iframe_instance=page,
        xpath=[
            '//div[@role="tabpanel"]/iframe[contains(@src, "/stock/message/stock_tenant")]',
            "//div[@class='gy-split-pane-content']//button[not(@disabled)]/span[contains(text(), '查 询')]",
        ],
        current_global=False, timeout=40,
    )

    # 库存统计商品库存导出 CSV（商品、规格、仓库全部不筛选）
    exported_at = datetime.now()
    # iframe2 市场指令：点击库存统计 iframe 的 CSV 导出按钮；
    # iframe_instance=页面对象，xpath=[业务 iframe, 导出按钮]；current_global=False；timeout=10 秒。
    iframe_api.click_by_xpath(
        iframe_instance=page,
        xpath=[
            '//div[@role="tabpanel"]/iframe[contains(@src, "/stock/message/stock_tenant")]',
            "//button/span[normalize-space(.)='商品库存导出CSV']",
        ],
        current_global=False, delay_after=0.1, timeout=10,
    )
    # iframe2 市场指令：在业务 iframe 内确认导出；
    # iframe_instance=页面对象，xpath=[业务 iframe, 确认按钮]；current_global=False；timeout=10 秒。
    iframe_api.click_by_xpath(
        iframe_instance=page,
        xpath=[
            '//div[@role="tabpanel"]/iframe[contains(@src, "/stock/message/stock_tenant")]',
            "//div[@class='ant-modal-content']//button[normalize-space(.)='确 认']",
        ],
        current_global=False, delay_after=0.1, timeout=10,
    )

    # 进入任务中心，按本轮导出时间和完整任务名称绑定下载
    page.find_by_xpath(
        "//div[@class='cerp-header']//div[@class='menu-item icon-menu-item'][last()]",
        timeout=10,
    ).click(delay_after=0.1)
    page.find_by_xpath(
        "//div[contains(@class, 'help-center-tips')]/div[@class='ant-popover-content']//a[contains(text(), '任务中心')]",
        timeout=10,
    ).click(delay_after=0.1)

    # iframe2 市场指令：切换到“执行中”任务；
    # iframe_instance=页面对象，xpath=[任务 iframe, 执行中 Tab]；current_global=False；timeout=20 秒。
    iframe_api.find_ele(
        iframe_instance=page,
        xpath=[
            '//iframe[contains(@src, "/task/task_center")]',
            "//span[@class='x-tab-inner x-tab-inner-center'][contains(text(), '执行中')]",
        ],
        current_global=False, timeout=20,
    ).click(delay_after=1)

    deadline = exported_at + timedelta(seconds=600)
    task_name = None
    while datetime.now() <= deadline and not task_name:
        # iframe2 市场指令：刷新“执行中”任务列表；
        # iframe_instance=页面对象，xpath=[任务 iframe, 刷新]；current_global=False；timeout=5 秒。
        iframe_api.find_ele(
            iframe_instance=page,
            xpath=[
                '//iframe[contains(@src, "/task/task_center")]',
                "//div[@id='detailTab-body']//div[@id='running']//span[text()='刷新']",
            ],
            current_global=False, timeout=5,
        ).click(delay_after=1)
        # iframe2 市场指令：读取执行中任务名称；
        # iframe_instance=页面对象，xpath=[任务 iframe, 名称单元格]；current_global=False；timeout=0.5 秒。
        names = iframe_api.find_all_ele(
            iframe_instance=page,
            xpath=[
                '//iframe[contains(@src, "/task/task_center")]',
                "//div[@id='running']//table[@role='presentation'][contains(@id, 'gridview')]//tr/td[2]",
            ],
            current_global=False, timeout=0.5,
        )
        # iframe2 市场指令：读取同一任务行的时间；
        # iframe_instance=页面对象，xpath=[任务 iframe, 时间单元格]；current_global=False；timeout=5 秒。
        times = iframe_api.find_all_ele(
            iframe_instance=page,
            xpath=[
                '//iframe[contains(@src, "/task/task_center")]',
                "//div[@id='running']//table[@role='presentation'][contains(@id, 'gridview')]//tr/td[3]",
            ],
            current_global=False, timeout=5,
        )
        for index, name_element in enumerate(names):
            name = clean_text(name_element.get_text())
            when = datetime.strptime(clean_text(times[index].get_text()), "%Y-%m-%d %H:%M:%S")
            if "库存" in name and when >= exported_at.replace(microsecond=0):
                task_name = name
                logging.info(f"[{SHEET_NAME}] 已找到本轮 C-ERP 导出任务：{name}")
                break
        if not task_name:
            time.sleep(1)
    if not task_name:
        raise TimeoutError("C-ERP 库存统计导出未出现在执行中任务列表（600 秒）")

    # iframe2 市场指令：切到任务中心“已完成”；
    # iframe_instance=页面对象，xpath=[任务 iframe, 已完成 Tab]；current_global=False；timeout=5 秒。
    iframe_api.find_ele(
        iframe_instance=page,
        xpath=[
            '//iframe[contains(@src, "/task/task_center")]',
            "//span[@class='x-tab-inner x-tab-inner-center'][contains(text(), '已完成')]",
        ],
        current_global=False, timeout=5,
    ).click(delay_after=1)
    while datetime.now() <= deadline:
        # iframe2 市场指令：刷新“已完成”任务列表；
        # iframe_instance=页面对象，xpath=[任务 iframe, 刷新]；current_global=False；timeout=5 秒。
        iframe_api.find_ele(
            iframe_instance=page,
            xpath=[
                '//iframe[contains(@src, "/task/task_center")]',
                "//div[@id='detailTab-body']//div[@id='finished']//span[text()='刷新']",
            ],
            current_global=False, timeout=5,
        ).click(delay_after=1)
        # iframe2 市场指令：读取已完成任务名称，用名称锁定本轮导出；
        # iframe_instance=页面对象，xpath=[任务 iframe, 名称单元格]；current_global=False；timeout=0.5 秒。
        names = iframe_api.find_all_ele(
            iframe_instance=page,
            xpath=[
                '//iframe[contains(@src, "/task/task_center")]',
                "//div[@id='finished']//table[@role='presentation'][contains(@id, 'gridview')]//tr/td[2]",
            ],
            current_global=False, timeout=0.5,
        )
        for index, element in enumerate(names):
            if clean_text(element.get_text()) != task_name:
                continue
            # iframe2 市场指令：读取已完成任务的下载链接；
            # iframe_instance=页面对象，xpath=[任务 iframe, 链接单元格]；current_global=False；timeout=5 秒。
            download_elements = iframe_api.find_all_ele(
                iframe_instance=page,
                xpath=[
                    '//iframe[contains(@src, "/task/task_center")]',
                    "//div[@id='finished']//table[@role='presentation'][contains(@id, 'gridview')]//tr/td[last()]//a",
                ],
                current_global=False, timeout=5,
            )
            download_dir = Path.home() / "Downloads"
            file_name = f"CERP库存-{exported_at:%Y%m%d_%H%M%S}"
            downloaded = download_elements[index].download(
                str(download_dir),
                file_name=f"{file_name}.tmp",
                overwrite=True,
                wait_complete=True,
                wait_complete_timeout=3600,
            )
            result = download_dir / f"{file_name}.csv"
            os.replace(downloaded, result)
            return {"data": _read_stock_csv(str(result))}
        time.sleep(1)
    raise TimeoutError("C-ERP 本轮库存统计导出任务未在 600 秒内完成")


def _read_stock_csv(path):
    """
    按导出原始列顺序读取 C-ERP CSV，并验证目标 RAW 布局。

    :param path: 本轮库存统计 CSV 文件路径
    :return: 可直接交给现有 RAW 写入接口的完整二维数据
    """
    content = Path(path).read_bytes()
    if not content:
        raise RuntimeError("C-ERP 库存统计导出文件为空")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("gb18030")
    data = [row for row in csv.reader(text.splitlines()) if any(clean_text(value) for value in row)]
    if len(data) < 2:
        raise RuntimeError("C-ERP 库存统计 CSV 没有有效数据行")
    width = max(len(row) for row in data)
    data = [
        [preserve_excel_scalar(value) for value in row] + [None] * (width - len(row))
        for row in data
    ]
    validate_raw_layout(SHEET_NAME, data, RAW_LAYOUT)
    if not any(clean_text(row[2]) for row in data[1:]):
        raise RuntimeError("C-ERP 库存统计 CSV 未包含有效商品规格代码")
    return data


def apply_update(workbook, payload):
    """
    更新 C-ERP 原始区，并按规格代码只追加/原行更新商品规格配置。

    :param workbook: 已打开的目标工作簿
    :param payload: ``prepare`` 返回的数据
    :return: 写入结果描述文本
    """
    data = payload["data"]
    # 先把产品库原始数据完整写回 RAW 区
    raw_detail = replace_raw_area(workbook, SHEET_NAME, data, RAW_LAYOUT)

    # 解析产品库导出的规格字段
    headers = [clean_text(value) for value in data[0]]
    required = ["商品代码", "商品规格代码", "商品规格名称", "商品分类"]
    validate_headers(data, required)
    indexes = {name: headers.index(name) for name in required}

    source_by_spec = defaultdict(list)
    source_order = []
    for row in data[1:]:
        spec_code = clean_text(row[indexes["商品规格代码"]])
        if not spec_code:
            continue
        record = {
            "product_code": clean_text(row[indexes["商品代码"]]),
            "spec_name": clean_text(row[indexes["商品规格名称"]]),
            "category": clean_text(row[indexes["商品分类"]]),
        }
        if spec_code not in source_by_spec:
            source_order.append(spec_code)
        if record not in source_by_spec[spec_code]:
            source_by_spec[spec_code].append(record)

    # 读取配置区现有商品规格配置，按规格代码建立索引
    config_sheet = workbook.get_sheet_by_name(STATUS_SHEET)
    last_row = max(config_sheet.get_first_free_row_on_column("O") - 1, 5)
    existing = config_sheet.get_range(6, "N", last_row, "R") if last_row >= 6 else []
    rows = [list(row) for row in existing]
    existing_index = {}
    for index, row in enumerate(rows):
        spec_code = clean_text(row[1] if len(row) > 1 else "")
        if spec_code:
            if spec_code in existing_index:
                raise RuntimeError(f"RPA 商品规格配置存在重复规格代码：{spec_code}")
            existing_index[spec_code] = index

    # 已有行按规格代码原行更新；新规格唯一命中才追加，冲突跳过
    matched = 0
    appended = 0
    skipped_conflicts = []
    for spec_code in source_order:
        variants = source_by_spec[spec_code]
        record = None
        if spec_code in existing_index:
            row = rows[existing_index[spec_code]]
            while len(row) < 5:
                row.append(None)
            if len(variants) == 1:
                record = variants[0]
            else:
                existing_product = clean_text(row[0])
                existing_name = clean_text(row[2])
                scored = []
                for variant in variants:
                    score = 0
                    if existing_product and variant["product_code"] == existing_product:
                        score += 2
                    if existing_name and variant["spec_name"] == existing_name:
                        score += 1
                    scored.append((score, variant))
                best_score = max(score for score, _ in scored)
                best = [variant for score, variant in scored if score == best_score]
                if best_score > 0 and len(best) == 1:
                    record = best[0]

            if record is None:
                skipped_conflicts.append(spec_code)
                continue
            if record["product_code"]:
                row[0] = record["product_code"]
            if record["spec_name"]:
                row[2] = record["spec_name"]
            if record["category"]:
                row[4] = record["category"]
            matched += 1
        else:
            if len(variants) != 1:
                skipped_conflicts.append(spec_code)
                continue
            record = variants[0]
            rows.append([
                record["product_code"],
                spec_code,
                record["spec_name"],
                "",
                record["category"],
            ])
            existing_index[spec_code] = len(rows) - 1
            appended += 1

    if rows:
        config_sheet.set_range(6, "N", rows)
    detail = f"{raw_detail}；商品规格匹配更新 {matched}，新增 {appended}"
    if skipped_conflicts:
        detail += f"，冲突跳过 {len(skipped_conflicts)} 个（{ '、'.join(skipped_conflicts[:5]) }）"
    return detail
