"""A8 CX, ORDER C2: a SHOW from the paper's own notes (design 40-show-rules, families A and C).

A. "Jeśli wybierzesz tę formę, wpisz poniżej nr rachunku" right under a choice: the fields after it are shown by the
   option printed last above the note; "Jeśli tak" by "Tak".
C. "Należy wypełnić w przypadku Wnioskodawcy – Klubu sportowego": the fields after it are shown by the option that
   shares the most words with the note.
Negative controls of design section 4: no choice on the paper, "jeśli różni się", "w przypadku jego braku": no SHOW.
Synthetic papers.
"""
from __future__ import annotations

from app.find import find
from app.mean import understand
from tests.find.find_builders import DOTS, flow, model


def _fields(*texts: str, bold: tuple[int, ...] = ()) -> dict[str, object]:
    m = model(flow(*texts, bold=bold))
    b = understand(m, find(m))
    return {f.label: f for s in b.matter for f in s.fields}


def test_family_a_note_under_a_choice_shows_the_account_on_the_last_option():
    got = _fields("WNIOSEK O ZWROT OPLATY", "5. Sposob zwrotu oplaty",
                  "□ Gotowka w kasie organu", "□ Przelewem na rachunek w banku",
                  "Jeśli wybierzesz tę formę, wpisz poniżej nr rachunku i dane jego właściciela",
                  "Nr rachunku: " + DOTS, "6. Podstawa prawna", "Art. 9 ustawy o oplacie", bold=(0, 1, 6))
    acc = next(f for k, f in got.items() if "rachunku" in k.casefold())
    assert acc.show_if is not None, got
    assert acc.show_if.is_ == "Przelewem na rachunek w banku"


def test_family_a_jesli_tak_shows_on_tak():
    got = _fields("WNIOSEK", "2. Zwierzeta", "Czy posiadasz psa?", "□ TAK", "□ NIE",
                  "Jeśli tak, podaj rasę psa", "Rasa psa: " + DOTS, bold=(0, 1))
    rasa = next(f for k, f in got.items() if "rasa" in k.casefold())
    assert rasa.show_if is not None and rasa.show_if.is_.casefold() == "tak", got


def test_family_c_note_names_its_option_and_shows_the_block():
    got = _fields("WNIOSEK O STYPENDIUM", "1. Wnioskodawca", "□ Prezydent Miasta", "□ Klub sportowy",
                  "Należy wypełnić w przypadku Wnioskodawcy – Klubu sportowego.",
                  "Numer licencji klubu sportowego " + DOTS, "Liczba zawodnikow klubu " + DOTS,
                  "2. Dane sportowca", "Dyscyplina " + DOTS, bold=(0, 1, 7))
    nazwa = next(f for k, f in got.items() if "licencji" in k.casefold())
    assert nazwa.show_if is not None and nazwa.show_if.is_ == "Klub sportowy", got
    dysc = next(f for k, f in got.items() if "dyscyplina" in k.casefold())
    assert dysc.show_if is None, "the next heading ends the block"


def test_negative_controls_stay_unconditioned():
    got = _fields("WNIOSEK", "1. Dane", "Jeśli wybierzesz tę formę, wpisz numer",
                  "Numer sprawy w urzedzie: " + DOTS,
                  "Adres do korespondencji (jeśli różni się od adresu zamieszkania) " + DOTS,
                  "Data szczepienia (w przypadku jego braku) " + DOTS,
                  "B.4 ADRES (wypełnić tylko w przypadku kiedy jest inny niż w poz. B.3)",
                  "Miejscowosc korespondencji " + DOTS, bold=(0, 1))
    assert got, got
    assert all(f.show_if is None for f in got.values()), {k: f.show_if for k, f in got.items()}


def test_family_c_one_shared_word_is_not_the_option():
    """Negative control: the only earlier choice shares one word by chance ("klubu") with the note."""
    got = _fields("WNIOSEK", "1. Korespondencja", "Na ktory adres kierowac korespondencje?",
                  "□ adres siedziby klubu", "□ inny adres korespondencyjny",
                  "Należy wypełnić w przypadku Wnioskodawcy – Klubu sportowego.",
                  "Numer licencji zawodnika " + DOTS, bold=(0, 1))
    lic = next(f for k, f in got.items() if "licencji" in k.casefold())
    assert lic.show_if is None, lic.show_if
