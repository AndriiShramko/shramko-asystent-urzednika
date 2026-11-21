"""The small hostile corpus, built from code (no hostile binary is committed). `apps/converter/tests/evil` replaces
it when WP-F16 lands. `build(folder)` writes the files and returns {name: path}."""
from __future__ import annotations

import struct
import zipfile
import zlib
from pathlib import Path


def _chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)


def png(width: int, height: int, rows: int = 1) -> bytes:
    """A PNG whose header says width x height; the data holds only `rows` scanlines of white."""
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    raw = (b"\x00" + b"\xff" * min(width, 64)) * rows
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(raw)) + _chunk(b"IEND", b"")


def _zip_bomb(path: Path, megabytes: int = 300) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        with z.open("word/document.xml", "w", force_zip64=True) as part:
            block = b"\x00" * (1 << 20)
            for _ in range(megabytes):
                part.write(block)


def _ods_repeated_rows(path: Path, repeat: int = 1_000_000) -> None:
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"><office:body><office:spreadsheet>'
        f'<table:table table:name="A"><table:table-row table:number-rows-repeated="{repeat}">'
        '<table:table-cell office:value-type="string"><text:p>x</text:p></table:table-cell>'
        "</table:table-row></table:table></office:spreadsheet></office:body></office:document-content>"
    )
    manifest = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">'
        '<manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.spreadsheet"/>'
        '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/></manifest:manifest>'
    )
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/vnd.oasis.opendocument.spreadsheet")
        z.writestr("content.xml", content, zipfile.ZIP_DEFLATED)
        z.writestr("META-INF/manifest.xml", manifest, zipfile.ZIP_DEFLATED)


def build(folder: Path) -> dict[str, Path]:
    folder.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}

    def put(name: str, data: bytes) -> None:
        out[name] = folder / name
        out[name].write_bytes(data)

    put("text-named-pdf.pdf", b"This is plain text, not a PDF.\n" * 20)
    put("empty.pdf", b"")
    put("truncated.pdf", b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R")
    out["zip-bomb.docx"] = folder / "zip-bomb.docx"
    _zip_bomb(out["zip-bomb.docx"])
    put("pixel.png", png(1, 1))
    put("huge-header.png", png(100_000, 100_000))
    out["repeated-rows.ods"] = folder / "repeated-rows.ods"
    _ods_repeated_rows(out["repeated-rows.ods"])
    return out
