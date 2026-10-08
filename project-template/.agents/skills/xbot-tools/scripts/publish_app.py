import argparse
import json
import os
import subprocess
from pathlib import Path


SHADOWBOT_CLI = Path(r"C:\Program Files\ShadowBot\shadowbot.shell-cli.exe")


def resolve_project_dir(project_dir=None):
    """Resolve the target ShadowBot project directory."""
    path = Path(project_dir).expanduser().resolve() if project_dir else Path.cwd().resolve()
    package_json_path = path / "package.json"
    if not package_json_path.exists():
        raise FileNotFoundError(f"目标项目目录缺少 package.json：{package_json_path}")
    return path


def load_app_id(project_dir):
    """Read the ShadowBot app UUID from package.json."""
    with (project_dir / "package.json").open("r", encoding="utf-8") as file:
        app_id = str(json.load(file).get("uuid") or "").strip()
    if not app_id:
        raise ValueError("package.json 缺少 uuid，无法确定影刀应用")
    return app_id


def run_cli(*args):
    """Run one ShadowBot CLI command and parse its JSON response."""
    if not SHADOWBOT_CLI.exists():
        raise FileNotFoundError(f"未找到影刀 CLI：{SHADOWBOT_CLI}")

    env = os.environ.copy()
    env["SWITCH_STUDIO_MCP_CLI_SUPPORT"] = "1"
    result = subprocess.run(
        [str(SHADOWBOT_CLI), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    try:
        payload = json.loads(result.stdout.lstrip("\ufeff"))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"影刀 CLI 未返回合法 JSON：{' '.join(args)}\n{result.stdout}") from error
    if payload.get("ok") is not True:
        raise RuntimeError(f"影刀 CLI 执行失败：{' '.join(args)}\n{result.stdout}")
    return payload


def find_app_id(value):
    """Find an app UUID from a nested CLI response."""
    if isinstance(value, dict):
        for key in ("appId", "uuid"):
            if value.get(key):
                return str(value[key]).strip()
        for item in value.values():
            app_id = find_app_id(item)
            if app_id:
                return app_id
    elif isinstance(value, list):
        for item in value:
            app_id = find_app_id(item)
            if app_id:
                return app_id
    return ""


def get_online_version(app_id):
    """Return the current online version metadata."""
    payload = run_cli("console", "app", "versions", "--app-id", app_id)
    for item in payload.get("data", {}).get("items", []):
        if item.get("isOnlineVersion"):
            return item
    return None


def publish_app(args):
    """Reload, save, sync and publish one existing ShadowBot app."""
    project_dir = resolve_project_dir(args.project_dir)
    app_id = load_app_id(project_dir)

    # 发布前确认服务、任务状态和当前线上版本。
    run_cli("system", "health")
    state = run_cli("system", "state").get("data", {})
    if state.get("hasRunningTask"):
        raise RuntimeError("当前影刀有正在运行的任务，停止发布以避免打断任务")
    before = get_online_version(app_id)

    # 外部修改必须先让 Studio 载入目标应用及磁盘最新状态。
    if state.get("hasStudioOpened"):
        current = run_cli("studio", "current", "get")
        current_app_id = find_app_id(current.get("data", {}))
        if not current_app_id:
            raise RuntimeError("Studio 已打开，但无法确认当前应用 ID")
        if current_app_id != app_id:
            raise RuntimeError(f"Studio 当前打开的是其它应用：{current_app_id}")
    else:
        run_cli("studio", "open", "--app-id", app_id)

    # 重新载入、保存编译并同步关闭 Studio。
    run_cli("studio", "app", "reload")
    run_cli("studio", "app", "save")
    run_cli("studio", "current", "sync")

    # 发布同步后的版本，并以线上 versionId 真正变化作为成功标准。
    publish_args = ["console", "app", "publish", "--app-id", app_id]
    if args.update_log:
        publish_args.extend(["--update-log", args.update_log])
    run_cli(*publish_args)
    after = get_online_version(app_id)
    if not after:
        raise RuntimeError("发布命令执行后未找到线上版本")
    if before and after.get("versionId") == before.get("versionId"):
        raise RuntimeError("发布命令返回成功，但线上 versionId 未变化，不能视为新版本发布成功")

    print(json.dumps({
        "app_id": app_id,
        "version": after.get("version"),
        "version_id": after.get("versionId"),
        "version_log": after.get("versionLog", ""),
        "is_online_version": after.get("isOnlineVersion"),
    }, ensure_ascii=False, indent=2))


def build_parser():
    parser = argparse.ArgumentParser(
        description="发布外部修改后的影刀应用：open → reload → save → sync → publish → 校验线上版本。"
    )
    parser.add_argument(
        "--project-dir",
        default=None,
        help="目标影刀项目目录；不传时默认使用当前工作目录",
    )
    parser.add_argument(
        "--update-log",
        default="",
        help="可选发布日志",
    )
    return parser


def main():
    publish_app(build_parser().parse_args())


if __name__ == "__main__":
    main()
