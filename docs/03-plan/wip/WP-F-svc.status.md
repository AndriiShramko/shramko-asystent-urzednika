# WP-F-svc service fixes for the jury's first run: status

Branch: wp/F-service-fixes   Stage now: core (whole package in one stage)

Sources of the items (data from reviewers, checked against the code): review-D19 (B1, B2, B3, M1, M3, Low) and
model-council note 3 "jury run readiness" (sections 2 and 5), both of 2026-11-21, in the lead's vault.

## Status
- [x] 1. J1 `AUTH_MODE=auto` default, `auth_enabled`, warning that names the cause
- [x] 1. committed as 734d419
- [x] 2. R1 cold-start race of the readers registry (lock, flag after the imports, warm-up in `create_app`)
- [x] 2. committed as 671ddf8
- [x] 3. R2 `job_timeout_s` 600; abandoned jobs count against the slots (BUSY, Retry-After 30)
- [ ] 4. R3 catch-all: unexpected exception and request validation as problem JSON; batch stream continues
- [ ] 5. J3 `GET /status`
- [ ] 6. J2 `convert --out` that cannot be written: one line, exit 4
- [ ] 7. R4 PDFium lock; robust time-limit test
- [ ] 8. Optional: wait for a free slot up to `QUEUE_WAIT_S` (only if the review page sends files in parallel)
- [ ] Acceptance: shell and readers tests, fast gate, negative control, evidence table

## Decisions
- J1: explicit `AUTH_MODE=off` keeps its old log line, `auto` without a key logs the new one / the two causes differ
  and an existing test pins the old text / rules out one message for both.
- J1: `auto` with a key file that does not exist refuses to start / a named key means the operator wanted tokens /
  rules out a silent fall back to "off" on a typo in the path.

- R1: the race test resets the registry (readers, hooks, flag, the reader modules out of `sys.modules`) and slows
  every import by 20 ms / the unfixed code then fails every run, not one run in ten / rules out a flaky proof.
- R1: a reader module that fails to import leaves the flag unset, so the next call tries again and `create_app`
  fails at start / a partial reader list answered false 422 / rules out a service that runs with half its readers.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|

## Negative control
R1, on the tree of item 2: in `app/readers/__init__.py::_discover` the lock was replaced by `if True:` and the flag
set before the import loop (the code as it was on main). `bash tools/gate.sh py -m pytest
apps/converter/tests/readers/test_registry_race.py -q` then gave **3 failed, 1 passed**:
`test_simultaneous_first_callers_all_see_the_full_registry`, `test_a_failed_import_is_tried_again_not_left_half_done`,
`test_two_simultaneous_first_requests_both_convert_with_equal_bytes` (the fourth test proves the warm-up, which was
left in place). Restored before the commit of item 2: 4 passed.

## Requests to lead
(none yet)

## Cost notes
(at the end)
