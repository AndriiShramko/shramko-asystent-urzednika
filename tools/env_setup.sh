#!/usr/bin/env bash
# Lead-only. Creates or refreshes the shared environment `.venv` of the MAIN checkout and the two lock files.
#   bash tools/env_setup.sh           install from the lock files (creates them when missing)
#   bash tools/env_setup.sh relock    resolve again, rewrite the lock files, then install
# Build-time tool: it uses the network. Nothing here runs in the product. Log: tmp/env-setup.log
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p tmp
LOG="tmp/env-setup.log"
: > "$LOG"
if [ -x .venv/Scripts/python.exe ]; then PY=.venv/Scripts/python.exe; elif [ -x .venv/bin/python ]; then PY=.venv/bin/python; else
  python -m venv .venv >> "$LOG" 2>&1 || { echo "FAIL: venv"; exit 1; }
  if [ -x .venv/Scripts/python.exe ]; then PY=.venv/Scripts/python.exe; else PY=.venv/bin/python; fi
fi
export UV_HTTP_TIMEOUT=120
try() { # try N command...: repeat on failure, the event network drops connections
  local n="$1"; shift
  local i=1
  while [ "$i" -le "$n" ]; do
    "$@" >> "$LOG" 2>&1 && return 0
    echo "retry $i of $n: $*" >> "$LOG"
    i=$((i + 1))
  done
  return 1
}
"$PY" -m uv --version >> "$LOG" 2>&1 || try 6 "$PY" -m pip install --quiet --disable-pip-version-check --timeout 90 --retries 5 uv \
  || { echo "FAIL: could not install uv (see $LOG)"; exit 1; }
P=apps/converter
if [ "${1:-}" = "relock" ] || [ ! -s "$P/requirements.lock" ] || [ ! -s "$P/requirements-dev.lock" ]; then
  try 4 "$PY" -m uv pip compile "$P/pyproject.toml" --universal --generate-hashes --python-version 3.13 --no-header \
    -o "$P/requirements.lock" || { echo "FAIL: lock (see $LOG)"; exit 1; }
  try 4 "$PY" -m uv pip compile "$P/pyproject.toml" --extra dev --universal --generate-hashes --python-version 3.13 --no-header \
    -o "$P/requirements-dev.lock" || { echo "FAIL: dev lock (see $LOG)"; exit 1; }
fi
try 6 "$PY" -m uv pip install --python "$PY" --require-hashes -r "$P/requirements-dev.lock" \
  || { echo "FAIL: install (see $LOG)"; exit 1; }
"$PY" -c "import fastapi, pydantic, pypdfium2, pdfplumber, docx, openpyxl, olefile, nh3, rapidfuzz, simplemma, jsonata, jwt, jsonschema, defusedxml, filetype, lxml, PIL, pytest, httpx, reportlab; print('OK: environment ready,', fastapi.__version__, pydantic.__version__)" 2>> "$LOG" \
  || { echo "FAIL: import check (see $LOG)"; exit 1; }
