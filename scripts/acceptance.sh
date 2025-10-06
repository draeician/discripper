#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SAMPLES_DIR="$ROOT_DIR/samples"

ACCEPTANCE_TEMP_DIR=""
cleanup() {
  if [[ -n "$ACCEPTANCE_TEMP_DIR" && -d "$ACCEPTANCE_TEMP_DIR" ]]; then
    rm -rf "$ACCEPTANCE_TEMP_DIR"
  fi
}
trap cleanup EXIT

if command -v discripper >/dev/null 2>&1; then
  CLI=(discripper)
else
  export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
  CLI=(python -m discripper.cli)
fi

if ! command -v dvdbackup >/dev/null 2>&1 && ! command -v ffmpeg >/dev/null 2>&1; then
  ACCEPTANCE_TEMP_DIR="$(mktemp -d)"
  cat <<'STUB' >"$ACCEPTANCE_TEMP_DIR/ffmpeg"
#!/usr/bin/env bash
echo "[acceptance] ffmpeg stub invoked with: $@" >&2
exit 0
STUB
  chmod +x "$ACCEPTANCE_TEMP_DIR/ffmpeg"
  export PATH="$ACCEPTANCE_TEMP_DIR:$PATH"
fi

abspath() {
  local path="$1"
  if [[ "$path" == /* ]]; then
    printf '%s\n' "$path"
    return
  fi

  local dir
  dir="$(cd "$(dirname "$path")" && pwd)"
  printf '%s/%s\n' "$dir" "$(basename "$path")"
}

run_case() {
  local label="$1"
  local fixture="$2"
  local expected_type="$3"
  local expected_plans="$4"

  local fixture_path
  fixture_path="$(abspath "$SAMPLES_DIR/$fixture")"

  echo "==> $label"
  local output
  if ! output=$("${CLI[@]}" --simulate "$fixture_path" 2>&1); then
    echo "$output"
    echo "[acceptance] Scenario '$label' failed" >&2
    return 1
  fi

  echo "$output"

  if ! grep -q "EVENT=CLASSIFIED TYPE=$expected_type" <<<"$output"; then
    echo "[acceptance] Expected classification type '$expected_type' not found for $label" >&2
    return 1
  fi

  if grep -q '^Error:' <<<"$output"; then
    echo "[acceptance] Encountered error output for $label" >&2
    return 1
  fi

  local plan_count
  plan_count=$(grep -c '\[dry-run\] Would execute:' <<<"$output" || true)
  if [[ "$plan_count" -ne "$expected_plans" ]]; then
    echo "[acceptance] Expected $expected_plans rip plans but saw $plan_count for $label" >&2
    return 1
  fi
}

run_case "Movie disc simulation" "simulated_movie.json" "movie" 1
run_case "Series disc simulation" "simulated_series.json" "series" 4

echo "All acceptance scenarios passed."
