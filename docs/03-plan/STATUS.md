# STATUS

Lead-owned. One screen. Update on every merge, on every start or stop of a sub-agent, and before any long wait.

Last update: 2026-11-21 17:22 CET. **Track F (the forms converter) is being built: read "Build log" first, then [`DECISIONS-forms-track.md`](DECISIONS-forms-track.md).**

## Build log (the lead's handoff; newest state on top)

**Milestones** (each is marked here with its commit when reached):

| | Milestone | State |
|---|---|---|
| (a) | REST service with a token takes PDF and DOCX and answers with a valid partner JSON; image built and published by Actions | **reached 15:13, commit `920dbf1`, tag `track-f-a`**: 430 tests; the PDF and DOCX of all nine sets answer 200 with 0 strict-linter errors; run on `main` green in three jobs; image `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:de661b017a6d950e9362f73ad3c49f555f59ad55a09823c5f067cab932be6acf` published, signed, pulled back without a login and converting with no network. **Caveat: the form holds the title and the standard pages only; the fields of the matter come with F3 and F4** |
| (b) | all eight formats, validators, dictionaries and initial data, conditions, the review page | not reached |
| (c) | JSON of the seven judged forms in `results/`, README, architecture document, metrics | not reached |
| (d) | PDF of ten slides and the script of the three-minute film | not reached |

**Merged into `main`:**

| When | Package | Merge commit | What it proves |
|---|---|---|---|
| 14:21 | WP-F0a form schema profiles, tolerant linter, golden list, contradiction docket (13 rows) | `1430f0a` | both exports pass the tolerant profile with zero errors and fail the strict one for the listed reasons; six negative controls |
| 14:28 | WP-F0b data contracts and shared models (`apps/converter/app/model/`, four generated schema files, examples) | `4bb8854` | 54 model tests; both exports load and dump back with nothing lost; fast gate 71 passed. No independent agent review: a second opinion of a hosted model was asked instead (`research/eden/e7-…`) |

| 14:32 | WP-F1 service shell: endpoints, guard, token check, command line, Dockerfile (never built yet), README | `efa807a` | independent review: merge; 266 tests; every file of the nine sets passes the guard |
| 14:51 | WP-F2a readers for PDF and DOCX (text boxes with boxes, form fields, tables, leaders) | `b60de98` | independent review: merge; 17 set files read, none refused, no unhandled exception |
| 14:51 | WP-F5 composer: library of standard sections, pages, ids from meaning, conditions, D16 to D18 | `0043f5a` | independent review: merge; fast gate on `main` 378 passed |

**HANDOFF (17:22): the third build lead stops (context at its limit: start plus about 100 thousand tokens). A FOURTH build lead starts fresh: read this block, then [`LEAD-HANDOFF.md`](LEAD-HANDOFF.md) (section "Learned by the third build lead"). The agents below report to the third lead's session, not to you: watch their branches with one background loop and read the status file on each branch.**

**Next, in order, for the fourth lead:**
1. When `wp/F20-f-user-formats` shows stage 1a done (status file on the branch): read its 15-line evidence, start stage 1b (items 5 to 8 of the plan section WP-F20f) with a direct `wp-builder` on sonnet in a worktree on the same branch, then stage 2 (items 9 to 11: image, fixtures, `READY_FORMATS`; that agent pushes the branch and waits for its run); merge only on a green branch run; then send the program lead the table "8 refusals: before, after".
2. Merge WP-F3b when its branch status has the acceptance stage and a review verdict (`tools/lead/merge.sh`), then refresh `results/` (`bash tools/gate.sh py tools/lead/snapshot_results.py .`) and run `bash tools/gate.sh py -m eval.chain --compare`.
3. When the wave of WP-F9 ends: merge; then write the first-build scope paragraph of WP-F10 like F9's (e-service preview, three languages, every device) and start its wave; the program lead was told F9 about 19:30, F10 about 22:00 (the film needs both).
4. After a green Actions run on `main` (`wait_run.py`): the image offline run on the real forms including the 27 set images (`tmp/image_run.sh <ref>` or `-m eval.chain --image <ref>`), then one line with the digest to the program lead (HackTribe text).
5. Then: WP-F2c-b OCR second pass (no plan section yet: write it from `research/19-ocr-offline-brief.md`, HEIC/RTF advice overruled by D24), WP-F14b (with a new ticket: `job_timeout_s` is never applied, so a stuck conversion never answers 504), WP-F8, WP-F2d, WP-F11b, WP-F7, WP-F6, WP-F15, WP-F16, WP-F11, WP-F12, README in Spanish (D25).

**Third build lead from 17:07** (started by the program lead; reports to the session "Программный лид 3" with SendMessage only on a merge, a blocker, a milestone or HANDOFF; first line `СБОРКА ЧЧ:ММ | слито | идёт | неделя A % / топ F % | нужно`). The second lead's session still merged F20e at 17:14 and was asked to merge nothing more. New orders: **D24** (the service does it for the user; LGPL only as a separate decoder program for HEIC) and **D25** (our interface in Polish, English, Spanish). Token rules of the program lead (17:10): the lead hands over at its start plus about 100 thousand tokens; at most two own agents at once, on sonnet; a file over 10 KB is read by an agent.

**Running (17:21):**

- **WP-F3b** matter quality: wave `wf_021fbbb6-7b7` of the second lead (its notices reach the old session, so check the branch), branch `wp/F3b-matter-quality` (at 17:13 `58758fa`, main merged in); done when the branch status file has the acceptance stage and a review verdict; the third lead merges it.
- **WP-F20f** do it for the user (plan section WP-F20f): stage 1a (routing by content, RTF, XLS with `xlrd`, TXT) by a direct `wp-builder` in a worktree, branch `wp/F20-f-user-formats`, status `docs/03-plan/wip/WP-F20f.status.md`; then stage 1b (PDF with an owner password, the annotation crash of one archive PDF, file names, HEIC reader) and stage 2 (image: `heif-dec`, fixtures, `READY_FORMATS`, push and branch run).
- **WP-F9** review page, first build (scope paragraph at the end of its plan section): wave `wf_a22fb414-2e0`, branch `wp/F9-review-web`. WP-F10 (e-service preview) follows; the film needs both (program lead told: F9 about 19:30, F10 about 22:00).

**Image:** `latest-main` is `98b2bcd` (16:53), `sha256:9bb506c96e9938c66c6be3e662ca486b93ae9203da179dc1f896541c92237f2e`: fields of the matter, no OCR adapter. Actions on `main` were red from `ef9a80c` (16:57; the image check still expected JPG and PNG to be refused) until the F20e merge; the run after `7dd018d` gives the next image, then the offline run on the real forms.

**Proven at the handoff:** the published image of commit `24034ef` converts **44 of 44** non-image files of the nine sets on the laptop with `--network none --read-only --cap-drop ALL` (script `tmp/image_run.sh <image ref>`, not in git); the same file gives a byte-identical JSON on two runs (PDF and DOCX); the check chain: 158 files, 0 failed, 0 gate failures, 0 strict-linter errors (sets 71: 44 converted, 27 images refused natively for lack of Tesseract; unseen 80: 72 converted, 8 refused with a reason: 5 rtf, 1 xls, 1 jpg, 1 pdf; hostile 7: all refused). The city archive (378 MB) is in `data/archive/` of the main checkout (git-ignored).

**Docker is up** (Docker Desktop 4.99.0; from a shell started before the install call `"/c/Program Files/Docker/Docker/resources/bin/docker.exe"`; WSL capped at 4 GB: one container at a time, not beside three test-heavy agents). `tools/ci/image_digest.py` needs the FULL commit hash; `--tag latest-main` gives the newest. **To do:** run `tmp/image_run.sh` (or `eval.chain --image`) on the image of the newest green `main` once Actions publish it (images of `559d839` and later were not yet published at 17:00), including the 27 images of the sets.

**Seven results (`results/`, commit `98b2bcd`, tag `track-f-a2`):** fields of the matter present; 0 strict-linter errors. Set 8's `form.json` is local only (quotes the office's account number; the publishing check refuses it); regenerate with `bash tools/gate.sh py tools/lead/snapshot_results.py .`, upload with the submission. `eval/briefs/*.json` are local only (they quote the partner's forms). Weak titles: set 6 "Wniosek", set 9 ends with "ii" (F3b or after). The program lead starts audit round 2 on these results.

**Next, in order:** merge F3b and F20e; then **WP-F2c-b, OCR second pass** from [`research/19-ocr-offline-brief.md`](../../research/19-ocr-offline-brief.md) (program lead, 17:10; unverified model research): tighter limits (pixels 40 M, pages 50, OCR timeout 30 s, PNG text chunks and frame count capped), erase table lines and cell walls on the copy sent to OCR, Pillow-only quality gates calibrated on the 27 set images before refusing anything, an A/B hour on the sets (`pol` vs `pol+eng`, grey vs binarised, 200 vs 300 dpi); AVIF and JPEG 2000 only if the built image decodes them; HEIC and RTF are converted now (D24, WP-F20f); refresh `results/` and run `bash tools/gate.sh py -m eval.chain --compare` after each merge (`--update-baseline` when better); WP-F8 (validators), WP-F2d (native readers: reference 5 `.doc` ReaderError, sheets give one run for reference 1, audit T5 and T10, D21), WP-F11b (content scorer, audit T2), WP-F14b (failure contract D19: G5 to G12 become warnings, header `X-Converter-Warnings`), WP-F7, WP-F6, WP-F15, WP-F16, WP-F9 with WP-F10 (every-device acceptance; review view first, D22), WP-F11, WP-F12. Audit tickets and their mapping: [`audit-tickets-2026-11-21.md`](audit-tickets-2026-11-21.md); decisions D19 to D23: section 6c of the decisions file.

**Budget, measured 17:04:** week 77 %, top model 84 %. At 16:06: 70 % and 80 %. The owner allows the subscription to 99 % and the whole Eden grant (cap 115 USD, 17.9 spent). The only stage allowed on the top model was the core of WP-F4 (done); keep thinking cores on `opus`, builders on `sonnet`.

**Merged since the table above** (all through `tools/lead/merge.sh`, fast gate green after each):

| When | Package | Merge commit | What it proves |
|---|---|---|---|
| 15:01 | WP-F20 image pipeline | `d576408` | both targets build on Python 3.14 with pinned bases and hashed wheels; not root, no capability, read-only, no network; SBOM gate |
| 15:06 | WP-F0c revision 1.1 of the models | `8611a0d` | additive: old output byte-identical; spans, dispositions, reader facts, safe builders |
| 15:10 | WP-F0p pipeline wiring and WP-F20b image checks for the real pipeline | `920dbf1` | **milestone (a)**; ready formats in one line of the workflow; Grype gate; image inspection; publishing and signing verified on `main` |
| 15:20 | WP-F14 pre-import gate | `af6794f` | twelve checks each with a fixture that fails only that check; both exports pass G1 to G10; seven journeys; zero-answer canary |
| 15:29 | WP-F0q gate behind the service and inside the image | `7be05a7` | a refused form is 500 `GATE_FAILED` without a form; the gate adds about 0.26 s per form; checked inside both images |
| 15:39 | WP-F3 finder | `7568884` | candidates for the PDF and DOCX of the nine sets with no unhandled error and no unassigned run; combs with masks, choice groups, blanks in a sentence; drills 3, 4, 7, 8, 10 |
| 15:47 | WP-F2b readers for XLSX, ODS and binary Word, with WP-F20d | `81e4781` | 42 of the 69 set files read (the other 27 are images); five formats convert inside both images; fast gate 540 passed |
| 16:25 | README files true to Track F (docs) | `24034ef` | pl, en, ru describe the converter, the published image, ready formats and what is not done |
| 16:50 | WP-F4 understanding and wiring | `559d839` | finder and understanding replace interim; fields of the matter (PDF): set 2: 5, 3: 2, 4: 7, 6: 18, 7: 10, 8: 32, 9: 83; gate 17/17; 584 tests. Review blockers (reference parity across formats, set 9 PDF selector) moved to WP-F3b; briefs stay local |
| 16:57 | WP-F2c images and OCR | `ef9a80c` | image reader with limits, tall scans cut into pages, raster lines and boxes, OCR adapter (Tesseract only in the image), pixel budget for huge PDF pages (audit T7); 616 tests |
| 17:01 | WP-F11a check chain | `3e7df8a` | `bash tools/gate.sh py -m eval.chain [--compare] [--update-baseline] [--image REF]`; 158 files, 0 failed; baseline committed; fast gate collects `eval/chain/tests`; owner's page `docs/03-plan/check-chain.ru.md` |
| 17:14 | WP-F20e image formats with F2e | `0f141c5` | jpeg, png and TIFF, BMP, GIF, WEBP, ODT converted inside the image by its workflow (branch run green, Tesseract only there); HEIC refused in Polish (libheif is LGPL); RTF refused. Open: `Format` of the models names seven kinds (new ones recorded as png or docx in `source.format`, `source.reader` tells them apart); OCR text of the CI images not inspected |

**Open follow-ups for packages that are merged** (small stages for a builder when a slot is free):

- **Finder, second pass (F3b):** on sets 8 and 9 between 20 and 31 places per file have no label; the PDF of set 9 yields no section; the notes of the hosted models in `eval/silver/` were not consulted; radio groups and declared tab leaders are untested on real files. Requests of the finder to the models (additive, a revision 1.2): a role per span, a label position "below", a mark for cell candidates that are rows of one repeating table. Requests to the readers: a flow table needs a place among the paragraphs (the 26-cell comb of reference 5 as DOCX gets no label); bold is not reported for the headings of the PDF of set 9.
- **Composer (F5):** attachment id from `Attachment.key`; `page_title` and `hint` of a matter section; a yes-or-no CHECKBOX without options; the `applicant` selector in conditions.
- **Readers (F2a):** the `safe` builders of revision 1.1; `leader`, `region`, `footnote`, widget values.
- **Shell (F1):** every forbidden character of a file name as a parameter of one test; two starts with two size limits; rotated key, issuer and audience; a plain Polish action in every problem answer (`verification-plan.md`, sections 1 and 6).
- **Wiring (lead files):** the finder and the understanding step replace `app/interim.py` (the finder is merged but not called yet); `assemble_ledger` gets the inverse of `ComposeResult.brief_keys`; `UploadInfo` reaches the pipeline; the sidecar `checks` take the shape of `Meta.checks`.
- **Standard fields carry no `REQUIRED`** (the strict linter warns on 45 fields per form; the exports carry none either): decide with WP-F8 whether the standard pages get validators (D8) or stay as in the exports.

**Lead decisions:** the hostile corpus runs from the CI runner against the container; the vulnerability gate is Grype on the SBOM and fails only on a critical finding that has a fix; `tools/licence_check.py` stays with WP-F12 and may reuse `tools/ci/sbom_gate.py`; the account of set 2 is one field, not a comb (the paper draws one box).


**For the owner's next report:** D16 changes two standard conditions against the exports (docket row 18); the seven results will be delivered with the path of the statutory representative, and a second variant with `STATUTORY_REPRESENTATIVE=off` beside them.

**Standing instructions of the owner (21 November, 14:22):**

1. Involve him only in extreme cases; when something truly cannot be done by an agent, say exactly what he has to download or click.
2. He does not test anything himself. The lead finds the right tests, covers everything the card asks and what the partner did not think of, and at every milestone walks him through plain-language proof (a page "requirement of the card, proof, how to see it").
3. Re-think and improve the planned structure at every stage.
4. **Docker:** do not interrupt running agents. When a quiet window comes (nothing running, work committed), tell him; the lead starts the installation itself (`winget`, WSL), he confirms the administrator prompt and reboots.
5. **The partner's credits are limited (100 EUR; the owner lifted the 60 USD cap at 16:45: the tool stops at 115 USD, the whole grant):** use them, and only with the strongest models (`anthropic/claude-fable-5-2`, `openai/gpt-6.2-astra`, `google/gemini-4-neon`), for research, second opinions and the jury-style critique of the seven outputs. Never at run time of the product.

**Done by the lead since 13:55:**

- Machine check: no Docker, no WSL, no Tesseract, no LibreOffice, no GitHub CLI; Python 3.13 and 3.11, Node 22; all nine task sets present; the credits key is set (2.6 of 60 USD spent). The owner was asked once whether he installs Docker; the default without an answer is "no": the image is built and published by Actions.
- **Actions and the registry are proven** (commit `d64c001`, workflow `probe`, branch `ci/probe`): the stored credential may push workflow files; the run was green; the image `ghcr.io/andriishramko/shramko-asystent-urzednika:probe` can be pulled without a login (anonymous manifest request answered 200). No click of the owner is needed.
- The two research files entered git with example identifiers rewritten (commit `5cf44c2`).
- Skeleton (commit `66e040c`): `apps/converter/pyproject.toml`, two lock files with hashes, the shared environment `.venv` in the main checkout (made by `bash tools/env_setup.sh`; PyPI is slow on the event's network, the script retries), `tools/gate.sh` (`py`, `fast`, `full`, `lock`), test markers, packages `app` and `converter`.
- Facts that change the plan: (1) **nothing of the partner's sets is in git**, so the image workflow can convert only synthetic fixtures; every module needs tests on fixtures built from code, and tests on the sets carry the marker `sets`. (2) The publishing check refuses literal identifiers with valid check digits: tests build them from a stem and a computed check digit (`AGENTS.md`, section Commands).

**Budget history:** 13:55: week 55 %, top model 70 %. 14:31: 59 % and 73 % (the first 37 minutes of the build cost 4 and 3 points, with three agents running and the lead very active). Rule of this session: builders on sonnet, reviews and most think cores on opus, the session's model only for the lead and the cores of the finder, the understanding step and the composer.

**Waiting for the owner:** (1) Docker on the laptop: yes or no (not blocking). (2) **Register the task with the partner by 19:00.** (3) **Send the HackTribe draft by 20:00** (`docs/05-hackathon/hacktribe-draft-formularze.md`; the lead re-reads it against the build by 17:45). (4) Nothing else: the answers of the business side arrived at 14:10 and are in section 6b of the decisions.

## Prepared before the build (21 November, 13:45)

**The task is fixed: "Cyfryzacja formularzy" (COI), Track F.** One sentence: a compiler with an accountant, not a scanner with AI. No application code exists yet; the build starts with the next session of the lead.

Prepared this afternoon by the preparing session on the owner's laptop:

| What | Where | State |
|---|---|---|
| Decisions of the track (contract with the importer, stack, accounting features, defaults for open questions) | [`DECISIONS-forms-track.md`](DECISIONS-forms-track.md) | done; wins over older documents |
| Detailed design of the converter | [`../02-architecture/converter-design.md`](../02-architecture/converter-design.md) | written by a background writer; the lead checks that it exists and follows the decisions |
| Work packages, version 2, with the clock from Saturday 14:30 to Sunday 10:30 | [`work-packages/WP-F-forms-to-json.md`](work-packages/WP-F-forms-to-json.md) | same |
| Rules, agent types, wave script, project skills, model routing, machine notes | `AGENTS.md`, `START_HERE.md`, `.claude/`, [`../04-orchestration/`](../04-orchestration/) | same |
| Submission text for 20:00, ten slides, film, defence questions | [`../05-hackathon/hacktribe-draft-formularze.md`](../05-hackathon/hacktribe-draft-formularze.md), [`../05-hackathon/presentation/storyboard-coi-v2.md`](../05-hackathon/presentation/storyboard-coi-v2.md), [`../05-hackathon/jury-qa-formularze.md`](../05-hackathon/jury-qa-formularze.md) | same |
| Research with sources: stack and licences under Python 3.14; the partner's platform and the origin of the format; security; applicant kinds; evolution and interoperability | `research/14` … `research/18` | done |
| Raw reports of hosted models (deep research, thirty ideas, defence questions) | `research/eden/` | done; unverified by design |
| The task sets: two references and seven judged forms | `data/coi/` **local only**, hashes in `data/coi/INDEX.json`; unpack with `tools/coi_unpack.py`; paths through `tools/coi_paths.py` | on the owner's laptop |
| Facts measured on both reference exports; the standard sections compared | [`../05-hackathon/mentor-questions/reference-json-forensics.txt`](../05-hackathon/mentor-questions/reference-json-forensics.txt), [`../../contracts/coi/standard-sections-diff.md`](../../contracts/coi/standard-sections-diff.md) | done |
| Second opinions of two hosted models on every form (what a careful reader finds on the paper) | `eval/silver/` **local only**; `python tools/eden/silver_briefs.py --compare` | done for the sets present |
| Client for the partner's model credits, with a ledger and a cap of 60 USD | `tools/eden/eden.py`; key only in the variable `EDENAI_API_KEY` | about 2 USD of 100 EUR spent |
| Questionnaire for the mentors (a hidden presentation: facts we found, our decisions to confirm) | private artifact of the owner; questions in [`../05-hackathon/mentor-questions/`](../05-hackathon/mentor-questions/) | owner meets the technical mentor at 13:30 and the business side at about 14:00 |

**Mentor answers, 13:40 (technical):** no hard requirements, "propose interesting solutions"; the jury reads conformity with the design standard and runs the image **on its own computer in Docker**, so the image must be published; LibreOffice and any open source are allowed; metadata may sit in the same JSON; the partner's materials may not be public (they left the repository; history is the owner's decision). Full table: section 6a of the decisions. The business meeting is at about 14:00; its answers will be in the store under `biz`. **The owner must register the task by 19:00.**

**Local only, not in git:** `research/17-applicant-kinds-person-business-representation.md` and `research/eden/e3-identifiers-and-law.sonar-deep-research.md` are on the owner's laptop in the main checkout; the publishing check stops on their example identifiers (PESEL, accounts, document numbers). First small job of the lead: replace the examples by clearly synthetic ones, run the check, commit.

**Where documents disagree:** the wave script and the playbook use native worktrees; where `docs/04-orchestration/git-workflow.md` says otherwise, the playbook wins. The GitHub Actions workflow that builds and publishes the image belongs to WP-F1 and WP-F20 (`.github/`).

**What the lead does first** (details in `START_HERE.md`):

1. Environment check. Measured at 13:20: **the laptop has no Docker and no WSL**, Python 3.13 and 3.11 only, 59 GB free. The owner installs WSL and Docker Desktop (administrator rights, a reboot) or the image is proved by GitHub Actions; code is developed natively either way.
2. Read the mentors' answers from the questionnaire store (ArtifactData, collection `ankieta`, documents `tech` and `biz`) and enter them into section 6 of the decisions; an answer may flip a switch (last page style, validators, LibreOffice).
3. Commit whatever the background writers left uncommitted (publishing check first), then start the first wave: WP-F1 (service shell), WP-F2 for PDF and DOCX, WP-F5 library of standard sections from `contracts/coi/standard-sections-diff.md`.
4. Fix `contracts/coi/form.schema.json` and `tools/coi_lint.py` for what reference set 5 showed (link ids that are not UUIDs, an option without `techName`): our output stays strict, the reader of references becomes tolerant.

**Budget, measured at 13:40:** 51 % of the week for all models and **65 % for the strongest model** are used (reset 26 November 13:00). The preparing session cost 5 and 9 points in one hour, mostly through forks of a large context: **do not fork a session above about 300 thousand tokens; brief fresh agents through files.** Builders run on the middle tier; the strongest model only for the lead and the three think packages (finder, understanding, composer); bulk work and second opinions go to the partner's credits.

Known inconsistencies of the partner's own exports (use them at the defence, never copy them): the address dictionary is `TERYT_DOWODOWY` in one place and `TERYT_4G_DOWODOWY` in the other, swapped between the two exports, and the field label equals the dictionary name; the same upload fields carry different `techName` in the two exports; REGON and KRS exist in one export only; three `validation` values are objects instead of lists; link ids of set 5 are five-character strings.

## Phase

**Event running since 11:00. No application code yet. The full task cards were read at 11:10–11:25** (digests: [`../05-hackathon/intake/README.md`](../05-hackathon/intake/README.md)).

1. **The forms task is not the product we prepared.** It asks for a converter: one blank form file in (PDF, DOC, DOCX, ODS, XLSX, JPG, PNG), one JSON in the partner's structure out, as a REST service in Docker with a token check, for the official who digitises forms. Language models reachable only through an API, and any external API, MCP or SaaS, are **forbidden inside the product** (allowed for writing the code). Finalists run on new files at the defence. Ten slides, a three-minute film, the JSON files. Analysis and what survives of our work: [`../01-product/coi-replan.md`](../01-product/coi-replan.md). New track with fourteen packages and its own clock: [`work-packages/WP-F-forms-to-json.md`](work-packages/WP-F-forms-to-json.md). **Track B (counter, QR handoff, print, WP-B1…B11) is not built for this task**; its documents stay as the vision and as tools.
2. **The city's task is close to Track A as specified** (calendar of requests, similar cases, departments, draft, anonymisation; a cloud model is allowed for the prototype). Gap table: [`../05-hackathon/intake/umb-task-card.md`](../05-hackathon/intake/umb-task-card.md), last section.
3. **One project only** for a single participant (a second needs a second team leader). The owner's standing decision is the forms task. The choice is open again: "Waiting for the owner", item 1.
4. **The partner's working materials were read at 11:30** and are in `data/coi/` (the materials and reference set 1; reference set 5 and the seven judged sets wait for the owner to download them). The format is described in [`../02-architecture/coi-json-format.md`](../02-architecture/coi-json-format.md), with a schema and a rule checker that the partner's sample passes. Finding: about four fifths of a finished form are standard sections that are not on the paper; a rules-only converter is realistic. WP-F0 is mostly done.
5. **The owner does not like the look of the existing presentations** (11:11). New concept: [`../05-hackathon/presentation/concept-document-deck.md`](../05-hackathon/presentation/concept-document-deck.md). The reading version (`tools/build_pakiet.py`) and the two live decks keep their facts; they are not the submission.

**What the lead does first:** ask the owner the one question of item 1 with the recommendation; meanwhile run WP-00 (scaffold) because both tracks need it, and WP-F0 as soon as the materials are in `data/private/coi/`.

The paragraphs below describe the briefs of the morning. They remain the owner's vision; for the forms task only the parts named in coi-replan §2 are built.

**Third brief of the owner (21 November, about 09:55): "one visit, complete set".** The second half of the demo is told as "from need to signature": the need yields the whole set of forms, the data are handed over once, the clerk types nothing and sees only what needs a look. **Read [`../01-product/one-visit-package.md`](../01-product/one-visit-package.md) before planning the build** (ten minutes). Requirements R33–R43, packages WP-B7…B9, facts in `research/12`. No gate moves.

**Fourth brief (21 November, 10:29–10:33): the resident's own AI agent.** A second, official entrance for assistants (MCP and API): find the matter, get the set, hold a visit, fill digitised forms with the owner's data inside a permission approved on the phone; "the assistant fills, the person confirms". Design: [`../01-product/agent-door.md`](../01-product/agent-door.md); requirements R44–R50; package WP-B10, **optional, after the M2 gate**, third part of the demo only if it passes its acceptance list.

**Fifth brief (21 November, 10:48–10:56): the whole catalogue in advance; a short opening; the model.** Every template the office publishes gets its first pass before any clerk opens the product; a person approves each description once; the clerk only adds a new document. The whole archive was measured: 661 unique documents, 461 of them open to a first pass from geometry and text, 24 scans ([`../../research/13-forms-census-and-opening-facts.md`](../../research/13-forms-census-and-opening-facts.md)). Package: [`work-packages/WP-B11-catalogue-in-advance.md`](work-packages/WP-B11-catalogue-in-advance.md). The reading version of the presentation now opens with the idea in half a minute. The owner builds with Claude Code and wants strong models, not weak local ones: see "Waiting for the owner", item 2.

## What exists

| Item | State | Where |
|---|---|---|
| Owner requirements R1–R32 | done | `docs/00-brief/requirements.md` |
| Research R1–R11 (hackathon, law, forms catalogue and anatomy, identity, data protection and AI law, technology, landscape, orchestration, 2022 lessons, pitch, the forms task and its partner) | done; each file lists what could not be verified | `research/` |
| Forms catalogue of Urząd Miasta Bydgoszczy: 275 service cards, 710 file links | done; the `fees` field is mostly empty and `online_handling` is a weak heuristic: read the card itself for those | `data/forms-catalog.json`, `.csv`, `tools/crawl_bydgoszcz_forms.py` |
| Form files themselves: 676 files, 183 MB archive plus manifest | done; attached to the release `pre-event` and verified by size | release assets; `data/demo-forms.md` lists the forms chosen for the demo |
| Request taxonomy, 12 response document types with Polish skeletons (Track A) | done; wording is a draft for the office's lawyer | `data/udip-taxonomy.json`, `data/udip-response-templates.md` |
| Canonical profile schema; descriptor for the residence-registration form: **all three pages measured** (31 fields), overlay check passes with zero changed pixels outside the field boxes | done; check: `python tools/descriptor_overlay_check.py data/form-descriptor.example.json <template.pdf>` | `data/canonical-profile.schema.json`, `data/form-descriptor.example.json` |
| Scope decision, the unifying idea, gaps, after-the-event plan | done (re-check at the 11:00 gate) | `docs/01-product/` |
| Architecture decisions, API contract v0, security and privacy, AI layer | done | `docs/02-architecture/` |
| Roadmap with the event clock for both tracks, 18 work packages, ownership table | done | `docs/03-plan/` |
| Orchestration playbook, brief template, git workflow, resume, publishing | done; corrected against official documentation (research/08) | `docs/04-orchestration/` |
| Agent definitions, project settings, wave workflow | done; `wp-wave.js` is untested (no code existed to run it on): try it on WP-00 alone first | `.claude/` |
| Runtime instructions for the product's AI steps (Polish), including form onboarding | starting versions | `prompts/` |
| Deck and site for the forms task (8 slides, two live demo slides) | done; opened on the live site in a browser (slides change, no errors except the expected missing demo videos); texts corrected after research R11; numbers and status lists are placeholders until the build measures them | `site-formularze/`, `docs/05-hackathon/presentation/storyboard-formularze.md`, `docs/05-hackathon/demo-script-formularze.md` |
| Deck and site for the city's task (11 slides) | done and checked on the live site | `site/`, `docs/05-hackathon/presentation/storyboard.md`, `docs/05-hackathon/demo-script.md` |
| Jury truth tables for both products, guide to the event for the owner | done | `docs/05-hackathon/` |
| Public sites | live: <https://formularze.flyreelstudio.eu> and <https://urzad.flyreelstudio.eu> (pull-based from `site-formularze/` and `site/`) | `docs/04-orchestration/deploy.md` |
| Audit of the earlier research (Russian) | done | `docs/06-audit/` |
| Third brief built in: the idea as one flow, pains table, rules of the check by exception, what is not claimed | done | `docs/01-product/one-visit-package.md`; for the owner in Russian: `docs/01-product/kak-eto-rabotaet.ru.md` |
| Research R12: the partner's announcement (open source, on-premise, LLM credits, PDF-DOCX-XLSX), the city's booking calendar, the seven-day rule, browser pre-fill, contact picker | done; four items are search excerpts only and are labelled | `research/12-one-visit-package-addendum.md` |
| Work packages WP-B7 (need to set), WP-B8 (comparison and check by exception), WP-B9 (profile start); two change requests to WP-B1 and WP-B2 | specified, not started | `docs/03-plan/work-packages/WP-B7-B9-one-visit.md` |
| The agent door: design with seven safety rules, interface of nine tools, two kinds of forms (`online`, `counter`); package WP-B10 in two parts (a: public tools and visit hold; b: permission and draft filling) | specified, not started, optional | `docs/01-product/agent-door.md`, `docs/03-plan/work-packages/WP-B10-agent-door.md` |
| Reading version of the presentation for the first judging stage (eleven pages, Polish; **page 1 is the idea in half a minute, page 2 the hook "one description, three kinds of user"**; page 7 is the agent door, marked „propozycja" until built; a two-page short version `skrot.html` with its own PDF) and its web page; the same in Russian for the owner | drafts; numbers and the "what works" page are placeholders until the build measures them; **not yet under `site-formularze/`**, see "Waiting for the owner" | `docs/05-hackathon/presentation/storyboard-pakiet.md`, `docs/05-hackathon/presentation/pakiet/` (pages), `docs/assets/deck-pakiet/` (PDF, contact sheet), generator `tools/build_pakiet.py` |
| Census of the city's whole forms archive: 661 unique documents; 461 open to a first pass from geometry and text (29 fillable PDFs, 186 vector PDFs, 246 word-processor files), 24 scans, 173 without places to fill | measured on 21 November, event time; simple rule, not approved fields | `tools/forms_census.py`, `data/forms-census.json`, `data/forms-census.csv`, `research/13-forms-census-and-opening-facts.md` |
| Package WP-B11: the whole catalogue in advance (batch first pass, life of a description `draft_geometry` → `draft_ai` → `reviewed` → `published`, review queue, catalogue view with a funnel) | specified, not started | `docs/03-plan/work-packages/WP-B11-catalogue-in-advance.md` |
| The partner's format for the forms task: description, our stricter schema, a rule checker with five negative controls; the partner's materials and reference set 1 | done on 21 November, event time; reference set 5 and the judged sets still to add | `docs/02-architecture/coi-json-format.md`, `contracts/coi/form.schema.json`, `tools/coi_lint.py`, `data/coi/` |

## Not done before the event (first tasks if time allows)

1. Submission texts for HackTribe in Polish: **drafted for the forms task** in `docs/05-hackathon/hacktribe-draft-formularze.md` (with the plan of the two-minute video); re-read them against the real task card after 11:00. For the city's task the templates are still in `research/10-pitch-and-presentation.md` §3.
2. After WP-00: add the gate hook described in `docs/04-orchestration/lead-agent-playbook.md`.
3. ~~Pages 2–3 of the residence-registration form descriptor~~ done on 21 November (see "What exists"). Still open: the descriptor of the temporary-residence form (same family, 115 cells) and the bundle's second form.
4. Work-package files of Track B are grouped in three files (`work-packages/WP-B1-B6-counter.md`, `work-packages/WP-B7-B9-one-visit.md`, `work-packages/WP-B10-agent-door.md`); each has its goal, method and acceptance list. Split a package into its own status file when it starts.
5. Apply the two change requests at the top of `WP-B7-B9-one-visit.md` when WP-B1 and WP-B2 are briefed (bundle fields; `autocomplete` tokens and the optional `intent` in the payload).
6. Build the two demo bundles from the text of the service cards (UMB55 and one of the vehicle department); `research/12` item 7 is a pointer, not a source.
7. **At the 11:00 gate, before the first product commit:** set the tag on the last preparation commit: `git tag -a pre-event-2 $(git rev-list -1 --before="2026-11-21 11:00 +0100" main) -m "end of pre-event material" && git push origin pre-event-2` (the preparing session was not allowed to push tags).
8. Rewrite the live deck's slide 4 and its demo around "od potrzeby do podpisu" (wording in `storyboard-pakiet.md`, section "Changes to the live deck"), and keep the reading version's page 10 equal to `status.json`.

## Budget

**Update 09:56:** the owner said the usage limits are no longer a problem ("тогда были проблемы с лимитами, сейчас их нету"). Check the real allowance once at the start; if it confirms, build at the planned width from 11:00 without waiting for 13:30, and use the top tier for every "think" package. The paragraph below describes the state at 09:05 and applies only if the check contradicts him.

The build runs on the owner's subscription. On 2026-11-21 at 09:05 the weekly allowance was 84 % used (reset on 26 November) and the current five-hour window was 84 % used (reset at 13:30 local time): between 11:00 and 13:30 there is room only for the intake and the scaffold; the main build starts after 13:30. **The owner allowed spending the weekly allowance to zero ("Расходуй всё до нуля", 21 November)**, so no reserve has to be kept, but the allowance itself is still the tightest constraint of the whole event. Check the remaining allowance at every milestone and narrow the scope before it runs out: for Track B the order of value is WP-B1, WP-B2, WP-B3, then WP-B6, then the rest. Prefer middle-tier builders. Width: three sub-agents at once.

## Running now

Nothing.

Notes for the presenter's laptop: if the drawings on the slides do not move, press `M` (Windows may have animation effects switched off); do not keep both decks open in one browser at the same time (they share one sync channel and can drive each other).

Points from research R11 to check at the partner's stand before building: the ministry plans a form generator for local governments on its e-services platform, and a central repository of electronic document templates already exists; present this product as the fast way from a paper form to an open description that can feed those, not as a new registry.

## Waiting for the owner

1. **Which task (one project).** Standing decision of the owner: the forms task, Track F. **Recommendation of the preparing session after reading the partner's materials: stay with it** (reasons in coi-replan §1a: most of the result comes from standard sections and rules; no model has to run; no paid key; our archive of real forms as a test set). An earlier note of 11:25 recommended the city's task; the materials changed that. The city's task remains the fallback: its card matches Track A and allows a cloud model, but a cloud model needs a paid key the owner does not have. The task is fixed in HackTribe by 20:00; do it by 18:00.
1a. **The remaining archives of the forms task:** the owner downloads archives 2 to 9 from the task's Discord channel "materiały-dodatkowe" into his Downloads folder (his browser asks where to save, so a session cannot finish the download alone); then they go to `data/coi/`. **Tokens are for the first 20 teams: ask at the partner's stand** (they are for building; nothing in the product may call a hosted model).
1b. Answered at 11:23: the owner's laptop cannot run any model. The product therefore runs on rules only (WP-F, rules of the track).
1c. **The template of the copyright-transfer agreement** (annex 1 of each task's regulations): the owner reads it before submitting. The winner transfers the economic copyrights of what was made for the task.
1d. **The look of the new presentation:** a sample of slides 1 and 10 of the document deck was sent to the owner at 11:40 (`docs/assets/deck-document/proba-wygladu.pdf`); he says yes or corrects, then WP-P1 builds the rest.
2. **Which model the product calls: decided by the owner on 21 November at 10:56; one point still open.** Decision (R54): the build runs on Claude Code; reading blank forms, which are public material, uses the strongest model available; a weak local model is not the default for that step; the partner's models or credits are welcome if the models are good, and nothing depends on them. State of the credits: the owner asked at the COI stand and was told they come "later" (10:49). Consequences for the lead: (a) the first pass over the catalogue (WP-B11) is done during the build by the agents themselves and committed as descriptor files, so the counter flow needs no model call at run time; (b) the live step "add a new form" needs one call at run time: partner credits if they arrive, otherwise ask the owner once for a few dollars of API credit, otherwise a recorded answer that the screen marks as recorded; (c) personal data never go to a cloud model: a spoken need is matched to a set by rules and the catalogue first, a model sees only text without personal data; (d) keep the `local` provider as a switch and measure it once on the residence form, because the partner announced that it rewards on-premise operation. **Still open: what "on-prem" means for the jury; the owner asks at the stand** (`docs/05-hackathon/ONSITE-INTAKE.md` §3a, question 5).
3. Whether a second person joins: only then can a second project be entered (it needs its own team leader).
4. **Whether the reading version goes live** at `formularze.flyreelstudio.eu/pakiet/` (move `docs/05-hackathon/presentation/pakiet/index.html` to `site-formularze/pakiet/` and push; the server publishes in two minutes). Default without an answer: keep it out of the public site until the build has replaced the placeholders, then publish before the final submission.
5. Answers from the stands to the questions of `docs/05-hackathon/ONSITE-INTAKE.md` §3a (COI) and §3b (clerks): they decide which pains the pitch may name as facts.

## Decisions taken

| Date | Decision | Where recorded |
|---|---|---|
| 2026-11-20 | One repository; pre-event material is tagged `pre-event`; product code comes after the tag | README, NOTICE |
| 2026-11-20 | At most three sub-agents at once | playbook |
| 2026-11-21 | Unifying idea "from request to answer": the city's request template is digitised with the same engine (WP-AB1) | scope-decision §1a |
| 2026-11-21 | Public sites on the owner's server are static only and update from the repository on push; test versions are static demo builds | deploy.md |
| 2026-11-21 | Stack: Python and FastAPI backend, React and TypeScript front ends, SQLite by default; no copyleft libraries in the core (the Polish spaCy model and PyMuPDF are excluded) | design-notes §2, research/06, research/07 |
| 2026-11-21 | **Primary track B (forms task); demo-first pitch; second site and deck** | scope-decision §0, roadmap |
| 2026-11-21 | Agents of residents get an official door; public tools carry no personal data; personal data pass only inside a one-matter permission approved on the person's phone; the agent never submits, signs or proves identity | agent-door §3, WP-B10 |
| 2026-11-21 | Everything committed before 11:00 on 21 November is pre-event material (the first tag `pre-event` is older than several preparation commits); the tag `pre-event-2` is to mark its end | NOTICE, CHANGELOG |
| 2026-11-21 | Jury texts use the partner's product name „Generator Formularzy e-Usług"; online pre-filling is never presented as new | research/12 item 11, one-visit-package §5 and §8 |
| 2026-11-21 | Second half of the demo is "one visit, complete set"; check by exception with a mandatory identity confirmation; intent before the visit without touching the city's booking system; open source and on-premise operation stated as product properties | one-visit-package, WP-B7…B9, research/12 |
| 2026-11-21 | Every template the office publishes gets its first pass in advance; a description moves `draft_geometry` → `draft_ai` → `reviewed` → `published` and only a published one prints or serves; a catalogue maintainer approves, not the counter clerk | WP-B11 |
| 2026-11-21 | Model policy (owner, 10:56): strongest model for public material such as blank forms; no cloud model for personal data; the `local` provider stays as a measured switch | requirements R54, ai-layer §2 |
| 2026-11-21 | The reading version opens with the idea in half a minute and a second page "one description, three entrances"; a two-page short version comes from the same source | storyboard-pakiet.md |
| 2026-11-21 | After the task cards: the forms task is built as Track F (converter to the partner's JSON); Track B is parked for that task; nothing in the product calls out of the container; R54 does not apply to the forms task | coi-replan, WP-F |
| 2026-11-21 | Presentations follow the "document deck" concept: the deck is an official form (or a request) that the product processes; ten slides; the criteria table pre-filled on the last one | concept-document-deck.md |
