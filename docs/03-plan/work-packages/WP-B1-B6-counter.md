# WP-B1 … WP-B6 — Module B: data once, forms pre-filled at the counter

> **After the task card (21 November, 11:25): not built for the task "Cyfryzacja formularzy".** That task asks for a converter from a form file to the partner's JSON: [`WP-F-forms-to-json.md`](WP-F-forms-to-json.md); why: [`../../01-product/coi-replan.md`](../../01-product/coi-replan.md). This file stays as the specification of the counter product (the owner's vision) and as a source of methods.

Built only after the Module A gate (M2) passes, or as the main track if the owner chooses the "Cyfryzacja formularzy" task; in that case WP-B6 and WP-B1 come first and are the centre of the demo. Each package has its own branch, worktree and status file.

Read first for all of them: `AGENTS.md`; `docs/02-architecture/design-notes.md` §1 and §6; `research/09-lessons-from-2022-prototype.md` (every rule there came from real use); `research/03b-form-anatomy-and-canonical-profile.md`; and, where named, `research/04-…` (identity sources) and `research/06-…` (libraries).

---

## WP-B1 — Canonical profile and forms engine

Kind: think · Model tier: top · Depends on: WP-00 · Branch: `wp/B1-forms-engine`

Goal: two real forms of the city hall come out as PDFs that are indistinguishable from the published templates except for the filled values.

Build:
1. `data/canonical-profile.schema.json` (start from the research file): case → persons → roles; identity document; addresses; contact; family relations; proxy; property owner; business; vehicle; real estate; case parameters. Validation: PESEL checksum and agreement with birth date and sex, NIP, REGON, postal code, identity-card number check digit, account number checksum. Every field value can carry provenance (`self_declared`, `mrz`, `chip`, `confirmed_by_clerk`) and a time.
2. Form descriptor format (start from `data/form-descriptor.example.json`): bound to the SHA-256 of the template file; `legal_status` (statutory template with its act, or local auxiliary); fields with canonical path, page, box in PDF points, kind (text, boxed characters, check box, date parts, signature line), font, size range, maximum length, transform (upper case, date format, split into boxes), `who_fills`, per-office overrides.
3. Fill: the template page is the background, values are drawn into boxes; automatic font fitting down to a minimum readable size, below which an overflow error is returned; boxed fields are drawn character by character on a measured grid; check boxes as vector marks; Polish diacritics from an embedded open font; no flattening of content the template already has. If the template has form fields, fill them and flatten; otherwise overlay. Output in memory only.
4. Template cache: templates are downloaded from the catalogue address into `data/forms-cache/` (git-ignored) and verified against the hash; a changed hash disables the descriptor with a clear message.
5. Bundles as data (`data/forms/bundles/*.json`): situation id and Polish title, forms, copies per person role, fees text, attachments checklist, print options (duplex), notes such as "no paper form: the clerk generates it in the state register"; each rule has a source address and a date.
6. Visual regression: render the filled PDF and the blank template to images; outside the union of field boxes the difference must be zero (within an anti-aliasing tolerance); inside each box there must be ink when a value was given. Run in the fast gate for each descriptor.
7. Descriptors for two forms chosen from the research (one with boxed characters, one free-text), each with a synthetic filled sample checked by the regression test.

Acceptance: both forms pass the visual regression; a 40-character surname triggers font fitting and then an overflow error at the limit, never a silent cut; a template with a different hash is refused (negative control); nothing is written to disk during fill (test with a read-only working directory).

---

## WP-B2 — Visitor page and encrypted QR handoff

Kind: think (security) · Model tier: top; independent review · Depends on: WP-00 · Branch: `wp/B2-handoff`

Build:
1. `apps/visitor-pwa`: installable web page, works offline after first load; languages Polish, Ukrainian, English; one field per row; large touch targets; the profile is stored only on the device (browser storage, encrypted with a key derived from a PIN chosen by the visitor); "delete my data" always visible.
2. Flow at the desk: scan the QR code shown on the clerk's screen (or type the short session code); the page fetches from the relay which fields the chosen case needs; the visitor sees exactly what will be shared and confirms; the page encrypts and uploads.
3. Cryptography: the office side creates a session key pair; the QR code carries the session id and the public key in the URL fragment; the phone encrypts with HPKE (base mode, P-256, HKDF-SHA256, AES-256-GCM) using a maintained library on both sides, or ECDH + HKDF + AES-GCM from the platform's cryptography API if the research recommends that instead; associated data binds the session id and the origin. Both screens display a short code derived from the exchange; the clerk compares it aloud before opening the record.
4. `apps/relay`: a tiny service that stores ciphertext in memory with a time-to-live (default 15 minutes), has no logs of bodies, rate limits, and deletes on fetch, on withdrawal and on expiry. The office server pulls by outbound requests only (long polling or server-sent events).
5. Office side: decrypts in memory; the session and its data are destroyed on print, on "delete now" and on expiry; deletion writes an audit event without personal values; daily counters only (sessions, forms printed).
6. Abuse: a QR code is single-use and short-lived; a second upload to the same session is rejected; the page shows the office's name and the origin so that a planted QR code leading elsewhere is noticeable; the clerk's screen never shows the QR code and personal data at the same time.

Acceptance: a test proves the relay never holds plaintext (property test over its storage and logs with synthetic identifiers); expiry and each deletion path are tested; a tampered ciphertext or a wrong session id fails to decrypt (negative controls); the page passes the accessibility scan and works at 320 px width; end-to-end test with a headless phone-sized browser and the clerk side.

---

## WP-B3 — Clerk counter view

Kind: by spec · Model tier: middle · Depends on: WP-B1, WP-B2 · Branch: `wp/B3-counter`

Build (`apps/clerk-web/src/features/counter`): "new visitor" shows the QR code; waiting list of sessions with the comparison code; opening a session shows the persons of the case; **large-print verification screen**: each field in very large type next to its provenance, with "confirm" and "correct" (the 2022 lesson: the clerk checks against the document before anything prints); choice of a bundle, or free-text description that calls the bundle recommender; list of forms with copies per person; findings of the checker inline; print preview with **the person's name in large type** and a confirmation step; print all or one; back-edit-reprint without losing the session; "delete now"; countdown of the session's time-to-live. Sticky actions, keyboard operation, highlighted incomplete fields.

Acceptance: end-to-end test of the full path with a synthetic family of four; the wrong-person guard is tested (changing the selected person changes the previewed name and the job's person id); all 2022 workstation rules of the research file §6 are ticked in the status file.

---

## WP-B4 — Identity sources

Kind: by spec · Model tier: middle · Depends on: WP-B2 · Branch: `wp/B4-identity`

Build: one interface `IdentitySource` with implementations: (1) typing; (2) camera reading of the machine-readable zone in the browser on the device, using live video frames in memory (no file input, no image stored or uploaded), check digits validated, fields shown for correction; documents without such a zone fall back to typing; (3) `apps/bridge`: a local service on the clerk's workstation bound to `127.0.0.1` with a pairing token, exposing `status`, `scan`, `print`; a simulator implementation returns synthetic reads; the adapter for the real reader is specified in the research file and is implemented only when the vendor SDK and licence files are present in the git-ignored `vendor-sdk/` folder; authenticity-check results are passed through as `passed`, `suspicious`, `failed`, `not_checked`; (4) government wallet adapter: a simulator that plays the relying-party flow described in the research, clearly labelled as a simulation in the UI.

Acceptance: check-digit tests for the standard document formats including invalid cases; the camera path keeps no image (test inspects storage and network); the bridge refuses calls without the token and from non-local origins; the simulator drives the counter view end to end.

---

## WP-B5 — Form checker

Kind: think · Model tier: top · Depends on: WP-B1, WP-A2 · Branch: `wp/B5-checker`

Build: deterministic rules first: checksums, required fields per descriptor, date logic (terms from the service cards), consistency between persons (child's surname and address defaults, marital status and grammatical sex, proxy fee exemption by relation), document-type-driven fields, bundle completeness (one form per person where required), channel rules from the service cards. Then a model check on local or pseudonymised data for free-text reasons and for likely recognition artefacts (0 and O, lost diacritics). Output: findings with severity (`blocker`, `warning`), field path, message in Polish, suggested fix; nothing is changed silently. Rules are data with a source and a date.

Acceptance: a table of at least 30 seeded mistakes, each caught with the right severity; a clean case yields no finding (negative control); the model step runs with the mock provider offline.

---

## WP-B6 — Form onboarding assistant ("digitise a form")

Kind: think · Model tier: top · Depends on: WP-B1 · Branch: `wp/B6-onboarding`

Goal: an office worker uploads a blank PDF form and, minutes later, has a reviewed descriptor, a generated accessible web form and a test print on the original template.

Facts from the form analysis that shape the method (`research/03b`): only one of 32 real forms has form fields, so layout analysis is the main path; the ministry's residence form has a broken text layer, so positions must come from vector geometry (rectangles and lines), not from text search; character boxes are runs of equal rectangles with a constant pitch (about 12.26 pt on that form); many templates are DOC or RTF and must first be converted to PDF and the result checked by a person; one template is Letter-sized.

Method: (1) read vector rectangles and lines from the page with a permissively licensed library; group runs of equal boxes into one boxed field; treat long horizontal rules and dotted lines as text fields; small squares as check boxes. (2) Render the page to an image and give the model the image plus the list of candidate boxes with ids; ask for a Polish label, kind, canonical-profile path or "case-specific", validation and `who_fills` per id, as structured output; never ask the model for coordinates. (3) Show the proposal on the page for correction by dragging. (4) Golden test: compare the proposal for the residence form with the hand-measured descriptor `data/form-descriptor.example.json` (share of fields found, overlap of boxes) and print the numbers; they feed the deck.

Build: analysis of the blank PDF (form fields if present; otherwise layout analysis of text, lines and boxes to propose field boxes); a model proposes for each field a Polish label, a kind, a canonical-profile path or "case-specific", validation, `who_fills`; blank public forms are `PUBLIC` data, so any provider may be used; a review screen overlays the proposed boxes on the page for correction by dragging; publishing writes the descriptor bound to the template hash and runs the visual regression test with a synthetic profile; a generated web form (grouped by person and section, only fields not already in the profile) is produced from the descriptor; a report states the share of fields mapped to the profile.

Acceptance: on three forms of different kinds from the catalogue the assistant proposes at least the share of correct field boxes recorded in the status file, and after human correction all three pass the regression test; time from upload to a passing test print is measured and reported; the generated web form passes the accessibility scan.
