# WP-F20 Image pipeline in CI: status

Branch: wp/F20-image-pipeline   Stage now: core

## Status
- [x] tools/ci/wait_run.py: token from `git credential fill`, kept in memory, polls runs of a commit (<= 540 s), prints jobs, steps, the log lines up to the last error of a failed job; tried on the probe commit d64c001 (success, exit 0)
- [x] tools/ci/make_fixtures.py: one synthetic blank form per extension (pdf, docx, xlsx, ods, doc, png, jpg, jpeg); .doc is a hand-built Word 97 binary (FIB + piece table)
- [x] tools/ci/formcheck.py: exactly title/tabs/flow + `coi_lint` strict (schema + rules) + same bytes twice; no stored copy
- [x] tools/ci/container_check.py: hardening probe, conversions with --network none, HTTP path and negative controls
- [x] tools/ci/check_pins.py (bases by digest, pip wheel-only with hashes, actions by commit hash); tools/ci/junit_summary.py (skips counted with reasons)
- [x] .github/workflows/image.yml (native job + image matrix core/plus, push test tag from wp/F20-*, publish and sign from main); probe.yml pinned by hash
- [x] Native tests tools/ci/tests: 22 pass
- [ ] First CI run on the package branch: both targets build, container checks green
- [ ] Step 4 of design 9.2: hostile corpus against the image and `/v1/selftest` in both network modes (needs WP-F16)
- [ ] Step 5: SBOM of the final image, vulnerability gate (Grype, pip-audit), licence gate (`tools/licence_check.py`, not yet in the repository) as artefacts
- [ ] Signing and `latest-main` (run only on main; unverified until the merge); README digest (lead)
- [ ] Live negative controls in CI (an unpinned base fails the run; an sdist-only dependency fails the build; a planted failing attack reddens the corpus step)
- [ ] Delete probe.yml once image.yml is green on main

## Decisions
- Fixtures are generated in CI by `tools/ci/make_fixtures.py`, never stored / no task set may enter git / rules out comparing with stored outputs.
- The conversion check is property-based (keys, lint strict, determinism) / it must hold when the real pipeline replaces the stub / rules out a golden copy of the stub's output.
- The hardening probe runs the image's own USER (no `--user` override) / proves the image, not the command line / rules out a pass that only the flags produce.
- Plain `docker build` and `docker push` instead of docker/* actions / fewer third-party actions to pin and trust / no GitHub build cache (builds are slower).
- HTTP checks live in one function used both in CI (container) and in a native unit test / the expected codes are proved before a CI minute is spent.
- Tags: main -> `<sha>`, `latest-main` (core) and `<sha>-plus`, `latest-main-plus`; wp/F20-* -> `test-<short sha>[-plus]`, pulled back by digest and run once; pull requests push nothing.

## Changes to files of WP-F1 (merged; allowed by the brief)
- apps/converter/Dockerfile.dockerignore: added `.claude` (worktrees of the main checkout) and `secrets` (the compose key file) to the excluded paths.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| CI tools, native (pins, fixtures through the guard, .doc piece table, every fixture converts natively to a passing form twice the same, probe weaknesses each refused, HTTP checks against the native service) | `bash tools/gate.sh py -m pytest tools/ci/tests -q -p no:cacheprovider` | 22 passed | see git log |

## Negative control
Native, as tests: a base without digest, a pip install without `--only-binary=:all:`, an action by tag, a fourth top-level key, a form failing lint strict, two different outputs, and each probe weakness (uid 0, capability, writable root, extra interface, a connect) are refused. The live ones in CI are left (see Status).

## Requests to lead

## Cost notes
