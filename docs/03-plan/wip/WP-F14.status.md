# WP-F14 Pre-import gate, journeys, canary: status

Branch: wp/F14-gate   Stage now: core

## Status
- [x] Gate module `apps/converter/app/gate/` (G1 ... G12, `check(form, profile, journeys, *, sidecar, fill_values)`), seven journeys as data in `app/gate/journeys/standard.json`, synthetic tests: twelve negative controls each failing exactly its check (commit 9e8139a)
- [x] Tests on the partner's two exports (`@pytest.mark.sets`): tolerant G1 ... G10 pass, journey snapshots, canary, Polska then Niemcy (commit after 9e8139a)
- [x] Merged main (00fa1fa); fast gate 488 passed; fail-closed test when the build lacks coi_lint (core stage, last commit)
- [x] Command `python -m app.gate FILE.json [--profile] [--json]` (exit 0/1/2), 3 tests, gate dir 62 passed (integration stage)
- [ ] Integration (lead): wire `check()` into the pipeline (500 GATE_FAILED with the check name, no form; today pipeline.py line 64 raises GATE_FAILED only for a composer exception); copy `tools/coi_lint.py` and `contracts/coi/form*.schema.json` into the image (see Requests)
- [ ] Not automated: compare the J5/J6 visible address fields of export 1 with the partner's visualisation document by eye (it is a picture/PDF, local only)
- [ ] Acceptance stage: re-run the fast gate on the merged result; the review

## Decisions
- G2 runs `tools/coi_lint.py` and routes each ERROR to the check that owns the rule (table `ROUTES` in structure.py) / one broken rule fails one check / rules out double counting; a change of a lint message shows in the twelve controls.
- `'x' in y` is equality in JSONata, so G5 resolves a reference only to the page title and techNames that equal it exactly, once each / coi_lint matches by substring / rules out conditions that hit by accident.
- G6 judges each condition over every option (plus unanswered) of the fields it reads: boolean always, not constant, literals are real options; single-field conditions without functions must be true for exactly the named options / intent beyond that is not knowable (a valid but wrong option passes, recorded in a test).
- G7 zero-answer: fields with a list default answer with it (the browser does); a condition that reads such a field (country preset to Polska) is counted as `decided_by_default`, not judged / both exports then pass with 11 and 13 judged / rules out the reading "Polska fields must be hidden too", which no form could meet.
- G8 "can become empty" is a rule: every page holds an unconditional section with an unconditional component (the composer's own rule) / sufficient, no search over answers / stricter than needed for complementary conditional sections, and then names the page.
- Journeys are data (`journeys/*.json`), answers as `[option name]` in `__userAnswer` (shape of `defaultValue: ["Polska"]`); a missing required field or option makes the journey `not_applicable` with a reason; expectations are techNames predicted by hand / the viewer replays the same file.
- G10: strict = our templates' allow-list through `app.compose.html.clean` (nh3) plus the export shell; tolerant = what the exports hold (span, img with data:image, pre, style, target...) / javascript:, vbscript:, data: outside a picture, events and CSS expression fail both / plain-text keys are not judged as HTML.
- G11 and G12 need inputs the form does not hold (sidecar; fill-area texts): optional keyword arguments; absent, the check is `not_applicable` with its reason / G12 findings name the place, never the value; values under 4 characters are not judged.
- A check that raises is `failed` with the exception; a non-object form fails every check / the gate never crashes and never passes what it could not read; without coi_lint or the schema files in the build G1 and G2 fail.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| each check has a fixture that fails exactly that check (12) | `bash tools/gate.sh py -m pytest apps/converter/tests/gate -q` | 12 of 12 (11 parametrised + G11 ledger) | core commit |
| our forms from both reference briefs pass strict, 7 of 7 journeys passed | same | passed | core commit |
| journey a form cannot take is not_applicable | same (`test_journey_the_form_cannot_take_is_not_applicable_never_passed`) | passed | core commit |
| both exports pass G1 ... G10 tolerant | `... pytest apps/converter/tests/gate/test_gate_sets.py -q` (sets local) | 11 passed; export 1: 29 conditions, 120 combinations; export 5: 31, 126 | sets commit |
| six journeys on both exports as snapshots, predicted by hand | same; `snapshots/reference-0{1,5}-*.json` | J1 ... J6 passed, J7 not_applicable on both (no statutory path in the exports) | sets commit |
| with no answer every conditional component is hidden | same (`test_zero_answer_hides_every_conditional_component`) | export 1: 11 judged hidden + 18 decided by the Polska default = 29; export 5: 13 + 18 = 31 | sets commit |
| a page that can become empty fails G8 | `test_fixture_fails_exactly_its_check[G8]`, `test_g8_names_the_page_that_can_become_empty` | passed | core commit |
| fast gate after merging main | `bash tools/gate.sh fast` | 488 passed, 8 deselected | merge of main 00fa1fa |
| time per form | scratch timing | about 0.2 to 0.3 s per check() on a form with about 30 conditions (jsonata-python, 2 ms per evaluation, cached) | core commit |

## Negative control
The twelve fixtures of `test_gate_core.py` (`CONTROLS` plus the ledger test) each break one rule of a passing synthetic form and assert that exactly that check fails.

## Requests to lead
- Image: copy `tools/coi_lint.py` to `/srv/converter/tools/coi_lint.py` and `contracts/coi/form.schema.json`, `form.tolerant.schema.json` to `/srv/converter/contracts/coi/` (both images). Without them G1 and G2 fail closed in the container. `coi_lint.PROFILES` then resolves unchanged.
- Pipeline (after merge): `report = app.gate.check(form)`; `report.raise_for_failure()` raises `GateFailed` with `.check.id`, `.check.name` and the findings: map to 500 GATE_FAILED without the form. Pass `sidecar=` and `fill_values=` when WP-F15 and WP-F17 provide them, else G11 and G12 stay not_applicable.
- Sidecar `checks` (meta.py `Checks`) can be filled from `report.get(...)`: G1 schema, G2 partner_rules, G3 grid, G6 detail evaluated, G8 detail passed/not_applicable, G7 zero_answer, G10 html. Status names differ (`passed`/`failed`/`not_applicable` vs `pass`/`fail`/`skipped`).

## Cost notes
- core: most turns went into reading the shape of the exports' conditions and HTML (two scratch scripts) before deciding G6, G7 and G10; a measured digest of "conditions and HTML tags per export" in the forensics file would have saved three replies.
- integration: small stage; pipeline and image wiring belong to the lead, so only a command line was added.
