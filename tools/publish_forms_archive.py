#!/usr/bin/env python3
"""Finish the slow download of the form files, pack them and attach the archive to a GitHub release.

Runs without a model and can be left alone: it resumes the downloader until it reports DONE, builds a zip
of the cache with its manifest, uploads the zip and the manifest as release assets, and verifies the upload
by size. The result is written to a JSON file next to the archive.

Usage:
  python tools/publish_forms_archive.py --tag pre-event --repo AndriiShramko/shramko-asystent-urzednika \
      --cache data/forms-cache/all --work U:/Temp/asystent-research

Requires the GitHub CLI (`gh`) to be logged in. The form files are official documents published by the
city hall; the archive only mirrors them with their source addresses and hashes.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import time
import zipfile


def run(cmd, cwd=None, timeout=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--cache", default="data/forms-cache/all")
    ap.add_argument("--work", default=".")
    ap.add_argument("--skip-download", action="store_true")
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache = os.path.join(root, args.cache)
    os.makedirs(args.work, exist_ok=True)
    log_path = os.path.join(args.work, "publish_forms.log")
    result_path = os.path.join(args.work, "publish_forms.result.json")

    def log(msg: str) -> None:
        line = "%s %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        print(line, flush=True)

    result = {"started": datetime.datetime.now().isoformat(timespec="seconds"), "ok": False}

    # 1. download until DONE (resumable); a blocked run waits and retries a few times
    if not args.skip_download:
        for attempt in range(1, 6):
            code, out = run([sys.executable, "-X", "utf8", os.path.join(root, "tools", "collect_forms.py"),
                             "--out", cache, "--min-delay", "4", "--max-delay", "9"], cwd=root, timeout=6 * 3600)
            tail = out.strip().splitlines()[-1] if out.strip() else ""
            log("download attempt %d exit %d: %s" % (attempt, code, tail))
            if code == 0 and "DONE" in out:
                break
            time.sleep(1800 if code == 3 else 120)
        else:
            log("download did not finish; packing what exists")

    manifest_path = os.path.join(cache, "MANIFEST.json")
    if not os.path.exists(manifest_path):
        log("no manifest: nothing to publish")
        json.dump(result, open(result_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return 2
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    ok_rows = [r for r in manifest if r.get("status") == 200 and r.get("file")]
    result["files"] = len(ok_rows)
    result["not_fetched"] = len(manifest) - len(ok_rows)
    result["bytes"] = sum(int(r.get("bytes") or 0) for r in ok_rows)

    # 2. zip
    stamp = datetime.date.today().isoformat()
    zip_path = os.path.join(args.work, "bydgoszcz-forms-%s.zip" % stamp)
    man_copy = os.path.join(args.work, "bydgoszcz-forms-manifest-%s.json" % stamp)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(manifest_path, "MANIFEST.json")
        zf.writestr("README.txt",
                    "Form templates published by Urzad Miasta Bydgoszczy (um.bydgoszcz.pl, bip.um.bydgoszcz.pl),\n"
                    "downloaded on %s. Each file is listed in MANIFEST.json with its source address, the service card,\n"
                    "size and SHA-256. Official documents; check the live service card for the current version.\n"
                    "Catalogue and tools: https://github.com/%s\n" % (stamp, args.repo))
        for r in ok_rows:
            src = os.path.join(cache, r["file"])
            if os.path.exists(src):
                zf.write(src, r["file"])
    with open(manifest_path, "rb") as src, open(man_copy, "wb") as dst:
        dst.write(src.read())
    result["zip"] = zip_path
    result["zip_bytes"] = os.path.getsize(zip_path)
    log("zip %s %.1f MB, files %d" % (zip_path, result["zip_bytes"] / 1e6, result["files"]))

    # 3. upload
    code, out = run(["gh", "release", "upload", args.tag, zip_path, man_copy, "--clobber", "--repo", args.repo], timeout=3600)
    log("upload exit %d %s" % (code, out.strip()[-200:]))

    # 4. verify by size
    code, out = run(["gh", "release", "view", args.tag, "--repo", args.repo, "--json", "assets"], timeout=120)
    try:
        assets = {a["name"]: a["size"] for a in json.loads(out).get("assets", [])}
    except Exception:
        assets = {}
    result["remote_assets"] = assets
    result["ok"] = assets.get(os.path.basename(zip_path)) == result["zip_bytes"]
    result["finished"] = datetime.datetime.now().isoformat(timespec="seconds")
    with open(result_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
    log("RESULT ok=%s files=%s zip_mb=%.1f" % (result["ok"], result["files"], result["zip_bytes"] / 1e6))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
