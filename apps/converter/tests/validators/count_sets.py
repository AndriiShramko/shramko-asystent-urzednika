"""Count validators and REQUIRED on the task sets (local only; nothing of the sets is written into git).

    bash tools/gate.sh py apps/converter/tests/validators/count_sets.py OUT.json [--all] [--off] [--paper]

One input per judged set, picked like `tools/lead/snapshot_results.py` (the PDF, else the DOCX); `--all` converts
every readable file of every set (judged and reference). `--off` runs with VALIDATORS=off; `--paper` with the
composer's required policy "paper". OUT.json holds, per input: the techNames per validator, and for REQUIRED the
basis the brief gave ("paper", "inferred", "substance", or "attachment" for an upload of the attachment list).
The table printed last holds the counts.
Compare two runs with:  ... count_sets.py --diff BEFORE.json AFTER.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

NAMES = ("REQUIRED", "PESEL", "NIP", "REGON", "ZIP_CODE", "EMAIL", "EPUAP", "ADE", "SERIAL_NUMBER_ID_CARD")
READABLE = {".pdf", ".doc", ".docx", ".ods", ".xlsx", ".jpg", ".jpeg", ".png"}


def _fields(form: dict) -> list[dict]:
    out = []
    for t in form["tabs"]:
        for q in t["questions"]:
            out.append(q["field"])
            out += [c["field"] for c in q["field"]["repeatingSectionGrid"]]
    return out


def measure(form: dict, sidecar: dict, brief) -> dict:
    """`brief` is the brief of the understanding step (None on the interim path): the basis of REQUIRED is read from
    it, per field of the matter; an upload of the attachment list has no basis in the brief and counts as "attachment"."""
    fields = _fields(form)
    keys = sidecar.get("meta", {}).get("brief_keys", {})
    origins = sidecar.get("meta", {}).get("origins", {})
    stated = {f.key: f.required_basis for m in brief.matter for f in m.fields} if brief is not None else {}
    per = {n: sorted(f["techName"] for f in fields if n in f["validation"]) for n in NAMES}
    basis = {}
    for f in fields:
        if "REQUIRED" in f["validation"]:
            key = keys.get(f["id"])
            basis[f["techName"]] = stated.get(key) or ("attachment" if origins.get(f["id"]) == "paper" and f["type"] == "FILE_UPLOADER" else "other")
    required_in_brief = sum(1 for b in stated.values() if b) + (sum(1 for a in brief.attachments if a.required and a.covered_by is None) if brief else 0)
    inputs = [f for f in fields if f["type"] not in ("SECTION", "REPEATING_SECTION", "TEXT_BLOCK", "INFO_SECTION", "CONSENT_SECTION")]
    foreign = [f["techName"] for f in fields for v in f["validation"] if v not in NAMES]
    return {"inputs": len(inputs), "validators": per, "required_basis": basis, "required_in_brief": required_in_brief,
            "outside_the_list": foreign}


def run(out: Path, every: bool, off: bool, policy: str | None = None) -> None:
    from app import pipeline
    from app.config import Settings
    from tools.coi_paths import sets

    seen: list = []
    understand = pipeline.understand

    def keep(*args, **kwargs):          # the brief is not in the sidecar: it is caught on its way to the composer
        seen.append(understand(*args, **kwargs))
        return seen[-1]

    pipeline.understand = keep
    if policy:                          # the service has no switch for it yet: the option is set on its way to the composer
        from dataclasses import replace

        options = pipeline.compose_options
        pipeline.compose_options = lambda s: replace(options(s), required_policy=policy)
    convert = pipeline.run
    settings = Settings.from_env({"AUTH_MODE": "off", **({"VALIDATORS": "off"} if off else {})})
    result: dict = {}
    for folder in sets("" if every else "judged"):
        files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in READABLE)
        if not every:
            pick = next((f for f in files if f.suffix.lower() == ".pdf"), None) or next(
                (f for f in files if f.suffix.lower() == ".docx" and "wizualizacja" not in f.name.lower()), None)
            files = [pick] if pick else []
        for n, path in enumerate(files):
            name = f"{folder.name[:9]}{'' if not every else f'#{n}{path.suffix.lower()}'}"
            seen.clear()
            try:
                r = convert(path.read_bytes(), path.name, settings)
            except Exception as exc:  # noqa: BLE001 - a count reports and goes on
                result[name] = {"error": type(exc).__name__}
                continue
            result[name] = measure(r.form, r.sidecar, seen[-1] if seen else None)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    table(result)


def table(result: dict) -> None:
    print("input | inputs | " + " | ".join(NAMES) + " | REQUIRED paper/substance/inferred/attachment/other | required in the brief | outside")
    for name, m in result.items():
        if "error" in m:
            print(f"{name} | {m['error']}")
            continue
        b = list(m["required_basis"].values())
        split = "/".join(str(b.count(k)) for k in ("paper", "substance", "inferred", "attachment", "other"))
        print(f"{name} | {m['inputs']} | " + " | ".join(str(len(m["validators"][n])) for n in NAMES)
              + f" | {split} | {m['required_in_brief']} | {len(m['outside_the_list'])}")


def diff(before: Path, after: Path) -> None:
    a, b = (json.loads(p.read_text(encoding="utf-8")) for p in (before, after))
    for name in sorted(a.keys() | b.keys()):
        x, y = a.get(name, {}), b.get(name, {})
        if "error" in x or "error" in y or not x or not y:
            print(f"{name}: {x.get('error', 'absent' if not x else 'ok')} -> {y.get('error', 'absent' if not y else 'ok')}")
            continue
        for n in NAMES:
            gone = sorted(set(x["validators"][n]) - set(y["validators"][n]))
            new = sorted(set(y["validators"][n]) - set(x["validators"][n]))
            if gone or new:
                print(f"{name} {n}: {len(x['validators'][n])} -> {len(y['validators'][n])}; +{new} -{gone}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--diff":
        diff(Path(args[1]), Path(args[2]))
    else:
        run(Path(args[0]), "--all" in args, "--off" in args, "paper" if "--paper" in args else None)
