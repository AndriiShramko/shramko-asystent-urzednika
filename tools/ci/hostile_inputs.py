#!/usr/bin/env python3
"""Small hostile inputs for the container check (WP-F20i). Built from code at run time: no hostile binary is in git.

Reused from `eval/chain/hostile.py` (the corpus of the chain run): a text file named .pdf, a zero-byte file, a
truncated PDF, a DOCX that really inflates to 300 MB, a PNG whose header claims 100000 x 100000 pixels.
Added here, because the chain corpus has none of them: a DOCX whose document part is an XML entity expansion
("billion laughs"), a DOCX whose zip headers DECLARE four gigabytes for a part of a few bytes, a PNG cut in half.

`build(folder)` writes the files and returns {name: path}. Every file is synthetic and under 400 kB.
"""
from __future__ import annotations

import io
import struct
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(1, str(ROOT))
import make_fixtures  # noqa: E402
from eval.chain import hostile as chain_hostile  # noqa: E402

FROM_CHAIN = ("text-named-pdf.pdf", "empty.pdf", "truncated.pdf", "zip-bomb.docx", "huge-header.png")
DECLARED_SIZE = 0xFFFFFFF0   # just under the zip32 limit: about four gigabytes

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
)
RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="word/document.xml"/></Relationships>'
)
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _docx(document_xml: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/document.xml", document_xml)
    return buf.getvalue()


def docx_entity_expansion(levels: int = 9) -> bytes:
    """word/document.xml declares nested entities; expanded, the one paragraph would be 10**levels words."""
    entities = ['<!ENTITY lol0 "Wniosek ">']
    for n in range(1, levels + 1):
        entities.append(f'<!ENTITY lol{n} "{("&lol%d;" % (n - 1)) * 10}">')
    xml = ('<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE lolz [' + "".join(entities) + "]>"
           f'<w:document xmlns:w="{W}"><w:body><w:p><w:r><w:t>&lol{levels};</w:t></w:r></w:p></w:body></w:document>')
    return _docx(xml)


def docx_declared_size(declared: int = DECLARED_SIZE) -> bytes:
    """An ordinary small DOCX, then the uncompressed size of word/document.xml is overwritten in the local header
    and in the central directory: the file is tiny, its headers promise about four gigabytes."""
    xml = (f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{W}"><w:body><w:p><w:r>'
           "<w:t>Wniosek o wydanie zaświadczenia</w:t></w:r></w:p></w:body></w:document>")
    raw = bytearray(_docx(xml))
    with zipfile.ZipFile(io.BytesIO(bytes(raw))) as z:
        info = z.getinfo("word/document.xml")
        local = info.header_offset
        start_dir = z.start_dir
    assert raw[local:local + 4] == b"PK\x03\x04"
    struct.pack_into("<I", raw, local + 22, declared)          # local file header: uncompressed size
    pos = start_dir
    while raw[pos:pos + 4] == b"PK\x01\x02":                    # central directory entries
        name_len, extra_len, comment_len = struct.unpack_from("<HHH", raw, pos + 28)
        if bytes(raw[pos + 46:pos + 46 + name_len]) == b"word/document.xml":
            struct.pack_into("<I", raw, pos + 24, declared)    # central header: uncompressed size
        pos += 46 + name_len + extra_len + comment_len
    return bytes(raw)


def truncated_png() -> bytes:
    """The raster fixture of the check, cut in the middle of its image data."""
    data = make_fixtures.png()
    return data[: len(data) // 2]


def build(folder: Path) -> dict[str, Path]:
    folder.mkdir(parents=True, exist_ok=True)
    chain = chain_hostile.build(folder / "chain")
    out: dict[str, Path] = {}
    for name in FROM_CHAIN:
        out[name] = folder / name
        out[name].write_bytes(chain[name].read_bytes())
    for name, data in (("entity-expansion.docx", docx_entity_expansion()), ("declared-size.docx", docx_declared_size()),
                       ("truncated.png", truncated_png())):
        out[name] = folder / name
        out[name].write_bytes(data)
    for path in (folder / "chain").iterdir():
        path.unlink()
    (folder / "chain").rmdir()
    return out


if __name__ == "__main__":
    for name, path in sorted(build(Path(sys.argv[1])).items()):
        print(f"{path.stat().st_size:>8}  {name}")
