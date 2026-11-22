"""AUDIT-8 VD-3 (04-F4): a scanned PDF page that also carries a short text layer (a scanner app's footer, a digital
stamp) has 20 or more characters, so it never took the image way and its form was lost.

A page is a scan when one picture covers most of it and its own text is short; then the image way is taken like
for a textless page. A searchable scan (a picture plus a full text layer) and a native page with a logo stay native.
"""
from __future__ import annotations

import io

from app import readers
from app.model.page import Page, Run
from app.readers import read_document
from readers_builders import pdf_bytes

W, H = 595.28, 841.89


def _picture():
    from PIL import Image
    from reportlab.lib.utils import ImageReader

    img = Image.new("L", (300, 424), 255)
    for x in range(30, 270):
        img.putpixel((x, 100), 0)   # a drawn line of the scanned form
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return ImageReader(buf)


def _scan_with_footer(c) -> None:  # noqa: ANN001
    c.drawImage(_picture(), 0, 0, W, H)
    c.setFont("Helvetica", 7)
    c.drawString(40, 20, "Zeskanowano aplikacja ScanApp 2026-11-21")   # 35 non-space characters


def _searchable_scan(c) -> None:  # noqa: ANN001
    c.drawImage(_picture(), 0, 0, W, H)
    c.setFont("Helvetica", 9)
    for i in range(30):
        c.drawString(40, 800 - 20 * i, f"Wiersz tekstu rozpoznanego numer {i} imie nazwisko adres")


def _native_with_logo(c) -> None:  # noqa: ANN001
    c.drawImage(_picture(), 40, 760, 60, 60)
    c.setFont("Helvetica", 9)
    c.drawString(120, 790, "WNIOSEK O WYDANIE ZASWIADCZENIA")
    c.drawString(40, 700, "Imie i nazwisko ........................................")


def _calls(monkeypatch, draw) -> tuple[list[int], object]:  # noqa: ANN001
    calls: list[int] = []

    def fake(data, index, number, ids, options):  # noqa: ANN001
        calls.append(number)
        run = Run(id=ids.next("r"), text="Imię i nazwisko", conf=0.9, box=(40.0, 90.0, 200.0, 102.0))
        return Page(number=number, width=W, height=H, origin="ocr", runs=[run]), []

    readers.formats()   # discover the reader modules first: image.py registers the real hook on import
    monkeypatch.setitem(readers._HOOKS, "pdf.textless_page", fake)
    return calls, read_document(pdf_bytes(draw), "pdf")


def test_scan_with_a_short_text_layer_takes_the_image_way(monkeypatch):
    calls, m = _calls(monkeypatch, _scan_with_footer)
    assert calls == [1]
    assert m.pages[0].origin == "ocr" and [r.text for r in m.pages[0].runs] == ["Imię i nazwisko"]
    assert [x.code for x in m.warnings] == ["OCR_USED"]


def test_searchable_scan_stays_native(monkeypatch):
    calls, m = _calls(monkeypatch, _searchable_scan)
    assert calls == [] and m.pages[0].origin == "native"


def test_native_page_with_a_logo_stays_native(monkeypatch):
    calls, m = _calls(monkeypatch, _native_with_logo)
    assert calls == [] and m.pages[0].origin == "native"
