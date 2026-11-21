#!/usr/bin/env python3
"""build_pakiet.py - reading version of the presentation "Od potrzeby do podpisu".

Writes two self-contained pages (plain HTML, CSS, inline SVG; no network):

  docs/05-hackathon/presentation/pakiet/index.html   Polish, for the jury
  docs/05-hackathon/presentation/pakiet/ru.html      the same pages + Russian commentary (owner only)

Run:  python tools/build_pakiet.py
PDF:  google-chrome --headless --no-pdf-header-footer \
        --print-to-pdf=docs/assets/deck-pakiet/Od-potrzeby-do-podpisu.pdf \
        docs/05-hackathon/presentation/pakiet/index.html

Specification and rules: docs/05-hackathon/presentation/storyboard-pakiet.md
Everything a lead agent edits is in the block "CONTENT" below.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

# ----------------------------------------------------------------------------
# CONTENT: edit here, then run the script again
# ----------------------------------------------------------------------------

# False = nothing is built yet: page 1 carries a "wersja robocza" ribbon and
# page 10 says "W prototypie budujemy". Set True only when WORKS equals
# site-formularze/deck/status.json and the truth table in docs/05-hackathon/jury-qa.md.
BUILT = False

# Measured in the demo run. None = not measured = not shown.
METRICS = {
    "digitise_seconds": None,        # page 5
    "fields_detected_pct": None,     # page 5
    "fields_in_set": None,           # page 9
    "fields_typed_by_clerk": None,   # page 9
    "fields_looked_at": None,        # page 9
    "scan_to_print_seconds": None,   # page 9
}

WORKS = [
    "rozpoznanie pól", "formularz online", "komplet wniosków",
    "przekazanie przez kod QR", "kontrola wyjątków", "wydruk na wzorze",
]
SIMULATED = ["mObywatel", "czytnik dokumentów", "login.gov.pl", "rezerwacja wizyt"]

# The agent door (WP-B10) is optional. False = the page carries the tag "propozycja".
AGENT_DOOR_BUILT = False

SITE_URL = "https://formularze.flyreelstudio.eu"   # change to .../pakiet/ after publishing
SITE_LABEL = "formularze.flyreelstudio.eu"
REPO_LABEL = "github.com/AndriiShramko/shramko-asystent-urzednika"
STATE_DATE = "21.11.2026"

BRAND = "Od potrzeby do podpisu"

# ----------------------------------------------------------------------------
# Colours (the same tokens as site-formularze/deck/deck.css)
# ----------------------------------------------------------------------------
BG, PANEL, LINE = "#0b1020", "#18213f", "#3a4878"
INK, MUTED = "#f5f7ff", "#b3bddc"
ACC, GREEN, RED, BLUE = "#ffc547", "#4ade80", "#ff6b6b", "#6cb2ff"
DARK, PAPER, PAPERLINE = "#0b1020", "#f5f7ff", "#c3cbe6"
DEEP = "#0f1630"

OUT = Path(__file__).resolve().parent.parent / "docs" / "05-hackathon" / "presentation" / "pakiet"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


_ORPHAN = re.compile(r"(?<![\w<])([aiouwzAIOUWZ])\s+(?=\S)")


def nb(s: str) -> str:
    """Polish typography: keep one-letter words (a, i, o, u, w, z) with the next word."""
    return _ORPHAN.sub(lambda m: m.group(1) + "\u00a0", s)


# ----------------------------------------------------------------------------
# SVG helpers
# ----------------------------------------------------------------------------
def tw(s: str, size: float, weight: int = 700) -> float:
    """Estimated text width (Inter / Segoe UI)."""
    return len(s) * size * (0.60 if weight >= 700 else 0.55)


def T(x, y, s, size=24, fill=INK, weight=700, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{extra}>{esc(s)}</text>')


def R(x, y, w, h, rx=12, fill=PANEL, stroke=LINE, sw=2, extra=""):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"{extra}/>')


def pill(cx, cy, s, size=22, fill=PANEL, stroke=LINE, color=INK, padx=18, weight=700):
    w = tw(s, size, weight) + 2 * padx
    h = size * 1.9
    return (R(cx - w / 2, cy - h / 2, w, h, rx=h / 2, fill=fill, stroke=stroke)
            + T(cx, cy + size * 0.36, s, size, color, weight, "middle"))


def defs(uid: str) -> str:
    out = ["<defs>"]
    for name, col in (("m", MUTED), ("a", ACC), ("r", RED), ("g", GREEN), ("b", BLUE)):
        out.append(
            f'<marker id="ah-{uid}-{name}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" '
            f'markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="{col}"/></marker>')
    out.append("</defs>")
    return "".join(out)


def arrow(uid, x1, y1, x2, y2, col="m", flow=True, sw=3, path=None):
    colour = {"m": MUTED, "a": ACC, "r": RED, "g": GREEN, "b": BLUE}[col]
    cls = ' class="flow"' if flow else ""
    dash = ' stroke-dasharray="10 9"' if flow else ""
    if path:
        return (f'<path d="{path}" fill="none" stroke="{colour}" stroke-width="{sw}" stroke-linecap="round"'
                f'{dash}{cls} marker-end="url(#ah-{uid}-{col})"/>')
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour}" stroke-width="{sw}" '
            f'stroke-linecap="round"{dash}{cls} marker-end="url(#ah-{uid}-{col})"/>')


def person(cx, cy, s=1.0, col=BLUE):
    return (f'<circle cx="{cx}" cy="{cy - 30 * s}" r="{17 * s}" fill="{col}"/>'
            f'<path d="M{cx - 32 * s} {cy + 34 * s} a{32 * s} {36 * s} 0 0 1 {64 * s} 0 z" fill="{col}"/>')


def sheet(x, y, w, h, lines=4, fill=PAPER, hl=(), hlcol=ACC, sig=False):
    out = [R(x, y, w, h, rx=max(4, w * 0.06), fill=fill, stroke="none", sw=0)]
    top = y + h * 0.16
    step = (h * 0.62) / max(lines, 1)
    for i in range(lines):
        ly = top + i * step
        lw = w * (0.72 if i % 2 == 0 else 0.56)
        col = hlcol if i in hl else PAPERLINE
        out.append(f'<rect x="{x + w * 0.14}" y="{ly}" width="{lw}" height="{max(3, h * 0.035)}" rx="2" fill="{col}"/>')
    if sig:
        sy = y + h * 0.86
        out.append(f'<line x1="{x + w * 0.14}" y1="{sy}" x2="{x + w * 0.86}" y2="{sy}" stroke="#7d87a8" '
                   f'stroke-width="2" stroke-dasharray="3 5"/>')
        out.append(f'<path d="M{x + w * 0.2} {sy - 6} q{w * 0.08} -{h * 0.09} {w * 0.16} 0 t{w * 0.16} 0 t{w * 0.14} -4" '
                   f'fill="none" stroke="#2f6fd6" stroke-width="3" stroke-linecap="round"/>')
    return "".join(out)


def phone(x, y, w, h, rows=4, hl=()):
    out = [R(x, y, w, h, rx=w * 0.16, fill=DEEP, stroke=LINE, sw=3)]
    top = y + h * 0.2
    step = (h * 0.62) / max(rows, 1)
    for i in range(rows):
        col = ACC if i in hl else "#2a3560"
        out.append(f'<rect x="{x + w * 0.16}" y="{top + i * step}" width="{w * 0.68}" height="{max(5, h * 0.06)}" '
                   f'rx="{max(2, h * 0.03)}" fill="{col}"/>')
    return "".join(out)


def building(cx, by, s=1.0, col=BLUE):
    w = 100 * s
    out = [f'<path d="M{cx - w / 2 - 8 * s} {by - 78 * s} L{cx} {by - 112 * s} L{cx + w / 2 + 8 * s} {by - 78 * s} z" '
           f'fill="none" stroke="{col}" stroke-width="{3 * s}" stroke-linejoin="round"/>']
    for i in range(4):
        px = cx - w / 2 + 8 * s + i * (w - 16 * s) / 3
        out.append(f'<line x1="{px}" y1="{by - 70 * s}" x2="{px}" y2="{by - 12 * s}" stroke="{col}" '
                   f'stroke-width="{4 * s}" stroke-linecap="round"/>')
    out.append(f'<rect x="{cx - w / 2 - 6 * s}" y="{by - 8 * s}" width="{w + 12 * s}" height="{8 * s}" rx="{3 * s}" fill="{col}"/>')
    return "".join(out)


def qr_fake(x, y, s):
    """Decorative code (not scannable): three finder patterns and scattered modules."""
    m = s / 9
    out = [R(x, y, s, s, rx=s * 0.1, fill=PAPER, stroke="none", sw=0)]

    def finder(fx, fy):
        return (f'<rect x="{fx}" y="{fy}" width="{3 * m}" height="{3 * m}" fill="{DARK}"/>'
                f'<rect x="{fx + m * 0.7}" y="{fy + m * 0.7}" width="{m * 1.6}" height="{m * 1.6}" fill="{PAPER}"/>'
                f'<rect x="{fx + m * 1.1}" y="{fy + m * 1.1}" width="{m * 0.8}" height="{m * 0.8}" fill="{DARK}"/>')

    out += [finder(x + m, y + m), finder(x + 5 * m, y + m), finder(x + m, y + 5 * m)]
    for cx_, cy_ in ((5, 5), (6, 6), (7, 5), (5, 7), (7, 7), (4.2, 2), (2, 4.2), (4.2, 4.2), (6.2, 4.2), (4.2, 6.2)):
        out.append(f'<rect x="{x + cx_ * m}" y="{y + cy_ * m}" width="{m * 0.8}" height="{m * 0.8}" fill="{DARK}"/>')
    return "".join(out)


def check(cx, cy, r=14):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{GREEN}"/>'
            f'<path d="M{cx - r * 0.45} {cy} l{r * 0.32} {r * 0.34} l{r * 0.6} -{r * 0.66}" fill="none" '
            f'stroke="{DARK}" stroke-width="{max(2.5, r * 0.22)}" stroke-linecap="round" stroke-linejoin="round"/>')


def warn(cx, cy, r=14, col=ACC):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}"/>'
            f'<rect x="{cx - r * 0.1}" y="{cy - r * 0.58}" width="{r * 0.2}" height="{r * 0.7}" rx="{r * 0.1}" fill="{DARK}"/>'
            f'<circle cx="{cx}" cy="{cy + r * 0.45}" r="{r * 0.13}" fill="{DARK}"/>')


def lock(cx, cy, s=1.0, col=ACC):
    return (f'<path d="M{cx - 8 * s} {cy - 4 * s} v-{6 * s} a{8 * s} {8 * s} 0 0 1 {16 * s} 0 v{6 * s}" fill="none" '
            f'stroke="{col}" stroke-width="{3.5 * s}"/>'
            f'<rect x="{cx - 12 * s}" y="{cy - 4 * s}" width="{24 * s}" height="{19 * s}" rx="{4 * s}" fill="{col}"/>')


def svg(uid, vb_w, vb_h, body, label):
    return (f'<svg viewBox="0 0 {vb_w} {vb_h}" role="img" aria-label="{esc(label)}" '
            f'xmlns="http://www.w3.org/2000/svg">{defs(uid)}{body}</svg>')


# ----------------------------------------------------------------------------
# Drawings
# ----------------------------------------------------------------------------
STEPS = [
    ("Potrzeba", ["Mówię, co chcę", "załatwić"]),
    ("Komplet", ["Wnioski, załączniki,", "opłaty"]),
    ("Dane raz", ["Z telefonu,", "przez kod QR"]),
    ("Kontrola wyjątków", ["System porównuje", "z dokumentem"]),
    ("Podpis", ["Wydruk na", "oryginalnym wzorze"]),
]


def ribbon(uid: str, sub: bool, base: bool) -> str:
    h = 250 + (70 if sub else 0) + (110 if base else 0)
    cxs = [160, 480, 800, 1120, 1440]
    b = []
    for i, cx in enumerate(cxs):
        g = [R(cx - 105, 20, 210, 160, rx=28)]
        cy = 100
        if i == 0:   # speech bubble
            g.append(f'<path d="M{cx - 56} 62 h112 a14 14 0 0 1 14 14 v36 a14 14 0 0 1 -14 14 h-66 l-22 22 v-22 h-24 '
                     f'a14 14 0 0 1 -14 -14 v-36 a14 14 0 0 1 14 -14 z" fill="none" stroke="{ACC}" stroke-width="4" '
                     f'stroke-linejoin="round"/>')
            for dx in (-26, 0, 26):
                g.append(f'<circle cx="{cx + dx}" cy="94" r="6" fill="{ACC}"/>')
        elif i == 1:  # set of forms
            g.append(sheet(cx - 58, 64, 60, 80, 3, fill="#aeb8d8"))
            g.append(sheet(cx - 34, 56, 60, 80, 3, fill="#d5dcf2"))
            g.append(sheet(cx - 8, 64, 60, 80, 3))
            g.append(check(cx + 56, 140, 17))
        elif i == 2:  # phone and code
            g.append(phone(cx - 62, 50, 56, 102, 3, hl=(0, 1)))
            g.append(qr_fake(cx + 6, 72, 58))
        elif i == 3:  # list with exceptions
            g.append(R(cx - 62, 54, 124, 96, rx=12, fill=DEEP))
            for k, yy in enumerate((76, 102, 128)):
                if k < 2:
                    g.append(check(cx - 40, yy, 9))
                    g.append(f'<rect x="{cx - 22}" y="{yy - 4}" width="66" height="8" rx="4" fill="#2a3560"/>')
                else:
                    g.append(warn(cx - 40, yy, 9))
                    g.append(f'<rect x="{cx - 22}" y="{yy - 4}" width="66" height="8" rx="4" fill="{ACC}"/>')
        else:         # signed sheet
            g.append(sheet(cx - 38, 50, 76, 102, 3, sig=True))
        g.append(f'<circle cx="{cx - 80}" cy="45" r="17" fill="{ACC}"/>')
        g.append(T(cx - 80, 52.5, str(i + 1), 21, DARK, 800, "middle"))
        g.append(T(cx, 226, STEPS[i][0], 30, INK, 800, "middle"))
        if sub:
            g.append(T(cx, 262, STEPS[i][1][0], 22, MUTED, 500, "middle"))
            g.append(T(cx, 290, STEPS[i][1][1], 22, MUTED, 500, "middle"))
        b.append(f'<g class="rvo" style="--d:{0.15 + i * 0.18:.2f}s">{"".join(g)}</g>')
        if i < 4:
            b.append(arrow(uid, cx + 116, cy, cxs[i + 1] - 118, cy, "a"))
    if base:
        y0 = h - 92
        g = [R(55, y0, 1490, 66, rx=33, fill="#10183a", stroke=BLUE, sw=2.5)]
        g.append(T(800, y0 + 42, "Krok 0: AI zamienia druk w usługę, człowiek zatwierdza", 27, INK, 700, "middle"))
        for cx in cxs:
            g.append(f'<line x1="{cx}" y1="{y0 - 6}" x2="{cx}" y2="{y0 - 24}" stroke="{BLUE}" stroke-width="3" '
                     f'stroke-linecap="round"/>')
        b.append(f'<g class="rvo" style="--d:1.2s">{"".join(g)}</g>')
    return svg(uid, 1600, h, "".join(b),
               "Pięć kroków: potrzeba, komplet, dane raz, kontrola wyjątków, podpis")


def draw_today() -> str:
    uid = "td"
    b = []
    boxes = {"A": (40, 30), "B": (530, 30), "C": (530, 350), "D": (40, 350)}
    labels = {
        "A": ["Który druk?", "Jaki załącznik?"],
        "B": ["Te same dane", "na każdym druku"],
        "C": ["Ręczne przepisywanie", "i porównywanie z dokumentem"],
        "D": ["Brak → wezwanie,", "co najmniej 7 dni"],
    }
    for n, (k, (x, y)) in enumerate(boxes.items()):
        g = [R(x, y, 430, 260, rx=24)]
        if k == "A":
            g.append(person(x + 95, y + 105, 1.25))
            g.append(T(x + 150, y + 78, "?", 58, ACC, 800))
            for j, (tag, col) in enumerate((("PDF", "#ff8f8f"), ("DOC", "#8fc2ff"), ("RTF", "#c9d1ea"))):
                sx = x + 215 + j * 66
                g.append(sheet(sx, y + 52, 56, 76, 3))
                g.append(R(sx, y + 40, 56, 20, rx=4, fill=col, stroke="none", sw=0))
                g.append(T(sx + 28, y + 55, tag, 13, DARK, 800, "middle"))
        elif k == "B":
            for j in range(3):
                g.append(sheet(x + 50 + j * 118, y + 36, 96, 124, 5, hl=(0, 1)))
            g.append(arrow(uid, x + 150, y + 76, x + 162, y + 76, "a", flow=False, sw=2.5))
            g.append(arrow(uid, x + 268, y + 76, x + 280, y + 76, "a", flow=False, sw=2.5))
        elif k == "C":
            g.append(R(x + 52, y + 56, 132, 84, rx=10, fill=PAPER, stroke="none", sw=0))
            g.append(f'<circle cx="{x + 86}" cy="{y + 90}" r="16" fill="#8fa0cf"/>')
            for j in range(3):
                g.append(f'<rect x="{x + 112}" y="{y + 74 + j * 18}" width="{58 - j * 10}" height="7" rx="3" fill="{PAPERLINE}"/>')
            g.append(sheet(x + 268, y + 36, 100, 126, 5, hl=(1,)))
            g.append(f'<circle cx="{x + 226}" cy="{y + 92}" r="21" fill="none" stroke="{ACC}" stroke-width="5"/>')
            g.append(f'<line x1="{x + 241}" y1="{y + 108}" x2="{x + 256}" y2="{y + 124}" stroke="{ACC}" stroke-width="6" stroke-linecap="round"/>')
        else:
            g.append(R(x + 62, y + 44, 104, 104, rx=12, fill=PAPER, stroke="none", sw=0))
            g.append(f'<path d="M{x + 62} {y + 74} v-18 a12 12 0 0 1 12 -12 h80 a12 12 0 0 1 12 12 v18 z" fill="{RED}"/>')
            g.append(T(x + 114, y + 124, "7+", 44, DARK, 800, "middle"))
            g.append(R(x + 232, y + 62, 124, 82, rx=8, fill=PAPER, stroke="none", sw=0))
            g.append(f'<path d="M{x + 232} {y + 66} l62 44 l62 -44" fill="none" stroke="#7d87a8" stroke-width="4" stroke-linejoin="round"/>')
            g.append(T(x + 294, y + 168, "wezwanie", 17, MUTED, 600, "middle"))
        g.append(warn(x + 40, y + 205, 15, RED))
        g.append(T(x + 68, y + 200, labels[k][0], 23, INK, 700))
        g.append(T(x + 68, y + 229, labels[k][1], 21 if k == "C" else 23, INK, 700))
        b.append(f'<g class="rvo" style="--d:{0.15 + n * 0.3:.2f}s">{"".join(g)}</g>')
    b.append(arrow(uid, 474, 160, 524, 160, "m"))
    b.append(arrow(uid, 745, 294, 745, 344, "m"))
    b.append(arrow(uid, 526, 480, 476, 480, "m"))
    b.append(arrow(uid, 255, 346, 255, 296, "r"))
    b.append(T(272, 327, "jeszcze raz", 18, MUTED, 600))
    return svg(uid, 1000, 640, "".join(b),
               "Dzisiejsza droga: wybór druków, te same dane na każdym druku, ręczne porównywanie, wezwanie do uzupełnienia braków")


def draw_step0() -> str:
    uid = "s0"
    b = []
    for j, tag in enumerate(("PDF", "DOCX", "XLSX")):
        b.append(pill(110 + j * 102, 46, tag, 19, fill="#10183a", stroke=LINE, color=MUTED, padx=14))
    b.append(R(60, 86, 300, 410, rx=14, fill=PAPER, stroke="none", sw=0))
    b.append(f'<rect x="92" y="116" width="170" height="12" rx="4" fill="#8f9ac0"/>')
    cols = [ACC, BLUE, GREEN, "#ff9a62", "#b79cff"]
    for i in range(5):
        y = 160 + i * 62
        b.append(f'<rect x="92" y="{y}" width="{90 - (i % 2) * 22}" height="7" rx="3" fill="{PAPERLINE}"/>')
        if i == 2:
            box = "".join(f'<rect x="{92 + k * 21}" y="{y + 14}" width="18" height="26" rx="3" fill="none" '
                          f'stroke="{cols[i]}" stroke-width="3"/>' for k in range(11))
        else:
            box = (f'<rect x="92" y="{y + 14}" width="{236 - (i % 3) * 30}" height="26" rx="5" fill="none" '
                   f'stroke="{cols[i]}" stroke-width="3"/>')
        b.append(f'<g class="rvo" style="--d:{0.4 + i * 0.25:.2f}s">{box}</g>')
    b.append(pill(210, 540, "AI proponuje pola", 22, fill="#2b2410", stroke=ACC))
    b.append(person(470, 262, 1.3))
    b.append(check(508, 300, 17))
    b.append(T(470, 348, "człowiek", 22, INK, 700, "middle"))
    b.append(T(470, 376, "zatwierdza", 22, INK, 700, "middle"))
    b.append(arrow(uid, 372, 262, 414, 262, "m"))
    outs = ["formularz online", "wydruk na wzorze", "reguły kontroli", "lista potrzebnych pól"]
    for i, lab in enumerate(outs):
        y = 44 + i * 138
        g = [R(600, y, 384, 108, rx=20)]
        ix, iy = 648, y + 54
        if i == 0:
            g.append(phone(ix - 20, iy - 36, 40, 72, 3, hl=(0,)))
        elif i == 1:
            g.append(sheet(ix - 26, iy - 34, 52, 68, 3, sig=True))
        elif i == 2:
            for k in range(3):
                g.append(check(ix - 14, iy - 22 + k * 22, 8))
                g.append(f'<rect x="{ix + 2}" y="{iy - 26 + k * 22}" width="26" height="7" rx="3" fill="{MUTED}"/>')
        else:
            for k in range(3):
                g.append(f'<circle cx="{ix - 16}" cy="{iy - 20 + k * 20}" r="5" fill="{BLUE}"/>')
                g.append(f'<rect x="{ix - 4}" y="{iy - 24 + k * 20}" width="{34 - k * 6}" height="7" rx="3" fill="{BLUE}"/>')
        g.append(T(696, y + 62, lab, 23, INK, 700))
        b.append(f'<g class="rvo" style="--d:{1.5 + i * 0.2:.2f}s">{"".join(g)}</g>')
        b.append(arrow(uid, 0, 0, 0, 0, "m", path=f"M528 262 C566 262 556 {y + 54} 592 {y + 54}"))
    return svg(uid, 1000, 620, "".join(b),
               "Pusty druk, AI proponuje pola, człowiek zatwierdza; wynik: formularz online, wydruk na wzorze, reguły kontroli, lista potrzebnych pól")


def draw_need() -> str:
    uid = "nd"
    b = [pill(930, 34, "przykład", 18, fill="#10183a", stroke=LINE, color=MUTED, padx=14)]
    b.append(f'<path d="M56 96 h290 a24 24 0 0 1 24 24 v82 a24 24 0 0 1 -24 24 h-190 l-36 40 v-40 h-64 '
             f'a24 24 0 0 1 -24 -24 v-82 a24 24 0 0 1 24 -24 z" fill="#1a2244" stroke="{ACC}" stroke-width="3.5" '
             f'stroke-linejoin="round"/>')
    b.append(T(64, 152, "„Chcę zameldować", 27, INK, 700))
    b.append(T(64, 188, "siebie i dziecko”", 27, INK, 700))
    b.append(person(118, 348, 1.5))
    b.append(person(208, 372, 0.95, "#9ccbff"))
    for j, (lab, cx) in enumerate((("w domu", 96), ("przy rezerwacji wizyty", 176), ("przy okienku", 118))):
        b.append(pill(cx, 468 + j * 52, lab, 19, fill="#10183a", stroke=LINE, color=MUTED, padx=14, weight=600))
    b.append(arrow(uid, 378, 180, 420, 180, "a"))
    card = [R(430, 66, 540, 322, rx=22)]
    card.append(T(462, 114, "Komplet", 30, INK, 800))
    card.append(f'<line x1="462" y1="132" x2="938" y2="132" stroke="{LINE}" stroke-width="2"/>')
    card.append(sheet(462, 152, 34, 46, 2, fill="#d5dcf2") + sheet(476, 160, 34, 46, 2))
    card.append(T(530, 178, "2 × zgłoszenie pobytu stałego", 23, INK, 700))
    card.append(T(530, 205, "osobne dla każdej osoby", 19, MUTED, 500))
    card.append(R(462, 238, 48, 34, rx=6, fill=PAPER, stroke="none", sw=0))
    card.append(f'<circle cx="476" cy="255" r="7" fill="#8fa0cf"/><rect x="488" y="248" width="16" height="5" rx="2" fill="{PAPERLINE}"/>'
                f'<rect x="488" y="258" width="12" height="5" rx="2" fill="{PAPERLINE}"/>')
    card.append(T(530, 252, "Zabierz: dokument tożsamości,", 22, INK, 700))
    card.append(T(530, 280, "tytuł prawny do lokalu", 22, INK, 700))
    card.append(f'<circle cx="486" cy="340" r="19" fill="none" stroke="{GREEN}" stroke-width="4"/>')
    card.append(T(486, 348, "0", 22, INK, 800, "middle"))
    card.append(T(530, 348, "Opłata: bezpłatnie", 22, INK, 700))
    b.append(f'<g class="rvo" style="--d:0.5s">{"".join(card)}</g>')
    q = [R(430, 408, 540, 100, rx=18, fill="#10224a", stroke=BLUE)]
    q.append(T(458, 446, "Czy masz tytuł prawny do lokalu?", 22, INK, 700))
    q.append(R(458, 462, 74, 34, rx=17, fill="none", stroke=LINE))
    q.append(T(495, 485, "Tak", 19, MUTED, 600, "middle"))
    q.append(R(546, 462, 74, 34, rx=17, fill=ACC, stroke=ACC))
    q.append(T(583, 485, "Nie", 19, DARK, 800, "middle"))
    b.append(f'<g class="rvo" style="--d:1.1s">{"".join(q)}</g>')
    add = [arrow(uid, 583, 510, 583, 538, "g")]
    add.append(R(430, 546, 540, 62, rx=16, fill="#123322", stroke=GREEN))
    add.append(f'<circle cx="466" cy="577" r="15" fill="{GREEN}"/><rect x="458" y="574.5" width="16" height="5" rx="2" fill="{DARK}"/>'
               f'<rect x="463.5" y="569" width="5" height="16" rx="2" fill="{DARK}"/>')
    add.append(T(496, 585, "potwierdzenie właściciela lokalu", 22, INK, 700))
    b.append(f'<g class="rvo" style="--d:1.7s">{"".join(add)}</g>')
    return svg(uid, 1000, 630, "".join(b),
               "Przykład: mieszkaniec opisuje sprawę, system pokazuje komplet wniosków, dokumenty do zabrania i opłatę; odpowiedź na pytanie zmienia komplet")


def draw_doors() -> str:
    uid = "dr"
    b = []
    if not AGENT_DOOR_BUILT:
        b.append(pill(926, 34, "propozycja", 18, fill="#10183a", stroke=LINE, color=MUTED, padx=14))
    # door 1
    b.append(T(30, 42, "Wejście 1: dla każdego", 21, INK, 800))
    b.append(person(72, 128, 1.0))
    b.append(arrow(uid, 118, 122, 176, 122, "m"))
    b.append(phone(188, 64, 66, 116, 3, hl=(0,)))
    b.append(T(221, 208, "strona na telefonie", 18, MUTED, 600, "middle"))
    b.append(T(221, 230, "albo okienko", 18, MUTED, 600, "middle"))
    b.append(arrow(uid, 0, 0, 0, 0, "a", path="M266 122 C440 122 520 150 610 226"))
    # door 2
    b.append(T(30, 286, "Wejście 2: dla osób z asystentem AI", 21, INK, 800))
    b.append(f'<path d="M52 304 h206 a16 16 0 0 1 16 16 v40 a16 16 0 0 1 -16 16 h-150 l-22 22 v-22 h-34 '
             f'a16 16 0 0 1 -16 -16 v-40 a16 16 0 0 1 16 -16 z" fill="#1a2244" stroke="{ACC}" stroke-width="3" '
             f'stroke-linejoin="round"/>')
    b.append(T(54, 334, "„Umów wizytę", 19, INK, 700))
    b.append(T(54, 360, "i przygotuj wnioski”", 19, INK, 700))
    b.append(person(72, 470, 1.0))
    b.append(R(128, 436, 66, 66, rx=16, fill="#2b2410", stroke=ACC, sw=3))
    b.append(f'<path d="M161 448 l6 15 l15 6 l-15 6 l-6 15 l-6 -15 l-15 -6 l15 -6 z" fill="{ACC}"/>')
    b.append(T(161, 528, "własny asystent AI", 18, MUTED, 600, "middle"))
    b.append(arrow(uid, 202, 469, 254, 469, "a"))
    door = [R(264, 388, 306, 166, rx=18, fill="#10224a", stroke=BLUE, sw=2.5)]
    door.append(T(284, 420, "Wejście dla agentów", 22, INK, 800))
    door.append(T(284, 443, "MCP · API · te same reguły", 16, MUTED, 600))
    chips = (("znajdź sprawę", 284, 458, 142), ("komplet", 434, 458, 118),
             ("termin wizyty", 284, 502, 142), ("wypełnij", 434, 502, 118))
    for lab, x, y, w in chips:
        door.append(R(x, y, w, 34, rx=17, fill="#18305f", stroke=BLUE, sw=1.5))
        door.append(T(x + w / 2, y + 23, lab, 16, INK, 700, "middle"))
    b.append(f'<g class="rvo" style="--d:0.5s">{"".join(door)}</g>')
    b.append(arrow(uid, 0, 0, 0, 0, "a", path="M578 440 C600 440 592 330 612 300"))
    # the set
    card = [R(620, 186, 176, 150, rx=20)]
    card.append(sheet(660, 204, 44, 58, 3, fill="#aeb8d8") + sheet(680, 198, 44, 58, 3, fill="#d5dcf2") + sheet(700, 204, 44, 58, 3))
    card.append(check(752, 258, 14))
    card.append(T(708, 296, "Komplet", 23, INK, 800, "middle"))
    card.append(T(708, 320, "te same reguły", 16, MUTED, 600, "middle"))
    b.append(f'<g class="rvo" style="--d:0.9s">{"".join(card)}</g>')
    ends = (("scyfryzowany", "wysyła człowiek", 96), ("papierowy", "podpis w urzędzie", 226))
    for i, (a, c, y) in enumerate(ends):
        g = [R(826, y, 160, 96, rx=16)]
        g.append(T(906, y + 42, a, 19, INK, 800, "middle"))
        g.append(T(906, y + 68, c, 15, MUTED, 600, "middle"))
        b.append(f'<g class="rvo" style="--d:{1.2 + i * 0.2:.2f}s">{"".join(g)}</g>')
    b.append(arrow(uid, 800, 232, 820, 168, "m", flow=False, sw=2.5))
    b.append(arrow(uid, 800, 290, 820, 280, "m", flow=False, sw=2.5))
    # the person's approval
    ok = [R(620, 396, 366, 174, rx=18)]
    ok.append(check(648, 426, 13))
    ok.append(T(672, 433, "zatwierdza człowiek", 20, INK, 800))
    for i, lab in enumerate(("Potwierdzam rezerwację", "Pozwalam wypełnić wniosek")):
        y = 450 + i * 54
        ok.append(R(640, y, 326, 42, rx=12, fill="#123322", stroke=GREEN))
        ok.append(T(803, y + 28, lab, 18, INK, 700, "middle"))
    b.append(f'<g class="rvo" style="--d:1.5s">{"".join(ok)}</g>')
    b.append(arrow(uid, 576, 520, 612, 500, "g"))
    return svg(uid, 1000, 600, "".join(b),
               "Dwa wejścia do tego samego kompletu: strona na telefonie albo okienko, oraz wejście dla asystentów AI; rezerwację i wypełnienie wniosku zatwierdza człowiek")


def draw_data() -> str:
    uid = "dt"
    b = []
    b.append(pill(232, 40, "1 dotknięcie: dane z przeglądarki", 20, fill="#10183a", stroke=LINE, color=INK, padx=16, weight=600))
    b.append(pill(150, 92, "aparat: dokument", 20, fill="#10183a", stroke=LINE, color=INK, padx=16, weight=600))
    b.append(arrow(uid, 200, 116, 200, 148, "m"))
    b.append(R(90, 160, 220, 400, rx=34, fill=DEEP, stroke=LINE, sw=3))
    b.append(lock(200, 212, 1.5))
    b.append(T(200, 268, "Profil", 22, INK, 700, "middle"))
    for i in range(6):
        col = ACC if i in (0, 2, 3) else "#2a3560"
        b.append(f'<rect x="122" y="{294 + i * 40}" width="156" height="20" rx="10" fill="{col}"/>')
    b.append(T(200, 598, "profil zostaje na telefonie", 20, MUTED, 600, "middle"))
    b.append(f'<g class="rvo" style="--d:0.6s">{qr_fake(432, 296, 128)}{T(496, 458, "kod QR urzędu", 20, MUTED, 600, "middle")}</g>')
    b.append(arrow(uid, 318, 360, 422, 360, "a"))
    b.append(arrow(uid, 570, 360, 762, 360, "a"))
    for k, px in enumerate((606, 652, 698)):
        b.append(f'<g class="rvo" style="--d:{1.0 + k * 0.2:.2f}s"><rect x="{px - 16}" y="320" width="32" height="24" rx="6" '
                 f'fill="{ACC}"/>{lock(px, 331, 0.5, DARK)}</g>')
    b.append(T(646, 298, "tylko potrzebne pola", 19, INK, 700, "middle"))
    b.append(T(646, 398, "zaszyfrowane", 18, MUTED, 600, "middle"))
    b.append(building(884, 420, 1.6))
    b.append(T(884, 456, "urząd", 22, INK, 700, "middle"))
    b.append(f'<circle cx="858" cy="208" r="22" fill="none" stroke="{MUTED}" stroke-width="3.5"/>'
             f'<path d="M858 194 v15 l10 7" fill="none" stroke="{MUTED}" stroke-width="3.5" stroke-linecap="round"/>')
    b.append(T(890, 215, "minuty", 20, MUTED, 600))
    return svg(uid, 1000, 620, "".join(b),
               "Profil na telefonie mieszkańca; przez kod QR urzędu trafiają do urzędu tylko potrzebne pola, zaszyfrowane, na kilka minut")


def draw_check() -> str:
    uid = "ck"
    m = METRICS
    n_ok = "12"
    typed = "0" if m["fields_typed_by_clerk"] is None else str(m["fields_typed_by_clerk"])
    b = []
    if m["fields_typed_by_clerk"] is None:
        b.append(pill(930, 34, "przykład", 18, fill="#10183a", stroke=LINE, color=MUTED, padx=14))
    b.append(R(30, 44, 630, 452, rx=22, fill=DEEP, stroke=LINE, sw=3))
    b.append(f'<rect x="305" y="496" width="80" height="44" fill="{LINE}"/><rect x="235" y="540" width="220" height="14" rx="7" fill="{LINE}"/>')
    b.append(person(72, 100, 0.55))
    b.append(T(102, 104, "Anna Przykładowa", 24, INK, 800))
    g1 = [R(56, 134, 578, 58, rx=14, fill="#123322", stroke=GREEN)]
    g1.append(check(90, 163, 14))
    g1.append(T(118, 171, "Zgodne z dokumentem", 23, INK, 700))
    g1.append(R(548, 147, 48, 32, rx=16, fill=GREEN, stroke=GREEN))
    g1.append(T(572, 170, n_ok, 20, DARK, 800, "middle"))
    g1.append(f'<path d="M608 155 l8 8 l-8 8" fill="none" stroke="{MUTED}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
    b.append(f'<g class="rvo" style="--d:0.4s">{"".join(g1)}</g>')
    g2 = [R(56, 208, 578, 176, rx=14, fill="#33290f", stroke=ACC)]
    g2.append(warn(90, 239, 14))
    g2.append(T(118, 247, "Do sprawdzenia", 23, INK, 700))
    g2.append(R(548, 223, 48, 32, rx=16, fill=ACC, stroke=ACC))
    g2.append(T(572, 246, "2", 20, DARK, 800, "middle"))
    rows = (("adres", "nie ma go w dokumencie", "potwierdź"),
            ("data urodzenia", "niezgodna z PESEL", "popraw"))
    for i, (name, why, btn) in enumerate(rows):
        y = 300 + i * 52
        g2.append(f'<line x1="76" y1="{y - 30}" x2="614" y2="{y - 30}" stroke="#5a4a1c" stroke-width="1.5"/>')
        g2.append(T(80, y, name, 21, INK, 800))
        g2.append(T(80 + tw(name, 21) + 14, y, why, 18, MUTED, 500))
        g2.append(R(520, y - 24, 96, 34, rx=17, fill="none", stroke=ACC))
        g2.append(T(568, y - 1, btn, 17, INK, 700, "middle"))
    b.append(f'<g class="rvo" style="--d:0.9s">{"".join(g2)}</g>')
    g3 = [R(60, 408, 32, 32, rx=7, fill=GREEN, stroke=GREEN)]
    g3.append(f'<path d="M67 424 l7 8 l12 -15" fill="none" stroke="{DARK}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
    g3.append(T(106, 433, "Tożsamość potwierdzona", 22, INK, 700))
    g3.append(R(404, 398, 230, 54, rx=14, fill=GREEN, stroke=GREEN))
    g3.append(T(519, 433, "Drukuj komplet", 22, DARK, 800, "middle"))
    b.append(f'<g class="rvo" style="--d:1.4s">{"".join(g3)}</g>')
    b.append(arrow(uid, 0, 0, 0, 0, "g", path="M640 425 C684 425 676 300 706 262"))
    sh = [f'<g transform="rotate(-5 800 220)">{sheet(716, 96, 176, 236, 5, sig=True)}</g>',
          f'<g transform="rotate(4 880 250)">{sheet(790, 120, 176, 236, 5, sig=True)}</g>']
    b.append(f'<g class="rvo" style="--d:1.8s">{"".join(sh)}</g>')
    b.append(R(700, 410, 270, 124, rx=18))
    b.append(T(835, 448, "wpisane przez urzędnika", 19, MUTED, 600, "middle"))
    b.append(T(835, 506, f"{typed} pól", 44, INK, 800, "middle"))
    b.append(T(345, 596, "AI wskazuje, urzędnik decyduje", 21, MUTED, 600, "middle"))
    return svg(uid, 1000, 620, "".join(b),
               "Ekran urzędnika: pola zgodne z dokumentem zwinięte, dwa pola do sprawdzenia, potwierdzenie tożsamości, wydruk kompletu")


def draw_scale() -> str:
    uid = "sc"
    b = []
    card = [R(50, 196, 270, 250, rx=20)]
    card.append(sheet(84, 226, 70, 92, 4))
    for k in range(4):
        card.append(f'<circle cx="182" cy="{240 + k * 24}" r="5" fill="{BLUE}"/>')
        card.append(f'<rect x="196" y="{236 + k * 24}" width="{96 - k * 12}" height="8" rx="4" fill="{BLUE}"/>')
    card.append(pill(185, 356, "suma kontrolna pliku", 17, fill="#10183a", stroke=LINE, color=MUTED, padx=12, weight=600))
    card.append(T(185, 412, "opis formularza", 24, INK, 800, "middle"))
    b.append("".join(card))
    b.append(T(185, 480, "bez danych osobowych", 20, MUTED, 600, "middle"))
    offices = (("urząd miasta", 150), ("urząd gminy", 340), ("starostwo", 530))
    for i, (lab, by) in enumerate(offices):
        b.append(arrow(uid, 0, 0, 0, 0, "b", path=f"M330 320 C470 320 520 {by - 50} 690 {by - 50}"))
        b.append(f'<g class="rvo" style="--d:{0.5 + i * 0.25:.2f}s">{building(790, by, 1.05)}'
                 f'{T(790, by + 32, lab, 21, INK, 700, "middle")}</g>')
    b.append(pill(470, 48, "Generator Formularzy e-Usług", 22, fill="#10224a", stroke=BLUE, padx=20))
    b.append(arrow(uid, 0, 0, 0, 0, "m", path="M185 188 C185 128 205 90 252 64"))
    b.append(T(160, 150, "może zasilić", 19, MUTED, 600, "end"))
    b.append(pill(385, 588, "pilotaż: 10 najczęstszych druków jednego urzędu", 21, fill="#2b2410", stroke=ACC, padx=20))
    return svg(uid, 1000, 630, "".join(b),
               "Jeden opis formularza, bez danych osobowych, służy wielu urzędom i może zasilić Generator Formularzy e-Usług")


def qr_real() -> str:
    try:
        import io
        import segno  # pip install segno
        buf = io.BytesIO()
        segno.make(SITE_URL, error="m").save(buf, kind="svg", scale=4, border=2, dark=DARK, light="#ffffff",
                                             xmldecl=False, svgns=True, nl=False, omitsize=True)
        return buf.getvalue().decode("utf-8").replace("<svg ", '<svg role="img" aria-label="Kod QR do strony projektu" ', 1)
    except Exception:  # segno missing: decorative placeholder, the address is printed next to it
        return svg("qr", 100, 100, qr_fake(0, 0, 100), "Adres strony projektu podano obok")


# ----------------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------------
def metric_line(pairs) -> str:
    items = [f"<span><b>{esc(str(METRICS[k]))}{esc(unit)}</b> {esc(label)}</span>"
             for k, unit, label in pairs if METRICS.get(k) is not None]
    return f'<p class="metrics">{"".join(items)}</p>' if items else ""


def tick_svg() -> str:
    return (f'<svg viewBox="0 0 28 28" aria-hidden="true">{check(14, 14, 13)}</svg>')


def dot_svg() -> str:
    return (f'<svg viewBox="0 0 28 28" aria-hidden="true"><circle cx="14" cy="14" r="9" fill="none" stroke="{ACC}" '
            f'stroke-width="4"/></svg>')


def pages() -> list[dict]:
    works_title = "Co działa" if BUILT else "W prototypie budujemy"
    p9_right = (
        f'<div class="status"><div><h3>{works_title}</h3><ul>'
        + "".join(f"<li>{tick_svg()}<span>{esc(w)}</span></li>" for w in WORKS)
        + '</ul></div><div><h3>Symulujemy</h3><ul>'
        + "".join(f"<li>{dot_svg()}<span>{esc(w)}</span></li>" for w in SIMULATED)
        + f'</ul><p class="tag">dane syntetyczne</p></div></div><p class="src">Stan na {STATE_DATE}.</p>')
    principles = [
        ("Dane zostają u mieszkańca.", "Urząd dostaje tylko pola potrzebne w sprawie."),
        ("AI proponuje, urzędnik zatwierdza.", "Każda decyzja zostawia ślad."),
        ("Dane osobowe nie trafiają do chmury.", "Model działa lokalnie."),
        ("Otwarty kod (MIT).", "Uruchomienie w infrastrukturze urzędu."),
        ("Interfejs zgodny z WCAG 2.1 AA." if BUILT else "Interfejs projektowany zgodnie z WCAG 2.1 AA.",
         "Klawiatura, kontrast, etykiety."),
    ]
    p9_left = '<ul class="principles">' + "".join(
        f"<li>{tick_svg()}<span><b>{esc(nb(a))}</b> {esc(nb(c))}</span></li>" for a, c in principles) + "</ul>"

    stats = (
        '<div class="stats">'
        '<div class="stat"><b data-count="275">275</b><span>kart usług w\u00a0jednym urzędzie miasta</span></div>'
        '<div class="stat"><b data-count="710">710</b><span>plików do pobrania w\u00a0tych kartach</span></div>'
        '<div class="stat"><b>ok. ½</b><span>z\u00a0nich to pliki Word i\u00a0RTF</span></div>'
        '<div class="stat"><b>1 z 32</b><span>w\u00a0próbie ma pola do wypełnienia na ekranie</span></div>'
        '</div>'
        '<div class="meter" role="img" aria-label="179 z 344 zmapowanych usług centralnych dla obywateli jest cyfrowych">'
        '<div class="meter-head"><span>Usługi centralne dla obywateli, które są już cyfrowe</span><b>179 z 344</b></div>'
        '<div class="track"><div class="fill" style="width:52%"></div></div></div>')

    return [
        dict(kind="title",
             ru=("ИИ превращает официальный бланк в услугу. Житель даёт данные только один раз. Чиновник ничего не "
                 "переписывает и проверяет только то, что требует проверки. Плашки: открытый код, работает локально "
                 "в учреждении, данные в показе выдуманные."),
             why=("Первая страница должна за пять секунд сказать, что это и чем отличается. Лента из пяти шагов "
                  "повторяется на странице 4 уже с пояснениями. Пока программа не построена, наверху стоит пометка "
                  "«рабочая версия»: агент снимет её, когда всё заработает.")),
        dict(h="Dziś: te same dane, wiele razy",
             body=("Mieszkaniec sam ustala, których druków potrzebuje, i na każdym wpisuje to samo. Urzędnik pomaga "
                   "wypełniać, przepisuje i porównuje dane z dokumentem litera po literze. Gdy zabraknie wniosku albo "
                   "załącznika, urząd wzywa do usunięcia braków w terminie nie krótszym niż siedem dni."),
             src="Art. 64 § 2 Kodeksu postępowania administracyjnego; obserwacje autora z punktu pomocy uchodźcom w Opolu (2022).",
             art=draw_today(),
             ru=("Житель сам выясняет, какие бланки нужны, и на каждом пишет одно и то же. Чиновник помогает "
                 "заполнять, переписывает и сверяет данные с документом по буквам. Если не хватает бланка или "
                 "приложения, учреждение требует устранить недостатки, срок не короче семи дней."),
             why=("Это страница «боль». Семь дней взяты из кодекса. Первые две фразы это твои наблюдения: если "
                  "чиновники на стенде скажут, что у них болит другое, агент перепишет страницу под их слова. "
                  "Сколько раз люди приходят дважды, мы не знаем и числа не называем.")),
        dict(h="Skala: jedno miasto",
             body=("Usługi centralne są coraz częściej cyfrowe. Lokalne druki pozostają plikami do wydrukowania "
                   "i wypełnienia ręcznie, a cyfryzacja każdego z nich to dziś czasochłonna, ręczna praca."),
             src=("Katalog kart usług i formularzy Urzędu Miasta Bydgoszczy w repozytorium projektu, stan na 21.11.2026; "
                  "próba 32 formularzy tego urzędu. Mapa Życia, Ministerstwo Cyfryzacji i COI, 13.05.2026."),
             art=stats, art_html=True,
             ru=("Центральные услуги всё чаще цифровые. Местные бланки остаются файлами, которые печатают и "
                 "заполняют от руки, а оцифровка каждого сегодня это долгая ручная работа. Числа: 275 карточек услуг, "
                 "710 файлов, около половины это Word и RTF, из 32 изученных только один можно заполнить на экране; "
                 "в стране цифровые 179 из 344 услуг."),
             why=("Масштаб на примере их же города. Все числа из нашего каталога и из публикации министерства; "
                  "люди из COI эти 179 из 344 знают сами. Мы не говорим «всё на бумаге», мы говорим «длинный хвост "
                  "местных бланков».")),
        dict(kind="wide", h="Rozwiązanie w jednym obrazie",
             body=("Najpierw druk staje się usługą. Potem każda wizyta przebiega tak samo: potrzeba, komplet, dane, "
                   "kontrola, podpis."),
             art=ribbon("rb2", sub=True, base=True),
             ru=("Сначала бланк становится услугой. Потом каждый визит идёт одинаково: потребность, комплект, "
                 "данные, проверка, подпись. Внизу «шаг 0»: ИИ превращает бланк в услугу, человек утверждает."),
             why=("Вся идея одной картинкой. Если жюри посмотрит только одну страницу, пусть это будет она. "
                  "Шаг 0 это прямое задание COI; шаги 1–5 это твоя идея «один визит, полный комплект».")),
        dict(h="Krok 0. Druk staje się usługą",
             body=("Pracownik urzędu wczytuje pusty druk: PDF, DOCX albo XLSX. AI rozpoznaje pola i proponuje ich "
                   "znaczenie, a człowiek poprawia i zatwierdza. Z jednego opisu powstają formularz online, wydruk "
                   "na oryginalnym wzorze i reguły kontroli. Automat porównuje wydruk z oryginałem."),
             extra=metric_line((("digitise_seconds", " s", "od wczytania do publikacji"),
                                ("fields_detected_pct", " %", "pól rozpoznanych poprawnie"))),
             art=draw_step0(),
             ru=("Сотрудник учреждения загружает пустой бланк: PDF, DOCX или XLSX. ИИ распознаёт поля и предлагает "
                 "их смысл, человек правит и утверждает. Из одного описания получаются онлайн-форма, печать на "
                 "оригинальном образце и правила проверки. Автомат сравнивает печать с оригиналом."),
             why=("Это то, о чём COI просит прямо: «инструмент ИИ, который превращает бланки в услуги». Они сами "
                  "назвали PDF, DOCX, XLSX. Если программа к сдаче не будет принимать Excel, агент уберёт XLSX из "
                  "текста. После показа здесь появятся измеренные секунды и процент распознанных полей.")),
        dict(h="Od potrzeby do kompletu",
             body=("Mieszkaniec wybiera sprawę albo opisuje ją jednym zdaniem: w domu, przy rezerwacji wizyty, albo "
                   "przy okienku. System pokazuje komplet: wnioski dla każdej osoby, dokumenty do zabrania i opłaty. "
                   "Odpowiedź na pytanie doprecyzowujące zmienia komplet od razu."),
             src="Reguły pochodzą z kart usług urzędu; AI tylko dopasowuje opis do gotowego kompletu.",
             art=draw_need(),
             ru=("Житель выбирает дело или описывает его одной фразой: дома, при записи на визит или у окошка. "
                 "Система показывает комплект: заявления на каждого человека, документы, которые надо взять, и "
                 "оплаты. Ответ на уточняющий вопрос сразу меняет комплект. Правила взяты из карточек услуг; ИИ "
                 "только подбирает готовый комплект под описание."),
             why=("Твоя главная мысль: «помощник сразу подбирает весь пакет, и забытого бланка не бывает». Пример на "
                  "картинке (прописка с ребёнком) агент сверит с карточкой услуги мэрии. Про онлайн-запись: мы "
                  "говорим «при записи на визит», но не говорим, что подключены к их системе.")),
        dict(h="Dwa wejścia: sam albo przez asystenta AI",
             body=("Coraz więcej osób powierza codzienne sprawy osobistym asystentom AI. Dziś taki asystent musi "
                   "klikać po stronach urzędu jak człowiek. Proponujemy oficjalne wejście dla agentów: ten sam "
                   "komplet i te same reguły przez otwarty interfejs (MCP i API). Asystent znajduje sprawę, umawia "
                   "wizytę zgodną z kalendarzem i wypełnia scyfryzowane formularze danymi swojego właściciela. "
                   "Rezerwację i wysłanie wniosku zawsze zatwierdza człowiek."),
             src=("Dane osobowe przechodzą tylko w ramach zgody na jedną sprawę, udzielonej na telefonie. "
                  "W prototypie kalendarz terminów i wysyłka wniosku są symulowane."),
             art=draw_doors(),
             ru=("Всё больше людей поручают повседневные дела личным ИИ-ассистентам. Сегодня такой ассистент "
                 "вынужден кликать по страницам учреждения как человек. Предлагаем официальный вход для агентов: "
                 "тот же комплект и те же правила через открытый интерфейс (MCP и API). Ассистент находит дело, "
                 "записывает на визит по календарю и заполняет оцифрованные формы данными своего владельца. "
                 "Запись и отправку заявления всегда подтверждает человек. Мелко: персональные данные проходят "
                 "только в рамках разрешения на одно дело, выданного на телефоне; в прототипе календарь и "
                 "отправка имитируются."),
             why=("Это твоя новая мысль: два варианта работы. Вход 1 для тех, кто не дружит с агентами (страница "
                  "в телефоне или окошко). Вход 2 для таких, как ты и дочь: говоришь ассистенту, он всё готовит. "
                  "Главное правило, которое надо говорить вслух: «Asystent wypełnia, człowiek zatwierdza» "
                  "(ассистент заполняет, человек подтверждает). Агент никогда не подписывает и не отправляет "
                  "за тебя. Пока это не построено, на картинке стоит пометка «propozycja» (предложение); если "
                  "агенты успеют сделать пакет WP-B10, пометку снимут и покажут вживую.")),
        dict(h="Dane raz, z telefonu mieszkańca",
             body=("Profil powstaje raz: przeglądarka podpowiada zapisane imię, adres i telefon, a dokument można "
                   "odczytać aparatem. Profil zostaje na telefonie. Przy okienku mieszkaniec skanuje kod QR, widzi, "
                   "które pola są potrzebne w tej sprawie, i zatwierdza. Do urzędu trafiają tylko te pola, "
                   "zaszyfrowane; po wydruku znikają, a w urzędzie zostaje podpisany wniosek."),
             extra=('<div class="side"><b>Docelowo: mObywatel.</b> Funkcja „Przekaż instytucji” już istnieje. Opis '
                    'formularza wskazuje, o które pola poprosić. To propozycja; w pokazie używamy własnego '
                    'przekazania przez kod QR.</div>'),
             art=draw_data(),
             ru=("Профиль создаётся один раз: браузер подсказывает сохранённые имя, адрес и телефон, документ можно "
                 "считать камерой. Профиль остаётся в телефоне. У окошка житель сканирует QR-код, видит, какие поля "
                 "нужны для этого дела, и подтверждает. Данные приходят в учреждение зашифрованными; временные "
                 "данные исчезают после печати, а в учреждении остаётся подписанное заявление. В рамке: в "
                 "перспективе mObywatel, это предложение."),
             why=("Здесь сразу три твоих пожелания: данные заранее, подтянуть из браузера, хорошо бы mObywatel. "
                  "Оговорки: браузер только предлагает, человек нажимает; PESEL и номер документа из браузера не "
                  "подтягиваются; про mObywatel говорим «docelowo» и «propozycja», никакой интеграции не заявляем.")),
        dict(h="Kontrola wyjątków i wydruk",
             body=("Urzędnik odczytuje dokument tożsamości. System porównuje go z danymi od mieszkańca i uruchamia "
                   "reguły kontroli. Na ekranie zostaje tylko to, co wymaga spojrzenia człowieka. Urzędnik potwierdza "
                   "tożsamość i drukuje komplet na oryginalnych wzorach, gotowy do podpisu."),
             extra=metric_line((("fields_in_set", "", "pól w komplecie"),
                                ("fields_looked_at", "", "pól obejrzanych przez urzędnika"),
                                ("scan_to_print_seconds", " s", "od skanu do wydruku"))),
             art=draw_check(),
             ru=("Чиновник считывает документ. Система сравнивает его с данными жителя и запускает правила "
                 "проверки. На экране остаётся только то, что требует взгляда человека. Чиновник подтверждает "
                 "личность и печатает комплект на оригинальных образцах, готовый к подписи. Внизу: ИИ указывает, "
                 "чиновник решает."),
             why=("Твоё «показывать только то, что надо перепроверить» и «сканер вместо ручной сверки». Числа на "
                  "картинке это пример; после показа их заменят измеренные. Адрес всегда попадает в «проверить», "
                  "потому что его нет на польском удостоверении. Чиновник всегда сам подтверждает личность: это "
                  "не обсуждается и это надо говорить вслух.")),
        dict(h="Bezpiecznie i gotowe do wdrożenia" if BUILT else "Bezpieczeństwo i wdrożenie",
             body_html=p9_left, art=p9_right, art_html=True,
             ru=("Принципы: данные остаются у жителя, учреждение получает только нужные поля; ИИ предлагает, "
                 "чиновник утверждает, каждое решение оставляет след; персональные данные не уходят в облако, "
                 "модель работает локально; открытый код, запуск в инфраструктуре учреждения; интерфейс по "
                 "стандарту доступности. Справа: что строим в прототипе и что имитируем; данные выдуманные."),
             why=("COI написал, что премирует open-source, который можно развернуть у себя (on-prem): эта страница "
                  "отвечает им прямо. Правая колонка сейчас называется «строим в прототипе», потому что кода ещё "
                  "нет. Перед сдачей агент заменит её на «что работает» и оставит только то, что реально работает.")),
        dict(h="Jeden opis, wiele urzędów",
             body=("Opis formularza nie zawiera danych osobowych, więc może być wspólny: druk opisany raz działa "
                   "w każdym urzędzie, a zmianę wzoru wykrywa suma kontrolna pliku. Opis w otwartym formacie może "
                   "zasilić Generator Formularzy e-Usług. Proponujemy pilotaż: dziesięć najczęstszych druków jednego "
                   "urzędu jako usługi „od potrzeby do podpisu”."),
             extra=(f'<div class="links"><div class="qr">{qr_real()}</div><div><b>{esc(SITE_LABEL)}</b>'
                    f'<span>{esc(REPO_LABEL)}</span><span>Andrii Shramko · Shramko Asystent Urzędnika</span></div></div>'),
             src=("Badania, katalog formularzy i specyfikacja powstały przed wydarzeniem i są jawnie oznaczone "
                  "w repozytorium; kod aplikacji powstaje w ciągu 24 godzin hackathonu. Projekt niezależny; nazwy "
                  "mObywatel i Generator Formularzy e-Usług należą do ich właścicieli."),
             art=draw_scale(),
             ru=("Описание бланка не содержит персональных данных, поэтому может быть общим: описанный один раз "
                 "бланк работает в любом учреждении, а смену образца видно по контрольной сумме файла. Описание в "
                 "открытом формате может питать государственный Generator Formularzy e-Usług. Предлагаем пилот: десять "
                 "самых частых бланков одного учреждения как услуги «от потребности до подписи»."),
             why=("Масштаб и предложение. Generator Formularzy e-Usług это продукт самого COI: в нём учреждения "
                  "собирают формы, которые публикуются на mobywatel.gov.pl. Мы не конкурент, мы «быстрый вход» в него. Мелким шрифтом честно сказано, что "
                  "исследование сделано заранее, а код пишется на хакатоне. QR-код ведёт на сайт проекта.")),
    ]


# ----------------------------------------------------------------------------
# HTML
# ----------------------------------------------------------------------------
CSS = """
:root{--bg:#0b1020;--panel:#18213f;--line:#3a4878;--ink:#f5f7ff;--muted:#b3bddc;--acc:#ffc547;--green:#4ade80;
--red:#ff6b6b;--blue:#6cb2ff;--deep:#0f1630;
--font:Inter,"Segoe UI",system-ui,-apple-system,Roboto,"Helvetica Neue",Arial,sans-serif}
*{box-sizing:border-box}
html{background:#060914}
body{margin:0;background:#060914;color:var(--ink);font-family:var(--font);-webkit-print-color-adjust:exact;print-color-adjust:exact}
.wrap{max-width:1320px;margin:0 auto;padding:20px 20px 60px}
.intro{color:var(--muted);font-size:15px;line-height:1.5;margin:6px 4px 18px}
.intro b{color:var(--ink)}
.page{container-type:inline-size;position:relative;background:var(--bg);border:1px solid #1c2647;border-radius:18px;
margin:0 0 22px;overflow:hidden}
.inner{--u:1cqw;aspect-ratio:16/9;display:flex;flex-direction:column;padding:calc(var(--u)*2.2) calc(var(--u)*3.4) calc(var(--u)*2.2)}
.top{display:flex;justify-content:space-between;align-items:center;font-size:calc(var(--u)*1.02);color:var(--muted);
letter-spacing:.04em;text-transform:uppercase;font-weight:600}
.top .pn{font-variant-numeric:tabular-nums;letter-spacing:0}
.grid{flex:1;display:grid;grid-template-columns:40fr 60fr;gap:calc(var(--u)*3);align-items:center;min-height:0}
.grid.wide{grid-template-columns:1fr;align-content:center;gap:calc(var(--u)*2.2)}
.txt{min-width:0}
h1,h2{margin:0;font-weight:800;letter-spacing:-.015em;line-height:1.08;text-wrap:balance}
h1{font-size:calc(var(--u)*5.6)}
h1 + .sub{font-size:calc(var(--u)*3);font-weight:800;color:var(--acc);margin:calc(var(--u)*.6) 0 0;letter-spacing:-.01em}
h2{font-size:calc(var(--u)*3.4)}
.kicker{font-size:calc(var(--u)*1.15);color:var(--muted);font-weight:600;margin:0 0 calc(var(--u)*1.1)}
.body{font-size:calc(var(--u)*1.6);line-height:1.45;color:#e2e7fa;margin:calc(var(--u)*1.4) 0 0;text-wrap:pretty}
.lead{font-size:calc(var(--u)*2);line-height:1.4;color:#e2e7fa;margin:calc(var(--u)*1.6) 0 0;max-width:46em;text-wrap:pretty}
.src{font-size:calc(var(--u)*1);line-height:1.4;color:var(--muted);margin:calc(var(--u)*1.2) 0 0}
.chips{display:flex;flex-wrap:wrap;gap:calc(var(--u)*.8);margin:calc(var(--u)*1.8) 0 0;padding:0;list-style:none}
.chips li{font-size:calc(var(--u)*1.2);font-weight:600;border:1px solid var(--line);background:var(--panel);
border-radius:99px;padding:calc(var(--u)*.45) calc(var(--u)*1.2)}
.draft{position:absolute;bottom:calc(var(--u)*2.2);right:calc(var(--u)*3.4);font-size:calc(var(--u)*1);font-weight:700;color:var(--bg);
background:var(--acc);border-radius:99px;padding:calc(var(--u)*.4) calc(var(--u)*1.1)}
.art{min-width:0;display:flex;flex-direction:column;justify-content:center}
.art svg{width:100%;height:auto;display:block;max-height:calc(var(--u)*45)}
.grid.wide .art svg{max-height:calc(var(--u)*30)}
svg text{font-family:var(--font)}
.side{font-size:calc(var(--u)*1.18);line-height:1.4;color:#e2e7fa;border:1px solid var(--blue);background:#10224a;
border-radius:calc(var(--u)*1);padding:calc(var(--u)*.9) calc(var(--u)*1.1);margin:calc(var(--u)*1.3) 0 0}
.side b{color:var(--ink)}
.metrics{display:flex;flex-wrap:wrap;gap:calc(var(--u)*1.4);font-size:calc(var(--u)*1.15);color:var(--muted);margin:calc(var(--u)*1.2) 0 0}
.metrics b{color:var(--ink);font-size:calc(var(--u)*1.7);font-weight:800;margin-right:.3em}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:calc(var(--u)*1.4)}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:calc(var(--u)*1.4);padding:calc(var(--u)*1.5) calc(var(--u)*1.7)}
.stat b{display:block;white-space:nowrap;font-size:calc(var(--u)*5);font-weight:800;line-height:1;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.stat span{display:block;font-size:calc(var(--u)*1.3);color:var(--muted);margin-top:calc(var(--u)*.7);line-height:1.3}
.meter{margin-top:calc(var(--u)*1.8);background:var(--panel);border:1px solid var(--line);border-radius:calc(var(--u)*1.4);
padding:calc(var(--u)*1.3) calc(var(--u)*1.7) calc(var(--u)*1.5)}
.meter-head{display:flex;justify-content:space-between;align-items:baseline;gap:1em;font-size:calc(var(--u)*1.3);color:var(--muted)}
.meter-head b{color:var(--ink);font-size:calc(var(--u)*1.9);font-weight:800;white-space:nowrap}
.track{height:calc(var(--u)*.9);border-radius:99px;background:#22407a;margin-top:calc(var(--u)*.9);overflow:hidden}
.fill{height:100%;border-radius:99px;background:var(--blue)}
.principles{list-style:none;margin:calc(var(--u)*1.6) 0 0;padding:0;display:grid;gap:calc(var(--u)*1.05)}
.principles li{display:grid;grid-template-columns:calc(var(--u)*2) 1fr;gap:calc(var(--u)*.9);align-items:start;
font-size:calc(var(--u)*1.5);line-height:1.38;color:#e2e7fa}
.principles b{color:var(--ink)}
.principles svg,.status svg{width:calc(var(--u)*1.9);height:calc(var(--u)*1.9);display:block}
.status{display:grid;grid-template-columns:1.25fr 1fr;gap:calc(var(--u)*1.6)}
.status>div{background:var(--panel);border:1px solid var(--line);border-radius:calc(var(--u)*1.4);padding:calc(var(--u)*1.5) calc(var(--u)*1.6)}
.status h3{margin:0 0 calc(var(--u)*1);font-size:calc(var(--u)*1.6);font-weight:800}
.status ul{list-style:none;margin:0;padding:0;display:grid;gap:calc(var(--u)*.75)}
.status li{display:grid;grid-template-columns:calc(var(--u)*1.9) 1fr;gap:calc(var(--u)*.8);align-items:center;font-size:calc(var(--u)*1.45);font-weight:600}
.tag{display:inline-block;margin:calc(var(--u)*1.3) 0 0;font-size:calc(var(--u)*1.1);font-weight:600;color:var(--muted);
border:1px solid var(--line);border-radius:99px;padding:calc(var(--u)*.35) calc(var(--u)*1)}
.links{display:flex;align-items:center;gap:calc(var(--u)*1.4);margin:calc(var(--u)*1.4) 0 0}
.links .qr{width:calc(var(--u)*8.2);flex:none;background:#fff;border-radius:calc(var(--u)*.7);padding:calc(var(--u)*.3);line-height:0}
.links .qr svg{width:100%;height:auto}
.links b{display:block;font-size:calc(var(--u)*1.55);color:var(--acc)}
.links span{display:block;font-size:calc(var(--u)*1);color:var(--muted);margin-top:calc(var(--u)*.35);overflow-wrap:anywhere}
.title-top{margin-top:calc(var(--u)*1.2)}
/* Russian commentary (ru.html only) */
.note{background:#101733;border:1px solid #26315c;border-radius:14px;margin:-10px 0 34px;padding:16px 20px;font-size:16px;line-height:1.55;color:#dfe5fb}
.note h3{margin:0 0 6px;font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--acc)}
.note p{margin:0 0 12px}.note p:last-child{margin:0}
/* motion: screen only, and only when scripts run */
.flow{animation:dash 1.1s linear infinite}
@keyframes dash{to{stroke-dashoffset:-19}}
.js .page:not(.in) .rv{opacity:0;transform:translateY(14px)}
.js .page:not(.in) .rvo{opacity:0}
.rv{transition:opacity .6s ease var(--d,0s),transform .6s ease var(--d,0s)}
.rvo{transition:opacity .7s ease var(--d,0s)}
.static .rv,.static .rvo{transition:none}.static .flow{animation:none}
@media (prefers-reduced-motion:reduce){.flow{animation:none}.rv,.rvo{transition:none}
.js .page:not(.in) .rv,.js .page:not(.in) .rvo{opacity:1;transform:none}}
@media screen and (max-width:760px){
.wrap{padding:10px 10px 40px}
.inner{--u:2.5vw;aspect-ratio:auto;padding:22px 18px 26px}
.top{font-size:11px;margin-bottom:14px}
.grid{grid-template-columns:1fr;gap:22px}
.art svg{max-height:none}
.grid.wide .art{overflow-x:auto;display:block}
.grid.wide .art svg{min-width:720px;max-height:none}
.stat b{font-size:calc(var(--u)*4.2)}
.draft{position:static;display:inline-block;margin:0 0 12px;font-size:12px;padding:4px 12px}
.status{grid-template-columns:1fr}
}
@page{size:13.333in 7.5in;margin:0}
@media print{
html,body{background:var(--bg)}
.wrap{max-width:none;padding:0}
.intro,.note{display:none}
.page{width:13.333in;height:7.5in;margin:0;border:0;border-radius:0;break-after:page;page-break-after:always;break-inside:avoid}
.page:last-of-type{break-after:auto;page-break-after:auto}
.inner{height:7.5in;aspect-ratio:auto}
.flow{animation:none}
.rv,.rvo{opacity:1!important;transform:none!important;transition:none}
}
"""

JS = """
document.documentElement.classList.add('js');
(function(){
  var pages=[].slice.call(document.querySelectorAll('.page'));
  var still=/[?&]static=1/.test(location.search)||window.matchMedia('print').matches;
  function finalNumbers(){still=true;[].forEach.call(document.querySelectorAll('[data-count]'),function(el){el.textContent=el.getAttribute('data-count');});}
  function count(el){
    var target=+el.getAttribute('data-count'),t0=null;
    if(still||!target||window.matchMedia('(prefers-reduced-motion: reduce)').matches){return;}
    function step(ts){if(still){el.textContent=target;return;}if(!t0){t0=ts;}var k=Math.min(1,(ts-t0)/900);
      el.textContent=Math.round(target*(1-Math.pow(1-k,3)));if(k<1){requestAnimationFrame(step);}}
    requestAnimationFrame(step);
  }
  function show(p){if(p.classList.contains('in')){return;}p.classList.add('in');
    [].forEach.call(p.querySelectorAll('[data-count]'),count);}
  /* ?static=1 shows everything at once, without motion (for screenshots and checks) */
  if(/[?&]static=1/.test(location.search)){document.documentElement.classList.add('static');pages.forEach(show);return;}
  if(!('IntersectionObserver' in window)||window.matchMedia('print').matches){pages.forEach(show);return;}
  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){show(e.target);io.unobserve(e.target);}});},{threshold:0,rootMargin:'0px 0px -12% 0px'});
  pages.forEach(function(p){io.observe(p);});
  window.addEventListener('beforeprint',function(){finalNumbers();pages.forEach(show);});
})();
"""


def render(lang: str) -> str:
    ps = pages()
    n = len(ps)
    out = []
    for i, p in enumerate(ps, 1):
        top = f'<div class="top"><span>{esc(BRAND)}</span><span class="pn">{i} / {n}</span></div>'
        if p.get("kind") == "title":
            draft = ("" if BUILT else
                     '<div class="draft">Wersja robocza: opis rozwiązania budowanego podczas hackathonu</div>')
            inner = (
                f'{draft}<div class="top"><span>HackNation 2026 · zadanie „Cyfryzacja formularzy”</span>'
                f'<span class="pn">{i} / {n}</span></div>'
                '<div class="grid wide"><div class="txt title-top">'
                '<h1 class="rv">Od potrzeby do podpisu</h1>'
                '<p class="sub rv" style="--d:.15s">Jedna wizyta, komplet wniosków.</p>'
                '<p class="lead rv" style="--d:.3s">AI zamienia urzędowy druk w\u00a0usługę. Mieszkaniec podaje dane tylko raz. '
                'Urzędnik niczego nie przepisuje i\u00a0sprawdza tylko to, co wymaga sprawdzenia.</p>'
                '<ul class="chips rv" style="--d:.45s"><li>otwarty kod (MIT)</li><li>działa lokalnie w urzędzie</li>'
                '<li>dane w pokazie są syntetyczne</li></ul></div>'
                f'<div class="art">{ribbon("rb1", sub=False, base=False)}</div></div>')
        else:
            body = p.get("body_html") or f'<p class="body rv" style="--d:.15s">{esc(nb(p["body"]))}</p>'
            src = f'<p class="src rv" style="--d:.3s">{esc(nb(p["src"]))}</p>' if p.get("src") else ""
            extra = nb(p.get("extra", "")) if "qr" not in p.get("extra", "") else p["extra"]
            art = p["art"]
            if p.get("kind") == "wide":
                inner = (f'{top}<div class="grid wide"><div class="txt"><h2 class="rv">{esc(p["h"])}</h2>{body}</div>'
                         f'<div class="art">{art}</div></div>')
            else:
                art_cls = "art rv" if p.get("art_html") else "art"
                inner = (f'{top}<div class="grid"><div class="txt"><h2 class="rv">{esc(p["h"])}</h2>{body}{extra}{src}</div>'
                         f'<div class="{art_cls}" style="--d:.2s">{art}</div></div>')
        out.append(f'<section class="page" id="s{i}"><div class="inner">{inner}</div></section>')
        if lang == "ru":
            out.append(f'<aside class="note"><h3>Страница {i}: по-русски</h3><p>{esc(p["ru"])}</p>'
                       f'<h3>Зачем она и что помнить</h3><p>{esc(p["why"])}</p></aside>')
    if lang == "ru":
        title = "Od potrzeby do podpisu: версия для чтения с пояснениями по-русски"
        intro = ('<p class="intro"><b>Версия для Андрея.</b> Это те же десять страниц, которые прочитает жюри, '
                 'по-польски. Под каждой страницей перевод и пояснение: зачем она нужна и что помнить. '
                 'Эту страницу не публикуем; для жюри предназначен файл <b>index.html</b> и PDF.</p>')
        html_lang = "ru"
    else:
        title = "Od potrzeby do podpisu: jedna wizyta, komplet wniosków"
        intro = ""
        html_lang = "pl"
    desc = ("AI zamienia urzędowy druk w usługę; mieszkaniec podaje dane raz, urzędnik sprawdza tylko wyjątki, "
            "komplet wniosków drukuje się na oryginalnych wzorach. Projekt na HackNation 2026, zadanie Cyfryzacja formularzy.")
    return (f'<!DOCTYPE html>\n<html lang="{html_lang}">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>{esc(title)}</title>\n'
            f'<meta name="description" content="{esc(desc)}">\n<style>{CSS}</style>\n</head>\n<body>\n'
            f'<main class="wrap" lang="pl">{intro}{"".join(out)}</main>\n<script>{JS}</script>\n</body>\n</html>\n')


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for lang, name in (("pl", "index.html"), ("ru", "ru.html")):
        (OUT / name).write_text(render(lang), encoding="utf-8")
        print("wrote", OUT / name)


if __name__ == "__main__":
    main()
