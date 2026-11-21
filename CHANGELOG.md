# Changelog

## 0.4.0 — 2026-11-21 (during the event; the full task cards)

- Digests of both task cards and of the task regulations with sources: `docs/05-hackathon/intake/`.
- The forms task is a converter from a form file to the partner's JSON: analysis, the owner's ideas placed against the card, thirteen unstated pains with answers, model policy, risks, questions for mentors (`docs/01-product/coi-replan.md`).
- Track F: fourteen work packages with acceptance lists and a clock (`docs/03-plan/work-packages/WP-F-forms-to-json.md`). Track B is parked for that task.
- Fit of the city's card with Track A, gap by gap.
- The partner's materials read: description of their JSON format, the standard sections, the ten questions a converter must answer about a paper form, eight contradictions in the materials (`docs/02-architecture/coi-json-format.md`); our stricter schema and `tools/coi_lint.py` with negative controls; the materials and reference set 1 in `data/coi/`.
- Requirements R55–R58. New presentation concept "the deck is an official document that the product processes" (`docs/05-hackathon/presentation/concept-document-deck.md`).

## 0.3.0 — 2026-11-21 (during the event, after 11:00; the owner's fifth brief)

- Requirements R51–R54: the system does the first pass on every document; all published templates are digitised in advance and a clerk only adds new ones; the presentation opens with the idea in half a minute and a large-scale hook; model policy (Claude Code for the build, a strong model for public material, no cloud model for personal data).
- Census of the whole forms archive of the city: `tools/forms_census.py`, `data/forms-census.json`, `data/forms-census.csv`. 661 unique documents; 461 open to a first pass from geometry and text; 24 scans.
- Research R13: the census with its limits, the French precedent of an official interface for AI assistants (verified on the platform's page), the national regulation behind the residence template, the number of communes.
- Work package WP-B11 "the whole catalogue in advance": batch first pass, life of a description, review queue, catalogue view.
- Reading version of the presentation rebuilt: page 1 is the idea in half a minute, page 2 "one description, three entrances"; a two-page short version with its own PDF.

## 0.2.0 — 2026-11-21 (pre-event, the owner's third brief)

- Requirements R33–R43: "one visit, complete set" (data kept in advance, the whole package of forms from one stated need, check by exception, comparison with the document, intent known from the booking, first entry from saved browser data, mObywatel as the home of the profile, a reading presentation with a web page).
- The idea as one flow with pains, rules and limits: `docs/01-product/one-visit-package.md`; the same for the owner in Russian: `docs/01-product/kak-eto-rabotaet.ru.md`.
- Research R12: the partner's announcement of the forms task (open source, on-premise, LLM credits, PDF-DOCX-XLSX), the city's online booking, the seven-day rule for incomplete applications, browser pre-fill and the contact picker.
- Work packages WP-B7 (need to set), WP-B8 (comparison with the document, check by exception), WP-B9 (profile start); change requests to WP-B1 and WP-B2.
- Reading version of the presentation for the first judging stage: storyboard of ten pages, the page in Polish and a longer one in Russian for the owner, a PDF.
- Questions for the partner's stand and for clerks in `docs/05-hackathon/ONSITE-INTAKE.md`.
- The descriptor of the residence-registration form covers all three pages (31 fields); `tools/descriptor_overlay_check.py` verifies a descriptor against its template (hash, no change outside the field boxes, ink in every filled field).
- HackTribe texts for the forms task and the plan of the two-minute video: `docs/05-hackathon/hacktribe-draft-formularze.md`.
- Requirements R44–R50 (fourth brief): an official door for residents' AI agents. Design `docs/01-product/agent-door.md`, package WP-B10, research items on official agent interfaces and on the protocol, page 7 of the reading version.
- End of the material prepared before the coding start: the last commit dated before 11:00 on 21 November 2026; the lead marks it with the tag `pre-event-2` (the preparing session could not push tags).

## 0.1.0 — 2026-11-21 (pre-event brief, tag `pre-event`)

- Owner requirements R1–R32, scope decision, gaps and additions.
- Research: HackNation 2026 rules, judging and last year's winners; access-to-public-information law and process; lessons from the 2022 prototype. Further research jobs are listed in `research/_jobs/` with their state in `docs/03-plan/STATUS.md`.
- Machine-readable catalogue of service cards and forms of Urząd Miasta Bydgoszczy with a re-runnable crawler.
- Orchestration: lead-agent playbook, sub-agent brief template, git workflow for parallel agents, resume protocol.
- Onsite intake procedure for material handed out at the hackathon.
- Research R3–R10: forms catalogue report and form anatomy, mObywatel and once-only, data protection and the AI regulation, technology, landscape, multi-agent orchestration, pitching. Request taxonomy and Polish response skeletons, canonical profile schema, a measured form descriptor.
- Architecture: design notes, API contract v0, security and privacy with a threat table, the AI layer. Eighteen work packages with acceptance lists and an ownership table.
- Agent definitions, project settings and a wave workflow in `.claude/`; runtime instructions for the product in `prompts/`.
- Public site https://urzad.flyreelstudio.eu with the animated pitch deck (presenter window, print mode); storyboard, demo script, jury truth table, a guide to the event for the owner.
- Point-by-point check of an earlier research draft (Russian).
