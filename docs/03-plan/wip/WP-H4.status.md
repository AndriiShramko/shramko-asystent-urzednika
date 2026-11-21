# WP-H4 the engine is always visible: status

Branch: wp/H4-engine-visible   Stage now: core

## Status
- [~] engine state module, settings names, header, /status, log, CLI line, warning codes, tests (in the working tree, not committed)
- [ ] byte comparison of form and sidecar against main 9e095ab (synthetic fixtures and the nine task sets)
- [ ] review page: badge of the last conversion
- [ ] negative control, fast gate, push

## Decisions
- (filled with the first commit)

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|

## Negative control
(not run yet)

## Requests to lead
- BLOCKING FOR THE IMAGE WORKFLOW: `tools/ci/container_check.py` line 222 fails a converted fixture when the
  CLI's stderr is not empty. The brief asks for one `ENGINE: ...` line on stderr of `convert`. `tools/ci/**` is not
  mine. Merge H4 together with the patch written below, or the image workflow goes red on every fixture.

## Left for the next stage
(nothing yet)

## Cost notes
- core: (filled at the end)
