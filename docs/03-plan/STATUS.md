# STATUS

Lead-owned. One screen. Update on every merge, on every start or stop of a sub-agent, and before any long wait.

Last update: 2026-11-20 23:10 CET, preparation session (before the event).

## Phase

**Preparation (pre-event).** No application code yet. The event starts Sat 21.11.2026 at 11:00.

## Preparation checklist

| Item | State | Where |
|---|---|---|
| Owner requirements R1–R32 | done | `docs/00-brief/requirements.md` |
| Lessons from the 2022 prototype | done | `research/09-lessons-from-2022-prototype.md` |
| R1 hackathon rules, judging, 2025 winners, jury questions | done | `research/01-hacknation-2026-task-rules-jury.md` |
| R2 UDIP law, decision tree, taxonomy, response catalogue | report done; `data/udip-taxonomy.json` and `data/udip-response-templates.md` **not written yet** | `research/02-udip-law-process-taxonomy.md`, job `research/_jobs/R2-udip.md` |
| R3 forms catalogue of Urząd Miasta Bydgoszczy | data done (`data/forms-catalog.json`, `.csv`), **report not written yet** | job `research/_jobs/R3-forms-catalog.md` |
| R3b form anatomy, canonical profile schema, descriptor example | **to do** | job `research/_jobs/R3b-form-anatomy.md` |
| R4 mObywatel, identity, once-only | **to do** | job `research/_jobs/R4-mobywatel.md` |
| R5 data protection, AI Act, security duties, model providers | **to do** | job `research/_jobs/R5-law-rodo-ai.md` |
| R6 technology stack (PDF, MRZ, QR handoff, reader, stack) | **to do** | job `research/_jobs/R6-tech.md` |
| R7 landscape and reusable components | **to do** | job `research/_jobs/R7-landscape.md` |
| R8 multi-agent and token-economy playbook check | **to do** | job `research/_jobs/R8-orchestration.md` |
| Scope decision | done (re-check at the 11:00 gate) | `docs/01-product/scope-decision.md` |
| Gaps and additions | done | `docs/01-product/gaps-and-additions.md` |
| Orchestration playbook, brief template, git workflow, resume | done | `docs/04-orchestration/` |
| Onsite intake procedure | done | `docs/05-hackathon/ONSITE-INTAKE.md` |
| Roadmap with event clock | done (work-package files: to do) | `docs/03-plan/roadmap.md` |
| Architecture documents, API contract | **to do** (after R3b, R5, R6) | `docs/02-architecture/` |
| Work-package files | **to do** | `docs/03-plan/work-packages/` |
| Audit of the earlier research | **to do** (verdicts already inside R1 and R2) | `docs/06-audit/` |
| Jury questions, demo script, pitch, Polish README | **to do** | `docs/05-hackathon/`, `README.pl.md` |

How to run a research job: start one web-research sub-agent with the whole text of the job file as its prompt. Each job writes its own files and returns a short summary. Three at a time at most. A job whose output file already exists continues it instead of starting over.

## Running now

Nothing.

## Waiting for the owner

1. Choice of the task at the 11:00 gate (default: Miasto Bydgoszcz, "Inteligentny asystent urzędnika"). See `docs/01-product/scope-decision.md` §5.

## Decisions taken

| Date | Decision | Where recorded |
|---|---|---|
| 2026-11-20 | One repository; pre-event material is tagged `pre-event`; product code comes after the tag | README, NOTICE |
| 2026-11-20 | Default track: Module A (UDIP assistant) for the Miasto Bydgoszcz task; Module B is a thin slice and a roadmap | scope-decision |
| 2026-11-20 | At most three sub-agents at once | playbook |
