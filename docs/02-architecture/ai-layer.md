# The AI layer: guardrails, model choice, speed, quality, integration, deployment

Last year's task card for an "assistant for officials" required exactly these sections in a submission. They are prepared here so that the lead can paste them into the submission form and adapt them to the real card at the 11:00 gate. Details: pipeline in [`design-notes.md`](design-notes.md) §3–§5, runtime instructions in [`prompts/`](../../prompts/), threats in [`security-and-privacy.md`](security-and-privacy.md).

## 1. Guardrails

| Guardrail | How it is enforced |
|---|---|
| The assistant never decides, sends or signs | No such action exists in the API for the model; approvals are role-checked human actions |
| No invented legal basis | Citations resolved and quotations compared by code against the stored act; failure blocks the draft |
| No invented facts | Facts only the office knows stay as visible placeholders; numbers, dates and names in a draft are compared with its inputs |
| Outside text cannot command the model | Delimited data block, fixed preamble, structured output, instruction-like text flagged |
| Personal data does not reach an external model in clear | Policy by data class inside the gateway; pseudonymisation; canary test in the gate |
| Uncertainty is shown | Confidence threshold; class "uncertain" with the two candidates; lawyer-review mark on every restrictive outcome |
| Anonymous or unsigned requests are never rejected by the system | A state "applicant not identified" and an office policy flag; both lines of case law shown |
| Model-written text is recognisable | Marked until a clerk accepts or edits it; origin of every section stored |
| Everything is reconstructible | Append-only audit trail: input, proposals, edits, approvals |

## 2. Model choice

One interface, three providers (`mock`, `local`, `cloud`), chosen per task in configuration. The default for an office is an open Polish model served inside the office.

| Option | Why | Limits |
|---|---|---|
| Open Polish model served locally (Bielik 11B v3 or PLLuM 12B; both Apache 2.0; avoid the non-commercial PLLuM variants) | Data stays in the office; no per-request fee; digital sovereignty; PLLuM is the ministry's own family of models | Needs a GPU server or runs slowly; structured output must be validated and retried by our code; quality on legal classification to be measured on the evaluation set |
| Commercial model through an EU region of a cloud platform | Highest quality for drafting; elastic | Processing agreement and transfer analysis; only pseudonymised text; availability of regions per model must be confirmed |
| Commercial model through the provider's own API | Simplest for a demo | No EU region; retention rules depend on the model; only public or pseudonymised input; not a production choice for an office without the office's decision |
| `mock` with recorded answers | Tests, offline demo, static demo site | Not a model |

Indicative cloud cost per analysed request with a cached legal block (from [`research/08`](../../research/08-claude-code-multi-agent-token-economy.md); assumed token counts, not measured): about 0.0015 USD on the small tier, 0.025 USD on the middle tier, 0.05 USD on the top tier. At 1,200 requests a year the model cost is negligible next to staff time; the real cost of a local deployment is one server.

For the build and the demo the owner must provide one of: a small amount of API credit, a local model on the laptop, or accept the mock for everything except the recorded runs. This is an open decision in [`../03-plan/STATUS.md`](../03-plan/STATUS.md).

## 3. Response time (targets to declare and to measure)

| Step | Target | Note |
|---|---|---|
| Registration and both deadline dates | under 1 second | no model |
| Extraction and classification of one request | under 20 seconds | one or two model calls; show progress |
| Search for similar cases and published information | under 2 seconds | local full-text search |
| Draft of one document | under 30 seconds | template assembly is instant; the model writes marked slots |
| Checks (citations, mandatory elements) | under 1 second | code only |

The demo shows the measured values from the evaluation run, per provider.

## 4. Quality: how we know it is good

- An evaluation set of about 40 synthetic requests covering every class of [`data/udip-taxonomy.json`](../../data/udip-taxonomy.json), with traps (hidden instruction, mixed letter, unsigned e-mail, campaign, personal data, compilation request, already published).
- Metrics per provider: letter-type accuracy, class accuracy, document-type accuracy, drafts with all mandatory elements, unresolved citations (must be 0), leaked identifiers (must be 0), flagged injection traps (must be all), seconds per request.
- The run is one command and one API call; results feed the deck (`site/deck/metrics.json`) and the desk's "quality" panel.
- Every miss is listed with a one-line reason; misses become new rules or better instructions, then the set is run again.
- What the set cannot prove (real requests of the office, the office's own templates) is stated; the first step of a pilot is a test on exported historical requests inside the office.

## 5. Integration plan

1. **Next to the document management system, not instead of it.** Step one: file import (a request exported as text or PDF) and export of the approved draft (DOCX, PDF). No change in existing systems.
2. Step two: an adapter to the system's programming interface when the office grants access (the nationwide system announces a sandbox; its public documentation was not found: see [`research/07`](../../research/07-landscape-existing-solutions-and-reuse.md)).
3. E-mail and electronic-delivery intake through adapters with the same internal contract as the file import.
4. Publication of approved answers to the public bulletin as an export the office reviews.
5. Identity provider of the office for login; roles mapped to the approval flow.

## 6. Deployment plan

| Phase | Duration | Content | Exit condition |
|---|---|---|---|
| Test on the office's data | 1–2 weeks | Exported historical requests, inside the office; local model; no connection to other systems | Accuracy and time measured on real cases; list of template differences |
| Pilot in one unit | 4–8 weeks | Daily use next to the current process; file import and export; weekly review of misses | Clerks choose to keep using it; handling time measured before and after |
| Hardening | parallel | Security review, impact assessment, accessibility audit, processing agreements, staff training | Sign-off by the data protection officer and IT |
| Roll-out and integration | after the pilot | Adapter to the document system; more units; the online request form | |

Requirements for the office: one server (a GPU if the local model is used), a browser on each workstation, no client installation.

## 7. Compliance summary

Controller, legal bases, the impact assessment, human oversight, transparency of AI-written text, records, accessibility and the classification under the AI regulation are covered control by control in [`research/05`](../../research/05-rodo-ai-act-security-requirements.md) §6. One point needs the office's attention before any pilot: the city's published privacy notice says data is not processed in an automated way; it must be reviewed with the data protection officer before an AI assistant touches real cases.
