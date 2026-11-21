#!/usr/bin/env python3
"""Build-time client for the Eden AI gateway (the partner's LLM credits for the forms task).

NOT part of the product: the converter never calls out of its container (task card, C-TECH-NOEXT).
This tool is for research, silver labels, lexicon mining and reviews while we build.

Key handling (the partner asked: no key in repositories, front-end code or agent prompts):
  * the key is read from the environment variable EDENAI_API_KEY, or on Windows from the
    user-level variable of the same name; it is never printed, logged or written to a file;
  * agents call this tool; they never see or pass the key.

Budget: every call is written to .eden/ledger.jsonl (git-ignored) and the tool refuses to call
when the ledger total reaches EDEN_BUDGET_USD (default 60; the partner's key holds 100 EUR).

Examples:
  python tools/eden/eden.py models --grep gemini
  python tools/eden/eden.py chat --model anthropic/claude-haiku-5-5 --prompt "Powiedz: działa" --purpose smoke
  python tools/eden/eden.py chat --model google/gemini-4-carbon --prompt-file q.md --out a.md --purpose research
  python tools/eden/eden.py budget
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.edenai.run/v3"
ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / ".eden"
LEDGER = STATE / "ledger.jsonl"
MODELS_CACHE = STATE / "models.json"


def _key() -> str:
    key = os.environ.get("EDENAI_API_KEY", "").strip()
    if not key and sys.platform == "win32":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                key = str(winreg.QueryValueEx(k, "EDENAI_API_KEY")[0]).strip()
        except OSError:
            key = ""
    if not key:
        sys.exit("EDENAI_API_KEY is not set (environment or Windows user variable). Ask the owner; never paste a key into a file or a prompt.")
    return key


def _spent() -> float:
    total = 0.0
    if LEDGER.exists():
        for line in LEDGER.read_text(encoding="utf-8").splitlines():
            try:
                total += float(json.loads(line).get("usd", 0) or 0)
            except (ValueError, TypeError):
                continue
    return total


def _cap() -> float:
    try:
        return float(os.environ.get("EDEN_BUDGET_USD", "60"))
    except ValueError:
        return 60.0


def _models(refresh: bool = False) -> list[dict]:
    STATE.mkdir(exist_ok=True)
    if refresh or not MODELS_CACHE.exists() or time.time() - MODELS_CACHE.stat().st_mtime > 6 * 3600:
        with urllib.request.urlopen(API + "/models", timeout=120) as r:
            MODELS_CACHE.write_bytes(r.read())
    data = json.loads(MODELS_CACHE.read_text(encoding="utf-8"))
    return data.get("data", data) if isinstance(data, dict) else data


def _price(model: str) -> tuple[float, float]:
    for m in _models():
        if m.get("id") == model:
            p = m.get("pricing") or {}
            return float(p.get("input_cost_per_token") or 0), float(p.get("output_cost_per_token") or 0)
    return 0.0, 0.0


def cmd_models(a: argparse.Namespace) -> None:
    rows = []
    for m in _models(refresh=a.refresh):
        if a.grep and a.grep.lower() not in m["id"].lower():
            continue
        p = m.get("pricing") or {}
        c = m.get("capabilities") or {}
        i, o = p.get("input_cost_per_token"), p.get("output_cost_per_token")
        rows.append(
            "%-52s in $%-7s out $%-7s per MTok | %s | web=%s | zdr=%s | %s"
            % (
                m["id"][:52],
                ("%.2f" % (i * 1e6)) if isinstance(i, (int, float)) else "-",
                ("%.2f" % (o * 1e6)) if isinstance(o, (int, float)) else "-",
                "+".join(c.get("input_modalities") or []),
                c.get("supports_web_search"),
                m.get("zero_data_retention"),
                ",".join(r.get("code", "") for r in (m.get("regions") or [])),
            )
        )
    print("\n".join(rows[: a.limit]))
    print("(%d shown of %d matching)" % (min(len(rows), a.limit), len(rows)))


def cmd_budget(_: argparse.Namespace) -> None:
    by: dict[str, float] = {}
    n = 0
    if LEDGER.exists():
        for line in LEDGER.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            n += 1
            by[e.get("purpose", "?")] = by.get(e.get("purpose", "?"), 0.0) + float(e.get("usd", 0) or 0)
    print("calls: %d | spent: $%.3f | cap: $%.2f" % (n, _spent(), _cap()))
    for k, v in sorted(by.items(), key=lambda kv: -kv[1]):
        print("  %-24s $%.3f" % (k, v))


def _content(prompt: str, images: list[str]) -> object:
    if not images:
        return prompt
    parts: list[dict] = [{"type": "text", "text": prompt}]
    for path in images:
        mime = mimetypes.guess_type(path)[0] or "image/png"
        b64 = base64.b64encode(Path(path).read_bytes()).decode("ascii")
        parts.append({"type": "image_url", "image_url": {"url": "data:%s;base64,%s" % (mime, b64)}})
    return parts


def request(body: dict, purpose: str, timeout: int = 900) -> dict:
    """One chat completion. Checks the cap, writes the ledger, returns
    {"text", "data", "in", "out", "usd", "seconds", "finish", "spent"}. Raises RuntimeError on failure."""
    spent, cap = _spent(), _cap()
    if spent >= cap:
        raise RuntimeError("Budget cap reached: spent $%.2f of $%.2f. Raise EDEN_BUDGET_USD only on the owner's word." % (spent, cap))
    req = urllib.request.Request(
        API + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": "Bearer " + _key(), "Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError("HTTP %s from the gateway: %s" % (e.code, e.read().decode("utf-8", "replace")[:600])) from None
    except Exception as e:  # network, timeout
        raise RuntimeError("Call failed: %s" % type(e).__name__) from None
    seconds = time.time() - t0
    usage = data.get("usage") or {}
    tin = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    tout = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    usd = None
    for candidate in (data.get("cost"), usage.get("cost")):
        try:
            usd = float(candidate)
            break
        except (TypeError, ValueError):
            continue
    if usd is None:
        pin, pout = _price(str(body.get("model")))
        usd = tin * pin + tout * pout
    STATE.mkdir(exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"t": int(time.time()), "model": body.get("model"), "in": tin, "out": tout, "usd": round(float(usd), 6), "s": round(seconds, 1), "purpose": purpose}) + "\n")
    choice = (data.get("choices") or [{}])[0]
    text = (choice.get("message") or {}).get("content") or ""
    if isinstance(text, list):
        text = "".join(part.get("text", "") for part in text if isinstance(part, dict))
    return {"text": text, "data": data, "in": tin, "out": tout, "usd": float(usd), "seconds": seconds, "finish": choice.get("finish_reason"), "spent": spent + float(usd)}


def cmd_chat(a: argparse.Namespace) -> None:
    prompt = a.prompt if a.prompt is not None else Path(a.prompt_file).read_text(encoding="utf-8")
    messages = []
    if a.system:
        messages.append({"role": "system", "content": a.system})
    messages.append({"role": "user", "content": _content(prompt, a.image or [])})
    body: dict = {"model": a.model, "messages": messages}
    if a.max_tokens:
        body["max_tokens"] = a.max_tokens
    if a.temperature is not None:
        body["temperature"] = a.temperature
    if a.json:
        body["response_format"] = {"type": "json_object"}
    if a.extra:
        body.update(json.loads(a.extra))
    try:
        r = request(body, a.purpose, a.timeout)
    except RuntimeError as e:
        sys.exit(str(e))
    if a.raw:
        Path(a.raw).write_text(json.dumps(r["data"], ensure_ascii=False, indent=1), encoding="utf-8")
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(r["text"], encoding="utf-8")
        print("ok: %s | in %d out %d tokens | $%.4f | %.0fs | finish=%s | total spent $%.3f" % (a.out, r["in"], r["out"], r["usd"], r["seconds"], r["finish"], r["spent"]))
    else:
        print(r["text"])
        print("\n-- in %d out %d tokens | $%.4f | %.0fs | total spent $%.3f" % (r["in"], r["out"], r["usd"], r["seconds"], r["spent"]), file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("models", help="list the gateway's catalogue (no key needed)")
    m.add_argument("--grep", default="")
    m.add_argument("--limit", type=int, default=60)
    m.add_argument("--refresh", action="store_true")
    m.set_defaults(fn=cmd_models)
    b = sub.add_parser("budget", help="show what the ledger says was spent")
    b.set_defaults(fn=cmd_budget)
    c = sub.add_parser("chat", help="one chat completion")
    c.add_argument("--model", required=True)
    g = c.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt")
    g.add_argument("--prompt-file")
    c.add_argument("--system")
    c.add_argument("--image", action="append", help="path of an image to attach (repeatable)")
    c.add_argument("--max-tokens", type=int)
    c.add_argument("--temperature", type=float)
    c.add_argument("--json", action="store_true", help="ask for a JSON object")
    c.add_argument("--extra", help="JSON object merged into the request body (provider options)")
    c.add_argument("--out", help="write the answer to this file")
    c.add_argument("--raw", help="write the whole response JSON to this file")
    c.add_argument("--timeout", type=int, default=900)
    c.add_argument("--purpose", default="unspecified", help="label for the ledger: research, silver-labels, lexicon, review, smoke")
    c.set_defaults(fn=cmd_chat)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
