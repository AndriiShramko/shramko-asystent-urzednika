# WP-F-tests Honest tests (audit section 5): status

Branch: wp/F-tests-honest   Stage now: core

## Status
- [x] 1. integration.mjs: digest check fails on a missing header, unreadable body, missing or on-by-default pretty switch (read-check only, see Evidence)
- [ ] 2. Endpoint contract tests (tests/shell/test_contract_honest.py)
- [ ] 3. Count-only assertions on the sets replaced or named
- [ ] 4. Determinism test (twice in-process, different thread count)
- [ ] 5. Negative control per new test
- [ ] 6. G11/G12 wiring or exact plan

## Decisions
- integration.mjs awaits the convert response with `waitForResponse` instead of a `once` listener / the old listener could resolve after the comparison, so a missing header was a race, not a fact / rules out the escape clause `!hdr || ...`.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| 1. integration.mjs | `node --check apps/review-web/scripts/integration.mjs` | syntax OK; not run: the `playwright` module does not resolve from apps/review-web (ERR_MODULE_NOT_FOUND) and the script needs a running service with AUTH_MODE=jwt and the partner's files, so this is a read-check | step 1 |

## Negative control

## Requests to lead

## Cost notes
