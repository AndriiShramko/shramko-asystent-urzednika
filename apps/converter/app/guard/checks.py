"""Checks of the guard, in the order of design 6.1: name, extension, size, content proof, archive limits,
declared part type. Pure functions over bytes; no file is written and no document is parsed."""
from __future__ import annotations

import hashlib
import io
import struct
import unicodedata
import warnings
import zipfile
import zlib
from dataclasses import dataclass

from app.config import Settings

from .problems import ProblemError

NAME_MAX = 250
NAME_FORBIDDEN = set(";:><\\/|'*%$")
# Direction overrides, embeddings, isolates and marks: a name must never reorder its own display.
NAME_BIDI = set("‎‏؜‪‫‬‭‮⁦⁧⁨⁩")

EXTENSIONS = ("pdf", "doc", "docx", "ods", "odt", "xls", "xlsx", "rtf", "txt", "jpg", "jpeg", "png", "tif", "tiff", "bmp",
              "gif", "webp", "heic", "heif")
KIND_OF_EXT = {"jpeg": "jpeg", "jpg": "jpeg", "tif": "tiff", "heif": "heic"}  # the other extensions are their own kind
# Content kinds a reader exists for (heic: stage 1b of WP-F20f). "zip" and "ole" are proofs of a container of no
# known kind: they never count as "the content is exactly one known kind".
READABLE_KINDS = frozenset({"pdf", "doc", "docx", "ods", "odt", "xls", "xlsx", "rtf", "txt", "jpeg", "png", "tiff",
                            "bmp", "gif", "webp", "heic"})
IMAGE_KINDS = ("jpeg", "png", "tiff", "bmp", "gif", "webp")
PILLOW_FORMAT = {"jpeg": "JPEG", "png": "PNG", "tiff": "TIFF", "bmp": "BMP", "gif": "GIF", "webp": "WEBP"}
HEIC_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"hevm", b"hevs", b"mif1", b"msf1"}
TEXT_OK_EXT = frozenset({"txt", "doc", "rtf", "xls"})   # kinds whose extension may hold plain text (WP-F20f)
KIND_LABEL = {
    "pdf": "dokument PDF", "docx": "dokument DOCX", "xlsx": "arkusz XLSX", "ods": "arkusz ODS",
    "doc": "dokument Word (DOC)", "jpeg": "obraz JPEG", "png": "obraz PNG", "zip": "archiwum ZIP",
    "odt": "dokument ODT", "tiff": "obraz TIFF", "bmp": "obraz BMP", "gif": "obraz GIF", "webp": "obraz WEBP",
    "heic": "zdjęcie HEIC/HEIF", "xls": "arkusz XLS", "rtf": "dokument RTF", "txt": "plik tekstowy",
    "ole": "plik OLE innego typu",
}
ZIP_FORMATS = ("docx", "xlsx", "ods", "odt")
# Where an Office package keeps an embedded object (a pasted Excel table or a chart in a DOCX): such a member may be a
# ZIP by its format and is never read (the readers take only the main parts), so it is not "a nested archive"; its bytes
# still count against the size and ratio limits. A macro-enabled one marks the file as having macros.
EMBEDDINGS = ("word/embeddings/", "xl/embeddings/", "ppt/embeddings/")
EMBEDDED_MACRO_EXT = (".xlsm", ".docm", ".pptm", ".xlsb", ".potm", ".dotm", ".xltm")
MIME = {
    "pdf": {"application/pdf"},
    "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    "xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    "ods": {"application/vnd.oasis.opendocument.spreadsheet"},
    "doc": {"application/msword"},
    "jpeg": {"image/jpeg", "image/jpg", "image/pjpeg"},
    "png": {"image/png"},
    "odt": {"application/vnd.oasis.opendocument.text"},
    "tiff": {"image/tiff", "image/x-tiff"},
    "bmp": {"image/bmp", "image/x-ms-bmp", "image/x-bmp"},
    "gif": {"image/gif"},
    "webp": {"image/webp"},
    "xls": {"application/vnd.ms-excel", "application/x-msexcel", "application/excel"},
    "rtf": {"application/rtf", "text/rtf", "text/richtext", "application/x-rtf"},
    "txt": {"text/plain"},
    "heic": {"image/heic", "image/heif", "image/heic-sequence", "image/heif-sequence"},
}
ZIP_MIME = {"application/zip", "application/x-zip-compressed"}
NEUTRAL_MIME = {"", "application/octet-stream", "binary/octet-stream"}

# Archive limits (design 6.1 item 5), enforced on bytes actually read.
ZIP_MAX_MEMBERS = 2000
ZIP_MAX_MEMBER_BYTES = 50 * 1024 * 1024
ZIP_MAX_TOTAL_BYTES = 200 * 1024 * 1024
ZIP_MAX_RATIO = 100
ZIP_RATIO_FLOOR = 1024 * 1024  # the ratio applies to members above 1 MB: tiny XML parts may legitimately compress 100:1

JPEG_DRAFT_FACTOR = 2   # a JPEG up to this many times the pixel budget is decoded reduced (same value as in readers/_raster.py)

OLE_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")


@dataclass(frozen=True)
class UploadInfo:
    """What the guard established. `name` is the normalised name: the caller keeps only its hash and extension."""
    name: str
    ext: str
    kind: str
    size: int
    sha256: str
    members: int | None = None
    macros: bool = False
    warnings: tuple[str, ...] = ()   # Polish sentences for the sidecar: the extension disagreed with the content

    @property
    def name_hash(self) -> str:
        return hashlib.sha256(self.name.encode("utf-8")).hexdigest()[:16]


def clean_name(raw: str | None) -> tuple[str, tuple[str, ...]]:
    """Normalise to NFC and clean what a name must never hold (WP-F20f, D25: the user is never asked to rename a file).
    Returns the cleaned name (fallback "plik") and the Polish sentences that say what was changed. The name is never a
    path and never logged: only its extension and its hash are kept by the caller."""
    changes: list[str] = []
    name = unicodedata.normalize("NFC", raw or "")
    kept = []
    removed_bad = removed_ctl = False
    for ch in name:
        if ch in NAME_FORBIDDEN:
            removed_bad = True
        elif unicodedata.category(ch) in ("Cc", "Cf") or ch in NAME_BIDI or ch in "\u2028\u2029":
            removed_ctl = True
        else:
            kept.append(ch)
    name = "".join(kept).strip()
    if removed_bad:
        changes.append("usunięto niedozwolone znaki")
    if removed_ctl:
        changes.append("usunięto znaki sterujące")
    if len(name) > NAME_MAX:
        ext = name.rsplit(".", 1)[1] if "." in name else ""
        keep = ("." + ext) if 0 < len(ext) <= 10 else ""
        name = name[: NAME_MAX - len(keep)] + keep
        changes.append(f"skrócono do {NAME_MAX} znaków")
    if not name or name == "." or not name.strip("."):
        name = "plik"
        changes.append("nazwa była pusta, przyjęto „plik”")
    notes = (f"Nazwa pliku została oczyszczona ({'; '.join(changes)}); usługa nie używa jej do niczego poza rozszerzeniem.",) if changes else ()
    return name, notes


def check_name(raw: str | None) -> str:
    """The cleaned name (see `clean_name`); kept for callers that need only the name."""
    return clean_name(raw)[0]


def check_extension(name: str, strict: bool) -> tuple[str, str]:
    """Return (extension as written in lower case, canonical extension). `.jpe` is `jpeg` unless `strict`."""
    ext = name.rsplit(".", 1)[1].lower() if "." in name else ""
    if ext == "jpe" and not strict:
        return ext, "jpeg"
    if ext not in EXTENSIONS:
        raise ProblemError("EXTENSION", "Obsługiwane rozszerzenia: " + ", ".join(EXTENSIONS) + ".")
    return ext, ext


def check_declared_length(length: int | None, settings: Settings) -> None:
    """The first look at size: the declared Content-Length, before one byte of the body is read."""
    if length is not None and length > settings.max_upload_bytes:
        raise too_large(settings)


def too_large(settings: Settings) -> ProblemError:
    return ProblemError("TOO_LARGE", f"Plik przekracza {settings.max_upload_bytes} bajtów.",
                        limits={"max_upload_bytes": settings.max_upload_bytes})


# ---- content proofs --------------------------------------------------------------------------------------------

def _eocd_entries(data: bytes) -> int | None:
    """Number of entries the end-of-central-directory record claims, read before the archive is opened."""
    i = data.rfind(b"PK\x05\x06", max(0, len(data) - 65557))
    if i < 0 or i + 22 > len(data):
        return None
    return struct.unpack_from("<H", data, i + 10)[0]


def _zip_kinds(zf: zipfile.ZipFile) -> set[str]:
    names = set(zf.namelist())
    out: set[str] = set()
    if "[Content_Types].xml" in names and "word/document.xml" in names:
        out.add("docx")
    if "[Content_Types].xml" in names and "xl/workbook.xml" in names:
        out.add("xlsx")
    if "mimetype" in names:
        with zf.open("mimetype") as f:
            mime = f.read(100).strip()
        if mime == b"application/vnd.oasis.opendocument.spreadsheet":
            out.add("ods")
        elif mime == b"application/vnd.oasis.opendocument.text":
            out.add("odt")
    return out or {"zip"}


def _ole_kind(data: bytes) -> set[str]:
    try:
        import olefile

        with olefile.OleFileIO(io.BytesIO(data)) as ole:
            kinds = set()
            if ole.exists("WordDocument"):
                kinds.add("doc")
            if ole.exists("Workbook") or ole.exists("Book"):   # BIFF8, BIFF5 (xlrd reads both)
                kinds.add("xls")
            return kinds or {"ole"}
    except Exception:  # noqa: BLE001 - a damaged compound file is "OLE of no known kind"
        return {"ole"}


def _embedded_in_ole(data: bytes) -> bool:
    """True for a compound file (legacy Word, Excel) that merely CONTAINS a zip package in the middle.

    Real Word 97 files carry an Office theme package in one of their streams (measured on the partner's sets: every
    .doc has one). The ZIP proof does not count there, because the archive does not end the file. A zip that does end
    the file, appended to a compound file, is still a polyglot.
    """
    if not data.startswith(OLE_MAGIC):
        return False
    i = data.rfind(b"PK", max(0, len(data) - 65557))
    if i < 0 or i + 22 > len(data):
        return True
    comment = struct.unpack_from("<H", data, i + 20)[0]
    return i + 22 + comment != len(data)


def check_archive(data: bytes, settings: Settings, office_members: bool = False) -> zipfile.ZipFile:
    """Open the ZIP and enforce design 6.1 item 5. Members are decompressed in chunks and counted, never written.
    `office_members` (the batch ZIP only): a member named .docx, .xlsx, .ods or .odt may itself be a ZIP package,
    since that is what those formats are; the guard of that member (`inspect_upload`) checks it on its own later."""
    claimed = _eocd_entries(data)
    if claimed is not None and claimed > ZIP_MAX_MEMBERS:
        raise ProblemError("ARCHIVE_LIMIT", f"Archiwum ma więcej niż {ZIP_MAX_MEMBERS} elementów.")
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except (zipfile.BadZipFile, OSError, ValueError, NotImplementedError) as exc:
        raise ProblemError("UNREADABLE", "Archiwum jest uszkodzone.") from exc
    infos = zf.infolist()
    if len(infos) > ZIP_MAX_MEMBERS:
        raise ProblemError("ARCHIVE_LIMIT", f"Archiwum ma więcej niż {ZIP_MAX_MEMBERS} elementów.")
    total = 0
    for info in infos:
        n = info.orig_filename  # before the library turns backslashes into slashes on Windows
        if ".." in n.replace("\\", "/").split("/") or n.startswith(("/", "\\")) or "\\" in n or (len(n) > 1 and n[1] == ":"):
            raise ProblemError("ARCHIVE_LIMIT", "Archiwum zawiera niedozwoloną nazwę elementu.")
        if info.flag_bits & 0x1:
            raise ProblemError("UNREADABLE", "Archiwum jest zaszyfrowane.")
        if info.is_dir():
            continue
        count = 0
        try:
            with zf.open(info) as f:
                head = f.read(4)
                member_ext = n.rsplit(".", 1)[-1].lower()
                embedded = n.startswith(EMBEDDINGS)   # an object Word/Excel embedded; never read
                if head == b"PK\x03\x04" and not embedded and not (office_members and member_ext in ZIP_FORMATS):
                    raise ProblemError("ARCHIVE_LIMIT", "Archiwum zawiera inne archiwum.")
                count = len(head)
                while True:
                    chunk = f.read(1 << 16)
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > ZIP_MAX_MEMBER_BYTES or total + count > ZIP_MAX_TOTAL_BYTES:
                        raise ProblemError("ARCHIVE_LIMIT", "Rozpakowana zawartość przekracza limit.")
                    if count > ZIP_RATIO_FLOOR and count > ZIP_MAX_RATIO * max(info.compress_size, 1):
                        raise ProblemError("ARCHIVE_LIMIT", f"Stopień kompresji przekracza {ZIP_MAX_RATIO}:1.")
        except (zipfile.BadZipFile, zlib.error, OSError, ValueError, NotImplementedError, EOFError, RuntimeError) as exc:
            raise ProblemError("UNREADABLE", "Archiwum jest uszkodzone.") from exc
        total += count
    return zf


def sniff_kinds(data: bytes, settings: Settings | None = None) -> set[str]:
    """Every content type whose proof the bytes satisfy. One element is a normal file; more is a polyglot."""
    settings = settings or Settings(auth_mode="off")
    kinds: set[str] = set()
    if data.startswith(b"%PDF-") and b"%%EOF" in data[-1024:]:
        kinds.add("pdf")
    if data.startswith(b"\xff\xd8\xff"):
        kinds.add("jpeg")
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        kinds.add("png")
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        kinds.add("tiff")
    if data[:6] in (b"GIF87a", b"GIF89a"):
        kinds.add("gif")
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        kinds.add("webp")
    if data[:2] == b"BM" and len(data) >= 26 and struct.unpack_from("<I", data, 14)[0] in (12, 40, 52, 56, 64, 108, 124):
        kinds.add("bmp")
    if data.startswith(b"{\\rtf"):
        kinds.add("rtf")
    if data[4:8] == b"ftyp" and data[8:12] in HEIC_BRANDS:
        kinds.add("heic")
    if data.startswith(OLE_MAGIC):
        kinds |= _ole_kind(data)
    if zipfile.is_zipfile(io.BytesIO(data)) and not _embedded_in_ole(data):
        zf = check_archive(data, settings)
        kinds |= _zip_kinds(zf)
    if not kinds and decode_text(data) is not None:
        kinds.add("txt")   # the fallback proof: text that no other proof claims
    return kinds


def decode_text(data: bytes) -> tuple[str, str] | None:
    """(text, encoding) when the bytes are plain text: UTF-8, UTF-16 with a byte-order mark, or cp1250; else None.

    Plain text has no NUL byte (UTF-16 apart) and no control character besides tab, line feeds and form feed; cp1250
    is tried last, since nearly any byte string without NUL decodes as a code page."""
    if not data.strip():
        return None
    if data.startswith(b"\xef\xbb\xbf"):
        tries = ("utf-8-sig",)
    elif data.startswith((b"\xff\xfe", b"\xfe\xff")):
        tries = ("utf-16",)
    elif b"\x00" in data:
        return None
    else:
        tries = ("utf-8", "cp1250")
    for enc in tries:
        try:
            text = data.decode(enc)
        except UnicodeDecodeError:
            continue
        if any((c < " " and c not in "\t\n\r\f") or "\x7f" <= c <= "\x9f" for c in text):
            return None
        return text, enc
    return None


def _check_image(kind: str, data: bytes, settings: Settings) -> list[str]:
    """Header only: decodable, within MAX_PIXELS, one frame (a multi-page TIFF may have up to max_pages; a GIF, WEBP, JPEG
    (MPO) or PNG (APNG) with more frames is read at its first frame, with a note). A JPEG with up to JPEG_DRAFT_FACTOR
    times the pixel budget is decoded at a reduced size (the reader's `draft`); above that it stays a refusal. The
    pixels are never decoded here. Returns the Polish notes for the sidecar."""
    from PIL import Image

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with Image.open(io.BytesIO(data), formats=[PILLOW_FORMAT[kind]]) as im:
                w, h = im.size
                frames = getattr(im, "n_frames", 1)
                if kind == "tiff":
                    over = 0
                    for i in range(min(frames, settings.max_pages + 1)):
                        im.seek(i)
                        over = max(over, im.size[0] * im.size[1])
                    w, h = over, 1
    except Image.DecompressionBombError as exc:
        raise ProblemError("TOO_MANY_PIXELS", "Obraz ma za dużo pikseli.",
                           limits={"max_pixels": settings.max_pixels}) from exc
    except Exception as exc:  # noqa: BLE001 - any decoder failure is "cannot read the header"
        raise ProblemError("UNREADABLE", "Nie udało się odczytać nagłówka obrazu.") from exc
    notes: list[str] = []
    budget = settings.max_pixels * (JPEG_DRAFT_FACTOR if kind == "jpeg" else 1)
    if w * h > budget:
        raise ProblemError("TOO_MANY_PIXELS", f"Obraz ma {w}x{h} pikseli.", limits={"max_pixels": settings.max_pixels})
    if w * h > settings.max_pixels:
        notes.append("Zdjęcie ma bardzo dużo pikseli; odczytano je w zmniejszonej rozdzielczości.")
    if kind == "tiff":
        if frames > settings.max_pages:
            raise ProblemError("TOO_LARGE", f"Obraz ma {frames} stron, limit to {settings.max_pages}.",
                               limits={"max_pages": settings.max_pages})
    elif frames > 1:
        notes.append(f"Obraz ma {frames} klatek; odczytano pierwszą." if kind != "gif" and kind != "webp"
                     else "Obraz jest animowany; odczytano pierwszą klatkę.")
    return notes


def _has_macros(kind: str, names: list[str]) -> bool:
    if kind in ("docx", "xlsx"):
        return any(n.lower().endswith("vbaproject.bin")
                   or (n.startswith(EMBEDDINGS) and n.lower().endswith(EMBEDDED_MACRO_EXT)) for n in names)
    if kind == "ods":
        return any(n.startswith(("Basic/", "Scripts/")) for n in names)
    return False


def inspect_upload(raw_name: str | None, data: bytes, settings: Settings, declared_type: str | None = None) -> UploadInfo:
    """The whole guard for one upload that is already in memory. Raises ProblemError; never parses a body."""
    name, warns_name = clean_name(raw_name)
    warns: list[str] = list(warns_name)
    no_ext = "." not in name
    if no_ext:
        # a name with no extension at all: the content decides when it is exactly one readable kind (D25)
        guess = sniff_kinds(data, settings) if len(data) <= settings.max_upload_bytes else set()
        if len(guess) == 1 and next(iter(guess)) in READABLE_KINDS:
            actual = next(iter(guess))
            name = f"{name}.{'jpg' if actual == 'jpeg' else actual}"
            warns.append(f"Plik bez rozszerzenia odczytano jako {KIND_LABEL[actual]}.")
    written, ext = check_extension(name, settings.strict_extensions)
    kind = KIND_OF_EXT.get(ext, ext)
    if ext == "doc" and settings.doc_reader == "off":
        raise ProblemError("DOC_READER_OFF", "Czytnik plików DOC jest wyłączony w tej instalacji.")
    if len(data) > settings.max_upload_bytes:
        raise too_large(settings)

    kinds = sniff_kinds(data, settings)
    if len(kinds) > 1:
        raise ProblemError("TYPE_MISMATCH", "Plik spełnia dowody kilku formatów naraz (" + ", ".join(sorted(kinds)) + ").")
    declared_kind = kind
    if not kinds:
        raise ProblemError("TYPE_MISMATCH", f"Rozszerzenie .{written}, a zawartość nie jest rozpoznanym formatem.")
    if kinds != {kind}:
        actual = next(iter(kinds))
        # Text is the weakest proof: it is read only where the person may well have sent text (a .doc or .xls that is
        # really text or CSV); a "PDF" or an image that is plain text is a damaged file, and stays refused (hostile corpus).
        if actual not in READABLE_KINDS or (actual == "txt" and declared_kind not in TEXT_OK_EXT):
            what = f"a zawartość to {KIND_LABEL[actual]}" if actual in KIND_LABEL else "a zawartość nie jest rozpoznanym formatem"
            raise ProblemError("TYPE_MISMATCH", f"Rozszerzenie .{written}, {what}.")
        # The content is exactly one known kind (a .doc that holds RTF or a DOCX is the common case, measured on the
        # partner's sets): the file is read as the kind it is and the sidecar says so (WP-F20f, D24).
        warns.append(f"Rozszerzenie .{written} nie zgadza się z zawartością; plik odczytano jako {KIND_LABEL[actual]}.")
        kind = actual

    if kind in IMAGE_KINDS:
        warns.extend(_check_image(kind, data, settings))

    if declared_type:
        mime = declared_type.split(";", 1)[0].strip().lower()
        allowed = MIME[kind] | MIME.get(declared_kind, set()) | (ZIP_MIME if kind in ZIP_FORMATS else set())
        if mime not in NEUTRAL_MIME and mime not in allowed:
            raise ProblemError("TYPE_MISMATCH", "Deklarowany typ części nie zgadza się z zawartością pliku.")

    members = None
    macros = False
    if kind in ZIP_FORMATS:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
        members = len(names)
        macros = _has_macros(kind, names)
        if macros and settings.active_content == "strict":
            raise ProblemError("ACTIVE_CONTENT", "Plik zawiera makra, a ACTIVE_CONTENT=strict.")
    return UploadInfo(name=name, ext=ext, kind=kind, size=len(data), sha256=hashlib.sha256(data).hexdigest(),
                      members=members, macros=macros, warnings=tuple(warns))
