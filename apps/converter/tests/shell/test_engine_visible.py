"""WP-H4: the engine is always visible. The state module, the header, /status, the log, the command line, and the
proof that nothing of the model's configuration but its name and host class ever leaves."""
from __future__ import annotations

import pytest

from app import engine
from app.config import ConfigError, Settings

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
    assert engine.EngineState(s).status() == {
        "engine": "rules", "engine_counts": {"rules": 0, "rules+model": 0, "rules-fallback": 0},
        "model": {"configured": False, "state": "OFF", "reason": "not-configured"}}


def test_a_configured_model_is_reported_by_name_and_host_class_and_is_not_used(tmp_path):
    s = Settings.from_env(model_env(tmp_path))
    cfg = engine.model_config(s)
    assert cfg == engine.ModelConfig(step="auto", configured=True, name=MODEL_NAME, host="public", key="file")
    assert engine.model_state(s) == ("UNAVAILABLE", "no-model-step") and engine.expected_engine(s) == "rules"
    assert engine.start_line(s) == f"engine=rules state=UNAVAILABLE model={MODEL_NAME} host=public reason=no-model-step"
    status = engine.EngineState(s).status()
    assert status["engine"] == "rules" and status["model"] == {
        "configured": True, "state": "UNAVAILABLE", "reason": "no-model-step", "name": MODEL_NAME, "host": "public", "key": "file"}
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
    assert engine.EngineState(s).status()["model"] == {"configured": False, "state": "OFF", "reason": "MODEL_STEP=off"}
    with pytest.raises(ConfigError, match="MODEL_STEP must be one of auto, off"):
        Settings.from_env({"MODEL_STEP": "on"})


def test_a_model_name_is_cleaned_to_a_safe_token():
    s = Settings.from_env({"MODEL_BASE_URL": "http://ollama:11434/v1", "MODEL_NAME": "qwen3:14b\r\nX-Evil: 1 <b>"})
    assert engine.model_config(s).name == "qwen3:14bX-Evil:1b"


def test_the_record_counts_conversions_by_engine_and_remembers_the_last():
    state = engine.EngineState(Settings.from_env({}))
    assert state.record({"warnings": []}) == "rules"
    assert state.record({"warnings": [{"code": "MODEL_USED"}]}) == "rules+model"
    assert state.record({"warnings": [{"code": "MODEL_FALLBACK"}]}) == "rules-fallback"
    assert state.status()["engine"] == "rules-fallback"
    assert state.status()["engine_counts"] == {"rules": 1, "rules+model": 1, "rules-fallback": 1}
    assert engine.cli_line("rules") == "ENGINE: rules"
