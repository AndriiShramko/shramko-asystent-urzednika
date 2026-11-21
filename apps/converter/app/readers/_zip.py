"""ZIP packages of the sheet readers (XLSX, ODS): open, read one part with limits, parse it safely.

The same limits as the DOCX reader (ReadOptions.max_part_bytes, max_ratio), checked on the sizes the archive
declares before a byte is unpacked, and again on what was really unpacked. XML with a document type or entity
declarations is refused; the parser never resolves entities, never loads a DTD and never touches the network.
"""
from __future__ import annotations

import io
import posixpath
import zipfile

from lxml import etree

from ._base import ReaderError, ReadOptions


def open_package(data: bytes, what: str) -> zipfile.ZipFile:
    try:
        return zipfile.ZipFile(io.BytesIO(data))
    except (zipfile.BadZipFile, ValueError, OSError):
        raise ReaderError("UNREADABLE", f"not a ZIP package, so not {what}") from None


def has(z: zipfile.ZipFile, name: str) -> bool:
    try:
        z.getinfo(name)
    except KeyError:
        return False
    return True


def part_bytes(z: zipfile.ZipFile, name: str, options: ReadOptions) -> bytes | None:
    try:
        info = z.getinfo(name)
    except KeyError:
        return None
    if info.flag_bits & 0x1:
        raise ReaderError("ENCRYPTED", f"the part {name} is encrypted")
    if info.file_size > options.max_part_bytes:
        raise ReaderError("TOO_LARGE", f"the part {name} unpacks to {info.file_size} bytes")
    if info.compress_size and info.file_size / info.compress_size > options.max_ratio:
        raise ReaderError("TOO_LARGE", f"the part {name} unpacks {info.file_size // info.compress_size} times its size")
    try:
        with z.open(info) as f:
            raw = f.read(options.max_part_bytes + 1)
    except (zipfile.BadZipFile, NotImplementedError, OSError, EOFError):
        raise ReaderError("UNREADABLE", f"the part {name} cannot be unpacked") from None
    if len(raw) > options.max_part_bytes:  # the declared size lied
        raise ReaderError("TOO_LARGE", f"the part {name} unpacks to more than {options.max_part_bytes} bytes")
    return raw


def part(z: zipfile.ZipFile, name: str, options: ReadOptions) -> etree._Element | None:
    raw = part_bytes(z, name, options)
    if raw is None:
        return None
    if b"<!DOCTYPE" in raw[:4096] or b"<!ENTITY" in raw:
        raise ReaderError("UNREADABLE", f"the part {name} declares a document type or entities (refused)")
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False,
                             remove_comments=True, remove_pis=True)
    try:
        return etree.fromstring(raw, parser)
    except etree.XMLSyntaxError:
        raise ReaderError("UNREADABLE", f"the part {name} is not well-formed XML") from None


def join(base_dir: str, target: str) -> str:
    """A relationship target resolved against the folder of its source part; absolute targets start at the root."""
    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))
    return posixpath.normpath(posixpath.join(base_dir, target))
