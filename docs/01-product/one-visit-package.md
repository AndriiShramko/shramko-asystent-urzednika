# One visit, complete set: the product as the owner wants it shown

Answers requirements R33–R43 (the owner's third brief, 21 November 2026, morning; [`../00-brief/requirements.md`](../00-brief/requirements.md) section F). It does not replace [`scope-decision.md`](scope-decision.md): the track is still B, the forms product for "Cyfryzacja formularzy", and the alternative is still Track A. It changes **what the second half of the demo is about** and adds three small work packages ([`../03-plan/work-packages/WP-B7-B9-one-visit.md`](../03-plan/work-packages/WP-B7-B9-one-visit.md)). Facts used here come from [`research/12`](../../research/12-one-visit-package-addendum.md), [`research/03b`](../../research/03b-form-anatomy-and-canonical-profile.md), [`research/04`](../../research/04-mobywatel-identity-once-only.md), [`research/09`](../../research/09-lessons-from-2022-prototype.md) and [`research/11`](../../research/11-coi-form-digitisation.md).

## 0. The idea in one paragraph

A resident says what they need. The system answers with the **complete set** for that need: every form, for every person, with the attachments to bring and the fees. The resident's data are already on their phone (later: in mObywatel) and are handed over once, by a QR code. The clerk types nothing: a reading of the identity document is compared with the handed-over data automatically, and the screen shows **only the fields that need a human look**. One click prints the whole set on the original templates, ready to sign. Behind this stands the part the partner asked for: an AI step that turns any paper or file form into such a service in minutes, with a person approving. In Polish, for the jury: **„Od potrzeby do podpisu: jedna wizyta, komplet wniosków."**

Why this is the right frame for the forms task: the task text says "droga od potrzeby do wygodnej usługi online" and the partner's announcement says "narzędzie AI, które zmieni formularze w zwinne cyfrowe usługi publiczne" (research/12 item 1). Part one of the demo shows the tool; part two shows that what the tool produces is a service a resident and a clerk can really use, from the need to the signature.

## 1. The journey

Stage 0 happens once per form, stage 1 once per person; stages 2–5 are one visit.

| # | Stage | Who, where | What happens | Personal data leave the phone? | Built by |
|---|---|---|---|---|---|
| 0 | **A form becomes a service** | office worker, laptop | A blank PDF, DOCX, RTF or XLSX is uploaded; AI proposes the fields and their meaning; the person corrects and publishes; the description yields the online form, the print on the original template and the checks | no personal data at all | WP-B6, WP-B1 |
| 1 | **Data once** | resident, own phone, at home or in the corridor | The profile is created once: the browser offers its saved name, address, e-mail and phone in one tap; the identity document can be read with the camera; the rest is typed. The profile stays on the phone, locked with a PIN | no | WP-B2, WP-B4, **WP-B9** |
| 2 | **From need to set** | resident before the visit, or clerk at the counter | The matter is chosen (as when booking a visit) or described in one sentence; the assistant proposes the set: forms per person, attachments to bring, fees, and what the state register generates without paper; up to three clarifying questions; an answer changes the set at once | no (the description carries no identifying data) | bundles in WP-B1, **WP-B7** |
| 3 | **Handoff** | resident and clerk, at the counter | The clerk's screen shows a QR code; the phone shows exactly which fields this set needs; the resident confirms; the fields travel encrypted to the office and nowhere else | yes: only the needed fields, for minutes | WP-B2 |
| 4 | **Check by exception** | clerk | The identity document is read (camera, reader, or typed); the system compares it with the handed-over data and runs the rules and the model check; the screen shows "zgodne z dokumentem" collapsed and "do sprawdzenia" open; the clerk confirms the person and the open fields | in office memory only | WP-B3, WP-B4, WP-B5, **WP-B8** |
| 5 | **Print and sign** | clerk and resident | The whole set prints on the original templates, the person's name in large type before each job; the resident signs; the office-side data are destroyed; only counters remain | destroyed | WP-B1, WP-B3 |

Rules that do not change: AI proposes, a clerk approves (AGENTS rule 7); synthetic data only; the profile is the resident's, the office holds data for minutes; nothing in the process depends on the system being up (paper fallback).

## 2. Pains and answers

The owner said he does not know yet what hurts clerks most ("я ещё не знаю, какие там проблемы"). The table separates what is evidenced from what must be asked on site ([`../05-hackathon/ONSITE-INTAKE.md`](../05-hackathon/ONSITE-INTAKE.md) §3b). A pain without evidence is said as an observation, never as a number.

| Who | Pain | Evidence and label | Answer in the product |
|---|---|---|---|
| Resident | Writes the same data on every form | identity, address and contact block on 14 of 14 analysed person forms; one profile fills about 55–60 % of fields of simple forms (own estimate, research/03b) | Stage 1 and 3: data once, every form of the set filled |
| Resident | Does not know which forms and attachments the matter needs; a missing one means another round | one matter lists several files (card UMB55: two registration forms, owner's statement, power of attorney, certificate request, multilingual form); an incomplete application leads to a call with a term of at least seven days (KPA art. 64 § 2, research/12 item 6); frequency: **unknown, ask** | Stage 2: the complete set with the list "co zabrać", shown before the visit |
| Resident | First-time data entry is a chore | the owner's observation | Stage 1: saved browser data in one tap, document read by camera |
| Clerk | Helps to fill in and re-types forms by hand | the owner's observation in offices and in Opole 2022 (research/09); 81 % of 6,093 surveyed officials name automation of routine tasks as the main benefit of AI (NASK, research/07) | Stage 3–5: the clerk types nothing |
| Clerk | Compares data with the document letter by letter; slips happen (0 and O, lost diacritics, the wrong person's printout in 2022) | research/09 §2; research/06 | Stage 4: automatic comparison, exceptions only; name in large type before print |
| Office | Queues at peaks | over 250,000 PESEL numbers in the first week of March 2022 (research/11 §6) | Data entry moves out of the counter: at home or in the queue |
| Office | Forms are not ready for automation | 275 service cards, 676 files mirrored, about half of them word-processor files, 1 fillable PDF among 32 analysed (research/03, 03b, `data/demo-forms.md`) | Stage 0: AI onboarding with a person approving |
| Makers of e-services | Converting forms by hand does not scale | 179 of 344 mapped national services digitised; the planned form generator targets 30–50 local governments in 2026 (research/11); abroad: 70 years for 11 teams, document forms 8 minutes slower to process (GDS, research/11 §5) | Stage 0 output is an open description that can feed the state's generator |
| Everyone | A shared database of people is not lawful | scope-decision §4 | Data stay with the person; what offices share is the description of forms |

## 3. What already existed and what is new

| Wish in the brief | State before this brief | New |
|---|---|---|
| Data stored in advance, handed over at the counter | Specified: profile on the phone, QR handoff, minutes of lifetime (R4, R5, WP-B2) | nothing; say it first in the demo |
| The assistant proposes the whole set | Specified: bundles as data, recommender prompt, free-text box in the counter view (R16, WP-B1, WP-B3) | The set carries attachments-to-bring and fees for the resident; clarifying answers change the set by rules, visibly (WP-B7) |
| The intent is known from the booking | not covered | "Prepare your visit" page; the intent travels with the handoff; the clerk opens the session with the set already proposed (WP-B7) |
| The clerk only checks, and only what matters | Partly: large-type screen showing every field with provenance (WP-B3) | Check by exception: three groups, matched fields collapsed (WP-B8) |
| Scanner compares instead of the human eye | Partly: identity sources and provenance (WP-B4) | A comparison engine between the document reading and the declared data, with normalisation rules (WP-B8) |
| The system re-checks itself | Specified: checker, rules first, then model (R8, R13, WP-B5) | its findings feed the "to check" group |
| First entry pre-filled from the browser | not covered | `autocomplete` tokens on every profile field from the first commit; optional contact-card shortcut on Android (WP-B9) |
| The profile app should be mObywatel | Researched: the function "Przekaż instytucji" exists, no public interface (research/04) | The form description doubles as the data request (§5 below); still simulated |
| A document that explains pains and scale without a presenter, plus a richer web page | Deck of 8 slides and its PDF with captions | A reading version of ten pages and its web page: [`../05-hackathon/presentation/storyboard-pakiet.md`](../05-hackathon/presentation/storyboard-pakiet.md) |

## 4. Check by exception: the rules

The 2022 lesson stands: nothing prints before the clerk has checked against the document. What changes is who does the letter-by-letter part.

1. **Three groups on the verification screen.**
   - *Zgodne z dokumentem (n)*: fields where the document reading equals the declared value. Collapsed; one tap expands them in large type.
   - *Do sprawdzenia (k)*: (a) fields where reading and declaration differ, both values side by side; (b) fields this set needs that the document cannot confirm (the address is not on the Polish identity card; parents' names and place of birth are not in the machine-readable zone); (c) findings of the checker. Open, in large type, each with "potwierdź" or "popraw".
   - *Wypełnia urzędnik lub puste* (office section, signature): listed, not editable by the resident.
2. **Identity fields never pass on a declaration alone.** Surname, given names, date of birth, document number and PESEL need a document reading that matches, or the clerk's explicit confirmation. Without any reading the screen falls back to the full large-type check of WP-B3.
3. **The clerk still confirms the person.** One explicit action, "Tożsamość potwierdzona: okazano dokument", is required even when every field matches. The system compares characters; a person compares a face with a photo.
4. **Normalisation is visible.** The machine-readable zone has no Polish letters and cuts long names. "ŁUKASZ" against "LUKASZ" is *zgodne po transliteracji* and is shown as such in the collapsed group; a real difference of a letter is a mismatch. PESEL counts as unconfirmed unless a reader returns it (research/12 item 10).
5. **Provenance is kept per field** (`self_declared`, `mrz`, `chip`, `confirmed_by_clerk`) and written to the audit event without the values.
6. **Nothing is corrected silently.** A proposed fix is applied only by the clerk's tap.
7. **Counters for the pitch**, measured in the demo: fields in the set, fields typed by the clerk (target 0), fields the clerk had to look at, seconds from scan to print.

## 5. The profile, and why mObywatel is its natural home

Today the profile is a page on the resident's phone, because there is no public interface to the government wallet. The architecture already has the adapter and labels it as a simulation. The message for the partner, to be said as a proposal:

- mObywatel already lets an institution show a QR code and receive data the citizen approves ("Przekaż instytucji", research/04).
- What a local office lacks is the list of fields a given paper form needs. **The description produced in stage 0 is exactly that list**: every field of every form is mapped to a path of one documented profile schema. A set of forms therefore yields a ready data request, "this matter needs these twelve fields".
- So the route from a paper form to "fill it from the wallet" is: digitise the form, publish its description, and the description tells the wallet what to ask for. Our own QR handoff runs the same pattern today with our own page as the wallet.

Open question for the COI stand (ONSITE-INTAKE §3a): can an institution in that function ask for a per-case list of fields, and which attributes are available?

## 6. Intent before the visit, without an integration

The city's booking calendar already makes the resident choose the matter (research/12 item 4). The design uses this without touching the booking system:

- A public page "Przygotuj wizytę" in the visitor app: pick the matter from the catalogue or write one sentence; answer up to three questions; see the set, the attachments to bring and the fees; fill what the profile lacks.
- The result, `intent`, is stored on the phone only: the bundle id, the answers, the composition of the case (roles and counts, no names).
- At the counter the phone scans the clerk's QR code as always; the encrypted payload carries the `intent` next to the fields. The clerk's session opens with the set already proposed and marked "wybrane przez mieszkańca". The clerk can change an answer; the set is recomputed by the bundle rules and the phone is asked only for the newly needed fields.
- What the booking system would add later is one link in its confirmation message leading to that page with the matter pre-selected. In the demo this link is a proposal on a slide.

## 7. What the jury sees now (delta to the demo script)

Part one is unchanged: a form never seen before becomes a service (WP-B6). Part two becomes "from need to signature":

1. Resident, phone: "Przygotuj wizytę" → "Chcę zameldować siebie i dziecko" → the set appears: two forms, what to bring, fee "bezpłatnie". The profile already exists (created earlier with one tap of saved browser data; show that tap once if time allows).
2. Clerk: "Nowy interesant", QR code. The phone lists the fields this set needs; confirm.
3. Clerk's session opens with the set proposed by the resident. The clerk asks one question ("mieszkanie własne czy wynajmowane?"), changes the answer, the set changes on screen.
4. The clerk reads the identity document (camera on a synthetic specimen, or the reader simulator). Screen: "12 pól zgodnych z dokumentem" collapsed; "do sprawdzenia: 2": the address (not on the document) and one seeded slip caught by the checker. Confirm, correct, "Tożsamość potwierdzona".
5. "Drukuj komplet": the forms on the original templates, one per person; "dane usunięte".
6. Counter on screen: fields in the set, typed by the clerk: 0, looked at by the clerk, seconds.

The detailed steps are in [`../05-hackathon/demo-script-formularze.md`](../05-hackathon/demo-script-formularze.md), section "Part two, extended".

## 8. What we do not claim

- No integration with the city's booking system, with mObywatel, with state registers or with the office's case system. Each is shown as a simulation or a proposal and named so.
- No number for visits saved, time saved in a real office or share of incomplete applications: nobody measured them. Only what the demo measured.
- No "the clerk no longer checks": the clerk checks less by hand and confirms the person always.
- No reading of the address or of PESEL from the machine-readable zone.
- No automatic import of browser data: the browser offers, the person accepts.

## 9. Order of value if time is short

The loop of M1 first (WP-B1, WP-B2 with the `autocomplete` tokens, WP-B3), then WP-B6. After that, in this order: the set with attachments and one clarifying question (WP-B7 items 1–3), the comparison and the three groups (WP-B8), the "prepare your visit" page (WP-B7 items 4–5), the contact-card shortcut (WP-B9 item 3). Each of them is small because the data model and the screens exist; none of them may delay the M2 gate.
