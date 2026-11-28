# DWS 钉钉通知：消息选择、A2UI 报告与定向提醒

适用：影刀 RPA 的钉钉通知设计与联调。DWS 是钉钉命令行工具。它的个人账号发送、企业机器人发送和 Webhook 是不同身份，不应相互替换。先在开发机用测试群和假数据验收，不把成功登录开发机等同于运行机可用。

## 选哪种消息

| 需求 | 推荐 |
| --- | --- |
| 简单告警、几行说明 | 文本或普通 Markdown |
| 边运行边展示阶段或生成进度 | 流式文本卡片；结束时更新同一张卡 |
| 多店铺或多站点执行报告、指标、可复制的表格 | DWS A2UI：原生组件和 A2UI Markdown 文本表格 |
| 明确要求由企业机器人发出 | 单独检查机器人身份、群权限和所用接口，不用个人会话冒发 |
| 附件、引用回复、历史回查 | 查本机 `dws chat` 帮助；本地文件与内联图片不是同一种消息 |

## 报告版式

- 顶部放标题、运行状态、统计范围和三个核心指标，例如成功店铺数、确认写入量、总耗时。指标用浅色卡片，结论不要埋在长文里。
- 异常置于明细之前，写清对象、失败步骤、实际影响和建议动作；没有异常不留空栏目。不改变业务原有的告警阈值、去重或 @ 规则。
- 正常明细一店一行；写入拆分单独用一行小字；相同退款日期在明细标题右侧只写一次。表格下方“采集补充”使用浅黄独立区块：先总结免采、已跟进跳过、滑块，再将有补充信息的店铺逐行列出；运行时间放独立页脚。确认写入数不等于新增数。
- 旧 `StandardCard` 的 Markdown 块曾将 `|` 原样显示；已验收的做法是发 DWS A2UI，表格写在其中的 `Markdown.content`。不要用普通文本和空格拼列，也不必转成图片。移动端和桌面端都应以实际显示验收。

## 发送与验证

1. 用 `dws --version`、`dws auth status` 和命令帮助核对本机能力、登录组织、发送身份。群名用只读搜索定位，确认唯一的群 ID，再发送。
2. 使用下方模板构造 A2UI JSON，并用 `dws aicard lint --preflight new-card` 离线检查。离线通过不说明客户端排版通过。
3. 创建只发一次。保存创建返回的 `bizId`（这张卡的业务 ID），用它更新**同一张卡**到 `FINISH`；不要再创建一张当作完结。Windows 脚本建议用 UTF-8 标准输入，不手拼多层命令行引号。
4. 分开记录：接口接受、群内回查、卡片完结、客户端排版。超时或回执缺失时先回查，不盲重发。群内出现不等于手机收到提醒或已读。

## 真正 @ 人

只在业务确实需要提醒时启用。先从目标群成员表核对同名和组织身份，取该成员的 `openDingTalkId`。A2UI Markdown 正文用 `<a atId="成员ID">成员显示名</a>`，离线检查和发卡各自的 `--at-open-dingtalk-ids` 都传同一个 ID。不要把普通消息的 `<@…>` 或字面 `@姓名` 当成 A2UI 的提及。完结更新不重新声明提醒对象，避免重复通知。不默认 @ 所有人。

## 上运行机前

在运行任务的 Windows 账号下核对 DWS 登录、组织和指定群，不复制开发机的登录凭据。保留原通知链路，先完成目标机小范围验收再决定是否切换。此文档不授权登录、改权限、正式发群或部署；示例中无真实群 ID、成员 ID、密钥、订单或验证码。

## 验证等级

- **外部链路已实测（2026-11-20，Windows 开发机）**：DWS 离线预检、A2UI 发卡、同卡完结、群内回查均成功。参考版实际桌面显示了表格、复制和展开入口；补充区版已发群，手机窄屏效果待验。定向提及通过接口及到群核对，手机弹窗及已读未核实。
- **模板代码本地验证**：下方脱敏生成脚本可输出 JSON。接入实际影刀任务和运行机无人值守发卡另行验收。

## 模板：本地生成卡片 JSON

保存为 `build_report_card.py`。默认不 @；只有明确获准时，才加 `--mention-id` 与 `--mention-name`。生成两份 JSON：创建正文和用于完结同一张卡片的更新消息。

```python
import argparse
import html
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--mention-id")
p.add_argument("--mention-name")
args = p.parse_args()
if bool(args.mention_id) != bool(args.mention_name):
    p.error("--mention-id 与 --mention-name 必须同时传入")

version = "v1.0"
surface = "collection-report"
components = []

def add(id_, component, **props):
    components.append({"id": id_, "component": component, **props})
    return id_

def text(id_, value, **props):
    return add(id_, "Text", text=value, **props)

title = text("title", "【测试】异常单｜采集完成", bold=True,
             sizeToken="common_h3_text_style__font_size", weight=1)
badge = add("status", "Column", children=[
    text("status-text", "✓ 全部成功", variant="caption", bold=True,
         customLightColor="#166534", customDarkColor="#14532D"),
], padding=5, cornerRadius=6, backgroundColor="#DCFCE7")
root = [add("heading", "Row", children=[title, badge], align="center")]

if args.mention_id:
    mention_id = html.escape(args.mention_id, quote=True)
    mention_name = html.escape(args.mention_name, quote=False)
    root.append(add("mention", "Markdown",
                    content=f'<a atId="{mention_id}">{mention_name}</a> 这是一条卡片提醒测试，无需处理。'))

tiles = []
for i, (value, label, tint, ink) in enumerate([
    ("2/2", "成功店铺", "#E7F8EF", "#166534"),
    ("18", "写入条数", "#EAF1FF", "#1D4ED8"),
    ("1分8秒", "运行耗时", "#F3EDFF", "#6D28D9"),
]):
    k = f"kpi-{i}"
    tiles.append(add(k, "Column", children=[
        text(f"{k}-value", value, bold=True,
             sizeToken="common_h1_text_style__font_size",
             customLightColor=ink, customDarkColor=ink),
        text(f"{k}-label", label, variant="caption",
             customLightColor=ink, customDarkColor=ink),
    ], align="center", weight=1, padding=10, gap=2,
        cornerRadius=8, backgroundColor=tint))

root.extend([
    add("kpis", "Row", children=tiles, align="stretch", gap=8),
    text("metrics", "写入拆分  新增 3 · 更新 15   ｜   进入详情 18",
         variant="caption", colorToken="common_level2_base_color"),
    add("detail-header", "Row", children=[
        text("detail", "店铺明细", bold=True, weight=1),
        text("refund-date", "退款日期 2026-01-01", variant="caption",
             colorToken="common_level2_base_color"),
    ], align="center"),
    add("table", "Markdown", content=(
        "| 店铺 | 写入 | 新增/更新 | 耗时 |\n"
        "| --- | ---: | ---: | ---: |\n"
        "| 示例旗舰店 A | 12 | 2/10 | 45秒 |\n"
        "| 示例旗舰店 B | 6 | 1/5 | 23秒 |"
    )),
    add("notes", "Column", children=[
        text("notes-label", "采集补充", variant="caption",
             colorToken="common_level2_base_color"),
        text("notes-summary", "免采 2 条 · 已跟进跳过 1 条 · 滑块 1 次，已通过",
             bold=True, customLightColor="#5E4420", customDarkColor="#5E4420"),
        text("notes-store-a", "示例旗舰店 A：免采 2 · 滑块 1 次（通过）",
             variant="caption", customLightColor="#78664B", customDarkColor="#78664B"),
        text("notes-store-b", "示例旗舰店 B：已跟进跳过 1",
             variant="caption", customLightColor="#78664B", customDarkColor="#78664B"),
    ], padding=12, gap=5, cornerRadius=9, backgroundColor="#FFF7E6"),
    text("time", "北京时间 09:00:00 至 09:01:08", variant="caption",
         colorToken="common_level2_base_color"),
])
add("root", "Column", children=root, gap=11)

messages = [
    {"version": version, "createSurface": {
        "surfaceId": surface,
        "catalogId": "https://dingtalk.com/card/a2ui/catalogs/public/catalog.json",
    }},
    {"version": version, "updateDataModel": {
        "surfaceId": surface, "path": "/", "value": {},
    }},
    {"version": version, "updateComponents": {
        "surfaceId": surface, "components": components,
    }},
]
finish = [{"version": version, "updateComponents": {
    "surfaceId": surface,
    "components": [components[0]],  # 同一标题定义，不重发正文和 @。
}}]

def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

Path("report.a2ui.json").write_text(compact(messages), encoding="utf-8")
# 发送命令要的是 JSON 字符串数组，而不是上面用于 lint 的对象数组。
Path("finish.wire.json").write_text(compact([compact(x) for x in finish]), encoding="utf-8")
```

## Windows 联调步骤

非执行调用说明（不可直接运行）：先替换占位符、核对授权。下方创建和完结步骤会写入钉钉。

```text
# 先只读核对目标群；群名必须唯一精确匹配。
dws chat +chat-search --keyword "<已授权群名>"
$group = "<从精确匹配返回的 openConversationId>"

# 不 @：保留空数组；需要 @ 时，先核对完整群成员名单中只命中一个真人。
$mentionArgs = @()
# dws chat +chat-members-list --conversation-id $group --member-types user
# $recipient = "<该唯一群成员的 openDingTalkId>"
# $mentionArgs = @("--at-open-dingtalk-ids", $recipient)
# python -B -X utf8 .\build_report_card.py --mention-id $recipient --mention-name "<群成员姓名>"
python -B -X utf8 .\build_report_card.py

# 带 @ 时使用上面带参数的构建命令，替代上一行默认构建；同一 ID 传给 lint 与 send。
$lint = dws aicard lint --file .\report.a2ui.json --preflight new-card --emit @mentionArgs | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or -not $lint.data.valid -or -not $lint.data.preflight.valid) { throw "卡片预检未通过，不发送" }
[IO.File]::WriteAllText((Join-Path (Get-Location) "report.wire.json"),
    (ConvertTo-Json -InputObject @($lint.data.a2uiMessages) -Compress),
    [Text.UTF8Encoding]::new($false))

# 以下两条会真实写入钉钉。明确获准发送后，只执行一次创建命令。
# 用 cmd 重定向原始 UTF-8 文件，避免 Windows PowerShell 的 stdin 编码转换。
$at = if ($mentionArgs.Count) { ' --at-open-dingtalk-ids "' + $recipient + '"' } else { "" }
cmd /d /c ('dws chat message send-a2ui-card --conversation-id "' + $group +
  '" --content - --summary "异常单采集测试" --support-forward=false --format json' + $at + ' < report.wire.json')

# 只填创建响应中的服务端 bizId，不能用请求侧 bizCardId、消息 ID 或 openTaskId。
$bizId = "<创建响应的 bizId>"
cmd /d /c ('dws chat message update-a2ui-card --biz-id "' + $bizId +
  '" --content - --flow-status FINISH --format json < finish.wire.json')

# 回查指定群和窄时间窗口。不要扩大到无关群或联系人。
dws chat +chat-messages --group $group --start "<ISO8601 发送前几秒>" --end "<ISO8601 发送后几秒>" --limit 5 --no-reactions -f json
```

## Windows 运行实现注意点

Python 启动已安装的 DWS 可用 `subprocess.run(["cmd", "/d", "/c", "dws", *args], input=payload, capture_output=True, timeout=40)`。其中 `payload` 是离线验证后的 JSON 字符串数组经 `encode("utf-8")` 得到的字节，命令加 `--content - --format json`。用 `json.loads(result.stdout.decode("utf-8-sig"))` 解析标准输出，允许 Windows 输出带 UTF-8 BOM，检查退出码和服务端错误，再从响应（可能有嵌套包装）取唯一非空 `bizId`。不要只靠 exit 0、也不要把 ID 打入业务日志。

保存同一次创建对应的 `bizId` 和结果。完结只用 `update-a2ui-card --biz-id <bizId> --content - --flow-status FINISH --format json`，输入该卡原组件的非空、保状态更新；不重送正文和 @。遇到超时、结构变化或 bizId 缺失，先按目标群及窄时间窗口回查，不自动重发。

## 参考

- [DWS 消息命令](https://github.com/DingTalk-Real-AI/dingtalk-workspace-cli/blob/main/skills/mono/references/products/chat.md)
- [A2UI 创建与完结](https://github.com/DingTalk-Real-AI/dingtalk-workspace-cli/blob/main/skills/mono/references/products/chat/a2ui.md)
- [A2UI 报告版式](https://github.com/DingTalk-Real-AI/dingtalk-workspace-cli/blob/main/skills/multi/dingtalk-aicard/references/patterns/report.md)
