# WP-F-val validators and REQUIRED only where the paper says it: status

Branch: wp/F-val-validators   Stage now: 1 (B8, validators)

Worktree branch `worktree-agent-a93ecdbb74987c1c9`, cut from `main` c940d03. Lead's notes: push the package branch at
each stage end; `eval.chain` in a worktree needs `--archive C:/dev/shramko-asystent-urzednika/data/archive`, log to a
file; never commit `eval/chain/summary.json` or `last-run.jsonl`; never `--update-baseline`.

## Status
- [x] Stage 1: measuring script `apps/converter/tests/validators/count_sets.py`, counts before
- [ ] Stage 1: root cause and fix (library `numer_pesel`; concept rows for ePUAP, e-Doręczenia, identity card; label rule in compose)
- [ ] Stage 1: one test per validator, negative control, counts after, fast gate, push
- [ ] Stage 2: REQUIRED measured per set (paper against inferred), rule decided or note for the lead
- [ ] Stage 2: tests, counts after, every changed field named, fast gate, push

## Decisions

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|

### Stage 1, before (main c940d03; one input per judged set, the PDF, as `tools/lead/snapshot_results.py` picks)
Command: `bash tools/gate.sh py apps/converter/tests/validators/count_sets.py OUT.json`

| set | inputs | REQUIRED | PESEL | NIP | REGON | ZIP_CODE | EMAIL | EPUAP | ADE | SERIAL_NUMBER_ID_CARD | REQUIRED paper/inferred |
|---|---|---|---|---|---|---|---|---|---|---|---|
| judged-02 | 50 | 5 | 0 | 1 | 0 | 3 | 1 | 0 | 0 | 0 | 0/5 |
| judged-03 | 36 | 2 | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 0/2 |
| judged-04 | 39 | 7 | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 1/6 |
| judged-06 | 69 | 23 | 0 | 1 | 0 | 3 | 1 | 0 | 0 | 0 | 6/17 |
| judged-07 | 45 | 11 | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 3/8 |
| judged-08 | 87 | 36 | 0 | 1 | 0 | 5 | 2 | 0 | 0 | 0 | 0/36 |
| judged-09 | 111 | 62 | 0 | 1 | 0 | 3 | 1 | 0 | 0 | 0 | 3/59 |

Fields that state an identifier and carry no validator, before (all readable files of all sets): `numer_pesel` of
"Twoje dane" (sets 03, 08, reference 05; standard, read-only); in set 09 the paper's "Skrzynka ePUAP - adres skrzynki",
"eDoręczenia - adres skrzynki", "Seria i numer dowodu osobistego" (up to three copies each).

## Negative control

## Requests to lead

## Cost notes
