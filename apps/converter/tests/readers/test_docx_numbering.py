"""WP-C3: the DOCX reader gives the list markers Word shows (w:numPr -> word/numbering.xml). Synthetic text only."""
from __future__ import annotations

import io
import zipfile

from app.readers import read_document
from readers_builders import NSDECL, docx_bytes, p


def _texts(model) -> list[str]:  # noqa: ANN001
    return [r.text for pg in model.pages for r in pg.runs]


def _with_numbering(data: bytes, numbering: str) -> bytes:
    """The package of docx_bytes with a word/numbering.xml added."""
    src = zipfile.ZipFile(io.BytesIO(data))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in src.namelist():
            z.writestr(name, src.read(name))
        z.writestr("word/numbering.xml",
                   f'<?xml version="1.0" encoding="UTF-8"?><w:numbering {NSDECL}>{numbering}</w:numbering>')
    return buf.getvalue()


def _lvl(ilvl: int, fmt: str, text: str, start: int = 1, font: str = "") -> str:
    rpr = f'<w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/></w:rPr>' if font else ""
    return (f'<w:lvl w:ilvl="{ilvl}"><w:start w:val="{start}"/><w:numFmt w:val="{fmt}"/>'
            f'<w:lvlText w:val="{text}"/>{rpr}</w:lvl>')


def _abstract(aid: int, *lvls: str) -> str:
    return f'<w:abstractNum w:abstractNumId="{aid}">{"".join(lvls)}</w:abstractNum>'


def _num(nid: int, aid: int, overrides: str = "") -> str:
    return f'<w:num w:numId="{nid}"><w:abstractNumId w:val="{aid}"/>{overrides}</w:num>'


def _np(text: str, nid: int, ilvl: int = 0) -> str:
    return p(text, ppr=f'<w:numPr><w:ilvl w:val="{ilvl}"/><w:numId w:val="{nid}"/></w:numPr>')


def _read(body: str, numbering: str, styles: str | None = None) -> list[str]:
    return _texts(read_document(_with_numbering(docx_bytes(body, styles=styles), numbering), "docx"))


def test_decimal_list() -> None:
    num = _abstract(1, _lvl(0, "decimal", "%1.")) + _num(5, 1)
    body = p("Załączniki:") + _np("Kopia dokumentu", 5) + _np("Pełnomocnictwo", 5) + _np("Inne", 5)
    assert _read(body, num) == ["Załączniki:", "1. Kopia dokumentu", "2. Pełnomocnictwo", "3. Inne"]


def test_letter_list_with_parenthesis() -> None:
    num = _abstract(1, _lvl(0, "lowerLetter", "%1)")) + _num(2, 1)
    body = _np("pierwsza", 2) + _np("druga", 2) + p("bez numeru") + _np("trzecia", 2)
    assert _read(body, num) == ["a) pierwsza", "b) druga", "bez numeru", "c) trzecia"]


def test_nested_list_restarts_deeper_level() -> None:
    num = _abstract(1, _lvl(0, "decimal", "%1."), _lvl(1, "decimal", "%1.%2."), _lvl(2, "upperRoman", "%3.")) \
        + _num(3, 1)
    body = (_np("Wnioskodawca", 3) + _np("imię", 3, 1) + _np("nazwisko", 3, 1) + _np("Adres", 3)
            + _np("ulica", 3, 1) + _np("dom", 3, 2) + _np("lokal", 3, 2))
    assert _read(body, num) == ["1. Wnioskodawca", "1.1. imię", "1.2. nazwisko", "2. Adres", "2.1. ulica",
                                "I. dom", "II. lokal"]


def test_symbol_box_bullet_becomes_box_and_round_bullet_becomes_dot() -> None:
    num = (_abstract(1, _lvl(0, "bullet", "", font="Wingdings"))
           + _abstract(2, _lvl(0, "bullet", "", font="Symbol"))
           + _abstract(3, _lvl(0, "bullet", "-", font="Calibri"))
           + _abstract(4, _lvl(0, "bullet", "", font="Symbol"))
           + _num(1, 1) + _num(2, 2) + _num(3, 3) + _num(4, 4))
    body = (_np("Wyrażam zgodę", 1) + _np("Nie wyrażam zgody", 1) + _np("punkt", 2) + _np("myślnik", 3)
            + _np("opcja", 4))
    assert _read(body, num) == ["□ Wyrażam zgodę", "□ Nie wyrażam zgody", "• punkt", "- myślnik", "□ opcja"]


def test_start_and_start_override() -> None:
    num = (_abstract(1, _lvl(0, "decimal", "%1.", start=4))
           + _num(1, 1)
           + _num(2, 1, '<w:lvlOverride w:ilvl="0"><w:startOverride w:val="7"/></w:lvlOverride>'))
    body = _np("czwarty", 1) + _np("piąty", 1) + _np("siódmy", 2) + _np("ósmy", 2)
    assert _read(body, num) == ["4. czwarty", "5. piąty", "7. siódmy", "8. ósmy"]


def test_numbering_through_paragraph_style_and_numid_zero() -> None:
    styles = ('<w:style w:type="paragraph" w:styleId="Lista"><w:pPr><w:numPr><w:numId w:val="4"/></w:numPr>'
              '</w:pPr></w:style>')
    num = _abstract(1, _lvl(0, "upperLetter", "%1.")) + _num(4, 1)
    off = p("wyłączony", ppr='<w:pStyle w:val="Lista"/><w:numPr><w:numId w:val="0"/></w:numPr>')
    body = p("tak", ppr='<w:pStyle w:val="Lista"/>') + off + p("nie", ppr='<w:pStyle w:val="Lista"/>')
    assert _read(body, num, styles) == ["A. tak", "wyłączony", "B. nie"]


def test_python_docx_list_number_style() -> None:
    import docx

    d = docx.Document()
    d.add_paragraph("Oświadczenia:")
    d.add_paragraph("pierwsze", style="List Number")
    d.add_paragraph("drugie", style="List Number")
    buf = io.BytesIO()
    d.save(buf)
    texts = [t for t in _texts(read_document(buf.getvalue(), "docx")) if t.strip()]
    assert texts == ["Oświadczenia:", "1. pierwsze", "2. drugie"]


def test_no_numbering_part_leaves_text_unchanged() -> None:
    body = p("zwykły akapit") + _np("bez definicji", 9)
    assert _texts(read_document(docx_bytes(body), "docx")) == ["zwykły akapit", "bez definicji"]
