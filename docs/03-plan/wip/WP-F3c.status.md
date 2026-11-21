# WP-F3c Matter quality round 2 (choice groups, attachments, no fragments): status

Branch: wp/F3c-matter-quality-2   Stage now: core (probe, items 1 to 5)

Owned: `apps/converter/app/find/**`, `app/mean/**`, `app/lexicon/**`, `app/compose/**`, their tests, `eval/probe/**`.
Probe: `bash tools/gate.sh py eval/probe/matter.py [--labels <scratch dir>] [--tickets <audit ticket file>]` (counts only;
labels go to a folder outside the repository for a before/after diff).

## Status
- [x] step 0: probe `eval/probe/matter.py`; before table below
- [x] item 1 (T1 choice groups): strike-out alternatives over runs of one printed line; "A/B* lub C/D*" pair; one box beside "Oświadczam" = optional CHECKBOX; a "Xxx:" line between options splits a group; a labelled group under the applicant heading whose options are not applicant kinds is matter. 9 synthetic tests (5 negative) in `tests/mean/test_mean_f3c.py`; find/mean/compose/pipeline 177 passed
- [x] item 2 (T2 attachments): list under "Załączniki ...:" (dash or numbered items, wrapped lines joined by indent), sentences "należy / można dołączyć | załączyć X", "w załączeniu X", "X załączyć do wniosku"; rows "N. X TAK NIE"; either-or pair = RADIO + two SHOW; covers by the standard pages (new lexicon row "dokumenty upoważniające"). 3 synthetic tests (1 negative: annex line of a regulation, bare heading); find/mean/compose/pipeline 180 passed. Uploaders of the matter, PDF: set 4 0 -> 1, set 6 0 -> 5 (+1 RADIO of the pair), set 7 0 -> 1, set 8 1 -> 3, set 9 0 -> 4. Not done: set 6 DOCX (list items carry no printed dash: Word numbering), attachments of set 9 are asked once, not per variant
- [ ] item 3 (T3 no field without an input cue)
- [ ] item 5 (T5 labels, T9 types)
- [ ] item 4 (T4 caption under a blank)
- [ ] items 6 and 7 (T7, T6): only if replies remain

## Probe (counts only; RADIO/CHECKBOX: count [options per field]; upl = uploaders of the matter; req = REQUIRED of the matter; low = labels whose printed words (evidence quote) start lower-case; <4 = labels with fewer than four letters)

Before (main de4acbe, after F3b) -> after item 1:

| set | fmt | fields | RADIO | CHECKBOX | upl | req | low | <4 | lint |
|---|---|---|---|---|---|---|---|---|---|
| 02 | docx | 5 | 2 [2, 2] | 0 | 0 | 5 | 0 | 0 | 0 |
| 02 | pdf | 5 | 1 [2] | 0 | 0 | 5 | 0 | 0 | 0 |
| 03 | docx | 2 | 0 | 0 | 0 | 2 | 1 | 0 | 0 |
| 03 | pdf | 3 | 0 | 1 [5] | 0 | 2 | 1 | 0 | 0 |
| 04 | docx | 6 | 0 | 0 | 0 | 6 | 3 | 0 | 0 |
| 04 | pdf | 7 | 1 [2] | 0 | 0 | 7 | 4 | 0 | 0 |
| 06 | docx | 16 | 0 | 0 | 0 | 16 | 12 | 2 | 0 |
| 06 | pdf | 18 | 0 | 0 | 0 | 18 | 13 | 3 | 0 |
| 07 | pdf | 10 -> 12 | 2 [2, 3] -> 4 [2, 2, 2, 3] | 0 | 0 | 8 -> 10 | 2 -> 4 | 0 | 0 |
| 08 | docx | 27 -> 28 | 7 [2 x7] | 1 [5] -> 2 [5, 0] | 1 | 27 | 17 | 0 | 0 |
| 08 | pdf | 38 -> 39 | 2 [2, 2] | 1 [4] -> 2 [4, 0] | 1 | 38 | 17 | 0 | 0 |
| 09 | docx | 42 -> 43 | 1 [3] -> 2 [3, 2] | 0 | 0 | 42 | 2 | 0 | 0 |
| 09 | pdf | 58 -> 61 | 2 [3, 2] -> 4 [3, 2, 2, 2] | 0 -> 1 [3] | 0 | 57 -> 60 | 14 -> 15 | 0 | 0 |

Label diff after item 1 (scratch, by type/label): sets 2, 3, 4, 6 unchanged; set 7 PDF only two RADIO added; set 8 only the
declaration CHECKBOX added (DOCX label has words glued by the reader); set 9 DOCX the "other address" text field became the
option blank of the new RADIO; set 9 PDF the 22-option SELECT became a CHECKBOX of 3 kinds and a SELECT of 20 disciplines,
plus the applicant RADIO of two options. ("[x, 0]": a CHECKBOX of one box; the composer writes the option "Tak".)

Ticket keys of T3 to T5 still present in the seven PDF forms: 12 of 12.

## Decisions
- Probe counts the brief (matter sections, attachments without `covered_by`) and lints the composed form / the brief is what the finder and the understanding step decide / rules out counting the standard pages and the fee uploader (T11, not this package).
- Strike-out alternatives are read on printed lines (runs on one baseline joined; flow runs alone), and "A/B* lub C/D*" (window of two lines) is one RADIO of the two phrases / a PDF writes the star as a run of its own (set 7) / rules out a choice without the paper's strike-out note.
- One box beside a sentence that starts "Oświadczam" is an optional CHECKBOX labelled with the whole sentence (lines printed right under it joined until "."); any other single box still waits / the paper asks it of some filers only / rules out a REQUIRED tick and a guessed yes-or-no label.
- A free body line of at most six words ending in ":" between options of one group splits it, each part with at least two options / set 9 prints kinds and disciplines as one column of boxes / rules out a split on a sentence or a one-option part.
- A labelled choice group under the applicant heading stays in the matter unless every option is an applicant kind of the lexicon ("wording" table); an unlabelled group keeps the old route / rules out "Prezydent / Klub" being swallowed by the standard pages, and a matter group titled only by the bare heading.
- Attachments in running text: label = the item up to its condition (", jeżeli / jeśli / w przypadku / gdy"), cut at the first ", " or " (" past 90 characters; optional on "można", "ewentualn", "opcjonaln" or a condition; a sentence continues only into lines that start lower-case / the paper names items in prose / rules out an upload from a heading alone or from "Załącznik nr N do ..." (needs "Załączniki ...:" with a colon or a verb of attaching).
- Either-or pair: an item whose condition holds "nie" and shares two word stems with another item's label / set 6 traffic project vs safety information / rules out pairing items that merely both have conditions.
- Lead additions (17:50): "właściwe zaznaczyć" is already exclusive wording, ☐ □ and drawn rectangles are already marks of the finder; ■ (filled) is not added: it reads as a ticked example (negative control of the card). "kopia" ("w załączeniu kopia ...") is taken in item 2. Sets 4 and 7: before/after rows are reported explicitly.

After item 2 (PDF; DOCX unchanged by item 2 except set 4 upl 0 -> 1 and set 9 upl 0 -> 4):

| set | fmt | fields | RADIO | CHECKBOX | upl | req | low | <4 | lint |
|---|---|---|---|---|---|---|---|---|---|
| 02 | pdf | 5 | 1 [2] | 0 | 0 | 5 | 0 | 0 | 0 |
| 03 | pdf | 3 | 0 | 1 [5] | 0 | 2 | 1 | 0 | 0 |
| 04 | pdf | 7 | 1 [2] | 0 | 1 | 7 | 4 | 0 | 0 |
| 06 | pdf | 19 | 1 [2] | 0 | 5 | 24 | 13 | 3 | 0 |
| 07 | pdf | 12 | 4 [2, 2, 2, 3] | 0 | 1 | 11 | 4 | 0 | 0 |
| 08 | pdf | 39 | 2 [2, 2] | 2 [4, 0] | 3 | 38 | 17 | 0 | 0 |
| 09 | pdf | 61 | 4 [3, 2, 2, 2] | 1 [3] | 4 | 62 | 15 | 0 | 0 |

Ticket keys of T3 to T5 still present: 12 of 12 (items 3 to 5 not started). Sets 4 and 7: label diff shows only additions
(set 4: one optional upload; set 7: two RADIO and one upload); no field of the matter and no label lost.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| synthetic tests items 1, 2 | `bash tools/gate.sh py -m pytest apps/converter/tests/mean/test_mean_f3c.py -q` | 12 passed (6 negative cases) | 31e2011 |
| find/mean/compose/pipeline incl. `sets` | `bash tools/gate.sh py -m pytest apps/converter/tests/find apps/converter/tests/mean apps/converter/tests/compose apps/converter/tests/pipeline -q -m "not slow"` | 180 passed, 1 skipped (local briefs absent) | 31e2011 |
| probe, 13 files | `bash tools/gate.sh py eval/probe/matter.py` | tables above; strict-lint errors 0 on all 13 | 31e2011 |
| fast gate | `bash tools/gate.sh fast` | 682 passed, 2 skipped, 22 deselected; chain tests 21 passed; "gate: fast PASSED on 31e2011" | 31e2011 |

## Negative control
The group split disabled (`if head and ...` -> `if False and head and ...` in `_split_group`): `test_a_line_ending_in_a_colon_between_options_splits_the_group_in_two` failed (1 failed, 11 passed); file restored with `git checkout --` -> 12 passed. Nothing committed in the broken state.

## Left for the next core stage (cases located on the PDFs with `dump` of reading order; no form text here)
- item 3 (T3): set 6 two short tails ("Mui", "Tj") are words after a blank inside a sentence; set 8 two section headings became fields of their own (a `cell` candidate whose label is the section heading: c58, c59 kind) and a printed rate cell became a field; set 9 a consent sentence tail. Plan: a `cell` candidate labelled only by its section heading and a candidate whose label is a printed amount ("NN zł NN gr") are text, LEFT_OUT with a reason; a label of one or two letters after a blank in a sentence is MERGED into the field before it.
- item 5 (T5/T9): label that starts lower-case and whose run continues a body line right above (geometry, `_below` in reverse) gets that line prepended (set 9 disciplines lead-in, "Inna" + "dyscyplina", the club opinion); set 8 household counts need the row header with the bound; types: "DD-MM-RRRR" / "dnia" -> DATEPICKER, "liczba / ilość / dni" -> NUMBER (lexicon `concepts`).
- item 4 (T4): set 6 a caption in parentheses or slashes under a blank: merge into the blank above as its hint (extend `_hint_after` to "/.../" and to a caption that the finder made a candidate of its own).
- set 9 channel group (single box + unlabelled group of two inboxes) is still split; set 3 DOCX options still need the reader's list marker (F3b request 1); set 6 DOCX attachments list has no printed dash.

## Requests to lead

## Cost notes
- core (items 1, 2, about 50 replies): the worktree guard refuses any command line holding the word of the evaluation folder in some forms (`ls`, `sed`, `cd`) and every compound command; scratch Python scripts (`dump.py` reading order with roles, `cmp.py` label diff of two probe `--labels` folders) made each item one probe run plus one diff. Cheaper next time: commit both helpers under `eval/probe/` (they print form text, so only with output to a folder outside git).
