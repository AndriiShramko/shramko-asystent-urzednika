# Onsite intake: what the organisers and the city hand out at the hackathon

The published challenge text is two sentences long. The full task description, the evaluation criteria, sample data and access to tools are expected at the start of the event and from mentors during it. **This file is where all of it goes.** The lead agent processes it before starting or continuing any build work, because it can change the scope.

## How the owner adds material (no technical steps)

Put anything you receive into the folder `docs/05-hackathon/intake/` or paste it into the chat with the lead agent:

- a photo of a slide or of a printed sheet,
- a PDF or a link,
- a voice note or a few typed sentences ("the mentor from the city said they receive most requests by e-mail and the worst part is ..."),
- answers to the questions in section 3.

Then tell the lead: "new intake". Nothing else is needed.

## Procedure for the lead agent

1. Read every new item in `intake/` (images: describe each in one sentence, transcribe the text that matters). Never put real personal data from sample documents into prompts for cloud models or into commits; if the organisers give real requests, keep them in `data/private/` (git-ignored) and derive synthetic look-alikes for tests.
2. Fill the log in section 2: one row per fact, with its source and the time.
3. For each fact decide: **confirms** the plan, **changes** the plan, or **new requirement**. For every change write the consequence in one line and the affected work packages.
4. Re-read [`../01-product/scope-decision.md`](../01-product/scope-decision.md) §6 "What would change this decision". If a trigger fired, propose the new scope to the owner as one question with a recommended option, and update the roadmap only after his answer (or after the default timeout stated in the question).
5. Update, in this order: `docs/03-plan/roadmap.md`, the affected work-package files (only packages that have not started; for running ones add a "Change request" section and tell the builder), `docs/05-hackathon/jury-qa.md`, `docs/05-hackathon/demo-script.md`, `docs/05-hackathon/pitch.md`.
6. Commit: `intake: <what changed>`.
7. Tell the owner in three lines what changed.

## 1. Facts we expect to receive (fill in)

| Topic | What we assumed before the event | What was actually said | Source |
|---|---|---|---|
| Full task description | Assistant for analysing UDIP requests and drafting answers | | |
| Evaluation criteria and weights | Fit with the task, usefulness for the office, security, feasibility of deployment, quality of the demo | | |
| What must be submitted, where, by when | Repository link, short description, presentation or video, live pitch | | |
| Pitch length and format | 3–5 minutes plus questions | | |
| Sample data from the city | None before the event; synthetic set prepared | | |
| How requests arrive in the city hall | E-mail, electronic delivery, paper | | |
| Which unit handles them and how many people | Unknown | | |
| Number of requests per year | Unknown | | |
| The document management system in use | Unknown | | |
| Tools the city already uses for this | None known | | |
| Allowed or provided language models and infrastructure | Own keys; local open models allowed | | |
| Constraints on cloud use for the city | Personal data must not leave the office unprotected | | |
| What the city considers the worst part of the work | Deadlines, repeated similar requests, anonymisation, legal form of the answer | | |
| Licence and ownership expectations | Open source accepted | | |
| Interest in the wider counter module | Unknown | | |

## 2. Intake log

| Time | Fact | Source (who, what document) | Effect: confirms / changes / new | Consequence and affected packages |
|---|---|---|---|---|
| | | | | |

## 3. Questions to ask the city's mentor (the owner asks, in Polish)

Each question is short on purpose; the answers change real decisions.

1. Ile wniosków o informację publiczną wpływa do urzędu rocznie i jakim kanałem najczęściej? *(How many requests per year and through which channel? → sizing, intake adapters.)*
2. Kto dziś decyduje, czy pismo jest wnioskiem o informację publiczną, i kto przygotowuje odpowiedź: koordynator czy wydział merytoryczny? *(Who triages, who drafts? → roles and workflow.)*
3. Co zajmuje najwięcej czasu: ustalenie, kto ma informację, zebranie dokumentów, anonimizacja czy napisanie pisma? *(Where is the time lost? → which feature is the centrepiece of the demo.)*
4. Jak często wydajecie decyzje odmowne i czy zdarzają się skargi na bezczynność? *(Refusals and court complaints → legal safety features.)*
5. W jakim systemie rejestrujecie sprawy i czy asystent może dostać z niego treść pisma? *(Document management system → integration adapter.)*
6. Czy odpowiedzi publikujecie w BIP i czy macie rejestr wniosków, z którego można korzystać? *(Register of past answers → similar-case search, test data.)*
7. Czy dane mogą być przetwarzane przez model w chmurze w UE, czy tylko lokalnie w urzędzie? *(Cloud or on-premise → provider policy defaults.)*
8. Co musiałby umieć asystent, żeby urzędnicy chcieli go używać od pierwszego dnia? *(Adoption → acceptance criteria.)*
9. Czy podobny problem powtarzalnych danych macie przy okienku w innych wydziałach? *(Opens the door for Module B without pushing it.)*

## 4. Decisions taken during the event

| Time | Decision | Why | Who decided |
|---|---|---|---|
| | | | |
