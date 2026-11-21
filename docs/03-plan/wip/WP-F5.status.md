# WP-F5 Composer: status

Branch: wp/F5-composer   Stage now: core (done) -> integration

## Status
- [x] Library of standard sections cut from both exports, `Standard` parameters, presets `EXPORT_1`, `EXPORT_5` (57b0de9)
- [x] `compose(brief, options) -> ComposeResult` in `apps/converter/app/compose/__init__.py`: pages, pagination, ids (D10), techNames (D7), HTML (D11), last page (D5), validators switch (D8), repeating style, origins and brief keys for the sidecar (57b0de9)
- [x] D16 statutory representative (on by default), D17 reason of exemption (off by default), D18 sole trader on the entity path (57b0de9)
- [x] Fixture briefs of reference sets 1 and 5 written by hand; synthetic briefs for the controls (57b0de9)
- [x] Tests without the sets (57) and with the sets (6); fast gate green (57b0de9)
- [x] One negative control recorded (see below)
- [ ] Integration: the lead wires `app/config.py` and `app/pipeline.py` to `ComposeOptions` and `compose` (request 4)
- [ ] Integration: replace `CONCEPT_VALIDATORS` by the table of WP-F8 and `compose/query.py` by the writer of WP-F7 when they exist; conditions inside repeating sections are theirs
- [ ] Acceptance: `git merge --no-edit main`, fast gate again, evidence table refreshed on that commit
- [ ] Acceptance: the "cheapest test" on the seven judged outputs (needs the briefs of WP-F4); today it runs on reference 5 only
- [ ] Acceptance: briefs from WP-F4 instead of the hand-written fixtures for the two reference sets

## Decisions
- Plan first, write last / builders return `spec.Sec`, `spec.Comp`; one step `_emit` gives names, ids and conditions / rules out a condition path that is stale after a rename.
- Comparison with an export ignores ids and grid, compares HTML by visible text (D11, answer J14) and conditions without white space / the markup is ours / rules out byte equality of HTML; 10 and 5 differences are named in `test_compose_sets.py` and the test fails on one more or one fewer.
- `Standard` holds what the two exports do differently; defaults are export 5's wording and `TERYT_4G_DOWODOWY` everywhere (design 6.6); the brief switches PESEL, REGON, KRS / rules out copying one export's accidents into every form.
- Not copied from the exports: the slip "pełnomonictwo", `defaultValue: ""` on `ulica_siedziba`, the uneven `searchEnabled` / `multiLevelTree` / listed in the library's docstring / rules out a silent difference.
- techName: library names are fixed and reserved first; a paper label gives its slug, on a collision the role suffix, then a number / design 6.5.7 / a changed label changes the techName, never an id.
- Ids: `uuid5(ns, "<form key>/<section role>/<field key>")`; the page is not in a field's path; a matter page takes the role of the section that opens it; parts of a split section are `#2`, `#3` / D10 / re-pagination changes no field id.
- Pagination: at most 10 fields on a matter page; a longer section is split into parts "(część n)"; a repeating section is never split; a page takes the title of its first section, made unique / design 6.5.2 / no page title in the brief (request 1).
- No empty page: structural rule, every page holds a section without a condition with a component without a condition, else a short note is added; `pages_without_fixed_content(form)` is exported for the gate / stronger than replaying journeys / rules out enumerating answers.
- D16: a third RADIO `wybierz_jako_kto_wnioskujesz_inna_osoba` (Pełnomocnik, Przedstawiciel ustawowy) shown for "Innej osoby", and its own proof section; power of attorney and stamp duty then need "Pełnomocnik" / the two radios of the exports stay unchanged / switch off gives the exports' block exactly.
- D17: one RADIO of five reasons shown when the answer is "Nie" / RADIO is a shape the exports show / off by default.
- D18: NIP, REGON or KRS asked of a person opens the entity path and is asked in "Dane podmiotu"; remark `SOLE_TRADER_AS_ENTITY` / a person's block never carries them.
- Validators: `REQUIRED` only from the brief; the concept table for paper fields; standard fields get format validators only (`ZIP_CODE`, `EMAIL`, `NIP`, `REGON`, typed `PESEL`) / the standard's required marks were not measured / rules out guessing obligation.
- Conditions: `compose/query.py` writes only the notation of the exports; a condition inside a repeating section is not written and is a remark / that notation belongs to WP-F7.
- Honest gaps: no title -> placeholder; no addressee -> empty editable field; applicants not stated -> the full standard block; no https address of the clause -> consent without a link; each with a remark / rules out a silent default.
- Remarks are our own `Remark(code, detail, field)` / the closed `WarningCode` list lacks most of them (request 3) / WP-F15 maps them.
- A label is text: titles and options are kept verbatim, HTML is made only by `compose/html.py` (escape, then `nh3` allow-list); angle brackets in a label give the remark `MARKUP_IN_LABEL`.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| Every standard section of both exports rebuilt, ids ignored | `bash tools/gate.sh py -m pytest apps/converter/tests/compose/test_compose_sets.py -q` | set 1: 15 sections, 49 components, 10 named tolerances; set 5: 15 sections, 48 components, 5 named tolerances | 57b0de9 |
| Same pages, same standard sections, fields of the matter; printed comparison | same file | set 1: 4 of 4 matter fields matched, 0 missing, 0 extra, page title "Lokalizacja budynku" vs "Informacje o budynku" (named); set 5: 7 of 7, 0, 0, the two conditions equal | 57b0de9 |
| Default options against the exports | same file | set 5: 73 matched, 0 missing, 3 extra (D16); set 1: 61 matched, 8 missing (wording variants, REGON, KRS, two techNames), 9 extra | 57b0de9 |
| Two runs byte-identical | `... -m pytest apps/converter/tests/compose/test_compose_core.py -q` | 9 briefs | 57b0de9 |
| One changed label changes that title and no id | same file | 1 title differs, 0 ids | 57b0de9 |
| No page empty on any journey | same file | 27 forms (9 briefs x 3 option sets): 0 pages without fixed content; seven journeys and the zero-answer canary evaluated with JSONata on reference 5 | 57b0de9 |
| Strict profile on every composed form | same file | 27 forms: schema and `coi_lint` strict, 0 errors; every condition parses | 57b0de9 |
| Negative controls | same file | same title twice -> unique techNames; `<img src=x onerror=1>` -> text, 0 markup, 6 escaped copies; 100 fields -> 10 pages of 10 | 57b0de9 |
| Fast gate | `bash tools/gate.sh fast` | 134 passed | 57b0de9 |

## Negative control
On 57b0de9, `Names.unique` was made to return the slug without the uniqueness check (working tree only, never committed). `pytest apps/converter/tests/compose/test_compose_core.py -k "same_title or gate"`: 7 failed of 28, among them `test_two_sections_with_the_same_title_give_unique_technames` and the gate test on the briefs whose labels collide with the library. Restored with `git checkout -- apps/converter/app/compose/names.py`; all 63 composer tests pass again.

## Requests to lead
1. Brief model: an optional page title (or heading level) on `MatterSection`. Today a matter page takes the title of its first section, so set 1 gives "Lokalizacja budynku" where the export says "Informacje o budynku".
2. Brief model: `MatterSection.hint` (export 5 has a description on "Korekta deklaracji"; ours is empty) and `Attachment.key` (an attachment's id is made from the slug of its label, so there a changed label changes the id).
3. `WarningCode`: no code for `CONDITION_NOT_WRITTEN`, `SECTION_SPLIT`, `REPEATING_FLATTENED`, `STEP_NOTE_ADDED`, `MARKUP_IN_LABEL`, `TITLE_MISSING`, `ADDRESSEE_MISSING`, `APPLICANTS_ASSUMED`, `SOLE_TRADER_AS_ENTITY`, `CLAUSE_LINK_MISSING`, `NO_MATTER`, `EXTRA_NOT_PLACED`. Either add them or let WP-F15 map `ComposeResult.remarks`.
4. Wiring (WP-F1 files): `FINISH_STYLE`, `VALIDATORS`, `REPEATING_STYLE`, `STATUTORY_REPRESENTATIVE`, `POA_EXEMPTION`, `FORM_KEY`, `ID_NAMESPACE` -> `app.compose.ComposeOptions`; the pipeline calls `compose(brief, options)`.
5. Docket of contradictions, three new rows: export 1's fee note names another form in the transfer title ("Wniosek o zwrot opłaty skarbowej"); both exports misspell "pełnomonictwo"; the contact page and the consent section are named differently in the two exports.
6. Owner's eye: with D16 on (default) the conditions of `pelnomocnictwo` and `oplata_skarbowa_pelnomocnictwo_1` differ from the exports (they also need "Pełnomocnik" in the new question).

## Not verified
- Whether the partner's engine skips `REQUIRED` on a field that a condition hides. We write `REQUIRED` from the brief also on conditional fields.
- Whether the partner's generator shows a title as text. A label with angle brackets is passed verbatim and reported.
- The wording of the D16 and D17 texts was written here and not read by a lawyer or the business side.

## Cost notes
- core: reading the two exports in full (about 12k tokens) and writing the library took the most; a committed, id-free digest of the standard sections (text and conditions per techName) would let the next stage skip the exports.
