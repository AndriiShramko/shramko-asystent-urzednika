# WP-F3b Matter quality (finder, understanding, composer second pass): status

Branch: wp/F3b-matter-quality   Stage now: acceptance (run on the merge of main; see Acceptance evidence)

Owned for this pass: `apps/converter/app/find/**`, `app/mean/**`, `app/lexicon/**`, `app/compose/**` and their tests.
New tests: `apps/converter/tests/find/test_find_f3b.py` (5), `apps/converter/tests/compose/test_compose_f3b.py` (3).
Measuring: `bash tools/gate.sh py eval/briefs/make_briefs.py <main checkout>/eval/silver` (briefs stay local, git-ignored).

## Status
- [x] item 3, set 3 PDF: symbol-font marks (U+F0F0, U+F092 and Wingdings box codes) at the start of a line are option marks; set 3 PDF gives the CHECKBOX of five certificate options with "inne" and its text field, plus the purpose field
- [x] item 1, set 9 PDF: numbered headings without bold among the first three lines of a page open sections; a one- or two-word line under a heading continues it; the understanding step strips "I." / "1." before the title words -> one selector `rodzaj_wniosku` with three options, sections per variant
- [x] fast gate passed on fcf7ff4 (592 passed)
- [x] review fixes: heading continuation needs the heading's style (bold, about the size) or a heading line over 60% of the page width; "osobiście" removes only the proxy route (other_person, pelnomocnik), keeps entity and reprezentant; 2 new synthetic tests failed before, pass after; find/mean/compose/pipeline 169 passed; sets tests of find and mean 17 passed; fast gate passed
- [x] item 5, composer: a CHECKBOX without options is written with one option "Tak" (strict linter 0 errors); `ComposeResult.brief_keys` carries `Attachment.key` of an upload (the upload's id is made from the key when the brief gives one)
- [ ] item 3, set 3 DOCX: the list has no glyph in the text (Word numbering symbols); needs the reader to give the list marker (request 1) or a rule "question ending with ':' + list lines"; today 2 fields
- [x] item 2 (part): single boxes numbered 1., 2., 3. ... on one page under one heading are one group even with other places between them (set 8 PDF: CHECKBOX "Okoliczności" of four options); set 9 "Dane pełnomocnika ..." are section switches, left awaiting on purpose
- [x] item 7 (part): title continues into a smaller bold lower-case line (set 6 PDF and DOCX: "Wniosek o wydanie zezwolenia na zajęcie pasa drogowego w celu prowadzenia robót", was "Wniosek")
- [ ] item 4: reference 1 addressee (PDF glued capital "W"; DOCX "Wnioskodawca: Adresat:" two-column line)
- [x] item 6: audit T1 fixtures as synthetic tests ("Numer sali" = TEXT_FIELD, "Liczba uczestników" = NUMBER; sale notice: buyer PESEL, "Numer VIN" (VIN added to the acronyms), "Data zbycia" DATEPICKER)
- [x] item 7: titles sentence case without "*" (already so on all 13 files), explicit exclusion "składa się wyłącznie osobiście" prunes other person / entity / capacities, the quote in evidence and in dropped (PAPER_INSTRUCTION; no new reason code, request 2); owners of parent/child and buyer blocks: not changed, see not verified
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

## Acceptance evidence (stage acceptance, main merged, head before this commit 58758fa)
| Item | Command | Result |
|---|---|---|
| 1 fast gate after merging main | `bash tools/gate.sh fast` | 630 passed, 2 skipped, 22 deselected; chain tests 21 passed; "gate: fast PASSED on 58758fa" (after the fix below, with the new test: 632 passed, 1 skipped, 22 deselected; chain tests 21 passed; fast PASSED) |
| 2 check chain | `bash tools/gate.sh py -m eval.chain --compare --archive <main checkout>/data/archive` (all three corpora) | 158 files: 145 converted, 13 refused, 0 failed; gate failures 0; strict-lint errors 0. compare: 3 worse (2 fatal), 32 better. Worse lines below |
| 3 matter fields per set, PDF (DOCX), main -> now | `make_briefs.py <silver>` | set 2: 5 (5) -> 5 (5); set 3: 2 (2) -> 3 (2); set 4: 7 (6) -> 7 (6); set 6: 18 (16) -> 18 (16); set 7: 10 -> 10; set 8: 32 (24) -> 38 (27); set 9: 83 (42) -> 58 (42). Lint errors 0 on all 13 |
| 3 silver (claude/gemini matched), PDF (DOCX) | same | set 3: 1/0 (0/0) [main 0/0]; set 4: 4/4 (4/4); set 6: 17/18 (16/18) |
| 4 reference 1 | scratch run of pipeline on PDF and DOCX | title "Wniosek o ustalenie numeru porządkowego" and the same 70 fields in the same order from both; Numer ewidencyjny działki, Obręb, Ulica, Numer budynku, Numer lokalu present in both. Addressee: still the open item (PDF glued "W", DOCX two-column line) |
| 4 set 9 PDF | scratch dump | RADIO "Wybierz rodzaj wniosku" / section "Rodzaj wniosku": one selector, sections per variant |
| 5 strict linter | chain (`strict-lint errors 0` on 145 converted files) and make_briefs (0 on 13) | 0 errors |
| 6 negative control | `_THIRD_PERSON.search(low)` made `and False` in `app/mean/_fields.py` | new test failed (1 failed, 4 passed); restored -> 5 passed |

Fix made in this stage (owned path `app/mean/_fields.py`): the first chain run had two fatal falls (set 9 ODS and XLSX 105 -> 65). Cause found by diffing unique labels against main: "Imię i nazwisko kandydata" / "... podopiecznego" under the heading "Wnioskodawca" were taken as the applicant's own name and passed to the standard block, so they vanished from the matter. A label of a third person (kandydat, podopieczn, zawodnik, sportowiec, trener, dziecko, uczestnik) is now a field of the matter. New test `test_a_name_asked_of_a_candidate_under_the_applicant_heading_is_a_field_of_the_matter`. After it ODS/XLSX 105 -> 72.

Worse lines after the fix (all set 9 "Wniosek o przyznanie stypendium"; no other file is worse):
- ODS 105 -> 72 (fatal by the 20 % rule), XLSX 105 -> 72 (fatal), PDF 133 -> 116. Reason: main copied the applicant's fields (Imię, Adres siedziby, EDoręczenia and so on) into six to nine "Szczegóły sprawy" sections, one per variant; now the heading "Wnioskodawca" routes them once to the standard sections and the variants hold only their own data. Unique labels that left the matter: "Nazwa klubu sportowego" (-> standard/dane_podmiotu) and "Telefon kontaktowy" (-> standard/dane_do_kontaktu) in ODS, XLSX and PDF; PDF "Poczta tradycyjna - ..." is now "Korespondencja z urzędem ..."; PDF gained 19 titles (selector, "Dane sportowca", "Dane trenera", consents, "Numer KRS"). DOCX unchanged (133 -> 133, no title lost or gained).
- This is the open item above (club data: entity applicant or matter). The two fatal lines need the lead's decision to move `eval/chain/baseline.json` (not owned here).

## Requests to lead (acceptance)
2. Decide the club data of set 9 (standard entity block, as now, or matter) and, if the lower field count of set 9 ODS/XLSX/PDF stands, run `python -m eval.chain --update-baseline`; `--compare` exits 1 on those two files until then.
3. `eval/chain` run overwrites the tracked `eval/chain/summary.json`; I restored it, did not commit it.
