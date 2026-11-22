# Security policy

## What must never be in this repository

- Real personal data of any kind: names with identifiers, PESEL, document numbers, addresses, phone numbers, scans or photos of documents, real requests received by an office.
- Secrets: API keys, tokens, passwords, `.env` files, cookies, signed links.
- Vendor software and licence files (for example the document-reader SDK and its device-bound licences).
- Downloaded form templates and other binaries (the catalogue stores links and hashes).

Tests, demos, screenshots and prompts use **synthetic persons and synthetic requests only** (the converter's CI converts synthetic blank forms written by `tools/ci/make_fixtures.py`). A synthetic PESEL is built in code from a stem and a computed check digit, never taken from memory or from a real document.

A commit-time scanner for identifier-like patterns and secrets was planned and is not built in this repository. CI checks the final image for secret-like environment variables (`tools/ci/container_check.py`). A value found in review is fixed by removing it.

## Reporting a vulnerability

Open a private security advisory on GitHub ("Security" tab → "Report a vulnerability") or write to the author (contact in [`README.md`](README.md)). Please do not open a public issue for a vulnerability and do not include real personal data in a report. You will get an answer within a few days.

## Design commitments of the parked UDIP assistant (not built)

These are requirements for any implementation of the UDIP assistant brief (the pre-event vision in `README.md`); they do not describe the forms converter in `apps/converter`, which has no language model and no database; the detailed controls are in [`docs/02-architecture/security-and-privacy.md`](docs/02-architecture/security-and-privacy.md).

1. Clients talk to an API only; nothing reaches a database directly.
2. Personal data of a counter visitor is end-to-end encrypted between the phone and the office side, lives in memory with a short time-to-live, and is deleted on print, on request and on expiry.
3. Images of identity documents are never stored or sent to an external service.
4. Text that contains personal data goes only to a language model inside the office's control, or to an external model after pseudonymisation; public material (legal texts, blank forms) may go to any model.
5. Text received from outside (requests, attachments) is data, never instructions, for any model.
6. No AI output leaves the office without a clerk's approval; every proposal, edit and approval is in an append-only audit log.
7. A legal basis cited in a draft is verified by code against the stored text of the act.
8. Logs contain identifiers of records, never the personal values.

## Converter service (the forms converter of Track F)

What a person who runs the image must know. Checked against the code on 22 November 2026.

- **Authentication is off unless a key is configured.** The default is `AUTH_MODE=auto`: a JWT is required when `JWT_SECRET_FILE`, `JWT_PUBLIC_KEY_FILE` or `JWT_JWKS_FILE` names a key file; with none of them the service accepts requests without a token, logs a warning at start and shows `"auth": "off"` in `GET /status`. The image starts this way so that the jury can run it with one command.
- **A key variable that is set but empty, or misspelt, means authentication is off.** For a deployment set `AUTH_MODE=jwt`: then a missing key refuses the start (exit 3). `docker-compose.yml` does this.
- **Publish the port on loopback only**: `-p 127.0.0.1:8080:8080`, as every command of the README does. `-p 8080:8080` opens it on every interface of the host. Open without a token are: convert, report, inspect, batches and the review page `/ui/`.
- **Why the open default is acceptable here:** the service is stateless, stores no upload and no result, and calls nothing outside the container; the exposure is processor time and the caller's own file. All callers without a token share one rate limit (60 requests a minute), so one outside client can exhaust it: another reason for loopback.
- **`/healthz` and `/status` never need a token**; they hold no key, no path and no file content.
- **A job over `JOB_TIMEOUT_S` (default 600 s) answers 504 but is not killed**: it ends in the background and keeps counting against the slots; while `CONCURRENCY` such jobs run, new requests get 429 `BUSY`. So at most 2 x `CONCURRENCY` - 1 conversions run at once.
- **Uploads are untrusted**: type by content, 20 MiB, 60 pages, 80 megapixels checked before decoding, archive limits, XML without DTD or entities; the image runs as a non-root user, works read-only with no capability.

## Scope and limits

This repository holds the forms converter built for HackNation 2026 (`apps/converter`, a REST service in Docker) and the specification and research package of the parked UDIP assistant. Neither has been audited. Before production use an office needs its own security review, a data protection impact assessment and an accessibility audit.
