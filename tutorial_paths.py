"""Locate the LiteX source checkout used by the tutorial scripts."""

import os
from pathlib import Path
import sys


def add_litex_to_path(tutorial_root):
    configured = os.environ.get("LITEX_ROOT")
    if configured:
        candidates = [Path(configured).expanduser()]
    else:
        candidates = [tutorial_root / "external/litex", tutorial_root.parent]

    for candidate in candidates:
        source = candidate.resolve()
        if (source / "litex/__init__.py").is_file():
            sys.path.insert(0, str(source))
            return source

    if configured:
        raise FileNotFoundError(
            f"LITEX_ROOT={configured} 不是 LiteX 源码根目录；应包含 litex/__init__.py"
        )
    return None  # 允许从当前 Python 环境中已安装的 LiteX 导入。
