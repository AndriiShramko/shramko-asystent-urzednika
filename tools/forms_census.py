#!/usr/bin/env python3
"""Census of a forms archive: what each template is and how far a machine gets alone.

Input: a directory made by tools/collect_forms.py (MANIFEST.json plus one folder
per service card). Output: a summary (JSON) and a worklist (CSV), one row per
unique document. No model is called and nothing is sent anywhere; the script
reads geometry and text only.

    python tools/forms_census.py ARCHIVE_DIR --work /tmp/census \
        --out-json data/forms-census.json --out-csv data/forms-census.csv

What is measured for every unique document (by SHA-256):
  pages         page count (word-processor files: after conversion to PDF)
  text_chars    characters in the text layer (first 40 pages)
  acro_fields   fillable fields the PDF itself declares (AcroForm)
  dotted        dotted or underscored leaders in the text ("......", "____")
  boxes         small drawn boxes, 6 to 26 pt (cells for digits, tick boxes)
  class         see CLASSES below

The two counts "dotted" and "boxes" are a simple rule, not approved fields:
they miss table cells and drawn lines, and they count a leader that wraps onto
two lines twice. They answer one question: is there something to fill in that
a program can find without looking at pixels.

The archive holds templates published by the city. Treat every file as
untrusted input: run with `python -I`, keep this script outside the archive.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import signal
import subprocess
import sys
import time
import zipfile
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

WORD_EXT = {"doc", "docx", "rtf", "odt"}
SHEET_EXT = {"xls", "xlsx", "ods"}
MAX_PAGES = 40
PER_FILE_SECONDS = 90

CLASSES = {
    "fillable_pdf": "PDF that declares its own fields: names and positions come from the file",
    "vector_form": "PDF with a text layer and places to fill found by the simple rule",
    "word_form": "word-processor file with places to fill found after conversion",
    "pdf_text_no_blanks": "PDF with a text layer, no places found: information sheet, or a form made of table cells",
    "word_no_blanks": "word-processor file, no places found: information sheet, or a form made of table cells",
    "scan": "PDF without a text layer: needs reading from pixels",
    "sheet": "spreadsheet",
    "other": "not a document template (image, text, unknown type)",
    "unreadable": "could not be opened or converted in the time limit",
}
FIRST_PASS_FROM_GEOMETRY = ("fillable_pdf", "vector_form", "word_form")

DOT_RUN = re.compile(r"(?:\.{6,}|…{3,}|_{6,}|(?:\. ){6,}|(?:_ ){6,})")
FORM_WORDS = (
    "wniosek", "wniosk", "zgłoszeni", "zgloszeni", "oświadczeni", "oswiadczeni",
    "pełnomocnictw", "pelnomocnictw", "deklaracj", "formularz", "upoważnieni",
    "upowaznieni", "zawiadomieni", "podanie", "druk", "ankiet", "zgoda", "zgod",
    "karta", "zlecenie", "protok",
)
INFO_WORDS = (
    "klauzul", "rodo", "informacj", "instrukcj", "wykaz", "regulamin", "zarządzeni",
    "zarzadzeni", "uchwał", "uchwal", "cennik", "wzór umowy", "objaśnieni", "objasnieni",
)


class _Timeout(Exception):
    pass


def _alarm(_sig, _frm):
    raise _Timeout()


def measure_pdf(path: str) -> dict:
    """Read one PDF. Runs in a worker process with a time limit."""
    out = {"pages": 0, "text_chars": 0, "acro_fields": 0, "dotted": 0,
           "boxes": 0, "image_pages": 0, "measured_pages": 0, "error": ""}
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(PER_FILE_SECONDS)
    try:
        from pypdf import PdfReader
        import pdfplumber

        reader = PdfReader(path, strict=False)
        out["pages"] = len(reader.pages)
        try:
            out["acro_fields"] = len(reader.get_fields() or {})
        except Exception:
            pass
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages[:MAX_PAGES]:
                text = page.extract_text() or ""
                out["text_chars"] += len(re.sub(r"\s", "", text))
                out["dotted"] += len(DOT_RUN.findall(text))
                out["boxes"] += sum(
                    1 for r in page.rects
                    if 6 <= r["width"] <= 26 and 6 <= r["height"] <= 26
                )
                area = float(page.width) * float(page.height)
                if any(float(im["width"]) * float(im["height"]) > 0.5 * area for im in page.images):
                    out["image_pages"] += 1
                out["measured_pages"] += 1
                page.flush_cache()
    except _Timeout:
        out["error"] = "timeout"
    except Exception as exc:  # a broken file must not stop the census
        out["error"] = type(exc).__name__
    finally:
        signal.alarm(0)
    return out


def docx_declared_fields(path: Path) -> int:
    """Content controls and legacy form fields a .docx declares itself."""
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", "replace")
    except Exception:
        return 0
    return xml.count("<w:sdt>") + xml.count("<w:ffData>")


def convert_office(items: list[tuple[str, Path]], work: Path, chunk: int = 30,
                   timeout: int = 600) -> dict[str, Path]:
    """Convert word-processor files to PDF with LibreOffice. Returns key -> pdf."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice or not items:
        return {}
    stage, out = work / "stage", work / "pdf"
    stage.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    staged = []
    for n, (key, src) in enumerate(items):
        ext = src.suffix.lstrip(".").lower()
        dst = stage / f"{n:04d}.{ext}"
        if not dst.exists():
            shutil.copyfile(src, dst)
        staged.append((key, dst, out / f"{n:04d}.pdf"))
    chunks = [staged[i:i + chunk] for i in range(0, len(staged), chunk)]

    def run(args):
        idx, part = args
        todo = [s for s in part if not s[2].exists()]
        if not todo:
            return
        profile = work / f"profile-{idx:03d}"
        cmd = [soffice, f"-env:UserInstallation=file://{profile}", "--headless",
               "--norestore", "--convert-to", "pdf", "--outdir", str(out)]
        cmd += [str(s[1]) for s in todo]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            pass
        shutil.rmtree(profile, ignore_errors=True)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(run, enumerate(chunks)))
    return {key: pdf for key, _src, pdf in staged if pdf.exists()}


def name_kind(text: str) -> str:
    low = text.lower()
    if any(w in low for w in INFO_WORDS) and not any(w in low for w in FORM_WORDS[:9]):
        return "information"
    if any(w in low for w in FORM_WORDS):
        return "form"
    return "unknown"


def classify(ext: str, m: dict | None, converted: bool) -> str:
    if ext in SHEET_EXT:
        return "sheet"
    if ext not in WORD_EXT and ext != "pdf":
        return "other"
    if m is None or (m["error"] and not m["pages"]):
        return "unreadable"
    blanks = m["dotted"] + m["boxes"]
    if ext == "pdf":
        if m["acro_fields"] > 0:
            return "fillable_pdf"
        measured = max(1, m["measured_pages"])
        if m["text_chars"] / measured < 40:
            return "scan"
        return "vector_form" if blanks >= 3 else "pdf_text_no_blanks"
    if not converted:
        return "unreadable"
    return "word_form" if blanks >= 3 else "word_no_blanks"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("archive", type=Path, help="directory with MANIFEST.json")
    ap.add_argument("--work", type=Path, default=Path("/tmp/forms-census"),
                    help="scratch directory for converted files")
    ap.add_argument("--out-json", type=Path, default=Path("data/forms-census.json"))
    ap.add_argument("--out-csv", type=Path, default=Path("data/forms-census.csv"))
    ap.add_argument("--no-office", action="store_true",
                    help="do not convert word-processor files (they are then only counted)")
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()

    t0 = time.time()
    manifest = json.loads((args.archive / "MANIFEST.json").read_text(encoding="utf-8"))
    entries = [e for e in manifest if e.get("file") and (args.archive / e["file"]).is_file()]

    docs: dict[str, dict] = {}
    cards_of: dict[str, set] = defaultdict(set)
    for e in entries:
        sha = e["sha256"]
        cards_of[sha].add(e.get("card_code", ""))
        if sha not in docs:
            p = args.archive / e["file"]
            docs[sha] = {
                "sha256": sha, "file": e["file"], "ext": (e.get("ext") or p.suffix.lstrip(".")).lower(),
                "bytes": e.get("bytes") or p.stat().st_size, "url": e.get("url", ""),
                "label": e.get("label", ""), "card_code": e.get("card_code", ""),
                "card_title": e.get("card_title", ""), "path": p,
            }

    word = [(sha, d["path"]) for sha, d in docs.items() if d["ext"] in WORD_EXT]
    t_conv = time.time()
    converted = {} if args.no_office else convert_office(word, args.work)
    conv_seconds = time.time() - t_conv

    jobs = {}
    for sha, d in docs.items():
        if d["ext"] == "pdf":
            jobs[sha] = str(d["path"])
        elif sha in converted:
            jobs[sha] = str(converted[sha])
    t_meas = time.time()
    measures: dict[str, dict] = {}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for sha, m in zip(jobs.keys(), pool.map(measure_pdf, jobs.values(), chunksize=4)):
            measures[sha] = m
    meas_seconds = time.time() - t_meas

    rows = []
    for sha, d in docs.items():
        m = measures.get(sha)
        cls = classify(d["ext"], m, sha in converted)
        declared = docx_declared_fields(d["path"]) if d["ext"] == "docx" else 0
        rows.append({
            "card_code": d["card_code"], "file": d["file"], "ext": d["ext"], "bytes": d["bytes"],
            "class": cls, "name_kind": name_kind(f'{d["label"]} {Path(d["file"]).name}'),
            "pages": m["pages"] if m else 0, "text_chars": m["text_chars"] if m else 0,
            "acro_fields": m["acro_fields"] if m else 0, "docx_declared_fields": declared,
            "dotted": m["dotted"] if m else 0, "boxes": m["boxes"] if m else 0,
            "used_in_cards": len(cards_of[sha]), "error": (m or {}).get("error", ""),
            "sha256": sha, "url": d["url"],
        })
    rows.sort(key=lambda r: (r["card_code"], r["file"]))

    by_class = Counter(r["class"] for r in rows)
    by_ext = Counter(r["ext"] for r in rows)
    forms = [r for r in rows if r["class"] in FIRST_PASS_FROM_GEOMETRY]
    reused = sorted((r for r in rows if r["used_in_cards"] > 1),
                    key=lambda r: -r["used_in_cards"])
    summary = {
        "what": "Census of the forms archive of Urzad Miasta Bydgoszczy (templates published on the city's service cards)",
        "made_by": "tools/forms_census.py",
        "made_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "method_note": "Counts come from file geometry and text; no model was used. 'dotted' and 'boxes' follow a simple rule and are not approved fields.",
        "manifest_entries": len(manifest),
        "files_present": len(entries),
        "unique_documents": len(rows),
        "service_cards": len({e.get("card_code") for e in entries}),
        "by_extension": dict(by_ext.most_common()),
        "by_class": {k: by_class.get(k, 0) for k in CLASSES},
        "class_meaning": CLASSES,
        "first_pass_from_geometry": {
            "classes": list(FIRST_PASS_FROM_GEOMETRY),
            "documents": len(forms),
            "pages": sum(r["pages"] for r in forms),
            "places_found_by_rule": sum(r["dotted"] + r["boxes"] for r in forms),
            "declared_pdf_fields": sum(r["acro_fields"] for r in forms),
        },
        "needs_reading_from_pixels": by_class.get("scan", 0),
        "no_places_found": by_class.get("pdf_text_no_blanks", 0) + by_class.get("word_no_blanks", 0),
        "pages_total": sum(r["pages"] for r in rows),
        "reuse": {
            "documents_used_in_more_than_one_card": len(reused),
            "card_uses_covered_by_them": sum(r["used_in_cards"] for r in reused),
            "top": [{"file": r["file"], "used_in_cards": r["used_in_cards"]} for r in reused[:8]],
        },
        "name_kind": dict(Counter(r["name_kind"] for r in rows)),
        "name_kind_of_first_pass_documents": dict(Counter(r["name_kind"] for r in forms)),
        "timing_seconds": {
            "office_conversion": round(conv_seconds, 1),
            "measurement": round(meas_seconds, 1),
            "total": round(time.time() - t0, 1),
            "workers": args.workers,
            "note": "Time to read geometry and text of the whole archive on this machine. It is not the time to produce approved form descriptions.",
        },
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with args.out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"unique documents: {len(rows)} of {len(entries)} files, {summary['service_cards']} cards")
    for k in CLASSES:
        if by_class.get(k):
            print(f"  {k:20s} {by_class[k]:4d}")
    fp = summary["first_pass_from_geometry"]
    print(f"first pass from geometry: {fp['documents']} documents, {fp['pages']} pages, "
          f"{fp['places_found_by_rule']} places by rule, {fp['declared_pdf_fields']} declared fields")
    print(f"time: conversion {conv_seconds:.0f} s, measurement {meas_seconds:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
