#!/usr/bin/env python3
"""descriptor_overlay_check.py - does a form descriptor fit its template?

Pre-event research tool (not product code): it fills every field of a descriptor with a
synthetic value, overlays the result on the original template and compares the rendering
with the blank template. Outside the union of the field boxes nothing may change; inside
every filled box there must be ink. It is the measurement behind the "regression_test"
block of data/form-descriptor.example.json and a seed for the visual regression test that
work package WP-B1 writes for the product.

    python tools/descriptor_overlay_check.py DESCRIPTOR.json TEMPLATE.pdf [--out DIR] [--font TTF]

Exit code 1 if the template hash differs from the descriptor, if a pixel changed outside
the mask, or if a filled field left no ink.

Dependencies (all permissive): reportlab, pypdf, pypdfium2, Pillow, numpy.
Only synthetic values are drawn; never run it with a real person's data.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

DPI = 150
MASK_PAD_PT = 1.5
DIFF_THRESHOLD = 30  # sum of absolute RGB differences per pixel

# Synthetic sample values by canonical path (invented person, invented address).
SAMPLES = {
    "person.surname": "PRZYKŁADOWA-ŻÓŁĆ",
    "person.given_names[*]": "ANNA MARIA",
    "person.pesel": "00000000000",
    "person.birth.country": "POLSKA",
    "person.previous_residence_country": "POLSKA",
    "person.birth.date": "01-02-1990",
    "person.birth.place": "BYDGOSZCZ",
    "contact.mobile_phone": "500600700",
    "contact.email": "ANNA@PRZYKLAD.EXAMPLE",
    "person.residence_address.street": "UL. PRZYKŁADOWA",
    "person.residence_address.house_number": "12A",
    "person.residence_address.flat_number": "5",
    "person.residence_address.postal_code": "85-001",
    "person.residence_address.city": "BYDGOSZCZ - ŚRÓDMIEŚCIE",
    "person.residence_address.commune": "M. BYDGOSZCZ",
    "person.residence_address.voivodeship": "KUJAWSKO-POMORSKIE",
    "proxy.person.surname": "PEŁNOMOCNIK",
    "proxy.person.given_names[0]": "JAN",
    "case.place": "BYDGOSZCZ",
    "case.date": "21-11-2026",
}
SKIP_WHO = {"applicant_by_hand", "property_owner_by_hand", "clerk"}  # stay blank on the printout


def sample_for(field: dict) -> str | None:
    if field.get("who_fills") in SKIP_WHO or field["kind"] == "signature":
        return None
    if field["kind"] == "checkbox":
        return "X"
    return SAMPLES.get(field.get("canonical_path", ""), "TEST")


def draw_field(c, field: dict, value: str, page_h: float, font: str) -> None:
    b = field["bbox"]
    size = float(field.get("size", 11))
    kind = field["kind"]
    if kind == "checkbox":
        c.setLineWidth(1.3)
        pad = 2.2
        c.line(b["x0"] + pad, page_h - b["y0"] - pad, b["x1"] - pad, page_h - b["y1"] + pad)
        c.line(b["x0"] + pad, page_h - b["y1"] + pad, b["x1"] - pad, page_h - b["y0"] - pad)
        return
    base = page_h - (b["y0"] + (b["y1"] - b["y0"]) / 2) - size * 0.34
    if kind in ("comb", "date-parts"):
        comb = field["comb"]
        grouped = kind == "date-parts" or comb.get("groups") or "digits_only" in field.get("transform", "")
        chars = [ch for ch in value if ch not in "- "] if grouped else list(value)
        c.setFont(font, size)
        for x0, ch in zip(comb["cells"], chars):
            c.drawCentredString(x0 + comb["cell_w"] / 2, base, ch)
        return
    width = b["x1"] - b["x0"] - 6
    while size > 7 and c.stringWidth(value, font, size) > width:
        size -= 0.5
    c.setFont(font, size)
    c.drawString(b["x0"] + 3, base, value)


def render(pdf_bytes: bytes):
    import numpy as np
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(pdf_bytes)
    return [np.asarray(doc[i].render(scale=DPI / 72).to_pil().convert("RGB")).astype(int) for i in range(len(doc))]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("descriptor")
    ap.add_argument("template")
    ap.add_argument("--out", default=None, help="folder for filled.pdf and page images (git-ignored place)")
    ap.add_argument("--font", default="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    help="TTF with Polish letters used for the check (the product embeds the descriptor's overlay_font)")
    args = ap.parse_args()

    import numpy as np
    from PIL import Image
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    desc = json.loads(Path(args.descriptor).read_text(encoding="utf-8"))
    template = Path(args.template).read_bytes()
    sha = hashlib.sha256(template).hexdigest()
    if sha != desc["source"]["sha256"]:
        print(f"FAIL template hash {sha[:16]} differs from the descriptor {desc['source']['sha256'][:16]}")
        return 1

    page_w, page_h = desc["page_size_pt"]["w"], desc["page_size_pt"]["h"]
    pdfmetrics.registerFont(TTFont("check", args.font))
    n_pages = desc["pages"]
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_w, page_h))
    filled = {p: [] for p in range(1, n_pages + 1)}
    for p in range(1, n_pages + 1):
        for f in desc["fields"]:
            if f["page"] != p:
                continue
            v = sample_for(f)
            if v is not None:
                draw_field(c, f, v, page_h, "check")
                filled[p].append(f["id"])
        c.showPage()
    c.save()

    base = PdfReader(io.BytesIO(template))
    over = PdfReader(io.BytesIO(buf.getvalue()))
    w = PdfWriter()
    for i, page in enumerate(base.pages):
        page.merge_page(over.pages[i])
        w.add_page(page)
    out_pdf = io.BytesIO()
    w.write(out_pdf)

    blank, full = render(template), render(out_pdf.getvalue())
    scale = DPI / 72
    ok = True
    for p in range(1, n_pages + 1):
        a, b = blank[p - 1], full[p - 1]
        diff = np.abs(a - b).sum(axis=2) > DIFF_THRESHOLD
        mask = np.zeros(diff.shape, dtype=bool)
        no_ink = []
        for f in desc["fields"]:
            if f["page"] != p:
                continue
            bb = f["bbox"]
            x0, y0 = int((bb["x0"] - MASK_PAD_PT) * scale), int((bb["y0"] - MASK_PAD_PT) * scale)
            x1, y1 = int((bb["x1"] + MASK_PAD_PT) * scale) + 1, int((bb["y1"] + MASK_PAD_PT) * scale) + 1
            mask[max(y0, 0):y1, max(x0, 0):x1] = True
            if f["id"] in filled[p] and not diff[max(y0, 0):y1, max(x0, 0):x1].any():
                no_ink.append(f["id"])
        inside, outside = int((diff & mask).sum()), int((diff & ~mask).sum())
        verdict = "ok" if outside == 0 and not no_ink else "FAIL"
        ok &= verdict == "ok"
        print(f"page {p}: fields {sum(1 for f in desc['fields'] if f['page'] == p)}, filled {len(filled[p])}, "
              f"changed px inside mask {inside}, outside {outside}, filled without ink {no_ink or 'none'}: {verdict}")
        if args.out:
            out = Path(args.out)
            out.mkdir(parents=True, exist_ok=True)
            Image.fromarray(b.astype("uint8")).save(out / f"filled-page-{p}.png")
    if args.out:
        (Path(args.out) / "filled.pdf").write_bytes(out_pdf.getvalue())
    print("RESULT", "pass" if ok else "FAIL", f"({DPI} dpi, mask = field boxes + {MASK_PAD_PT} pt)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
