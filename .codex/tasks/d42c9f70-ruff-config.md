---
id: d42c9f70
title: "Add Ruff config"
role: Coder
priority: P0
phase_id: "P1-T5"
depends_on:
  - 4a7d2c19
acceptance:
  - "`pyproject.toml` configures Ruff under `[tool.ruff]` (and sub-tables) with target version `py311`, src layout includes `src` and `tests`, and enables lint rules agreed for the project."
  - "`ruff check .` passes without diagnostics on a clean checkout."
  - "`README.md` (or equivalent developer docs) documents how to run `ruff check .` in the Local Gates section."
evidence:
  expected:
    - "pip install -e ."
    - "ruff check ."
    - "pytest -q --cov=src --cov-fail-under=80"
  artifacts:
    - "pyproject.toml"
    - "README.md"
---

## Context
Introduce linting early to keep style consistent, matching the repo's local gates and enabling CI enforcement later.

## Plan
- Add a Ruff configuration to `pyproject.toml` covering the `src/` and `tests/` directories with the desired target version and rule set.
- Verify linting succeeds on a clean workspace using the standard command.
- Update `README.md` (or developer guide) to mention Ruff in the contributor workflow and align with the local gates.
