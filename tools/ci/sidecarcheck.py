"""The check every sidecar of a converted form must pass in CI (WP-F20i).

A sidecar passes when
  1. the bytes are one JSON object valid against tools/ci/sidecar.v1.schema.json: the shape app/pipeline.py emits
     today (version, converter, counts, warnings, checks, meta, and the two digests the command line adds);
  2. the twelve gate checks G1 to G12 are each there exactly once;
  3. meta.ledger, when present, is valid against `Ledger` of contracts/coi/meta.schema.json (the one part the
     product and the contract of the full sidecar share today);
  4. (when the form is given) form_sha256 is the SHA-256 of the form bytes the same conversion answered with.

The full contract contracts/coi/meta.schema.json is NOT applied to the whole object: the product does not emit
that shape yet (`differences_from_contract` counts the differences; the count is reported, never hidden).
"""
from __future__ import annotations

import hashlib
import json
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHAPE = Path(__file__).resolve().parent / "sidecar.v1.schema.json"
CONTRACT = ROOT / "contracts" / "coi" / "meta.schema.json"
CHECK_IDS = [f"G{n}" for n in range(1, 13)]


@lru_cache(maxsize=1)
def _validators():
    from jsonschema import Draft202012Validator

    shape = json.loads(SHAPE.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    ledger = {"$schema": contract["$schema"], "$defs": contract["$defs"], "$ref": "#/$defs/Ledger"}
    return Draft202012Validator(shape), Draft202012Validator(ledger), Draft202012Validator(contract)


def _lines(validator, doc, prefix: str, limit: int = 5) -> list[str]:
    """One line per schema error: the place and the rule, never a value of the document."""
    errors = sorted(validator.iter_errors(doc), key=lambda e: [str(p) for p in e.absolute_path])
    out = [f"{prefix} /{'/'.join(str(p) for p in e.absolute_path)}: rule '{e.validator}' not met" for e in errors[:limit]]
    if len(errors) > limit:
        out.append(f"{prefix}: {len(errors) - limit} more schema errors")
    return out


def problems_of_sidecar(raw: bytes, form: bytes | None = None) -> list[str]:
    """Empty list when the bytes are a sidecar we may answer with; else one line per problem (no content)."""
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"sidecar is not JSON: {type(exc).__name__}"]
    if not isinstance(doc, dict):
        return [f"sidecar is not an object: {type(doc).__name__}"]
    shape, ledger, _ = _validators()
    out = _lines(shape, doc, "sidecar")
    if out:
        return out
    ids = [c["id"] for c in doc["checks"]]
    if sorted(ids) != sorted(CHECK_IDS):
        out.append(f"sidecar checks are {ids}, not G1 to G12 once each")
    if "ledger" in doc["meta"]:
        out += _lines(ledger, doc["meta"]["ledger"], "sidecar meta/ledger (contract Ledger)")
    if form is not None:
        if "form_sha256" not in doc:
            out.append("sidecar has no form_sha256")
        elif doc["form_sha256"] != hashlib.sha256(form).hexdigest():
            out.append("sidecar form_sha256 is not the digest of the form of the same conversion")
    return out


def differences_from_contract(raw: bytes) -> int:
    """How many rules of contracts/coi/meta.schema.json the whole sidecar does not meet (0 = it is the contract)."""
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return -1
    return sum(1 for _ in _validators()[2].iter_errors(doc))


def main(argv: list[str]) -> int:
    """python tools/ci/sidecarcheck.py NAME.meta.json ... -> one line per file; exit 1 when one fails."""
    bad = 0
    for name in argv:
        raw = Path(name).read_bytes()
        found = problems_of_sidecar(raw)
        print(f"{Path(name).name}: " + ("passes" if not found else "; ".join(found))
              + f" (differences from the contract of the full sidecar: {differences_from_contract(raw)})")
        bad += bool(found)
    return 1 if bad or not argv else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
