# WP-F0p wire the readers and the composer into the service: status

Branch: wp/F0p-pipeline   Stage now: done (one stage)

## Status
- [x] Configuration: STATUTORY_REPRESENTATIVE, POA_EXEMPTION, OCR_MIN_CHARS; `read_options`, `compose_options`; ID_NAMESPACE checked as UUID; README rows
- [x] `app.pipeline.run`: format from the guard's content proof, read, interim brief, compose; form as dict plus sidecar
- [x] `app/interim.py`: title by rule, everything else not_found; sidecar warning `BRIEF_NOT_READ` (Polish message)
- [x] Failures: ReaderError -> ProblemError (UNREADABLE 422, TOO_LARGE 413, UNSUPPORTED_FORMAT -> EXTENSION 415); no reader -> 422 UNREADABLE "jeszcze"; ComposeError -> 500 GATE_FAILED. main.py needed no change: it already maps ProblemError
- [x] Tests `apps/converter/tests/pipeline/` (14, two of them `sets`); shell tests adapted (formats without a reader answer 422)
- [x] Negative control; fast gate

## Decisions
- Title rule: a short line that starts with a form-kind word (wniosek, deklaracja, ...) wins by weight; else the heaviest of the first 14 non-furniture runs. Furniture: attachment mark, place-and-date, addressee block, leader lines, bracketed hints, labels ending in a colon. Wrapped heading joined only for same look directly below (flow: second bold paragraph starting in lower case).
- The sidecar warning code `BRIEF_NOT_READ` lives in the sidecar dict only: `WarningCode` (model, not mine) has no such code.
- `FILLED_FORM`, `ACTIVE_CONTENT` warnings are not yet in the sidecar (guard facts are not passed to `run`).

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| pipeline tests | `bash tools/gate.sh py -m pytest apps/converter/tests/pipeline -q` | 14 passed (sets present on this machine: all PDF and DOCX of nine sets 200, strict linter 0 errors, titles of both reference forms hold their words) | see log |
| fast gate | `bash tools/gate.sh fast` | 392 passed, 8 deselected; PASSED | bf265b3 + shell test edits |

Titles measured on the sets (PDF/DOCX): 9 of 9 judged-or-reference forms give a heading with the word "wniosek" or "deklaracja"; known weak spots: judged-06 gives "WNIOSEK" only; judged-09 PDF may join two headings.

## Negative control
`pipeline.run` set the title to the old stub's "Formularz próbny" after compose: 6 pipeline tests failed (two-titles, title-of-the-file x2, furniture, doc-as-docx, reference words). Restored.

## Requests to lead
- `WarningCode` (model): add `BRIEF_NOT_READ` when WP-F4 replaces the interim step, or leave it a sidecar-only code.
- Pass the guard's `UploadInfo` (macros, kind) to `pipeline.run` when WP-F15 builds the sidecar (ACTIVE_CONTENT warning).

## Cost notes
- One round went to a heredoc that turned `\b` and `\n` into control characters in a regex; use the Edit/Write tools for regexes.
