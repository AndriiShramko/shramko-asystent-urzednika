# WP-F0q The gate behind the service and inside the image: status

Branch: wp/F20-c-gate-image   Stage now: integration (lead-owned)

## Status
- [x] Pipeline: `gate.check(form)` after composing; a failed check is 500 `GATE_FAILED` (id, name, first five findings; quoted values stripped, so no paper content), no form in the body; the command line exits 2, prints the problem on stderr, writes no file. Sidecar `checks`: list of `{id, name, status[, reason]}` for G1 ... G12.
- [x] Image: both targets copy `tools/coi_lint.py` to `/srv/converter/tools/` and the two form schemas to `/srv/converter/contracts/coi/` (where `coi_lint.CONTRACTS` resolves from `__file__`). `.dockerignore` needed no change (tools and contracts are not excluded).
- [x] Container check `check_gate_inside` in tools/ci/container_check.py: runs the pipeline inside the hardened container on a synthetic PDF; G1 and G2 must be `passed`.
- [x] Tests (tests/pipeline: 18 passed; tools/ci/tests: 46 passed).
- [x] CI run on code commit 0d19c3f: actions/runs/44913958216, image (core), image (plus) and native all success; the container check ran the new row inside both images. `bash tools/gate.sh fast`: 496 passed, 8 deselected.

## Decisions
- The detail of GATE_FAILED holds the check id and name and the findings as place plus rule text, with quoted values replaced by `'...'` / a jsonschema message echoes the offending value; the answer must not carry content of the file.
- Sidecar `checks` is a flat list of all twelve ids, not the `meta.py` `Checks` shape / the interim sidecar is not a `Meta` yet; the mapping to `Meta.checks` belongs to the real pipeline.
- G11 and G12 stay `not_applicable` until WP-F15 and WP-F17 hand over sidecar and fill values.
- The test breaks a techName (61 characters): G1 (schema) fires first, G3 would too.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| gate cost per form | scratch timing of `gate.check` on a converted one-page PDF form | about 0.26 s per form (journeys on) | working tree |
| refusal 500 GATE_FAILED, CLI no file | `bash tools/gate.sh py -m pytest apps/converter/tests/pipeline -q` | 18 passed | working tree |
| nine sets answer 200 | same with `-m sets` | 2 passed (PDF and DOCX of all sets, linter clean, titles) | working tree |
| container check logic | `bash tools/gate.sh py -m pytest tools/ci/tests -q` | 46 passed | working tree |

## Negative control
Line `if not report.passed:` in pipeline.py replaced by `if False and ...`: the HTTP refusal test and the command-line refusal test failed (2 failed, 16 passed); restored, 18 passed.

## Requests to lead
- none.

## Cost notes
- integration: the shell refuses multi-line commands in a worktree, so scripts went through the file tool; heredoc-free edits cost two extra replies.
