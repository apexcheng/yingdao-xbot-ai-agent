# 浏览器下载｜识别本轮完成的文件

适用于点击下载按钮后，浏览器直接将文件写入固定下载目录的场景。先使用影刀原生网页下载 API；只有**没有直接返回可靠本轮文件路径**时，再使用下面的磁盘等待逻辑。不依赖「增强工具2026」。

记录 `start_time=time.time()` 后才触发下载；此时间值只用于**排除旧文件**，不能证明哪条异步导出任务属于本轮。任务唯一性参阅 [Web 导出任务绑定](../web.md#绑定本轮导出任务)。

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
                if path.is_file() and path.suffix.lower() not in {".crdownload", ".part", ".tmp"}
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
                if stat.st_size == 0 or stat.st_mtime < start_time - 2:
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

这里的 XPath 仅是调用形式示例，**不是任何真实网站的已核下载按钮**。若多个文件同时生成、目录共享、文件名碰撞或下载完成还需后端任务确认，不能盲选最新文件；先在业务代码中确认文件归属。

证据：参考已核实 `wait_download_file` 的关键行为（临时后缀、时间边界、连续两次稳定、超时异常），采用更精简的标准库写法；未做浏览器真实下载验证。
