from __future__ import annotations

import os
from pathlib import Path
import sys


def _bootstrap_repo_paths() -> Path:
    """Make root-level `python app.py` stable from any working directory."""
    repo_root = Path(__file__).resolve().parent
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    os.chdir(repo_root)
    return repo_root


def main() -> None:
    _bootstrap_repo_paths()
    from radio_sucrose.app import main as package_main

    package_main()


if __name__ == "__main__":
    main()
