"""Wave 10 fill and print: POST /v1/forms/preview (page pictures and field places, read only).

Contract: wave-10 FP-contract.md. The invariants tested here: one picture per page of the size of the page, the
candidate ids join with every ledger row of `/convert?report=1`, the same file gives the same bytes, `/convert`
answers the same bytes before and after a preview, formats without page geometry answer anchors and no picture,
and the endpoint has the guards of `/convert` (token, limits, parameters, time limit) and is in the OpenAPI.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import time
from pathlib import Path

import factory as fx
import jwt
import pytest
from fastapi.testclient import TestClient

from app import pipeline, preview
from app.config import Settings
from app.main import create_app

OPEN = {"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"}
A4 = (595.28, 841.89)


def client(**over) -> TestClient:
    return TestClient(create_app(Settings.from_env({**OPEN, **{k: str(v) for k, v in over.items()}})))


def post(c: TestClient, url: str, name: str, data: bytes, headers: dict | None = None):
    body, ctype = fx.multipart([("file", name, data, "application/octet-stream")])
    return c.post(url, content=body, headers={"Content-Type": ctype, **(headers or {})})


def matter_pdf(pages: int = 2) -> bytes:
    from reportlab.lib.pagesizes import A4 as size
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=size, invariant=1)
    for p in range(pages):
        c.setFont("Helvetica-Bold", 16)
        c.drawString(120, 780, "WNIOSEK O WYNAJEM SWIETLICY" if p == 0 else "CZESC DRUGA WNIOSKU")
        c.setFont("Helvetica", 11)
        y = 720
        for label in (("Termin wynajmu", "Cel wynajmu", "Liczba osob") if p == 0 else ("Rodzaj imprezy", "Uwagi")):
            c.drawString(56, y, label + " ")
            c.drawString(56 + c.stringWidth(label + " ", "Helvetica", 11), y, "." * 60)
            y -= 28
        c.showPage()
    c.save()
    return buf.getvalue()


def matter_docx() -> bytes:
    import docx as pydocx

    d = pydocx.Document()
    d.add_paragraph("WNIOSEK O WYNAJEM SWIETLICY")
    for label in ("Termin wynajmu", "Cel wynajmu", "Liczba osob"):
        d.add_paragraph(label + " " + "." * 60)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def scan_png() -> bytes:
    from PIL import Image, ImageDraw

    img = Image.new("L", (1654, 2339), 255)   # A4 at 200 dpi
    d = ImageDraw.Draw(img)
    for y in (400, 600, 800):
        d.line((300, y, 1400, y), fill=0, width=3)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def ledger_of(multipart: bytes) -> dict:
    """The meta.json part of `/convert?report=1`."""
    part = multipart.split(b'filename="meta.json"\r\n\r\n', 1)[1].rsplit(b"\r\n--", 1)[0]
    return json.loads(part)


def png_size(b64: str) -> tuple[int, int]:
    raw = base64.b64decode(b64)
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    return int.from_bytes(raw[16:20], "big"), int.from_bytes(raw[20:24], "big")


# ---- the PDF path -------------------------------------------------------------------------------------------

def test_pdf_gives_one_picture_per_page_of_the_page_size_and_places_join_the_ledger():
    c = client()
    data = matter_pdf()
    r = post(c, "/v1/forms/preview", "wniosek.pdf", data)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/json")
    body = r.json()
    assert (body["version"], body["format"], body["units"], body["origin"], body["page_images"]) == (1, "pdf", "pt", "top-left", "OK")
    assert [p["n"] for p in body["pages"]] == [1, 2] and body["counts"]["pages"] == 2
    for p in body["pages"]:
        assert (round(p["w"], 1), round(p["h"], 1)) == (round(A4[0], 1), round(A4[1], 1))
        img = p["img"]
        assert img["media_type"] == "image/png" and img["dpi"] == 150
        assert (img["width_px"], img["height_px"]) == png_size(img["data"])
        assert abs(img["width_px"] - p["w"] * 150 / 72) <= 1 and abs(img["height_px"] - p["h"] * 150 / 72) <= 1
    conv = post(c, "/v1/forms/convert?report=1", "wniosek.pdf", data)
    assert conv.status_code == 200
    meta = ledger_of(conv.content)
    assert meta["converter"]["pipeline"] == "brief"
    rows = meta["meta"]["ledger"]["rows"]
    assert rows and all(row["candidate"] in body["places"] for row in rows)   # the join invariant
    assert list(body["places"]) == [row["candidate"] for row in rows]          # the finder's order
    assert body["input_sha256"] == conv.headers["X-Input-SHA256"] == r.headers["X-Input-SHA256"]
    for place in body["places"].values():
        assert place["page"] in (1, 2) and "box" in place and None not in place.values()
        x0, y0, x1, y1 = place["box"]
        assert 0 <= x0 <= x1 <= A4[0] + 1 and 0 <= y0 <= y1 <= A4[1] + 1
    assert body["counts"]["boxed"] == body["counts"]["places"] == len(rows)


def test_same_file_same_bytes_and_convert_unchanged_by_preview():
    c = client()
    data = matter_pdf()
    before = post(c, "/v1/forms/convert?report=1", "wniosek.pdf", data).content
    a = post(c, "/v1/forms/preview", "wniosek.pdf", data).content
    b = post(c, "/v1/forms/preview", "inna-nazwa.pdf", data).content
    after = post(c, "/v1/forms/convert?report=1", "wniosek.pdf", data).content
    assert a == b
    assert before == after


def test_images_0_leaves_the_pictures_out_and_dpi_is_honoured():
    c = client()
    data = matter_pdf(1)
    off = post(c, "/v1/forms/preview?images=0", "w.pdf", data).json()
    assert off["page_images"] == "OMITTED" and off["pages"] and all("img" not in p for p in off["pages"])
    low = post(c, "/v1/forms/preview?dpi=72", "w.pdf", data).json()
    assert low["pages"][0]["img"]["dpi"] == 72 and abs(low["pages"][0]["img"]["width_px"] - 595) <= 1
    assert off["places"] == low["places"]


def test_pixel_budget_lowers_the_dpi_and_says_so():
    data = matter_pdf(1)
    body = post(client(MAX_PIXELS=1_000_000), "/v1/forms/preview", "w.pdf", data).json()
    img = body["pages"][0]["img"]
    assert img["width_px"] * img["height_px"] <= 1_000_000 + 2000
    assert img["dpi"] < 150


@pytest.mark.parametrize("query", ["dpi=10", "dpi=300", "images=2", "dpi=abc"])
def test_bad_parameters_are_400_problem(query):
    r = post(client(), f"/v1/forms/preview?{query}", "w.pdf", matter_pdf(1))
    assert r.status_code == 400 and r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["code"] == "BAD_REQUEST"


# ---- formats without page geometry, and scans ---------------------------------------------------------------

def test_docx_answers_anchors_and_no_picture():
    r = post(client(), "/v1/forms/preview", "wniosek.docx", matter_docx())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["format"] == "docx" and body["page_images"] == "NO_PAGE_IMAGE" and body["pages"] == []
    assert body["places"] and all("anchor" in p for p in body["places"].values())
    assert body["counts"]["anchored"] == len(body["places"])


def test_png_scan_gives_the_strip_as_its_picture():
    r = post(client(), "/v1/forms/preview", "skan.png", scan_png())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["format"] == "png" and body["page_images"] == "OK" and len(body["pages"]) == 1
    p = body["pages"][0]
    assert abs(p["img"]["width_px"] - p["w"] * p["img"]["dpi"] / 72) <= 1
    assert (p["img"]["width_px"], p["img"]["height_px"]) == png_size(p["img"]["data"])


# ---- the guards of /convert ----------------------------------------------------------------------------------

def test_jwt_mode_needs_a_token(tmp_path: Path):
    key = tmp_path / "secret.key"
    key.write_bytes(fx.SECRET + b"\n")
    c = TestClient(create_app(Settings.from_env({"JWT_SECRET_FILE": str(key), "UI_ENABLED": "false"})))
    r = post(c, "/v1/forms/preview", "w.pdf", matter_pdf(1))
    assert r.status_code == 401 and r.headers["content-type"].startswith("application/problem+json")
    ok = post(c, "/v1/forms/preview", "w.pdf", matter_pdf(1),
              {"Authorization": "Bearer " + jwt.encode(fx.claims(), fx.SECRET, algorithm="HS256")})
    assert ok.status_code == 200


def test_size_and_type_limits_are_those_of_convert():
    big = post(client(MAX_UPLOAD_BYTES=2000), "/v1/forms/preview", "w.pdf", matter_pdf(2))
    assert big.status_code == 413 and big.json()["code"] == "TOO_LARGE"
    wrong = post(client(), "/v1/forms/preview", "w.exe", fx.png())
    assert wrong.status_code == 415 and wrong.json()["code"] == "EXTENSION"
    c = client()   # a content that disagrees with its extension: preview answers as convert does
    assert post(c, "/v1/forms/preview", "w.pdf", fx.png()).status_code == post(c, "/v1/forms/convert", "w.pdf", fx.png()).status_code
    pages = post(client(MAX_PAGES=1), "/v1/forms/preview", "w.pdf", matter_pdf(2))
    assert pages.status_code == 413


def test_time_limit_answers_504(monkeypatch):
    def slow(*_a, **_k):
        time.sleep(3)
        return {}

    monkeypatch.setattr(preview, "preview", slow)
    r = post(client(JOB_TIMEOUT_S=1), "/v1/forms/preview", "w.pdf", matter_pdf(1))
    assert r.status_code == 504 and r.json()["code"] == "TIMEOUT"
    time.sleep(2.5)
    with pipeline._abandoned_lock:
        pipeline._abandoned[:] = [t for t in pipeline._abandoned if t.is_alive()]


def test_route_is_in_the_openapi():
    spec = client().get("/openapi.json").json()
    assert "post" in spec["paths"]["/v1/forms/preview"]


def test_preview_makes_no_external_call():
    src = Path(preview.__file__).read_text(encoding="utf-8")
    assert "http://" not in src and "https://" not in src and "urllib" not in src and "requests" not in src


# ---- the partner's task sets (local only) -----------------------------------------------------------------

@pytest.mark.sets
def test_every_judged_pdf_has_pictures_and_every_ledger_row_a_place():
    from tools.coi_paths import sets

    s = Settings.from_env(OPEN)
    done = 0
    for folder in sets("judged"):
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() != ".pdf":
                continue
            data = f.read_bytes()
            res = pipeline.run(data, f.name, s)
            body = preview.preview(data, s, images=False)
            rows = res.sidecar["meta"]["ledger"]["rows"]
            assert all(r["candidate"] in body["places"] for r in rows), folder.name
            assert body["page_images"] == "OMITTED" and len(body["pages"]) == res.sidecar["counts"]["source_pages"]
            done += 1
    assert done >= 7
    one = next(f for folder in sets("judged") if "judged-07" in folder.name for f in sorted(folder.iterdir())
               if f.suffix.lower() == ".pdf")
    a = json.dumps(preview.preview(one.read_bytes(), s), ensure_ascii=False, separators=(",", ":")).encode()
    b = json.dumps(preview.preview(one.read_bytes(), s), ensure_ascii=False, separators=(",", ":")).encode()
    assert hashlib.sha256(a).digest() == hashlib.sha256(b).digest()
