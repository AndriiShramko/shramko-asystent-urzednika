# WP-F11a Check chain: status

Branch: wp/F11a-check-chain   Stage now: core (done) -> integration

## Status
- [x] Module `eval/chain/`: worker (one file in a subprocess through guard + `app.pipeline.run`), corpora (sets, unseen, hostile), runner (native, `--image` with docker mocked in tests), report (summary, baseline, compare), CLI `bash tools/gate.sh py -m eval.chain`
- [x] Unit tests on synthetic fixtures: `eval/chain/tests/test_chain.py` (17 pass): converted / refused / failed (forced exception, timeout, worker crash, refusal without Polish reason, gate failure), compare, sample, hostile, image outcomes
- [x] `.gitignore`: `data/archive/`, `eval/chain/last-run.jsonl`
- [ ] Download the archive (182,931,304 bytes per the release) into `data/archive/`, unpack, `--build-sample` -> `eval/chain/sample.json`
- [ ] First full run, results below; `--update-baseline`; `baseline.json`, `summary.json` committed
- [ ] Owner's page `docs/03-plan/check-chain.ru.md`
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

## Negative control
Forced exception inside the pipeline (`CHAIN_FAULT=raise`) is classed `failed` and `main` returns 1: `test_forced_exception_is_failed_and_exit_nonzero`. A baseline with one more field: `test_baseline_with_one_more_field_reports_a_regression`.

## Requests to lead
- Let the fast gate also collect `eval/chain/tests` (or tell me where else it should live).

## Cost notes
- core: the shell tool refuses commands containing the word eval or git inside compound commands; use Glob/Read and plain commands.
