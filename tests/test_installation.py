"""Installation flow smoke tests."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _bin_dir(venv_dir: Path) -> Path:
    """Return the bin/Scripts directory for a virtual environment."""

    if os.name == "nt":  # pragma: no cover - Windows fallback
        return venv_dir / "Scripts"
    return venv_dir / "bin"


def _run(cmd: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Execute a command and return the completed process."""

    return subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.mark.slow
def test_editable_install_via_pip_and_pipx(tmp_path: Path) -> None:
    """Editable installs via pip and pipx expose the CLI entry point."""

    repo_root = Path(__file__).resolve().parents[1]

    # pip install -e . in an isolated virtual environment
    pip_venv = tmp_path / "pip-venv"
    _run([sys.executable, "-m", "venv", str(pip_venv)])
    pip_python = _bin_dir(pip_venv) / "python"
    _run([str(pip_python), "-m", "pip", "install", "--upgrade", "pip"])
    _run([str(pip_python), "-m", "pip", "install", "--editable", str(repo_root)])
    pip_cli = _bin_dir(pip_venv) / "discripper"
    pip_help = _run([str(pip_cli), "--help"])
    assert pip_help.stdout.lower().startswith("usage:"), pip_help.stdout

    # Ensure pipx is available, installing it locally if needed
    if importlib.util.find_spec("pipx") is None:  # pragma: no cover - executed when pipx missing
        _run([sys.executable, "-m", "pip", "install", "pipx"])

    pipx_env = os.environ.copy()
    pipx_env.update(
        {
            "PIPX_HOME": str(tmp_path / "pipx-home"),
            "PIPX_BIN_DIR": str(tmp_path / "pipx-bin"),
            "PIPX_SHARED_LIBS": str(tmp_path / "pipx-shared"),
        }
    )

    pipx_command = [sys.executable, "-m", "pipx"]
    _run(pipx_command + ["install", "--editable", str(repo_root)], env=pipx_env)
    pipx_cli = Path(pipx_env["PIPX_BIN_DIR"]) / "discripper"
    pipx_help = _run([str(pipx_cli), "--help"], env=pipx_env)
    assert pipx_help.stdout.lower().startswith("usage:"), pipx_help.stdout
    _run(pipx_command + ["uninstall", "discripper"], env=pipx_env)
