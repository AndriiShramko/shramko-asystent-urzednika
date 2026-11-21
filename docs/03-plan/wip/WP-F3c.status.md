# WP-F3c Matter quality round 2 (choice groups, attachments, no fragments): status

Branch: wp/F3c-matter-quality-2   Stage now: acceptance done (items 1 to 5); items 6, 7 not started

Owned: `apps/converter/app/find/**`, `app/mean/**`, `app/lexicon/**`, `app/compose/**`, their tests, `eval/probe/**`.
Probe: `bash tools/gate.sh py eval/probe/matter.py [--labels <scratch dir>] [--tickets <audit ticket file>]` (counts only;
labels go to a folder outside the repository for a before/after diff).

## Status
- [x] step 0: probe `eval/probe/matter.py`; before table below
- [x] item 1 (T1 choice groups): strike-out alternatives over runs of one printed line; "A/B* lub C/D*" pair; one box beside "Oświadczam" = optional CHECKBOX; a "Xxx:" line between options splits a group; a labelled group under the applicant heading whose options are not applicant kinds is matter. 9 synthetic tests (5 negative) in `tests/mean/test_mean_f3c.py`; find/mean/compose/pipeline 177 passed
- [x] item 2 (T2 attachments): list under "Załączniki ...:" (dash or numbered items, wrapped lines joined by indent), sentences "należy / można dołączyć | załączyć X", "w załączeniu X", "X załączyć do wniosku"; rows "N. X TAK NIE"; either-or pair = RADIO + two SHOW; covers by the standard pages (new lexicon row "dokumenty upoważniające"). 3 synthetic tests (1 negative: annex line of a regulation, bare heading); find/mean/compose/pipeline 180 passed. Uploaders of the matter, PDF: set 4 0 -> 1, set 6 0 -> 5 (+1 RADIO of the pair), set 7 0 -> 1, set 8 1 -> 3, set 9 0 -> 4. Not done: set 6 DOCX (list items carry no printed dash: Word numbering), attachments of set 9 are asked once, not per variant
- [x] item 3 (T3 no field without an input cue): printed amount, heading strip, last line of a sentence, stub label; 8 synthetic tests (4 negative)
- [x] item 5 (T5 labels, T9 types): lower-case label takes the body line above (and a numbered heading above wrapped lines); DD-MM-RRRR / "dnia" -> DATEPICKER, "dni" -> NUMBER; 4 tests (3 negative)
- [x] item 4 (T4 caption under a blank): caption in slashes or brackets on a second dotted line is the hint of the blank above, `_hint_after` takes "/.../"; 3 tests (1 negative group)
- [ ] items 6 and 7 (T7, T6): not started (second core stage or F3d)
- [x] acceptance stage: probe before/after, sets tests, fast gate, chain compare, negative control (Evidence)

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
Ticket keys of T3 to T5 still present in the seven PDF forms after items 3 to 5 (probe `--tickets`, 18:45, head a0d3190): 3 of 12 (was 12 of 12). The three left are not named by the probe; to be named when items 6 and 7 are planned.

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

- Item 3 (all in `mean/_fields.py`, finder untouched): a `cell` whose only label is its section heading, one line high and flush (gap <= 3 pt) under that heading is the heading's edge, LEFT_OUT `EXPLANATION` / a drawn band of set 8 became fields / rules out dropping a box with room under a heading (test). A label that is a printed amount ("15 zł 00 gr") is LEFT_OUT `EXPLANATION` / set 8 rate cell / rules out "Stawka 15 zł".
- The last line of a sentence is no label: label of >= 4 words ending "." while the line above does not end a sentence (>= 5 words or ends on a preposition / conjunction, no full stop) and the blank is not a line block; the caption printed under the blank (<= 5 words, no full stop) becomes the label, else the place waits / set 9 consent date lines labelled by the sentence tail / rules out a short complete caption ("Dane osoby ... ." of four words) and a line block (its question may end in a full stop).
- A stub of fewer than four letters that is no known phrase, concept or abbreviation takes the caption under the blank, or "Liczba <unit>" when the text after the blank starts with "dni / miesięcy / lat / godzin / sztuk" (also inside the same run: a flow file); without either it stays as it was / set 6 "Mui", "tj." / rules out dropping a one-word label such as "Cel". New phrases "zam", "zam." -> "Adres zamieszkania" (was "Zam").
- Item 5: a label that starts lower-case takes the line printed right above (geometry: nearest above that covers the left edge up to a 45 pt indent; flow: previous run), up to three lines, only when that line says its sentence goes on (>= 5 words or ends on a function word, no full stop) / sets 6, 8, 9 / rules out a title, a line in capitals, a heading (except a numbered heading above already stitched wrapped lines: "36. Liczba ... zajmujących" + row header + bound), a caption printed under a blank, and a short line ("Dane wnioskodawcy"). The evidence quote is the whole stitched text. Not done: "Inna" + "dyscyplina" (one capitalised word is not a sentence that goes on).
- Types: lexicon `concepts` rows "DD-MM-RRRR" or label ending "dnia" -> DATEPICKER, label ending "dni" -> NUMBER; the bracket hint of a label is tried for DATEPICKER rows / rules out typing from "dni" inside a longer label.
- Item 4: a second dotted line labelled only by a caption in brackets or slashes under it (label how "leader", single run, adjacent to the blank above) is MERGED into the blank above (LINE_BLOCK), whose field becomes a TEXTAREA with the caption as hint; `_hint_after` accepts "/ ... /" / set 6 "w celu wykonania" + "rodzaj robót" / rules out a caption without brackets and a caption of a blank that has its own label.

After items 3, 5, 4 (probe, PDF and DOCX as before; fields of sets 2, 3, 4, 7 and their labels are identical to the table above, label diff of those seven files: 0 lines):

| set | fmt | fields | RADIO | CHECKBOX | upl | req | low | <4 | lint |
|---|---|---|---|---|---|---|---|---|---|
| 02 | pdf | 5 | 1 [2] | 0 | 0 | 5 | 0 | 0 | 0 |
| 03 | pdf | 3 | 0 | 1 [5] | 0 | 2 | 1 | 0 | 0 |
| 04 | pdf | 7 | 1 [2] | 0 | 1 | 7 | 4 | 0 | 0 |
| 06 | pdf | 19 -> 18 | 1 [2] | 0 | 5 | 24 -> 23 | 13 | 3 -> 0 | 0 |
| 07 | pdf | 12 | 4 [2, 2, 2, 3] | 0 | 1 | 11 | 4 | 0 | 0 |
| 08 | pdf | 39 -> 37 | 2 [2, 2] | 2 [4, 0] | 3 | 38 -> 36 | 17 -> 6 | 0 | 0 |
| 09 | pdf | 61 | 4 [3, 2, 2, 2] | 1 [3] | 4 | 62 | 15 -> 7 | 0 | 0 |

DOCX: 06 16 fields (unchanged), low 12, <4 2 -> 0; 08 28 -> 25 fields, low 17 -> 8; 09 43, low 2.
Removed fragments (count): set 6 PDF one field merged (caption line); set 8 PDF two (heading strips, c58 c59) plus the rate cell and the "Inne załączniki" now comes from the open line "Inne: (podać jakie)" instead of a heading strip; set 8 DOCX three (two headings, rate). Label diff of set 8: the ten count cells now read "Liczba gospodarstw domowych ... <bound>" with type NUMBER (were the bare bound, TEXT_FIELD); set 9 PDF: lower-case fragments (low 15 -> 7) now carry their question, the consent sentence tails became "Data" (DATEPICKER) or "Data sporządzenia wniosku". Nothing of sets 2, 3, 4, 7 changed.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| synthetic tests items 1, 2 | `bash tools/gate.sh py -m pytest apps/converter/tests/mean/test_mean_f3c.py -q` | 12 passed (6 negative cases) | 31e2011 |
| find/mean/compose/pipeline incl. `sets` | `bash tools/gate.sh py -m pytest apps/converter/tests/find apps/converter/tests/mean apps/converter/tests/compose apps/converter/tests/pipeline -q -m "not slow"` | 180 passed, 1 skipped (local briefs absent) | 31e2011 |
| probe, 13 files | `bash tools/gate.sh py eval/probe/matter.py` | tables above; strict-lint errors 0 on all 13 | 31e2011 |
| fast gate | `bash tools/gate.sh fast` | 682 passed, 2 skipped, 22 deselected; chain tests 21 passed; "gate: fast PASSED on 31e2011" | 31e2011 |
| synthetic tests items 1 to 5 | `bash tools/gate.sh py -m pytest apps/converter/tests/mean/test_mean_f3c.py -q` | 26 passed (11 negative cases) | items 3, 5, 4 commit |
| find/mean/compose/pipeline | same selection as above | 194 passed, 1 skipped | items 3, 5, 4 commit |
| probe, 13 files | `bash tools/gate.sh py eval/probe/matter.py --labels <scratch>` | table "After items 3, 5, 4"; 0 strict-lint errors on all 13; sets 2, 3, 4, 7 label diff 0 lines | items 3, 5, 4 commit |
| fast gate | `bash tools/gate.sh fast` | 696 passed, 2 skipped, 22 deselected; chain tests 21 passed; PASSED | items 3, 5, 4 commit (run on the working tree before the commit) |
| acceptance: sets tests | `bash tools/gate.sh py -m pytest apps/converter/tests -q -m sets` | 125 passed, 1 skipped (local briefs absent) | merge 7ab5ae3 |
| acceptance: probe before (aa8b0be) and after (a0d3190) | `bash tools/gate.sh py eval/probe/matter.py` in two worktrees | table below (13 files, lint 0 on all) | aa8b0be, a0d3190 |
| acceptance: fast gate after merging main | `bash tools/gate.sh fast` | 696 passed, 2 skipped, 22 deselected; chain tests 21 passed; PASSED | 7ab5ae3 |
| acceptance: chain compare | `bash tools/gate.sh py -m eval.chain --corpus sets,hostile --compare` (archive of unseen files absent here, so 80 baseline rows of "unseen" are notes) | 78 files: 72 converted, 6 refused (hostile), 0 failed; gate failures 0; strict-lint errors 0; compare 1 worse (non-fatal), 15 better; exit 0 | 7ab5ae3 |

Acceptance probe table, aa8b0be (before this stage) -> a0d3190 (after items 3, 5, 4); rows not shown are identical:

| set | fmt | fields | RADIO | CHECKBOX | upl | req | low | <4 |
|---|---|---|---|---|---|---|---|---|
| 06 | docx | 16 | 0 | 0 | 0 | 16 | 12 | 2 -> 0 |
| 06 | pdf | 19 -> 18 | 1 [2] | 0 | 5 | 24 -> 23 | 13 | 3 -> 0 |
| 08 | docx | 28 -> 25 | 7 x [2] | 2 [5, 0] | 1 | 27 -> 24 | 17 -> 8 | 0 |
| 08 | pdf | 39 -> 37 | 2 [2, 2] | 2 [4, 0] | 3 | 38 -> 36 | 17 -> 6 | 0 |
| 09 | pdf | 61 | 4 [3, 2, 2, 2] | 1 [3] | 4 | 62 | 15 -> 7 | 0 |

Chain: the only "worse" row is set 8 DOCX, 80 -> 78 fields of the whole form, which are the removed fragments counted above (two section headings and a rate cell; one count cell is gained elsewhere). Fifteen sets rows gain fields (+1 to +7). No regression in outcome, gate or lint.
Acceptance negative control: `_AMOUNT` check in `mean/_fields.py` line 143 switched off (`if False and label and ...`): `test_a_printed_rate_is_text_of_the_form_not_a_field` failed (1 failed, 25 passed); restored with `git checkout --` -> 26 passed. Nothing committed broken.

## Negative control
Items 3, 5, 4: the lead-in switched off (`if False and text[:1].islower()` in `_clarify`): the two lead-in tests failed (2 failed, 24 passed); line restored -> 26 passed. Nothing committed in the broken state. Item 1 control below.

The group split disabled (`if head and ...` -> `if False and head and ...` in `_split_group`): `test_a_line_ending_in_a_colon_between_options_splits_the_group_in_two` failed (1 failed, 11 passed); file restored with `git checkout --` -> 12 passed. Nothing committed in the broken state.

## Left for the next core stage (cases located on the PDFs; no form text here)
Done in core stage 2: items 3, 5, 4 (see Status). Not started: item 6 (T7 optional marks) and item 7 (T6 table cells). Open:
- set 9 channel group (single box + unlabelled group of two inboxes) is still split;
- set 3 DOCX options need the reader's list marker (F3b request 1);
- set 6 DOCX attachments list has no printed dash (Word numbering), so no uploader there;
- "Inna" + "dyscyplina" (one capitalised word is not a sentence that goes on); set 9 attachments are asked once, not per variant;
- no synthetic test is named for the "ticked box drawn in an instruction is not a group" control (the filled square is simply not a mark).

## Requests to lead

## Cost notes
- core (items 1, 2, about 50 replies): the worktree guard refuses any command line holding the word of the evaluation folder in some forms (`ls`, `sed`, `cd`) and every compound command; scratch Python scripts (`dump.py` reading order with roles, `cmp.py` label diff of two probe `--labels` folders) made each item one probe run plus one diff. Cheaper next time: commit both helpers under `eval/probe/` (they print form text, so only with output to a folder outside git).
- acceptance: the long runs (sets tests 3 min, fast gate 2.5 min) took the waiting turns; the chain needed `--corpus sets,hostile` because the archive of unseen files is absent here.

**Critic round (Eden, 19:5x, diff 24e14ec):** blocker "either-or from any nie" confirmed with a stub (old code made a RADIO from "plan organizacji ruchu nie przewiduje zamknięcia drogi"); fixed: `_NOT_REQUIRED` must name "nie jest wymagany / konieczny / potrzebny", "nie dotyczy" or "w przypadku braku"; test `test_a_negation_that_does_not_say_the_other_item_is_not_required_is_no_either_or`. Blocker "empty group crashes `_split_group`": reachable only with `options == []`, which the finder never creates (groups need a chain of two or more); guard added anyway; the variant with an option without runs returns one part and does not crash (stub run). Open (major, not changed): split groups share one candidate id; `_heading_edge` may drop a real one-line field under a heading.

**Critic round 2 (Eden, e909925):** confirmed by a probe and fixed: "X należy załączyć do wniosku" made an upload "Do wniosku" (old probe output: [("Do wniosku", True)]); a condition naming "pełnomocnictwo" covered an unrelated item (cover is now matched on the item, not its condition); "Nie można dołączyć X" made an optional upload (old probe: [("Kopii dowodu", False)]). Not confirmed: Gemini "ValueError in _split_group on out-of-order runs" (an empty range is not an error; no min/max of an empty list). Open: shared candidate id of split groups.
