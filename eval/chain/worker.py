"""One file through the service's entry, in its own process: `python -m eval.chain.worker FILE [NAME]`.

Prints exactly one JSON line (no file content, no exception message) and exits 0. The parent decides about time
limits. The guard runs first (`inspect_upload`, as the command line and the HTTP shell do), then `pipeline.run`.
Fault injection for the tests of the chain itself: the variable CHAIN_FAULT=raise makes the pipeline raise.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

_POLISH = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]|\b(plik|pliku|nie|jest|format|dokument|strony|rozmiar|przekracza|zawiera)\b", re.I)


def is_polish(text: str) -> bool:
    return bool(text) and bool(_POLISH.search(text))


def classify(path: Path, name: str) -> dict:
    from app import pipeline
    from app.config import Settings
    from app.guard import ProblemError, inspect_upload

    rec: dict = {"outcome": "failed", "gate": "n/a", "lint_errors": 0, "fields": 0, "fields_matter": 0,
                 "no_label": 0, "warnings": {}, "error": ""}
    t0 = time.monotonic()
    try:
        # the corpus holds rtf, odt, tif and more: the chain measures every reader, so the extra formats are on
        settings = Settings.from_env({"STRICT_EXTENSIONS": "false", **os.environ, "AUTH_MODE": "off"})
        data = path.read_bytes()
        info = inspect_upload(name, data, settings)
        if os.environ.get("CHAIN_FAULT") == "raise":
            raise RuntimeError("fault injected by the chain test")
        result = pipeline.run(data, info.name, settings)
    except ProblemError as exc:
        rec["problem_code"] = exc.code
        if exc.code == "GATE_FAILED":
            rec.update(gate="failed", error="GATE_FAILED")
        elif is_polish(exc.detail):
            rec["outcome"] = "refused"
        else:
            rec["error"] = "RefusalWithoutPolishReason:" + exc.code
    except BaseException as exc:  # noqa: BLE001 - every other exception is a failure; only its class is kept
        rec["error"] = type(exc).__name__
    else:
        from tools.coi_lint import check

        rec["outcome"] = "converted"
        rec["gate"] = "passed" if all(c["status"] != "failed" for c in result.sidecar["checks"]) else "failed"
        rec["lint_errors"] = sum(1 for level, _ in check(result.form, "strict") if level == "ERROR")
        rec["fields"] = result.sidecar["counts"]["fields"]
        codes: dict[str, int] = {}
        for w in result.sidecar["warnings"]:
            codes[w["code"]] = codes.get(w["code"], 0) + 1
        rec["warnings"] = codes
        rec["no_label"] = sum(n for c, n in codes.items() if "LABEL" in c)
        origins = result.sidecar.get("meta", {}).get("origins")
        if isinstance(origins, dict):
            rec["fields_matter"] = sum(1 for v in origins.values() if v != "standard")
        if "NO_MATTER" in codes:
            rec["fields_matter"] = 0
    rec["seconds"] = round(time.monotonic() - t0, 2)
    return rec


def main(argv: list[str]) -> int:
    path = Path(argv[1])
    print(json.dumps(classify(path, argv[2] if len(argv) > 2 else path.name), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
