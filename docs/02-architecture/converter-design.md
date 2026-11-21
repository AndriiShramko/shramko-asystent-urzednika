# The converter: detailed design (Track F)

Written on 21 November 2026, 13:40, by the preparing session. It follows [`../03-plan/DECISIONS-forms-track.md`](../03-plan/DECISIONS-forms-track.md) (ids `D1` … `D14` below refer to it; that file wins over this one). Format of the partner: [`coi-json-format.md`](coi-json-format.md). Packages that build this: [`../03-plan/work-packages/WP-F-forms-to-json.md`](../03-plan/work-packages/WP-F-forms-to-json.md).

Sources of the facts used here: `research/14` (stack, wheels, licences), `research/15` (the partner's platform), `research/16` (security), `research/18` (versions, exports, evaluation), the model reports in `research/eden/` (`e2` document analysis, `e3` identifiers and law, `e5` ideas), the forensic facts in `docs/05-hackathon/mentor-questions/reference-json-forensics.txt`, and our own reading of the nine sets in `data/coi/`. A statement marked *(inference)* is ours and is not shown by any material.

Words used below. **Paper**: the uploaded file, whatever its format. **Form**: the partner's JSON (`title`, `tabs`, `flow`). **Brief**: our small description of what the paper asks. **Sidecar**: our `meta` document that travels beside the form and never inside it.

## 1. One picture

```
client ── bearer token ──▶ API process (Z1)                      holds the token key, never parses a file
                             │ guard: name, size, extension, content proof          4xx with a reason
                             │ spawn one worker per upload, bytes over a pipe
                             ▼
                           worker process (Z2)                    no key, no network, limits, killed on timeout
                             read      pdf | docx | doc | xlsx | ods | image  ─▶ page model
                             find      places to fill, labels, groups, sections ─▶ candidates
                             mean      ten questions about the paper            ─▶ brief (with evidence)
                             compose   standard sections + pages of the matter  ─▶ form (partner JSON)
                             account   origins, ledger, omissions, receipts     ─▶ sidecar
                             gate      schema, rules, grid, conditions, journeys, HTML
                             │ one JSON document on stdout, size-capped
                             ▼
                           API process re-validates, answers:
                             POST /v1/forms/convert            ─▶ the form, nothing else (D1)
                             POST /v1/forms/convert?report=1   ─▶ multipart/mixed: form + sidecar (D2)
                             POST /v1/forms/report             ─▶ the sidecar alone
```

Nothing in this picture calls out of the container (D13). No language model takes part (D12).

## 2. Module layout

One package owns one folder ([`../03-plan/ownership.md`](../03-plan/ownership.md)).

```
apps/converter/
  Dockerfile                 two targets: core (Alpine) and plus (slim), section 9
  pyproject.toml             pinned dependencies with hashes
  README.md                  build, run, configuration, API (task card C-TECH-DOC)
  app/
    main.py                  API process: routes, token check, limits, worker spawning, answers
    cli.py                   the same pipeline without HTTP: python -m converter convert FILE [--report]
    config.py                environment variables -> typed settings, validated at start
    auth/                    token verification (algorithm allow-list, claims)
    guard/                   file name, size, extension, content proof per format, active-content inspection
    worker/                  entry of the worker process: egress guard, pipeline runner;
                             limits_posix.py and limits_windows.py behind one interface (section 9.3)
    model/                   pydantic models: page model, candidate, brief, form tree, sidecar
    readers/                 pdf.py docx.py doc.py xlsx.py ods.py image.py ocr.py raster.py
    find/                    candidates, reading order, label association, sections
    lexicon/                 data tables with source and date: phrases, concepts, label -> type, fees
    mean/                    the brief: rules for D1..D10, applicant model, paper habits
    compose/                 library/ (standard sections), matter pages, ids, grid, flow
    conditions/              predicate tree -> JSONata text; reference resolver; evaluator wrapper
    validation/              check digits and formats; concept -> partner validator name
    dictionaries/            linking to known dictionaries and initial data; proposals
    gate/                    schema, partner rules, grid, conditions, journeys, canary, HTML allow-list
    sidecar/                 origins, ledger, omissions, receipts, coverage, hashes -> meta
    privacy/                 filled-form alarm, content-free audit events
    security/                egress guard, self-test probes, sanitiser wrapper
    diff/                    two forms -> typed list of changes
    export/                  agent pack (JSON Schema, tool description, text), form family
    metrics/                 per-request resource report, cost aggregation
  tests/                     one folder per module; tests/evil/ holds the hostile corpus
apps/review-web/             one front end, two views (decision below)
contracts/coi/               form.schema.json (ours, strict), brief.schema.json, meta.schema.json, examples
eval/                        golden.json, run.py, score.py, silver/ (build-time labels), cost.py
results/                     the form and the sidecar for each judged set (part of the submission)
.github/workflows/image.yml  the CI that builds and proves the image (section 9.2)
tools/env_check.py           what this machine has and what to do about what it lacks (WP-F1, step 0)
```

**One front end with two views, not two applications.** View "Przegląd" is for the official: the paper beside the form tree, the ledger, the decisions. View "Podgląd e-usługi" renders the form as a citizen would see it, with live conditions and the journeys. One application because both views need the same JSONata evaluator, the same form model and the same component renderer; one build, one bundle, no second container. The static files are built in a Node stage of the Dockerfile and served by the API process under `/ui`; `UI_ENABLED=false` removes them from a deployment that wants the bare service. The reference `jsonata` library is bundled, never loaded from a network.

## 3. Endpoints

| Method and path | Token scope | Answer |
|---|---|---|
| `POST /v1/forms/convert` (multipart, one part `file`) | `convert` | `200 application/json`: the form (D1). Headers: `X-Input-SHA256`, `X-Form-SHA256`, `X-Converter-Version`, `Server-Timing` |
| `POST /v1/forms/convert?report=1` | `convert` | `200 multipart/mixed`: part `form.json`, part `meta.json` (D2) |
| `POST /v1/forms/report` | `convert` | `200 application/json`: the sidecar alone. Same input gives the same hashes as `convert` |
| `POST /v1/forms/inspect` | `convert` | what the guard sees without converting: type proof, pages, macros, external links, embedded files |
| `POST /v1/batches` (several parts `file`, or one ZIP) | `convert` | `200 application/x-ndjson`: one line per file as it finishes: name hash, state, counts, warnings, seconds, the form. Nothing is kept after the stream ends |
| `POST /v1/forms/diff` (two form JSON files) | `convert` | typed list of changes (section 6.9) |
| `POST /v1/forms/export` (one form JSON, optional sidecar) | `convert` | the agent pack as `multipart/mixed` |
| `GET /status` | none | service name and version, `engine: "rules"`, the token mode, the readable formats, the limits. The offline proof is not an endpoint: it is `convert` in a container started with `--network none` (section 8); a self-test endpoint was planned here and never built |
| `GET /healthz` | none | `200` when the worker pool answers |
| `GET /about/licences`, `/about/sbom`, `/about/build` | none | licence list, SBOM, git commit and base image digest |
| `GET /openapi.json`, `/ui/` | none | the generated API description; the front end |

The same pipeline runs without HTTP: `python -m converter convert FILE [--report DIR]` writes the form (and the sidecar) to files. CI uses it inside a container that has no network, the evaluation run uses it for the judged sets, and it is the quickest way to work on Windows. `python -m converter serve` starts the API and the front end without a container.

Errors are `application/problem+json` (RFC 9457) with a Polish `title` and a stable `code`:

```json
{
  "type": "https://formularze.flyreelstudio.eu/problems/type-mismatch",
  "title": "Zawartość pliku nie zgadza się z rozszerzeniem",
  "status": 415,
  "code": "TYPE_MISMATCH",
  "detail": "Rozszerzenie .pdf, a zawartość to obraz PNG.",
  "limits": {"max_upload_bytes": 20971520}
}
```

| Status | `code` | When |
|---|---|---|
| 400 | `BAD_NAME` | name longer than 250 characters or holding one of `; : > < / \ | ' * % $`, control or direction-override characters |
| 401 | `TOKEN_MISSING`, `TOKEN_INVALID`, `TOKEN_EXPIRED` | token check failed; the reason is never more specific than these three |
| 403 | `SCOPE` | token without the scope of the endpoint |
| 413 | `TOO_LARGE`, `TOO_MANY_PAGES`, `TOO_MANY_PIXELS`, `ARCHIVE_LIMIT` | a limit of section 4 or 8 |
| 415 | `EXTENSION`, `TYPE_MISMATCH`, `DOC_READER_OFF` | not one of the eight formats; content is another type; binary Word arrives while its reader is switched off |
| 422 | `UNREADABLE`, `NOT_A_FORM`, `ACTIVE_CONTENT` | nothing could be read; no place to fill was found; macros with `ACTIVE_CONTENT=strict` |
| 429 | `BUSY` | concurrency or rate limit, with `Retry-After` |
| 500 | `GATE_FAILED` | our own gate refused the result; the body names the failed check; **a broken form is never sent** |
| 504 | `TIMEOUT` | the job ran longer than `JOB_TIMEOUT_S`: no result is returned; the job is NOT killed, it ends in the background and counts against the slots until it does (at `CONCURRENCY` such jobs the next request is 429 `BUSY`) |

A paper that is partly unreadable still gives `200` with a valid form and warnings in the sidecar. `422 UNREADABLE` only when no text at all was obtained.

## 4. Configuration

Every value comes from the environment or from a file named by the environment; nothing secret is in the image (C-TECH-DOCKER, C-TECH-CONF). The service refuses to start on an inconsistent set (for example a public key given with `HS256`).

| Variable | Default | Meaning |
|---|---|---|
| `MAX_UPLOAD_BYTES` | `20971520` | largest upload (C-TECH-SIZE). The largest file of the judged sets is 6.7 MB |
| `MAX_PAGES` | `60` | pages per document |
| `MAX_PIXELS` | `80000000` | pixels of one decoded image. **Not lower: the scan of set 9 is 1654 × 37424 = 61.9 million pixels** |
| `JOB_TIMEOUT_S` | `600` | wall-clock limit of one conversion; over it the request answers 504 and the job ends in the background |
| `WORKER_MEMORY_MB` | `1024` | address-space limit of one worker |
| `CONCURRENCY` | `2` | workers at once; more uploads wait or get `429` |
| `RATE_LIMIT_PER_MIN` | `60` | per token subject |
| `AUTH_MODE` | `auto` | `auto`: JWT when a key file is configured, otherwise open; `jwt`: a key file is required, start refused without it (exit 3); `off`: open. An open start is logged as a warning and shown by `GET /status` |
| `JWT_ALG` | `HS256` | one of `HS256`, `HS384`, `HS512`, `RS256`, `ES256`, `EdDSA`; never read from the token |
| `JWT_SECRET_FILE` / `JWT_PUBLIC_KEY_FILE` / `JWT_JWKS_FILE` | none | the key, by file. A JWKS **URL** is not supported: the service calls nothing (D13) |
| `JWT_ISSUER`, `JWT_AUDIENCE` | none | required equal when set |
| `JWT_REQUIRED_CLAIMS` | `exp` | comma list; `exp` cannot be removed |
| `JWT_LEEWAY_S` | `30` | clock tolerance, at most 120 |
| `FINISH_STYLE` | `export` | `export`: `SECTION` with `TEXT_BLOCK` (D5); `info_section` |
| `VALIDATORS` | `on` | `off` writes empty lists as in the exports (D8) |
| `REPEATING_STYLE` | `native` | `native`: `REPEATING_SECTION`; `flat`: one plain section and a warning, for an importer that refuses the inferred shape |
| `STRICT_EXTENSIONS` | `false` | `false` accepts `.jpe` as JPEG when the content is JPEG (set 7 holds such a file); `true` accepts exactly the eight extensions of the card |
| `DOC_READER` | `native` | `native`, `libreoffice` (image `plus` only, D4 of the stack table), `off` |
| `OCR_LANGS` | `pol+eng` | Tesseract languages |
| `OCR_DPI` | `300` | rendering resolution of pages without text |
| `OCR_SECOND_ENGINE` | `off` | `on` in `plus`: agreement check with the second engine |
| `ACTIVE_CONTENT` | `warn` | `strict` refuses files with macros or DDE |
| `FILLED_FORM` | `warn` | `reject` answers 422 when the paper looks filled in |
| `FORM_KEY` | empty | fixed key for ids; empty: the slug of the title (D10) |
| `ID_NAMESPACE` | fixed UUID in the code | namespace of the ids; an office may set its own |
| `SIGN_OUTPUT` | `off` | `jws`: detached signature in `X-Content-Signature`; key from `SIGNING_KEY_FILE` |
| `MODEL_STEP` | `off` | the interface of D12; with `off` nothing is loaded |
| `UI_ENABLED` | `true` | serve the front end |
| `LOG_LEVEL` | `info` | logs are content-free at every level |

## 5. Data contracts

**Binding shape since 21 November, 14:28:** the pydantic models in `apps/converter/app/model/` and the examples in `contracts/coi/examples/` (the four schema files are generated from the models; a test fails on drift). The examples printed below are the first sketch and differ in three ways: our contracts never write `null` (a missing key means none), every stated value has one shape `{status, value, evidence[]}`, and the ledger closes by total, by row and by fate. The reasons are the nineteen decisions in [`../03-plan/wip/WP-F0b.status.md`](../03-plan/wip/WP-F0b.status.md). A step that needs a field the models lack asks the lead; it never adds a key of its own.

Schemas live in `contracts/coi/`. All coordinates are in points with the origin at the top left of the page.

### 5.1 Page model (output of every reader)

```json
{
  "source": {"sha256": "9f2c…", "format": "pdf", "reader": "pdf.native", "pages": 2},
  "pages": [{
    "number": 1, "width": 595.3, "height": 841.9, "origin": "native",
    "runs": [{"id": "r17", "text": "Nazwa /Imię i nazwisko", "box": [56.7, 212.4, 190.2, 223.9],
              "size": 9.0, "bold": false, "conf": 1.0}],
    "lines": [{"id": "l3", "box": [56.7, 240.1, 538.6, 240.1], "style": "solid"}],
    "rects": [{"id": "q41", "box": [200.1, 228.0, 212.0, 242.0]}],
    "tables": [{"id": "t1", "box": [56.7, 300.0, 538.6, 380.0],
                "cells": [{"r": 0, "c": 0, "rs": 1, "cs": 2, "box": [56.7, 300.0, 297.6, 320.0], "runs": ["r20"]}]}],
    "widgets": [{"id": "w1", "kind": "text", "name": "nip", "box": [220.0, 228.0, 360.0, 242.0],
                 "max_len": 10, "comb": true}]
  }]
}
```

- `origin`: `native` (text and vectors from the file), `ocr` (recognised from pixels; every run has `conf` below 1), `flow` (a format without page geometry: binary Word, a DOCX made of ordinary paragraphs). In `flow` pages `box` is absent and every run carries an `anchor` instead: `"p[12]"` for a paragraph, `"p[12]/cell[2,3]"`, `"Arkusz1!B7"` for a sheet cell. Readers never invent coordinates.
- `widgets` are what the format itself declares: PDF form fields, content controls and legacy form fields of Word, data-validation lists of sheets.
- The page model is the only thing the later steps see. No step opens the file again.

### 5.2 Candidate (output of the finder)

```json
{"id": "c12", "kind": "comb", "page": 1, "box": [220.0, 228.0, 360.0, 242.0], "cells": 11,
 "label": {"text": "PESEL", "runs": ["r31"], "how": "left", "margin": 0.42},
 "group": null, "section": "s2", "footnotes": ["*"],
 "conf": {"geometry": 0.95, "label": 0.80, "text": 1.0}}
```

`kind` is one of: `leader` (dots or underscores to write on), `line_block` (several dotted lines: a long text), `comb` (a row of equal boxes: one value), `box` (one small square), `choice_group` (boxes or crossed-out alternatives that share a question), `cell` (an empty table cell under or beside a header), `widget`, `blank_in_sentence`, `signature`, `office_use`. Text that is not a candidate gets a role too: `heading`, `note`, `instruction`, `legal_basis`, `clause`, `page_furniture`. `label.margin` is the score distance to the second-best label; a small margin lowers confidence.

### 5.3 Brief (output of the understanding step)

The answers to questions D1–D10 of `coi-json-format.md` §8, each with evidence. Example cut from judged set 2 ("Wniosek o zwrot opłaty skarbowej"):

```json
{
  "brief_version": 1,
  "input": {"sha256": "9f2c…", "format": "pdf"},
  "title": {"status": "stated", "value": "Wniosek o zwrot opłaty skarbowej",
            "evidence": [{"page": 1, "runs": ["r3"], "quote": "Wniosek o zwrot opłaty skarbowej"}]},
  "addressee": {"status": "stated", "kind": "office", "name": "Urząd Gminy Stawiguda",
                "evidence": [{"page": 1, "runs": ["r2"], "quote": "Urząd Gminy Stawiguda"}]},
  "applicants": {"status": "stated", "self": true, "other_person": true, "entity": true,
                 "capacities": ["pelnomocnik"],
                 "evidence": [{"quote": "Nazwa /Imię i nazwisko"}, {"quote": "NIP"},
                              {"quote": "Adres siedziby lub miejsca zamieszkania"}, {"quote": "2.4. Dane pełnomocnika"}]},
  "applicant_extras": [{"concept": "nip", "party": "entity", "required": false}],
  "matter": [
    {"title": "Informacje o opłacie skarbowej", "role": "matter/oplata", "fields": [
      {"key": "data_uiszczenia_oplaty", "label": "Data uiszczenia opłaty", "type": "DATEPICKER",
       "concept": "date", "required": true, "candidate": "c21", "conf": 0.90},
      {"key": "wysokosc_oplaty", "label": "Wysokość opłaty", "type": "NUMBER", "concept": "amount_pln",
       "required": true, "candidate": "c22", "conf": 0.85},
      {"key": "nazwa_organu_w_ktorym_zaplacono_oplate", "label": "Nazwa organu, w którym zapłacono opłatę",
       "type": "TEXT_FIELD", "required": true, "candidate": "c23", "conf": 0.90}]},
    {"title": "Uzasadnienie", "role": "matter/uzasadnienie", "fields": [
      {"key": "uzasadnienie", "label": "Uzasadnienie", "type": "TEXTAREA", "required": true,
       "hint": "Opisz, dlaczego opłata skarbowa została błędnie uiszczona.", "candidate": "c24", "conf": 0.90}]},
    {"title": "Sposób zwrotu opłaty", "role": "matter/zwrot", "fields": [
      {"key": "sposob_zwrotu", "label": "Wybierz sposób zwrotu opłaty", "type": "RADIO",
       "options": ["Gotówką w kasie organu", "Przelewem na rachunek w banku"], "required": true, "candidate": "c25"},
      {"key": "numer_rachunku", "label": "Numer rachunku", "type": "TEXT_FIELD", "concept": "nrb", "length": 26,
       "show_if": {"field": "sposob_zwrotu", "is": "Przelewem na rachunek w banku"}, "candidate": "c26"},
      {"key": "dane_wlasciciela_rachunku", "label": "Dane właściciela rachunku", "type": "TEXT_FIELD",
       "show_if": {"field": "sposob_zwrotu", "is": "Przelewem na rachunek w banku"}, "candidate": "c27"}]}
  ],
  "attachments": [{"label": "Dokument stwierdzający udzielenie pełnomocnictwa", "covered_by": "standard/pelnomocnictwo"},
                  {"label": "Dowód uiszczenia opłaty skarbowej za pełnomocnictwo", "covered_by": "standard/oplata_skarbowa"}],
  "declarations": {"consents": [], "clause": {"status": "not_found"}},
  "fee": {"status": "not_found"},
  "legal_basis": {"status": "stated", "quote": "Art. 9 ustawy z dnia 16 listopada 2006 r. o opłacie skarbowej"},
  "dropped": [
    {"what": "1. Instrukcja wypełnienia dokumentu", "reason": "PAPER_INSTRUCTION", "page": 1},
    {"what": "2.1–2.4 dane wnioskodawcy i pełnomocnika", "reason": "COVERED_BY_STANDARD", "page": 1},
    {"what": "8. Data i podpis wnioskodawcy", "reason": "SIGNATURE_AND_DATE", "page": 2}]
}
```

`status` is always one of `stated` (with a quote), `not_found`, `ambiguous` (with the competing quotes). A value is never filled in without one of the three.

### 5.4 Sidecar `meta` (keyed by the ids of the form)

```json
{
  "meta_version": 1,
  "converter": {"version": "0.4.0", "image": "core", "profile": "FINISH_STYLE=export;VALIDATORS=on;REPEATING_STYLE=native"},
  "hashes": {"input_sha256": "9f2c…", "form_sha256": "41aa…", "brief_sha256": "77b0…"},
  "origins": {"<field id>": "paper", "<field id>": "standard", "<field id>": "reviewer"},
  "evidence": {"<field id>": {"page": 2, "box": [70.9, 130.2, 300.0, 144.0], "quote": "Wysokość opłaty", "candidate": "c22"}},
  "confidence": {"<field id>": {"value": 0.85, "parts": {"geometry": 0.95, "label": 0.80, "text": 1.0, "rule": 0.7}}},
  "ledger": {
    "blanks_found": 31,
    "became_field": 9, "merged": 14, "covered_by_standard": 6, "left_out": 2, "awaiting_decision": 0,
    "rows": [{"candidate": "c26", "fate": "FIELD", "field": "<field id>"},
             {"candidate": "c40", "fate": "MERGED", "into": "c26", "why": "COMB_CELLS"},
             {"candidate": "c05", "fate": "STANDARD", "section": "twoje_dane"},
             {"candidate": "c61", "fate": "LEFT_OUT", "reason": "SIGNATURE_AND_DATE"}]
  },
  "omissions": [{"what": "1. Instrukcja wypełnienia dokumentu", "reason": "PAPER_INSTRUCTION", "page": 1}],
  "receipts": {
    "fee": {"status": "not_found"},
    "who_may_apply": {"status": "stated", "quote": "Nazwa /Imię i nazwisko"},
    "mandatory_attachments": {"status": "ambiguous", "quotes": ["7. Załączniki (postaw „x” w wybranym polu)"]}
  },
  "coverage": {"runs_total": 96, "assigned": 96, "unassigned": []},
  "decisions": [{"id": "dec-1", "question": "Czy numer rachunku jest wymagany przy zwrocie przelewem?",
                 "resolves": ["warning-3", "warning-4"], "default": "tak"}],
  "warnings": [{"id": "warning-3", "code": "REQUIRED_INFERRED", "field": "<field id>", "page": 2}],
  "unsupported": [],
  "proposals": {
    "dictionaries": [],
    "initial_data": [{"field": "<field id>", "source": "KRS.name", "why": "pole „Nazwa” w sekcji danych podmiotu"}],
    "validators": [{"field": "<field id>", "name": "NRB", "why": "26 kratek, etykieta „Nr rachunku”"}]
  },
  "concepts": {"<field id>": "http://data.europa.eu/m8g/…"},
  "legal_basis": {"quote": "Art. 9 ustawy z dnia 16 listopada 2006 r. o opłacie skarbowej", "eli": null},
  "checks": {"schema": "pass", "partner_rules": "pass", "grid": "pass", "conditions": {"total": 31, "evaluated": 31, "failed": 0},
             "journeys": {"run": 6, "passed": 6, "not_applicable": 0}, "zero_answer": "pass", "html": "pass"},
  "resources": {"wall_ms": 840, "cpu_ms": 610, "peak_rss_mb": 142, "pages": 2, "ocr_pages": 0}
}
```

Rules: the ledger must close (`blanks_found` equals the sum of the five fates) or the gate fails; it is called a ledger and never accuracy, because a blank the finder missed is outside it. `unsupported` lists behaviour of the paper that the partner's format cannot express as far as the materials show (a computed sum, for example). `proposals` is the only place for dictionaries, sources and validators that the partner has not named (D9).

## 6. The steps and their rules

### 6.1 Guard (API process, before any parsing)

1. File name: normalise to NFC; at most 250 characters; none of `; : > < / \ | ' * % $`; no control, NUL or direction-override characters. The name is never a path, never logged; only its hash and extension are kept.
2. Extension, case-insensitive (the sets contain `.PDF`, `.DOC`, `.ODS`, `.PNG`, `.JPG`): `pdf doc docx ods xlsx jpg jpeg png`. `.jpe` is treated as `jpeg` unless `STRICT_EXTENSIONS=true`.
3. Size: `Content-Length` first, then bytes counted while reading.
4. Content proof, so that content matches the extension (C-TECH-MIME). A generic sniffer says "zip" for three of our formats, so each has its own proof:

| Extension | Proof |
|---|---|
| `pdf` | `%PDF-` at offset 0 and an `%%EOF` marker in the tail |
| `docx` | ZIP with `[Content_Types].xml` and `word/document.xml` |
| `xlsx` | ZIP with `[Content_Types].xml` and `xl/workbook.xml` |
| `ods` | ZIP whose `mimetype` member says `application/vnd.oasis.opendocument.spreadsheet` |
| `doc` | OLE compound file with a `WordDocument` stream (a legacy workbook renamed `.doc` has a `Workbook` stream and fails) |
| `jpg`, `jpeg` | JPEG start marker; decodable header; one frame |
| `png` | PNG signature; decodable header; not animated |

A file that passes two proofs (a polyglot) is refused. The declared part type of the upload is a third opinion; a disagreement is refused.

5. Archive limits for the three ZIP formats, enforced on bytes actually read: at most 2,000 members, 50 MB per member, 200 MB in total, ratio 100:1; no member name with `..`, a leading slash, a backslash or a drive letter; no archive inside an archive. Nothing is ever extracted to disk.

### 6.2 Readers

Every set of the partner holds one form in up to eight formats, and the files differ in kind far more than in extension. Verified on the sets:

| Format | What the sets really contain | Reader |
|---|---|---|
| PDF | text layer and vector lines in every set; no scan-only PDF among them (the defence may bring one) | text and character boxes with `pypdfium2`, lines and rectangles with `pdfminer.six`/`pdfplumber`, declared fields with `pypdf`. A page with fewer than 20 characters of text is rendered at `OCR_DPI` and goes the image way |
| DOCX | **two kinds.** Sets 3, 4, 6, 9: ordinary paragraphs (set 9 has 282 paragraphs and no table; boxes are the character `□`). Sets 2 and 8: the whole page is **text boxes** made by a PDF-to-Word conversion (130 and 1,302 `w:txbxContent`, no body text; `python-docx` returns nothing) | own reader on `zipfile` + `lxml`: body paragraphs, tables, tabs and leaders, symbols, content controls (`w:sdt`), legacy form fields (`FORMTEXT`, `FORMCHECKBOX`), footnotes; and text boxes with their anchor offsets, which give a page with geometry (`origin: native`) |
| XLSX | the sheet grid is the layout: 35 to 759 merged ranges per form, no data-validation list, set 9 has four sheets | cells, merged ranges, borders, column widths and row heights from the XML; an empty bordered range beside or under a label is a place to fill; hidden sheets are read for option lists and reported |
| ODS | same layout as the XLSX | own reader of `content.xml`: rows and cells with repeat counts **bounded before expanding**, spans, text, automatic styles for borders |
| DOC | binary Word; present in every set | own reader (section 6.2.1); `origin: flow` |
| JPG, JPEG, PNG | 1654 pixels wide (A4 at 200 dpi), **all pages stacked in one tall image**: 4,678 pixels for two pages, 14,034 for six, 37,424 for sixteen | decode with Pillow restricted to JPEG and PNG, drop metadata, cut into pages at the A4 ratio snapped to the nearest band of white rows, then OCR and raster detection per page |

#### 6.2.1 Binary Word without an office suite

The `core` image has no LibreOffice (D of the stack table; question J9). The native reader does the minimum that the rules need: the OLE container is opened with `olefile`; the `WordDocument` stream gives the file information block; the table stream named there gives the piece table; the pieces give the text, as 8-bit code page or UTF-16. Marks kept: paragraph end, cell end, row end, page break, tab. Field codes between the field-begin and field-separator marks are read only to recognise `FORMTEXT` and `FORMCHECKBOX`; their results are kept as text. Output is a `flow` page model: paragraphs and table cells in order, leaders as text. Encrypted or fast-saved files that the reader cannot follow answer `422 UNREADABLE` with the reason; in `plus` with `DOC_READER=libreoffice` they are converted by a separately executed, unmodified office program with its own profile folder and a timeout. *(Inference: the Word binary layout is public, the reader is about 200 lines; it is the one reader we have not seen working.)*

#### 6.2.2 Pixels

OCR: Tesseract with `pol+eng`, word boxes and word confidence from its TSV output, run as a subprocess on a re-encoded PNG. Raster detection without OpenCV: horizontal and vertical run lengths for lines; connected components for near-square boxes; periodic small components on one baseline for dotted leaders; equal boxes with equal gaps for combs. In `plus`, the second engine reads the same strips and the agreement of the two per line becomes part of the confidence (section 7.5).

### 6.3 Finder: from the page model to candidates

1. **Reading order**: columns and enclosures first; recursive cuts along whitespace; tables stay whole and are walked by row; a heading goes before what it heads. In `flow` pages the order is the file's own.
2. **Roles of text**: page furniture (running headers, "Strona 1 z 2", version marks, "Załącznik nr … do …", stamps), headings (numbering such as `2.1`, `B.3`, capitals, bold, size), instructions, footnotes and their marks, legal basis, the data-protection clause, signature and date lines, office-only parts.
3. **Candidates** by kind (list in 5.2). A row of at least three equal boxes with equal gaps is one `comb` with its count; never one field per box. Dots or underscores of at least eight characters are a `leader`; two or more dotted lines without a label between them are one `line_block`.
4. **Labels**: a score, not "nearest text wins". Order of preference: the declared name of a widget; text in the same cell; text joined by the leader; text directly left; text directly above; row and column headers for an empty cell; for a choice group, the question above plus the text beside each box. Crossing a ruled line costs more than distance.
5. **Groups**: boxes that share a question, and crossed-out alternatives (6.4.3), become one `choice_group`.

Hard cases the finder must pass, taken from the sets: an eleven-cell PESEL comb is one field; `❑ pies ❑ suka` is one group of two; `□` in running text of a DOCX is a box; the date comb `DD-MM-RRRR` with printed separators is one date; a postal code comb with a printed hyphen is one postal code; an instruction paragraph with a drawn example of a ticked box is not a group.

### 6.4 Understanding: the brief

Rules only (D12). Lexicons are data files with a source and a date, so a rule changes without code.

#### 6.4.1 Title, addressee

- Title: the largest or boldest heading that starts with or contains "wniosek", "deklaracja", "zgłoszenie", "oświadczenie"; lines split by layout are joined ("WNIOSEK" / "o" / "wynajęcie/użyczenie* świetlicy wiejskiej"); written in sentence case; references to legal acts removed; a header such as "Załącznik nr 2 do Regulaminu …" is never the title. Crossed-out alternatives inside a title are kept as "lub" ("Wniosek o wynajęcie lub użyczenie świetlicy wiejskiej").
- Addressee: a block with the name of an office or body and an address, or a section headed "Organ, do którego …". A body ("Wójt", "Burmistrz", "Prezydent Miasta", "Starosta") gives "Organ / Nazwa organu"; an office gives "Urząd / Nazwa urzędu". When the paper names two different offices (set 6 does: one in the addressee, another in the clause), the addressee block wins and the sidecar carries a warning `ADDRESSEE_CONFLICT` with both quotes.

#### 6.4.2 Who may apply: three separate notions

| Notion | Meaning | Where its data come from |
|---|---|---|
| The **person at the keyboard** | whoever is logged in and signs | `MLPZ` or `PESEL` initial data, read-only identity (D6) |
| The **party** | on whose behalf: the person, another person, an entity | typed, or proposed sources for entities (sidecar) |
| The **capacity** | why this person may act for the party: pełnomocnik, reprezentant, przedstawiciel ustawowy | choice, plus proof (upload) |

A field belongs to a notion, not to a page. The person's address is never copied into the entity's seat. The wording of the paper selects which options exist:

| Wording found on the paper | Party options | Capacities | Standard sections that follow |
|---|---|---|---|
| only data of a natural person: "imię i nazwisko", PESEL, "adres zamieszkania" | self and another person (the partner's standard, page 10, asks for both) | pełnomocnik for the other person | Podmiot wniosku with two options; Twoje dane; Adres zamieszkania; Dane innej osoby; Adres zamieszkania innej osoby; Pełnomocnictwo; Opłata skarbowa |
| only data of a company or institution: "nazwa", "siedziba", NIP, REGON, KRS | entity | pełnomocnik, reprezentant | Twoje dane; Dane podmiotu; Adres siedziby; Potwierdzenie, że jesteś reprezentantem; Pełnomocnictwo; Opłata skarbowa |
| both: "imię i nazwisko / nazwa", "nazwa firmy", "adres zamieszkania / siedziby" | self, another person, entity | pełnomocnik, reprezentant | all of the above (this is what both exports show) |
| the matter can only be done in person (the paper says so, or the official decides) | self only: the section "Podmiot wniosku" is left out (standard, page 9) | none | Twoje dane; Adres zamieszkania |
| "rodzic / opiekun prawny", "przedstawiciel ustawowy" (set 9) | the paper's consent of a parent or guardian stays in the matter, shown when the candidate is a minor | the standard block has two capacities only; a third one, przedstawiciel ustawowy (other proof, **no stamp duty**: `research/17`), is a proposal in the sidecar | no change of the standard block |
| "klub sportowy", "wspólnota mieszkaniowa", "spółdzielnia", "inny podmiot" (sets 8, 9) | entity (with the printed kinds as a choice) | reprezentant, pełnomocnik | Dane podmiotu with the kind as RADIO or SELECT |
| "*PESEL wpisują osoby fizyczne …, NIP pozostali" (reference 5) | self and entity | as above | PESEL from the register for the person, NIP for the entity |

A sole trader stays a natural person with NIP and REGON added, not an entity (`research/eden/e3`); question P7 of the questionnaire asks the mentors to confirm. Fixed facts used by the library, with their source in the lexicon: stamp duty for a power of attorney is 17 zł with the exemptions for close family; a certificate costs 17 zł unless the paper says otherwise (`research/17` §3 with the articles of the act; `research/eden/e3` agrees). The standard's fee section already carries the partner's own wording; we do not write a new one.

#### 6.4.3 Paper habits translated

| On the paper | In the form | When left out: reason code |
|---|---|---|
| a row of boxes for one value | one field; the count becomes the length; the concept (PESEL, NIP, date, postal code, account) comes from the label and the count | |
| `dd-mm-rrrr`, "od … do …" | `DATEPICKER`; a from–to pair is two dates in one section | |
| "wynajęcie/użyczenie*" with "*niepotrzebne skreślić" | one `RADIO` with the alternatives; when the same alternative recurs in a sentence it is the same field, asked once | |
| "hodowanie/utrzymywanie* charta/chartów*" where the alternatives are only grammar (singular or plural) | no field; the neutral wording goes into the label | `GRAMMAR_VARIANT` |
| tick boxes that share a question | `RADIO` when the wording or the content excludes ("pies / suka", "tak / nie", "zaznaczyć właściwą kratkę"); `CHECKBOX` when several may hold ("zaznacz wszystkie, które dotyczą"); `SELECT` above five options, with search above fifteen | |
| an option followed by a blank ("inne ……", "mikroprocesor ……") | the option, plus a text field shown when it is chosen | |
| a footnote that makes something optional ("1) Dane nieobowiązkowe", "/**Opcjonalnie/", "(opcjonalnie)", "pola nieobowiązkowe") | the field without `REQUIRED` | |
| a footnote or bracket that states a condition ("wypełnić tylko w przypadku zaznaczenia kratki w poz. B 1.1.2", "jeśli różni się od …", "w przypadku, gdy …") | a `SHOW` state when the referenced answer resolves; otherwise a hint and a decision for the official | |
| "(rodzaj uroczystości, np. wesele, urodziny …)" under a line | hint of the field | |
| a table of equal empty rows; "w przypadku więcej niż jednego … pobrać odpowiednią liczbę załączników" | `REPEATING_SECTION` with the columns as fields | |
| printed arithmetic ("× stawka =", "razem", "SUMA poz. 51 lub 67 oraz 68") | the operands and the results are plain `NUMBER` fields; fixed rates are text in a `TEXT_BLOCK`; the arithmetic itself goes to `unsupported` | `COMPUTED_VALUE` for the note |
| "Załączniki:" with a list | one `FILE_UPLOADER` per named item; an item with "jeżeli", "w przypadku" is shown by a condition when it resolves, optional otherwise; open lines "2) …… 3) ……" become one uploader "Inne załączniki" | |
| "Oświadczam, że …" items | one `CONSENT_SECTION`; each item one consent; never a lone checkbox | |
| the data-protection clause | a consent with a link, as in both exports; the text is not copied | `CLAUSE_LINKED` |
| applicant block (name, address, PESEL, phone, e-mail) | the standard sections; phone and e-mail go to "Dane do kontaktu" | `COVERED_BY_STANDARD` |
| "miejscowość, data", "podpis wnioskodawcy", "czytelny podpis" | nothing; the last page tells the citizen to check the preview before signing | `SIGNATURE_AND_DATE` |
| "wypełnia organ", "Nr sprawy", "adnotacja organu", "miejsce na pieczęć" | nothing | `OFFICE_USE` |
| "WYPEŁNIJ WIELKIMI LITERAMI", "wypełniaj kolorem czarnym" | nothing | `PAPER_INSTRUCTION` |
| page numbers, version marks, "Załącznik nr … do zarządzenia …" | nothing | `PAGE_FURNITURE` |
| explanations keyed to positions ("Objaśnienie dotyczące części D.1 …") | hint of the field or section they name; the rest left out with the count | `EXPLANATION` |
| a fee stated on the paper ("Opłata skarbowa – 82 zł", account number) | a `TEXT_BLOCK` with the quote and a `FILE_UPLOADER` for the proof of payment; the receipt says `stated` | |

Required or not: required when the paper marks it or when the field is the substance of the request; optional when a footnote, a bracket or the standard says so; everything else is `REQUIRED_INFERRED` in the sidecar, so the official sees which ones were our call.

Labels are written by the standard's rules: sentence case, no trailing colon, no legal reference, the noun phrase before a blank put into the nominative by the phrase table first, by the lemmatiser second, as raw words with a flag last.

#### 6.4.4 Composite papers

Set 9 is three applications in one file, and the partner names the set "połączenie 3 wniosków w 1": one e-service is expected. Rule: when a paper has a list "Rodzaje wniosków" or repeats a title pattern with its own body, the form opens with one `RADIO` "Wybierz rodzaj wniosku" and each variant's sections carry a `SHOW` state on it. Sections that are word-for-word equal across variants are emitted once without a condition. When the bodies have nothing in common and no selector is printed, the brief says `COMPOSITE_UNRESOLVED` and the official decides; we never emit three forms from one upload.

### 6.5 Composer

1. **Library of standard sections** (`compose/library/`): one builder per section of `coi-json-format.md` §7, cut from the two exports, with the names as parameters and the suffix convention of D7. A test rebuilds every standard section of both exports and compares it with the export, ignoring ids. Where the two exports differ (export 1 has REGON and KRS in "Dane podmiotu", export 5 has only NIP; export 1 takes identity from `MLPZ`, export 5 from `PESEL` with the PESEL number), the builder takes a parameter and the brief sets it: PESEL shown and sourced from the register when the paper asks for PESEL; REGON and KRS when the paper names them.
2. **Pages**: "Dane" (parties), one or more pages of the matter, "Kontakt z urzędem" or "Kontakt i zgody" (contact, consents), "Strona końcowa" (`FINISH`, D5). A matter page holds at most about eight to ten fields; sections of the paper map to sections; a new page starts at a top-level heading of the paper when the page is full.
3. **Alternative content** *(inference; the materials do not show how the importer expresses a conditional page: `flow.links` has only `id`, `source`, `target`)*. Pages stay in one linear chain. What depends on an answer is a section with a `SHOW` state. **No page may become empty on any journey**: the composer keeps at least one unconditional component on every page (a short `TEXT_BLOCK` naming the step if nothing else), and the gate checks it.
4. **Repeating sections** (`REPEATING_STYLE=native`): `type: "REPEATING_SECTION"` in the place of a section, children in `repeatingSectionGrid`, conditions inside it in the second notation of the partner's rules (`__userAnswer[$repeatingSectionIndex]`). No export shows one; every use is listed in the sidecar as `INFERRED_SHAPE` until question J1 is answered.
5. **Grid and order** by D3, D4: one column; section `y` continues from the previous section's `y + rows`; `questionOrder` equals `y`.
6. **Ids** (D10): `uuid5(ID_NAMESPACE, "<form key>/<page role>/<section role>/<field key>")`. The form key is the slug of the title unless `FORM_KEY` is set. Roles are meanings, not positions (`dane/twoje_dane/imie`, `matter/zwrot/numer_rachunku`); a second instance of the same role in one parent gets `#2`. Flow links: `uuid5(namespace, "<form key>/flow/<source role>→<target role>")`. Option `id` and `name` are the visible text and `techName` its slug, as in the exports. Consequence: the same paper gives byte-identical output; a changed label changes no id; a moved field keeps its id as long as its role holds.
7. **`techName`** (D7): slug of the label (ASCII, lower case, `_`), cut to 60 characters at a word boundary, made unique across the form with the role suffix first and a number last. JSONata paths refer to page titles and techNames, so both come from one function and are checked by the resolver.
8. **HTML** (D11): `description`, text blocks and consents are rendered from our templates; any text from the paper is escaped, then the whole string passes the allow-list (`p`, `br`, `strong`, `em`, `ul`, `ol`, `li`, `a` with `https` targets only).

### 6.6 Dictionaries, initial data, proposals

- Known dictionaries only (D9): country fields get `Kraje` with default `["Polska"]`; Polish addresses get the territorial multi-level select as in the exports. **The two exports disagree on which of the two territorial dictionaries an address gets**: export 1 uses `TERYT_DOWODOWY` for the applicant and `TERYT_4G_DOWODOWY` for the entity and the other person; export 5 uses `TERYT_4G_DOWODOWY` for the applicant and the entity and `TERYT_DOWODOWY` for the other person. We write `TERYT_4G_DOWODOWY` for all three (four of the six uses), keep it a parameter of the address builder, and list it in the contradiction docket; question J5 settles it.
- Initial data only from the three documented sources and only for the person at the keyboard: `MLPZ.*`, `PESEL.*`, `PESEL_ADDRESS.*` with `defaultValueType: "EXTERNAL_SYSTEM"`; read-only for identity, editable for address and contact (D6).
- Proposals (sidecar only): a group of options that recurs or looks like a register value becomes a proposed dictionary with its name, entries, the literal variants seen and the pages; entity fields get proposed sources in the partner's notation (`KRS.name`, `CEIDG.nip`, `REGON.regon`, `ADE.address`); fields whose concept has no partner validator get a proposed validator (`NRB`, `KRS`, `KW`, `PHONE_PL`, `DATE_RANGE`). Two proposals come from the law and not from a single paper (`research/17`): an e-Delivery address field in the contact section when the party is an entity or a sole trader (every entrepreneur has such an address since 1 October 2026), and a third capacity for statutory representatives.

### 6.7 Conditions

Built from a typed predicate tree (`is(field, option)`, `any_of`, `all_of`, `not_`), never typed by hand. The writer emits exactly the subset seen in the exports: `("O" in tabs['P' in title].questions['S' in field.techName].field.repeatingSectionGrid['F' in field.techName].field.__userAnswer)` joined with `and`, `or` and brackets. In JSONata `'x' in y` is membership, and for a single string it means equality, not "contains": `tabs['Dane' in title]` selects the page whose title is exactly "Dane". A path therefore stays unambiguous only while page titles are unique in the form and techNames are unique (D7). The resolver refuses a form in which a path selects more than one page, section or field: two pages with the same title, or two labels whose slugs collide (`Łódź` and `Lodz` both give `lodz`) before the uniqueness suffix is applied.

### 6.8 Validation

| Concept | Evidence | Partner validator written (D8) | Our check of values (viewer, filled-form alarm) |
|---|---|---|---|
| required | section 6.4.3 | `REQUIRED` | |
| PESEL | label; 11 cells | `PESEL` | weights 1 3 7 9 1 3 7 9 1 3, control digit, date with the century offsets |
| NIP | label; 10 cells | `NIP` | weights 6 5 7 2 3 4 5 6 7, modulo 11, remainder 10 invalid |
| REGON | label; 9 or 14 cells | `REGON` | weights 8 9 2 3 4 5 6 7 (and the 14-digit set), modulo 11, 10 counts as 0 |
| postal code | label; comb `__-___` | `ZIP_CODE` | two digits, hyphen, three digits |
| e-mail | label | `EMAIL` | syntax only |
| ePUAP box | label "skrytka ePUAP" (set 9) | `EPUAP` | two path segments |
| e-Delivery address | label "eDoręczenia", "adres do doręczeń elektronicznych" (set 9) | `ADE` | the format `AE:PL-ddddd-ddddd-lllll-dd` only: the rule of its two control digits is not confirmed (`research/17` tested real addresses against the published guesses and found no match; `research/eden/e3` quotes a rule without an official source) |
| identity card | label "seria i numer dowodu osobistego" (set 9) | `SERIAL_NUMBER_ID_CARD` | three letters, six digits, weights 7 3 1 9 7 3 1 7 3 |
| bank account | label; 26 cells | none: proposal `NRB` | modulo 97 as a Polish IBAN |
| KRS number, land register number, parcel identifier, phone | label | none: proposals | ten digits; court code, number and control digit by the commonly used rule (not confirmed by an official source); `WWPPGG_R.XXXX.NDZ` for a full parcel identifier (`research/17`); nine digits with optional prefix |
| amount, count, area | label, unit beside the blank ("zł", "m2", "dni") | type `NUMBER` | |

The weights and formats come from `research/eden/e3`, which marks several of them as not published by an official source; each rule ships with valid and invalid synthetic values and none with a real person's number.

### 6.9 Two versions of one form

`diff/`: both forms are flattened to records; matched by id, then by path of techNames, then by fuzzy label inside the same section, then anywhere (a move). Each change is typed (`ADDED`, `REMOVED`, `RENAMED`, `MOVED`, `TYPE_CHANGED`, `OPTIONS_CHANGED`, `VALIDATION_CHANGED`, `CONDITION_CHANGED`, `REQUIRED_CHANGED`) and graded: breaking, compatible, information. With both sidecars, the diff also compares the receipts, so the report can say "the fee changed from 82 zł to 87 zł" and not only "a text block changed" (`research/18` §1.3).

## 7. Checks before anything is answered

### 7.1 The gate

A failed check is `500 GATE_FAILED` with its name. The form is never sent broken.

| # | Check |
|---|---|
| G1 | the form validates against `contracts/coi/form.schema.json`; top keys are exactly `title`, `tabs`, `flow` (D1) |
| G2 | the partner's nine rules (`tools/coi_lint.py` as a module): two pages or more, last `FINISH`, no input on it, sections not nested, links chain the pages |
| G3 | D3, D4, D7: key spelling, the six always-present keys, list-valued `validation`, one column, unique techNames, length |
| G4 | ids are UUIDs and unique; every link points to existing pages |
| G5 | every condition parses; every path in it resolves to exactly one page, one section, one field |
| G6 | every condition is evaluated with `jsonata-python`: for each option of the field it reads, the result is a boolean and it is true for exactly the intended options |
| G7 | zero-answer canary: with no answer at all, every component with a `SHOW` state is hidden |
| G8 | the journeys of 7.2 give the expected visible sections; **no page is empty on any journey** |
| G9 | dictionaries: only known names; a component with a dictionary has empty `options`; initial data only in the documented notation |
| G10 | HTML allow-list on every HTML string; no `javascript:` or `data:` target; length caps (title 255) |
| G11 | the ledger closes; coverage has no unassigned run |
| G12 | no value from a fill area of the paper appears in the form (protects against a filled form leaking into a template) |

### 7.2 Journeys

Six fixtures replay the citizen's first choices against the generated conditions, with the same evaluator: (1) for myself; (2) for another person as pełnomocnik; (3) for an entity as reprezentant; (4) for an entity as pełnomocnik; (5) address in Poland; (6) address abroad. For each the expected set is derived from the brief, not from the form: which standard sections are visible, which uploads are demanded, which defaults are locked. A journey that the paper does not allow is marked not applicable. The untouched exports of the partner are run through the same harness first: if our harness disagrees with their own forms, the harness is wrong.

### 7.3 Eight formats, one form

For every set, all formats are converted and the briefs compared: title equal; applicant options equal; fields of the matter matched by label (similarity 85 or more, one-to-one assignment). The agreement table is an evaluation output and a slide. It is a test of the readers, not a run-time feature.

### 7.4 Coverage of the source

Every text run of the page model ends in exactly one role: title, heading, label, option, hint, static text, consent, covered by standard, or left out with a reason code. Runs without a role are listed in `coverage.unassigned`; one such run of more than three words fails G11. This is the check that catches a silent page: a page with ink and no candidate is reported by number.

### 7.5 Confidence

A composition of independent parts, kept separately in the sidecar: geometry (how the place was found), label margin, text confidence (1 for native text; the OCR word confidence; in `plus` the agreement of two engines), rule strength (a table value per rule). The review view sorts by the lowest. Hard findings override the number: an unresolved reference, an ambiguous choice group, a required field we inferred.

## 8. Security: control and the test that proves it

| Threat | Control | Negative test in `tests/evil/` |
|---|---|---|
| a parser hangs or eats memory | **airlock**: one worker process per upload, started fresh with a scrubbed environment and resource limits, in its own process group, killed at `JOB_TIMEOUT_S`; the API process never touches file bytes. **As built today: the conversion runs in a thread of the service, not in a separate worker; at `JOB_TIMEOUT_S` the request answers 504 and the thread is abandoned, not killed (an OCR child is killed at its own limit of 90 s per page)** | as built: a job that spins answers 504, keeps its slot until it ends, and with `CONCURRENCY` such jobs the service answers 429 `BUSY`; a job that is killed and leaves no process needs the worker of WP-F16 |
| the worker leaks the key | the worker receives no key and no environment beyond `PATH`, `TMPDIR`, `LANG`; its only output is one JSON document that the API process validates as untrusted | the worker's environment dump in a test contains no `JWT` name |
| a file makes the service call out (remote template, linked image, external entity) | no HTTP client in the worker; an audit hook raises on name resolution, connect, bind and on any subprocess other than the allowed OCR and office programs | a DOCX whose template target is a local listener: the listener sees no connection, the guard counter is one |
| claim "no network" is only words | the proof is a run, not an endpoint: `convert` in a container started with `--network none` (command 1 of the README) gives the form with no network at all; a REST server under `--network none` cannot be reached from the host, so the published port is the other mode and is not offered as the proof. (A self-test endpoint was planned here and never built.) | command 1 of the README passes on the image under `--network none` |
| entity tricks in XML | any part with `<!DOCTYPE` or `<!ENTITY` is refused before parsing; the parser has entities, DTD loading and network off | billion-laughs DOCX, XLSX and ODS: 422 within two seconds, memory flat |
| archive bombs, traversal | limits of 6.1 on bytes read; names checked; nothing extracted | a member of 1 GB of zeros; a member named `../../x` |
| image bombs | header read before decoding; `MAX_PIXELS`; only JPEG and PNG decoders; one frame | a 100,000 × 100,000 one-bit PNG is refused from its header |
| PDF actions, embedded files, huge page trees | never executed or followed; counted and reported by `/v1/forms/inspect`; page and size caps | a PDF with an open action and a launch action converts with warnings and spawns nothing |
| macros, DDE | never executed; reported; `ACTIVE_CONTENT=strict` refuses | a DOCX with a macro part; a sheet cell starting `=cmd|` appears as escaped text or not at all |
| extension spoofing, polyglots | the proofs of 6.1 | PNG bytes named `.pdf`; DOCX named `.xlsx`; a legacy workbook named `.doc`; a file that is both PDF and ZIP |
| token abuse | algorithm from configuration only; `none` never accepted; one family per deployment; `exp` required; issuer and audience equal when set; leeway capped; no key fetching | sixteen tokens: no algorithm, wrong family against the same key, expired, future, wrong issuer, wrong audience, missing claim, oversized |
| hostile text becomes script in the partner's generator | D11: templates, escaping, allow-list; the gate re-checks | a form whose label is `<img src=x onerror=…>` and one with a `javascript:` link: both arrive as plain text |
| a filled form is uploaded | **alarm**: valid PESEL, NIP or account numbers inside fill areas, typed values in declared fields, ink density inside boxes and on leaders. Default: convert, warn, copy no value (G12). `FILLED_FORM=reject` answers 422 | a fixture with a synthetic valid PESEL in the comb: warning present, the number absent from form, sidecar and logs |
| content in logs | events are structured and content-free: stage, reason code, size and time buckets, random job id, hash of the input; never the name, the text or the token | a sentinel surname in the file name, in the text and in a parser exception appears in no log line |
| container | non-root user, read-only root, `tmpfs` for `/tmp`, all capabilities dropped, no new privileges, process and memory limits, one port | the commands of the README run with `--read-only --cap-drop ALL`; the image user is uid 10001 (Dockerfile) |
| supply chain | base images pinned by digest; `pip --require-hashes`; SBOM from the final image plus what a scanner misses (OCR data, fonts, front-end bundle); vulnerability gate (Grype, pip-audit); licence gate; signature of the image | `tools/licence_check.py` fails on a planted GPL package; the build fails on an unpinned line |
| prompt injection | no model (D12). The switched-off interface can only return one value of an enumeration | none needed while `MODEL_STEP=off`; a test asserts that nothing is loaded |

`python -m tests.evil` (also `make evil`) builds the hostile corpus and prints one line per attack with pass or fail. It runs in two places: natively against the source for everything that does not depend on the operating system, and **in CI against the built image**, which is the run that counts (section 9.2). Controls that exist only on Linux (resource limits, process groups, the reads of `/proc` in the self-test, the container flags) are tested only there; on Windows those tests are skipped by a marker and reported as skipped, never as passed.

Framework behind these controls, with article numbers and status: `research/16` §5.

## 9. Two images from one Dockerfile

| | `core` (default) | `plus` |
|---|---|---|
| Base | `python:3.14-alpine`, digest pinned | `python:3.14-slim-trixie`, digest pinned |
| Why | the card prefers light images and names Alpine; every dependency of the rule path has a wheel for it (`research/14` §3) | the second OCR engine, OpenCV and Morfeusz have no wheel for Alpine |
| Readers | all eight formats; binary Word by the native reader | the same, plus optional LibreOffice for binary Word (`DOC_READER=libreoffice`, only after J9) |
| OCR | Tesseract with `pol` and `eng` from the distribution's packages | plus RapidOCR on onnxruntime as the second opinion |
| Polish wording | phrase table, `simplemma` | plus Morfeusz2 |
| Model | none | none shipped; the interface only |
| Front end | built in a Node stage, copied as static files | the same |

Both run as a dedicated user, expose one port, carry no secret, use no `latest` tag. The submission and the defence use `core`. `plus` exists to show that quality can be bought with megabytes, not that it is needed.

### 9.1 The build machine has no Docker (measured on 21 November, 13:45)

The owner's laptop has no Docker and no WSL, and only Python 3.13 and 3.11. Two ways forward; the design works with either, and neither changes a line of product code.

| | (a) The owner installs WSL 2 and Docker Desktop | (b) No Docker on the laptop |
|---|---|---|
| Who | the owner: it needs administrator rights and probably a restart; an agent cannot do it | nobody |
| Development and tests | native Python on Windows, plus local image builds | native Python on Windows |
| Where the image is built and proved | CI, and locally for speed | CI only |
| The defence | `docker run` of the published image on the laptop | the published image on any machine with Docker; the laptop shows the native run and the CI record |

### 9.2 CI is the source of truth for the image, in both cases

A workflow in the public repository runs on every push to `main` and on every pull request (`.github/workflows/image.yml`). What it does, in order; a failed step fails the push:

1. Lint, type check and the native test suite on Linux with Python 3.14.
2. Build both targets with every base pinned by digest and `pip --require-hashes --only-binary=:all:` (a missing wheel for Alpine fails here, in the first hour, not at the defence).
3. Start `core` with `--network none`, a read-only root, a dedicated user and no capabilities, and convert reference set 1 **inside** the container through the command line entry (`python -m converter convert`): the result must pass the gate and equal the stored expectation. A second start with a published port checks the HTTP path with a token: `healthz`, one conversion, the negative controls of the guard and of the token.
4. Run the hostile corpus against the container. Run `convert` under `--network none` and assert the form; with the port published assert what `GET /status` reports.
5. Produce the SBOM from the final image, run the vulnerability and licence gates, attach the reports to the run.
6. Push the image to the registry of the repository under the commit hash and sign it. The README names the image by digest.

The record of that workflow is the proof for the card's Docker requirements (C-TECH-DOCKER) when the laptop cannot build an image. The judged sets are not in git, so CI converts reference set 1 and the synthetic fixtures; the seven judged forms are converted natively and by the published image on the day.

### 9.3 Every code path runs natively on Windows

- The pipeline is plain Python with wheels for Windows; nothing in `readers/`, `find/`, `mean/`, `compose/`, `gate/`, `sidecar/` may import a module that exists only on Linux. A test imports every module on Windows.
- The source stays compatible with Python 3.13 while the image runs 3.14: no syntax or library feature that only 3.14 has, until the laptop has 3.14 too (it installs per user, without administrator rights).
- The worker's limits sit behind one interface with two implementations chosen by platform. `limits_posix.py`: resource limits, a new session, kill of the process group. `limits_windows.py`: a new process group, a wall-clock kill of the process tree, no memory limit; it logs once that limits are weaker on this platform. The self-test says which implementation is active.
- OCR goes through one interface with two engines. Tesseract is a program that must be installed; where it is missing on the laptop, the second engine installs with `pip` and stands in for development, and tests that need Tesseract itself are skipped by a marker and run in CI.
- Binary Word is read by our own reader, so no office suite is needed anywhere.
- Paths are built with `pathlib`; temporary files with `tempfile`; no shell commands in product code.
- The front end builds with Node on Windows; the API serves the built files, so the whole product runs with `python -m converter serve` and no container.

## 10. Evaluation and cost

**Golden pairs** (`eval/golden.json`): reference set 1 (eight inputs, one expected form) and reference set 5 (seven inputs, one expected form). **Judged sets**: seven, no expected form.

| Metric | How | Where it is shown |
|---|---|---|
| fields found: precision, recall, F1 | one-to-one matching on label similarity inside the same section; reported twice: all fields, and **fields of the matter only**, because the standard sections would flatter the number | `eval/metrics.json`, one slide |
| type, validator, dictionary, initial-data accuracy | among matched fields | the same |
| conditions | behaviour, not text: the journeys give the same visible sections on our form and on the reference | the same |
| standard sections | by techName: present, missing, extra | printed comparison |
| eight-format agreement | section 7.3, per set | table |
| ledger and coverage | closed or not; share of runs with a role | per judged form |
| gate | passes per form | per judged form |
| time and memory | wall and CPU milliseconds, peak memory, per input class (native PDF, office file, scan) | README and the cost dial |

`python -m eval.run` produces everything with one command on a clean checkout and writes `results/<set>/form.json` and `results/<set>/meta.json` for the seven judged sets. The inputs are found through `tools/coi_paths.py`, because the sets are not in git.

**Silver labels** (`eval/silver/`): while building, a hosted model reads each judged form and answers the ten questions (`tools/eden/eden.py`, D14). The answers are compared with our briefs to find what the rules miss; a disagreement is a task for a rule or a decision, never a patch of the output.

**Cost dial**: the per-request resource report (`metrics/`) is aggregated by input class; the front end multiplies openly: forms per municipality × 2,479 municipalities × measured CPU seconds, with the share of scans and the review minutes as visible assumptions. Review time will dominate; the dial says so.

## 11. The nine sets: what is hard in each

Read from `data/coi/text/` and from the files themselves on 21 November.

| Set | Paper | Size | What is hard |
|---|---|---|---|
| reference 1 | Wniosek o ustalenie numeru porządkowego nieruchomości (Wójt Gminy Elbląg) | 1 page + clause | one sentence with four blanks is the whole matter; "imię i nazwisko / nazwa" opens all three applicant options; footnote "1) Dane nieobowiązkowe"; the clause becomes a linked consent |
| reference 5 | Wniosek o stwierdzenie nadpłaty podatku (Urząd Gminy Ulan-Majorat) | 1 page | PESEL or NIP by a footnote rule; a two-way choice whose branches each own a field (tax name, account number); legal basis inside the request sentence; "w załączeniu" with one named item and two open lines |
| judged 2 | Wniosek o zwrot opłaty skarbowej (Urząd Gminy Stawiguda) | 2 pages | combs for postal code, two dates and a 26-digit account; person or entity on one line; a printed block for the pełnomocnik that the standard sections replace; refund in cash or by transfer with dependent fields; attachments as tick boxes; **the DOCX is all text boxes** |
| judged 3 | Wniosek o wydanie zaświadczenia (Młynary) | 1 page | applicant block as bare lines with captions in slashes; five kinds of certificate marked only by an asterisk, one with a free text ("inne …"): single or multiple choice is not said; purpose as a blank in a sentence; fee 17 zł per copy and the office's account in an information block |
| judged 4 | Wniosek o wynajęcie lub użyczenie świetlicy wiejskiej (Wójt Gminy Płoskinia) | 1 page | "wynajęcie/użyczenie*" in the title and again in the request: one choice; from–to dates; a responsible adult who may be another person, which demands that person's consent; four declarations; a regulation header that must not become the title |
| judged 6 | Wniosek o wydanie zezwolenia na zajęcie pasa drogowego (Urząd Miasta i Gminy Miasteczko) | 2 pages | a table of four surface kinds with repeated rows, "razem" per row and a total; dates and a number of days; contractor and a responsible person; six attachments of which three are conditional and one brings stamp duty; a consent sentence under the clause; **the paper names two different offices** |
| judged 7 | Wniosek o wydanie zezwolenia na hodowanie lub utrzymywanie psów ras uznawanych za agresywne (Urząd Miejski Wrocławia) | 2 pages; six files, one named `.JPE`, no DOCX, no XLSX | fee and account in the page header; "Nr sprawy /wypełnia organ/"; **section B (the dog) is printed before section A (the applicant)**; grammar alternatives with asterisks; two choice groups, one with number fields on two of its options; "more than one dog: take more copies of table B", which is a repeating section; an optional-marked part of one label; three declarations, one implying an upload; the title speaks of aggressive breeds and the body of greyhounds |
| judged 8 | Deklaracja o wysokości miesięcznej opłaty za gospodarowanie odpadami komunalnymi (Prezydent Miasta Gdyni) | 6 pages; scan 1654 × 14034 | about seventy numbered positions that refer to each other ("poz. 34", "B 1.1.2"); six kinds of filer that decide PESEL or NIP/REGON and a spouse section; four circumstances each with its own date; correspondence address only if different; a fee table of counts times fixed rates with sums; an office-only part; two pages of explanations keyed to positions; **the DOCX is 1,302 text boxes**; 759 merged ranges in the sheet |
| judged 9 | Wniosek o przyznanie stypendium, nagrody lub wyróżnienia sportowego Rady Miasta Zgierza | 16 pages; scan 1654 × 37424 (61.9 million pixels); sheet with four tabs | **three applications in one file**: a selector and conditional sections; the applicant is the mayor or a sports club, the club acts through a reprezentant or a pełnomocnik (identity card number, power of attorney, stamp duty); correspondence by post, ePUAP box or e-Delivery address, which calls for three of the partner's validators nobody else uses; consents that differ for an adult and for a minor; a list of a coach's wards; boxes written as the character `□` |

Set 9 is the partner's test of dynamic flow, set 8 of scale and tables, set 7 of reading order, sets 2 and 8 of the DOCX reader, sets 8 and 9 of tall scans.

## 12. What in this document is inference

| Statement | Why we hold it | What settles it |
|---|---|---|
| a conditional page is written as conditional sections on a page that never becomes empty | `flow.links` carries no condition; pages carry no `states` in either export | J1 or an import test (J13) |
| shapes of `REPEATING_SECTION`, `CHECKBOX`, `DATEPICKER`, `INFO_SECTION` | the rules document describes their keys; no export shows them | J1 |
| `__userAnswer` holds the chosen option's name, or a list of names | the exports' conditions test `"Polska" in … __userAnswer` | J12, J13 |
| printed arithmetic cannot be expressed | no key for it in schema, rules or exports | the mentors |
| the native reader of binary Word is enough for forms | forms are mostly plain paragraphs, leaders and simple tables | the eight-format agreement on the nine `.doc` files |
| `.jpe` is meant as JPEG | it sits in a judged set between `.JPG` and `.PNG` of the same form | the mentors; `STRICT_EXTENSIONS` |
| the importer tolerates UUIDs of version 5 | export 5 itself has link ids that are not UUIDs at all | J13 |
