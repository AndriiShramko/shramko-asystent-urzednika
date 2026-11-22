"""WP-C1 measuring tool, not a test: what the understanding step says about REQUIRED, per field of the matter.

    bash tools/gate.sh py apps/converter/tests/mean/dump_required.py OUT.tsv [judged-08 judged-09 ...]

One line per field: input, section title, label (cut at 70 characters), required, basis, hint (cut at 50). The task
sets are reached through `tools/coi_paths.py` only; the output goes under `tmp/` and is never committed. Compare two
runs with any text diff. Images are skipped (their reading is slow and is not what this package changes).
"""
from __future__ import annotations

import sys
from pathlib import Path

FORMATS = (".pdf", ".doc", ".docx", ".ods", ".xlsx")


def main(out: Path, only: list[str]) -> None:
    from app import pipeline
    from app.config import Settings
    from tools.coi_paths import sets

    seen: list = []
    understand = pipeline.understand

    def keep(*args, **kwargs):          # the brief is caught on its way to the composer
        seen.append(understand(*args, **kwargs))
        return seen[-1]

    pipeline.understand = keep
    settings = Settings.from_env({"AUTH_MODE": "off"})
    lines: list[str] = []
    for folder in sets(""):
        name = folder.name[:9]
        if only and name not in only:
            continue
        for path in sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in FORMATS):
            seen.clear()
            tag = f"{name}{path.suffix.lower()}"
            try:
                pipeline.run(path.read_bytes(), path.name, settings)
            except Exception as exc:  # noqa: BLE001 - a count reports and goes on
                lines.append(f"{tag}\tERROR {type(exc).__name__}")
                continue
            if not seen:
                lines.append(f"{tag}\tno brief")
                continue
            for section in seen[-1].matter:
                title = (getattr(section, "title", None) or "")[:50]
                for f in section.fields:
                    lines.append("\t".join([tag, title, f.label[:70], "required" if f.required else "optional",
                                            f.required_basis or "-", (f.hint or "")[:50]]))
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(lines)} lines; required {sum(1 for x in lines if chr(9) + 'required' + chr(9) in x)};"
          f" paper {sum(1 for x in lines if chr(9) + 'paper' + chr(9) in x)}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2:])
