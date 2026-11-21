# STATUS

Lead-owned. One screen. Update on every merge, on every start or stop of a sub-agent, and before any long wait.

Last update: 2026-11-21 09:00 CET, preparation session (before the event).

## Phase

**Preparation finished (pre-event).** No application code yet. The event starts Sat 21.11.2026 at 11:00. The first job of the lead is the 11:00 gate: [`roadmap.md`](roadmap.md), row G0.

**Primary track since the owner's decision of 21 November: B, the forms product for the task "Cyfryzacja formularzy".** Track A (the city's task) is the alternative and stays ready. See [`../01-product/scope-decision.md`](../01-product/scope-decision.md) §0. The owner wants a working two-sided product (visitor and clerk) shown live, with as little theory on slides as possible.

## What exists

| Item | State | Where |
|---|---|---|
| Owner requirements R1–R32 | done | `docs/00-brief/requirements.md` |
| Research R1–R11 (hackathon, law, forms catalogue and anatomy, identity, data protection and AI law, technology, landscape, orchestration, 2022 lessons, pitch, the forms task and its partner) | done; each file lists what could not be verified | `research/` |
| Forms catalogue of Urząd Miasta Bydgoszczy: 275 service cards, 710 file links | done; the `fees` field is mostly empty and `online_handling` is a weak heuristic: read the card itself for those | `data/forms-catalog.json`, `.csv`, `tools/crawl_bydgoszcz_forms.py` |
| Form files themselves: 676 files, 183 MB archive plus manifest | done; attached to the release `pre-event` and verified by size | release assets; `data/demo-forms.md` lists the forms chosen for the demo |
| Request taxonomy, 12 response document types with Polish skeletons (Track A) | done; wording is a draft for the office's lawyer | `data/udip-taxonomy.json`, `data/udip-response-templates.md` |
| Canonical profile schema; descriptor example for the residence-registration form (page 1 measured) | done | `data/canonical-profile.schema.json`, `data/form-descriptor.example.json` |
| Scope decision, the unifying idea, gaps, after-the-event plan | done (re-check at the 11:00 gate) | `docs/01-product/` |
| Architecture decisions, API contract v0, security and privacy, AI layer | done | `docs/02-architecture/` |
| Roadmap with the event clock for both tracks, 18 work packages, ownership table | done | `docs/03-plan/` |
| Orchestration playbook, brief template, git workflow, resume, publishing | done; corrected against official documentation (research/08) | `docs/04-orchestration/` |
| Agent definitions, project settings, wave workflow | done; `wp-wave.js` is untested (no code existed to run it on): try it on WP-00 alone first | `.claude/` |
| Runtime instructions for the product's AI steps (Polish), including form onboarding | starting versions | `prompts/` |
| Deck and site for the forms task (8 slides, two live demo slides) | done; opened on the live site in a browser (slides change, no errors except the expected missing demo videos); texts corrected after research R11; numbers and status lists are placeholders until the build measures them | `site-formularze/`, `docs/05-hackathon/presentation/storyboard-formularze.md`, `docs/05-hackathon/demo-script-formularze.md` |
| Deck and site for the city's task (11 slides) | done and checked on the live site | `site/`, `docs/05-hackathon/presentation/storyboard.md`, `docs/05-hackathon/demo-script.md` |
| Jury truth tables for both products, guide to the event for the owner | done | `docs/05-hackathon/` |
| Public sites | live: <https://formularze.flyreelstudio.eu> and <https://urzad.flyreelstudio.eu> (pull-based from `site-formularze/` and `site/`) | `docs/04-orchestration/deploy.md` |
| Audit of the earlier research (Russian) | done | `docs/06-audit/` |

## Not done before the event (first tasks if time allows)

1. Submission texts for HackTribe in Polish: templates are in `research/10-pitch-and-presentation.md` §3; rewrite them for the chosen task after reading the real task card.
2. After WP-00: add the gate hook described in `docs/04-orchestration/lead-agent-playbook.md`.
3. Pages 2–3 of the residence-registration form descriptor (needed for part two of the forms demo).
4. Work-package files of Track B are grouped in one file (`work-packages/WP-B1-B6-counter.md`); each has its goal, method and acceptance list. Split a package into its own status file when it starts.

## Budget

The build runs on the owner's subscription; on 2026-11-21 09:00 about one fifth of the weekly allowance was left until the reset on 26 November. This is the tightest constraint of the whole event. Check the remaining allowance at every milestone and narrow the scope before it runs out: for Track B the order of value is WP-B1, WP-B2, WP-B3, then WP-B6, then the rest. Prefer middle-tier builders. Width: three sub-agents at once.

## Running now

Nothing.

Notes for the presenter's laptop: if the drawings on the slides do not move, press `M` (Windows may have animation effects switched off); do not keep both decks open in one browser at the same time (they share one sync channel and can drive each other).

Points from research R11 to check at the partner's stand before building: the ministry plans a form generator for local governments on its e-services platform, and a central repository of electronic document templates already exists; present this product as the fast way from a paper form to an open description that can feed those, not as a new registry.

## Waiting for the owner

1. **Confirmation of the task after the 11:00 gate** (default: "Cyfryzacja formularzy"; alternative: the city's task). The choice is fixed in the HackTribe draft by 20:00; do it by 18:00.
2. **Which model the product calls.** The owner's API key has no credit left. Options: add a few dollars of credit; run an open Polish model locally on the laptop; use recorded answers (mock) for the demo. Default without an answer: local model if the laptop can run it, otherwise mock for the hosted demo and the owner is asked once for credit. Field recognition on blank forms works on public data, so any provider is allowed there.
3. Whether a second person joins (only then a second submission is possible).

## Decisions taken

| Date | Decision | Where recorded |
|---|---|---|
| 2026-11-20 | One repository; pre-event material is tagged `pre-event`; product code comes after the tag | README, NOTICE |
| 2026-11-20 | At most three sub-agents at once | playbook |
| 2026-11-21 | Unifying idea "from request to answer": the city's request template is digitised with the same engine (WP-AB1) | scope-decision §1a |
| 2026-11-21 | Public sites on the owner's server are static only and update from the repository on push; test versions are static demo builds | deploy.md |
| 2026-11-21 | Stack: Python and FastAPI backend, React and TypeScript front ends, SQLite by default; no copyleft libraries in the core (the Polish spaCy model and PyMuPDF are excluded) | design-notes §2, research/06, research/07 |
| 2026-11-21 | **Primary track B (forms task); demo-first pitch; second site and deck** | scope-decision §0, roadmap |
