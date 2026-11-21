# Data protection, AI Act and security requirements for "Shramko Asystent Urzędnika"

Status date: 2026-11-21 (access date for all sources). Scope: (a) AI-assisted handling of UDIP requests (wnioski o dostęp do informacji publicznej), (b) collecting citizen data by phone, QR or ID scan and printing pre-filled forms in a Polish city office.
Legend: VERIFIED = primary source opened and read in this session; SECONDARY = reliable secondary source or search result only; UNVERIFIED = not found or not opened (stated from general knowledge, check before relying). This is research for builders, not legal advice; the city's IOD (Inspektor Ochrony Danych) and legal department must sign off any real deployment.

## TL;DR for builders

- **Hackathon posture:** demo with synthetic data only. No real citizen data, no real ID images, in any LLM call or repo. This removes almost every legal blocker for the 24 hours and lets you show the production design instead.
- **Legal basis in production:** art. 6(1)(c) and (e) RODO (legal obligation / public task), with the task defined in statute (UDIP act, KPA, the specific procedure act). Never consent as the basis for a citizen-office relationship. Special categories (art. 9) need art. 9(2)(g) plus a Polish statutory basis.
- **"Enter everything once, up front" conflicts with art. 5(1)(c) minimisation.** Compliant design: the full profile lives only on the citizen's device (encrypted, local); once forms are chosen, only the union of the fields those forms need is transmitted, end-to-end encrypted to the clerk workstation, with a short TTL; the office keeps only what the signed form must contain.
- **ID documents:** UODO punishes bulk scanning without necessity (ING Bank Śląski, DKN.5112.6.2020, PLN 18,416,400; Restaurant Partner Polska / Glovo, DKN.5112.33.2022, PLN 5,898,064). Both are private companies and neither is final. Design rule: read-verify-discard (MRZ or chip read in memory, show to clerk in large print, store nothing, never keep the image); copy only where a statute for that office requires it.
- **AI Act state (Nov 2026):** Digital Omnibus on AI is in force (Regulation (EU) 2026/1744, OJ 24 Jul 2026, in force 27 Jul 2026). Annex III high-risk obligations now apply from **2 Dec 2027**. Art. 5 bans, art. 4 (softened) and art. 50 transparency (from 2 Aug 2026) apply now.
- **Classification:** a UDIP drafting assistant and a form-completeness checker are not in Annex III as such (point 5(a) covers eligibility for essential public benefits; point 8 covers judicial authorities and elections). Keep them out of Annex III by design: prepare and flag, never evaluate eligibility, never profile, never decide.
- **Human decides, always.** Refusals and limitations under UDIP are administrative decisions; the clerk reads, edits and signs. The AI produces drafts with citations of the statute and of the request text. This also keeps art. 22 RODO out of play.
- **Polish AI act** (ustawa o systemach sztucznej inteligencji, 3 Jul 2026, Dz.U. 2026 poz. 1003) is published; most of it in force 11 Aug 2026, art. 8-18 and chapters 3-5, 8, 9 from 28 Oct 2026 (SECONDARY). It creates the KRiBSI authority; it does not change the classification logic.
- **Security baseline for a city office:** KRI (Dz.U. 2024 poz. 773), the NIS2 amendment of the KSC act (in force April 2026; treat a city office as in scope), WCAG 2.1 AA minimum (build to 2.2 AA) under the digital accessibility act, audit logging, no direct DB access (API-only), SCCO for any cloud.
- **Anthropic first-party API has no EU region.** `inference_geo` accepts only `global` and `us`; workspace geo only `us` (VERIFIED, official docs). For EU residency use Claude through Amazon Bedrock EU geographic inference profiles (SECONDARY) or a sovereign/local model (PLLuM, Bielik). Default retention 30 days; ZDR by contract per organisation; flagged content up to 2 years.
- **Pseudonymised text is still personal data for the sender** (the office holds the mapping). After CJEU C-413/23 P (4 Sep 2025) it may not be personal data for a recipient with no means of re-identification, but free text leaks context, so treat tokenised text as personal data and keep a processor agreement. A tokenising gateway is a risk reducer, not an exit from RODO.
- **IOD is mandatory and must be involved** (art. 37(1)(a), art. 38(1), art. 35(2) RODO). Ship a DPIA draft, a processing-record entry (art. 30) and the UODO "RODO and AI" public-sector checklist filled in as part of the repo; this is the single most jury-visible compliance artefact.

---

## 1. Legal bases, roles, DPIA, retention, privacy by design

### 1.1 Legal bases (RODO, Regulation (EU) 2016/679)

| Processing | Basis | Notes |
|---|---|---|
| Handling a UDIP request (read, analyse, answer) | art. 6(1)(c) and (e) with the UDIP act (ustawa z 6 IX 2001 o dostępie do informacji publicznej) and KPA | Basis must be laid down in law (art. 6(3)). UNVERIFIED in this session: UDIP art. 5(2) limits access for privacy of a natural person, art. 13 sets the 14-day deadline, art. 16 governs refusal by decision. Confirm on isap.sejm.gov.pl. |
| Citizen enters personal data to start a service/case | art. 6(1)(e) (public task) or (c) per the procedure | Not consent: consent is not "freely given" toward an authority. A voluntary pre-registration convenience may use art. 6(1)(e) if the office's task includes service provision; ask the IOD. |
| Special categories (health, disability, religion in forms) | art. 9(2)(g) substantial public interest on a statutory basis | Many life-situation forms (benefits, disability) carry art. 9 data. Collect only when the chosen form requires it. |
| PESEL | processed under the statute that requires it for the form | PESEL plus name is a strong identifier; UODO treats it as high risk in the ING decision (VERIFIED, below). |
| Public access to official documents | art. 86 RODO | Member-state law may reconcile access with data protection; this is the legal hook for the UDIP privacy-limit analysis, not a licence to publish personal data. |

### 1.2 Roles

- **Controller (administrator):** the city (gmina Miasto Bydgoszcz) acting through the Prezydent Miasta. The office decides purposes and means.
- **Processor (art. 28):** any vendor hosting the system, running the LLM, doing OCR or relaying messages. Needs a written art. 28(3) agreement: instructions, confidentiality, security (art. 32), sub-processors, assistance with data-subject rights, deletion/return, audit. For a hackathon prototype that never sees real data, no processor exists; state so in the repo.
- **Joint controllers (art. 26):** not expected; avoid designs where the vendor sets its own purposes (e.g. training on prompts).
- **The citizen's own device:** local storage of the profile in the citizen's browser is the citizen's processing as long as the office does not receive it. The office still must not read it; ePrivacy rules on terminal storage apply (Polish implementation: Prawo komunikacji elektronicznej; "strictly necessary" exemption for a service the user asked for; UNVERIFIED article number).
- **IOD (art. 37(1)(a)):** a public authority or body must designate a data protection officer; art. 38(1) requires involvement in all data-protection issues; art. 35(2) requires seeking the IOD's advice in a DPIA. CONFIRMED in substance (text of RODO; eur-lex not re-opened in this session).

### 1.3 DPIA (art. 35) and the UODO list

- Authority: art. 35(4) RODO; list = Komunikat Prezesa UODO of 17 June 2019, M.P. 2019 poz. 666 (replacing the 2018 list, M.P. 2018 poz. 827). UODO says processing meeting at least two criteria will generally require a DPIA; the examples are not exhaustive (SECONDARY, search summary of UODO pages; full text at https://eli.gov.pl/api/acts/MP/2019/666/text/O/M20190666.pdf, not opened).
- Criteria likely to be hit here (judge by the list's own wording before claiming): innovative technology (AI/LLM), large-scale processing of PESEL and ID data, processing of data of persons in a dependency relationship toward the authority, combining datasets (profile plus forms), possibly biometrics if a face is matched to a document photo (avoid; see section 2).
- Conclusion: **DPIA is required in practice** for the production system; also for each AI use case separately (UODO checklist says process-by-process). Prior consultation (art. 36) only if residual risk stays high.
- UODO's own starting point (VERIFIED, opened): "Listy pytań inicjalnych" published 2026-08-05, updated 2026-08-28, four sets (SME users of ready-made AI; **public sector**, which "uwzględnia zasadę legalizmu i reguły postępowania administracyjnego"; version 0 for model builders; extended version with AI Act signals: risk classification and fundamental-rights impact). The questions "nie zastąpią analizy ryzyka, oceny skutków dla ochrony danych". Public-sector docx: https://uodo.gov.pl/pl/file/7877 (title seen in search, not opened). Comments to pytania_inicjalne@uodo.gov.pl until 30 Sep 2026.

### 1.4 Retention and records

- Art. 5(1)(e) storage limitation and art. 30 records of processing activities (the city needs a register entry for the new system).
- Case files: retention is set by the office's instrukcja kancelaryjna and jednolity rzeczowy wykaz akt (UDIP files, benefit files have category A/B/BE periods). UNVERIFIED in this session; the system must not hold files longer than the wykaz akt and must not become a parallel archive.
- Proposed technical retention: relay payloads 15 minutes max or until fetched; clerk app wipes the pre-fill buffer after printing/closing; audit logs contain event metadata and pseudonymous identifiers only, retained per the IOD's policy (suggest 12 months, UNVERIFIED as policy).
- Breach duty: art. 33 (72 hours to UODO), art. 34 (notify data subjects if high risk). Ship an incident runbook.

### 1.5 The "enter everything that might ever be needed" request vs minimisation

Conflict: art. 5(1)(c) (data adequate, relevant, limited to what is necessary for the purposes), art. 25 (data protection by design and default) and the ING and Glovo findings (excess data, "just in case" collection, no legal basis) mean the office may not receive and store a super-profile in advance. The owner's UX goal is legitimate if the super-profile stays with the citizen.

Compliant design ("profile on device, minimal projection to office"):

1. **Local profile.** The citizen page is a PWA/SPA. Profile stored in IndexedDB, encrypted with a WebCrypto AES-GCM key held as a non-extractable key (optionally unlocked by device biometrics via WebAuthn). Nothing leaves the device while the citizen edits it. No analytics on field values.
2. **Per-form field schema.** Every form in the catalogue ships a machine-readable schema: field id, legal basis for requiring it, whether it is mandatory. The "required fields" for a chosen life situation = union of schemas of the proposed form chain.
3. **Minimal projection.** On "send to clerk", the page builds a payload containing only those fields and shows the citizen exactly what will be sent (a diff view) before sending.
4. **Ephemeral transport.** The clerk desktop app shows a QR containing a one-time session id plus a fresh public key (HPKE/age-style). The citizen page encrypts the payload to that key. The API relay stores ciphertext only, TTL minutes, deletes on fetch. The relay never holds plaintext or keys.
5. **Clerk side.** Decrypt in memory, pre-fill, clerk verifies, print the officially approved template, wipe. What the office keeps is the signed form in the case file, by the wykaz akt.
6. **Citizen control.** One button erases the local profile; export as file. Transparency text: who is the controller, purposes, legal basis, recipients, retention (art. 13), shown before sending.
7. **Optional later fields.** If a later form needs a field not in the projection, the clerk asks the citizen to send that field only (an extra request), not "everything".

This also answers "very large print" verification: the clerk app renders the received identity fields in large type for a face-to-face check.

---

## 2. Identity documents: copying, photographing, scanning, reading

### 2.1 UODO decisions (claim C18, all VERIFIED on uodo.gov.pl unless noted)

| Item | ING Bank Śląski | Restaurant Partner Polska (Glovo app) |
|---|---|---|
| Reference | DKN.5112.6.2020 | **DKN.5112.33.2022** (the claim's "5112.33.2022" lacks the DKN prefix) |
| Page | https://uodo.gov.pl/en/553/1990 | https://bip.uodo.gov.pl/en/553/2206 |
| Fine | PLN 18,416,400 (SECONDARY: bezprawnik.pl, telepolis.pl; UODO page says only "effective, proportionate and dissuasive") | PLN 5,898,064 (VERIFIED on UODO page) |
| What was penalised | Scanning identity documents of customers and prospects in situations unrelated to AML duties, without individual risk assessment, 1 Apr 2019 to 23 Sep 2020; breached art. 5(1)(a)(b)(c) and 6(1) RODO | Requiring scans/photos of ID cards or passports from app users for anti-fraud; excess data, no legal basis; art. 5(1)(a)(c), 5(2), 6(1); more than 3.4 million users; since July 2019; ordered to stop and delete within 30 days |
| Key reasoning | Scanning is lawful only if AML financial-security measures make it necessary; mass scale raises due-diligence level; PESEL plus name uniquely identifies a person | Anti-fraud does not justify collecting full documents; the act on public documents gives first-category documents (ID, passport) a special protection regime |
| Status | WSA Warszawa dismissed ING's complaint on 23 Oct 2026 (SECONDARY: https://www.telepolis.pl/fintech/uodo-kara-bank-ing-skanowanie-dowodow); not final, cassation to NSA possible | Reported not final as of 16 Mar 2026 (SECONDARY: https://www.telepolis.pl/wiadomosci/uodo-kara-dla-glovo-dane-osobowe-skany-dokumentow) |

Verdict on C18: numbers and parties confirmed; both targets are private companies, so they establish the principle (necessity must be proven, per case, with a statutory basis) but not a rule about city offices. UODO decision date of the ING decision: not verified. A public office is not the AML-obliged entity and has no blanket right to copy either; its basis would have to come from the specific procedure act.

2025-2026 search for further decisions: nothing found on a public authority copying IDs. UODO's reply of 1 Aug 2025 about ID card and biometric data (via RPO) exists (https://bip.brpo.gov.pl/sites/default/files/2025-08/Odpowiedz_PUODO_dowod_osobisty_dane_biometryczne_1_08_2025.pdf) but was not opened (UNVERIFIED content).

### 2.2 Ustawa o dokumentach publicznych (22 Nov 2018), art. 58

- Art. 58 creates an offence of producing a replica of a public document (copy with features of authenticity, size 75-120 percent of the original, excluding an ordinary photocopy or computer print) (SECONDARY: https://www.prawo.pl/kadry/ksero-dowodu-dozwolone-przetwarzanie-danych-nie,441907.html, as cited by search; article not opened). Plain scanning or photocopying is not the offence. Text of art. 58 itself not opened: UNVERIFIED.
- Relevance: not a bar to scanning, but UODO cites the act's protective regime as an argument against casual copying (VERIFIED in the Glovo decision summary). Builders: never output an "ID-like" rendering; never print a document replica; do not store the image.

### 2.3 On-the-fly MRZ or chip read without storing the image

- RODO view: reading the MRZ or chip in the citizen's or clerk's device memory, displaying fields, and discarding is still "processing" (collection, use) and needs a basis and necessity, but it is much easier to defend than storing a copy: it satisfies minimisation (only the fields the form needs), storage limitation (nothing kept) and the UODO line that necessity must be shown per case. The office's basis is art. 6(1)(c)/(e) via the procedure that requires identity establishment; **identification by showing ("okazanie") the document is the normal legal act; copying is a separate choice that needs its own justification** (the ING reasoning, VERIFIED).
- Do not match the face photo biometrically (art. 9 biometric data for unique identification; high-risk; no basis). A clerk looking at the person and the photo is a human check, not biometric processing.
- Authenticity check with a reader: legal basis is the same public task of establishing identity (art. 6(1)(e)); technically verify chip signature (passive authentication of the document security object) and MRZ check digits, show pass/fail, do not store the chip's photo (DG2) or fingerprint data. The statutory rules on who may read the e-layer of an ID card and how (ustawa o dowodach osobistych, current consolidated text Dz.U. 2025 poz. 1753, per search result) were not opened: **UNVERIFIED; the IOD must confirm that an office reader flow (access key printed on the card, CAN) is lawful in this setting**. Prefer: the citizen's own phone reads the chip or shows mObywatel mDokument and transmits only the needed fields plus the verification result (mObywatel route not verified in this session).
- Clerk-side phone photo of an ID: treat as copying; avoid; if a statute requires a copy, store it in the case file only, encrypted, with retention per wykaz akt.
- Large-print display: render in memory only; disable screenshots/caching for that view; no logs of field values.

---

## 3. AI in public administration (November 2026)

### 3.1 AI Act timeline as of 21 Nov 2026

| Date | What applies | Status |
|---|---|---|
| 1 Aug 2024 | Regulation (EU) 2024/1689 entered into force | known |
| 2 Feb 2025 | art. 5 prohibitions; art. 4 AI literacy | applies (art. 4 recast by the Omnibus, below) |
| 2 Aug 2025 | GPAI model obligations, governance | applies |
| 24 Jul 2026 | Digital Omnibus on AI published in the OJ (OJ:L_202601744, Regulation (EU) 2026/1744) | VERIFIED date and reference via Lewis Silkin: https://www.lewissilkin.com/insights/2026/07/27/the-digital-omnibus-on-ai-enters-into-force-today ; SECONDARY (law-firm summaries; OJ text itself not opened) |
| 27 Jul 2026 | Omnibus in force | same |
| 2 Aug 2026 | Art. 50 transparency duties (chatbot disclosure, labelling); the original Annex III date, now moved | Lewis Silkin: systems placed on market before 2 Aug 2026 have until 2 Dec 2026 for the watermarking duty; other art. 50 duties from 2 Aug 2026 |
| **2 Dec 2027** | **Annex III high-risk obligations (was 2 Aug 2026)** | confirmed by White & Case, Orrick, Lewis Silkin summaries (SECONDARY) |
| 2 Aug 2028 | Annex I (product-embedded) high-risk | same |

- **Art. 4 AI literacy:** the Omnibus changes it to a duty to "take measures supporting AI literacy" (Lewis Silkin quote) rather than a hard individual-level obligation. Still: document short training for clerks. Ministerstwo Cyfryzacji runs AI training for government officials (https://www.gov.pl/web/cyfryzacja/szkolenia-z-ai-dla-urzednikow-administracji-rzadowej, seen in search).
- **Art. 27 FRIA** (fundamental rights impact assessment) is a deployer duty for Annex III high-risk systems used by public bodies, so it moves with Annex III to 2 Dec 2027. Not applicable now to a non-high-risk assistant; do a lightweight version anyway because UODO's extended checklist asks for it (VERIFIED, UODO page). Text of art. 27 not re-opened: UNVERIFIED in this session.
- **Art. 50:** an AI system that interacts directly with people (e.g. a chat helper on the citizen page) must tell them they are dealing with AI (applies since 2 Aug 2026 per Lewis Silkin). Disclose in the UI.

### 3.2 Is the assistant high-risk? (Annex III analysis)

Annex III text checked at https://artificialintelligenceact.eu/annex/3/ (SECONDARY mirror of the Regulation):

- Point 5(a): AI "intended to be used by public authorities or on behalf of public authorities to evaluate the eligibility of natural persons for essential public assistance benefits and services … as well as to grant, reduce, revoke, or reclaim such benefits and services". **UDIP handling is not a benefit eligibility evaluation**: no. A form assistant that chooses "which benefits you qualify for" would be. Keep the life-situation matcher a **catalogue lookup** (situation to forms) with no eligibility scoring.
- Point 8: judicial authorities and election influence: not applicable to a city office clerk.
- Points 1-4, 6, 7: biometrics, critical infrastructure, education, employment, law enforcement, migration: not applicable, unless you add biometric identification (do not).
- Conclusion: UDIP analysis/drafting (D) and form checking (C) are **not high-risk under Annex III as designed**. Art. 6(3) derogations (narrow procedural task, improving a human activity's result, detecting deviations without replacing human review, preparatory task) would additionally apply, but an Annex III system that profiles natural persons is always high-risk (VERIFIED text, https://artificialintelligenceact.eu/article/6/), and a provider relying on 6(3) must document the assessment and register (art. 6(4), art. 49(2)). Design therefore: no profiling of citizens, no risk scores, no ranking.
- Provider vs deployer: the vendor building it is a **provider**, the city a **deployer** (art. 25 can flip roles if the city substantially modifies or rebrands). Transparency and human oversight go in the product (art. 14-style oversight as good practice even if not mandatory).
- Chatbot or generative output labelling: art. 50(2) machine-readable marking applies to providers of generative systems; for text drafted for a clerk who edits and signs, mark drafts "AI-generated draft" in the UI and metadata.

### 3.3 Poland: implementing act and authorities

- Ustawa o systemach sztucznej inteligencji: government adopted the bill 31 Mar 2026; Sejm passed 11 Jun 2026 (421 for, 3 against, 18 abstaining); Senate 25 Jun 2026 with 25 amendments; act dated 3 Jul 2026, published 27 Jul 2026 (Dz.U. 2026 poz. 1003), status "obowiązujący", in force **11 Aug 2026** with art. 8-18 and chapters 3-5, 8 and 9 in force **28 Oct 2026** (SECONDARY: search results from api.sejm.gov.pl, eli.gov.pl/eli/DU/2026/1003, gov.pl; the ELI page returned HTTP 500 when fetched, so not VERIFIED). It establishes the Komisja Rozwoju i Bezpieczeństwa Sztucznej Inteligencji (KRiBSI). Government press: https://www.gov.pl/web/cyfryzacja/koniec-ery-nieuchwytnych-algorytmow--projekt-ustawy-o-systemach-sztucznej-inteligencji-przyjety-przez-rade-ministrow
- Cooperating authority for personal data stays the Prezes UODO.

### 3.4 Art. 22 RODO, human in the loop, who signs

- Art. 22(1): a decision based solely on automated processing with legal or similarly significant effects is restricted; exceptions need law with safeguards (art. 22(2)(b), 22(3)).
- A UDIP refusal or limitation is an administrative decision (UDIP art. 16, UNVERIFIED here). Under KPA a decision is issued by the authority and signed by the authorised employee (KPA art. 107, UNVERIFIED here). Therefore: **AI drafts, a named clerk reviews, edits and signs; the system never sends an answer or issues a decision itself.** The review must be real (not rubber-stamp): show sources and uncertainty, require explicit "accept/edit/reject" per paragraph, log it. This keeps processing outside art. 22 and is the honest answer to "human-in-the-loop".
- Form checker (C): advisory only; flags missing fields or inconsistencies; the citizen or clerk decides.

### 3.5 Official guidance

- UODO "Zanim wdrożysz narzędzie AI…" and the four checklists (VERIFIED, opened): https://uodo.gov.pl/pl/138/4533 (the page has a 2026-08-05 introduction date and 2026-08-28 update; certificate error in WebFetch, read via curl).
- Ministerstwo Cyfryzacji: "Przewodnik po sztucznej inteligencji dla administracji publicznej" (SECONDARY): https://samorzad.gov.pl/web/gov/przewodnik-po-sztucznej-inteligencji-dla-administracji-publicznej and PDF https://www.gov.pl/attachment/7c30aa1a-c191-49dd-acb4-bca4b5e4c308 (not opened). NASK report "AI w administracji publicznej" (March 2026): https://nask.pl/media/2026/03/AI-w-administracji-publicznej_.pdf (not opened). The ai.gov.pl article "AI w urzędzie: od czego zacząć" could not be found or fetched (gov.pl/web/ai/... returned a homepage).
- PLLuM guidance: see section 5.3.

---

## 4. Security and accessibility duties

| Duty | Source | State (Nov 2026) | What it means for the build |
|---|---|---|---|
| KRI | Rozporządzenie Rady Ministrów z 21 maja 2024 r. w sprawie Krajowych Ram Interoperacyjności, minimalnych wymagań dla rejestrów publicznych i wymiany informacji w postaci elektronicznej oraz minimalnych wymagań dla systemów teleinformatycznych, Dz.U. 2024 poz. 773 | in force (published 22 May 2024, in force 23 May 2024 per search; SECONDARY: https://eli.gov.pl/eli/DU/2024/773) | Public entities must meet minimum ICT requirements incl. information-security management; exact paragraphs not read: UNVERIFIED. Build: documented risk analysis, access control, logging, backup, incident handling, API-based interoperability. |
| KSC / NIS2 | Nowelizacja ustawy o krajowym systemie cyberbezpieczeństwa | in force from early April 2026 (3 Apr per gov.pl summaries; one source says 2 Apr); Wykaz KSC opened 13 Apr 2026; self-registration from 7 May 2026 (one source: until 3 Oct 2026); 12-month adaptation period (SECONDARY: https://www.gov.pl/web/cyfryzacja/nowelizacja-ustawy-o-krajowym-systemie-cyberbezpieczenstwa-ksc---kogo-obejmuje) | The act lists "Podmioty publiczne" in Annex 1 item 10 (key) and Annex 2 item 9 (important; others). Whether gminas are in is **not confirmed on the page**; assume a city office is covered as a public entity and ask the city's security officer. Fines timeline unverified. |
| Digital accessibility | Ustawa z 4 kwietnia 2019 o dostępności cyfrowej stron internetowych i aplikacji mobilnych podmiotów publicznych (Dz.U. 2019 poz. 848, consolidated 2023 poz. 1440 per search results) | applies to public bodies; requires WCAG 2.1 AA equivalent through EN 301 549 v3.2.1, an accessibility declaration (deklaracja dostępności) per site and app (SECONDARY; no confirmed move to WCAG 2.2 in Poland as of search) | Citizen page and clerk app: build to WCAG 2.2 AA (a superset), test with keyboard and screen reader, large-print mode, publish a declaration; the large-print ID verification view is itself an accessibility feature. |
| Audit/logging | RODO art. 5(2), 32; KRI | n/a | Immutable audit log: who opened which case, which AI draft, who edited/signed, exports and prints. No field values in logs. |
| Cloud | SCCO (Standardy Cyberbezpieczeństwa Chmur Obliczeniowych); original v1.00 from 2019 (M.P. 2019 poz. 862 per search); update consulted in 2025, gov.pl headline reports adoption of new standards (details not read) | UNVERIFIED current content; criteria on jurisdiction of data centres for public clouds were relaxed after consultations (SECONDARY: itwiz.pl summary) | Public clouds for city data need SCCO-level analysis by the system administrator; document the data classification (legally protected data = higher SCCO level). Page: https://www.gov.pl/web/cyfryzacja/standardy-cyberbezpieczenstwa-chmur-obliczeniowych |
| Data residency | No statute found that forbids EU-cloud processing of city data; SCCO and the office's risk analysis decide | UNVERIFIED | Default to EU region or on-prem; for LLM calls prefer EU endpoint (section 5). |

Security architecture that satisfies the "everything through APIs, no direct DB" requirement: API gateway with OAuth2/OIDC (clerk SSO via the city's identity provider, citizen page unauthenticated but rate-limited and session-bound), mTLS between services, per-role scopes (clerk can read only the case they opened), row-level authorisation inside the service, secrets in a vault, SBOM and dependency scanning, CSP/HSTS, no third-party scripts on the citizen page, encrypted backups, tested restore.

---

## 5. LLM provider options for this use case

### 5.1 Anthropic first-party API (VERIFIED, official docs opened 2026-11-21)

Sources: https://platform.claude.com/docs/en/manage-claude/data-residency ; https://platform.claude.com/docs/en/manage-claude/api-and-data-retention ; https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data

- **Data residency:** `inference_geo` values `"global"` (default) and `"us"` only; "Only 'us' and 'global' are available"; **workspace geo "Currently, 'us' is the only available workspace geo"**. US-only inference costs 1.1x. No EU option on the first-party API, on Claude Platform on AWS, on Claude Models on Google Cloud (Anthropic managed), or via Microsoft Foundry (Foundry: US Data Zone Standard only). `inference_geo` is not applicable on Amazon Bedrock and on Google Cloud (Google managed): there the endpoint URL or inference profile determines the region.
- **Models current in the docs:** Claude Sonnet 5.5, Sonnet 5, Opus 5.5, Opus 5, Haiku 5.5, Opus 4.8/4.7/4.6, Sonnet 4.6, plus Fable and Mythos 5.x.
- **Retention:** privacy centre: "we automatically delete inputs and outputs on our backend within 30 days of receipt or generation" unless agreed otherwise (e.g. ZDR); flagged content up to 2 years, trust-and-safety classification scores up to 7 years. The platform doc says retained data is "never used for model training without your express permission" and that conversation content is not retained by default except Covered Models (30 days): the two pages are worded differently, so quote the contract, not the docs.
- **ZDR:** by request through Anthropic sales, enabled per organisation; no storage of prompts/responses at rest after the response. Not covered: Batch API (29-day retention), Files API, code execution/programmatic tool calling, MCP connector, Agent Skills, Managed Agents (not ZDR except self-hosted), Console/playground, consumer products. Even under ZDR: legal holds and flagged content up to 2 years.
- **Covered Models:** Fable 5/5.1/5.2 and Mythos 5/5.1/5.2 require 30-day retention and are not ZDR-eligible unless Anthropic authorises it. Sonnet 5.5, Opus 5.5 and Haiku 5.5 are not Covered Models (not in the list).
- **DPA and SCCs:** not found in the pages opened; Anthropic's commercial terms include a DPA with SCCs to my knowledge, UNVERIFIED in this session (Trust Center: https://trust.anthropic.com/resources). Without an EU region, each request is a transfer to a third country (art. 44 ff.) and would need SCCs plus a transfer impact assessment; for a city office this makes first-party API a poor fit for real citizen data.
- **Hackathon use:** fine with synthetic or public data (UDIP request texts and public law only). Say in the repo that real data never goes to this endpoint.

### 5.2 Claude through hyperscaler EU endpoints

- Amazon Bedrock: Claude available through geographic cross-region inference profiles; the EU profile routes only within EU regions; prompts/outputs may leave the source region but stay in the geography; single-region requires an application inference profile and the model's in-region availability (SECONDARY: AWS docs and blogs from search, e.g. https://docs.aws.amazon.com/bedrock/latest/userguide/geographic-cross-region-inference.html , https://aws.amazon.com/blogs/machine-learning/unlocking-ai-flexibility-in-europe-a-guide-to-cross-region-inference-for-eu-data-processing-and-model-access/ ). On Bedrock "the cloud provider is the data processor" (VERIFIED, Anthropic retention page). Which models have an EU profile, and whether prompts are visible to Anthropic: UNVERIFIED (an unanswered re:Post thread asks exactly this for Sonnet 5).
- Google Cloud: two flavours: Google-managed (Google is processor; region by endpoint) and Anthropic-managed (Anthropic is processor; workspace geo US only, inference `global` or `us`, VERIFIED). So "Vertex AI EU" is EU only in the Google-managed flavour; the specific EU availability list was not verified.
- Microsoft Foundry: Anthropic is the data processor ("Hosted on Anthropic" or "Hosted on Azure"); only US Data Zone Standard is documented for Azure-hosted data residency (VERIFIED); no EU zone documented on the page read.

### 5.3 Sovereign / local options

| Option | Licence and access | Notes |
|---|---|---|
| PLLuM (NASK-led consortium, Hugging Face org CYFRAGOVPL) | Per model: Apache 2.0 (12B base/instruct/chat; 8x7B base/chat), Llama 3.1 licence (Llama-based 8B/70B), CC-BY-NC-4.0 for all "nc" models; some gated by contact-info form (SECONDARY, HF cards via search: https://huggingface.co/CYFRAGOVPL/models ; https://huggingface.co/CYFRAGOVPL/PLLuM-12b-nc-base-2507 ; paper https://arxiv.org/abs/2511.03823 ; NASK news https://science.nask.pl/en/news/12757) | Check the licence per model before an office uses it; "nc" is unsuitable for a municipal service. 2512 releases (Dec 2025) exist for Llama-PLLuM 8B and 70B. Who offers hosted access to administrations and under what terms: not found, UNVERIFIED. |
| Bielik (SpeakLeash/ACK Cyfronet) | Apache 2.0 (Bielik-11B-v3.0-Instruct and v3.1, 56 languages; Bielik v3 small 1.5B and 4.5B); weights gated behind a contact form on Hugging Face (SECONDARY: https://huggingface.co/speakleash/bielik-11b-v3.0-instruct ; https://osai-index.eu/model/bielik ; https://arxiv.org/abs/2601.11579) | 11B is the practical size for one GPU. |
| Local serving needs (my estimates, not measured) | 11-12B model: about 24 GB VRAM at 16-bit, about 8-12 GB at 4-bit; 70B: multi-GPU or heavy quantisation; use vLLM or llama.cpp behind the same API gateway | Quality on legal drafting must be measured on the project's test set, not assumed. |

Recommendation: **provider-agnostic LLM adapter** (one interface, config picks provider). Real citizen data only to a local or EU endpoint (Bielik/PLLuM on city or EU hardware, or Claude via Bedrock EU after DPA/IOD review). Demo may use any provider with synthetic data.

### 5.4 Pseudonymisation gateway pattern

Pattern: gateway replaces names, PESEL, addresses, phone, e-mail, ID numbers with typed placeholders before the LLM call; keeps the mapping in the office's memory only; re-inserts after the call.

- **EDPB Guidelines 01/2025 on pseudonymisation**: adopted 17 Jan 2025 for public consultation (until 28 Feb 2025); they state that pseudonymised data attributable to a person with additional information "remains information related to an identifiable natural person" (VERIFIED: https://edpb.europa.eu/news/news/2025/edpb-adopts-pseudonymisation-guidelines-and-paves-way-improve-cooperation_en). A December 2025 EDPB discussion paper says the Board is reassessing in light of the CJEU judgment (SECONDARY: https://www.edpb.europa.eu/system/files/2025-12/stakeholder-event-20251212-discussion-paper_en.pdf). Whether a final version was adopted: UNVERIFIED.
- **CJEU C-413/23 P, EDPS v SRB, judgment of 4 Sep 2025**: set aside the General Court's 2023 judgment; the contextual approach asks whether the **recipient** has reasonable means to re-identify; pseudonymised data can be non-personal for a recipient without such means, while remaining personal for the controller who holds the key and must still inform data subjects about recipients (SECONDARY: https://www.cliffordchance.com/insights/resources/blogs/talking-tech/en/articles/2025/09/pseudonymized-data-after-edps-v-srb.html ; https://www.fieldfisher.com/en-be/locations/belgium/insights/edps-v-srb-cjeu%e2%80%99s-contextual-approach-to-pseudonym ; fieldfisher page returned 403 so only the search summary was read; judgment text on curia.europa.eu not opened). The Clifford Chance title mis-types the case number as "T-413/23P".
- **Consequences for sending tokenised text to a cloud LLM:** (1) for the office the text stays personal data; art. 5, 25, 32 and the information duties still apply, and the LLM provider is a recipient/processor to name in the privacy notice. (2) Even if a provider could argue "not personal for us", UDIP text and form text contain indirect identifiers (job, street, case facts), so re-identification by context is realistic; do not rely on the relative approach. (3) Pseudonymisation is an art. 32 safeguard and a strong DPIA mitigation, not an exemption. (4) Free-text redaction is imperfect: run a detector for PESEL (checksum), ID numbers (MRZ patterns), phone, e-mail, IBAN, plus NER for names and addresses; block the call if confidence is low; test with a red-team set. (5) Keep the mapping out of the prompt, logs and any provider-side cache.

---

## 6. Compliance checklist (24 controls)

MUST = legal duty; SHOULD = good practice; DEMO = can be demonstrated within 24 hours.

| # | Control | Legal source | Class |
|---|---|---|---|
| 1 | Written legal basis per processing activity (UDIP handling, form pre-fill, ID verification) listed in repo docs | RODO art. 6(1)(c)(e), 6(3) | MUST, DEMO |
| 2 | IOD named in the docs as reviewer; DPIA draft, art. 30 register entry template, incident runbook | RODO art. 35, 37-39, 30, 33 | MUST, DEMO |
| 3 | DPIA draft mapped to the UODO list criteria (innovative tech, large-scale PESEL/ID, public-authority relationship) | RODO art. 35; M.P. 2019 poz. 666 | MUST, DEMO |
| 4 | UODO "RODO and AI" public-sector initial-question list filled in, kept as documentation | UODO lists 2026-08 | SHOULD, DEMO |
| 5 | Citizen profile stays on device; encrypted local store; one-click erase and export | RODO art. 5(1)(c), 25 | MUST, DEMO |
| 6 | Per-form field schema with legal basis; transmitted payload = union of required fields only; pre-send diff view for the citizen | RODO art. 5(1)(c), 25(2) | MUST, DEMO |
| 7 | End-to-end encrypted relay (clerk public key in QR), ciphertext only, TTL of minutes, delete on fetch | RODO art. 32 | MUST, DEMO |
| 8 | Information clause shown before sending (controller, purposes, basis, recipients incl. LLM provider, retention, rights) | RODO art. 13 | MUST, DEMO |
| 9 | No ID image stored; MRZ/chip read in memory; no biometric face matching; no screenshots of the verification view | RODO art. 5, 9; UODO DKN.5112.6.2020, DKN.5112.33.2022 | MUST, DEMO |
| 10 | Authenticity check verifies chip signature and MRZ check digits, shows pass/fail only; legal basis confirmed by IOD | RODO art. 6(1)(e); ustawa o dowodach osobistych (UNVERIFIED) | MUST (IOD sign-off), DEMO |
| 11 | Large-print verification screen, keyboard and screen-reader operable | ustawa o dostępności cyfrowej (WCAG 2.1 AA); aim 2.2 AA | MUST, DEMO |
| 12 | Accessibility declaration (deklaracja dostępności) template for both apps | ustawa o dostępności cyfrowej | MUST, DEMO |
| 13 | AI drafts only; clerk must accept/edit per paragraph; nothing is sent or issued by AI | RODO art. 22; KPA art. 107 (UNVERIFIED); AI Act art. 14 as good practice | MUST, DEMO |
| 14 | Every AI draft carries source citations (statute article, request quote) and a visible "AI-generated draft" label | AI Act art. 50; transparency good practice | SHOULD, DEMO |
| 15 | No profiling, scoring or eligibility evaluation of citizens (keeps system out of Annex III 5(a)/6(3) profiling rule) | AI Act Annex III, art. 6(3) | MUST (to stay non-high-risk), DEMO |
| 16 | AI disclosure on any citizen-facing chat/assist feature | AI Act art. 50(1) (from 2 Aug 2026) | MUST, DEMO |
| 17 | Clerk AI-literacy note (one page) and usage policy | AI Act art. 4 as amended | SHOULD, DEMO |
| 18 | Provider-agnostic LLM adapter; real data only to EU/local endpoint; demo uses synthetic data; no training on prompts | RODO art. 28, 44 ff.; Anthropic data-residency docs | MUST, DEMO |
| 19 | Pseudonymisation gateway with checksum detectors (PESEL, IBAN), block-on-low-confidence, mapping kept in memory only | RODO art. 25, 32; EDPB 01/2025; C-413/23 P | SHOULD, DEMO |
| 20 | API-only access, no direct DB; OIDC SSO for clerks, scoped tokens, mTLS between services | KRI Dz.U. 2024 poz. 773; RODO art. 32 | MUST, DEMO |
| 21 | Immutable audit log of access, AI drafts, edits, signatures, prints; no field values in logs | RODO art. 5(2), 32; KRI | MUST, DEMO |
| 22 | Retention job: relay payloads, buffers, logs purged on schedule; case-file retention per wykaz akt | RODO art. 5(1)(e) | MUST, DEMO |
| 23 | Threat model (STRIDE) and security tests: rate limiting, CSP/HSTS, dependency scan, SBOM, secrets in vault | RODO art. 32; KSC/NIS2 risk management | SHOULD, DEMO |
| 24 | Cloud choice documented against SCCO; EU region or on-prem; processor agreement template (art. 28) | SCCO; RODO art. 28 | MUST (production) |
| 25 | Prior-consultation and rights-handling procedures (access, erasure) written for the office | RODO art. 15-22, 36 | MUST (production) |
| 26 | Evaluation set for UDIP drafting (accuracy, legal-citation correctness, hallucination rate) published with the repo | AI Act art. 15-style robustness as good practice | SHOULD, DEMO |

---

## Verdicts on the previous research

| ID | Verdict | Source and one-line correction |
|---|---|---|
| C18 | PARTLY | DKN.5112.6.2020 = ING Bank Śląski, PLN 18,416,400 (amount SECONDARY), WSA dismissed complaint 23 Oct 2026, not final; "5112.33.2022" is DKN.5112.33.2022 = Restaurant Partner Polska (Glovo), PLN 5,898,064, not final; both penalise ID scanning without necessity/legal basis, both against private firms. https://uodo.gov.pl/en/553/1990 ; https://bip.uodo.gov.pl/en/553/2206 |
| C19 | CONFIRMED | "aż 95,9% nie uważa się za przygotowane do wdrożenia AI zgodnie z RODO" from the "Badanie potrzeb organizacji" by UODO's Społeczny Zespół Ekspertów (not a general poll of all organisations); page dated 2026-08-05, updated 2026-08-28. https://uodo.gov.pl/pl/138/4533 |
| C20 | PARTLY | The UODO "Listy pytań inicjalnych" exist (four sets, including a public-sector version) and are real; the ai.gov.pl article "AI w urzędzie: od czego zacząć" could not be found or fetched, so the reference link is unverified. https://uodo.gov.pl/pl/138/4533 |
| C21 | PARTLY | Annex III obligations moved to 2 Dec 2027 by Regulation (EU) 2026/1744 (OJ 24 Jul 2026, in force 27 Jul 2026), confirmed by secondary sources; FRIA (art. 27) moves with it; art. 4 AI literacy applied from 2 Feb 2025 but the Omnibus recast it as "take measures supporting AI literacy". https://www.lewissilkin.com/insights/2026/07/27/the-digital-omnibus-on-ai-enters-into-force-today |
| C22 | CONFIRMED | Art. 37(1)(a) RODO (public authority must designate an IOD), art. 38(1) involvement, art. 35(2) advice in a DPIA; text known, eur-lex not re-opened this session. |
| C23 | PARTLY | Correct: first-party API has only `global` and `us` geo, workspace geo US only; ZDR by contract per org, Batch (29 days) and Files API not covered; Covered Models (Fable/Mythos 5.x) mandatory 30 days; flagged content up to 2 years (7 years for classification scores). Needs nuance: 30-day default is stated on privacy.claude.com while the platform page says content is "not retained by default" apart from Covered Models; EU residency exists on Bedrock EU profiles (SECONDARY), whereas "Vertex AI EU" holds only for the Google-managed flavour, and Anthropic-managed Google Cloud is US-only. https://platform.claude.com/docs/en/manage-claude/data-residency ; https://platform.claude.com/docs/en/manage-claude/api-and-data-retention |

## Open questions and what could not be verified

- Text of Regulation (EU) 2026/1744 itself (OJ L 2026/1744): only law-firm summaries read; eur-lex not opened. Art. 27, art. 4 final wording not re-read.
- ELI page of the Polish AI act (Dz.U. 2026 poz. 1003): fetch failed (HTTP 500); dates come from search summaries of Sejm, ELI and gov.pl pages. Provisions on offices as deployers not read.
- Whether gminas are "podmioty publiczne" within the NIS2 amendment annexes and which category: gov.pl page only says "Podmioty publiczne"; Wykaz KSC (wykaz-ksc.gov.pl) was not checked.
- KRI paragraph-level requirements (logging, SZBI, passwords) not read; SCCO adopted version, levels and data-centre jurisdiction criteria not read.
- UDIP act article numbers (5(2), 13, 16), KPA art. 107, ustawa o dokumentach publicznych art. 58 text, ustawa o dowodach osobistych rules on reading the e-layer: not opened. Check isap.sejm.gov.pl / api.sejm.gov.pl ELI.
- Anthropic DPA and SCC text; Bedrock EU profile availability per model and whether Anthropic sees prompts there; Vertex AI EU availability.
- Final status of EDPB Guidelines 01/2025; the CJEU judgment text (C-413/23 P) on curia.europa.eu was not opened.
- Whether UODO or any court issued a 2025-2026 decision about a public authority scanning IDs: none found in the searches (uodo.gov.pl pages, general web). Date of the ING decision unverified.
- ai.gov.pl article "AI w urzędzie: od czego zacząć" not found (gov.pl/web/ai paths returned a homepage); mObywatel verification route for identity and PLLuM hosted access for administrations not researched.

## Sources

- https://uodo.gov.pl/pl/138/4533 (UODO checklists, read via curl; TLS error in WebFetch)
- https://uodo.gov.pl/en/553/1990 (ING decision summary, DKN.5112.6.2020)
- https://bip.uodo.gov.pl/en/553/2206 (Glovo / Restaurant Partner Polska decision summary, DKN.5112.33.2022)
- https://www.telepolis.pl/fintech/uodo-kara-bank-ing-skanowanie-dowodow
- https://www.telepolis.pl/wiadomosci/uodo-kara-dla-glovo-dane-osobowe-skany-dokumentow
- https://bezprawnik.pl/skanowanie-dowodu-osobistego/ (search result, not opened)
- https://www.prawo.pl/kadry/ksero-dowodu-dozwolone-przetwarzanie-danych-nie,441907.html (search result, not opened)
- https://bip.brpo.gov.pl/sites/default/files/2025-08/Odpowiedz_PUODO_dowod_osobisty_dane_biometryczne_1_08_2025.pdf (not opened)
- https://eli.gov.pl/api/acts/MP/2019/666/text/O/M20190666.pdf (UODO DPIA list, not opened)
- https://www.lewissilkin.com/insights/2026/07/27/the-digital-omnibus-on-ai-enters-into-force-today
- https://www.whitecase.com/insight-alert/eu-ai-omnibus-enters-force-amending-ai-act (search result; fetch 403)
- https://www.orrick.com/ja-JP/Insights/2026/07/EU-AI-Act-Update-Digital-Omnibus-Finalizes-8-Compliance-Changes (search result)
- https://artificialintelligenceact.eu/annex/3/ ; https://artificialintelligenceact.eu/article/6/
- https://www.gov.pl/web/cyfryzacja/koniec-ery-nieuchwytnych-algorytmow--projekt-ustawy-o-systemach-sztucznej-inteligencji-przyjety-przez-rade-ministrow ; https://eli.gov.pl/eli/DU/2026/1003 (fetch failed)
- https://samorzad.gov.pl/web/gov/przewodnik-po-sztucznej-inteligencji-dla-administracji-publicznej ; https://www.gov.pl/attachment/7c30aa1a-c191-49dd-acb4-bca4b5e4c308 ; https://nask.pl/media/2026/03/AI-w-administracji-publicznej_.pdf
- https://www.gov.pl/web/cyfryzacja/nowelizacja-ustawy-o-krajowym-systemie-cyberbezpieczenstwa-ksc---kogo-obejmuje
- https://eli.gov.pl/eli/DU/2024/773 (KRI, search result)
- https://www.gov.pl/web/cyfryzacja/standardy-cyberbezpieczenstwa-chmur-obliczeniowych ; https://www.gov.pl/web/cyfryzacja/przyjeto-nowe-standardy-cyberbezpieczenstwa-chmur-obliczeniowych--najwazniejsze-zmiany
- https://www.gov.pl/web/dostepnosc-cyfrowa ; https://digital-strategy.ec.europa.eu/pl/policies/latest-changes-accessibility-standard
- https://platform.claude.com/docs/en/manage-claude/data-residency ; https://platform.claude.com/docs/en/manage-claude/api-and-data-retention ; https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data ; https://trust.anthropic.com/resources
- https://docs.aws.amazon.com/bedrock/latest/userguide/geographic-cross-region-inference.html ; https://aws.amazon.com/blogs/machine-learning/unlocking-ai-flexibility-in-europe-a-guide-to-cross-region-inference-for-eu-data-processing-and-model-access/
- https://huggingface.co/CYFRAGOVPL/models ; https://arxiv.org/abs/2511.03823 ; https://science.nask.pl/en/news/12757
- https://huggingface.co/speakleash/bielik-11b-v3.0-instruct ; https://osai-index.eu/model/bielik ; https://arxiv.org/abs/2601.11579
- https://edpb.europa.eu/news/news/2025/edpb-adopts-pseudonymisation-guidelines-and-paves-way-improve-cooperation_en ; https://www.edpb.europa.eu/system/files/2025-12/stakeholder-event-20251212-discussion-paper_en.pdf
- https://www.cliffordchance.com/insights/resources/blogs/talking-tech/en/articles/2025/09/pseudonymized-data-after-edps-v-srb.html ; https://www.fieldfisher.com/en-be/locations/belgium/insights/edps-v-srb-cjeu%e2%80%99s-contextual-approach-to-pseudonym
