#!/usr/bin/env bash
# Lead only: merge one package branch into main the way this project requires, in one command.
#
#   bash tools/lead/merge.sh <branch> "<one-line message>" ['<regex of the paths the package owns>']
#
# What it does, in order:
#   1. lists the files the branch changes outside the owned paths (it does not refuse: the lead decides);
#   2. stages the merge WITHOUT committing, so that the owner's publishing check sees everything the branch brings;
#   3. runs the publishing check. Exit 4 means a value that looks like a secret or an identifier: the flagged
#      lines are located (kind and line, never the value) and the script stops with the merge still staged.
#      Fix the lines, `git add` them and run the same command again: it continues the staged merge.
#      Exit 1 means findings to read: only findings that are not the bare words token or secret are printed;
#   4. commits, runs the fast gate, pushes main. A red gate leaves main unpushed.
# Known traps of the scanner: a bare eleven-digit number (a run id of GitHub Actions) can pass its PESEL check,
# write it as actions/runs/<id>; "token: VALUE" in a comment reads as a secret; no literal identifier with a
# valid check digit may be in any file.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
br="${1:?branch}"
msg="${2:?message}"
own="${3:-}"
coauthor="${LEAD_COAUTHOR:-Claude Fable 5.2 <noreply@anthropic.com>}"
[ "$(git rev-parse --abbrev-ref HEAD)" = "main" ] || { echo "not on main"; exit 2; }
mkdir -p tmp
if [ -f .git/MERGE_HEAD ]; then
  echo "continuing the staged merge"
else
  git rev-parse --verify -q "$br" > /dev/null || { echo "no such branch: $br"; exit 2; }
  echo "branch $br at $(git rev-parse --short "$br");$(git diff "main...$br" --shortstat)"
  if [ -n "$own" ]; then
    echo "outside the owned paths: $(git diff "main...$br" --name-only | grep -v -E "$own" | tr '\n' ' ')"
  fi
  git merge --no-ff --no-commit "$br" 2>&1 | tail -1
fi
PRE="$HOME/.claude/skills/gh-publish/scripts/gh_precheck.py"
[ -f "$PRE" ] || { echo "publishing check NOT FOUND at $PRE: nothing committed, nothing pushed"; exit 5; }
python -X utf8 "$PRE" --repo . > tmp/precheck-merge.log 2>&1
rc=$?
echo "publishing check: exit $rc; findings other than bare words: $(grep -E '^  ' tmp/precheck-merge.log | grep -v -c 'слово секрета')"
grep -E '^  ' tmp/precheck-merge.log | grep -v 'слово секрета' | cut -c1-160 | head -8
if [ "$rc" -eq 4 ]; then
  # shellcheck disable=SC2046
  python -X utf8 tools/lead/scan_lines.py $(git diff --cached --name-only) 2>&1 | tail -12
  echo "STOPPED: fix the lines above, git add them, run the same command again (the merge stays staged)"
  exit 4
fi
git commit -q -m "$msg

Co-Authored-By: $coauthor" || { echo "commit failed"; exit 1; }
if ! bash tools/gate.sh fast > tmp/gate-merge.log 2>&1; then
  tail -15 tmp/gate-merge.log
  echo "GATE FAILED after the merge: main is NOT pushed"
  exit 1
fi
tail -2 tmp/gate-merge.log
git push origin main 2>&1 | tail -1
git log --oneline -1
