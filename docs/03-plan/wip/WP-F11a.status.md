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

## Review fixes (after WP-F4 merged)
- [x] compare lists every drop as worse; exit code from a separate fatal list (new failed, new gate failure, fall over 20 % of fields on a file of the sets, converted -> refused anywhere); tests added (21 pass in eval/chain/tests)
- [x] `docs/03-plan/check-chain.ru.md` matches the code
- [x] `tools/gate.sh fast` also runs eval/chain/tests (lead's grant). Fast gate: 583 passed, 21 deselected, 1 failed: `tests/mean/test_mean_sets.py::test_the_stored_briefs_cover_every_judged_set` (WP-F4's test; the briefs are local, not in git, so a worktree has none; not mine). Chain tests alone: 21 passed.
- [x] Full chain native after merge of main (archive read from another worktree's git-ignored data/archive/files): old baseline gave 13 worse, 8 fatal (sets fields 49 -> 37..42, the effect of F4's matter fields); baseline.json and summary.json rewritten with `--update-baseline`; compare after: 0 worse.
- Totals (files / converted / refused / failed, fields): hostile 7/0/7/0, 0. sets 71/44/27/0, 2794. unseen 80/72/8/0, 4109. All 158: 116/42/0, 6903 fields; 0 gate failures, 0 strict-lint errors.
- Per format. sets: doc 9/9/0/0 485; docx 10/10/0/0 592; ods 9/9/0/0 631; pdf 9/9/0/0 577; xlsx 7/7/0/0 509; jpg 9, jpeg 8, jpe 1, png 9 all refused (no Tesseract here). unseen: doc 19/19 1017; docx 20/20 1090; pdf 33/32 conv, 1 refused, 1922; xlsx 1/1 80; jpg 1, xls 1, rtf 5 refused. hostile: docx 1, ods 1, pdf 3, png 2 all refused.

## Decisions
- Outcome classes in `eval/chain/worker.py`: `refused` = ProblemError (not GATE_FAILED) with a Polish detail (diacritic or common Polish word); GATE_FAILED, an empty or non-Polish detail, any other exception, timeout, crash = `failed`.
- Baseline and sample hold hashes only (sha256 of content, first 16 hex); hostile items are keyed by their built names.
- `fields_matter` and `no_label` come from the sidecar (origins other than `standard`; warnings whose code contains LABEL). They are 0 while the pipeline is the interim one.
- Tests of the chain live in `eval/chain/tests`, run by `bash tools/gate.sh py -m pytest eval/chain/tests -q`; the fast gate does not collect them (it runs `apps/converter/tests` only): request below.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| Core tests | `bash tools/gate.sh py -m pytest eval/chain/tests -q -p no:cacheprovider` | 17 passed | see git log |
| Acceptance: main merged | `git merge --no-edit main` | already up to date | 57283fa |
| Acceptance: chain tests | same command | 18 passed | 57283fa |
| Acceptance: fast gate | `bash tools/gate.sh fast` | 540 passed, 21 deselected; PASSED | 57283fa |
| Acceptance: full chain run | not re-run: data/archive is absent in this worktree (git-ignored), code unchanged since the first full run above | numbers above stand | 68fb4da |

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

Acceptance control (57283fa): in `eval/chain/worker.py` the GATE_FAILED branch disabled (`if False and ...`): `test_gate_failure_is_failed` FAILED (1 failed, 17 passed); restored: 18 passed.

## Requests to lead
- Run `--image` in CI (Docker) to prove the 27 image files of the sets convert; unproven here.
- Let the fast gate also collect `eval/chain/tests` (or tell me where else it should live).

## Cost notes
- acceptance: fast gate (78 s) and one compound-command refusal took the most; keep git commands single.
- integration: one reply set, only the owner page was left; nothing else needed.
- core: the shell tool refuses commands containing the word eval or git inside compound commands; use Glob/Read and plain commands.
