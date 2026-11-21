#!/usr/bin/env python3
"""Check a form-definition JSON against the partner's rules that a schema cannot express.

    python tools/coi_lint.py FORM.json [FORM2.json ...] [--schema contracts/coi/form.schema.json]

Exit code 1 when an ERROR is found. WARN marks places where the partner's own
sample export departs from the partner's written rules, so we report without failing.
Rules and their sources: docs/02-architecture/coi-json-format.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SECTIONS = {"SECTION", "REPEATING_SECTION"}
INPUTS = {"TEXT_FIELD", "CHECKBOX", "NUMBER", "CONSENT_SECTION", "SELECT", "TEXTAREA",
          "FILE_UPLOADER", "RADIO", "DATEPICKER"}
STATIC = {"TEXT_BLOCK", "INFO_SECTION"}
DICT_TYPES = {"SELECT", "CHECKBOX", "RADIO"}
INITIAL = {
    "PESEL": {"pesel", "name", "surname", "birthDate", "citizenship", "motherName", "birthPlace",
              "motherSurname", "sex", "fatherName", "secondName", "birthCountry", "foreignBirthUSC",
              "familyName", "fatherSurname", "maritalStatus"},
    "PESEL_ADDRESS": {f"{k}Address{p}" for k in ("temporary", "permanent") for p in (
        "Voivodeship", "District", "Community", "Place", "StreetType", "Street", "HouseNumber",
        "ApartmentNumber", "PostalCode")},
    "MLPZ": {"name", "secondName", "surname", "pesel", "phoneNumber", "email", "country", "voivodeship",
             "district", "community", "place", "postCode", "street", "building", "apartment",
             "institutionName", "descriptiveOrganizationName"},
}
REF = re.compile(r"tabs\['([^']+)'\s*in title\]\.questions\['([^']+)'\s*in field\.techName\]"
                 r"(?:\.field\.repeatingSectionGrid\['([^']+)'\s*in field\.techName\])?")


def lint(doc: dict) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    err = lambda m: out.append(("ERROR", m))
    warn = lambda m: out.append(("WARN", m))
    tabs = doc.get("tabs") or []
    if len(doc.get("title", "")) > 255:
        err("title is longer than 255 characters")
    if len(tabs) < 2:
        err("a form needs at least two pages")
    kinds = [t.get("type") for t in tabs]
    if kinds.count("FINISH") != 1 or (kinds and kinds[-1] != "FINISH"):
        err(f"exactly one FINISH page, and it must be the last; found {kinds}")
    ids: set[str] = set()
    index: dict[tuple[str, str], set[str]] = {}
    optional: list[str] = []

    def seen(i, where):
        if i in ids:
            err(f"id used twice: {i} ({where})")
        ids.add(i)

    for t in tabs:
        seen(t.get("id"), f"page {t.get('title')!r}")
        qs = t.get("questions") or []
        if not qs:
            err(f"page {t.get('title')!r} has no component")
        names = set()
        y_next = 0
        for q in sorted(qs, key=lambda q: q.get("y", 0)):
            f = q["field"]
            seen(f.get("id"), f.get("techName"))
            where = f"{t.get('title')}/{f.get('techName')}"
            if f.get("type") not in SECTIONS:
                err(f"{where}: {f.get('type')} sits directly on the page; every component must be inside a section")
                continue
            if f.get("techName") in names:
                err(f"{where}: section techName repeats on the page")
            names.add(f.get("techName"))
            if q.get("y") != y_next:
                warn(f"{where}: y={q.get('y')}, expected {y_next} (sections stack: y of the next = y + rows)")
            y_next = q.get("y", 0) + q.get("rows", 0)
            inner = f.get("repeatingSectionGrid")
            if inner is None and "repetingSectionGrid" in f:
                err(f"{where}: key 'repetingSectionGrid' (the misspelling of the partner's schema file); the sample export and the JSONata paths use 'repeatingSectionGrid'")
                inner = f["repetingSectionGrid"]
            inner = inner or []
            if not inner:
                err(f"{where}: empty section")
            inner_names = set()
            index[(t.get("title"), f.get("techName"))] = inner_names
            for iq in inner:
                g = iq["field"]
                seen(g.get("id"), g.get("techName"))
                w2 = f"{where}/{g.get('techName')}"
                if g.get("type") in SECTIONS:
                    err(f"{w2}: a section inside a section")
                if g.get("techName") in inner_names:
                    err(f"{w2}: techName repeats inside the section")
                inner_names.add(g.get("techName"))
                if t.get("type") == "FINISH" and g.get("type") in INPUTS:
                    err(f"{w2}: input component on the FINISH page")
                if g.get("dictionaryName") and g.get("type") not in DICT_TYPES:
                    err(f"{w2}: dictionary on a {g.get('type')}")
                if g.get("dictionaryName") and g.get("options"):
                    err(f"{w2}: options must be empty when a dictionary is set")
                if g.get("type") in {"RADIO", "CHECKBOX", "SELECT"} and not g.get("dictionaryName") and not g.get("options"):
                    err(f"{w2}: choice component without options and without dictionary")
                if g.get("defaultValueType") == "EXTERNAL_SYSTEM":
                    src, _, attr = str(g.get("defaultValue", "")).partition(".")
                    if attr not in INITIAL.get(src, ()):
                        err(f"{w2}: unknown initial data {g.get('defaultValue')!r}")
                    if not g.get("readOnly"):
                        warn(f"{w2}: initial data on a field that is not read-only (the written rule asks for read-only; the sample leaves contact and address fields editable)")
                if g.get("type") in INPUTS and g.get("type") != "CONSENT_SECTION" and "REQUIRED" not in (g.get("validation") or []):
                    optional.append(g.get("techName"))
                if g.get("type") == "CONSENT_SECTION" and not (g.get("consentSectionConfig") or {}).get("consents"):
                    err(f"{w2}: consent section without consents")

    if optional:
        warn(f"{len(optional)} input fields carry no REQUIRED validator (first: {', '.join(optional[:4])}); "
             "the partner's sample has none at all, the written rules ask for the attribute on every field")

    # state queries must point at components that exist
    def walk(t):
        for q in t.get("questions") or []:
            yield q["field"]
            yield from (iq["field"] for iq in q["field"].get("repeatingSectionGrid") or [])
    titles = [t.get("title") for t in tabs]
    for t in tabs:
        for f in walk(t):
            for s in f.get("states") or []:
                refs = REF.findall(s.get("query", ""))
                if not refs:
                    warn(f"{f.get('techName')}: state query has no recognisable reference")
                for tab_part, sec, inner in refs:
                    hit = [tt for tt in titles if tab_part in (tt or "")]
                    if not hit:
                        err(f"{f.get('techName')}: state refers to a page containing {tab_part!r}, none exists")
                        continue
                    secs = [k for k in index if k[0] in hit and sec in (k[1] or "")]
                    if not secs:
                        err(f"{f.get('techName')}: state refers to section {sec!r}, none exists")
                    elif inner and not any(any(inner in n for n in index[k]) for k in secs):
                        err(f"{f.get('techName')}: state refers to field {inner!r}, none exists in {sec!r}")

    # pages must be chained by flow links
    links = {(l.get("source"), l.get("target")) for l in (doc.get("flow") or {}).get("links") or []}
    for l in (doc.get("flow") or {}).get("links") or []:
        seen(l.get("id"), "flow link")
    tab_ids = [t.get("id") for t in tabs]
    for a, b in links:
        if a not in tab_ids or b not in tab_ids:
            err("flow link points at a page that does not exist")
    reach = {tab_ids[0]} if tab_ids else set()
    grew = True
    while grew:
        grew = False
        for a, b in links:
            if a in reach and b not in reach:
                reach.add(b); grew = True
    for t in tabs:
        if t.get("id") not in reach:
            err(f"page {t.get('title')!r} cannot be reached through flow links from the first page")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--schema", type=Path, default=Path(__file__).resolve().parent.parent / "contracts" / "coi" / "form.schema.json")
    args = ap.parse_args()
    validator = None
    try:
        import jsonschema
        validator = jsonschema.Draft202012Validator(json.loads(args.schema.read_text(encoding="utf-8")))
    except ImportError:
        print("jsonschema is not installed: schema check skipped", file=sys.stderr)
    bad = False
    for path in args.files:
        doc = json.loads(path.read_text(encoding="utf-8"))
        findings = []
        if validator:
            findings += [("ERROR", "schema: " + "/".join(map(str, e.absolute_path)) + ": " + e.message[:160])
                         for e in validator.iter_errors(doc)]
        findings += lint(doc)
        errors = sum(1 for k, _ in findings if k == "ERROR")
        print(f"{path.name}: {errors} errors, {len(findings) - errors} warnings")
        for kind, msg in findings:
            print(f"  {kind}  {msg}")
        bad = bad or errors > 0
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
