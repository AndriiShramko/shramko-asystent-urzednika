# WP-B11 — The whole catalogue in advance

> **After the task card (21 November, 11:25): this package is not built as written.** The forms task asks for a converter to the partner's JSON; the batch over a whole office lives on as the batch mode of WP-F9 and the archive run of WP-F2 and WP-F11 ([`WP-F-forms-to-json.md`](WP-F-forms-to-json.md)). Item 9 below (a cloud model reads the forms) is **forbidden inside that product**. The life of a description and the review queue remain the model for the review screen.

Owner's fifth brief (21 November 2026, 10:48; requirements R51–R52): "when a clerk adds a document to make it digital, the first thing is done by the system. Better still, we load and digitise all possible documents ourselves in advance, without the clerk. Only when a new document appears does the clerk add it to the shared system."

Kind: part a by spec, part b think · Model tier: middle (a), top (b) · Depends on: WP-B1 (descriptor format), WP-B6 method step 1 (geometry) · Branch: `wp/B11-catalogue`

## Goal

Before any clerk opens the product, every template the office publishes has already gone through the first pass. The clerk at the counter meets ready services. A person approves each description once, for the whole office (and for every other office that uses the same template). Adding a new document is the exception, and it enters the same queue.

## What is already measured (do not repeat, read)

`tools/forms_census.py` read the whole archive of the city on 21 November: [`data/forms-census.json`](../../../data/forms-census.json) (summary) and [`data/forms-census.csv`](../../../data/forms-census.csv) (worklist, one row per unique document). Numbers and method: [`research/13`](../../../research/13-forms-census-and-opening-facts.md).

| Class in the worklist | Documents | First pass |
|---|---|---|
| `fillable_pdf` | 29 | field names, kinds and positions are read from the file itself (2,319 declared fields); no model needed for geometry |
| `vector_form` | 186 | boxes and dotted leaders from vector geometry and the text layer (WP-B6 step 1) |
| `word_form` | 246 | convert to PDF with LibreOffice, then as `vector_form`; a person confirms that the converted page still looks like the template |
| `scan` | 24 | render the page and read it from pixels (model with vision); always reviewed field by field |
| `pdf_text_no_blanks`, `word_no_blanks` | 173 | probably information sheets, or forms made of table cells; one look decides `no_fields` or sends it to the model path |
| `sheet`, `other` | 3 | by hand, last |

## The life of a description

One field in the descriptor, `review_state`. (The existing field `template.status` describes the legal status of the template and stays as it is.)

| `review_state` | Meaning | Who moves it on |
|---|---|---|
| `draft_geometry` | places to fill were found by the program; no meanings yet | the batch (part a) |
| `draft_ai` | every field has a proposed label, kind, profile path or "case-specific", `who_fills`, with a confidence | the batch (part b) |
| `reviewed` | a person looked at every field on the page and accepted or corrected it | the catalogue maintainer |
| `published` | the overlay check passed (template hash matches, zero changed pixels outside the field boxes, ink in every filled field) | the system, automatically after `reviewed` |
| `no_fields` | information sheet or clause: nothing to fill; it is still listed in a set as "to read" or "to bring" | the catalogue maintainer |
| `stale` | the office replaced the file (hash changed at the weekly crawl); the old description is kept, the first pass runs again and the differences are shown | the system |

Hard rule, tested: **only `published` descriptions print, serve an online form or answer the agent door.** A draft never meets a visitor's data. This is rule 7 of `AGENTS.md` applied to the catalogue.

Who is "the catalogue maintainer": a role, not the counter clerk. One person per office is enough, and for templates fixed by national law one approval serves every office, because a description holds no personal data and is bound to the file by its hash. In the demo the role is played by the presenter.

## Part a — the batch over the whole archive (by spec)

1. `tools/batch_first_pass.py ARCHIVE_DIR --worklist data/forms-census.csv --out data/descriptors/` runs WP-B6 step 1 over every row of the classes `fillable_pdf`, `vector_form`, `word_form`, in that order. Output: one descriptor per document, named by the first 12 characters of the template hash, `review_state: draft_geometry`, `origin: batch`, with the source address and the service cards that use it.
2. For `fillable_pdf` the declared fields become descriptor fields directly (name, kind, rectangle, page). Report how many of them carry a usable label.
3. A report `data/descriptors/REPORT.json`: documents processed, fields found, failures with reasons, seconds. No personal data anywhere: the inputs are blank public templates.
4. Catalogue view in the clerk application ("Katalog druków"): a funnel with the real counts (all documents, first pass done, meanings proposed, approved, published) and a list by service card; a card is "gotowa" when every form of its set is `published`.
5. The API refuses to print or serve a description that is not `published` (HTTP 409 with a readable reason).
6. The weekly crawl compares hashes; a changed file sets `stale` and queues the first pass again.

Acceptance (a): the batch finishes over the whole archive and the report exists; every output validates against the descriptor schema; the count of processed documents equals the count of worklist rows of the three classes, or every difference is listed with its reason; the catalogue view shows the same numbers as the report; **negative control:** a request to print with a `draft_geometry` description returns 409 and nothing is printed; a template whose bytes were changed by one byte is reported as `stale`.

## Part b — meanings for the forms that matter first (think)

7. Order of work: the forms of the demo sets (WP-B7), then the documents used by the most service cards (`used_in_cards` in the worklist), then documents whose name says "wniosek", "zgłoszenie", "oświadczenie" (`name_kind = form`), largest number of places first. Stop where the time ends; the funnel shows honestly how far it got.
8. For each document the model receives the rendered page and the numbered candidate boxes and returns label, kind, profile path or "case-specific", validation and `who_fills` per id (WP-B6 step 2; the model never returns coordinates). Result: `review_state: draft_ai`.
9. **Which model** (owner's decision of 21 November, 10:56; R54): the strongest model available, because blank templates are public material (`AGENTS.md` rule 9, data class "Public"). During the event the building agents do this pass themselves and commit the descriptors, so the product needs no model call for forms that are already in the catalogue. A weak local model is not used for this step. The provider stays a switch in the gateway (`mock`, `local`, `cloud`) so that the same step can be repeated and measured inside an office later.
10. Review queue for the maintainer: page with the proposal drawn over the template, fields sorted by confidence (lowest first), one key to accept, drag to correct (the screen of WP-B6, opened from the queue). Accepting the last field sets `reviewed`; the overlay check then sets `published`.
11. "Dodaj nowy druk": the only thing a clerk ever does for the catalogue. Upload, the first pass runs at once, the document appears in the queue as `draft_ai`, the maintainer is notified.

Acceptance (b): the forms of both demo sets are `published`; at least the number of further documents recorded in the status file reached `draft_ai`, each with a confidence per field; the share of fields the maintainer changed during review is measured on the published forms and written into the report (it is the honest quality number for the deck); a new upload reaches the queue without any manual step; **negative control:** a model answer that names a box id not in the candidate list is rejected and logged.

## What this package does not do

- It does not publish anything a person has not approved, however confident the model is.
- It does not claim that all 661 documents are ready services. The funnel says how many are; the deck repeats the funnel.
- It does not move descriptions between offices by itself. The format and the hash binding make that possible; an exchange between offices is a proposal for the pilot.

## Numbers this package feeds into the deck

`data/descriptors/REPORT.json` → `site-formularze/deck/metrics.json` and the `CENSUS` and `METRICS` blocks of `tools/build_pakiet.py`: documents with a first pass, fields found, documents published, share of fields changed by the reviewer, seconds for the batch.
