# WP-F3 Finder: status

Branch: wp/F3-finder   Stage now: integration (done as far as this package owns it)

Entry: `from app.find import find`; `find(page_model, options=None) -> FinderOutput` (revision 1.1, spans).
Files: `apps/converter/app/find/__init__.py` (entry, safety net), `_text.py` (runs -> lines with run offsets),
`_shapes.py` (boxes from rects and ruled lines, combs, reading order), `_core.py` (roles, sections, places, groups,
labels), `survey.py` (-> `eval/finder-sets.json`). Tests: `apps/converter/tests/find/`.

## Status
- [x] text layer: runs -> lines that keep run and offset; geometry pages joined by row and gap, flow pages in file order
- [x] boxes from rectangles and from separate ruled segments; combs with separators and printed pattern; reading order by white-space cuts
- [x] roles: page furniture, notes, clause (mode), headings -> sections with numbers and parents, instructions, legal basis
- [x] places: leader, line_block, blank_in_sentence, box (character and drawn), choice_group, comb, cell (drawn, labelled, table), widget, signature, office_use
- [x] labels by score (same line, left, caption under, above, header, question) with margin; honest gaps as warnings
- [x] synthetic tests (23) and tests on the sets (7); drills 3, 4, 7, 8, 10 each have a test (commit c591299)
- [x] survey module and `eval/finder-sets.json`; `main` merged, fast gate 519 passed (merge 7e54a49)
- [x] one negative control recorded
- [x] integration: `main` merged again (already up to date), fast gate 519 passed on 2a41ae3; wiring `find` into `app/pipeline.py` is the lead's (request 7)
- [ ] set 2: the account is a `cell`, not a comb (see Evidence): needs the lead's word or a raster reader
- [ ] DOCX of set 2: three stray drawn boxes on page 2 (two beside the date combs, one beside a hint) become `box` candidates; sub-headings 2.1-2.4 are not sections there (8 sections, the PDF gives 12)
- [ ] set 9 PDF: 0 sections (headings are neither numbered nor capitals; the PDF reader reports no bold there), DOCX gives 24
- [ ] sets 8 and 9: 17-31 `LABEL_NOT_FOUND` per file, not looked at one by one yet (compare with the silver notes)
- [ ] widgets: one candidate per widget, radio buttons of one field are not grouped yet; no set has widgets
- [ ] tab leaders the source declares (`Run.leader`) are read as leaders; no reader fills them yet, so only the rule exists (no test on a real file)
- [ ] `SILENT_PAGE` and `FILLED_FORM` are not raised here (F15, F17)

## Decisions
- Lines, not runs, are the unit of every rule; a line maps each character back to (run, start, end) / the PDF reader cuts "❑ p" + "ies" at a font change and a DOCX paragraph is one run / rules out rules that look at one run alone.
- A run shared by a place and plain words (dots and "ul. Browarna 85" after a tab) is named in `roles` with the role of the rest / `roles` is keyed by whole runs and `count_coverage` then counts it assigned / rules out "exactly one owner" for such a run (request 1).
- A caption in brackets or slashes directly under a leader is its label, reported as `how: "leader"` / `LabelHow` has no "below" / rules out telling it from words on the same line (request 2).
- A crossed or ticked box is a box like any other; only an instruction makes it an example: a line with an instruction word whose boxes are all ticked, a drawn box in the row of such a line, or any place under a heading "Instrukcja / Pouczenie / Objaśnienia" / the cheapest test wants the crossed box in the group, the negative control wants no group / rules out "ink inside means example".
- Boxes join a group on one row always, down a column only when left-aligned, near (2.5 line heights) and with no ruled line strictly between them / set 7 prints "pies | suka" in two table cells and the next question one row lower / rules out grouping across a row border.
- Comb: three or more equal boxes in a row, gaps up to 1.6 cell widths; one or two characters printed in a gap are the mask, more is a label and ends the row; a pattern such as "DD-MM-RRRR" next to it replaces the mask when its shape matches / design 6.3.3 / rules out one field per box and "Nr domu [ ] Nr lokalu [ ]" as a comb.
- The clause is a mode: it starts at its title words and lasts until a heading without clause vocabulary or a line that is only a leader / the clause yields no candidate / rules out a place inside a clause sentence (dots after "tel." there are not read).
- Headings: bold start with a number or letter, or capitals (bold: 6 letters; not bold: two words and 10 letters); a lone bold letter left of a heading is its number / testable without font statistics / rules out a plain bold line and a one-word capital label ("NAZWISKO") as headings.
- The first place under a heading that has no text of its own takes the heading as label with `how: "header"`, no runs, label confidence 0.5 / "4. Uzasadnienie wniosku" over a big empty box / rules out a warning there and double ownership of the heading run.
- Label score: same line 0.9; left 0.9 - distance/800 (-0.1 across a ruled line, never across another place); caption under 0.85; above 0.7 - distance/100 (-0.45 across a ruled line); margin under 0.05 adds `LOW_CONFIDENCE`; no text reaching 0.3 means no label and `LABEL_NOT_FOUND`.
- Reading order: columns need a gutter of 18 pt with two items on both sides, blocks a band of 14 pt, then rows left to right; a flow page (any run without a box) keeps the file's order / drills 3 and 4 / rules out mixing geometry and file order on one page.
- A table of empty cells only is a comb per row of three or more; an empty cell under a header row takes the header (`how: "header"`), else the text of the cell on its left; a first table on the next page with the same number of columns and no header row of its own continues the table: same headers, same section / drill 10 / the model cannot say "one repeating table" (request 3).
- `find` never raises: a failing rule gives `UNREADABLE_PART` and no candidates; `strict` lets the exception through (tests, survey).

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| unit tests on synthetic papers | `bash tools/gate.sh py -m pytest apps/converter/tests/find -q` | 30 passed (23 synthetic, 7 on the sets) | core commit |
| reference 1: four blanks with labels, PDF and DOCX | `test_reference_1_has_the_four_blanks...` | pass: w miejscowości, przy ulicy (footnote 1), nr ewidencyjny działki, w obrębie; page 2 (clause) no candidate | core commit |
| set 2: postal code, both dates one comb each | `test_set_2_postal_codes_and_dates_are_one_comb_each` | pass: NIP 10; Kod pocztowy 5 `__-___` twice; two dates 8 `DD-MM-RRRR` | core commit |
| set 2: the account one comb | scratch dump of the page model | NOT MET: the PDF draws the account as one box of 352 x 21 pt from four segments, no dividers in vectors; reported as `cell` "Nr rachunku" | core commit |
| set 7: groups, blanks, section A first | `test_set_7_groups_blanks_and_the_applicant_section_first` | pass: [pies, suka]; [mikroprocesor, tatuaż, brak] with blanks on the first two; sections A then B | core commit |
| set 9: the square character is a box | `test_set_9_the_square_character_counts_as_a_box` | pass, PDF and DOCX: 12 boxes, 3 groups | core commit |
| candidates per kind for the nine sets | `bash tools/gate.sh py -m app.find.survey --check` | exit 0: 17 files (9 PDF, 8 DOCX; set 7 has no DOCX), found 17, unhandled 0, unassigned runs 0 in every file; top-level places 9 to 89 per file, 0.01 to 1.05 s per file; `LABEL_NOT_FOUND` 0 in 6 files, 2 to 4 in 7 files, 20 to 31 in the four files of sets 8 and 9 | c591299 |
| fast gate after merging `main` | `bash tools/gate.sh fast` | 519 passed, 15 deselected | 7e54a49 |
| negative: information sheet | `test_an_information_sheet_has_no_candidates_and_says_not_a_form` | pass | core commit |
| negative: instruction with a ticked example | `test_an_instruction_with_ticked_example_boxes_is_not_a_group`; on set 2 `...instruction_example_boxes_are_not_candidates` | pass | core commit |
| negative: clause | `test_the_data_protection_clause_yields_no_candidate...`; on reference 1 and set 7 page 2 | pass | core commit |
| cheapest test | `test_empty_box_bullet_crossed_box_and_eleven_cells_are_one_group_and_one_field` | pass | core commit |
| drills 3, 4, 7, 8, 10 | `test_drill_3...`, `test_drill_4...`, `test_drill_7...`, `test_eleven_boxes...`, `test_drill_10...` | pass | core commit |

## Negative control
Break-and-restore on c591299: the comb rule in `_shapes.combs` was changed to need 300 boxes in a row instead of 3.
`bash tools/gate.sh py -m pytest apps/converter/tests/find/test_find_core.py -q` then gave 4 failed, 19 passed
(`test_eleven_boxes_are_one_value...`, `test_a_date_comb_takes_the_pattern...`, `test_empty_box_bullet_crossed_box...`,
`test_drill_3_two_columns...`). The line was restored (`git diff -- apps/converter/app/find` empty) and the fast gate
passed. The negative controls of the acceptance list are tests of their own (see Evidence).

## Acceptance stage (commit e9ea955, main already merged)
- `bash tools/gate.sh fast`: 519 passed, 15 deselected, 69 s, "gate: fast PASSED on e9ea955".
- `bash tools/gate.sh py -m pytest apps/converter/tests/find -q`: 30 passed.
- `bash tools/gate.sh py -m app.find.survey --check`: 17 files, found 17.
- Negative control repeated: `_shapes.py` line 134 `>= 3` -> `>= 300`: 4 failed, 19 passed (test_find_core.py); restored, 30 passed.
- Open items of Status stay open (set 2 account, set 9 PDF headings, label gaps on sets 8/9, radio grouping); see Requests.

## Requests to lead
1. Model (WP-F0): a role for a part of a run. Today a run shared by a place and plain words is named in `roles` as a whole and also carries spans; `FinderOutput.roles` could accept spans, or the rule "exactly one owner" could say "per character".
2. Model (WP-F0): `LabelHow` value `"below"` for a caption under a line ("(imię i nazwisko)" under dots); reported as `"leader"` until then.
3. Model (WP-F0): a way to say that cell candidates are rows of one repeating table (`Candidate.table` and `row`, or a `repeat` group); today they only share labels and section, and no warning code says "multiplicity".
4. Readers (WP-F2): a table of a flow page has the anchor `tbl[0]` and no place among the paragraphs, so the finder cannot label it from the paragraph before it (reference 5 DOCX: the 26-cell comb has no label). An anchor such as `p[33]+tbl[0]` or the index of the paragraph before would do.
5. Readers (WP-F2a): bold is not reported for the headings of set 9 in the PDF (the DOCX has it); drawn example pictures aside, the DOCX of set 2 gives small rectangles beside the date combs that are not on the PDF.
6. Lead: the acceptance line "the account is one comb" cannot hold for the PDF of set 2 from vectors (one box, no dividers). Either the wording changes to "one field", or the dividers come from a raster pass (WP-F2c).

7. Lead: wire `from app.find import find` into `app/pipeline.py` (never raises; `strict` for tests). Open items in Status (set 2 account, set 9 PDF headings, LABEL_NOT_FOUND on sets 8 and 9, radio grouping) were not touched in this stage.

## Cost notes
- core: most turns went to reading the page models of the sets before designing (one dump script, read once) and to two rounds of fixes after the first run on the sets; a ready dump of the nine page models as text, made by the readers' survey, would save three turns.
- acceptance: 6 replies, nothing failed; the survey rewrites eval/finder-sets.json with new timings on each run and dirties the tree (a non-writing --check would save a step).
- integration: 3 replies; the wiring is outside owned paths, so only the merge and gate were done.
