# Owner requirements (R1–R32)

This is the complete list of what the project owner asked for, extracted from his spoken brief (two messages, 20 November 2026, originally in Russian). Every requirement has an id that the rest of the repository refers to. "Where" points to the document that answers it. Nothing here is optional unless the scope decision ([`docs/01-product/scope-decision.md`](../01-product/scope-decision.md)) says so.

Vocabulary used by the owner: *wniosek* = application form or request filed in a Polish office; *urzędnik* = clerk, the office worker at the counter; *urząd* = public office (here: Urząd Miasta Bydgoszczy, the city hall); *UDIP* = the Polish Act on Access to Public Information; *mObywatel* = the Polish government's mobile app with digital documents.

## A. The hackathon challenge (verbatim, Miasto Bydgoszcz)

> Inteligentny asystent urzędnika. Jak usprawnić obsługę wniosków o dostęp do informacji publicznej i odciążyć urzędników od powtarzalnych zadań? Wyzwanie polega na stworzeniu inteligentnego i bezpiecznego asystenta, który wesprze pracowników urzędu w analizie wniosków i przygotowywaniu odpowiedzi. Celem jest skrócenie czasu obsługi spraw i usprawnienie codziennej pracy administracji.

English gloss: an intelligent and secure assistant that supports office staff in analysing access-to-public-information requests and preparing answers; the goal is shorter handling time and easier daily work.

## B. Product requirements

| Id | Requirement | Where |
|---|---|---|
| R1 | Find out which forms people fill in again and again in the office, online and on paper; collect all templates. | [`research/03-forms-catalog-bydgoszcz.md`](../../research/03-forms-catalog-bydgoszcz.md), [`data/forms-catalog.json`](../../data/forms-catalog.json) |
| R2 | Two applications. (1) A web page the visitor opens on their own phone, enters their data, and the data goes straight to the clerk. (2) The clerk's application: sees who has filled in their data, picks the forms, the system fills them and prints them; the visitor only signs. | [`docs/02-architecture/design-notes.md`](../02-architecture/design-notes.md) §1, §6 |
| R3 | The visitor may say which form they need, or photograph their document, check the recognised data and send it. | [`docs/02-architecture/design-notes.md`](../02-architecture/design-notes.md) §6, [`research/04`](../../research/04-mobywatel-identity-once-only.md), [`research/06`](../../research/06-tech-stack-pdf-ocr-qr-scanner.md) |
| R4 | Data is entered once and reused on every form: names, addresses, relatives, children and so on. | [`data/canonical-profile.schema.json`](../../data/canonical-profile.schema.json), [`research/03b`](../../research/03b-form-anatomy-and-canonical-profile.md) |
| R5 | The visitor can enter data at home or in the corridor before the visit, including data that may be needed later, not only what one chosen form needs. | [`security-and-privacy.md`](../02-architecture/security-and-privacy.md) (minimisation: the profile stays on the phone until needed) |
| R6 | If storing the data on a server is not allowed, keep it temporarily inside the office network: the visitor scans a QR code at the office, fills in, sends, and the clerk has it at once. | [`security-and-privacy.md`](../02-architecture/security-and-privacy.md) |
| R7 | The clerk finds the visitor by name, picks the forms, prints. | [`api-contract.md`](../02-architecture/api-contract.md), work package WP-B3 |
| R8 | An AI agent checks each filled form for correctness and completeness, proposes corrections, and tells the clerk what is missing or suspicious. | [`prompts/`](../../prompts/), [`docs/02-architecture/design-notes.md`](../02-architecture/design-notes.md) §4, work package WP-B5 |
| R9 | AI through an API (for example Claude); a local model when sending data to an outside API is too risky. | [`docs/02-architecture/design-notes.md`](../02-architecture/design-notes.md) §5, [`research/05`](../../research/05-rodo-ai-act-security-requirements.md) |
| R10 | Applications never talk to the database directly, only through an API. The structure for safe temporary and permanent storage, the API design and current security practice must be thought through from the start. | [`api-contract.md`](../02-architecture/api-contract.md), [`security-and-privacy.md`](../02-architecture/security-and-privacy.md) |
| R11 | A list of links where agents can download every form; for online-only forms, where to analyse them. A detailed project structure that agents can act on. | forms catalogue, work packages |
| R12 | Phone instead of a scanner: when the visitor has filled in nothing (for example an elderly person), the clerk photographs the document, the system recognises it and shows the result very large and clear for checking against the document; after confirmation it appears like any other visitor record. | identity-sources |
| R13 | A second check of the clerk's work and of the forms so that mistakes are rare: which mistakes happen, what to watch, what instructions the checking agents need. | [`prompts/README.md`](../../prompts/README.md) |
| R14 | Turn the PDF forms into online forms convenient for the clerk: one screen with all the visitor's data, then a choice of forms. | work packages [`WP-B1 … WP-B6`](../03-plan/work-packages/WP-B1-B6-counter.md) |
| R15 | The printout must be identical to the officially approved template: no shifted fields, no reflowed paragraphs. Establish whether this is legally required. | [`research/03b-form-anatomy-and-canonical-profile.md`](../../research/03b-form-anatomy-and-canonical-profile.md), work package WP-B1 |
| R16 | Chains of forms: the clerk names the situation (or ticks boxes, or describes it to the assistant) and the system proposes all the forms that situation needs. | work package WP-B1 (bundles), [`prompts/bundle-recommender-system.md`](../../prompts/bundle-recommender-system.md) |
| R17 | Support a hardware passport and ID reader that also tells genuine documents from forged ones. Find the old correspondence with the manufacturer, the software and the licence so the reader can be connected. | work package WP-B4; hardware facts in [`research/09-lessons-from-2022-prototype.md`](../../research/09-lessons-from-2022-prototype.md); licence files stay private |
| R24 | mObywatel: can the data be pulled from it? Is there a QR-based solution in it already? If not, propose one to its developers, and meanwhile show our own working flow on site. | [`research/04-mobywatel-identity-once-only.md`](../../research/04-mobywatel-identity-once-only.md) |
| R27 | Many institutions: can there be one database with everything about the person, safely and lawfully? If not, how can several institutions benefit so that nobody fills in the same data again? "I want to come with a request and get the form printed with everything already in it." | [`scope-decision.md`](../01-product/scope-decision.md) §4 |

## C. Research and verification requirements

| Id | Requirement | Where |
|---|---|---|
| R18 | Re-check the earlier research made by another agent: what is right, what is wrong, fix it, improve it. | [`docs/06-audit/previous-research-audit.ru.md`](../06-audit/previous-research-audit.ru.md) (Russian, for the owner) |
| R19 | Deep research; prepare everything so that agents can build correctly, step by step, with current technology and methods. | [`research/`](../../research/) |
| R23 | Think through what the owner did not think of and add it to the specification. | [`docs/01-product/gaps-and-additions.md`](../01-product/gaps-and-additions.md) |
| R25 | Analyse the Trello boards of the 2022 prototype: which problems appeared, and take them into account. | [`research/09-lessons-from-2022-prototype.md`](../../research/09-lessons-from-2022-prototype.md) |
| R26 | Decide whether joining the hackathon case with the wide counter platform is right, or whether to focus on one thing while keeping a scalable base; say what to build and what to show the jury. | scope-decision |
| R28 | Establish who the customer is and what they really want; the first prototype must remove real pains of the direct customer and allow growth to other offices. | [`scope-decision.md`](../01-product/scope-decision.md) §2 |

## D. Delivery requirements

| Id | Requirement | Where |
|---|---|---|
| R20 | A separate git repository, public, with no sensitive data, following the owner's publication rules for search engines and AI assistants. | this repository, [`SECURITY.md`](../../SECURITY.md), [`llms.txt`](../../llms.txt) |
| R21 | The repository must let the owner start a lead agent in a new chat on another computer; the lead runs sub-agents on separate tasks, uses the token-saving techniques of the current Claude models, does all development through git so that agents do not disturb each other, and keeps its own context small. | [`START_HERE.md`](../../START_HERE.md), [`docs/04-orchestration/`](../04-orchestration/) |
| R22 | The repository must answer what a hackathon jury usually asks, so that no extra questions remain. | [`docs/05-hackathon/`](../05-hackathon/), [`README.pl.md`](../../README.pl.md) |
| R29 | Leave a place for the extra information that will be handed out at the hackathon, to be analysed and built in. | [`docs/05-hackathon/ONSITE-INTAKE.md`](../05-hackathon/ONSITE-INTAKE.md) |
| R30 | Everything needed to build the system must be in git: the next agent starts from the repository alone. | whole repository |
| R31 | If a usage limit interrupts the preparation, the work continues by itself after the limit resets. | handled outside this repository; the same protocol for the build phase is in [`docs/04-orchestration/resume-after-limit.md`](../04-orchestration/resume-after-limit.md) |
| R32 | Everything not yet pushed on the preparing computer is pushed to the owner's private notes repository. | done outside this repository |

## E. Constraints stated or implied

- The owner is not a programmer; he directs AI agents. Questions to him must be answerable without technical knowledge, one at a time, with a recommended default.
- Every new product, site and repository of the owner carries "Shramko" in its name.
- The owner speaks English, Polish and Russian. Documents he reads himself are in Russian ([`README.ru.md`](../../README.ru.md)); agent-facing specifications are in English; jury-facing texts are in Polish.
- Real personal data never enters the repository, prompts sent to cloud models, logs or issue trackers.
