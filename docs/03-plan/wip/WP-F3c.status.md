# WP-F3c Matter quality round 2 (choice groups, attachments, no fragments): status

Branch: wp/F3c-matter-quality-2   Stage now: core (probe, items 1 to 5)

Owned: `apps/converter/app/find/**`, `app/mean/**`, `app/lexicon/**`, `app/compose/**`, their tests, `eval/probe/**`.
Probe: `bash tools/gate.sh py eval/probe/matter.py [--labels <scratch dir>] [--tickets <audit ticket file>]` (counts only;
labels go to a folder outside the repository for a before/after diff).

## Status
- [x] step 0: probe `eval/probe/matter.py`; before table below
- [x] item 1 (T1 choice groups): strike-out alternatives over runs of one printed line; "A/B* lub C/D*" pair; one box beside "Oświadczam" = optional CHECKBOX; a "Xxx:" line between options splits a group; a labelled group under the applicant heading whose options are not applicant kinds is matter. 9 synthetic tests (5 negative) in `tests/mean/test_mean_f3c.py`; find/mean/compose/pipeline 177 passed
- [ ] item 2 (T2 attachments)
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
- Lead additions (17:50): "właściwe zaznaczyć" is already exclusive wording, ☐ □ and drawn rectangles are already marks of the finder; ■ (filled) is not added: it reads as a ticked example (negative control of the card). "kopia" ("w załączeniu kopia ...") is taken in item 2. Sets 4 and 7: before/after rows are reported explicitly.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|

## Negative control

## Requests to lead

## Cost notes
