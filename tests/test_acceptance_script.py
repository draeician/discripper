"""Tests for the acceptance helper script."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_acceptance_script_runs() -> None:
    """Running the acceptance script succeeds and reports success."""

    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "acceptance.sh"

    assert script.exists(), "acceptance script must exist"

    env = os.environ.copy()
    env.setdefault(
        "PYTHONPATH",
        f"{repo_root / 'src'}{os.pathsep}{env.get('PYTHONPATH', '')}".rstrip(os.pathsep),
    )

    result = subprocess.run(
        ["bash", str(script)],
        cwd=repo_root,
        capture_output=True,
        check=True,
        text=True,
        env=env,
    )

    combined_output = f"{result.stdout}{result.stderr}".strip()

    assert "All acceptance scenarios passed." in combined_output
    assert combined_output.count("[dry-run] Would execute:") == 5
