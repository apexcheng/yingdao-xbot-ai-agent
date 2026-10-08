"""示例关联业务：统一汇总两个地区的销量。"""


def update_all(workbook):
    """
    在同一工作簿读取订单 RAW 数据并重算地区汇总。

    :param workbook: 主流程已经打开的共享工作簿
    :return: 地区销量更新说明
    """
    source = workbook.get_sheet_by_name("订单数据")
    last_row = source.get_first_free_row() - 1
    if last_row < 2:
        raise RuntimeError("订单数据 RAW 区没有有效记录")

    # 不依赖公式重算：直接读取本轮工作簿内的 RAW 值
    total = {"北区": 0, "南区": 0}
    for date, region, quantity in source.get_range(2, "A", last_row, "C"):
        if region not in total:
            raise RuntimeError(f"订单数据 RAW 出现未知地区：{region}")
        total[region] += int(quantity)

    workbook.get_sheet_by_name("地区销量").set_range(
        1, "A", [["地区", "销量"], ["北区", total["北区"]], ["南区", total["南区"]]]
    )
    return f"北区 {total['北区']}，南区 {total['南区']}"
