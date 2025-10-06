---
id: 4a7d2c19
title: "Initialize PEP 621 project"
role: Coder
priority: P0
phase_id: "P1-T1"
depends_on: []
acceptance:
  - "`pyproject.toml` defines a `[project]` table for `discripper` with name, version, description, authors, and `readme = \"README.md\"`, and configures `hatchling` in `[build-system]`."
  - "`src/discripper/__init__.py` exists with a module docstring and exported `__all__`, and a `tests/__init__.py` file anchors the `tests/` package."
  - "`python -m build` completes successfully from the repository root."
evidence:
  expected:
    - "pip install -e ."
    - "ruff check ."
    - "pytest -q --cov=src --cov-fail-under=80"
    - "python -m build"
  artifacts:
    - "pyproject.toml"
    - "src/discripper/__init__.py"
    - "tests/__init__.py"
---

## Context
Lay the packaging foundation so future tasks can add console hooks, configuration handling, and implementation modules without reworking project metadata.

## Plan
- Create `pyproject.toml` with PEP 621 metadata for `discripper` and configure `hatchling` as the build backend.
- Add `src/discripper/__init__.py` exporting a placeholder namespace and create `tests/__init__.py` to enable package-style tests.
- Run `python -m build` plus the local gates to verify the project builds and tooling succeeds.
