"""将知识库最新 Agent 规则同步到本机全部影刀账号及项目。"""

import os
import shutil
from pathlib import Path


TEMPLATE = Path(__file__).resolve().parent.parent / "project-template"
APPS = Path(os.environ["LOCALAPPDATA"]) / "ShadowBot" / "users"
SKILLS = ("code-quality", "rpa-practices", "spreadsheet-operations", "xbot-tools")
OLD_SKILLS = (
    "code-consistency", "code-review", "code-simplifier",
    "shadowbot-cli", "xbot-app-lifecycle", "xbot-project-diagnostics",
)
OLD_REFERENCES = (
    ".agents/skills/rpa-practices/references/excel-wps.md",
    ".agents/skills/rpa-practices/references/workflow-composition.md",
)


def remove(path):
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def sync(project, sources):
    updated = 0
    for source in sources:
        target = project / source.relative_to(TEMPLATE)
        if target.is_file() and target.read_bytes() == source.read_bytes():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        updated += 1

    for old in OLD_REFERENCES:
        (project / old).unlink(missing_ok=True)
    for name in OLD_SKILLS:
        for parent in (".agents/skills", ".claude/skills"):
            remove(project / parent / name)

    for name in SKILLS:
        link = project / ".claude" / "skills" / name
        destination = Path("../../.agents/skills") / name
        if link.is_symlink() and link.readlink() == destination:
            continue
        link.parent.mkdir(parents=True, exist_ok=True)
        remove(link)
        link.symlink_to(destination, target_is_directory=True)

    if any((project / source.relative_to(TEMPLATE)).read_bytes() != source.read_bytes()
           for source in sources):
        raise RuntimeError("同步文件校验失败")
    if any(not (project / ".claude" / "skills" / name).is_dir() for name in SKILLS):
        raise RuntimeError("Claude Skill 链接校验失败")
    return updated


def main():
    if not APPS.is_dir():
        raise FileNotFoundError(f"未找到影刀用户目录：{APPS}")

    sources = [
        path for path in TEMPLATE.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.relative_to(TEMPLATE).parts[0] in ("AGENTS.md", ".agents", ".claude", ".codex")
    ]
    projects = sorted(APPS.glob("*/apps/*/xbot_robot"))
    successful = skipped = updated = 0
    failed = []
    for project in projects:
        if not (project / "package.json").is_file():
            skipped += 1
            continue
        try:
            updated += sync(project, sources)
            successful += 1
        except Exception as error:
            failed.append((project, error))

    print(f"扫描 {len(projects)} 个目录；成功 {successful}，跳过 {skipped}，失败 {len(failed)}；更新规则文件 {updated} 个")
    for project, error in failed:
        print(f"失败：{project}：{error}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
