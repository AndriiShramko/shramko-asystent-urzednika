# WP-F20e More image formats and ODT: status

Branch `wp/F20-e-image-formats` (from main `ef9a80c`). Stage: one (core + integration + image run).

## Status

- [x] READY_FORMATS in `.github/workflows/image.yml`: png jpg jpeg (and the new formats odt tiff bmp gif webp)
- [x] `tools/ci/make_fixtures.py`: synthetic PNG/JPG (already drawn: Polish title, comb boxes, leaders) plus odt tiff (2 frames) bmp gif webp
- [x] Readers: TIFF (each frame a page), BMP, GIF and WEBP (first frame) in `readers/image.py` + `_raster.decode_frames`; ODT in `readers/odt.py`
- [x] Guard: extensions, magic-number proofs, MIME, HEIC/HEIF refused with a Polish reason (JPG advice), RTF still refused
- [x] Tests: `apps/converter/tests/readers/test_image_formats.py`
- [ ] Fast gate green
- [ ] Publishing check clean, push, image run green

## Decisions

- Limits: the pixel limit is checked per frame from the header before decoding; frames of a TIFF are counted against `max_pages` in the guard and in the reader; one frame is in memory at a time.
- GIF and WEBP: the first frame only (no refusal for animations, unlike JPEG/PNG).
- ODT: one flow page; paragraphs `p[n]`, tables `tbl[n]` with `tbl[n]/cell[r,c]`; no styles, borders or frames.
- BMP is proven by "BM" plus a known DIB header size at offset 14 (two bytes alone are not proof).

## Requests to lead

- `app/model/common.py` `Format` (and `contracts/coi/page-model.schema.json`) name only seven kinds. Until extended (additive: tiff, bmp, gif, webp, odt), `readers.MODEL_FORMAT` records the new kinds as `png` (images) and `docx` (odt) in `source.format`; `source.reader` (`image.*`, `odt`) tells them apart. Remove the mapping after the extension.
- `docs/02-architecture/converter-design.md` and the README list of accepted extensions should name tif/tiff, bmp, gif, webp, odt and the HEIC refusal.

## Evidence

(filled in below)

## Cost notes

Most turns: finding that a heredoc turned `\x00` into a real null byte in `checks.py` (fixed with a binary-safe script).
