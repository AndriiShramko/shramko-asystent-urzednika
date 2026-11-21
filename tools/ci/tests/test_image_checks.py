"""Tests of the image checks of WP-F20i: the pure halves of tools/ci/container_check.py (environment, locale,
determinism, sidecar, hostile files), each with its negative control, and the HTTP half against the native
service. No Docker is needed: the container half runs in CI.

    bash tools/gate.sh py -m pytest tools/ci/tests/test_image_checks.py -q
"""
from __future__ import annotations

import copy
import io
import json
import os
import socket
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "ci"))
sys.path.insert(0, str(ROOT / "apps" / "converter"))
sys.path.insert(0, str(ROOT))

import container_check  # noqa: E402
import hostile_inputs  # noqa: E402
import make_fixtures  # noqa: E402
import sidecarcheck  # noqa: E402


def env_with_paths() -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT / "apps" / "converter"), str(ROOT), env.get("PYTHONPATH", "")])
    env["PYTHONUTF8"] = "1"
    return env


def _convert(path: Path, *more: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "converter", "convert", str(path), *more], capture_output=True,
                          env=env_with_paths(), timeout=120)


@pytest.fixture(scope="module")
def converted(tmp_path_factory) -> dict[str, tuple[bytes, bytes]]:
    """name -> (form bytes, sidecar bytes) of one native conversion with --report, for a PDF and a raster."""
    folder = tmp_path_factory.mktemp("converted")
    out = {}
    for name, data in (("wniosek.pdf", make_fixtures.pdf()), ("wniosek.png", make_fixtures.png())):
        (folder / name).write_bytes(data)
        cp = _convert(folder / name, "--report", str(folder / "report"))
        assert cp.returncode == 0, cp.stderr[-300:]
        out[name] = (cp.stdout.rstrip(b"\r\n"), (folder / "report" / (Path(name).stem + ".meta.json")).read_bytes())
    return out


# ---- the sidecar -----------------------------------------------------------------------------------------------
def test_sidecar_of_a_pdf_and_of_a_raster_passes_and_carries_the_digest_of_its_form(converted):
    for name, (form, sidecar) in converted.items():
        assert sidecarcheck.problems_of_sidecar(sidecar, form) == [], name
    assert "ledger" in json.loads(converted["wniosek.pdf"][1])["meta"]   # the contract part is really exercised


def _drop_check(d):
    d["checks"].pop()


def _status(d):
    d["checks"][0]["status"] = "ok"


def _twice(d):
    d["checks"][1]["id"] = "G1"


def _extra_key(d):
    d["debug"] = True


def _no_counts(d):
    del d["counts"]


def _warning_without_code(d):
    d["warnings"].append({"detail": "no code"})


def _ledger_broken(d):
    d["meta"]["ledger"]["rows"] = "none"


def _digest(d):
    d["form_sha256"] = "0" * 64


@pytest.mark.parametrize("change, expect", [
    (_drop_check, "minItems"), (_status, "enum"), (_twice, "G1 to G12 once each"), (_extra_key, "additionalProperties"),
    (_no_counts, "required"), (_warning_without_code, "required"), (_ledger_broken, "contract Ledger"),
    (_digest, "not the digest"),
])
def test_negative_control_a_broken_sidecar_is_refused(converted, change, expect):
    form, sidecar = converted["wniosek.pdf"]
    doc = json.loads(sidecar)
    change(doc)
    found = sidecarcheck.problems_of_sidecar(json.dumps(doc).encode(), form)
    assert any(expect in f for f in found), found


def test_negative_control_sidecar_that_is_not_json_or_not_an_object_is_refused():
    assert sidecarcheck.problems_of_sidecar(b"")[0].startswith("sidecar is not JSON")
    assert sidecarcheck.problems_of_sidecar(b"[]") == ["sidecar is not an object: list"]


def test_a_broken_sidecar_makes_the_conversion_row_fail_and_so_the_run_red(converted):
    """The row of a fixture is what turns CI red (main returns 1 when a row failed)."""
    form, sidecar = converted["wniosek.pdf"]
    good, bad = container_check.Results(), container_check.Results()
    good.add("convert", container_check.conversion_problems(form + b"\n", b"", 0, form, sidecar))
    assert good.failed == 0, good.rows
    doc = json.loads(sidecar)
    del doc["checks"]
    bad.add("convert", container_check.conversion_problems(form + b"\n", b"", 0, form, json.dumps(doc).encode()))
    assert bad.failed == 1 and "sidecar" in bad.rows[0]["detail"]
    for broken in (container_check.conversion_problems(form + b"\n", b"", 0, form, b""),          # no sidecar came
                   container_check.conversion_problems(form + b"\n", b"", 2, b"", b""),            # --report failed
                   container_check.conversion_problems(form + b"\n", b"", 0, form + b" ", sidecar)):   # other bytes
        assert broken


def test_the_emitted_sidecar_is_not_yet_the_contract_and_the_check_says_how_far(converted):
    """An honest number, not a hidden gap: the full contract is not met; when it is, this test must change."""
    assert sidecarcheck.differences_from_contract(converted["wniosek.pdf"][1]) > 0
    assert sidecarcheck.differences_from_contract(b"{") == -1


# ---- the image environment and the locale probe ------------------------------------------------------------------
GOOD_ENV = [f"{k}={v}" for k, v in container_check.REQUIRED_ENV.items()] + ["PATH=/usr/local/bin", "PYTHONUTF8=1"]
GOOD_LOCALE = {"env": dict(container_check.REQUIRED_ENV), "locale": "C.UTF-8", "codeset": "UTF-8",
               "utc_offset": "+0000", "epoch_hour": 0}


def test_image_environment_with_every_pinned_variable_passes():
    assert container_check.problems_of_image_env({"Env": GOOD_ENV}) == []
    assert container_check.problems_of_locale(GOOD_LOCALE) == []
    assert container_check.problems_of_locale({**GOOD_LOCALE, "locale": "C.UTF-8;C;C;C;C;C"}) == []   # musl


@pytest.mark.parametrize("name", sorted(container_check.REQUIRED_ENV))
def test_negative_control_a_missing_or_changed_variable_of_the_image_is_refused(name):
    assert name in container_check.problems_of_image_env({"Env": [e for e in GOOD_ENV if not e.startswith(name + "=")]})[0]
    changed = [e if not e.startswith(name + "=") else f"{name}=4" for e in GOOD_ENV]
    assert name in container_check.problems_of_image_env({"Env": changed})[0]
    env = {**container_check.REQUIRED_ENV, name: "other"}
    assert any(name in f for f in container_check.problems_of_locale({**GOOD_LOCALE, "env": env}))


@pytest.mark.parametrize("change, expect", [
    ({"locale": "ERROR Error"}, "refused the locale"), ({"codeset": "ANSI_X3.4-1968"}, "not UTF-8"),
    ({"utc_offset": "+0100", "epoch_hour": 1}, "not UTC"),
])
def test_negative_control_locale_probe_refuses_each_weakness(change, expect):
    found = container_check.problems_of_locale({**GOOD_LOCALE, **change})
    assert any(expect in f for f in found), found


# ---- determinism ----------------------------------------------------------------------------------------------
def test_four_equal_runs_pass_and_any_difference_is_refused():
    runs = [(f"run {n}", 0, b'{"title":"a"}', b'{"version":1}') for n in range(4)]
    assert container_check.problems_of_runs(runs) == []
    other_form = copy.copy(runs)
    other_form[3] = ("run 3", 0, b'{"title":"b"}', b'{"version":1}')
    assert "form bytes differ" in container_check.problems_of_runs(other_form)[0]
    other_side = copy.copy(runs)
    other_side[2] = ("run 2", 0, b'{"title":"a"}', b'{"version":2}')
    assert "sidecar bytes differ" in container_check.problems_of_runs(other_side)[0]
    assert container_check.problems_of_runs([("run 0", 137, b"", b"")]) == ["run 0: exit 137"]
    assert container_check.problems_of_runs([("run 0", 0, b"", b"")]) == ["a run gave no form or no sidecar"]


def test_native_conversion_is_the_same_bytes_with_one_and_with_four_threads(tmp_path):
    """The native twin of the container check: form and sidecar of a PDF, thread limit 1 against 4."""
    (tmp_path / "wniosek.pdf").write_bytes(make_fixtures.pdf())
    runs = []
    for threads in ("1", "4"):
        env = env_with_paths()
        env.update({"OMP_THREAD_LIMIT": threads, "OMP_NUM_THREADS": threads})
        cp = subprocess.run([sys.executable, "-m", "converter", "convert", str(tmp_path / "wniosek.pdf"), "--report",
                             str(tmp_path / threads)], capture_output=True, env=env, timeout=120)
        runs.append((f"{threads} threads", cp.returncode, cp.stdout, (tmp_path / threads / "wniosek.meta.json").read_bytes()))
    assert container_check.problems_of_runs(runs) == []


# ---- hostile files ----------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def hostile(tmp_path_factory) -> Path:
    folder = tmp_path_factory.mktemp("hostile")
    hostile_inputs.build(folder)
    return folder


def test_hostile_files_are_what_they_claim_and_small(hostile):
    names = sorted(p.name for p in hostile.iterdir())
    assert names == sorted([*hostile_inputs.FROM_CHAIN, "declared-size.docx", "entity-expansion.docx", "truncated.png"])
    assert all(p.stat().st_size < 400_000 for p in hostile.iterdir())
    assert (hostile / "empty.pdf").stat().st_size == 0
    with zipfile.ZipFile(hostile / "declared-size.docx") as z:
        info = z.getinfo("word/document.xml")
        assert info.file_size == hostile_inputs.DECLARED_SIZE and info.compress_size < 400
    with zipfile.ZipFile(hostile / "entity-expansion.docx") as z:
        xml = z.read("word/document.xml")
        assert xml.count(b"<!ENTITY") == 10 and b"&lol9;" in xml and len(xml) < 2000
    with zipfile.ZipFile(hostile / "zip-bomb.docx") as z:
        assert z.getinfo("word/document.xml").file_size == 300 * (1 << 20)
    png = (hostile / "truncated.png").read_bytes()
    assert png.startswith(b"\x89PNG") and b"IEND" not in png
    from PIL import Image
    with pytest.raises(OSError):
        Image.open(io.BytesIO(png)).load()


def test_every_hostile_file_is_refused_natively_in_time_with_exit_2_and_problem_json(hostile):
    import time
    for path in sorted(hostile.iterdir()):
        t0 = time.monotonic()
        cp = _convert(path)
        found = container_check.problems_of_hostile_cli(cp.returncode, cp.stdout, cp.stderr, time.monotonic() - t0)
        assert found == [], (path.name, found)


GOOD_PROBLEM = json.dumps({"type": "about:blank", "title": "x", "status": 422, "code": "UNREADABLE"}).encode()


@pytest.mark.parametrize("args, expect", [
    ((None, b"", b"", 60.0), "hangs"),
    ((0, b'{"title":"x"}', b"", 1.0), "a form was produced"),
    ((1, b"", b"Traceback (most recent call last):\n  ...\nValueError", 1.0), "traceback"),
    ((1, b"", GOOD_PROBLEM, 1.0), "not the refusal code"),
    ((2, b"", b"refused", 1.0), "problem JSON"),
    ((2, b"", json.dumps({"status": 500, "code": "INTERNAL"}).encode(), 1.0), "problem JSON"),
    ((2, b"", GOOD_PROBLEM, 10.5), "over 10 s"),
])
def test_negative_control_hostile_command_line_answer_is_refused(args, expect):
    assert container_check.problems_of_hostile_cli(2, b"", GOOD_PROBLEM, 1.0) == []
    found = container_check.problems_of_hostile_cli(*args)
    assert any(expect in f for f in found), found


@pytest.mark.parametrize("args, expect", [
    ((0, b"", "", 30.0), "no HTTP answer"),
    ((200, b'{"title":"x"}', "application/json", 1.0), "not a 4xx"),
    ((500, b"Internal Server Error", "text/plain; charset=utf-8", 1.0), "not a 4xx"),
    ((500, b"Internal Server Error", "text/plain; charset=utf-8", 1.0), "not application/problem+json"),
    ((422, b"Unprocessable", "application/problem+json", 1.0), "not a problem JSON"),
    ((415, GOOD_PROBLEM, "application/problem+json", 1.0), "the body says status 422"),
    ((422, GOOD_PROBLEM, "application/problem+json", 11.0), "over 10 s"),
])
def test_negative_control_hostile_http_answer_is_refused(args, expect):
    assert container_check.problems_of_hostile_http(422, GOOD_PROBLEM, "application/problem+json", 1.0) == []
    found = container_check.problems_of_hostile_http(*args)
    assert any(expect in f for f in found), found


def test_job_log_keeps_the_rows_of_the_check_and_drops_the_time_stamps():
    import job_log

    log = ("2026-11-21T10:00:00.1234567Z PASS  a  (x)\n2026-11-21T10:00:01.0000000Z noise PASS  \n"
           "2026-11-21T10:00:02.0Z FAIL  b  (y)\n2026-11-21T10:00:03.0Z 56 passed, 1 failed\n")
    assert job_log.matching(log, r"^(PASS|FAIL)  |^\d+ passed, \d+ failed") == [
        "PASS  a  (x)", "FAIL  b  (y)", "56 passed, 1 failed"]


# ---- the HTTP half, against the service started natively ----------------------------------------------------------
def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_hostile_files_and_the_sidecar_over_http_against_the_native_service(hostile, tmp_path):
    key = os.urandom(32).hex().encode()  # random per run, synthetic, never printed
    (tmp_path / "k").write_bytes(key)
    (tmp_path / "fixtures").mkdir()
    (tmp_path / "fixtures" / "wniosek.pdf").write_bytes(make_fixtures.pdf())
    port = _free_port()
    env = env_with_paths()
    env.update({"JWT_ALG": "HS256", "JWT_SECRET_FILE": str(tmp_path / "k"), "AUTH_MODE": "jwt"})
    proc = subprocess.Popen([sys.executable, "-m", "converter", "serve", "--port", str(port)], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        base = f"http://127.0.0.1:{port}"
        assert container_check.wait_healthy(base) == 200
        res = container_check.Results()
        container_check.http_sidecar_check(base, container_check.token(key), tmp_path / "fixtures", res)
        container_check.http_hostile_checks(base, container_check.token(key), hostile, res)
        assert res.failed == 0, [r for r in res.rows if not r["ok"]]
        assert len(res.rows) == 1 + 8 + 1   # the sidecar, eight hostile files, healthz afterwards
    finally:
        proc.terminate()
        proc.wait(timeout=10)
