# WP-F-val validators and REQUIRED only where the paper says it: status

Branch: wp/F-val-validators   Stage now: 2 (B9, REQUIRED), acceptance

Worktree branch `worktree-agent-a93ecdbb74987c1c9`, cut from `main` c940d03; `main` 9e095ab merged in e26d9dc (F1 patch
of `mean/_fields.py`, service fixes, new chain baseline). Lead's notes: push the package branch at each stage end;
`eval.chain` in a worktree needs `--archive C:/dev/shramko-asystent-urzednika/data/archive`, log to a file; never
commit `eval/chain/summary.json` or `last-run.jsonl`; never `--update-baseline`.

## Status
- [x] Stage 1: measuring script `apps/converter/tests/validators/count_sets.py`, counts before (159d02a)
- [x] Stage 1: root cause and fix: library `numer_pesel`; concept rows for ePUAP, e-Doręczenia, identity card; label rule in `compose/validators.py` (5755f0f, 7c67cab)
- [x] Stage 1: one test per validator, negative control, counts after, fast gate green on 7c67cab (787bb0c); pushed with 768a936
- [x] Stage 2: REQUIRED measured per set by the basis of the brief (table below), on the merged tree e26d9dc
- [x] Stage 2: rule 1 (inferred REQUIRED yields to the paper's optional or conditional words) and the policy switch in the composer, 14 tests (c5b20a9)
- [x] Stage 2: counts after, every changed field named, negative control (this commit)
- [~] Stage 2: fast gate on c5b20a9 and the push: see the last rows of "Evidence"; if they are empty, run `bash tools/gate.sh fast > tmp/fast.log 2>&1` and push
- [ ] Not started: `eval.chain --compare` on this branch (see "Not verified")

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
- Stage 2, rule 1 (on by default, `compose/required.py`): an *inferred* REQUIRED is not written when the paper's own
  words make the field optional or conditional: "nieobowiązkow/opcjonaln/fakultatywn" in the hint, the label or the
  section title; "jeśli/jeżeli/o ile/w przypadku" in the hint or at the start of the label. Each case is a remark
  `REQUIRED_INFERRED` naming the field and the words. Rules out: touching a REQUIRED the paper marks (basis paper,
  substance) or an upload of the attachment list; guessing from a conditional word in the middle of a label.
- Stage 2, rule 2 (policy, default unchanged): `ComposeOptions.required_policy` is `"inferred"` (today's behaviour,
  design 6.4.3) or `"paper"` (no inferred REQUIRED at all, one remark with the count). The default stays "inferred"
  because the reading is not clear: see the note. Rules out a silent change of 133 fields of the seven results.
- The rule lives in the composer, not in `app/mean` (not my path): the brief still says `required: true, inferred`
  for a field whose REQUIRED the composer does not write. `ComposeResult.required_dropped` lists those brief keys.

## Note for the lead: is "REQUIRED_INFERRED" conformant? (the reading is not clear; behaviour kept)
1. `coi-json-format.md` section 10 item 2 (line 157): "We write REQUIRED where the paper or the standard says so and
   report the rest as optional." Read literally, an inferred REQUIRED is against it.
2. `converter-design.md` 6.4.3 (line 403): "required when the paper marks it or when the field is the substance of the
   request; optional when a footnote, a bracket or the standard says so; everything else is REQUIRED_INFERRED in the
   sidecar". This is what the code does. D8 says only "where the paper or the standard supports them".
3. Measured on the seven judged PDFs (e26d9dc): 146 REQUIRED = 4 paper + 1 substance + 8 uploads of the attachment
   list + 133 inferred. The partner's two exports carry 0 REQUIRED (the analyst's memo; not re-measured here).
4. With the policy "paper" the seven results would carry 13 REQUIRED (0, 0, 1, 6, 3, 0, 3) instead of 142.
5. Risk of "paper": a jury that expects obligatory fields sees almost none. Risk of "inferred": the format document
   promises something else, and 133 fields are refused empty although the paper is silent.
6. Not decided here. Both readings are one option apart: the proposed service switch is in "Requests to lead" (1).
7. Whatever the choice, either `coi-json-format.md` line 157 or `converter-design.md` line 403 needs one sentence
   changed so the two documents agree (not my paths).
8. The analyst's memo also says the habit `required` fires on "nie jest wymagany" (`wymagan` has no guard): not
   verified here, it sits in `app/mean`.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| tests of the package, stage 1 | `bash tools/gate.sh py -m pytest apps/converter/tests/compose apps/converter/tests/validators -q` | 93 passed (27 new in `tests/validators`) | 7c67cab |
| fast gate, stage 1 | `bash tools/gate.sh fast > tmp/fast1.log 2>&1` | 808 passed, 3 skipped; chain tests 21 passed; "gate: fast PASSED on 7c67cab" | 7c67cab |
| `VALIDATORS=off` | `count_sets.py OUT.json --off` | 0 validators in all seven results | 7c67cab |
| tests of the package, stage 2 | same command | 107 passed (41 in `tests/validators`: 27 validators, 14 REQUIRED) | c5b20a9 |
| partner's linter and gate on the seven results | `count_sets.py` converts through `pipeline.run` (schema, `coi_lint`, conditions inside); `test_a_synthetic_paper...` asserts `coi_lint.check(form, "strict")` has no ERROR | 7 of 7 converted under both policies, 0 validators outside the list | c5b20a9 |
| fast gate, stage 2 | `bash tools/gate.sh fast > tmp/fast3.log 2>&1` | (filled in by the next commit) | c5b20a9 |

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

### Stage 2: REQUIRED per judged set by the basis of the brief, before (e26d9dc) and after (c5b20a9)
Same inputs and command; `--paper` runs the policy "paper" (not reachable through the service yet).
Basis: paper / substance / inferred / upload of the attachment list. The validators of stage 1 are unchanged by stage 2.

| set | REQUIRED before | basis before | REQUIRED after (default) | basis after | REQUIRED with policy "paper" |
|---|---|---|---|---|---|
| judged-02 | 5 | 0/0/5/0 | 5 | 0/0/5/0 | 0 |
| judged-03 | 2 | 0/0/2/0 | 2 | 0/0/2/0 | 0 |
| judged-04 | 7 | 1/0/6/0 | 7 | 1/0/6/0 | 1 |
| judged-06 | 23 | 1/0/17/5 | 23 | 1/0/17/5 | 6 |
| judged-07 | 11 | 2/0/8/1 | **10** | 2/0/7/1 | 3 |
| judged-08 | 36 | 0/0/36/0 | 36 | 0/0/36/0 | 0 |
| judged-09 | 62 | 0/1/59/2 | **59** | 0/1/56/2 | 3 |
| total | 146 | 4/1/133/8 | 142 | 4/1/129/8 | 13 |

Every field of the seven judged results whose REQUIRED changes (the whole diff, 4 fields, all lose an inferred REQUIRED):
- judged-07 `data_szczepienia` ("Data szczepienia", hint of the paper "w przypadku jego braku");
- judged-09 `adres_do_korespondencji`, `adres_do_korespondencji_dane_sportowca`, `adres_do_korespondencji_dane_trenera`
  ("Adres do korespondencji", hint of the paper "jeśli różni się od adresu zameldowania").
Looked at and deliberately unchanged: judged-04 "Imię i nazwisko – wnioskodawca, w przypadku innej osoby ..." (the words
stand in the middle of the label), judged-08 "W zarządzie lub użytkowaniu" (hint "należy podać jaki ...").

## Negative control
Stage 1: `validation=("PESEL",)` removed from `your_data` in `compose/library/__init__.py` (working tree only, on
5755f0f): `tests/validators/test_validators.py::test_every_standard_field_that_states_a_value_names_its_validator`
failed, with the two snapshot tests of `test_compose_core.py` (3 failed, 90 passed). Restored with `git checkout` of
the file; 93 passed again.
Stage 2: in `compose/required.py` the line `m = CONDITIONAL.search(hint or "")` replaced by `m = None` (working tree
only, on c5b20a9): `tests/validators/test_required.py::test_an_inferred_required_yields_to_an_optional_or_conditional_mark_of_the_paper`
failed, with three more tests of the file (4 failed, 103 passed). Restored with `git checkout`; 107 passed.

## Not verified
- `eval.chain --compare` was not run on this branch: one interrupted fast gate cost the time. The fast gate holds the
  chain's own tests; the archive and sets run is the lead's to repeat after the merge.
- The other formats of the sets were looked at for stage 1 before the fix only (the PDF, DOC, DOCX, ODS and XLSX
  files of all nine sets, none failed to convert; images not run); the after tables are the seven PDFs.
- The archive: 189 of its files were scanned once before the fix to find label shapes (lists, alternatives, hints
  with "jeśli", "o ile"); no before/after count on the archive.
- A fast-gate run that overlapped the merge of `main` and my edits (tmp/fast2.log) failed one chain test on a mixed
  tree; it is not evidence either way and is replaced by the run on c5b20a9.

## Requests to lead
1. Service switch for the policy, `apps/converter/app/config.py` (three lines): field `required_policy: str = "inferred"`
   beside `validators`; in `choices` add `"required_policy": ("inferred", "paper"),`; in `compose_options` add
   `required_policy=s.required_policy,`. The variable is then `REQUIRED_POLICY`. The default is the lead's decision
   (see the note above).
2. `apps/converter/app/pipeline.py`, the line that copies `brief.warnings` into the sidecar: skip the brief's stale
   warning for a field whose REQUIRED the composer did not write:
   `... for w in (*finder.warnings, *brief.warnings) if not (w.code == "REQUIRED_INFERRED" and w.field in composed.required_dropped)]`.
   Until then the sidecar of sets 07 and 09 holds both the brief's "marked required by our rule" and the composer's
   "REQUIRED is not written" for the four fields above.
3. `apps/converter/app/model/common.py`, `WarningCode`: add `"VALIDATOR_NOT_WRITTEN",  # D8: a label that asks for more
   than one value gets no validator` (and `warn.VALIDATOR_NOT_WRITTEN` in `apps/review-web/src/i18n/{pl,en,es}.ts`).
   Until then the composer reports this gap as `LOW_CONFIDENCE`, because
   `tests/model/test_model_rev11.py::test_composer_remark_codes_are_warning_codes` refuses a code outside the list.
4. `results/` are not refreshed here (the lead's snapshot): after the merge sets 03, 07, 08, 09 change.
5. Decision wanted on the analyst's memo V-1 (REGON in "Dane podmiotu" and `TERYT_DOWODOWY` for the other person by
   default): not done, it changes the standard sections without a cue on the paper.

## Cost notes
- Stage 1: the fast gate ran about 25 minutes beside an archive scan; run long measurements after the gate, not with it.
- Stage 2: never merge or edit while a gate runs: the run on a moving tree failed one test and had to be repeated.
