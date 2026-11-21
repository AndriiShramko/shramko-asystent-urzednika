"""The finder on the partner's task sets (local only; skipped where they are absent, e.g. in CI). WP-F3 acceptance.

Every behaviour asserted here also has a synthetic twin in test_find_core.py, because the image workflow sees no set.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.find import find
from app.model import count_coverage
from app.readers import read_document

pytestmark = [pytest.mark.sets, pytest.mark.slow]


def _found(set_key: str, fmt: str):  # noqa: ANN202
    from eval.golden import golden_inputs, judged_inputs

    hits = [p for p in golden_inputs() + judged_inputs()
            if set_key in Path(p).parent.name and p.suffix.lower() == f".{fmt}" and p.exists()]
    assert len(hits) == 1, f"{set_key} {fmt}: {len(hits)} files"
    pm = read_document(hits[0].read_bytes(), fmt)
    out = find(pm, {"strict": True})
    assert count_coverage(out, pm).unassigned == []
    return out


@pytest.mark.parametrize("fmt", ["pdf", "docx"])
def test_reference_1_has_the_four_blanks_of_the_sentence_with_their_labels(fmt):
    out = _found("reference-01", fmt)
    blanks = [c for c in out.candidates if c.kind == "blank_in_sentence"]
    assert [c.label.text for c in blanks] == ["w miejscowości", "przy ulicy", "nr ewidencyjny działki", "w obrębie"]
    assert [c.footnotes for c in blanks] == [[], ["1"], [], []]
    assert not any(c.page == 2 for c in out.candidates)        # the clause on page two yields no candidate


def test_set_2_postal_codes_and_dates_are_one_comb_each():
    out = _found("judged-02", "pdf")
    combs = {(c.label.text, c.cells, c.mask) for c in out.candidates if c.kind == "comb"}
    assert combs == {("NIP", 10, None), ("Kod pocztowy", 5, "__-___"), ("Data uiszczenia opłaty", 8, "DD-MM-RRRR"),
                     ("Data", 8, "DD-MM-RRRR")}
    assert sum(c.kind == "comb" and c.label.text == "Kod pocztowy" for c in out.candidates) == 2
    assert not any(c.section == "s1" for c in out.candidates)  # the instruction with example boxes: no candidate


def test_set_2_docx_instruction_example_boxes_are_not_candidates():
    out = _found("judged-02", "docx")
    assert not any(c.kind in ("box", "choice_group") and c.page == 1 for c in out.candidates)


def test_set_7_groups_blanks_and_the_applicant_section_first():
    out = _found("judged-07", "pdf")
    groups = [c for c in out.candidates if c.kind == "choice_group"]
    assert [[o.text for o in g.options] for g in groups] == [["pies", "suka"], ["mikroprocesor", "tatuaż", "brak"]]
    assert [o.blank is not None for o in groups[1].options] == [True, True, False]
    assert [g.label.text for g in groups] == ["Płeć", "Sposób oznakowania psa / nr ident."]
    assert [(s.number, s.title) for s in out.sections][:2] == [("A", "DANE IDENTYFIKACYJNE WNIOSKODAWCY"),
                                                               ("B", "INFORMACJA O POSIADANYM PSIE")]
    in_a = [c.label.text for c in out.candidates if c.section == out.sections[0].id]
    assert in_a[0] == "Imię i nazwisko" and len(in_a) >= 6
    assert not any(c.page == 2 and c.kind != "signature" for c in out.candidates)   # the clause: no candidate


@pytest.mark.parametrize("fmt", ["pdf", "docx"])
def test_set_9_the_square_character_counts_as_a_box(fmt):
    out = _found("judged-09", fmt)
    assert sum(c.kind == "box" for c in out.candidates) >= 9
    assert any(c.kind == "choice_group" and len(c.options) == 2 for c in out.candidates)
