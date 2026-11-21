# WP-H4 the engine is always visible: status
Claimed by: build7 (agent h4-engine); heartbeat: 2026-11-22 00:40; state: running

Branch: wp/H4-engine-visible   Stage now: core

## Status
- [x] engine state module `app/engine.py`, settings names in `app/config.py`, unit tests (this commit; saved first as 26fb3e9)
- [x] header `X-Converter-Engine` on convert, report; `engine` in every batch line; engine in the request log line
- [x] `/status` extended (engine, engine_counts, model), start log line
- [x] CLI line `ENGINE: rules` on stderr after a successful conversion (exit 0 only)
- [x] warning codes MODEL_USED, MODEL_FALLBACK, MODEL_SKIPPED and the four regenerated schema files (diff: the three names only)
- [x] no-leak test over HTTP, log and CLI with a fake configured model; `/healthz` byte check
- [ ] byte comparison of form and sidecar against main 9e095ab (synthetic fixtures and the nine task sets)
- [ ] negative control, fast gate, merge of main
- [ ] review page: badge of the last conversion (skip with a plan if it costs more than 15 replies)

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
- "Configured" means MODEL_BASE_URL is set and MODEL_STEP is not off. Whether a key is required is H1's rule
  (a local Ollama has none); `/status` shows `key: file|variable|none`.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| engine module unit tests | `bash tools/gate.sh py -m pytest apps/converter/tests/shell/test_engine_visible.py -q` | 33 passed | f82d414 |
| shell tests (header on convert, report, batch line; /status; /healthz bytes; log; CLI stderr; no secret with a fake configured model; a simulated MODEL_USED, MODEL_FALLBACK, MODEL_SKIPPED drives header, log, batch and /status with no shell change) | `bash tools/gate.sh py -m pytest apps/converter/tests/shell -q` | 258 passed | the commit "shell shows the engine" |

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
The Python side is wired and tested. Left, in this order:
1. Byte proof (hard acceptance, NOT run yet): a scratch script outside the tree; `git archive 9e095ab
   apps/converter/app | tar -x -C <scratch>/main`; run `pipeline.run` over the synthetic fixtures of
   `apps/converter/tests/shell/factory.py` and the readable files of the nine sets (`tools/coi_paths.py`), once
   with `<scratch>/main/apps/converter` first on `sys.path`, once with this checkout; compare SHA-256 of the
   canonical form and sidecar; write N of N into "## Evidence".
2. Negative control: remove the `engine.HEADER` line in `headers_for` (`app/main.py`), see
   `test_every_conversion_answer_carries_the_engine_header` fail, restore.
3. `git merge --no-edit main` (keep both sides in `config.py`: `required_policy` and the `model_*` fields), then
   `bash tools/gate.sh fast > <log> 2>&1`, read the tail.
4. Review page badge (`apps/review-web/src/lib/api.ts` reads `x-converter-engine` into the outcome; `ui/result.ts`
   draws it; texts in `src/i18n/{pl,en,es}.ts`; colours in `src/style.css`, checked by `tests/contrast.test.ts`).
   `npm ci` is needed first: no `node_modules` in this worktree.
Checks passed: `bash tools/gate.sh py -m pytest apps/converter/tests/shell -q` 258 passed on this commit. The fast
gate has not run yet.

## Cost notes
- core: the 5-hour limit cut the first session after 9 replies of reading; the lead saved the loose files.
