"""影刀编码版业务入口（模板示例）。

真实项目应将本模板文件复制或合并到已有 ``package.json`` 的影刀项目根目录。
``主流程.flow`` 是影刀主入口，必须保持不变；由用户在该流程中调用本模块的
``main(args)``。后续编码版业务在本文件中开发，不在模板中修改 ``主流程.flow``。
"""

from xbot.app.dialog import show_custom_dialog
from xbot_extensions.xbot_enhance_tools.market_config import (
    dialog_result_to_dict,
    load_secret_config,
    save_secret_config,
)

# CONFIG_PATH 是模板配置示例。知识库规定真实项目目录为包含 package.json 的影刀项目根目录；
# 配置文件默认存放在当前 Windows 用户的 .xbot/<项目功能名>/project_config.json，
# 复制模板后应按真实项目需要在 config.py 中确认或调整，不能继续使用“项目功能名”占位目录。
from .config import CONFIG_PATH


def init_config():
    # 以下初始化对话框仅用于演示加密配置的读取、首次填写和保存流程。
    # 真实项目可按已确认的业务字段、默认值、按钮文案和是否持久化进行修改。
    config = load_secret_config(str(CONFIG_PATH))
    if config:
        return config

    dialog_settings = {
        "dialogTitle": "初始化配置",
        "settings": {
            "editors": [
                {
                    "type": "TextBox",
                    "label": "账号",
                    "VariableName": "username",
                    "value": None,
                    "nullText": "请输入账号",
                },
                {
                    "type": "TextBox",
                    "label": "密码",
                    "VariableName": "password",
                    "value": None,
                    "nullText": "请输入密码",
                },
            ],
            "buttons": [
                {
                    "type": "Button",
                    "label": "保存并启动",
                    "theme": "red",
                    "hotkey": "Enter",
                },
                {
                    "type": "Button",
                    "label": "启动",
                    "theme": "white",
                },
                {
                    "type": "Button",
                    "label": "取消",
                    "theme": "white",
                    "hotkey": "Esc",
                },
            ],
        },
    }

    dialog_result = show_custom_dialog(dialog_settings)
    config = dialog_result_to_dict(dialog_result)

    action = config.get("pressed_button")
    if action == "取消":
        return None

    if action == "保存并启动":
        save_secret_config(str(CONFIG_PATH), config)

    return config


def main(args):
    # 主流程.flow 调用此编码版入口；在此按真实项目需求编写业务流程。
    config = init_config()

    if not config:
        return

    # TODO: 后续业务流程从 config 和已确认的 args 参数中取值。
