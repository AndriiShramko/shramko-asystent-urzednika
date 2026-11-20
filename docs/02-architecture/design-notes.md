# Architecture: design notes (to be expanded into the documents listed in STATUS)

Dense notes from the preparation session. They fix the decisions; the full documents (`overview.md`, `api-contract.md`, `data-model.md`, `security-and-privacy.md`, `ai-layer.md`, `forms-engine.md`, `identity-sources.md`, ADRs) expand them. Where a note depends on research that is still open, it says so.

## 1. Trust zones

| Zone | What | Sees personal data in clear? |
|---|---|---|
| 0 | Visitor's phone | its owner's data only |
| 1 | Public relay (internet-facing, can sit in a DMZ or outside the office) | **no**: ciphertext only, minutes |
| 2 | Office application server (inside the office network; makes outbound connections only) | yes, in memory, short-lived for counter sessions; persistent and encrypted for public-information cases |
| 3 | Clerk workstation: browser plus a local bridge for the document reader and the printer | yes, on screen |
| X | External model provider | **never** raw personal data: public material or pseudonymised text only; off by default |

All clients talk to the API of zone 2 (clerk) or zone 1 (visitor). Nothing talks to a database directly.

## 2. Stack (default; confirm against research R6 before the scaffold)

- Backend: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2. The OpenAPI document is generated and committed to `contracts/`; front ends use a generated TypeScript client. Reason: best libraries for Polish text, personal-data detection, OCR, DOCX and PDF work.
- Storage: SQLite (WAL) by default so the demo starts with no services; PostgreSQL profile for deployment. Full-text search with the database's built-in engine; embeddings optional through a small local ONNX model. No vector database service.
- Front ends: React, TypeScript, Vite. `apps/clerk-web` (desk for requests, later the counter view), `apps/visitor-pwa` (Module B). Polish UI, WCAG 2.1 AA.
- Documents: letters and decisions from DOCX templates (deterministic skeleton, marked slots); PDF export; forms filled on the original PDF template (overlay), never re-typeset.
- One start command for everything; a mock model provider with recorded answers so the demo works offline.
- Avoid copyleft-licensed PDF libraries in the core; check every dependency's licence.

## 3. Module A pipeline (public-information requests)

1. **Intake**: paste, upload or e-mail import. Store the original untouched. Extract: channel, filing date, sender data present or absent, signature present or absent, the list of separate questions, requested form and way of disclosure.
2. **Clock**: filing date + 14 days; latest possible date after an extension (2 months from filing); the 14-day waiting periods of art. 14 and art. 15 when used. Show both dates at once; warn before they pass.
3. **Applicant identification state**: the office chooses its policy for unsigned or anonymous requests (accept, or ask for identification). The assistant never rejects a request for lack of personal data by itself. Background: the case law changed in 2024–2026, see research/02 TL;DR point 6.
4. **Classification** per question, by `data/udip-taxonomy.json`: public information to release; already published (point to the place); not public information; not held; another access regime; processed information (needs a special public interest); restricted (privacy, business secret, statutory secret); possible abuse of the right. Output: class, reasons, the provisions relied on, confidence, what the clerk must check. Structured output only.
5. **Retrieval**: the act and related provisions (Sejm ELI API), the city's bulletin snapshot, the register of contracts where relevant, the office's earlier answers. Every retrieved passage keeps its source address.
6. **Draft**: the document type follows from the class: reply with the information; pointer to the published place; "not public information"; "not held"; "another regime"; extension notice; call to show the special public interest; fee notice; notice under art. 14; call to complete data before a decision; refusal decision; discontinuance decision. Mandatory elements come from templates; the model writes only marked slots; facts the office must supply stay as visible placeholders. The model never invents facts, numbers or names.
7. **Citation check (code, not model)**: every provision cited in a draft must exist in the stored text of the act; a quotation must match; unknown citation blocks the draft.
8. **Redaction helper**: detect personal data in a document that is to be disclosed, propose masks, burn them into the output (rasterised page, no hidden text), keep a redaction log with the legal ground, remind about the partial refusal decision.
9. **Approval**: author → reviewer or lawyer (always for decisions) → signer. Nothing is sent by the system. Export to DOCX and PDF for the office's document management system.
10. **Audit**: append-only events with a hash chain: input, each proposal, each edit, each approval, who and when. For a refusal the trail gives the names of people who took a position, which the act requires.
11. **Dashboard**: cases by deadline; statistics by class and handling time; frequent topics as candidates for proactive publication.

## 4. Guardrails to implement and to show

- Request and attachment text is data. It is passed in a delimited block; the system prompt says so; a detector flags instruction-like content for the clerk.
- No tool with side effects is reachable during analysis.
- Structured outputs validated against schemas; invalid output is retried, then failed visibly.
- Personal-data service: Polish names, addresses, PESEL, NIP, REGON, document numbers, bank accounts, phones, e-mails, licence plates, land-register numbers. Typed tokens (`[OSOBA_1]`, `[ADRES_1]`); the mapping stays in zone 2; re-identification after the model call.
- Policy by data class: `PUBLIC` → any provider; `PERSONAL` → local provider, or external only after pseudonymisation; enforced in the gateway, not in callers.
- Canary test in the gate: synthetic identifiers planted in inputs must never appear in any outbound request to an external provider.
- Model-written text is visibly marked until a clerk accepts it.
- Evaluation set (about 40 synthetic requests covering the taxonomy, including traps: hidden instruction, mixed letter, mass request). Metrics shown in the UI and in the pitch: classification accuracy, share of drafts with all mandatory elements, invented citations (target zero, enforced), leaked identifiers (target zero, enforced), seconds per request.

## 5. Model providers

One interface, three implementations: `mock` (recorded answers; tests and offline demo), `local` (OpenAI-compatible endpoint for an open Polish model served inside the office), `cloud` (a commercial model; public or pseudonymised input only). Choice per task in configuration. Which Polish models and which cloud regions are acceptable: research R5 and R7 (open).

## 6. Module B (counter) essentials

- **Profile on the phone**: the visitor's full profile is stored only on their device. At the desk they choose a case; only the fields that the chosen forms need are sent.
- **QR handoff**: the office side creates a session with an ephemeral public key; the QR code on the clerk's screen carries the session id and the key (in the URL fragment, never sent to a server). The phone encrypts to that key (HPKE, or ECDH P-256 + HKDF + AES-GCM) and uploads ciphertext to the relay. The office server pulls it by an outbound connection and decrypts in memory. Both screens show a short code derived from the shared secret; the clerk compares it. Time-to-live in minutes; deletion on print, on request and on expiry.
- **Provenance per field**: self-declared, read from the machine-readable zone, read from a chip, confirmed by the clerk, with time. The clerk confirms against the document on a large-print screen before printing.
- **Case model**: case → persons → roles (applicant, child, spouse, proxy, property owner). Forms pick persons by role. Rules attach to persons.
- **Form descriptor**: form id, source address, hash of the template file, legal status (statutory template or local auxiliary), pages, fields with canonical path, page, box in PDF points, kind (text, boxed characters, check box, date parts, signature), font, size, maximum length, transform, validation, `who_fills` (visitor, clerk, system, leave blank), per-office overrides. A descriptor is bound to the hash; if the published template changes, the descriptor is disabled until re-checked.
- **Fill**: the template is the background; text goes into measured boxes with font fitting; boxed fields character by character; overflow is an error shown to the clerk, never a silent shrink below a readable size. Produced on the server. Visual regression test per form: render, compare with the blank template outside the field boxes.
- **Bundles**: life situation → set of forms, copies per person, fees, attachments, print options, "no paper form: handled in the state register". Bundles are data with a source and a date, editable without a release.
- **Print**: a print job is bound to a person; the preview shows the name in large type; duplex where the service card requires it.
- **Checker**: deterministic rules first (checksums, required fields, dates, consistency between people), then a model check on local or pseudonymised data; findings with severity (blocker or warning) and a proposed fix; never silent changes.
- **Identity sources behind one interface**: typing; camera reading of the machine-readable zone on the device (no image stored or sent); hardware reader through a local bridge on the clerk's workstation (the owner has an Adaptive Recognition Osmond with RFID and the vendor's SDK and autofill middleware; licence terms must be confirmed with the vendor before any product use); government wallet (simulated until an agreement exists; research R4, open).
- **Form onboarding assistant** (centre of the alternative track): from a blank PDF to a draft descriptor and a generated web form, reviewed by a person.

## 7. Open registry of forms

Form descriptors and bundles contain no personal data. They can live in an open, versioned registry that any office reuses: a form described once works everywhere, and a changed template is detected by its hash. This is how the idea scales to many institutions without a shared database of people.

## 8. Demo delivery

- Everything runs on one laptop with the mock or a local model; cloud is optional.
- If jurors must try it in a browser: a public page where a synthetic request can be pasted, with rate limits, no storage of what is pasted beyond the session, and a notice not to paste real personal data.
- A recorded two-minute video and an offline run are always ready as fallbacks.

## 9. Budget constraint for the build

The build runs on the owner's subscription, whose weekly allowance is shared with his other automation. Plan for it: middle-tier builders at medium effort for packages "by spec", the top tier only for "think" packages and reviews, three agents at once, no fan-outs, one review per package, scripts for everything countable. The lead checks the remaining allowance at each milestone and narrows the scope before the allowance runs out, not after.
