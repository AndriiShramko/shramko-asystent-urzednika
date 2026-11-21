# WP-00 — Scaffold, gate, synthetic data

Kind: by spec · Model tier: middle, medium effort · Depends on: nothing · Branch: `wp/00-scaffold` · Milestone: M0 (one hour; this package blocks everything, keep it small)

## Goal

A walking skeleton that every other package builds on: the monorepo layout, a running API with typed stubs for the whole contract, a running clerk web app that calls it, one command to start, one command to check, and generators of synthetic test data.

## Read first

1. `AGENTS.md`
2. `docs/02-architecture/api-contract.md` (the routes you stub)
3. `docs/03-plan/ownership.md` (the folders you create)
4. `docs/02-architecture/design-notes.md` §2 (stack)

## Build

1. Layout: `apps/api` (Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, pytest), `apps/clerk-web` (React, TypeScript, Vite, vitest), `packages/api-client` (generated), `tools/`, `data/`, `prompts/`, `contracts/`. Use `uv` for Python if available, otherwise `venv` + `pip`; `npm` workspaces for the front end.
2. `apps/api/app/main.py`: application factory that discovers `app/modules/*/routes.py` and mounts each module's router. A module that does not exist yet must not break start-up.
3. `apps/api/app/core/`: settings from environment (`.env.example` committed, `.env` ignored), database session (SQLite file under `var/`, WAL; PostgreSQL through one URL), problem-details error handler, demo authentication with four seeded users (clerk, reviewer, signer, admin) and a role dependency, request-id middleware, structured logging that never logs request bodies.
4. Stubs: every route of the contract exists with its request and response models and returns `501` with a problem-details body, except `GET /health`, the auth routes and `POST /cases` + `GET /cases` + `GET /cases/{id}` which work against an in-memory store, so the web app has something to show.
5. `tools/export_openapi.py` writes `contracts/openapi.json`; `npm run gen:client` generates `packages/api-client` from it.
6. `apps/clerk-web`: login, an inbox page that lists cases from the API, a case page that shows the original text and the two deadline dates. Polish UI strings in one file. Keyboard-usable, visible focus, sufficient contrast.
7. `tools/gate.sh fast`: format and lint (ruff, eslint), type checks (mypy or pyright on `app/`, `tsc`), unit tests, contract check (generated OpenAPI equals the committed file), `tools/precommit_scan.py` on staged and tracked files. `tools/gate.sh full` adds end-to-end tests (Playwright, headless) and an accessibility scan (axe) of each page. Both print a final line `GATE PASS` or `GATE FAIL <step>` and write the long output to `var/gate.log`.
8. `tools/precommit_scan.py`: blocks secrets (key-like strings, `.env` content) and identifier patterns (11-digit numbers with a valid PESEL checksum, 26-digit account numbers, document-number patterns) outside `tools/testdata` and files marked `# synthetic`. Prints type and file, never the value.
9. `tools/testdata/`: `persons.py` generates synthetic persons (names from small built-in lists, PESEL with valid checksum from a reserved birth-year range that is documented as synthetic, addresses on invented streets, document numbers with valid check digits); `requests.py` generates synthetic public-information requests from templates covering every class of `data/udip-taxonomy.json`, with seeds for repeatability. `python -m tools.testdata --persons 20 --requests 40 --seed 1 --out data/eval/`.
10. `Makefile` or `justfile` with `dev` (starts API and web), `gate`, `gen`. `README` section "Run it" with the exact commands, tested on a clean clone.

## Acceptance

- [ ] On a clean clone: the documented start command brings up API and web; logging in as the demo clerk shows the inbox; creating a case through the UI shows it with both dates.
- [ ] `tools/gate.sh fast` prints `GATE PASS`.
- [ ] `contracts/openapi.json` contains every route of `api-contract.md`.
- [ ] `python -m tools.testdata --persons 5 --requests 10 --seed 1` is deterministic (same output twice).
- [ ] `tools/precommit_scan.py` blocks a file containing a planted valid PESEL and passes when the line is removed (negative control, recorded in the status file).
- [ ] No dependency with a copyleft licence in the core; the list of dependencies with licences is in `docs/03-plan/wip/WP-00.status.md`.

## Out of scope

Real persistence of cases beyond the three working routes (WP-A1), any model call (WP-A2), styling beyond clean and accessible.
