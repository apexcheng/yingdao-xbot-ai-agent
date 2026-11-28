# 浏览器下载｜识别本轮完成的文件

先使用影刀原生网页下载 API。没有可靠的本轮返回路径时，只有下载目录和文件名规则能唯一确定本轮候选，才使用下面的磁盘等待逻辑。

在触发下载前记录 `start_time=time.time()`。模板排除早于这个时点的文件，适用于修改时间能反映本轮写入的下载。异步导出任务归属参阅 [Web 导出任务绑定](../web.md#绑定本轮导出任务)。

```python
import fnmatch
import time
from pathlib import Path


def wait_download_file(download_dir, filename_pattern, start_time, timeout=300):
    """等待本次点击后出现的非临时文件，大小和修改时间连续两次稳定。"""
    folder = Path(download_dir)
    pattern = filename_pattern if any(c in filename_pattern for c in "*?[]") else f"*{filename_pattern}*"
    states = {}
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if folder.exists():
            files = [
                path for path in folder.iterdir()
                if path.is_file()
                and not path.name.startswith("~$")
                and path.suffix.lower() not in {".crdownload", ".part", ".tmp"}
                and fnmatch.fnmatch(path.name, pattern)
            ]
            try:
                files.sort(key=lambda item: item.stat().st_mtime, reverse=True)
            except FileNotFoundError:
                time.sleep(1)
                continue
            for path in files:
                try:
                    stat = path.stat()
                except FileNotFoundError:
                    continue
                if stat.st_size == 0 or stat.st_mtime < start_time:
                    continue
                state = (stat.st_size, stat.st_mtime)
                if states.get(path) == state:
                    return path
                states[path] = state
        time.sleep(1)
    raise TimeoutError(f"本轮下载等待超时：{filename_pattern}")
```

调用方：

```python
start_time = time.time()
page.find_by_xpath("//button[contains(., '下载')]", timeout=5).click()
file_path = wait_download_file(download_dir, "*.xlsx", start_time)
```

XPath 仅用于演示调用形式。模板跳过 `~$` 开头的 Office 锁文件及浏览器临时文件。两次状态稳定只说明候选文件暂时未变化。目录共享、同名覆盖或多个候选无法区分时，先按业务流程确认文件归属。

证据：离线模拟覆盖了 Office 锁文件、点击前旧文件和本轮写入的候选。未做浏览器真实下载验证。
