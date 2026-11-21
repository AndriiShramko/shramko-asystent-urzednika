# Verification plan: how we know it works, and how the owner sees it

Lead-owned. Written on 21 November 2026 at 14:50 after the owner's instruction of 14:22 (he tests nothing himself; the lead finds the right tests and shows the proof) and after two second opinions of a hosted model: the audit of the plan ([`research/eden/e6-coverage-audit.gpt-6.2-astra.md`](../../research/eden/e6-coverage-audit.gpt-6.2-astra.md)) and the review of the shared models ([`research/eden/e7-models-review.gpt-6.2-astra.md`](../../research/eden/e7-models-review.gpt-6.2-astra.md)). Those reports are raw and unverified; a row is here only after the lead checked it against the task card ([`../05-hackathon/intake/coi-task-card.md`](../05-hackathon/intake/coi-task-card.md)) and the code. Every package brief from now on names the rows it owns.

Words that are never used without a measurement: accuracy, "imports into the partner's system" (there is no importer to try, answer J13), time saved for officials, "works on any form".

## 1. Requirement of the card, proof, what is still to add

State: `proven` = a test exists and passed on `main`; `planned` = in a package's acceptance list; `to add` = the audit found the proof weak.

| Card id | Proof | Check to add | Package | State |
|---|---|---|---|---|
| C-MIN-1 (a) content of the form | finder and brief tests on the nine sets | for each judged form: every field of the matter that both hosted readings (`eval/silver/`) name is in our form or in the omissions with a reason; the jury-style critique of section 4 | F3, F4, F11 | planned |
| C-MIN-1 (b) structure | strict profile, linter, typed form model | every answer of the service passes the gate, in CI, for a synthetic form of each of the eight formats | F0 (proven), F14, F20 | partly proven |
| C-MIN-1 (c) design rules | standard sections rebuilt and compared with both exports | each rule of the design standard is a numbered gate check with a fixture that fails exactly that check | F5, F14 | planned |
| C-MIN-2, C-TECH-DOC | README, architecture document | an agent that has not seen the project builds, changes one setting and converts from the README alone, and traces upload, reader, gate, answer in the architecture document | F12 | planned |
| C-OPT-1, C-OPT-2 | dictionaries and initial data of both exports reproduced; proposals with evidence | none beyond the acceptance list | F6 | planned |
| C-OPT-3 | conditions parsed and written back; journeys | two different choices and the zero-answer state evaluated by the reference JavaScript JSONata give the predicted visible sections; **seven** journeys (D16 adds the statutory representative), `not_applicable` where a form has no such path | F7, F14, F10 | planned |
| C-OPT-4 | review page | two different files uploaded in a browser; the downloaded forms equal the REST answers byte for byte | F9 | planned |
| C-OPT-5 | viewer renders both exports | one route predicted by hand before clicking | F10 | planned |
| C-OPT-6 | validators with valid and invalid synthetic values; batch | none beyond the acceptance list | F8, F9 | planned |
| C-TECH-LANG | image on Python 3.14; suite on 3.14 in CI | none | F20 | planned |
| C-TECH-OSS | licence gate with a planted copyleft dependency | the inventory is taken from the final image, native libraries, fonts and OCR data listed separately | F12, F20 | planned |
| C-TECH-NOEXT | container converts with `--network none`; egress canaries | none | F16, F20 | planned |
| C-TECH-API | one POST, one form, exactly `title`, `tabs`, `flow` | the stub is gone: the answer differs between two different forms | F1 (proven for the shell), F4, F5 | partly proven |
| C-TECH-FMT | readers for eight formats | one genuine file per extension through the published image; a binary Word file must not "pass" by answering 422 | F2a, F2b, F2c, F20 | planned |
| C-TECH-MIME | content proofs, swapped suffixes refused | `.jpe` is our documented exception (the partner's own set 7 ships one): a row in the contradiction docket, and `STRICT_EXTENSIONS=true` proves the literal reading | F1 (proven), docket | to add: docket row |
| C-TECH-NAME | `%`, 251 characters | every forbidden character as a parameter of one test; 250 passes, 251 refused | F1 follow-up | to add |
| C-TECH-SIZE, C-TECH-CONF | limit plus one byte; token negatives | two starts with two limits: the same upload flips from 200 to 413; key, issuer and audience rotated: old token refused, new accepted | F1 follow-up | to add |
| C-TECH-TEMP | temporary files removed in `finally` | after a success, a parse error and a killed worker the temporary directory is empty | F16 | to add |
| C-TECH-DOCKER | digests pinned, dedicated user, one port | the final image is inspected in CI: user, exposed port, no secret in environment or history | F20 | planned |
| C-SUB | seven results, deck, film | a script counts seven form files that pass the gate, at most ten pages in the deck PDF, at most 180 seconds of film | F11, P1 | planned |
| C-TEST | none yet | the defence drill of section 2 | F11 | to add |

## 2. New files at the defence: ten drills and one run on unseen forms

Each drill is a synthetic fixture with a test, or a documented fallback that the service really takes (a warning with the page, never a crash, never a silent default).

| # | Failure | Check | Fallback | Package |
|---|---|---|---|---|
| 1 | a skewed, pale scan loses Polish letters and box outlines | rotate and fade a labelled page; compare labels and counts | the page is flagged for reading by a person, not "no fields" | F2c |
| 2 | a PDF with text headers and a photographed body | a page with both; the body field must be found | OCR of the region, or the region is reported unread | F2a, F2c |
| 3 | two columns: the right-hand PESEL goes to the left-hand person | label, box and owner asserted together | the link stays unresolved, as a decision | F3 |
| 4 | floating text boxes of a DOCX in another order than on the page | shuffle the XML order without moving the boxes; section membership must not change | anchors shown for inspection | F2a, F3 |
| 5 | binary Word loses table geometry | neighbouring names of applicant and proxy stay separate fields | flow-only ambiguity reported; 422 only when nothing is readable | F2b |
| 6 | merged cells, a hidden helper sheet, a row repeated a thousand times | one field per labelled merge; helpers left out and reported | uncertain grid flagged | F2b |
| 7 | `□ inne (jakie?)` next to a bullet | one option with a conditional text field | wording kept, grouping asked as a decision | F3, F7 |
| 8 | eleven PESEL boxes or `NN-NNN` become separate numbers | one text value, leading zero kept | plain text without a validator | F3 |
| 9 | `wypełnia organ`, `niepotrzebne skreślić` read as fields of the resident | office block left out with its reason; crossed alternatives become one choice | the instruction is quoted, nothing is guessed | F4 |
| 10 | a repeating table that continues on the next page | one repeating section, not two | multiplicity flagged, never cut silently | F3, F5 |

**Run on unseen forms.** After the image is frozen: forms of the city's archive that no rule author has opened (release `pre-event`, 661 documents, all formats) go through the service. Recorded per file: status, seconds, peak memory, fields, warnings. No unhandled exception is allowed; the counts, the failures and the skipped files are published as they are.

## 3. What the owner is shown (ten minutes, at every milestone)

One page in Russian, in this order: the commit and the image digest with the proof that it starts without network; a blank dropped on the review page with the paper beside the form; the eight formats and the seven judged outputs with what the gate says; two choices and the zero-answer state in the viewer, one refused PESEL, one omission with its quoted reason; refused uploads and the empty temporary directory; seconds and memory per form; and a list of what failed or was skipped.

## 4. Second opinions on the partner's credits (build-time only)

1. Before milestone (c): each of the seven outputs, with the text of its paper and the partner's design standard, is read by two model families in the role of the jury; findings become rule fixes or documented omissions, never product output.
2. Before each milestone: one review of the diff by another model family.
3. Reasoning models need room: at 14,000 output tokens two of three calls returned an empty text; use at least 40,000 or a lower reasoning effort, and check that the file is not empty.

## 5. Revision 1.1 of the shared models (accepted from the review; all additive)

Nothing valid today becomes invalid. Done by one agent before the finder starts.

| # | Change | Who needs it |
|---|---|---|
| 1 | placement per element: an element may carry a box **and** an anchor (a text box anchored to a paragraph), so a DOCX page may mix flow paragraphs and placed boxes | F2a, F3 |
| 2 | the brief carries a disposition for every finder candidate (field, merged into, covered by a standard section, left out with a reason, awaiting a decision); the composer returns the map from brief key to form id; the ledger is assembled from them and checked against the finder's ids | F4, F5, F15 |
| 3 | spans `(run, start, end)` for marks, labels and options inside one run (`❑ pies ❑ suka`), coverage counted over spans | F3, F15 |
| 4 | applicant options as items (stable key, party, capacity, evidence) beside the flags; the applicant selector is a legal target of a condition | F4, F5, F7 |
| 5 | reader facts kept when the source declares them: tab leaders, region (body, header, footer, footnote), footnote links, picture bounds or an ink flag per page, row heights and column widths of sheets | F2a, F2b, F3 |
| 6 | widgets keep the field reference, display and export values and button states; the brief allows a single yes-or-no checkbox without options | F2a, F4 |
| 7 | a list of evidence records per field in the sidecar; located evidence without a quote for a drawn blank; `required` from the paper needs evidence | F4, F15 |
| 8 | the receipt on mandatory attachments travels from the brief; a proposed fee has its own place and never upgrades `not_found`; declaration and consent are told apart | F4, F15 |
| 9 | constructors at the reader boundary that normalise a bad observation (zero font size, reversed rectangle) into a warning `UNREADABLE_PART` instead of an exception | F2a, F2b, F2c |

Not taken: restricting dictionary names to the three seen (answer J5 allows well-argued own dictionaries; the F6 negative control stays a test of the composer, not of the model); stable keys for options and one id helper (the composer owns ids, D10); the empty-page check per journey (gate check G8).

## 6. Additions accepted from the audit

1. Every problem answer carries a plain Polish action for the official (for example: save the binary Word file as DOCX and send it again). F1 follow-up.
2. The seventh journey (statutory representative). F14, F10.
3. A rollback line in the README: the command that starts the previous tested image digest. F12.
