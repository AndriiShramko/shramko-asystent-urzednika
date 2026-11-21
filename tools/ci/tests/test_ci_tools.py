"""Native tests of the CI tools (WP-F20). Run: bash tools/gate.sh py -m pytest tools/ci/tests -q

Everything here runs on Windows and Linux without Docker. What only a container can show is proved by
tools/ci/container_check.py in the image workflow; these tests prove the checks themselves (including that each
one fails on a planted fault) and run the HTTP half of it against the service started natively.
"""
from __future__ import annotations

import json
import os
import socket
import struct
import subprocess
import sys
from pathlib import Path

import pytest

CI = Path(__file__).resolve().parents[1]
ROOT = CI.parents[1]
sys.path.insert(0, str(CI))
sys.path.insert(0, str(ROOT / "apps" / "converter"))
sys.path.insert(0, str(ROOT))

import check_pins  # noqa: E402
import container_check  # noqa: E402
import formcheck  # noqa: E402
import junit_summary  # noqa: E402
import make_fixtures  # noqa: E402
import wait_run  # noqa: E402

GOOD_DIGEST = "@sha256:" + "a" * 64


def env_with_paths() -> dict:
    env = dict(os.environ)
    sep = os.pathsep
    env["PYTHONPATH"] = sep.join([str(ROOT / "apps" / "converter"), str(ROOT), env.get("PYTHONPATH", "")])
    env["PYTHONUTF8"] = "1"
    return env


@pytest.fixture(scope="module")
def fixtures(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("fixtures")
    make_fixtures.write_all(out)
    return out


# ---- pins ------------------------------------------------------------------------------------------------------
def test_repository_pins_are_clean():
    assert check_pins.main([]) == 0


def _dockerfile(tmp_path: Path, text: str) -> list[str]:
    p = tmp_path / "Dockerfile"
    p.write_text(text, encoding="utf-8")
    return check_pins.check_dockerfile(p)


def test_negative_control_base_without_digest_is_refused(tmp_path):
    found = _dockerfile(tmp_path, "FROM python:3.14-alpine AS core\n")
    assert any("not pinned by digest" in f for f in found)
    found = _dockerfile(tmp_path, "ARG BASE=python:3.14-alpine\nFROM ${BASE} AS core\n")
    assert any("not pinned by digest" in f for f in found)


def test_pinned_bases_and_stage_references_pass(tmp_path):
    text = (f"ARG B=python:3.14-alpine{GOOD_DIGEST}\nFROM ${{B}} AS ui\nFROM ui AS core\n"
            "RUN pip install --require-hashes \\\n    --only-binary=:all: -r requirements.lock\n")
    assert _dockerfile(tmp_path, text) == []


def test_negative_control_pip_install_without_wheel_only_is_refused(tmp_path):
    found = _dockerfile(tmp_path, f"FROM python{GOOD_DIGEST}\nRUN pip install --require-hashes -r requirements.lock\n")
    assert any("--only-binary=:all:" in f for f in found)
    found = _dockerfile(tmp_path, f"FROM python{GOOD_DIGEST}\nRUN pip install --only-binary=:all: fastapi\n")
    assert any("--require-hashes" in f for f in found) and any(".lock" in f for f in found)


def test_negative_control_action_by_tag_is_refused(tmp_path):
    w = tmp_path / "w.yml"
    w.write_text("steps:\n  - uses: actions/checkout@v4\n  - uses: ./local\n"
                 f"  - uses: actions/setup-python@{'b' * 40} # v7\n", encoding="utf-8")
    found = check_pins.check_workflow(w)
    assert len(found) == 1 and "actions/checkout@v4" in found[0]


# ---- fixtures --------------------------------------------------------------------------------------------------
def test_one_fixture_per_extension_each_accepted_by_the_guard_as_its_own_kind(fixtures):
    from app.config import Settings
    from app.guard import inspect_upload

    s = Settings.from_env({"AUTH_MODE": "off"})
    names = sorted(p.name for p in fixtures.iterdir())
    assert names == sorted(f"wniosek.{e}" for e in make_fixtures.EXTENSIONS)
    kinds = {p.suffix[1:]: inspect_upload(p.name, p.read_bytes(), s).kind for p in fixtures.iterdir()}
    assert kinds["doc"] == "doc" and kinds["docx"] == "docx" and kinds["ods"] == "ods" and kinds["xlsx"] == "xlsx"
    assert kinds["pdf"] == "pdf" and kinds["png"] == "png" and kinds["jpg"] == kinds["jpeg"]
    assert kinds["odt"] == "odt" and kinds["tiff"] == "tiff" and kinds["bmp"] == "bmp"
    assert kinds["gif"] == "gif" and kinds["webp"] == "webp"
    assert all(p.stat().st_size < 400_000 for p in fixtures.iterdir())


def test_doc_fixture_is_readable_through_its_piece_table(fixtures):
    """Read the .doc the way a piece-table reader does: FIB -> table stream -> CLX -> piece -> text."""
    import olefile

    with olefile.OleFileIO(str(fixtures / "wniosek.doc")) as ole:
        word = ole.openstream("WordDocument").read()
        flags = struct.unpack_from("<H", word, 10)[0]
        table = ole.openstream("1Table" if flags & 0x0200 else "0Table").read()
    assert struct.unpack_from("<H", word, 0)[0] == 0xA5EC
    fc_clx, lcb_clx = struct.unpack_from("<II", word, 154 + 33 * 8)
    clx = table[fc_clx:fc_clx + lcb_clx]
    assert clx[0] == 0x02
    plc = clx[5:5 + struct.unpack_from("<I", clx, 1)[0]]
    cp0, cp1 = struct.unpack_from("<II", plc, 0)
    fc = struct.unpack_from("<I", plc, 10)[0]
    assert not fc & 0x40000000  # uncompressed piece
    text = word[fc:fc + (cp1 - cp0) * 2].decode("utf-16-le")
    assert text.startswith(make_fixtures.TITLE) and "Nazwisko: ...." in text and text.endswith("\r")
    assert cp1 == struct.unpack_from("<I", word, 76)[0]  # ccpText


# ---- the form check, on the service as it is today (stub or real pipeline) -------------------------------------
def _convert(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "converter", "convert", str(path)], capture_output=True,
                          env=env_with_paths(), timeout=120)


READY = container_check.READY_DEFAULT


def test_ready_fixtures_convert_natively_to_a_passing_form_with_the_same_bytes_twice(fixtures):
    for path in sorted(fixtures.iterdir()):
        if container_check.ext_of(path) not in READY:
            continue
        a, b = _convert(path), _convert(path)
        assert a.returncode == 0, (path.name, a.stderr[-300:])
        assert formcheck.problems_of_form(a.stdout.rstrip(b"\n")) == [], path.name
        assert formcheck.problems_of_pair(a.stdout, b.stdout) == [], path.name


def test_other_fixtures_are_refused_with_a_typed_refusal_and_no_traceback(fixtures):
    refused = 0
    for path in sorted(fixtures.iterdir()):
        if container_check.ext_of(path) in READY:
            continue
        cp = _convert(path)
        assert container_check.problems_of_refusal(cp.returncode, cp.stdout, cp.stderr) == [], path.name
        refused += 1
    assert refused == 0   # every fixture has a reader now (WP-F20e); the refusal is proven below on a HEIC photo


def test_a_heic_photo_is_refused_with_a_typed_refusal_and_no_traceback(tmp_path):
    path = tmp_path / "wniosek.heic"
    path.write_bytes(b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic" + b"\x00" * 64)
    cp = _convert(path)
    assert cp.returncode != 0
    assert container_check.problems_of_refusal(cp.returncode, cp.stdout, cp.stderr) == []


def test_gate_probe_reports_g1_and_g2_passed_for_a_converted_pdf(tmp_path):
    """The program the container check runs inside the image, run natively on a synthetic PDF."""
    (tmp_path / "a.pdf").write_bytes(make_fixtures.pdf(make_fixtures.TITLE))
    cp = subprocess.run([sys.executable, "-c", container_check.GATE_PROBE, str(tmp_path / "a.pdf")],
                        capture_output=True, env=env_with_paths(), timeout=120)
    assert cp.returncode == 0, cp.stderr[-300:]
    checks = json.loads(cp.stdout.decode().strip().splitlines()[-1])
    assert list(checks) == [f"G{i}" for i in range(1, 13)]
    assert container_check.problems_of_gate_checks(checks) == []


@pytest.mark.parametrize("status", ["failed", "not_applicable", "absent"])
def test_negative_control_gate_g1_or_g2_not_passed_inside_the_image_is_refused(status):
    ok = {"G1": "passed", "G2": "passed"}
    for cid in ("G1", "G2"):
        bad = dict(ok)
        if status == "absent":
            del bad[cid]
        else:
            bad[cid] = status
        assert container_check.problems_of_gate_checks(bad) == [f"{cid}: {status}, expected passed"]


def test_two_different_pdfs_give_two_different_titles(tmp_path):
    outs = []
    for name, title in (("a.pdf", make_fixtures.TITLE), ("b.pdf", container_check.OTHER_TITLE)):
        (tmp_path / name).write_bytes(make_fixtures.pdf(title))
        outs.append(_convert(tmp_path / name).stdout)
    assert container_check.problems_of_titles(*outs) == []


def test_negative_control_same_title_for_different_files_is_refused():
    same = b'{"title": "Wniosek", "tabs": [], "flow": []}'
    assert container_check.problems_of_titles(same, same)
    assert container_check.problems_of_titles(None, same)


def test_negative_control_refusal_check_fails_on_a_form_a_traceback_or_silence():
    pr = container_check.problems_of_refusal
    assert pr(0, b"{}", b"")
    assert pr(1, b"", b"Traceback (most recent call last)")
    assert pr(1, b"", b"")
    assert pr(1, b"", b"Ta wersja uslugi nie potrafi jeszcze czytac tego formatu") == []


GOOD_CFG = {"User": "10001:10001", "ExposedPorts": {"8080/tcp": {}}, "Env": ["PATH=/usr/bin", "LANG=C.UTF-8"]}


def test_image_config_check_passes_a_clean_image():
    assert container_check.problems_of_image_config(GOOD_CFG, ["RUN pip install x", "ARG BASE=python"]) == []


@pytest.mark.parametrize("cfg,history,expect", [
    ({**GOOD_CFG, "User": ""}, [], "image user"),
    ({**GOOD_CFG, "User": "root"}, [], "image user"),
    ({**GOOD_CFG, "ExposedPorts": {"8080/tcp": {}, "22/tcp": {}}}, [], "exposed ports"),
    ({**GOOD_CFG, "ExposedPorts": {}}, [], "exposed ports"),
    ({**GOOD_CFG, "Env": ["API_TOKEN=x"]}, [], "environment"),
    (GOOD_CFG, ["|1 SENTINEL_SECRET=x /bin/sh -c ARG SENTINEL_SECRET"], "history"),
    (GOOD_CFG, ["ENV DB_PASSWORD=x"], "history"),
])
def test_negative_control_image_config_check_refuses_each_weakness(cfg, history, expect):
    found = container_check.problems_of_image_config(cfg, history)
    assert found and any(expect in f for f in found), found
    assert not any("=x" in f for f in found)  # never a value


def test_negative_control_form_check_refuses_a_fourth_key_broken_json_and_changed_bytes(fixtures):
    raw = _convert(fixtures / "wniosek.pdf").stdout
    doc = json.loads(raw)
    doc["meta"] = {}
    assert any("top-level keys" in p for p in formcheck.problems_of_form(json.dumps(doc).encode()))
    doc.pop("meta")
    doc["tabs"][0].pop("id", None)
    assert any(p.startswith("lint strict") for p in formcheck.problems_of_form(json.dumps(doc).encode()))
    assert formcheck.problems_of_form(b"{not json") == ["not JSON: JSONDecodeError"]
    assert formcheck.problems_of_pair(raw, raw + b" ") != []


# ---- the hardening probe ---------------------------------------------------------------------------------------
GOOD_PROBE = {"uid": 10001, "gid": 10001, "euid": 10001,
              "status": {"CapEff": "0000000000000000", "CapPrm": "0000000000000000", "NoNewPrivs": "1"},
              "root_writable": False, "app_writable": False, "tmp_writable": True, "ifaces": ["lo"],
              "connect": "OSError"}


def test_probe_of_a_hardened_container_passes():
    assert container_check.problems_of_probe(GOOD_PROBE) == []


@pytest.mark.parametrize("change, expect", [
    ({"uid": 0, "euid": 0}, "uid 0"),
    ({"gid": 0}, "gid 0"),
    ({"status": {**GOOD_PROBE["status"], "CapEff": "00000000a80425fb"}}, "CapEff"),
    ({"status": {**GOOD_PROBE["status"], "NoNewPrivs": "0"}}, "no_new_privs"),
    ({"root_writable": True}, "root file system"),
    ({"app_writable": True}, "application folder"),
    ({"ifaces": ["eth0", "lo"]}, "loopback"),
    ({"connect": "connected"}, "never-routed"),
])
def test_negative_control_probe_refuses_each_weakness(change, expect):
    found = container_check.problems_of_probe({**GOOD_PROBE, **change})
    assert any(expect in f for f in found), found


# ---- the HTTP half, against the service started natively -------------------------------------------------------
def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_http_checks_pass_against_the_native_service(fixtures, tmp_path):
    key = os.urandom(32).hex().encode()  # random per run, synthetic, never printed
    (tmp_path / "k").write_bytes(key)
    port = _free_port()
    env = env_with_paths()
    env.update({"JWT_ALG": "HS256", "JWT_SECRET_FILE": str(tmp_path / "k"), "AUTH_MODE": "jwt"})
    proc = subprocess.Popen([sys.executable, "-m", "converter", "serve", "--port", str(port)], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        res = container_check.Results()
        assert container_check.http_checks(f"http://127.0.0.1:{port}", key, fixtures, res)
        assert res.failed == 0, [r for r in res.rows if not r["ok"]]
        assert len(res.rows) == 8  # no non-ready fixture is left to refuse over HTTP (WP-F20e)
    finally:
        proc.terminate()
        proc.wait(timeout=10)


# ---- small helpers ---------------------------------------------------------------------------------------------
def test_wait_run_prints_the_lines_up_to_the_last_error():
    log = "\n".join([f"line {i}" for i in range(100)] + ["##[error]Process completed with exit code 1.", "post"])
    tail = wait_run.failed_tail(log, 5)
    assert tail[-1].startswith("##[error]") and tail[0] == "line 96" and len(tail) == 5


def test_junit_summary_counts_skips_with_their_reasons(tmp_path):
    xml = tmp_path / "r.xml"
    xml.write_text('<testsuites><testsuite><testcase name="a"/><testcase name="b"><skipped message="sets: absent"/>'
                   '</testcase><testcase name="c"><skipped message="sets: absent"/></testcase></testsuite></testsuites>',
                   encoding="utf-8")
    totals, reasons = junit_summary.summarise([str(xml)])
    assert totals == {"tests": 3, "failed": 0, "errors": 0, "skipped": 2, "passed": 1}
    assert reasons["sets: absent"] == 2
    assert junit_summary.main([str(xml)]) == 0


def test_tools_do_not_print_the_credential(monkeypatch):
    """wait_run never echoes what git credential fill gives; the value only ever goes into a header."""
    src = (CI / "wait_run.py").read_text(encoding="utf-8")
    assert "print(token" not in src and "print(f\"{token" not in src and "{token}" not in src
