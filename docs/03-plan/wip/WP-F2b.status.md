# WP-F2b Readers of XLSX, ODS and binary Word: status

Branch: wp/F2b-readers-sheets-doc   Stage now: core done; next integration/acceptance

## Status
- [x] Shared pieces: `_zip.py` (part limits, safe XML), `_sheet.py` (grid of one sheet -> one flow page), `ReadOptions.max_cells`
- [x] XLSX reader `xlsx.py`, ODS reader `ods.py`, binary Word reader `doc.py` (piece table, PAPX, CHPX, fonts, text boxes)
- [x] Unit tests on synthetic files: `tests/readers/test_sheet_doc_readers.py` (16 tests) with `sheet_doc_builders.py` (hand-made ODS, OLE writer, Word 97 streams)
- [ ] survey.py: read `.doc` files that are DOCX by content (guard's `sniff_kinds`), then refresh `eval/readers-sets.json`
- [ ] sets tests (`@pytest.mark.sets`) for xlsx, ods, doc: every file reads; every OLE `.doc` has a title word in the first 20 runs (scratch check: run index 1..12 on all 7)
- [ ] negative control recorded by break and restore; fast gate after merging main
- [ ] after merge (lead): READY_FORMATS and the formats-without-reader list (see Requests to lead)

## Decisions
- Sheets: one page per sheet, origin flow, one table per sheet anchored at the used range; cell r,c = sheet indices from 0 / lines up with row_heights, col_widths / rules out per-region tables (the finder's job).
- Table cells = text cells, merges (top-left), empty cells with a drawn border; empty borderless merges dropped; a side is drawn if the cell or its neighbour across the edge declares it / places to fill stay visible / rules out one cell per grid square.
- Merges clamped to the used range before expansion; sizes listed only up to the last used row and column; hidden rows and columns get 0 / no million-entry lists / rules out sizes of unused space.
- ODS repeats: an element without text, border, span or validation only moves the position; one with content is charged repeats x cells against `max_cells` BEFORE expansion (TOO_LARGE over it); content repeated >100 times is kept and flagged UNREADABLE_PART / bounded and honest / rules out expanding trailing rows.
- XLSX own reader on zipfile+lxml (no openpyxl at run time); numbers written as stored (shortest form), number formats not applied; column width = chars x 5.25 pt / same limits as DOCX / rules out openpyxl's unbounded loading.
- Data-validation lists (quoted, range, defined name; ODS quoted or range) -> widget "choice"; unresolved list -> no options + UNREADABLE_PART / never a guessed list.
- DOC: main story then text-box story ("txbx[j]/p[k]", after the body, one warning that their place is unknown); pages only at explicit page breaks / the file records nothing else / rules out invented page splits.
- DOC tables from PAPX (sprmPFInTable, sprmPFTtp, huge PAPX in Data): cell c = ordinal in the row, no widths, merges or borders, one UNREADABLE_PART "flow only" warning; without PAPX cells become paragraphs and a warning says so (drill 5).
- DOC symbols via CHPX sprmCSymbol + font table (Wingdings boxes -> Unicode boxes, else U+FFFD); a PUA character without a font is U+FFFD; bold = direct bold on most non-space characters, size only when direct / no styles parsed / rules out "(" for a box.
- DOC refusals: encrypted or obfuscated -> ENCRYPTED; Word 6/95 (nFib < 193), missing table stream, broken piece table, no text -> UNREADABLE with the reason.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| unit tests, synthetic | `bash tools/gate.sh py -m pytest apps/converter/tests/readers -q` | 73 passed (16 new; sets tests of F2a included) | core commit |
| sets, scratch read | scratch script over 7 OLE .doc, 7 xlsx, 9 ods | all read, 0 refused, 0 crashes, <= 0.21 s each; xlsx and ods give equal runs and cells in 6 of 7 sets (set 3: 22 vs 23 runs); .doc title word at run index 1..12 | core commit |

## Negative control
Planned: `test_negative_control_ods_row_repeated_a_million_times_is_refused_before_expanding` with the budget check disabled must fail (time or no refusal). Not yet run.

## Requests to lead
- After merge, `.github/workflows/image.yml`: `READY_FORMATS: "pdf docx"` -> `READY_FORMATS: "pdf docx xlsx ods doc"`.
- `app/pipeline.py` has no fixed list: it refuses `fmt not in formats()`; the three readers register themselves, so no line changes there. The interim brief over sheet pages is untested.
- Optional (WP-F1 owner): map a setting onto `ReadOptions.max_cells` (default 200,000) in `app/config.py::read_options`.

## Cost notes
- core: most turns went to the binary Word format (FIB, piece table, FKP pages) and to a byte-level test builder; a reference of MS-DOC offsets in the brief would save two turns.
