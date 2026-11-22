"""Negative controls of the guard (design 6.1; WP-F1 acceptance, native). Every file is built in code."""
from __future__ import annotations

import unicodedata

import factory as fx
import pytest

from app.config import Settings
from app.guard import ProblemError, inspect_upload

S = Settings(auth_mode="off", max_upload_bytes=200_000)


def refused(name, data, code, settings=S, declared=None):
    with pytest.raises(ProblemError) as ei:
        inspect_upload(name, data, settings, declared)
    assert ei.value.code == code, ei.value.detail
    return ei.value


# ---- positive: each of the eight extensions with matching content ----------------------------------------------

@pytest.mark.parametrize("name,data,kind", [
    ("a.pdf", fx.pdf(), "pdf"), ("a.docx", fx.docx(), "docx"), ("a.xlsx", fx.xlsx(), "xlsx"),
    ("a.ods", fx.ods(), "ods"), ("a.doc", fx.doc(), "doc"), ("a.jpg", fx.jpeg(), "jpeg"),
    ("a.jpeg", fx.jpeg(), "jpeg"), ("a.png", fx.png(), "png"),
])
def test_matching_content_is_accepted(name, data, kind):
    info = inspect_upload(name, data, S)
    assert info.kind == kind and info.size == len(data) and len(info.sha256) == 64


def test_upper_case_extension_is_accepted():
    assert inspect_upload("FORMULARZ.PDF", fx.pdf(), S).kind == "pdf"


# ---- extension --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["a.exe", "a.dll", "a.pdf.exe", "a."])
def test_wrong_extension(name):
    refused(name, fx.pdf(), "EXTENSION")


def test_jpe_is_read_as_jpeg_in_both_modes():
    # a10 STRICT: the default is the card's eight; `.jpe` stays a JPEG spelling (the partner's judged set 7 ships one)
    assert inspect_upload("scan.jpe", fx.jpeg(), S).kind == "jpeg"
    assert inspect_upload("scan.jpe", fx.jpeg(), Settings(auth_mode="off", strict_extensions=False)).kind == "jpeg"


# ---- names ------------------------------------------------------------------------------------------------------

CLEAN = Settings(auth_mode="off", max_upload_bytes=200_000, name_policy="clean")


def cleaned(raw, expected_name):
    """NAME_POLICY=clean (WP-F20f): the name is cleaned, not refused."""
    info = inspect_upload(raw, fx.pdf(), CLEAN)
    assert info.name == expected_name and info.kind == "pdf"
    assert info.warnings and info.warnings[0].startswith("Nazwa pliku została oczyszczona")
    return info


@pytest.mark.parametrize("ch", list(";:><" + chr(92) + "/|'*%$"))
def test_by_default_a_name_with_a_character_the_card_forbids_is_refused(ch):
    """BL12: the task card's "Walidacja nazwy pliku" is the default (NAME_POLICY=refuse): 400 BAD_NAME in Polish."""
    with pytest.raises(ProblemError) as e:
        inspect_upload(f"a{ch}b.pdf", fx.pdf(), S)
    assert e.value.code == "BAD_NAME" and "Zmień nazwę pliku" in str(e.value) and ch in str(e.value)


def test_by_default_a_name_over_250_characters_is_refused_and_250_pass():
    with pytest.raises(ProblemError) as e:
        inspect_upload("a" * 247 + ".pdf", fx.pdf(), S)
    assert e.value.code == "BAD_NAME" and "250" in str(e.value)
    assert inspect_upload("a" * 246 + ".pdf", fx.pdf(), S).name == "a" * 246 + ".pdf"


def test_by_default_control_characters_are_still_only_removed():
    info = inspect_upload("a" + chr(0x202E) + "b.pdf", fx.pdf(), S)
    assert info.name == "ab.pdf" and info.warnings


def test_name_with_percent_is_cleaned():
    cleaned("wniosek%20.pdf", "wniosek20.pdf")


@pytest.mark.parametrize("ch", list(";:><" + chr(92) + "/|'*$") + [chr(0), chr(7), chr(0x202E), chr(0x2066)])
def test_name_with_forbidden_or_control_character_is_cleaned(ch):
    cleaned(f"a{ch}b.pdf", "ab.pdf")


def test_name_of_251_characters_is_cut_to_250():
    info = cleaned("a" * 247 + ".pdf", "a" * 246 + ".pdf")
    assert len(info.name) == 250
    assert not inspect_upload("a" * 246 + ".pdf", fx.pdf(), CLEAN).warnings  # 250 characters: unchanged


def test_name_is_normalised_to_nfc():
    info = inspect_upload("Zo" + unicodedata.normalize("NFD", "\u00f3") + "\u0142w.pdf", fx.pdf(), S)
    assert info.name == unicodedata.normalize("NFC", info.name)


def test_missing_name_is_read_by_content():
    info = inspect_upload(None, fx.pdf(), S)
    assert info.kind == "pdf" and info.name == "plik.pdf" and len(info.warnings) == 2
    assert inspect_upload("noextension", fx.pdf(), S).kind == "pdf"


# ---- content proofs ---------------------------------------------------------------------------------------------

def test_png_bytes_named_pdf_are_read_as_png_with_a_warning():
    info = inspect_upload("a.pdf", fx.png(), S)
    assert info.kind == "png" and "obraz PNG" in info.warnings[0]


def test_text_named_pdf_and_empty_file():
    refused("a.pdf", b"just text, not a pdf", "TYPE_MISMATCH")
    refused("a.pdf", b"", "TYPE_MISMATCH")


def test_pdf_without_end_marker():
    refused("a.pdf", b"%PDF-1.4\n" + bytes(1) + b"x" * 5000, "TYPE_MISMATCH")   # not text either (a NUL byte)


@pytest.mark.parametrize("data,name,actual", [
    (fx.docx(), "a.xlsx", "DOCX"), (fx.xlsx(), "a.ods", "XLSX"), (fx.ods(), "a.docx", "ODS"),
    (fx.docx(), "a.ods", "DOCX"), (fx.xlsx(), "a.docx", "XLSX"),
])
def test_swapped_zip_suffixes_are_read_by_content_with_a_warning(data, name, actual):
    info = inspect_upload(name, data, S)   # WP-F20f: exactly one known kind is read as that kind
    assert info.kind == actual.lower() and actual in info.warnings[0] and "ZIP" not in info.warnings[0]


def test_legacy_workbook_named_doc_is_read_as_xls_with_a_warning():
    info = inspect_upload("a.doc", fx.legacy_workbook(), S)
    assert info.kind == "xls" and "XLS" in info.warnings[0]


def test_plain_zip_named_docx():
    refused("a.docx", fx.zip_of({"hello.txt": b"x"}), "TYPE_MISMATCH")


def test_file_that_is_both_pdf_and_zip():
    data = fx.pdf_and_zip()
    assert data.startswith(b"%PDF-") and b"%%EOF" in data[-1024:]
    e = refused("a.pdf", data, "TYPE_MISMATCH")
    assert "pdf" in e.detail and "kilku" in e.detail


def test_doc_reader_off():
    refused("a.doc", fx.doc(), "DOC_READER_OFF", Settings(auth_mode="off", doc_reader="off"))


def test_declared_part_type_must_agree():
    assert inspect_upload("a.pdf", fx.pdf(), S, "application/pdf").kind == "pdf"
    assert inspect_upload("a.pdf", fx.pdf(), S, "application/octet-stream").kind == "pdf"
    refused("a.pdf", fx.pdf(), "TYPE_MISMATCH", declared="image/png")
    assert inspect_upload("a.docx", fx.docx(), S, "application/zip").kind == "docx"


# ---- size -------------------------------------------------------------------------------------------------------

def test_one_byte_over_the_limit_and_exactly_at_it():
    small = Settings(auth_mode="off", max_upload_bytes=5000)
    body = b"%PDF-1.4\n" + b"0" * (5000 - 9 - 7) + b"\n%%EOF\n"
    assert len(body) == 5000
    assert inspect_upload("a.pdf", body, small).kind == "pdf"
    e = refused("a.pdf", body + b" ", "TOO_LARGE", small)
    assert e.limits == {"max_upload_bytes": 5000}


# ---- images -----------------------------------------------------------------------------------------------------

def test_image_of_100000_by_100000_is_refused_from_its_header():
    refused("a.png", fx.png_header_only(100_000, 100_000), "TOO_MANY_PIXELS")


def test_image_over_max_pixels_but_not_a_bomb():
    e = refused("a.png", fx.png_header_only(9_000, 9_000), "TOO_MANY_PIXELS")  # 81 million > 80 million
    assert e.limits == {"max_pixels": 80_000_000}


def test_tall_scan_of_set_9_size_is_within_the_limit():
    assert inspect_upload("a.png", fx.png_header_only(1654, 37424), S).kind == "png"  # 61.9 million pixels


def test_broken_jpeg_header():
    refused("a.jpg", b"\xff\xd8\xff" + b"\x00" * 20, "UNREADABLE")


# ---- archives ---------------------------------------------------------------------------------------------------

BIG = Settings(auth_mode="off", max_upload_bytes=5_000_000)


def test_member_of_a_gigabyte_of_zeros_is_stopped_while_reading():
    # 60 MB of zeros packs to about 60 KB; the guard reads at most 50 MB + one chunk of it.
    bomb = fx.zip_of({"[Content_Types].xml": b"x", "word/document.xml": b"\0" * (60 * 1024 * 1024)})
    assert len(bomb) < 200_000
    refused("a.docx", bomb, "ARCHIVE_LIMIT", BIG)


def test_member_with_a_path_traversal_name():
    refused("a.docx", fx.zip_of({"../../x": b"x", "[Content_Types].xml": b"x", "word/document.xml": b"x"}), "ARCHIVE_LIMIT")


@pytest.mark.parametrize("member", ["/etc/x", "C:/x", "dir\\x"])
def test_member_with_a_rooted_or_drive_or_backslash_name(member):
    # zipfile itself turns a backslash into a slash on Windows when writing: patch the bytes of the name instead.
    raw = fx.zip_of({member.replace("\\", "Q"): b"x", "[Content_Types].xml": b"x", "word/document.xml": b"x"})
    raw = raw.replace(member.replace("\\", "Q").encode(), member.encode())
    refused("a.docx", raw, "ARCHIVE_LIMIT")


def test_more_than_2000_members():
    members = {f"m{i}.txt": b"" for i in range(2001)}
    members.update({"[Content_Types].xml": b"x", "word/document.xml": b"x"})
    refused("a.docx", fx.zip_of(members), "ARCHIVE_LIMIT", BIG)


def test_archive_inside_an_archive():
    inner = fx.zip_of({"a.txt": b"x"})
    refused("a.docx", fx.zip_of({"[Content_Types].xml": b"x", "word/document.xml": b"x", "embedded.bin": inner}), "ARCHIVE_LIMIT")


def test_macro_part_is_reported_and_refused_only_in_strict_mode():
    data = fx.zip_of({"[Content_Types].xml": b"x", "word/document.xml": b"x", "word/vbaProject.bin": b"x"})
    assert inspect_upload("a.docx", data, S).macros is True
    refused("a.docx", data, "ACTIVE_CONTENT", Settings(auth_mode="off", active_content="strict"))
