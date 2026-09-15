import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
EXCLUDED_PYTHON_FILES = {"__init__.py", "package.py", "shadowbot_sync_tool.py"}


def resolve_project_dir(project_dir=None):
    """Resolve the target ShadowBot project directory.

    :param str|None project_dir: Optional project directory.
    :return pathlib.Path: Resolved project directory.
    """
    if project_dir:
        path = Path(project_dir).expanduser().resolve()
    else:
        path = Path.cwd().resolve()

    if not path.exists():
        raise FileNotFoundError(f"目标项目目录不存在：{path}")

    package_json_path = path / "package.json"
    if not package_json_path.exists():
        raise FileNotFoundError(f"目标项目目录缺少 package.json：{package_json_path}")

    return path


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


def find_shadowbot_python():
    """Locate the ShadowBot Python interpreter.

    :return pathlib.Path: Python executable path.
    """
    candidates = [
        ROOT_DIR.parent / "venv310" / "Scripts" / "python.exe",
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
    python_exe = find_shadowbot_python()
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
    """Sync externally edited code into ShadowBot.

    It scans root Python files, removes stale Code flow registrations, ensures current
    Code flows exist and compiles all valid files.
    """
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

    for file_name in valid_files:
        existing_flow = find_flow(package_data, file_name)
        if existing_flow and existing_flow.get("kind") != "Code":
            continue

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


def build_parser():
    """Build the CLI parser.

    :return argparse.ArgumentParser: Configured parser instance.
    """
    parser = argparse.ArgumentParser(
        description="将外部修改的影刀项目代码同步到影刀编辑器的工具。"
    )
    parser.add_argument(
        "--project-dir",
        default=None,
        help="目标影刀项目目录；不传时默认使用当前工作目录",
    )
    parser.add_argument(
        "--group",
        default=None,
        help="新登记 flow 的统一分组名；不传则使用空分组",
    )
    return parser


def main():
    """Program entry point."""
    parser = build_parser()
    args = parser.parse_args()
    sync_project(args)


if __name__ == "__main__":
    main()
