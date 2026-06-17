from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_root_app_help_works_from_other_cwd(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(repo_root / "app.py"), "--help"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Run radio-sucrose live loop" in result.stdout
