"""AUDIT-8 VD-1: a binary Word tab whose tab stop has a dotted leader is the paper's blank to fill.

The docx reader writes such a tab as ten leader characters; the doc reader dropped the leader and kept a bare tab,
so the same form in .doc lost its blanks (judged-06: 9 matter fields from .doc against 17 from .docx).
"""
from __future__ import annotations

import struct

from app.readers import read_document
from sheet_doc_builders import doc_bytes, sprm

DOT, NONE = 1 << 3, 0      # TBD: tlc in bits 3-5, jc in bits 0-2
BAR = 4                    # jc = bar: no tab character goes to it


def tabs_papx(add: list[tuple[int, int]], delete: tuple[int, ...] = ()) -> bytes:
    """sprmPChgTabsPapx (0xC60D) operand: cb, then the delete list, then the add list (positions, TBDs)."""
    body = bytes([len(delete)]) + struct.pack(f"<{len(delete)}h", *delete)
    body += bytes([len(add)]) + struct.pack(f"<{len(add)}h", *[p for p, _ in add]) + bytes(t for _, t in add)
    return sprm(0xC60D, bytes([len(body)]) + body)


def _texts(main: str, para: dict[int, bytes]) -> list[str]:
    m = read_document(doc_bytes(main, para=para), "doc")
    return [r.text for p in m.pages for r in p.runs]


def test_dotted_tab_stops_become_leaders():
    p1 = "Wykonawcą Robót będzie\t\r"
    p2 = "długość\tszerokość\trazem\tm2\r"
    main = p1 + p2
    para = {len(p1) - 1: tabs_papx([(9178, DOT)]),
            len(main) - 1: tabs_papx([(3470, DOT), (6221, DOT), (8635, DOT)])}
    assert _texts(main, para) == ["Wykonawcą Robót będzie" + "." * 10,
                                  "długość" + "." * 10 + "szerokość" + "." * 10 + "razem" + "." * 10 + "m2"]


def test_tab_without_leader_stays_a_tab_and_order_follows_position():
    p1 = "a\tb\tc\r"
    # stops given out of order: the first tab goes to the leftmost stop (no leader), the second to the dotted one
    para = {len(p1) - 1: tabs_papx([(6000, DOT), (2000, NONE)])}
    assert _texts(p1, para) == ["a\tb" + "." * 10 + "c"]


def test_bar_tab_takes_no_tab_character():
    p1 = "Imię\tNazwisko\t\r"
    para = {len(p1) - 1: tabs_papx([(1000, BAR), (3000, DOT), (5000, NONE)])}
    assert _texts(p1, para) == ["Imię" + "." * 10 + "Nazwisko"]


def test_delete_list_is_skipped_before_the_add_list():
    # a delete list of two positions comes first in the operand; the add list after it must still be found
    p1 = "Data\t\r"
    para = {len(p1) - 1: tabs_papx([(3000, DOT)], delete=(1500, 2500))}
    assert _texts(p1, para) == ["Data" + "." * 10]


def test_delete_of_a_stop_set_in_the_same_paragraph_removes_it():
    # sprmPChgTabsPapx adds a dotted stop, sprmPChgTabs (read after it) deletes it again: the tab stays a tab
    p1 = "x\ty\r"
    body = bytes([1]) + struct.pack("<h", 3000) + struct.pack("<h", 0) + bytes([0])   # ndel, del, close, nadd
    para = {len(p1) - 1: tabs_papx([(3000, DOT)]) + sprm(0xC615, bytes([len(body)]) + body)}
    assert _texts(p1, para) == ["x\ty"]


def test_paragraph_without_tab_stops_is_unchanged():
    assert _texts("x\ty\r", {}) == ["x\ty"]
