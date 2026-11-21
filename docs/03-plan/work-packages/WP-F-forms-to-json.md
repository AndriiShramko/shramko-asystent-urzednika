# WP-F0 … WP-F13 — Track F: a form file in, the partner's JSON out

Track for the task "Cyfryzacja formularzy" as published on 21 November 2026. It replaces Track B (the counter product) as the build for that task. Why: [`../../01-product/coi-replan.md`](../../01-product/coi-replan.md). The card, with the ids `C-…` used below: [`../../05-hackathon/intake/coi-task-card.md`](../../05-hackathon/intake/coi-task-card.md).

Rules of this track, on top of `AGENTS.md`:

- **Nothing in the product calls out of the container.** No external API, no hosted model, no MCP client, no SaaS (C-TECH-NOEXT). A test in the gate starts the container without network and runs the conversion.
- Python 3.14, FastAPI. Every dependency is open source and not copyleft; `tools/licence_check.py` fails the gate on GPL, AGPL, LGPL or an unknown licence. Model weights and OCR data are dependencies too.
- Uploaded files live only in memory or in a temporary directory removed in a `finally` block; file content is never logged.
- The partner's materials (their sample forms, JSON files, rules, dictionaries) stay in `data/private/coi/`, which is git-ignored. What we commit is our own description of the format and our own outputs.
- Module layout: `apps/converter/` (service), `apps/review-web/` (front end), `contracts/coi/` (schema and examples written by us), `eval/` (evaluation). One package owns one folder.

| Id | Package | Depends on | Kind | Card |
|---|---|---|---|---|
| WP-F0 | Read the partner's materials; write the format description and the schema; golden pairs | none | think, lead | C-MAT |
| WP-F1 | Service shell: endpoint, guard, token, configuration, Docker, README | none | by spec | C-TECH |
| WP-F2 | Readers: every input format to one page model | F1 | by spec | C-TECH-FMT |
| WP-F3 | Field finder: places to fill, labels, groups, sections | F2 | think | C-MIN-1a |
| WP-F4 | Meaning: concept, type, required, paper habits translated, thematic pages | F3, F0 | think | C-MIN-1c |
| WP-F5 | Writer: the partner's JSON, validated; report | F0, F4 | by spec | C-MIN-1b |
| WP-F6 | Dictionaries and initial data; proposal of a new dictionary | F0, F4 | think | C-OPT-1, C-OPT-2 |
| WP-F7 | Dependencies and dynamic flows | F4 | think | C-OPT-3 |
| WP-F8 | Validation pack | F4 | by spec | C-OPT-6 |
| WP-F9 | Review front end: upload, tree, source view, batch table | F1 | by spec | C-OPT-4, C-OPT-6 |
| WP-F10 | Viewer: the e-service rendered from the JSON | F0 | by spec | C-OPT-5 |
| WP-F11 | Evaluation run and numbers | F5 | by spec | C-TEST |
| WP-F12 | Architecture document, README, licence list | F1…F8 | by spec | C-MIN-2, C-TECH-DOC |
| WP-F13 | Originality: agent-readable export; form family | F5 | by spec | originality |
| WP-P1 | Presentation, film, submission texts | F11 | think | C-SUB |

## WP-F0 — The partner's format (first hour, lead)

1. Put every file from the task's Discord section "materiały-dodatkowe" into `data/private/coi/` and list it (name, size, SHA-256, what it is) in `data/private/coi/INDEX.md`.
2. Write `docs/02-architecture/coi-json-format.md` in our words: every element of their JSON with its meaning, allowed values, required or optional, and one small example composed by us; the form-design rules as a numbered list; the dictionaries and initial data as a table (id, meaning, when to use).
3. Write `contracts/coi/form.schema.json` (JSON Schema) from the samples and the rules. Every sample JSON must validate against it; **negative control:** a sample with one required element removed must fail.
4. Pair the sample forms with their sample JSON files: `eval/golden.json` (paths inside `data/private/coi/`, no content).
5. List what the samples do not explain; hand the list to the owner as questions for the mentors, in Polish, the same hour.

Acceptance: the four files exist; all sample JSON files validate; the negative control fails; the open questions are in `docs/05-hackathon/ONSITE-INTAKE.md`.

## WP-F1 — Service shell

`POST /v1/forms/convert` (multipart, one file) returns the JSON; `GET /healthz`. Bearer token checked as JWT: algorithm, key or secret, issuer and audience come from configuration; missing or bad token is 401. Guard before any parsing: extension in the allowed list; content sniffed and equal to the extension (magic numbers; a ZIP container is opened to tell DOCX, XLSX and ODS apart); name at most 250 characters and free of `; : > < / \ | ' * % $`; size at most `MAX_UPLOAD_BYTES`. Errors as `application/problem+json` with a Polish message. Configuration through environment variables, documented, with safe defaults and no secret in the image. Dockerfile: official Python 3.14 base with a pinned version and digest, Alpine if every wheel exists, otherwise the slim image with the reason written in the README; a dedicated user without privileges; one exposed port; no `latest` anywhere; `docker compose up` starts service and front end. OpenAPI document generated and committed.

Acceptance: the image builds from a clean checkout and answers `healthz`; a valid PDF returns 200 with a body that validates against the schema (a stub form is enough at this point); **negative controls**, each a test: wrong extension; PNG bytes named `.pdf`; name with `%`; name of 251 characters; file one byte over the limit; no token; expired token; the container started with `--network none` still converts.

## WP-F2 — Readers

One page model for all formats: pages with text runs (text, box, font size, bold), lines, rectangles, tables with cells, images, plus what the format itself declares (PDF form fields; content controls and legacy form fields in DOCX; data-validation lists, merged cells and comments in XLSX and ODS). PDF with a text layer: geometry and text. DOCX: structure read directly, and a rendering to pages for geometry. XLSX and ODS: the sheet grid is the layout. DOC: converted (the tool depends on the mentors' answer about its licence; until then behind a switch). JPG, PNG and PDFs without text: OCR with an open engine and Polish data, line and box detection on the image; every text run carries a confidence.

Acceptance: for each of the eight extensions a fixture produces a page model with at least one text run and one candidate place; a broken file gives a 422 with a reason and no stack trace; the whole city archive (`data/forms-census.csv`, 661 documents) runs through the readers without an unhandled exception, with the count of failures and their reasons written to `eval/readers-archive.json`.

## WP-F3 — Field finder

From the page model to candidate fields: dotted and underscored leaders, rows of equal boxes (one field with a length), single boxes (tick or choice), table cells meant to be filled, declared fields. The label is the nearest text by reading order and geometry; groups are boxes that share a question; sections come from headings and numbering; notes, instructions, legal basis and clauses are kept as their own kinds, not as fields. Every candidate keeps its page and rectangle and a confidence. Method and thresholds of `tools/forms_census.py` and of WP-B6 are the starting point.

Acceptance: on the residence form the finder recovers at least the share of the 31 hand-measured fields recorded in the status file (`data/form-descriptor.example.json` is the reference); on the partner's samples it finds at least the recorded share of the fields named in their JSON; **negative control:** an information sheet without places to fill yields zero fields and a warning, not invented fields.

## WP-F4 — Meaning

Rules first, in this order: dictionary of known labels (Polish, with variants) to a concept of the canonical list (`data/canonical-profile.schema.json` is the seed); type and requiredness from the concept, the wording and marks such as an asterisk; paper habits translated (table in coi-replan §3 row 2); sections assigned to thematic pages by the partner's design rules. Then, only if the switch is on, a small open model inside the container answers closed questions about wording the rules could not decide; its answer is validated against an enumeration and retried once, otherwise the rule result stays and a warning is written. The model never sees more than labels and headings of a blank form.

Acceptance: with the model switched off the result still validates and every field has a type; the share of fields decided by rules alone is measured and reported; with the model on, the same forms give at least as many correctly typed fields on the golden pairs; **negative control:** a model answer outside the enumeration is rejected and logged.

## WP-F5 — Writer

Compose the partner's JSON from the internal model, in their order and naming, and validate it against `contracts/coi/form.schema.json` before answering. The report (warnings with page and place, confidence per field, seconds, hash of the input, which steps used the model) travels as the format allows: inside the answer if their structure tolerates extra elements, otherwise from `GET /v1/forms/report/{id}` kept in memory for a few minutes. Deterministic output: the same file gives the same JSON.

Acceptance: every golden form converts to a JSON that validates; the comparison with the partner's sample JSON is printed as fields matched, missing, extra; two runs on the same file are byte-identical; a form the readers could not fully read still answers 200 with warnings, or 422 when nothing was readable.

## WP-F6 — Dictionaries and initial data

Load the partner's dictionaries and initial data from configuration files derived in WP-F0. Link a field when its concept or its option list matches (exact concept first, then similarity of option texts above a threshold). Mark fields the state already knows about a logged-in person as initial data. When a group of options matches nothing, propose a new dictionary: a name, the entries, and where it was seen, in the report and, if their structure allows, in the JSON.

Acceptance: on the golden pairs the links agree with the partner's sample JSON at the recorded share; a made-up option list produces a proposal, not a wrong link; **negative control:** two similar but different dictionaries are not confused on the fixture written for it.

## WP-F7 — Dependencies and dynamic flows

Find conditions: wording ("jeżeli", "w przypadku", "dotyczy", "wypełnić, gdy"), a yes/no or tick in front of a section, alternative blocks ("pełnomocnik"). Write them in the partner's notation as field, section or page conditions. The viewer shows them as it would behave.

Acceptance: three fixtures with a known condition each (field, section, page) produce the expected dependency; a form without conditions produces none.

## WP-F8 — Validation pack

Per concept: type, length (from the count of boxes where present), pattern, and check digits where they exist (PESEL, NIP, REGON, bank account), postal code, phone, e-mail, dates and their ranges. Written into the JSON in the partner's notation; the same functions are used by the viewer. Each rule has unit tests with valid and invalid synthetic values.

Acceptance: every rule has at least one passing and one failing case; the residence form's boxed fields carry the right lengths.

## WP-F9 — Review front end

One page, Polish, keyboard-usable, WCAG 2.1 AA. Upload by drag or button; the result as a tree of pages, sections and fields beside the image of the original page with the found places outlined; selecting either highlights the other; fields the system is unsure about come first and can be filtered; the JSON can be read, copied and downloaded. Batch: several files or a ZIP give a table (file, state, fields, warnings, seconds) with the same detail view per row and one download of all results.

Acceptance: the three-minute film can be recorded on it without a cut; an accessibility scan shows no critical finding; a batch of fifty files of the archive finishes and the table matches the service's reports.

## WP-F10 — Viewer

Renders the e-service from a JSON file alone (pasted, uploaded or handed over by the review page): pages as steps, sections, fields with hints, dictionaries as lists, conditions live, validation messages in Polish. It is the proof that the JSON is a working form.

Acceptance: each partner sample JSON renders without an error; our own outputs for the judged forms render; a condition and a validation are shown working in the film.

## WP-F11 — Evaluation run

`python -m eval.run` converts the golden forms and the judged forms, compares with the samples, runs the archive in batch, and writes `eval/metrics.json`: fields matched, typed correctly, linked to dictionaries, share decided without a model, seconds per form (median and slowest), failures with reasons. It writes the JSON files for the judged forms into `results/` (committed: they are part of the submission, C-SUB).

Acceptance: `results/` holds one JSON per judged form and each validates; `metrics.json` is produced by one command on a clean checkout; the numbers in the presentation equal the file.

## WP-F12 — Architecture, README, licences

`README.md` at the top of the service: build, run, configuration table, the API with a `curl` example, limits. `docs/02-architecture/converter.md`: one diagram, the steps, what runs without a model, the data that never leaves the container, measured cost per form. `LICENCES.md`: every dependency, model and data file with its licence and source, produced by `tools/licence_check.py`.

Acceptance: a person who has not seen the project builds and calls the service from the README alone (the reviewer agent does it in a clean container); the licence check passes.

## WP-F13 — Originality (after the minimum and three extensions)

1. Agent-readable export: from the form JSON a second file with the form as a tool description (name, purpose, typed parameters with validation, which answers are choices from which dictionary, which fields come from initial data). A file, not a server. One screen in the review page shows it.
2. Form family: after each conversion compare the set of field concepts with the forms already converted; show the nearest ones with the overlap. On the archive: how many groups of near-identical forms one city holds.

Acceptance: the export validates as JSON Schema; the family view names the two residence forms of the archive as one family.

## WP-P1 — Presentation, film, submission

Concept and rules: [`../../05-hackathon/presentation/concept-document-deck.md`](../../05-hackathon/presentation/concept-document-deck.md). At most ten slides as PDF; a film of at most three minutes; title and description for HackTribe; every number from `eval/metrics.json`.

## Clock for this track

| When | What | Gate |
|---|---|---|
| Sat to 12:30 | F0 and F1 in parallel | schema validates the samples; image answers; open questions with the owner |
| Sat 12:30–17:30 | F2 (PDF, DOCX first), F3, F5 | a golden PDF and a golden DOCX convert to valid JSON through the API |
| Sat by 18:00 | HackTribe draft | owner confirms |
| Sat 17:30–23:30 | F4, F8, F6, F9 first cut; F2 for XLSX, ODS, DOC | three extensions visible in the JSON; upload page works |
| Sat 23:30–Sun 04:00 | F7, F2 for images, F10, batch in F9 | a scan converts with warnings; viewer shows a condition |
| Sun 04:00–08:00 | F11, F12, F13, hardening, clean-container run | `results/` complete; metrics file; README test passes |
| Sun 08:00–10:00 | P1: PDF, film, texts; submit by 10:30 | owner submits |
