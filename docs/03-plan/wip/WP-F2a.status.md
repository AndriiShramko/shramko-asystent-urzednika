# WP-F2a Readers, PDF and DOCX: status

Branch: wp/F2a-readers-pdf-docx   Stage now: core

## Status
- [x] Registry `app/readers/__init__.py` (self-registering modules, `read_document`, hooks), `_base.py`, `pdf.py`, `docx.py`
- [x] Unit tests on synthetic files: 42 pass (reportlab PDF; python-docx and raw-XML DOCX)
- [ ] Tests on the sets (`@pytest.mark.sets`)
- [ ] `app/readers/survey.py` writing `eval/readers-sets.json`
- [ ] Acceptance stage: survey over the nine sets, negative control, fast gate after merging main

## Decisions
- One registry: every non-underscore module of `app/readers/` is imported on first use and registers `@register(fmt)`; F2b/F2c add a file, no edit / testable by `formats()` / rules out a central format table.
- Any exception of a reader becomes `ReaderError(code, reason)` in `read_document` (UNREADABLE, ENCRYPTED, TOO_LARGE, UNSUPPORTED_FORMAT); reason names structure, never content / 422 without a stack trace / rules out library exceptions reaching the API.
- PDF text, vectors and fields all from pdfplumber (one coordinate space); pypdfium2 stays for rendering in F2c, pypdf unused / smallest design, boxes agree / rules out mismatched origins between three libraries.
- PDF runs: chars joined on one line while gap <= 1.2 x size, same weight and size; 3+ leader chars (dots, underscores, ellipsis) are their own run / leaders are places to fill / rules out leaders glued to labels.
- PDF page with < `ocr_min_chars` (20) characters: hook "pdf.textless_page" (F2c) if registered, else the page keeps what it has plus UNREADABLE_PART with the page number / honest gap / rules out a silent empty page.
- PDF vectors: rect thinner than 3 pt is a line; white or invisible shapes and dots under 1 pt dropped; dash pattern on-length <= 1.5 x width is dotted / testable / rules out page backgrounds as boxes.
- DOCX native vs flow: native when >= 80 % of the text sits in anchored text boxes (Fallback copies ignored); else flow / sets 2 and 8 native, others flow / rules out mixed pages.
- DOCX native geometry: anchor offset + base (page 0, margin/column = margin, paragraph = top margin only for the first paragraph of a page); a run takes its text box's box; unplaceable drawings and body text are counted in UNREADABLE_PART / readers never invent coordinates / rules out per-line boxes inside a box.
- DOCX flow: one run per paragraph; anchors `p[n]`, `tbl[m]/cell[r,c]/p[k]`, `p[n]/txbx[j]/p[k]`, `fn[i]/p[k]`; pages end at page breaks, last rendered page breaks and section breaks (body level only; a table stays on its first page) / testable / rules out page guesses.
- DOCX text rules: tab with a leader stop -> 10 leader chars; 3+ underlined blanks -> underscores; Wingdings boxes -> Unicode boxes, unknown symbol -> U+FFFD; legacy check box -> a box char; field codes, hidden and deleted text dropped; a content control showing its placeholder gives no text.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|

## Negative control
(acceptance stage)

## Requests to lead
- Acceptance "the DOCX of sets 2 and 8 give more than 100 runs each with boxes": set 2 holds 65 text boxes, not 130 (each is written twice, `mc:Choice` and its VML `mc:Fallback`); the reader gives 65 runs with boxes for set 2 (its PDF gives 70) and 651 for set 8. Proposed wording: "set 2 at least 60, set 8 more than 600 runs with boxes".

## Cost notes
