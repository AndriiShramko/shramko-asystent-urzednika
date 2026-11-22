"""The routes of the page block "Model AI (opcjonalnie)" (wave 11, KEY). The rules are in `app.vision.session`;
this file only speaks HTTP. No answer holds a key."""
from __future__ import annotations

import json
import logging
from typing import Any, Callable

from fastapi import Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.engine import host_class
from app.guard import ProblemError
from app.vision import session
from app.vision.session import message, public_state

log = logging.getLogger("converter")


def mount(app, authorize: Callable[[Any, str], str], auth_enabled: bool) -> None:
    """Adds the four routes. `authorize(request, scope)` is the shell's own check (token, scope, rate limit)."""
    def answer(body: dict, status: int = 200) -> JSONResponse:
        return JSONResponse(body, status_code=status, headers={"Cache-Control": "no-store"})

    def refusal(code: str, status: int) -> JSONResponse:
        return answer({"ok": False, "code": code, "message": message(code), "model": public_state(True)}, status)

    async def read_json(request: Request) -> dict | None:
        raw = await request.body()
        if len(raw) > session.MAX_BODY:
            return None
        if not raw.strip():
            return {}
        try:
            body = json.loads(raw.decode("utf-8"))
        except ValueError:
            return None
        return body if isinstance(body, dict) else None

    @app.get("/v1/model", summary="State of the optional open-model step (no key in the answer)")
    async def model_state(request: Request) -> JSONResponse:
        authorized = not auth_enabled
        if auth_enabled:
            try:
                authorize(request, "convert")
                authorized = True
            except ProblemError:
                authorized = False
        return answer(public_state(authorized))

    @app.put("/v1/model/session", summary="Use an address, a model name and a key until restart (memory only)")
    async def model_session(request: Request) -> JSONResponse:
        authorize(request, "convert")
        if not session.page_config_allowed():
            return refusal("locked", 403)
        body = await read_json(request)
        if body is None:
            return refusal("bad_request", 400)
        code = session.set_override(body)
        if code:
            return refusal(code, 403 if code == "disabled" else 400)
        return answer({"ok": True, "code": "ok", "model": public_state(True)})

    @app.delete("/v1/model/session", summary="Forget the settings typed on the page")
    async def model_session_clear(request: Request) -> JSONResponse:
        authorize(request, "convert")
        if not session.page_config_allowed():
            return refusal("locked", 403)
        session.clear()
        return answer({"ok": True, "code": "ok", "model": public_state(True)})

    @app.post("/v1/model/check", summary="One small call to the model server; says in Polish what is wrong")
    async def model_check(request: Request) -> JSONResponse:
        authorize(request, "convert")
        body = await read_json(request)
        if body is None:
            return refusal("bad_request", 400)
        typed = any(str(body.get(k) or "").strip() for k in ("base_url", "model", "key"))
        if typed and not session.page_config_allowed():
            return refusal("locked", 403)
        env_cfg = session._env_cfg()
        if env_cfg.mode == "off":
            return refusal("disabled", 403)
        current = session.apply(env_cfg)
        if typed:
            settings, code = session.merge(body, current)
        elif current.configured:
            settings, code = {"base_url": current.base_url, "model": current.model, "key": current.key}, ""
        else:
            settings, code = None, "not_configured"
        if settings is None:
            return answer({"ok": False, "code": code, "http": None, "ms": 0, "message": message(code)})
        if not session._CHECK_LOCK.acquire(blocking=False):
            return answer({"ok": False, "code": "busy", "http": None, "ms": 0, "message": message("busy")}, 429)
        try:
            result = await run_in_threadpool(session.probe, settings)
        finally:
            session._CHECK_LOCK.release()
        same = (settings["base_url"], settings["model"], settings["key"]) == (current.base_url, current.model, current.key)
        if same and current.configured:
            if result["ok"]:
                session._fresh_start()   # the settings in use answer again: a fallback of before is over
            else:   # the settings in use do not answer: the state says so at once, not only after the next scan
                session.mark_failed(result["code"], current.model)
        log.info("stage=model-check result=%s host=%s", result["code"], host_class(settings["base_url"]))
        return answer({**result, "message": message(result["code"])})
