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

## 3a. Questions to ask at the stand of Centralny Ośrodek Informatyki (forms task)

The owner asks in Polish; the line in italics is the meaning in Russian for him; the arrow says what the answer decides.

1. Czy pula kredytów na modele LLM dla zespołów jest dostępna i jak ją uzyskać? *(Есть ли обещанные кредиты на модели и как их получить?)* → the model provider of the build (STATUS, "Waiting for the owner" 2).
2. Jakie pliki formularzy są dla Państwa najważniejsze: PDF, DOCX, XLSX? Czy dostaniemy przykładowe? *(Какие файлы бланков для вас главные и дадите ли примеры?)* → inputs of WP-B6, forms for the live demo.
3. Co ma być wynikiem: formularz dla Generatora Formularzy ePUC, opis w konkretnym formacie, czy działająca usługa? *(Что должно быть результатом: форма для вашего генератора, описание в формате или работающая услуга?)* → export target; answer card 4.
4. Kto będzie użytkownikiem narzędzia: urzędnik publikujący formularze, analityk w COI, mieszkaniec? *(Кто пользователь инструмента?)* → the first screen of the demo.
5. Co znaczy „on-prem” w Państwa ocenie: bez żadnej chmury, z lokalnym modelem? Jaki sprzęt zakładamy? *(Что вы понимаете под on-prem: совсем без облака, локальная модель, какое железо?)* → default provider in the demo, the "what works" page.
6. Jak będzie oceniana poprawność: na Państwa formularzach testowych? *(Как будете проверять точность: на своих бланках?)* → the golden test and the numbers on the slides.
7. Czy w funkcji „Przekaż instytucji” w mObywatelu instytucja może poprosić o listę pól zależną od sprawy? Jakie atrybuty są dostępne? *(Может ли учреждение в mObywatel запросить набор полей под конкретное дело и какие поля доступны?)* → `docs/01-product/one-visit-package.md` §5; whether that slide may be said as more than a proposal.
8. Czy pokaz „od potrzeby do podpisu” w urzędzie (komplet wniosków, dane raz, kontrola wyjątków) jest dla Państwa w zakresie zadania, czy tylko dodatkiem? *(Наш показ «от потребности до подписи» входит в задание или это только дополнение?)* → the split of the five minutes between part one and part two.

## 3b. Questions to ask clerks about the counter (city's stand, or any official present)

The owner said he does not know yet what hurts clerks most. These answers decide which pains the pitch may state as facts ([`../01-product/one-visit-package.md`](../01-product/one-visit-package.md) §2). Write down the answer and who said it; no names of residents, no real cases.

1. Co zajmuje najwięcej czasu przy okienku: pomoc w wypełnianiu, przepisywanie danych, sprawdzanie z dokumentem, czy wprowadzanie do systemu? *(Что отнимает больше всего времени у окошка?)* → which stage the demo dwells on.
2. Jak często mieszkaniec musi przyjść drugi raz, bo zabrakło wniosku albo załącznika? *(Как часто человек приходит второй раз из-за забытого бланка или приложения?)* → whether "complete set" may be said with a number.
3. Jak często wzywacie do uzupełnienia braków formalnych? *(Как часто приходится требовать дополнить заявление?)* → the same.
4. Jakie błędy w wypełnionych wnioskach powtarzają się najczęściej? *(Какие ошибки в заявлениях повторяются чаще всего?)* → seeded mistakes of the checker (WP-B5) and of the comparison (WP-B8).
5. Czy przy rezerwacji wizyty przez internet widzicie, w jakiej sprawie przychodzi mieszkaniec, zanim podejdzie do okienka? Co jeszcze chcielibyście wiedzieć wcześniej? *(Видите ли вы заранее, по какому делу человек записался? Что ещё хотели бы знать до визита?)* → WP-B7 items 4–5.
6. Po wydrukowaniu i podpisaniu wniosku: czy dane trzeba jeszcze raz wpisać do systemu dziedzinowego? Do jakiego? *(После подписи данные ещё раз вводят в рабочую систему? В какую?)* → the honest limit "printing does not remove typing into the domain system" and the next step (bridge to desktop applications).
7. Czy macie przy stanowisku czytnik dokumentów albo skaner? Czy wolno Wam sprawdzać mDowód kodem QR? *(Есть ли у вас сканер документов? Проверяете ли mDowód по QR?)* → identity sources worth showing.
8. Co musiałoby działać, żebyście chcieli tego używać od pierwszego dnia? *(Что должно работать, чтобы вы захотели пользоваться этим с первого дня?)* → acceptance of the clerk's screens.

## 4. Decisions taken during the event

| Time | Decision | Why | Who decided |
|---|---|---|---|
| | | | |
