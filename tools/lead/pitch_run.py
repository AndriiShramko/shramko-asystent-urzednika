"""Lead's recorded run for the pitch: one real blank in, its form JSON out, the twelve gate checks, the fate of every
place of the paper.

    bash tools/gate.sh py tools/lead/pitch_run.py --set 04 [--ext pdf] [--image REF] [--out-root DIR]

Natively it runs `python -m converter convert` of this checkout. With --image it runs that image the way the README
documents it: --network none --read-only --cap-drop ALL, a non-root user and --tmpfs /tmp (OCR needs a writable /tmp
until WP-F20f stage 2 ships one). The partner's files never enter git: everything goes under --out-root, which
defaults to C:/ShramkoU/HackNation2026/pitch-evidence, outside the repository.

Writes into a new folder: input/<the blank>, form.json, <stem>.meta.json (the sidecar), run.json (machine summary)
and run.md (Polish, for slides 3 and 7). Prints only the folder and three counts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.coi_paths import sets  # noqa: E402

DOCKER = r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"
FATE_PL = {
    "FIELD": "pole formularza",
    "STANDARD": "pokryte sekcją standardową",
    "LEFT_OUT": "pominięte z powodem",
    "MERGED": "scalone z innym polem",
    "AWAITING_DECISION": "czeka na decyzję urzędnika",
}
CHECK_PL = {"passed": "zaliczone", "failed": "NIEZALICZONE", "warning": "ostrzeżenie", "not_applicable": "nie dotyczy"}


def pick_file(set_no: str, ext: str) -> Path:
    folders = [p for p in sets("judged") if p.name.startswith(f"judged-{int(set_no):02d}")]
    if not folders:
        raise SystemExit(f"no judged set {set_no} on this machine (python tools/coi_paths.py)")
    files = sorted(p for p in folders[0].iterdir() if p.is_file() and p.suffix.lower() == f".{ext.lower()}")
    if not files:
        raise SystemExit(f"set {set_no} has no .{ext} file")
    return files[0]


def git_head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def run(src: Path, out: Path, image: str | None) -> tuple[list[str], int, float, str]:
    if image:
        cmd = [DOCKER, "run", "--rm", "--network", "none", "--read-only", "--tmpfs", "/tmp", "--cap-drop", "ALL",
               "--user", "10001", "--memory", "1g", "-v", f"{out / 'input'}:/in:ro", "-v", f"{out}:/out",
               image, "convert", f"/in/{src.name}", "--out", "/out/form.json", "--report", "/out"]
        env = dict(os.environ, MSYS_NO_PATHCONV="1")
    else:
        cmd = [sys.executable, "-m", "converter", "convert", str(out / "input" / src.name),
               "--out", str(out / "form.json"), "--report", str(out)]
        env = dict(os.environ)
    t0 = time.perf_counter()
    p = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return cmd, p.returncode, round(time.perf_counter() - t0, 2), (p.stderr or "")[-2000:]


def fields_by_id(form: object) -> dict[str, dict]:
    found: dict[str, dict] = {}

    def walk(o: object) -> None:
        if isinstance(o, dict):
            if isinstance(o.get("id"), str) and "type" in o and "title" in o:
                found[o["id"]] = o
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(form)
    return found


def required(f: dict) -> bool:
    return any(v == "REQUIRED" or (isinstance(v, dict) and v.get("type") == "REQUIRED") for v in f.get("validation") or [])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, help="number of the judged set, e.g. 04")
    ap.add_argument("--ext", default="pdf")
    ap.add_argument("--image", help="image reference; natively when absent")
    ap.add_argument("--out-root", default=r"C:\ShramkoU\HackNation2026\pitch-evidence")
    a = ap.parse_args()

    src = pick_file(a.set, a.ext)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = Path(a.out_root) / f"{stamp}_set{int(a.set):02d}_{a.ext}_{'image' if a.image else 'native'}"
    (out / "input").mkdir(parents=True, exist_ok=False)
    shutil.copy2(src, out / "input" / src.name)
    started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cmd, rc, secs, err = run(src, out, a.image)

    form_path, meta_path = out / "form.json", out / f"{src.stem}.meta.json"
    form = json.loads(form_path.read_text(encoding="utf-8")) if form_path.is_file() else None
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
    fields = fields_by_id(form) if form else {}
    ledger = (meta.get("meta") or {}).get("ledger") or {}
    rows = ledger.get("rows") or []
    checks = meta.get("checks") or []
    warn = Counter(w.get("code") for w in meta.get("warnings") or [])
    summary = {
        "started": started, "seconds": secs, "exit_code": rc, "input": src.name,
        "input_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
        "how": f"image {a.image}" if a.image else f"natively, commit {git_head()}",
        "command": " ".join(x if " " not in x else f'"{x}"' for x in cmd[1:]),
        "title": (form or {}).get("title"), "counts": meta.get("counts"),
        "checks": checks, "ledger": {k: v for k, v in ledger.items() if k != "rows"},
        "fates": dict(Counter(r.get("fate") for r in rows)), "warnings": dict(warn), "stderr_tail": err if rc else "",
    }
    (out / "run.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [f"# Zapis przebiegu: {src.name}", "",
          f"- Start: {started}; czas konwersji: {secs} s; kod wyjścia: {rc}",
          f"- Jak: {summary['how']}" + (" (bez sieci, system plików tylko do odczytu, bez uprawnień)" if a.image else ""),
          f"- SHA-256 pliku wejściowego: `{summary['input_sha256']}`",
          f"- Tytuł formularza: {summary['title']}",
          f"- Liczby: {json.dumps(summary['counts'], ensure_ascii=False)}", "",
          "## Bramka importu: 12 kontroli", "", "| Kontrola | Nazwa | Wynik | Uwagi |", "|---|---|---|---|"]
    for c in checks:
        md.append(f"| {c.get('id')} | {c.get('name')} | {CHECK_PL.get(c.get('status'), c.get('status'))} | {c.get('reason', '')} |")
    md += ["", "## Każde miejsce do wypełnienia na papierze", "",
           f"Znaleziono miejsc: {ledger.get('blanks_found')}; pola: {ledger.get('became_field')}; "
           f"sekcje standardowe: {ledger.get('covered_by_standard')}; pominięte z powodem: {ledger.get('left_out')}; "
           f"scalone: {ledger.get('merged')}; czeka na decyzję: {ledger.get('awaiting_decision')}.", "",
           "| Miejsce | Los | Pole / sekcja / powód | Typ | Wymagane |", "|---|---|---|---|---|"]
    for r in rows:
        fate = r.get("fate")
        f = fields.get(r.get("field") or "", {})
        what = f.get("title") or r.get("section") or r.get("reason") or ""
        md.append(f"| {r.get('candidate')} | {FATE_PL.get(fate, fate)} | {what} | {f.get('type', '')} | "
                  f"{'tak' if f and required(f) else ''} |")
    md += ["", "## Ostrzeżenia w pliku towarzyszącym (sidecar)", ""]
    md += [f"- {code}: {n}" for code, n in sorted(warn.items())] or ["- brak"]
    if rc:
        md += ["", "## Błąd", "", "```", err, "```"]
    (out / "run.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{out}\nexit={rc} seconds={secs} fields={(summary['counts'] or {}).get('fields')} "
          f"checks={dict(Counter(c.get('status') for c in checks))}")
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
