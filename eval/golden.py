"""The golden list: which input files of which task set are golden, and what form JSON is expected.

    from eval.golden import golden_inputs, judged_inputs, expected_forms

The list itself is eval/golden.json. It holds only paths relative to the folder that
tools.coi_paths.coi_dir() returns (set folder / file name), with format and size: never an absolute
path and never a copy of a file (the partner's sets are local only). This module resolves the list on
this machine. Rebuild the list after the sets change:  python -m eval.golden --write
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.coi_paths import coi_dir, sets

LIST = Path(__file__).resolve().parent / "golden.json"
INPUT_FORMATS = {"pdf", "doc", "docx", "ods", "xlsx", "jpg", "jpeg", "png"}
ALIASES = {"jpe": "jpeg"}  # judged set 07 delivers its JPEG with the extension .JPE


def load() -> dict:
    return json.loads(LIST.read_text(encoding="utf-8"))


def _resolve(rel: str) -> Path:
    return coi_dir() / rel


def golden_inputs() -> list[Path]:
    """Input files of the two reference sets, resolved on this machine (may not exist: check .exists())."""
    return [_resolve(f["path"]) for s in load()["reference"] for f in s["inputs"]]


def judged_inputs() -> list[Path]:
    """Input files of the seven judged sets, resolved on this machine."""
    return [_resolve(f["path"]) for s in load()["judged"] for f in s["inputs"]]


def expected_forms() -> dict[str, Path]:
    """Reference set id -> path of the partner's export (the expected form JSON)."""
    return {s["id"]: _resolve(s["expected"]["path"]) for s in load()["reference"]}


def build() -> dict:
    """Scan the local sets and return the list (what is written to eval/golden.json)."""
    out: dict = {
        "description": "Golden list of the converter evaluation. Paths are relative to the folder returned by "
                       "tools.coi_paths.coi_dir(); the files are local only and never in git.",
        "reference": [], "judged": [],
    }
    for folder in sets():
        entry: dict = {"id": folder.name, "inputs": [], "expected": None, "visualisation": []}
        for f in sorted(folder.iterdir()):
            if not f.is_file():
                continue
            ext = ALIASES.get(f.suffix.lower().lstrip("."), f.suffix.lower().lstrip("."))
            item = {"path": f"{folder.name}/{f.name}", "format": ext, "size": f.stat().st_size}
            if ext == "json":
                entry["expected"] = item
            elif "wizualizacja" in f.name.lower():
                entry["visualisation"].append(item)
            elif ext in INPUT_FORMATS:
                entry["inputs"].append(item)
            else:
                raise SystemExit(f"unclassified file in {folder.name}: {f.name}")
        if folder.name.startswith("reference-"):
            out["reference"].append(entry)
        else:
            entry.pop("expected"), entry.pop("visualisation")
            out["judged"].append(entry)
    return out


if __name__ == "__main__":
    if "--write" in sys.argv:
        data = build()
        LIST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("written", LIST, "reference inputs:", sum(len(s["inputs"]) for s in data["reference"]),
              "judged inputs:", sum(len(s["inputs"]) for s in data["judged"]))
    else:
        print(len(golden_inputs()), "golden inputs,", len(judged_inputs()), "judged inputs,",
              sum(p.exists() for p in golden_inputs() + judged_inputs()), "present")
