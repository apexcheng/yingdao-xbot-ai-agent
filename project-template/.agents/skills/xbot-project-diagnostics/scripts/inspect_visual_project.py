from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path
from xml.etree import ElementTree


def load_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def analyze_code_flow(path: Path):
    try:
        source = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeError) as error:
        return {"error": str(error)}

    imports = []
    functions = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            imports.append(module)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = [argument.arg for argument in node.args.posonlyargs + node.args.args]
            if node.args.vararg:
                arguments.append("*" + node.args.vararg.arg)
            arguments.extend(argument.arg for argument in node.args.kwonlyargs)
            if node.args.kwarg:
                arguments.append("**" + node.args.kwarg.arg)
            functions.append({"name": node.name, "arguments": arguments})

    return {"imports": sorted(set(imports)), "functions": functions}


def inspect_repository(path: Path):
    if not path.exists():
        return {"exists": False, "count": 0, "names": []}

    try:
        root = ElementTree.parse(path).getroot()
    except (OSError, ElementTree.ParseError) as error:
        return {"exists": True, "error": str(error)}

    names = []
    for element in root.iter():
        for key in ("name", "Name"):
            value = element.attrib.get(key)
            if value:
                names.append(value)
                break

    entry_count = sum(1 for _ in root.iter()) - 1
    return {"exists": True, "count": entry_count, "names": sorted(set(names))}


def inspect_project(project_root: Path):
    package_path = project_root / "package.json"
    if not package_path.exists():
        raise FileNotFoundError(f"package.json not found: {package_path}")

    package_data = load_json(package_path)
    flows = []
    for flow in package_data.get("flows", []):
        filename = flow.get("filename") or flow.get("name")
        kind = flow.get("kind") or ""
        suffix = ".pybx" if kind.lower() == "visual" else ".py"
        flow_path = project_root / f"{filename}{suffix}"
        item = {
            "name": flow.get("name"),
            "filename": filename,
            "kind": kind,
            "groupName": flow.get("groupName"),
            "file": flow_path.name,
            "exists": flow_path.exists(),
        }
        if flow_path.exists() and kind.lower() == "visual":
            data = flow_path.read_bytes()
            item["size"] = len(data)
            item["sha256"] = hashlib.sha256(data).hexdigest()
            item["binary"] = True
        elif flow_path.exists():
            item["code"] = analyze_code_flow(flow_path)
        flows.append(item)

    variables = package_data.get("variables") or []
    variable_names = []
    if isinstance(variables, list):
        variable_names = [item.get("name") for item in variables if isinstance(item, dict) and item.get("name")]
    elif isinstance(variables, dict):
        variable_names = list(variables)

    return {
        "startup": package_data.get("startup"),
        "robot_type": package_data.get("robot_type"),
        "flows": flows,
        "variable_names": sorted(set(variable_names)),
        "selectors": inspect_repository(project_root / "selectorsV2.xml"),
        "images": inspect_repository(project_root / "imagesV2.xml"),
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only inventory of a ShadowBot project")
    parser.add_argument("project_root", nargs="?", default=".", help="Directory containing package.json")
    args = parser.parse_args()

    try:
        result = inspect_project(Path(args.project_root).resolve())
    except (FileNotFoundError, json.JSONDecodeError, OSError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
