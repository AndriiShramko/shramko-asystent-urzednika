# WP-F0 … WP-F20 — Track F: a form file in, the partner's JSON out (version 2)

Version 2 of 21 November 2026, 13:55. It replaces the plan written at 11:30. What changed: the decisions of [`../DECISIONS-forms-track.md`](../DECISIONS-forms-track.md) (ids `D1` … `D14`; that file wins), the design in [`../../02-architecture/converter-design.md`](../../02-architecture/converter-design.md) (read its sections named in your package), seven new packages for the accounting features, the measured fact that the build machine has no Docker, and a clock that starts at 14:30.

The card with the ids `C-…`: [`../../05-hackathon/intake/coi-task-card.md`](../../05-hackathon/intake/coi-task-card.md). The partner's format: [`../../02-architecture/coi-json-format.md`](../../02-architecture/coi-json-format.md).

## Rules of this track, on top of `AGENTS.md`

1. **The endpoint answers with the partner's JSON and nothing else** (D1). Everything of ours is in the sidecar (D2).
2. **Nothing in the product calls out; no language model runs** (D12, D13). Hosted models are a build tool only (`tools/eden/eden.py`, D14): silver labels, lexicon mining, a second opinion on a diff. What they produce becomes a rule, a table row or a test, never product output.
3. **Every package runs and tests natively on Windows.** The laptop has no Docker and no WSL. Source stays compatible with Python 3.13; the image runs 3.14. Code that exists only on Linux sits behind the platform switch of the worker (design 9.3). A test that needs Linux, Docker or Tesseract carries a marker (`linux`, `container`, `tesseract`) and is reported as skipped, never as passed.
4. **CI is the source of truth for the image** (design 9.2, WP-F20). A package whose acceptance mentions the container is accepted on the CI run, not on a local build.
5. Dependencies: open source, not copyleft, wheel only, pinned with hashes. A builder asks the lead for a new dependency in its status file; the lead adds it to `apps/converter/pyproject.toml`. `tools/licence_check.py` fails the gate on GPL, AGPL, LGPL, MPL or an unknown licence; weights, OCR data and fonts count as dependencies.
6. Uploaded files live in memory or in a temporary directory removed in a `finally` block; content is never logged.
7. The task sets are **not in git**. Code finds them with `tools/coi_paths.py`; nobody commits them.
8. Contracts first: `contracts/coi/*.schema.json` are written by the lead (WP-F0) before the first wave. A builder who needs a contract change writes a request; it does not edit the contract.
9. Every package keeps `docs/03-plan/wip/WP-F<n>.status.md`, starts with the resume block of `docs/04-orchestration/subagent-brief-template.md`, and commits after every finished step.

## Which packages need Docker

| Needs a container to be accepted | Everything else |
|---|---|
| WP-F1 (only its image items), WP-F16 (the limits and the self-test on Linux), WP-F20, WP-F12 (the SBOM of the final image, the clean-container README test) | WP-F0, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F13, F14, F15, F17, F18, F19: native Python and Node on Windows are enough |

## Packages

| Id | Package | Depends on | Kind | Card and criterion |
|---|---|---|---|---|
| WP-F0 | Contracts, golden pairs, the docket of contradictions | none | think, lead | C-MAT |
| WP-F1 | Environment check; service shell: endpoint, guard, token, configuration, command line, Dockerfile, README | none | by spec | C-TECH |
| WP-F2 | Readers: a) PDF and DOCX, b) XLSX, ODS, binary Word, c) images | F0 | by spec | C-TECH-FMT |
| WP-F3 | Finder: places to fill, labels, groups, sections | F2a | think | C-MIN-1a |
| WP-F4 | Understanding: the brief | F3 | think | C-MIN-1a, 1c |
| WP-F5 | Composer: library of standard sections, pages, ids | F0 | think | C-MIN-1b, 1c |
| WP-F6 | Dictionaries, initial data, proposals | F4, F5 | think | C-OPT-1, C-OPT-2 |
| WP-F7 | Conditions | F5 | think | C-OPT-3 |
| WP-F8 | Validation pack | F0 | by spec | C-OPT-6 |
| WP-F9 | Front end, view "Przegląd" | F0 | by spec | C-OPT-4, intuitiveness |
| WP-F10 | Front end, view "Podgląd e-usługi" with journeys | F0 | by spec | C-OPT-5, intuitiveness |
| WP-F11 | Evaluation run, results, numbers | F5 | by spec | C-TEST, C-SUB |
| WP-F12 | README, architecture document, licences, SBOM | F1 … F8 | by spec | C-MIN-2, C-TECH-DOC |
| WP-F13 | Agent pack; form family | F5 | by spec | originality |
| **WP-F14** | **Pre-import gate, journeys, zero-answer canary** | F0 | think | code quality, C-TEST |
| **WP-F15** | **Accounting sidecar: origins, ledger of blanks, omissions, receipts, coverage** | F3, F5 | think | intuitiveness, originality |
| **WP-F16** | **Parser airlock, egress guard, self-test, hostile corpus** | F1 | by spec | code quality, deployment |
| **WP-F17** | **Filled-form alarm, content-free audit** | F3 | by spec | deployment |
| **WP-F18** | **Legal redline: two versions, typed changes** | F5 | by spec | originality, deployment |
| **WP-F19** | **Resource report and cost dial** | F1 | by spec | deployment (cost) |
| **WP-F20** | **Image pipeline in CI** | F1 | by spec | C-TECH-DOCKER |
| WP-P1 | Presentation, film, submission texts | F11 | think | C-SUB |

Owned paths of every package: [`../ownership.md`](../ownership.md). Tests of a module live in `apps/converter/tests/<module>/` and belong to the owner of the module.

---

## WP-F0 — Contracts, golden pairs, docket (lead)

Done on 21 November: the materials and reference set 1 are in git; all nine sets are unpacked locally; the format is described; `contracts/coi/form.schema.json` and `tools/coi_lint.py` exist; the facts of both exports are measured.

Left, before the first wave:

1. Two profiles of the form schema. `strict`: what we emit (D3, D4, D7; no key outside the documented ones plus `multiLevelTree`, `searchEnabled` where the exports have them). `tolerant`: what the partner's own exports contain (link ids that are not UUIDs, an option without `techName`, `validation: {}`, `minItemRows`).
2. `contracts/coi/page-model.schema.json`, `brief.schema.json`, `meta.schema.json`, each with one example, from design section 5.
3. `eval/golden.json`: reference set 1 (eight inputs) and reference set 5 (seven inputs), two expected forms; the seven judged sets with their inputs.
4. `docs/02-architecture/contradiction-docket.md`: the places where the partner's materials disagree, each with the rule text, what the exports show, our decision, the switch, the question id. One page.
5. The mentors' answers go into DECISIONS section 6 and 7 the moment the owner brings them.

Acceptance: both exports pass the `tolerant` profile and the linter with zero errors (reference set 5 gives four errors today); the five existing negative controls still fail; `golden.json` lists fifteen golden inputs and two expected forms; every contract example validates. **Negative control:** a form with a fourth top-level key fails `strict`.

## WP-F1 — Environment check and service shell

**Step 0, before anything else: `python tools/env_check.py`.** It prints one line per piece and never changes the machine.

| Piece | Check | If missing | Who can fix it |
|---|---|---|---|
| Python 3.14 | `py -3.14 --version` | install for the current user only (no administrator rights). Until then develop on 3.13; the source stays compatible | an agent may try the per-user install; otherwise the owner |
| Docker | `docker version` | path (a): the owner installs WSL 2 and Docker Desktop (administrator rights, a restart). Path (b): go on without it; CI builds and proves the image (WP-F20) | the owner only |
| WSL | `wsl --status` | as above | the owner only |
| Tesseract with Polish data | `tesseract --list-langs` shows `pol` | install it for the user, or go on: the second OCR engine installs with `pip` for development and the Tesseract tests run in CI | the owner or an agent |
| Node 22 | `node --version` | present on the laptop | |
| Push of a workflow file | a one-line workflow pushed to a branch | sign in to git again so that the credential may change workflows | the owner |
| Actions and the registry | the first run is green and the image is listed | repository settings: Actions on; the package set to public | the owner, one click each |

The result is written to `docs/03-plan/wip/environment.md` and decides nothing in the code: the product never asks which path was taken.

Then the shell: `POST /v1/forms/convert`, `?report=1`, `/v1/forms/report`, `/v1/forms/inspect`, `/v1/batches`, `GET /healthz`, the problem answers (design 3); the command line `python -m converter convert|serve`; configuration (design 4), validated at start, refusing an inconsistent set; token check (design 8: algorithm from configuration only, never `none`, `exp` required, issuer and audience when set, capped leeway, key by file, no key fetching); the guard (design 6.1). At this point the pipeline behind it may be a stub that returns a fixed valid form. Dockerfile with the two targets of design 9, digests pinned, a dedicated user, one port, the front end built in a Node stage; `docker-compose.yml`; `apps/converter/README.md` with build, run (native and container), configuration table, the API with a `curl` example.

Acceptance, native: the service answers `healthz`; a valid PDF returns 200 and the body passes the gate; **negative controls**, each a test: wrong extension; PNG bytes named `.pdf`; a DOCX named `.xlsx`; a legacy workbook named `.doc`; a file that is both PDF and ZIP; `.jpe` accepted by default and refused with `STRICT_EXTENSIONS=true`; upper-case extension accepted; name with `%`; name of 251 characters; a file one byte over the limit, also when the declared length lies; no token; expired token; a token with no algorithm; a token of the wrong family signed with the public key as secret; wrong audience. Acceptance, container (on the CI run): both targets build from a clean checkout; the process is not root; with `--network none` the command line converts reference set 1.

Cheapest test that would prove us wrong: swap the suffixes of a valid DOCX, XLSX and ODS; all three must be refused by content, not by a generic "it is a ZIP".

## WP-F2 — Readers

One page model for all formats (design 5.1, 6.2). Three parts that touch different files and can run at different times.

**F2a: PDF and DOCX.** PDF: text and character boxes, lines and rectangles, declared fields; a page with almost no text goes to the image way (F2c). DOCX: body paragraphs, tables, tabs and leaders, symbols, content controls, legacy form fields, footnotes, **and text boxes with their anchor offsets**: the DOCX files of sets 2 and 8 are nothing but text boxes (65 and 651 of them; each is stored twice in the file, as a drawing and as its fallback, which is where the first count of 130 and 1,302 came from) and a reader of ordinary paragraphs returns an empty document.

**F2b: XLSX, ODS, binary Word.** Sheets: the grid is the layout (35 to 759 merged ranges per form); cells, merges, borders, sizes; repeat counts of ODS bounded before expanding; hidden sheets read and reported. Binary Word: the native reader of design 6.2.1, `origin: flow`.

**F2c: images.** Decode with limits, drop metadata, cut the tall scan into pages (the scans are 1654 pixels wide and up to 37,424 high), OCR per page with word boxes and confidence, raster detection of lines, boxes, leaders and combs without OpenCV. A PDF without text takes this way after rendering.

Acceptance: `eval/readers-sets.json` lists, for every file of the nine sets, the reader used, pages, runs, lines, rectangles, seconds, and no unhandled exception; the DOCX of sets 2 and 8 are read **with boxes**: at least 60 runs for set 2 and more than 600 for set 8 (measured by WP-F2a: 65 and 651; the PDF of set 2 gives 70); the scan of set 9 becomes sixteen pages and the one of set 8 six; every `.doc` of the nine sets gives the title of its form in the first twenty runs, or a 422 with a reason; a broken file gives 422 without a stack trace. **Negative controls:** a text file named `.docx` never reaches a reader; an ODS with a row repeated a million times is refused before it is expanded; a scan of 100,000 × 100,000 pixels is refused from its header.

Cheapest tests that would prove us wrong: (1) a PDF made only of a photographed page, converted offline: it must take the OCR way; (2) the same form through all its formats must give the same title in the first heading run (this is the first line of the eight-format table of WP-F11).

## WP-F3 — Finder

Design 6.3: reading order; roles of text; candidates by kind; labels by score; groups.

Acceptance: `eval/finder-sets.json` records candidates per kind for the PDF and DOCX of the nine sets; on reference set 1 the four blanks of the sentence are found with their labels; on set 2 the postal code and both dates are **one comb each** with the right cell count and mask, and the account is **one field** (the paper draws a single box without dividers, measured by WP-F3 on the PDF and on the DOCX; that it holds 26 digits is the understanding step's knowledge of the label, not a count of cells); on set 7 `❑ pies ❑ suka` is one group of two and the three marking boxes one group of three, two of them with a blank; on set 9 the character `□` counts as a box; section A of set 7 is recognised as the applicant block although it is printed after section B. **Negative controls:** an information sheet without places to fill yields zero candidates and the warning `NOT_A_FORM`; an instruction with a drawn example of a ticked box is not a group; the data-protection clause yields no candidate.

Cheapest test that would prove us wrong: one page hand-marked with an empty box, a printed bullet, a crossed box and an eleven-cell PESEL must come back as one choice group (not four fields) and one PESEL field.

## WP-F4 — Understanding: the brief

Design 6.4. Rules in this order: title and addressee; who may apply (the three notions: person at the keyboard, party, capacity) from the wording table; the paper habits table; required or not; labels rewritten by the standard's rules; composite papers. Lexicons are data files in `apps/converter/app/lexicon/` with a source and a date per row. Build-time help: `tools/eden/eden.py` may mine the labels of the nine sets and of the city archive for phrase variants; a mined row enters a lexicon only after a rule test uses it.

Acceptance: for reference sets 1 and 5 the brief from every format has the same title, addressee, applicant options and fields of the matter (labels from images may differ by the recorded distance); for each judged set a brief is stored in `eval/briefs/` and its differences from the silver labels are listed and explained; every `REQUIRED` in a brief has evidence or the flag `REQUIRED_INFERRED`; set 6 produces the warning `ADDRESSEE_CONFLICT` with both quotes; set 9 produces one selector and no second form. **Negative controls:** "Załącznik nr 2 do Regulaminu …" never becomes a title; the clause on page two never becomes fields; "hodowanie/utrzymywanie*" becomes one choice while "charta/chartów*" becomes none; a fee that is not on the paper stays `not_found`.

Cheapest tests that would prove us wrong: (1) rename the file, replace the municipality and the title, run again: the fields of the matter must not change; (2) one form from the city archive that no author of the rules has seen: read its brief before reading its paper.

## WP-F3b — Matter quality: finder, understanding and composer second pass (new, 21 November 17:45)

WP-F4 is merged (`559d839`): the pipeline runs reader → finder → understanding → composer, and the judged sets give fields of the matter (PDF, DOCX): set 2: 5 (5); 3: 2 (2); 4: 7 (6); 6: 18 (16); 7: 10; 8: 32 (24); 9: 83 (42). Silver labels (two hosted models, `eval/silver/`, local) found more on sets 3 (3 vs 2, and ours do not match), 4 (7 vs 4 matched), 6 (24 vs 16 to 18). This package owns `apps/converter/app/find/**`, `app/mean/**`, `app/lexicon/**`, `app/compose/**` and their tests, for this pass only, so that no fix waits on a request between packages. Audit tickets T1 (field tests) and T4 apply ([`../audit-tickets-2026-11-21.md`](../audit-tickets-2026-11-21.md)); decision D20 (scaffold pruned only on an explicit exclusion).

Fix, each with a test on a synthetic fixture and, where the sets show it, a `sets` test:
1. **Set 9 PDF:** no section and no bold in the finder, so both alternatives flatten into one section of 83 fields; it must give one selector (`rodzaj_wniosku`) and sections like the DOCX.
2. **Single boxes not grouped** on sets 8 and 9 (22 to 35 candidates per file wait for a decision): group options on one line or one column under one question.
3. **Set 3:** the private-use character U+F0F0 marks options, not boxes; the certificate options (five, including "inne" with its text field) and the purpose field must come out.
4. **Reference 1:** PDF capital "W" of the addressee sits in the previous run; DOCX two-column line "Wnioskodawca: Adresat:" needs an addressee rule. Reference 1 must give the same title, addressee and four property fields from PDF and DOCX.
5. **Composer:** a yes-or-no CHECKBOX of the brief (no options) must compose into a shape the strict linter accepts (an option pair, or the partner's own form of a single box as measured in the exports); `ComposeResult.brief_keys` carries `Attachment.key` for FILE_UPLOADER.
6. **Audit T1 fixtures:** two one-page PDFs "Wniosek o rezerwację" with "Numer sali ...." versus "Liczba uczestników ....": different outputs, a room field and a numeric count; "ZAWIADOMIENIE O ZBYCIU POJAZDU" with buyer PESEL, VIN, "Data zbycia" (DATEPICKER).
7. **Audit T4:** titles in sentence case without "*"; "Wniosek składa się wyłącznie osobiście" removes the proxy route (D20, quote in the sidecar); a parent/child or buyer block keeps its own owner and is never prefilled from the logged-in user.

Acceptance: on the judged sets, fields of the matter matched to the silver labels rise on sets 3, 4 and 6 (table before/after in the status file); no set loses a field it had; reference 1 gives the same brief from PDF and DOCX; set 9 PDF has one selector; every converted set passes the gate with 0 strict-linter errors; the check chain (`bash tools/gate.sh py -m eval.chain --compare`) shows no new failure. **Negative controls:** the RODO clause yields no field; "Załącznik nr 2 do Regulaminu" never becomes a title; a drawn example of a ticked box in an instruction is not a group.

## WP-F5 — Composer

Design 6.5. Library of standard sections cut from both exports, with parameters where the exports differ; pages; alternative content as conditional sections on pages that never become empty; repeating sections (`REPEATING_STYLE`); grid; ids from meaning (D10); techNames (D7); HTML from templates only (D11); the last page (D5).

Acceptance: a test rebuilds every standard section of both exports and compares it with the export, ignoring ids; for both reference sets our form has the same pages, the same standard sections by techName and the fields of the matter of the export, and a printed comparison lists matched, missing and extra components; two runs on the same file are byte-identical; **changing one label of a fixture brief changes that title and no id**; no page can be empty on any journey. **Negative controls:** two sections with the same title still give unique techNames; a label `<img src=x onerror=1>` arrives as text; a brief with a hundred fields in one section is split over pages.

Cheapest test that would prove us wrong: remove every node of origin `standard` from each of the seven outputs and give a reader only what is left: can the reader tell which service it is and fill in its substance? If not, the standard scaffold is hiding an empty matter.

## WP-F6 — Dictionaries, initial data, proposals

Design 6.6. In the form: only `Kraje`, `TERYT_DOWODOWY`, `TERYT_4G_DOWODOWY` (D9) and only the three documented sources, for the person at the keyboard. In the sidecar: proposed dictionaries with evidence, proposed sources for entities in the partner's notation, proposed validators.

Acceptance: on both golden pairs every dictionary and every initial-data source of the export is reproduced on the same field; set 8 yields a proposed dictionary for the kinds of filer, set 3 for the kinds of certificate, each with its entries and pages; entity fields carry proposed sources. **Negative controls:** a made-up option list never produces a `dictionaryName` in the form; with a pełnomocnik acting for an entity, no field of the entity has a default from `MLPZ` or `PESEL` (sentinel test).

## WP-F7 — Conditions

Design 6.7. A typed predicate tree; a writer that emits only the subset seen in the exports, plus the repeating-section notation of the rules document; a resolver; conditions from the wording of the paper ("jeżeli", "w przypadku", "dotyczy", "wypełnić tylko w przypadku zaznaczenia …", "jeśli różni się od …"), from an option followed by a blank, from alternative blocks.

Acceptance: every condition of both exports is parsed into the tree and written back to the same text; fixtures with a known condition on a field, on a section, on an "inne" text field and inside a repeating section produce the expected text; set 2: the account number is shown only for the transfer; set 8: the spouse section only for the second kind of filer; set 9: the variant sections only for their variant. **Negative controls:** a condition whose path selects two sections is refused; a reference to a position number that does not resolve ("poz. 34" when no field carries 34) becomes a hint and a decision, not a condition; a form without conditional wording gets none beyond the standard ones.

Cheapest test that would prove us wrong: two labels `Łódź` and `Lodz` in one section, a page title in quotes, then rename a page: every state must still resolve to exactly one field.

## WP-F8 — Validation pack

Design 6.8. Our own checks of values (PESEL, NIP, REGON 9 and 14, postal code, e-mail, ePUAP box, e-Delivery address, identity card, bank account, KRS, land register, phone); the table concept → partner validator name (D8); the same functions exported for the viewer and for the filled-form alarm.

Acceptance: every rule has at least one valid and one invalid synthetic value, and no value of a real person; set 9 gets `EPUAP`, `ADE` and `SERIAL_NUMBER_ID_CARD` on the right fields; set 2's account becomes the proposal `NRB` in the sidecar and nothing in the form; `VALIDATORS=off` gives empty lists everywhere. **Negative controls:** a nine-cell comb labelled "telefon" does not become REGON; a field labelled "PESEL współmałżonka" is still PESEL.

## WP-F9 — Front end, view "Przegląd"

One application with WP-F10 (design 2). Polish, keyboard-usable, WCAG 2.1 AA. Upload by drag or button; the paper's page beside the form tree, found places outlined, a click on either side selects the other; **two ink colours** with the switch "tylko to, co przyszło z papieru"; the ledger as five numbers that open their rows; omissions with their reasons; the three receipts; decisions as a few cards, each naming how many warnings it settles; lowest confidence first; the form as text to read, copy, download; the batch table fed by `/v1/batches`. No editor of forms.

Acceptance: the film can be recorded on it without a cut; both exports' sets and two judged sets load; an automatic accessibility check of our own rules (labels, focus order, contrast tokens) has no critical finding; fifty files finish in the batch table and the table equals the stream. **Negative control:** with the sidecar missing, the view still shows the form and says what is absent. **Every device (owner, 21 November 16:45):** every page a person opens is checked at phone width (375 px), tablet (768 px) and desktop (1280 px and wider), in at least two engines (Chromium and Firefox or WebKit, through Playwright), with no horizontal scroll, no overlapping or cut text and every control reachable; one screenshot per width and engine is the evidence in the status file.

Cheapest test that would prove us wrong: time someone who did not write it correcting one wrongly grouped choice. If that is impossible without the source code, the view is called inspection in every text, not review.

## WP-F10 — Front end, view "Podgląd e-usługi"

Renders the e-service from a form alone: pages as steps, sections, fields with hints, known dictionaries as short sample lists marked as samples, conditions live with the bundled reference evaluator, validation messages in Polish, locks on read-only initial data (fictitious values, marked). Buttons for the six journeys and for the zero-answer state; a list "what this journey shows and hides".

Acceptance: both exports render without an error and behave as hand-predicted on one route each; our outputs for the judged sets render; one condition and one validation are shown working in the film. **Negative control:** a form with a condition that does not parse shows the error at the field, not a blank page. **Every device (owner, 21 November 16:45):** every page a person opens is checked at phone width (375 px), tablet (768 px) and desktop (1280 px and wider), in at least two engines (Chromium and Firefox or WebKit, through Playwright), with no horizontal scroll, no overlapping or cut text and every control reachable; one screenshot per width and engine is the evidence in the status file.

Cheapest test that would prove us wrong: load both **untouched** exports and predict one route by hand from the JSON before clicking. If viewer and emitter only agree with each other, they share a bug.

## WP-F11 — Evaluation run and numbers

`python -m eval.run`: converts the golden and the judged sets natively (and, where Docker exists, through the image), compares with the exports (design 10: fields all and matter-only, types, validators, dictionaries, conditions by behaviour, standard sections), builds the eight-format agreement table, checks ledger, coverage and gate per form, aggregates time and memory by input class, and writes `eval/metrics.json` and `results/<set>/form.json` with `meta.json` for the seven judged sets. `eval/silver/` holds the build-time labels of a hosted model for the nine sets and the comparison with our briefs.

Acceptance: `results/` holds a form and a sidecar per judged set and each passes the gate; `metrics.json` comes from one command on a clean checkout; every number in the presentation equals the file. **Negative controls:** an export scored against itself gives 1.0 everywhere; the same export with one field removed scores below 1.0 in recall and nowhere else.

Cheapest test that would prove us wrong: from the city archive take one random page per kind of file, hand-score it, and publish the unique counts, the failures and the peak memory, not only the throughput.

## WP-F11a — Check chain (new, 21 November 16:40, explicit request of the owner)

The owner: no form of any kind may surprise us at the finals; the files the partner showed and unseen files must all pass. One command, `bash tools/gate.sh py -m eval.chain` (module `eval/chain/`, owned with `eval/**`), runs three corpora through the same entry the service uses (`app.pipeline.run`, natively; `--image <ref>` runs the same corpus through `docker run --network none --read-only` and `python -m converter convert` when Docker exists):

1. **Sets:** all 69 files of the nine task sets, found only through `tools/coi_paths.py`.
2. **Unseen:** a fixed, seeded sample of the city archive (asset of the GitHub release `pre-event` of this repository, 676 files, about 183 MB; download it once with `curl` into the git-ignored folder `data/archive/`, add that folder to `.gitignore`, verify the size against the release). The sample: up to 15 files per format (pdf, doc, docx, odt if present, ods, xls, xlsx, jpg, jpeg, png), at least 80 files in all, chosen by a fixed seed and written as a list of names and hashes to `eval/chain/sample.json` (committed; the files are not). Run `-I` Python on these downloaded files where Python reads them outside the pipeline.
3. **Hostile:** the hostile corpus built from code (`apps/converter/tests/evil` when WP-F16 lands; until then a small set made in `eval/chain/hostile.py`: a text file named `.pdf`, an empty file, a truncated PDF, a zip bomb named `.docx`, a 1×1 PNG, a PNG with a 100,000 × 100,000 header, an ODS with a row repeated a million times).

Per file (one JSON line in `eval/chain/last-run.jsonl`, git-ignored, and a summary `eval/chain/summary.json`, committed): corpus, format, outcome class `converted` | `refused` (a problem answer with a Polish `detail`) | `failed` (any other exception, a timeout of 120 s per file run in a subprocess, or a refusal without a Polish reason), seconds, gate verdict, number of strict-linter errors (`tools/coi_lint.py` strict profile), fields found, fields of the matter, places without a label, warnings by code. Totals per corpus and per format. **No content of any file is logged; names of archive files are hashed in committed files.**

Baseline: `eval/chain/baseline.json` (committed). `--compare` prints, per file and per total, what got better and what got worse against it, and exits non-zero on any new `failed`, any new gate failure, or a fall in fields found of more than 20 % on a file of the sets. `--update-baseline` rewrites it (the lead runs it after a merge that improves numbers).

Acceptance: the chain runs on a clean checkout in under 15 minutes natively; zero `failed` on all three corpora (a failure found is fixed in the owning package or recorded as a request to the lead with the file's hash and the exception class); a test on synthetic fixtures proves each outcome class and the compare step; the owner's page `docs/03-plan/check-chain.ru.md` (Russian, plain words, one screen): what the chain checks, the last totals, how to read better/worse. **Negative controls:** a corrupted fixture forced to raise inside the pipeline is classed `failed` and makes the chain exit non-zero; a baseline with one more field on one file makes `--compare` report a regression.

## WP-F12 — README, architecture, licences

`apps/converter/README.md` complete (build, run native and by image digest, configuration, API with `curl`, limits). `docs/02-architecture/converter.md`: the jury's architecture document (C-MIN-2), four pages cut from the design: one diagram, the steps, what runs without a model, what never leaves the container, measured cost. `LICENCES.md` from `tools/licence_check.py`, **listing separately** Python wheels, native libraries inside wheels, programs called (Tesseract), OCR data, fonts, the front-end bundle, packages of the base image. The docket of contradictions as a page. SBOM and signature come from WP-F20.

Acceptance: a reviewer agent that has not seen the project runs the service natively from the README alone and converts reference set 1; the CI log shows the same from the image; the licence check passes. **Negative control:** a planted GPL dependency fails the check.

## WP-F13 — Agent pack and form family (after the gate G-F)

Agent pack: from a form and its sidecar, three files: a JSON Schema of the answers, a tool description (name, purpose, typed parameters, choices, which fields come from a register, which need the person: consents, declarations, signature), a short text description. Files, not a server; no tool submits anything. Form family: field concepts of a converted form compared with those already converted; shown as shared part and differences in fees and attachments.

Acceptance: the schema validates as JSON Schema 2020-12 and accepts the answers of journey 1 and refuses an answer for a hidden field; the family view groups the two residence forms of the city archive. **Negative control:** the pack contains no endpoint and no credential field.

## WP-F14 — Pre-import gate, journeys, canary (new)

Design 7.1, 7.2. Checks G1 … G12 as one module used by the service before every answer and by the evaluation; the journey harness with `jsonata-python`; the six fixtures; the zero-answer canary. It can start at once: its first inputs are the partner's two exports.

Acceptance: both exports pass G1 … G10 under the `tolerant` profile; **each check has a fixture that fails exactly that check** (twelve negative controls); the six journeys on both exports are stored as snapshots after one route of each was predicted by hand; with no answer, every conditional component of both exports is hidden; a form with a page that can become empty fails G8; a gate failure in the service is a 500 with the name of the check and no form.

Cheapest test that would prove us wrong: answer "Polska" and then "Niemcy" in the country field of export 1 and compare the visible address fields with the partner's visualisation document.

## WP-F15 — Accounting sidecar (new)

Design 5.4, 7.4. Origins per node (`paper`, `standard`, `reviewer`); evidence (page, box or anchor, quote); the ledger of blanks with its five fates; omissions with reason codes; the three receipts (fee, who may apply, mandatory attachments) with `stated`, `not_found`, `ambiguous`; coverage of text runs; decisions grouped so that one settles many warnings; `unsupported` behaviour of the paper.

Acceptance: the ledger closes on all nine sets; coverage has no unassigned run of more than three words; every field of origin `paper` has evidence; set 7 states the fee with its quote, set 2 says `not_found`, set 3 states 17 zł per copy; set 8 lists the arithmetic under `unsupported`. **Negative controls:** deleting the fate of one candidate fails G11; a page with ink and no candidate is reported by number; the word accuracy does not occur in the sidecar or in the view.

## WP-F16 — Parser airlock and the hostile corpus (new)

Design 8, 9.3. The worker process per upload with the two limit implementations; the audit-hook guard; `GET /v1/selftest`; `python -m tests.evil`, which builds every hostile file from code (no hostile binary is committed) and prints a pass or fail line per attack.

Acceptance, native: the corpus runs on Windows for everything that does not depend on the operating system; a job that spins is killed at the timeout and **the next job succeeds**; the worker's environment holds no key. Acceptance, container (CI): all attacks of the design table pass; the self-test reports `none` and both blocks with `--network none`, and "kernel: not isolated; guard: active" with a published port; the process has no capability and cannot write to the root. **Negative controls:** the corpus itself; plus one test that the guard, when switched off, lets the canary connection through (so the test is able to fail).

## WP-F17 — Filled-form alarm and content-free audit (new)

Design 8. Signs of a filled form: valid PESEL, NIP or account numbers inside fill areas; typed values in declared fields; ink density inside boxes and on leaders. Behaviour by `FILLED_FORM`. Audit events with stage, reason code, buckets, random job id, hash of the input.

Acceptance: a synthetic filled fixture raises the warning and its values are absent from the form, the sidecar and every log line; the nine blank sets raise no alarm. **Negative controls:** the dummy account number printed in the information block of set 3 and the one in the header of set 7 are not fill-area values and raise nothing; a sentinel surname placed in the file name, in the text and in a parser error appears in no log.

## WP-F18 — Legal redline (new, after G-F)

Design 6.9. `POST /v1/forms/diff` and a panel in the review view.

Acceptance: a fixture pair (one label changed, one field added, one option removed, the fee changed) gives exactly those typed changes with their grades, and the fee change is named as a fee change; two identical forms give an empty list; the unrelated ids of the pair are equal. **Negative control:** a field moved to another section is reported as moved, not as removed plus added.

## WP-F19 — Resource report and cost dial (new, after G-F)

The per-request report (`Server-Timing`, the `resources` block of the sidecar): wall and CPU time, peak memory, pages, OCR pages. Aggregation by input class. A panel that multiplies openly to 2,477 municipalities with the share of scans and the review minutes as editable assumptions.

Acceptance: numbers come from the run, not from constants; the panel marks every extrapolated figure; the README quotes the same file. **Negative control:** with no measurement file the panel shows no number.

## WP-F20 — Image pipeline in CI (new)

Design 9.2. `.github/workflows/image.yml` and helper scripts in `tools/ci/`.

First step, in the first half hour, by the lead: a one-job workflow that only prints the Python version, pushed to a branch: it proves that workflows can be pushed and run.

Then the six steps of design 9.2: native suite on Linux with Python 3.14; both targets built with pinned digests and wheel-only installs; `core` started with no network, read-only root, a dedicated user, no capabilities, converting reference set 1 through the command line and comparing with the stored expectation; a second start with a port for the HTTP path and the negative controls; the hostile corpus and the self-test; SBOM, vulnerability gate, licence gate as artefacts; push to the repository's registry under the commit hash, signed; the digest written into the README by the lead.

Acceptance: the workflow is green on `main`; the run page shows the conversion inside the container without network; the image can be pulled by digest and started on a machine that has only Docker. **Negative controls:** a base image without a digest fails the run; a dependency that has only a source distribution fails the build; a planted failing attack makes the corpus step red.

Cheapest test that would prove us wrong: pull the published image on another machine, start it without network, convert one genuine file of every extension, and read the error stream: nothing may be downloaded at start, no data file may be missing.

## WP-F20f — Do it for the user: every format the service can read itself (new, 21 November 17:25, D24)

The owner's order of 17:10: never ask the user to re-save a file; the service converts whatever it safely can. The lead's inventory of refusals (17:15): 6 of the 8 refusals of the unseen sample are decided by the extension alone (5 RTF, all cp1250, 4 of them with tables; 1 BIFF8 `.xls`); one PDF is a reader crash, not a bad file (pdfplumber `page.annots` raises `UnicodeDecodeError` on a legacy 8-bit annotation string of a normal 10-page text PDF; the catch-all reports it as "uszkodzony"); one JPG did not reproduce natively.

Branch `wp/F20-f-user-formats` from `main` (the image workflow runs for `wp/F20-**`). Status `docs/03-plan/wip/WP-F20f.status.md`. Owned: `apps/converter/app/guard/**`, `apps/converter/app/readers/**` (new `rtf.py`, `xls.py`, `txt.py`, `heic.py`), the list of formats without a reader in `apps/converter/app/pipeline.py`, `apps/converter/tests/readers/**`, `apps/converter/tests/guard/**`, `apps/converter/Dockerfile`, `.github/workflows/image.yml`, `tools/ci/**`, `apps/converter/pyproject.toml`, `apps/converter/requirements*.lock`, `NOTICE`.

**Stage 1a (natively): routing by content and three readers.**
1. The guard routes by content. New extensions: `rtf`, `xls`, `txt`, `heic`, `heif` (WP-F20e added tif, tiff, bmp, gif, webp, odt). Proofs: `{\rtf` → rtf; OLE with a `Workbook` stream → xls (a `Book` stream is BIFF5: read it if xlrd does, otherwise a plain refusal); ISO-BMFF `ftyp` with a brand heic, heix, hevc, hevx, heim, heis, mif1 or msf1 → heic; bytes without NUL that decode as UTF-8, UTF-16 with a BOM or cp1250 → txt. When the extension and the content disagree and the content is exactly one known kind, the file is read as that kind with a warning ("Rozszerzenie .X nie zgadza się z zawartością; plik odczytano jako Y."), never refused (a `.doc` that holds RTF is the common case). A polyglot (several proofs) stays refused.
2. RTF reader, our own, pure Python, no dependency: an explicit stack (no recursion) with a depth cap; the `\ansicpg` code page, `\'xx`, `\uN` with `\ucN` skipping; `\*` destinations and fonttbl, colortbl, stylesheet, info, pict, object, header and footer skipped; `\par` and `\line` break paragraphs, `\tab` is kept; tables `\trowd … \cell … \row` (nested `\nestcell` and `\nestrow` flattened) become table cells; a field gives its `\fldrslt` text; a form field `\formfield` with `\fftype1` is a checkbox candidate and with `\fftype0` a text blank. It gives the same flow page model as the ODT reader of WP-F20e (paragraphs `p[n]`, tables `tbl[n]/cell[r,c]`). Limits on characters, cells and groups.
3. XLS reader: `xlrd` 2.0.2 (BSD-3-Clause, approved by the lead; `research/20`), the same model as the XLSX reader (cells, merged ranges; bold where `formatting_info=True` works). Added to `pyproject.toml` and both lock files with `bash tools/gate.sh lock`, then `bash tools/env_setup.sh` (the only allowed way to change the shared environment). If xlrd fails on Python 3.14: stop and report.
4. TXT reader: one flow page of paragraphs.

**Stage 1b (natively): PDF, images, names, HEIC reader.**
5. PDF: a PDF with an owner password only opens with the empty user password; a refusal only when a user password is needed ("Plik PDF jest chroniony hasłem otwarcia; usługa nie zna hasła."). The annotation parse is guarded: legacy bytes decode as PDFDocEncoding, then cp1250; one annotation never sinks a page. The catch-all of `readers/__init__.py` keeps the exception class name in the sidecar warning.
6. Images: an animated JPEG or PNG (MPO, APNG) is read at its first frame, not refused; a JPEG over the pixel budget is decoded with `draft()` to fit it, not refused; the hard bomb limit stays a refusal.
7. File names: a bad name (empty, too long, control or bidi characters) is cleaned (fallback `plik`) with a warning, not refused; the name is never used as a path.
8. HEIC reader `readers/heic.py`: `heif-dec` as a child process (no shell, timeout 30 s, its own 0700 temporary folder for input and output); its PNG goes through the image reader with the same limits. Where `heif-dec` is absent (this laptop) a plain refusal "Ta instalacja nie ma dekodera HEIC."; its tests carry the marker `linux`.

**Stage 2 (image; the agent pushes its branch and waits for the run).**
9. Dockerfile: `plus` installs `libheif-examples libheif-plugin-libde265` with `--no-install-recommends`; `core` installs the narrowest Alpine package that gives `heif-dec` (`libheif-tools`), never `libheif-plugins-all`. A build step lists the installed packages and fails if any name contains `x265`; `heif-dec --version` runs in both targets.
10. `tools/ci/make_fixtures.py`: synthetic RTF (cp1250 text, a table, a checkbox form field), XLS, TXT, HEIC (made on the CI runner only, for example `heif-enc` with the x265 plugin installed on the runner, never in the image), an owner-password PDF, an APNG, a `.doc` holding RTF. `READY_FORMATS` gets rtf, xls, txt, heic, heif; the container check's negative control for an unknown extension moves from `.txt` to `.exe`.
11. `NOTICE` names libheif and libde265 with their licence (D24).

**Acceptance.** The 5 RTF and the XLS of the unseen sample convert natively with 0 strict-linter errors and the PDF `899c…` converts (`bash tools/gate.sh py -m eval.chain --corpus unseen --compare`); every remaining refusal has a plain reason; sets: no regression (`--corpus sets --compare`); hostile corpus: 7 of 7 still refused; the branch image run is green with every new format converted inside both images with `--network none` and the x265 check passing; one negative control per new reader; the fast gate after merging `main`. Report the table "file → before → after" for the 8 refusals.

## WP-P1 — Presentation, film, submission

Concept and rules: [`../../05-hackathon/presentation/concept-document-deck.md`](../../05-hackathon/presentation/concept-document-deck.md). At most ten slides as PDF; a film of at most three minutes; title and description for HackTribe; every number from `eval/metrics.json`; the docket of contradictions and the "what works, what is inferred" list on a slide.

---

## Clock: Saturday 14:30 to Sunday 10:30

At most three builders at once. A wave starts when its inputs exist, not when the clock says so; the lead pulls a package forward when a slot is free.

| When | Running (at most three) | Gate at the end |
|---|---|---|
| Sat 14:30–15:00 | lead alone: WP-F0 contracts; environment check with the owner; the one-job workflow of WP-F20 | contracts committed; the workflow ran |
| Sat 15:00–17:30 | **F1** ‖ **F2a** ‖ **F5** | **G-A**: the service answers natively with a token; reference set 1 as PDF and DOCX gives a page model; every standard section of both exports is rebuilt equal |
| Sat 17:30–20:00 | **F3** ‖ **F14** ‖ **F20** | **G-B**: candidates on the PDF and DOCX of all nine sets; both exports pass the gate and the journeys; CI builds `core` and converts the stub without network |
| Sat by 18:00 | the owner sends the HackTribe draft; the lead hands him the text by 17:45 | |
| Sat 20:00–23:00 | **F4** ‖ **F8** ‖ **F2b** | **G-C, the mandatory minimum**: both reference sets, as PDF and DOCX, come out of the API as valid forms with the right pages and standard sections; briefs exist for the seven judged sets; validators are written |
| Sat 23:00–Sun 02:00 | **F7** ‖ **F6** ‖ **F15** | **G-D**: conditions from the paper's wording; dictionaries and initial data; the ledger closes on nine sets |
| Sun 02:00–05:00 | **F2c** ‖ **F9 with F10** (one builder, one application) ‖ **F16** | **G-E**: a scan converts with warnings; both views usable; the hostile corpus passes in CI |
| Sun 05:00–07:30 | **F11** ‖ **F12** ‖ **F17** | **G-F, the submission is safe**: `results/` complete, `metrics.json`, README test passed, the image published by digest. **From here the image is frozen** |
| Sun 07:30–08:30 | only if G-F passed: **F18** ‖ **F19** ‖ **F13** | each is merged only if its acceptance passes; otherwise it is left out without a trace |
| Sun 08:30–10:00 | **P1**: deck PDF, film, texts; rehearsal on a fresh start of the published image | the owner submits by 10:30 |

The front end (F9, F10) needs only the contracts and the two exports, so it may start any time after 15:00 if a builder is free.

## Order of value if time is short

1. C-MIN through the API for PDF and DOCX: F1, F2a, F3, F4, F5, F14 (the gate).
2. The image proved by CI: F20. Without it C-TECH-DOCKER is words.
3. Validators (F8), dictionaries and initial data (F6), conditions (F7): three scored extensions.
4. The remaining formats: sheets and binary Word (F2b), then images (F2c). Finalists get new files in any format.
5. The outputs for the seven judged sets and the numbers (F11); the README and the architecture document (F12).
6. The front end (F9, F10): a scored extension and the film.
7. The accounting sidecar (F15) and the airlock with the hostile corpus (F16): what makes us different.
8. The alarm (F17), the redline (F18), the cost dial (F19), the agent pack (F13).

## What is cut first, plainly

- **First:** the form family; the agent pack; the cost dial; the redline. Each is one slide that can be told as "designed, not built".
- **Second:** the image `plus` and the second OCR engine; the batch table; handwriting detection in the alarm.
- **Third:** raster detection on scans beyond text and lines (a scan then gives fewer fields and more warnings, and says so).
- **Never:** the gate; the mandatory minimum on PDF and DOCX; the seven output files; the README; the CI image.

A feature that is not built is not on a slide as built. The slide "co działa, co jest wnioskowaniem" is filled from `eval/metrics.json` and from design section 12.
