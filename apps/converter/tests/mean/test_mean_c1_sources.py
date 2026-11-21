"""WP-C1 step e: the cues are read in the field's hint and in the title of its own section, not only in the label.
The field's own words (label, hint, footnote) outrank the title. Synthetic labels; before this step every case
here was "required, inferred"."""
from __future__ import annotations

from tests.mean.test_mean_c1_negation import field_of


def test_an_optional_wording_in_the_hint_makes_the_field_optional_and_the_hint_stays() -> None:
    f = field_of("Adres składzika (jeśli różni się od adresu ogrodu)")
    assert (f.required, f.required_basis, f.hint) == (False, None, "jeśli różni się od adresu ogrodu")


def test_a_required_cue_in_the_hint_is_required_by_the_paper() -> None:
    f = field_of("Nazwa ogrodu (pole wymagane)")
    assert (f.required, f.required_basis) == (True, "paper")


def test_a_negated_cue_in_the_hint_is_optional() -> None:
    f = field_of("Kolor furtki (nie jest wymagany)")
    assert (f.required, f.required_basis) == (False, None)


def test_a_conditional_cue_in_the_hint_is_not_required_by_the_paper() -> None:
    f = field_of("Kolor furtki (wymagany w przypadku ogrodu z ogrodzeniem)")
    assert (f.required, f.required_basis) == (True, "inferred")


def test_the_section_title_makes_its_fields_optional() -> None:
    f = field_of("Kolor furtki", title="Dane dodatkowe (pola nieobowiązkowe)")
    assert (f.required, f.required_basis) == (False, None)


def test_a_bracket_of_the_section_title_makes_its_fields_required_by_the_paper() -> None:
    f = field_of("Nazwa ogrodu", title="Dane ogrodu (pola obowiązkowe)")
    assert (f.required, f.required_basis) == (True, "paper")


def test_a_cue_word_in_the_running_title_of_a_section_is_no_cue() -> None:
    f = field_of("Nazwa ogrodu", title="Informacja o wymaganych nasadzeniach")
    assert (f.required, f.required_basis) == (True, "inferred")


def test_a_conditional_bracket_of_the_section_title_is_no_cue() -> None:
    f = field_of("Nazwa ogrodu", title="Dane ogrodu (wymagane w przypadku ogrodu z ogrodzeniem)")
    assert (f.required, f.required_basis) == (True, "inferred")


def test_the_fields_own_words_outrank_the_section_title() -> None:
    f = field_of("Ewentualne uwagi o ogrodzie", title="Dane ogrodu (pola obowiązkowe)")
    assert (f.required, f.required_basis) == (False, None)
    f = field_of("Nazwa ogrodu - pole wymagane", title="Dane dodatkowe (pola nieobowiązkowe)")
    assert (f.required, f.required_basis) == (True, "paper")
