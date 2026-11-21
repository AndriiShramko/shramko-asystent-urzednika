# Jury questions and the truth table

Two things live here: the list that says what in the demo is real, and where the prepared answers are. The lead agent keeps both true to the software at every milestone. A claim that the software does not show is removed from the pitch, not defended.

## What is live, simulated or planned

Update the "State" column at each milestone gate. Allowed values: **live** (works in the demo on real code paths), **simulated** (scripted or mocked; say so), **planned** (not shown).

| Capability | State before the event | Notes for the answer |
|---|---|---|
| Registering a request and both deadline dates | planned | |
| Letter-type recognition and split into questions | planned | |
| Classification with reasons and provisions | planned | |
| Citation check against the stored text of the act | planned | |
| Draft of a reply or notice from templates | planned | Template wording is a draft for the office's lawyer |
| Masking of personal data before a model call; "what the model received" | planned | |
| Local open Polish model | planned | State which model actually ran in the demo |
| Cloud model on pseudonymised text | planned | State the provider |
| Search in earlier answers | planned | The archive is synthetic |
| Search in the city's public bulletin | planned | Snapshot of public pages, with dates |
| Redaction of a document to disclose | planned | |
| Approval flow and audit trail with hash chain | planned | |
| Connection to the office's document management system | simulated | File import and export only |
| Login with the office's identity provider | simulated | Demo users |
| Online request form with "already published" hint | planned | |
| Counter module (data once, forms filled) | planned | Shown as a slide unless built |
| mObywatel or wallet data sharing | simulated | No agreement exists; never claim an integration |
| Hardware document reader | planned | Simulator only |
| Real personal data anywhere | never | Synthetic data only |

## The same table for the forms product (primary track)

| Capability | State before the event | Notes for the answer |
|---|---|---|
| Recognition of fields on a blank form and proposals of labels and meaning | planned | Say the measured share of fields found on the golden form |
| Review screen with correction by dragging | planned | |
| Generated online form for the phone | planned | |
| Print on the original template with an automatic comparison | planned | Say "on the original template file, without re-typesetting" |
| Phone page with a profile kept on the device | planned | |
| QR handoff with end-to-end encryption, comparison code, lifetime of minutes | planned | Show what the relay stores: ciphertext |
| Clerk's view: waiting list, large-type check, provenance marks | planned | |
| Checker: rules first, then a model | planned | State which model ran |
| Bundles: one data entry, several forms and persons | planned | |
| The complete set from one sentence or one chosen matter, with attachments to bring and fees; a clarifying answer changes the set | planned | Rules come from the service cards, each with its source; the model only picks among existing sets |
| "Prepare your visit": the intent chosen at home arrives with the handoff | planned | The link from the city's booking system is a proposal: **never claim an integration** |
| Comparison of the document reading with the declared data; check by exception in three groups | planned | Say "urzędnik potwierdza tożsamość zawsze"; the address and PESEL are not confirmed by the machine-readable zone |
| First profile entry from saved browser data (`autocomplete`) | planned | The browser offers, the person accepts; the page does not read saved data |
| The agent door: an assistant finds the matter, gets the set and holds a visit; the person confirms on the phone | planned, optional | The calendar is a demo calendar; **no link to the city's booking system** |
| The agent door: an assistant fills the draft of a digitised form inside a permission approved on the phone; the person reads and submits | planned, optional | Filing is simulated; say "asystent wypełnia, człowiek zatwierdza"; the agent never signs, submits or proves identity |
| Runs with no cloud: local open model, one start command | planned | The partner rewards open source that can be hosted on premise (research/12) |
| Camera reading of the machine-readable zone on the device | planned | No image stored or sent |
| Government wallet or mObywatel data sharing | simulated | The flow exists for selected partners; no agreement: never claim an integration |
| Hardware document reader | simulated | The owner has a reader; licence and consent of the manufacturer are open |
| Login with the office's identity provider | simulated | Demo users |
| Export to the formats of central platforms | planned, not shown | A next step to agree with the partner |
| Real personal data anywhere | never | Synthetic data only |

## Prepared answers

- **"Does it work without a cloud?" (the partner rewards on-premise operation).** Polish: „Tak. Dane osobowe nigdy nie trafiają do modelu: porównanie z dokumentem, kontrola i wydruk działają na regułach, w infrastrukturze urzędu. Model czyta tylko puste druki, raz, z wyprzedzeniem, a dostawcę modelu można przełączyć na lokalny." Say the last clause only if the `local` switch was run and measured; otherwise stop after "z wyprzedzeniem" and add „dziś użyliśmy modelu w chmurze, bo puste druki są jawne". Source: ai-layer §2, WP-B11 item 9.
- **"Are all 661 documents ready?"** No. „Wszystkie przeszły pierwszy etap automatycznie; zatwierdzone przez człowieka są te, które pokazujemy. Lejek na ekranie pokazuje prawdziwe liczby." Source: WP-B11.
- Ten short answers in Polish with Russian hints are in the presenter window of the deck (keys 1–9 and 0). Their source is [`presentation/storyboard.md`](presentation/storyboard.md), section "Answer cards".
- Twenty-five likely questions with longer answers in English are in [`research/01-hacknation-2026-task-rules-jury.md`](../../research/01-hacknation-2026-task-rules-jury.md) §4. After the 11:00 gate the lead rewrites the ten most likely ones in Polish for the real criteria and updates the cards.
- Facts behind the answers: law and process in [`research/02`](../../research/02-udip-law-process-taxonomy.md); data protection, the AI regulation and model providers in [`research/05`](../../research/05-rodo-ai-act-security-requirements.md); integration and existing tools in [`research/07`](../../research/07-landscape-existing-solutions-and-reuse.md).

## Numbers that may be said, with their sources

| Number | Source | Label |
|---|---|---|
| 14 days; at most 2 months after an announced extension | the act, art. 13 | verified |
| Bydgoszcz received between 501 and 1,200 requests for 2022 | Watchdog Polska monitoring 2023, via research/02 | verified |
| 81 % of officials expect automation of routine tasks; 67 % want natural-language search in documents; 6 % accept AI deciding about people | NASK survey, via research/07 | verified |
| 95.9 % of surveyed organisations do not feel ready to deploy AI in line with data-protection law | the data-protection authority's expert team survey, via research/05 | verified |
| A profile fills about 55–60 % of fields on simple resident forms, about 36 % across all analysed forms | own analysis of 32 forms, research/03b | estimate, say "our estimate" |
| A call to complete an application gives a term of at least seven days | Kodeks postępowania administracyjnego art. 64 § 2, via research/12 | secondary; confirm in the Sejm ELI API before the final PDF |
| 661 unique documents in the city's archive; in 461 (70 %) a program finds the places to fill without a model; 24 are scans; the whole archive was read in 142 seconds on two cores | `tools/forms_census.py`, research/13 §1 | measured; always add "pierwszy etap, nie gotowe usługi" and that the count of places follows a simple rule |
| 2,479 communes; the residence template is fixed by a national regulation | Ministry of the Interior and Administration, state on 1 January 2026; Dz. U. 2022 poz. 2070; research/13 §3 | verified; say "wzory ustawowe", do not extend to the city's own templates |
| France: an official, experimental interface for AI assistants to about 74,000 public datasets since February 2026 | the platform's own announcement; research/13 §2 | verified (the count is secondary); it covers data, not services |
| Fields in the set, fields typed by the clerk, fields the clerk looked at, seconds from scan to print | counters of the demo run (WP-B7, WP-B8) | only after it is measured |
| Accuracy, time per request, zero invented citations, zero leaks | the evaluation run of the build (`metrics.json`) | only after it is measured |

Never say: that the state supports or plans an interface for agents, how many people use AI assistants (say "coraz więcej osób"), how often residents come twice or how many applications are incomplete (no data; say "zdarza się" and give the seven days), that the booking system of the city is connected, a number for time or money saved in the real office (nobody measured it), that the city uses a specific document system (not established), that mObywatel is integrated, that the print is "legally identical" to a statutory template (no primary source; say "on the original template file, without re-typesetting").

## If a question is not understood

Polish phrases for the presenter: „Proszę powtórzyć pytanie.” (please repeat the question) · „Czy dobrze rozumiem, że pytają Państwo o …?” (do I understand correctly that you ask about …) · „Nie wiem. Sprawdzimy to i odpowiemy po prezentacji.” (I do not know; we will check and answer after the presentation). An honest "I do not know" costs less than a wrong claim.
