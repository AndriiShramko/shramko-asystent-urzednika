# WP-F-val validators and REQUIRED only where the paper says it: status

Branch: wp/F-val-validators   Stage now: 2 (B9, REQUIRED)

Worktree branch `worktree-agent-a93ecdbb74987c1c9`, cut from `main` c940d03. Lead's notes: push the package branch at
each stage end; `eval.chain` in a worktree needs `--archive C:/dev/shramko-asystent-urzednika/data/archive`, log to a
file; never commit `eval/chain/summary.json` or `last-run.jsonl`; never `--update-baseline`.

## Status
- [x] Stage 1: measuring script `apps/converter/tests/validators/count_sets.py`, counts before (159d02a)
- [x] Stage 1: root cause and fix: library `numer_pesel`; concept rows for ePUAP, e-Doręczenia, identity card; label rule in `compose/validators.py` (5755f0f, 7c67cab)
- [x] Stage 1: one test per validator, negative control, counts after, fast gate, push (this commit)
- [ ] Stage 2: REQUIRED measured per set by the basis of the brief, rule decided or note for the lead
- [ ] Stage 2: tests, counts after, every changed field named, fast gate, push

## Decisions
- Stage 1, root cause: three causes, one per layer. (a) Library: `your_data` built `numer_pesel` with no validator
  (sets 03, 08, reference 05). (b) Concept typing: `lexicon/concepts.json` had no row for ePUAP, e-Doręczenia, the
  identity card, so set 09 got none. (c) Matter path: correct, it maps concept to validator. Fixed in (a) and (b).
- One rule, in `compose/validators.py`: a typed text field whose concept or label states one of the eight values gets
  that validator; the label is read with the lexicon's own rows (one table of patterns). Rules out a second table.
- No validator when the label asks for more than one value (two kinds, a list with `,` `;` `/`, "lub/albo/oraz", a
  name, "paszport", "miejscowość"): the first pattern's validator would refuse an honest answer ("Imię i nazwisko
  członka rodziny, PESEL" got PESEL before). The gap is a remark, code `LOW_CONFIDENCE` (a new code needs `common.py`).
- Only `TEXT_FIELD` takes a validator of a value (never a date, a choice, an upload, a long text). No judged result
  changes by this: the lexicon types all eight concepts as `TEXT_FIELD`.
- The identity-card row needs "seria/numer/nr" beside "dowód osobisty": "Data wydania dowodu osobistego" stays a date.
- Not done from the analyst's memo V-1: `entity_regon=True` and `teryt_other=TERYT` by default. They add a field and
  change a dictionary of the standard sections with no cue on the paper; outside the stage's brief. For the lead.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| tests of the package | `bash tools/gate.sh py -m pytest apps/converter/tests/compose apps/converter/tests/validators -q` | 93 passed (27 new in `tests/validators`) | 7c67cab |
| fast gate | `bash tools/gate.sh fast > tmp/fast.log 2>&1` | see the row at the end of stage 1 below | |
| partner's linter on the seven results | `count_sets.py` converts through `pipeline.run` (gate inside); `test_a_synthetic_paper...` asserts `coi_lint.check(form, "strict")` has no ERROR | 7 of 7 converted, 0 validators outside the list | 7c67cab |
| `VALIDATORS=off` | `count_sets.py OUT.json --off` | 0 validators in all seven results | 7c67cab |

### Stage 1: fields per validator, before (main c940d03) and after (7c67cab)
One input per judged set (the PDF, as `tools/lead/snapshot_results.py` picks).
Command: `bash tools/gate.sh py apps/converter/tests/validators/count_sets.py OUT.json`, then `--diff BEFORE.json AFTER.json`.

| set | inputs | PESEL | NIP | REGON | ZIP_CODE | EMAIL | EPUAP | ADE | SERIAL_NUMBER_ID_CARD | REQUIRED |
|---|---|---|---|---|---|---|---|---|---|---|
| judged-02 | 50 | 0 → 0 | 1 → 1 | 0 → 0 | 3 → 3 | 1 → 1 | 0 → 0 | 0 → 0 | 0 → 0 | 5 → 5 |
| judged-03 | 36 | 0 → **1** | 0 → 0 | 0 → 0 | 2 → 2 | 1 → 1 | 0 → 0 | 0 → 0 | 0 → 0 | 2 → 2 |
| judged-04 | 39 | 0 → 0 | 0 → 0 | 0 → 0 | 2 → 2 | 1 → 1 | 0 → 0 | 0 → 0 | 0 → 0 | 7 → 7 |
| judged-06 | 69 | 0 → 0 | 1 → 1 | 0 → 0 | 3 → 3 | 1 → 1 | 0 → 0 | 0 → 0 | 0 → 0 | 23 → 23 |
| judged-07 | 45 | 0 → 0 | 0 → 0 | 0 → 0 | 2 → 2 | 1 → 1 | 0 → 0 | 0 → 0 | 0 → 0 | 11 → 11 |
| judged-08 | 87 | 0 → **1** | 1 → 1 | 0 → 0 | 5 → 5 | 2 → 2 | 0 → 0 | 0 → 0 | 0 → 0 | 36 → 36 |
| judged-09 | 111 | 0 → 0 | 1 → 1 | 0 → 0 | 3 → 3 | 1 → 1 | 0 → **2** | 0 → **2** | 0 → **2** | 62 → 62 |

Every field that changed (the whole diff): `numer_pesel` in sets 03 and 08 (+PESEL); in set 09
`skrzynka_epuap_adres_skrzynki` and `..._wnioskodawca` (+EPUAP), `edoreczenia_adres_skrzynki` and `..._wnioskodawca`
(+ADE), `seria_i_numer_dowodu_osobistego` and `..._wnioskodawca` (+SERIAL_NUMBER_ID_CARD). No validator was removed
from any of the seven results. REGON stays 0: no judged paper asks for it outside the applicant block.

## Negative control
Stage 1: `validation=("PESEL",)` removed from `your_data` in `compose/library/__init__.py` (working tree only, on
5755f0f): `tests/validators/test_validators.py::test_every_standard_field_that_states_a_value_names_its_validator`
failed, with the two snapshot tests of `test_compose_core.py` (3 failed, 90 passed). Restored with `git checkout` of
the file; 93 passed again.

## Requests to lead
- `apps/converter/app/model/common.py`, `WarningCode`: add `"VALIDATOR_NOT_WRITTEN",  # D8: a label that asks for more
  than one value gets no validator` (and `warn.VALIDATOR_NOT_WRITTEN` in `apps/review-web/src/i18n/{pl,en,es}.ts`).
  Until then the composer reports this gap as `LOW_CONFIDENCE`, because
  `tests/model/test_model_rev11.py::test_composer_remark_codes_are_warning_codes` refuses a code outside the list.
  After the code exists: in `compose/__init__.py` replace `Remark("LOW_CONFIDENCE", f"field {f.key}: no validator ...`
  by `Remark("VALIDATOR_NOT_WRITTEN", ...` and the same word in `tests/validators/test_validators.py`.

## Cost notes
- Stage 1: the fast gate ran about 25 minutes beside an archive scan; run long measurements after the gate, not with it.
