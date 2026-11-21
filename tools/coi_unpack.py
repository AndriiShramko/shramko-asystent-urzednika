#!/usr/bin/env python3
"""Unpack the partner's task archives into data/coi/ under short folder names.

Why this exists: the archives from the task's Discord channel hold a long top folder plus long file
names, and Windows refuses to unpack them in place (path longer than 260 characters). This tool reads
each archive in memory and writes only the base names into short folders, so the paths stay short.

  python tools/coi_unpack.py "<folder with the downloaded archives>"

What it writes (all git-ignored until the partner confirms the sets may be public):
  data/coi/reference-05-nadplata-podatku/     the second form that comes with its JSON
  data/coi/judged-02 … judged-09/             the seven forms whose outputs are judged
  data/coi/text/<set>/<file>.txt              plain text of every DOCX, PDF and XLSX, for quick reading
It then rebuilds data/coi/INDEX.json (size and first 16 hex characters of SHA-256 of every file).

Archives are untrusted input: names are reduced to their base name, nothing is executed, sizes are capped.
Text extraction needs python-docx, pypdf and openpyxl; without them the files are still unpacked.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
COI = REPO / "data" / "coi"
MAX_MEMBER_BYTES = 200 * 1024 * 1024

FOLDERS = {
    1: "reference-01-numer-porzadkowy",
    2: "judged-02-zwrot-oplaty-skarbowej",
    3: "judged-03-wydanie-zaswiadczenia",
    4: "judged-04-wynajecie-swietlicy",
    5: "reference-05-nadplata-podatku",
    6: "judged-06-zajecie-pasa-drogowego",
    7: "judged-07-psy-rasy-agresywne",
    8: "judged-08-deklaracja-odpady",
    9: "judged-09-stypendium-sportowe",
}


def member_full_name(info: zipfile.ZipInfo) -> str:
    name = info.filename
    if not info.flag_bits & 0x800:  # not flagged as UTF-8: undo the cp437 guess of the zip module
        for codec in ("utf-8", "cp852"):
            try:
                name = name.encode("cp437").decode(codec)
                break
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
    return name.replace("\\", "/")


def member_name(info: zipfile.ZipInfo) -> str:
    return member_full_name(info).rsplit("/", 1)[-1]


def unpack(src: Path) -> int:
    seen: set[str] = set()
    written = 0
    for archive in sorted(src.glob("*.zip")):
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest in seen:  # the same archive downloaded twice ("… (1).zip")
            continue
        seen.add(digest)
        with zipfile.ZipFile(archive) as z:
            # The set is recognised by the top folder INSIDE the archive ("2. Wniosek o zwrot …"),
            # because people rename the downloaded archives to shorten them.
            tops = {member_full_name(i).split("/", 1)[0] for i in z.infolist() if not i.is_dir()}
            top = sorted(tops)[0] if tops else archive.name
            m = re.match(r"\s*(\d+)\.", top) or re.match(r"\s*(\d+)\.", archive.name)
            if m:
                folder = FOLDERS.get(int(m.group(1)))
            elif top.lower().startswith("materia"):
                folder = "materials"
            else:
                folder = None
            if folder is None:
                print("skipped (not a known set):", archive.name, "->", top[:60])
                continue
            target = COI / folder
            target.mkdir(parents=True, exist_ok=True)
            for info in z.infolist():
                base = member_name(info)
                if info.is_dir() or not base or base in (".", "..") or info.file_size > MAX_MEMBER_BYTES:
                    continue
                (target / base).write_bytes(z.read(info))
                written += 1
    return written


def text_of(path: Path) -> str | None:
    ext = path.suffix.lower()
    try:
        if ext == ".docx":
            import docx  # python-docx, MIT

            d = docx.Document(str(path))
            lines = [p.text for p in d.paragraphs if p.text.strip()]
            for table in d.tables:
                for row in table.rows:
                    cells, last = [], None
                    for c in row.cells:
                        if c._tc is last:
                            continue
                        last = c._tc
                        cells.append(" ".join(c.text.split()))
                    lines.append("| " + " | ".join(cells) + " |")
            return "\n".join(lines)
        if ext == ".pdf":
            from pypdf import PdfReader  # BSD-3-Clause

            reader = PdfReader(str(path))
            return "\n".join("--- page %d ---\n%s" % (i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages))
        if ext == ".xlsx":
            import openpyxl  # MIT

            wb = openpyxl.load_workbook(str(path), data_only=False)
            out = []
            for ws in wb.worksheets:
                out.append("--- sheet %s (%dx%d) ---" % (ws.title, ws.max_row, ws.max_column))
                for row in ws.iter_rows():
                    cells = ["%s=%s" % (c.coordinate, c.value) for c in row if c.value is not None]
                    if cells:
                        out.append(" ; ".join(cells))
            return "\n".join(out)
    except Exception as e:  # a broken or unusual file must not stop the unpacking
        return "(text extraction failed: %s)" % type(e).__name__
    return None


def extract_text() -> int:
    n = 0
    for folder in sorted(p for p in COI.iterdir() if p.is_dir() and p.name != "text"):
        for f in sorted(folder.iterdir()):
            if not f.is_file():
                continue
            text = text_of(f)
            if text:
                out = COI / "text" / folder.name / (f.name + ".txt")
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(text, encoding="utf-8", newline="\n")
                n += 1
    return n


def rebuild_index() -> int:
    entries = []
    for f in sorted(COI.rglob("*")):
        if not f.is_file() or f.name == "INDEX.json" or "text" in f.relative_to(COI).parts[:1]:
            continue
        rel = f.relative_to(REPO).as_posix()
        entries.append({"file": rel, "bytes": f.stat().st_size, "sha256_16": hashlib.sha256(f.read_bytes()).hexdigest()[:16]})
    (COI / "INDEX.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return len(entries)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    if not src.is_dir():
        sys.exit("Not a folder: %s" % src)
    written = unpack(src)
    texts = extract_text()
    entries = rebuild_index()
    print("unpacked %d files; wrote %d text files; index has %d entries" % (written, texts, entries))


if __name__ == "__main__":
    main()
