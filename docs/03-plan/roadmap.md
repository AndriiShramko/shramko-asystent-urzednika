# Roadmap

Clock times are for the event (Sat 21 – Sun 22 November 2026, local time). Gates are hard: a milestone is not started until the previous gate passes. Work-package files live in `work-packages/`; packages without a file yet are specified by the lead from the architecture documents before they start (state in [`STATUS.md`](STATUS.md)).

## Timeline

| Time | Milestone | Gate |
|---|---|---|
| before Sat 11:00 | **P. Preparation**: finish open research jobs and architecture documents listed in STATUS; machine check; model access and an offline fallback ready | STATUS has no blocking "to do" |
| Sat 11:00–12:00 | **G0. Intake**: read the full task cards of both matching tasks, fill `docs/05-hackathon/ONSITE-INTAKE.md`, map the criteria to features. The build follows the unified plan (Module A, then the bridge WP-AB1); the owner fixes the task by 18:00 | criteria table in the intake file; model provider for the product decided (see STATUS) |
| Sat 12:00–13:00 | **M0. Scaffold**: WP-00 | `tools/gate.sh fast` passes on an empty walking skeleton; one command starts API and web |
| Sat 13:00–17:30 | **M1. Core and walking skeleton**: WP-A1, WP-A2, WP-A3 in parallel | a synthetic request goes in through the API, gets a mock analysis, appears in the web desk with deadlines; audit entries exist |
| by Sat 18:00 | **HackTribe draft** (deadline 20:00): the lead prepares every field as text; the owner submits | owner confirms it is submitted |
| Sat 17:30–23:30 | **M2. The assistant**: WP-A4, WP-A5, WP-A6 | the demo request of scope-decision §7 runs end to end with a real model and with the mock; citation check blocks an invented provision; evaluation set runs |
| Sat 23:30–Sun 04:00 | **M3. Hardening and the strong moments**: WP-A7, WP-A8, WP-A9 | masking shown on screen; injection test set passes; similar-case search works on the synthetic archive; accessibility check has no critical finding |
| Sun 04:00–08:00 | **M4. The bridge and optional depth**: WP-AB1 first; then a Module B slice (WP-B1…B3) **or** depth for Module A, decided by the lead from the state of M3 and the intake | chosen items pass their acceptance lists; nothing half-built is shown |
| Sun 08:00–10:00 | **M5. Submission**: WP-DEMO; presentation PDF from the deck print mode (under 10 MB), demo video (under 2 minutes), README for jurors, static demo at urzad.flyreelstudio.eu/app/, all links checked from a clean browser | owner submits in HackTribe by 10:00 (deadline 11:00) |
| Sun 11:00–15:00 | **Pitch rehearsal**: 5-minute pitch, answers from `docs/05-hackathon/jury-qa.md`, backup video and offline demo | one timed run-through |
| Sun 15:15 | Finals (if selected) | |

## Work packages

Module A and the core (Track A, default):

| Id | Package | Depends on | Kind |
|---|---|---|---|
| WP-00 | Scaffold: monorepo, API skeleton, web skeleton, gate script, pre-commit scan, synthetic data generator (persons, requests) | none | by spec |
| WP-A1 | Case store and API: cases, documents, events (audit, append-only), deadline calculator, roles | WP-00 | by spec |
| WP-A2 | Model gateway and personal-data service: provider interface (mock, cloud, local), policy by data class, pseudonymisation and re-identification, canary test | WP-00 | think (security) |
| WP-A3 | Knowledge base: ingest the act and related provisions from the Sejm ELI API, the city's public bulletin snapshot, a synthetic archive of earlier answers; search API returning sources | WP-00 | by spec |
| WP-A4 | Analysis pipeline: extraction (sender, channel, date, questions), classification by `data/udip-taxonomy.json`, structured output, evaluation set and metrics | WP-A2, WP-A3 | think |
| WP-A5 | Draft generator: document types and mandatory elements from templates, model-written parts marked, citation checker, export to DOCX and PDF | WP-A3, WP-A4 | think (legal form) |
| WP-A6 | Clerk web desk: inbox with clocks, request view with highlights, analysis panel, draft editor, approve and export, audit view; WCAG 2.1 AA; Polish UI | WP-A1 | by spec |
| WP-A7 | Redaction helper: detect personal data in a document to disclose, propose masks, burn them in, redaction log | WP-A2 | by spec |
| WP-A8 | Similar cases, duplicate and campaign detection; dashboard of deadlines and statistics | WP-A3, WP-A6 | by spec |
| WP-A9 | Security pack: injection test set, audit hash chain check, access rules test, accessibility check, threat-model review | M2 | think (review) |
| WP-A10 | Paste-a-request public page with synthetic data and rate limits (if the jury must try it in a browser) | M2 | by spec |
| WP-AB1 | **The bridge**: the public-information request as a digitised online form with an "already published" hint; requests arrive structured (joins both matching tasks, see scope-decision §1a) | M2, WP-A3 | by spec |
| WP-DEMO | Static demo build of the desk (recorded responses in the browser) published to `site/app/`; demo video; deck numbers (`metrics.json`, `status.json`) | M2 | by spec |

Module B (Track B, or optional slice in M4):

| Id | Package | Depends on | Kind |
|---|---|---|---|
| WP-B1 | Canonical profile schema and forms engine: descriptor to filled PDF on the original template, two forms, visual regression test | WP-00 | think |
| WP-B2 | Visitor page (phone) and QR handoff with end-to-end encryption through a relay; time-to-live and delete | WP-00 | think (security) |
| WP-B3 | Clerk counter view: waiting list, large-print check against the document, bundles of forms, print | WP-B1, WP-B2 | by spec |
| WP-B4 | Identity sources: camera reading of the machine-readable zone on the device; adapter interface for a hardware reader and for a government wallet (simulated) | WP-B2 | by spec |
| WP-B5 | Form checker: deterministic rules first, model check on pseudonymised or local data, findings with severity | WP-B1, WP-A2 | think |
| WP-B6 | Form onboarding assistant: from a blank PDF to a draft descriptor and a web form (the "digitise a form" pipeline; centre of Track B) | WP-B1 | think |

Rules: three packages at once at most; "think" packages go to the top model tier and always get an independent review; "by spec" packages go to the middle tier at medium effort. Each package has one owner branch and one status file. See [`../04-orchestration/`](../04-orchestration/).

## After the event

Pilot plan, deployment requirements and maintenance are described in `docs/01-product/after-the-hackathon.md` (to do).
