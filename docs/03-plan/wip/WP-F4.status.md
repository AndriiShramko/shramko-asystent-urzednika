# WP-F4 Understanding (the brief): status

Branch: wp/F4-understanding   Stage now: core (done); next: integration, then acceptance

Entry: `from app.mean import understand`; `understand(page_model, finder_output, options=None) -> Brief` (revision 1.1,
one disposition per finder candidate). Files: `apps/converter/app/mean/__init__.py` (entry, safety net), `_doc.py`
(reading order, roles, text operations), `_head.py` (title, variants, addressee, applicants, legal basis, fee, clause),
`_fields.py` (fate of every candidate, fields of the matter, declarations, composite). Lexicons:
`apps/converter/app/lexicon/*.json` (six tables, a source and a date per row) with the loader `app.lexicon`.
Tests: `apps/converter/tests/mean/test_mean_core.py` (30, synthetic papers built from code).

## Status
- [x] lexicons as data files and their loader (a row without source or date is refused)
- [x] title (lines joined, sentence case, legal reference removed, crossed alternatives as "lub", annex header never a title) and addressee (body or office, name on two lines, section "Organ, do którego", `ADDRESSEE_CONFLICT` with both quotes)
- [x] fate of every candidate: applicant block -> STANDARD with a role, signature / place and date / office use -> LEFT_OUT with a reason, unlabelled -> AWAITING_DECISION, the rest -> fields of the matter with type, concept, length, hint, evidence, confidence
- [x] who may apply from the wording table (person, entity, both; capacities; NIP/REGON/KRS/PESEL as applicant extras)
- [x] paper habits: combs by mask and label, "od ... do ..." as two dates, starred alternatives (one RADIO asked once; grammar variants no field), choice groups (RADIO / CHECKBOX / SELECT), an option followed by a blank (field with `show_if`), equal rows -> repeating section, attachments (named items, cover by the standard, "Inne załączniki"), declarations "Oświadczam, że" as items, clause linked, fee stated / ambiguous / not_found, legal basis
- [x] required: optional only when the paper says so; every other field required with basis `inferred` and the warning `REQUIRED_INFERRED`
- [x] composite papers: one selector `rodzaj_wniosku`, sections shown by it, equal sections written once (`SAME_ALTERNATIVE`)
- [x] 30 unit tests pass; smoke on the nine local sets (PDF and DOCX, 17 files): no exception, gate passes, 0 strict-linter errors; one negative control recorded
- [ ] INTEGRATION: wire `find` + `understand` into `apps/converter/app/pipeline.py` in place of `interim.brief_from_pages` (interim stays the fallback when the finder yields no candidate, with a warning); `assemble_ledger` through the inverse of `ComposeResult.brief_keys`; meta `converter.pipeline` = `brief`; finder and brief warnings into the sidecar
- [ ] ACCEPTANCE: `eval/briefs/<set>.json` per judged set and the differences from the silver labels (`tools/eden/silver_briefs.py --compare`) listed and explained; set tests with `@pytest.mark.sets`
- [ ] ACCEPTANCE: reference 1 and 5 give the same brief from every format. Today: reference 1 has 4 fields of the matter from PDF and from DOCX but the addressee is `not_found` in both (PDF: the capital "W" of "Wójt" is glued to the run before it; DOCX: not looked at); reference 5 has 6 fields from DOCX and 5 from PDF. Formats other than PDF and DOCX were not run
- [ ] ACCEPTANCE: set 9 from the PDF gives no selector (the finder reports no section and no bold there; the DOCX gives the selector); set 3 has 2 fields only (the finder does not see the list printed with the glyph U+F0F0 as boxes)
- [ ] not built: `applicants.options` items; the row "in person only"; a condition stated by a footnote ("wypełnić tylko w przypadku ...") as `show_if`; explanations keyed to positions as hints; the lemmatiser step for labels (phrase table, then raw words with `LABEL_RAW`); `mandatory_attachments` is always `not_found`
- [ ] labels cut from sentences stay raw on sets 6, 8, 9 (1 to 7 `LABEL_RAW` per file): the phrase table has 7 rows; mine more with `tools/eden/eden.py`, each row with a rule test

## Decisions
- Entry `understand(pm, fo, options)`; without `strict` it never raises: a failing rule gives a brief with `UNREADABLE_PART` and every candidate AWAITING_DECISION / the pipeline must not answer 500 / rules out a partial brief after a crash.
- Lexicons are six JSON tables read by `app.lexicon` (`rows`, `regex`, `compiled`); code holds no wording except structural patterns (numbering, brackets) / a rule changes without code / rules out word lists inside the rules.
- Applicant block = a label the standard asks AND (before the title on its page OR under an applicant heading) / "telefon" of a contractor in the matter is a field of the matter / rules out sending every "imię i nazwisko" to the standard.
- A place without a label waits for a decision; only a dotted line directly under a field of the matter is merged (LINE_BLOCK, the field becomes TEXTAREA) / no label is invented / rules out guessing from position.
- Required: optional only by the paper's mark (bracket or footnote, matched with whitespace removed); everything else required with `REQUIRED_INFERRED` per field; a field shown by an option is not required / design 6.4.3 / rules out silent defaults.
- Starred alternatives are read only when the paper says "niepotrzebne skreślić"; grammar = same stem (prefix of at least 60 % of the shorter word) or a bare ending / testable, no dictionary / a star alone is a footnote mark.
- Choice group: two options or an excluding word -> RADIO; more than five -> SELECT; otherwise CHECKBOX with options and `AMBIGUOUS_GROUP` / RADIO would forbid several answers the paper may allow.
- A single box outside a group waits for a decision with `AMBIGUOUS_GROUP` / on sets 8 and 9 such boxes are options the finder did not group, and the composer writes a yes-or-no CHECKBOX in a shape the strict linter refuses (request 1) / rules out one yes-or-no field per box.
- Equal rows: the same run of 2 to 6 distinct labels at least three times in one section -> one repeating section, later rows MERGED (TABLE_ROW) / two equal blocks may be two persons / rules out merging at two repeats.
- Composite: the title's own word ("wniosek") again in a title-like line among the first eight lines of a later page, each with candidates -> one RADIO; sections equal word for word are written once / never a second form.
- Addressee conflict: another office or body named anywhere whose proper-name words share no four-letter beginning with the addressee's / declension keeps the beginning / body and office of one municipality do not conflict.
- Fee is `stated` only with an amount in złoty beside the word; two different amounts: `ambiguous`; `legal_basis` and the clause are quotes / the receipt never guesses.
- Title: a line that starts with a title word and stands out (bold, capitals or a finder heading); when none stands out the plain rule of `app.interim.find_title` is the fallback, filtered by the same words / no regression against today's results.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| unit tests of the rules (title, addressee, applicants, habits, required, composite, negative controls) | `bash tools/gate.sh py -m pytest apps/converter/tests/mean -q` | 30 passed | 9004715 |
| negative controls of the package: annex header never a title; clause never fields; "hodowanie/utrzymywanie*" one choice, "charta/chartów*" none; fee not on the paper `not_found` | same run: `test_an_annex_header_...`, `test_the_clause_never_...`, `test_grammar_alternatives_...`, `test_a_fee_that_is_not_...` | passed | 9004715 |
| cheapest test 1 (another municipality and title: the fields do not change) | same run: `test_another_municipality_...` | passed | 9004715 |
| fields of the matter per judged set, PDF (DOCX): smoke script, read -> find -> understand(strict) -> compose -> gate -> `tools.coi_lint.check` | scratch script (not in git), 17 files | set 2: 5 (5); set 3: 2 (2); set 4: 7 (6); set 6: 18 (16); set 7: 10 (no DOCX); set 8: 32 (24); set 9: 83 (42 with the selector); reference 1: 4 (4); reference 5: 5 (6). Gate passed 17 of 17; strict linter 0 ERROR, 7 WARN on each | 9004715 |
| set 6 `ADDRESSEE_CONFLICT` | same smoke | raised from PDF and from DOCX, two quotes | 9004715 |
| set 9 one selector, no second form | same smoke | DOCX: one RADIO `rodzaj_wniosku`; PDF: none yet (see Status) | 9004715 |
| fast gate of the repository | `bash tools/gate.sh fast` | 570 passed, 21 deselected; "gate: fast PASSED" | 9004715 |

The smoke is a measurement, not yet a test in git: the acceptance stage turns it into `@pytest.mark.sets` tests and `eval/briefs/`.

## Negative control
The requirement "the paper says niepotrzebne skreślić" was switched off (`app.mean._doc._STRIKE` replaced by a pattern
that always matches): `test_without_the_strike_out_note_a_star_is_only_a_footnote_mark` failed (a RADIO appeared for
"Imię/nazwa*"); with the pattern restored it passes. Run in the smoke script, nothing committed in the broken state.
A first attempt (switching off the annex-header pattern) did not fail the test, because the title words and the plain
rule of `app.interim` each refuse that header too: that control is redundant by design.

## Requests to lead
1. WP-F5: a CHECKBOX of the brief without options (contract 1.1: one yes-or-no box) is composed as a choice component without options; the strict linter answers "choice component without options and without dictionary" (seen on sets 2 DOCX, 8, 9 before decision "single box"). WP-F4 emits none until the composer has a shape for it.
2. WP-F5: check that `ComposeResult.brief_keys` carries the keys of attachments (`Attachment.key`); a FIELD disposition may name one, and `assemble_ledger` needs its form id (integration stage).
3. WP-F3: (a) set 3: options printed with the glyph U+F0F0 are not boxes, the group "Proszę o wydanie zaświadczenia o" is lost; (b) set 9 PDF: no section, no bold; (c) sets 8 and 9: single boxes with long texts are not grouped (22 to 35 candidates wait for a decision per file); (d) reference 1 PDF: the capital "W" of the addressee is part of the run before it.
4. Ownership: `apps/converter/tests/mean/**` is used by convention (as `tests/find/` is); please add it to the WP-F4 row.
5. Integration needs the edit of `apps/converter/app/pipeline.py` the brief of this stage grants; nothing outside the owned paths was edited in the core stage.

## Cost notes
- core: reading the finder's output on the nine sets (four dump views) and writing the rules in one pass took the most context; the fixes were three small rounds. Cheaper: a committed dump tool of the finder (`python -m app.find.survey --view <set>`) so the next stage does not write its own.
