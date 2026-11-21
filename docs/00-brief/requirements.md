# Owner requirements (R1–R54)

This is the complete list of what the project owner asked for, extracted from his spoken briefs (two messages of 20 November 2026, a third, a fourth and a fifth of 21 November, sections F, G and H; originally in Russian). Every requirement has an id that the rest of the repository refers to. "Where" points to the document that answers it. Nothing here is optional unless the scope decision ([`docs/01-product/scope-decision.md`](../01-product/scope-decision.md)) says so.

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

## F. Third brief: one visit, complete set (21 November 2026, morning)

The owner's words in short: "the data about me are stored in advance; I tell the clerk what I need, the clerk tells the assistant, the assistant picks the whole package of forms; I hand over my data and the forms are filled; the clerk fills in nothing and only checks, and the system shows only what must be re-checked, re-checks itself and looks for errors; if all is fine, print." The idea as one flow: [`docs/01-product/one-visit-package.md`](../01-product/one-visit-package.md).

| Id | Requirement | Where |
|---|---|---|
| R33 | The resident's data are entered and kept in advance; at the counter they are handed over and every form is filled automatically. The clerk types nothing. (Sharpens R4, R5.) | one-visit-package §1; WP-B2 |
| R34 | The resident says what they need; the assistant proposes at once the complete package of forms for that need, so that a forgotten form never forces the resident to fill everything in again. (Sharpens R16.) | [`WP-B7`](../03-plan/work-packages/WP-B7-B9-one-visit.md) |
| R35 | The clerk only verifies, quickly: the screen shows only the data that must be re-checked; the system re-checks itself and searches for possible errors; if all is fine the set is printed. | one-visit-package §4; WP-B8, WP-B5 |
| R36 | If the resident books a visit in the electronic queue and states the matter, the clerk who opens that request is offered the package at once; the clerk can still clarify what the resident wants, and the package changes. | one-visit-package §6; WP-B7; [`research/12`](../../research/12-one-visit-package-addendum.md) item 4 |
| R37 | No manual comparison: a document scanner (the owner's reader) or a phone reads the document, the system compares it with what the resident provided and removes the clerk's mechanical error; the result goes to print, to the office's system, or both. | WP-B8, WP-B4 |
| R38 | When the resident enters their data for the first time, fields already known to the browser (name, surname, address, e-mail) are pulled in so that nobody starts from zero. | WP-B9; research/12 items 8–9 |
| R39 | The application that keeps the resident's data should ideally be mObywatel. | one-visit-package §5; [`research/04`](../../research/04-mobywatel-identity-once-only.md); adapter simulated in WP-B4 |
| R40 | The most important thing is an effective presentation. First a document for the jury (PDF if that is all they accept) that shows by infographics and short text which pains are solved, how convenient it is and what the scale can be; with a link to a richer web page with infographics and animation for those who want more. | [`storyboard-pakiet.md`](../05-hackathon/presentation/storyboard-pakiet.md); `site-formularze/pakiet/` |
| R41 | All of this is in git so that a new chat can hand the work to the next agent quickly and clearly. | [`START_HERE.md`](../../START_HERE.md), [`STATUS.md`](../03-plan/STATUS.md), this section |
| R42 | Whatever was left unresearched or unfinished because of usage limits is finished now; the limits are no longer a constraint (owner, 21 November, 09:56). | research/12; STATUS "Budget" |
| R43 | The owner does not know yet what hurts clerks most ("mostly helping to fill in and writing the forms in"); find out and close as many of those pains as possible. | one-visit-package §2; [`ONSITE-INTAKE.md`](../05-hackathon/ONSITE-INTAKE.md) §3a–3b |

## G. Fourth brief: the resident's own AI agent (21 November 2026, 10:29–10:33)

The owner's words in short: "I work with agents as personal secretaries, and so does my daughter; soon everybody will. Today my agents help me book visits and fill online forms, but only through the browser version of sites, which is very inconvenient. I want my agent to connect to the office officially and safely, through MCP or an API: pick the right services, the date and the time, book me, put it into my calendar after checking when I am free, and fill the digitised forms with my data, which are kept on my side. Part of the documents is still signed on paper in the office and part is digitised: with the digitised ones it would be perfect to work online through agents. Offer both variants: for advanced users, and for those who do not and will not work with agents." The idea as a design: [`docs/01-product/agent-door.md`](../01-product/agent-door.md).

| Id | Requirement | Where |
|---|---|---|
| R44 | A resident's own AI agent can reach the office's services officially and safely (MCP, API or what is right): find the needed service, choose date and time, book the visit. | agent-door §4; [`WP-B10`](../03-plan/work-packages/WP-B10-agent-door.md) part a |
| R45 | The agent checks the resident's calendar, enters the visit into it and prepares everything the resident must hand over; the resident comes and only hands over the data. | agent-door §2, §5; WP-B10 items 5–6 |
| R46 | The agent can fill the office's **digitised** forms online with the data its owner keeps. | agent-door §1, §3 rule 4; WP-B10 part b |
| R47 | The system distinguishes documents still signed on paper in the office from digitised ones, and lets agents work online with the digitised ones. | agent-door §1 (`channel` per form) |
| R48 | Two variants side by side, the same result: for people who work with agents and for people who do not. | agent-door §0, §2; reading version page 7 |
| R49 | The presentation speaks to the generation that already lives with AI assistants and shows which of its pains this removes (browser automation of public sites is slow and fragile). | [`storyboard-pakiet.md`](../05-hackathon/presentation/storyboard-pakiet.md) page 7; agent-door §6 |
| R50 | Build on the owner's earlier open work on agents acting for a person (purchases under a signed mandate with limits and an audit log). | agent-door §3 rule 7 |

## H. Fifth brief: the whole catalogue in advance, a short opening, the model (21 November 2026, 10:48–10:56)

The owner's words in short: "when a clerk adds a document to make it digital, the system does the first step itself. Better: we load and digitise all possible documents ourselves in advance, without the clerk; he only adds new ones to the shared system. Make the presentation extremely short at the start, so that the ideas and the problems are clear at once, and only then expand. Hook the judges and mentors with something unusual, global, large in scale." At 10:56: "I do not want to use their code or local models if they are poor. I build with Claude Code. Their models only for simple things; if they give credits for good models, gladly."

| Id | Requirement | Where |
|---|---|---|
| R51 | When a clerk adds a document, the system does the first pass by itself; the person only looks and approves. (Sharpens R17.) | WP-B6; [`WP-B11`](../03-plan/work-packages/WP-B11-catalogue-in-advance.md) item 11 |
| R52 | All documents the office already publishes are loaded and given the first pass in advance by the team, without the counter clerks; a clerk only adds a new document to the shared catalogue. | WP-B11; [`research/13`](../../research/13-forms-census-and-opening-facts.md) §1; `data/forms-census.json` |
| R53 | The presentation opens with the whole idea in half a minute (problem, solution, scale) and only then expands; it carries a hook that is unusual and large in scale. | [`storyboard-pakiet.md`](../05-hackathon/presentation/storyboard-pakiet.md) pages 1–2 and the short version |
| R54 | The build is done with Claude Code. The product uses a strong model wherever no personal data are involved (reading blank forms); a weak local model is not the default for that step; the partner's models or credits are used if they are good; nothing may depend on credits arriving. Personal data still never go to a cloud model (`AGENTS.md` rule 9). | [`ai-layer.md`](../02-architecture/ai-layer.md) §2; STATUS "Waiting for the owner" item 2; WP-B11 item 9 |

## E. Constraints stated or implied

- The owner is not a programmer; he directs AI agents. Questions to him must be answerable without technical knowledge, one at a time, with a recommended default.
- Every new product, site and repository of the owner carries "Shramko" in its name.
- The owner speaks English, Polish and Russian. Documents he reads himself are in Russian ([`README.ru.md`](../../README.ru.md)); agent-facing specifications are in English; jury-facing texts are in Polish.
- Real personal data never enters the repository, prompts sent to cloud models, logs or issue trackers.
