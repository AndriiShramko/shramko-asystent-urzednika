"""Configuration validation and the command line."""
from __future__ import annotations

import json
from pathlib import Path

import factory as fx
import pytest

from app import cli
from app.config import ConfigError, Settings


def env(tmp_path: Path, **over: str) -> dict[str, str]:
    key = tmp_path / "secret.key"
    key.write_bytes(fx.SECRET)
    base = {"JWT_SECRET_FILE": str(key)}
    base.update(over)
    return base


def test_defaults_follow_the_design(tmp_path):
    s = Settings.from_env(env(tmp_path))
    assert (s.max_upload_bytes, s.max_pages, s.max_pixels, s.job_timeout_s) == (20971520, 60, 80000000, 600)
    assert (s.concurrency, s.rate_limit_per_min, s.jwt_alg, s.jwt_leeway_s) == (2, 60, "HS256", 30)
    assert s.jwt_required_claims == ("exp",) and s.strict_extensions is True and s.auth_enabled


def test_values_come_from_the_environment(tmp_path):
    s = Settings.from_env(env(tmp_path, MAX_UPLOAD_BYTES="1000", STRICT_EXTENSIONS="FALSE", JWT_REQUIRED_CLAIMS="exp, sub"))
    assert s.max_upload_bytes == 1000 and not s.strict_extensions and s.jwt_required_claims == ("exp", "sub")


@pytest.mark.parametrize("over,fragment", [
    ({"JWT_PUBLIC_KEY_FILE": "{pub}"}, "HS256 takes JWT_SECRET_FILE only"),         # public key with HS256
    ({"JWT_ALG": "RS256"}, "shared secret belongs to HS256"),                        # secret with an asymmetric alg
    ({"JWT_ALG": "none"}, "must not be none"),
    ({"JWT_ALG": "HS1"}, "JWT_ALG must be one of"),
    ({"JWT_LEEWAY_S": "121"}, "at most 120"),
    ({"JWT_REQUIRED_CLAIMS": "sub"}, "exp"),
    ({"MAX_UPLOAD_BYTES": "lots"}, "whole number"),
    ({"MAX_UPLOAD_BYTES": "0"}, "positive"),
    ({"STRICT_EXTENSIONS": "maybe"}, "true or false"),
    ({"JWT_SECRET_FILE": "https://keys.example/k"}, "a URL is not supported"),
    ({"JWT_SECRET_FILE": "/no/such/file"}, "does not exist"),
    ({"MODEL_STEP": "on"}, "MODEL_STEP must be one of"),
    ({"SIGN_OUTPUT": "jws"}, "SIGNING_KEY_FILE"),
])
def test_inconsistent_sets_are_refused(tmp_path, over, fragment):
    pub = tmp_path / "pub.pem"
    pub.write_text("x")
    over = {k: v.replace("{pub}", str(pub)) for k, v in over.items()}
    with pytest.raises(ConfigError) as ei:
        Settings.from_env(env(tmp_path, **over))
    assert any(fragment in p for p in ei.value.problems), ei.value.problems


def test_jwt_mode_without_any_key_is_refused():
    with pytest.raises(ConfigError, match="needs a key file"):
        Settings.from_env({"AUTH_MODE": "jwt"})


def test_the_default_auth_mode_is_auto_off_without_a_key_and_jwt_with_one(tmp_path):
    bare = Settings.from_env({})
    assert bare.auth_mode == "auto" and not bare.auth_enabled
    keyed = Settings.from_env(env(tmp_path))
    assert keyed.auth_mode == "auto" and keyed.auth_enabled
    with pytest.raises(ConfigError, match="does not exist"):   # auto with a key that is not there fails closed
        Settings.from_env({"JWT_SECRET_FILE": str(tmp_path / "none.key")})
    with pytest.raises(ConfigError, match="AUTH_MODE must be one of"):
        Settings.from_env({"AUTH_MODE": "maybe"})


def test_serve_with_an_empty_environment_starts_and_healthz_answers(monkeypatch, caplog):
    import logging

    import uvicorn
    from fastapi.testclient import TestClient

    for name in ("AUTH_MODE", "JWT_SECRET_FILE", "JWT_PUBLIC_KEY_FILE", "JWT_JWKS_FILE"):
        monkeypatch.delenv(name, raising=False)
    seen: dict = {}
    monkeypatch.setattr(uvicorn, "run", lambda app, **kw: seen.update(app=app))
    with caplog.at_level(logging.WARNING, logger="converter"):
        assert cli.main(["serve"]) == 0
    assert "No JWT key configured" in caplog.text and "WITHOUT a token" in caplog.text
    client = TestClient(seen["app"])
    assert client.get("/healthz").status_code == 200
    body, ctype = fx.multipart([("file", "a.pdf", fx.pdf(), "application/pdf")])
    assert client.post("/v1/forms/convert", content=body, headers={"Content-Type": ctype}).status_code == 200


def test_serve_with_explicit_jwt_and_no_key_exits_3(monkeypatch, capsys):
    for name in ("JWT_SECRET_FILE", "JWT_PUBLIC_KEY_FILE", "JWT_JWKS_FILE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AUTH_MODE", "jwt")
    assert cli.main(["serve"]) == 3
    assert "AUTH_MODE=jwt needs a key file" in capsys.readouterr().err


def test_auth_off_needs_no_key():
    assert not Settings.from_env({"AUTH_MODE": "off"}).auth_enabled


def test_every_problem_is_listed_at_once(tmp_path):
    with pytest.raises(ConfigError) as ei:
        Settings.from_env(env(tmp_path, JWT_LEEWAY_S="500", STRICT_EXTENSIONS="x", JWT_REQUIRED_CLAIMS="sub"))
    assert len(ei.value.problems) == 3


# ---- command line -----------------------------------------------------------------------------------------------

def test_convert_writes_form_and_sidecar(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("JWT_SECRET_FILE", raising=False)
    src = tmp_path / "wniosek.pdf"
    src.write_bytes(fx.pdf())
    out = tmp_path / "form.json"
    assert cli.main(["convert", str(src), "--out", str(out), "--report", str(tmp_path / "rep")]) == 0
    form = json.loads(out.read_text(encoding="utf-8"))
    assert set(form) == {"title", "tabs", "flow"}
    meta = json.loads((tmp_path / "rep" / "wniosek.meta.json").read_text(encoding="utf-8"))
    assert len(meta["input_sha256"]) == 64 and len(meta["form_sha256"]) == 64


def test_convert_prints_the_form_to_standard_output(tmp_path, capsys):
    src = tmp_path / "a.docx"
    src.write_bytes(fx.docx())
    assert cli.main(["convert", str(src)]) == 0
    assert set(json.loads(capsys.readouterr().out)) == {"title", "tabs", "flow"}


def test_convert_refuses_a_spoofed_file_with_exit_2_and_a_problem(tmp_path, capsys):
    src = tmp_path / "a.pdf"
    src.write_bytes(bytes(3) + b"spoof")   # neither a known format nor text (WP-F20f: a PNG named .pdf is now read as PNG)
    assert cli.main(["convert", str(src)]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and json.loads(captured.err)["code"] == "TYPE_MISMATCH"


def test_convert_refuses_a_missing_file_and_a_bad_configuration(tmp_path, monkeypatch, capsys):
    assert cli.main(["convert", str(tmp_path / "none.pdf")]) == 4
    src = tmp_path / "a.pdf"
    src.write_bytes(fx.pdf())
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "abc")
    assert cli.main(["convert", str(src)]) == 3
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "100")
    assert cli.main(["convert", str(src)]) == 2  # TOO_LARGE, judged from the size on disk
    assert json.loads(capsys.readouterr().err.splitlines()[-1])["code"] == "TOO_LARGE"


def test_an_output_that_cannot_be_written_is_one_line_and_exit_4(tmp_path, monkeypatch, capsys):
    src = tmp_path / "a.pdf"
    src.write_bytes(fx.pdf())
    out = tmp_path / "no-such-folder" / "form.json"   # a real OSError of the file system
    assert cli.main(["convert", str(src), "--out", str(out)]) == 4
    captured = capsys.readouterr()
    lines = captured.err.splitlines()
    assert captured.out == "" and len(lines) == 1 and "Traceback" not in captured.err
    assert lines[0].startswith(f"Cannot write {out}: ") and lines[0].endswith('On Linux add --user "$(id -u):$(id -g)"')

    def denied(self, *a, **kw):   # what a folder owned by another user answers inside the container
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(Path, "write_text", denied)
    assert cli.main(["convert", str(src), "--out", str(tmp_path / "form.json")]) == 4
    assert capsys.readouterr().err.splitlines() == [
        f'Cannot write {tmp_path / "form.json"}: Permission denied. On Linux add --user "$(id -u):$(id -g)"']
    assert cli.main(["convert", str(src), "--report", str(tmp_path / "rep")]) == 4   # the sidecar file the same way
    assert capsys.readouterr().err.count("Cannot write") == 1
