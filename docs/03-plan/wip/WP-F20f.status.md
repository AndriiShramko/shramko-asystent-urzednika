# WP-F20f Do it for the user: status

Branch: wp/F20-f-user-formats   Stage now: 1a done natively (items 1 to 4); next 1b (items 5 to 8), then stage 2 (image, push)

## Status
- [x] 1. Guard routes by content: extensions rtf xls txt heic heif; proofs `{\rtf`, OLE `Workbook` or `Book` stream, ISO-BMFF brands (already), text (UTF-8, UTF-16 with BOM, cp1250); a disagreeing extension with exactly one known content kind is read as that kind with the Polish warning in `UploadInfo.warnings`; polyglots refused (`apps/converter/app/guard/checks.py`)
- [x] 2. RTF reader `readers/rtf.py` (own, pure Python, explicit stack, depth cap 128, limits on characters, groups, cells)
- [x] 3. XLS reader `readers/xls.py` with xlrd 2.0.2 (pyproject + both locks, only xlrd added)
- [x] 4. TXT reader `readers/txt.py`
- [x] Readers registered by discovery; HEIC ends in "Ta instalacja nie ma dekodera HEIC." (pipeline), no re-save advice
- [ ] Stage 1b: PDF owner password and annotation guard, animated JPEG/PNG, draft() for big JPEG, file-name cleaning, HEIC reader
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
| new tests | `bash tools/gate.sh py -m pytest apps/converter/tests/readers/test_user_formats.py -q` | see below | (filled at commit) |

## Negative control
(to fill)

## Requests to lead
- `app/model/common.py` `Format` and `contracts/coi/page-model.schema.json`: add rtf, xls, txt, heic (additive), then drop the four entries from `readers.MODEL_FORMAT`. Add warning codes if wanted (extension disagreed; styles not read).
- `app/pipeline.py` / `app/main.py`: `inspect_upload(...).warnings` (the Polish "Rozszerzenie .X nie zgadza się z zawartością; plik odczytano jako Y.") is not yet carried into the sidecar: `pipeline.run` gets no `UploadInfo`. Either pass `info.warnings` to `run` or recompute it there; the shell is not my path.
- Tests outside my paths changed because the policy changed (each edit is small): `apps/converter/tests/shell/test_shell_guard.py`, `test_shell_guard_ole.py`, `test_shell_config_cli.py`, `test_shell_http.py` (a spoof now needs bytes that are neither a known format nor text; `.txt` as the wrong-extension sample became `.exe`).
- `xlrd` declares no Python 3.14 classifier; it works on the project's Python here (3.13.3, `xlrd.__VERSION__` 2.0.2). The image's Python must be checked in the image run (research/20 item 5).

## Cost notes
- Stage 1a: most turns went to the old tests that encoded the strict policy and to a tool quirk (a unicode escape such as backslash-u in a tool argument is decoded; test files use a `@u` placeholder).
