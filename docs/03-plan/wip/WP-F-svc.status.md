# WP-F-svc service fixes for the jury's first run: status

Branch: wp/F-service-fixes   Stage now: core (whole package in one stage)

Sources of the items (data from reviewers, checked against the code): review-D19 (B1, B2, B3, M1, M3, Low) and
model-council note 3 "jury run readiness" (sections 2 and 5), both of 2026-11-21, in the lead's vault.

## Status
- [x] 1. J1 `AUTH_MODE=auto` default, `auth_enabled`, warning that names the cause (commit 734d419)
- [x] 2. R1 cold-start race of the readers registry (lock, flag after the imports, warm-up in `create_app`) (671ddf8)
- [x] 3. R2 `job_timeout_s` 600; abandoned jobs count against the slots (BUSY, Retry-After 30) (e021b98); the
      time-limit test of item 7 was made robust here already, because a leaked job would now block later tests
- [x] 4. R3 catch-all: unexpected exception and request validation as problem JSON; batch stream continues  (6349e8d)
- [x] 5. J3 `GET /status` (2fa9651)
- [x] 6. J2 `convert --out` that cannot be written: one line, exit 4 (10b47ed)
- [x] 7. R4 PDFium lock (test: four threads, one render at a time) (5b0d092); the time-limit test was fixed in e021b98
- [x] 8. SKIPPED as the brief says: the review page does not send files in parallel. `apps/review-web/src/ui/app.ts`
      lines 84-95 (`run`): of several dropped files only `files[0]` is sent, in one request, with the notice
      `upload.multiple`. No `QUEUE_WAIT_S` was added; a full service still answers 429 BUSY at once.
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
- R2: the BUSY of abandoned jobs is raised inside `pipeline.run_limited` (Retry-After 30), apart from the slot BUSY
  of the shell (Retry-After 5) / the brief asks for it there / running jobs are at most 2 x CONCURRENCY - 1, not
  CONCURRENCY: an abandoned job is not counted together with the running ones.
- R2: the time-limit test holds its job on an event (it would run 30 s) and asserts 0.9 s <= answer < 15 s / the old
  margin was 0.1 s / rules out a `sleep` whose thread outlives the test and trips the new abandoned-job count.
- R3: the catch-all is the pure ASGI middleware `CatchAll` (outermost of ours); `@app.exception_handler(Exception)`
  is registered too, as the backstop / Starlette re-raises after that handler, so the server would still log a stack
  trace with the text of the exception (it may quote the file) / rules out the handler alone.
- R3: the code of an unexpected exception is `GATE_FAILED` (500), detail "Błąd wewnętrzny usługi." / the table of
  codes lives in `app/guard/problems.py`, not mine, and the reviewer's patch uses it / rules out a new code now.
- R3: the 400 of a request validation error names the parameter and never its value.
- J3: `/status` has exactly six keys (`service`, `version`, `engine`, `auth`, `formats`, `limits`) and reads the
  formats from the readers registry / small, and H4 extends it / rules out paths, key names, environment dumps.
- J2: `--report DIR` that cannot be written gets the same line and exit 4 as `--out` / same cause on a mounted
  folder / rules out a traceback on the second output.
- R4: the lock covers open, render and close of the PDF page, not the OCR of the rendered picture / OCR is the
  long part and is a separate process / rules out serialising whole scanned documents.

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
- Optional, after the freeze: a code of its own for an unexpected exception (`INTERNAL`, 500) in
  `app/guard/problems.py` and in the table of `docs/02-architecture/converter-design.md` section 3; today it is
  `GATE_FAILED` with the detail "Błąd wewnętrzny usługi.".

## Cost notes
(at the end)
