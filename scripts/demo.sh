#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SAMPLES_DIR="$ROOT_DIR/samples"

DEMO_TEMP_DIR=""
cleanup() {
  if [[ -n "$DEMO_TEMP_DIR" && -d "$DEMO_TEMP_DIR" ]]; then
    rm -rf "$DEMO_TEMP_DIR"
  fi
}
trap cleanup EXIT

if ! command -v ffmpeg >/dev/null 2>&1; then
  DEMO_TEMP_DIR="$(mktemp -d)"
  cat <<'STUB' >"$DEMO_TEMP_DIR/ffmpeg"
#!/usr/bin/env bash
echo "[demo] ffmpeg stub invoked with: $@" >&2
exit 0
STUB
  chmod +x "$DEMO_TEMP_DIR/ffmpeg"
  export PATH="$DEMO_TEMP_DIR:$PATH"
fi

if command -v discripper >/dev/null 2>&1; then
  CLI=(discripper)
else
  export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
  CLI=(python -m discripper.cli)
fi

run_demo() {
  local label="$1"
  local fixture="$2"
  echo "==> $label"
  "${CLI[@]}" --simulate "$fixture" --dry-run
  echo
}

run_demo "Movie disc simulation" "$SAMPLES_DIR/simulated_movie.json"
run_demo "Series disc simulation" "$SAMPLES_DIR/simulated_series.json"
