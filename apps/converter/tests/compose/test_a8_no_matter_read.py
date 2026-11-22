"""A8 DX-3: a conversion that read no field of the paper says so, once, with the code NO_MATTER and a Polish text,
also when the matter holds only text, the fee or nothing but standard uploads (before: only when no matter section
was made at all). The form, the HTTP code and the JSON shape do not change: it is a remark, i.e. a sidecar warning
and the X-Converter-Warnings header. Synthetic briefs only."""
from __future__ import annotations

from compose_helpers import brief

from app.compose import compose

INFO = {"key": "pouczenie", "label": "Wniosek składa się w terminie 14 dni.", "type": "TEXT_BLOCK"}
FEE = {"status": "stated", "value": "Opłata skarbowa – 17 zł", "evidence": [{"quote": "Opłata skarbowa – 17 zł"}]}


def _no_matter(r) -> list:
    return [x for x in r.remarks if x.code == "NO_MATTER"]


def test_matter_of_text_only_is_reported_once_in_polish() -> None:
    r = compose(brief(matter=[{"title": "Pouczenie", "role": "matter/pouczenie", "fields": [INFO]}]))
    found = _no_matter(r)
    assert len(found) == 1
    assert "nie odczytano" in found[0].detail.casefold() and "ręcznie" in found[0].detail


def test_fee_alone_is_not_a_field_read_from_the_paper() -> None:
    assert len(_no_matter(compose(brief(matter=[], fee=FEE)))) == 1


def test_no_matter_at_all_is_reported_once() -> None:
    assert len(_no_matter(compose(brief(matter=[])))) == 1


def test_a_field_or_an_attachment_of_the_paper_is_not_reported() -> None:
    assert _no_matter(compose(brief())) == []
    assert _no_matter(compose(brief(matter=[], attachments=[{"label": "Mapa z zaznaczonym terenem", "required": True}]))) == []


def test_the_form_is_the_same_with_the_remark() -> None:
    b = brief(matter=[{"title": "Pouczenie", "role": "matter/pouczenie", "fields": [INFO]}])
    assert compose(b).form.to_json_bytes() == compose(b).form.to_json_bytes()
    assert [t.title for t in compose(b).form.tabs][-1] == "Strona końcowa"
