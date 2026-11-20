# Lessons from the 2022 prototype (Opole refugee help centre)

Source: the owner's two private Trello boards from March–April 2022 (194 cards, 143 of them closed) and his e-mail thread with the document-reader manufacturer. The prototype itself is gone; the cards are the surviving record. Everything below is anonymised: no names, no identifiers, no credentials. Read on 2026-11-20.

## TL;DR for builders

- This exact product idea already ran in production for about five weeks in 2022: volunteers in a refugee help centre in Opole filled Polish benefit applications for people arriving from Ukraine. The flow that survived contact with reality was: **the visitor types their own data on their phone while queuing, the clerk finds the visitor by the first characters of an identifier or name, picks the forms, prints, the visitor signs.**
- The decision to let visitors type their data was made **because a document scanner was not available yet**. It then turned out to be the faster path anyway. Scanning is an accelerator, never a prerequisite.
- Two thirds of all cards are about three things: **print layout breaking**, **defaults and conditional rules**, and **data linkage between people in one family**. Budget the work accordingly.
- Generating forms as HTML and printing from the browser failed repeatedly (overflow onto a new page, device-dependent layout, digits outside their boxes). **Fill the original PDF template; never re-typeset the form.**
- One bug printed the wrong person's form. Every print job must show the person's name in large type and must be confirmed.
- The team kept wanting to delete data fast ("delete after N hours", "delete everything at the end of the day", "keep only a count"). Short retention was a user requirement from day one, not a compliance afterthought.
- Bug reports in the tracker contained real identifiers. **Use synthetic test persons only**; never paste real data into issues, commits or prompts.

## 1. What was built

| Area | What existed in 2022 |
|---|---|
| Forms | Border-crossing declaration (oświadczenie o przekroczeniu granicy), one-off 300 zł benefit application, family allowance application SR-1 (15 pages) with attachments ZSR-05 and OSR-01, parental benefit SR-7, regional family card application, declaration under criminal liability, PESEL application for Ukrainian citizens |
| Visitor side | A mobile web page in Ukrainian: applicant, children, family members, bank account. One field per row so it works on the cheapest phones. Final screen: "Thank you, your document will be printed when your turn comes" plus "Go back and edit" |
| Clerk side | Choose forms (all pre-selected), type the first digits of the identifier, get name suggestions, click, all fields of all chosen forms are filled; print each form or all |
| Recognition | Planned: photo of the passport with the phone, recognise name, surname, place and date of birth, document series and number, show a correction screen; the photo is not stored. A paid cloud OCR was evaluated, then a hardware passport reader was obtained |
| Hardware | Adaptive Recognition Osmond passport reader with RFID, with the vendor's Passport Reader software package and the Autofill ("Digital Reception") middleware that pushes read data into web forms through a Chrome extension. Provided free of charge by the manufacturer for the refugee registration work |
| Operations | End-of-day list of served people and counts of applications and persons; then deletion of all personal data |

## 2. Product lessons

### 2.1 The queue is the best data-entry moment
The winning change was described in one card: instead of waiting for a scanner, give everyone in the queue a link, let them type applicant, children, family members and bank account, and let the clerk pull the record. The card also defined the gate question first ("Do you live in this city? If not, here is where to go instead"), which removed ineligible cases before any typing.

Requirement for the new system: **eligibility and routing questions come before data entry**; the visitor never fills a form the office cannot accept.

### 2.2 Link identical fields across forms, but keep them overridable
The original design note: open any form, fill a field, every linked field in the other forms fills itself; some fields must stay editable per form (for example a declined surname in a sentence). Later the team moved all typed fields to a separate tab and treated the forms as output only.

Requirement: one canonical profile, forms are projections of it, **per-form overrides are allowed and are visibly marked**.

### 2.3 A case is a small database of people
Forms repeatedly ask "which child", "which family member". The team asked for a people list inside the case (children, spouse, other family members), then drop-downs on each form to pick from it. Rules were attached to people, not forms: a spouse who stayed abroad gets an empty entry date, does not get their own benefit application, and triggers an extra attachment.

Requirement: **case → persons → roles**; forms select persons by role; chain rules are evaluated on persons.

### 2.4 Chains of forms are rules, and clerks know them
Examples from the cards: a child's birth tick box generates the parental benefit application; a family member with income generates the income attachment; a family member abroad generates the abroad attachment; each adult gets their own benefit application while children go onto the guardian's one. This is exactly the "life situation → bundle of forms" feature, and it came from clerks, one rule at a time.

Requirement: bundle rules are **data (a rule table with a source and a date), editable without a release**, each with an explanation shown to the clerk.

### 2.5 Local conventions override the printed form
Clerks asked to leave certain fields empty on purpose (a date and place on one page, all tick boxes on another, the school type by default) because the office fills them by hand or because a default was wrong more often than right. One default copied the parent's marital status to the child and was always wrong.

Requirement: each field in a form descriptor has `who_fills` (citizen, clerk, system, leave blank) and **per-office overrides**. Never infer a value for a field just because the profile has something similar.

## 3. Defaults and conditional logic that proved necessary

| Rule | Why it mattered |
|---|---|
| Child's surname, citizenship and address default from the parent; each next child copies the previous child's non-personal fields | Families of 3–5 were common; this removed most typing |
| Locality and commune default to the office's city, with a list of neighbouring communes | Almost everyone lived locally |
| Marital status and sex must agree (Polish forms use gendered words) | Otherwise the printed form is self-contradictory |
| Document type drives the fields: an ID card has no series, a birth certificate has series and number in one field, a passport of a third country needs a free-text country | Wrong fields produced wrong printouts |
| Every drop-down needs an "other, type your own" option | Atypical cases appear daily |
| Dates: typed as digits with visible separators and auto-advance, day-month-year order; a calendar widget only where the date is recent | A calendar for a birth date is slow |
| Bank account: digits only, strip spaces, exact length | Otherwise empty boxes appear on the form |
| Sums are calculated; an empty amount prints as empty, not as zero | Zeros changed the meaning of the form |
| Conditional sections stay hidden until relevant; column headers do not show before the first row exists | Novices were confused by empty tables |
| Transliteration from Cyrillic to Latin for names and document series, with the instruction "copy exactly as in your document"; search works in both scripts | Names were entered inconsistently |
| A sample photo shows where the document number is on each document type | People did not know which number was asked for |

## 4. Print fidelity failures (the largest bug class)

- A form with two children pushed the signature onto a third page; the clerk reduced the print scale by hand for that one form.
- The same form rendered differently depending on tablet orientation; on one tablet the browser printed the web page instead of the form.
- An empty second page was generated.
- Identifier digits and tick marks drifted out of their boxes; long or upper-case surnames shifted the line.
- Font size had to be tuned so that characters fill the boxes.
- People did not know where to sign until a dotted line was added.

Conclusion for the forms engine: the template PDF is the background and is never re-flowed; text is placed into measured boxes with automatic font fitting and explicit overflow errors; boxed (comb) fields are placed character by character; the PDF is produced on the server so that the result does not depend on the device; every form has a visual regression test.

## 5. Data integrity bugs

- **Wrong person printed.** Pressing print for one family member printed another. Mitigation: print jobs carry the person id, the preview shows the name in large type, and the job is confirmed.
- **Second save ignored.** A visitor who saved, left, came back and saved again was found by the clerk with the first, incomplete record. Mitigation: one session per visitor with versioned updates; the clerk always sees the latest version and its time.
- **Children duplicated or missing** on forms after editing. Mitigation: persons have stable ids inside the case; forms reference ids, never copies.
- **Edits after printing.** Clerks need "back, fix, print again" without losing the case.

## 6. Clerk workstation UX

- Action buttons always visible (sticky header with one print button per document and "print all").
- Fields that still need attention are highlighted.
- Cursor lands in the first field after "add child".
- Compact single-line layouts; large high-contrast buttons.
- Leaving the page asks for confirmation.
- A free-text note field per case.

## 7. Recognition and hardware

- The intended phone flow: pick document type, the camera opens, recognised fields appear for correction, unrecognised dates fall back to three drop-downs (day, month, year); the image is not stored.
- Handwritten or dot-matrix internal passports cannot be read by machines (confirmed by the reader manufacturer); those remain manual.
- The Machine Readable Zone gives name, document number, nationality, date of birth, sex and expiry. It does **not** give address, parents' names or place of birth.
- The reader was meant to be triggered **per person slot**: press "scan" in the mother's section, then in the father's, then for each child. The vendor middleware fills a web form through a browser extension; a multi-person form needs explicit targeting of the section being filled.
- Reading the chip (RFID) was requested mainly to obtain the face photo for a form that required a printed photo.
- The vendor's licences are device-bound files loaded into the reader with the vendor's licence manager; the software package and the licence files are kept privately by the owner and must never be committed to this repository.

## 8. Privacy practice in 2022 and what to keep

| Practice then | Decision now |
|---|---|
| "Store nothing on the server except the adult's name and the registration date" | Keep the spirit: personal data lives in a short-lived session; only non-personal counters are retained |
| Delete saved data after a few hours or at the end of the day | Time-to-live per session plus an explicit "delete now" on both sides |
| A "delete my personal data" button for the visitor and for the clerk | Keep both |
| Plan to move from a hosted server to a local server in the room | On-premise deployment is a first-class target |
| Real identifiers pasted into bug cards | Synthetic persons only; a generator for valid test identifiers is part of the test tooling |

## 9. Checklist derived from the cards

- [ ] Eligibility and routing questions before data entry.
- [ ] One field per row on the phone; works on low-end devices and in both orientations.
- [ ] Case with persons and roles; copy-forward defaults for children.
- [ ] Bundle rules as editable data with explanations.
- [ ] Per-field `who_fills` and per-office overrides.
- [ ] Template PDF as background, measured boxes, comb fields, font fitting, overflow errors.
- [ ] Server-side PDF, visual regression test per form.
- [ ] Print job bound to a person, large-type confirmation.
- [ ] Session versioning; clerk sees the latest save.
- [ ] Back-edit-reprint loop.
- [ ] Sticky print actions; highlight incomplete fields.
- [ ] Transliteration and search in both scripts.
- [ ] Time-to-live deletion, "delete now", daily anonymous statistics.
- [ ] Synthetic test data only.
