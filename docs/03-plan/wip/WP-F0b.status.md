# WP-F0b Data contracts and shared models: status

Branch: wp/F0b-models   Stage now: acceptance (single stage)

## Status
- [x] Models in apps/converter/app/model/: common, page, candidate, brief, form, meta, schemas, __init__
- [x] Four schema files written from the models (`python -m app.model.schemas`; `--check` in a test)
- [x] Four examples in contracts/coi/examples/, taken from design 5.1-5.4 and adapted to the decisions below
- [x] Tests in apps/converter/tests/model/ (54 pass locally, sets present), negative controls as tests
- [ ] Negative control recorded by breaking and restoring (next commit)
- [ ] Fast gate after merging main

## Decisions
- Our contracts never write null; absent means none, explicit null refused / one rule, non-nullable schemas / rules out `"group": null` of design 5.2 (left out instead).
- Schemas are generated from the models and committed; a test fails on drift / one source of truth / rules out hand edits of the four files.
- Every Stated value (brief and meta receipts, legal basis) is {status, value, evidence[]}; design's bare `quote`/`quotes` moved into evidence / one shape for F4, F15, F9 / rules out per-field ad hoc shapes.
- `ambiguous` needs at least one evidence entry, not two / the meta example of design 5.4 has one quote / rules out enforcing "two competing quotes".
- Element placement: run, table, cell, widget, candidate carry exactly one of box|anchor; flow pages use anchors only, native/ocr boxes only; lines and rects always boxes and absent in flow / testable rule / rules out mixed pages.
- Page model has `model_version`, page `name` (sheet) and `hidden`, cell `borders` (t r b l), widget `options`, document `warnings` / F2b sheets and hidden sheets / rules out readers adding keys of their own.
- OCR runs are not forced below conf 1 (design says they are) / a perfect OCR word would crash a reader / rules out a model-level check of it.
- Groups are candidates of kind choice_group with options {text, runs, mark, blank}; members point back via `group`; no separate groups list / F3 "group of three, two with a blank" / rules out a second group structure.
- Finder output carries `order` (run ids in reading order), `sections` (headings with number and parent) and `roles` (run id -> role) with an added role `body` for ordinary text / every run gets a place (7.4) / rules out unlabelled body text.
- Candidate adds `runs`, `lines` (line_block), `mask` (printed separators), `widget`; a comb must state `cells` / F3 combs with hyphens / rules out one field per box.
- Brief fields: `required` needs `required_basis` paper|substance|inferred / F4 "every REQUIRED has evidence or REQUIRED_INFERRED" / rules out unexplained required flags.
- Conditions in the brief are a tree {field,is} | any_of | all_of | not; every leaf names an existing key and, if the field has options, one of them / design 6.7 / rules out free-text conditions.
- Ledger closes strictly: blanks_found = sum of five fates = number of rows, and counts equal rows by fate; fifth fate is AWAITING_DECISION (needs `decision`) / F15 "deleting the fate of one candidate fails" / design 5.4 example shrunk to 4 consistent rows.
- `resources` is the only non-deterministic part of meta; `Meta.to_json_bytes()` leaves it out by default (`deterministic=False` keeps it) / byte-identical runs / rules out timing in the compared bytes.
- Form: one model, two readings via validation context: strict by default; `Form.from_partner_export` relaxes exactly: non-UUID ids, option without techName, `validation: {}` (read as []), `minItemRows`, missing `states`, D4/D7 checks / exports load losslessly / rules out other unknown keys in either reading.
- Form serialisation follows the exports' key order (id, type, techName, title, description, dictionaryName, options, multiLevelTree, validation, searchEnabled, readOnly, repeatingSectionGrid, defaultValue, defaultValueType, consentSectionConfig, states, questionOrder, tooltipMessage) / measured on both exports / rules out alphabetical order.
- Helpers lay out the grid: section rows = components + 1 (28 of 34 sections in the exports), component y = questionOrder = index, section y continues; empty section description is the empty HTML document / D4 / composer may pass `rows`.
- Strict form also refuses dictionaryName, multiLevelTree, searchEnabled outside SELECT and consentSectionConfig outside CONSENT_SECTION / both exports / rules out stray optional keys.
- Format names content: `jpeg` covers .jpg and .jpeg / one value per content kind / rules out "jpg".

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| Examples validate against schema and model; round trip lossless; schemas match models | `bash tools/gate.sh py -m pytest apps/converter/tests/model -q` | 54 passed | see Status |
| Both exports load tolerant and dump with no component lost (types, techNames, full equality modulo 2 normalisations) | same, `@pytest.mark.sets` | 3 passed (sets present) | see Status |

## Negative control
Tests: run with neither box nor anchor refused; component with unknown key refused (strict and tolerant); meta whose ledger does not close refused; each example with an extra top-level key fails its schema and model; a fourth top-level key of the form refused.

## Requests to lead
- contracts/coi/form.schema.json (F0a) and this model must agree: the model refuses `minItemRows` in strict reading and accepts `multiLevelTree`, `searchEnabled` only on SELECT. If F0a's strict profile differs, tell me which one wins.
- The design's examples (5.1-5.4) differ from the contracts in the decisions above (no nulls, unified Stated, consistent ledger). Design section 5 could point to contracts/coi/examples/ as the binding shape.

## Cost notes
- F0b: most turns went into measuring the exports' key order and quirks; a one-page "export facts" table (key order, rows rule) in the forensics file would save that.
