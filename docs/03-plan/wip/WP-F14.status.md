# WP-F14 Pre-import gate, journeys, canary: status

Branch: wp/F14-gate   Stage now: core

## Status
- [x] Gate module `apps/converter/app/gate/` (G1 ... G12, `check(form, profile, journeys, *, sidecar, fill_values)`), seven journeys as data in `app/gate/journeys/standard.json`, synthetic tests: twelve negative controls each failing exactly its check (commit: see git log, "WP-F14: gate core")
- [ ] Tests on the partner's two exports (`@pytest.mark.sets`): tolerant G1 ... G10 pass, journey snapshots, canary
- [ ] Integration (lead): wire `check()` into the pipeline (500 GATE_FAILED with the check name, no form); copy `tools/coi_lint.py` and `contracts/coi/form*.schema.json` into the image (see Requests)
- [ ] Acceptance: fast gate after merging main; evidence table; negative control recorded

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

## Negative control
The twelve fixtures of `test_gate_core.py` (`CONTROLS` plus the ledger test) each break one rule of a passing synthetic form and assert that exactly that check fails.

## Requests to lead
- Image: copy `tools/coi_lint.py` to `/srv/converter/tools/coi_lint.py` and `contracts/coi/form.schema.json`, `form.tolerant.schema.json` to `/srv/converter/contracts/coi/` (both images). Without them G1 and G2 fail closed in the container. `coi_lint.PROFILES` then resolves unchanged.
- Pipeline (after merge): `report = app.gate.check(form)`; `report.raise_for_failure()` raises `GateFailed` with `.check.id`, `.check.name` and the findings: map to 500 GATE_FAILED without the form. Pass `sidecar=` and `fill_values=` when WP-F15 and WP-F17 provide them, else G11 and G12 stay not_applicable.
- Sidecar `checks` (meta.py `Checks`) can be filled from `report.get(...)`: G1 schema, G2 partner_rules, G3 grid, G6 detail evaluated, G8 detail passed/not_applicable, G7 zero_answer, G10 html. Status names differ (`passed`/`failed`/`not_applicable` vs `pass`/`fail`/`skipped`).

## Cost notes
