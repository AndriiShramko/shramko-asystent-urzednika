# WP-H4 the engine is always visible: status
Claimed by: build7 (agent h4-engine); heartbeat: 2026-11-22 01:08; state: running

Branch: wp/H4-engine-visible   Stage now: core

## Status
- [x] engine state module `app/engine.py`, settings names in `app/config.py`, unit tests (this commit; saved first as 26fb3e9)
- [x] header `X-Converter-Engine` on convert, report; `engine` in every batch line; engine in the request log line
- [x] `/status` extended (engine, engine_counts, model), start log line
- [x] CLI line `ENGINE: rules` on stderr after a successful conversion (exit 0 only)
- [x] warning codes MODEL_USED, MODEL_FALLBACK, MODEL_SKIPPED and the four regenerated schema files (diff: the three names only)
- [x] no-leak test over HTTP, log and CLI with a fake configured model; `/healthz` byte check
- [x] byte comparison of form and sidecar against main 9e095ab, synthetic fixtures and the nine task sets: 79 of 79
- [x] review page: band with the engine of the last conversion, three languages, contrast pairs, tests (this commit)
- [~] byte comparison on the 158 files of the chain corpora (71 sets, 80 unseen, 7 hostile): both runs started 01:05, not compared yet
- [ ] negative control, merge of main, fast gate

## Decisions
- The engine of one conversion is read from the warning codes of its sidecar (`engine.engine_of`): MODEL_FALLBACK
  -> rules-fallback, MODEL_USED -> rules+model, else rules. Why: H1 emits a warning in the pipeline and the shell
  follows with no new plumbing. Rules out: a second channel from the pipeline to the shell.
- `MODEL_STEP` default `auto`, choices `auto|off` (owner override). `engine.MODEL_STEP_BUILT = False` is the one
  switch H1 turns on; until then a configured model is state UNAVAILABLE, reason `no-model-step`, engine `rules`.
  Rules out: showing "rules+model" or "rules-fallback" for a model that nothing calls.
- The key is never stored: settings hold only `model_api_key_set` (MODEL_API_KEY is not empty) and the path
  `model_api_key_file` (never opened here, kept out of `repr`, like `model_base_url`). Rules out: a key in a
  settings dump.
- Of the URL only the host CLASS is shown (`loopback|private|public|invalid`), computed from the shape of the
  host, never resolved. Why: the brief says name and host class; a host name may itself be private. Rules out: the
  host name, port, user, path and query in any output. A dotted name is `public` whatever it points at.
- The CLI line is printed only on exit 0, after the outputs are written. Why: the existing tests fix stderr of a
  refusal and of an unwritable output to exactly one line. Rules out: an engine line beside a problem JSON.
- A refusal carries no engine header and its batch line no `engine` key: no engine ran. `/status.engine` is the
  engine of the last conversion; before the first one, the engine the next is expected to run on.
- Review page: the band is a paragraph after the title of the result: label, the token of the header in `code`,
  a sentence; grey, green, amber only repeat the words. No header or an unknown value is shown as "not stated",
  never as `rules`. The three new codes got `warn.*` texts in pl, en, es (an existing test demands them).
- "Configured" means MODEL_BASE_URL is set and MODEL_STEP is not off. Whether a key is required is H1's rule
  (a local Ollama has none); `/status` shows `key: file|variable|none`.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| engine module unit tests | `bash tools/gate.sh py -m pytest apps/converter/tests/shell/test_engine_visible.py -q` | 33 passed | f82d414 |
| shell tests (header on convert, report, batch line; /status; /healthz bytes; log; CLI stderr; no secret with a fake configured model; a simulated MODEL_USED, MODEL_FALLBACK, MODEL_SKIPPED drives header, log, batch and /status with no shell change) | `bash tools/gate.sh py -m pytest apps/converter/tests/shell -q` | 258 passed | the commit "shell shows the engine" |
| HARD: form and sidecar byte-identical to main 9e095ab | scratch `byteproof.py` (outside the tree): `pipeline.run` behind `inspect_upload`, once with `git archive 9e095ab apps/converter/app` first on `sys.path` (asserted by `app.__file__`), once with this checkout; SHA-256 of the canonical form and sidecar | 79 of 79 identical (9 synthetic drawn once and read by both runs, 70 files of the nine sets; 78 converted, 1 refused UNREADABLE, the same in both; 0 errors) | 937cb2a |
| the same with a fake configured model (MODEL_BASE_URL with user, password, port, query; MODEL_NAME; MODEL_API_KEY) | same script, argument `model` | 79 of 79 identical to main | 937cb2a |
| review page builds and its tests pass | `npm ci`, `npm run build` (tsc and vite), `npm test` in `apps/review-web` | built; 54 passed (3 files): engine read from the header, band in pl, en, es with words and token, nothing focusable, 9 new contrast pairs | this commit |

## Negative control
(not run yet)

## Requests to lead
- BLOCKING FOR THE IMAGE WORKFLOW: `tools/ci/container_check.py` line 222 (`if cp.stderr.strip(): problems.append("stderr
  not empty…")`) fails every converted fixture once the CLI prints `ENGINE: rules` on stderr, which the brief asks
  for. `tools/ci/**` is not mine. Proposed text for lines 222-223:
  `noise = [ln for ln in cp.stderr.decode(errors="replace").splitlines() if ln.strip() and not ln.startswith("ENGINE: ")]`
  `if noise: problems.append(f"stderr not empty: {' | '.join(noise)[-200:]}")`
  Merge H4 together with this patch, or the image workflow goes red.

## Left for the next stage
Python side and review page are done and tested. Left, in this order:
1. The 158-file comparison (the corpora of `eval.chain`: sets, unseen sample of `data/archive` of the main
   checkout, hostile files built once). It needs a scratch script (mine is not in git): for each item of
   `eval.chain.corpora.sets_items() + unseen_items(archive=<main checkout>/data/archive) + hostile_items(<dir>)` run
   `inspect_upload` and `pipeline.run`, hash the canonical form and sidecar, once per code tree, compare.
2. Negative control: remove the `engine.HEADER` line in `headers_for` (`app/main.py`), see
   `test_every_conversion_answer_carries_the_engine_header` fail, restore.
3. `git merge --no-edit main` (keep both sides in `config.py`: `required_policy` and the `model_*` fields), then
   `bash tools/gate.sh fast > <log> 2>&1`, read the tail; re-run the byte proof only if `main` changed code under
   `apps/converter/app` (then against the new main, not 9e095ab).
Checks passed: shell tests 258 passed on 937cb2a; byte proof 79 of 79 on 937cb2a (review page files do not enter
the Python package); `npm run build` and `npm test` 54 passed on this commit. The fast gate has not run yet.

## Cost notes
- core: the 5-hour limit cut the first session after 9 replies of reading; the lead saved the loose files.
