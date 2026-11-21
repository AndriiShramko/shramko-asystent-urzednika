"""Checks of the guard, in the order of design 6.1: name, extension, size, content proof, archive limits,
declared part type. Pure functions over bytes; no file is written and no document is parsed."""
from __future__ import annotations

import hashlib
import io
import struct
import unicodedata
import warnings
import zipfile
from dataclasses import dataclass

from app.config import Settings

from .problems import ProblemError

NAME_MAX = 250
NAME_FORBIDDEN = set(";:><\\/|'*%$")
# Direction overrides, embeddings, isolates and marks: a name must never reorder its own display.
NAME_BIDI = set("‎‏؜‪‫‬‭‮⁦⁧⁨⁩")

EXTENSIONS = ("pdf", "doc", "docx", "ods", "odt", "xlsx", "jpg", "jpeg", "png", "tif", "tiff", "bmp", "gif", "webp")
KIND_OF_EXT = {"jpeg": "jpeg", "jpg": "jpeg", "tif": "tiff"}  # the other extensions are their own kind
# Formats we recognise by content and refuse on purpose, with the reason shown to the person (WP-F20e).
REFUSED_EXT = {
    "heic": "heic", "heif": "heic",
}
HEIC_REASON = ("Zdjęcia HEIC/HEIF nie są obsługiwane (nie mamy dekodera na wolnej licencji). "
               "Zapisz zdjęcie jako JPG (na telefonie: udostępnij lub eksportuj jako JPG) i wyślij ponownie.")
IMAGE_KINDS = ("jpeg", "png", "tiff", "bmp", "gif", "webp")
PILLOW_FORMAT = {"jpeg": "JPEG", "png": "PNG", "tiff": "TIFF", "bmp": "BMP", "gif": "GIF", "webp": "WEBP"}
HEIC_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"hevm", b"hevs", b"mif1", b"msf1"}
KIND_LABEL = {
    "pdf": "dokument PDF", "docx": "dokument DOCX", "xlsx": "arkusz XLSX", "ods": "arkusz ODS",
    "doc": "dokument Word (DOC)", "jpeg": "obraz JPEG", "png": "obraz PNG", "zip": "archiwum ZIP",
    "odt": "dokument ODT", "tiff": "obraz TIFF", "bmp": "obraz BMP", "gif": "obraz GIF", "webp": "obraz WEBP",
    "heic": "zdjęcie HEIC/HEIF (zapisz je jako JPG)",
    "ole": "plik OLE innego typu (na przykład stary arkusz)",
}
ZIP_FORMATS = ("docx", "xlsx", "ods", "odt")
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
}
ZIP_MIME = {"application/zip", "application/x-zip-compressed"}
NEUTRAL_MIME = {"", "application/octet-stream", "binary/octet-stream"}

# Archive limits (design 6.1 item 5), enforced on bytes actually read.
ZIP_MAX_MEMBERS = 2000
ZIP_MAX_MEMBER_BYTES = 50 * 1024 * 1024
ZIP_MAX_TOTAL_BYTES = 200 * 1024 * 1024
ZIP_MAX_RATIO = 100
ZIP_RATIO_FLOOR = 1024 * 1024  # the ratio applies to members above 1 MB: tiny XML parts may legitimately compress 100:1

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

    @property
    def name_hash(self) -> str:
        return hashlib.sha256(self.name.encode("utf-8")).hexdigest()[:16]


def check_name(raw: str | None) -> str:
    """Normalise to NFC and refuse what a name must never hold. The name is never a path and never logged."""
    if not raw:
        raise ProblemError("BAD_NAME", "Brak nazwy pliku.")
    name = unicodedata.normalize("NFC", raw)
    if len(name) > NAME_MAX:
        raise ProblemError("BAD_NAME", f"Nazwa ma więcej niż {NAME_MAX} znaków.")
    for ch in name:
        if ch in NAME_FORBIDDEN:
            raise ProblemError("BAD_NAME", "Nazwa zawiera niedozwolony znak.")
        if unicodedata.category(ch) == "Cc" or ch in NAME_BIDI:
            raise ProblemError("BAD_NAME", "Nazwa zawiera znak sterujący.")
    return name


def check_extension(name: str, strict: bool) -> tuple[str, str]:
    """Return (extension as written in lower case, canonical extension). `.jpe` is `jpeg` unless `strict`."""
    ext = name.rsplit(".", 1)[1].lower() if "." in name else ""
    if ext == "jpe" and not strict:
        return ext, "jpeg"
    if ext in REFUSED_EXT:
        raise ProblemError("EXTENSION", HEIC_REASON)
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


def _ole_kind(data: bytes) -> str:
    try:
        import olefile

        with olefile.OleFileIO(io.BytesIO(data)) as ole:
            return "doc" if ole.exists("WordDocument") else "ole"
    except Exception:  # noqa: BLE001 - a damaged compound file is "OLE of no known kind"
        return "ole"


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


def check_archive(data: bytes, settings: Settings) -> zipfile.ZipFile:
    """Open the ZIP and enforce design 6.1 item 5. Members are decompressed in chunks and counted, never written."""
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
                if head == b"PK\x03\x04":
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
        except (zipfile.BadZipFile, OSError, ValueError, NotImplementedError, EOFError, RuntimeError) as exc:
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
    if data[4:8] == b"ftyp" and data[8:12] in HEIC_BRANDS:
        kinds.add("heic")
    if data.startswith(OLE_MAGIC):
        kinds.add(_ole_kind(data))
    if zipfile.is_zipfile(io.BytesIO(data)) and not _embedded_in_ole(data):
        zf = check_archive(data, settings)
        kinds |= _zip_kinds(zf)
    return kinds


def _check_image(kind: str, data: bytes, settings: Settings) -> None:
    """Header only: decodable, within MAX_PIXELS, one frame (a multi-page TIFF may have up to max_pages; a GIF or WEBP
    with more frames is read at its first frame). The pixels are never decoded here."""
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
    if w * h > settings.max_pixels:
        raise ProblemError("TOO_MANY_PIXELS", f"Obraz ma {w}x{h} pikseli.", limits={"max_pixels": settings.max_pixels})
    if kind == "tiff":
        if frames > settings.max_pages:
            raise ProblemError("TOO_LARGE", f"Obraz ma {frames} stron, limit to {settings.max_pages}.",
                               limits={"max_pages": settings.max_pages})
    elif kind not in ("gif", "webp") and frames != 1:
        raise ProblemError("TYPE_MISMATCH", "Obraz z wieloma klatkami (animacja) nie jest obsługiwany.")


def _has_macros(kind: str, names: list[str]) -> bool:
    if kind in ("docx", "xlsx"):
        return any(n.lower().endswith("vbaproject.bin") for n in names)
    if kind == "ods":
        return any(n.startswith(("Basic/", "Scripts/")) for n in names)
    return False


def inspect_upload(raw_name: str | None, data: bytes, settings: Settings, declared_type: str | None = None) -> UploadInfo:
    """The whole guard for one upload that is already in memory. Raises ProblemError; never parses a body."""
    name = check_name(raw_name)
    written, ext = check_extension(name, settings.strict_extensions)
    kind = KIND_OF_EXT.get(ext, ext)
    if ext == "doc" and settings.doc_reader == "off":
        raise ProblemError("DOC_READER_OFF", "Czytnik plików DOC jest wyłączony w tej instalacji.")
    if len(data) > settings.max_upload_bytes:
        raise too_large(settings)

    kinds = sniff_kinds(data, settings)
    if ext == "doc" and kinds == {"docx"}:
        # Measured on the partner's sets: two forms named .DOC hold a DOCX package (set 7 and reference 5). The
        # content proof is exact, so the file is read as the DOCX it is; the caller sees kind docx, ext doc.
        kind = "docx"
    if kinds == {"heic"}:
        raise ProblemError("TYPE_MISMATCH", HEIC_REASON)
    if len(kinds) > 1:
        raise ProblemError("TYPE_MISMATCH", "Plik spełnia dowody kilku formatów naraz (" + ", ".join(sorted(kinds)) + ").")
    if kinds != {kind}:
        actual = KIND_LABEL.get(next(iter(kinds)), "") if kinds else ""
        what = f"a zawartość to {actual}" if actual else "a zawartość nie jest rozpoznanym formatem"
        raise ProblemError("TYPE_MISMATCH", f"Rozszerzenie .{written}, {what}.")

    if kind in IMAGE_KINDS:
        _check_image(kind, data, settings)

    if declared_type:
        mime = declared_type.split(";", 1)[0].strip().lower()
        allowed = MIME[kind] | (ZIP_MIME if kind in ZIP_FORMATS else set())
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
                      members=members, macros=macros)
