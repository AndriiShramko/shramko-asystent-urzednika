"""WP-F20f stage 1a: routing by content (rtf, xls, txt, heic) and the RTF, XLS and TXT readers.
Every file is built in the test from code; nothing of the archive or the task sets is read."""
from __future__ import annotations

import pytest
from user_format_builders import RTF_HEAD, rtf, rtf_row, xls_file

from app import readers
from app.config import Settings
from app.guard import ProblemError, inspect_upload, sniff_kinds
from app.readers import ReaderError, read_document
from app.readers import rtf as rtf_module

S = Settings(auth_mode="off", max_upload_bytes=5_000_000)
HEIC = b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic" + b"\x00" * 64


def texts(model, page=0):
    p = model.pages[page]
    by_id = {r.id: r for r in p.runs}
    return p, by_id


# ---- the guard routes by content --------------------------------------------------------------------------------

def test_registered_formats_include_the_new_readers():
    assert {"rtf", "xls", "txt"} <= set(readers.formats())
    assert "heic" not in readers.formats()   # stage 1b


def test_rtf_xls_txt_proofs_and_extensions():
    assert inspect_upload("a.rtf", rtf(r"\pard Wniosek\par"), S).kind == "rtf"
    assert inspect_upload("a.xls", xls_file(cells={(0, 0): "x"}), S).kind == "xls"
    info = inspect_upload("a.txt", "Wniosek o wydanie\n".encode("utf-8"), S)
    assert info.kind == "txt" and info.warnings == ()
    assert inspect_upload("a.doc", "Wniosek o wydanie\n".encode("utf-8"), S).kind == "txt"
    assert inspect_upload("a.heic", HEIC, S).kind == "heic"
    assert inspect_upload("a.HEIF", HEIC, S).kind == "heic"


def test_doc_holding_rtf_is_read_as_rtf_with_a_polish_warning():
    info = inspect_upload("stary.doc", rtf(r"\pard Wniosek\par"), S)
    assert info.kind == "rtf" and info.ext == "doc"
    assert info.warnings == ("Rozszerzenie .doc nie zgadza się z zawartością; plik odczytano jako dokument RTF.",)


def test_png_named_gif_is_read_as_what_it_is_with_a_warning():
    import io

    from PIL import Image

    out = io.BytesIO()
    Image.new("L", (64, 64), 255).save(out, format="PNG")
    info = inspect_upload("a.gif", out.getvalue(), S)
    assert info.kind == "png" and "obraz PNG" in info.warnings[0]


@pytest.mark.parametrize("name", ["a.doc", "a.rtf", "a.xls"])
def test_text_under_a_text_capable_extension_is_read_as_text_with_a_warning(name):
    info = inspect_upload(name, b"To jest zwykly tekst.\n" * 5, S)
    assert info.kind == "txt" and info.warnings and info.warnings[0].startswith("Rozszerzenie .")


@pytest.mark.parametrize("name", ["a.pdf", "a.docx", "a.xlsx", "a.ods", "a.odt", "a.jpg", "a.png", "a.tiff"])
def test_text_under_a_binary_format_extension_stays_refused(name):
    with pytest.raises(ProblemError) as e:
        inspect_upload(name, b"To jest zwykly tekst.\n" * 5, S)
    assert e.value.code == "TYPE_MISMATCH" and "plik tekstowy" in e.value.detail


@pytest.mark.parametrize("data", [b"\x00\x01\x02binary\x00" * 30, b"", b"   \n  "])
def test_not_text_and_not_known_is_refused(data):
    with pytest.raises(ProblemError) as e:
        inspect_upload("a.txt", data, S)
    assert e.value.code == "TYPE_MISMATCH"


def test_unknown_container_under_a_known_extension_is_still_refused():
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("hello.bin", b"x")
    with pytest.raises(ProblemError) as e:
        inspect_upload("a.docx", buf.getvalue(), S)
    assert e.value.code == "TYPE_MISMATCH"


def test_polyglot_rtf_and_zip_stays_refused():
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("a.txt", b"x")
    assert sniff_kinds(rtf(r"\pard x\par") + buf.getvalue()) == {"rtf", "zip"}
    with pytest.raises(ProblemError) as e:
        inspect_upload("a.rtf", rtf(r"\pard x\par") + buf.getvalue(), S)
    assert e.value.code == "TYPE_MISMATCH"


def test_utf16_with_bom_and_cp1250_are_text():
    assert sniff_kinds("Zażółć gęślą jaźń".encode("utf-16")) == {"txt"}
    assert sniff_kinds("Zażółć gęślą jaźń".encode("cp1250")) == {"txt"}
    assert sniff_kinds("Zażółć".encode("utf-8-sig")) == {"txt"}


def test_ole_without_word_or_workbook_stream_is_not_xls():
    from sheet_doc_builders import ole_bytes

    assert sniff_kinds(ole_bytes({"Other": b"x"})) == {"ole"}
    assert sniff_kinds(ole_bytes({"Book": b"x"})) == {"xls"}   # BIFF5 stream name
    assert sniff_kinds(ole_bytes({"WordDocument": b"x", "Workbook": b"x"})) == {"doc", "xls"}


def test_heic_has_no_reader_yet_and_the_refusal_is_plain():
    from app import pipeline

    with pytest.raises(ProblemError) as e:
        pipeline.run(HEIC, "a.heic", S)
    assert e.value.detail == "Ta instalacja nie ma dekodera HEIC." and "JPG" not in e.value.detail


# ---- RTF --------------------------------------------------------------------------------------------------------

def test_rtf_paragraphs_code_page_and_escapes():
    data = rtf(r"\pard Imi\'ea: \u380\'bf\par \pard Za\'bf\'f3\'b3\'e6 @u8212\'97 koniec\line druga linia\par")
    m = read_document(data, "rtf")
    p, by = texts(m)
    got = [r.text for r in p.runs]
    assert got[0] == "Imię: ż"   # \'ea is cp1250 ę; \u380 is ż and its fallback \'bf is skipped
    assert got[1] == "Zażółć — koniec".replace("ć", "ć") and got[2] == "druga linia"
    assert [r.anchor for r in p.runs[:3]] == ["p[0]", "p[1]", "p[2]"] and p.origin == "flow"
    assert m.source.reader == "rtf" and m.source.format == "doc"


def test_rtf_raw_8bit_bytes_follow_the_code_page():
    m = read_document("{\\rtf1\\ansi\\ansicpg1250 \\pard Zażółć gęślą\\par}".encode("cp1250"), "rtf")
    assert m.pages[0].runs[0].text == "Zażółć gęślą"


def test_rtf_unicode_skips_uc_fallback_and_pairs_surrogates():
    m = read_document(rtf(r"\uc2\pard A@u8364xyB\par \uc1 \u-10179\'3f\u-8704\'3fC\par"), "rtf")
    got = [r.text for r in m.pages[0].runs]
    assert got[0] == "A€B"
    assert got[1] == "\U0001F600C"


def test_rtf_skips_font_color_style_info_pict_header_and_star_destinations():
    body = (r"{\stylesheet{\s0 Normal;}}{\info{\title SECRET-TITLE}}{\header HEADER-TEXT\par}{\footer FOOT\par}"
            r"{\pict\wmetafile8 0102030405}{\*\generator Ghost;}{\*\listtext 1.\tab}\pard Treść{\*\bkmkstart x}\par")
    m = read_document(rtf(body), "rtf")
    assert [r.text for r in m.pages[0].runs] == ["Treść"]


def test_rtf_bin_data_is_skipped_by_length():
    m = read_document(rtf(r"{\pict\bin5 {}\}\par}\pard OK\par"), "rtf")
    assert [r.text for r in m.pages[0].runs] == ["OK"]


def test_rtf_table_cells_rows_merges_and_flattened_nested_table():
    body = (r"\pard Przed tabelą\par" + "\n"
            + rtf_row("Imię", "Nazwisko") + rtf_row("Jan", "Kowalski")
            + r"\trowd\clmgf\cellx1000\clmrg\cellx2000\pard\intbl Szeroka\cell\pard\intbl\cell\row" + "\n"
            + r"\trowd\cellx3000\pard\intbl Zewnętrzna\par" + "\n"
            + r"\pard\intbl\itap2 Wewn1\nestcell\pard\intbl\itap2 Wewn2\nestcell{\*\nesttableprops\trowd\cellx500\nestrow}"
            + r"\pard\intbl\cell\row" + "\n"
            + r"\pard Po tabeli\par")
    m = read_document(rtf(body), "rtf")
    p = m.pages[0]
    by = {r.id: r.text for r in p.runs}
    assert [r.text for r in p.runs if r.anchor.startswith("p[")] == ["Przed tabelą", "Po tabeli"]
    assert len(p.tables) == 1 and p.tables[0].anchor == "tbl[0]"
    cells = {(c.r, c.c): c for c in p.tables[0].cells}
    assert [by[i] for i in cells[(0, 0)].runs] == ["Imię"] and [by[i] for i in cells[(1, 1)].runs] == ["Kowalski"]
    assert cells[(2, 0)].cs == 2 and [by[i] for i in cells[(2, 0)].runs] == ["Szeroka"] and (2, 1) not in cells
    assert [by[i] for i in cells[(3, 0)].runs] == ["Zewnętrzna", "Wewn1", "Wewn2"]
    assert cells[(0, 0)].anchor == "tbl[0]/cell[0,0]"


def test_rtf_vertical_merge():
    body = (r"\trowd\clvmgf\cellx1000\cellx2000\pard\intbl A\cell\pard\intbl B\cell\row" + "\n"
            + r"\trowd\clvmrg\cellx1000\cellx2000\pard\intbl\cell\pard\intbl C\cell\row" + "\n")
    cells = {(c.r, c.c): c for c in read_document(rtf(body), "rtf").pages[0].tables[0].cells}
    assert cells[(0, 0)].rs == 2 and (1, 0) not in cells and (1, 1) in cells


def test_rtf_field_result_is_kept_and_instruction_dropped():
    body = r"\pard Strona {\field{\*\fldinst PAGE HYPERLINK}{\fldrslt 7}} z dokumentu\par"
    assert read_document(rtf(body), "rtf").pages[0].runs[0].text == "Strona 7 z dokumentu"


def test_rtf_form_fields_checkbox_and_text_blank():
    body = (r"\pard Zgoda {\field{\*\fldinst FORMCHECKBOX {\*\formfield{\fftype1\ffres1{\*\checkbox\cb0}}}}{\fldrslt X}}"
            r" i {\field{\*\fldinst FORMCHECKBOX {\*\formfield{\fftype1\ffdefres0}}}{\fldrslt}}"
            r" i {\field{\*\fldinst FORMTEXT {\*\formfield{\fftype0\ffmaxlen20{\*\ffname Pole}}}}{\fldrslt ab}} nazwa\par")
    p = read_document(rtf(body), "rtf").pages[0]
    assert p.runs[0].text == "Zgoda ☒ i ☐ i __________ nazwa"
    assert [(w.kind, w.max_len, w.anchor) for w in p.widgets] == [("checkbox", None, "p[0]"), ("checkbox", None, "p[0]"),
                                                                  ("text", 20, "p[0]")]


def test_rtf_widget_in_a_table_cell_is_anchored_to_the_cell_paragraph():
    cell = r"\field{\*\fldinst FORMCHECKBOX {\*\formfield{\fftype1\ffres1}}}{\fldrslt} Tak"
    p = read_document(rtf(rtf_row(cell)), "rtf").pages[0]
    assert p.tables[0].cells[0].anchor == "tbl[0]/cell[0,0]" and p.widgets[0].anchor == "tbl[0]/cell[0,0]/p[0]"


def test_rtf_deep_nesting_is_refused_not_a_crash():
    data = ("{\\rtf1 " + "{" * 5000 + "x" + "}" * 5000 + "}").encode()
    with pytest.raises(ReaderError) as e:
        read_document(data, "rtf")
    assert e.value.code == "UNREADABLE"


def test_rtf_limits_on_cells_characters_and_groups(monkeypatch):
    many = "".join(r"\pard x\par " for _ in range(50))
    with pytest.raises(ReaderError) as e:
        read_document(rtf(many), "rtf", {"max_cells": 10})
    assert e.value.code == "TOO_LARGE"
    monkeypatch.setattr(rtf_module, "MAX_CHARS", 100)
    with pytest.raises(ReaderError) as e:
        read_document(rtf(r"\pard " + "a" * 200 + r"\par"), "rtf")
    assert e.value.code == "TOO_LARGE"
    monkeypatch.setattr(rtf_module, "MAX_GROUPS", 5)
    with pytest.raises(ReaderError) as e:
        read_document(rtf("{a}" * 10), "rtf")
    assert e.value.code == "TOO_LARGE"


def test_rtf_unbalanced_and_truncated_input_never_crashes():
    for body in ("}}}\\pard x\\par", "{{\\pard unterminated", "\\pard x\\par \\", "\\u99999999999? \\'zz"):
        read_document(("{\\rtf1 " + body).encode("cp1250"), "rtf")


def test_rtf_without_text_is_one_empty_page():
    m = read_document(rtf(""), "rtf")
    assert len(m.pages) == 1 and m.pages[0].runs == []


def test_rtf_runs_through_the_whole_pipeline():
    from app import pipeline

    body = (r"\pard\b WNIOSEK O WYDANIE ZAŚWIADCZENIA\b0\par" + "\n"
            + rtf_row("Imię i nazwisko wnioskodawcy", "") + rtf_row("Adres zamieszkania", ""))
    res = pipeline.run(rtf(body), "a.rtf", S)
    assert res.sidecar["converter"]["reader"] == "rtf" and res.form["tabs"]


# ---- XLS --------------------------------------------------------------------------------------------------------

def test_xls_cells_bold_borders_merges_and_numbers():
    data = xls_file(cells={(0, 0): "Imie i nazwisko", (0, 1): "wpisz", (1, 0): 3.0, (1, 1): 2.5, (2, 0): "Podpis"},
                    bold={(0, 0)}, boxed={(0, 1)}, merges=[(2, 3, 0, 2)])
    m = read_document(data, "xls")
    p = m.pages[0]
    assert m.source.reader == "xls" and m.source.format == "xlsx" and p.name == "Arkusz1" and p.origin == "flow"
    by_text = {r.text: r for r in p.runs}
    assert {"Imie i nazwisko", "wpisz", "3", "2.5", "Podpis"} <= set(by_text)
    assert by_text["Imie i nazwisko"].bold and not by_text["wpisz"].bold
    merged = [c for t in p.tables for c in t.cells if c.cs == 2]
    assert merged and merged[0].r == 2 and merged[0].c == 0


def test_xls_reads_through_the_whole_pipeline():
    from app import pipeline

    data = xls_file(cells={(0, 0): "WNIOSEK", (2, 0): "Imie i nazwisko", (3, 0): "Adres", (4, 0): "Podpis"},
                    boxed={(2, 1), (3, 1), (4, 1)})
    res = pipeline.run(data, "a.xls", S)
    assert res.sidecar["converter"]["reader"] == "xls"


def test_xls_cell_budget_is_a_refusal():
    data = xls_file(cells={(r, c): "x" for r in range(10) for c in range(10)})
    with pytest.raises(ReaderError) as e:
        read_document(data, "xls", {"max_cells": 20})
    assert e.value.code == "TOO_LARGE"


def test_xls_broken_workbook_is_a_reader_error():
    data = xls_file(cells={(0, 0): "x"})
    with pytest.raises(ReaderError):
        read_document(data[:700] + b"\xff" * 3000, "xls")


# ---- TXT --------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("enc", ["utf-8", "utf-8-sig", "utf-16", "cp1250"])
def test_txt_encodings(enc):
    raw = "WNIOSEK\r\nImię i nazwisko: ........\r\n\r\nPodpis".encode(enc)
    m = read_document(raw, "txt")
    p = m.pages[0]
    assert [r.text for r in p.runs] == ["WNIOSEK", "Imię i nazwisko: ........", "Podpis"]
    assert [r.anchor for r in p.runs] == ["p[0]", "p[1]", "p[2]"] and p.origin == "flow"
    assert m.source.reader == "txt"


def test_txt_line_limit_and_binary_refusal():
    with pytest.raises(ReaderError) as e:
        read_document(b"a\n" * 50, "txt", {"max_cells": 10})
    assert e.value.code == "TOO_LARGE"
    with pytest.raises(ReaderError):
        read_document(b"\x00\x01\x02", "txt")
