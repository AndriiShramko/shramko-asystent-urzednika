"""EM-1: a binary Word form drawn as floating text boxes and shapes (a PDF exported to Word, judged sets 02 and 08)
is read with its geometry (reader doc.native), as the same form saved as DOCX is (docx.native): the text boxes are
placed at their shapes, a thin filled shape is a line, an outlined shape is a box, so the finder sees the places to
fill. A document whose text is mostly body text stays a flow, and a shape whose place is not known is not guessed."""
from __future__ import annotations

import struct

from app.find import find
from app.readers import read_document

from sheet_doc_builders import doc_bytes

TEXTBOX, FREEFORM, RECTANGLE = 202, 0, 1
PAGE, PARAGRAPH = 1, 2   # what bx and by measure from
NO_LINE, NO_FILL = 0x00080000, 0x00100000   # fUsefLine set and fLine clear; fUsefFilled set and fFilled clear
BLACK = 0x000000


def _rec(ver: int, inst: int, typ: int, body: bytes) -> bytes:
    return struct.pack("<HHI", ver | (inst << 4), typ, len(body)) + body


def _shape(spid: int, typ: int, props: dict[int, int]) -> bytes:
    fsp = _rec(2, typ, 0xF00A, struct.pack("<II", spid, 0xA00))
    fopt = _rec(3, len(props), 0xF00B, b"".join(struct.pack("<HI", p, v) for p, v in sorted(props.items())))
    return _rec(0xF, 0, 0xF004, fsp + fopt)


def _dgg(shapes: list[bytes]) -> bytes:
    """OfficeArtContent: an empty drawing group, then the main document's drawing (label byte 0)."""
    group = _rec(0xF, 0, 0xF003, b"".join(shapes))
    return _rec(0xF, 0, 0xF000, b"") + b"\x00" + _rec(0xF, 0, 0xF002, group)


def _spa(anchors: list[tuple]) -> bytes:
    """PlcSpaMom: CPs then FSPA (spid, rectangle in twips, flags with bx in bits 1-2 and by in bits 3-4)."""
    cps = [a[0] for a in anchors] + [anchors[-1][0] + 1]
    body = b"".join(struct.pack("<IiiiiHi", spid, *rect, (bx << 1) | (by << 3), 0)
                    for _cp, spid, rect, bx, by in anchors)
    return struct.pack(f"<{len(cps)}i", *cps) + body


def _form(by: int = PAGE, body: str = "", lead: str = "") -> bytes:
    """Two caption text boxes, each with a frame to its right to write in (an outlined rectangle on a white fill)
    and a black hairline under the frame (a thin filled shape): the paper of a PDF exported to Word."""
    boxes = ["Imię i nazwisko\r", "Adres zamieszkania\r"]
    main = lead + "\x08" * 6 + body + "\r"
    shapes = [
        _shape(1025, TEXTBOX, {0x0080: 1 << 16, 0x01FF: NO_LINE, 0x01BF: NO_FILL}),
        _shape(1026, TEXTBOX, {0x0080: 2 << 16, 0x01FF: NO_LINE, 0x01BF: NO_FILL}),
        _shape(1027, FREEFORM, {0x0181: BLACK, 0x01FF: NO_LINE}),
        _shape(1028, FREEFORM, {0x0181: BLACK, 0x01FF: NO_LINE}),
        _shape(1029, RECTANGLE, {}),
        _shape(1030, RECTANGLE, {}),
    ]
    anchors = [
        (0, 1025, (1440, 2000, 3600, 2240), PAGE, by),
        (1, 1026, (1440, 3000, 3600, 3240), PAGE, by),
        (2, 1027, (3700, 2230, 10000, 2240), PAGE, by),
        (3, 1028, (3700, 3230, 10000, 3240), PAGE, by),
        (4, 1029, (3700, 1900, 10000, 2200), PAGE, by),
        (5, 1030, (3700, 2900, 10000, 3200), PAGE, by),
    ]
    anchors = [(cp + len(lead), *rest) for cp, *rest in anchors]
    return doc_bytes(main, txbx=boxes, extra={40: _spa(anchors), 50: _dgg(shapes)})


def test_text_box_form_is_read_with_its_geometry():
    m = read_document(_form(), "doc")
    assert m.source.reader == "doc.native"
    page = m.pages[0]
    assert page.origin == "native" and page.width and page.height
    runs = {r.text: r.box for r in page.runs}
    assert runs["Imię i nazwisko"] == (72.0, 100.0, 180.0, 112.0)
    assert runs["Adres zamieszkania"] == (72.0, 150.0, 180.0, 162.0)
    assert sorted(ln.box for ln in page.lines) == [(185.0, 111.75, 500.0, 111.75), (185.0, 161.75, 500.0, 161.75)]
    assert sorted(q.box for q in page.rects) == [(185.0, 95.0, 500.0, 110.0), (185.0, 145.0, 500.0, 160.0)]


def test_the_finder_sees_a_place_to_fill_after_each_caption():
    out = find(read_document(_form(), "doc"))
    assert len(out.candidates) >= 2
    labels = " ".join(str(getattr(c, "label", "")) for c in out.candidates)
    assert "Imię i nazwisko" in labels and "Adres zamieszkania" in labels


def test_mostly_body_text_stays_a_flow():
    m = read_document(_form(body="Treść pisma " * 20), "doc")
    assert m.source.reader == "doc.flow"
    assert {r.text for r in m.pages[0].runs} >= {"Imię i nazwisko", "Adres zamieszkania"}


def test_position_from_the_first_paragraph_starts_at_the_top_margin():
    """by = paragraph is known only for the first paragraph of a page, which starts at the top margin (72 pt)."""
    m = read_document(_form(by=PARAGRAPH), "doc")
    assert m.source.reader == "doc.native"
    runs = {r.text: r.box for r in m.pages[0].runs}
    assert runs["Imię i nazwisko"][1] == 72.0 + 100.0


def test_position_from_a_later_paragraph_is_not_guessed():
    """The anchors sit in the second paragraph: its place on the page is not known, so nothing is placed and the
    document is read as a flow (no text lost)."""
    m = read_document(_form(by=PARAGRAPH, lead="Wniosek\r"), "doc")
    assert m.source.reader == "doc.flow"
    assert {r.text for r in m.pages[0].runs} >= {"Wniosek", "Imię i nazwisko", "Adres zamieszkania"}
