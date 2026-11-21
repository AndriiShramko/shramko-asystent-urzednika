#!/usr/bin/env python3
"""Slowly download the form templates listed in data/forms-catalog.json into a local cache.

The catalogue (links and metadata) is the source; this tool fetches the files themselves, one at a time,
with long random pauses, so that the city's servers see ordinary, light traffic. It is resumable: files
already present with a manifest entry are skipped. Binaries are NOT committed to git (the cache folder is
git-ignored); a curated subset or a release archive is published separately.

Usage:
  python tools/collect_forms.py --out data/forms-cache/all                 # everything, slowly
  python tools/collect_forms.py --out data/forms-cache/all --codes UMB55,UMB60 --min-delay 4 --max-delay 9
  python tools/collect_forms.py --out data/forms-cache/all --limit 50

Stops by itself on signs of blocking (HTTP 403 or 429 twice in a row) and can be started again later.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/131.0.0.0 Safari/537.36")
MAX_BYTES = 20 * 1024 * 1024
ALLOWED_HOSTS = {"um.bydgoszcz.pl", "www.um.bydgoszcz.pl", "bip.um.bydgoszcz.pl", "www.bydgoszcz.pl", "bydgoszcz.pl"}


def safe_name(text: str, fallback: str) -> str:
    text = urllib.parse.unquote(text or "")
    text = re.sub(r"[^\w.\-]+", "_", text, flags=re.UNICODE).strip("._")
    return (text or fallback)[:120]


def load_targets(catalog_path: str, codes: set[str] | None):
    with open(catalog_path, encoding="utf-8") as fh:
        cat = json.load(fh)
    seen: dict[str, dict] = {}
    for card in cat.get("cards", []):
        code = (card.get("code") or "").strip()
        if codes and code not in codes:
            continue
        for att in card.get("attachments", []):
            url = att.get("url")
            if not url or url in seen:
                continue
            host = urllib.parse.urlsplit(url).hostname or ""
            if host not in ALLOWED_HOSTS:
                continue
            seen[url] = {
                "url": url,
                "card_code": code or "no-code",
                "card_title": card.get("title"),
                "card_url": card.get("url"),
                "label": att.get("label"),
                "ext": (att.get("ext") or "").lower(),
            }
    return list(seen.values())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalog", default="data/forms-catalog.json")
    ap.add_argument("--out", default="data/forms-cache/all")
    ap.add_argument("--codes", default="", help="comma-separated card codes; empty = all cards")
    ap.add_argument("--limit", type=int, default=0, help="stop after N downloaded files (0 = no limit)")
    ap.add_argument("--min-delay", type=float, default=4.0)
    ap.add_argument("--max-delay", type=float, default=9.0)
    args = ap.parse_args()

    codes = {c.strip() for c in args.codes.split(",") if c.strip()} or None
    targets = load_targets(args.catalog, codes)
    os.makedirs(args.out, exist_ok=True)
    manifest_path = os.path.join(args.out, "MANIFEST.json")
    manifest: dict[str, dict] = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = {row["url"]: row for row in json.load(fh)}

    robots: dict[str, urllib.robotparser.RobotFileParser] = {}

    def allowed(url: str) -> bool:
        parts = urllib.parse.urlsplit(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in robots:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(base + "/robots.txt")
            try:
                rp.read()
            except Exception:
                rp = None  # unreadable robots.txt: treat as no rules
            robots[base] = rp
        rp = robots[base]
        return True if rp is None else rp.can_fetch(UA, url)

    def save_manifest() -> None:
        rows = sorted(manifest.values(), key=lambda r: (r.get("card_code") or "", r.get("file") or ""))
        tmp = manifest_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, manifest_path)

    done = blocked = 0
    todo = [t for t in targets if not (t["url"] in manifest and manifest[t["url"]].get("status") == 200
                                       and os.path.exists(os.path.join(args.out, manifest[t["url"]]["file"])))]
    print(f"targets {len(targets)}, already have {len(targets) - len(todo)}, to fetch {len(todo)}", flush=True)
    for i, t in enumerate(todo, 1):
        url = t["url"]
        if not allowed(url):
            manifest[url] = {**t, "status": "robots-disallow"}
            continue
        folder = os.path.join(args.out, safe_name(t["card_code"], "no-code"))
        os.makedirs(folder, exist_ok=True)
        name = safe_name(os.path.basename(urllib.parse.urlsplit(url).path), "file")
        if "." not in name and t["ext"]:
            name += "." + t["ext"]
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.6",
            "Referer": t.get("card_url") or "https://um.bydgoszcz.pl/",
        })
        try:
            with urllib.request.urlopen(req, timeout=40) as resp:
                status = resp.status
                ctype = resp.headers.get("Content-Type", "")
                data = resp.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                manifest[url] = {**t, "status": "too-large"}
            else:
                cd_name = None
                # BIP download links carry the real file name only in the response; keep the URL id as prefix
                if "attachments/download" in url:
                    ext = {"application/pdf": "pdf", "application/msword": "doc", "application/rtf": "rtf",
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx"}.get(
                        ctype.split(";")[0].strip(), t["ext"] or "bin")
                    cd_name = f"bip-{name}.{ext}"
                rel = os.path.join(os.path.basename(folder), cd_name or name)
                with open(os.path.join(args.out, rel), "wb") as fh:
                    fh.write(data)
                manifest[url] = {**t, "status": status, "file": rel.replace("\\", "/"), "bytes": len(data),
                                 "content_type": ctype, "sha256": hashlib.sha256(data).hexdigest(),
                                 "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
                done += 1
                blocked = 0
        except urllib.error.HTTPError as err:
            manifest[url] = {**t, "status": err.code}
            if err.code in (403, 429):
                blocked += 1
                if blocked >= 2:
                    save_manifest()
                    print(f"STOP: HTTP {err.code} twice in a row; start again later", flush=True)
                    return 3
                time.sleep(120)
        except Exception as err:  # network errors: record and go on
            manifest[url] = {**t, "status": f"error: {type(err).__name__}"}
        if i % 10 == 0 or i == len(todo):
            save_manifest()
            total = sum(r.get("bytes", 0) for r in manifest.values() if isinstance(r.get("bytes"), int))
            print(f"{i}/{len(todo)} fetched_ok={done} total_mb={total / 1e6:.1f}", flush=True)
        if args.limit and done >= args.limit:
            break
        time.sleep(random.uniform(args.min_delay, args.max_delay))
    save_manifest()
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
