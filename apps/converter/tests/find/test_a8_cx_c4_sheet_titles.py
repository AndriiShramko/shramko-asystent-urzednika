"""A8 CX, ORDER C4: tables of sheets and Word files.

1. A row of a lone letter or number and one text cell across most of the width ("B | INFORMACJA O ...") is a section
   title: never the column header of the places under it, never a label.
2. A label cell merged over several rows names one place, not one place per row it covers.
3. A blank with no words left of it takes its name from a caption printed right under it ("/ numer karty /"), or
   from a lead-in line ending in ":" right above it.

Synthetic words only; built with openpyxl and read by our own XLSX reader.
"""
from __future__ import annotations

import io

from app.find import find
from app.readers import read_document
from find_builders import STRICT, flow, model, tops

DOTS = "." * 30


def test_long_lead_in_with_colon_names_the_dotted_line_under_it():
    page = flow("B. INFORMACJA O ZWIERZECIU",
                "Pochodzenie zwierzecia (metryka, numer rodowodu, imie, nazwisko i adres poprzedniego wlasciciela):",
                DOTS, bold=(0,))
    out = find(model(page), STRICT)
    labels = [c.label.text if c.label else None for c in tops(out)]
    assert any(lab and lab.startswith("Pochodzenie zwierzecia") for lab in labels), labels


def test_head_of_a_list_or_a_long_instruction_names_no_blank():
    """Negative control: "Załączniki do wniosku:" and a 15-word instruction ending in ':' above empty cells."""
    from openpyxl.styles import Border, Side

    thin = Side(style="thin")

    def fill(ws):  # noqa: ANN001
        ws["A1"] = "Nr sprawy:"    # a first row that is not a header of columns
        ws["A2"] = "Załączniki do wniosku:"
        ws.merge_cells("A2:H2")
        ws["A5"] = ("Wskaz rodzaje dyscyplin, w ktorych bierze udzial osoba objeta wnioskiem, a nastepnie wybierz "
                    "dyscypliny z listy ponizej:")
        ws.merge_cells("A5:H5")
        for r in (3, 7):
            ws.merge_cells(f"A{r}:G{r}")
            for col in "ABCDEFG":
                ws[f"{col}{r}"].border = Border(bottom=thin)

    labels, _ = _labels(_book(fill))
    assert not any(lab and ("Załączniki" in lab or "Wskaz" in lab) for lab in labels), labels


def _book(fill) -> bytes:  # noqa: ANN001
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Formularz"
    fill(ws)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _labels(data: bytes) -> tuple[list[str | None], object]:
    out = find(read_document(data, "xlsx"), STRICT)
    return [c.label.text if c.label else None for c in tops(out)], out


def test_lettered_full_width_row_is_a_section_title_not_a_column_header():
    def fill(ws):  # noqa: ANN001
        ws["A1"] = "B"
        ws["B1"] = "INFORMACJA O ZWIERZETACH (w przypadku wiecej niz jednego wypelnic kilka kart)"
        ws.merge_cells("B1:F1")
        ws["A2"] = "Gatunek:"
        ws["B2"] = DOTS
        ws.merge_cells("B2:F2")
        ws["A3"] = "Data nabycia:"
        ws["B3"] = DOTS
        ws.merge_cells("B3:F3")

    labels, out = _labels(_book(fill))
    assert not any(lab and "INFORMACJA" in lab.upper() for lab in labels), labels
    assert any(lab and "Gatunek" in lab for lab in labels), labels
    assert any(lab and "Data nabycia" in lab for lab in labels), labels
    titles = [(s.number, s.title) for s in out.sections]
    assert ("B", "INFORMACJA O ZWIERZETACH") in titles, titles


def test_a_real_header_row_still_labels_its_columns():
    """Negative control: a header row of two or more words is still a header (rows of a list)."""
    def fill(ws):  # noqa: ANN001
        ws["A1"] = "Nazwisko"
        ws["B1"] = "Adres"
        ws["C1"] = "Kwota"
        ws["A2"] = DOTS
        ws["B2"] = DOTS
        ws["C2"] = DOTS

    labels, _ = _labels(_book(fill))
    assert {"Nazwisko", "Adres", "Kwota"} <= {lab for lab in labels if lab}, labels


def test_label_merged_over_rows_names_one_place():
    from openpyxl.styles import Border, Side

    thin = Side(style="thin")

    def fill(ws):  # noqa: ANN001
        for r in range(1, 20):
            ws.row_dimensions[r].height = 4
        ws["A3"] = "Kolor siersci:"
        ws.merge_cells("A3:C5")
        for r in (3, 4, 5):
            ws[f"D{r}"].border = Border(left=thin)
        ws.merge_cells("E4:H4")
        for col in "EFGH":
            ws[f"{col}4"].border = Border(bottom=thin)

    labels, _ = _labels(_book(fill))
    assert sum(1 for lab in labels if lab and "Kolor" in lab) == 1, labels


def test_caption_under_a_blank_names_it():
    def fill(ws):  # noqa: ANN001
        ws["A2"] = "Urzad Gminy Przykladowo"
        ws["A3"] = DOTS
        ws["A4"] = "/ numer karty /"
        ws["A6"] = DOTS
        ws["A7"] = "/ nr telefonu /"

    labels, out = _labels(_book(fill))
    assert "numer karty" in labels, labels
    assert "nr telefonu" in labels, labels


def test_lead_in_with_colon_above_a_blank_names_it():
    from openpyxl.styles import Border, Side

    thin = Side(style="thin")

    def fill(ws):  # noqa: ANN001
        ws["A1"] = "3. Osoba kontaktowa (pelnoletnia) w czasie wydarzenia:"
        ws.merge_cells("A1:H1")
        ws.merge_cells("A3:G3")
        for col in "ABCDEFG":
            ws[f"{col}3"].border = Border(bottom=thin)

    labels, _ = _labels(_book(fill))
    assert any(lab and "Osoba kontaktowa" in lab for lab in labels), labels


def test_caption_below_does_not_rename_a_place_labelled_on_its_left():
    """Negative control: words left of the place win over a hint printed under it."""
    def fill(ws):  # noqa: ANN001
        ws["A2"] = "Cel wynajecia:"
        ws["B2"] = DOTS
        ws["B3"] = "(rodzaj uroczystosci, np. urodziny)"

    labels, _ = _labels(_book(fill))
    assert "Cel wynajecia" in labels, labels
    assert not any(lab and "rodzaj uroczystosci" in lab for lab in labels), labels
