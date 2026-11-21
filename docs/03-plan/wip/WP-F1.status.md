# WP-F1 Environment check and service shell: status

Branch: wp/F1-service-shell   Stage now: core (done) -> integration

## Status
- [x] Configuration (design 4), validated at start, inconsistent sets refused with every problem listed (app/config.py)
- [x] Guard (design 6.1): name, extension, size, content proofs, polyglot, declared type, archive limits, macros (app/guard/)
- [x] Token check and per-subject rate limit (app/auth/)
- [x] Pipeline seam: ONE function `app.pipeline.run(data, filename, settings) -> PipelineResult(form, sidecar)`, stub returns a fixed form that passes tools/coi_lint
- [x] HTTP shell: convert, ?report=1 (multipart/mixed), report, inspect, batches (files or one ZIP), healthz, problem answers, body limit with counted bytes, static front end mount when a build exists (app/main.py)
- [x] Command line `convert` (exit codes 0/2/3/4) and `serve` (app/cli.py)
- [x] Core tests: apps/converter/tests/shell/ (121 pass)
- [ ] Dockerfile (two targets, digests pinned, dedicated user, one port, Node stage that tolerates a missing apps/review-web), docker-compose.yml
- [ ] apps/converter/README.md (build, run native and container, configuration table, API with curl)
- [ ] tools/env_check.py and docs/03-plan/wip/environment.md (step 0 of the package)
- [ ] Integration: check each README command, concurrency BUSY test, an end-to-end `python -m converter serve` run with curl
- [ ] Container acceptance (needs CI, WP-F20): both targets build, non-root, `--network none` conversion of reference set 1

## Decisions
- Body limit is a pure ASGI middleware: declared Content-Length first (cap = limit + 1 MiB framing; batches 5x), then bytes counted as they arrive, so a lying header cannot pass a large body. The exact file limit is judged by the guard on the part itself. Rules out: relying on the framework's buffering.
- Token and scope and rate limit run before the body is read (a test proves it).
- Zip ratio rule (100:1) applies only to members above 1 MB: tiny XML parts may legitimately compress that well; the 50 MB / 200 MB / 2,000 member / nested / name rules are unconditional.
- Zip member names are judged from `orig_filename`: on Windows zipfile rewrites backslashes before we see them.
- The shell's own gate is the key check (title, tabs, flow only, D1); `GATE_FAILED` otherwise. The full gate belongs to WP-F14 and will be called inside or behind `pipeline.run`.
- CLI `convert` ignores AUTH_MODE (no HTTP, no token): it forces `off`. `serve` honours it. Additions beyond design 4: `UI_DIR`, `--host`, `--port`.
- Concurrency: when all `CONCURRENCY` slots are busy the request gets 429 BUSY at once (no queue).
- Guard sniffs every proof, not only the one for the extension: more than one satisfied proof = TYPE_MISMATCH ("polyglot").

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| core tests: healthz, valid PDF 200 and passes tools/coi_lint, negative controls of guard and token, config, CLI | `bash tools/gate.sh py -m pytest apps/converter/tests -q` | 121 passed | see git log |
| cheapest test (swapped DOCX/XLSX/ODS suffixes refused by content) | test_swapped_zip_suffixes_are_refused_by_content_not_as_a_generic_zip | 5 cases pass, detail names the real format | see git log |

## Negative control
Not yet recorded (acceptance stage).

## Requests to lead
- `bash tools/gate.sh fast` fails in this worktree at lint: `ruff` is given the folder `eval`, which does not exist yet ("E902 ... eval:1:1"). The pytest half of the gate was run directly instead (121 passed). Either create `eval/` or make the lint skip missing folders.
- Starlette prints a deprecation: its TestClient wants `httpx2` instead of `httpx` (test client only, no product effect). No action needed now.
- `app/pipeline.py` is not in docs/03-plan/ownership.md; the brief assigns it to this package until a reader package takes the body over. Please add the row.

## Cost notes
- core: the most turns went to reading the design and the lint rules to build a valid form and OLE/ZIP fixtures; a ready-made fixture module and a valid stub form in the skeleton would have saved about five replies.
