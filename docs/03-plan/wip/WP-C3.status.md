# WP-C3 the DOCX reader gives the list numbers and bullets the paper shows: status
Claimed by: build7 (agent c3-docx); heartbeat: 2026-11-22 01:10; state: running

Branch: wp/C3-docx-numbering   Stage now: core

## Status
- [x] (a) status file
- [x] (b) counts before (sets 03, 04, 06 DOCX via pipeline.run; scratch script tmp/c3_counts.py, not committed), on 8314f43:
  - 03 DOCX: CONSENT_SECTION 1, FILE_UPLOADER 4, RADIO 3, SELECT 4, TEXT_BLOCK 3, TEXT_FIELD 24, SECTION 14
  - 04 DOCX: CONSENT_SECTION 2, DATEPICKER 2, FILE_UPLOADER 4, NUMBER 1, RADIO 3, SELECT 4, TEXT_BLOCK 2, TEXT_FIELD 24, SECTION 15
  - 06 DOCX: CONSENT_SECTION 1, DATEPICKER 2, FILE_UPLOADER 6, NUMBER 5, RADIO 4, REPEATING_SECTION 1, SELECT 6, TEXT_BLOCK 4, TEXT_FIELD 39, SECTION 19
  - (no CHECKBOX in any; scratch script: walk the form, Counter of every dict "type")
- [x] (c) marker function `_Numbering` in app/readers/docx.py (markers precomputed for all body paragraphs in document order, VML fallback copies skipped) + 8 unit tests in apps/converter/tests/readers/test_docx_numbering.py: 8 passed
- [x] (d) wiring (`_Reader.para` prefixes `marker + " "`; `read()` parses word/numbering.xml); Symbol PUA option marks of the finder (U+F0F0 etc., set 03) as bullets -> "□". Counts after:
  - 03 DOCX: **CHECKBOX 0 -> 1** (the five Symbol-U+F0F0 bulleted options), SHOW 20 -> 21; rest equal
  - 04 DOCX: unchanged (markers "1)".."4)" and "1.","2." are produced, but the finder/mean do not make consents of them: see Requests to lead)
  - 06 DOCX: **FILE_UPLOADER 6 -> 11, RADIO 4 -> 5**, MAIN 4 -> 5, SECTION 19 -> 21, SHOW 31 -> 33 (the six "-" bulleted attachments)
  - markers found (tmp/c3_markers.py): 03: 5 bullets + 3 numbers; 04: 6 numbers; 06: 6 dashes
- [ ] (e) readers tests + fast gate
- [ ] (f) eval.chain --compare, WORSE lines explained, state ready_to_merge

## Decisions
- Counters per numId (as the brief says), not per abstractNum / simple and deterministic / Word's sharing of counters between nums of one abstract is not reproduced.
- Box bullets -> "□" (BOX_CHARS[0] of the finder); dash bullets -> "-"; every other bullet (Symbol U+F0B7, Courier "o", Wingdings small square) -> "•" (both find.BULLET and mean._doc.BULLET strip it).
- Marker and text are joined by one space (not the w:suff tab: a tab can be read as a blank by later steps).

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| unit tests | `bash tools/gate.sh py -m pytest apps/converter/tests/readers/test_docx_numbering.py -q` | 8 passed | step (c) commit |

## Negative control
Replaced `out.text = f"{marker} {text}" if marker else text` by `out.text = text` in `_Reader.para`: test_docx_numbering.py 7 failed, 1 passed (the no-numbering test); restored: 8 passed.

## Left for the next stage
(e), (f). Next commands (in the worktree):
- `bash tools/gate.sh py tmp/c3_counts.py` (scratch, not committed: for judged sets 03, 04, 06 DOCX found through tools/coi_paths.py, run pipeline.run with Settings.from_env({}), print Counter of every dict "type" in the form; recreate if missing)
- `bash tools/gate.sh py -m pytest apps/converter/tests/readers -q`
- `bash tools/gate.sh fast > tmp/fast.log 2>&1`
- `bash tools/gate.sh py -m eval.chain --compare --archive C:/dev/shramko-asystent-urzednika/data/archive > tmp/chain.log 2>&1`; then `git checkout eval/chain/summary.json`

## Requests to lead
- Set 04 DOCX: the four consents are now read as "1) zapoznałem/am się ...", "2) ...", "3) ...", "4) ..." but no consent appears. Probable cause (not verified): `NOTE = re.compile(r"^/?\s*(?:\d{1,2}\s?\)|\*{1,3}\)?)\s*\S")` in app/find/_core.py takes a line starting "1) " as a footnote; and no rule turns a numbered list of first-person declarations into consents. Needs an owner of app/find or app/mean.

## Cost notes
