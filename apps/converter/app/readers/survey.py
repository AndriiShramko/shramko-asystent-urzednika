"""Survey of the readers over every input file of the nine task sets -> eval/readers-sets.json (WP-F2 acceptance).

    bash tools/gate.sh py -m app.readers.survey            # read every file, write the list, print a summary
    bash tools/gate.sh py -m app.readers.survey --check    # also exit 1 when a file raised an unhandled exception

The sets are local only (tools.coi_paths); the list holds relative paths, counts and timings, never content.
A format without a reader in this build is listed with status "no_reader". Imports of eval and tools happen
inside main(), so importing this module (the registry imports every module of the package) costs nothing.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from . import ReaderError, formats, read_document

KIND = {"jpg": "jpeg", "jpe": "jpeg"}
OUT = Path(__file__).resolve().parents[4] / "eval" / "readers-sets.json"


def survey_file(path: Path, fmt: str) -> dict[str, Any]:
    row: dict[str, Any] = {"format": fmt}
    if fmt not in formats():
        row.update(status="no_reader")
        return row
    t = time.perf_counter()
    try:
        model = read_document(path.read_bytes(), fmt)
    except ReaderError as e:
        row.update(status="refused", code=e.code, reason=e.reason)
    except Exception as e:  # noqa: BLE001 - this is exactly what the survey must catch and report
        row.update(status="unhandled", error=type(e).__name__)
    else:
        pages = model.pages
        runs = [r for p in pages for r in p.runs]
        row.update(
            status="read", reader=model.source.reader, pages=len(pages),
            origins=sorted({p.origin for p in pages}),
            runs=len(runs), runs_with_box=sum(r.box is not None for r in runs),
            lines=sum(len(p.lines) for p in pages), rects=sum(len(p.rects) for p in pages),
            tables=sum(len(p.tables) for p in pages), widgets=sum(len(p.widgets) for p in pages),
            warnings=sorted(w.code for w in model.warnings),
        )
    row["seconds"] = round(time.perf_counter() - t, 3)
    return row


def main(argv: list[str]) -> int:
    from eval.golden import load
    from tools.coi_paths import coi_dir

    base = coi_dir()
    golden = load()
    files: list[dict[str, Any]] = []
    for kind in ("reference", "judged"):
        for s in golden[kind]:
            for item in s["inputs"]:
                path = base / item["path"]
                fmt = KIND.get(item["format"], item["format"])
                row = {"set": s["id"], "path": item["path"]}
                row.update(survey_file(path, fmt) if path.exists() else {"format": fmt, "status": "missing"})
                files.append(row)
    counts: dict[str, int] = {}
    for f in files:
        counts[f["status"]] = counts.get(f["status"], 0) + 1
    out = {
        "description": "Readers over every input file of the nine task sets (WP-F2). Paths are relative to "
                       "tools.coi_paths.coi_dir(); counts only, no content. Written by python -m app.readers.survey.",
        "readers": formats(),
        "summary": dict(sorted(counts.items())),
        "files": files,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"written {OUT.name}: {len(files)} files, " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    if "--check" in argv and counts.get("unhandled"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
