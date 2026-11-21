# WP-F20i the image proves the jury's first run: status

Branch: wp/F20-image-checks   Stage now: integration (stage 2 of 2)

Worktree cut from main c940d03. Pushing this branch starts the image workflow (`wp/F20-**`), tag `test-<short sha>`.
A push while a run of this branch is in progress CANCELS that run (workflow concurrency): wait for the result first.

## Status
- [x] Stage 1 code: image environment (S3), sidecar check (V1), determinism under processor limits, hostile files; 40 unit tests (commit c97b2a5)
- [x] Stage 1 CI run GREEN on c97b2a5: actions/runs/44953569833 (native, image core, image plus all success; container check 57 passed, 0 failed in each target)
- [x] Stage 2: `wp/F-service-fixes` merged at dc77011 (merge commit 1ae882e); then main merged twice, last at 27b2621, which holds the lead's merge 9e095ab of the same branch (merge commit 2c30940, documents only on top of 16582c5)
- [x] Stage 2 code: `tools/ci/first_run.py` called by `container_check.py`; 12 unit tests, three of them the same first run against the native service (commit 4e2ba15; log tool `tools/ci/job_log.py` in 6d50964)
- [~] Stage 2 CI run: pushed the head named in the next status commit; waiting with `wait_run.py <hash> --timeout 1500` (it returns after 540 s at most: exit 2 means call again)
- [ ] One recorded RED run on a throw-away commit (plan: `ENV AUTH_MODE=jwt` baked into the Dockerfile, so the first run exits 3), then the fix
- [ ] Final run of the branch head green for both targets; digests recorded

## Decisions
- Sidecar schema: `tools/ci/sidecar.v1.schema.json` describes the shape `app/pipeline.py` emits (version, converter, counts, warnings, checks, meta); `meta.ledger` is validated against `Ledger` of `contracts/coi/meta.schema.json`. Why: the emitted sidecar does not meet the contract (10 to 11 rules: required `hashes`, `ledger`, `receipts`, `coverage`, `legal_basis` absent, `checks` is a list not an object, warning codes outside the enum), so validating against the contract would be red on every run. Rules out: saying "the sidecar meets meta.schema.json"; the count of unmet rules is printed in every conversion row.
- Sidecar out of the container: the second of the two conversions runs `sh -c 'python -m converter convert ... --report /tmp/report && cat ...'` in the same hardened container. Why: no writable mount, no extra container run. Rules out: a host folder writable by uid 10001.
- Processor limits: `--cpus 1 --cpuset-cpus 0` against `--cpus 2`. Why: `--cpus` alone is a quota and leaves the visible processor count unchanged; the cpuset makes the one-processor run see one. Rules out: a runner with a single processor (the row fails there with Docker's message).
- Locale: asked, not assumed. The probe calls `setlocale(LC_ALL, "")` and `nl_langinfo(CODESET)` inside each image; a missing locale raises on glibc. Measured on the pinned bases on 21 Nov 2026: Debian trixie glibc 2.41 answers `C.UTF-8`, Alpine musl answers `C.UTF-8;C;C;C;C;C`, both `UTF-8`, offset `+0000`; a made-up locale on glibc gives `locale.Error`.
- Hostile files: five reused from `eval/chain/hostile.py` (text named .pdf, zero bytes, truncated PDF, real 300 MB zip bomb, PNG with a 100000 x 100000 header), three added in `tools/ci/hostile_inputs.py` (entity expansion DOCX, DOCX with a declared 4 GB part, PNG cut in half). Refusal = exit 2 with a 4xx problem JSON on stderr; HTTP = 4xx `application/problem+json`; 10 s includes the start of the container.
- First run: `docker run -d -p 127.0.0.1:PORT:8080 IMAGE` and nothing else (not even the hardening flags: a jury types the short command). Three fresh containers, a file of another reader each (PDF, DOCX, PNG for OCR); `/status` is asked AFTER the pair, because it reads the readers registry and would warm it. Rules out: a pair that is not really first.
- Open API in the log: the check looks for "without a token" (case-insensitive) in the container log. Why: the brief asks for a warning; this is the text of `app/main.py`. Rules out: rewording that line without changing `first_run.OPEN_API_LOG`.
- Unwritable `--out`: two folders, a tmpfs of mode 0755 (root-owned: EACCES) and a host folder mounted `:ro` (EROFS). Why: no `sudo` in the check. Rules out: nothing; both must exit 4 with the one line.
- Time limit: `JOB_TIMEOUT_S=2` and a 40-page PDF without a text layer (the raster fixture on every page, 60 is the page limit), so every page is one OCR run. After the 504 the check asks `/healthz` and converts a DOCX. Rules out: proving it natively on the laptop (no Tesseract there: the file finishes at once).

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| Unit tests of the stage 1 checks | `bash tools/gate.sh py -m pytest tools/ci/tests/test_image_checks.py -q` | 40 passed | c97b2a5 |
| All CI tool tests | `bash tools/gate.sh py -m pytest tools/ci/tests -q` | 87 passed in 118 s | c97b2a5 |
| Fast gate before the first push | `bash tools/gate.sh fast` | 781 passed, 3 skipped, exit 0 (8 min) | c97b2a5 |
| C.UTF-8 exists in both bases | probe of `container_check.PROBE` in a local core image with `-e`; `docker run python:3.14-slim-trixie@sha256:9aaa47...` | see Decisions (locale) | c97b2a5 |
| Hostile files refused natively | part of the unit tests (8 files, exit 2, about 1 s each) | passed | c97b2a5 |
| First run natively, no configuration | `bash tools/gate.sh py -m pytest tools/ci/tests/test_first_run.py tools/ci/tests/test_image_checks.py -q` | 52 passed in 49 s | 4e2ba15 |
| Stage 1 in CI, both targets | `bash tools/gate.sh py tools/ci/job_log.py c97b2a5e20badbcfdc3aa65bf380b1933cfec3c2 --job "image ("` | actions/runs/44953569833: core 57 passed 0 failed, plus 57 passed 0 failed. Locale: core (musl) `C.UTF-8;C;C;C;C;C`, plus (glibc) `C.UTF-8`, both codeset UTF-8, offset +0000. Determinism: PNG form sha256 8a400f2edda6 and sidecar f71fc4c4a07a, PDF form 5c101d40c2fd and sidecar 0494608a8ab6, each the same in 4 conversions AND the same in core and plus. Hostile: 8 of 8 refused on the command line (exit 2, 0.6 to 1.6 s) and over HTTP (413, 415, 422, at most 0.1 s), healthz 200 after. Sidecars of 21 fixtures valid; 10 rules of the full contract not met | c97b2a5 |
| Fast gate before the second push | `bash tools/gate.sh fast` | `gate: fast PASSED on 16582c5` (log `%TEMP%/f20i_fast2.log`); after it only `tools/ci/**` and documents changed: `bash tools/gate.sh py -m pytest tools/ci/tests -q` 100 passed in 209 s, lint selection of the gate clean on `tools/ci` | 16582c5, then 6d50964 |
| The slow file really is slow | one local container of an older core image, `convert /in/skan.pdf` (40 pages, 52599 bytes) | 121 s on the laptop, about 3 s a page; the command line has no time limit | local image 18892d084c8e |

## Negative control
Unit level (in `tools/ci/tests/test_image_checks.py`, `test_first_run.py`): a broken sidecar (8 kinds), a changed image variable (5), a refused locale, wrong offset, differing bytes between runs, a hostile answer that is a form, a traceback, a 500 plain text, a hang, a first pair with one 429 or different bytes, exit 1 instead of 3 or 4, a 200 instead of 504: each makes its check report a problem. The recorded RED CI run comes next.

## Requests to lead
- `contracts/coi/meta.schema.json` and the emitted sidecar disagree (see Decisions). Either the product moves to the contract (WP-F15 scope) or the contract gets a note that version 1 of the sidecar is the interim shape. Until then documents must not claim the sidecar is validated against `meta.schema.json`; it is validated against `tools/ci/sidecar.v1.schema.json` plus the contract's `Ledger`.
- `docs/03-plan/ownership.md` has no line for `tools/ci/**` under WP-F20i (it names WP-F20); the brief of this package is the authority used.
- `docker-compose.yml` is untouched: it keeps `AUTH_MODE: ${AUTH_MODE:-jwt}`. Its comment and the README still describe the old default of the service; the README is not mine.

## Cost notes
- stage 1: the fast gate takes 8 minutes on this laptop and must not overlap an edit of the tree; the surprise was the sidecar contract (two probes to find out).
