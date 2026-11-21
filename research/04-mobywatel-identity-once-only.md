# R4 - mObywatel, mDowód, login.gov.pl, state registers, EUDI Wallet and once-only: what can feed citizen data into a city-office form-prefill system (status 21 Nov 2026)

Access date for all sources: 2026-11-21. Legend: VERIFIED = primary source opened and read (full text or official page); SECONDARY = reliable secondary / search-result-level only; UNVERIFIED = could not open or find. Budget was limited (45 calls); gaps are listed in section 9.

## TL;DR for builders

- There IS an mObywatel flow exactly like the owner imagined: "Przekaż instytucji" (mTożsamość tab): the institution shows a QR code (on a website or on site), the citizen scans it in mObywatel, sees which institution gets which data, confirms, and the institution receives the data set. Launched 22 July 2020 with PZU; the ministry invited local governments and companies to join via mobywatel@mc.gov.pl. VERIFIED (gov.pl 2020 article, via fetch). Current 2026 onboarding terms, attribute list, cost, API docs: NOT publicly found = UNVERIFIED.
- There is no public, self-service developer API or sandbox for that flow. Plan for "integration-ready adapter + mock", not for a live connection tomorrow. Do not claim a live mObywatel integration in the demo.
- Verification of the document itself (mDowód) is a separate, public flow: the verifier (any person or institution) shows or scans a QR / 6-digit code, the citizen approves a data scope, the verifier sees data for a few minutes, nothing is stored; web verifier at weryfikator.mobywatel.gov.pl. VERIFIED (gov.pl page). It is a human-in-the-loop check, not a documented machine API.
- Legal status of mDowód: act of 26 May 2023 (Dz.U. 2023 poz. 1234), art. 7 ust. 4: where law requires proof of identity "w szczególności na podstawie dowodu osobistego", the duty is met by an mObywatel document. Art. 7 ust. 5: no border crossing; not usable where certainty/security cannot be ensured. Not usable to apply for a new dowód osobisty (gov.pl statement; statutory article not opened). VERIFIED / SECONDARY as marked.
- login.gov.pl (Węzeł Krajowy) gives only a minimal identity set (surname, first name, date of birth, unique identifier; PESEL only where the service is authorised/at the right assurance level - not confirmed). Protocol SAML 2.0; public entities use login.gov.pl, private entities podmiotyzewnetrzne.login.gov.pl; application via ePUAP to KPRM. VERIFIED (gov.pl) / SECONDARY (search snippets).
- A gmina clerk already works through ŹRÓDŁO (SRP: PESEL, RDO, BUSC, RDK...). Own systems can connect by WebServices (forms B/E/F on gov.pl "Jak uzyskać dostęp do SRP"); verification services return yes/no only; you must declare whether the system stores the data. VERIFIED. Bydgoszcz's own IT department decides this; a hackathon prototype must NOT touch these registers.
- Once-only (art. 220 KPA, SDG art. 14 OOTS) forbids demanding from the citizen what the office can get from registers; it does NOT create a lawful basis for a new shared citizen database. Lawful design: citizen-held data shared on demand + register look-ups under a legal basis + ephemeral processing (session-only, no persistence). Analysis (legal opinion, not law text).
- EUDI Wallet: Regulation (EU) 2024/1183 art. 5a(1): each Member State provides at least one wallet within 24 months of entry into force of the implementing acts. VERIFIED (EUR-Lex). Poland: wallet inside the mObywatel ecosystem; sandbox EPTC opened 16 Sep 2026 with a demo app "mObywatel Europa" and a web verifier (QR); bill on the European Digital Identity Wallet adopted by the government 17 Nov 2026 (register of relying parties). VERIFIED (gov.pl) / SECONDARY.
- Design the identity layer as an "Identity Source Adapter" interface with implementations: (1) manual entry, (2) document OCR/clerk verify, (3) mObywatel "Przekaż instytucji"/verifier, (4) EUDI OpenID4VP, (5) login.gov.pl. For the hackathon ship 1, 2 and a MOCK of 3/4 with the same JSON contract.
- Open-source starting point for the EUDI/OpenID4VP side: EU reference verifier endpoint `eudi-srv-web-verifier-endpoint-23220-4-kt` (Kotlin/Spring Boot, Apache-2.0, OpenID4VP 1.0, SD-JWT VC and mso_mdoc, POST /ui/presentations returns QR PNG). The README says not for production and has no access control on the verifier API. VERIFIED (GitHub README).
- e-Doręczenia is the main official delivery channel from 1 Jan 2026 (transition ended 31 Dec 2025); ePUAP is NOT switched off (mailbox maintenance rules reported to 30 Sep 2029). VERIFIED (gov.pl) for the former; SECONDARY for 2029.

---

## 1. mObywatel today

### 1.1 Legal status of mDowód (ustawa z dnia 26 maja 2023 r. o aplikacji mObywatel, Dz.U. 2023 poz. 1234, as amended; a consolidated text in Dz.U. 2026 poz. 1232 was reported by search - not opened)

Read directly from the act text on api.sejm.gov.pl (VERIFIED, https://api.sejm.gov.pl/eli/acts/DU/2023/1234/text.html; note this is the 2023 published text - later amendments are not reflected):

| Provision | Content (Polish key phrases) | Meaning |
|---|---|---|
| art. 2 pkt 8 | "dokument mobilny stwierdzający tożsamość i obywatelstwo polskie" (via fetch summary, SECONDARY wording) | mDowód is a mobile identity document |
| art. 7 ust. 1 | dokument mObywatel contains: nazwisko, imię/imiona, PESEL, data urodzenia, obywatelstwo, imię ojca, imię matki (from Rejestr PESEL); fotografia (from Rejestr Dowodów Osobistych); numer, seria, data wydania, termin ważności | Attribute set of the document |
| art. 7 ust. 2 | issued automatically after identity established, for 5 years | |
| art. 7 ust. 4 | "Jeżeli z przepisu prawa wynika obowiązek stwierdzenia tożsamości lub obywatelstwa polskiego na podstawie dokumentu tożsamości, w szczególności na podstawie dowodu osobistego, obowiązek ten uznaje się za spełniony..." on the basis of mObywatel document | Equivalence to dowód osobisty |
| art. 7 ust. 5 pkt 1 | "nie uprawnia do przekraczania granicy państwowej" | Border: no |
| art. 7 ust. 5 pkt 2 | may not be used where circumstances do not ensure necessary certainty and security | Open-ended exclusion |
| art. 7 ust. 6 | Council of Ministers sets by regulation the cases where it cannot be used | Delegation |
| art. 9 ust. 1-2 | document handed over for verification is signed with the user certificate; verifier may check (1) data, (2) advanced electronic seal of the minister, (3) signature with user certificate, (4) visual security features, (5) correct functioning of the service handling the document | The five statutory verification means |
| art. 5 ust. 1-2 | public entity enables the user to download data from its register through the app; and enables the minister to integrate the mObywatel system with its system | Data flows INTO the app from registers |
| art. 3 ust. 1 | services in the app let the user download data from registers; (a further point allowing the user to pass data to others was reported by a fetch summary - not verified by me) | |
| art. 19 ust. 1 pkt 7 | minister provides the "mWeryfikator" app and a dedicated online verification service | Verifier tools are statutory |

Where it cannot be used (VERIFIED on gov.pl notice dated 24 July 2023, https://www.gov.pl/web/cyfryzacja/przypominamy-urzedy-w-polsce-maja-obowiazek-uznawac-mdowod): applying for a new dowód osobisty; crossing the border; matters at institutions covered by the AML act (banks etc.) - the notice says from 1 September 2023. Effective date of the new rules: 14 July 2023. The notice does not name the article that imposes the acceptance duty; the duty follows from art. 7 ust. 4 (equivalence) read with the rule that the office may not insist on a physical card. The statutory article forbidding the municipal body to confirm identity for a new ID by mDowód is in the ustawa o dowodach osobistych (not opened; a fetch summary cited "art. 29a ust. 2a" - treat as UNVERIFIED).
The Council of Ministers regulation under art. 7 ust. 6: not found (searched api.sejm/ISAP via search); status UNVERIFIED.

### 1.2 Verification methods - exactly how they work

Ministry naming (SECONDARY from gov.pl snippets, consistent with the case study at Interoperable Europe): three methods - wizualna (visual), funkcjonalna (functional), kryptograficzna (cryptographic).

| Method | How it works | Statutory hook (art. 9 ust. 2) | Strength |
|---|---|---|---|
| Wizualna | Clerk looks at the app screen: animated flag, hologram-like elements, date/time, photo, shaking/animation effects | pkt 4 zabezpieczenia wizualne | Weakest; forgeable by screen mock-ups |
| Funkcjonalna | Check that the app behaves as the real one (e.g. the document refreshes, "Odśwież", responds to touch, shows current time) | pkt 5 poprawność funkcjonowania usługi | Weak-medium |
| Kryptograficzna | Verifier and holder use mObywatel/web verifier. QR (or 6-digit code) shown by the holder is scanned/typed by the verifier; holder sees the data scope and approves; verifier screen shows data for a few minutes, not stored on the verifier's device; data fetched in real time from the state register; devices do not connect directly | pkt 1-3 (data, ministerial seal, user certificate signature) | "Most reliable" per the ministry |

Source for the cryptographic flow: https://www.gov.pl/web/cyfryzacja/kod-qr--skuteczna-metoda-weryfikacji-mdowodu (VERIFIED, opened). Web verifier: weryfikator.mobywatel.gov.pl (VERIFIED in the same page). Descriptions of the visual/functional features above are my explanation from general knowledge of the app and the statutory wording; the gov.pl page I opened covers only the cryptographic method - mark SECONDARY.

### 1.3 Verification and data-sharing for institutions - what exists

1. mWeryfikator / web verifier (document verification): public to any person who needs to verify (offices, shops, election commissions). Free. Flow: holder shows QR/6 digits - see 1.2. Returns the data the holder approves (identity data, age confirmation); exact attribute list not on the opened page (UNVERIFIED). No documented machine API, no onboarding agreement found. The ministry ran trainings for officials ("Jak sprawdzić mDowód drugiej osoby", gov.pl) (SECONDARY, title only).
2. "Przekaż instytucji" (institution scans nothing; the CITIZEN scans the institution's QR). VERIFIED at https://www.gov.pl/web/cyfryzacja/nowe-funkcjonalnosci-mobywatela: in mTożsamość the user selects "Przekaż instytucji" (later UI wording: "Przekaż" -> "Instytucji lub firmie", SECONDARY) and scans the code the institution provides on its website or on site; the user sees which institution gets which data and confirms ("Potwierdzam"); the participating institution can generate unique codes; the ministry says code substitution is not possible. First deployer: PZU (mojePZU). The article says other offices, companies, universities may join, and instructs institutions to contact mobywatel@mc.gov.pl; it names local governments specifically. Use cases listed: registering with an institution, confirming identity, submitting forms, receiving documents. Attribute list, contract type (umowa/porozumienie with the Minister of Digital Affairs/COI), price, onboarding time, sandbox: NOT PUBLISHED in anything I could open = UNVERIFIED. The 2020 article is old; whether the flow was renamed or restructured in 2026 (mObywatel 2.0, 26.x terms) is UNVERIFIED. The user terms (Regulamin aplikacji mObywatel 26.0.0, https://www.gov.pl/attachment/a3f74ecd-21a7-4579-b3bc-24c2ea5164d2) describe voluntary data transfer to institutions - not opened in full.
3. Other relying-party style integrations that exist: logging in to e-Urząd Skarbowy and some services with mObywatel by scanning a QR (SECONDARY); bank/AML identity checks (excluded for mDowód alone).

Answer to "does the flow the owner imagined exist": YES, as "Przekaż instytucji", for institutions that have onboarded with the ministry/COI; for a city office onboarding is by contacting the ministry; no public sandbox or API documentation was found. Whether it accepts "family data" (spouse, children) is UNVERIFIED; art. 3 ust. 1 lit. d of the act lets a parent download data about a minor child into the app (VERIFIED in the act text read), which suggests the data model can carry children's data, but sharing it onward is not confirmed.

## 2. login.gov.pl, Profil Zaufany, e-dowód

### 2.1 login.gov.pl (Węzeł Krajowy Identyfikacji Elektronicznej)
- Who: public entities that provide online services requiring authentication must connect; page "Dla integratorów" https://www.gov.pl/web/login/dla-integratorow (VERIFIED) lists the minimum returned set (encrypted): current surname(s), first name(s), date of birth, unique identifier. PESEL release depends on the means and the service configuration - not confirmed (UNVERIFIED).
- Environments and protocol: SAML 2.0 (artifact binding), XML Signature/Encryption; int.login.gov.pl (integration), login.gov.pl (public entities, production), podmiotyzewnetrzne.login.gov.pl (private entities) - SECONDARY (search snippet of the integration guide and a third-party package). OIDC not confirmed.
- Onboarding: application sent via ePUAP to the Departament Rozwoju Usług in KPRM; integrator buys own certificates and uploads them to the "Współpraca Cyfrowa Tożsamość" portal - SECONDARY. Documentation: https://mc.bip.gov.pl/interoperacyjnosc-mc/wezel-krajowy-dokumentacja-dotyczaca-integracji-z-wezlem-krajowym.html (URL taken from the verified gov.pl page; not opened). Node stores no personal data except a minimal incident-reconstruction log (VERIFIED on the same page).
- Fit for the product: good for authenticating a citizen on the mobile page (assurance low/substantial/high via Profil Zaufany, mObywatel, e-dowód, bank login) but returns too little to pre-fill a family wniosek. Use it for identity binding, not as the data source.

### 2.2 e-dowód (warstwa elektroniczna)
- Chip read is contactless (NFC); access protected by CAN (printed on the card) plus PIN1 (4 digits, online identity/authentication certificate) and PIN2 (6 digits, personal signature). VERIFIED in the regulation text opened (https://api.sejm.gov.pl/eli/acts/DU/2022/1431/text.html) for CAN + 4-digit PIN1 to use the identification and authentication certificate; PIN2 described in gov.pl material (SECONDARY).
- Gmina offices already use card readers per the MSWiA "specyfikacja wymagań dla czytników kart e-dowodu dla urzędów gmin" (version 6.0, 12 Feb 2024, SECONDARY - title only). Whether a third-party app may read the electronic layer data group for a clerk's use: the legal basis lies in the ustawa o dowodach osobistych (art. 12a describes the contents - SECONDARY; no article on reading by offices was confirmed). UNVERIFIED: do not promise "read the chip" in the demo; present it as an adapter slot ("e-dowód reader") requiring a legal opinion from the office's IOD.
- Use of the chip for authentication in the app (user holds the card to the phone, enters CAN + PIN1) is supported by mObywatel (activation of e-dowód in the app; PIN changes via NFC since app 4.74 - SECONDARY, android.com.pl). Technically the same NFC flow is available to private apps only through an authorised eID provider - not through direct chip access.

### 2.3 Profil Zaufany
Remains an authentication means connected to Węzeł Krajowy (assurance substantial/high depending on method). Transition toward mObywatel as the main means is ongoing; exact 2026 status UNVERIFIED.

## 3. State registers a gmina clerk already uses

VERIFIED at https://www.gov.pl/cyfryzacja/jak-uzyskac-dostep-do-srp (opened):
- ŹRÓDŁO is the web application through which gmina and civil-registry staff access the System Rejestrów Państwowych: Rejestr PESEL, Rejestr Dowodów Osobistych (RDO), Baza Usług Stanu Cywilnego (BUSC), Centralny Rejestr Sprzeciwów, System Odznaczeń Państwowych, Rejestr Danych Kontaktowych (RDK) (SECONDARY snippet of an attached instruction).
- Access forms: A (gmina employees in ŹRÓDŁO), B (entities with a decision for PESEL/RDO data via WebServices with own system), E (producers of alternative applications for local governments, to test WebService solutions), F (gminas connecting own systems by WebServices), G (local administrator). Applications go to COI Łódź.
- WebService types: search, verification, sharing, subscription; verification returns only yes/no; the applicant declares whether the system stores retrieved data or only displays it (SECONDARY snippet of the form instructions).
- Consequence: yes, a gmina can integrate its own systems with PESEL/RDO by web services (form F) - an agent for the office would be a vendor of such a system and must file form E for tests. Legal basis for sharing within one office: each department uses the registers under its own task-specific statutory basis (e.g. ustawa o ewidencji ludności, ustawa o dowodach osobistych); cross-department reuse is lawful only for a purpose covered by the task and within the authorisations - there is no blanket "same office" permission (analysis; statute not opened - UNVERIFIED).
- Hackathon rule: never connect to real registers; use synthetic data and a fake "register adapter" with the same shape as the service contract.

## 4. Once-only principle and the "one shared citizen database" idea

- Art. 220 KPA (opened via arslege.pl summary, SECONDARY; exact wording not read verbatim): § 1 an authority may not demand a certificate or declaration confirming facts or legal status if it knows them ex officio or can establish them from its own records, public registers accessible electronically, exchange with other public entities, or an official document shown (ID, vehicle registration); § 2 where it demands one, it must cite the provision that requires such a form; § 3 electronic copies may be authenticated with kwalifikowany podpis, Profil Zaufany or podpis osobisty. Source: https://arslege.pl/kodeks-postepowania-administracyjnego/k3/a810/.
- Ustawa o informatyzacji działalności podmiotów realizujących zadania publiczne (17 Feb 2005): obliges entities to exchange data electronically instead of asking the citizen - specific article (e.g. art. 5, art. 13) not verified (UNVERIFIED).
- SDG Regulation (EU) 2018/1724 art. 14: Once-Only Technical System (OOTS) for cross-border evidence exchange, mandatory for the listed procedures since 12 Dec 2023 (the deadline commonly cited; not independently confirmed here). Poland status: an EC OOTS news item (26 Oct 2026) says Poland connects its first procedure to the business portal (title only, SECONDARY). Interoperable Europe Act (Reg. (EU) 2024/903): interoperability assessments and cooperation; not a data-sharing authorisation. Only a general mention; not opened.
- Why a new central citizen database is not the lawful route (analysis): (1) every processing needs a legal basis and a purpose limit (RODO art. 5, 6(1)(e)); (2) the Polish state already operates the authoritative sources (PESEL, RDO, SRP); duplicating them creates a new controller, new retention duty, and an attractive breach target; (3) once-only is implemented by pulling from sources with a legal basis, not by a copy; (4) a citizen's self-entered family data are not an "authentic source" and would not satisfy art. 220 KPA unless the clerk verifies them.
- Lawful alternatives to build: (a) citizen-held data shared on demand (mObywatel Przekaż instytucji, EUDI wallet presentation, or session-only self-entry by QR page); (b) register look-ups by the office under its own legal basis, through the office's SRP connection, never by the prototype; (c) ephemeral processing: data live in memory/encrypted short-TTL session store tied to one visit, wiped after the print/signing step; only the filled wniosek enters the office's own EZD/records (the office's data, the office's retention); (d) audit log without payload.

## 5. EUDI Wallet (Regulation (EU) 2024/1183)

| Item | Finding | Status |
|---|---|---|
| Wallet provision deadline | art. 5a(1): each Member State provides at least one EUDI Wallet within 24 months of entry into force of the implementing acts referred to in art. 5a(23) and art. 5c(6); press quotes 24 Dec 2026 | VERIFIED text (eur-lex https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202401183); date SECONDARY |
| Private relying parties | art. 5f: those required to use strong authentication (banking, transport, energy, telecom, etc., excl. micro and small) must accept wallets within 36 months of entry into force of the implementing acts (press: Dec 2027) | VERIFIED text (part), date SECONDARY |
| Public sector acceptance | Obligation for public bodies under national rules; for Poland governed by the national act | SECONDARY |
| Relying party registration | art. 5b; relying parties identify themselves with access certificates; Implementing Reg. 2025/848 sets registration rules | SECONDARY |
| Poland - wallet | Inside the mObywatel ecosystem; the case study describes phase 1 as a separate pilot app and a later integration, with a possible 2028 date as an estimate; chip.pl reported a separate app linked to mObywatel | SECONDARY, partly conflicting |
| Poland - sandbox EPTC | Opened 16 Sep 2026 by the Ministry and COI; free; demo app "mObywatel Europa" (Android/iOS), web verifier that generates a QR; test identity data; application via form at https://info.mobywatel.gov.pl/eidas-2/dolacz-do-sandboxa (requires signed statement and proof of representation; result by e-mail; contact eidas.sandbox@cyfra.gov.pl); about 80 applicants (another source: 61) | SECONDARY (search snippets of gov.pl/mObywatel/COI pages; form page itself returned empty) |
| Poland - law | Draft act on the European Digital Identity Wallet adopted by the Council of Ministers; article dated 17 Nov 2026: register of relying parties, voluntary use, Minister of Digital Affairs responsible, wallet part of mObywatel; entry into force not stated | VERIFIED (gov.pl, https://www.gov.pl/web/cyfryzacja/rzad-przyjal-projekt-ustawy-o-europejskim-portfelu-tozsamosci-cyfrowej) |

Protocols (general standards, not Polish-specific confirmation): OpenID4VP (presentation to a verifier, also by QR / deep link), OpenID4VCI (issuance), ISO/IEC 18013-5 (mdoc proximity and remote), SD-JWT VC and mso_mdoc credential formats, HAIP profile. The Polish profile for relying parties: UNVERIFIED.

Relying-party QR flow (as implemented by the EU reference verifier): the verifier backend creates a transaction with a DCQL query (which attributes), returns request_uri + QR; the wallet scans, shows the requested attributes to the user, the user approves, the wallet posts a vp_token to the verifier; the verifier validates signatures and trust chain and returns the claims to the office app. VERIFIED mechanics from the README of the reference verifier.

Open-source building blocks:
- https://github.com/eu-digital-identity-wallet/eudi-srv-web-verifier-endpoint-23220-4-kt - Kotlin/Spring Boot verifier endpoint, Apache-2.0, OpenID4VP 1.0, `profile` openid4vp or haip, SD-JWT VC and mso_mdoc; POST /ui/presentations with dcql_query, nonce, jar_mode, response_mode; `Accept: image/png` returns a QR PNG; Docker image ghcr.io/eu-digital-identity-wallet/eudi-srv-verifier-endpoint; README: not comprehensively documented, not for production, verifier API has no access control (put it behind your own gateway). VERIFIED.
- EU reference wallet apps (Android/iOS) from the same GitHub organisation; entry page https://eu-digital-identity-wallet.github.io/ (SECONDARY).
- Others named in search results, NOT verified for licence/maintenance: walt.id (waltid-openid4vc), Sphereon SIOP-OpenID4VP, @openeudi/core (TypeScript), Tessio.Verifier.OpenId4Vp (NuGet), a PHP package. Check each before use.
- German reference material for relying-party onboarding: https://bmi.usercontent.opencode.de/eudi-wallet/developer-guide/ (SECONDARY; a model, not Polish docs).

### Identity Source Adapter (design)

```
interface IdentitySourceAdapter {
  id: "manual" | "document-ocr" | "mobywatel-share" | "eudi-openid4vp" | "login-gov-pl" | "e-dowod-reader"
  startSession(visitId, requestedAttributes[], purpose): { qrPayload?, expiresAt }
  poll|callback(sessionId): { status, claims: {name, value, assurance, sourceId, verifiedAt}[] }
  evidence(): { method, issuer?, timestamp, signatureValid? }
}
```
Rules: every claim carries provenance (source, assurance level, timestamp) so the form pre-filler and the clerk see "verified by mObywatel" vs "typed by citizen"; claim names mapped to one internal profile schema (JSON Schema) so that mObywatel mDowód attributes (art. 7 ust. 1), EUDI PID attributes and manual fields converge; consent record per session; TTL wipe; no adapter returns more than the requested attribute set (data minimisation, RODO art. 5(1)(c)).

## 6. QR data-exchange precedents and channels in 2026

- "Przekaż instytucji" (PZU 2020) - see 1.3.
- mDowód verification with QR (elections 2025: ministry guidance for election commissions - gov.pl page title found; election identity verification via mObywatel, SECONDARY).
- Nocleg z mObywatelem (hotel check-in): a gov.pl page "Nocleg z mObywatelem" exists (https://www.gov.pl/web/cyfryzacja/nocleg-z-mobywatelem); contents not opened - the nature of the hotel pilot is UNVERIFIED.
- mStłuczka (accident report between two drivers in mObywatel): exists as a service in the app (SECONDARY, gov.pl service list, no details read); a precedent of two citizens exchanging a data set by QR; mechanism UNVERIFIED.
- Login to e-Urząd Skarbowy by scanning a QR with mObywatel (SECONDARY).
- e-Doręczenia: per https://www.gov.pl/web/cyfryzacja/zmiany-w-e-doreczeniach-dla-podmiotow-publicznych (VERIFIED): public entities needed an active ADE address from 1 Jan 2025; transition ended end of 2025; from 1 Jan 2026 e-Doręczenia is the standard channel between public and non-public entities; ePUAP is not switched off; the fiction of delivery via ePUAP to non-public entities ends. Citizen side: https://www.gov.pl/web/cyfryzacja/od-nowego-roku-e-doreczenia-podstawowym-kanalem-komunikacji-z-urzedami-co-to-oznacza-dla-obywateli (VERIFIED): to send electronic applications to offices a citizen needs an e-Doręczenia address (may be offered during e-service use). ePUAP mailboxes: official FAQ reportedly says maintenance duty until 30 Sep 2029 (SECONDARY). Mandatory e-Doręczenia for CEIDG firms from 1 Oct 2026 (SECONDARY, Infor).
- Rejestr Danych Kontaktowych (RDK): available to offices in ŹRÓDŁO (SECONDARY snippet); the e-Doręczenia address database ("baza adresów do doręczeń elektronicznych") is the lookup used to deliver. Details UNVERIFIED.

Implication for the product: the clerk's outgoing answer to a UDIP request should be built to leave through e-Doręczenia first (with fallbacks e-mail with the applicant's chosen address per art. 14 ust. 2 ustawy o dostępie do informacji publicznej - R2's domain, not re-verified here).

## 7. Conclusion for tomorrow's demo

| Show with no agreement | Present as integration-ready (mock + contract) | Do not claim |
|---|---|---|
| Citizen mobile page by QR at the desk: self-entry, session-only | "Przekaż instytucji / mObywatel verifier" adapter: same JSON contract, mock responder, clearly labelled SIMULATION | Live mObywatel data, real registers, a signed agreement with COI |
| Clerk screen verifying recognised ID data in very large print (OCR from synthetic ID or typed) | EUDI OpenID4VP adapter running against the open-source EU reference verifier with the EU reference wallet or a mock wallet; same QR UX | Reading the e-dowód chip as a lawful office function |
| Form chain and pre-fill from one profile, print as official template | login.gov.pl as authentication adapter (SAML) - architecture slide only | "mDowód replaces a dowód for everything" (exceptions: new ID, border, AML) |
| AI checks of filled forms; UDIP assistant (hackathon core) | SRP/ŹRÓDŁO read-only adapter stub ("verification yes/no" semantics) | Central citizen database |

Fake data discipline: synthetic persons only; mark every screen "DEMO - dane fikcyjne".

### Proposal to the Ministry of Digital Affairs (suggested wording, English with Polish key line)

Title: "Wypełnij wniosek z mObywatela" - a relying-party flow for city offices.
1. Problem: citizens re-type the same personal and family data in every wniosek; the office re-types it again; art. 220 KPA and the once-only principle say the office should not ask for what the state already holds.
2. Proposal: pilot with Miasto Bydgoszcz. The clerk's system shows a one-time QR; the citizen opens mObywatel "Przekaż instytucji" (or later the EUDI wallet via OpenID4VP), sees a named purpose ("Wniosek o ... w Urzędzie Miasta Bydgoszczy") and an explicit attribute list (imię, nazwisko, PESEL, data urodzenia, adres zameldowania, dane dzieci - only those needed), confirms; the data reach the office session only and are used to pre-fill the chain of wnioski; nothing is stored beyond the generated wniosek.
3. Asks to the Ministry/COI: (a) accept the city as a pilot institution for "Przekaż instytucji" with a purpose-bound attribute catalogue; (b) provide sandbox credentials and technical documentation (the public sources show none); (c) confirm the legal basis for a clerk's system to receive a parent's and children's data from the app; (d) include the pilot in the EPTC sandbox track as a public-sector relying party; (e) name a technical contact at COI.
4. Offer: open-source adapter layer (Apache-2.0 or compatible), data-protection impact assessment template, security test results, and a report of citizen/clerk time saved.
5. Closing line (PL): "Prosimy o rozważenie pilotażu usługi 'Wypełnij wniosek z mObywatela' w Urzędzie Miasta Bydgoszczy jako przykładu zasady jednorazowego podawania danych (once-only)."
Contact for the ask: mobywatel@mc.gov.pl (2020 article, UNVERIFIED for 2026) and eidas.sandbox@cyfra.gov.pl (SECONDARY).

## 8. Verdicts on the previous research

| ID | Verdict | Source and correction |
|---|---|---|
| C11 | CONFIRMED (secondary for the statute) | gov.pl notice 24 Jul 2023 lists "wniosek o nowy dowód" among exclusions: https://www.gov.pl/web/cyfryzacja/przypominamy-urzedy-w-polsce-maja-obowiazek-uznawac-mdowod ; the exact article in the dowody osobiste act not opened. |
| C16 | PARTLY | Equality: act art. 7 ust. 4 (VERIFIED, https://api.sejm.gov.pl/eli/acts/DU/2023/1234/text.html); effective 14 Jul 2023 (gov.pl). Correction: the equivalence is a statutory fiction of fulfilled duty "gdy przepis wymaga stwierdzenia tożsamości", with exceptions: border (art. 7 ust. 5 pkt 1), cases of insufficient certainty (pkt 2 and a Council of Ministers regulation), new ID, and AML-covered institutions (from 1 Sep 2023, gov.pl). "Must accept" is the ministry's reading, not a named article. |
| C17 | PARTLY | Three ministry-named methods are wizualna, funkcjonalna, kryptograficzna; the QR-code method IS the cryptographic one (gov.pl QR page), not a separate "functional" one. The act itself lists five means in art. 9 ust. 2 (data, seal, user-certificate signature, visual features, functioning of the service). |
| C24 | PARTLY | Transition ended 31 Dec 2025; from 1 Jan 2026 e-Doręczenia is the basic channel for public bodies (VERIFIED, gov.pl). But ePUAP did not end: it still works where special provisions apply and the duty to keep ePUAP mailboxes is reported to run to 30 Sep 2029 (SECONDARY). |

## 9. Open questions and what could not be verified

- Whether "Przekaż instytucji" is open to a city office in 2026: terms, agreement type (umowa/porozumienie), attribute catalogue, family data, cost, onboarding time, sandbox, public docs. Looked at: gov.pl mObywatel pages, 2020 launch article, sandbox pages (form page returned no text). Ask mobywatel@mc.gov.pl / COI.
- Statutory article about reading the e-dowód chip by offices; Council of Ministers regulation under art. 7 ust. 6 mObywatel act; article in the dowody osobiste act on mDowód and new ID.
- Verbatim text of art. 220 KPA and the exact article of the informatyzacja act; Poland's OOTS connection status; 12 Dec 2027 date for SDG art. 14.
- login.gov.pl: PESEL release conditions, OIDC availability, current onboarding page (mc.bip.gov.pl not opened).
- EUDI: Polish relying-party profile and registration procedure (bill not yet law); implementing-act entry-into-force date that starts the 24- and 36-month clocks.
- Nocleg z mObywatelem and mStłuczka mechanics (page titles only).
- Searched but nothing in the opened sources on Bydgoszcz's own mObywatel integration.

## 10. Sources

- https://api.sejm.gov.pl/eli/acts/DU/2023/1234/text.html (act on mObywatel, text read)
- https://www.gov.pl/web/cyfryzacja/kod-qr--skuteczna-metoda-weryfikacji-mdowodu
- https://www.gov.pl/web/cyfryzacja/przypominamy-urzedy-w-polsce-maja-obowiazek-uznawac-mdowod
- https://www.gov.pl/web/cyfryzacja/nowe-funkcjonalnosci-mobywatela
- https://www.gov.pl/web/cyfryzacja/nocleg-z-mobywatelem
- https://www.gov.pl/attachment/a3f74ecd-21a7-4579-b3bc-24c2ea5164d2 (Regulamin mObywatel 26.0.0, not opened)
- https://www.gov.pl/web/login/dla-integratorow
- https://mc.bip.gov.pl/interoperacyjnosc-mc/wezel-krajowy-dokumentacja-dotyczaca-integracji-z-wezlem-krajowym.html
- https://api.sejm.gov.pl/eli/acts/DU/2022/1431/text.html (technical requirements of the e-dowód electronic layer)
- https://www.gov.pl/cyfryzacja/jak-uzyskac-dostep-do-srp
- https://arslege.pl/kodeks-postepowania-administracyjnego/k3/a810/
- https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202401183
- https://www.gov.pl/web/cyfryzacja/rzad-przyjal-projekt-ustawy-o-europejskim-portfelu-tozsamosci-cyfrowej
- https://info.mobywatel.gov.pl/eidas-2/dolacz-do-sandboxa
- https://redakcja.www.gov.pl/web/cyfryzacja/polska-uruchomila-sandbox-europejskiego-portfela-tozsamosci-cyfrowej-firmy-moga-juz-testowac-przyszle-uslugi-cyfrowej-identyfikacji
- https://interoperable-europe.ec.europa.eu/collection/guidelines-sharing-interoperability-solutions/document/case-study-adapting-polands-mobywatel-ecosystem-european-digital-identity-wallet
- https://github.com/eu-digital-identity-wallet/eudi-srv-web-verifier-endpoint-23220-4-kt
- https://www.gov.pl/web/cyfryzacja/zmiany-w-e-doreczeniach-dla-podmiotow-publicznych
- https://www.gov.pl/web/cyfryzacja/od-nowego-roku-e-doreczenia-podstawowym-kanalem-komunikacji-z-urzedami-co-to-oznacza-dla-obywateli
- https://idtechwire.com/poland-opens-mobywatel-europa-sandbox-for-digital-identity-wallet-integrations/
- https://bmi.usercontent.opencode.de/eudi-wallet/developer-guide/ (German RP onboarding model)
