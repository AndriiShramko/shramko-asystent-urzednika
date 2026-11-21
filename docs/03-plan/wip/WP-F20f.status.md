# WP-F20f Do it for the user: status

Branch: wp/F20-f-user-formats   Stage now: 1a and 1b done natively (items 1 to 8); next stage 2 (image, push)

## Status
- [x] 1. Guard routes by content: extensions rtf xls txt heic heif; proofs `{\rtf`, OLE `Workbook` or `Book` stream, ISO-BMFF brands (already), text (UTF-8, UTF-16 with BOM, cp1250); a disagreeing extension with exactly one known content kind is read as that kind with the Polish warning in `UploadInfo.warnings`; polyglots refused (`apps/converter/app/guard/checks.py`)
- [x] 2. RTF reader `readers/rtf.py` (own, pure Python, explicit stack, depth cap 128, limits on characters, groups, cells)
- [x] 3. XLS reader `readers/xls.py` with xlrd 2.0.2 (pyproject + both locks, only xlrd added)
- [x] 4. TXT reader `readers/txt.py`
- [x] Readers registered by discovery; HEIC ends in "Ta instalacja nie ma dekodera HEIC." (pipeline), no re-save advice
- [x] 5. PDF: owner password opens (empty user password; pdfplumber `raise_unicode_errors=False`, a failing widget pass is a warning, the page stays); a user password gives "Plik PDF jest chroniony hasłem otwarcia; usługa nie zna hasła." (pdfplumber wraps pdfminer's PDFPasswordIncorrect in PdfminerException: the old catch never fired, fixed)
- [x] 6. Images: animated PNG (APNG) and MPO give the first frame (note in the sidecar); JPEG up to 2x the pixel budget decoded with `draft()` (1/2, 1/4, 1/8), above 2x or any other format over the budget still refused
- [x] 7. File names cleaned by `clean_name` (forbidden, control, bidi characters removed; cut to 250 keeping the extension; empty becomes `plik`; a name with no extension is read by its content); Polish note in `UploadInfo.warnings`
- [x] 8. HEIC reader `readers/heic.py` (`heif-dec` child process, no shell, 30 s, own temp folder, PNG through the image reader); without the program: code NO_DECODER, "Ta instalacja nie ma dekodera HEIC."
- [x] Granted: `Format` has rtf, xls, txt, heic (schemas regenerated with `python -m app.model.schemas`), `MODEL_FORMAT` cut to the F20e entries; `UploadInfo.warnings` reach the sidecar as `{"code": "INPUT_NOTE", "detail": ...}` through `pipeline.run(..., notes=)` from `main.py` and `cli.py`
- [ ] Stage 2: image, fixtures, NOTICE (not mine now)

## Decisions
- Plain text is the weakest proof and a fallback: it counts only when no other proof matches (a tiny ASCII PDF is not a polyglot of pdf and txt), and a disagreeing extension is accepted for text only under txt, doc, rtf, xls (`TEXT_OK_EXT`). A text file named .pdf, .docx, .xlsx, .ods, .odt or an image extension stays refused (TYPE_MISMATCH, "plik tekstowy"): this keeps the hostile corpus file `text-named-pdf.pdf` refused (7 of 7). This is a deliberate narrowing of the plan text ("exactly one known kind is never refused"); the lead may widen `TEXT_OK_EXT`.
- Text proof also needs no control characters other than tab, line feeds and form feed (random binary without NUL is not text).
- OLE with both a WordDocument and a Workbook stream is a polyglot (refused); BIFF5 `Book` stream routes to xls (xlrd reads it; styles are then not read and the sidecar says so).
- RTF: `\*` destinations are skipped except `\*\formfield`, `\*\fldinst` (muted) and the field result. A checkbox is written into the text as the glyph and into widgets as `checkbox`; a text blank as `__________` and widget `text`. Nested tables are flattened into the enclosing cell. Text boxes, footnotes, headers, footers, list numbers are not read (documented in the module).
- Codes: the page-model `Format` has no rtf, xls, txt, heic; `readers.MODEL_FORMAT` records them as doc, xlsx, doc, png (`source.reader` tells them apart). Warning codes: only `UNREADABLE_PART` exists, used for the BIFF5 "styles not read" note.
- Old tests that held the strict policy (a PNG named .pdf refused, swapped zip suffixes refused, `.txt` refused as an extension, HEIC refused by the guard) were rewritten in place: tests/readers (mine) and four files of tests/shell (see Requests).

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| new tests | `bash tools/gate.sh py -m pytest apps/converter/tests/readers/test_user_formats.py -q` | 47 passed | 6ac4aa0 |
| readers + shell tests | `pytest apps/converter/tests/readers apps/converter/tests/shell -q` | 393 passed, 1 skipped | 6ac4aa0 |
| unseen sample | `bash tools/gate.sh py -m eval.chain --corpus unseen --archive <archive> --compare` | 80 files: 79 converted, 1 refused, 0 failed; gate failures 0; strict-lint errors 0; 0 worse, 7 better | 6ac4aa0 |
| sets | same, `--corpus sets` | 71 of 71 converted, 0 worse, 27 better (their baseline predates later work), strict-lint 0 | 6ac4aa0 |
| hostile | same, `--corpus hostile` | 6 refused, 1 converted: `pixel.png` (a 1x1 PNG, the baseline predates the F20e image formats and is not changed by this stage); the other 6 incl. `text-named-pdf.pdf` still refused; 0 worse | 6ac4aa0 |

Table of the 8 refusals of the unseen baseline (ids are the sample hashes): 097a6c53 rtf refused -> converted (53 fields); 5cfc8acc rtf -> converted (59); 663c3b77 rtf -> converted (53); d2ca0d42 rtf -> converted (51); e652b3c0 rtf -> converted (62); 123b1988 xls -> converted (146); 93be3909 jpg -> converted (49; not a change of this stage: the image formats of F20e); 899c15a1 pdf -> still refused UNREADABLE (annotation crash, stage 1b). All converted: gate passed, 0 strict-lint errors.

## Evidence stage 1b
| Check | Command | Result | Commit |
|---|---|---|---|
| new tests | `bash tools/gate.sh py -m pytest apps/converter/tests/readers/test_user_formats_1b.py -q` | 27 passed, 1 skipped (`linux`: real child process) | a114770 + next |
| fast gate (after merging main) | `bash tools/gate.sh fast` | 743 passed, 3 skipped, 22 deselected | a114770 |
| chain | `bash tools/gate.sh py -m eval.chain --compare --archive <archive>` | 158 files: 152 converted, 6 refused, 0 failed; gate failures 0; strict-lint errors 0. unseen 80 of 80 converted (before: 79 of 80, the one refusal 899c15a1 now 151 fields); sets 71 of 71; hostile 6 refused, 1 converted (`pixel.png`, F20e, unchanged) | next |
| compare | same | 39 better; 3 worse, all in sets 9 (105 -> 72 twice, 133 -> 116): exactly the accepted F3b change (WP-F3b status, applicant fields dropped by D20; the baseline predates it), not this stage | next |

Archive PDF 899c15a1: `UnicodeDecodeError` in `page.annots` before, 151 fields after (local check only, nothing of it committed).

## Negative control 1b
`raise_unicode_errors=True` in `readers/pdf.py` (annotation guard off): `test_legacy_bytes_in_an_annotation_do_not_sink_the_page` failed ("the form fields of the page were not read (UnicodeDecodeError)"); restored to False, 27 passed.

## Requests to lead (1b)
- Tests outside my paths edited for item 7 (a bad name is cleaned, not refused): `tests/shell/test_shell_guard.py` (percent, forbidden characters, 251 characters, missing name, `noextension`) and `tests/shell/test_shell_http.py` (two BAD_NAME lines now expect 200).
- `pipeline.run` got `notes=`; `main.py` and `cli.py` pass it only when there are notes (other tests replace `pipeline.run` with a three-argument fake). The sidecar code of the notes is `INPUT_NOTE` (not in `WarningCode`: the sidecar is not typed by it; same as `LEDGER_NOT_CLOSED`).
- Stage 2: install `heif-dec` in the images; the Linux test `test_heic_with_a_real_child_process` uses a stand-in script; a real HEIC (made on the CI runner) is the end-to-end proof. `BAD_NAME` stays in the problem table, now unused by the guard.
- Not verified here: a real HEIC file (no `heif-dec` on this laptop); MPO/APNG only with Pillow-made files.

## Negative control
`MAX_DEPTH` of `readers/rtf.py` set to 10**9: `test_rtf_deep_nesting_is_refused_not_a_crash` failed ("DID NOT RAISE ReaderError"); restored to 128, 47 passed.

## Requests to lead
- `app/model/common.py` `Format` and `contracts/coi/page-model.schema.json`: add rtf, xls, txt, heic (additive), then drop the four entries from `readers.MODEL_FORMAT`. Add warning codes if wanted (extension disagreed; styles not read).
- `app/pipeline.py` / `app/main.py`: `inspect_upload(...).warnings` (the Polish "Rozszerzenie .X nie zgadza się z zawartością; plik odczytano jako Y.") is not yet carried into the sidecar: `pipeline.run` gets no `UploadInfo`. Either pass `info.warnings` to `run` or recompute it there; the shell is not my path.
- Tests outside my paths changed because the policy changed (each edit is small): `apps/converter/tests/shell/test_shell_guard.py`, `test_shell_guard_ole.py`, `test_shell_config_cli.py`, `test_shell_http.py` (a spoof now needs bytes that are neither a known format nor text; `.txt` as the wrong-extension sample became `.exe`).
- `xlrd` declares no Python 3.14 classifier; it works on the project's Python here (3.13.3, `xlrd.__VERSION__` 2.0.2). The image's Python must be checked in the image run (research/20 item 5).

## Cost notes
- Stage 1a: most turns went to the old tests that encoded the strict policy and to a tool quirk (a unicode escape such as backslash-u in a tool argument is decoded; test files use a `@u` placeholder).
- Stage 1b: most turns went to the PDF password path (pdfplumber wraps pdfminer's exception) and to shell tests that encoded the old name policy; a tool argument decodes backslash escapes, so control characters in tests are written with chr().
