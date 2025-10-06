---
id: 9b3e6d84
title: "Expose console entry point"
role: Coder
priority: P0
phase_id: "P1-T2"
depends_on:
  - 4a7d2c19
acceptance:
  - "`pyproject.toml` declares a `console_scripts` entry so `{ENTRYPOINT}` resolves to the package's CLI module."
  - "Editable install (`python -m pip install -e .`) creates a `{ENTRYPOINT}` executable on PATH."
  - "Running `{ENTRYPOINT} --help` succeeds and prints a placeholder usage message (no stack trace)."
evidence:
  expected:
    - "python -m pip install -e ."
    - "{ENTRYPOINT} --help"
  artifacts:
    - "pyproject.toml"
    - "src/{PROJECT_SLUG}/cli.py"
---

## Context
Ensure the package exposes the `{ENTRYPOINT}` command early so future CLI features can plug into the same executable.

## Plan
- Update `pyproject.toml` to map `{ENTRYPOINT}` to the CLI module function stub.
- Provide a minimal CLI callable that emits usage text without failing.
- Validate editable install places the `{ENTRYPOINT}` script and `--help` runs without errors.
