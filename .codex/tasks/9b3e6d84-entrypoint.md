---
id: 9b3e6d84
title: "Expose console entry point"
role: Coder
priority: P0
phase_id: "P1-T2"
depends_on:
  - 4a7d2c19
acceptance:
  - "`pyproject.toml` adds a `console_scripts` entry mapping `discripper = discripper.cli:main`."
  - "`pip install -e .` creates an executable named `discripper` on `PATH` that resolves to the package CLI."
  - "Running `discripper --help` prints the placeholder usage text without raising an exception."
evidence:
  expected:
    - "pip install -e ."
    - "ruff check ."
    - "pytest -q --cov=src --cov-fail-under=80"
    - "discripper --help"
  artifacts:
    - "pyproject.toml"
    - "src/discripper/cli.py"
---

## Context
Make the command-line entry point available early so downstream tasks can add subcommands and configuration flags against the same executable.

## Plan
- Update `pyproject.toml` to declare `discripper` as a console script targeting `discripper.cli:main`.
- Implement a minimal `main()` function in `src/discripper/cli.py` that prints usage help and exits cleanly.
- Verify the local gates and confirm `discripper --help` works after an editable install.
