# WP-F0a form schema profiles, rule checker, golden list, docket: status

Branch: wp/F0a-profiles   Stage now: core (single stage)

## Status
- [x] Strict and tolerant profiles (`contracts/coi/form.schema.json`, `form.tolerant.schema.json`), `tools/coi_lint.py --profile strict|tolerant` and `check()` function
- [x] `eval/golden.json` and `eval/golden.py` (15 golden inputs, 2 expected forms, 7 judged sets with 54 inputs)
- [x] `docs/02-architecture/contradiction-docket.md` (13 rows)
- [x] Tests `apps/converter/tests/contracts/test_form_profiles.py`
- [x] Fast gate

## Decisions
- Tolerant findings: errors of the tolerant schema stay ERROR; what only strict rejects becomes `WARN departs from strict` / the tolerant profile is strictly looser, so zero errors on both exports.
- Strict now forbids unknown keys everywhere (top, flow, link, tab, wrapper, field) and requires the six D3 keys (`options`, `validation`, `readOnly`, `repeatingSectionGrid`, `states`, `tooltipMessage`) on every field; `validation` is a list only; ids UUID; option needs techName; components have an empty grid; `multiLevelTree`, `searchEnabled` admitted.
- A missing `jsonschema` now makes the linter exit 2 instead of silently skipping the schema.
- Judged set 07 delivers its JPEG as `.JPE` and has no docx and xlsx; the golden list records format `jpeg` and keeps the file name. Each reference set has one "wizualizacja" file, listed under `visualisation`, not as an input.
- The "five negative controls" are not enumerated in the documents; the tests build six: misspelled grid key, component directly on a page, section in a section, input on FINISH page, state pointing nowhere, duplicate id.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| exports pass tolerant, zero errors | `bash tools/gate.sh py tools/coi_lint.py --profile tolerant <both exports>` | 0 errors, 12 and 11 warnings | see git log |
| exports fail strict for listed reasons | same with `--profile strict` | export 1: 5 errors (3x validation `{}`, minItemRows, states); export 5: 4 errors (3 link ids, 1 option techName) | see git log |
| tests | `bash tools/gate.sh py -m pytest apps/converter/tests/contracts -q -rs` | 15 passed, 0 skipped | see git log |
| golden list | test `test_golden_list_shape_*`, `test_golden_files_exist_*` | 8 + 7 inputs, 2 expected, 7 judged sets, every file exists | see git log |

## Negative control
A form with a fourth top-level key (`meta`) fails strict: `test_negative_control_fourth_top_level_key_fails_strict`. Broken on purpose: the top-level `"additionalProperties": false` was removed from the strict schema; that test failed (1 failed, 14 passed); the line was restored and 15 passed.

## Requests to lead
- `META=inline` (J6) puts a key under the top level, which the strict profile refuses by design. When that option is built, the strict profile needs one named optional top-level key; a contract change for the lead.
- `eval/` has no `__init__.py` (namespace package works through the gate's PYTHONPATH); add one if a tool needs it.

## Cost notes
- core: reading the forensics file and the schema took the most turns; the tests passed at the first run.
