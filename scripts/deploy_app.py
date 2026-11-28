"""一次调用完成影刀项目的 Git 提交推送、Code Flow 同步和线上发布。"""

import argparse
import contextlib
import ctypes
import ctypes.wintypes
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


EXCLUDED_PYTHON_FILES = {"__init__.py", "package.py"}


def load_package_json(project_dir):
    """Load `package.json` as a Python object.

    :param pathlib.Path project_dir: Target project directory.
    :return dict: Parsed package metadata.
    """
    package_json_path = project_dir / "package.json"
    with package_json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_package_json(project_dir, package_data):
    """Write package metadata back to `package.json`.

    :param pathlib.Path project_dir: Target project directory.
    :param dict package_data: Updated package metadata.
    """
    package_json_path = project_dir / "package.json"
    with package_json_path.open("w", encoding="utf-8") as f:
        json.dump(package_data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def normalize_python_file_name(file_name):
    """Normalize a Python file path into file and flow names.

    :param str file_name: Python file name.
    :return tuple[str, str]: `(file_name, flow_name)`.
    """
    path = Path(file_name)
    if path.suffix != ".py":
        raise ValueError(f"只支持 .py 文件：{file_name}")
    return path.name, path.stem


def ensure_group_exists(package_data, group_name):
    """Make sure the requested group exists in `flow_groups`.

    :param dict package_data: Package metadata.
    :param str group_name: Group name to add.
    :return str: Final group name.
    """
    for item in package_data.get("flow_groups", []):
        if item.get("name") == group_name:
            return group_name

    package_data.setdefault("flow_groups", []).append({"name": group_name})
    return group_name


def ensure_code_flow(package_data, file_name, group_name=None):
    """Ensure a Python file is registered as a ShadowBot Code flow.

    :param dict package_data: Package metadata.
    :param str file_name: Python file name.
    :param str group_name: Target flow group.
    :return dict: Summary of the registration result.
    """
    py_name, flow_name = normalize_python_file_name(file_name)
    existing_flow = None
    for flow in package_data.get("flows", []):
        if flow.get("filename") == flow_name:
            existing_flow = flow
            break

    target_group_name = None
    if group_name is not None:
        target_group_name = ensure_group_exists(package_data, group_name)

    if existing_flow:
        changed = False
        updates = {
            "name": flow_name,
            "filename": flow_name,
            "kind": "Code",
            "opened": False,
            "enableCopilot": False,
        }
        if group_name is not None:
            updates["groupName"] = target_group_name
        for key, value in updates.items():
            if existing_flow.get(key) != value:
                existing_flow[key] = value
                changed = True
        return {
            "file": py_name,
            "flow": flow_name,
            "group": existing_flow.get("groupName"),
            "action": "updated",
            "changed": changed,
        }

    new_flow = {
        "name": flow_name,
        "filename": flow_name,
        "kind": "Code",
        "opened": False,
        "groupName": target_group_name if target_group_name is not None else "",
        "enableCopilot": False,
    }
    package_data.setdefault("flows", []).append(new_flow)
    return {
        "file": py_name,
        "flow": flow_name,
        "group": new_flow.get("groupName"),
        "action": "created",
        "changed": True,
    }


def find_shadowbot_python(project_dir):
    """Locate the ShadowBot Python interpreter for the target project.

    :param pathlib.Path project_dir: Target ShadowBot project directory.
    :return pathlib.Path: Python executable path.
    """
    candidates = [
        project_dir.parent / "venv310" / "Scripts" / "python.exe",
        Path(sys.executable),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError("未找到可用的 Python 解释器")


def compile_files(project_dir, files):
    """Compile files with the ShadowBot interpreter.

    :param pathlib.Path project_dir: Target project directory.
    :param list[str] files: Files to compile.
    :return pathlib.Path: Python executable used for compilation.
    """
    python_exe = find_shadowbot_python(project_dir)
    if files:
        command = [str(python_exe), "-m", "py_compile", *files]
        subprocess.run(command, cwd=project_dir, check=True)
    return python_exe


def scan_project_python_files(project_dir):
    """Scan Python files directly under the project root.

    :param pathlib.Path project_dir: Target project directory.
    :return tuple[list[str], list[str], list[str]]: Scanned, excluded and valid file names.
    """
    scanned_files = sorted(path.name for path in project_dir.glob("*.py"))
    excluded_files = [
        file_name for file_name in scanned_files
        if file_name in EXCLUDED_PYTHON_FILES
    ]
    valid_files = [
        file_name for file_name in scanned_files
        if file_name not in EXCLUDED_PYTHON_FILES
    ]
    return scanned_files, excluded_files, valid_files


def find_flow(package_data, file_name):
    """Get the flow entry for a Python file.

    :param dict package_data: Package metadata.
    :param str file_name: Python file name.
    :return dict|None: Matching flow entry if found.
    """
    _, flow_name = normalize_python_file_name(file_name)
    for flow in package_data.get("flows", []):
        if flow.get("filename") == flow_name:
            return flow
    return None


def sync_project(args):
    """Sync externally edited code into ShadowBot."""
    project_dir = resolve_project_dir(args.project_dir)
    package_data = load_package_json(project_dir)
    scanned_files, excluded_files, valid_files = scan_project_python_files(project_dir)
    created_flows = []
    removed_flows = []
    updated_flows = []
    package_changed = False

    # 删除已不存在 Python 文件对应的 Code flow 注册；Visual 等其它流程不处理。
    kept_flows = []
    for flow in package_data.get("flows", []):
        flow_name = flow.get("filename")
        if flow.get("kind") == "Code" and flow_name and not (project_dir / f"{flow_name}.py").exists():
            removed_flows.append(flow_name)
            package_changed = True
            continue
        kept_flows.append(flow)
    package_data["flows"] = kept_flows

    # 同名 Visual 等非 Code flow 不可被覆盖或静默跳过，否则会误报同步成功。
    for file_name in valid_files:
        flow_name = Path(file_name).stem
        if any(flow.get("kind") != "Code" and
               flow_name in (flow.get("name"), flow.get("filename"))
               for flow in package_data.get("flows", [])):
            raise ValueError(f"Code Flow 名称冲突：{file_name} 与现有非 Code flow 同名")
        existing_flow = find_flow(package_data, file_name)
        result = ensure_code_flow(
            package_data,
            file_name,
            args.group if existing_flow is None else None,
        )
        package_changed = package_changed or result["changed"]
        if result["action"] == "created":
            created_flows.append(file_name)
        else:
            updated_flows.append(file_name)

    # 使用目标影刀应用自己的 Python 环境编译，再按需保存 manifest。
    python_exe = compile_files(project_dir, valid_files)
    if package_changed:
        save_package_json(project_dir, package_data)

    print(f"scanned_files={len(scanned_files)}")
    print(f"excluded_files={excluded_files}")
    print(f"created_flows={created_flows}")
    print(f"removed_flows={removed_flows}")
    print(f"updated_flows={updated_flows}")
    print(f"compiled_files={valid_files}")
    print(f"compiled_with={python_exe}")


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
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if result.returncode:
        detail = result.stdout.strip() or result.stderr.strip() or f"退出码 {result.returncode}"
        raise RuntimeError(f"影刀 CLI 执行失败：{' '.join(args)}\n{detail}")
    try:
        payload = json.loads(result.stdout.lstrip("\ufeff"))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"影刀 CLI 未返回合法 JSON：{' '.join(args)}\n{result.stdout}") from error
    if payload.get("ok") is not True or (payload.get("data") or {}).get("success") is False:
        raise RuntimeError(f"影刀 CLI 执行失败：{' '.join(args)}\n{result.stdout}")
    return payload


class StudioClient:
    """Call the local ShadowBot Copilot endpoint for Studio operations."""

    def __init__(self):
        session_id = ctypes.wintypes.DWORD()
        if not ctypes.windll.kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(session_id)):
            raise RuntimeError("无法确定当前 Windows 会话")
        port_file = Path(tempfile.gettempdir()) / f"shadowbot.cli.{session_id.value}.port"
        try:
            port = int(port_file.read_text(encoding="utf-8-sig").strip())
            if not 1 <= port <= 65535:
                raise ValueError(port)
        except (OSError, ValueError) as error:
            raise RuntimeError(f"无法读取影刀本机端口：{port_file}") from error

        self.url = f"http://127.0.0.1:{port}/api/v1/copilot-mcp/mcp"
        self.opener = build_opener(ProxyHandler({}))
        self.headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        self.request_id = 0
        self.request("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "shadowbot-project-deploy", "version": "1"},
        })

    def request(self, method, params):
        self.request_id += 1
        body = json.dumps({"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params})
        request = Request(self.url, data=body.encode("utf-8"), headers=self.headers, method="POST")
        try:
            with self.opener.open(request, timeout=60) as response:
                session = response.headers.get("Mcp-Session-Id")
                if session:
                    self.headers["Mcp-Session-Id"] = session
                payload = json.load(response)
        except HTTPError as error:
            detail = error.read(2000).decode("utf-8", errors="replace")
            raise RuntimeError(f"影刀编辑器接口 {method} 返回 HTTP {error.code}：{detail}") from error
        except (URLError, TimeoutError, ValueError) as error:
            raise RuntimeError(f"影刀编辑器接口 {method} 失败：{error}") from error
        if "result" not in payload:
            raise RuntimeError(f"影刀编辑器接口 {method} 失败：{payload.get('error', payload)}")
        return payload["result"]

    def command(self, command, explanation):
        try:
            result = self.request("tools/call", {
                "name": "xbot-bash",
                "arguments": {"command": f"xbot-bash {command}", "explanation": explanation},
            })
        except RuntimeError as error:
            raise RuntimeError(f"xbot-bash {command} 失败：{error}") from error
        data = result.get("structuredContent")
        if result.get("isError") or not isinstance(data, dict) or data.get("success") is False:
            raise RuntimeError(f"xbot-bash {command} 失败：{data or result.get('content')}")
        return data


def confirm_studio_app(studio, app_id):
    app = studio.command("app info", "核对当前影刀应用").get("app") or {}
    current_app_id = app.get("app_id")
    if not current_app_id or current_app_id.lower() != app_id.lower():
        raise RuntimeError(f"Studio 当前应用与部署目标不一致：{current_app_id or '无法识别'}")
    return app


def get_online_version(app_id):
    """Return the current online version metadata."""
    payload = run_cli("console", "app", "versions", "--app-id", app_id)
    for item in payload.get("data", {}).get("items", []):
        if item.get("isOnlineVersion"):
            return item
    return None


def deployment_state():
    state = run_cli("system", "state").get("data", {})
    if state.get("hasRunningTask") is not False:
        raise RuntimeError("影刀正在运行任务或任务状态不明，停止部署")
    if not isinstance(state.get("hasStudioOpened"), bool):
        raise RuntimeError("无法确认 Studio 是否打开，停止部署")
    return state


def require_saved_studio_app(studio, app_id):
    if confirm_studio_app(studio, app_id).get("has_unsaved_changes") is not False:
        raise RuntimeError("Studio 有未保存的编辑，或保存状态不明，停止部署")


def preflight_deploy(project_dir):
    """Check the live project and Studio before changing local files or Git."""
    if project_dir.parent.name.casefold().endswith("_release"):
        raise RuntimeError("不能从 _Release 目录部署，请切换到影刀开发目录")
    app_id = load_app_id(project_dir)
    run_cli("system", "health")
    state = deployment_state()
    account = run_cli("auth", "current").get("data", {})
    user_id = account.get("userId")
    if account.get("loggedIn") is not True or not user_id:
        raise RuntimeError("无法识别已登录的影刀账号，停止部署")
    expected = (Path(os.environ["LOCALAPPDATA"]) / "ShadowBot" / "users" / str(user_id)
                / "apps" / app_id / "xbot_robot").resolve()
    if project_dir != expected:
        raise RuntimeError(f"部署必须从当前影刀账号的开发目录发起：{expected}")

    studio = StudioClient()
    if state["hasStudioOpened"]:
        require_saved_studio_app(studio, app_id)
    return app_id


def publish_app(app_id, update_log):
    """Reload, save, sync and publish the verified ShadowBot app."""
    # Git 等操作结束后，重新确认运行状态；已打开的应用还须核对 ID 和保存状态。
    state = deployment_state()
    before = get_online_version(app_id)
    if not state["hasStudioOpened"]:
        run_cli("studio", "open", "--app-id", app_id)

    studio = StudioClient()
    require_saved_studio_app(studio, app_id)

    # 重载后可能出现待保存状态，保存和同步前分别确认仍是目标应用。
    if studio.command("app reload", "从磁盘重新加载应用").get("success") is not True:
        raise RuntimeError("影刀未确认应用已重新加载")
    confirm_studio_app(studio, app_id)
    if studio.command("app save", "保存并编译应用").get("success") is not True:
        raise RuntimeError("影刀未确认应用已保存")
    require_saved_studio_app(studio, app_id)
    synced = run_cli("studio", "current", "sync").get("data", {})
    if (synced.get("state") or {}).get("hasStudioOpened") is not False:
        raise RuntimeError("影刀未确认 Studio 已同步并关闭")

    # 发布同步后的版本，并以线上 versionId 真正变化作为成功标准。
    publish_args = ["console", "app", "publish", "--app-id", app_id]
    if update_log:
        publish_args.extend(["--update-log", update_log])
    run_cli(*publish_args)
    after = get_online_version(app_id)
    if not after:
        raise RuntimeError("发布命令执行后未找到线上版本")
    if not after.get("versionId"):
        raise RuntimeError("发布命令执行后线上版本缺少 versionId，无法校验发布结果")
    if before and after.get("versionId") == before.get("versionId"):
        raise RuntimeError("发布命令返回成功，但线上 versionId 未变化，不能视为新版本发布成功")

    return {
        "status": "success",
        "message": "发布成功，线上版本已更新" if before else "发布成功，已确认线上版本（发布前无版本可比较）",
        "app_id": app_id,
        "version": after.get("version"),
        "version_id": after.get("versionId"),
        "version_log": after.get("versionLog", ""),
        "is_online_version": after.get("isOnlineVersion"),
    }


def git(project_dir, *args):
    try:
        result = subprocess.run(
            ["git", "-C", str(project_dir), *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"Git {args[0]} 失败：{error.stderr or error.stdout}") from error
    return result.stdout.strip()


def deploy(args):
    project_dir = resolve_project_dir(args.project_dir)
    app_id = preflight_deploy(project_dir)
    # 新增/删除根目录 Python 流程时同步注册；普通代码修改不重复编译全部流程。
    package = json.loads((project_dir / "package.json").read_text(encoding="utf-8"))
    existing = {path.stem for path in project_dir.glob("*.py") if path.name not in EXCLUDED_PYTHON_FILES}
    registered = {str(flow.get("filename")) for flow in package.get("flows", []) if flow.get("kind") == "Code"}
    codeflows_synced = bool(existing - registered or registered - existing)
    if codeflows_synced:
        with contextlib.redirect_stdout(io.StringIO()):
            sync_project(argparse.Namespace(project_dir=str(project_dir), group=None))
        synced = load_package_json(project_dir)
        synced_registered = {str(flow.get("filename")) for flow in synced.get("flows", [])
                             if flow.get("kind") == "Code"}
        if synced_registered != existing:
            raise RuntimeError(f"Code Flow 同步后注册仍不一致：未注册={sorted(existing - synced_registered)}，残留={sorted(synced_registered - existing)}")

    git_result = {"git_commit": None, "git_changed": False, "git_pushed": False,
                  "git_error": None, "untracked_skipped": []}
    try:
        git_result.update(deploy_git(project_dir, args, git_result))
    except (RuntimeError, OSError) as error:
        if args.require_git_push:
            commit = git_result["git_commit"]
            local_head = f"（本地 Git HEAD {commit}）" if commit else ""
            raise RuntimeError(f"Git 操作失败{local_head}，已停止影刀发布：{error}") from error
        git_result["git_error"] = str(error)

    try:
        result = publish_app(app_id, args.update_log)
    except Exception as error:
        git_status = f"Git 已推送（{git_result['git_commit']}）" if git_result["git_pushed"] else f"Git 未推送（{git_result['git_error']}）"
        raise RuntimeError(f"{git_status}，但影刀同步/发布未完成：{error}") from error
    result.update(git_result)
    if git_result["git_error"] is not None:
        result["message"] += "。Git 操作失败，详见 git_error"
    result["codeflows_synced"] = codeflows_synced
    return result


def deploy_git(project_dir, args, result):
    """Stage changes, commit when needed, and push the project."""
    repo_root = Path(git(project_dir, "rev-parse", "--show-toplevel")).resolve()
    if repo_root != project_dir:
        raise RuntimeError(f"影刀项目目录不是 Git 仓库根目录：{repo_root}")
    # 避免盲目 git add -A 将 .idea、备份目录、临时文件等无关内容提交。
    # 已跟踪文件全部暂存；新增根目录 .py 自动暂存以支持新 Code flow。
    git(project_dir, "add", "--update", "--", ".")
    # git ls-files --others 只返回未跟踪且未被忽略的文件。
    untracked = [name for name in git(project_dir, "ls-files", "--others", "--exclude-standard", "-z").split("\0") if name]
    new_python = [name for name in untracked
                  if "/" not in name.replace("\\", "/") and name.endswith(".py")]
    if new_python:
        git(project_dir, "add", "--", *new_python)
    if args.add:
        git(project_dir, "add", "--", *args.add)

    changed = bool(git(project_dir, "diff", "--cached", "--name-only", "--", "."))
    result["git_changed"] = changed
    result["untracked_skipped"] = sorted(set(untracked) - set(new_python) - set(args.add))
    if changed:
        message = args.commit_message or f"deploy: {args.update_log or 'update ShadowBot application'}"
        git(project_dir, "commit", "-m", message)
    result["git_commit"] = git(project_dir, "rev-parse", "--short", "HEAD")
    git(project_dir, "push")
    result["git_pushed"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description="Git 提交推送 → 影刀同步 → 发布 → 验证线上版本（单次调用）。")
    parser.add_argument("--project-dir", default=None, help="影刀项目目录，默认当前目录")
    parser.add_argument("--commit-message", default="", help="Git 提交信息，默认使用发布日志")
    parser.add_argument("--update-log", default="", help="影刀版本更新说明")
    parser.add_argument("--require-git-push", action="store_true", help="Git 操作失败时停止影刀发布（用于“push 并部署”）")
    parser.add_argument("--add", action="append", default=[], help="额外纳入本次提交的新增文件，可重复传入")
    args = parser.parse_args()
    try:
        print(json.dumps(deploy(args), ensure_ascii=False, indent=2))
    except Exception as error:
        print(json.dumps({"status": "failed", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
