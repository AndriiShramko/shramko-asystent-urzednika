"""WP-F4 acceptance: store the brief of every judged set in eval/briefs/<set>.<format>.json and print, per set,
the fields of the matter, strict-linter errors, the ledger, and the difference from the local silver labels.

  bash tools/gate.sh py eval/briefs/make_briefs.py [SILVER_DIR]

The briefs hold labels read from the blank papers (no personal data). The silver labels are local (eval/silver/,
not in git); without them the comparison columns are left out.
"""
from __future__ import annotations

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

OUT = Path(__file__).resolve().parent
SETTINGS = Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false"})


def words(text: str) -> set[str]:
    return {w[:5] for w in re.findall(r"\w+", text.lower()) if len(w) > 2}


def best_overlap(label: str, others: list[str]) -> float:
    a = words(label)
    if not a:
        return 0.0
    return max((len(a & words(o)) / len(a | words(o)) for o in others if words(o)), default=0.0)


def silver_labels(folder: str, silver: Path | None) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    if silver is None:
        return out
    for f in sorted(silver.glob(folder + ".*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        out[f.name.split(".")[1]] = [x["label"] for s in d.get("matter", []) if isinstance(s, dict) for x in s.get("fields", [])]
    return out


def main() -> None:
    silver = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    for folder in sets("judged"):
        sil = silver_labels(folder.name, silver)
        for f in sorted(folder.iterdir()):
            fmt = f.suffix.lower()
            if fmt not in (".pdf", ".docx"):
                continue
            model = read_document(f.read_bytes(), fmt[1:], read_options(SETTINGS))
            brief = understand(model, find(model))
            form = json.loads(compose(brief, compose_options(SETTINGS)).form.to_json_bytes())
            errors = [m for k, m in coi_lint.check(form, "strict") if k == "ERROR"]
            labels = [x.label for s in brief.matter for x in s.fields]
            (OUT / f"{folder.name}{fmt}.json").write_text(
                json.dumps(brief.model_dump(mode="json", exclude_none=True, by_alias=True), ensure_ascii=False, indent=1), encoding="utf-8")
            cols = ""
            for name, sl in sil.items():
                found = sum(1 for s in sl if best_overlap(s, labels) >= 0.4)
                cols += f" | silver {name[:12]}: {len(sl)} fields, {found} matched by a field of ours"
            print(f"{folder.name[:34]:34} {fmt:5} matter fields {len(labels):3} | lint errors {len(errors)}{cols}")


if __name__ == "__main__":
    main()
