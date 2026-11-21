#!/usr/bin/env bash
# The gate of the repository and the one way to run the project's Python. Lead-owned.
#
#   bash tools/gate.sh py ARGS...   the shared interpreter with THIS checkout's code importable
#                                   (packages app, converter, tools, eval) and UTF-8 everywhere, for example
#                                     bash tools/gate.sh py -m pytest apps/converter/tests/readers -q
#                                     bash tools/gate.sh py -m converter convert FILE
#   bash tools/gate.sh fast [ARGS]  before every hand-over: syntax-level lint, the tests without the slow ones
#   bash tools/gate.sh full [ARGS]  at a milestone: every test (markers decide what is skipped here), links
#   bash tools/gate.sh lock         lead only: resolve the dependencies again and rewrite the lock files
#
# The interpreter: $GATE_PYTHON, else .venv of this checkout, else .venv of the main checkout (a git worktree
# has none of its own), else python3 or python on the path (CI and the image).
# Never `pip install` to make a test pass: a new dependency is a request to the lead.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

find_python() {
  if [ -n "${GATE_PYTHON:-}" ]; then echo "$GATE_PYTHON"; return; fi
  local common main base rel
  common="$(git -C "$ROOT" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
  main="${common%/.git}"
  for base in "$ROOT" "$main"; do
    [ -n "$base" ] || continue
    for rel in .venv/Scripts/python.exe .venv/bin/python; do
      if [ -x "$base/$rel" ]; then echo "$base/$rel"; return; fi
    done
  done
  if command -v python3 >/dev/null 2>&1; then echo python3; else echo python; fi
}

PY="$(find_python)"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) R="$(cygpath -m "$ROOT")"; SEP=';' ;;
  *) R="$ROOT"; SEP=':' ;;
esac
export PYTHONPATH="$R/apps/converter$SEP$R${PYTHONPATH:+$SEP$PYTHONPATH}"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8

lint() {
  if "$PY" -m ruff --version >/dev/null 2>&1; then
    # Only what is a bug in any style: syntax errors, undefined names, broken comparisons.
    "$PY" -m ruff check --quiet --select E9,F63,F7,F82 "$R/apps/converter" "$R/tools" "$R/eval"
    echo "gate: lint ok"
  else
    echo "gate: lint SKIPPED (ruff is not installed in $PY)"
  fi
}

mode="${1:-}"
[ "$#" -gt 0 ] && shift
case "$mode" in
  py)
    exec "$PY" "$@"
    ;;
  fast)
    lint
    (cd "$ROOT/apps/converter" && "$PY" -m pytest -q --maxfail=20 -m "not slow" "$@")
    echo "gate: fast PASSED on $(git -C "$ROOT" rev-parse --short HEAD)"
    ;;
  full)
    lint
    (cd "$ROOT/apps/converter" && "$PY" -m pytest -q "$@")
    "$PY" "$R/tools/check_links.py" "$R"
    echo "gate: full PASSED on $(git -C "$ROOT" rev-parse --short HEAD)"
    ;;
  lock)
    exec bash "$ROOT/tools/env_setup.sh" relock
    ;;
  *)
    sed -n '2,14p' "${BASH_SOURCE[0]}"
    exit 2
    ;;
esac
