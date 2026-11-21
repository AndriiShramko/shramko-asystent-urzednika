"""WP-F3c probe: the matter of the seven judged sets in counts, never in form text.

  bash tools/gate.sh py eval/probe/matter.py [--labels DIR] [--tickets FILE]

Per PDF and DOCX of each judged set (paths only through tools.coi_paths) the converter runs natively (reader,
finder, understanding, composer) and the probe prints: fields of the matter; RADIO and CHECKBOX of the matter with
their option counts; FILE_UPLOADER of the matter (attachments not covered by a standard page, plus uploader fields);
REQUIRED fields of the matter; labels whose printed words (the evidence quote) start lower-case; labels shorter than four letters; strict-linter errors.

--labels DIR   writes one file per input with section role, key, type, required and label, for a before/after diff.
               The labels are text of the partner's forms: DIR must lie outside the repository (the scratch folder).
--tickets FILE counts how many keys quoted in tickets T3, T4 and T5 of the audit file still occur as a key of a
               composed form (the file and its keys stay outside git; only the count is printed).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from app.compose import compose
from app.config import Settings, compose_options, read_options
from app.find import find
from app.mean import understand
from app.readers import read_document
from tools import coi_lint
from tools.coi_paths import sets

REPO = Path(__file__).resolve().parents[2]
SETTINGS = Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false"})
CHOICE = ("RADIO", "CHECKBOX")


def letters(label: str) -> int:
    return sum(1 for c in label if c.isalpha())


def raw_label(x: object) -> str:
    """The label as the paper prints it (the evidence quote; the brief label is sentence-cased), numbering removed."""
    quote = next((e.quote for e in x.evidence if e.quote), None) or x.label  # type: ignore[attr-defined]
    return re.sub(r"^\s*(?:[A-Z]?\d+(?:\.\d+)*[.)]?|[IVX]+\.)\s+", "", quote).lstrip(" -–•*□")


def tech_names(node: object, out: set[str]) -> set[str]:
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "techName" and isinstance(v, str):
                out.add(v)
            else:
                tech_names(v, out)
    elif isinstance(node, list):
        for v in node:
            tech_names(v, out)
    return out


def ticket_keys(path: Path) -> list[str]:
    keys: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"T[345] ", line):
            keys += re.findall(r"`([a-z0-9_.]+)`", line)
    return keys


def key_present(key: str, names: set[str]) -> bool:
    if key.endswith("..."):
        stem = key.rstrip(".")
        return any(n.startswith(stem) for n in names)
    return key in names


def probe(f: Path) -> tuple[dict, list[str], set[str]]:
    model = read_document(f.read_bytes(), f.suffix.lower()[1:], read_options(SETTINGS))
    brief = understand(model, find(model))
    form = json.loads(compose(brief, compose_options(SETTINGS)).form.to_json_bytes())
    fields = [(s.role, x) for s in brief.matter for x in s.fields]
    uploads = [a for a in brief.attachments if a.covered_by is None]
    choices = {t: [len(x.options) for _, x in fields if x.type == t] for t in CHOICE}
    row = {
        "fields": len(fields),
        "RADIO": choices["RADIO"],
        "CHECKBOX": choices["CHECKBOX"],
        "uploaders": len(uploads) + sum(1 for _, x in fields if x.type == "FILE_UPLOADER"),
        "required": sum(1 for _, x in fields if x.required) + sum(1 for a in uploads if a.required),
        "lower": sum(1 for _, x in fields if raw_label(x)[:1].islower()),
        "short": sum(1 for _, x in fields if letters(x.label) < 4),
        "lint": sum(1 for k, _ in coi_lint.check(form, "strict") if k == "ERROR"),
    }
    lines = [f"{r}\t{x.key}\t{x.type}\t{'R' if x.required else '-'}\t{x.label}\t{'|'.join(x.options)}" for r, x in fields]
    lines += [f"attachment\t{a.key}\tFILE_UPLOADER\t{'R' if a.required else '-'}\t{a.label}\t" for a in uploads]
    return row, lines, tech_names(form, set())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", type=Path)
    ap.add_argument("--tickets", type=Path)
    a = ap.parse_args()
    if a.labels is not None:
        if a.labels.resolve().is_relative_to(REPO):
            sys.exit("--labels must point outside the repository: the labels are text of the partner's forms")
        a.labels.mkdir(parents=True, exist_ok=True)
    keys = ticket_keys(a.tickets) if a.tickets else []
    names: set[str] = set()
    print(f"{'set':10} {'fmt':5} {'fields':>6} {'RADIO (options)':18} {'CHECKBOX (options)':20} {'upl':>3} {'req':>3} {'low':>3} {'<4':>3} {'lint':>4}")
    for folder in sets("judged"):
        for f in sorted(folder.iterdir()):
            fmt = f.suffix.lower()
            if fmt not in (".pdf", ".docx"):
                continue
            row, lines, tn = probe(f)
            if fmt == ".pdf":
                names |= tn
            if a.labels is not None:
                (a.labels / f"{folder.name}{fmt}.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
            radio = f"{len(row['RADIO'])} {row['RADIO']}" if row["RADIO"] else "0"
            box = f"{len(row['CHECKBOX'])} {row['CHECKBOX']}" if row["CHECKBOX"] else "0"
            print(f"{folder.name[:9]:10} {fmt:5} {row['fields']:6} {radio:18} {box:20} {row['uploaders']:3} {row['required']:3} "
                  f"{row['lower']:3} {row['short']:3} {row['lint']:4}")
    if keys:
        left = sum(1 for k in keys if key_present(k, names))
        print(f"ticket keys T3-T5 still present in the PDF forms: {left} of {len(keys)}")


if __name__ == "__main__":
    main()
