# 不必再封装的原生写法与已知边界

这些动作优先直接在业务代码里使用，只有明确完整、可独立复用的职责才提取为函数；不要再做一套「增强工具2026」同义封装。

## XPath：直接查找或等待

```python
# 要求找到唯一元素，原生查找已具备 timeout：
page.find_by_xpath("//button[contains(., '查询')]", timeout=10).click()

# 允许同一 XPath 对应多个元素，超时不阻塞：
buttons = page.find_all_by_xpath("//button[contains(., '查询')]", timeout=3)
if buttons:
    buttons[0].click()
```

前述 XPath 仅作语法示例，不代表某站点真实选择器。需要循环判断状态变化时，在业务代码就地循环 `find_all_by_xpath(..., timeout=1)`，而不是创建通用等待包装。网页定位参数见 [browser API](../../../../../../xbot-api-docs/docs/browser.md)。

## 异常堆栈

```python
import traceback
from xbot.app import logging

try:
    do_business_step()
except Exception:
    logging.error(f"业务步骤异常：\n{traceback.format_exc()}")
    raise
```

不要把同一个异常在各层重复格式化、重复通知。

## WPS：确认目标工作簿是否只读

```python
if workbook.workbook.ReadOnly:
    raise RuntimeError("目标工作簿以只读方式打开，不能保存本轮写入")
```

这只能检测 **ReadOnly**，**不能代替**旧 `get_wps_lock_user` 通过 WPS 的锁文件解析占用者用户名。若业务确需用户名，应单独核对当前 WPS 锁文件格式与 Windows 共享读取，且避免将锁文件解析结果当作必然准确。

## Python 内联 Markdown 表格

仅需小表时直接生成当前业务列：

```python
rows = [{"店铺": "示例店铺", "状态": "成功"}]
message = "| 店铺 | 状态 |\n| --- | --- |\n"
message += "".join(f"| {row['店铺']} | {row['状态']} |\n" for row in rows)
```

真实数据可能包含 `|` 或换行，需按业务需求转义/简化；不视为 `to_markdown_table` 在所有输入上的完全替代。

## 原生 Windows 元素点击条件

`is_win_element_clickable` 的实际能力包括可见、可用、有效矩形及中心点位于屏幕范围。仅使用 `visible` 或 `enabled` 不能等价证明在屏幕内或没有遮挡。当前没有统一适用于所有 Win32 元素类型的已核原生一行替代，**新项目按其使用的元素 API 实际返回类型作局部判断**，不要复制旧市场指令源码或猜测属性。

## 首次配置 / DPAPI

一般项目遵循 [文件职责与配置](../../../code-quality/references/coding-style.md#2-文件职责)，使用 Git 忽略的本地 `config.py`，不需要弹窗结果自动转换和 DPAPI 方案。若用户明确要求 Windows 用户级加密持久化，旧 `save_secret_config/load_secret_config` 的能力不能用纯 JSON 或明文 config 冒充；该能力仍需要单独依据 Windows DPAPI 和原生对话框的正式 API 设计验证。

本页的原生写法是**能力简化**，不是宣称对每个旧扩展函数都已完成同能力迁移。
