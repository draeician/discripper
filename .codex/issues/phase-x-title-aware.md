---
title: "Tracking Issue: Phase X – Title-aware Ripping & Metadata JSON"
labels:
  - phase:title-aware
  - component:cli
  - component:ripper
  - type:feature
  - area:metadata
---

## Summary
Coordinate the implementation of Phase X tasks from `TASKS.md` to introduce a title-aware ripping flow with deterministic naming and structured metadata export.

## Task Links
- [ ] `TASKS.md` → Phase X task [#PX-T1]
- [ ] `TASKS.md` → Phase X task [#PX-T2]
- [ ] `TASKS.md` → Phase X task [#PX-T3]
- [ ] `TASKS.md` → Phase X task [#PX-T4]
- [ ] `TASKS.md` → Phase X task [#PX-T5]
- [ ] `TASKS.md` → Phase X task [#PX-T6]
- [ ] `TASKS.md` → Phase X task [#PX-T7]
- [ ] `TASKS.md` → Phase X task [#PX-T8]

## Comments
[START] Phase X – Title-aware Ripping & Metadata JSON
[TEAM-COMM] Summary of new Phase X tasks
task: TASKS.md#phase-x--title-aware-ripping--metadata-json
role: Task Master
status: START
links: n/a
notes: Phase X ready for CODER pickup

Highlights for CODER:
- `#PX-T1`: CLI accepts `--title/-t`, falls back to disc label when omitted, and logs the resolved title.
- `#PX-T2`: Title slug drives deterministic output structure `{slug}/{slug}_track{NN}.{ext}` honoring `{CONFIG_PATH}` overrides.
- `#PX-T3`: Write `{slug}/metadata.json` capturing disc + track metadata; schema to be documented in `docs/metadata-schema.md`.
- `#PX-T6`: Tests cover CLI flag, slug rules, metadata writer (including missing field tolerances).
- `#PX-T7`: Docs require README updates plus full schema documentation in `docs/metadata-schema.md`.
