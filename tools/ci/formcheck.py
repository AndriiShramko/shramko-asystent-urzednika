"""The check every converted form must pass in CI, whatever the pipeline behind the service is (WP-F20).

It never compares with a stored copy of an output: the stub of today and the real pipeline of tomorrow must both
pass. A form passes when
  1. the bytes are one JSON object whose keys are exactly title, tabs, flow (D1);
  2. `tools/coi_lint.py --profile strict` finds no ERROR: that is contracts/coi/form.schema.json (Draft 2020-12)
     plus the partner's rules that a schema cannot express;
  3. (by the caller) a second conversion of the same input gives the same bytes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TOP_KEYS = {"title", "tabs", "flow"}


def problems_of_form(raw: bytes) -> list[str]:
    """Empty list when the bytes are a form we may answer with; else one line per problem (no content)."""
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"not JSON: {type(exc).__name__}"]
    if not isinstance(doc, dict):
        return [f"not an object: {type(doc).__name__}"]
    out = []
    if set(doc) != TOP_KEYS:
        out.append(f"top-level keys {sorted(doc)} are not exactly {sorted(TOP_KEYS)}")
    from tools.coi_lint import check

    out += [f"lint strict: {msg}" for kind, msg in check(doc, "strict") if kind == "ERROR"]
    return out


def problems_of_pair(first: bytes, second: bytes) -> list[str]:
    """Two conversions of the same input must be byte-equal."""
    return [] if first == second else ["two conversions of the same input differ"]


def main(argv: list[str]) -> int:
    """python tools/ci/formcheck.py FORM.json ... -> one line per file; exit 1 when one fails."""
    bad = 0
    for name in argv:
        found = problems_of_form(Path(name).read_bytes().rstrip(b"\r\n"))
        print(f"{Path(name).name}: " + ("passes" if not found else "; ".join(found)))
        bad += bool(found)
    return 1 if bad or not argv else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
