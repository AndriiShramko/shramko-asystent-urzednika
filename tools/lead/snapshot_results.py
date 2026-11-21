"""Milestone snapshot: convert one input of each judged set natively and write results/<set>/form.json.

Run from the repository root with the project's Python:  bash tools/gate.sh py <this file> <repo root>
Prefers the PDF of a set, then the DOCX. Prints one line per set; exits 1 when a set gave no form.
"""
import json
import sys
from pathlib import Path

from app.config import Settings
from app.pipeline import run
from tools.coi_paths import sets

root = Path(sys.argv[1])
try:
    settings = Settings.from_env({"AUTH_MODE": "off"})
except Exception:  # the constructor name differs between versions of the shell
    from app.config import load_settings

    settings = load_settings({"AUTH_MODE": "off"})

bad = 0
for folder in sets("judged"):
    files = sorted(folder.iterdir())
    pick = next((f for f in files if f.suffix.lower() == ".pdf"), None) or next(
        (f for f in files if f.suffix.lower() == ".docx" and "wizualizacja" not in f.name.lower()), None)
    if pick is None:
        print("%s: no PDF or DOCX" % folder.name)
        bad += 1
        continue
    try:
        result = run(pick.read_bytes(), pick.name, settings)
    except Exception as exc:  # noqa: BLE001 - a snapshot reports and goes on
        print("%s: FAILED %s: %s" % (folder.name, type(exc).__name__, str(exc)[:120]))
        bad += 1
        continue
    out = root / "results" / folder.name
    out.mkdir(parents=True, exist_ok=True)
    (out / "form.json").write_text(json.dumps(result.form, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (out / "meta.json").write_text(json.dumps(result.sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    tabs = result.form.get("tabs", [])
    print("%s: %s -> title=%r pages=%d" % (folder.name, pick.suffix.lower(), result.form.get("title"), len(tabs)))
sys.exit(1 if bad else 0)
