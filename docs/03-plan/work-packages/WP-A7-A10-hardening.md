# WP-A7 … WP-A10 — Redaction helper, similar cases and dashboard, security pack, public page

Four smaller packages for milestone M3. Each gets its own branch, worktree and status file; they are described together because each is short.

---

## WP-A7 — Redaction helper

Kind: by spec · Model tier: middle · Depends on: WP-A2 · Branch: `wp/A7-redaction`

Goal: a document that is to be disclosed (a contract, an invoice, a protocol) comes out with personal data of private persons blacked out, and the clerk has a log that justifies every mask.

Build:
1. Upload PDF or DOCX; render pages to images locally; extract text with positions (text layer first, OCR fallback if a local OCR engine is installed; without it, say so in the UI).
2. Detect with the personal-data service of WP-A2; propose masks as rectangles with type and confidence. Names of persons performing public functions in connection with the function are **not** masked by default but are listed for the clerk's decision, with the provision that grounds the exception.
3. UI (`features/redaction`): page view with proposed masks; accept, remove, add by drawing; choose the legal ground per mask type.
4. Output: a new PDF built from rasterised pages with masks burnt in (no text layer underneath, no hidden content); redaction log (page, type, ground, who accepted, when) attached to the case; a reminder that a partial restriction needs a refusal decision for the hidden part, with a button that creates that draft.

Acceptance: on five synthetic documents all planted identifiers are masked; text extraction from the output finds none of them (negative control: an overlay-only output would fail this test, show it once); the log lists every mask; the original file stays unchanged.

---

## WP-A8 — Similar cases, campaigns, dashboard

Kind: by spec · Model tier: middle · Depends on: WP-A3, WP-A6 · Branch: `wp/A8-similar-dashboard`

Build:
1. Similarity of a new request to the archive: normalised text shingles plus full-text scores; optional embeddings behind the same setting as WP-A3. `GET /cases/{id}/similar` returns the closest earlier cases with the answer given, the date and a similarity score; near-duplicates above a threshold are labelled "same question".
2. Campaign detection: several incoming requests within a window with near-identical text from different senders → one group; the clerk can answer the group from one draft.
3. Dashboard: cases by days left (overdue, 0–3, 4–7, later); counts by class and by letter type; median handling time by state; "frequent topics" (clusters of similar questions) as candidates for proactive publication, with an export of the list.
4. A "time saved" panel for the demo: per case, the time between registration and approved draft, compared with a manually entered baseline per document type (the baseline is a setting and is shown as an assumption).

Acceptance: on the synthetic archive the planted near-duplicates and the planted campaign are found; an unrelated request gets no "same question" label (negative control); dashboard numbers equal the numbers computed by a test query.

---

## WP-A9 — Security pack

Kind: think (review) · Model tier: top · Depends on: milestone M2 merged · Branch: `wp/A9-security`

Build and verify:
1. Injection test set (`apps/api/tests/security/injection/`): at least 20 hostile requests (direct instructions, instructions inside a quoted "attachment", role-play, encoded text, a request to reveal the system prompt, a request to mark the case as approved). Assert: every one is flagged; none changes the output schema; no state transition happens; no approval is created.
2. Access rules: for each route and role a test of allow or deny from a table.
3. Audit: tamper tests for insert, delete, modify.
4. Data handling: grep of logs and of every outbound call captured during the full test run for all synthetic identifiers (extends the canary test of WP-A2 to the whole system); check that exports and traces never contain token maps.
5. Dependency licences and known vulnerabilities report.
6. Accessibility: full scan plus a keyboard-only and a screen-reader smoke run of the main path; findings fixed or listed.
7. `docs/02-architecture/threat-model-check.md`: for each threat of `security-and-privacy.md`, the control, the test that proves it, and the residual risk in one line.

Acceptance: all tests in the fast gate; the threat-model table has no row without a test or an explicit "not covered, reason".

---

## WP-A10 — Public paste-a-request page (only if the jury must try the solution in a browser)

Kind: by spec · Model tier: middle · Depends on: M2 · Branch: `wp/A10-public`

Build: one page without login. A text box with three synthetic examples to click, a clear notice in Polish not to paste real personal data, a button "analyse". The response shows letter type, questions, classes with reasons and provisions, deadlines, the proposed document type and the first lines of a draft. Server side: rate limits per address, size limit, no persistence of the pasted text beyond the request, the pseudonymiser always on, the `local` or `mock` provider by default, `cloud` only if the owner sets it. Deployment note for the lead: a public address needs a host; options and the choice are recorded in the status file (owner's server, a tunnel from the laptop as a fallback, the recorded video as the last resort).

Acceptance: load test of 30 requests in a minute stays within limits and degrades with a polite message; a pasted synthetic identifier never reaches an outbound call (canary); the page passes the accessibility scan.
