# STATUS

Lead-owned. One screen. Update on every merge, on every start or stop of a sub-agent, and before any long wait.

Last update: 2026-11-21 04:45 CET, preparation session (before the event).

## Phase

**Preparation finished (pre-event).** No application code yet. The event starts Sat 21.11.2026 at 11:00. The first job of the lead is the 11:00 gate: [`roadmap.md`](roadmap.md), row G0.

## What exists

| Item | State | Where |
|---|---|---|
| Owner requirements R1–R32 | done | `docs/00-brief/requirements.md` |
| Research R1–R10 (hackathon, law, forms catalogue and anatomy, identity, data protection and AI law, technology, landscape, orchestration, 2022 lessons, pitch) | done; each file lists what could not be verified | `research/` |
| Forms catalogue of Urząd Miasta Bydgoszczy: 275 service cards, 710 file links | done; the `fees` field is mostly empty and `online_handling` is a weak heuristic: read the card itself for those | `data/forms-catalog.json`, `.csv`, `tools/crawl_bydgoszcz_forms.py` |
| Form files themselves | being downloaded slowly on the preparing computer into a git-ignored cache; a script attaches the archive and its manifest to the release `pre-event` when the download finishes (expected in the morning of 21 November). Check: `gh release view pre-event --repo AndriiShramko/shramko-asystent-urzednika`. If the assets are missing, the catalogue links still work and `tools/publish_forms_archive.py` repeats the job | `tools/collect_forms.py`, `tools/publish_forms_archive.py` |
| Request taxonomy, 12 response document types with Polish skeletons | done; wording is a draft for the office's lawyer | `data/udip-taxonomy.json`, `data/udip-response-templates.md` |
| Canonical profile schema; descriptor example for the residence-registration form (page 1 measured) | done | `data/canonical-profile.schema.json`, `data/form-descriptor.example.json` |
| Scope decision, the unifying idea, gaps, after-the-event plan | done (re-check at the 11:00 gate) | `docs/01-product/` |
| Architecture decisions, API contract v0, security and privacy, AI layer | done | `docs/02-architecture/` |
| Roadmap with the event clock, 18 work packages, ownership table | done | `docs/03-plan/` |
| Orchestration playbook, brief template, git workflow, resume, publishing | done; corrected against official documentation (research/08) | `docs/04-orchestration/` |
| Agent definitions, project settings, wave workflow | done; `wp-wave.js` is untested (no code existed to run it on): try it on WP-00 alone first | `.claude/` |
| Runtime instructions for the product's AI steps (Polish) | starting versions | `prompts/` |
| Pitch deck (11 slides, presenter window, print mode), storyboard, demo script, jury truth table, guide for the owner | done and checked on the live site in a real browser (both windows stay in step, answer cards open); numbers and the status lists are placeholders until the build measures them; full-screen mode and a real demo video were not tested | `site/deck/`, `docs/05-hackathon/` |
| Public site | live: <https://urzad.flyreelstudio.eu> (pull-based from `site/`) | `docs/04-orchestration/deploy.md` |
| Audit of the earlier research (Russian) | done | `docs/06-audit/` |

## Not done before the event (first tasks if time allows)

1. Submission texts for HackTribe in Polish: templates are in `research/10-pitch-and-presentation.md` §3; adapt them after reading the real task card.
2. `after WP-00`: add the gate hook described in `docs/04-orchestration/lead-agent-playbook.md`.
3. Pages 2–3 of the residence-registration form descriptor and descriptors of other forms (only if Module B is built).

## Budget

The build runs on the owner's subscription; on 2026-11-21 about one third of the weekly allowance was left until the reset on 26 November. Check the remaining allowance at every milestone and narrow the scope before it runs out. Prefer middle-tier builders. Width: three sub-agents at once.

## Running now

Nothing.

## Waiting for the owner

1. **Which task to submit to** (default: Miasto Bydgoszcz, "Inteligentny asystent urzędnika"; alternative: "Cyfryzacja formularzy"). The build is the same until Saturday 18:00; the choice is fixed in the HackTribe draft by 20:00. See `docs/01-product/scope-decision.md` §1a and §5.
2. **Which model the product calls.** The owner's API key has no credit left. Options: add a few dollars of credit; run an open Polish model locally on the laptop; use recorded answers (mock) for the demo. Default without an answer: local model if the laptop can run it, otherwise mock for the hosted demo and the owner is asked once for credit.
3. Whether a second person joins (only then a second submission is possible).

## Decisions taken

| Date | Decision | Where recorded |
|---|---|---|
| 2026-11-20 | One repository; pre-event material is tagged `pre-event`; product code comes after the tag | README, NOTICE |
| 2026-11-20 | Default track: Module A (public-information assistant) for the city's task | scope-decision |
| 2026-11-20 | At most three sub-agents at once | playbook |
| 2026-11-21 | Unifying idea "from request to answer": Module A, then the bridge WP-AB1 (the request as a digitised online form), then counter work | scope-decision §1a, roadmap |
| 2026-11-21 | Public site on the owner's server is static only and updates from `site/` on push; test versions are static demo builds | deploy.md |
| 2026-11-21 | Stack: Python and FastAPI backend, React and TypeScript front ends, SQLite by default; no copyleft libraries in the core (the Polish spaCy model and PyMuPDF are excluded) | design-notes §2, research/06, research/07 |
