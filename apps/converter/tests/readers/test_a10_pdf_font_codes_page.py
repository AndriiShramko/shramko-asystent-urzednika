"""WAVE-10 VJF-1: a PDF page whose font is embedded without a map to letters (no ToUnicode, Identity encoding) gives
its text as glyph codes "(cid:17)(cid:108)...". It has thousands of characters, so it never took the image way, and
every place on it got a label made of font codes (one unseen city form gave 27 fields that are not on the paper).

Such a page is read from its pixels like a scan; its declared form fields stay. With no OCR engine the font codes are
dropped from the page and a warning says the labels are missing. A normal page stays native.
"""
from __future__ import annotations

from app import readers
from app.model.page import Page, Run
from app.readers import read_document

W, H = 595, 842


def _pdf(text_lines: list[str], identity_font: bool, widget: bool = False) -> bytes:
    """A one-page PDF built by hand. identity_font: a Type0 font with Identity-H and no ToUnicode, so pdfminer
    cannot name the letters; else the standard Helvetica."""
    if identity_font:
        body = "".join(f"BT /F1 10 Tf 40 {800 - 14 * i} Td <{''.join(f'{ord(ch) - 29:04X}' for ch in t)}> Tj ET\n"
                       for i, t in enumerate(text_lines))
        font = ("<< /Type /Font /Subtype /Type0 /BaseFont /ABCDEF+Lato-Regular /Encoding /Identity-H "
                "/DescendantFonts [6 0 R] >>")
    else:
        body = "".join(f"BT /F1 10 Tf 40 {800 - 14 * i} Td ({t}) Tj ET\n" for i, t in enumerate(text_lines))
        font = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    annots = " /Annots [7 0 R]" if widget else ""
    objs = [
        "<< /Type /Catalog /Pages 2 0 R" + (" /AcroForm << /Fields [7 0 R] >>" if widget else "") + " >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 5 0 R >> >> "
        f"/Contents 4 0 R{annots} >>",
        f"<< /Length {len(body)} >>\nstream\n{body}endstream",
        font,
        "<< /Type /Font /Subtype /CIDFontType2 /BaseFont /ABCDEF+Lato-Regular "
        "/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> /DW 500 >>",
        "<< /Type /Annot /Subtype /Widget /FT /Tx /T (Imie_Osoba) /Rect [200 600 500 618] /P 3 0 R >>",
    ]
    out = b"%PDF-1.4\n"
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    x = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offs).encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF\n".encode()
    return out


LINES = [f"Imie i nazwisko wnioskodawcy numer {i} adres zamieszkania" for i in range(6)]


def _read(monkeypatch, data: bytes, engine: bool = True):  # noqa: ANN001
    calls: list[int] = []

    def fake(data, index, number, ids, options):  # noqa: ANN001
        calls.append(number)
        if not engine:
            return Page(number=number, width=W, height=H, origin="ocr"), [
                __import__("app.model.common", fromlist=["Warning"]).Warning(
                    code="UNREADABLE_PART", page=number, detail="page not read: no OCR engine in this build")]
        run = Run(id=ids.next("r"), text="Imię (imiona)", conf=0.9, box=(40.0, 200.0, 120.0, 212.0))
        return Page(number=number, width=W, height=H, origin="ocr", runs=[run]), []

    readers.formats()
    monkeypatch.setitem(readers._HOOKS, "pdf.textless_page", fake)
    return calls, read_document(data, "pdf")


def test_the_builder_really_gives_font_codes():
    import io

    import pdfplumber
    with pdfplumber.open(io.BytesIO(_pdf(LINES, True))) as pdf:
        chars = [c["text"] for c in pdf.pages[0].chars if not c["text"].isspace()]
    assert chars and all(c.startswith("(cid:") for c in chars)


def test_page_of_font_codes_is_read_from_its_pixels(monkeypatch):
    calls, m = _read(monkeypatch, _pdf(LINES, True))
    assert calls == [1]
    assert m.pages[0].origin == "ocr" and [r.text for r in m.pages[0].runs] == ["Imię (imiona)"]
    assert [x.code for x in m.warnings] == ["OCR_USED"] and "font codes" in m.warnings[0].detail


def test_declared_fields_of_that_page_stay(monkeypatch):
    calls, m = _read(monkeypatch, _pdf(LINES, True, widget=True))
    assert calls == [1] and m.pages[0].origin == "ocr"
    assert [w.name for w in m.pages[0].widgets] == ["Imie_Osoba"]


def test_without_ocr_no_font_code_becomes_text(monkeypatch):
    calls, m = _read(monkeypatch, _pdf(LINES, True), engine=False)
    assert calls == [1] and m.pages[0].origin == "native"
    assert not any("(cid:" in r.text for r in m.pages[0].runs)
    assert any(x.code == "UNREADABLE_PART" and "font codes" in (x.detail or "") for x in m.warnings)


def test_a_normal_text_page_stays_native(monkeypatch):
    calls, m = _read(monkeypatch, _pdf(LINES, False))
    assert calls == [] and m.pages[0].origin == "native"
    assert any("Imie i nazwisko" in r.text for r in m.pages[0].runs)
