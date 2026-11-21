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

@pytest.mark.parametrize("name", ["a.txt", "a.exe", "noextension", "a.pdf.exe", "a."])
def test_wrong_extension(name):
    refused(name, fx.pdf(), "EXTENSION")


def test_jpe_is_accepted_by_default_and_refused_when_strict():
    assert inspect_upload("scan.jpe", fx.jpeg(), S).kind == "jpeg"
    refused("scan.jpe", fx.jpeg(), "EXTENSION", Settings(auth_mode="off", strict_extensions=True))


# ---- names ------------------------------------------------------------------------------------------------------

def test_name_with_percent():
    refused("wniosek%20.pdf", fx.pdf(), "BAD_NAME")


@pytest.mark.parametrize("ch", list(";:><\\/|'*$") + ["\x00", "\x07", "\u202e", "\u2066"])
def test_name_with_forbidden_or_control_character(ch):
    refused(f"a{ch}b.pdf", fx.pdf(), "BAD_NAME")


def test_name_of_251_characters_refused_and_250_accepted():
    refused("a" * 247 + ".pdf", fx.pdf(), "BAD_NAME")  # 251 characters
    assert inspect_upload("a" * 246 + ".pdf", fx.pdf(), S).kind == "pdf"  # 250 characters


def test_name_is_normalised_to_nfc():
    info = inspect_upload("Zo" + unicodedata.normalize("NFD", "\u00f3") + "\u0142w.pdf", fx.pdf(), S)
    assert info.name == unicodedata.normalize("NFC", info.name)


def test_missing_name():
    refused(None, fx.pdf(), "BAD_NAME")


# ---- content proofs ---------------------------------------------------------------------------------------------

def test_png_bytes_named_pdf():
    e = refused("a.pdf", fx.png(), "TYPE_MISMATCH")
    assert "PNG" in e.detail


def test_text_named_pdf_and_empty_file():
    refused("a.pdf", b"just text, not a pdf", "TYPE_MISMATCH")
    refused("a.pdf", b"", "TYPE_MISMATCH")


def test_pdf_without_end_marker():
    refused("a.pdf", b"%PDF-1.4\n" + b"x" * 5000, "TYPE_MISMATCH")


@pytest.mark.parametrize("data,name,actual", [
    (fx.docx(), "a.xlsx", "DOCX"), (fx.xlsx(), "a.ods", "XLSX"), (fx.ods(), "a.docx", "ODS"),
    (fx.docx(), "a.ods", "DOCX"), (fx.xlsx(), "a.docx", "XLSX"),
])
def test_swapped_zip_suffixes_are_refused_by_content_not_as_a_generic_zip(data, name, actual):
    e = refused(name, data, "TYPE_MISMATCH")
    assert actual in e.detail and "ZIP" not in e.detail


def test_legacy_workbook_named_doc():
    e = refused("a.doc", fx.legacy_workbook(), "TYPE_MISMATCH")
    assert "OLE" in e.detail


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
