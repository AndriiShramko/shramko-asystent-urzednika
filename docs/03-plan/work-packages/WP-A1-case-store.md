# WP-A1 — Case store, deadlines, audit trail

Kind: by spec · Model tier: middle, medium effort · Depends on: WP-00 · Branch: `wp/A1-case-store` · Milestone: M1

## Goal

Persistent cases for public-information requests with correct clocks, a state machine, roles, and an append-only audit trail with a hash chain.

## Read first

1. `AGENTS.md`
2. `docs/02-architecture/api-contract.md` (Module A routes and core objects)
3. `research/02-udip-law-process-taxonomy.md`: TL;DR and section 2 (decision tree: which waiting periods and dates exist)
4. `docs/02-architecture/design-notes.md` §3 points 1–3, 9, 10

## Build

1. Models and migration: `Case`, `Question`, `Document`, `Draft` (table only; logic is WP-A5), `Event`, `User`. Applicant contact values are stored encrypted (application-level encryption with a key from the environment) and exposed to other modules as tokens.
2. Case number generator `UDIP/<year>/<running number>`.
3. **Deadline calculator** (pure functions, heavily tested): `due = filing date + 14 days`; `latest_after_extension = filing date + 2 months`; waiting periods (14 days) that can be opened and closed by events; rule for a term ending on a Saturday or a public holiday taken from the research file (if the research marks it unverified, implement both variants behind a setting and default to the earlier, safer date). Polish public holidays table for 2026–2027 including movable feasts.
4. State machine with allowed transitions and required role per transition: `new → analysed → with_unit → draft → review → signed → sent → closed`, plus `waiting_for_applicant` and `discontinued`. Illegal transitions return a problem-details error.
5. Routes: all `/cases*` routes except analysis, similar and drafts; `/cases/{id}/events`; `/audit/verify`.
6. Audit module: `record(actor, case_id, type, payload)` stores the SHA-256 of the canonical payload, the previous event's hash and its own hash; payloads with personal data are stored encrypted, the hash is over the clear canonical form. `verify()` walks the chain. Every mutating route of this package records an event; other packages call `record`.
7. Policy flag per office: `anonymous_requests = accept | ask_identification` (default `accept`); a case from an unidentified sender shows the flag and the consequence, the system never rejects by itself.

## Acceptance

- [ ] Deadline tests: at least 20 dated cases including month ends, leap day, year change, a term ending on a holiday; all pass.
- [ ] Creating, reading, filtering by `due_before`, assigning and moving a case through the full state path works through the API with the right roles and fails with the wrong ones.
- [ ] After 50 mixed operations `GET /audit/verify` reports an intact chain; after one event row is altered directly in the database it reports the first broken link (negative control, recorded).
- [ ] No personal value appears in logs during the test run (the test greps the captured log for the synthetic identifiers).
- [ ] `tools/gate.sh fast` passes.

## Out of scope

Analysis, drafts content, search, UI.
