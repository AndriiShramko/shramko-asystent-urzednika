# WP-B7 … WP-B9 — One visit, complete set

> **After the task card (21 November, 11:25): not built for the task "Cyfryzacja formularzy".** That task asks for a converter from a form file to the partner's JSON: [`WP-F-forms-to-json.md`](WP-F-forms-to-json.md); why: [`../../01-product/coi-replan.md`](../../01-product/coi-replan.md). This file stays as the specification of the counter product (the owner's vision) and as a source of methods.

Three small packages added by the owner's brief of 21 November (R33–R43). Read first: `AGENTS.md`; [`docs/01-product/one-visit-package.md`](../../01-product/one-visit-package.md) (the whole idea, the rules of the check by exception, what is not claimed); [`research/12-one-visit-package-addendum.md`](../../../research/12-one-visit-package-addendum.md) (facts). They extend WP-B1…B5 and never replace them. None of them may delay the M1 or M2 gate: start them only when the loop of M1 runs.

Two lines of this file apply to **earlier packages from their first commit** (change requests, cheap now, expensive later):

- **WP-B2:** every field of the profile form carries the correct `autocomplete` token, a programmatic label and a stable `name` (table in WP-B9 item 1). The payload of the handoff has an optional `intent` object (WP-B7 item 4).
- **WP-B1:** a bundle file carries `attachments_to_bring`, `fees`, `questions` and `rules` as specified in WP-B7 item 1; a descriptor field keeps `canonical_path` so that the list of fields a set needs can be computed.

---

## WP-B7 — From need to set (package recommender and "prepare your visit")

Kind: by spec · Model tier: middle · Depends on: WP-B1 (bundles), WP-B3 first cut · Branch: `wp/B7-need-to-set`

Goal: one sentence or one chosen matter yields the complete set of forms with attachments and fees; a clarifying answer changes the set at once; the resident can do this before the visit and the clerk finds the set already proposed.

Build:
1. **Bundle data** (`data/forms/bundles/*.json`, owner WP-B1; this package adds fields and two more bundles): `id`, Polish `title`, `matter_keywords`, `forms[]` with `form_id`, `per` (`case`, `person`, `adult`, `child`) and `when` (a rule over answers), `questions[]` with `id`, Polish text and closed answers, `attachments_to_bring[]` with `when`, `fees[]` with `when`, `no_paper_note`, and for every item `source_url` and `source_date`. Bundles for the demo: "zameldowanie na pobyt stały: rodzic z dzieckiem" from card UMB55, and one from the vehicle department (card UMB202 family) or any second matter with at least two forms. Every rule comes from the text of the service card; a rule without a source is not shipped.
2. **Resolver** (`apps/api/app/modules/bundles/`): pure function `resolve(bundle, answers, composition) -> set` returning forms with copies per person, attachments, fees, notes, the still-open questions and `needed_fields` (the union of `canonical_path` of all fields with `who_fills = visitor`). Deterministic; unit-tested; no model inside.
3. **Recommender**: `POST /bundles/recommend` takes a description without identifying data and the composition; the model (data class `PUBLIC`: mock, local or cloud) maps it to at most three bundle ids with one-sentence reasons and may ask up to three of the bundle's own questions; it can only return ids that exist ([`prompts/bundle-recommender-system.md`](../../../prompts/bundle-recommender-system.md)). With the mock provider a keyword match over `matter_keywords` gives the same contract, so the demo works offline.
4. **Intent on the phone** (`apps/visitor-pwa/src/features/prepare/`): page "Przygotuj wizytę": choose a matter from the list or write one sentence; answer the questions; see the set, "co zabrać" and the fees; the profile fields this set needs and lacks are asked now. The result `intent = {bundle_id, answers, composition}` is stored on the device only and is added to the encrypted payload at the handoff.
5. **Clerk side** (`apps/clerk-web/src/features/counter/`, owner WP-B3; this package adds a panel): a session that arrives with an `intent` opens with the set marked "wybrane przez mieszkańca"; the clerk can change an answer or pick another bundle; the resolver recomputes; if new fields are needed the phone is asked for exactly those (a second, smaller confirmation on the phone). Without an intent the clerk types a sentence or picks a bundle, as specified in WP-B3.
6. **Counters** shown at the end of a session and exposed for the deck: forms in the set, persons, fields in the set, fields typed by the clerk.

Acceptance: resolver tests cover every `when` rule of both demo bundles; changing one answer changes the set in the UI without a reload (end-to-end test); a description containing an identifier pattern is rejected before it reaches a model (negative control, reuse the scan of WP-00); the recommender never returns an unknown id (test with a mock answer that contains one); the page works at 320 px and passes the accessibility scan; every rule in the two bundles has a source address and date.

Not in scope: any call to the city's booking system. The link from a booking confirmation is described in the concept document and shown on a slide only.

---

## WP-B8 — Comparison with the document and the check by exception

Kind: think · Model tier: top; independent review · Depends on: WP-B3 first cut, WP-B4 (at least typing and the reader simulator) · Branch: `wp/B8-crosscheck`

Goal: the clerk no longer compares characters; the screen shows only what needs a human look; nothing identity-related passes on a declaration alone. The seven rules are in the concept document §4 and are this package's specification.

Build:
1. **Comparison engine** (`apps/api/app/modules/crosscheck/`): input: the declared fields of one person and one document reading (from the machine-readable zone, from the reader bridge, or typed by the clerk) with its provenance; output per field: `match`, `match_after_transliteration`, `mismatch` (both values), `not_on_document`, `not_declared`. Normalisation as data, tested: upper case, Polish letters to the zone's alphabet, the zone's filler and truncation, date formats, document-number check digit. PESEL is `not_on_document` for a zone reading (research/12 item 10).
2. **Endpoint** `POST /sessions/{id}/persons/{pid}/crosscheck` (contract change: request it from the lead before coding); the result lives in session memory and dies with the session; the audit event carries field names, results and provenance, never values.
3. **Verification screen in three groups** (extends the large-type screen of WP-B3): "Zgodne z dokumentem (n)" collapsed, expandable in large type; "Do sprawdzenia (k)" open: mismatches side by side, fields the set needs that the document cannot confirm, checker findings; "Wypełnia urzędnik". Each open field has "potwierdź" and "popraw". A required action "Tożsamość potwierdzona: okazano dokument". Printing is disabled until group two is empty and that action is done.
4. **Fallback:** with no reading at all, the screen is the full large-type check of WP-B3 and says why.
5. **Counters:** fields matched automatically, fields the clerk looked at, corrections made.

Acceptance: a table of at least 20 seeded pairs (equal, transliteration only, one letter changed, swapped day and month, truncated long surname, wrong check digit, missing reading), each with the expected result; with a full match the print button is still disabled until the identity action (negative control); a self-declared surname with no reading can never reach `match` (negative control); no personal value appears in logs or audit events (scan); keyboard operation and screen-reader labels of the three groups pass the accessibility check.

---

## WP-B9 — Profile start without typing

Kind: by spec · Model tier: middle · Depends on: WP-B2 · Branch: `wp/B9-profile-start`

Goal: a first-time resident has a usable profile in under a minute.

Build:
1. **`autocomplete` tokens** on the profile form (the form itself is WP-B2's; this item is its change request and its test). One `<form>`, real `<label>` elements, `name` attributes, `inputmode` where it helps:

   | Profile field | Token |
   |---|---|
   | given name | `given-name` |
   | second name | `additional-name` |
   | surname | `family-name` |
   | date of birth | `bday` (or `bday-day`, `bday-month`, `bday-year` for split inputs) |
   | street, house and flat | `address-line1` (one field) or `street-address` |
   | postal code | `postal-code` |
   | town | `address-level2` |
   | country | `country` |
   | phone | `tel` |
   | e-mail | `email` |
   | PESEL, document number, parents' names, place of birth | none exists: `autocomplete="off"`, typed or read from the document |

   For a second person in the case (a child) use a `section-…` prefix so the browser does not copy the parent's data into the child's fields. The page never reads saved data itself; the browser offers them and the person accepts.
2. **A test** that loads the form headless and asserts the token of every field in the table (it doubles as evidence for the accessibility criterion on input purpose).
3. **Contact-card shortcut** (optional, behind feature detection `'contacts' in navigator`): button "Wstaw dane z mojej wizytówki" → `navigator.contacts.select(['name','email','tel','address'])` → fields filled for review. Android Chrome only; hidden elsewhere.
4. **Document read** for the identity block: the camera reading of the machine-readable zone from WP-B4, offered as "Zeskanuj dokument" next to the typed fields; provenance `mrz`.
5. **A first-run screen** that offers the three ways in this order: saved browser data, document, typing; and states where the data are kept ("tylko na tym telefonie").

Acceptance: the token test passes; with a browser profile that holds a saved address the form is filled by one accepted suggestion (manual check on one Android and one iOS phone, recorded in the status file); the contact shortcut is absent on a browser without the interface (negative control); nothing is sent anywhere during profile creation (network log empty in the end-to-end test).

---

## Ownership of new paths

`apps/api/app/modules/bundles/**`, `apps/visitor-pwa/src/features/prepare/**` → WP-B7 · `apps/api/app/modules/crosscheck/**` → WP-B8 · `apps/visitor-pwa/src/features/profile-start/**` → WP-B9. Panels inside `apps/clerk-web/src/features/counter/**` stay WP-B3's: B7 and B8 deliver them as sub-folders `counter/set/**` and `counter/verify/**` agreed with the lead.
