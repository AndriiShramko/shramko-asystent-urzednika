# STATUS

Lead-owned. One screen. Update on every merge, on every start or stop of a sub-agent, and before any long wait.

Last update: 2026-11-21 11:21 CET. **The task cards are published and they change the plan: read the section "Phase" before anything else.**

## Phase

**Event running since 11:00. No application code yet. The full task cards were read at 11:10–11:25** (digests: [`../05-hackathon/intake/README.md`](../05-hackathon/intake/README.md)).

1. **The forms task is not the product we prepared.** It asks for a converter: one blank form file in (PDF, DOC, DOCX, ODS, XLSX, JPG, PNG), one JSON in the partner's structure out, as a REST service in Docker with a token check, for the official who digitises forms. Language models reachable only through an API, and any external API, MCP or SaaS, are **forbidden inside the product** (allowed for writing the code). Finalists run on new files at the defence. Ten slides, a three-minute film, the JSON files. Analysis and what survives of our work: [`../01-product/coi-replan.md`](../01-product/coi-replan.md). New track with fourteen packages and its own clock: [`work-packages/WP-F-forms-to-json.md`](work-packages/WP-F-forms-to-json.md). **Track B (counter, QR handoff, print, WP-B1…B11) is not built for this task**; its documents stay as the vision and as tools.
2. **The city's task is close to Track A as specified** (calendar of requests, similar cases, departments, draft, anonymisation; a cloud model is allowed for the prototype). Gap table: [`../05-hackathon/intake/umb-task-card.md`](../05-hackathon/intake/umb-task-card.md), last section.
3. **One project only** for a single participant (a second needs a second team leader). The owner's standing decision is the forms task. The choice is open again: "Waiting for the owner", item 1.
4. **The partner's working materials were read at 11:30** and are in `data/coi/` (the materials and reference set 1; reference set 5 and the seven judged sets wait for the owner to download them). The format is described in [`../02-architecture/coi-json-format.md`](../02-architecture/coi-json-format.md), with a schema and a rule checker that the partner's sample passes. Finding: about four fifths of a finished form are standard sections that are not on the paper; a rules-only converter is realistic. WP-F0 is mostly done.
5. **The owner does not like the look of the existing presentations** (11:11). New concept: [`../05-hackathon/presentation/concept-document-deck.md`](../05-hackathon/presentation/concept-document-deck.md). The reading version (`tools/build_pakiet.py`) and the two live decks keep their facts; they are not the submission.

**What the lead does first:** ask the owner the one question of item 1 with the recommendation; meanwhile run WP-00 (scaffold) because both tracks need it, and WP-F0 as soon as the materials are in `data/private/coi/`.

The paragraphs below describe the briefs of the morning. They remain the owner's vision; for the forms task only the parts named in coi-replan §2 are built.

**Third brief of the owner (21 November, about 09:55): "one visit, complete set".** The second half of the demo is told as "from need to signature": the need yields the whole set of forms, the data are handed over once, the clerk types nothing and sees only what needs a look. **Read [`../01-product/one-visit-package.md`](../01-product/one-visit-package.md) before planning the build** (ten minutes). Requirements R33–R43, packages WP-B7…B9, facts in `research/12`. No gate moves.

**Fourth brief (21 November, 10:29–10:33): the resident's own AI agent.** A second, official entrance for assistants (MCP and API): find the matter, get the set, hold a visit, fill digitised forms with the owner's data inside a permission approved on the phone; "the assistant fills, the person confirms". Design: [`../01-product/agent-door.md`](../01-product/agent-door.md); requirements R44–R50; package WP-B10, **optional, after the M2 gate**, third part of the demo only if it passes its acceptance list.

**Fifth brief (21 November, 10:48–10:56): the whole catalogue in advance; a short opening; the model.** Every template the office publishes gets its first pass before any clerk opens the product; a person approves each description once; the clerk only adds a new document. The whole archive was measured: 661 unique documents, 461 of them open to a first pass from geometry and text, 24 scans ([`../../research/13-forms-census-and-opening-facts.md`](../../research/13-forms-census-and-opening-facts.md)). Package: [`work-packages/WP-B11-catalogue-in-advance.md`](work-packages/WP-B11-catalogue-in-advance.md). The reading version of the presentation now opens with the idea in half a minute. The owner builds with Claude Code and wants strong models, not weak local ones: see "Waiting for the owner", item 2.

## What exists

| Item | State | Where |
|---|---|---|
| Owner requirements R1–R32 | done | `docs/00-brief/requirements.md` |
| Research R1–R11 (hackathon, law, forms catalogue and anatomy, identity, data protection and AI law, technology, landscape, orchestration, 2022 lessons, pitch, the forms task and its partner) | done; each file lists what could not be verified | `research/` |
| Forms catalogue of Urząd Miasta Bydgoszczy: 275 service cards, 710 file links | done; the `fees` field is mostly empty and `online_handling` is a weak heuristic: read the card itself for those | `data/forms-catalog.json`, `.csv`, `tools/crawl_bydgoszcz_forms.py` |
| Form files themselves: 676 files, 183 MB archive plus manifest | done; attached to the release `pre-event` and verified by size | release assets; `data/demo-forms.md` lists the forms chosen for the demo |
| Request taxonomy, 12 response document types with Polish skeletons (Track A) | done; wording is a draft for the office's lawyer | `data/udip-taxonomy.json`, `data/udip-response-templates.md` |
| Canonical profile schema; descriptor for the residence-registration form: **all three pages measured** (31 fields), overlay check passes with zero changed pixels outside the field boxes | done; check: `python tools/descriptor_overlay_check.py data/form-descriptor.example.json <template.pdf>` | `data/canonical-profile.schema.json`, `data/form-descriptor.example.json` |
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
| Third brief built in: the idea as one flow, pains table, rules of the check by exception, what is not claimed | done | `docs/01-product/one-visit-package.md`; for the owner in Russian: `docs/01-product/kak-eto-rabotaet.ru.md` |
| Research R12: the partner's announcement (open source, on-premise, LLM credits, PDF-DOCX-XLSX), the city's booking calendar, the seven-day rule, browser pre-fill, contact picker | done; four items are search excerpts only and are labelled | `research/12-one-visit-package-addendum.md` |
| Work packages WP-B7 (need to set), WP-B8 (comparison and check by exception), WP-B9 (profile start); two change requests to WP-B1 and WP-B2 | specified, not started | `docs/03-plan/work-packages/WP-B7-B9-one-visit.md` |
| The agent door: design with seven safety rules, interface of nine tools, two kinds of forms (`online`, `counter`); package WP-B10 in two parts (a: public tools and visit hold; b: permission and draft filling) | specified, not started, optional | `docs/01-product/agent-door.md`, `docs/03-plan/work-packages/WP-B10-agent-door.md` |
| Reading version of the presentation for the first judging stage (eleven pages, Polish; **page 1 is the idea in half a minute, page 2 the hook "one description, three kinds of user"**; page 7 is the agent door, marked „propozycja" until built; a two-page short version `skrot.html` with its own PDF) and its web page; the same in Russian for the owner | drafts; numbers and the "what works" page are placeholders until the build measures them; **not yet under `site-formularze/`**, see "Waiting for the owner" | `docs/05-hackathon/presentation/storyboard-pakiet.md`, `docs/05-hackathon/presentation/pakiet/` (pages), `docs/assets/deck-pakiet/` (PDF, contact sheet), generator `tools/build_pakiet.py` |
| Census of the city's whole forms archive: 661 unique documents; 461 open to a first pass from geometry and text (29 fillable PDFs, 186 vector PDFs, 246 word-processor files), 24 scans, 173 without places to fill | measured on 21 November, event time; simple rule, not approved fields | `tools/forms_census.py`, `data/forms-census.json`, `data/forms-census.csv`, `research/13-forms-census-and-opening-facts.md` |
| Package WP-B11: the whole catalogue in advance (batch first pass, life of a description `draft_geometry` → `draft_ai` → `reviewed` → `published`, review queue, catalogue view with a funnel) | specified, not started | `docs/03-plan/work-packages/WP-B11-catalogue-in-advance.md` |
| The partner's format for the forms task: description, our stricter schema, a rule checker with five negative controls; the partner's materials and reference set 1 | done on 21 November, event time; reference set 5 and the judged sets still to add | `docs/02-architecture/coi-json-format.md`, `contracts/coi/form.schema.json`, `tools/coi_lint.py`, `data/coi/` |

## Not done before the event (first tasks if time allows)

1. Submission texts for HackTribe in Polish: **drafted for the forms task** in `docs/05-hackathon/hacktribe-draft-formularze.md` (with the plan of the two-minute video); re-read them against the real task card after 11:00. For the city's task the templates are still in `research/10-pitch-and-presentation.md` §3.
2. After WP-00: add the gate hook described in `docs/04-orchestration/lead-agent-playbook.md`.
3. ~~Pages 2–3 of the residence-registration form descriptor~~ done on 21 November (see "What exists"). Still open: the descriptor of the temporary-residence form (same family, 115 cells) and the bundle's second form.
4. Work-package files of Track B are grouped in three files (`work-packages/WP-B1-B6-counter.md`, `work-packages/WP-B7-B9-one-visit.md`, `work-packages/WP-B10-agent-door.md`); each has its goal, method and acceptance list. Split a package into its own status file when it starts.
5. Apply the two change requests at the top of `WP-B7-B9-one-visit.md` when WP-B1 and WP-B2 are briefed (bundle fields; `autocomplete` tokens and the optional `intent` in the payload).
6. Build the two demo bundles from the text of the service cards (UMB55 and one of the vehicle department); `research/12` item 7 is a pointer, not a source.
7. **At the 11:00 gate, before the first product commit:** set the tag on the last preparation commit: `git tag -a pre-event-2 $(git rev-list -1 --before="2026-11-21 11:00 +0100" main) -m "end of pre-event material" && git push origin pre-event-2` (the preparing session was not allowed to push tags).
8. Rewrite the live deck's slide 4 and its demo around "od potrzeby do podpisu" (wording in `storyboard-pakiet.md`, section "Changes to the live deck"), and keep the reading version's page 10 equal to `status.json`.

## Budget

**Update 09:56:** the owner said the usage limits are no longer a problem ("тогда были проблемы с лимитами, сейчас их нету"). Check the real allowance once at the start; if it confirms, build at the planned width from 11:00 without waiting for 13:30, and use the top tier for every "think" package. The paragraph below describes the state at 09:05 and applies only if the check contradicts him.

The build runs on the owner's subscription. On 2026-11-21 at 09:05 the weekly allowance was 84 % used (reset on 26 November) and the current five-hour window was 84 % used (reset at 13:30 local time): between 11:00 and 13:30 there is room only for the intake and the scaffold; the main build starts after 13:30. **The owner allowed spending the weekly allowance to zero ("Расходуй всё до нуля", 21 November)**, so no reserve has to be kept, but the allowance itself is still the tightest constraint of the whole event. Check the remaining allowance at every milestone and narrow the scope before it runs out: for Track B the order of value is WP-B1, WP-B2, WP-B3, then WP-B6, then the rest. Prefer middle-tier builders. Width: three sub-agents at once.

## Running now

Nothing.

Notes for the presenter's laptop: if the drawings on the slides do not move, press `M` (Windows may have animation effects switched off); do not keep both decks open in one browser at the same time (they share one sync channel and can drive each other).

Points from research R11 to check at the partner's stand before building: the ministry plans a form generator for local governments on its e-services platform, and a central repository of electronic document templates already exists; present this product as the fast way from a paper form to an open description that can feed those, not as a new registry.

## Waiting for the owner

1. **Which task (one project).** Standing decision of the owner: the forms task, Track F. **Recommendation of the preparing session after reading the partner's materials: stay with it** (reasons in coi-replan §1a: most of the result comes from standard sections and rules; no model has to run; no paid key; our archive of real forms as a test set). An earlier note of 11:25 recommended the city's task; the materials changed that. The city's task remains the fallback: its card matches Track A and allows a cloud model, but a cloud model needs a paid key the owner does not have. The task is fixed in HackTribe by 20:00; do it by 18:00.
1a. **The remaining archives of the forms task:** the owner downloads archives 2 to 9 from the task's Discord channel "materiały-dodatkowe" into his Downloads folder (his browser asks where to save, so a session cannot finish the download alone); then they go to `data/coi/`. **Tokens are for the first 20 teams: ask at the partner's stand** (they are for building; nothing in the product may call a hosted model).
1b. Answered at 11:23: the owner's laptop cannot run any model. The product therefore runs on rules only (WP-F, rules of the track).
1c. **The template of the copyright-transfer agreement** (annex 1 of each task's regulations): the owner reads it before submitting. The winner transfers the economic copyrights of what was made for the task.
1d. **The look of the new presentation:** a sample of slides 1 and 10 of the document deck was sent to the owner at 11:40 (`docs/assets/deck-document/proba-wygladu.pdf`); he says yes or corrects, then WP-P1 builds the rest.
2. **Which model the product calls: decided by the owner on 21 November at 10:56; one point still open.** Decision (R54): the build runs on Claude Code; reading blank forms, which are public material, uses the strongest model available; a weak local model is not the default for that step; the partner's models or credits are welcome if the models are good, and nothing depends on them. State of the credits: the owner asked at the COI stand and was told they come "later" (10:49). Consequences for the lead: (a) the first pass over the catalogue (WP-B11) is done during the build by the agents themselves and committed as descriptor files, so the counter flow needs no model call at run time; (b) the live step "add a new form" needs one call at run time: partner credits if they arrive, otherwise ask the owner once for a few dollars of API credit, otherwise a recorded answer that the screen marks as recorded; (c) personal data never go to a cloud model: a spoken need is matched to a set by rules and the catalogue first, a model sees only text without personal data; (d) keep the `local` provider as a switch and measure it once on the residence form, because the partner announced that it rewards on-premise operation. **Still open: what "on-prem" means for the jury; the owner asks at the stand** (`docs/05-hackathon/ONSITE-INTAKE.md` §3a, question 5).
3. Whether a second person joins: only then can a second project be entered (it needs its own team leader).
4. **Whether the reading version goes live** at `formularze.flyreelstudio.eu/pakiet/` (move `docs/05-hackathon/presentation/pakiet/index.html` to `site-formularze/pakiet/` and push; the server publishes in two minutes). Default without an answer: keep it out of the public site until the build has replaced the placeholders, then publish before the final submission.
5. Answers from the stands to the questions of `docs/05-hackathon/ONSITE-INTAKE.md` §3a (COI) and §3b (clerks): they decide which pains the pitch may name as facts.

## Decisions taken

| Date | Decision | Where recorded |
|---|---|---|
| 2026-11-20 | One repository; pre-event material is tagged `pre-event`; product code comes after the tag | README, NOTICE |
| 2026-11-20 | At most three sub-agents at once | playbook |
| 2026-11-21 | Unifying idea "from request to answer": the city's request template is digitised with the same engine (WP-AB1) | scope-decision §1a |
| 2026-11-21 | Public sites on the owner's server are static only and update from the repository on push; test versions are static demo builds | deploy.md |
| 2026-11-21 | Stack: Python and FastAPI backend, React and TypeScript front ends, SQLite by default; no copyleft libraries in the core (the Polish spaCy model and PyMuPDF are excluded) | design-notes §2, research/06, research/07 |
| 2026-11-21 | **Primary track B (forms task); demo-first pitch; second site and deck** | scope-decision §0, roadmap |
| 2026-11-21 | Agents of residents get an official door; public tools carry no personal data; personal data pass only inside a one-matter permission approved on the person's phone; the agent never submits, signs or proves identity | agent-door §3, WP-B10 |
| 2026-11-21 | Everything committed before 11:00 on 21 November is pre-event material (the first tag `pre-event` is older than several preparation commits); the tag `pre-event-2` is to mark its end | NOTICE, CHANGELOG |
| 2026-11-21 | Jury texts use the partner's product name „Generator Formularzy e-Usług"; online pre-filling is never presented as new | research/12 item 11, one-visit-package §5 and §8 |
| 2026-11-21 | Second half of the demo is "one visit, complete set"; check by exception with a mandatory identity confirmation; intent before the visit without touching the city's booking system; open source and on-premise operation stated as product properties | one-visit-package, WP-B7…B9, research/12 |
| 2026-11-21 | Every template the office publishes gets its first pass in advance; a description moves `draft_geometry` → `draft_ai` → `reviewed` → `published` and only a published one prints or serves; a catalogue maintainer approves, not the counter clerk | WP-B11 |
| 2026-11-21 | Model policy (owner, 10:56): strongest model for public material such as blank forms; no cloud model for personal data; the `local` provider stays as a measured switch | requirements R54, ai-layer §2 |
| 2026-11-21 | The reading version opens with the idea in half a minute and a second page "one description, three entrances"; a two-page short version comes from the same source | storyboard-pakiet.md |
| 2026-11-21 | After the task cards: the forms task is built as Track F (converter to the partner's JSON); Track B is parked for that task; nothing in the product calls out of the container; R54 does not apply to the forms task | coi-replan, WP-F |
| 2026-11-21 | Presentations follow the "document deck" concept: the deck is an official form (or a request) that the product processes; ten slides; the criteria table pre-filled on the last one | concept-document-deck.md |
