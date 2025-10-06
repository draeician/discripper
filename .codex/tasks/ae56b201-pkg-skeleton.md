---
id: ae56b201
title: "Create package skeleton"
role: Coder
priority: P0
phase_id: "P1-T3"
depends_on:
  - 4a7d2c19
acceptance:
  - "`src/discripper/cli.py` defines a `main()` callable that returns an exit code and will be wired to the console script."
  - "`src/discripper/core/__init__.py` exists so the `discripper.core` namespace is importable for future modules."
  - "`python -c \"import discripper; import discripper.cli; import discripper.core\"` succeeds without raising exceptions."
evidence:
  expected:
    - "pip install -e ."
    - "ruff check ."
    - "pytest -q --cov=src --cov-fail-under=80"
    - "python -c \"import discripper; import discripper.cli; import discripper.core\""
  artifacts:
    - "src/discripper/cli.py"
    - "src/discripper/core/__init__.py"
---

## Context
Establish the CLI module and core package namespaces so later tasks can focus on business logic rather than scaffolding.

## Plan
- Implement a placeholder `main()` function in `src/discripper/cli.py` that coordinates with the console script entry point.
- Create the `src/discripper/core/` package with `__init__.py` exporting a stub to anchor future components.
- Run the local gates and a manual import smoke test to confirm the package skeleton is wired correctly.
