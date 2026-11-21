# WP-H4 the engine is always visible: status
Claimed by: build7 (agent h4-engine); heartbeat: 2026-11-22 02:30; state: running

Branch: wp/H4-engine-visible   Stage now: core

## Status
- [x] engine state module `app/engine.py`, settings names in `app/config.py`, unit tests (this commit; saved first as 26fb3e9)
- [x] header `X-Converter-Engine` on convert, report; `engine` in every batch line; engine in the request log line
- [x] `/status`: `engine` always; the key `model` (state, reason, name, host class, key source, conversions by engine) only when MODEL_BASE_URL is set, so with nothing configured the body is byte for byte main's; start log line
- [x] CLI line `ENGINE: rules` on stderr after a successful conversion (exit 0 only)
- [x] warning codes MODEL_USED, MODEL_FALLBACK, MODEL_SKIPPED and the four regenerated schema files (diff: the three names only)
- [x] no-leak test over HTTP, log and CLI with a fake configured model; `/healthz` byte check
- [x] byte comparison of form and sidecar against main 9e095ab, synthetic fixtures and the nine task sets: 79 of 79
- [x] review page: band with the engine of the last conversion, three languages, contrast pairs, tests (this commit)
- [x] negative control (on 913f787), merge of main a7f2cee (b5d42f4)
- [x] byte comparison after the merge against main a7f2cee, code tree of b5d42f4: 158 of 158 on the chain corpora (71 sets, 80 unseen, 7 hostile) and 79 of 79 on the fixtures and sets, also with a fake configured model
- [x] fast gate on the merged tree: PASSED on 2af59a7
- [x] `/status` brought back to its six keys when nothing is configured (this commit): `tools/ci/first_run.py` on main fixes them, and its test failed on 2af59a7
- [x] the log lines reach the output of a real server (this commit): found by a smoke run on 127.0.0.1 that the logger `converter` had no handler, so neither the engine line nor the line per conversion was ever printed
- [~] on this commit, started and not read yet: the fast gate, `tools/ci/tests`, the byte comparison of this head's code tree against main a7f2cee

## Decisions
- `serve` gives the logger `converter` the server's own handler (a copy of uvicorn's log configuration with one
  more logger), and the engine line is written at start-up (lifespan), not while the app is built. Why: on a real
  server every line of ours below a warning was lost, the tests saw them only through `caplog`. Rules out: a
  handler installed at import or in `create_app` (it would leak into every test and every embedding). Side effect
  to know: the content-free line `stage=convert result=ok job=… size=… engine=…` is now printed per conversion.
- `/status` gains nothing while no model is configured; `model` appears with MODEL_BASE_URL. Why: the image's
  first-run check (`tools/ci/first_run.py`, `STATUS_KEYS`, not mine) demands exactly six keys, and the brief says
  "with nothing configured the output is byte-identical". Rules out: `configured: no` as an explicit field; a
  status without the key `model` means no model is configured, and `"engine":"rules"` says the rest.
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
| review page builds and its tests pass | `npm ci`, `npm run build` (tsc and vite), `npm test` in `apps/review-web` | built; 54 passed (3 files): engine read from the header, band in pl, en, es with words and token, nothing focusable, 9 new contrast pairs | 913f787, again on b5d42f4 |
| HARD, after the merge: form and sidecar byte-identical to main a7f2cee | same script; both code trees unpacked outside the repository (`git archive a7f2cee apps/converter/app`, `git archive b5d42f4 apps/converter/app`) and put first on `sys.path`; the 158 items of `eval.chain.corpora` | 158 of 158 identical (152 converted, 6 refused, 0 errors: the numbers of the chain baseline) | b5d42f4 |
| the same on the 9 synthetic fixtures and the 70 files of the nine sets, without and with a fake configured model | same script | 79 of 79 and 79 of 79 identical to main a7f2cee | b5d42f4 |
| the comparison can fail | same script, main 9e095ab against main a7f2cee (the validators merge) | 56 of 158 identical, 102 differ: a real change of the output is seen | scratch trees |
| before the merge, the 158 items against main 9e095ab | same script; the branch side read the checkout while main was being merged into it, so this row is a hint and not a proof | 158 of 158 identical | 913f787 |
| shell tests on the merged tree | `bash tools/gate.sh py -m pytest apps/converter/tests/shell -q` | 258 passed | 2af59a7 |
| fast gate on the merged tree | `bash tools/gate.sh fast` | `gate: fast PASSED on 2af59a7` | 2af59a7 |
| the checks of the image that run without Docker | `bash tools/gate.sh py -m pytest tools/ci/tests -q` | 2af59a7: 1 failed (`test_first_run_of_the_native_service_with_no_configuration`: `/status` had eight keys), 99 passed. The fast gate does not run this folder | 2af59a7 |
| `/status` back to six keys with no model; first-run check | `bash tools/gate.sh py -m pytest apps/converter/tests/shell/test_engine_visible.py apps/converter/tests/shell/test_service_fixes.py tools/ci/tests/test_first_run.py::test_first_run_of_the_native_service_with_no_configuration -q` | 54 passed | e4fc776 |
| a real server on 127.0.0.1 (scratch `smoke.sh`: `python -m converter serve`, `curl`), without and with a fake configured model | `/healthz`, `/status`, convert, report, batch, `/ui/` bundle, the server's log | `/healthz` `{"status":"ok","version":"0.1.0"}` in both; header `x-converter-engine: rules` on convert and report; `"engine":"rules"` in both batch lines; the same `x-form-sha256` with and without the model; `/status` six keys without, `model` with (name, `host: public`, `key: variable`); the bundle holds the band's text; log: `INFO: engine=rules state=UNAVAILABLE model=… host=public reason=no-model-step` and `stage=convert result=ok … engine=rules`; 0 lines with the fake password, key, host, port, path or query in the log and the form | this commit |
| engine and CLI tests after the log fix | `bash tools/gate.sh py -m pytest apps/converter/tests/shell/test_engine_visible.py apps/converter/tests/shell/test_shell_config_cli.py -q` | 75 passed | this commit |

## Negative control
On 913f787 the line `engine.HEADER: engine.engine_of(...)` was removed from `headers_for` in `app/main.py`:
`bash tools/gate.sh py -m pytest apps/converter/tests/shell/test_engine_visible.py -q` gave 5 failed, 42 passed; the
failures were `test_every_conversion_answer_carries_the_engine_header`, the three cases of
`test_the_shell_follows_a_model_step_without_being_changed` and
`test_a_configured_model_changes_no_byte_of_the_form_or_the_sidecar`. The line was put back (`git diff` empty);
nothing of the control was committed.

## Requests to lead
1. BLOCKING FOR THE IMAGE WORKFLOW (the run on this branch is expected red until it is applied).
   `tools/ci/container_check.py`, function `conversion_problems` (lines 293-294 on main a7f2cee), fails every
   converted fixture when the CLI's stderr is not empty; the brief asks for the line `ENGINE: rules` on stderr.
   `tools/ci/**` is not mine. Proposed text in place of the two lines:
   `    noise = [ln for ln in first_stderr.decode(errors="replace").splitlines() if ln.strip() and not ln.startswith("ENGINE: ")]`
   `    if noise:`
   `        problems.append(f"stderr not empty: {' | '.join(noise)[-200:]}")`
   `    if b"ENGINE: " not in first_stderr:`
   `        problems.append("no ENGINE line on stderr")`
   and in `tools/ci/tests/test_image_checks.py` lines 118-126 the second argument `b""` becomes `b"ENGINE: rules\n"`.
   If the lead prefers no change in `tools/ci`, the other way is to drop the CLI line (one `print` in
   `app/cli.py`, one test); the header, `/status`, the log and the page do not depend on it.
2. Documents (not mine), exact proposed text:
   - `docs/05-hackathon/jury-qa-formularze.md:99`: "…w produkcie nie ma żadnego modelu, klucza ani wywołania
     sieciowego. Dowodem jest kontener uruchomiony bez sieci i punkt `GET /v1/selftest`." becomes "…w produkcie
     domyślnie nie działa żaden model: bez konfiguracji nie ma klucza ani wywołania sieciowego, a wynik powstaje z
     samych reguł. Dowodem jest kontener uruchomiony bez sieci, nagłówek `X-Converter-Engine: rules` w każdej
     odpowiedzi i punkt `GET /status`." (line 101, the Russian gloss, the same way.)
   - `docs/03-plan/DECISIONS-forms-track.md` D12: "…A model step exists only as an interface that picks from an
     enumeration, switched off; no weights are shipped" becomes "…A model step is optional: `MODEL_STEP=auto` (the
     default) uses a model only when `MODEL_BASE_URL` is configured, and with nothing configured the output is
     byte-identical to the rules; the engine of every conversion is shown (`X-Converter-Engine`, `GET /status`); no
     weights are shipped".
   - D13: "`GET /v1/selftest` reports the mode and proves it" becomes "`GET /status` names the engine and whether a
     model is configured (by default none: nothing leaves the container)". D14, one line added: "Exception (owner,
     21 Nov): an open model the operator configures by `MODEL_BASE_URL` may be called by the product's model step;
     never by default, never with a key in the image."
   - `docs/02-architecture/converter-design.md:154`: "| `MODEL_STEP` | `auto` | `auto`: the model step runs when
     `MODEL_BASE_URL` is set and the step is built (WP-H1); `off`: rules only. With nothing configured nothing is
     loaded or called |", and three new rows `MODEL_BASE_URL`, `MODEL_NAME`, `MODEL_API_KEY_FILE` (or the
     variable `MODEL_API_KEY`), all empty by default. Lines 88, 135, 499, 510, 550 still name `/v1/selftest`,
     which does not exist; `GET /status` exists.
3. For WP-H1 (not built here, by the brief): the header `X-Converter-Model`, the page `GET /`, the probe, the
   state REFUSED, `meta.model` in the sidecar. H1 sets `engine.MODEL_STEP_BUILT = True`, refines
   `engine.model_state`, and emits MODEL_USED, MODEL_FALLBACK or MODEL_SKIPPED in the sidecar warnings.

## Left for the next stage
Everything of the brief is built. Main a7f2cee is merged (b5d42f4; `config.py` holds both `required_policy` and the
`model_*` fields, no conflict). Running when this was committed, results not read yet:
1. `bash tools/gate.sh fast` on the merged tree. If it was cut: run it again, log to a file, read the tail.
2. Byte proof after the merge, because main changed code under `apps/converter/app`: `git archive a7f2cee
   apps/converter/app` against `git archive <this head> apps/converter/app`, both unpacked outside the tree and
   put first on `sys.path`; the 158 items of `eval.chain.corpora` (`sets_items()`, `unseen_items(archive=<main
   checkout>/data/archive)`, `hostile_items(<dir>)` built once) and the 9 synthetic fixtures; compare SHA-256 of
   the canonical form and sidecar. The scratch script is not in git; this paragraph is its whole recipe.
Checks passed: shell tests 258 passed on 937cb2a; byte proof 79 of 79 against 9e095ab on 937cb2a; `npm run build`
and `npm test` 54 passed on 913f787; negative control on 913f787. Not yet passed on the merged tree: the fast gate,
the byte proof against a7f2cee.

## Cost notes
- core: the 5-hour limit cut the first session after 9 replies of reading; the lead saved the loose files.
