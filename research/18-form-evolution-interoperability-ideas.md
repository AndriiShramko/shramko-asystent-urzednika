# Form evolution, interoperability and ideas the partner did not ask for

Written 21 November 2026. Sources were opened on 2026-11-21 unless noted. Labels: "inference" = our reasoning; "unverified" = not confirmed from a source we opened. Web pages contained no instructions aimed at us.

## TL;DR for builders

- Make every field carry a stable id and a stable `techName`. Without them no diff, no changelog, no migration of collected answers is possible. FHIR Questionnaire does the same with `linkId` (unique per questionnaire) and `url`+`version` (https://hl7.org/fhir/questionnaire.html).
- Build one small module `formdiff`: match fields by id, then by (section techName, fuzzy label), then by position. Emit a typed change list (added, removed, renamed, moved, option changed, validator changed, condition changed). Core: `rapidfuzz` (MIT, 3.14.6) + plain Python. Optional: `deepdiff` (MIT, 9.2.1) and `jsonpatch` (BSD-3-Clause, 1.48) for RFC 6902 output. Licences from PyPI JSON, opened 2026-11-21.
- Do NOT add new keys into the partner's JSON. Put all extras (concept URIs, legal basis, version, confidence) in a sidecar file `<form>.meta.json` keyed by field `id`. The partner's importer behaviour on unknown keys is unknown (T3), so the sidecar is safe by design.
- Legal basis: store an ELI URI per form in the sidecar (e.g. `https://eli.gov.pl/eli/DU/2023/123`, pattern inferred from the API path `/acts/{publisher}/{year}/{position}`). Watch for amendments through an OFFLINE snapshot of `/changes/acts?since=...` that an operator imports as a file. The product itself never calls the network.
- The Sejm ELI API (https://api.sejm.gov.pl/eli/openapi/) has `/acts/search`, `/changes/acts` (needs `since`, limit max 500), `/references`, `text.html`, `text.pdf`. Its OpenAPI spec states no licence or rate limit; treat terms as unverified.
- From the same internal model, emit four agent exports: JSON Schema 2020-12, an OpenAPI 3.1 operation, an MCP tool definition (`name`, `title`, `description`, `inputSchema`, optional `outputSchema`, per https://modelcontextprotocol.io/specification/2025-06-18/server/tools), and an `llms.txt` (https://llmstxt.org/). All are plain JSON/Markdown files generated locally; no external call.
- Safe-for-assistant rule: the export must say which fields are read-only, which come from a register, which need human confirmation (signature, consent, declarations). MCP spec itself says a human SHOULD stay in the loop.
- Plain-language check offline: implement FOG-PL / Pisarek-style indices ourselves (formulas are public, a few lines of code) with a Polish syllable counter. Avoid Pyphen (GPL/LGPL/MPL tri-licence; we avoid it). Jasnopis and Logios are web tools; we found no public API or licence (unverified), so only mimic the idea.
- Accessibility check offline: axe-core is MPL-2.0 and pa11y is LGPL-3.0 (search result, 2026-11-21), both on our "avoid / ask first" list. Write ~15 own rules on the generated form JSON (label present, hint present, no lone checkbox, order, language) instead of a browser engine. Cheap and fully ours.
- Evaluation harness: score our JSON against the partner's two reference exports with field precision/recall (fuzzy label via rapidfuzz), type/validator/dictionary/condition accuracy, and tree edit distance (`zss`, MIT per our memory, PyPI licence field is empty: verify before use). Show the score on a slide.
- Datasets: FUNSD is non-commercial research only; XFUND is CC BY-NC-SA 4.0; DocLayNet is CDLA-Permissive (card says 1.0, a mirror says 2.0). Only DocLayNet is usable for anything shipped; for the hackathon we need none of them at run time. Keep them out of the repo.
- Fifteen+ ideas are ranked in the last section. Top five: semantic diff with changelog, sidecar with concept URIs and ELI, agent export pack (JSON Schema + MCP + llms.txt), self-score harness with a reference set, "form family" canonical model with local variants.

---

## 1. Versioning and diff of form definitions

### 1.1 What the partner's JSON gives us
From `docs/02-architecture/coi-json-format.md`: each component has `id` (UUID), `techName` (lower case slug from the label, unique inside its section; JSONata paths refer to it), `title`, `questionOrder`. Pages have `id`. `flow.links` use page ids. There is no version, no `url`, no `derivedFrom` key. Question T20 (stable id between versions) is open.

Consequence (inference): the JSONata conditions use `techName` and page `title`, NOT `id`. So a rename of a label that changes `techName` or a page title silently breaks conditions elsewhere. A diff tool should flag "renamed field referenced by N conditions" as a high-severity change. This is something a checker gives the partner for free and nobody asked for it.

### 1.2 Prior art (what to copy)
| System | What it does for evolution | Source | Take |
|---|---|---|---|
| FHIR Questionnaire | `url` canonical id, free `version` string, `derivedFrom`, `date` changes with content; `linkId` unique per questionnaire so answers map to items; page itself warns data from different versions often is not comparable | https://hl7.org/fhir/questionnaire.html | Copy the triple url+version+derivedFrom into the sidecar. Copy the warning as a report line "answers not comparable". |
| ODK XLSForm | `version` setting in the form; `name` column is the stable key of a question, label may change | unverified (from memory, not opened today) | Same idea: techName = stable key, title = free text. |
| W3C XForms | model with instance data separate from the UI; binds by XPath | unverified (not opened) | Separation of definition and answers: our sidecar does this. |
| Form.io, SurveyJS, JSON Forms | JSON definitions stored in a repository; versioning is left to the host application (revisions). Form.io has revision support in the enterprise product | unverified (not opened) | Do not depend on them; they are generators, the partner has its own. |
| JSON Schema evolution | Adding optional properties is compatible; removing, narrowing types or adding `required` breaks consumers | inference from the spec rules | Use as the severity table: breaking / compatible. |
| OpenAPI diff tools (oasdiff and others) | Classify changes as breaking, warning, info | unverified (not opened today) | Same three levels in our changelog. |

### 1.3 Diff algorithm (proposal)
1. Flatten both forms to records: (page title, section techName, field techName, id, type, title, options, validation, dictionaryName, states, readOnly, defaultValue).
2. Match in four passes: (a) equal `id`; (b) equal path of techNames; (c) same section and rapidfuzz `token_set_ratio` of title >= 90; (d) same type and title >= 85 anywhere (move).
3. Classify: ADDED, REMOVED, RENAMED (title or techName), MOVED (section/page/order), TYPE_CHANGED, OPTIONS_CHANGED (added, removed, renamed options), VALIDATION_CHANGED, DICTIONARY_CHANGED, CONDITION_CHANGED (JSONata text compared after normalising), REQUIRED_CHANGED, DEFAULT_CHANGED.
4. Severity: breaking (REMOVED, TYPE_CHANGED, techName rename referenced by a condition, REQUIRED added), compatible (ADDED optional, label text only), info (order).
5. For answers already collected: emit a migration note per change ("field removed: archive answers", "option renamed: map old value to new", "type changed: manual review"). Do not migrate data; only describe (we never hold answer data).
6. Output: `changes.json` (typed list), `CHANGELOG.md` (human, Polish), optional RFC 6902 patch from `jsonpatch`.

### 1.4 Libraries
| Library | Licence | Version | Use | Source |
|---|---|---|---|---|
| deepdiff | MIT | 9.2.1, Python >=3.11 | generic tree diff, fallback | https://pypi.org/pypi/deepdiff/json |
| jsonpatch | BSD-3-Clause | 1.48, Python >=3.11 | RFC 6902 export/apply | https://pypi.org/pypi/jsonpatch/json |
| rapidfuzz | MIT | 3.14.6, Python >=3.11 | fuzzy label match | https://pypi.org/pypi/rapidfuzz/json |
| jsonschema | MIT | 4.26.0, Python >=3.10 | validate sidecar, exports | https://pypi.org/pypi/jsonschema/json |
| jsondiffpatch | MIT (JS library) | unverified | JS only; skip, we are Python | unverified |
| zss (tree edit distance) | PyPI licence field empty; repo reported as MIT | 1.2.0 | evaluation | https://pypi.org/pypi/zss/json; licence unverified |

All Python >=3.11, so 3.14 is expected to work (inference; wheels for rapidfuzz on 3.14 not checked). Check that `pip install` works in the Alpine image: rapidfuzz ships compiled code, and musl wheels exist for many versions but this is unverified; fall back to a Debian slim image if needed.

---

## 2. Watching the legal source

### 2.1 The ELI API of the Sejm
Base `https://api.sejm.gov.pl/eli` (spec https://api.sejm.gov.pl/eli/openapi/, opened 2026-11-21). Endpoints read from the spec:
- `/acts` publishers; `/acts/{publisher}/{year}` list; `/acts/{publisher}/{year}/{position}` one act; `/acts/{address}` by publication address. The spec's only publisher example is `DU` (Dziennik Ustaw). Whether `MP` (Monitor Polski) is served: the spec does not say. Unverified.
- `/acts/search` with dates, title, keyword, type, publisher, year, in-force status; `limit` default 500, `offset`.
- `/changes/acts?since=...` lists recently changed acts (`since` required, limit up to 500).
- `/acts/{publisher}/{year}/{position}/references` (relations: amends, repeals, based on); `/struct`; `text.html`, `text.pdf`.
- Licence, terms, rate limits: none in the spec. Unverified. Voivodeship official journals are NOT in this API as far as the spec shows (inference); they have separate portals, not checked.

### 2.2 How to link a form to its legal basis
- Sidecar field `legalBasis`: list of `{eli: "DU/2024/1234", role: "basis" | "annex-template", annexNo: "2", checkedOn: "2026-11-21", textHash: "sha256..."}`.
- Where the form template IS an annex to a regulation, `role = annex-template` and the hash of the annex text lets the offline checker say "the annex text differs from the one we converted".
- Voivodeship or local resolutions: same structure with a free `uri` instead of ELI, flagged "no ELI available" (inference).

### 2.3 Offline feed design (product may not call external services)
1. An operator (outside the product, or a separate optional CLI that is not in the Docker image) saves `changes.json` from `/changes/acts?since=<date>` and drops it in a folder or uploads it to a local endpoint `POST /v1/legal-feed`.
2. The service joins feed entries with `legalBasis` of stored forms and returns "form X: act Y changed on date Z, references: amended by ...".
3. Format of the feed: just the API's own JSON, so there is nothing to design. A signed bundle (checksum file) allows air-gapped transfer.
Pitch value: it answers question B9 (do forms change often) in the partner's own language: "which of your forms stand on an act that changed this month".

### 2.4 Risk
The feed is only useful if forms are linked to acts; paper forms rarely cite the act. Linking is a human or heuristic step (title match against `/acts/search`, done offline once). Inference.

---

## 3. "Form family" across offices

- Same procedure, many offices: e.g. the sample "Wniosek o ustalenie numeru porządkowego nieruchomości" (Gmina Elbląg) exists in every gmina (sample from `coi-json-format.md`). Each gmina has its own paper layout; legally it is one procedure.
- Canonical concept model (proposal): a procedure id, a list of concepts (applicant name, parcel number, building location, contact), each concept with a datatype and a concept URI; each local form maps its fields to concepts through the sidecar. Local variants = canonical form + overrides (extra field, different addressee, local fee).
- Similarity measures to detect that two forms belong to one family (all offline, no model): (a) rapidfuzz token_set_ratio on titles; (b) Jaccard of normalised field-label sets; (c) tree edit distance on the section skeleton (`zss`); (d) cosine of TF-IDF vectors (own code or `scikit-learn`, BSD-3, heavy; skip); (e) shared legal basis ELI (strongest signal, exact). Combine as a weighted score; report "family candidates" for human approval. Inference; no benchmark exists for Polish forms.
- Value for COI (inference): one canonical form maintained centrally, local variants as small patches; an amendment is applied once. Needs question B22 answered.
- Demo with only the two reference JSONs is thin; a demo needs 3 to 5 gmina variants of one form. `docs/05-hackathon` may hold such data (not checked).

---

## 4. Interoperability hooks (cheap now, valuable later)

| Standard | What to carry | Source / status |
|---|---|---|
| EU Core Vocabularies (Core Person, Core Business, Core Location, CPSV-AP) | concept URIs per field, e.g. Core Person `givenName`, `familyName`; CPSV-AP for the public service itself (form = service channel) | CC BY 4.0 per SEMIC handbook (https://semiceu.github.io/core-vocs-handbook/develop/semic-core-vocabularies.html). Versions seen: Person 2.1.2, Business 2.1.0 or draft 2.2.0, CPSV-AP 3.2.0 (https://interoperable-europe.ec.europa.eu/collection/semic-support-centre/core-vocabularies); current versions unverified |
| Single Digital Gateway / Once-Only Technical System (OOTS) | the form's "initial data" (`MLPZ`, `PESEL` sources) is the same idea as once-only; sidecar maps `SOURCE.attribute` to Core Person terms | EC page on OOTS schemas: https://ec.europa.eu/digital-building-blocks/sites/display/TDD/10+-+Schemas (search result only; content unverified) |
| eIDAS 2 / EUDI Wallet PID | attribute names `family_name`, `given_name`, `birth_date`; optional `family_name_birth`, `given_name_birth`, `birth_place`; mandatory set includes `age_over_18` | ARF Annex 3.01 PID rulebook https://eu-digital-identity-wallet.github.io/eudi-doc-architecture-and-reference-framework/latest/annexes/annex-3/annex-3.01-pid-rulebook (search result; German rulebook uses `birth_name` instead, so national variants exist). Baseline text may have moved to CIR 2026/1731 (unverified) |
| Polish register attributes | the partner's own list: `MLPZ`, `PESEL`, `PESEL_ADDRESS` attribute names (doc section 6). Map them to PID and Core Person names in one table | partner docs; CEIDG/KRS/REGON attribute names unverified (question B11) |
| schema.org | `Person.givenName`, `familyName`, `PostalAddress` as a human-friendly fallback | unverified (from memory) |

### How to carry concept URIs without touching the partner's JSON
Sidecar `<form>.meta.json`, validated by our own JSON Schema:
```
{ "form": {"id": "<title-slug>", "version": "2026-11-21", "derivedFrom": null,
           "legalBasis": [{"eli": "...", "role": "basis"}]},
  "fields": { "<field-uuid>": {"concept": "https://data.europa.eu/m8g/...",
              "pid": "family_name", "register": "MLPZ.surname",
              "confidence": 0.93, "source": "page 1, box 2"} } }
```
Key = field `id`, which the partner's JSON already has. The partner may ignore the file. If the partner later wants the data in the JSON, a one-line merge script adds it. The exact Core Vocabulary URIs must be copied from the published vocabulary files at build time; not verified today.

---

## 5. Machine-readable exports for AI agents

One internal model (our own, richer than the partner's JSON) produces the partner's JSON AND these exports:

| Export | Content | Notes |
|---|---|---|
| JSON Schema 2020-12 | one property per field, `type`, `enum` from options/dictionary, `pattern` for PESEL/NIP/REGON/ZIP, `required`, `if/then` for JSONata `states` where translatable | `jsonschema` (MIT) to validate our own output. JSONata to JSON Schema `if/then` works only for simple "option chosen" conditions (inference); report the rest as `x-condition-text` |
| OpenAPI 3.1 operation | `POST /submissions/{formId}` with the schema as request body; 3.1 uses JSON Schema 2020-12 | no external call; just a file |
| MCP tool definition | `name`, `title`, `description`, `inputSchema`, optional `outputSchema`, `annotations` (https://modelcontextprotocol.io/specification/2025-06-18/server/tools). We only EMIT the JSON; we do not run an MCP server (task card forbids dependence on MCP; emitting a file is not a dependency; confirm with mentors, see below) |
| llms.txt | H1 form title, blockquote summary, H2 sections with links (https://llmstxt.org/) | Polish text, short |

What makes a form safely fillable by an assistant (proposal, inference):
- Field-level flags: `sensitive` (PESEL, health), `fromRegister` (do not ask the user; read-only), `requiresHumanAttestation` (signature, consent, "oświadczam"), `legalEffect` (declaration under penalty).
- Enumerations with stable codes, not only labels.
- Conditions as explicit machine text, not prose.
- A "dry run" rule: the agent produces a filled draft; the citizen confirms on the preview page (the partner's last page already says "check the preview").
- Explicit refusal list: never fill consents, never choose "pełnomocnik" for the user.
- Prompt injection: free-text field descriptions from paper forms can contain text aimed at an agent; the export must mark them as data (e.g. wrapped in a `description` field, never in `instructions`). Inference.

---

## 6. Plain language and accessibility offline

### Polish readability
- FOG-PL is an adaptation of the Gunning FOG index to Polish; Pisarek's method is Flesch-based and highly correlated with FOG (summary of search result, https://czasopisma.uni.lodz.pl/kpc/article/download/11914/11545 and others; details unverified). Jasnopis (7-point scale, FOG + Pisarek-based) and Logios (plain language index) are web tools by their authors; the searches showed no public API or licence terms. Unverified: do not depend on them.
- Proposal: implement `fog_pl(text)` = 0.4 * (words/sentence + 100 * share of words with >=4 syllables) (the generic FOG formula; the Polish syllable threshold differs by source, check before claiming "FOG-PL") with a vowel-group syllable counter for Polish (a, e, i, o, u, y, ą, ę, ó; "ia", "ie", "io", "iu" count as one). Own code: no licence issue. Also report average sentence length, share of passive/long words, legal-jargon list (own list).
- Run on every `title`, `description`, `tooltipMessage` and section text; return per-field warnings in the sidecar/report. This directly serves the partner's own design standard (short sentences, active voice, second person) listed in `coi-json-format.md` section 7.
- Avoid Pyphen for hyphenation: GPL 2+/LGPL 2.1+/MPL 1.1 tri-licence (https://pypi.org/pypi/pyphen/json).

### Accessibility (WCAG 2.1 AA, EN 301 549) offline
- Browser engines are not an option in the image: axe-core is MPL-2.0 and pa11y LGPL-3.0 (search result https://github.com/pa11y/pa11y); HTML_CodeSniffer licence not confirmed. Also they need a browser and Node.
- Instead check the definition, not the rendered page (inference): every input has a label and a `tooltipMessage` (WCAG 1.3.1, 3.3.2); required fields marked as such (3.3.2); no consent as a lone checkbox (partner rule); error identification needs a message for each validator (3.3.1); logical order equals `questionOrder` (1.3.2, 2.4.3); radio/checkbox groups have a section title (1.3.1); alt text for images in descriptions (1.1.1); language declared `pl` (3.1.1); no colour-only meaning in descriptions (1.4.1); target sizes are the generator's job. Our own code, no library.
- `beautifulsoup4` (MIT, 4.15.0, https://pypi.org/pypi/beautifulsoup4/json) to parse the HTML in `description` fields.
- Caveat: EN 301 549 needs the rendered front end; our checks cover only what the JSON controls. Say so on the slide.

---

## 7. Evaluation method for form digitisation

Reference set: the partner's two reference JSON exports (facts in `reference-json-forensics.txt`) and the sample paper form in eight formats. Only two references exist, so the harness is a demo of method, not a benchmark (inference).

Metrics (all offline, own code plus rapidfuzz and zss):
| Metric | How |
|---|---|
| Field precision / recall / F1 | match produced to reference fields with Hungarian assignment (`scipy` BSD-3, or greedy) on rapidfuzz title similarity >= 85, same section name |
| Type accuracy | among matched, `type` equal |
| Validator accuracy | set equality of `validation` |
| Dictionary accuracy | `dictionaryName` equal or both none |
| Condition accuracy | compare normalised JSONata AST or the (field, option) pair that triggers |
| Structure | tree edit distance (`zss`) between page/section/field trees, normalised by size |
| Standard-sections check | partner's nine rules via the existing `tools/coi_lint.py` |
Expose as `python tools/score.py produced.json reference.json` and as a slide: "wynik na formularzu wzorcowym: F1 = x". Because four fifths of the reference JSON is standard sections (doc section 1), report two scores: all fields and "matter fields only", or the number will look better than it is.

Datasets and papers (usable under our rules?):
| Dataset | Licence | Usable? | Source |
|---|---|---|---|
| FUNSD | non-commercial, research and educational only | Not shipped; reading papers is fine | https://arxiv.org/pdf/2211.07730 (QueryForm paper quoting the licence) |
| XFUND | CC BY-NC-SA 4.0 (a Hugging Face copy labels itself MIT, but derivative) | No (NC and share-alike) | same source |
| DocLayNet | CDLA-Permissive-1.0 per official card; a mirror says 2.0 | Yes in principle, but layout of reports and manuals, not administrative forms; no need at run time | https://huggingface.co/datasets/ds4sd/DocLayNet/blame/main/README.md |
| FormNet, LayoutLM family | models and licences not checked today | unverified; weights from Microsoft are often non-commercial (inference, unverified) | |
No dataset of Polish administrative forms was found in this session; we did not search the Polish open-data portal specifically (unverified). Consequence: the best evaluation set is the 2 references plus forms we convert ourselves and hand-correct.

---

## Questions of questions-v1.md answered here

| id | our answer | confidence | evidence |
|---|---|---|---|
| T3 | Cannot be known; design so it does not matter: all extras go in a sidecar file, the JSON stays strictly in the partner's shape | high (design), low (their behaviour) | section 4; no source for the importer |
| T11 | Return the partner's JSON as the body; put the report (warnings, confidence, changes) in a separate endpoint or a sidecar | medium | inference from T3 risk |
| T18 | Treat `techName` as unique per section AND unique form-wide when we generate (safe in both cases); conditions use section + field techName | medium | `coi-json-format.md` sections 2, 5 |
| T20 | Ask for stable ids, but do not wait: our diff matches by id, then techName path, then fuzzy title, so it works either way | high | section 1.3 |
| B9 | Law changes are continuous; the ELI API has a dedicated changes endpoint with `since`, which implies frequent amendments; how often forms change is for the partner | low | https://api.sejm.gov.pl/eli/openapi/ (2026-11-21) |
| B10 | Offer the diff as a bonus either way; no reason to wait for the answer | medium | sections 1, 7 |
| B22 | Technically feasible (section 3); whether COI wants it is theirs | medium | inference |
| B23 | Yes: MCP and llms.txt formats exist and are cheap to emit from the same model | medium | https://modelcontextprotocol.io/specification/2025-06-18/server/tools ; https://llmstxt.org/ |
| T8 | Not answerable outside the partner. Our plan needs no LLM for sections 1 to 7 | high (plan) | this file |

## Only the partner can answer

- Whether the importer ignores unknown keys (T3): only their code knows.
- Whether ids must be stable across versions (T20) and whether their system keeps form versions at all: internal data model.
- Their real list of dictionary names and register attribute names (CEIDG, KRS, REGON): internal catalogue; not published.
- Whether emitting an MCP tool definition or `llms.txt` as a static FILE counts as "depending on MCP" under the task card: rule interpretation belongs to the organiser.
- How many gmina variants of the same form they hold (for the form-family demo) and permission to use them.
- Whether the legal-feed import is wanted in their network (air-gapped transfer policy).

## Proposals beyond what the partner asked

Ranked. Jury criteria: C = completeness 30, I = intuitiveness 20, O = originality 10, Q = code quality 20, D = deployment potential 20.

| # | Proposal (Polish pitch for a slide) | Criterion | Effort | Libraries and licences | Risk |
|---|---|---|---|---|---|
| 1 | "Co się zmieniło w formularzu? Pokażemy to jednym raportem": semantic diff of two versions with breaking/compatible levels and Polish changelog | D, O, Q | M | rapidfuzz MIT, deepdiff MIT, jsonpatch BSD-3 | Matching errors without stable ids; mitigate with 4-pass match |
| 2 | "Ten sam JSON, ale z metadanymi bez ryzyka dla importu": sidecar file with concept URIs, version, legal basis | D, Q | S | jsonschema MIT | Partner ignores it; low cost |
| 3 | "Formularz dla ludzi i dla asystentów AI z jednego modelu": JSON Schema 2020-12, OpenAPI 3.1 operation, MCP tool definition, llms.txt | O, D | M | jsonschema MIT | MCP file may be read as forbidden MCP dependence; ask once |
| 4 | "Mierzymy sami siebie": scoring harness (field P/R/F1, type, validator, dictionary, condition, tree edit distance) with a score on the slide | Q, C | M | rapidfuzz MIT, zss (verify licence), scipy BSD-3 optional | Only two references; report matter-fields-only score too |
| 5 | "Rodzina formularzy: jeden wzór centralny, lokalne warianty jako poprawki": canonical concept model and similarity | O, D | L | rapidfuzz MIT, zss | Needs several variants of one form for a demo |
| 6 | "Podstawa prawna w formularzu": ELI link and offline notice "ustawa się zmieniła, sprawdź formularz" from an imported ELI changes file | O, D | M | stdlib only | ELI API terms unverified; link between form and act is manual |
| 7 | "Kontrola warunków: zmiana nazwy pola nie psuje reguł": reference checker for JSONata conditions after edits | Q, C | S | `jsonata-python` (licence unverified) or regex over our own builder | Low |
| 8 | "Mapa pól na pojęcia europejskie i portfel UE": table `MLPZ/PESEL` attributes to Core Person and PID names | D, O | S | none (CC BY 4.0 vocabularies as reference data) | Vocabulary versions unverified |
| 9 | "Ocena prostoty języka bez internetu": offline Polish readability index per label (FOG-style), with suggestions | I, O | S | own code; avoid Pyphen (GPL/LGPL/MPL) | Polish syllable threshold needs calibration |
| 10 | "Dostępność sprawdzona w definicji formularza": ~15 offline WCAG 2.1 AA and EN 301 549 rules on the JSON | I, Q | S | beautifulsoup4 MIT; do not use axe-core (MPL-2.0) or pa11y (LGPL-3.0) | Covers only what JSON controls |
| 11 | "Co agent może wypełnić, a co musi człowiek": per-field flags sensitive, from register, needs human attestation | O, D | S | none | Needs agreed vocabulary of flags |
| 12 | "Notatka migracji dla zebranych odpowiedzi": per-change advice for answers already collected | D | S | built on #1 | Advice only, no data touched |
| 13 | "Raport tego, czego nie przeniesiono i dlaczego": paper-only items (signature, stamp, "wypełnia urząd") listed | I, C | S | none | Already planned (D10, B8) |
| 14 | "Ślad pochodzenia każdego pola": sidecar stores page, box coordinates and confidence per field, so the clerk can click to the source | I, Q | M | none beyond converter | Needs converter to keep coordinates |
| 15 | "Sprawdzamy duplikaty i sprzeczności": lint for duplicate techNames, orphan options, unreachable conditions | Q, C | S | none | Low |
| 16 | "Tryb pracy w sieci urzędu bez internetu": all of the above ship offline, with a signed offline bundle for the ELI feed | D | S | none | Needs checksum policy |
| 17 | "Test regresji na nowych plikach": snapshot tests that fail when output changes between releases, using diff #1 | Q | S | pytest (MIT) | Low |
| 18 | "Mapa podobnych formularzy": heat map of similar forms across offices | I, O | M | rapidfuzz MIT | Weak without data |
