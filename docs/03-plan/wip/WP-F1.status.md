# WP-F1 Environment check and service shell: status

Branch: wp/F1-service-shell   Stage now: integration (done) -> acceptance

## Status
- [x] Configuration (design 4), validated at start, inconsistent sets refused with every problem listed (app/config.py)
- [x] Guard (design 6.1): name, extension, size, content proofs, polyglot, declared type, archive limits, macros (app/guard/)
- [x] Token check and per-subject rate limit (app/auth/)
- [x] Pipeline seam: ONE function `app.pipeline.run(data, filename, settings) -> PipelineResult(form, sidecar)`, stub returns a fixed form that passes tools/coi_lint
- [x] HTTP shell: convert, ?report=1 (multipart/mixed), report, inspect, batches (files or one ZIP), healthz, problem answers, body limit with counted bytes, static front end mount when a build exists (app/main.py)
- [x] Command line `convert` (exit codes 0/2/3/4) and `serve` (app/cli.py)
- [x] Core tests: apps/converter/tests/shell/ (121 pass)
- [x] Dockerfile (two targets, digests pinned, dedicated user, one port, Node stage that tolerates a missing apps/review-web), docker-compose.yml; NOT built (no Docker here)
- [x] apps/converter/README.md (build, run native and container, configuration table, API with curl)
- [x] tools/env_check.py and docs/03-plan/wip/environment.md (step 0 of the package)
- [x] Integration: README commands run, concurrency BUSY test, end-to-end serve run with curl, task-set files through guard and HTTP
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

## Integration evidence
| Item | Command | Result |
|---|---|---|
| all tests | `bash tools/gate.sh fast` | 212 passed, gate fast PASSED (lint clean) |
| task sets (marker sets): 68 real files of 9 sets, guard by own extension; 70 files through HTTP convert, 200 and 0 linter errors | `bash tools/gate.sh py -m pytest apps/converter/tests/shell/test_shell_sets.py -q` | pass |
| BUSY when all slots taken, first request unharmed, slot free again | test_shell_concurrency.py | pass |
| slots given back over 12 sequential requests, both client modes | test_shell_sequence.py | pass |
| end-to-end: `serve` with a real token; curl healthz 200, no token 401, convert 200 application/json, PNG named .pdf 415 TYPE_MISMATCH, report 200 multipart/mixed, inspect, batch (ok line and error line); CLI output byte-equal to HTTP output; log lines with file name or token: 0 | script run once, synthetic file | as listed |
| README links | `python tools/check_links.py .` | broken links: 0 |
| env check | `python tools/env_check.py` | Docker, WSL, Tesseract, Python 3.14 missing; Node 22 present (environment.md) |

### Findings from the real sets (fixed in app/guard/checks.py, pinned by synthetic tests in test_shell_guard_ole.py)
- Every real .doc embeds an Office theme ZIP package inside a stream; the polyglot rule called all of them TYPE_MISMATCH (doc, zip). Now a zip counts as a proof only if it ends the file for compound files; a zip appended to a .doc is still refused.
- Two forms (set 7 and reference 5) are named .DOC but hold a DOCX package. Read as DOCX (kind docx, ext doc). A DOCX named .xlsx and a legacy workbook named .doc stay refused.
- The rate limit answers 429 with code BUSY, as the design table says; a 61st request inside a minute is not a concurrency fault.

## Negative control
Not yet recorded (acceptance stage).

## Requests to lead
- `bash tools/gate.sh fast` fails in this worktree at lint: `ruff` is given the folder `eval`, which does not exist yet ("E902 ... eval:1:1"). The pytest half of the gate was run directly instead (121 passed). Either create `eval/` or make the lint skip missing folders.
- Dockerfile.dockerignore (next to the Dockerfile, BuildKit reads it) is added by this package to keep data/ and .git out of the context; a root .dockerignore would be an alternative. docker-compose.yml expects secrets/jwt_secret (ignored by .gitignore).
- Starlette prints a deprecation: its TestClient wants `httpx2` instead of `httpx` (test client only, no product effect). No action needed now.
- `app/pipeline.py` is not in docs/03-plan/ownership.md; the brief assigns it to this package until a reader package takes the body over. Please add the row.

## Cost notes
- integration: the most turns went to the real-sets findings (the .doc polyglot, the .DOC holding DOCX, a rate limit mistaken for a slot leak); a first run of the sets test with per-file status output would have found all three at once.
- core: the most turns went to reading the design and the lint rules to build a valid form and OLE/ZIP fixtures; a ready-made fixture module and a valid stub form in the skeleton would have saved about five replies.
