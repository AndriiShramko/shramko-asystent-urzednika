# WP-F-svc service fixes for the jury's first run: status

Branch: wp/F-service-fixes   Stage now: core (whole package in one stage)

Sources of the items (data from reviewers, checked against the code): review-D19 (B1, B2, B3, M1, M3, Low) and
model-council note 3 "jury run readiness" (sections 2 and 5), both of 2026-11-21, in the lead's vault.

## Status
- [x] 1. J1 `AUTH_MODE=auto` default, `auth_enabled`, warning that names the cause
- [ ] 2. R1 cold-start race of the readers registry (lock, flag after the imports, warm-up in `create_app`)
- [ ] 3. R2 `job_timeout_s` 600; abandoned jobs count against the slots (BUSY, Retry-After 30)
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

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|

## Negative control
(not yet)

## Requests to lead
(none yet)

## Cost notes
(at the end)
