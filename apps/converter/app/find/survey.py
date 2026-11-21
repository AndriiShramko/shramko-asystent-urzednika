"""Survey of the finder over the PDF and DOCX of the nine task sets -> eval/finder-sets.json (WP-F3 acceptance).

    bash tools/gate.sh py -m app.find.survey            # read, find, write the list, print a summary
    bash tools/gate.sh py -m app.find.survey --check    # also exit 1 when a file raised an unhandled exception

The sets are local only (tools.coi_paths); the list holds relative paths and counts, never content: candidates
per kind, combs with their cell counts, groups with their option counts, sections, warnings per code, and the
coverage of the runs (app.model.count_coverage). Imports of eval and tools happen inside main().
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

FORMATS = ("pdf", "docx")
OUT = Path(__file__).resolve().parents[4] / "eval" / "finder-sets.json"


def survey_file(path: Path, fmt: str) -> dict[str, Any]:
    from app.find import find
    from app.model import count_coverage
    from app.readers import ReaderError, read_document

    row: dict[str, Any] = {"format": fmt}
    t = time.perf_counter()
    try:
        model = read_document(path.read_bytes(), fmt)
    except ReaderError as e:
        row.update(status="refused", code=e.code)
        return row
    try:
        out = find(model, {"strict": True})
        cov = count_coverage(out, model)
    except Exception as e:  # noqa: BLE001 - this is exactly what the survey must catch and report
        row.update(status="unhandled", error=type(e).__name__)
        return row
    top = [c for c in out.candidates if c.group is None]
    row.update(
        status="found", pages=len(model.pages), runs=sum(len(p.runs) for p in model.pages),
        candidates=len(out.candidates), top_level=len(top),
        kinds=dict(sorted(Counter(c.kind for c in out.candidates).items())),
        combs=[c.cells for c in out.candidates if c.kind == "comb"],
        groups=[len(c.options) for c in out.candidates if c.kind == "choice_group"],
        labelled=sum(c.label is not None for c in top),
        label_how=dict(sorted(Counter(c.label.how for c in top if c.label is not None).items())),
        sections=len(out.sections),
        roles=dict(sorted(Counter(out.roles.values()).items())),
        warnings=dict(sorted(Counter(w.code for w in out.warnings).items())),
        unassigned_runs=len(cov.unassigned),
        seconds=round(time.perf_counter() - t, 3),
    )
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
                if item["format"] not in FORMATS:
                    continue
                path = base / item["path"]
                row = {"set": s["id"], "path": item["path"]}
                row.update(survey_file(path, item["format"]) if path.exists() else {"format": item["format"], "status": "missing"})
                files.append(row)
    counts = Counter(f["status"] for f in files)
    out = {
        "description": "Finder over the PDF and DOCX of the nine task sets (WP-F3). Paths are relative to "
                       "tools.coi_paths.coi_dir(); counts only, no content. Written by python -m app.find.survey.",
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
