"""The engine state (WP-H4): which engine a conversion ran on, and what is said about the model.

Three engines, and nothing else is ever shown:

    rules           the rules alone
    rules+model     the rules, then the model step changed or confirmed something
    rules-fallback  the model step was tried and failed; the output is the output of the rules

This build has NO model step. A conversion therefore always runs on `rules`, with or without a model configured;
a configured model is reported as configured and unused. The shell (HTTP, command line, log) asks this module
and prints the answer, so the package that adds the step (WP-H1) changes this file and the pipeline, not the shell:

- the engine of one conversion is read from the warnings of its sidecar (`engine_of`): H1 emits `MODEL_USED`,
  `MODEL_FALLBACK` or `MODEL_SKIPPED` there, and the header, the log line and the page follow;
- the state of the model (`model_state`) is decided here; H1 sets `MODEL_STEP_BUILT` and refines the rule.

Nothing here reads a key, opens a file, resolves a name or opens a socket. Of the configuration only two things
ever leave: the model's name (cleaned) and the CLASS of its host. Never the URL, its user, password, port, path or
query, never the path of the key file, never the key.
"""
from __future__ import annotations

import ipaddress
import re
import threading
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

RULES, RULES_MODEL, RULES_FALLBACK = "rules", "rules+model", "rules-fallback"
ENGINES = (RULES, RULES_MODEL, RULES_FALLBACK)
HEADER = "X-Converter-Engine"

# WP-H1 sets this to True in the commit that adds the model step. While it is False nothing is ever called.
MODEL_STEP_BUILT = False

_PRIVATE_SUFFIXES = (".local", ".internal", ".lan", ".home", ".localhost")


def engine_of(sidecar: Any) -> str:
    """The engine one finished conversion ran on, from the warning codes of its sidecar. A fallback wins over a
    use: the stronger claim (`rules+model`) is never made for a conversion in which the step also failed."""
    found = sidecar.get("warnings") if isinstance(sidecar, dict) else None
    codes = {w.get("code") for w in found if isinstance(w, dict)} if isinstance(found, list) else set()
    if "MODEL_FALLBACK" in codes:
        return RULES_FALLBACK
    if "MODEL_USED" in codes:
        return RULES_MODEL
    return RULES


def host_class(url: str) -> str:
    """`loopback`, `private`, `public` or `invalid`, from the shape of the host alone: the name is never resolved,
    so a dotted name counts as public whatever it points at."""
    try:
        host = (urlsplit(url.strip()).hostname or "").lower().rstrip(".")
    except ValueError:
        return "invalid"
    if not host:
        return "invalid"
    if host == "localhost":
        return "loopback"
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return "private" if "." not in host or host.endswith(_PRIVATE_SUFFIXES) else "public"
    if ip.is_loopback:
        return "loopback"
    return "private" if (ip.is_private or ip.is_link_local) else "public"


def _clean_name(name: str) -> str:
    """A model name as an ASCII token that is safe in a header and a log line; anything else is dropped."""
    return re.sub(r"[^A-Za-z0-9._:/+-]", "", name)[:80]


@dataclass(frozen=True)
class ModelConfig:
    """What the settings say about the model, already reduced to what may be shown."""

    step: str          # auto | off
    configured: bool   # a base URL is named and the step is not switched off
    name: str          # cleaned model name, "" when none is given
    host: str          # host class of the base URL, "" when none is given
    key: str           # where a key would come from: file | variable | none. Never the key, never the path.


def model_config(s: Any) -> ModelConfig:
    url = (getattr(s, "model_base_url", "") or "").strip()
    step = getattr(s, "model_step", "off")
    key = "file" if getattr(s, "model_api_key_file", "") else "variable" if getattr(s, "model_api_key_set", False) else "none"
    return ModelConfig(step=step, configured=bool(url) and step != "off", name=_clean_name(getattr(s, "model_name", "") or ""),
                       host=host_class(url) if url else "", key=key)


def model_state(s: Any) -> tuple[str, str]:
    """(state, reason). OFF: switched off or nothing configured. UNAVAILABLE: configured and not usable; in this
    build always, because there is no model step. ON is reached only once WP-H1 has built the step."""
    cfg = model_config(s)
    if cfg.step == "off":
        return "OFF", "MODEL_STEP=off"
    if not cfg.configured:
        return "OFF", "not-configured"
    if not MODEL_STEP_BUILT:
        return "UNAVAILABLE", "no-model-step"
    return "ON", "configured"


def expected_engine(s: Any) -> str:
    """The engine the next conversion is expected to run on."""
    return RULES_MODEL if model_state(s)[0] == "ON" else RULES


def start_line(s: Any) -> str:
    """One log line at start. Name and host class only."""
    cfg = model_config(s)
    state, reason = model_state(s)
    about = f" model={cfg.name or 'unnamed'} host={cfg.host}" if cfg.configured else ""
    return f"engine={expected_engine(s)} state={state}{about} reason={reason}"


def cli_line(engine: str) -> str:
    """The one line the command line prints on standard error after a conversion."""
    return f"ENGINE: {engine}"


class EngineState:
    """The record of one running service: how many conversions ran on which engine, and the last one."""

    def __init__(self, settings: Any) -> None:
        self._s = settings
        self._lock = threading.Lock()
        self._counts = {e: 0 for e in ENGINES}
        self._last: str | None = None

    def record(self, sidecar: Any) -> str:
        """Count one finished conversion and return its engine."""
        engine = engine_of(sidecar)
        with self._lock:
            self._counts[engine] += 1
            self._last = engine
        return engine

    def status(self) -> dict[str, Any]:
        """The part of `GET /status` about the engine. `engine` is the engine of the last conversion; before the
        first one, the engine the next conversion is expected to run on."""
        cfg = model_config(self._s)
        state, reason = model_state(self._s)
        with self._lock:
            counts, last = dict(self._counts), self._last
        model: dict[str, Any] = {"configured": cfg.configured, "state": state, "reason": reason}
        if cfg.configured:
            model.update(name=cfg.name or None, host=cfg.host, key=cfg.key)
        return {"engine": last or expected_engine(self._s), "engine_counts": counts, "model": model}
