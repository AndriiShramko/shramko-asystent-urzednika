# WP-F11a Check chain: status

Branch: wp/F11a-check-chain   Stage now: integration (core done)

## Status
- [x] Module `eval/chain/`: worker (one file in a subprocess through guard + `app.pipeline.run`), corpora (sets, unseen, hostile), runner (native, `--image` with docker mocked in tests), report (summary, baseline, compare), CLI `bash tools/gate.sh py -m eval.chain`
- [x] Unit tests on synthetic fixtures: `eval/chain/tests/test_chain.py` (17 pass): converted / refused / failed (forced exception, timeout, worker crash, refusal without Polish reason, gate failure), compare, sample, hostile, image outcomes
- [x] `.gitignore`: `data/archive/`, `eval/chain/last-run.jsonl`
- [x] Archive downloaded (182,931,304 bytes, equals the release), unpacked to data/archive/files (678 files); `--build-sample` -> `eval/chain/sample.json`: 80 files (seed 20261121; doc 15, docx 15, pdf 15 plus top-up, jpg 1, xls 1, xlsx 1, rtf 5 as refusal check; the archive has no ods, odt, png)
- [x] First full run (below); `baseline.json` and `summary.json` committed (18 tests pass)
- [x] Owner's page `docs/03-plan/check-chain.ru.md`
- [ ] Hostile corpus swap to `apps/converter/tests/evil` when WP-F16 lands

## Decisions
- Outcome classes in `eval/chain/worker.py`: `refused` = ProblemError (not GATE_FAILED) with a Polish detail (diacritic or common Polish word); GATE_FAILED, an empty or non-Polish detail, any other exception, timeout, crash = `failed`.
- Baseline and sample hold hashes only (sha256 of content, first 16 hex); hostile items are keyed by their built names.
- `fields_matter` and `no_label` come from the sidecar (origins other than `standard`; warnings whose code contains LABEL). They are 0 while the pipeline is the interim one.
- Tests of the chain live in `eval/chain/tests`, run by `bash tools/gate.sh py -m pytest eval/chain/tests -q`; the fast gate does not collect them (it runs `apps/converter/tests` only): request below.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| Core tests | `bash tools/gate.sh py -m pytest eval/chain/tests -q -p no:cacheprovider` | 17 passed | see git log |

## First full run (native, `bash tools/gate.sh py -m eval.chain --archive data/archive/files`, 110 s; 0 failed, 0 gate failures, 0 strict-lint errors)
| Corpus | Files | Converted | Refused | Failed |
|---|---|---|---|---|
| sets | 71 | 44 | 27 | 0 |
| unseen | 80 | 72 | 8 | 0 |
| hostile | 7 | 0 | 7 | 0 |

- sets per format: doc 9/9, docx 10/10, ods 9/9, pdf 9/9, xlsx 7/7 converted; jpg 9, jpeg 8, png 9, jpe 1 refused (UNREADABLE, Polish detail): no OCR on this laptop (no Tesseract), so images refuse here; the image run in CI must convert them. The sets hold 71 files of readable extensions, not 69 (one `.JPE` among them).
- unseen refused: rtf 5 (EXTENSION, expected), xls 1 (EXTENSION: no reader for old sheets), pdf 1 and jpg 1 (UNREADABLE).
- `--compare` against the fresh baseline: 0 worse, 0 better. `--image` is code plus mocked tests only: Docker is not on this laptop.

## Negative control
Forced exception inside the pipeline (`CHAIN_FAULT=raise`) is classed `failed` and `main` returns 1: `test_forced_exception_is_failed_and_exit_nonzero`. A baseline with one more field: `test_baseline_with_one_more_field_reports_a_regression`.

## Requests to lead
- Let the fast gate also collect `eval/chain/tests` (or tell me where else it should live).

## Cost notes
- integration: one reply set, only the owner page was left; nothing else needed.
- core: the shell tool refuses commands containing the word eval or git inside compound commands; use Glob/Read and plain commands.
