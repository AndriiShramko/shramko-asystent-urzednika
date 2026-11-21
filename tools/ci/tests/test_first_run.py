"""Tests of tools/ci/first_run.py (WP-F20i stage 2): the pure halves with their negative controls, and the same
first run against the service started natively with NO configuration. The container half runs in CI.

    bash tools/gate.sh py -m pytest tools/ci/tests/test_first_run.py -q
"""
from __future__ import annotations

import io
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "ci"))
sys.path.insert(0, str(ROOT / "apps" / "converter"))
sys.path.insert(0, str(ROOT))

import container_check  # noqa: E402
import first_run  # noqa: E402
import make_fixtures  # noqa: E402

CONFIG_NAMES = ("AUTH_MODE", "JWT_ALG", "JWT_SECRET_FILE", "JWT_PUBLIC_KEY_FILE", "JWT_JWKS_FILE", "JOB_TIMEOUT_S",
                "CONCURRENCY")


def bare_env() -> dict:
    """The environment of the jury's first run: the paths of this checkout and nothing of the configuration."""
    env = {k: v for k, v in os.environ.items() if k not in CONFIG_NAMES}
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT / "apps" / "converter"), str(ROOT), env.get("PYTHONPATH", "")])
    env["PYTHONUTF8"] = "1"
    return env


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def form(tmp_path_factory) -> bytes:
    path = tmp_path_factory.mktemp("form") / "wniosek.pdf"
    path.write_bytes(make_fixtures.pdf())
    cp = subprocess.run([sys.executable, "-m", "converter", "convert", str(path)], capture_output=True,
                        env=bare_env(), timeout=120)
    assert cp.returncode == 0, cp.stderr[-300:]
    return cp.stdout.rstrip(b"\r\n")


# ---- the slow file ----------------------------------------------------------------------------------------------
def test_slow_pdf_has_forty_pages_no_text_layer_and_is_small():
    from pypdf import PdfReader

    raw = first_run.many_page_raster_pdf()
    assert raw == first_run.many_page_raster_pdf()   # built the same way twice
    reader = PdfReader(io.BytesIO(raw))
    assert len(reader.pages) == first_run.SLOW_PAGES == 40
    assert all(not (p.extract_text() or "").strip() for p in reader.pages)
    assert len(raw) < 400_000


# ---- pure halves ------------------------------------------------------------------------------------------------
def test_two_equal_passing_answers_pass_and_each_weakness_is_refused(form):
    assert first_run.problems_of_first_pair([(200, form), (200, form)]) == []
    busy = json.dumps({"status": 429, "code": "BUSY"}).encode()
    assert "request 2: status 429 code BUSY" in first_run.problems_of_first_pair([(200, form), (429, busy)])
    assert "request 1: status 422 code UNREADABLE" in first_run.problems_of_first_pair(
        [(422, json.dumps({"status": 422, "code": "UNREADABLE"}).encode()), (200, form)])
    other = json.dumps({**json.loads(form), "title": "Inny"}, ensure_ascii=False, separators=(",", ":")).encode()
    assert "different bytes" in first_run.problems_of_first_pair([(200, form), (200, other)])[0]
    assert first_run.problems_of_first_pair([(200, b"{}"), (200, b"{}")])   # equal, but not a form
    assert first_run.problems_of_first_pair([(0, b""), (0, b"")])           # no answer at all


GOOD_STATUS = {"service": "converter", "version": "0.1.0", "engine": "rules", "auth": "off", "formats": ["docx", "pdf"],
               "limits": {"job_timeout_s": 600, "concurrency": 2, "max_pages": 60, "max_upload_bytes": 20971520}}


@pytest.mark.parametrize("change, expect", [
    ({"auth": "jwt"}, "auth is 'jwt'"), ({"formats": []}, "formats"), ({"limits": {"job_timeout_s": 0}}, "limits"),
    ({"secret_path": "/run/secrets"}, "keys"),
])
def test_status_answer_passes_and_each_weakness_is_refused(change, expect):
    assert first_run.problems_of_status(200, json.dumps(GOOD_STATUS).encode(), "off") == []
    found = first_run.problems_of_status(200, json.dumps({**GOOD_STATUS, **change}).encode(), "off")
    assert any(expect in f for f in found), found
    assert first_run.problems_of_status(404, b"{}", "off") == ["status 404"]
    assert first_run.problems_of_status(200, b"ok", "off") == ["the body is not JSON"]


def test_config_exit_passes_on_exit_3_with_the_reason_and_refuses_the_rest():
    reason = b"Configuration refused:\n  AUTH_MODE=jwt needs a key\n"
    assert first_run.problems_of_config_exit(3, b"", reason) == []
    assert "did not exit" in first_run.problems_of_config_exit(None, b"", b"")[0]
    assert "exit 1, not 3" in first_run.problems_of_config_exit(1, b"", reason)
    assert "traceback in the output" in first_run.problems_of_config_exit(3, b"", reason + b"Traceback (most recent call last):")
    assert first_run.problems_of_config_exit(3, b"", b"") == ["stderr does not say that the configuration was refused"]


def test_unwritable_out_passes_on_exit_4_with_one_line_and_refuses_the_rest():
    line = b'Cannot write /out/form.json: Permission denied. On Linux add --user "$(id -u):$(id -g)"\n'
    assert first_run.problems_of_unwritable(4, b"", line) == []
    trace = b"Traceback (most recent call last):\n  File x\nPermissionError: [Errno 13] Permission denied: '/out/form.json'\n"
    found = first_run.problems_of_unwritable(1, b"", trace)
    assert "exit 1, not 4" in found and "traceback on stderr" in found
    assert first_run.problems_of_unwritable(4, b"", line + b"and a second line\n")
    assert first_run.problems_of_unwritable(4, b'{"title":"x"}', line) == ["stdout not empty (13 bytes)"]


def test_timeout_answer_passes_and_each_weakness_is_refused():
    body = json.dumps({"type": "about:blank", "title": "x", "status": 504, "code": "TIMEOUT"}).encode()
    pj = "application/problem+json"
    assert first_run.problems_of_timeout(504, body, pj, 2.3) == []
    assert "got 200" in first_run.problems_of_timeout(200, b'{"title":"x"}', "application/json", 30.0)[0]
    assert "got 500 GATE_FAILED" in first_run.problems_of_timeout(500, json.dumps({"status": 500, "code": "GATE_FAILED"}).encode(), pj, 2.0)[0]
    assert "no HTTP answer" in first_run.problems_of_timeout(0, b"", "", 90.0)[0]
    assert "content type" in first_run.problems_of_timeout(504, body, "text/plain", 2.3)[0]
    assert "with a limit of 2 s" in first_run.problems_of_timeout(504, body, pj, 40.0)[0]
    assert "with a limit of 2 s" in first_run.problems_of_timeout(504, body, pj, 0.2)[0]   # answered before the limit


# ---- the same first run, natively ---------------------------------------------------------------------------------
def test_first_run_of_the_native_service_with_no_configuration(tmp_path):
    """No variable, no key: healthy, the log says the API is open, two simultaneous first requests equal, /status."""
    port = _free_port()
    log = open(tmp_path / "serve.log", "wb")
    proc = subprocess.Popen([sys.executable, "-m", "converter", "serve", "--port", str(port)], env=bare_env(),
                            stdout=log, stderr=subprocess.STDOUT)
    try:
        base = f"http://127.0.0.1:{port}"
        assert first_run.seconds_until_healthy(base) is not None
        answers = first_run.simultaneous_posts(base + "/v1/forms/convert", "wniosek.pdf", make_fixtures.pdf())
        assert first_run.problems_of_first_pair(answers) == []
        st, body = first_run.get(base + "/status")
        assert first_run.problems_of_status(st, body, "off") == []
        res = container_check.Results()
        (tmp_path / "f").mkdir()
        (tmp_path / "f" / "wniosek.pdf").write_bytes(make_fixtures.pdf())
        container_check.http_sidecar_check(base, None, tmp_path / "f", res)
        assert res.failed == 0, res.rows
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        log.close()
    assert first_run.OPEN_API_LOG in (tmp_path / "serve.log").read_text(encoding="utf-8", errors="replace").lower()


def test_native_service_with_auth_mode_jwt_and_no_key_exits_3():
    env = bare_env()
    env["AUTH_MODE"] = "jwt"
    cp = subprocess.run([sys.executable, "-m", "converter", "serve", "--port", str(_free_port())], env=env,
                        capture_output=True, timeout=60)
    assert first_run.problems_of_config_exit(cp.returncode, cp.stdout, cp.stderr) == []


def test_native_convert_out_into_a_missing_folder_exits_4_with_one_line(tmp_path):
    (tmp_path / "wniosek.pdf").write_bytes(make_fixtures.pdf())
    cp = subprocess.run([sys.executable, "-m", "converter", "convert", str(tmp_path / "wniosek.pdf"), "--out",
                         str(tmp_path / "no-such-folder" / "form.json")], env=bare_env(), capture_output=True, timeout=120)
    assert first_run.problems_of_unwritable(cp.returncode, cp.stdout, cp.stderr) == []
