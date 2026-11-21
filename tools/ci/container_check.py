#!/usr/bin/env python3
"""Prove one built image of the converter on the CI runner (WP-F20, design 9.2 step 3).

    python tools/ci/container_check.py --image converter:core --fixtures out/fixtures [--report out/check.json]
                                       [--no-http]

1. Hardening probe. The container is started as the image defines it (its own USER, no --user override) with
   --network none, --read-only, --cap-drop ALL, no-new-privileges, a tmpfs /tmp, pid and memory limits. Inside,
   it reports uid, gid, effective capabilities, whether / and the app folder are writable, its network
   interfaces and what a connect to a never-routed address does. Asserted: uid and gid not 0, no capability,
   root and app folder not writable, /tmp writable, only the loopback interface, connect refused.
2. Conversion without network. Every fixture is converted TWICE through the command line inside such a
   container. Each output must pass tools/ci/formcheck.py (exactly title, tabs, flow; lint strict = schema plus
   the partner's rules) and both outputs must be byte-equal. Never compared with a stored copy.
3. HTTP path (unless --no-http). The same image started with a published loopback port and a token key as a
   read-only file: healthz 200; convert with a token 200 and a passing form; and the negative controls of the
   guard and the token (no token, expired, algorithm none, PNG bytes named .pdf, wrong extension).

The token key is random per run, lives in a temporary folder and is never printed. Exit 1 when a check fails.
Writes a Markdown table to $GITHUB_STEP_SUMMARY when that variable is set.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from formcheck import problems_of_form, problems_of_pair  # noqa: E402

HARDENED = ["--network", "none", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--tmpfs", "/tmp:rw,size=128m", "--pids-limit", "256", "--memory", "1g"]

PROBE = r"""
import json, os, socket
def writable(p):
    try:
        with open(p, 'w') as f: f.write('x')
        os.remove(p); return True
    except OSError: return False
st = {}
for line in open('/proc/self/status'):
    k, _, v = line.partition(':')
    if k in ('CapEff', 'CapPrm', 'CapBnd', 'NoNewPrivs'): st[k] = v.strip()
try:
    socket.create_connection(('192.0.2.1', 80), timeout=3).close(); conn = 'connected'
except OSError as e:
    conn = type(e).__name__
print(json.dumps({'uid': os.getuid(), 'gid': os.getgid(), 'euid': os.geteuid(), 'status': st,
    'root_writable': writable('/probe'), 'app_writable': writable(os.getcwd() + '/probe'),
    'tmp_writable': writable('/tmp/probe'), 'ifaces': sorted(os.listdir('/sys/class/net')), 'connect': conn}))
"""


def problems_of_probe(p: dict) -> list[str]:
    """What the hardening probe must show; empty list when all holds."""
    out = []
    if p.get("uid") in (0, None) or p.get("euid") in (0, None):
        out.append(f"process runs as uid {p.get('uid')} / euid {p.get('euid')}")
    if p.get("gid") in (0, None):
        out.append(f"process runs with gid {p.get('gid')}")
    st = p.get("status", {})
    for key in ("CapEff", "CapPrm"):
        if int(st.get(key, "1"), 16) != 0:
            out.append(f"{key} is {st.get(key)}, not zero")
    if st.get("NoNewPrivs") != "1":
        out.append("no_new_privs is not set")
    if p.get("root_writable"):
        out.append("the root file system is writable")
    if p.get("app_writable"):
        out.append("the application folder is writable")
    if not p.get("tmp_writable"):
        out.append("/tmp is not writable (the service needs it)")
    if p.get("ifaces") != ["lo"]:
        out.append(f"network interfaces {p.get('ifaces')} are not only the loopback")
    if p.get("connect") == "connected":
        out.append("a connect to a never-routed address succeeded")
    return out


class Results:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, check: str, problems: list[str], detail: str = "") -> None:
        ok = not problems
        self.rows.append({"check": check, "ok": ok, "detail": "; ".join(problems) if problems else detail})
        print(f"{'PASS' if ok else 'FAIL'}  {check}" + (f"  ({self.rows[-1]['detail']})" if self.rows[-1]["detail"] else ""))

    @property
    def failed(self) -> int:
        return sum(1 for r in self.rows if not r["ok"])


def docker(*args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], capture_output=True, timeout=timeout)


def check_image_config(image: str, res: Results) -> None:
    cp = docker("image", "inspect", "-f", "{{.Config.User}}", image)
    user = cp.stdout.decode().strip()
    bad = [] if cp.returncode == 0 and user and user.split(":")[0] not in ("0", "root") else [f"image user is {user!r}"]
    res.add("image declares a non-root USER", bad, f"USER {user}")


def check_probe(image: str, res: Results) -> None:
    cp = docker("run", "--rm", *HARDENED, "--entrypoint", "python", image, "-c", PROBE)
    if cp.returncode != 0:
        res.add("hardening probe runs", [f"exit {cp.returncode}: {cp.stderr.decode(errors='replace')[-300:]}"])
        return
    probe = json.loads(cp.stdout.decode())
    res.add("hardened container: not root, no capabilities, read-only root, no network", problems_of_probe(probe),
            f"uid={probe['uid']} gid={probe['gid']} CapEff={probe['status'].get('CapEff')} "
            f"ifaces={probe['ifaces']} connect={probe['connect']}")


def check_conversions(image: str, fixtures: Path, res: Results) -> None:
    files = sorted(p for p in fixtures.iterdir() if p.is_file())
    if not files:
        res.add("fixtures present", [f"no file in {fixtures}"])
        return
    mount = ["-v", f"{fixtures.resolve()}:/in:ro"]
    for path in files:
        outs = []
        for _ in range(2):
            t0 = time.monotonic()
            cp = docker("run", "--rm", *HARDENED, *mount, image, "convert", f"/in/{path.name}", timeout=180)
            outs.append((cp, time.monotonic() - t0))
        cp, secs = outs[0]
        if cp.returncode != 0:
            res.add(f"convert {path.name} with --network none", [
                f"exit {cp.returncode}; stderr: {cp.stderr.decode(errors='replace')[-300:]}"])
            continue
        problems = problems_of_form(cp.stdout.rstrip(b"\n"))
        problems += problems_of_pair(cp.stdout, outs[1][0].stdout)
        if cp.stderr.strip():
            problems.append(f"stderr not empty: {cp.stderr.decode(errors='replace')[-200:]}")
        res.add(f"convert {path.name} with --network none", problems,
                f"{len(cp.stdout)} bytes, sha256 {hashlib.sha256(cp.stdout).hexdigest()[:12]}, {secs:.1f} s, "
                "keys title/tabs/flow, lint strict clean, same bytes twice")


# ---- HTTP ------------------------------------------------------------------------------------------------------
def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def token(key: bytes | None, alg: str = "HS256", **claims) -> str:
    body = {"sub": "ci", "scope": "convert", "exp": int(time.time()) + 600}
    body.update(claims)
    signing = _b64(json.dumps({"alg": alg, "typ": "JWT"}).encode()) + "." + _b64(json.dumps(body).encode())
    sig = hmac.new(key, signing.encode(), hashlib.sha256).digest() if key is not None else b""
    return signing + "." + _b64(sig)


def post_file(url: str, name: str, data: bytes, bearer: str | None) -> tuple[int, bytes]:
    boundary = "b" + uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _code(body: bytes) -> str:
    try:
        return str(json.loads(body).get("code"))
    except (ValueError, AttributeError):
        return "?"


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def check_http(image: str, fixtures: Path, res: Results) -> None:
    key = secrets.token_urlsafe(48).encode()
    secdir = Path(tempfile.mkdtemp(prefix="convkey"))
    name = "convcheck-" + uuid.uuid4().hex[:8]
    try:
        (secdir / "jwt_secret").write_bytes(key)
        os.chmod(secdir, 0o755)
        os.chmod(secdir / "jwt_secret", 0o644)
        port = free_port()
        cp = docker("run", "-d", "--name", name, "--read-only", "--cap-drop", "ALL", "--security-opt",
                    "no-new-privileges", "--tmpfs", "/tmp:rw,size=128m", "-p", f"127.0.0.1:{port}:8080",
                    "-e", "JWT_ALG=HS256", "-e", "JWT_SECRET_FILE=/run/secrets/jwt_secret",
                    "-v", f"{secdir}:/run/secrets:ro", image)
        if cp.returncode != 0:
            res.add("HTTP container starts", [cp.stderr.decode(errors="replace")[-300:]])
            return
        if not http_checks(f"http://127.0.0.1:{port}", key, fixtures, res):
            logs = docker("logs", "--tail", "40", name)
            print((logs.stdout + logs.stderr).decode(errors="replace")[-3000:])
    finally:
        docker("rm", "-f", name)
        shutil.rmtree(secdir, ignore_errors=True)


def wait_healthy(base: str, seconds: float = 45) -> int:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(base + "/healthz", timeout=3) as r:
                return r.status
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.5)
    return 0


def http_checks(base: str, key: bytes, fixtures: Path, res: Results) -> bool:
    """The HTTP path against a running service (a container in CI, a native process in the unit test).
    Returns False when the service never became healthy."""
    status = wait_healthy(base)
    res.add("GET /healthz", [] if status == 200 else [f"status {status}"], "200")
    if status != 200:
        return False
    url = base + "/v1/forms/convert"
    pdf = (fixtures / "wniosek.pdf").read_bytes()
    png = (fixtures / "wniosek.png").read_bytes()
    good = token(key)
    st, body = post_file(url, "wniosek.pdf", pdf, good)
    res.add("POST convert with a token: 200 and a passing form",
            ([f"status {st} code {_code(body)}"] if st != 200 else problems_of_form(body)), f"{len(body)} bytes")
    cases = [
        ("no token", "wniosek.pdf", pdf, None, 401, "TOKEN_MISSING"),
        ("expired token", "wniosek.pdf", pdf, token(key, exp=int(time.time()) - 3600), 401, "TOKEN_EXPIRED"),
        ("token with algorithm none", "wniosek.pdf", pdf, token(None, alg="none"), 401, "TOKEN_INVALID"),
        ("token signed with another key", "wniosek.pdf", pdf, token(b"x" * 64), 401, "TOKEN_INVALID"),
        ("PNG bytes named .pdf", "wniosek.pdf", png, good, 415, "TYPE_MISMATCH"),
        ("extension .txt", "wniosek.txt", b"Wniosek\n", good, 415, "EXTENSION"),
    ]
    for label, fname, data, bearer, want, code in cases:
        st, body = post_file(url, fname, data, bearer)
        got = _code(body)
        res.add(f"negative control: {label} -> {want} {code}",
                [] if (st, got) == (want, code) else [f"got {st} {got}"], f"{st} {got}")
    return True


def summary_markdown(image: str, res: Results) -> str:
    lines = [f"### Container check of `{image}`", "", "| Result | Check | Detail |", "|---|---|---|"]
    for r in res.rows:
        lines.append(f"| {'PASS' if r['ok'] else '**FAIL**'} | {r['check']} | {r['detail'].replace('|', '/')} |")
    lines.append(f"\n{len(res.rows) - res.failed} passed, {res.failed} failed.\n")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--image", required=True)
    ap.add_argument("--fixtures", type=Path, required=True)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--no-http", action="store_true")
    args = ap.parse_args()
    res = Results()
    check_image_config(args.image, res)
    check_probe(args.image, res)
    check_conversions(args.image, args.fixtures, res)
    if not args.no_http:
        check_http(args.image, args.fixtures, res)
    md = summary_markdown(args.image, res)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(md + "\n")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({"image": args.image, "rows": res.rows}, indent=2), encoding="utf-8")
    print(f"{len(res.rows) - res.failed} passed, {res.failed} failed")
    return 1 if res.failed else 0


if __name__ == "__main__":
    sys.exit(main())
