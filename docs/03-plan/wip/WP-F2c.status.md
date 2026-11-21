# WP-F2c Reader of images (JPEG, PNG) and the image way of a PDF: status

Branch: wp/F2c-images-ocr   Stage now: core done; next integration

## Status
- [x] `_raster.py`: decode with limits (formats restricted, size from header before decoding, `max_pixels`), metadata drop (pixels re-wrapped, EXIF orientation applied first), transparency on white, Otsu binarisation
- [x] tall-scan cutting at A4 ratio snapped to the nearest white band; unsnapped cut is a warning
- [x] raster detection with Pillow and `re` only: lines, closed boxes (cells that share borders cut by their sides), combs, dotted leaders
- [x] `_ocr.py`: engine interface, Tesseract in a subprocess (TSV words, confidence), `set_engine` for a fake; `image.py`: readers `jpeg` and `png`, pages of origin "ocr" in points (200 dpi), hook `pdf.textless_page` (pypdfium2 render)
- [x] without an engine or on engine failure: valid form, one UNREADABLE_PART "page not read" per page, shapes kept
- [x] `pdf.py`: hook may return (page, warnings); a page the image way could not read stays native with the reason (no OCR_USED then)
- [x] unit tests `tests/readers/test_image_reader.py` (23 pass, 1 tesseract-marked skipped here)
- [x] `eval/readers-sets.json` refreshed by the survey: 69 of 69 read (was 42 + 27 no_reader); scans give 2, 6, 16 pages
- [x] negative control
- [ ] integration: end to end through `pipeline.run` (no lint ERROR) for synthetic scans and the 27 set images; real Tesseract in the image workflow (marker `tesseract`)
- [ ] acceptance: fast gate green after the lead's changes below; drills 1 and 2 of verification plan section 2 need the finder

## Decisions
- Units: pixels x 0.36 = points (a 1654 px wide scan is A4 at 200 dpi); a PDF page rendered at 200 dpi (less if over `max_pixels`) maps back with 1/scale / one constant, no DPI from metadata / rules out trusting declared DPI.
- Page count of a stack = round(height / (width x sqrt 2)); each nominal cut moves to the centre of the nearest white run within 8 % of a page / the sets' 4678, 14034, 37424 px give 2, 6, 16 / rules out cutting at a fixed height.
- Shapes: boxes found from a top edge, a bottom edge of the same extent and solid sides (columns at least 90 % ink), so letters (E, B) make none; the comb is reported by `detect` (`Shapes.combs`) and the page lists its cells as plain rects: the finder groups them (design 6.3 rule 3) / leaders become Line style "dotted" / no new model element.
- One run per OCR word, `conf` = word confidence / 100, `size` = 0.85 x tallest box of its line in points (a comparable measure, not a font size).
- No engine installed: reader name `image.raster` (not `image.ocr`); the registry hook is always registered.
- Images with more than 4000 shapes per page: the rest is dropped with a warning.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| unit tests, synthetic | `bash tools/gate.sh py -m pytest apps/converter/tests/readers/test_image_reader.py -q` | 23 passed, 1 skipped (tesseract) | core commit |
| readers suite | `bash tools/gate.sh py -m pytest apps/converter/tests/readers -q` | 106 earlier run with 2 failures since fixed; image + pdf modules 36 passed | core commit |
| survey over the sets | `bash tools/gate.sh py -m app.readers.survey --check` | 69 files, read 69; the 27 images: pages 1 (9 files), 2 (12), 6 (3), 16 (3); slowest 2.9 s (16 pages, no OCR) | core commit |
| 16-page scan 1654 x 37424 synthetic | test_a_sixteen_page_scan_of_37424_pixels_is_sixteen_pages | 16 pages, 0.8 s | core commit |

## Negative control
In `_raster.py` the metadata-dropping `Image.frombytes` was replaced by `return grey` and the white-row test by `False`: `test_decode_drops_metadata_and_applies_orientation` and `test_tall_scan_is_cut_into_pages_at_white_bands` failed (2 failed, 21 passed); restored, 23 passed.

## Requests to lead
- `app/pipeline.py`: nothing to change if it refuses only `fmt not in formats()`; the list of formats without a reader (if any message names jpg/png) must drop `jpeg` and `png`. `formats()` now has jpeg and png.
- `.github/workflows/image.yml`: `READY_FORMATS` add `jpeg png` (all seven formats ready). The image installs tesseract-ocr with pol and eng already (Dockerfile); the `tesseract` marker test runs there.
- Stale tests outside our paths that fail now because images have a reader (fast gate, 7 failures): in `apps/converter/tests/shell/test_shell_http.py` the parametrize of `test_a_format_without_a_reader_passes_the_guard_and_is_422` (a.jpg, a.png), the batch tests `test_batch_streams_one_line_per_file_and_isolates_errors` and `test_batch_from_one_zip` (they use a tiny `fx.png()` as the "unreadable" file; a PNG now reads to a blank page, use a truncated PNG or another broken file), and `test_upper_case_extension_and_jpe_through_http` (a.jpe expects 422 UNREADABLE, now 200 for a valid JPEG).
- Optional (WP-F1 owner): map settings onto `ReadOptions.max_pixels`, `ocr_lang`, `ocr_timeout` in `app/config.py::read_options`.

## Cost notes
- core: most turns went to the shape detector (leader false positive on long rules, box sides) and to the knock-on PDF hook behaviour; a test with a drawn page at the start would have saved two turns.
