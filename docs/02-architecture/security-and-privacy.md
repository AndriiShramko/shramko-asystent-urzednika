# Security and privacy

"Bezpieczny" is one of the two adjectives in the task sentence. This page is the short version a builder implements and a juror can check. The legal analysis with sources and the full list of 26 controls mapped to their legal basis is in [`research/05-rodo-ai-act-security-requirements.md`](../../research/05-rodo-ai-act-security-requirements.md) §6; the trust zones and data flows are in [`design-notes.md`](design-notes.md) §1.

## Principles

1. **The office stays the controller; the tool is an instrument.** Legal basis for handling a request or a form is the office's legal obligation or public task, never consent. A supplier acts only under a processing agreement. The office's data protection officer reviews the deployment and the impact assessment.
2. **Least data, shortest time.** A counter visitor's full profile never leaves their phone; only fields needed by the chosen forms are sent, end-to-end encrypted, kept in memory for minutes. Public-information cases are kept as long as the office's file rules require, encrypted.
3. **No copies of identity documents.** Reading the data in front of the person is what a clerk already does; the image is never stored or sent. No face matching.
4. **A person decides.** The assistant drafts and cites; a named clerk approves; a lawyer reviews decisions. No profiling, no scoring, no evaluation of a person's eligibility: this also keeps the system outside the high-risk class of the AI regulation as analysed in the research.
5. **Models see masks.** Text with personal data goes to a model inside the office's control, or to an external model only after pseudonymisation. Pseudonymised text is still personal data for the office; the gateway is a safeguard, not an exemption, so a processing agreement with any external provider is still required.
6. **Everything that happens is recorded, without the personal values.**

## Threats and controls

| # | Threat | Control | Proven by | Package |
|---|---|---|---|---|
| T1 | Personal data sent to an external model | Policy inside the gateway by data class; pseudonymiser that callers cannot bypass | Canary test on every outbound call | WP-A2, WP-A9 |
| T2 | A request or attachment carries instructions for the model | Outside text only inside a delimited data block; structured output; no tool with side effects reachable; instruction-like text flagged for the clerk | Injection test set: all flagged, no state change | WP-A2, WP-A4, WP-A9 |
| T3 | The model invents a legal basis or a fact | Citation check by code against the stored act; placeholders for facts only the office knows; comparison of numbers, dates and names in a draft with its inputs | Negative controls in WP-A5; evaluation set | WP-A3, WP-A5 |
| T4 | A wrong document type or a missing mandatory element | Document types and elements as data; mandatory-element check; decisions cannot be exported without review | Element-removal tests | WP-A5 |
| T5 | A deadline is missed or miscounted | Pure, tested date functions; both dates shown at registration; warnings | Dated test cases including holidays | WP-A1 |
| T6 | A clerk sees or changes what their role does not allow | Role checks on every route; API only, no direct database access | Allow and deny table tests | WP-A1, WP-A9 |
| T7 | The audit trail is altered | Append-only events with a hash chain; verification endpoint | Tamper tests | WP-A1, WP-A9 |
| T8 | Personal values in logs, traces, exports, screenshots, bug reports | Logs carry ids only; traces carry pseudonymised text; synthetic data in tests and demos; pre-commit scan | Log grep for synthetic identifiers during the full test run | WP-00, WP-A9 |
| T9 | Disclosure of personal data in a released document | Detection and masking proposals; masks burnt into rasterised pages; redaction log; reminder about the partial refusal | Text extraction from the output finds nothing | WP-A7 |
| T10 | The relay or the network reads a visitor's data | End-to-end encryption to a session key shown in the QR code; relay stores ciphertext in memory with a time-to-live | Property test: no plaintext in relay storage or logs | WP-B2 |
| T11 | A planted QR code or a mixed-up visitor | QR code only on the clerk's screen, single use, minutes; short comparison code on both screens; office name and origin on the phone page | Wrong session and tampered ciphertext fail | WP-B2, WP-B3 |
| T12 | The wrong person's form is printed | Print job bound to a person id; name in large type before printing; confirmation | End-to-end test of the guard | WP-B3 |
| T13 | An identity document image is kept | Camera frames only in memory on the device; no file input; nothing uploaded | Storage and network inspection test | WP-B4 |
| T14 | Self-declared data is treated as verified | Provenance on every field; clerk confirmation against the document before printing | UI test: unconfirmed fields are marked | WP-B1, WP-B3 |
| T15 | Data outlives its purpose | Time-to-live, delete on print and on request, deletion events in the audit trail, daily counters only | Expiry and deletion tests | WP-B2 |
| T16 | A changed template silently breaks a form | Descriptor bound to the template's hash; mismatch disables it | Negative control with a different hash | WP-B1 |
| T17 | Abuse of public pages | Rate limits, size limits, nothing stored beyond the request | Load test | WP-A10, WP-AB1 |
| T18 | A dependency brings an incompatible licence or a known vulnerability | Licence and vulnerability report in the gate; no copyleft libraries in the core | Report in the status file | WP-00, WP-A9 |
| T19 | Excluded users | Accessibility as an acceptance criterion: keyboard, contrast, labels, scalable text, large-print verification | Automated scan plus a keyboard run | every UI package |

## Data classes and where they may go

| Class | Examples | Storage | May be sent to |
|---|---|---|---|
| Public | legal texts, blank forms, public bulletin pages, service cards | repository, knowledge base | any model provider |
| Personal, case | request text with names, applicant contact, drafts | office database, encrypted; tokens elsewhere | local model; external model only pseudonymised and under a processing agreement |
| Personal, counter session | visitor profile fields | memory of the office server, minutes | local model only; rules first |
| Secret | keys, licence files, vendor SDK | the machine, outside git | nowhere |

## What a juror can see in five minutes

The masked text the model received; the citation check blocking an invented provision; the warning on a letter that contains instructions; the approval step and the audit entry; the verification of the audit chain; the statement of what is simulated. For the counter module: the comparison code, the countdown of a session and the "delete now" button.

## Before production (not part of the hackathon)

The office's own security review, a data protection impact assessment, an entry in the record of processing, a processing agreement with every supplier and model provider, an accessibility audit and declaration, staff training on working with AI drafts, and a decision of the data protection officer on reading document chips. The research lists the open legal points that need the office's lawyers: [`research/05`](../../research/05-rodo-ai-act-security-requirements.md), "Open questions".
