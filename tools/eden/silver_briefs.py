#!/usr/bin/env python3
"""Silver briefs: what a careful reader (a hosted model) reads from each task form.

Build-time only, never part of the product. For every set under data/coi (found through
tools/coi_paths.py) it sends the form to one or more hosted models through tools/eden/eden.py and
stores each answer as eval/silver/<set>.<model>.json. The answers follow the ten questions of
docs/02-architecture/coi-json-format.md section 8. They are an independent second opinion for the
rules pipeline: where two models and our rules agree we are probably right, where they differ a
person or a rule must decide. They are never copied into a result.

  python tools/eden/silver_briefs.py                         # all sets, default models
  python tools/eden/silver_briefs.py --sets judged-03 --models anthropic/claude-sonnet-5-5
  python tools/eden/silver_briefs.py --compare               # agreement table of what is on disk

Blank forms are public material; do not use this tool on filled forms.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import eden  # noqa: E402  (the gateway client beside this file)
from tools.coi_paths import coi_dir, sets  # noqa: E402

OUT = ROOT / "eval" / "silver"
DEFAULT_MODELS = ["anthropic/claude-sonnet-5-5", "google/gemini-4-carbon"]

SYSTEM = """You read blank Polish official forms for a team that converts them into electronic forms.
Answer with ONE JSON object and nothing else. Quote the paper exactly in every "quote" (Polish, as printed).
Never invent content that is not on the paper; when the paper does not say, use null and say so in "notes".
The target electronic form has standard sections that are NOT your job (the applicant's name and address, contact data,
consent to data processing, the final page). Your job is what only the paper can tell."""

TASK = """Read the attached form and answer these ten questions as JSON with exactly these keys:

"title": the name of the service as a citizen would see it (sentence case, no legal references), and "title_quote": the heading as printed.
"addressee": {"kind": "office" | "body" | "unknown", "name": string or null, "quote": string or null}. A body is e.g. "Wójt Gminy X", "Prezydent Miasta Y"; an office is e.g. "Urząd Gminy X".
"who_may_apply": {"self": bool, "other_person": bool, "entity": bool, "representatives": [strings such as "pełnomocnik", "przedstawiciel ustawowy"], "evidence": [quotes]}. "entity" means a legal person or an organisational unit (look for "nazwa", NIP, REGON, KRS, "siedziba").
"applicant_extra_data": [{"label": string, "concept": one of "pesel","nip","regon","krs","birth_date","id_document","phone","email","bank_account","other", "required": bool or null, "quote": string}] for data about the applicant that the paper asks for BEYOND name and address.
"matter": [{"section": string, "repeating": bool, "fields": [{"label": string (nominative, sentence case), "type": one of "TEXT_FIELD","TEXTAREA","NUMBER","DATEPICKER","RADIO","CHECKBOX","SELECT","FILE_UPLOADER", "options": [strings] (for RADIO, CHECKBOX, SELECT), "required": bool or null, "validators": [any of "PESEL","NIP","REGON","ZIP_CODE","EMAIL","EPUAP","ADE","SERIAL_NUMBER_ID_CARD"], "hint": string or null, "depends_on": string or null (the condition in plain Polish, e.g. "gdy wybrano: przelewem"), "page": integer, "quote": string}]}]: the fields about the matter itself, grouped in thematic sections in the order of the paper. A row of boxes for one value is ONE field. "niepotrzebne skreślić" is ONE choice. A table with equal rows is a repeating section whose fields are the columns.
"attachments": [{"label": string, "required": bool or null, "depends_on": string or null, "quote": string}].
"declarations": [{"kind": "declaration" | "consent" | "information_clause", "text": string (shortened to 200 characters), "quote_start": string}].
"fee": {"status": "stated" | "not_found" | "ambiguous", "amount": string or null, "what_for": string or null, "quote": string or null}.
"dropped": [{"what": string, "reason": one of "signature","place_and_date","office_use","print_instruction","legal_basis","footnote","duplicate_header","other", "quote": string}]: what exists only because the form is paper.
"conditions": [{"if": string, "then": string, "quote": string}] for every dependency between answers that the wording states.
"composite": {"is_composite": bool, "parts": [strings]}: true when one file holds several applications or variants.
"difficulties": [strings]: what would be hard for an automatic converter on this form.
"notes": [strings]: doubts, unreadable places, things you did not find."""


def pick(folder: Path) -> dict:
    files = {f.suffix.lower(): f for f in sorted(folder.iterdir()) if f.is_file()}
    pdf = next((f for f in sorted(folder.iterdir()) if f.suffix.lower() == ".pdf" and "wizualizacja" not in f.name.lower()), None)
    text = None
    tdir = coi_dir() / "text" / folder.name
    if pdf is not None and (tdir / (pdf.name + ".txt")).exists():
        text = (tdir / (pdf.name + ".txt")).read_text(encoding="utf-8")
    return {"pdf": pdf, "png": files.get(".png"), "text": text}


def messages(src: dict, mode: str) -> list[dict]:
    parts: list[dict] = [{"type": "text", "text": TASK}]
    if mode == "file" and src["pdf"] is not None:
        b64 = base64.b64encode(src["pdf"].read_bytes()).decode("ascii")
        parts.append({"type": "file", "file": {"filename": "form.pdf", "file_data": "data:application/pdf;base64," + b64}})
    else:
        if src["text"]:
            parts.append({"type": "text", "text": "TEXT LAYER OF THE FORM (page marks included):\n" + src["text"][:60000]})
        if src["png"] is not None and src["png"].stat().st_size < 4_000_000:
            b64 = base64.b64encode(src["png"].read_bytes()).decode("ascii")
            parts.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}})
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": parts}]


def parse_json(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except ValueError:
        return None


def run(args: argparse.Namespace) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wanted = [s for s in sets() if not args.sets or any(s.name.startswith(x) for x in args.sets)]
    for folder in wanted:
        src = pick(folder)
        for model in args.models:
            tag = model.split("/")[-1]
            target = OUT / ("%s.%s.json" % (folder.name, tag))
            if target.exists() and not args.force:
                print("exists :", target.name)
                continue
            result = None
            for mode in ("file", "text+image"):
                try:
                    r = eden.request({"model": model, "messages": messages(src, mode), "max_tokens": args.max_tokens}, "silver-labels", 900)
                except RuntimeError as e:
                    print("failed :", folder.name, tag, mode, str(e)[:160])
                    continue
                result = parse_json(r["text"])
                if result is not None:
                    result["_silver"] = {"model": model, "input": mode, "usd": round(r["usd"], 4), "seconds": round(r["seconds"]), "set": folder.name}
                    break
                print("no json:", folder.name, tag, mode, "finish=%s" % r["finish"])
            if result is None:
                continue
            target.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
            n = sum(len(s.get("fields", [])) for s in result.get("matter", []) if isinstance(s, dict))
            print("ok     : %-52s matter fields %-3d $%.3f" % (target.name, n, result["_silver"]["usd"]))


def compare(_: argparse.Namespace) -> None:
    by_set: dict[str, list[dict]] = {}
    for f in sorted(OUT.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        by_set.setdefault(f.name.split(".")[0], []).append(d)
    print("%-36s %-22s %6s %6s %6s %6s  %s" % ("set", "model", "fields", "attach", "decl", "cond", "who (self/other/entity) fee"))
    for name, briefs in by_set.items():
        for d in briefs:
            who = d.get("who_may_apply") or {}
            n = sum(len(s.get("fields", [])) for s in d.get("matter", []) if isinstance(s, dict))
            print("%-36s %-22s %6d %6d %6d %6d  %s/%s/%s %s" % (
                name[:36], (d.get("_silver") or {}).get("model", "?").split("/")[-1][:22], n,
                len(d.get("attachments") or []), len(d.get("declarations") or []), len(d.get("conditions") or []),
                who.get("self"), who.get("other_person"), who.get("entity"), (d.get("fee") or {}).get("status")))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sets", nargs="*", help="prefixes of set folders, e.g. judged-03 reference")
    ap.add_argument("--models", nargs="*", default=DEFAULT_MODELS)
    ap.add_argument("--max-tokens", type=int, default=16000)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--compare", action="store_true")
    a = ap.parse_args()
    (compare if a.compare else run)(a)


if __name__ == "__main__":
    main()
