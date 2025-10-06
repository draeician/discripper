# Local Gates — discripper

These are the **required local verification commands** that must pass **before** a `[REVIEW-REQUEST]` is posted for any task in this repository.
They override the defaults listed in `.codex/modes/CODER.md` and reflect the tooling and conventions defined in `PRD.md`.

---

## 🧪 Required Local Verification Commands

```bash
# 1. Install dependencies in editable mode
pip install -e .

# 2. Lint with ruff
ruff check .

# 3. Run unit tests with pytest and enforce minimum coverage
pytest -q --cov=src --cov-fail-under=80
```

---

## 🧰 Guidelines for Coders

* ✅ **All three commands must succeed** locally before posting `[REVIEW-REQUEST]`.
* 📋 Include the **exact transcript** (trimmed) of these commands in your `[REVIEW-REQUEST]` comment.
* 🔁 If any step fails, fix the issues locally and rerun before requesting review.
* 🧪 Tests should pass with at least **80% coverage**. If coverage is below the threshold, either improve tests or document why in your review notes.
* 🪶 Do **not** rely on CI to find failures. Local gates must pass first.

---

## 📌 Notes

* These gates are intentionally minimal to keep `discripper` lightweight and easy to contribute to.
* If the project later adds type checking (`mypy`), packaging steps, or other checks, update this file accordingly.
* All Coders and Reviewers should treat this file as the **s
