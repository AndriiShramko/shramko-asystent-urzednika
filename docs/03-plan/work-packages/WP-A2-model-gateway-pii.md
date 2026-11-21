# WP-A2 — Model gateway and personal-data service

Kind: think (security) · Model tier: top, high effort; independent review mandatory · Depends on: WP-00 · Branch: `wp/A2-gateway-pii` · Milestone: M1

## Goal

One door for every model call, with a policy that makes it impossible to send raw personal data to an external provider, and a service that detects and pseudonymises personal data in Polish text.

## Read first

1. `AGENTS.md` (rules 1, 8, 9)
2. `docs/02-architecture/design-notes.md` §1, §4, §5
3. `research/05-rodo-ai-act-security-requirements.md`: TL;DR and the section on model providers (if the file is not there yet, proceed with the defaults below and note it)

## Build

1. `llm/gateway.py`: `complete(task, messages, schema=None, data_class)`. `data_class` is `PUBLIC` or `PERSONAL` and is a required argument. Providers: `mock` (recorded answers keyed by task and input hash, with a recorder mode), `local` (OpenAI-compatible HTTP endpoint, address from settings), `cloud` (Anthropic API; model name from settings; no model name hard-coded in callers).
2. **Policy, enforced inside the gateway:** `PUBLIC` → any provider. `PERSONAL` → `local`, or `cloud` only through the pseudonymiser: the gateway itself pseudonymises the input, calls the provider, re-identifies the output. A caller cannot bypass this; there is no parameter to switch it off. Provider choice per task comes from configuration (`llm.tasks.<task>.provider`).
3. Structured output: when `schema` is given, validate the provider's answer against it; one repair attempt; then a typed failure. Timeouts, bounded retries, a per-request cost and latency record (no content) for the dashboard.
4. `pii/detect.py`: layered detection. Deterministic recognisers with checksum validation where one exists: PESEL, NIP, REGON, identity-card and passport numbers, bank account numbers, land-register numbers, licence plates, phones, e-mails, postal codes with street addresses. Named entities (persons, places, organisations) through a Polish NER model with a permissive licence if installed (the Polish spaCy model is GPL-3.0 and must not enter the core; see `research/07` for Apache-2.0 and CC BY options and for the recogniser framework under MIT), otherwise a rule-and-dictionary fallback that errs on the side of masking capitalised name-like sequences. Return spans with type and confidence.
5. `pii/pseudonymise.py`: replace spans with typed, numbered tokens (`[OSOBA_1]`, `[ADRES_1]`, `[PESEL_1]`); the same value gets the same token within one case; inflected forms of one surname map to one token where the detector can tell; the mapping lives in memory of the office side and is never serialised into logs or outbound calls. `reidentify(text, mapping)`.
6. Trace for the UI: per call, store provider, data class, the text actually sent (already pseudonymised), counts of entities by type. Exposed by `GET /cases/{id}/analysis/trace` and by `POST /pii/pseudonymise`.
7. **Canary test** (part of the fast gate): feed inputs containing synthetic identifiers through every task with the `cloud` provider replaced by a capturing fake; assert that no captured outbound payload contains any planted value, including inside URLs and headers.
8. Prompt-injection hygiene helpers used by all callers: `wrap_untrusted(text)` puts outside text into a delimited data block with a fixed preamble; `looks_like_instruction(text)` returns flags for the clerk (phrases addressing a model, role-play requests, "ignore previous", encoded blobs).

## Acceptance

- [ ] Detection test set of at least 60 synthetic Polish sentences (names in different grammatical cases, identifiers with and without separators, addresses): recall for identifiers with checksums 100 %, for names at least the level recorded in the status file; false negatives are listed.
- [ ] Round trip: pseudonymise then re-identify returns the original text for all test inputs.
- [ ] Canary test passes; breaking the policy on purpose in a scratch branch makes it fail (negative control, recorded).
- [ ] A `PERSONAL` call with provider `cloud` and the pseudonymiser monkey-patched away raises instead of sending.
- [ ] The mock provider makes the whole test suite run with no network.
- [ ] `tools/gate.sh fast` passes.

## Out of scope

Prompts for specific tasks (WP-A4, WP-A5), redaction of documents (WP-A7).
