"""WP-H4: the engine is always visible. The state module, the header, /status, the log, the command line, and the
proof that nothing of the model's configuration but its name and host class ever leaves."""
from __future__ import annotations

import json
import logging

import factory as fx
import pytest
from fastapi.testclient import TestClient

from app import __version__, cli, engine, pipeline
from app.config import ConfigError, Settings
from app.main import create_app

# A configured model with everything that must never be shown. All values are synthetic.
URL_USER, URL_PASS, URL_HOST, URL_PORT, URL_QUERY = "apiuser", "FAKEPASSWORD-9x", "models.example.test", "8443", "FAKEQUERYTOKEN-7z"
KEY_VALUE = "FAKE-KEY-VALUE-do-not-show-123"
KEY_IN_FILE = "FAKE-FILE-KEY-do-not-show-456"
MODEL_NAME = "open-lab/Open-Model-3B"


def model_env(tmp_path) -> dict[str, str]:
    key_file = tmp_path / "model-key-folder" / "model.key"
    key_file.parent.mkdir(exist_ok=True)
    key_file.write_text(KEY_IN_FILE, encoding="utf-8")
    return {
        "MODEL_BASE_URL": f"https://{URL_USER}:{URL_PASS}@{URL_HOST}:{URL_PORT}/v1/secretpath?api_key={URL_QUERY}",
        "MODEL_NAME": MODEL_NAME, "MODEL_API_KEY": KEY_VALUE, "MODEL_API_KEY_FILE": str(key_file),
    }


ZERO = {"rules": 0, "rules+model": 0, "rules-fallback": 0}
FORBIDDEN = (URL_USER, URL_PASS, URL_HOST, URL_PORT, URL_QUERY, "secretpath", KEY_VALUE, KEY_IN_FILE, "model-key-folder",
             "model.key")


def assert_nothing_secret(text: str, where: str) -> None:
    found = [x for x in FORBIDDEN if x in text]
    assert not found, f"{where} shows {found}"


# ---- the state module -------------------------------------------------------------------------------------------

@pytest.mark.parametrize("codes, expected", [
    ([], "rules"),
    (["OCR_USED", "LABEL_RAW"], "rules"),
    (["MODEL_SKIPPED"], "rules"),
    (["MODEL_USED"], "rules+model"),
    (["MODEL_FALLBACK"], "rules-fallback"),
    (["MODEL_USED", "MODEL_FALLBACK"], "rules-fallback"),   # the stronger claim is never made when the step also failed
])
def test_the_engine_of_a_conversion_is_read_from_its_sidecar_warnings(codes, expected):
    assert engine.engine_of({"warnings": [{"code": c} for c in codes]}) == expected


@pytest.mark.parametrize("sidecar", [None, {}, {"warnings": None}, {"warnings": ["MODEL_USED", 3, None]}, "MODEL_USED", []])
def test_a_sidecar_of_any_shape_is_rules_and_never_a_crash(sidecar):
    assert engine.engine_of(sidecar) == "rules"


def test_the_three_engines_and_the_header_name_are_fixed():
    assert engine.ENGINES == ("rules", "rules+model", "rules-fallback") and engine.HEADER == "X-Converter-Engine"
    assert engine.MODEL_STEP_BUILT is False   # this build has no model step; WP-H1 turns it on


@pytest.mark.parametrize("url, expected", [
    ("http://localhost:11434/v1", "loopback"), ("http://127.0.0.1:8000", "loopback"), ("http://[::1]:8000/v1", "loopback"),
    ("http://10.0.0.5:8000/v1", "private"), ("http://192.168.1.20/v1", "private"), ("http://ollama:11434/v1", "private"),
    ("http://host.docker.internal:11434/v1", "private"), ("http://gpu.lan/v1", "private"),
    ("https://models.example.test/v1", "public"), ("https://u:p@models.example.test:8443/v1?k=v", "public"),
    ("http://8.8.8.8/v1", "public"), ("not a url", "invalid"), ("http://", "invalid"), ("http://[bad", "invalid"),
])
def test_host_class_comes_from_the_shape_of_the_host_and_resolves_nothing(url, expected, monkeypatch):
    import socket

    def no_network(*a, **kw):
        raise AssertionError("the engine module must not touch the network")

    monkeypatch.setattr(socket, "getaddrinfo", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    assert engine.host_class(url) == expected


def test_with_nothing_configured_the_state_is_off_and_the_engine_is_rules():
    s = Settings.from_env({})
    assert s.model_step == "auto" and (s.model_base_url, s.model_name, s.model_api_key_file, s.model_api_key_set) == ("", "", "", False)
    assert engine.model_state(s) == ("OFF", "not-configured") and engine.expected_engine(s) == "rules"
    assert engine.model_config(s) == engine.ModelConfig(step="auto", configured=False, name="", host="", key="none")
    assert engine.start_line(s) == "engine=rules state=OFF reason=not-configured"
    assert engine.EngineState(s).status() == {"engine": "rules"}   # nothing else: /status keeps its six keys


def test_a_configured_model_is_reported_by_name_and_host_class_and_is_not_used(tmp_path):
    s = Settings.from_env(model_env(tmp_path))
    cfg = engine.model_config(s)
    assert cfg == engine.ModelConfig(step="auto", configured=True, name=MODEL_NAME, host="public", key="file")
    assert engine.model_state(s) == ("UNAVAILABLE", "no-model-step") and engine.expected_engine(s) == "rules"
    assert engine.start_line(s) == f"engine=rules state=UNAVAILABLE model={MODEL_NAME} host=public reason=no-model-step"
    status = engine.EngineState(s).status()
    assert status["engine"] == "rules" and status["model"] == {
        "configured": True, "state": "UNAVAILABLE", "reason": "no-model-step", "name": MODEL_NAME, "host": "public", "key": "file",
        "conversions": ZERO}
    for text, where in ((repr(s), "repr(Settings)"), (repr(cfg), "repr(ModelConfig)"), (engine.start_line(s), "start line"),
                        (repr(status), "status")):
        assert_nothing_secret(text, where)


def test_the_key_variable_is_seen_as_present_and_its_value_is_never_stored(tmp_path):
    env = {k: v for k, v in model_env(tmp_path).items() if k != "MODEL_API_KEY_FILE"}
    s = Settings.from_env(env)
    assert s.model_api_key_set is True and engine.model_config(s).key == "variable"
    assert not hasattr(s, "model_api_key") and KEY_VALUE not in repr(s) and KEY_VALUE not in repr(vars(s))
    assert Settings.from_env({"MODEL_API_KEY_SET": "true"}).model_api_key_set is False   # only MODEL_API_KEY counts
    assert engine.model_config(Settings.from_env({"MODEL_BASE_URL": "http://ollama:11434/v1"})).key == "none"


def test_model_step_off_wins_over_a_configured_model_and_other_values_are_refused(tmp_path):
    s = Settings.from_env({**model_env(tmp_path), "MODEL_STEP": "off"})
    assert engine.model_state(s) == ("OFF", "MODEL_STEP=off") and engine.model_config(s).configured is False
    assert engine.EngineState(s).status()["model"] == {
        "configured": False, "state": "OFF", "reason": "MODEL_STEP=off", "name": MODEL_NAME, "host": "public", "key": "file",
        "conversions": ZERO}
    with pytest.raises(ConfigError, match="MODEL_STEP must be one of auto, off"):
        Settings.from_env({"MODEL_STEP": "on"})


def test_a_model_name_is_cleaned_to_a_safe_token():
    s = Settings.from_env({"MODEL_BASE_URL": "http://ollama:11434/v1", "MODEL_NAME": "qwen3:14b\r\nX-Evil: 1 <b>"})
    assert engine.model_config(s).name == "qwen3:14bX-Evil:1b"


def test_the_record_counts_conversions_by_engine_and_remembers_the_last():
    state = engine.EngineState(Settings.from_env({"MODEL_BASE_URL": "http://ollama:11434/v1"}))
    assert state.record({"warnings": []}) == "rules"
    assert state.record({"warnings": [{"code": "MODEL_USED"}]}) == "rules+model"
    assert state.record({"warnings": [{"code": "MODEL_FALLBACK"}]}) == "rules-fallback"
    assert state.status()["engine"] == "rules-fallback"
    assert state.status()["model"]["conversions"] == {"rules": 1, "rules+model": 1, "rules-fallback": 1}
    assert state.status()["model"]["name"] is None and state.status()["model"]["key"] == "none"   # unnamed, no key: said so
    assert engine.cli_line("rules") == "ENGINE: rules"


# ---- the shell: header, batch line, /status, log ----------------------------------------------------------------

def make(**over) -> TestClient:
    env = {"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000", **over}
    return TestClient(create_app(Settings.from_env(env)))


def post(client: TestClient, path: str = "/v1/forms/convert"):
    return client.post(path, files={"file": ("a.pdf", fx.pdf(), "application/pdf")})


def batch(client: TestClient):
    body, ctype = fx.multipart([("file", "a.pdf", fx.pdf(), "application/pdf"), ("file", "b.docx", fx.docx(), "application/zip"),
                                ("file", "c.pdf", bytes(3) + b"junk", "application/pdf")])
    return client.post("/v1/batches", content=body, headers={"Content-Type": ctype})


def model_step_says(monkeypatch, code: str) -> None:
    """What WP-H1 will do inside the pipeline: one warning in the sidecar. Nothing of the shell is touched."""
    real = pipeline.run_limited

    def run_limited(*a, **kw):
        result = real(*a, **kw)
        result.sidecar.setdefault("warnings", []).append({"code": code})
        return result

    monkeypatch.setattr(pipeline, "run_limited", run_limited)


def test_every_conversion_answer_carries_the_engine_header():
    client = make()
    for path in ("/v1/forms/convert", "/v1/forms/convert?report=1", "/v1/forms/report"):
        r = post(client, path)
        assert r.status_code == 200 and r.headers["X-Converter-Engine"] == "rules", path


def test_every_batch_line_of_a_converted_file_names_the_engine():
    lines = [json.loads(x) for x in batch(make()).text.splitlines()]
    assert [x["state"] for x in lines] == ["ok", "ok", "error"]
    assert [x.get("engine") for x in lines] == ["rules", "rules", None]   # a refused file ran on no engine


def test_a_refusal_carries_no_engine_header():
    r = make().post("/v1/forms/convert", files={"file": ("a.pdf", bytes(3) + b"junk", "application/pdf")})
    assert r.status_code == 415 and "X-Converter-Engine" not in r.headers


@pytest.mark.parametrize("code, expected", [("MODEL_USED", "rules+model"), ("MODEL_FALLBACK", "rules-fallback"),
                                            ("MODEL_SKIPPED", "rules")])
def test_the_shell_follows_a_model_step_without_being_changed(monkeypatch, caplog, code, expected):
    model_step_says(monkeypatch, code)
    client = make(MODEL_BASE_URL="http://ollama:11434/v1", MODEL_NAME="open-model")
    with caplog.at_level(logging.INFO, logger="converter"):
        r = post(client)
    assert r.status_code == 200 and r.headers["X-Converter-Engine"] == expected
    assert code in r.headers["X-Converter-Warnings"]
    assert f"stage=convert result=ok job=" in caplog.text and f" engine={expected}" in caplog.text
    assert [x.get("engine") for x in map(json.loads, batch(client).text.splitlines())] == [expected, expected, None]
    status = client.get("/status").json()
    assert status["engine"] == expected and status["model"]["conversions"][expected] == 3


def test_status_with_no_model_configured_is_byte_for_byte_what_it_was():
    """The first-run check of the image (`tools/ci/first_run.py`) fixes the six keys; main 9e095ab answered exactly
    this body. The engine is in it already: `"engine":"rules"`."""
    from app import readers

    client = make()
    s = Settings.from_env({"AUTH_MODE": "off"})
    before = client.get("/status")
    expected = {"service": "Konwerter formularzy", "version": __version__, "engine": "rules", "auth": "off",
                "formats": readers.formats(),
                "limits": {"job_timeout_s": s.job_timeout_s, "concurrency": s.concurrency, "max_pages": s.max_pages,
                           "max_upload_bytes": s.max_upload_bytes}}
    assert before.content == json.dumps(expected, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert post(client).status_code == 200
    assert client.get("/status").content == before.content   # and a conversion on the rules changes nothing in it
    assert make(MODEL_STEP="off").get("/status").content == before.content


def test_status_names_a_configured_model_and_counts_its_conversions():
    client = make(MODEL_BASE_URL="http://localhost:11434/v1", MODEL_NAME="qwen3:14b")
    body = client.get("/status").json()
    assert set(body) == {"service", "version", "engine", "model", "auth", "formats", "limits"}
    assert body["engine"] == "rules" and body["model"] == {
        "configured": True, "state": "UNAVAILABLE", "reason": "no-model-step", "name": "qwen3:14b", "host": "loopback",
        "key": "none", "conversions": ZERO}
    assert post(client).status_code == 200
    assert client.get("/status").json()["model"]["conversions"] == {**ZERO, "rules": 1}


def test_healthz_is_unchanged_byte_for_byte(tmp_path):
    expected = ('{"status":"ok","version":"' + __version__ + '"}').encode()
    for client in (make(), make(**model_env(tmp_path)), make(MODEL_STEP="off")):
        r = client.get("/healthz")
        assert r.status_code == 200 and r.content == expected and r.headers["content-type"] == "application/json"
        assert "X-Converter-Engine" not in r.headers


def test_the_log_names_the_engine_at_start_and_for_every_conversion(caplog):
    with caplog.at_level(logging.INFO, logger="converter"):
        client = make()
        assert post(client).status_code == 200
    lines = caplog.text.splitlines()
    assert sum("engine=rules state=OFF reason=not-configured" in x for x in lines) == 1
    done = [x for x in lines if "stage=convert result=ok" in x]
    assert len(done) == 1 and done[0].endswith(" engine=rules")


# ---- a configured model: reported, unused, and nothing secret anywhere ------------------------------------------

def test_a_configured_model_changes_no_byte_of_the_form_or_the_sidecar(tmp_path):
    plain, configured = make(), make(**model_env(tmp_path))
    for path in ("/v1/forms/convert", "/v1/forms/report"):
        a, b = post(plain, path), post(configured, path)
        assert a.status_code == b.status_code == 200 and a.content == b.content, path
        assert a.headers["X-Form-SHA256"] == b.headers["X-Form-SHA256"]
        assert a.headers["X-Converter-Engine"] == b.headers["X-Converter-Engine"] == "rules"


def test_nothing_of_the_model_configuration_but_name_and_host_class_leaves_the_service(tmp_path, caplog, monkeypatch):
    import socket

    def no_network(*a, **kw):
        raise AssertionError("a configured model must not make this build open a connection")

    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(socket, "getaddrinfo", no_network)
    with caplog.at_level(logging.DEBUG):
        client = make(**model_env(tmp_path))
        answers = {
            "/status": client.get("/status"), "/healthz": client.get("/healthz"), "convert": post(client),
            "convert+report": post(client, "/v1/forms/convert?report=1"), "report": post(client, "/v1/forms/report"),
            "batch": batch(client), "refusal": client.post("/v1/forms/convert", files={"file": ("a.pdf", b"\0\0\0junk", "application/pdf")}),
            "not found": client.get("/nope"),
        }
    for where, r in answers.items():
        assert_nothing_secret(r.text, f"body of {where}")
        assert_nothing_secret(repr(sorted(r.headers.items())), f"headers of {where}")
    assert_nothing_secret(caplog.text, "the log")
    status = answers["/status"].json()
    assert status["engine"] == "rules" and status["model"] == {
        "configured": True, "state": "UNAVAILABLE", "reason": "no-model-step", "name": MODEL_NAME, "host": "public", "key": "file",
        "conversions": ZERO}
    assert f"engine=rules state=UNAVAILABLE model={MODEL_NAME} host=public reason=no-model-step" in caplog.text


# ---- the command line -------------------------------------------------------------------------------------------

def test_the_command_line_names_the_engine_on_standard_error_and_never_on_standard_output(tmp_path, capsys, monkeypatch):
    for name in ("MODEL_STEP", "MODEL_BASE_URL", "MODEL_NAME", "MODEL_API_KEY", "MODEL_API_KEY_FILE"):
        monkeypatch.delenv(name, raising=False)
    src = tmp_path / "a.docx"
    src.write_bytes(fx.docx())
    assert cli.main(["convert", str(src)]) == 0
    plain = capsys.readouterr()
    assert plain.err == "ENGINE: rules\n"
    assert set(json.loads(plain.out)) == {"title", "tabs", "flow"} and "ENGINE" not in plain.out

    assert cli.main(["convert", str(src), "--out", str(tmp_path / "form.json"), "--report", str(tmp_path / "rep")]) == 0
    to_file = capsys.readouterr()
    assert to_file.out == "" and to_file.err == "ENGINE: rules\n"
    assert (tmp_path / "form.json").read_text(encoding="utf-8") + "\n" == plain.out

    for name, value in model_env(tmp_path).items():   # a configured model: the same bytes, the same line, no secret
        monkeypatch.setenv(name, value)
    assert cli.main(["convert", str(src), "--report", str(tmp_path / "rep2")]) == 0
    configured = capsys.readouterr()
    assert configured.out == plain.out and configured.err == "ENGINE: rules\n"
    assert (tmp_path / "rep2" / "a.meta.json").read_bytes() == (tmp_path / "rep" / "a.meta.json").read_bytes()
    assert_nothing_secret(configured.out + configured.err + (tmp_path / "rep2" / "a.meta.json").read_text(encoding="utf-8"), "CLI")


def test_a_refused_file_prints_no_engine_line(tmp_path, capsys):
    src = tmp_path / "a.pdf"
    src.write_bytes(bytes(3) + b"spoof")
    assert cli.main(["convert", str(src)]) == 2
    assert "ENGINE" not in capsys.readouterr().err


# ---- the warning codes ------------------------------------------------------------------------------------------

def test_the_three_model_codes_are_in_the_list_and_nothing_emits_them_yet():
    from typing import get_args

    from app.model.common import WarningCode

    assert {"MODEL_USED", "MODEL_FALLBACK", "MODEL_SKIPPED"} <= set(get_args(WarningCode))
    sidecar = pipeline.run(fx.pdf(), "a.pdf", Settings.from_env({"AUTH_MODE": "off"})).sidecar
    assert not [w for w in sidecar.get("warnings", []) if str(w.get("code", "")).startswith("MODEL_")]
