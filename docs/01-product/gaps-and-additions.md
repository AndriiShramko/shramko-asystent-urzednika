# What the original idea did not cover (and what was added)

The owner asked for everything he had not thought of to be thought through and added to the specification (R23). Each item says what the gap is, why it matters, and where the repository now handles it. Items marked **decide** need the owner or the customer; everything else already has a default.

## 1. Fit with the hackathon challenge

| # | Gap | Why it matters | Now handled in |
|---|---|---|---|
| 1 | The challenge is about requests for public information (UDIP). The owner's idea is about forms at the counter. They are different problems with different users in the office. | A jury scores fit with the task first. An excellent counter product presented as the answer to a UDIP challenge loses to an average UDIP assistant. | [`scope-decision.md`](scope-decision.md): Module A (UDIP) is the product shown; Module B (counter) is a thin slice on the same core |
| 2 | "Assistant" was read as "agent picks the forms". For the city it means: read the request, classify it legally, find the answer, draft the letter, keep the deadline. | Different features, different data, different risks. | [`../02-architecture/ai-layer.md`](../02-architecture/ai-layer.md) |
| 3 | Nothing in the idea measures success. | "Shorter handling time" is the stated goal; a jury wants a number. | Evaluation harness and metrics in ai-layer; pitch numbers in [`../05-hackathon/presentation/storyboard.md`](../05-hackathon/presentation/storyboard.md) |

## 2. Law and roles

| # | Gap | Why it matters | Now handled in |
|---|---|---|---|
| 4 | Who is responsible for the data. | In an office the controller is the office; a software supplier is a processor under a written agreement; the data protection officer of the office must be involved and a data protection impact assessment is expected for new technology on citizens' data. | [`../02-architecture/security-and-privacy.md`](../02-architecture/security-and-privacy.md) |
| 5 | "Enter all data that may ever be needed" conflicts with data minimisation. | An office may process only what a given case needs. | The full profile stays on the visitor's phone; only the fields required by the chosen forms are sent (ADR-003) |
| 6 | One database of everybody for many institutions. | A public body needs a legal basis for every data set and purpose; a new central register of residents' data built by a supplier has none, and state registers already exist. | [`scope-decision.md`](scope-decision.md) §4: centralise the forms, not the personal data; ADR-006 |
| 7 | Photographing identity documents. | The supervisory authority treats copies of identity documents as excessive unless a statute requires them. Reading the data in front of the citizen is what a clerk does anyway; storing the image is the problem. | No image is stored or sent anywhere; recognition runs on the device or inside the office network; identity-sources.md |
| 8 | AI in an office is regulated: transparency, human oversight, staff AI literacy, possible high-risk classification. | The city's lawyers will ask on day one. | Human approval of every output, AI-marked text, audit trail; classification analysis in [`research/05-rodo-ai-act-security-requirements.md`](../../research/05-rodo-ai-act-security-requirements.md) |
| 9 | Statutory templates versus local auxiliary templates. | Some forms have a layout fixed by regulation; others are just a convenience of one office. "Identical print" means different things for the two. | `legal_status` in every form descriptor; forms-engine.md |
| 10 | The reader and its software were donated for refugee registration. | Using them in a product or a paid deployment needs the manufacturer's consent and probably other licences. **decide**: ask the manufacturer; they may become a partner. | identity-sources.md §hardware |

## 3. People the idea forgot

| # | Gap | Now handled in |
|---|---|---|
| 11 | Visitors without a smartphone, without mobile data, or unable to type: the clerk-assisted path must be as fast as the self-service path. | Assisted flow B3; a tablet at the desk can run the visitor page |
| 12 | Blind and low-vision visitors and clerks, elderly people, low literacy. Public-sector web and mobile applications in Poland must meet the accessibility standard. | Accessibility is an acceptance criterion in every UI work package; large-print verification screen |
| 13 | Foreigners: no PESEL, names in another script, foreign documents. This was the whole 2022 user base. | Canonical profile allows "no PESEL"; transliteration; document-type-driven fields |
| 14 | Representatives: parents for children, legal guardians, proxies with a power of attorney. | Persons and roles in the case model; proxy forms in bundles |
| 15 | The clerk is the real daily user. Clerks decide whether the tool lives. | Clerk workstation rules from the 2022 cards ([`research/09`](../../research/09-lessons-from-2022-prototype.md) §6) are acceptance criteria |

## 4. Trust and security

| # | Gap | Now handled in |
|---|---|---|
| 16 | Data typed by the visitor is a declaration, not a verified fact. | Every field carries its provenance: self-declared, read from a document, read from a chip, confirmed by the clerk. The clerk confirms against the document before printing |
| 17 | The visitor's phone is on mobile data, the clerk's computer is in a closed office network. "Send it over the local network without servers" cannot work as described. | Relay with end-to-end encryption: the relay sees only ciphertext; the office side only makes outbound connections (ADR-002) |
| 18 | A QR code on a wall can be replaced by an attacker's sticker. | The QR code is shown on the clerk's screen or an official display, is valid for minutes, and both sides compare a short code derived from the shared key |
| 19 | Requests arriving by e-mail are untrusted text that an AI will read: prompt injection. | The request is data, never instructions; structured output only; no tool with side effects is reachable from analysis; an injection test set is part of the gate |
| 20 | An AI can invent a legal basis. | Every cited provision is checked by code against the stored text of the act; an unknown citation blocks the draft |
| 21 | Sending personal data to a cloud model. | Policy by data class: public material may go to any provider; personal data only to a model inside the office or after pseudonymisation; a canary test proves nothing leaks |
| 22 | Logs and bug trackers leak personal data (it happened in 2022). | Logs carry ids, never values; synthetic test persons only; pre-commit scan for identifier patterns |
| 23 | Deleting data must be provable. | Session time-to-live, explicit delete, deletion events in the audit log, daily counters without personal data |

## 5. Daily reality of an office

| # | Gap | Now handled in |
|---|---|---|
| 24 | For several procedures the state system already generates the form (identity card applications since the end of 2023), so a pre-filled paper form would be useless or wrong. | Bundle rules can say "no paper form: handled in the state register" and show what to bring instead |
| 25 | Printing a form does not remove the clerk's typing into the domain system. | Honest limit in the pitch. The local bridge can later hand verified data to other desktop applications, as vendor "autofill" tools do; register integrations are the long-term path |
| 26 | Forms change. A template replaced on the city site silently invalidates coordinates. | The catalogue stores a hash per template; the crawler reports changes; a descriptor is bound to a hash and is disabled when the hash changes |
| 27 | Fees, attachments, who must appear in person, duplex printing. | Bundle rules carry fees, attachment checklists and print options from the service cards |
| 28 | Each office has its own conventions (fields left empty on purpose). | `who_fills` per field and per-office overrides |
| 29 | Signature. | Paper with a handwritten signature stays the baseline; electronic signature and e-delivery are extension points |
| 30 | System down, printer down. | Paper fallback is always possible; nothing in the process depends on the system being up |
| 31 | For public-information cases: anonymisation of documents before disclosure, "processed information", formal elements of decisions, retention class of the case file, publication of answers, yearly statistics. | Module A features F5–F10 in ai-layer.md and the UDIP research |
| 32 | Integration with the office's document management system. | Import and export at the edges (file drop, e-mail, API); an adapter interface; nothing in the core assumes a specific system |

## 6. Delivery and the hackathon

| # | Gap | Now handled in |
|---|---|---|
| 33 | Digital sovereignty: an office may not be allowed, or may not want, to depend on a foreign cloud model. | Provider abstraction with a Polish open model served locally as a first-class option |
| 34 | The demo must work on one laptop without the internet. | Mock provider with recorded answers, local model option, synthetic data, single start command |
| 35 | Material handed out at the hackathon can change the task. | [`../05-hackathon/ONSITE-INTAKE.md`](../05-hackathon/ONSITE-INTAKE.md) with a procedure for the lead agent |
| 36 | What the jury will ask. | [`../05-hackathon/jury-qa.md`](../05-hackathon/jury-qa.md) |
| 37 | After the hackathon: pilot, procurement, maintenance, cost. | [`../01-product/after-the-hackathon.md`](after-the-hackathon.md) |
| 38 | Names and marks: mObywatel, the city, the ministry are not partners of this project. | Disclaimers in README; integrations with state systems are described as proposals until an agreement exists |
