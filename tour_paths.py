"""Locate the LiteX source checkout used by the tour scripts."""

import os
from pathlib import Path
import sys


def add_litex_to_path(tour_root):
    configured = os.environ.get("LITEX_ROOT")
    if configured:
        candidates = [Path(configured).expanduser()]
    else:
        candidates = [tour_root / "external/litex", tour_root.parent]

    for candidate in candidates:
        source = candidate.resolve()
        if (source / "litex/__init__.py").is_file():
            sys.path.insert(0, str(source))
            return source

    if configured:
        raise FileNotFoundError(
            f"LITEX_ROOT={configured} is not a LiteX source root containing litex/__init__.py"
        )
    return None  # Fall back to LiteX installed in the active Python environment.
