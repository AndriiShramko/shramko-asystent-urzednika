"""Synthetic ODS packages and binary Word files for the F2b reader tests, built in code. Synthetic text only.

ODS: a small ZIP of XML written by hand (no writer dependency). Binary Word: no writer exists here, so the
WordDocument and table streams are assembled byte by byte (FIB, piece table, PAPX and CHPX pages, font table,
text-box bounds) and wrapped in a minimal OLE compound file (version 3, every stream in the regular FAT).
"""
from __future__ import annotations

import io
import struct
import zipfile

# ---------------------------------------------------------------- ODS

ODS_NS = (
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
    'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
    'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" office:version="1.2"'
)
ODS_STYLES = (
    '<style:style style:name="co1" style:family="table-column">'
    '<style:table-column-properties style:column-width="2.54cm"/></style:style>'
    '<style:style style:name="ro1" style:family="table-row">'
    '<style:table-row-properties style:row-height="20pt"/></style:style>'
    '<style:style style:name="ta1" style:family="table"><style:table-properties table:display="true"/></style:style>'
    '<style:style style:name="taH" style:family="table"><style:table-properties table:display="false"/></style:style>'
    '<style:style style:name="ceB" style:family="table-cell">'
    '<style:table-cell-properties fo:border="0.06pt solid #000000"/></style:style>'
    '<style:style style:name="ceBold" style:family="table-cell">'
    '<style:text-properties fo:font-weight="bold" fo:font-size="14pt"/></style:style>'
)


def ods_bytes(tables: str, validations: str = "", styles: str = ODS_STYLES, mimetype: bool = True) -> bytes:
    content = (f'<?xml version="1.0" encoding="UTF-8"?><office:document-content {ODS_NS}>'
               f'<office:automatic-styles>{styles}</office:automatic-styles><office:body><office:spreadsheet>'
               + (f"<table:content-validations>{validations}</table:content-validations>" if validations else "")
               + f"{tables}</office:spreadsheet></office:body></office:document-content>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        if mimetype:
            z.writestr("mimetype", "application/vnd.oasis.opendocument.spreadsheet", compress_type=zipfile.ZIP_STORED)
        z.writestr("content.xml", content)
    return buf.getvalue()


def ods_cell(text: str = "", style: str | None = None, extra: str = "") -> str:
    st = f' table:style-name="{style}"' if style else ""
    body = f"<text:p>{text}</text:p>" if text else ""
    return f"<table:table-cell{st} {extra}>{body}</table:table-cell>"


# ---------------------------------------------------------------- OLE

FREE, END, FATSECT = 0xFFFFFFFF, 0xFFFFFFFE, 0xFFFFFFFD


def ole_bytes(streams: dict[str, bytes]) -> bytes:
    """A version 3 compound file: header, one FAT sector, one directory sector, then each stream padded to sectors
    (every stream at least 4096 bytes, so the mini stream is never needed). At most three streams."""
    assert len(streams) <= 3
    names = list(streams)
    bodies = [streams[n].ljust(4096, b"\0") for n in names]
    bodies = [b.ljust(-(-len(b) // 512) * 512, b"\0") for b in bodies]
    fat = [FATSECT, END]
    starts = []
    for b in bodies:
        n = len(b) // 512
        start = len(fat)
        starts.append(start)
        fat += [start + i + 1 for i in range(n - 1)] + [END]
    assert len(fat) <= 128
    fat += [FREE] * (128 - len(fat))
    header = bytearray(512)
    header[0:8] = bytes.fromhex("d0cf11e0a1b11ae1")
    struct.pack_into("<HHHHH", header, 24, 0x3E, 3, 0xFFFE, 9, 6)
    struct.pack_into("<IIIIIIIII", header, 40, 0, 1, 1, 0, 4096, END, 0, END, 0)
    struct.pack_into("<109I", header, 76, *([0] + [FREE] * 108))

    def entry(name: str, kind: int, right: int, child: int, start: int, size: int) -> bytes:
        raw = (name + "\0").encode("utf-16-le")
        return struct.pack("<64sHBBIII16sIQQIQ", raw.ljust(64, b"\0"), len(raw), kind, 1, FREE, right, child,
                           b"\0" * 16, 0, 0, 0, start, size)

    dir_ = entry("Root Entry", 5, FREE, 1, END, 0)
    for i, n in enumerate(names):
        dir_ += entry(n, 2, i + 2 if i + 1 < len(names) else FREE, FREE, starts[i], max(4096, len(streams[n])))
    dir_ = dir_.ljust(512, b"\0")
    return bytes(header) + struct.pack("<128I", *fat) + dir_ + b"".join(bodies)


# ---------------------------------------------------------------- binary Word

TEXT_C, TEXT_W, PAPX_PN, CHPX_PN = 1024, 2048, 8, 9   # byte offsets of the texts, FKP page numbers


def sprm(code: int, operand: bytes) -> bytes:
    return struct.pack("<H", code) + operand


IN_TABLE = sprm(0x2416, b"\x01")
ROW_END = sprm(0x2416, b"\x01") + sprm(0x2417, b"\x01")
BOLD = sprm(0x0835, b"\x01")


def symbol(font_index: int, code: int) -> bytes:
    return sprm(0x6A09, struct.pack("<HH", font_index, code))


def _fkp(runs: list[tuple[int, int, bytes]], papx: bool) -> bytes:
    """One 512-byte FKP page for contiguous runs (fc0, fc1, grpprl); papx adds an istd of 0 before the grpprl."""
    page = bytearray(512)
    crun = len(runs)
    struct.pack_into(f"<{crun + 1}I", page, 0, *([r[0] for r in runs] + [runs[-1][1]]))
    top = 511
    for i, (_a, _b, grp) in enumerate(runs):
        off = 0
        if grp:
            if papx:
                body = b"\0\0" + grp
                blob = bytes([(len(body) + 1) // 2]) + body if len(body) % 2 else bytes([0, len(body) // 2]) + body
            else:
                blob = bytes([len(grp)]) + grp
            top = (top - len(blob)) & ~1
            page[top:top + len(blob)] = blob
            off = top // 2
        page[4 * (crun + 1) + (13 * i if papx else i)] = off
    page[511] = crun
    assert 4 * (crun + 1) + (13 if papx else 1) * crun < top
    return bytes(page)


def _runs(fcs: list[int], props: dict[int, bytes], width: dict[int, int]) -> list[tuple[int, int, bytes]]:
    """Contiguous FC runs over all characters; a run starts at each character that has properties."""
    cuts = sorted({fcs[0], *(fcs[cp] for cp in props), *(fcs[cp] + width[cp] for cp in props),
                   max(f + width[i] for i, f in enumerate(fcs))} | {min(fcs)})
    by_fc = {fcs[cp]: props[cp] for cp in props}
    return [(a, b, by_fc.get(a, b"")) for a, b in zip(cuts, cuts[1:]) if b > a]


def doc_bytes(main: str, txbx: list[str] | None = None, para: dict[int, bytes] | None = None,
              chars: dict[int, bytes] | None = None, compressed: int = 0, fonts: tuple[str, ...] = ("Times New Roman",
              "Wingdings"), flags: int = 0x0200, nfib: int = 0x00C1, with_papx: bool = True,
              table_name: str | None = None, extra: dict[int, bytes] | None = None) -> bytes:
    """A Word 97 binary document. `main` and the text-box texts use Word's marks (\\r paragraph, \\x07 cell or row
    end, \\x0c page break, \\x13 \\x14 \\x15 fields). The first `compressed` characters are stored as an 8-bit piece,
    the rest as UTF-16. `para` maps the CP of a paragraph mark to its sprms, `chars` the CP of a character to its.
    `extra` maps a fibRgFcLcb97 index to a table-stream structure that holds no stream offsets (PlcSpaMom, DggInfo)."""
    para, chars = para or {}, chars or {}
    boxes = txbx or []
    full = main + "".join(boxes)
    a, b = full[:compressed], full[compressed:]
    fcs = [TEXT_C + i for i in range(len(a))] + [TEXT_W + 2 * i for i in range(len(b))]
    width = {i: (1 if i < len(a) else 2) for i in range(len(full))}
    assert TEXT_C + len(a) <= TEXT_W and TEXT_W + 2 * len(b) <= PAPX_PN * 512
    wd = bytearray(CHPX_PN * 512 + 512)
    wd[TEXT_C:TEXT_C + len(a)] = a.encode("cp1252")
    wd[TEXT_W:TEXT_W + 2 * len(b)] = b.encode("utf-16-le")

    # table stream: Clx, PlcBtePapx, PlcBteChpx, SttbfFfn, PlcftxbxTxt
    tbl = bytearray()
    pcds = []
    cps = [0]
    if a:
        pcds.append(struct.pack("<HIH", 0, (TEXT_C * 2) | 0x40000000, 0))
        cps.append(len(a))
    if b:
        pcds.append(struct.pack("<HIH", 0, TEXT_W, 0))
        cps.append(len(full))
    plc = struct.pack(f"<{len(cps)}I", *cps) + b"".join(pcds)
    clx = b"\x02" + struct.pack("<I", len(plc)) + plc
    fc_clx = len(tbl)
    tbl += clx
    fclcb: dict[int, tuple[int, int]] = {33: (fc_clx, len(clx))}
    if with_papx and full:
        pr = _runs(fcs, para, width)
        wd[PAPX_PN * 512:PAPX_PN * 512 + 512] = _fkp(pr, papx=True)
        bte = struct.pack("<3I", pr[0][0], pr[-1][1], PAPX_PN)
        fclcb[13] = (len(tbl), len(bte))
        tbl += bte
    if chars and full:
        cr = _runs(fcs, chars, width)
        wd[CHPX_PN * 512:CHPX_PN * 512 + 512] = _fkp(cr, papx=False)
        bte = struct.pack("<3I", cr[0][0], cr[-1][1], CHPX_PN)
        fclcb[12] = (len(tbl), len(bte))
        tbl += bte
    ffn = struct.pack("<HH", len(fonts), 0)
    for f in fonts:
        body = b"\0" * 39 + (f + "\0").encode("utf-16-le")
        ffn += bytes([len(body)]) + body
    fclcb[15] = (len(tbl), len(ffn))
    tbl += ffn
    if boxes:
        bounds = [0]
        for t in boxes:
            bounds.append(bounds[-1] + len(t))
        bounds.append(bounds[-1] + 1)  # the dummy last box
        blob = struct.pack(f"<{len(bounds)}I", *bounds) + b"\0" * 22 * (len(bounds) - 1)
        fclcb[56] = (len(tbl), len(blob))
        tbl += blob
    for index, blob in (extra or {}).items():
        fclcb[index] = (len(tbl), len(blob))
        tbl += blob

    lw = [0] * 22
    lw[3], lw[9] = len(main), sum(len(t) for t in boxes)
    fib = bytearray(32)
    struct.pack_into("<HH", fib, 0, 0xA5EC, nfib)
    struct.pack_into("<H", fib, 0x0A, flags)
    fib += struct.pack("<H", 14) + b"\0" * 28 + struct.pack("<H", 22) + struct.pack("<22i", *lw)
    rg = [fclcb.get(i, (0, 0)) for i in range(93)]
    fib += struct.pack("<H", 93) + b"".join(struct.pack("<II", *p) for p in rg)
    assert len(fib) <= TEXT_C
    wd[0:len(fib)] = fib
    name = table_name or ("1Table" if flags & 0x0200 else "0Table")
    return ole_bytes({"WordDocument": bytes(wd), name: bytes(tbl)})
