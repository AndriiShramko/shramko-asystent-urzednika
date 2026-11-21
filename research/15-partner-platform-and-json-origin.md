# 15. The partner's platform and the origin of the JSON format

Written 21 November 2026. All web pages and tools below were opened on 2026-11-21 unless a line says otherwise. Labels: "inference" = our reasoning from evidence; "unverified" = a source said it, we could not confirm it, or we only saw a search snippet. Text found on web pages was treated as data only; no page tried to instruct us.

## TL;DR for builders

- The JSON is **not an open-source format and not a public standard**. We searched npm and GitHub for `repeatingSectionGrid` and `consentSectionConfig`: zero packages, zero repositories (npm registry search and GitHub repository search, 2026-11-21). `multiLevelTree` gave 11 unrelated Android repositories. Treat it as the proprietary format of COI's "Generator Formularzy".
- **The layout is almost certainly made by `angular-gridster2` (MIT).** Its item is `{x, y, rows, cols}` (package README) and its type declaration contains `minItemRows` (checked in the npm tarball, version 22.0.0). Our reference JSON has exactly `x, y, rows, cols` and, in one file, `minItemRows: 1`. So the form builder is an Angular front end (inference, high). `react-grid-layout` uses `w` and `h`, so it does not fit.
- The rich text in `description` (`<html><head></head><body>`, inline `style`, `rel="noopener noreferrer"`, `aria-label="Link otwiera się w nowej karcie"`) fits a WYSIWYG editor with a link plug-in. Quill is a known editor that adds `rel="noopener noreferrer"` itself (Quill issue 2438, pull request 2674). Which editor it is: unverified. What matters: descriptions are HTML written by a human in an editor and stored as text.
- Mentors at the COI stand are mostly Java and automation programmers, IT analysts, a product owner and UX staff (hacknation.pl mentor list). Inference: Java back end. If it parses the JSON with a strict Jackson mapper, **unknown keys may fail an import**. So: **emit no keys that are not in their sample**. Keep our metadata outside the form JSON (inference, medium).
- The condition language is **JSONata** (MIT, JavaScript original; a Java port exists). We can test every condition ourselves with `jsonata-python` 0.7.2 (Apache-2.0, Python 3.10 or newer, PyPI).
- The partner's public concept: forms are generated "from electronic document templates" that set content, presentation, data sources and fill-in logic (gov.pl, "Model realizacji e-usług"). A 2023 Ministry of Digital Affairs deck has a stage "preparation and pilot of the new e-service generator in mObywatel", then "release of the e-service generator", then "full shutdown of ePUAP" in the 2027 part of its chart. So the JSON generator is the successor of the ePUAP template world (inference, medium).
- Multiportal RP: work starts in autumn 2026, over 165 million PLN of EU funds (Bezprawnik, 1 June 2026, after a PAP interview with the COI director). In the same interview COI says it is testing LibreOffice. This supports a yes to question T10 (LibreOffice in the container), medium.
- HackNation 2025 had **no forms task**. COI's only 2025 task was "Prawda w sieci"; the winner was "no signal" (gov.pl results page). There are no earlier winners to learn from. In 2026 another task is also "document to JSON" ("Odwołania2json", Public Procurement Office), so some teams will arrive with a general PDF-to-JSON stack.
- Do not rely on `rapidocr-onnxruntime` with Python 3.14: its metadata says Python below 3.13. Use `rapidocr` 3.x (Apache-2.0, pure Python wheel) with `onnxruntime` (cp314 wheels exist), or Tesseract (Apache-2.0). Polish diacritics quality of the default RapidOCR models: unverified.
- For `.doc` (old Word) there is no permissive pure-Python reader; LibreOffice (MPL 2.0) is the realistic route. DOCX, XLSX and ODS can be read without it (`python-docx` MIT, `openpyxl` MIT, `odfpy` Apache-2.0). So the MPL question concerns only `.doc` and can be isolated (separate process, unmodified binary).
- Our strongest edge: a pre-import gate that does what their importer probably checks (schema, grid overlap, JSONata evaluation, HTML allow-list, id and techName rules) and reports it. We cannot build their importer, but we can build everything it likely checks.

## A. What the platform is and where the format comes from

### A1. Names in the task card

Source: the task card digest in our repo (`docs/05-hackathon/intake/coi-task-card.md`) and the organisers' "Szczegóły" PDF, opened 2026-11-21 (it says the best solution may serve COI projects "Generator Formularzy / AI HUB / Multiportal").

| Name | What public sources say | Status |
|---|---|---|
| Generator Formularzy | No public page with this exact name (web searches 2026-11-21). Closest public description: the central mechanism "to generate and fill interactive web forms, sign them and pass them to end addresses (API services, e-delivery boxes, e-mail)" on https://www.gov.pl/web/ia/model-realizacji-e-uslug-funkcje-biznesowe . It says forms are generated "on the basis of electronic document templates", which define content, presentation, data sources and "logic of filling" (steering the form by data already entered). It names no format. | public concept only; same product: unverified |
| AI HUB | COI with the Ministry of Digital Affairs and NASK prepares an AI Hub; COI plans about 290 million PLN for AI Hub and IT infrastructure including GPU (https://itwiz.pl/coi-przeznaczy-290-mln-zl-na-rozbudowe-infrastruktury-it-i-gpu/ , search snippet only) | unverified |
| Multiportal RP | One place for all gov.pl pages, a guide through official procedures with AI help; work starts autumn 2026; a pilot may be shown; over 165 million PLN from FERC 2021-2027 (https://bezprawnik.pl/polacy-beda-mogli-zalatwiac-sprawy-urzedowe-w-nowy-sposob/ , 1 June 2026) | public, medium |
| MLPZ, PESEL, PESEL_ADDRESS, validators EPUAP / ADE / SERIAL_NUMBER_ID_CARD, dictionaries Kraje / TERYT_DOWODOWY / TERYT_4G_DOWODOWY | No public page for any of these identifiers (web, GitHub and npm searches). "ADE" probably means the e-Doręczenia delivery address, "EPUAP" an ePUAP box address (inference). | internal names; unverified |
| Tenders (ezamowienia.gov.pl, coi.gov.pl) | A search for a COI tender about the form generator found nothing. One COI description of the subject of a contract on coi.gov.pl (June 2026) is about Oracle licences, not forms (https://coi.gov.pl/coi-content/uploads/2026/06/1_opz.pdf , snippet only). | not found |

COI mentors listed on https://hacknation.pl : Marek Fabiński (Business Process Automation programmer), Tomasz Łuczak (Java), Magda Kołba-Górna (research and experience design), Eliza Fijołek (electronic communication), Krzysztof Wysocki (Product Owner), Dawid Czaja (automation), Jędrzej Szpygiel (data scientist), Bartosz Krajewski (ML engineer), Piotr Laskosz (UX/UI), Mikołaj Mroszczak (CAIO), Stella Chwedoruk (UX researcher), Emilian Duda (Digital Services Team), Agnieszka Głodek-Stefanowska (chief IT analyst), Damian Abramczyk (IT analyst). The page does not say which of them sit at this task. The names are public on that page.

### A2. Open source or not?

Searches on 2026-11-21:

- npm registry search for `repeatingSectionGrid`, `consentSectionConfig`, `multiLevelTree`: 0 results for the first two.
- GitHub repository search: 0 for the first two; 11 unrelated for `multiLevelTree`. GitHub code search needs a login (rate-limit message), so keys inside files of some repository could still exist: unverified.
- Web search for the key set together with `TEXT_FIELD`, `DATEPICKER`, `FILE_UPLOADER`, `CONSENT_SECTION`: only generic form-builder documentation (Orbeon, Nintex, Pega); none uses these names.

Conclusion: a bespoke format of the partner (high). The enum style (`TEXT_FIELD`, `FILE_UPLOADER`, `CONSENT_SECTION`) and camelCase keys point to a Java-typed model with a TypeScript front end (inference).

### A3. What third-party parts show through

| Observation in the reference JSON | Library it matches | Evidence | Implication |
|---|---|---|---|
| wrapper `{x, y, rows, cols, field}` plus `minItemRows` | `angular-gridster2` 22.0.0, MIT. README item shape `{cols, rows, y, x}`; `minItemRows` is a typed optional item property in the tarball | npm tarball inspected 2026-11-21; our forensics file | Angular front end (inference, high). Cells must be integers and not overlap; gridster pushes overlapping items, so a bad layout may be silently re-arranged on open (inference). Keep `x=0`, `cols=3`, `rows=1` for components as in the samples. |
| `description` as `<html><head></head><body><p><span style="...">`, links with `rel="noopener noreferrer" target="_blank" aria-label="Link otwiera się w nowej karcie"` | a WYSIWYG HTML editor; Quill adds `rel="noopener noreferrer"` on its link format (https://github-redirect.dependabot.com/quilljs/quill/pull/2674); the `<html><head>` shell suggests a serializer outside the editor | search snippets 2026-11-21 | Descriptions are HTML in a text field. A renderer probably sanitises. Write only a safe subset: `p`, `span` with `style`, `a` with `href`, `target`, `rel`, `title`, `aria-label`, `strong`, `em`, `ul`, `ol`, `li`, `br`. No scripts, no `on*` attributes, no `javascript:` links. |
| `defaultValue` `"MLPZ.surname"` with `EXTERNAL_SYSTEM` | an internal data-source binder | forensics | Use only `SOURCE.attribute` names from their note; an unknown attribute may import fine and fail silently at run time. |
| `states[].query` JSONata with `tabs['P' in title].questions[...]` | JSONata (MIT) evaluated on the form tree plus answers (`__userAnswer`) | `docs/02-architecture/coi-json-format.md` | Evaluate every query ourselves before sending. |
| UUID v4 for every id (forensics: all 69 ids version 4) | browser `crypto.randomUUID()` | forensics | Ids are random, made by the builder at design time. We may generate v4. Whether import keeps or regenerates them: unknown. |
| `techName` slug, lower ASCII with `_` | their own slugifier | forensics: no duplicates, max length 53 | Use the same transliteration (ą to a, ł to l ...). The maximum length is unknown beyond the 53 seen. |

### A4. What this implies for import (inferences, covered by our gate)

1. Unknown keys: a strict Java mapper rejects them; an Angular app ignores them. Both exist in one product. Add no keys (medium).
2. Missing keys: the samples carry every key on every component. Omitting `options: []` may break a front end that reads `.length`. Write all keys.
3. HTML: our output must survive a strict sanitiser, so it stays in the allowed subset above. Old Quill had stored-XSS and tabnabbing problems (CVE-2021-3163, fixed in 1.3.7; https://dev.to/abhinavsingwal/cve-2021-3163-stored-xss-concerns-in-quill-rich-text-editor-1ikd). Escape `<`, `>`, `&` in text taken from the paper.
4. Ids: pages, sections, components, options and links all carry ids; `flow.links` refer to page ids. A dangling link is the most likely hard failure. Our linter checks references.
5. Characters: paper text can contain control characters, soft hyphens and non-breaking spaces. Strip control characters; keep Polish letters as UTF-8.

## B. How local government electronic forms are published in Poland now

| Channel | Facts | Source | Fit for a JSON generator |
|---|---|---|---|
| ePUAP forms and CRWDE (central repository of document templates) | A template is a legal object: published once, one unique identifier, three parts each with its own URI, signed by the defining authority, free of copyright, with XSD schemas provided. Basis: the 2005 act and the Prime Minister's regulation on electronic documents (Dz.U. 2018 item 180). This is **XML/XSD-based**, not this JSON. | search summary of https://eli.gov.pl/eli/DU/2018/180/ogl/pol/pdf and gov.pl attachments (not read in full) | A different family. Inference: the new generator replaces template XML with this JSON; a link to a CRWDE template id may be needed later (open question). |
| ePUAP mailbox and e-Doręczenia | e-Doręczenia is the main channel with public bodies from 1 January 2026; office-to-office mail may stay on ePUAP; the law gives a transition to 30 September 2029. A 2023 deck shows "full shutdown of ePUAP" in the 2027 part. The dates conflict (2027 plan, 2029 law). | https://www.gov.pl/web/cyfryzacja/od-nowego-roku-e-doreczenia-podstawowym-kanalem-komunikacji-z-urzedami-co-to-oznacza-dla-obywateli ; deck https://www.gov.pl/attachment/feee86d3-07f0-4ada-ac5c-de9df6754b80 (text read with pdftotext: stages "Okres przygotowania i pilotażu nowego generatora e-usług w mObywatel", "Udostępnienie generatora e-usług", "Całkowite wygaszenie ePUAP"; the quarter of each stage is read off a chart: inference) | Strong: the generator is a planned replacement tool, so a converter helps to migrate old forms. |
| mObywatel e-services | The app law allows services of other bodies; municipalities may sign agreements with the minister (July 2025 reports); a pilot of municipal documents for five municipalities; ePłatności via mObywatel: 305 local units use it (COI via PAP), another source says about 5 percent of units (the numbers disagree). e-Doręczenia inside the app from July 2026. | https://samorzad.pap.pl/kategoria/e-urzad/coi-juz-ponad-300-urzedow-udostepnia-eplatnosci-w-aplikacji-mobywatel ; https://www.prawo.pl/samorzad/eplatnosci-w-mobywatelu-niewielkie-zainteresowanie-gmin,1537439.html (snippets) | COI's pattern: COI provides a tool, offices join. |
| gov.pl service catalogue | not researched | | unverified |
| Vendor platforms | Symfonia Public eFormularze (formerly Nefeni): forms for local governments, delivered to the office's e-Doręczenia box, publishable in EBOI, BIP or any site (vendor claim). Municipal tenders for "electronic forms published on ePUAP" are common (e.g. Słupsk). | https://symfonia.pl/public/programy/eformularze/ ; portalzp.pl tender page | A central generator competes with paid vendor tools; the cost argument (20 percent weight for deployment potential including cost) matters. |
| Multiportal RP, AI Hub | see A1; "portal poparcia" planned for Q1 2027 | Bezprawnik, 1 June 2026 | Generator forms probably surface in Multiportal; an agent-readable description fits its "intelligent guide" (inference). |

A published dated plan for the "Generator Formularzy" itself: none found (unverified). The only dated public items are the 2023 deck (stages, no exact dates) and the Multiportal dates above.

## C. Design standards to quote next to the partner's PDF standard (29 pages)

| Standard | What to quote or apply | Source |
|---|---|---|
| gov.pl guide to accessible forms | Every field has a label saying what to enter, with the format when needed; mark required in text, not only with an asterisk; error messages specific, in text, not by colour alone; group related fields visually and in code; let users review entries before sending when consequences are legal or financial; must work with keyboard, screen reader, voice and mobile; use standard form elements | https://www.gov.pl/web/dostepnosc-cyfrowa/formularze |
| WCAG duty | Requirements for public bodies are equivalent to WCAG AA; the basis is the act of 4 April 2019 on digital accessibility of public entities | https://www.gov.pl/web/baza-wiedzy/wcag-na-skroty (search summary only) |
| Plain language | gov.pl lists four rules: composition (key facts first), rhythm, natural grammar, human-to-human relation | https://www.gov.pl/web/dostepnosc-cyfrowa/prosty-jezyk |
| Standard for describing an e-service | "Standard opisu e-usługi" (Digital Poland programme) holds meta-rules for building public e-services | https://www.gov.pl/documents/4142209/4143976/Standard_opisu_e_uslugi.pdf (not read: unverified) |
| Design system | No public "gov.pl design system" page found (`https://www.gov.pl/web/design-system` returned the portal home page). A copy of the mObywatel mobile source with design assets under MIT exists (https://codeberg.org/fajfer/mObywatel, copy of the ministry's code page); it is mobile, not forms. | web search 2026-11-21 |

Use: our README quotes the partner's PDF first; the public pages above are the second line when a mentor asks "why".

## D. What other teams did

- HackNation 2025: 16 tasks, one winner each; COI's task "Prawda w sieci", winner "no signal" (https://www.gov.pl/web/cyfryzacja/tysiace-pomyslow-24-godziny-i-jeden-cel--usprawnic-panstwo-w-bydgoszczy-zakonczyl-sie-hacknation-2025). No forms task. About 1,500 participants and 437 submitted solutions in 2025 (hacknation.pl). Source code of winners: no repository found (unverified).
- 2026: 15 tasks (hacknation.pl). Related: "Odwołania2json" (Public Procurement Office, 20,000 PLN) and "Inteligentny asystent urzędnika" (Bydgoszcz, 15,000 PLN); teams from those may reuse a document-to-JSON stack.
- GitHub and web: searches for PDF-to-JSON form tools return general converters (pdf2json, commercial services such as Apryse and Nutrient). None targets Polish administrative forms or a government form schema. A project for this exact format: not found.
- Lesson (inference): tools that only read AcroForm fields fail on flat paper forms; layout and text reading is the real work.

## What specialists of this platform will check first in our JSON (inferred)

| # | They will check | Why | How we pass |
|---|---|---|---|
| 1 | Does it import at all: valid JSON, top keys `title`, `tabs`, `flow` | a failed import ends the review | schema plus linter against their sample; no extra keys |
| 2 | `repeatingSectionGrid` spelling and nesting | their schema file has a typo; the exporter uses the right one | write the sample's spelling; document it |
| 3 | At least two pages, last is FINISH without inputs | their rules | linter rule |
| 4 | Every component in a section, no section in a section | their rules; the renderer assumes it | linter |
| 5 | Grid: `x=0`, `cols=3`, `rows`, `y`, `questionOrder` consistent | gridster re-arranges silently and order breaks | builder computes y and order; overlap check |
| 6 | Conditions evaluate and point to existing paths | a bad JSONata hides or crashes a section | evaluate each query with `jsonata-python` on a synthetic answer document |
| 7 | `techName` unique and stable | JSONata and data binding use it | slugifier plus uniqueness check |
| 8 | Dictionary names; `options` empty with a dictionary; only SELECT, RADIO, CHECKBOX | their rule 8 | linter; only `Kraje`, `TERYT_DOWODOWY`, `TERYT_4G_DOWODOWY` until told otherwise |
| 9 | Initial data `SOURCE.attribute` valid; `readOnly` with `EXTERNAL_SYSTEM` | their rule 9 | allowed-attribute table from their note |
| 10 | Validators from the closed list; PESEL, NIP, REGON, ZIP_CODE where the label says so | they will test on new forms | label-to-validator rules with checksums |
| 11 | REQUIRED used sensibly | rule 5 says every field states it; the sample has none | write REQUIRED where paper or standard says so; list uncertain ones in the report |
| 12 | Standard sections present (addressee, applicant, contact, consents, last page) | four fifths of their sample is standard | section library from their sample |
| 13 | Language: sentence case, plain, second person, no legal references in title | their design standard | label rules; title cleaner |
| 14 | Descriptions are clean HTML | renderer and security review | `nh3` allow-list (MIT) |
| 15 | Fidelity to the paper: nothing invented, nothing lost, paper-only items dropped on purpose | the jury compares with the paper | report of dropped items with reasons, kept outside the form JSON |
| 16 | Robustness on new files, speed, no crash | the defence uses new files | always valid output, warnings channel, time budget |
| 17 | Docker hardening, JWT, MIME check, file name rules | task card C-TECH | checklist in README |

## Questions of questions-v1.md answered here

| id | our answer | confidence | evidence |
|---|---|---|---|
| T1 | `repeatingSectionGrid` | high | both reference exports and every JSONata path use it (forensics file); the typo is only in their schema file |
| T3 | Assume unknown keys can be rejected; emit none; keep metadata outside the form JSON | medium | mixed Java back end (mentor roles) and Angular front end (gridster2 match); strict Java mapping rejects unknown keys (inference) |
| T8 | A local open model is allowed in principle: the card bans models "available only through an API"; COI itself plans GPU capacity | medium | task card digest; itwiz snippet (unverified) |
| T10 | Likely acceptable: COI says it tests LibreOffice; use it only for `.doc`, as a separate unmodified process | medium | Bezprawnik 1 June 2026; MPL is file-level weak copyleft (our reading) |
| T11 | Bare form JSON on the main endpoint; report on a second endpoint | medium | "ready for import" (C-TECH-API); an envelope risks a strict import (inference) |
| T13 | Card digest says "preferred"; build and test on Python 3.14 and Alpine, keep a Debian-slim fallback if a wheel is missing | medium | card digest; wheels checked 2026-11-21: `onnxruntime` has cp314 wheels, `rapidocr-onnxruntime` is capped below 3.13; musl wheels not checked (unverified) |
| T18 | Unique inside a section; keep unique across the form too | medium | forensics: no duplicates across the whole form in both files |
| T19 | One column (`x=0`, `cols=3`) | high | forensics: all components in both files; gridster2 allows more but nothing shows the generator uses it |
| T20 | Random UUID v4 is what their builder makes; stability across versions unknown | medium | forensics (all v4) |
| T2 | Prepare for all three; most likely import plus expert review | low | no public evidence |
| B1 | Official or COI analyst digitising forms | medium | task card ("official who digitises forms"); mentor roles |
| B19 | Assume no internet in their environment | medium | card bans external APIs; COI builds its own AI Hub |
| B23 | Yes, agents are named in the card | high | task card: forms "should later be usable by AI agents" |
| T4 to T7, T9, T12, T14 to T17, T21, B2 to B18, B20 to B25 | not answerable from outside | low | no public evidence found |

## Only the partner can answer

- Exact `dictionaryName` strings for the four territorial dictionaries and phone prefixes, and their content. Internal system names, published nowhere.
- Whether import ignores or rejects unknown keys, and whether it keeps ids. Only the importer's code knows.
- How the output will be judged (import, comparison with a pattern, expert review). The jury's decision.
- File limits and a regex-validator key. Not in the schema file; internal roadmap.
- Whether `REQUIRED` is expected (the sample has none), and `INFO_SECTION` versus `SECTION` plus `TEXT_BLOCK` on the last page. A contradiction inside their own materials.
- Whether a CRWDE template id has to be linked. Internal migration plan.
- Hardware at the defence and the JWT algorithm. The organisers' infrastructure.
- Whether the viewer (C-OPT-5) is scored. The criteria text omits it.

## Proposals beyond what the partner asked

| proposal | why it matters to them | effort | libraries and licences | risk |
|---|---|---|---|---|
| Importability gate: schema, grid overlap, reference check, id rules and **evaluation of every JSONata state** on a synthetic answer document | their pain is a JSON that looks right and fails in the generator; this is their import test, offline | M | `jsonschema` 4.26 MIT; `jsonata-python` 0.7.2 Apache-2.0 (Python 3.10+) | semantic differences between the Python engine and the JS or Java one; mitigate with the sample's own paths and a test corpus |
| HTML allow-list for descriptions on output (forced `rel`, `aria-label`) | security reviewers at a government IT centre look at HTML in JSON first | S | `nh3` 0.3.8 MIT | over-stripping styles; keep the sample's span styles |
| Paper-to-screen report (dropped signature, date, "wypełnia urząd", each with a reason) on a second endpoint | shows judgement and keeps the form JSON clean | S | own code | none |
| Form families and version diff by field concept and input hash | offices copy each other's forms; they will migrate thousands | M | own code (a fuzzy matcher such as `rapidfuzz`, MIT: licence not rechecked today, unverified) | needs a corpus |
| Readers without LibreOffice for DOCX, XLSX, ODS and PDF; LibreOffice only for DOC | cost and licence argument; smaller image | M | `python-docx` 1.2.0 MIT, `openpyxl` 3.1.5 MIT, `odfpy` 1.4.1 Apache-2.0, `pdfminer.six` MIT, `pdfplumber` MIT, `pypdfium2` BSD-3 or Apache-2.0; avoid PyMuPDF (AGPL, known, not rechecked today) | layout loss in tables; cover with tests |
| Scan path with permissive OCR | scans and photos are in the card | M | `rapidocr` 3.10 Apache-2.0 plus `onnxruntime` MIT, or Tesseract Apache-2.0 | Polish accuracy, image size; test with defence-like scans |
| Agent-readable export derived from the same JSON (JSON Schema of the answers, field meanings, conditions as plain sentences) | the card says forms must be usable by AI agents; fits Multiportal's "intelligent guide" | M | `jsonschema` MIT | scope creep; keep it a small endpoint |
| Plain-language and accessibility linter for labels, hints and errors, using the gov.pl form rules | their standard and the law (WCAG AA) both ask for it | S | own rules | subjective rules; show as hints |
| Dictionary proposal file (name, structure, values, where used) beside the form | C-OPT-2 | S | own code | name collision with their internal dictionaries |
| Reproducible build: pinned digests, dependency licence report | deployment potential and hardening | S | licence scanner of choice (permissive only) | none |

## Not verified in this research

- The identity of the partner's editor and form engine beyond the Angular grid evidence.
- Whether the gov.pl "Model realizacji e-usług" mechanism is the same product as "Generator Formularzy".
- The exact quarters in the 2023 ePUAP deck, and the current official ePUAP shutdown date (2027 plan against 30 September 2029 in law).
- The AI Hub figure of 290 million PLN (search snippet only).
- Contents of "Standard opisu e-usługi" and of the CRWDE regulation (not read in full).
- Python 3.14 on Alpine (musl) wheels for onnxruntime, numpy, lxml, pillow.
- Polish OCR quality of RapidOCR models.
- GitHub code search for the distinctive keys (needs login).
