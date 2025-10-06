# .codex/tasks/

This directory holds **all task files** for the project.  
Each task is a standalone markdown file named with a random 8-hex hash and a short slug:

```

abcd1234-add-config-loader.md

```

---

## 📌 Structure

Each task file follows the format defined in `.codex/instructions/TASK_TEMPLATE.md`, including:

- Front-matter fields (`id`, `title`, `role`, `priority`, `phase_id`, etc.)
- Acceptance checks
- Evidence expectations
- Context and plan sections

---

## 🧠 Conventions

- One file per task.
- Do not edit tasks once they are marked complete — instead, create follow-up tasks.
- Use `[CLAIM]`, `[WIP]`, `[REVIEW-REQUEST]`, and `[DONE]` status signals in task threads and link back here.
- Task files map directly to items in `TASKS.md` via `phase_id`.

---

## 📂 Examples

```

.codex/tasks/
├── a1b2c3d4-implement-inspection.md
├── e5f6a7b8-classify-series-vs-movie.md
└── 9abc1234-add-dry-run-flag.md

```

> 🛠️ Tip: use `openssl rand -hex 4` to generate the 8-hex hash prefix.
```
