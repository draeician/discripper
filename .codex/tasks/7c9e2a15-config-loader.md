---
id: 7c9e2a15
title: "Implement config loader"
role: Coder
priority: P1
phase_id: "P2-T1"
depends_on:
  - 4a7d2c19
  - ae56b201
  - f3a1c5d2
acceptance:
  - "Implement a config loader that merges defaults, `{CONFIG_PATH}` contents, and CLI overrides with precedence: defaults < file < flags."
  - "Support overriding the config path via a CLI option or function argument for tests."
  - "Unit tests cover precedence scenarios (no file, file only, file plus overrides) and pass with `pytest -q`."
evidence:
  expected:
    - "pytest -q"
  artifacts:
    - "src/{PROJECT_SLUG}/config.py"
    - "tests/config/test_loader.py"
---

## Context
Phase 2 introduces configuration management; we need a loader that respects `{CONFIG_PATH}` while allowing CLI flags to take priority per the PRD.

## Plan
- Define defaults and implement loader functions/classes that read YAML from `{CONFIG_PATH}` when present.
- Allow callers to override the config path (for CLI flag + testing) and merge inputs with correct precedence.
- Add targeted pytest coverage verifying precedence logic and ensure the suite passes.
