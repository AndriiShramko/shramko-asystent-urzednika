# WP-C3 the DOCX reader gives the list numbers and bullets the paper shows: status
Claimed by: build7 (agent c3-docx); heartbeat: 2026-11-22 00:45; state: running

Branch: wp/C3-docx-numbering   Stage now: core

## Status
- [x] (a) status file
- [ ] (b) counts before (sets 03, 04, 06 DOCX via pipeline.run; scratch script tmp/c3_counts.py, not committed)
- [ ] (c) marker function + unit tests (apps/converter/tests/readers/test_docx_numbering.py), negative control
- [ ] (d) wiring into paragraph reading, counts after
- [ ] (e) readers tests + fast gate
- [ ] (f) eval.chain --compare, WORSE lines explained, state ready_to_merge

## Decisions

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|

## Negative control

## Left for the next stage
All of (b) to (f). Next commands (in the worktree):
- `bash tools/gate.sh py tmp/c3_counts.py` (write it first: for sets 03, 04, 06 DOCX found through tools/coi_paths.py, run pipeline.run, print count of fields by type)
- `bash tools/gate.sh py -m pytest apps/converter/tests/readers -q`
- `bash tools/gate.sh fast > tmp/fast.log 2>&1`
- `bash tools/gate.sh py -m eval.chain --compare --archive C:/dev/shramko-asystent-urzednika/data/archive > tmp/chain.log 2>&1`; then `git checkout eval/chain/summary.json`

## Requests to lead

## Cost notes
