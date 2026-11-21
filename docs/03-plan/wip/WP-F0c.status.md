# WP-F0c Revision 1.1 of the shared models: status

Branch: wp/F0c-models11   Stage now: acceptance (single stage, lead-owned contracts of WP-F0)

## Status
- [x] Models 1.1 in apps/converter/app/model/ (common, page, candidate, brief, meta, new ledger.py, __init__, schemas)
- [x] Four schema files regenerated from the models; five new 1.1 example files beside the untouched 1.0 examples
- [x] Tests: tests/model/test_model_rev11.py (38 tests) and two tests of test_model_contracts.py adapted to 1.1
- [x] Byte-for-byte proof against the 1.0 models of main; fast gate 416 passed with zero edits outside owned paths
- [x] Negative control recorded by breaking and restoring

## Decisions
- New keys are optional and left out while unused (None, or an empty list via `omit_empty` = pydantic `exclude_if`) / byte-for-byte rule / rules out `[]` defaults written into old documents.
- Version fields take `1` or `1.1`, default `1.1` (JSON number) / the bump asked for, old files keep `1` / rules out a string version and refusing 1.0 files.
- Placement: an element carries box, anchor or both, never neither; the page origin names the mandatory one (flow: anchor, native/ocr: box) / smallest rule that allows anchored text boxes / rules out anchor frames and signed offsets (review finding 1 extra).
- A flow page may state width and height (both or neither); only then may it carry lines, rects and pictures / anchored drawings keep page coordinates / rules out boxes without a frame.
- `Evidence` and `FieldEvidence`: quote optional when box or anchor locate the blank; `Stated` stated/ambiguous still needs one quoted record / 1.0 guarantee kept / rules out quote-less textual claims.
- Meta `evidence` value is one record (1.0) or a non-empty list (1.1); `Meta.evidence_of(id)` reads both as a list / additive / rules out a second parallel evidence map.
- Span = object `{run, start, end}`, Python string indices, end exclusive; on Candidate, Label, ChoiceOption (and Evidence); `FinderOutput.check_spans(page_model)` refuses unknown runs and spans past the text / testable without the page model in the finder file / rules out glyph boxes on spans.
- `count_coverage(finder, page_model)`: a run is assigned if named whole or if its spans cover every non-space character; partly covered runs are unassigned and their stretches go to `coverage.gaps` / honest partial coverage / rules out counting a half-read run as covered.
- Disposition `{candidate, fate, key|into+why|role|reason|decision}` uses the ledger's five fates (moved to common, re-exported by meta); exactly its fate's keys / one vocabulary for F4 and F15 / rules out free-form fates.
- `assemble_ledger(finder, dispositions, form_ids key->form id, decisions=None)` raises `LedgerError` on missing or extra candidate ids, a key without form id, a merge that leaves the finder or circles, an unlisted decision; STANDARD rows carry the brief role verbatim in `section` / F15 check / rules out role->techName mapping here.
- Applicant options `{key, party, capacity?, evidence}`; condition target `APPLICANT_SELECTOR = "applicant"` is legal only when options exist, then no matter field may use that key / additive / rules out a keyboard-person vs party split (not asked).
- Optionless CHECKBOX is one yes-or-no box; a condition on it says "true" or "false"; RADIO still needs options / testable leaf values / rules out made-up options.
- Reader facts: Run `leader` (dots|underscores|none), `region` (body|header|footer|footnote), `footnote` (same id on mark and footnote text); Table `region`; Page `pictures`, `ink`, `row_heights`, `col_widths` (>= 0) / absent means not declared / rules out readers inferring them.
- Widget `field` (shared radio field), `values` [{display, export}], `on_state`; old `options` stays / additive / rules out replacing the string list.
- `Box` is a class used only as annotation (same core schema, values stay plain tuples) so `Box.from_raw` exists; `X.safe(page, **kw)` on Run, Line, Rect, Widget returns (element|None, warnings) and never raises / reader boundary / rules out exceptions on one bad observation.
- `Consent.kind` consent|declaration, default consent, left out when consent; `Brief.mandatory_attachments` (Stated), `Brief.proposed_fee` and `Proposals.fee` (ProposedFee) apart from `fee` / no upgrade of not_found by construction / rules out a fee status changed by a proposal.
- `check_paper_evidence(brief)` returns REQUIRED_WITHOUT_EVIDENCE warnings (new code) instead of a validation error / old briefs (1.0 example field `sposob_zwrotu`) still load / rules out refusing 1.0 data.
- WarningCode gains the twelve composer remark codes (test reads `Remark("...")` in app/compose and checks the subset); MatterSection `page_title`, `hint`; Attachment `key` (unique) / WP-F5 requests 1-3.
- Schema generator strips null members from object defaults (Proposals default) / no nulls in our contracts / rules out `"fee": null` in a schema default.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| model tests | `bash tools/gate.sh py -m pytest apps/converter/tests/model -q` | 92 passed | this branch |
| schemas match models | test_schema_files_match_the_models | pass | this branch |
| 1.0 bytes unchanged | scratch script: 1.0 models of main vs 1.1 models on 4 old examples + 2 composer brief fixtures; readers' DOCX and PDF output | 6/6 identical; reader output identical except `model_version` 1 -> 1.1 | this branch |
| fast gate, zero edits in readers/compose/guard/auth | `bash tools/gate.sh fast` | 416 passed (378 before), 8 deselected | this branch |

## Negative control
Tests: element with neither box nor anchor refused; span past the text of its run refused; ledger from dispositions missing c51 refused; old 1.0 examples validate against the 1.1 schema and model. Break-and-restore on 3f2bbf3: the missing-candidate check of
`assemble_ledger` disabled -> `test_negative_control_ledger_missing_a_finder_candidate_is_refused` failed (1 failed,
37 passed); file restored from git, 38 passed. The gate's two warnings come from fastapi/jwt, not from the models.

## Requests to lead
- Composer (WP-F5 owner): make the attachment id from `Attachment.key` when present; use `MatterSection.page_title` and `hint`; accept an optionless CHECKBOX (conditions "true"/"false") and the `applicant` selector in conditions; map `Remark.code` to `Warning.code` 1:1.
- Wiring: `assemble_ledger` takes brief key -> form id; invert `ComposeResult.brief_keys` (form id -> key). STANDARD rows carry the role (`standard/...`), not a techName: if F15 wants techNames, the composer should return role -> techName.
- Readers (WP-F2a owner): switch to `Run.safe`/`Widget.safe`/`Line.safe`/`Rect.safe` and fill the 1.1 reader facts; nothing breaks if they do not.

## Cost notes
- single stage: most turns went to designing additive defaults; `exclude_if` (pydantic 2.11+) made "left out while unused" cheap.
