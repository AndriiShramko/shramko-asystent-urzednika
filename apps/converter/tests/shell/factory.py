"""Synthetic files and tokens for the shell tests. Everything is built from code; no task set is read."""
from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import struct
import time
import uuid
import zipfile
import zlib

SECRET = b"synthetic-test-secret-0123456789abcdef-xyz"  # not a real key: 41 bytes of text
OLE_FREE, OLE_END, OLE_FAT = 0xFFFFFFFF, 0xFFFFFFFE, 0xFFFFFFFD


def pdf() -> bytes:
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 750, "Wniosek probny")
    c.save()
    return buf.getvalue()


def docx() -> bytes:
    import docx as pydocx

    d = pydocx.Document()
    d.add_paragraph("Wniosek probny")
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def xlsx() -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    wb.active["A1"] = "Wniosek probny"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def ods() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("mimetype", "application/vnd.oasis.opendocument.spreadsheet", compress_type=zipfile.ZIP_STORED)
        z.writestr("content.xml", "<office:document-content xmlns:office='urn:x'/>")
    return buf.getvalue()


def png(size=(8, 8)) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", size, "white").save(buf, "PNG")
    return buf.getvalue()


def jpeg(size=(8, 8)) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", size, "white").save(buf, "JPEG")
    return buf.getvalue()


def png_header_only(width: int, height: int) -> bytes:
    """A PNG whose header claims a huge size and whose pixel data is a few bytes: refused from its header."""
    def chunk(tag: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body))
    ihdr = struct.pack(">IIBBBBB", width, height, 1, 0, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(b"\x00")) + chunk(b"IEND", b"")


def ole(stream_name: str) -> bytes:
    """A minimal OLE compound file (version 3) with one 4096-byte stream: enough for olefile to list it."""
    sector = 512
    header = bytearray(sector)
    header[0:8] = bytes.fromhex("d0cf11e0a1b11ae1")
    struct.pack_into("<HHHHH", header, 24, 0x3E, 3, 0xFFFE, 9, 6)
    struct.pack_into("<IIIIIIIII", header, 40, 0, 1, 1, 0, 4096, OLE_END, 0, OLE_END, 0)
    difat = [0] + [OLE_FREE] * 108
    struct.pack_into("<109I", header, 76, *difat)
    fat = [OLE_FAT, OLE_END] + list(range(3, 10)) + [OLE_END] + [OLE_FREE] * (128 - 10)
    fat_sector = struct.pack("<128I", *fat)

    def entry(name: str, kind: int, left: int, right: int, child: int, start: int, size: int) -> bytes:
        raw = (name + "\0").encode("utf-16-le")
        return struct.pack("<64sHBBIII16sIQQIQ", raw.ljust(64, b"\0"), len(raw), kind, 1, left, right, child,
                           b"\0" * 16, 0, 0, 0, start, size)
    empty = entry("", 0, OLE_FREE, OLE_FREE, OLE_FREE, 0, 0)
    directory = (entry("Root Entry", 5, OLE_FREE, OLE_FREE, 1, OLE_END, 0)
                 + entry(stream_name, 2, OLE_FREE, OLE_FREE, OLE_FREE, 2, 4096) + empty + empty)
    return bytes(header) + fat_sector + directory + b"\0" * 4096


def doc() -> bytes:
    return ole("WordDocument")


def legacy_workbook() -> bytes:
    return ole("Workbook")


def zip_of(members: dict[str, bytes], store: bool = False) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED if store else zipfile.ZIP_DEFLATED) as z:
        for name, body in members.items():
            z.writestr(name, body)
    return buf.getvalue()


def pdf_and_zip() -> bytes:
    """Satisfies the proof of PDF (start marker, end marker in the tail) and is a ZIP at the same time."""
    return b"%PDF-1.4\n%synthetic\n" + zip_of({"a.txt": b"x"}) + b"\n%%EOF\n"


def multipart(parts: list[tuple[str, str, bytes, str]]) -> tuple[bytes, str]:
    """parts: (field, filename, body, content type) -> (body, Content-Type header)."""
    boundary = "b" + uuid.uuid4().hex
    out = b""
    for field, filename, body, ctype in parts:
        out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{filename}\"\r\n"
                f"Content-Type: {ctype}\r\n\r\n").encode("utf-8") + body + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return out, f"multipart/form-data; boundary={boundary}"


def b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def raw_token(header: dict, payload: dict, key: bytes | None, digest=hashlib.sha256) -> str:
    """A token signed by hand, so that a test can build what the library refuses to build."""
    signing = b64(json.dumps(header).encode()) + "." + b64(json.dumps(payload).encode())
    sig = hmac.new(key, signing.encode(), digest).digest() if key is not None else b""
    return signing + "." + b64(sig)


def claims(**over) -> dict:
    base = {"sub": "tester", "scope": "convert", "exp": int(time.time()) + 600}
    base.update(over)
    return {k: v for k, v in base.items() if v is not None}
