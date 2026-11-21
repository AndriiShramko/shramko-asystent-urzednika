# WP-F-d19 Gate warnings, warnings header, job timeout: status

Branch: wp/F-d19-gate-warnings   Stage now: done; next: lead reviews and merges

## Status
- [x] 1. Only G1 to G4 raise GATE_FAILED (500); a failed G5 to G12 becomes a warning `GATE_G<n>` (Polish, places only, no values) in the sidecar, response 200 (`pipeline.py`: `BLOCKING_CHECKS`, `_gate_warning`)
- [x] 2. `X-Converter-Warnings: <count>; CODE, CODE` (ASCII, deduplicated, 200 characters at most, `...` when cut) on convert and report, sent only when a warning exists (`main.py`)
- [x] 3. `job_timeout_s` applied: `pipeline.run_limited` runs `run` in a daemon thread, the caller waits `job_timeout_s`; on expiry problem `TIMEOUT` (504, already in the problem table: "Przekroczono czas przetwarzania"); used by convert, report and batch items (`run_one`)
- [x] Tests `apps/converter/tests/shell/test_d19.py` (9), fast gate green

## Decisions
- Timeout code: existing `TIMEOUT` = 504 (closest; no new code). A Python thread cannot be killed: on timeout the abandoned job finishes by itself in the background (daemon, does not block exit); the concurrency slot is released at once. A process-based limit would kill it but costs a fork of the models and a new copy of the input; not done.
- Blocking set is exactly G1 to G4 as ordered. Note: in code G3 is `grid` and G5 `condition_references` holds the "condition does not parse" finding, so D19's wording ("conditions that do not parse" among G1 to G4) differs from the check numbering; now a parse failure in G5 is a warning. The composer never emits conditions today. Lead: decide whether G5 parse failures should block.
- No existing test asserted GATE_FAILED for a non-blocking check (the broken-composer tests fail G1); none changed. No README or architecture text named the old behaviour.

## Evidence
| Check | Command | Result |
|---|---|---|
| new tests | `bash tools/gate.sh py -m pytest apps/converter/tests/shell/test_d19.py -q` | 9 passed |
| negative control | `BLOCKING_CHECKS` set to G1..G12 | `test_a_failed_non_blocking_check_is_a_warning_of_a_200` FAILED (1 failed, 8 passed); restored, 9 passed |
| fast gate | `bash tools/gate.sh fast` | 752 passed, 3 skipped; PASSED |

## Requests to lead
- Decide G5 parse failures (see Decisions). Quarantine of a group with an unparsable condition (D19 last sentence) is not part of this package.

## Cost notes
- Most turns: finding where the gate ids and the timeout live; the work itself was one pass.
