"""AUDIT-8 VD-4 (Q4): a character typed in a symbol font (U+F0xx, no sprmCSymbol) became U+FFFD in a .doc, so a
check box of Wingdings 2 was lost (city archive: 10 boxes of one UMB form). The font is the run's ASCII font
(sprmCRgFtc0); with it the box maps through the same symbol table as sprmCSymbol does.
"""
from __future__ import annotations

import struct

from app.readers import read_document
from sheet_doc_builders import doc_bytes, sprm

FONTS = ("Times New Roman", "Wingdings", "Wingdings 2")


def ftc0(index: int) -> bytes:
    return sprm(0x4A4F, struct.pack("<H", index))


def _text(main: str, chars: dict[int, bytes]) -> str:
    m = read_document(doc_bytes(main, chars=chars, fonts=FONTS), "doc")
    return "\n".join(r.text for p in m.pages for r in p.runs)


def test_symbol_font_box_typed_as_private_use_char_is_a_box():
    main = " Wniosek\r"
    assert _text(main, {0: ftc0(2)}) == "□ Wniosek"


def test_symbol_font_in_the_second_font_slot_and_written_without_space():
    # as in the archive file: ASCII font Arial, the East Asian slot names "Wingdings2" (no space)
    main = " Tak\r"
    m = read_document(doc_bytes(main, chars={0: ftc0(0) + sprm(0x4A50, struct.pack("<H", 1))},
                                fonts=("Arial", "Wingdings2")), "doc")
    assert [r.text for p in m.pages for r in p.runs] == ["□ Tak"]


def test_private_use_char_without_a_known_font_stays_unknown():
    assert _text(" Wniosek\r", {}) == "� Wniosek"


def test_unknown_code_in_a_known_symbol_font_stays_unknown():
    assert _text(" x\r", {0: ftc0(1)}) == "� x"
