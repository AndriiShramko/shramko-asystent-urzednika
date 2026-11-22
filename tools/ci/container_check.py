#!/usr/bin/env python3
"""Prove one built image of the converter on the CI runner (WP-F20, design 9.2 step 3).

    python tools/ci/container_check.py --image converter:core --fixtures out/fixtures [--report out/check.json]
                                       [--no-http]

1. Hardening probe. The container is started as the image defines it (its own USER, no --user override) with
   --network none, --read-only, --cap-drop ALL, no-new-privileges, a tmpfs /tmp, pid and memory limits. Inside,
   it reports uid, gid, effective capabilities, whether / and the app folder are writable, its network
   interfaces and what a connect to a never-routed address does. Asserted: uid and gid not 0, no capability,
   root and app folder not writable, /tmp writable, only the loopback interface, connect refused.
2. Conversion without network. Formats named by --ready (the readers that exist; the workflow has one line for
   them) must convert; every other fixture must be refused with a typed refusal (exit non-zero, no form on
   stdout, no traceback), and a form for it is a failure. Every ready fixture is converted TWICE through the command line inside such a
   container. Each output must pass tools/ci/formcheck.py (exactly title, tabs, flow; lint strict = schema plus
   the partner's rules) and both outputs must be byte-equal. Never compared with a stored copy. Two synthetic PDFs
   with different titles must give different titles.
3. HTTP path (unless --no-http). The same image started with a published loopback port and a token key as a
   read-only file: healthz 200; convert with a token 200 and a passing form; and the negative controls of the
   guard and the token (no token, expired, algorithm none, PNG bytes named .pdf, wrong extension), and for every
   non-ready fixture HTTP 422 with code UNREADABLE.
4. Final image: configured user not root, exactly one exposed port, no secret-like variable in the environment
   or in the history (the layer commands).
5. WP-F20i. The image environment pins one OCR thread, the C.UTF-8 locale and UTC, and the C library inside
   accepts that locale (asked, not assumed: glibc and musl differ). Every converted fixture also gives its
   sidecar, checked by tools/ci/sidecarcheck.py. One OCR raster and one PDF are converted twice with one
   processor and twice with two: all forms byte-equal, all sidecars byte-equal. Small hostile files made by
   tools/ci/hostile_inputs.py must each be refused within 10 s: exit 2 with problem JSON on the command line,
   a 4xx problem JSON over HTTP, and the service still healthy afterwards.
6. WP-F20i. The jury's first run (tools/ci/first_run.py): the image started with nothing but a published port
   is healthy within 30 s and two simultaneous first requests agree, on three fresh containers; AUTH_MODE=jwt
   with no key exits 3; --out into a folder that cannot be written exits 4; JOB_TIMEOUT_S=2 gives 504 TIMEOUT.

The token key is random per run, lives in a temporary folder and is never printed. Exit 1 when a check fails.
Writes a Markdown table to $GITHUB_STEP_SUMMARY when that variable is set.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import re
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
import hostile_inputs  # noqa: E402
import make_fixtures  # noqa: E402
from formcheck import problems_of_form, problems_of_pair  # noqa: E402
from sidecarcheck import differences_from_contract, problems_of_sidecar  # noqa: E402

READY_DEFAULT = frozenset({"pdf", "docx", "xlsx", "ods", "doc", "png", "jpg", "jpeg", "odt", "tiff", "bmp", "gif", "webp",
                          "rtf", "xls", "txt"})   # heic and heif need the decoder: the workflow adds them per target

HARDENED = ["--network", "none", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--tmpfs", "/tmp:rw,size=128m", "--pids-limit", "256", "--memory", "1g"]

REQUIRED_ENV = {"OMP_THREAD_LIMIT": "1", "OMP_NUM_THREADS": "1", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC"}
REFUSAL_SECONDS = 10.0   # a hostile file is answered within this, the start of its container included
EXIT_REFUSED = 2         # app/cli.py: 0 done, 2 refused (problem JSON on stderr), 3 configuration, 4 disk

PROBE = r"""
import json, os, socket, locale, time
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
try:
    loc = locale.setlocale(locale.LC_ALL, '')   # the C library is asked for the locale the environment names
    codeset = locale.nl_langinfo(locale.CODESET)
except (locale.Error, ValueError) as e:
    loc, codeset = 'ERROR ' + type(e).__name__, ''
print(json.dumps({'uid': os.getuid(), 'gid': os.getgid(), 'euid': os.geteuid(), 'status': st,
    'root_writable': writable('/probe'), 'app_writable': writable(os.getcwd() + '/probe'),
    'tmp_writable': writable('/tmp/probe'), 'ifaces': sorted(os.listdir('/sys/class/net')), 'connect': conn,
    'env': {k: os.environ.get(k) for k in ('OMP_THREAD_LIMIT', 'OMP_NUM_THREADS', 'LANG', 'LC_ALL', 'TZ')},
    'locale': loc, 'codeset': codeset, 'utc_offset': time.strftime('%z'),
    'epoch_hour': time.localtime(0).tm_hour}))
"""


def problems_of_image_env(cfg: dict) -> list[str]:
    """cfg is `docker image inspect` .Config: the image itself must pin the threads, the locale and the zone."""
    env = dict(e.partition("=")[::2] for e in cfg.get("Env") or [])
    return [f"{name} is {env.get(name)!r} in the image environment, expected {want!r}"
            for name, want in REQUIRED_ENV.items() if env.get(name) != want]


def problems_of_locale(p: dict) -> list[str]:
    """What the probe must show about the process: the variables arrive, the C library accepts the locale and
    answers UTF-8, the clock is UTC."""
    out = [f"{name} is {(p.get('env') or {}).get(name)!r} inside the container, expected {want!r}"
           for name, want in REQUIRED_ENV.items() if (p.get("env") or {}).get(name) != want]
    if str(p.get("locale", "")).startswith("ERROR") or not p.get("locale"):
        out.append(f"the C library refused the locale of the environment ({p.get('locale')})")
    if str(p.get("codeset", "")).upper().replace("-", "") != "UTF8":
        out.append(f"the locale's character set is {p.get('codeset')!r}, not UTF-8")
    if p.get("utc_offset") != "+0000" or p.get("epoch_hour") != 0:
        out.append(f"the local time is not UTC (offset {p.get('utc_offset')}, hour of the epoch {p.get('epoch_hour')})")
    return out


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


SECRET_WORDS = ("secret", "password", "passwd", "token", "apikey", "api_key", "private_key", "credential")
SECRET_VALUE_HINTS = ("-----BEGIN", "ghp_", "eyJ")
NAME_IN_HISTORY = re.compile(r"(?:\bARG\s+|\bENV\s+|--build-arg[ =]|\bexport\s+)([A-Za-z0-9_]+)", re.IGNORECASE)


def problems_of_image_config(cfg: dict, history: list[str]) -> list[str]:
    """cfg is `docker image inspect` .Config; history the CreatedBy lines. Names are reported, never a value."""
    out = []
    user = (cfg.get("User") or "").strip()
    if not user or user.split(":")[0] in ("0", "root"):
        out.append(f"image user is {user!r}")
    ports = sorted((cfg.get("ExposedPorts") or {}).keys())
    if len(ports) != 1:
        out.append(f"{len(ports)} exposed ports {ports}, expected exactly one")
    for entry in cfg.get("Env") or []:
        name, _, value = entry.partition("=")
        if any(w in name.lower() for w in SECRET_WORDS) or any(h in value for h in SECRET_VALUE_HINTS):
            out.append(f"secret-like variable in the environment: {name}")
    for line in history:
        for name in NAME_IN_HISTORY.findall(line):
            if any(w in name.lower() for w in SECRET_WORDS):
                out.append(f"secret-like name in the build history: {name}")
        if any(h in line for h in SECRET_VALUE_HINTS):
            out.append("secret-like value in the build history")
    return sorted(set(out))


def check_image_config(image: str, res: Results) -> None:
    cp = docker("image", "inspect", "-f", "{{json .Config}}", image)
    hp = docker("history", "--no-trunc", "--format", "{{.CreatedBy}}", image)
    if cp.returncode != 0 or hp.returncode != 0:
        res.add("final image configuration", [f"inspect exit {cp.returncode}, history exit {hp.returncode}"])
        return
    cfg = json.loads(cp.stdout.decode())
    history = hp.stdout.decode(errors="replace").splitlines()
    res.add("final image: non-root USER, one exposed port, no secret-like variable in environment or history",
            problems_of_image_config(cfg, history),
            f"USER {cfg.get('User')}, ports {sorted((cfg.get('ExposedPorts') or {}))}, "
            f"{len(cfg.get('Env') or [])} variables, {len(history)} layers")
    res.add("final image environment: one OCR thread, C.UTF-8, UTC", problems_of_image_env(cfg),
            " ".join(f"{k}={v}" for k, v in REQUIRED_ENV.items()))


def check_probe(image: str, res: Results) -> None:
    cp = docker("run", "--rm", *HARDENED, "--entrypoint", "python", image, "-c", PROBE)
    if cp.returncode != 0:
        res.add("hardening probe runs", [f"exit {cp.returncode}: {cp.stderr.decode(errors='replace')[-300:]}"])
        return
    probe = json.loads(cp.stdout.decode())
    res.add("hardened container: not root, no capabilities, read-only root, no network", problems_of_probe(probe),
            f"uid={probe['uid']} gid={probe['gid']} CapEff={probe['status'].get('CapEff')} "
            f"ifaces={probe['ifaces']} connect={probe['connect']}")
    res.add("inside the container: the C library accepts the locale (UTF-8), the clock is UTC, one OCR thread",
            problems_of_locale(probe),
            f"setlocale -> {probe.get('locale')}, codeset {probe.get('codeset')}, offset {probe.get('utc_offset')}")


def ext_of(path: Path) -> str:
    return path.suffix.lstrip(".").lower()


def problems_of_refusal(returncode: int, stdout: bytes, stderr: bytes) -> list[str]:
    """A typed refusal: non-zero exit, no form, a message, no traceback."""
    out = []
    if returncode == 0:
        out.append("exit 0: a form was produced for a format that has no reader")
    if stdout.strip():
        out.append(f"stdout not empty ({len(stdout)} bytes)")
    if b"Traceback" in stderr:
        out.append("traceback on stderr")
    if returncode != 0 and not stderr.strip():
        out.append("no message on stderr")
    return out


def check_conversions(image: str, fixtures: Path, res: Results, ready: frozenset[str] = READY_DEFAULT) -> None:
    files = sorted(p for p in fixtures.iterdir() if p.is_file())
    if not files:
        res.add("fixtures present", [f"no file in {fixtures}"])
        return
    mount = ["-v", f"{fixtures.resolve()}:/in:ro"]
    have = {ext_of(p) for p in files}
    res.add("a fixture exists for every format that must convert", [f"no fixture for .{e}" for e in sorted(ready - have)],
            ", ".join(sorted(ready)))
    for path in files:
        if ext_of(path) not in ready:
            cp = docker("run", "--rm", *HARDENED, *mount, image, "convert", f"/in/{path.name}", timeout=180)
            res.add(f"refuse {path.name}: typed refusal, no form (no reader yet)",
                    problems_of_refusal(cp.returncode, cp.stdout, cp.stderr),
                    f"exit {cp.returncode}, {len(cp.stdout)} bytes on stdout")
            continue
        t0 = time.monotonic()
        cp = docker("run", "--rm", *HARDENED, *mount, image, "convert", f"/in/{path.name}", timeout=180)
        secs = time.monotonic() - t0
        if cp.returncode != 0:
            res.add(f"convert {path.name} with --network none", [
                f"exit {cp.returncode}; stderr: {cp.stderr.decode(errors='replace')[-300:]}"])
            continue
        # the second conversion also asks for the sidecar: the same command line, plus --report
        second, form2, sidecar = convert_with_sidecar(image, mount, path.name)
        problems = conversion_problems(cp.stdout, cp.stderr, second.returncode, form2, sidecar)
        res.add(f"convert {path.name} with --network none", problems,
                f"{len(form2)} bytes, sha256 {hashlib.sha256(form2).hexdigest()[:12]}, {secs:.1f} s, "
                f"keys title/tabs/flow, lint strict clean, same bytes twice; sidecar {len(sidecar)} bytes valid "
                f"({differences_from_contract(sidecar)} rules of the full contract not met yet)")


SIDECAR_SCRIPT = 'python -m converter convert "/in/$0" --report /tmp/report && cat "/tmp/report/$1.meta.json"'


def convert_with_sidecar(image: str, mount: list[str], name: str, extra: tuple[str, ...] = ()
                         ) -> tuple[subprocess.CompletedProcess, bytes, bytes]:
    """One hardened conversion through the command line that also writes the sidecar (--report into the tmpfs)
    and prints it after the form. Returns the process, the form bytes and the sidecar bytes."""
    cp = docker("run", "--rm", *HARDENED, *extra, *mount, "--entrypoint", "sh", image, "-c", SIDECAR_SCRIPT,
                name, Path(name).stem, timeout=180)
    form, _, sidecar = cp.stdout.partition(b"\n")   # the form is one line of compact JSON
    return cp, form, sidecar


def conversion_problems(first_stdout: bytes, first_stderr: bytes, second_exit: int, second_form: bytes,
                        sidecar: bytes) -> list[str]:
    """What two conversions of one fixture must show: a passing form, the same bytes twice, a valid sidecar."""
    form = first_stdout.rstrip(b"\n")
    problems = problems_of_form(form)
    # WP-H4: the command line names its engine in one line on stderr; anything else there is a problem.
    noise = [ln for ln in first_stderr.decode(errors="replace").splitlines()
             if ln.strip() and not ln.startswith("ENGINE: ")]
    if noise:
        problems.append(f"stderr not empty: {' | '.join(noise)[-200:]}")
    if b"ENGINE: " not in first_stderr:
        problems.append("no ENGINE line on stderr")
    if second_exit != 0:
        return problems + [f"the conversion with --report exits {second_exit}"]
    return problems + problems_of_pair(form, second_form) + problems_of_sidecar(sidecar, second_form)


CPU_LIMITS = (("one processor", ("--cpus", "1", "--cpuset-cpus", "0")), ("two processors", ("--cpus", "2")))


def problems_of_runs(runs: list[tuple[str, int, bytes, bytes]]) -> list[str]:
    """runs: (label, exit code, form bytes, sidecar bytes) of the same input under different processor limits."""
    out = [f"{label}: exit {code}" for label, code, _, _ in runs if code != 0]
    if out:
        return out
    if len({form for _, _, form, _ in runs}) != 1:
        out.append("the form bytes differ between runs: " + ", ".join(
            f"{label} {hashlib.sha256(form).hexdigest()[:8]}" for label, _, form, _ in runs))
    if len({side for _, _, _, side in runs}) != 1:
        out.append("the sidecar bytes differ between runs: " + ", ".join(
            f"{label} {hashlib.sha256(side).hexdigest()[:8]}" for label, _, _, side in runs))
    if not runs or not runs[0][2] or not runs[0][3]:
        out.append("a run gave no form or no sidecar")
    return out


def check_determinism(image: str, fixtures: Path, res: Results, ready: frozenset[str] = READY_DEFAULT) -> None:
    """One OCR raster and one PDF, each converted twice with one processor (--cpus 1 on one core) and twice with
    two: eight conversions, the form and the sidecar must be the same bytes in all four of a file."""
    mount = ["-v", f"{fixtures.resolve()}:/in:ro"]
    for name in ("wniosek.png", "wniosek.pdf"):
        if not (fixtures / name).exists() or ext_of(Path(name)) not in ready:
            continue
        runs = []
        for label, flags in CPU_LIMITS:
            for n in (1, 2):
                cp, form, sidecar = convert_with_sidecar(image, mount, name, flags)
                if cp.returncode != 0:
                    print(cp.stderr.decode(errors="replace")[-300:])
                runs.append((f"{label} run {n}", cp.returncode, form, sidecar))
        res.add(f"deterministic {name}: twice with one processor, twice with two, form and sidecar byte-equal",
                problems_of_runs(runs) + (problems_of_form(runs[0][2]) if runs[0][1] == 0 else []),
                f"form sha256 {hashlib.sha256(runs[0][2]).hexdigest()[:12]}, "
                f"sidecar sha256 {hashlib.sha256(runs[0][3]).hexdigest()[:12]}, {len(runs)} conversions")


def problem_of(text: bytes) -> dict | None:
    """The problem JSON of a refusal (the last line of stderr, or an HTTP body); None when it is not one."""
    try:
        doc = json.loads(text.decode("utf-8").strip().splitlines()[-1])
    except (UnicodeDecodeError, ValueError, IndexError):
        return None
    ok = isinstance(doc, dict) and isinstance(doc.get("code"), str) and isinstance(doc.get("status"), int)
    return doc if ok else None


def problems_of_hostile_cli(returncode: int | None, stdout: bytes, stderr: bytes, seconds: float) -> list[str]:
    """A hostile file on the command line: refused with exit 2 and problem JSON, in time. None = it never ended."""
    if returncode is None:
        return [f"no answer in {seconds:.0f} s: the conversion hangs"]
    out = problems_of_refusal(returncode, stdout, stderr)
    if returncode not in (0, EXIT_REFUSED):
        out.append(f"exit {returncode}, not the refusal code {EXIT_REFUSED} (a crash, not a refusal)")
    doc = problem_of(stderr)
    if returncode != 0 and (doc is None or not 400 <= doc["status"] < 500):
        out.append("stderr does not end with a problem JSON of a 4xx refusal")
    if seconds > REFUSAL_SECONDS:
        out.append(f"answered in {seconds:.1f} s, over {REFUSAL_SECONDS:.0f} s")
    return out


def check_hostile_cli(image: str, res: Results) -> Path:
    """Every hostile file through the command line in a hardened container. Returns the folder (the HTTP half
    reuses the files; the caller removes it)."""
    tmp = Path(tempfile.mkdtemp(prefix="convhostile"))
    files = hostile_inputs.build(tmp)
    os.chmod(tmp, 0o755)
    for f in files.values():
        os.chmod(f, 0o644)
    for fname in sorted(files):
        cname = "convhostile-" + uuid.uuid4().hex[:8]
        t0 = time.monotonic()
        try:
            cp = docker("run", "--rm", "--name", cname, *HARDENED, "-v", f"{tmp}:/in:ro", image, "convert",
                        f"/in/{fname}", timeout=60)
            code, out, err = cp.returncode, cp.stdout, cp.stderr
        except subprocess.TimeoutExpired:
            docker("rm", "-f", cname)
            code, out, err = None, b"", b""
        secs = time.monotonic() - t0
        doc = problem_of(err) or {}
        res.add(f"hostile {fname} on the command line: refused in time, exit {EXIT_REFUSED}, problem JSON",
                problems_of_hostile_cli(code, out, err, secs), f"exit {code}, {doc.get('code')}, {secs:.1f} s")
    return tmp


def check_ocr_without_tmpfs(image: str, fixtures: Path, res: Results) -> None:
    """OCR of an image needs a writable /tmp. The documented run has --read-only and NO --tmpfs: the image itself
    must give /tmp (a declared volume). A raster form must convert to a passing form there."""
    png = fixtures / "wniosek.png"
    if not png.exists():
        return
    cp = docker("run", "--rm", "--network", "none", "--read-only", "--cap-drop", "ALL", "--security-opt",
                "no-new-privileges", "--pids-limit", "256", "--memory", "1g", "-v", f"{fixtures.resolve()}:/in:ro",
                image, "convert", "/in/wniosek.png", timeout=180)
    problems = ([f"exit {cp.returncode}; stderr: {cp.stderr.decode(errors='replace')[-300:]}"] if cp.returncode != 0
                else problems_of_form(cp.stdout.rstrip(b"\n")))
    res.add("PNG converts with --read-only and no --tmpfs (the image gives a writable /tmp for OCR)", problems,
            f"{len(cp.stdout)} bytes")


GATE_PROBE = r"""
import json, sys
from app import pipeline
from app.config import Settings
r = pipeline.run(open(sys.argv[1], "rb").read(), "x", Settings.from_env({"AUTH_MODE": "off"}))
print(json.dumps({c["id"]: c["status"] for c in r.sidecar["checks"]}))
"""


def problems_of_gate_checks(checks: dict) -> list[str]:
    """G1 (schema) and G2 (partner rules) must have RUN and passed inside the image: failed means the linter or the
    schema files are missing from it, not_applicable means the gate did not look."""
    return [f"{cid}: {checks.get(cid, 'absent')}, expected passed" for cid in ("G1", "G2") if checks.get(cid) != "passed"]


def check_gate_inside(image: str, fixtures: Path, res: Results, ready: frozenset[str] = READY_DEFAULT) -> None:
    pdfs = sorted(p for p in fixtures.iterdir() if p.suffix.lower() == ".pdf" and "pdf" in ready)
    if not pdfs:
        return
    cp = docker("run", "--rm", *HARDENED, "-v", f"{fixtures.resolve()}:/in:ro", "--entrypoint", "python", image,
                "-c", GATE_PROBE, f"/in/{pdfs[0].name}", timeout=180)
    if cp.returncode != 0:
        res.add("gate inside the image: G1 and G2 passed", [f"exit {cp.returncode}: {cp.stderr.decode(errors='replace')[-300:]}"])
        return
    checks = json.loads(cp.stdout.decode().strip().splitlines()[-1])
    res.add("gate inside the image: G1 schema and G2 partner rules passed (not failed, not not_applicable)",
            problems_of_gate_checks(checks),
            ", ".join(f"{k} {v}" for k, v in checks.items()))


OTHER_TITLE = "Wniosek o zmianę adresu zameldowania"


def title_of(raw: bytes | None) -> str | None:
    try:
        return json.loads(raw)["title"]
    except (ValueError, KeyError, TypeError):
        return None


def problems_of_titles(a: bytes | None, b: bytes | None) -> list[str]:
    ta, tb = title_of(a), title_of(b)
    if ta is None or tb is None:
        return ["a conversion gave no form with a title"]
    if ta == tb:
        return ["two different files gave the same title: the output does not depend on the input"]
    return []


def check_different_forms(image: str, res: Results, ready: frozenset[str] = READY_DEFAULT) -> None:
    if "pdf" not in ready:
        return
    tmp = Path(tempfile.mkdtemp(prefix="convtitles"))
    try:
        os.chmod(tmp, 0o755)
        (tmp / "a.pdf").write_bytes(make_fixtures.pdf())
        (tmp / "b.pdf").write_bytes(make_fixtures.pdf(OTHER_TITLE))
        for f in tmp.iterdir():
            os.chmod(f, 0o644)
        outs = [docker("run", "--rm", *HARDENED, "-v", f"{tmp}:/in:ro", image, "convert", f"/in/{n}.pdf",
                       timeout=180).stdout for n in ("a", "b")]
        res.add("two different files give two different forms (titles differ)", problems_of_titles(*outs),
                f"{title_of(outs[0])!r} vs {title_of(outs[1])!r}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


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
    status, body, _, _ = post_file_full(url, name, data, bearer)
    return status, body


def post_file_full(url: str, name: str, data: bytes, bearer: str | None, timeout: float = 60
                   ) -> tuple[int, bytes, str, float]:
    """Status, body, content type and seconds. Status 0 = no HTTP answer (time-out or a dropped connection)."""
    boundary = "b" + uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), r.headers.get("Content-Type", ""), time.monotonic() - t0
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), exc.headers.get("Content-Type", ""), time.monotonic() - t0
    except (urllib.error.URLError, OSError):
        return 0, b"", "", time.monotonic() - t0


def problems_of_hostile_http(status: int, body: bytes, content_type: str, seconds: float) -> list[str]:
    """A hostile file over HTTP: a 4xx problem JSON in time; never a form, a 5xx, plain text or silence."""
    if status == 0:
        return [f"no HTTP answer after {seconds:.1f} s (a hang or a dropped connection)"]
    out = []
    if not 400 <= status < 500:
        out.append(f"status {status}, not a 4xx refusal")
    if not content_type.startswith("application/problem+json"):
        out.append(f"content type {content_type!r}, not application/problem+json")
    doc = problem_of(body)
    if doc is None:
        out.append("the body is not a problem JSON with a code and a status")
    elif doc["status"] != status:
        out.append(f"the body says status {doc['status']}, the answer is {status}")
    if seconds > REFUSAL_SECONDS:
        out.append(f"answered in {seconds:.1f} s, over {REFUSAL_SECONDS:.0f} s")
    return out


def http_hostile_checks(base: str, bearer: str | None, folder: Path, res: Results) -> None:
    """Every hostile file posted to the running service, then the service must still be healthy."""
    for path in sorted(p for p in folder.iterdir() if p.is_file()):
        st, body, ctype, secs = post_file_full(base + "/v1/forms/convert", path.name, path.read_bytes(), bearer,
                                               timeout=30)
        res.add(f"hostile {path.name} over HTTP: 4xx problem JSON in time",
                problems_of_hostile_http(st, body, ctype, secs), f"{st} {_code(body)}, {secs:.1f} s")
    status = wait_healthy(base, seconds=10)
    res.add("GET /healthz after the hostile files", [] if status == 200 else [f"status {status}"], "200")


def http_sidecar_check(base: str, bearer: str | None, fixtures: Path, res: Results) -> None:
    """POST /v1/forms/report answers with the sidecar: the same check as on the command line (no digest pair:
    the endpoint does not add form_sha256)."""
    st, body, _, _ = post_file_full(base + "/v1/forms/report", "wniosek.pdf", (fixtures / "wniosek.pdf").read_bytes(),
                                    bearer)
    res.add("POST report with a token: 200 and a valid sidecar",
            [f"status {st} code {_code(body)}"] if st != 200 else problems_of_sidecar(body), f"{len(body)} bytes")


def _code(body: bytes) -> str:
    try:
        return str(json.loads(body).get("code"))
    except (ValueError, AttributeError):
        return "?"


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def check_http(image: str, fixtures: Path, res: Results, ready: frozenset[str] = READY_DEFAULT,
               hostile: Path | None = None) -> None:
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
        base = f"http://127.0.0.1:{port}"
        failed_before = res.failed
        if http_checks(base, key, fixtures, res, ready):
            http_sidecar_check(base, token(key), fixtures, res)
            import first_run

            st, body = first_run.get(base + "/status")
            res.add("GET /status with a key configured: 200 without a token, auth jwt",
                    first_run.problems_of_status(st, body, "jwt"), f"{len(body)} bytes")
            if hostile is not None:
                http_hostile_checks(base, token(key), hostile, res)
        if res.failed > failed_before:
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


def http_checks(base: str, key: bytes, fixtures: Path, res: Results,
                ready: frozenset[str] = READY_DEFAULT) -> bool:
    """The HTTP path against a running service (a container in CI, a native process in the unit test).
    Returns False when the service never became healthy."""
    status = wait_healthy(base)
    res.add("GET /healthz", [] if status == 200 else [f"status {status}"], "200")
    if status != 200:
        return False
    url = base + "/v1/forms/convert"
    pdf = (fixtures / "wniosek.pdf").read_bytes()
    junk = bytes(3) + b"junk"   # neither a known format nor text (WP-F20f: a PNG named .pdf is now read as a PNG)
    good = token(key)
    st, body = post_file(url, "wniosek.pdf", pdf, good)
    res.add("POST convert with a token: 200 and a passing form",
            ([f"status {st} code {_code(body)}"] if st != 200 else problems_of_form(body)), f"{len(body)} bytes")
    cases = [
        ("no token", "wniosek.pdf", pdf, None, 401, "TOKEN_MISSING"),
        ("expired token", "wniosek.pdf", pdf, token(key, exp=int(time.time()) - 3600), 401, "TOKEN_EXPIRED"),
        ("token with algorithm none", "wniosek.pdf", pdf, token(None, alg="none"), 401, "TOKEN_INVALID"),
        ("token signed with another key", "wniosek.pdf", pdf, token(b"x" * 64), 401, "TOKEN_INVALID"),
        ("bytes of no known format named .pdf", "wniosek.pdf", junk, good, 415, "TYPE_MISMATCH"),
        ("extension .exe", "wniosek.exe", b"Wniosek\n", good, 415, "EXTENSION"),
    ]
    for label, fname, data, bearer, want, code in cases:
        st, body = post_file(url, fname, data, bearer)
        got = _code(body)
        res.add(f"negative control: {label} -> {want} {code}",
                [] if (st, got) == (want, code) else [f"got {st} {got}"], f"{st} {got}")
    for path in sorted(p for p in fixtures.iterdir() if p.is_file() and ext_of(p) not in ready):
        st, body = post_file(url, path.name, path.read_bytes(), good)
        got = _code(body)
        res.add(f"refusal over HTTP: {path.name} -> 422 UNREADABLE (no reader yet)",
                [] if (st, got) == (422, "UNREADABLE") else [f"got {st} {got}"], f"{st} {got}")
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
    ap.add_argument("--ready", default=",".join(sorted(READY_DEFAULT)),
                    help="comma list of extensions that must convert; every other fixture must be refused")
    ap.add_argument("--no-http", action="store_true")
    args = ap.parse_args()
    res = Results()
    check_image_config(args.image, res)
    check_probe(args.image, res)
    ready = frozenset(e.strip().lower() for e in args.ready.split(",") if e.strip())
    check_conversions(args.image, args.fixtures, res, ready)
    check_ocr_without_tmpfs(args.image, args.fixtures, res)
    check_different_forms(args.image, res, ready)
    check_gate_inside(args.image, args.fixtures, res, ready)
    check_determinism(args.image, args.fixtures, res, ready)
    hostile = check_hostile_cli(args.image, res)
    try:
        if not args.no_http:
            check_http(args.image, args.fixtures, res, ready, hostile)
    finally:
        shutil.rmtree(hostile, ignore_errors=True)
    if not args.no_http:
        import first_run   # imports this module by name: see the last lines of the file

        first_run.run_all(args.image, args.fixtures, res)
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
    import container_check   # one copy of this module for first_run.py too, not `__main__` plus a second import

    sys.exit(container_check.main())
