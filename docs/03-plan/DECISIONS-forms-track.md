# Decisions for Track F (forms task), 21 November 2026, 13:15

Lead-owned. Taken by the preparing session after reading the partner's materials, both reference exports, five research files (`research/14` … `research/18`) and the model reports in `research/eden/`. Every later document of Track F follows this file; where an older document disagrees, this file wins. A decision changes only by an entry in the last section.

## 1. What we build, in one sentence

**A compiler with an accountant, not a scanner with AI.** The service compiles a paper form into the partner's form grammar by rules and a library of the partner's standard sections, and it accounts for everything: where each field came from, what happened to every blank of the paper, what was left out and why, and what it refused to guess.

Slide line (Polish): „Kompilator z księgowym, nie skaner z AI. Urzędnik zatwierdza znaczenie, nie przepisuje rubryk.”

## 2. The contract with the partner's importer

| # | Decision | Evidence |
|---|---|---|
| D1 | `POST /v1/forms/convert` answers with **the partner's JSON and nothing else**: top keys `title`, `tabs`, `flow`. No envelope, no extra keys | task card C-TECH-API; unknown keys may fail a strict importer (research/15) |
| D2 | Everything else travels beside it: a sidecar `meta` (origins, evidence, confidence, ledger, proposals, concept URIs, legal basis) from `POST /v1/forms/convert?report=1` as `multipart/mixed` or from `POST /v1/forms/report`, keyed by field `id` | research/18; GPT report |
| D3 | Spelling `repeatingSectionGrid`; every component carries `options: []`, `validation: []`, `readOnly`, `repeatingSectionGrid: []`, `states: []`, `tooltipMessage: ""`; `validation` is always a list | both exports: 34 of 34 occurrences; forensics file |
| D4 | One column: `x = 0`, `cols = 3`; component `rows = 1`; sections never nested; pages chained by `flow.links` in order | both exports |
| D5 | Last page: `SECTION` holding one `TEXT_BLOCK`, as in both exports, although the rules say `INFO_SECTION`. A switch `FINISH_STYLE=info_section` exists and is one line | both exports; question J3 |
| D6 | Identity fields from a register are read-only; address and contact from `MLPZ` are pre-filled and editable | both exports (2 of 2) |
| D7 | `techName` is unique across the whole form; repeated blocks get the partner's suffixes (`_siedziba`, `_inna_osoba`, `_zagranica`); at most 60 characters | both exports: no duplicate, longest 53 |
| D8 | We write validators where the paper or the standard supports them: `REQUIRED`, `PESEL`, `NIP`, `REGON`, `ZIP_CODE`, `EMAIL`, `EPUAP`, `ADE`, `SERIAL_NUMBER_ID_CARD`. A switch `VALIDATORS=off` reproduces the exports' empty lists | the rules list them; the exports use none; question J4 |
| D9 | Dictionaries: only names seen in the exports (`Kraje`, `TERYT_DOWODOWY`, `TERYT_4G_DOWODOWY`) go into the form. Every other candidate is a **proposal in the sidecar** with its evidence | question J5 |
| D10 | Ids are UUIDs made deterministically from meaning, not from the file: `uuid5(namespace, form key / page role / section role / field key)`. The form key defaults to the slug of the title. One changed label does not change a hundred ids | research/18; GPT report idea 9; question J7 |
| D11 | HTML in `description` and consents is built only from our own templates; text taken from the paper is escaped and passed through an allow-list sanitiser (`nh3`, MIT). A hostile form must not become stored script in the partner's generator | research/16 |

## 3. The product has no language model and calls nothing

| # | Decision |
|---|---|
| D12 | Default path: readers, geometry, rules, lexicons. It must produce a valid, useful form alone. A model step exists only as an interface that picks from an enumeration, switched off; no weights are shipped |
| D13 | Nothing leaves the container at run time. An audit hook blocks name resolution and connects inside the worker; `GET /v1/selftest` reports the mode and proves it |
| D14 | Hosted models (the partner's credits) are used only while building: silver labels, lexicon mining, reviews by a second model family, research. Tool: `tools/eden/eden.py`. Nothing they produce is trusted without a rule or a test that keeps it |

## 4. Stack (verified in research/14)

| Job | Choice | Licence | Fallback |
|---|---|---|---|
| Language, web | Python 3.14, FastAPI, uvicorn, pydantic 2, python-multipart | MIT / BSD / Apache-2.0 | none |
| Images | **`core`** on `python:3.14-alpine` (default, honours "Alpine preferred"): rules, all readers except binary Word by office suite, Tesseract. **`plus`** on `python:3.14-slim-trixie`: second OCR engine, Morfeusz, optional LibreOffice. One Dockerfile, two targets, digests pinned | | |
| PDF | `pypdfium2` (render, character boxes), `pdfminer.six` or `pdfplumber` (lines, rectangles, tables), `pypdf` (declared form fields). PyMuPDF is AGPL: forbidden | Apache-2.0/BSD, MIT, BSD | |
| DOCX, XLSX, ODS | own readers on `zipfile` + `lxml` with entity declarations refused; `python-docx`, `openpyxl` where they help | BSD, MIT | |
| DOC (binary Word) | own small reader of the Word binary text (OLE container via `olefile`, piece table): text, paragraph and cell marks, no geometry. In `plus`: LibreOffice as a separately executed program, behind a switch, only if the mentors accept MPL-2.0 (J9) | BSD | answer 422 with the reason |
| Scans | Tesseract 5 with `pol` data from the Alpine repository; in `plus` RapidOCR on onnxruntime as the second opinion; OpenCV-free line and box detection first (run lengths on Pillow), OpenCV headless only in `plus` | Apache-2.0, HPND | |
| Conditions | built from a small typed predicate tree, written as JSONata, **evaluated before answering** with `jsonata-python`; the viewer uses the reference `jsonata` | Apache-2.0, MIT | |
| Polish wording | `simplemma` in `core`, Morfeusz2 in `plus`, plus our own table of frequent form phrases | MIT, BSD-2-Clause | raw words, flagged |
| Checks of values | our own check digits and formats (PESEL, NIP, REGON 9 and 14, KRS, identity card, land register, NRB/IBAN, postal code, e-Delivery address); `python-stdnum` is LGPL: not used | ours | |
| MIME, XML, token, schema | `filetype` or `puremagic` plus our container sniffing (ZIP parts, OLE streams); `defusedxml`; `PyJWT`; `jsonschema`; `rapidfuzz` | MIT, PSF, MIT, MIT, MIT | |
| Supply chain | digest-pinned bases, `pip --require-hashes`, SBOM (Syft or cyclonedx-bom), Grype and pip-audit as gates, licence gate, cosign | Apache-2.0 | |

Excluded with reason: PyMuPDF (AGPL), Surya and Marker (weights not open), MinerU (custom terms), spaCy Polish models (GPL-3.0), Pyphen, axe-core and pa11y (copyleft families), antiword and catdoc (GPL), python-stdnum (LGPL), Gemma weights (custom terms).

## 5. The accounting features (what the partner did not ask for)

Order of building after the mandatory minimum. Each has a package in `work-packages/WP-F-forms-to-json.md`.

1. **Two ink colours**: every node has an origin `paper`, `standard` or `reviewer`; the review page toggles "only what came from the paper".
2. **Ledger of blanks**: every place to fill found on the paper ends as a field, merged into another, left out with a named reason, or waiting for a decision. Never called accuracy.
3. **Do-not-guess receipt**: fee, who may apply, mandatory attachments are `stated` (with the quote), `not found` or `ambiguous`; never a silent default.
4. **Journeys**: six fixtures (self; another person through a pełnomocnik; entity through a reprezentant; entity through a pełnomocnik; address in Poland; address abroad) replayed against the generated conditions, plus the **zero-answer canary** (nothing chosen yet: conditional sections must stay hidden).
5. **Pre-import gate**: schema, partner rules, grid, every JSONata condition evaluated, HTML allow-list, references resolved. A failure is an error with the finding, never a broken JSON.
6. **Contradiction docket**: the eight places where the partner's materials disagree, each with our decision, the evidence and the switch. One slide and one page of the README.
7. **Parser airlock**: each upload is parsed in a short-lived worker process with limits; the API process holds the token key and never touches file bytes. A hung job is killed and the next one succeeds.
8. **Filled-form alarm and content-free audit**: a form that looks filled in (valid PESEL in a fill area, typed values, handwriting proxy) raises a warning; nothing is stored; audit events carry hashes and reason codes only.
9. **Stable ids and the legal redline**: two conversions of two versions of a form give a typed list of changes (fee, obligation, attachment, wording, layout).
10. **Proposals with evidence**: new dictionaries and new initial-data sources (`KRS`, `CEIDG`, `REGON`, e-Delivery address) in the sidecar, in the partner's own notation, each with where it was seen.
11. **Cost dial**: measured CPU seconds and memory per form by input class, extrapolated openly to 2,479 municipalities (count of 1 January 2026, source in `research/13`).
12. **Agent pack**: from the same model a JSON Schema, a tool description and a short text description, as files. No server, no submission.

Deliberately not built: a search product over the city's archive; a full editor of forms; any feature that needs a hosted model at run time.

## 6. What only the mentors can tell (asked through the owner's questionnaire)

The questionnaire with the owner's answers is a private artifact; its questions are in `docs/05-hackathon/mentor-questions/`. Until an answer arrives, the default in the right column applies.

| Id | Question | Default until answered |
|---|---|---|
| J1 | A small export with `REPEATING_SECTION`, `CHECKBOX`, `DATEPICKER`, `INFO_SECTION` | shapes inferred from the rules document; flagged in the report whenever used |
| J13 | May we test one import before the defence, or get a validator | our own gate |
| J2 | How the JSON is judged | assume import plus expert reading |
| J3 | Last page style | as in the exports (D5) |
| J4 | Validators accepted and scored | on (D8) |
| J5 | Exact dictionary identifiers | only the three seen (D9) |
| J6 | Metadata inside the JSON or beside it | beside it (D2) |
| J7 | Stable ids on re-import | stable (D10) |
| J8 | Hardware at the defence | our laptop, no GPU, no network |
| J9 | LibreOffice under MPL-2.0 for `.doc` | not used in `core` |
| J10 | Keys for file limits, pattern, length, date range | none written; proposals in the sidecar |
| J11 | Task materials in a public repository | new sets stay local |
| J12 | JSONata engine and version | conditions limited to the subset seen in the exports |

## 6a. Answers of the technical mentor (21 November, about 13:40)

The owner met the author of the partner's JSON description and noted the answers himself, in his own words. They are recorded here as he wrote them, with what follows for the build. The mentor set no hard requirements: **"propose interesting solutions"**.

| Id | Answer as noted | What follows |
|---|---|---|
| J1 | no extra export; the materials already describe how to use these components (the rules document) | shapes of `REPEATING_SECTION`, `CHECKBOX`, `DATEPICKER`, `INFO_SECTION` come from the rules document; every use is listed in the report |
| J13 | forms are added straight away; there is no import check to try | our own gate is the only check: it must be strict and visible |
| J2 | the jury has a sample and reads whether everything follows the standard; the number of fields may differ from their sample when ours is better and more convenient | the score is conformity with the design standard plus judgement, not a field-by-field match. Invest in the standard's rules and in clear structure |
| J3 | different interpretations are allowed | D5 stays (as in the exports) |
| J4 | our own validations on our own interpretation are allowed | D8 stays on |
| J5 | the dictionaries of the materials, or our own better ones | D9 relaxed: a well-argued own dictionary may be named in the form; the proposal with evidence stays in the sidecar |
| J6 | **in the same JSON** | extra keys do not break anything on their side. D1 and D2 stay the default (clean form, sidecar), and an option `META=inline` puts the same data under one top-level key; the judged results are delivered clean with the sidecar beside them |
| J14 | they do not have to work with that HTML | plain, minimal HTML from our templates is enough (D11 stays) |
| J7 | identifiers need not be added to the JSON | ids are not a contract. We still write deterministic UUIDs (they cost nothing and make diffs readable) |
| J8 | **the jury runs the solution on their own computer, in Docker: we publish the image somewhere.** | the image must be pullable: GitHub Actions builds and publishes it to the registry of the repository; that pipeline is part of the minimum, not an extra |
| J9 | no restriction: any open source may be used | LibreOffice is allowed for `.doc` and as a renderer. We still keep GPL and AGPL code out of what we link, because the task card names them |
| J10 | may be proposed, but they do not check it; own extra checks are not what matters now | validation keys beyond the standard go last in the order of work |
| J11 | **no; check the regulations** | the partner's materials left the repository on 21 November (they stay on the owner's machine); whether history must be cleaned is the owner's decision after he reads the regulations |
| J12 | JavaScript | the viewer and the tests evaluate conditions with the reference JavaScript implementation, the same engine as theirs |

Not said by the mentor but noted by the owner at J8: **by 19:00 today he must register that he takes this task.**

## 6b. Answers of the business side (21 November, about 14:10)

Noted by the owner at the meeting, in his own words; read from the questionnaire store (`biz`, version 41) at 14:13. The questions are in `docs/05-hackathon/mentor-questions/README.md` (ids `P…`). P17 was not answered.

| Id | Answer as noted | What follows |
|---|---|---|
| P1 | skipped | two ink colours keep their place; no claim on a slide that the partner asked for them |
| P2 | "Mile widziane" | the ledger of blanks stays feature 2; say "welcome", not "missing" |
| P3 | it depends: for a fee, an amount may be given from an analysis of the rates, and a service may also be free | **D15.** The fee receipt stays `stated` / `not_found` / `ambiguous`; in addition a **proposed amount** from a statutory rate table (for example stamp duty) may be attached, marked as a proposal with its legal basis, never written as a fact of the paper |
| P4 | "Urzędnik merytoryczny" | the review page speaks to the subject-matter official: plain words, no JSON terms in the decisions |
| P18 | "Wolno rozszerzać": the same data as they have, and extending is allowed | the library reproduces the standard sections unchanged; extensions enter the form behind switches (P19, P20) |
| P19 | "Tak, dodać" | **D16.** A path for the statutory representative (parent, guardian, curator): its own proof upload, no stamp duty; switch `STATUTORY_REPRESENTATIVE=on` (default on); a seventh journey in the fixtures |
| P21 | the forms are made for the resident, not for entrepreneurs; the note ends with "but it has to be checked", and **what** is to be checked was not written down (ambiguous; the owner may know) | no e-Delivery field is added to the contact block by default; where the paper itself asks for the address, the field gets the validator `ADE` (this is D8 and holds under either reading); for entities it stays a proposal in the sidecar |
| P5 | it depends on the application | the six journeys stay, plus the seventh of P19; a journey that a form cannot take is reported as `not_applicable` |
| P20 | "propose something interesting, in variants" | **D17.** The stamp-duty question of a power of attorney may be extended by the reason of exemption (spouse, parents, children, siblings); switch `POA_EXEMPTION=off` by default, shown in the viewer as a variant |
| P6 | "Tak" | new initial-data sources for entities (KRS, CEIDG, REGON, e-Delivery address) fit their plans: they stay proposals in the sidecar and get a line on slide 10 |
| P7 | treat it as an entity (a note; no option was chosen) | **D18.** A sole trader takes the entity path (design 6.4 said: a natural person with NIP and REGON) |
| P8, P9 | "our decision" | the redline and the form family stay last in the order of value |
| P10 | by the rules of the materials they sent | the task card decides: no GPU and no model remain our choice and our claim (D12) |
| P11 | identity document, street type, offices and authorities; "the rest probably too" | these three dictionary proposals are prepared first (feature 10) |
| P12 | "Wolno upraszczać więcej" | hints and labels may be simplified further; declarations, consents and quoted law stay verbatim (our own rule, unchanged) |
| P13 | does not apply, not known | the agent pack stays last; no claim about AI HUB |
| P14 | "our decision" | `FILLED_FORM=warn` stays the default |
| P15 | "Dzień lub więcej" | slide 3 may say that one form takes a day or more by hand, with the note „wg zespołu COI, 21.11.2026" |
| P16 | not known; anything may be corrected | the order of the checks on the review page stays ours |

## 6c. After the independent audit (21 November, about 17:00; program lead and build lead)

Source: tickets of an audit by hosted models of three vendors, kept in [`audit-tickets-2026-11-21.md`](audit-tickets-2026-11-21.md).

| Id | Decision |
|---|---|
| D19 | **Failure contract in three states.** Nothing readable: `422` with a plain Polish reason. Text read but the matter partly or not understood: `200` with the best form and a warning that every client sees (the response header `X-Converter-Warnings` with the count and the codes, and the review page), not only the sidecar. `500` only for our own faults. **`GATE_FAILED` stays `500`** (a form we built that fails the import gate is our fault), but only the blocking checks G1 to G4 (schema, partner rules, ids and references, conditions that do not parse) can raise it; G5 to G12 become warnings of a `200`. A condition that does not parse quarantines its dependent group (the guard stays, the group is kept), never deletes it |
| D20 | **The standard scaffold stays when the paper is silent.** A standard section or route (proxy, entity, fee) is pruned only on an explicit exclusion written on the paper (for example "Wniosek składa się wyłącznie osobiście"), with the quote in the sidecar |
| D21 | **Binary Word keeps the hand-made reader.** LibreOffice only if a measured comparison against each `.docx` sibling shows it clearly better (label Jaccard below 0.7 and not fixable in an hour) |
| D22 | **Front end: the review view first** (upload, fields of the matter first with page and snippet, warnings, standard sections collapsed, download byte-equal to REST); the e-service preview of a branch only if conditions ship |
| D23 | **arm64: nothing** until the jury's hardware is known (question to COI pending) |

## 7. Changes to this file

| Time | Change | Why |
|---|---|---|
| 21 Nov 13:50 | D9 relaxed (own dictionaries may be named), `META=inline` option added to D2, LibreOffice allowed, image publishing moved into the minimum, partner materials removed from the repository | answers J5, J6, J9, J8, J11 above |
| 21 Nov 14:17 | Section 6b added. New decisions D15 (a fee amount only as a marked proposal), D16 (path of the statutory representative, on by default, seventh journey), D17 (reason of exemption from stamp duty, behind a switch), D18 (a sole trader takes the entity path). Three dictionary proposals come first: identity document, street type, offices and authorities | answers P3, P19, P20, P7, P11 of the business side |
| 21 Nov 14:17 | Fact for every package: the image is published to `ghcr.io/andriishramko/shramko-asystent-urzednika` and is public (probe run on commit `d64c001`); nothing of the partner's sets is in git, so the image workflow proves itself on synthetic fixtures only | the probe workflow; `git ls-files data/coi` |
