# WP-F3b Matter quality (finder, understanding, composer second pass): status

Branch: wp/F3b-matter-quality   Stage now: core (first pass done; items 2, 4, 6, 7 left)

Owned for this pass: `apps/converter/app/find/**`, `app/mean/**`, `app/lexicon/**`, `app/compose/**` and their tests.
New tests: `apps/converter/tests/find/test_find_f3b.py` (5), `apps/converter/tests/compose/test_compose_f3b.py` (3).
Measuring: `bash tools/gate.sh py eval/briefs/make_briefs.py <main checkout>/eval/silver` (briefs stay local, git-ignored).

## Status
- [x] item 3, set 3 PDF: symbol-font marks (U+F0F0, U+F092 and Wingdings box codes) at the start of a line are option marks; set 3 PDF gives the CHECKBOX of five certificate options with "inne" and its text field, plus the purpose field
- [x] item 1, set 9 PDF: numbered headings without bold among the first three lines of a page open sections; a one- or two-word line under a heading continues it; the understanding step strips "I." / "1." before the title words -> one selector `rodzaj_wniosku` with three options, sections per variant
- [x] fast gate passed on fcf7ff4 (592 passed)
- [x] item 5, composer: a CHECKBOX without options is written with one option "Tak" (strict linter 0 errors); `ComposeResult.brief_keys` carries `Attachment.key` of an upload (the upload's id is made from the key when the brief gives one)
- [ ] item 3, set 3 DOCX: the list has no glyph in the text (Word numbering symbols); needs the reader to give the list marker (request 1) or a rule "question ending with ':' + list lines"; today 2 fields
- [x] item 2 (part): single boxes numbered 1., 2., 3. ... on one page under one heading are one group even with other places between them (set 8 PDF: CHECKBOX "Okoliczności" of four options); set 9 "Dane pełnomocnika ..." are section switches, left awaiting on purpose
- [x] item 7 (part): title continues into a smaller bold lower-case line (set 6 PDF and DOCX: "Wniosek o wydanie zezwolenia na zajęcie pasa drogowego w celu prowadzenia robót", was "Wniosek")
- [ ] item 4: reference 1 addressee (PDF glued capital "W"; DOCX "Wnioskodawca: Adresat:" two-column line)
- [ ] item 6: audit T1 fixtures (reservation PDFs "Numer sali" vs "Liczba uczestników"; vehicle sale notice with buyer PESEL, VIN, "Data zbycia")
- [ ] item 7: audit T4 (titles sentence case without "*", "Wniosek składa się wyłącznie osobiście" prunes the proxy route with the quote, parent/child and buyer blocks keep their owner)
- [ ] set 9 PDF lost per variant the fields "Numer telefonu", "Nazwa klubu sportowego", "Adres siedziby", "Telefon kontaktowy" (now under the heading "Wnioskodawca" they go to the standard applicant block); decide whether the club data are the entity applicant (standard) or matter
- [ ] acceptance: fast gate after merging main, check chain `bash tools/gate.sh py -m eval.chain --compare`, sets tests for the new numbers, reference 1 PDF = DOCX

## Decisions
- Symbol-font option marks: a fixed list of private-use glyphs (U+F0F0, U+F092, U+F06F, U+F071, U+F0A8, U+F0FE) counts as a mark only at the start of a line and before a word / measured on sets 3 and 9 PDF / rules out Symbol bullets (U+F0B7) and a glyph inside a sentence becoming a box.
- A numbered line that is not bold ("1. Wnioskodawca", "II. Wniosek o ...") is a heading only among the first three body lines of its page, at most ten words, no trailing ".:,;" / set 9 PDF starts each section on a new page, set 8 numbers its field labels in the body / rules out set 8's numbered labels becoming 100 sections (measured: first try without the page rule gave 95 and 106).
- A heading continues into the next line when that line has one or two words, starts with a capital, is not numbered and sits within one line height under it, not left of it / "Rady Miasta" / "Zgierza" / rules out the wrapped word becoming the label of the next group.
- A single yes-or-no box composes as CHECKBOX with one option "Tak" under the question's label / the strict linter refuses a choice without options and no export shows a CHECKBOX / rules out an option made from the label (brief 1.1) and a RADIO Tak/Nie that would force an answer.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| fields of the matter per judged set, before -> after, PDF (DOCX) | `bash tools/gate.sh py eval/briefs/make_briefs.py <silver>` | set 2: 5 (5) -> 5 (5); set 3: 2 (2) -> 3 (2); set 4: 7 (6) -> 7 (6); set 6: 18 (16) -> 18 (16); set 7: 10 -> 10; set 8: 32 (24) -> 38 (27); set 9: 83 (42) -> 62 (42). Strict-linter errors 0 on all 13 files | fcf7ff4 |
| silver match (Claude / Gemini labels matched by a field of ours), set 3 PDF | same | 0 / 0 -> 1 / 0 (the loose label measure does not credit the CHECKBOX options) | fcf7ff4 |
| set 8: no field lost | scratch diff of the briefs before/after | PDF: only additions (Województwo, Gmina); DOCX: only additions (Numer nieruchomości/domu, Numer lokalu, Kod pocztowy) | fcf7ff4 |
| set 9 PDF one selector | scratch dump | RADIO `rodzaj_wniosku` with 3 options; sections `matter/w1/...`, `w2`, `w3` shown by it; title "Wniosek o przyznanie stypendium sportowego Rady Miasta Zgierza" (was "... Zgierza ii") | fcf7ff4 |
| unit tests | `bash tools/gate.sh py -m pytest apps/converter/tests/find apps/converter/tests/mean apps/converter/tests/compose apps/converter/tests/pipeline -q -m "not slow"` | 159 passed (151 before the new tests), sets tests included | fcf7ff4 |
| fast gate | `bash tools/gate.sh fast` | 592 passed, 21 deselected; "gate: fast PASSED on fcf7ff4" | fcf7ff4 |

## Negative control
`PUA_RE` switched off in `app/find/_core.py` (`if pua:` -> `if pua and False:`): `test_symbol_font_marks_make_one_group_with_the_blank_of_inne` failed (1 failed, 4 passed); file restored from a copy -> 5 passed. Nothing committed in the broken state.

## Requests to lead
1. WP-F2 (DOCX reader): give the list marker of a numbered or bulleted paragraph (`w:numPr` with a symbol-font level, e.g. Wingdings) as text or as a run attribute; set 3 DOCX prints its certificate options only through list numbering, so no rule here can see them as options.

## Cost notes
- core: getting a before/after per field took the most turns (the worktree guard refuses compound git commands; a baseline had to be produced by copying the old module in and out). Cheaper: a committed `make_briefs.py --out DIR` and a `--diff OLD NEW` mode.
