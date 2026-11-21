# WP-F20i the image proves the jury's first run: status

Branch: wp/F20-image-checks   Stage now: core (stage 1 of 2)

Worktree cut from main c940d03. Pushing this branch starts the image workflow (`wp/F20-**`), tag `test-<short sha>`.

## Status
- [~] Stage 1 code: image environment (S3), sidecar check (V1), determinism under processor limits, hostile files; unit tests 40 passed natively; not yet run in CI
- [ ] Stage 1 CI run green for both targets (run id here)
- [ ] Stage 2: merge `wp/F-service-fixes` (not visible locally or on origin at 21 Nov, start of stage 1)
- [ ] Stage 2: the jury's first run as a check (no environment: healthz and status; two simultaneous first requests on 3 fresh containers; AUTH_MODE=jwt without a key exits 3; --out into a read-only mount exits 4; JOB_TIMEOUT_S=2 gives 504 TIMEOUT and healthz after)
- [ ] One recorded RED run on a throw-away commit, then the fix
- [ ] Final run of the branch head green for both targets; digests recorded

## Decisions
- Sidecar schema: `tools/ci/sidecar.v1.schema.json` describes the shape `app/pipeline.py` emits (version, converter, counts, warnings, checks, meta); `meta.ledger` is validated against `Ledger` of `contracts/coi/meta.schema.json`. Why: the emitted sidecar does not meet the contract (10 to 11 rules: required `hashes`, `ledger`, `receipts`, `coverage`, `legal_basis` absent, `checks` is a list not an object, warning codes outside the enum), so validating against the contract would be red on every run. Rules out: saying "the sidecar meets meta.schema.json"; the count of unmet rules is printed in every conversion row.
- Sidecar out of the container: the second of the two conversions runs `sh -c 'python -m converter convert ... --report /tmp/report && cat ...'` in the same hardened container. Why: no writable mount, no extra container run. Rules out: a host folder writable by uid 10001.
- Processor limits: `--cpus 1 --cpuset-cpus 0` against `--cpus 2`. Why: `--cpus` alone is a quota and leaves the visible processor count unchanged; the cpuset makes the one-processor run see one. Rules out: a runner with a single processor (the row fails there with Docker's message).
- Locale: asked, not assumed. The probe calls `setlocale(LC_ALL, "")` and `nl_langinfo(CODESET)` inside each image; a missing locale raises on glibc. Measured on the pinned bases on 21 Nov 2026: Debian trixie glibc 2.41 answers `C.UTF-8`, Alpine musl answers `C.UTF-8;C;C;C;C;C`, both `UTF-8`, offset `+0000`; a made-up locale on glibc gives `locale.Error`.
- Hostile files: five reused from `eval/chain/hostile.py` (text named .pdf, zero bytes, truncated PDF, real 300 MB zip bomb, PNG with a 100000 x 100000 header), three added in `tools/ci/hostile_inputs.py` (entity expansion DOCX, DOCX with a declared 4 GB part, PNG cut in half). Refusal = exit 2 with a 4xx problem JSON on stderr; HTTP = 4xx `application/problem+json`; 10 s includes the start of the container.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| Unit tests of the new checks | `bash tools/gate.sh py -m pytest tools/ci/tests/test_image_checks.py -q` | 40 passed in 19 s | working tree before the first commit |
| C.UTF-8 exists in both bases | probe of `container_check.PROBE` in a local core image with `-e`; `docker run python:3.14-slim-trixie@sha256:9aaa47...` | see Decisions (locale) | working tree |
| Hostile files refused natively | part of the unit tests (8 files, exit 2, about 1 s each) | passed | working tree |

## Negative control
Unit level (in `tools/ci/tests/test_image_checks.py`): a broken sidecar (8 kinds), a changed image variable (5), a refused locale, wrong offset, differing bytes between runs, a hostile answer that is a form, a traceback, a 500 plain text, a hang: each makes its check report a problem. The recorded RED CI run comes in stage 2.

## Requests to lead
- `contracts/coi/meta.schema.json` and the emitted sidecar disagree (see Decisions). Either the product moves to the contract (WP-F15 scope) or the contract gets a note that version 1 of the sidecar is the interim shape. Until then documents must not claim the sidecar is validated against `meta.schema.json`; it is validated against `tools/ci/sidecar.v1.schema.json` plus the contract's `Ledger`.
- `docs/03-plan/ownership.md` has no line for `tools/ci/**` under WP-F20i (it names WP-F20); the brief of this package is the authority used.

## Cost notes
- stage 1: (to fill at the stage end)
