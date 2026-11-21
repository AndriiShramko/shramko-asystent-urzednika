# WP-F3c Matter quality round 2 (choice groups, attachments, no fragments): status

Branch: wp/F3c-matter-quality-2   Stage now: core (probe, items 1 to 5)

Owned: `apps/converter/app/find/**`, `app/mean/**`, `app/lexicon/**`, `app/compose/**`, their tests, `eval/probe/**`.
Probe: `bash tools/gate.sh py eval/probe/matter.py [--labels <scratch dir>] [--tickets <audit ticket file>]` (counts only;
labels go to a folder outside the repository for a before/after diff).

## Status
- [x] step 0: probe `eval/probe/matter.py`; before table below
- [ ] item 1 (T1 choice groups)
- [ ] item 2 (T2 attachments)
- [ ] item 3 (T3 no field without an input cue)
- [ ] item 5 (T5 labels, T9 types)
- [ ] item 4 (T4 caption under a blank)
- [ ] items 6 and 7 (T7, T6): only if replies remain

## Probe (counts only; RADIO/CHECKBOX: count [options per field]; upl = uploaders of the matter; req = REQUIRED of the matter; low = labels starting lower-case; <4 = labels with fewer than four letters)

Before (main de4acbe, after F3b):

| set | fmt | fields | RADIO | CHECKBOX | upl | req | low | <4 | lint |
|---|---|---|---|---|---|---|---|---|---|
| 02 | docx | 5 | 2 [2, 2] | 0 | 0 | 5 | 0 | 0 | 0 |
| 02 | pdf | 5 | 1 [2] | 0 | 0 | 5 | 0 | 0 | 0 |
| 03 | docx | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| 03 | pdf | 3 | 0 | 1 [5] | 0 | 2 | 0 | 0 | 0 |
| 04 | docx | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| 04 | pdf | 7 | 1 [2] | 0 | 0 | 7 | 0 | 0 | 0 |
| 06 | docx | 16 | 0 | 0 | 0 | 16 | 0 | 2 | 0 |
| 06 | pdf | 18 | 0 | 0 | 0 | 18 | 0 | 3 | 0 |
| 07 | pdf | 10 | 2 [2, 3] | 0 | 0 | 8 | 0 | 0 | 0 |
| 08 | docx | 27 | 7 [2 x7] | 1 [5] | 1 | 27 | 0 | 0 | 0 |
| 08 | pdf | 38 | 2 [2, 2] | 1 [4] | 1 | 38 | 0 | 0 | 0 |
| 09 | docx | 42 | 1 [3] | 0 | 0 | 42 | 0 | 0 | 0 |
| 09 | pdf | 58 | 2 [3, 2] | 0 | 0 | 57 | 0 | 0 | 0 |

Ticket keys of T3 to T5 still present in the seven PDF forms: 12 of 12.

## Decisions
- Probe counts the brief (matter sections, attachments without `covered_by`) and lints the composed form / the brief is what the finder and the understanding step decide / rules out counting the standard pages and the fee uploader (T11, not this package).

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|

## Negative control

## Requests to lead

## Cost notes
