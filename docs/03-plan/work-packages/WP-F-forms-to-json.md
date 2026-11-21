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

**F2a: PDF and DOCX.** PDF: text and character boxes, lines and rectangles, declared fields; a page with almost no text goes to the image way (F2c). DOCX: body paragraphs, tables, tabs and leaders, symbols, content controls, legacy form fields, footnotes, **and text boxes with their anchor offsets**: the DOCX files of sets 2 and 8 are nothing but text boxes (130 and 1,302 of them) and a reader of ordinary paragraphs returns an empty document.

**F2b: XLSX, ODS, binary Word.** Sheets: the grid is the layout (35 to 759 merged ranges per form); cells, merges, borders, sizes; repeat counts of ODS bounded before expanding; hidden sheets read and reported. Binary Word: the native reader of design 6.2.1, `origin: flow`.

**F2c: images.** Decode with limits, drop metadata, cut the tall scan into pages (the scans are 1654 pixels wide and up to 37,424 high), OCR per page with word boxes and confidence, raster detection of lines, boxes, leaders and combs without OpenCV. A PDF without text takes this way after rendering.

Acceptance: `eval/readers-sets.json` lists, for every file of the nine sets, the reader used, pages, runs, lines, rectangles, seconds, and no unhandled exception; the DOCX of sets 2 and 8 give more than 100 runs each **with boxes**; the scan of set 9 becomes sixteen pages and the one of set 8 six; every `.doc` of the nine sets gives the title of its form in the first twenty runs, or a 422 with a reason; a broken file gives 422 without a stack trace. **Negative controls:** a text file named `.docx` never reaches a reader; an ODS with a row repeated a million times is refused before it is expanded; a scan of 100,000 × 100,000 pixels is refused from its header.

Cheapest tests that would prove us wrong: (1) a PDF made only of a photographed page, converted offline: it must take the OCR way; (2) the same form through all its formats must give the same title in the first heading run (this is the first line of the eight-format table of WP-F11).

## WP-F3 — Finder

Design 6.3: reading order; roles of text; candidates by kind; labels by score; groups.

Acceptance: `eval/finder-sets.json` records candidates per kind for the PDF and DOCX of the nine sets; on reference set 1 the four blanks of the sentence are found with their labels; on set 2 the postal code, both dates and the account are **one comb each** with the right cell count; on set 7 `❑ pies ❑ suka` is one group of two and the three marking boxes one group of three, two of them with a blank; on set 9 the character `□` counts as a box; section A of set 7 is recognised as the applicant block although it is printed after section B. **Negative controls:** an information sheet without places to fill yields zero candidates and the warning `NOT_A_FORM`; an instruction with a drawn example of a ticked box is not a group; the data-protection clause yields no candidate.

Cheapest test that would prove us wrong: one page hand-marked with an empty box, a printed bullet, a crossed box and an eleven-cell PESEL must come back as one choice group (not four fields) and one PESEL field.

## WP-F4 — Understanding: the brief

Design 6.4. Rules in this order: title and addressee; who may apply (the three notions: person at the keyboard, party, capacity) from the wording table; the paper habits table; required or not; labels rewritten by the standard's rules; composite papers. Lexicons are data files in `apps/converter/app/lexicon/` with a source and a date per row. Build-time help: `tools/eden/eden.py` may mine the labels of the nine sets and of the city archive for phrase variants; a mined row enters a lexicon only after a rule test uses it.

Acceptance: for reference sets 1 and 5 the brief from every format has the same title, addressee, applicant options and fields of the matter (labels from images may differ by the recorded distance); for each judged set a brief is stored in `eval/briefs/` and its differences from the silver labels are listed and explained; every `REQUIRED` in a brief has evidence or the flag `REQUIRED_INFERRED`; set 6 produces the warning `ADDRESSEE_CONFLICT` with both quotes; set 9 produces one selector and no second form. **Negative controls:** "Załącznik nr 2 do Regulaminu …" never becomes a title; the clause on page two never becomes fields; "hodowanie/utrzymywanie*" becomes one choice while "charta/chartów*" becomes none; a fee that is not on the paper stays `not_found`.

Cheapest tests that would prove us wrong: (1) rename the file, replace the municipality and the title, run again: the fields of the matter must not change; (2) one form from the city archive that no author of the rules has seen: read its brief before reading its paper.

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

Acceptance: the film can be recorded on it without a cut; both exports' sets and two judged sets load; an automatic accessibility check of our own rules (labels, focus order, contrast tokens) has no critical finding; fifty files finish in the batch table and the table equals the stream. **Negative control:** with the sidecar missing, the view still shows the form and says what is absent.

Cheapest test that would prove us wrong: time someone who did not write it correcting one wrongly grouped choice. If that is impossible without the source code, the view is called inspection in every text, not review.

## WP-F10 — Front end, view "Podgląd e-usługi"

Renders the e-service from a form alone: pages as steps, sections, fields with hints, known dictionaries as short sample lists marked as samples, conditions live with the bundled reference evaluator, validation messages in Polish, locks on read-only initial data (fictitious values, marked). Buttons for the six journeys and for the zero-answer state; a list "what this journey shows and hides".

Acceptance: both exports render without an error and behave as hand-predicted on one route each; our outputs for the judged sets render; one condition and one validation are shown working in the film. **Negative control:** a form with a condition that does not parse shows the error at the field, not a blank page.

Cheapest test that would prove us wrong: load both **untouched** exports and predict one route by hand from the JSON before clicking. If viewer and emitter only agree with each other, they share a bug.

## WP-F11 — Evaluation run and numbers

`python -m eval.run`: converts the golden and the judged sets natively (and, where Docker exists, through the image), compares with the exports (design 10: fields all and matter-only, types, validators, dictionaries, conditions by behaviour, standard sections), builds the eight-format agreement table, checks ledger, coverage and gate per form, aggregates time and memory by input class, and writes `eval/metrics.json` and `results/<set>/form.json` with `meta.json` for the seven judged sets. `eval/silver/` holds the build-time labels of a hosted model for the nine sets and the comparison with our briefs.

Acceptance: `results/` holds a form and a sidecar per judged set and each passes the gate; `metrics.json` comes from one command on a clean checkout; every number in the presentation equals the file. **Negative controls:** an export scored against itself gives 1.0 everywhere; the same export with one field removed scores below 1.0 in recall and nowhere else.

Cheapest test that would prove us wrong: from the city archive take one random page per kind of file, hand-score it, and publish the unique counts, the failures and the peak memory, not only the throughput.

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
