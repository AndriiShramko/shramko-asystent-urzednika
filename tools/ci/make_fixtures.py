#!/usr/bin/env python3
"""Write one small SYNTHETIC blank form per accepted extension (WP-F20, build-time tool).

    python tools/ci/make_fixtures.py OUT_DIR

Nothing of the partner's task sets is in git, so CI converts these. Each file is a blank application with a
title, labelled places to fill (dotted leaders, empty cells, comb boxes) and no value filled in. The words are
generic and invented; no person, office or number is real. Writes wniosek.{pdf,docx,xlsx,ods,doc,png,jpg,jpeg,odt,tiff,bmp,gif,webp,rtf,xls,txt,heic,heif} and (WP-F20f)
wniosek-owner.pdf, wniosek-anim.png, wniosek-rtf.doc; prints one line per file. The HEIC files need heif-enc with
an encoder plugin on the machine that runs this (CI installs it on the runner, never in the image);
--require-heic makes its absence an error.

Needs the test environment (reportlab, python-docx, openpyxl, Pillow from requirements-dev.lock). The .doc is a
minimal Word 97 binary built by hand: an OLE container with WordDocument and 1Table streams, a FIB and a piece
table over UTF-16 text. A piece-table reader can read it; Word itself may refuse it (no style sheet).
"""
from __future__ import annotations

import io
import struct
import sys
import zipfile
from pathlib import Path

TITLE = "Wniosek o wydanie zaświadczenia"
NOTE = "Formularz syntetyczny do testów. Proszę wypełnić drukowanymi literami."
FIELDS = ["Imię", "Nazwisko", "Numer PESEL", "Adres zamieszkania", "Kod pocztowy", "Miejscowość",
          "Numer telefonu", "Adres e-mail", "Cel wydania zaświadczenia"]
CLOSING = ["Data", "Podpis wnioskodawcy"]
ASCII = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
EXTENSIONS = ("pdf", "docx", "xlsx", "ods", "doc", "png", "jpg", "jpeg", "odt", "tiff", "bmp", "gif", "webp",
              "rtf", "xls", "txt", "heic", "heif")
NEEDS_HEIF_ENC = ("heic", "heif")


def pdf(title: str = TITLE, encrypt: object = None) -> bytes:
    """reportlab's built-in fonts have no Polish letters: the PDF carries the same words without diacritics."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, invariant=1, encrypt=encrypt)
    c.setTitle(title.translate(ASCII))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 780, title.translate(ASCII))
    c.setFont("Helvetica", 9)
    c.drawString(72, 762, NOTE.translate(ASCII))
    y = 730
    c.setFont("Helvetica", 10)
    for label in FIELDS:
        c.drawString(72, y, label.translate(ASCII) + ":")
        if label == "Numer PESEL":
            for i in range(11):
                c.rect(230 + i * 16, y - 3, 14, 14)
        else:
            c.setDash(1, 2)
            c.line(230, y - 2, 520, y - 2)
            c.setDash()
        y -= 32
    c.rect(72, y - 4, 10, 10)
    c.drawString(90, y - 2, "Odbior osobisty")
    c.rect(230, y - 4, 10, 10)
    c.drawString(248, y - 2, "Wysylka na adres")
    y -= 48
    for i, label in enumerate(CLOSING):
        x = 72 + i * 260
        c.setDash(1, 2)
        c.line(x, y, x + 180, y)
        c.setDash()
        c.drawString(x, y - 12, label)
    c.save()
    return buf.getvalue()


def docx() -> bytes:
    import docx as pydocx

    d = pydocx.Document()
    d.core_properties.title = TITLE
    d.add_heading(TITLE, level=1)
    d.add_paragraph(NOTE)
    table = d.add_table(rows=0, cols=2)
    table.style = "Table Grid"
    for label in FIELDS:
        row = table.add_row().cells
        row[0].text = label
        row[1].text = ""
    d.add_paragraph("☐ Odbiór osobisty    ☐ Wysyłka na adres")
    for label in CLOSING:
        d.add_paragraph(f"{label}: ........................................")
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def xlsx() -> bytes:
    import openpyxl
    from openpyxl.styles import Border, Font, Side

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Wniosek"
    ws["A1"] = TITLE
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = NOTE
    thin = Side(style="thin")
    for i, label in enumerate(FIELDS + CLOSING, start=4):
        ws.cell(row=i, column=1, value=label)
        ws.cell(row=i, column=2).border = Border(top=thin, bottom=thin, left=thin, right=thin)
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 50
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def ods() -> bytes:
    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    rows = [f'<table:table-row><table:table-cell office:value-type="string"><text:p>{esc(TITLE)}</text:p>'
            '</table:table-cell></table:table-row>',
            f'<table:table-row><table:table-cell office:value-type="string"><text:p>{esc(NOTE)}</text:p>'
            '</table:table-cell></table:table-row>']
    for label in FIELDS + CLOSING:
        rows.append(f'<table:table-row><table:table-cell office:value-type="string"><text:p>{esc(label)}</text:p>'
                    '</table:table-cell><table:table-cell/></table:table-row>')
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.3">'
        '<office:body><office:spreadsheet><table:table table:name="Wniosek">'
        '<table:table-column table:number-columns-repeated="2"/>'
        + "".join(rows) + "</table:table></office:spreadsheet></office:body></office:document-content>")
    manifest = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3">'
        '<manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.spreadsheet"/>'
        '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
        "</manifest:manifest>")
    buf = io.BytesIO()
    stamp = (2026, 11, 21, 12, 0, 0)
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype", stamp), "application/vnd.oasis.opendocument.spreadsheet",
                   compress_type=zipfile.ZIP_STORED)
        z.writestr(zipfile.ZipInfo("content.xml", stamp), content, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr(zipfile.ZipInfo("META-INF/manifest.xml", stamp), manifest, compress_type=zipfile.ZIP_DEFLATED)
    return buf.getvalue()


# ---- binary Word ---------------------------------------------------------------------------------------------
OLE_FREE, OLE_END, OLE_FAT = 0xFFFFFFFF, 0xFFFFFFFE, 0xFFFFFFFD
SECTOR = 512


def ole(streams: list[tuple[str, bytes]]) -> bytes:
    """An OLE compound file, version 3. Every stream is padded to at least 4096 bytes, so no mini stream is
    needed. Streams are listed in the directory in the order given: entry 1 is the root's child, every next one
    its left sibling (names must come in descending OLE order: longer names first)."""
    padded = []
    for name, body in streams:
        size = max(4096, -(-len(body) // SECTOR) * SECTOR)
        padded.append((name, body.ljust(size, b"\0")))
    fat = [OLE_FAT, OLE_END]
    starts = []
    for _, body in padded:
        start = len(fat)
        n = len(body) // SECTOR
        fat += list(range(start + 1, start + n)) + [OLE_END]
        starts.append(start)
    assert len(fat) <= 128, "one FAT sector only"
    fat += [OLE_FREE] * (128 - len(fat))

    header = bytearray(SECTOR)
    header[0:8] = bytes.fromhex("d0cf11e0a1b11ae1")
    struct.pack_into("<HHHHH", header, 24, 0x3E, 3, 0xFFFE, 9, 6)
    struct.pack_into("<IIIIIIIII", header, 40, 0, 1, 1, 0, 4096, OLE_END, 0, OLE_END, 0)
    struct.pack_into("<109I", header, 76, *([0] + [OLE_FREE] * 108))

    def entry(name: str, kind: int, left: int, right: int, child: int, start: int, size: int) -> bytes:
        raw = (name + "\0").encode("utf-16-le") if name else b""
        return struct.pack("<64sHBBIII16sIQQIQ", raw.ljust(64, b"\0"), len(raw), kind, 1, left, right, child,
                           b"\0" * 16, 0, 0, 0, start, size)
    entries = [entry("Root Entry", 5, OLE_FREE, OLE_FREE, 1, OLE_END, 0)]
    for i, (name, body) in enumerate(padded, start=1):
        left = i + 1 if i < len(padded) else OLE_FREE
        entries.append(entry(name, 2, left, OLE_FREE, OLE_FREE, starts[i - 1], len(body)))
    while len(entries) % 4:
        entries.append(entry("", 0, OLE_FREE, OLE_FREE, OLE_FREE, 0, 0))
    assert len(entries) == 4, "one directory sector only"
    return bytes(header) + struct.pack("<128I", *fat) + b"".join(entries) + b"".join(b for _, b in padded)


def doc() -> bytes:
    """Word 97 binary: FIB (nFib 0xC1, table stream 1Table) and a CLX with one uncompressed piece."""
    lines = [TITLE, NOTE] + [f"{label}: ........................................" for label in FIELDS + CLOSING]
    text = "\r".join(lines) + "\r"
    ccp = len(text)
    fc_text = 1024
    fib = bytearray(fc_text)
    struct.pack_into("<HHHHHH", fib, 0, 0xA5EC, 0x00C1, 0, 0x0415, 0, 0x1200)  # fWhichTblStm, fExtChar
    struct.pack_into("<H", fib, 12, 0x00BF)
    struct.pack_into("<H", fib, 32, 14)          # csw
    struct.pack_into("<H", fib, 62, 22)          # cslw
    body = bytes(fib) + text.encode("utf-16-le")
    struct.pack_into("<I", fib, 64, len(body))   # cbMac
    struct.pack_into("<I", fib, 76, ccp)         # ccpText
    struct.pack_into("<H", fib, 152, 0x5D)       # cbRgFcLcb
    plc = struct.pack("<II", 0, ccp) + struct.pack("<HIH", 0, fc_text, 0)  # aCP[2], one PCD (uncompressed)
    clx = b"\x02" + struct.pack("<I", len(plc)) + plc
    struct.pack_into("<II", fib, 154 + 33 * 8, 0, len(clx))  # fcClx, lcbClx
    word = bytes(fib) + text.encode("utf-16-le")
    return ole([("WordDocument", word), ("1Table", clx)])


# ---- images --------------------------------------------------------------------------------------------------
def _page():
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("L", (1240, 1754), 255)  # A4 at 150 dpi, grey scale
    d = ImageDraw.Draw(img)
    try:
        big, small = ImageFont.load_default(size=40), ImageFont.load_default(size=28)
    except TypeError:  # an old Pillow without the scalable default font
        big = small = ImageFont.load_default()
    d.text((120, 120), TITLE, font=big, fill=0)
    d.text((120, 190), NOTE, font=small, fill=0)
    y = 290
    for label in FIELDS + CLOSING:
        d.text((120, y), label + ":", font=small, fill=0)
        if label == "Numer PESEL":
            for i in range(11):
                d.rectangle((520 + i * 44, y - 6, 558 + i * 44, y + 36), outline=0, width=2)
        else:
            for x in range(520, 1120, 12):
                d.line((x, y + 32, x + 5, y + 32), fill=0, width=2)
        y += 96
    return img


def png() -> bytes:
    buf = io.BytesIO()
    _page().save(buf, "PNG", optimize=True)
    return buf.getvalue()


def jpeg() -> bytes:
    buf = io.BytesIO()
    _page().save(buf, "JPEG", quality=85)
    return buf.getvalue()


def tiff() -> bytes:
    """Two frames: the form, then a second page that carries the closing lines only (each frame is a page)."""
    from PIL import Image, ImageDraw, ImageFont

    second = Image.new("L", (1240, 1754), 255)
    d = ImageDraw.Draw(second)
    try:
        font = ImageFont.load_default(size=28)
    except TypeError:
        font = ImageFont.load_default()
    d.text((120, 120), "Strona druga: oświadczenia", font=font, fill=0)
    d.text((120, 200), "Podpis wnioskodawcy:", font=font, fill=0)
    d.line((520, 232, 1120, 232), fill=0, width=3)
    buf = io.BytesIO()
    _page().save(buf, "TIFF", save_all=True, append_images=[second], compression="tiff_lzw")
    return buf.getvalue()


def bmp() -> bytes:
    buf = io.BytesIO()
    _page().convert("1").save(buf, "BMP")  # 1 bit: a grey BMP of this size would be 2 MB
    return buf.getvalue()


def gif() -> bytes:
    buf = io.BytesIO()
    _page().save(buf, "GIF")
    return buf.getvalue()


def webp() -> bytes:
    buf = io.BytesIO()
    _page().save(buf, "WEBP", lossless=True)
    return buf.getvalue()


def odt() -> bytes:
    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    rows = "".join(
        f'<table:table-row><table:table-cell office:value-type="string"><text:p>{esc(label)}:</text:p>'
        '</table:table-cell><table:table-cell><text:p/></table:table-cell></table:table-row>'
        for label in FIELDS + CLOSING)
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.3">'
        f'<office:body><office:text><text:h text:outline-level="1">{esc(TITLE)}</text:h>'
        f'<text:p>{esc(NOTE)}</text:p>'
        f'<table:table table:name="Tabela1"><table:table-column table:number-columns-repeated="2"/>{rows}</table:table>'
        '</office:text></office:body></office:document-content>')
    manifest = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3">'
        '<manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>'
        '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
        "</manifest:manifest>")
    buf = io.BytesIO()
    stamp = (2026, 11, 21, 12, 0, 0)
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype", stamp), "application/vnd.oasis.opendocument.text",
                   compress_type=zipfile.ZIP_STORED)
        z.writestr(zipfile.ZipInfo("content.xml", stamp), content, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr(zipfile.ZipInfo("META-INF/manifest.xml", stamp), manifest, compress_type=zipfile.ZIP_DEFLATED)
    return buf.getvalue()


# ---- WP-F20f: rtf, xls, txt, heic, owner-password pdf, apng, a .doc that holds RTF ---------------------------------
BS = chr(92)   # one backslash: RTF control words are written as BS + word


def rtf() -> bytes:
    """cp1250 RTF (the diacritics are raw cp1250 bytes), a two-column table, two checkbox form fields."""
    def w(text: str) -> str:
        return text.replace("@", BS)   # "@par" stands for the RTF word par

    def cell(text: str) -> str:
        return w(f"@pard@intbl {text}@cell")

    rows = "".join(w("@trowd@cellx3600@cellx9000") + cell(label + ":") + cell("") + w("@row") + "\n"
                   for label in FIELDS)
    box = w("{@field{@*@fldinst FORMCHECKBOX {@*@formfield{@fftype1@ffres0}}}{@fldrslt}}")
    body = (w(f"@pard@b {TITLE}@b0@par") + "\n" + w(f"@pard {NOTE}@par") + "\n" + rows +
            w(f"@pard {box} Odbiór osobisty    {box} Wysyłka na adres@par") + "\n" +
            "".join(w(f"@pard {label}: ........................................@par") + "\n" for label in CLOSING))
    head = w("{@rtf1@ansi@ansicpg1250@deff0{@fonttbl{@f0@fnil Arial;}}{@colortbl;@red0@green0@blue0;}")
    return (head + body + "}").encode("cp1250")


def _rec(rid: int, body: bytes) -> bytes:
    return struct.pack("<HH", rid, len(body)) + body


def xls() -> bytes:
    """A BIFF8 workbook of one sheet inside a compound file (no writer library is installed): labels, a bold title,
    boxed empty cells next to the labels. XF 15 plain, 16 bold, 17 boxed; the first 15 XFs are style XFs."""
    def font(weight: int) -> bytes:
        return _rec(0x0031, struct.pack("<HHHHHBBBB", 200, 0, 0x7FFF, weight, 0, 0, 0, 0, 0) + bytes([5, 0]) + b"Arial")

    def xf(font_i: int, style: bool, borders: int = 0) -> bytes:
        return _rec(0x00E0, struct.pack("<HHHBBBBIIH", font_i, 0, 0xFFF5 if style else 0x0001, 0, 0, 0,
                                        0xFC if style else 0, borders, 0, 0))
    version = 0x0600
    glob = _rec(0x0809, struct.pack("<HHHHII", version, 0x0005, 0x0DBB, 0x07CC, 0, 6))
    glob += _rec(0x0042, struct.pack("<H", 1200)) + font(400) + font(700)
    glob += b"".join(xf(0, True) for _ in range(15)) + xf(0, False) + xf(1, False) + xf(0, False, borders=0x1111)
    name = b"Wniosek"
    eof = _rec(0x000A, b"")
    sheet_at = len(glob) + 4 + 4 + 2 + 2 + len(name) + len(eof)
    glob += _rec(0x0085, struct.pack("<IBB", sheet_at, 0, 0) + bytes([len(name), 0]) + name) + eof
    labels = [TITLE, NOTE, ""] + FIELDS + CLOSING
    sh = _rec(0x0809, struct.pack("<HHHHII", version, 0x0010, 0x0DBB, 0x07CC, 0, 6))
    sh += _rec(0x0200, struct.pack("<IIHHH", 0, len(labels), 0, 2, 0))
    for r, text in enumerate(labels):
        if not text:
            continue
        text = text.translate(ASCII)
        sh += _rec(0x0204, struct.pack("<HHHHB", r, 0, 16 if r == 0 else 15, len(text), 0) + text.encode("latin-1"))
        if r >= 3:
            sh += _rec(0x0201, struct.pack("<HHH", r, 1, 17))   # a blank cell with a box
    sh += _rec(0x000A, b"")
    return ole([("Workbook", glob + sh)])


def txt() -> bytes:
    lines = [TITLE, NOTE, ""] + [f"{label}: ........................................" for label in FIELDS + CLOSING]
    return ("\n".join(lines) + "\n").encode("utf-8")


def heic() -> bytes:
    """Made by heif-enc on the CI runner only (an x265 plugin installed THERE, never in the image)."""
    import shutil
    import subprocess
    import tempfile

    if not shutil.which("heif-enc"):
        raise FileNotFoundError("heif-enc is not installed")
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp, "form.png"), Path(tmp, "form.heic")
        _page().convert("RGB").save(src, "PNG")
        subprocess.run(["heif-enc", "-q", "70", str(src), "-o", str(dst)], check=True, capture_output=True, timeout=120)
        return dst.read_bytes()


def pdf_owner_password() -> bytes:
    """Encrypted with an owner password only: it opens with the empty user password."""
    from reportlab.lib.pdfencrypt import StandardEncryption

    return pdf(encrypt=StandardEncryption(userPassword="", ownerPassword="owner-synthetic", canPrint=0, canModify=0))


def apng() -> bytes:
    """An animated PNG of two frames: the form, then a blank page. The first frame is the form."""
    from PIL import Image

    buf = io.BytesIO()
    _page().save(buf, "PNG", save_all=True, append_images=[Image.new("L", (1240, 1754), 255)], duration=500, loop=0)
    return buf.getvalue()


BUILDERS = {"pdf": pdf, "docx": docx, "xlsx": xlsx, "ods": ods, "doc": doc, "png": png, "jpg": jpeg, "jpeg": jpeg,
            "odt": odt, "tiff": tiff, "bmp": bmp, "gif": gif, "webp": webp, "rtf": rtf, "xls": xls, "txt": txt}
# More files of kinds that already have an extension above (WP-F20f). Each converts like the plain ones.
EXTRA_BUILDERS = {"wniosek-owner.pdf": pdf_owner_password, "wniosek-anim.png": apng, "wniosek-rtf.doc": rtf}


def write_all(out: Path, require_heic: bool = False) -> list[Path]:
    """Without heif-enc the two HEIC files are left out (a laptop); require_heic=True makes that an error (CI)."""
    out.mkdir(parents=True, exist_ok=True)
    written = []
    heic_bytes = None
    for ext in EXTENSIONS:
        path = out / f"wniosek.{ext}"
        if ext in NEEDS_HEIF_ENC:
            try:
                heic_bytes = heic_bytes or heic()
            except FileNotFoundError:
                if require_heic:
                    raise
                continue
            path.write_bytes(heic_bytes)
        else:
            path.write_bytes(BUILDERS[ext]())
        written.append(path)
    for name, build in EXTRA_BUILDERS.items():
        (out / name).write_bytes(build())
        written.append(out / name)
    return written


def main(argv: list[str]) -> int:
    flags = [a for a in argv if a.startswith("--")]
    argv = [a for a in argv if not a.startswith("--")]
    if len(argv) != 1 or set(flags) - {"--require-heic"}:
        print(__doc__.split("\n\n")[1] + " [--require-heic]", file=sys.stderr)
        return 2
    for path in write_all(Path(argv[0]), require_heic="--require-heic" in flags):
        print(f"{path.name}\t{path.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
