"""WAVE-10 VJF-3: a list of attachments announced in the filer's own words ("Do wniosku o dokonanie podziału
dołączam:", "Załączam następujące dokumenty:") with numbered items and no lines to write on gave no upload at all;
only "Załączniki:" and "Do wniosku należy dołączyć:" opened a list. Synthetic papers; negative cases: the header
alone, and a sentence that only mentions an attachment, give no upload.
"""
from __future__ import annotations

from app.find import find
from app.mean import understand
from tests.find.find_builders import DOTS, Native, model


def _paper(header: str, items: tuple[str, ...]) -> list[str]:
    n = Native()
    n.text(70, 60, "WNIOSEK O PODZIAL NIERUCHOMOSCI", 300, bold=True)
    n.text(50, 100, "Nazwa wnioskodawcy", 100)
    n.text(160, 100, DOTS, 200)
    n.text(50, 140, header, 250)
    y = 154
    for item in items:
        n.text(60, y, item, 300)
        y += 14
    n.text(50, y + 30, "Podpis wnioskodawcy", 150)
    m = model(n.page())
    return [a.label for a in understand(m, find(m)).attachments if a.covered_by is None]


ITEMS = ("1. mapę z projektem podziału,", "2. wypis z rejestru gruntów,", "3. decyzję o warunkach zabudowy.")
WANT = ["Mapę z projektem podziału", "Wypis z rejestru gruntów", "Decyzję o warunkach zabudowy"]


def test_a_numbered_list_after_dolaczam_is_one_upload_per_item() -> None:
    assert _paper("Do wniosku o dokonanie podziału dołączam:", ITEMS) == WANT


def test_other_first_person_headers_open_the_list_too() -> None:
    assert _paper("Załączam następujące dokumenty:", ITEMS) == WANT
    assert _paper("Do zgłoszenia dołącza się:", ITEMS) == WANT


def test_open_lines_under_zalaczam_are_one_upload_not_a_text() -> None:
    n = Native()
    n.text(70, 60, "ZGLOSZENIE ZMIAN DANYCH", 300, bold=True)
    n.text(50, 100, "Nazwa wnioskodawcy", 100)
    n.text(160, 100, DOTS, 200)
    n.text(50, 140, "Do zgłoszenia załączam:", 150)
    n.text(50, 156, DOTS, 400)
    n.text(50, 172, DOTS, 400)
    m = model(n.page())
    b = understand(m, find(m))
    assert [a.label for a in b.attachments if a.covered_by is None] == ["Inne załączniki"]
    assert not any("załączam" in f.label for s in b.matter for f in s.fields)


def test_the_header_alone_gives_no_upload() -> None:
    assert _paper("Do wniosku dołączam:", ()) == []
