import contextlib
import io
import json
import os
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PROJECT_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "project-template"
sys.path.insert(0, str(PROJECT_TEMPLATE_DIR))

import shadowbot_sync_tool


class SyncToolTests(unittest.TestCase):
    def write_package_json(self, project_dir, package_data):
        (project_dir / "package.json").write_text(
            json.dumps(package_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def run_sync(self, project_dir, group=None):
        output = io.StringIO()
        args = SimpleNamespace(project_dir=str(project_dir), group=group)
        with contextlib.redirect_stdout(output):
            shadowbot_sync_tool.sync_project(args)
        return output.getvalue()

    def test_sync_scans_registers_compiles_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            package_data = {
                "flows": [
                    {
                        "name": "run",
                        "filename": "run",
                        "kind": "Code",
                        "opened": True,
                        "groupName": "主流程",
                        "enableCopilot": True,
                        "customField": "keep",
                    },
                    {
                        "name": "process1",
                        "filename": "process1",
                        "kind": "Visual",
                        "groupName": "可视化",
                    },
                ],
                "flow_groups": [{"name": "主流程"}, {"name": "可视化"}],
            }
            self.write_package_json(project_dir, package_data)
            for file_name in (
                "run.py",
                "low_stock_lock.py",
                "tools.py",
                "process1.py",
                "package.py",
                "__init__.py",
                "shadowbot_sync_tool.py",
            ):
                (project_dir / file_name).write_text("value = 1\n", encoding="utf-8")

            first_output = self.run_sync(project_dir)
            first_package_text = (project_dir / "package.json").read_text(encoding="utf-8")
            first_package = json.loads(first_package_text)
            flows = {flow["filename"]: flow for flow in first_package["flows"]}

            self.assertEqual(set(flows), {"run", "process1", "low_stock_lock", "tools"})
            self.assertEqual(flows["run"]["groupName"], "主流程")
            self.assertEqual(flows["run"]["customField"], "keep")
            self.assertFalse(flows["run"]["opened"])
            self.assertFalse(flows["run"]["enableCopilot"])
            self.assertEqual(flows["process1"]["kind"], "Visual")
            self.assertEqual(flows["process1"]["groupName"], "可视化")

            for flow_name in ("low_stock_lock", "tools"):
                self.assertEqual(
                    flows[flow_name],
                    {
                        "name": flow_name,
                        "filename": flow_name,
                        "kind": "Code",
                        "opened": False,
                        "groupName": "",
                        "enableCopilot": False,
                    },
                )

            self.assertNotIn("package", flows)
            self.assertNotIn("__init__", flows)
            for file_name in ("run.py", "low_stock_lock.py", "tools.py", "process1.py"):
                compiled = list(
                    (project_dir / "__pycache__").glob(f"{Path(file_name).stem}.*.pyc")
                )
                self.assertTrue(compiled, file_name)

            self.assertIn("scanned_files=7", first_output)
            self.assertIn(
                "excluded_files=['__init__.py', 'package.py', 'shadowbot_sync_tool.py']",
                first_output,
            )
            self.assertIn("created_flows=['low_stock_lock.py', 'tools.py']", first_output)
            self.assertIn("updated_flows=['run.py']", first_output)
            self.assertIn(
                "compiled_files=['low_stock_lock.py', 'process1.py', 'run.py', 'tools.py']",
                first_output,
            )

            second_output = self.run_sync(project_dir)
            second_package_text = (project_dir / "package.json").read_text(encoding="utf-8")
            second_package = json.loads(second_package_text)
            filenames = [flow["filename"] for flow in second_package["flows"]]

            self.assertEqual(first_package_text, second_package_text)
            self.assertEqual(len(filenames), len(set(filenames)))
            self.assertIn("created_flows=[]", second_output)

    def test_group_only_applies_to_new_flows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            self.write_package_json(
                project_dir,
                {
                    "flows": [
                        {
                            "name": "run",
                            "filename": "run",
                            "kind": "Code",
                            "opened": False,
                            "groupName": "主流程",
                            "enableCopilot": False,
                        }
                    ],
                    "flow_groups": [{"name": "主流程"}],
                },
            )
            (project_dir / "run.py").write_text("value = 1\n", encoding="utf-8")
            (project_dir / "constants.py").write_text("VALUE = 1\n", encoding="utf-8")

            self.run_sync(project_dir, group="工具")
            package_data = json.loads(
                (project_dir / "package.json").read_text(encoding="utf-8")
            )
            flows = {flow["filename"]: flow for flow in package_data["flows"]}

            self.assertEqual(flows["run"]["groupName"], "主流程")
            self.assertEqual(flows["constants"]["groupName"], "工具")
            self.assertIn({"name": "工具"}, package_data["flow_groups"])

    def test_syntax_error_returns_failure_without_saving_flow(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            self.write_package_json(project_dir, {"flows": [], "flow_groups": []})
            original_package_text = (project_dir / "package.json").read_text(encoding="utf-8")
            (project_dir / "broken.py").write_text("def broken(:\n", encoding="utf-8")

            with self.assertRaises(subprocess.CalledProcessError):
                self.run_sync(project_dir)

            self.assertEqual(
                (project_dir / "package.json").read_text(encoding="utf-8"),
                original_package_text,
            )

    def test_sync_succeeds_when_only_excluded_files_exist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            self.write_package_json(project_dir, {"flows": [], "flow_groups": []})
            (project_dir / "package.py").write_text("value = 1\n", encoding="utf-8")
            (project_dir / "__init__.py").write_text("value = 1\n", encoding="utf-8")
            (project_dir / "shadowbot_sync_tool.py").write_text(
                "value = 1\n",
                encoding="utf-8",
            )

            output = self.run_sync(project_dir)

            self.assertIn("scanned_files=3", output)
            self.assertIn("created_flows=[]", output)
            self.assertIn("compiled_files=[]", output)

    def test_direct_invocation_accepts_no_arguments(self):
        args = shadowbot_sync_tool.build_parser().parse_args([])
        self.assertIsNone(args.project_dir)
        self.assertIsNone(args.group)

    def test_rejects_file_arguments(self):
        parser = shadowbot_sync_tool.build_parser()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(["run.py"])

    def test_project_template_base_files_register_as_code_flows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            self.write_package_json(
                project_dir,
                {
                    "startup": "main",
                    "flows": [
                        {
                            "name": "main",
                            "filename": "main",
                            "kind": "Visual",
                            "opened": False,
                            "groupName": None,
                            "enableCopilot": False,
                        }
                    ],
                    "flow_groups": [],
                },
            )
            (project_dir / "main.pybx").write_bytes(b"visual-flow")
            for file_name in ("run.py", "config.py"):
                shutil.copy2(PROJECT_TEMPLATE_DIR / file_name, project_dir / file_name)

            self.run_sync(project_dir)

            package_data = json.loads(
                (project_dir / "package.json").read_text(encoding="utf-8")
            )
            flows = {flow["filename"]: flow for flow in package_data["flows"]}

            self.assertEqual(package_data["startup"], "main")
            self.assertEqual(flows["main"]["kind"], "Visual")
            self.assertEqual(flows["run"]["kind"], "Code")
            self.assertEqual(flows["config"]["kind"], "Code")

    def test_base_config_uses_user_xbot_directory_and_is_isolated_by_project_function(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_root = Path(temp_dir).resolve()
            user_dir = temporary_root / "user"
            project_dirs = [
                temporary_root / "project_a" / "xbot_robot",
                temporary_root / "project_b" / "xbot_robot",
            ]
            project_functions = ["功能A", "功能B"]
            for project_dir, project_function in zip(project_dirs, project_functions):
                project_dir.mkdir(parents=True)
                shutil.copy2(PROJECT_TEMPLATE_DIR / "config.py", project_dir / "config.py")
                config_code = (project_dir / "config.py").read_text(encoding="utf-8")
                (project_dir / "config.py").write_text(
                    config_code.replace("项目功能名", project_function),
                    encoding="utf-8",
                )

            original_cwd = Path.cwd()
            config_paths = []
            try:
                os.chdir(temporary_root)
                with patch.object(Path, "home", return_value=user_dir):
                    for index, project_dir in enumerate(project_dirs):
                        config_path = runpy.run_path(str(project_dir / "config.py"))["CONFIG_PATH"]
                        self.assertEqual(
                            config_path,
                            user_dir / ".xbot" / project_functions[index] / "project_config.json",
                        )
                        config_path.parent.mkdir(parents=True, exist_ok=True)
                        config_path.write_text(f"project-{index}", encoding="utf-8")
                        config_paths.append(config_path)

                    self.assertNotEqual(config_paths[0], config_paths[1])
                    self.assertEqual(config_paths[0].read_text(encoding="utf-8"), "project-0")
                    self.assertEqual(config_paths[1].read_text(encoding="utf-8"), "project-1")

                    os.chdir(project_dirs[1])
                    reloaded_path = runpy.run_path(str(project_dirs[0] / "config.py"))["CONFIG_PATH"]
                    self.assertEqual(reloaded_path, config_paths[0])
                    self.assertEqual(reloaded_path.read_text(encoding="utf-8"), "project-0")
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
