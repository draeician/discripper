from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_demo_script_runs_successfully() -> None:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "demo.sh"
    assert script_path.exists(), "demo.sh must exist for the demo task"

    env = os.environ.copy()

    result = subprocess.run(
        ["bash", str(script_path)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    if result.returncode != 0:
        message = (
            "demo.sh failed with exit code "
            f"{result.returncode}:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        raise AssertionError(message)

    assert "[dry-run]" in result.stdout, "demo script should display dry-run output"
