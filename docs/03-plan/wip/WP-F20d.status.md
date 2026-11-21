# WP-F20d status

Stage: lead-owned, one stage. Branch wp/F20-d-more-formats (includes wp/F2b-readers-sheets-doc).

## Status
- [x] stale tests updated (shell 422 parametrize: jpg, png only; pipeline: xlsx, ods, doc give 200 + gate; png still 422 "jeszcze")
- [x] image.yml READY_FORMATS "pdf docx xlsx ods doc"
- [x] MAX_CELLS setting -> ReadOptions.max_cells, README row
- [x] fast gate: 517 passed, 14 deselected
- [x] native check of tools/ci/make_fixtures.py fixtures through `converter serve`: pdf, docx, xlsx, ods, doc 200 with formcheck clean; png, jpg, jpeg 422 UNREADABLE. No fixture change needed.
- [ ] image workflow run green

## Evidence
(see below after the run)

## Requests to lead
none

## Cost notes
- most turns: finding how to start the service natively (cwd apps/converter, port 8080).
