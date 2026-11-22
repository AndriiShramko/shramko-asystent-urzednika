"""The model settings a person types on the review page (wave 11, KEY), the connection check, and the three
endpoints the page block "Model AI (opcjonalnie)" talks to.

What is kept and where
  The settings of the environment (VISION_BASE_URL, VISION_API_KEY_FILE or VISION_API_KEY, VISION_MODEL) are read
  as before. On top of them ONE override may be held in the memory of this process: an address, a model name and a
  key typed on the page. It is never written to a file, a log line, an exception text or an answer; a restart of
  the service forgets it. With nothing typed `apply` returns the configuration unchanged, so a service with
  nothing configured behaves byte for byte as before this module existed.

What never leaves
  No answer of this module holds a key. `GET /v1/model` gives at most the last four characters of a key of sixteen
  or more (enough to recognise which key is in use, useless to spend it), and only to a caller who may convert.
  A full key is never returned: this service does not know who asks from inside a container (every client arrives
  through the bridge address), so "only on this computer" cannot be checked here.

A key belongs to its address
  The key of the environment is sent only to the address of the environment. A request that names another address
  must bring its own key (`key_needed`); otherwise anybody could ask the service to post the operator's key to a
  server of their choice.

Who may change
  The same callers who may convert (`authorize`, scope `convert`): with tokens on, a token; with tokens off the
  service is for local work, as its start-up warning says. `VISION_PAGE_CONFIG=off` forbids changes from the page
  altogether; `VISION_MODE=off` or `MODEL_STEP=off` keeps the step off whatever is typed.

Endpoints (all JSON; no key in any answer)
  GET    /v1/model           state (off | on | fallback | disabled), where the settings come from, model name
  PUT    /v1/model/session   {base_url?, model?, key?}: use these until restart; answers like GET
  DELETE /v1/model/session   forget them; back to the environment
  POST   /v1/model/check     {base_url?, model?, key?} or {}: ONE small call; {ok, code, http, ms, message}
"""
from __future__ import annotations

import http.client
import json
import logging
import os
import re
import threading
import time
import urllib.parse
from dataclasses import replace
from typing import Any, Callable, Mapping

log = logging.getLogger("converter")

MAX_BODY = 8192
TAIL = 4
TAIL_MIN_KEY = 16
CHECK_CONNECT_S = 3.0
CHECK_READ_S = 20.0
_MODEL_RE = re.compile(r"[A-Za-z0-9._:/+@-]{1,120}")
_KEY_RE = re.compile(r"[\x21-\x7e]{1,512}")

_LOCK = threading.Lock()
_OVERRIDE: dict[str, str] | None = None      # {"base_url", "model", "key"}; memory only
_CHECK_LOCK = threading.Lock()               # one connection check at a time

STILL_WORKS = "Konwersja działa dalej bez modelu."
# code -> what is wrong and what to do, in plain Polish. The page has the same sentences in its dictionaries; these
# are for a person who calls the endpoint by hand.
MESSAGES = {
    "ok": "Połączenie działa: model odpowiedział.",
    "bad_key": "Serwer modelu odrzucił klucz. Wpisz poprawny klucz i sprawdź ponownie.",
    "no_credit": "Na koncie tego klucza skończyły się środki. Doładuj konto albo wpisz inny klucz.",
    "rate_limit": "Przekroczono limit zapytań lub środków dla tego klucza. Poczekaj kilka minut albo wpisz inny klucz.",
    "unreachable": "Nie udało się połączyć z serwerem modelu. Sprawdź adres i dostęp usługi do sieci.",
    "timeout": "Serwer modelu nie odpowiedział na czas. Spróbuj ponownie za chwilę albo wskaż inny serwer.",
    "model_not_found": "Serwer nie zna modelu o tej nazwie. Popraw nazwę modelu na taką, jaką podaje serwer.",
    "not_api": "Pod tym adresem nie odpowiada API zgodne z OpenAI. Sprawdź adres (zwykle kończy się na /v1).",
    "server_error": "Serwer modelu zgłosił własny błąd. Spróbuj ponownie później.",
    "bad_url": "Adres serwera modelu musi zaczynać się od http:// lub https:// i nie może zawierać hasła.",
    "bad_model": "Nazwa modelu zawiera niedozwolone znaki albo jest za długa.",
    "bad_key_form": "Klucz zawiera niedozwolone znaki (na przykład spacje) albo jest za długi.",
    "key_needed": "Dla innego adresu wpisz też klucz: klucz serwera jest wysyłany tylko pod adres ustawiony na serwerze.",
    "not_configured": "Nie ma czego sprawdzać: wpisz adres serwera modelu i klucz.",
    "locked": "Operator usługi wyłączył zmianę ustawień modelu z tej strony.",
    "disabled": "Operator usługi wyłączył krok modelu; na tej stronie nie można go włączyć.",
    "busy": "Trwa inne sprawdzenie połączenia. Spróbuj za chwilę.",
    "bad_request": "Treść żądania nie jest poprawnym obiektem JSON z polami base_url, model, key.",
}


def message(code: str) -> str:
    text = MESSAGES.get(code, MESSAGES["server_error"])
    return text if code == "ok" else f"{text} {STILL_WORKS}"


# ---- the override ---------------------------------------------------------------------------------------------------

def apply(cfg):
    """The configuration of the environment with the page's override on top. A step switched off by the operator
    (mode off) stays off. Called by `VisionConfig.from_env()` for the process environment only."""
    with _LOCK:
        o = dict(_OVERRIDE) if _OVERRIDE else None
    if o is None or cfg.mode == "off":
        return cfg
    return replace(cfg, base_url=o["base_url"], model=o["model"], key=o["key"])


def active() -> bool:
    with _LOCK:
        return _OVERRIDE is not None


def clear() -> None:
    global _OVERRIDE
    with _LOCK:
        had = _OVERRIDE is not None
        _OVERRIDE = None
    if had:
        _fresh_start()
        log.info("stage=model-config result=cleared source=environment")


def page_config_allowed(env: Mapping[str, str] | None = None) -> bool:
    env = os.environ if env is None else env
    return (env.get("VISION_PAGE_CONFIG") or "on").strip().lower() != "off"


def _fresh_start() -> None:
    """New settings deserve a new try: the breaker closes, answers of the old server are dropped, the state is
    "no call yet"."""
    from app import vision

    vision.BREAKER.ok()
    vision.CACHE = vision.Cache()
    vision._set_state("OFF", "", "")


def _env_cfg():
    from app.vision import VisionConfig

    return VisionConfig.from_env(dict(os.environ))   # an explicit mapping: the environment alone, no override


def clean_url(raw: str) -> str | None:
    """A base URL we accept: http or https, a host, no user or password, no fragment; at most 300 characters."""
    url = (raw or "").strip().rstrip("/")
    if not url or len(url) > 300 or any(ch.isspace() or ord(ch) < 0x21 or ord(ch) > 0x7e for ch in url):
        return None
    try:
        u = urllib.parse.urlsplit(url)
        _ = u.port
    except ValueError:
        return None
    if u.scheme not in ("http", "https") or not u.hostname or u.username or u.password or u.fragment:
        return None
    return url


def shown_address(url: str) -> str:
    """scheme://host[:port]/path, never a user, a password or a query."""
    try:
        u = urllib.parse.urlsplit(url)
        port = f":{u.port}" if u.port else ""
        return f"{u.scheme}://{u.hostname}{port}{u.path}"[:200]
    except ValueError:
        return ""


def merge(body: Mapping[str, Any], base=None) -> tuple[dict[str, str] | None, str]:
    """What the caller typed, completed from the settings in use (`base`: the environment, or the override when
    one is held): ({base_url, model, key}, "") or (None, code). A key is completed only for the address it belongs
    to: the same address as in `base`."""
    from app.vision import DEFAULT_MODEL

    base = base or apply(_env_cfg())
    for name in ("base_url", "model", "key"):
        if name in body and body[name] is not None and not isinstance(body[name], str):
            return None, "bad_request"
    raw_url, raw_model, raw_key = (str(body.get(k) or "").strip() for k in ("base_url", "model", "key"))
    url = clean_url(raw_url) if raw_url else base.base_url
    if raw_url and url is None:
        return None, "bad_url"
    if raw_model and not _MODEL_RE.fullmatch(raw_model):
        return None, "bad_model"
    if raw_key and not _KEY_RE.fullmatch(raw_key):
        return None, "bad_key_form"
    model = raw_model or base.model or DEFAULT_MODEL
    if not url:
        return None, "not_configured"
    key = raw_key
    if not key:
        if not base.key:
            return None, "not_configured"
        if url != base.base_url:
            return None, "key_needed"
        key = base.key
    return {"base_url": url, "model": model, "key": key}, ""


def set_override(body: Mapping[str, Any]) -> str:
    """Keep what the page sent, in memory. Returns "" or the code of the refusal."""
    global _OVERRIDE
    env_cfg = _env_cfg()
    if env_cfg.mode == "off":
        return "disabled"
    merged, code = merge(body, apply(env_cfg))
    if merged is None:
        return code
    with _LOCK:
        _OVERRIDE = merged
    _fresh_start()
    from app.engine import host_class

    log.info("stage=model-config result=set source=session host=%s", host_class(merged["base_url"]))
    return ""


# ---- what a failure means --------------------------------------------------------------------------------------------

def problem_of(reason: str) -> str:
    """A short reason of the step (`VisionError.reason`, kept in the state) -> the code of MESSAGES."""
    r = reason or ""
    if r in ("http_401", "http_403"):
        return "bad_key"
    if r == "http_402":
        return "no_credit"
    if r == "http_429":
        return "rate_limit"
    if r in ("http_404", "model_not_found"):
        return "model_not_found"
    if r in ("connect", "network"):
        return "unreachable"
    if r in ("timeout", "deadline"):
        return "timeout"
    if r in ("bad_url",):
        return "bad_url"
    if r in ("not_json", "not_api"):
        return "not_api"
    return "server_error"   # http_5xx, breaker_open, bad_answer, cut_*, fewer_places, gate: the server or its answer


def _names_model(raw: bytes) -> bool:
    """Does an error body speak about the model? Read only to choose between two sentences; never returned."""
    text = raw[:4000].decode("utf-8", "replace").lower()
    return "model" in text


def probe(settings: Mapping[str, str], post: Callable[..., tuple[int, bytes]] | None = None) -> dict:
    """ONE small call (`max_tokens` 4) to `{base_url}/chat/completions`. Answers {ok, code, http, ms}; never raises,
    never returns or logs a body, a URL or a key."""
    t0 = time.perf_counter()
    http_status: int | None = None
    try:
        http_status, raw = (post or _post)(settings)
        if http_status == 200:
            try:
                data = json.loads(raw.decode("utf-8"))
                ok = isinstance(data, dict) and isinstance(data.get("choices"), list) and bool(data["choices"])
            except ValueError:
                ok = False
            code = "ok" if ok else "not_api"
        elif http_status in (401, 403):
            code = "bad_key"
        elif http_status == 402:
            code = "no_credit"
        elif http_status == 429:
            code = "rate_limit"
        elif http_status in (400, 404, 422):
            code = "model_not_found" if _names_model(raw) else ("not_api" if http_status == 404 else "server_error")
        elif http_status in (301, 302, 303, 307, 308, 405):
            code = "not_api"
        else:
            code = "server_error"
    except _Probe as exc:
        code = exc.code
    except Exception:   # noqa: BLE001 - a check never fails the request and never leaks the text of an exception
        code = "server_error"
    return {"ok": code == "ok", "code": code, "http": http_status, "ms": int((time.perf_counter() - t0) * 1000)}


class _Probe(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _post(settings: Mapping[str, str]) -> tuple[int, bytes]:
    u = urllib.parse.urlsplit(settings["base_url"] + "/chat/completions")
    if u.scheme not in ("http", "https") or not u.hostname:
        raise _Probe("bad_url")
    conn_cls = http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection
    conn = conn_cls(u.hostname, u.port, timeout=CHECK_CONNECT_S)
    try:
        try:
            conn.connect()
        except TimeoutError:
            raise _Probe("unreachable") from None
        except OSError:
            raise _Probe("unreachable") from None
        conn.sock.settimeout(CHECK_READ_S)
        payload = json.dumps({"model": settings["model"], "temperature": 0, "max_tokens": 4,
                              "messages": [{"role": "user", "content": "Odpowiedz jednym słowem: OK"}]}).encode("utf-8")
        try:
            conn.request("POST", u.path + (("?" + u.query) if u.query else ""), body=payload, headers={
                "Content-Type": "application/json", "Authorization": "Bearer " + settings["key"]})
            resp = conn.getresponse()
            return resp.status, resp.read(200_000)
        except TimeoutError:
            raise _Probe("timeout") from None
        except OSError:
            raise _Probe("unreachable") from None
    finally:
        conn.close()


# ---- the public state ------------------------------------------------------------------------------------------------

def public_state(authorized: bool) -> dict:
    """For the page: no key, ever. The address and the tail of the key only for a caller who may convert."""
    from app import vision
    from app.engine import host_class

    env_cfg = _env_cfg()
    cfg = apply(env_cfg)
    session = active() and env_cfg.mode != "off"
    out: dict[str, Any] = {"page_config": page_config_allowed() and env_cfg.mode != "off"}
    if env_cfg.mode == "off":
        out.update(state="disabled", source="none")
        return out
    if not cfg.configured:
        out.update(state="off", source="none")
        return out
    st = vision.status(cfg)
    out.update(state="fallback" if st["state"] == "FALLBACK" else "on",
               source="session" if session else "environment", model=engine_name(cfg.model),
               host=host_class(cfg.base_url), used=st.get("calls") != "none yet")
    if st.get("reason"):
        out["reason"] = str(st["reason"])[:40]
        out["problem"] = problem_of(str(st["reason"]))
    key_origin = "session" if session and cfg.key != env_cfg.key else (
        "environment-file" if (os.environ.get("VISION_API_KEY_FILE") or "").strip() else "environment-variable")
    key: dict[str, Any] = {"set": True, "origin": key_origin}
    if authorized:
        out["address"] = shown_address(cfg.base_url)
        if len(cfg.key) >= TAIL_MIN_KEY:
            key["tail"] = cfg.key[-TAIL:]
    out["key"] = key
    return out


def engine_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._:/+@-]", "", name)[:120]
