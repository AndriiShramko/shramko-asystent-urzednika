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
| Shell and readers tests | `bash tools/gate.sh py -m pytest apps/converter/tests/shell apps/converter/tests/readers -q` | 443 passed, 2 skipped (Tesseract, Linux), 410 s | 5b0d092 (code of the head) |
| J1: `{}` gives off, a key gives jwt, explicit jwt without a key refuses | `test_shell_config_cli.py`: `test_the_default_auth_mode_is_auto_off_without_a_key_and_jwt_with_one`, `test_jwt_mode_without_any_key_is_refused`, `test_serve_with_explicit_jwt_and_no_key_exits_3` | passed (exit 3 on explicit jwt) | 5b0d092 |
| J1: the service starts with an empty environment | real process: `python -m converter serve --port 18431` with every `AUTH_*` and `JWT_*` variable removed, called on loopback by a probe script | `/healthz` 200 after 3.3 s; the log holds "No JWT key configured: the API accepts requests WITHOUT a token..."; no traceback | 5b0d092 |
| R1: simultaneous first callers | `tests/readers/test_registry_race.py` (8 threads on a reset registry; 2 simultaneous first HTTP requests) | 4 tests passed; real process: two simultaneous first requests 200 and 200, equal bytes | 5b0d092 |
| R2: default 600; abandoned jobs | `test_defaults_follow_the_design`, `test_d19.py::test_abandoned_jobs_count_against_the_slots`, `::test_the_job_time_limit_answers_504_timeout` | passed: 504, 504, then 429 BUSY with `Retry-After: 30` in under 0.9 s, 200 after the jobs ended | 5b0d092 |
| R3: problem JSON for everything | `tests/shell/test_service_fixes.py` (4 tests of R3) | passed: 500 `application/problem+json` `GATE_FAILED`, log line `stage=internal result=KeyError` without the text of the exception; `?report=true` is 400 `BAD_REQUEST` (also in the real process); batch states ok, error, ok | 5b0d092 |
| J3: `GET /status` | `test_service_fixes.py::test_status_tells_what_runs_here_without_a_token` | passed; real process: 16 formats, `auth: off`, limits 600 s, 2, 60 pages, 20971520 bytes | 5b0d092 |
| J2: unwritable output | `test_shell_config_cli.py::test_an_output_that_cannot_be_written_is_one_line_and_exit_4` | passed: exit 4, one line on stderr, no traceback | 5b0d092 |
| R4: PDFium lock | `test_registry_race.py::test_pdfium_renders_one_page_at_a_time` | passed: 4 threads, never 2 renders at once | 5b0d092 |
| Form and sidecar byte-identical | scratch script: `pipeline.run` on 4 synthetic files and the 70 readable files of the nine task sets, once with `apps/converter/app` of main c940d03 (`git archive`), once with this branch; SHA-256 of the canonical form and of the sidecar | 74 of 74 inputs converted on both, 74 identical pairs of hashes, 0 different | 5b0d092 against c940d03 |

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
- Documents that now disagree with the behaviour (not my paths): `apps/converter/README.md` line 54 (`AUTH_MODE`
  default is `auto`) and its exit codes (4 is also "the output cannot be written"); `docs/02-architecture/
  converter-design.md` lines 131 and 135 (`JOB_TIMEOUT_S` 600, `AUTH_MODE` `auto`, and the `/v1/selftest` it names
  does not exist: `/status` does); the READMEs' jury commands of review D19 B3 (final digest, `--user "$(id -u):$(id -g)"`).
- `docker-compose.yml` keeps `AUTH_MODE: ${AUTH_MODE:-jwt}`: nothing to change, deployment stays on tokens.
- Not done, for a decision: review D19 M2 (G5 "conditions that do not parse" is a warning in code, blocking in the
  text of D19) and the "Low" note that a slow upload holds a slot; neither was in the brief.
- Item 8 was skipped (the page sends one file). If the jury's script sends three files at once, the third still gets
  429 BUSY with `Retry-After: 5`; waiting up to `QUEUE_WAIT_S` is about 15 lines in `main.py` if the lead wants it.

## Not verified
- Nothing ran in a container: the laptop has no Docker. The start with an empty environment, the two simultaneous
  first requests and `/status` were checked on a real local process, not on the image; the image workflow has to
  confirm them after the push (the jury acceptance script described in model-council note 3, section 4, which I
  did not see or run, is said to check exactly these: unwritable `/out`, the cold race, explicit jwt without a key).
- `--out` on a folder owned by another user on a real Linux host: the test raises the same `PermissionError` by hand.
- The PDFium lock under real load (two scanned PDFs at once): the test proves that renders do not overlap, with a
  stand-in for PDFium; the reviewer could not reproduce a crash without the lock either.

## Cost notes
- core: the two long waits were the shell and readers run (410 s) and the fast gate; the shell guard refuses a
  command that names the folder `eval` or chains `git` with `cp`, so such steps took an extra reply each.
