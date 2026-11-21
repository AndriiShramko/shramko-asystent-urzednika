"""The jury's first run, as a check of one built image (WP-F20i stage 2). Called by tools/ci/container_check.py.

What a person does first with an image they did not build, and what must then happen:

1. `docker run -p 127.0.0.1:PORT:8080 IMAGE` and nothing else: no variable, no key, no flag. /healthz answers 200
   within 30 s; the log says the API is open; two simultaneous FIRST conversions both answer 200 with the same
   bytes and a passing form; /status answers 200 and says `auth: off`. Repeated on three fresh containers, each
   with a file of another reader (PDF, DOCX, a raster for OCR): a cold-start race shows on the first request only.
2. `AUTH_MODE=jwt` with no key: the container exits 3 with the reason, no traceback (fail closed stays).
3. `convert --out` into a folder the container's user may not write (root-owned, and a read-only mount): exit 4,
   one line, no traceback.
4. `JOB_TIMEOUT_S=2` and a scanned PDF that needs far longer (many raster pages, made here): 504 problem JSON
   `TIMEOUT`, then /healthz answers and an ordinary file still converts.

The pure halves (`problems_of_*`) are tested natively in tools/ci/tests/test_first_run.py.
"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import container_check as cc
import make_fixtures
from formcheck import problems_of_form

HEALTHY_WITHIN = 30.0
EXIT_CONFIG = 3      # app/cli.py: the configuration is inconsistent
EXIT_DISK = 4        # app/cli.py: the file cannot be read from disk or the output cannot be written
STATUS_KEYS = {"service", "version", "engine", "auth", "formats", "limits"}
FIRST_FILES = ("wniosek.pdf", "wniosek.docx", "wniosek.png")   # one fresh container each
OPEN_API_LOG = "without a token"   # app/main.py warns: "... the API accepts requests WITHOUT a token."
SLOW_PAGES = 40      # under MAX_PAGES (60); each page is one full-page picture, so each page is one OCR run
JOB_TIMEOUT_S = 2


def many_page_raster_pdf(pages: int = SLOW_PAGES) -> bytes:
    """A PDF with no text layer: the raster page of the fixtures drawn on every page. Synthetic, small (the picture
    is stored once), and far too long to read in two seconds because every page goes through OCR."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    picture = ImageReader(io.BytesIO(make_fixtures.png()))
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, invariant=1)
    for _ in range(pages):
        c.drawImage(picture, 0, 0, width=A4[0], height=A4[1])
        c.showPage()
    c.save()
    return buf.getvalue()


def get(url: str, timeout: float = 5) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except (urllib.error.URLError, OSError):
        return 0, b""


def seconds_until_healthy(base: str, limit: float = HEALTHY_WITHIN) -> float | None:
    """Seconds until /healthz first answers 200; None when it does not within the limit."""
    t0 = time.monotonic()
    while time.monotonic() - t0 < limit:
        if get(base + "/healthz", timeout=2)[0] == 200:
            return time.monotonic() - t0
        time.sleep(0.25)
    return None


def simultaneous_posts(url: str, name: str, data: bytes, n: int = 2) -> list[tuple[int, bytes]]:
    """n requests released together by a barrier, no token."""
    barrier = threading.Barrier(n)
    out: list[tuple[int, bytes]] = [(0, b"")] * n

    def work(i: int) -> None:
        barrier.wait(timeout=10)
        out[i] = cc.post_file_full(url, name, data, None, timeout=150)[:2]

    threads = [threading.Thread(target=work, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=170)
    return out


def problems_of_first_pair(answers: list[tuple[int, bytes]]) -> list[str]:
    """Two simultaneous first requests: each 200, the same bytes, a passing form."""
    out = [f"request {i + 1}: status {st} code {cc._code(body)}" for i, (st, body) in enumerate(answers) if st != 200]
    if out or len(answers) < 2:
        return out or ["fewer than two answers"]
    if len({body for _, body in answers}) != 1:
        out.append("the simultaneous first requests answered with different bytes")
    return out + problems_of_form(answers[0][1])


def problems_of_status(status: int, body: bytes, auth: str) -> list[str]:
    """GET /status: 200, exactly the six keys, the expected `auth`, a list of formats with pdf, the limits."""
    if status != 200:
        return [f"status {status}"]
    try:
        doc = json.loads(body)
    except ValueError:
        return ["the body is not JSON"]
    if not isinstance(doc, dict) or set(doc) != STATUS_KEYS:
        return [f"keys {sorted(doc) if isinstance(doc, dict) else type(doc).__name__} are not {sorted(STATUS_KEYS)}"]
    out = []
    if doc["auth"] != auth:
        out.append(f"auth is {doc['auth']!r}, expected {auth!r}")
    if not isinstance(doc["formats"], list) or "pdf" not in doc["formats"]:
        out.append("formats is not a list with pdf")
    limits = doc["limits"]
    if not isinstance(limits, dict) or not all(isinstance(limits.get(k), int) and limits[k] > 0
                                               for k in ("job_timeout_s", "concurrency", "max_pages", "max_upload_bytes")):
        out.append("limits does not carry the four positive numbers")
    return out


def problems_of_config_exit(returncode: int | None, stdout: bytes, stderr: bytes) -> list[str]:
    """`AUTH_MODE=jwt` and no key: the service must not start, and must say why."""
    if returncode is None:
        return ["the container did not exit: the service started with AUTH_MODE=jwt and no key"]
    out = []
    if returncode != EXIT_CONFIG:
        out.append(f"exit {returncode}, not {EXIT_CONFIG}")
    if b"Traceback" in stderr or b"Traceback" in stdout:
        out.append("traceback in the output")
    if b"Configuration refused" not in stderr:
        out.append("stderr does not say that the configuration was refused")
    return out


def problems_of_unwritable(returncode: int, stdout: bytes, stderr: bytes) -> list[str]:
    """`convert --out` where the user may not write: exit 4, one line, no traceback, no form on stdout."""
    out = []
    if returncode != EXIT_DISK:
        out.append(f"exit {returncode}, not {EXIT_DISK}")
    if b"Traceback" in stderr:
        out.append("traceback on stderr")
    lines = [ln for ln in stderr.decode(errors="replace").splitlines() if ln.strip()]
    if len(lines) != 1 or not lines[0].startswith("Cannot write"):
        out.append(f"stderr is {len(lines)} lines, expected the one line 'Cannot write ...'")
    if stdout.strip():
        out.append(f"stdout not empty ({len(stdout)} bytes)")
    return out


def problems_of_timeout(status: int, body: bytes, content_type: str, seconds: float, limit: int = JOB_TIMEOUT_S) -> list[str]:
    """The job limit in the real image: 504, problem JSON with code TIMEOUT, soon after the limit."""
    if status == 0:
        return [f"no HTTP answer after {seconds:.1f} s"]
    out = []
    doc = cc.problem_of(body)
    if status != 504 or doc is None or doc.get("code") != "TIMEOUT":
        out.append(f"got {status} {cc._code(body)}, expected 504 TIMEOUT")
    if not content_type.startswith("application/problem+json"):
        out.append(f"content type {content_type!r}, not application/problem+json")
    if status == 504 and not limit - 0.5 <= seconds <= limit + 15:
        out.append(f"answered after {seconds:.1f} s with a limit of {limit} s")
    return out


# ---- the container halves ------------------------------------------------------------------------------------------
def _logs(name: str) -> str:
    cp = cc.docker("logs", "--tail", "60", name)
    return (cp.stdout + cp.stderr).decode(errors="replace")


def check_first_run(image: str, fixtures: Path, res: cc.Results, files: tuple[str, ...] = FIRST_FILES) -> None:
    for n, fname in enumerate(files, 1):
        path = fixtures / fname
        if not path.exists():
            res.add(f"first run {n}: fixture {fname}", ["the fixture is missing"])
            continue
        name = "convfirst-" + uuid.uuid4().hex[:8]
        port = cc.free_port()
        base = f"http://127.0.0.1:{port}"
        failed_before = res.failed
        try:
            cp = cc.docker("run", "-d", "--name", name, "-p", f"127.0.0.1:{port}:8080", image)   # nothing else
            if cp.returncode != 0:
                res.add(f"first run {n}: the container starts", [cp.stderr.decode(errors="replace")[-300:]])
                continue
            secs = seconds_until_healthy(base)
            res.add(f"first run {n}: no variable, no key, no flag but the port; /healthz 200 within {HEALTHY_WITHIN:.0f} s",
                    [] if secs is not None else ["no 200 in time"], f"{secs:.1f} s" if secs is not None else "")
            if secs is None:
                continue
            answers = simultaneous_posts(base + "/v1/forms/convert", fname, path.read_bytes())
            res.add(f"first run {n}: two simultaneous FIRST requests ({fname}, no token) both 200, same bytes, passing form",
                    problems_of_first_pair(answers), f"{len(answers[0][1])} bytes each")
            st, body = get(base + "/status")
            res.add(f"first run {n}: GET /status 200, auth off", problems_of_status(st, body, "off"), f"{len(body)} bytes")
            if n == 1:
                said = OPEN_API_LOG in _logs(name).lower()
                res.add("first run 1: the log warns that the API accepts requests without a token",
                        [] if said else ["no such line in the container log"])
        finally:
            if res.failed > failed_before:
                print(_logs(name)[-3000:])
            cc.docker("rm", "-f", name)


def check_jwt_without_key(image: str, res: cc.Results) -> None:
    name = "convnokey-" + uuid.uuid4().hex[:8]
    try:
        cp = cc.docker("run", "--name", name, "-e", "AUTH_MODE=jwt", image, timeout=40)
        code, out, err = cp.returncode, cp.stdout, cp.stderr
    except subprocess.TimeoutExpired:
        code, out, err = None, b"", b""
    finally:
        cc.docker("rm", "-f", name)
    res.add(f"AUTH_MODE=jwt with no key: the container exits {EXIT_CONFIG} with the reason, no traceback",
            problems_of_config_exit(code, out, err), f"exit {code}")


def check_unwritable_out(image: str, fixtures: Path, res: cc.Results) -> None:
    """Two folders the container's user (10001) may not write: a root-owned one (a tmpfs of mode 0755 belongs to
    root) and a host folder mounted read-only."""
    empty = Path(tempfile.mkdtemp(prefix="convout"))
    try:
        os.chmod(empty, 0o755)
        mounts = (("a root-owned folder", ("--tmpfs", "/out:mode=0755")),
                  ("a read-only mount", ("-v", f"{empty}:/out:ro")))
        for label, flags in mounts:
            cp = cc.docker("run", "--rm", *cc.HARDENED, *flags, "-v", f"{fixtures.resolve()}:/in:ro", image,
                           "convert", "/in/wniosek.pdf", "--out", "/out/form.json", timeout=120)
            res.add(f"convert --out into {label}: exit {EXIT_DISK}, one line, no traceback",
                    problems_of_unwritable(cp.returncode, cp.stdout, cp.stderr),
                    f"exit {cp.returncode}: {cp.stderr.decode(errors='replace').strip()[:80]}")
    finally:
        shutil.rmtree(empty, ignore_errors=True)


def check_job_timeout(image: str, fixtures: Path, res: cc.Results) -> None:
    name = "convslow-" + uuid.uuid4().hex[:8]
    port = cc.free_port()
    base = f"http://127.0.0.1:{port}"
    slow = many_page_raster_pdf()
    failed_before = res.failed
    try:
        cp = cc.docker("run", "-d", "--name", name, "-p", f"127.0.0.1:{port}:8080", "-e",
                       f"JOB_TIMEOUT_S={JOB_TIMEOUT_S}", image)
        if cp.returncode != 0 or seconds_until_healthy(base) is None:
            res.add(f"JOB_TIMEOUT_S={JOB_TIMEOUT_S}: the container starts", [cp.stderr.decode(errors="replace")[-300:] or "not healthy"])
            return
        st, body, ctype, secs = cc.post_file_full(base + "/v1/forms/convert", "skan.pdf", slow, None, timeout=90)
        res.add(f"JOB_TIMEOUT_S={JOB_TIMEOUT_S} and a scanned PDF of {SLOW_PAGES} pages: 504 problem JSON TIMEOUT",
                problems_of_timeout(st, body, ctype, secs), f"{st} {cc._code(body)} after {secs:.1f} s, {len(slow)} bytes sent")
        health = get(base + "/healthz")[0]
        res.add("after the time-out: GET /healthz 200", [] if health == 200 else [f"status {health}"], "200")
        st, body, _, secs = cc.post_file_full(base + "/v1/forms/convert", "wniosek.docx",
                                              (fixtures / "wniosek.docx").read_bytes(), None, timeout=60)
        res.add("after the time-out: an ordinary file still converts (200, passing form)",
                [f"status {st} code {cc._code(body)}"] if st != 200 else problems_of_form(body), f"{secs:.1f} s")
    finally:
        if res.failed > failed_before:
            print(_logs(name)[-3000:])
        cc.docker("rm", "-f", name)


def run_all(image: str, fixtures: Path, res: cc.Results) -> None:
    check_first_run(image, fixtures, res)
    check_jwt_without_key(image, res)
    check_unwritable_out(image, fixtures, res)
    check_job_timeout(image, fixtures, res)
