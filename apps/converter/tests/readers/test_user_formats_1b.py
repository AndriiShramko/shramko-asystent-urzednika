"""WP-F20f stage 1b: PDF with an owner password, a broken annotation, animated images, big JPEG, file names, HEIC reader.
Every file is built in the test from code (reportlab, Pillow); nothing of the archive is read."""
from __future__ import annotations

import io
import os
import stat
import sys

import pytest
from PIL import Image, ImageDraw
from readers_builders import pdf_bytes

from app import pipeline, readers
from app.config import Settings
from app.guard import ProblemError, clean_name, inspect_upload
from app.readers import ReaderError, _ocr, heic, read_document
from app.readers._base import ReadOptions

S = Settings(auth_mode="off", max_upload_bytes=20_000_000)


@pytest.fixture(autouse=True)
def no_engine():
    _ocr.set_engine(None, disabled=True)
    yield
    _ocr.set_engine(None)


def draw_form(c) -> None:  # noqa: ANN001
    c.setFont("Helvetica", 11)
    c.drawString(56, 780, "WNIOSEK TESTOWY O WYDANIE ZASWIADCZENIA")
    c.drawString(56, 740, "Imie i nazwisko wnioskodawcy ...............................")
    c.drawString(56, 710, "Adres zamieszkania ................................................")
    c.rect(56, 670, 12, 12)
    c.drawString(76, 672, "Wyrazam zgode")


# ---- 5. PDF ------------------------------------------------------------------------------------------------------

def encrypted_pdf(user: str, owner: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.pdfencrypt import StandardEncryption
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, invariant=1,
                      encrypt=StandardEncryption(userPassword=user, ownerPassword=owner, canPrint=0, canModify=0))
    draw_form(c)
    c.save()
    return buf.getvalue()


def test_pdf_with_owner_password_opens_and_converts():
    data = encrypted_pdf("", "owner-secret")
    assert b"/Encrypt" in data
    info = inspect_upload("a.pdf", data, S)
    assert info.kind == "pdf"
    m = read_document(data, "pdf")
    assert any("Adres zamieszkania" in r.text for r in m.pages[0].runs)
    res = pipeline.run(data, "a.pdf", S)
    assert res.form["tabs"] and res.sidecar["counts"]["fields"] >= 2


def test_pdf_with_user_password_is_refused_with_the_plain_reason():
    data = encrypted_pdf("open-me", "owner-secret")
    with pytest.raises(ReaderError) as e:
        read_document(data, "pdf")
    assert e.value.code == "ENCRYPTED"
    with pytest.raises(ProblemError) as p:
        pipeline.run(data, "a.pdf", S)
    assert p.value.detail == "Plik PDF jest chroniony hasłem otwarcia; usługa nie zna hasła."


def pdf_with_legacy_annotation(count: int = 1) -> bytes:
    """A link annotation whose /Contents holds bytes that are neither UTF-8 nor UTF-16 (a legacy 8-bit string)."""
    def draw(c):  # noqa: ANN001
        draw_form(c)
        for i in range(count):
            c.bookmarkPage(f"k{i}")
            c.linkAbsolute("ABCDE", f"k{i}", (56, 700 - 30 * i, 300, 720 - 30 * i), Border="[0 0 0]")
    data = pdf_bytes(draw)
    assert data.count(b"(ABCDE)") == count
    return data.replace(b"(ABCDE)", b"(\xf3tek\xf3)")   # same length, so the cross-reference table stays right


def test_legacy_bytes_in_an_annotation_do_not_sink_the_page():
    data = pdf_with_legacy_annotation(2)
    m = read_document(data, "pdf")
    assert len(m.pages) == 1 and any("Adres zamieszkania" in r.text for r in m.pages[0].runs)
    assert not [w for w in m.warnings if "form fields" in (w.detail or "")]   # the bad string is dropped, not a failed pass
    assert pipeline.run(data, "a.pdf", S).form["tabs"]


def test_a_broken_widget_pass_keeps_the_page_and_says_so(monkeypatch):
    from app.readers import pdf as pdf_module

    def boom(page, ids):  # noqa: ANN001
        raise KeyError("Rect")
    monkeypatch.setattr(pdf_module, "_widgets", boom)
    m = read_document(pdf_bytes(draw_form), "pdf")
    assert m.pages[0].runs and not m.pages[0].widgets
    assert any(w.code == "UNREADABLE_PART" and "KeyError" in (w.detail or "") for w in m.warnings)


def test_the_catch_all_keeps_the_exception_class(monkeypatch):
    from app.readers import pdf as pdf_module

    monkeypatch.setattr(pdf_module, "_runs", lambda chars, ids: (_ for _ in ()).throw(UnicodeDecodeError("x", b"", 0, 1, "y")))
    with pytest.raises(ReaderError) as e:
        read_document(pdf_bytes(draw_form), "pdf")
    assert "UnicodeDecodeError" in e.value.reason


# ---- 6. images ---------------------------------------------------------------------------------------------------

def scan(width: int = 400, height: int = 300, shade: int = 255) -> Image.Image:
    img = Image.new("L", (width, height), shade)
    d = ImageDraw.Draw(img)
    d.rectangle((20, 20, width // 2, 60), outline=0, width=3)
    d.line((20, 120, width - 20, 120), fill=0, width=3)
    return img


def test_animated_png_gives_its_first_frame():
    out = io.BytesIO()
    frames = [scan(shade=255), scan(shade=200), scan(shade=120)]
    frames[0].save(out, format="PNG", save_all=True, append_images=frames[1:], duration=100, loop=0)
    data = out.getvalue()
    assert b"acTL" in data
    info = inspect_upload("a.png", data, S)
    assert any("klatek" in w for w in info.warnings)
    m = read_document(data, "png")
    assert len(m.pages) == 1 and m.pages[0].ink and m.pages[0].lines


def test_multi_picture_jpeg_gives_its_first_picture():
    out = io.BytesIO()
    a, b = scan().convert("RGB"), scan(shade=200).convert("RGB")
    a.save(out, format="MPO", save_all=True, append_images=[b])
    data = out.getvalue()
    assert Image.open(io.BytesIO(data)).n_frames == 2
    info = inspect_upload("a.jpg", data, S)
    assert info.kind == "jpeg" and any("klatek" in w for w in info.warnings)
    m = read_document(data, "jpeg")
    assert len(m.pages) == 1 and m.pages[0].lines


def jpeg(width: int, height: int) -> bytes:
    out = io.BytesIO()
    scan(width, height).save(out, format="JPEG", quality=85)
    return out.getvalue()


def test_a_jpeg_over_the_pixel_budget_is_drafted_not_refused():
    small = Settings(auth_mode="off", max_upload_bytes=20_000_000, max_pixels=500_000)
    data = jpeg(1000, 800)                      # 800 000 pixels: over the budget, within twice the budget
    info = inspect_upload("a.jpg", data, small)
    assert any("zmniejszonej rozdzielczości" in w for w in info.warnings)
    opts = ReadOptions(max_pixels=500_000)
    m = read_document(data, "jpeg", opts)
    page = m.pages[0]
    assert page.width * page.height <= 500_000 * (72 / 200) ** 2 + 1                 # decoded at 1/2: 500 x 400
    assert any("decoded at" in (w.detail or "") for w in m.warnings)


def test_the_hard_limit_stays_a_refusal():
    small = Settings(auth_mode="off", max_upload_bytes=20_000_000, max_pixels=500_000)
    data = jpeg(1500, 800)                      # 1 200 000 pixels: more than twice the budget
    with pytest.raises(ProblemError) as e:
        inspect_upload("a.jpg", data, small)
    assert e.value.code == "TOO_MANY_PIXELS"
    with pytest.raises(ReaderError) as r:
        read_document(data, "jpeg", ReadOptions(max_pixels=500_000))
    assert r.value.code == "TOO_LARGE"


def test_a_png_over_the_budget_is_still_refused():
    out = io.BytesIO()
    scan(1000, 800).save(out, format="PNG")
    small = Settings(auth_mode="off", max_upload_bytes=20_000_000, max_pixels=500_000)
    with pytest.raises(ProblemError) as e:
        inspect_upload("a.png", out.getvalue(), small)
    assert e.value.code == "TOO_MANY_PIXELS"


# ---- 7. file names -----------------------------------------------------------------------------------------------

BIDI = chr(0x202E)


@pytest.mark.parametrize("raw,expected,said", [
    ("wniosek.pdf", "wniosek.pdf", False),
    ("wniosek%20.pdf", "wniosek20.pdf", True),
    ("a;b:c.pdf", "abc.pdf", True),
    ("a" + BIDI + "fdp.pdf", "afdp.pdf", True),
    ("a\x00b\n.pdf", "ab.pdf", True),
    ("../../etc/passwd.pdf", "....etcpasswd.pdf", True),
    ("a" * 400 + ".pdf", "a" * 246 + ".pdf", True),
    ("", "plik", True),
    (None, "plik", True),
    (BIDI + "\x07", "plik", True),
])
def test_names_are_cleaned_not_refused(raw, expected, said):
    name, notes = clean_name(raw)
    assert name == expected and len(name) <= 250
    assert bool(notes) is said
    assert all("/" not in name and "\\" not in name and "\x00" not in name for _ in [0])
    if said:
        assert notes[0].startswith("Nazwa pliku została oczyszczona")


def test_a_cleaned_name_reaches_the_upload_info_and_the_sidecar():
    data = pdf_bytes(draw_form)
    info = inspect_upload("wnio%sek;.pdf", data, Settings(auth_mode="off", max_upload_bytes=20_000_000, name_policy="clean"))
    assert info.name == "wniosek.pdf" and info.ext == "pdf" and info.warnings
    res = pipeline.run(data, info.name, S, info.warnings)
    notes = [w for w in res.sidecar["warnings"] if w["code"] == "INPUT_NOTE"]
    assert [w["detail"] for w in notes] == list(info.warnings)


def test_a_name_without_an_extension_is_read_by_its_content():
    data = pdf_bytes(draw_form)
    for raw in (None, "", "wniosek", "pdf"):
        info = inspect_upload(raw, data, S)
        assert info.kind == "pdf" and info.ext == "pdf" and info.warnings
    with pytest.raises(ProblemError) as e:            # no content proof: still refused, the extension rule stays
        inspect_upload("wniosek.exe", data, S)
    assert e.value.code == "EXTENSION"
    with pytest.raises(ProblemError):
        inspect_upload(None, b"\x00\x01\x02\x03 not a known kind \x00", S)


# ---- 8. HEIC -----------------------------------------------------------------------------------------------------

HEIC = b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic" + b"\x00" * 64


def png_scan() -> bytes:
    out = io.BytesIO()
    scan(600, 500).save(out, format="PNG")
    return out.getvalue()


def test_heic_without_the_decoder_is_a_plain_refusal(monkeypatch):
    monkeypatch.setattr(heic, "find_decoder", lambda: None)
    with pytest.raises(ReaderError) as e:
        read_document(HEIC, "heic")
    assert e.value.code == "NO_DECODER"
    with pytest.raises(ProblemError) as p:
        pipeline.run(HEIC, "a.heic", S)
    assert p.value.detail == "Ta instalacja nie ma dekodera HEIC."
    assert "zapisz" not in p.value.detail.lower() and "JPG" not in p.value.detail


def test_heic_goes_through_the_decoder_and_the_image_reader(monkeypatch):
    seen = {}

    def fake_run(argv, **kw):
        seen.update(argv=argv, kw=kw)
        with open(argv[2], "wb") as f:
            f.write(png_scan())
        return type("Done", (), {"returncode": 0, "stdout": b"", "stderr": b""})()

    monkeypatch.setattr(heic, "find_decoder", lambda: "heif-dec")
    monkeypatch.setattr(heic.subprocess, "run", fake_run)
    m = read_document(HEIC, "heic")
    assert m.source.format == "heic" and m.source.reader.startswith("heic.image_")
    assert len(m.pages) == 1 and m.pages[0].lines
    kw = seen["kw"]
    assert kw["timeout"] == 30.0 and "shell" not in kw and isinstance(seen["argv"], list)
    assert os.path.dirname(seen["argv"][1]) == os.path.dirname(seen["argv"][2]) == kw["cwd"]
    assert not os.path.exists(kw["cwd"])               # its own folder is gone
    assert "EDENAI_API_KEY" not in kw["env"]


def test_heic_decoder_failures_are_reader_errors(monkeypatch):
    monkeypatch.setattr(heic, "find_decoder", lambda: "heif-dec")

    def bad(argv, **kw):
        return type("Done", (), {"returncode": 1, "stdout": b"", "stderr": b""})()

    monkeypatch.setattr(heic.subprocess, "run", bad)
    with pytest.raises(ReaderError) as e:
        read_document(HEIC, "heic")
    assert e.value.code == "UNREADABLE" and "code 1" in e.value.reason

    def silent(argv, **kw):
        return type("Done", (), {"returncode": 0, "stdout": b"", "stderr": b""})()

    monkeypatch.setattr(heic.subprocess, "run", silent)
    with pytest.raises(ReaderError) as e:
        read_document(HEIC, "heic")
    assert "no image" in e.value.reason

    def slow(argv, **kw):
        raise heic.subprocess.TimeoutExpired(argv, kw["timeout"])

    monkeypatch.setattr(heic.subprocess, "run", slow)
    with pytest.raises(ReaderError) as e:
        read_document(HEIC, "heic")
    assert "30 s" in e.value.reason


def test_the_png_of_the_decoder_keeps_the_pixel_limit(monkeypatch):
    def fake_run(argv, **kw):
        with open(argv[2], "wb") as f:
            f.write(png_scan())
        return type("Done", (), {"returncode": 0, "stdout": b"", "stderr": b""})()

    monkeypatch.setattr(heic, "find_decoder", lambda: "heif-dec")
    monkeypatch.setattr(heic.subprocess, "run", fake_run)
    with pytest.raises(ReaderError) as e:
        read_document(HEIC, "heic", ReadOptions(max_pixels=1000))
    assert e.value.code == "TOO_LARGE"


@pytest.mark.linux
def test_heic_with_a_real_child_process(tmp_path, monkeypatch):
    """A stand-in `heif-dec` (a shell script) proves the argument list, the working folder and the timeout end to end."""
    png = tmp_path / "ready.png"
    png.write_bytes(png_scan())
    exe = tmp_path / "heif-dec"
    exe.write_text(f'#!/bin/sh\ncp "{png}" "$2"\n')
    exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    m = read_document(HEIC, "heic")
    assert len(m.pages) == 1 and m.pages[0].lines
    exe.write_text("#!/bin/sh\nsleep 5\n")
    with pytest.raises(ReaderError) as e:
        heic._png_of(HEIC, str(exe), timeout=0.5)
    assert "did not finish" in e.value.reason


def test_the_registry_lists_heic():
    assert "heic" in readers.formats() and sys.platform
