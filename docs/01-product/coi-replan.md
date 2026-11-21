# The forms task as it really is, and what changes (re-plan of 21 November 2026, 11:30)

Read first: the digest of the card, [`../05-hackathon/intake/coi-task-card.md`](../05-hackathon/intake/coi-task-card.md). Ids `C-…` below refer to it. Packages: [`../03-plan/work-packages/WP-F-forms-to-json.md`](../03-plan/work-packages/WP-F-forms-to-json.md).

## 1. The finding

We prepared a two-sided counter product: a resident's data once, a set of forms, a comparison with the identity document, a print on the original template. **The card asks for none of that.** It asks for a converter: one blank form file in, one JSON document in the partner's own structure out, as a REST service in Docker, used by the official who digitises forms. Seventy per cent of the score is completeness against their list, intuitiveness and code quality; twenty per cent is deployment potential including cost; ten per cent is originality.

Three rules of the card overturn decisions we had recorded:

| Rule of the card | What it overturns |
|---|---|
| C-TECH-NOEXT: no model that is available only through an API, no external API, MCP or SaaS as a dependency | the owner's model decision of 10:56 (R54) for this task: a cloud model may **build** the product, it may not run inside it; the agent door as a part of the product |
| C-TEST: finalists run the solution on new files at the defence | a demo on prepared forms is not enough; the pipeline must behave on files nobody has seen |
| C-SUB: ten slides at most, a film of three minutes at most, the JSON files themselves | the eleven-page reading version and the two-minute film plan |

What stays true and becomes more valuable: the geometry-first reading of forms, the measured archive of 661 real documents of one city as a robustness set, the batch idea (the card names batch processing as a scored convenience), the rule "AI proposes, a person approves", the ban on copyleft libraries (already our rule), open source and on-premise operation.

## 1a. What the partner's materials added (read at 11:30)

The partner's sample shows what "convert" means: a one-page paper form becomes a four-page e-service with 69 components, and about four fifths of them are standard sections from the partner's design standard that are not on the paper at all. From the paper come the title, the addressee, who may apply, the fields of the matter, attachments, declarations and fees. Details: [`../02-architecture/coi-json-format.md`](../02-architecture/coi-json-format.md).

Consequences: (1) a library of standard sections plus a short list of questions about the paper gives most of the result, by rules, without a model; (2) every set holds the same form in eight formats, so the readers matter as much as the understanding; (3) the review screen should show the questions and their evidence, not sixty-nine components; (4) the materials contradict each other in eight places, which we list and ask about instead of guessing silently.

**Recommendation on the task, changed after the materials: stay with the forms task.** Most of the score can be reached by rules written by the agents; nothing has to run that the owner's laptop cannot run; no paid model key is needed; our archive of 661 real forms is a test set nobody else has. The city's task stays the fallback (STATUS, "Waiting for the owner", item 1).

## 2. The owner's ideas, placed against the card

| Idea (requirement) | Place now |
|---|---|
| The system does the first pass; all documents of an office digitised in advance; the official only adds new ones (R51–R52) | **Core.** Batch mode over a folder or archive, with a funnel and a review queue. Scored under C-OPT-6 and under deployment potential |
| One description, several users; the resident's AI assistant fills digitised forms (R44–R50) | **Originality, as an export.** The card itself says the forms should later be usable by AI agents. From the same JSON we write a second file that an agent can read (a tool description with typed fields and validation). No MCP server inside the product, no network: C-TECH-NOEXT stays intact. One slide, one screen |
| Data kept once; the profile; mObywatel (R33, R38, R39) | **Inside C-OPT-1.** "Initial data" in their terms: fields the state already knows about a logged-in person. We mark such fields as pre-filled. Nothing else of the profile is built |
| Check by exception; the screen shows only what needs a look (R35) | **The review screen of the converter.** The official sees the fields the system is unsure about first, the rest folded. Scored under intuitiveness |
| From a need to the complete set of forms (R34, R36) | **Parked, one sentence in the outlook.** Possible later as links between forms of one procedure |
| QR handoff, comparison with the document, print on the original template (R37, WP-B2…B4, B8, B9) | **Parked.** Not asked, not scored. The overlay check stays in the repository as a tool |
| A strong cloud model in the product (R54) | **Not allowed here.** See §4 |

## 3. Pains they did not spell out, and our answer

Each line names the criterion it serves. This is the list to build beyond the minimum; order by value.

| # | Unspoken pain | Answer | Criterion |
|---|---|---|---|
| 1 | The official must trust the result, and checking a whole JSON by eye is as slow as writing it | Side by side: the original page with every found field outlined, and the form tree; a click on either side highlights the other. Fields sorted by the system's confidence, lowest first | intuitiveness |
| 2 | A paper form copied field by field makes a bad electronic form | Rules that **translate paper habits**: a row of boxes becomes one field with a length; "niepotrzebne skreślić" becomes a choice; "miejscowość, data" and the signature line leave the citizen's form; "wypełnia urząd" sections are split off; printed instructions become hints | completeness (design rules), intuitiveness |
| 3 | Validation is written by hand for every form | Length from the number of boxes; type from the label and the dictionary (PESEL, NIP, REGON, postal code, phone, e-mail, bank account, date); check digits where they exist | C-OPT-6 |
| 4 | The same thing is asked under twenty different labels | Every field is mapped to one concept of a small canonical list, then to their dictionary or initial data; an unmapped group of options becomes a proposed new dictionary | C-OPT-1, C-OPT-2 |
| 5 | Conditions hide in the wording ("jeżeli", "dotyczy", "w przypadku pełnomocnika") | Detection of conditional wording and of yes/no gates in front of sections; dependencies written into the JSON and shown as arrows in the viewer | C-OPT-3 |
| 6 | One form is not the problem; thousands are | Batch: a folder or an archive in, a table of results out (done, needs a look, failed and why), with the seconds per form. Proven on the 661 documents of one city | C-OPT-6, deployment potential |
| 7 | Cost: a model with a graphics card for every office is not realistic | Rules and geometry first; a small open model only for the wording; scans are the only path that needs more. The README states seconds per form on a plain processor and the share of forms that needed no model | deployment potential (cost) |
| 8 | Somebody will upload a filled form with a real person's data | The file never leaves memory or temporary space (their rule); nothing of the content is logged; a warning when the upload looks filled in (handwriting or typed values in the fields) | deployment potential, code quality |
| 9 | Offices change their templates | The answer carries the hash of the input; two runs can be compared: what was added, removed, renamed | originality, deployment potential |
| 10 | The same procedure exists in many offices in different layouts | "Form family": after conversion, the field concepts of a new form are compared with those already converted; the official sees "92 % the same as the form of office X" and can reuse it | originality |
| 11 | A wrong JSON that looks right is worse than an honest gap | The answer always validates against the schema; whatever could not be read is listed in a `warnings` part with the page and place; never a silent guess, never a crash on a strange file | code quality, C-TEST |
| 12 | Forms must be readable by everybody | A plain-language hint proposed next to an official label (the label itself is kept); checks of the produced form against basic accessibility rules in the viewer | intuitiveness |
| 13 | Tomorrow's user is an AI assistant | The agent-readable export of §2 | originality |

## 4. Which model runs inside the product

- Allowed: rules, classical methods, and open models whose weights sit in the container or on a mounted volume. Not allowed: any call out of the container.
- Default path uses **no language model**: readers, geometry, rules, dictionaries. It must produce a valid, useful JSON alone.
- Second step, switchable: a small open model served inside the container for wording tasks only (clean a label, name a section, decide the concept of a field, read a condition). Candidates already named in [`../02-architecture/ai-layer.md`](../02-architecture/ai-layer.md) §2 with their licences: an open Polish model. Size is chosen after the owner says which laptop is at the event; the licence of the weights is checked and written into the licence list before use.
- Scans and photos: optical character recognition with an open engine plus line and box detection, then the same path. A vision model is a later option, only if the hardware allows.
- The owner's wish for strong models is met where the card allows it: Claude Code writes, tests and reviews everything.
- **Owner, 11:23: his laptop cannot run any model, and he would rather use cloud models for everything.** For this task that is not possible inside the product. Therefore the product at the event runs on rules only; the model step stays a switched-off interface. An open model on a server the owner rents, inside our own container, is a possible later step, only after a mentor confirms that it meets the rule (question 2 below).

## 5. Shape of the service

```
POST /v1/forms/convert   (one file, bearer token)
  guard      extension, MIME sniffing, file name, size        -> 4xx with a reason
  read       pdf | docx | doc | ods | xlsx | image            -> pages: text, lines, boxes, tables
  find       labels, places to fill, groups, sections, notes  -> candidates with place and confidence
  mean       concept, type, required, validation, dictionary,
             initial data, conditions, paper habits translated
  compose    thematic pages, order, their JSON structure      -> validated against the schema
  answer     { form: <their JSON>, report: { warnings, confidence, source places, seconds } }
```

Whether the report may travel inside the answer or must be a second endpoint depends on their structure: decided in WP-F0 after reading the materials. Around the service: a review front end (upload, tree, source view, batch table), a viewer that renders the e-service from the JSON, the agent-readable export, an evaluation run.

## 6. Risks, with the early test for each

| Risk | Early test |
|---|---|
| Their JSON structure is richer than we can infer from samples | WP-F0 in the first hour: write the schema from the samples and rules; list every element we cannot explain; ask the mentors the same hour |
| The laptop cannot run a useful open model | The default path needs none; measure the model step on the residence form before building on it |
| Python 3.14 lacks a wheel for a library we need | WP-F1 builds the image first with the full dependency list; a missing wheel is known in the first hour |
| DOC and ODS need LibreOffice, whose licence is weak copyleft | Ask the mentors (question 1 below); fallback: read DOCX, XLSX and ODS directly with permissive libraries and convert only DOC |
| Scans read badly | State it: the answer marks low-confidence text; do not pretend |
| The copyright transfer conflicts with the open licence of the repository | The owner reads the template; material made before the event is marked as such (`NOTICE`) |

## 7. Questions for the partner's mentors (owner asks; Polish, meaning in Russian)

1. **Czy do konwersji plików DOC i ODS możemy użyć LibreOffice (licencja MPL 2.0) uruchomionego w kontenerze?** *(Можно ли LibreOffice в контейнере, при его лицензии?)*
2. **Czy otwarty model uruchomiony lokalnie w kontenerze spełnia wymóg „bez modeli dostępnych wyłącznie przez API”? Na jakim sprzęcie uruchamiamy rozwiązanie na obronie?** *(Локальная открытая модель годится? На каком железе запуск на защите?)*
3. **Kryteria wymieniają pięć rozszerzeń, a treść zadania sześć. Czy aplikacja do wizualizacji JSON jest punktowana?** *(В критериях пять расширений, в задании шесть: визуализатор оценивается?)*
4. **Czy istnieje schemat albo walidator JSON, którym możemy sprawdzać wynik?** *(Есть ли схема или валидатор JSON?)*
5. **JWT: jaki algorytm i skąd klucz na obronie? Czy wystarczy weryfikacja podpisu i terminu ważności?** *(Какой алгоритм JWT и откуда ключ?)*
6. **Czy nowe pliki na obronie będą podobne do tych z materiałów? W jakich formatach?** *(Новые файлы на защите похожи на материалы? Форматы?)*
7. **Python 3.14: wymóg czy preferencja? A obraz Alpine?** *(3.14 и Alpine: требование или предпочтение?)*
8. **Jak odebrać tokeny i do jakich modeli są?** *(Как получить токены и к каким они моделям?)*
9. **Gdzie jest wzór umowy przeniesienia praw (załącznik nr 1)?** *(Где образец договора о передаче прав?)*
10. **Schemat i opis mają klucz „repetingSectionGrid”, a przykładowy JSON i zapytania JSONata „repeatingSectionGrid”. Który jest poprawny przy imporcie?** *(В схеме и в образце ключ написан по-разному: какой правильный?)*
11. **Jakie są dokładne nazwy słowników do pola „dictionaryName” (Województwo, Powiat, Gmina, Miejscowość, Numery kierunkowe)? W przykładzie są „Kraje” i „TERYT_DOWODOWY”.** *(Точные имена словарей?)*
12. **W przykładowym JSON żadne pole nie ma walidatora REQUIRED. Czy mamy go ustawiać?** *(В образце нет обязательных полей: ставить ли REQUIRED?)*
13. **Jak zapisać w JSON limit plików (liczba, rozmiar, formaty) i walidację wzorcem (regex)?** *(Как записать ограничения файлов и регулярное выражение?)*
14. **Czy materiały do zadania możemy trzymać w publicznym repozytorium z rozwiązaniem?** *(Можно ли держать ваши материалы в открытом репозитории?)*

## 8. Order of value if time is short

C-MIN-1 on PDF and DOCX with a valid JSON → guard, token, Docker, README (C-TECH) → validations (C-OPT-6) → dictionaries and initial data (C-OPT-1) → upload and review front end (C-OPT-4) → XLSX, ODS, DOC → dependencies (C-OPT-3) → new dictionary (C-OPT-2) → batch table → scans → viewer (C-OPT-5) → agent-readable export → form family.
