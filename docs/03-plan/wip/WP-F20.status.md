# WP-F20 Image pipeline in CI: status

Branch: wp/F20-image-pipeline   Stage now: integration (SBOM + licence gate, live pin control; CI run pending)

## Status
- [x] tools/ci/wait_run.py: token from `git credential fill`, kept in memory, polls runs of a commit (<= 540 s), prints jobs, steps, the log lines up to the last error of a failed job; tried on the probe commit d64c001 (success, exit 0)
- [x] tools/ci/make_fixtures.py: one synthetic blank form per extension (pdf, docx, xlsx, ods, doc, png, jpg, jpeg); .doc is a hand-built Word 97 binary (FIB + piece table)
- [x] tools/ci/formcheck.py: exactly title/tabs/flow + `coi_lint` strict (schema + rules) + same bytes twice; no stored copy
- [x] tools/ci/container_check.py: hardening probe, conversions with --network none, HTTP path and negative controls
- [x] tools/ci/check_pins.py (bases by digest, pip wheel-only with hashes, actions by commit hash); tools/ci/junit_summary.py (skips counted with reasons)
- [x] .github/workflows/image.yml (native job + image matrix core/plus, push test tag from wp/F20-*, publish and sign from main); probe.yml pinned by hash
- [x] Native tests tools/ci/tests: 22 pass
- [x] First CI run on the package branch green (run actions/runs/44910300706 on b2fd0a1): both targets build, 18 of 18 container checks each, test tags pushed and pulled back by digest (the first run 44910179858 on 8b206b9 failed: a plain YAML scalar held `:all: -r`; fixed by a block scalar)
- [x] No change to Dockerfile, docker-compose.yml or the README was needed: the digests of WP-F1 are the real index digests (checked against Docker Hub on 21 Nov) and every wheel of requirements.lock exists for Alpine on Python 3.14
- [ ] Step 4 of design 9.2: hostile corpus against the image and `/v1/selftest` in both network modes (needs WP-F16)
- [x] Step 5 (part): tools/ci/sbom_gate.py: CycloneDX SBOM of the image's installed distributions, licence gate (copyleft refused, MPL needs lead, installed == locked), artefact per target; 4 native tests
- [ ] Step 5 (rest): vulnerability gate (pip-audit or Grype: new build-time tool, see Requests to lead)
- [ ] Signing and `latest-main` (run only on main; unverified until the merge); README digest (lead)
- [x] Live negative control in CI native job: an unpinned-base Dockerfile must fail check_pins (3 findings locally, exit 1)
- [ ] Other live controls ( an sdist-only dependency fails the build; a planted failing attack reddens the corpus step)
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
| CI tools, native (pins, fixtures through the guard, .doc piece table, every fixture converts natively to a passing form twice the same, probe weaknesses each refused, HTTP checks against the native service) | `bash tools/gate.sh py -m pytest tools/ci/tests -q -p no:cacheprovider` | 22 passed | 8b206b9 |
| Native suite on Linux, Python 3.14 (design 9.2 step 1) | CI job `native`: `bash tools/gate.sh full` + CI tool tests + `junit_summary.py` | lint ok; 214 passed, 0 failed, 8 skipped of 222 (7: task sets absent, never in git; 1: empty parameter set of the sets test); links ok | run actions/runs/44910300706, b2fd0a1 |
| Both targets build from a clean checkout, bases by digest, wheel-only installs with hashes (step 2) | CI job `image` matrix core/plus, `check_pins.py` first | core 274 MB, plus 363 MB; check_pins 0 findings | run actions/runs/44910300706, b2fd0a1 |
| Not root, no capabilities, read-only root, no network (design 8 container row) | `container_check.py` probe, image's own USER | uid 10001 gid 10001, CapEff 0, NoNewPrivs 1, root and /srv/converter not writable, ifaces ['lo'], connect OSError; both targets | run actions/runs/44910300706 |
| Conversion inside the container with `--network none` (step 3) | `container_check.py`, 8 synthetic fixtures (pdf docx xlsx ods doc png jpg jpeg), each converted twice | 8 of 8 per target: keys title/tabs/flow, lint strict 0 errors, same bytes twice (stub output today) | run actions/runs/44910300706 |
| HTTP path with a token and its negative controls (step 3) | `container_check.py` http part | healthz 200, convert 200 passing; no token 401 TOKEN_MISSING, expired 401 TOKEN_EXPIRED, alg none 401 TOKEN_INVALID, other key 401 TOKEN_INVALID, PNG named .pdf 415 TYPE_MISMATCH, .txt 415 EXTENSION | run actions/runs/44910300706 |
| Pull by digest and start (branch test tag) | push `test-b2fd0a1[-plus]`, `docker pull IMAGE@sha256`, convert with `--network none`, `formcheck.py` | core `sha256:ca3000acd221226fa41ef6c4557e8f289b3e0d044653c74ee247cdb151947d2e`, plus `sha256:292d36898a141895edfc59941f4f344cdb408b82ca8a0226a2dac518c0cf2989`: pulled.json passes | run actions/runs/44910300706 |

| SBOM + licence gate on both targets; live pin control | CI steps `sbom_gate.py`, "Live negative control" | all jobs success (native, core, plus); the SBOM step passed with 0 findings; the unpinned-base Dockerfile was refused in CI | run on 907b989 |

## Acceptance stage (commit 7133d5c, main already merged: up to date)
| Check | Result |
|---|---|
| `bash tools/gate.sh fast` | PASSED: 378 passed, 8 deselected |
| `bash tools/gate.sh py -m pytest tools/ci/tests -q` | 26 passed |
| Negative control: digests stripped from apps/converter/Dockerfile, `python tools/ci/check_pins.py` | 3 findings, exit 1; restored: 0 findings |
| CI | green on 907b989 (native, core, plus) as recorded above; no code changed in this stage |

## Negative control
Native, as tests: a base without digest, a pip install without `--only-binary=:all:`, an action by tag, a fourth top-level key, a form failing lint strict, two different outputs, and each probe weakness (uid 0, capability, writable root, extra interface, a connect) are refused. The live ones in CI are left (see Status).

## Requests to lead
- The README of the converter should name the image by digest once main publishes (lead, design 9.2 step 6). The test-tag digests above are from a branch, not for the README.
- WP-F16: the hostile corpus (`python -m tests.evil`) and `GET /v1/selftest` are needed for design 9.2 step 4; `tests/` is excluded from the image by Dockerfile.dockerignore, so the corpus must run from the runner against the container (as container_check.py does) or the lead decides to ship it.
- The licence gate needs `tools/licence_check.py` (named in the track rules, not in the repository yet): who writes it?

- Vulnerability gate: needs a new build-time tool (pip-audit, Apache-2.0, or Grype, Apache-2.0, a binary download). Lead to pick and set the severity threshold.
- Hostile corpus step waits for WP-F16 (not on main).

## Left for the next stage
- Step 5: SBOM of the final image (anchore/sbom-action or syft), vulnerability gate (Grype, pip-audit), licence gate, reports as artefacts; decide the severity threshold with the lead.
- Live negative controls in CI, recorded once: a branch commit with an unpinned base (check_pins red), a lock line for an sdist-only package (build red), a planted failing attack (after WP-F16).
- On main after the merge: verify the publish path (tags `<sha>`, `latest-main`, cosign signature by digest), then delete probe.yml.

## Cost notes
- core: two CI runs (one YAML slip: `:all: -r` in a plain scalar); everything else passed on the first real run because the HTTP checks were first proved natively against the service. Checking YAML locally needs PyYAML, which the environment lacks: a block scalar for every `run:` line avoids the class of error.
- integration: little to wire because WP-F16 and the licence tool are not on main; the stage added the SBOM/licence gate and one live control. Cheaper: land F16 before this stage.
- acceptance: three commands, no CI run; the tool refuses compound git commands in a worktree, so split them.
