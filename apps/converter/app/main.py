"""The HTTP shell (design section 3): endpoints, problem answers, token and rate checks, body limit.

Order inside every conversion request: token, scope, rate limit, concurrency, then the body is read (counted),
then the guard, then the pipeline behind `app.pipeline.run`. Nothing here parses a document.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import asyncio
from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response, StreamingResponse
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app import __version__, engine, pipeline, preview
from app.auth import RateLimiter, TokenVerifier, scopes_of
from app.config import Settings
from app.guard import ProblemError, UploadInfo, inspect_upload
from app.guard.checks import EXTENSIONS, check_archive, too_large
from app.readers import formats as reader_formats

log = logging.getLogger("converter")

FRAMING_SLACK = 1 << 20          # multipart framing around the one file part
BATCH_MAX_FILES = 20
BATCH_MAX_FACTOR = 5             # a batch body may be this many times the single-file limit
PROBLEM_JSON = "application/problem+json"
FORM_KEYS = {"title", "tabs", "flow"}  # decision D1: the partner's object and nothing else


def _upload_body(file_schema: dict) -> dict:
    """The body the routes read by hand (`read_parts`), declared for /openapi.json and /docs (audit-8 VC-6, 06-F7)."""
    return {"requestBody": {"required": True, "content": {"multipart/form-data": {"schema": {
        "type": "object", "required": ["file"], "properties": {"file": file_schema}}}}}}


UPLOAD_ONE = _upload_body({"type": "string", "format": "binary", "description": "one blank form"})
UPLOAD_MANY = _upload_body({"type": "array", "items": {"type": "string", "format": "binary"}, "maxItems": BATCH_MAX_FILES,
                            "description": f"up to {BATCH_MAX_FILES} forms, or one .zip holding them"})


def _event(stage: str, result: str, job: str, size: int | None = None, ran_on: str | None = None) -> None:
    """Content-free log line: stage, result code, random job id, a size bucket, and for a finished conversion the
    engine it ran on (`app.engine`). Never a name, text or token."""
    bucket = "n/a" if size is None else f"<=2^{max(size, 1).bit_length()}"
    if ran_on is None:
        log.info("stage=%s result=%s job=%s size=%s", stage, result, job, bucket)
    else:
        log.info("stage=%s result=%s job=%s size=%s engine=%s", stage, result, job, bucket, ran_on)


def problem_response(exc: ProblemError) -> JSONResponse:
    return JSONResponse(exc.body(), status_code=exc.status, media_type=PROBLEM_JSON, headers=exc.headers)


class BodyLimit:
    """Pure ASGI middleware: the declared Content-Length first, then bytes counted as they arrive, so a lying
    header cannot let a large body through and the body is never read to its end once it is over the cap."""

    class _Over(Exception):
        pass

    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        self.app = app
        self.s = settings

    def _cap(self, path: str) -> int:
        factor = BATCH_MAX_FACTOR if path.startswith("/v1/batches") else 1
        return self.s.max_upload_bytes * factor + FRAMING_SLACK

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] not in ("POST", "PUT", "PATCH"):
            await self.app(scope, receive, send)
            return
        cap = self._cap(scope["path"])
        declared = None
        for k, v in scope["headers"]:
            if k == b"content-length":
                try:
                    declared = int(v)
                except ValueError:
                    declared = None
        started = False
        seen = 0

        async def counting_receive() -> Message:
            nonlocal seen
            msg = await receive()
            if msg["type"] == "http.request":
                seen += len(msg.get("body", b""))
                if seen > cap:
                    raise BodyLimit._Over()
            return msg

        async def tracking_send(msg: Message) -> None:
            nonlocal started
            started = started or msg["type"] == "http.response.start"
            await send(msg)

        if declared is not None and declared > cap:
            await problem_response(too_large(self.s))(scope, receive, send)
            return
        try:
            await self.app(scope, counting_receive, tracking_send)
        except BodyLimit._Over:
            if not started:
                await problem_response(too_large(self.s))(scope, receive, send)


def internal_problem(exc: BaseException) -> ProblemError:
    """An exception nobody expected: one log line with the type of the exception and nothing of its text (a message
    may quote the file), and the 500 of the contract. `GATE_FAILED` is the code for "our fault" (D19)."""
    log.error("stage=internal result=%s", type(exc).__name__)
    return ProblemError("GATE_FAILED", "Błąd wewnętrzny usługi.")


class CatchAll:
    """Pure ASGI middleware, the outermost of ours: an unexpected exception becomes the problem answer here, so it
    never reaches the server, which would answer plain text and log a stack trace with the text of the exception."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = False

        async def tracking_send(msg: Message) -> None:
            nonlocal started
            started = started or msg["type"] == "http.response.start"
            await send(msg)

        try:
            await self.app(scope, receive, tracking_send)
        except Exception as exc:  # noqa: BLE001 - the last line of defence: every error is application/problem+json
            problem = internal_problem(exc)
            if not started:   # a stream that has begun cannot change its status; it just ends
                await problem_response(problem)(scope, receive, send)


def create_app(settings: Settings | None = None) -> FastAPI:
    s = settings or Settings.from_env()
    logging.getLogger("converter").setLevel(s.log_level.upper())
    verifier = TokenVerifier(s) if s.auth_enabled else None
    limiter = RateLimiter(s.rate_limit_per_min)
    gate = asyncio.Semaphore(s.concurrency)
    if s.auth_mode == "off":
        log.warning("AUTH_MODE=off: every request is accepted without a token. Local work only.")
    elif not s.auth_enabled:   # AUTH_MODE=auto and no key file
        log.warning("No JWT key configured: the API accepts requests WITHOUT a token. "
                    "For shared networks set AUTH_MODE=jwt and JWT_SECRET_FILE.")
    engine_state = engine.EngineState(s)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        # Which engine runs here: the model's name and host class at most, never a URL or a key. Logged at start-up
        # and not while the app is built, because only then do the log handlers of the server exist.
        log.info(engine.start_line(s))
        yield

    app = FastAPI(title="Konwerter formularzy", version=__version__, lifespan=lifespan)
    app.state.settings = s
    app.add_middleware(BodyLimit, settings=s)
    app.add_middleware(CatchAll)   # added last, so it wraps everything of ours

    @app.exception_handler(ProblemError)
    async def _problem(_: Request, exc: ProblemError) -> JSONResponse:
        return problem_response(exc)

    @app.exception_handler(RequestValidationError)
    async def _invalid(_: Request, exc: RequestValidationError) -> JSONResponse:
        """A parameter of ours with a value of the wrong type (`?report=true`): 400 in the contract's shape, with the
        names of the parameters and never their values."""
        names = sorted({str(e["loc"][-1]) for e in exc.errors() if e.get("loc") and re.fullmatch(r"[a-z_]{1,30}", str(e["loc"][-1]))})
        where = f" ({', '.join(names)})" if names else ""
        return problem_response(ProblemError("BAD_REQUEST", f"Nieprawidłowa wartość parametru żądania{where}."))

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:   # behind CatchAll: only if that is bypassed
        return problem_response(internal_problem(exc))

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Routing errors of the framework (404, 405) in the contract's shape, with a code like every other answer."""
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code)
        if code:
            return problem_response(ProblemError(code, headers=dict(exc.headers or {})))
        body = {"type": "about:blank", "title": str(exc.detail), "status": exc.status_code}
        return JSONResponse(body, status_code=exc.status_code, media_type=PROBLEM_JSON)

    # ---- shared steps ------------------------------------------------------------------------------------------

    def authorize(request: Request, scope: str) -> str:
        """Token, scope and rate limit; returns the subject. With AUTH_MODE=off the subject is `anonymous`."""
        if verifier is None:
            subject = "anonymous"
        else:
            header = request.headers.get("authorization", "")
            scheme, _, token = header.partition(" ")
            claims = verifier.verify(token.strip() if scheme.lower() == "bearer" else None)
            if scope not in scopes_of(claims):
                raise ProblemError("SCOPE", f"Wymagany zakres: {scope}.")
            subject = str(claims.get("sub", "unknown"))
        limiter.check(subject)
        return subject

    async def read_parts(request: Request, many: bool = False) -> list[UploadFile]:
        try:
            form = await request.form(max_files=BATCH_MAX_FILES + 1, max_fields=10)
        except ProblemError:
            raise
        except BodyLimit._Over:
            raise
        except Exception as exc:  # noqa: BLE001 - a malformed multipart body is the client's error
            raise ProblemError("BAD_REQUEST", "Treść żądania nie jest poprawnym multipart/form-data.") from exc
        parts = [p for p in form.getlist("file") if isinstance(p, UploadFile)]
        if not parts or (not many and len(parts) != 1):
            raise ProblemError("BAD_REQUEST", "Oczekiwano dokładnie jednej części o nazwie `file`." if not many
                               else "Oczekiwano części `file`.")
        return parts

    def run_one(name: str | None, data: bytes, declared: str | None) -> tuple[UploadInfo, pipeline.PipelineResult, int]:
        t0 = time.perf_counter()
        info = inspect_upload(name, data, s, declared)
        result = pipeline.run_limited(data, info.name, s, **({"notes": info.warnings} if info.warnings else {}))
        if set(result.form) != FORM_KEYS:  # the shell's own gate; the full gate (WP-F14) comes behind the pipeline
            raise ProblemError("GATE_FAILED", "Wynik ma klucze inne niż title, tabs, flow.")
        return info, result, int((time.perf_counter() - t0) * 1000)

    async def convert_request(request: Request, scope: str) -> tuple[UploadInfo, pipeline.PipelineResult, int, str]:
        job = uuid.uuid4().hex[:12]
        authorize(request, scope)
        # The body is read before a slot is taken: a slow upload must not hold a processing slot (audit-8 VC-10,
        # 06-F4); BodyLimit caps what is read.
        part = (await read_parts(request))[0]
        data = await part.read()
        await part.close()
        if gate.locked():
            raise ProblemError("BUSY", "Wszystkie stanowiska przetwarzania są zajęte.", headers={"Retry-After": "5"})
        async with gate:
            try:
                info, result, ms = await run_in_threadpool(run_one, part.filename, data, part.content_type)
            except ProblemError as exc:
                _event("convert", exc.code, job, len(data))
                raise
        _event("convert", "ok", job, info.size, engine_state.record(result.sidecar))
        return info, result, ms, job

    def canonical(obj: dict) -> bytes:
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def warnings_header(result: pipeline.PipelineResult) -> str:
        """D19: `3; GATE_G8, INPUT_NOTE`: the count and the distinct codes, ASCII, cut at 200 characters."""
        found = result.sidecar.get("warnings", []) if isinstance(result.sidecar, dict) else []
        codes: list[str] = []
        for w in found:
            code = re.sub(r"[^A-Za-z0-9_.-]", "", str(w.get("code", ""))) if isinstance(w, dict) else ""
            if code and code not in codes:
                codes.append(code)
        text = f"{len(found)}; "
        shown = 0
        for code in codes:
            nxt = text + (", " if shown else "") + code
            if len(nxt) > 200:
                text += ", ..." if shown else "..."
                break
            text, shown = nxt, shown + 1
        return text.rstrip("; ") if not shown and not codes else text

    def headers_for(info: UploadInfo, body: bytes, ms: int, result: pipeline.PipelineResult | None = None) -> dict[str, str]:
        extra = {}
        if result is not None and isinstance(result.sidecar, dict) and result.sidecar.get("warnings"):
            extra["X-Converter-Warnings"] = warnings_header(result)
        return {**extra,
            engine.HEADER: engine.engine_of(result.sidecar if result is not None else None),
            "X-Input-SHA256": info.sha256,
            "X-Form-SHA256": hashlib.sha256(body).hexdigest(),
            "X-Converter-Version": __version__,
            "Server-Timing": f"total;dur={ms}",
        }

    # ---- endpoints ---------------------------------------------------------------------------------------------

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "ok", "version": __version__}

    @app.get("/status")
    async def status() -> dict:
        """What runs here, for a person or a script before the first upload. No token, like `/healthz`, and so
        nothing that needs one: no secret, no path, no key material; the name, the version and the limits in force.
        `engine` comes from `app.engine`; so does the key `model`, present only when a model is configured, and
        then with its name and the class of its host at most. With no model configured the six keys are fixed."""
        body = {
            "service": app.title,
            "version": __version__,
            **engine_state.status(),
            "auth": "jwt" if s.auth_enabled else "off",
            "formats": reader_formats(),
            "limits": {"job_timeout_s": s.job_timeout_s, "concurrency": s.concurrency, "max_pages": s.max_pages,
                       "max_upload_bytes": s.max_upload_bytes},
        }
        if pipeline.vision_on(s):   # ORDER M2 P1, weak image page reader: ON or FALLBACK{reason} and the model name
            from app import vision

            body["vision"] = vision.status()
        return body

    @app.post("/v1/forms/convert", openapi_extra=UPLOAD_ONE)
    async def convert(request: Request, report: int = 0) -> Response:
        info, result, ms, _ = await convert_request(request, "convert")
        form_body = canonical(result.form)
        headers = headers_for(info, form_body, ms, result)
        if not report:
            return Response(form_body, media_type="application/json", headers=headers)
        meta_body = canonical(result.sidecar)
        boundary = "formularze-" + headers["X-Form-SHA256"][:24]
        out = b""
        for name, payload in (("form.json", form_body), ("meta.json", meta_body)):
            out += (f"--{boundary}\r\nContent-Type: application/json\r\n"
                    f'Content-Disposition: attachment; filename="{name}"\r\n\r\n').encode() + payload + b"\r\n"
        out += f"--{boundary}--\r\n".encode()
        return Response(out, media_type=f"multipart/mixed; boundary={boundary}", headers=headers)

    @app.post("/v1/forms/report", openapi_extra=UPLOAD_ONE)
    async def report_only(request: Request) -> Response:
        info, result, ms, _ = await convert_request(request, "convert")
        form_body = canonical(result.form)
        return Response(canonical(result.sidecar), media_type="application/json", headers=headers_for(info, form_body, ms, result))

    @app.post("/v1/forms/preview", openapi_extra=UPLOAD_ONE, summary="Page pictures and field places (read only)", responses={200: {
        "description": "`{version, input_sha256, format, units, origin, page_images, pages[{n,w,h,source,img?}], "
                       "places{candidate id: {page, kind, box|anchor, label?, cells?, group?, options?}}, counts}`; "
                       "page_images is OK, OMITTED (images=0) or NO_PAGE_IMAGE (DOCX, DOC, XLSX, ODS: anchors only).",
        "content": {"application/json": {"example": {"version": 1, "format": "pdf", "units": "pt", "origin": "top-left",
                    "page_images": "OMITTED", "pages": [{"n": 1, "w": 595.32, "h": 842.04, "source": "native"}],
                    "places": {"c12": {"page": 1, "kind": "leader", "box": [257.81, 429.65, 365.32, 437.69], "label": "Rasa psa"}},
                    "counts": {"pages": 1, "places": 1, "boxed": 1, "anchored": 0}}}}}})
    async def preview_pages(request: Request, images: int = 1, dpi: int = preview.DPI_DEFAULT) -> Response:
        """Read only (wave 10, fill and print): page pictures and the place of every field candidate, with the ids of
        the ledger rows of `/convert?report=1`. The same token, guard, slots and time limit as `/convert`."""
        job = uuid.uuid4().hex[:12]
        authorize(request, "convert")
        if images not in (0, 1) or not preview.DPI_MIN <= dpi <= preview.DPI_MAX:
            raise ProblemError("BAD_REQUEST", f"Parametr images to 0 lub 1, dpi od {preview.DPI_MIN} do {preview.DPI_MAX}.")
        part = (await read_parts(request))[0]
        data = await part.read()
        await part.close()
        if gate.locked():
            raise ProblemError("BUSY", "Wszystkie stanowiska przetwarzania są zajęte.", headers={"Retry-After": "5"})

        def work() -> tuple[UploadInfo, dict, int]:
            t0 = time.perf_counter()
            info = inspect_upload(part.filename, data, s, part.content_type)
            body = preview.preview_limited(data, s, bool(images), dpi)
            return info, body, int((time.perf_counter() - t0) * 1000)

        async with gate:
            try:
                info, body, ms = await run_in_threadpool(work)
            except ProblemError as exc:
                _event("preview", exc.code, job, len(data))
                raise
        _event("preview", "ok", job, info.size)
        return Response(canonical(body), media_type="application/json", headers={
            "X-Input-SHA256": info.sha256, "X-Converter-Version": __version__, "Server-Timing": f"total;dur={ms}"})

    @app.post("/v1/forms/inspect", openapi_extra=UPLOAD_ONE)
    async def inspect(request: Request) -> JSONResponse:
        authorize(request, "convert")
        part = (await read_parts(request))[0]
        data = await part.read()
        await part.close()
        info = await run_in_threadpool(inspect_upload, part.filename, data, s, part.content_type)
        # What the shell cannot see yet is null, never a guess: the readers (WP-F2) fill pages and links in.
        return JSONResponse({
            "name_sha256_16": info.name_hash, "extension": info.ext, "content_kind": info.kind,
            "size_bytes": info.size, "sha256": info.sha256, "archive_members": info.members,
            "macros": info.macros, "pages": None, "external_links": None, "embedded_files": None,
        })

    @app.post("/v1/batches", openapi_extra=UPLOAD_MANY)
    async def batches(request: Request) -> StreamingResponse:
        authorize(request, "convert")
        parts = await read_parts(request, many=True)
        if len(parts) > BATCH_MAX_FILES:
            raise ProblemError("BAD_REQUEST", f"Co najwyżej {BATCH_MAX_FILES} plików w jednym żądaniu.")
        items: list[tuple[str | None, bytes, str | None]] = []
        zip_name = parts[0].filename or ""
        if len(parts) == 1 and zip_name.lower().endswith(".zip"):
            items = await run_in_threadpool(_zip_items, await parts[0].read(), s)
        else:
            for p in parts:
                items.append((p.filename, await p.read(), p.content_type))
        for p in parts:
            await p.close()
        if gate.locked():
            raise ProblemError("BUSY", "Wszystkie stanowiska przetwarzania są zajęte.", headers={"Retry-After": "5"})

        async def lines() -> AsyncIterator[bytes]:
            async with gate:
                for name, data, declared in items:
                    t0 = time.perf_counter()
                    line: dict = {"name_sha256_16": hashlib.sha256((name or "").encode()).hexdigest()[:16]}
                    try:
                        info, result, _ = await run_in_threadpool(run_one, name, data, declared)
                        line.update(state="ok", engine=engine_state.record(result.sidecar), counts=result.sidecar.get("counts", {}),
                                    warnings=result.sidecar.get("warnings", []), form=result.form)
                    except ProblemError as exc:
                        line.update(state="error", code=exc.code, status=exc.status, counts={}, warnings=[], form=None)
                    except Exception as exc:  # noqa: BLE001 - one file must not cut the stream of the others
                        bad = internal_problem(exc)
                        line.update(state="error", code=bad.code, status=bad.status, counts={}, warnings=[], form=None)
                    line["seconds"] = round(time.perf_counter() - t0, 3)
                    yield canonical(line) + b"\n"

        return StreamingResponse(lines(), media_type="application/x-ndjson")

    # ---- front end ---------------------------------------------------------------------------------------------

    if s.ui_enabled:
        here = Path(__file__).resolve().parent.parent
        for cand in (s.ui_dir, str(here / "ui"), str(here.parent / "review-web" / "dist")):
            if cand and Path(cand).is_dir():
                app.mount("/ui", StaticFiles(directory=cand, html=True), name="ui")
                break
    # Warm the readers registry before the first request: /healthz does not touch it, and two simultaneous first
    # conversions must not meet a half-filled list.
    reader_formats()
    return app


def _zip_items(data: bytes, s: Settings) -> list[tuple[str | None, bytes, str | None]]:
    """The members of a batch ZIP, in memory. Archive limits first; only the eight formats are taken."""
    if not data.startswith(b"PK"):
        raise ProblemError("TYPE_MISMATCH", "Plik .zip nie jest archiwum ZIP.")
    zf = check_archive(data, s, office_members=True)   # a DOCX, XLSX, ODS or ODT member is a ZIP by its format
    out: list[tuple[str | None, bytes, str | None]] = []
    for info in zf.infolist():
        if info.is_dir():
            continue
        base = info.filename.rsplit("/", 1)[-1]
        if base.rsplit(".", 1)[-1].lower() in EXTENSIONS + ("jpe",):
            out.append((base, zf.read(info), None))
        if len(out) > BATCH_MAX_FILES:
            raise ProblemError("BAD_REQUEST", f"Co najwyżej {BATCH_MAX_FILES} plików w jednym żądaniu.")
    if not out:
        raise ProblemError("BAD_REQUEST", "Archiwum nie zawiera plików obsługiwanych formatów.")
    return out
