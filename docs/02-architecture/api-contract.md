# API contract (v0)

Every client talks to this API; nothing reaches a database directly (R10). The backend is the source of the machine-readable contract: route stubs with typed request and response models are created first (WP-00), the generated OpenAPI document is committed to `contracts/openapi.json`, and the TypeScript client in `packages/api-client` is generated from it. A front-end package can therefore start against stubs on the first day.

Changing the contract: only the lead, on `main`, in a small commit announced in `docs/03-plan/STATUS.md`. A builder who needs a change writes a request in its status file and continues against a mock.

Conventions: JSON; UTF-8; ISO 8601 times in UTC with the office time zone applied in the UI; ids are opaque strings; errors use `application/problem+json` with `type`, `title`, `detail`, `code`; lists are paginated with `limit` and `cursor`; every mutating call writes an audit event. Authentication for the demo is a session cookie from `POST /auth/login` with seeded demo users; roles: `clerk`, `reviewer`, `signer`, `admin`. An identity provider of the office replaces it later without changing the routes.

## Module A: public-information cases

| Method and path | Purpose | Role |
|---|---|---|
| `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` | demo session | any |
| `POST /cases` | register a request: `channel`, `received_at`, `raw_text` or an uploaded file; returns the case with both deadline dates | clerk |
| `GET /cases` | inbox with filters `state`, `due_before`, `assignee`, `q`; each item carries the clocks | clerk |
| `GET /cases/{id}` | full case: original text, questions, analysis, drafts, clocks, state, policy flags | clerk |
| `PATCH /cases/{id}` | assign, change state, record a policy decision (for example "ask the applicant to identify themselves") | clerk |
| `POST /cases/{id}/analysis` | start the analysis pipeline (asynchronous); `GET /cases/{id}/analysis` returns status and result | clerk |
| `GET /cases/{id}/analysis/trace` | what was sent to the model: provider, data class, the pseudonymised text, token map size (never the map) | clerk |
| `PUT /cases/{id}/questions/{qid}/classification` | the clerk confirms or changes the class, with a reason | clerk |
| `GET /cases/{id}/similar` | earlier cases and answers that look alike, with similarity and links | clerk |
| `POST /cases/{id}/drafts` | create a draft of a `document_type` for chosen questions | clerk |
| `GET /drafts/{id}`, `PUT /drafts/{id}` | read and edit; sections carry `origin`: `template`, `model`, `clerk` | clerk |
| `POST /drafts/{id}/check` | citation check and mandatory-element check; returns findings | clerk |
| `POST /drafts/{id}/submit`, `/approve`, `/reject` | approval flow: author → reviewer (always for decisions) → signer | by role |
| `GET /drafts/{id}/export?format=docx\|pdf` | export for the office's document system; allowed only after approval unless `preview=true` | clerk |
| `POST /cases/{id}/documents` | upload a document that is to be disclosed | clerk |
| `POST /documents/{id}/redaction/proposals` | detect personal data and propose masks | clerk |
| `PUT /documents/{id}/redaction` | accepted masks with legal ground | clerk |
| `GET /documents/{id}/redacted` | the redacted file (masks burnt in) | clerk |
| `GET /cases/{id}/events` | audit trail of the case | clerk, admin |
| `GET /audit/verify` | verifies the hash chain; returns the first broken link if any | admin |
| `GET /dashboard/deadlines`, `GET /dashboard/stats` | clocks across cases; counts by class, handling time, frequent topics | clerk |
| `GET /kb/search?q=&source=law\|bulletin\|archive` | passages with source address and date | clerk |
| `GET /kb/provisions/{act}/{unit}` | the stored text of a provision (used by the citation check and by the UI) | clerk |
| `POST /pii/pseudonymise` | demo endpoint: text in, tokenised text and entity types out | clerk |
| `POST /eval/run`, `GET /eval/last` | run the evaluation set; metrics | admin |
| `POST /public/analyse` | optional public page for jurors: synthetic or pasted text, rate-limited, nothing stored beyond the response | none |

## Module B: counter

| Method and path | Purpose | Zone |
|---|---|---|
| `POST /sessions` | the clerk opens a handoff session: returns `session_id`, the session public key, `expires_at`, the content for the QR code | office (2) |
| `GET /sessions?state=waiting\|received` | waiting list on the clerk's screen | office |
| `GET /relay/sessions/{id}` | the phone asks which fields the chosen case needs (no personal data in this call) | relay (1) |
| `PUT /relay/sessions/{id}/payload` | the phone uploads ciphertext: `enc`, `ciphertext`, `aad` | relay |
| `DELETE /relay/sessions/{id}` | the visitor withdraws | relay |
| `GET /sessions/{id}` | the office side returns the decrypted profile from memory, with provenance per field and the short comparison code | office |
| `PUT /sessions/{id}/persons/{pid}` | the clerk corrects or confirms fields (provenance becomes `confirmed_by_clerk`) | office |
| `DELETE /sessions/{id}` | delete now; also happens on print and on expiry | office |
| `GET /forms`, `GET /forms/{form_id}` | form descriptors (no personal data) | office |
| `GET /bundles`, `POST /bundles/recommend` | bundles; recommendation from a short description of the situation (no identifying data in the request) | office |
| `POST /sessions/{id}/fill` | fill chosen forms for chosen persons; returns PDF streams; nothing is written to disk | office |
| `POST /sessions/{id}/check` | findings of the checker with severity | office |
| `POST /identity/mrz/validate` | check digits and field parsing for text read on the device (the image never leaves the device) | office |
| `POST /onboarding/forms`, `GET/PUT /onboarding/forms/{id}` | blank PDF in, draft descriptor out; a person reviews and publishes it | office |
| `GET /bridge/status`, `POST /bridge/scan`, `POST /bridge/print` | local bridge on the clerk's workstation (`127.0.0.1` only, pairing token): document reader and printer | workstation (3) |

## Core objects (sketch; the typed models in code are authoritative)

```json
{
  "Case": {
    "id": "c_…", "number": "UDIP/2026/000123", "channel": "email|edelivery|paper|oral|epuap",
    "received_at": "…", "state": "new|analysed|with_unit|draft|review|signed|sent|closed",
    "applicant": {"identified": false, "has_signature": false, "contact": "token:…"},
    "clocks": {"due": "…", "latest_after_extension": "…", "waiting_until": null},
    "questions": ["Question"], "policy": {"anonymous_requests": "accept|ask_identification"}
  },
  "Question": {
    "id": "q_…", "text": "…", "class": "taxonomy id from data/udip-taxonomy.json",
    "reasons": ["…"], "provisions": ["udip:art.13:ust.2"], "confidence": 0.0,
    "clerk_must_check": ["…"], "confirmed_by": null
  },
  "Draft": {
    "id": "d_…", "document_type": "id from the taxonomy", "state": "draft|in_review|approved|rejected",
    "sections": [{"id": "s1", "origin": "template|model|clerk", "text": "…", "citations": ["…"]}],
    "checks": {"citations": "pass|fail", "mandatory_elements": "pass|fail", "findings": []}
  },
  "Event": {
    "id": "e_…", "ts": "…", "actor": "user id or system", "case_id": "…", "type": "…",
    "payload_hash": "sha256…", "prev_hash": "…", "hash": "…"
  },
  "Finding": {"severity": "blocker|warning", "path": "…", "message": "…", "suggested_fix": null}
}
```

Personal values of an applicant are stored encrypted and are referenced by tokens in everything that can reach a model or a log.
