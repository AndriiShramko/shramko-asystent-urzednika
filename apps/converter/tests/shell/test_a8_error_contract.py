"""A8 TT: the error contract of the REST layer. Every refusal and every error is a problem JSON
(`application/problem+json`, RFC 9457) that carries `status` equal to the HTTP status and a machine `code`, and that
never carries document text, a file name, a Python traceback or an exception message.

Covered: 404, 405, 413, 415, 422 (a refused file and a malformed query), 429, 500 (an unexpected crash inside the
pipeline), 504. The partner's front end and the jury's scripts branch on `code`; a plain-text 500 or a problem without
`code` breaks that branch, and a traceback or document text in an answer is a leak.
"""
from __future__ import annotations

import dataclasses
import io
import json
import time

import pytest
from fastapi.testclient import TestClient

from app import pipeline
from app.config import Settings
from app.main import create_app

BASE = Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"})
MARKER = "ZQXJ7 tajny tekst dokumentu"   # stands for document text; must never come back in an error
NAME_MARKER = "Kowalski-wniosek-QPWX"   # stands for a private file name
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def client(**over) -> TestClient:
    return TestClient(create_app(dataclasses.replace(BASE, **over)), raise_server_exceptions=False)


def docx_with_text(text: str) -> bytes:
    import docx as pydocx

    d = pydocx.Document()
    d.add_paragraph(text)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def assert_problem(r, status: int) -> dict:
    assert r.status_code == status, (r.status_code, r.text[:300])
    ctype = r.headers.get("content-type", "")
    assert ctype.startswith("application/problem+json"), (status, ctype, r.text[:300])
    body = r.json()
    assert body.get("status") == status, body
    assert isinstance(body.get("code"), str) and body["code"], ("problem without a machine code", body)
    assert body.get("title"), body
    text = r.text
    for bad in ("Traceback", "File \"", MARKER, NAME_MARKER, "RuntimeError", "Exception"):
        assert bad not in text, (status, bad, text[:300])
    return body


def test_404_unknown_path():
    assert_problem(client().get("/v1/nothing-here"), 404)


def test_405_wrong_method():
    assert_problem(client().get("/v1/forms/convert"), 405)


def test_413_declared_body_over_the_limit():
    c = client(max_upload_bytes=1024)
    data = b"%PDF-1.4\n" + b"0" * (3 << 20)
    r = c.post("/v1/forms/convert", files={"file": (f"{NAME_MARKER}.pdf", data, "application/pdf")})
    assert assert_problem(r, 413)["code"] == "TOO_LARGE"


def test_415_unsupported_extension():
    r = client().post("/v1/forms/convert", files={"file": (f"{NAME_MARKER}.exe", b"MZ" + b"\0" * 64, "application/octet-stream")})
    assert_problem(r, 415)


def broken_docx(text: str) -> bytes:
    """A real DOCX whose main part is cut in the middle of the document text: the reader must refuse it."""
    import zipfile

    src = zipfile.ZipFile(io.BytesIO(docx_with_text(text)))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as out:
        for item in src.infolist():
            body = src.read(item)
            if item.filename == "word/document.xml":
                body = body[: body.index(text.encode()) + 10]
            out.writestr(item, body)
    return buf.getvalue()


def test_422_a_broken_file_is_refused_without_echoing_its_text():
    r = client().post("/v1/forms/convert", files={"file": (f"{NAME_MARKER}.docx", broken_docx(MARKER), DOCX)})
    assert r.status_code in (415, 422), (r.status_code, r.text[:300])
    assert_problem(r, r.status_code)


def test_malformed_query_parameter_is_a_problem_with_a_code():
    """The service answers 400 BAD_REQUEST here (its own choice, documented); the contract is the problem shape."""
    r = client().post("/v1/forms/convert?report=" + MARKER.replace(" ", "%20"),
                      files={"file": ("a.docx", docx_with_text("Imie i nazwisko"), DOCX)})
    assert r.status_code in (400, 422), (r.status_code, r.text[:300])
    assert_problem(r, r.status_code)


def test_429_rate_limit():
    c = client(rate_limit_per_min=1)
    files = {"file": ("a.exe", b"MZ", "application/octet-stream")}
    c.post("/v1/forms/convert", files=files)
    r = c.post("/v1/forms/convert", files=files)
    body = assert_problem(r, 429)
    assert r.headers.get("Retry-After"), body


def test_500_an_unexpected_crash_is_a_problem_without_its_message(monkeypatch):
    def boom(*_a, **_k):
        raise RuntimeError(f"reader crashed on {MARKER}")

    monkeypatch.setattr(pipeline, "run_limited", boom)
    r = client().post("/v1/forms/convert", files={"file": ("a.docx", docx_with_text("Imie i nazwisko"), DOCX)})
    assert_problem(r, 500)


def test_504_timeout(monkeypatch):
    real_run = pipeline.run

    def slow(*a, **k):
        time.sleep(3)
        return real_run(*a, **k)

    monkeypatch.setattr(pipeline, "run", slow)
    r = client(job_timeout_s=1).post("/v1/forms/convert", files={"file": ("a.docx", docx_with_text("Imie i nazwisko"), DOCX)})
    for t in list(pipeline._abandoned):   # the abandoned job must not hold a slot in the next test (RC: VC-10 test)
        t.join(10)
    assert assert_problem(r, 504)["code"] == "TIMEOUT"


def test_batch_line_error_carries_a_code_and_no_text():
    r = client().post("/v1/batches", files=[("file", (f"{NAME_MARKER}.exe", b"MZ", "application/octet-stream")),
                                            ("file", ("b.docx", docx_with_text(MARKER), DOCX))])
    assert r.status_code == 200, r.text[:300]
    for line in r.text.splitlines():
        item = json.loads(line)
        assert NAME_MARKER not in line
        if item["state"] == "error":
            assert item["code"] and isinstance(item["status"], int), item
            assert MARKER not in line, line[:300]
