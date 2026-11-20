# R2 - Access to public information (UDIP) in a Polish city office: law, real process, taxonomy, response templates, data sources

Research date: 2026-11-20 (evening). Scope: Urząd Miasta Bydgoszczy as the reference office; law status as of November 2026.

Evidence labels used on every important claim:

- **[V]** VERIFIED - the primary source was opened and read in this session (statute text from the Sejm ELI API, the judgment page on orzeczenia.nsa.gov.pl, the BIP page, the downloaded file).
- **[S]** SECONDARY - reliable secondary source or a search-engine summary of a primary page that was not opened.
- **[U]** UNVERIFIED tonight - established doctrine or case law quoted from background knowledge; correct to the best of the author's knowledge but not re-opened. Builders must not hard-code these without a lawyer's check.

Companion files: `data/udip-taxonomy.json` (machine-readable taxonomy) and `data/udip-response-templates.md` (Polish skeletons).

## TL;DR for builders

1. **The governing text** is ustawa z 6 września 2001 r. o dostępie do informacji publicznej, consolidated text **Dz.U. 2022 poz. 902**, amended once since: **Dz.U. 2025 poz. 1844**, which rewrote art. 10 ust. 1 from **1 July 2026**. There is no newer consolidated text. [V]
2. **Centralny Rejestr Umów did NOT start on 1 January 2026.** The act of 4 December 2025 replaced it with the *Centralny Rejestr Umów Jednostek Sektora Finansów Publicznych (CRU JSFP)*: account applications from 1 April 2026, mandatory for contracts concluded **from 1 July 2026**, entry within 30 days. Since 1 July 2026 a request for data that is in CRU JSFP can be answered by pointing to the register, exactly like BIP. [V]
3. **Hard clock:** answer "bez zbędnej zwłoki", at the latest **14 days from filing**; one extension possible only if the applicant is told the reasons and the new date **inside those 14 days**, maximum **2 months from filing** (art. 13). The assistant must compute and display both dates the moment a request is registered. [V]
4. **Only two outcomes are administrative decisions** (art. 16): refusal (odmowa) and discontinuance after an unanswered art. 14 ust. 2 notice (umorzenie). Everything else is a plain letter or a "czynność materialno-techniczna" (just sending the information). Decisions need KPA form, a signature of an authorised person and an appeal instruction; appeal to SKO, which has 14 days. [V]
5. **"Not public information", "we do not hold it", "another access regime applies"** are answered by an ordinary letter, not a decision. Bydgoszcz states this on its own BIP card. The letter must still arrive within 14 days, otherwise the applicant wins a skarga na bezczynność. [V]
6. **Anonymous requests are no longer a safe assumption.** The old line (NSA I OSK 1277/08, I OSK 692/18) accepted an unsigned e-mail without personal data. The newer NSA line (III OSK 1602/24 of 18.12.2024; **III OSK 2396/25 of 9.06.2026**, dismissing the Ombudsman's cassation) accepts that the office may require the applicant's name and run a clarification step when the sender cannot be identified, explicitly mentioning automatically generated (AI) requests. The product needs an "applicant identification" state and must leave the policy choice to the office. [V]
7. **Informacja przetworzona** (processed information) is released only if "szczególnie istotne dla interesu publicznego". Statute gives no procedure; practice built by courts: call the applicant to show the special public interest, then either release or issue a refusal decision that explains both why the information is processed and why the interest is missing. [V for the pattern, see I OSK 977/11, I OSK 1347/05]
8. **Restrictions (art. 5):** classified information and other statutory secrets, privacy of a natural person, tajemnica przedsiębiorcy. Privacy does not cover persons performing public functions in connection with that function. Partial restriction means: release the anonymised document and issue a refusal decision for the blacked-out part. [V for art. 5; U for the anonymise-plus-decision practice]
9. **AI must never decide.** Classification as "not public information", "processed", "abuse of right", "internal document", every art. 5 restriction and every decision are legal assessments that end in court if wrong; art. 23 makes non-disclosure a crime. The assistant drafts and cites, a named clerk approves, a lawyer approves decisions. Art. 16 ust. 2 pkt 2 requires naming the people who "took a position" in a refusal - keep that audit trail. [V for the statute; design rule]
10. **No public register of UDIP requests exists for UM Bydgoszcz** (BIP sitemap checked). Usable evaluation data: Watchdog Polska's Feder system (public REST API, about 75 thousand cases), court judgments in CBOSA (41 UDIP rulings of WSA Bydgoszcz in 2026 so far), BIP content, dane.gov.pl. [V]
11. **Volume benchmark:** Bydgoszcz reported between 501 and 1200 requests for 2022 (lowest of the nine cities in that band); Wrocław about 2000 a year; Kraków 2898; Warszawa 8507. [V, Watchdog 2023 monitoring and a Wrocław city letter]
12. **Grounding stack that works without keys:** Sejm ELI API (statutes, JSON plus HTML text), CBOSA (HTML only, throttles bursts, cache everything), Feder API, dane.gov.pl API. SAOS does **not** contain administrative court judgments. BIP Bydgoszcz has no API, an empty RSS feed and an HTML sitemap. [V]

## 1. Law as of 20 November 2026

### 1.1 Status of the acts

| Act | Current text | Status / last change | Label |
|---|---|---|---|
| Ustawa z 6.09.2001 o dostępie do informacji publicznej (UDIP) | t.j. **Dz.U. 2022 poz. 902** | In force. 20 amending acts in total; the only one after the consolidated text is Dz.U. 2025 poz. 1844 (art. 10 ust. 1, in force 1.07.2026). ELI record last changed 2026-07-28. | [V] |
| Ustawa z 4.12.2025 zmieniająca ustawę o zmianie ustawy - Kodeks karny ... (CRU JSFP) | Dz.U. 2025 poz. 1844 | Published 23.12.2025; in force 1.01.2026, art. 2 (UDIP change) from 1.07.2026 | [V] |
| Ustawa z 11.08.2021 o otwartych danych i ponownym wykorzystywaniu informacji sektora publicznego | t.j. **Dz.U. 2023 poz. 1524** | In force (ELI status "obowiązujący") | [V] |
| Kodeks postępowania administracyjnego (KPA) | t.j. **Dz.U. 2025 poz. 1691** (obwieszczenie z 7.11.2025) | In force; check later amendments through ELI before citing | [V] |
| Prawo o postępowaniu przed sądami administracyjnymi (PPSA) | t.j. **Dz.U. 2026 poz. 143** (obwieszczenie z 21.01.2026) | In force. Note: UDIP art. 21 still cites "Dz.U. z 2022 r. poz. 329" in the consolidated text. | [V] |
| RODO (Regulation (EU) 2016/679), art. 86 | OJ L 119, 4.5.2016 | Art. 86 lets Member State law reconcile access to official documents with data protection | [U] |

Citation string to use in letters today: "ustawa z dnia 6 września 2001 r. o dostępie do informacji publicznej (Dz. U. z 2022 r. poz. 902 oraz z 2025 r. poz. 1844)". The Bydgoszcz BIP card still cites only "t.j. Dz. U. 2022, poz. 902". [V]

### 1.2 Article by article: operational meaning

| Article | Content (short) | What it means for the clerk and for the assistant | Label |
|---|---|---|---|
| art. 1 ust. 1 | Every piece of information on public matters is public information | Broad test: does the content concern public tasks, public money or public office? Authorship and form do not matter. | [V] |
| art. 1 ust. 2 | UDIP does not override other acts with different access rules | Route out: KPA art. 73 (party's access to own case files), environmental information, archives, land register, civil status records, geodetic data and so on. Answer: letter pointing to the right regime. | [V] |
| art. 2 ust. 1 | "Każdemu" - everyone has the right | No citizenship, residence or age test. | [V] |
| art. 2 ust. 2 | No one may be asked to show a legal or factual interest | Never ask "why do you need it". Exception: processed information (art. 3 ust. 1 pkt 1). | [V] |
| art. 3 ust. 1 pkt 1 | Right to obtain information, including processed information "w takim zakresie, w jakim jest to szczególnie istotne dla interesu publicznego" | The only place where the applicant's purpose matters. | [V] |
| art. 3 ust. 1 pkt 2-3, ust. 2 | Inspection of official documents, access to sittings of elected collegial bodies, right to current information without delay | "Wgląd" on site is a valid form of disclosure; council sessions and their recordings are a separate channel. | [V] |
| art. 4 ust. 1, 3 | Obliged entities: public authorities and others performing public tasks, **if they hold the information** | Prezydent Miasta is the obliged entity for the city office. Not holding it means a letter, not a decision, and no duty to forward. | [V] |
| art. 5 ust. 1 | Limits: classified information and other statutory secrets | Tax secrecy, statistical secrecy, professional secrets and so on. Refusal decision. | [V] |
| art. 5 ust. 2 | Limits: privacy of a natural person, tajemnica przedsiębiorcy; not for persons performing public functions in connection with the function, nor where the person waives protection | Anonymise private persons; do not anonymise officials acting in office. Trade secret needs both a formal and a material test. | [V] |
| art. 5 ust. 2a-2b, 3-4 | Resolution regime limits; no restriction of information on cases decided before state bodies where public bodies or officials are concerned | Rare in a city office. | [V] |
| art. 6 | Open catalogue of public information; ust. 2 defines dokument urzędowy | Use as a positive checklist: organisation, competences, assets, budget, contracts, decisions, audit documentation, registers, recruitment. | [V] |
| art. 7 | Channels: BIP, on request (art. 10), display (art. 11), access to sittings, portal danych; access is free except art. 15 | The channel list drives the "already published" answer. | [V] |
| art. 10 ust. 1 | Information **not** made available in (1) BIP, (2) portal danych, (3) **CRU JSFP** is provided on request | Wording in force since 1.07.2026. If it is published there, answer with the exact location (deep link), not with the document. | [V] |
| art. 10 ust. 2 | Information that can be given immediately is given orally or in writing without a written request | Phone and counter questions: answer on the spot, no file needed. | [V] |
| art. 11 | Display or posting in public places, kiosks | Rarely relevant. | [V] |
| art. 12 | Released information is marked with: disclosing entity, identity of the author or person responsible for content, identity of the person who released it, date | Mandatory metadata block on every outgoing disclosure. Automate it. | [V] |
| art. 13 ust. 1 | Without undue delay, at the latest 14 days from filing | Day 0 is the day the request reaches the office. | [V] |
| art. 13 ust. 2 | If impossible: notify within those 14 days of the reasons and the new date, not later than 2 months from filing | One-shot extension; reasons must be concrete. | [V] |
| art. 14 ust. 1 | Release in the manner and form requested unless the office's technical means do not allow it | The applicant chooses e-mail, paper, scans, on-site inspection. | [V] |
| art. 14 ust. 2 | If not possible as requested: written notice with reasons and the manner or form available immediately; if the applicant does not file a new request within 14 days, the proceeding is discontinued | Leads to the only "umorzenie" decision in UDIP. | [V] |
| art. 15 | Fee only for additional costs caused by the requested manner or conversion; notify the amount within 14 days from filing; release after 14 days from the notice unless the applicant changes or withdraws the request | Fee equals real cost, never staff time for searching. | [V] |
| art. 16 ust. 1 | Refusal and art. 14 ust. 2 discontinuance by a public authority are **decisions** | Closed list. | [V] |
| art. 16 ust. 2 | KPA applies to those decisions; appeal decided in 14 days; the reasoning of a refusal names the persons who took a position and the entities whose art. 5 ust. 2 interests caused the refusal | Extra mandatory elements on top of KPA art. 107. | [V] |
| art. 17 | Non-authority obliged entities: art. 16 applies accordingly; wniosek o ponowne rozpatrzenie sprawy instead of appeal | Relevant for municipal companies, not for the city office. | [V] |
| art. 21 | Court complaints follow PPSA, but files and the answer go to the court within 15 days and the court decides within 30 days of receiving them | The office has 15 days, not 30, to transmit a complaint. | [V] |
| art. 22 | Repealed | - | [V] |
| art. 23 | Whoever, against a duty, does not make public information available: fine, restriction of liberty or imprisonment up to one year | Personal criminal exposure of the responsible person. | [V] |

### 1.3 Amendments 2024-2026

- The ELI record of Dz.U. 2001 poz. 1198 lists 20 amending acts; after the 2021 acts (Dz.U. 2021 poz. 1598 and 1641) the only later one is **Dz.U. 2025 poz. 1844**. No amendment was adopted in 2024. [V]
- Dz.U. 2025 poz. 1844, art. 2: art. 10 ust. 1 now reads that public information not made available in (1) Biuletyn Informacji Publicznej, (2) portal danych, (3) Centralny Rejestr Umów Jednostek Sektora Finansów Publicznych is provided on request. In force 1 July 2026. [V]
- Pending or discussed, not law: a 2026 deputies' bill (Sejm print 2721) amending UDIP and the petitions act for users of Polish Sign Language; interpelacja nr 15564 (24.02.2026) asking whether anonymous, duplicated or automatically generated requests will be curbed. Neither was opened tonight. [S]
- Constitutional Tribunal case **K 1/21** (motion of the First President of the Supreme Court against core notions of UDIP): no final outcome could be confirmed. [U]

### 1.4 Centralny Rejestr Umów (CRU JSFP)

Verified from the text of Dz.U. 2025 poz. 1844 [V]:

| Question | Answer |
|---|---|
| Did the register start on 1 January 2026? | **No.** The act entered into force on 1.01.2026, but art. 34a and art. 34b ust. 5-7, 9, 10 of the Public Finance Act take effect on **1.07.2026** and apply to contracts **concluded from 1.07.2026**; account applications from **1.04.2026**. |
| Who enters data | Kierownik jednostki sektora finansów publicznych; for a contract of a public authority, the head of the unit serving it (the city office for Prezydent Miasta). |
| Which contracts | Contracts that are a "zamówienie" in the sense of art. 7 pkt 32 Prawo zamówień publicznych and were concluded in written, documentary, electronic or another special form. The statute text contains no value threshold. Exclusions: special services, defence and security, NFZ healthcare contracts and others (art. 34a ust. 5). |
| Which data | Number, date, term, parties, subject, value, EU funding flag, status and end date, legal basis of any non-disclosure and who decided it, basis of updates (art. 34a ust. 7). Not the contract text. |
| Deadline | Without undue delay, at the latest 30 days from conclusion or change. |
| Link with UDIP | Information restricted under UDIP art. 5 ust. 1 and 2-2b is not shown (art. 34a ust. 8); the register is public; publishing counts as making information available for re-use free of charge; data removed 5 years after the end of the year the contract expired. |
| Operator | Minister Finansów. |

Whether the system actually opened on schedule: Ministry of Finance pages and trade press say account applications opened 1.04.2026 and disclosure began 1.07.2026; a public portal name "rejestrumow.gov.pl" appears in one secondary source. Not opened tonight. [S]

Impact on the assistant:

1. For requests about contracts concluded on or after 1.07.2026, first check CRU JSFP and answer with a pointer (art. 10 ust. 1 pkt 3) for the fields the register holds.
2. Requests for the **content** (scan) of a contract, annexes, invoices, or for contracts concluded before 1.07.2026 remain ordinary UDIP requests.
3. Bydgoszcz also publishes its own departmental "Rejestry umów" pages in BIP (many entries in the BIP sitemap), which stay the source for older contracts. [V]

### 1.5 Re-use requests (ustawa z 11.08.2021, t.j. Dz.U. 2023 poz. 1524) versus UDIP

| Feature | UDIP request | Re-use request (wniosek o ponowne wykorzystywanie) | Label |
|---|---|---|---|
| Purpose | To learn the information | To use it for another purpose (commercial or not) than the one it was produced for | [U] for the definition; Bydgoszcz BIP card repeats it [V] |
| When a request is needed | Information not in BIP, portal danych or CRU JSFP | Art. 39 ust. 1: not in BIP or portal danych; published elsewhere without re-use conditions; to be used on other conditions; obtained under other acts | [V] |
| Formal content | None in the statute | Art. 39 ust. 3: name of the obliged entity, **applicant's name and address**, indication of the information, **purpose of re-use** (type of activity, goods, products, services), form and data format, manner of transfer | [V] |
| Formal defects | No statutory rule (see 2.3) | Art. 39 ust. 5: call to remedy within 7 days, otherwise left without consideration | [V] |
| Deadline | 14 days, extension to 2 months from filing | Art. 40: 14 days from receipt, extension to 2 months from filing | [V] |
| Outcomes | Release, letters, refusal or discontinuance decision | Art. 41: transfer without conditions; information that it is not held; information that no conditions apply; **offer** with conditions or fees; **decision** refusing consent | [V] |
| Applicant's reaction | - | 14 days to accept the offer or file a **sprzeciw**; silence equals withdrawal; after sprzeciw the entity decides by decision | [V] |
| Appeal body | SKO for a city president | Art. 43 ust. 1 names the minister właściwy do spraw informatyzacji as the appeal body; how this interacts with the SKO route for local-government bodies was not checked tonight | [V] for the text, open question for local government |
| Real-time access | - | Art. 39 ust. 2: request for constant, direct, real-time access to data in the entity's IT system | [V] |

Triage signal for the assistant: the words "ponowne wykorzystywanie", a stated commercial purpose, a request for a data feed or API, or a declared product or service point to the re-use route. A request that only asks for a document is UDIP even when the sender is a company.

### 1.6 Relation to RODO, privacy and trade secret

- RODO does not block disclosure: art. 86 RODO leaves reconciliation to national law, and in Poland that law is UDIP art. 5 ust. 2. Data protection is therefore applied **through** art. 5 ust. 2, not instead of UDIP. [U]
- **Private persons** in disclosed documents (names of applicants in decisions, addresses, PESEL, signatures of citizens, contractors who are natural persons outside public functions): anonymise. [U]
- **Persons performing public functions** (president, deputies, councillors, officials who decide or prepare decisions, heads of municipal units): name, position, pay elements linked to the function, decisions signed, are disclosed; data unrelated to the function (home address, PESEL, health) are not. Leading case: TK K 17/05 of 20.03.2006. [U]
- **Names of contractors** who are natural persons in contracts paid from public money are disclosed according to the line started by SN I CSK 190/12 of 8.11.2012. [U]
- **Tajemnica przedsiębiorcy** needs a formal element (the company took steps to keep the information confidential, usually a clause marked at submission) and a material element (real economic value). The price and subject of a public contract are normally not secret. [U]
- **Anonymisation is not "processing"** that would turn simple information into processed information, unless the volume makes it a major project (courts look at the scale). [U]
- **Form of a partial restriction:** send the anonymised document and issue a refusal decision for the removed scope, naming in the reasoning the entities whose interests are protected (art. 16 ust. 2 pkt 2). A different line accepts routine anonymisation of data of private persons without a decision when the applicant did not ask for those data. Office policy must choose; the assistant must flag every redaction. [U]
- The applicant's own data: the Bydgoszcz clause states the purpose (legal obligation under UDIP), that data become mandatory when a decision is issued (KPA), retention under archival law, and that data "nie są przetwarzane w sposób zautomatyzowany oraz nie podlegają profilowaniu". [V] **Product consequence:** if an AI assistant analyses requests, the office must review this sentence and its record of processing with the IOD before going live.

### 1.7 When KPA applies

- Art. 16 ust. 2: KPA applies **to the decisions** named in art. 16 ust. 1, with two modifications (14 days for the appeal body; extra content of the reasoning). [V]
- The disclosure stage itself is not an administrative proceeding: no KPA deadlines (art. 35), no notice of initiation, no ponaglenie requirement before a court complaint, no duty to forward to the competent body (art. 65 KPA does not apply; the office just says it does not hold the information). [U]
- From the moment the office "zmierza do wydania decyzji" KPA applies in full: party identification, signature (art. 63 and 64 § 2 KPA), active participation of the party (art. 10), decision elements (art. 107 § 1), service rules, appeal to SKO within 14 days of service (art. 129 § 2). [U for KPA articles; V for the court statements in I OSK 692/18 and III OSK 2396/25 that missing personal data and signature are formal defects curable under art. 64 § 2 KPA at this stage]

### 1.8 Skarga na bezczynność (complaint about inaction) to the WSA

- Available whenever 14 days pass without release, extension notice, decision or a correct letter; also when the answer is incomplete, off-topic, or a letter was sent where a decision was required. No ponaglenie is needed in UDIP matters. [U]
- Filed through the office; **the office has 15 days** to send the files and its answer (art. 21 pkt 1 UDIP), the court has 30 days (pkt 2). [V] A fine can be imposed for late transmission (PPSA art. 55 § 1). [U]
- Court outcomes (PPSA art. 149): obligation to handle the request within a set time (usually 14 days); a finding whether the inaction was "z rażącym naruszeniem prawa"; optionally a fine on the office or a sum awarded to the complainant; costs. If the office answers before the hearing, the obligation part is discontinued but the inaction is still assessed. [U]
- Volume signal: CBOSA lists **4786** rulings with case symbol 6480 (public information and press law) dated 2025 nationwide; **15** from WSA Bydgoszcz for 2025 and **41** for 1.01-20.11.2026 (all obliged entities in the court's district, not only the city). [V]

### 1.9 Art. 23 - criminal liability

Text: "Kto, wbrew ciążącemu na nim obowiązkowi, nie udostępnia informacji publicznej, podlega grzywnie, karze ograniczenia wolności albo pozbawienia wolności do roku." [V] It is an intentional offence prosecuted ex officio; convictions are rare but notifications to the prosecutor are a routine pressure tool of watchdog organisations. [U] Design consequence: the system must make it impossible for a request to disappear (mandatory registration, immutable log, escalation before day 14).

## 2. The clerk's real decision tree

### 2.1 Steps, inputs, outputs, deadlines

Day 0 = the day the request reaches the office (any channel). All deadlines below are calendar days. When the last day falls on a Saturday or a public holiday, practice applies KPA art. 57 § 4 by analogy and moves it to the next working day; the assistant should show the conservative date (no shifting) as the target. [U]

| Step | Question | Inputs | Output if "yes" | Output if "no" | Deadline |
|---|---|---|---|---|---|
| S0 | Register the incoming item (EZD case number, channel, timestamp, sender data as given) | E-mail, ePUAP, e-Doręczenia, paper, fax, oral request recorded in a note | Case opened, deadlines D14 and D60 computed | - | Day 0 |
| S1 | Is it a UDIP request at all? Test the content, not the title | Text of the request | Continue to S2 | Route out by ordinary letter naming the right regime (see 2.2); still within 14 days | Day 14 |
| S2 | Can the applicant be identified enough to answer and, if needed, to serve a decision? | Name, address or e-mail, signature | Continue | Office policy: answer anyway (traditional line) or call for identification (line of III OSK 1602/24 and III OSK 2396/25). Mandatory call under art. 64 § 2 KPA once a decision is planned | Call as early as possible; at least 7 days to respond |
| S3 | Split into separate questions; each gets its own path | Request text | List of items with IDs | - | Day 1-2 |
| S4 | Does the item concern public matters (art. 1, art. 6)? | Item, catalogue of art. 6, case law | Continue | Letter "nie stanowi informacji publicznej" with reasons | Day 14 |
| S5 | Does the office hold the information (art. 4 ust. 3)? Ask the substantive department | Department reply, EZD, registers | Continue | Letter "nie posiadamy"; add where it may be held if known (courtesy, not a duty) | Day 14 |
| S6 | Is it already published in BIP, portal danych or CRU JSFP (art. 10 ust. 1)? | BIP search, dane.gov.pl, CRU | Letter with the exact link and path | Continue | Day 14 |
| S7 | Does a separate access regime apply (art. 1 ust. 2)? | Subject matter | Letter "inny tryb" | Continue | Day 14 |
| S8 | Simple or processed information? | Department estimate of work: which sources, how many files, what operations | Processed: call to show special public interest (wezwanie); usually together with an art. 13 ust. 2 notice. Then: interest shown = prepare and release; not shown = refusal decision | Simple: continue | Call within day 14; decision or release within the extended date |
| S9 | Do art. 5 restrictions apply to all or part? | Document content, contractor confidentiality clauses, classification | Full: refusal decision. Part: release anonymised version plus refusal decision for the rest | Continue | Day 14 or extended date |
| S10 | Can it be released in the manner and form requested (art. 14)? | Technical means | Continue | Art. 14 ust. 2 notice; 14 days for the applicant; silence = decision o umorzeniu | Notice by day 14; decision after the 14 days pass |
| S11 | Additional costs (art. 15)? | Cost calculation: media, copies, postage | Fee notice within 14 days from filing; release after 14 days from the notice unless the applicant changes or withdraws | Continue | Notice by day 14 |
| S12 | Can it be done by day 14? | Workload | Release with the art. 12 metadata block | Art. 13 ust. 2 notice with concrete reasons and a date not later than day 60 (2 months from filing) | Day 14 |
| S13 | Close: record what was sent, to whom, by whom, when; archive | Outgoing letter, attachments | Case closed in EZD | - | - |

### 2.2 S1 in detail: what is not a UDIP request

| Looks like | Real regime | Legal basis | Deadline in that regime | Response from the UDIP desk | Label |
|---|---|---|---|---|---|
| Party asks for files of its own case | Access to files | KPA art. 73-74 | Without delay; refusal by postanowienie | Letter: other regime; pass to the department running the case | [U] |
| "I complain about the clerk", "I demand that the city repairs..." | Skarga or wniosek | KPA Dział VIII (art. 221-259) | 1 month | Transfer to the complaints unit | [U] |
| Demand to change law or take a general action in the public interest | Petycja | Ustawa z 11.07.2014 o petycjach | 3 months | Transfer to the petitions unit | [U] |
| Journalist's questions | Still UDIP for public information | Prawo prasowe art. 3a refers to UDIP | 14 days | Handle as UDIP; no privilege, no worse treatment | [U] |
| Request for data sets to build a service, with declared purpose | Re-use | Act of 11.08.2021, art. 39-43 | 14 days, up to 2 months | Handle under the re-use act (formal elements required) | [V] |
| Environmental information (emissions, tree felling permits, environmental decisions) | Environmental information | Ustawa z 3.10.2008 (OOŚ), dział II | 1 month, up to 2 months | Letter or direct handling by the environment department | [U] |
| Historical records already transferred to the state archive | Archives | Ustawa o narodowym zasobie archiwalnym i archiwach | - | Letter: not held, held by Archiwum Państwowe | [U] |
| Request for a certificate, a copy of a civil status record, registered address data | Sector acts (akty stanu cywilnego, ewidencja ludności, zaświadczenia KPA art. 217) | Sector acts | Sector deadlines | Letter: other regime | [U] |
| Question about the law or request for legal advice, request to "explain why" or to create a new opinion | Not a request for existing information | art. 1, art. 6 UDIP | 14 days | Letter: not public information in this scope | [U] |
| Request for a prosecutor's or similar case file as a whole | Not a UDIP request | NSA resolution I OPS 7/13 of 9.12.2013 | - | Letter | [V] |
| Request for future facts or plans not yet recorded | Information does not exist | art. 4 ust. 3 | 14 days | Letter: not held | [U] |

### 2.3 Signature and personal data (case law on art. 63-64 KPA)

| Line | Holding | Source | Label |
|---|---|---|---|
| Classic | A question sent by e-mail is a written request even without an electronic signature | NSA 16.03.2009, I OSK 1277/08 | [V] |
| Classic | UDIP sets no formal requirements beyond a recorded form; the applicant need not give personal data. Whether art. 64 § 2 KPA must be used before a refusal was the disputed issue in that case | NSA 14.11.2019, I OSK 692/18 | [V] |
| Decision stage | When the office heads towards a decision, the lack of the applicant's personal data and signature is a formal defect curable under art. 64 § 2 KPA (call, at least 7 days, otherwise left without consideration) | Stated in NSA III OSK 2396/25; also WSA position quoted in I OSK 692/18 | [V] |
| New restrictive line | Given current threats and automatically generated mail, the office may establish who the applicant is; in the case decided the name was treated as a necessary element because the e-mail address did not identify the sender; "sui generis" clarification procedure allowed | NSA 18.12.2024, III OSK 1602/24; NSA 9.06.2026, **III OSK 2396/25** (cassation of the Ombudsman dismissed; first instance WSA Warszawa 13.08.2025, II SAB/Wa 333/25) | [V] |
| Counter-arguments | The Ombudsman argued that this creates an extra-statutory limit on a constitutional right | RPO cassation of 22.10.2025 | [V] |

Design consequences:

- Never auto-reject an anonymous request. Flag `applicant_identified = false`, show both lines of case law, let the office policy decide.
- If the outcome will be a decision, the assistant must propose the art. 64 § 2 KPA call first (template T9) and stop the decision draft until identification data and a signature are on file.
- The Bydgoszcz form (updated 30.03.2026, before the June 2026 NSA judgment) says "Podanie danych nie jest obowiązkowe" and its privacy clause says data become mandatory when a decision is issued. [V]

### 2.4 Processed information (informacja przetworzona)

- Working definition used by courts: information that does not exist in the requested shape and must be produced specially for the applicant from simple information through analyses, calculations, statistical compilations, with noticeable use of staff and money. NSA 17.10.2006, I OSK 1347/05. [V]
- The statute divides information into processed (released when the special public interest exists) and simple (released without it). NSA 9.08.2011, I OSK 977/11, in a case where the office called the applicant to indicate the interest and then refused. [V]
- A large number of simple items requiring organisational effort that disturbs normal work may also be treated as processed (the "sum of simple information" line). [U]
- Special public interest: the applicant has a real possibility to use the information to improve the functioning of public bodies (councillors, MPs, researchers, watchdog organisations, journalists often qualify; private disputes do not). [U]
- Procedure (court-made): (1) the department describes concretely what must be done; (2) wezwanie to show the special public interest with a reasonable time limit (7-14 days in practice, no statutory term), sent with an art. 13 ust. 2 notice so the clock does not run out; (3) release or refusal decision. Silence of the applicant does not allow leaving the request without consideration; a decision is needed. [U]

### 2.5 Abuse of the right to information (nadużycie prawa)

- Concept accepted by the NSA: using the access institution for a purpose other than concern for the public good (transparency, legality, openness). NSA 23.11.2016, I OSK 1601/15, approving abuse as the basis for dismissing a complaint. [V]
- Typical fact patterns in case law: dozens or hundreds of requests aimed at paralysing the office or harassing a specific official; requests used to collect court costs from inaction complaints (argued by the office in NSA 14.02.2017, I OSK 2642/16) [V that the argument was raised]; requests serving only a private dispute. [U]
- Form of the reaction is disputed: one line says the office answers by letter that the request is not handled under UDIP; another requires a refusal decision under art. 16. [U]
- Rule for the product: the assistant may surface indicators (same sender, volume, repetition, near-duplicate text) but must never label a request as abuse. A lawyer decides.

### 2.6 Internal document (dokument wewnętrzny)

- Doctrine: working materials that do not express the body's position and are not directed outside (drafts, notes, internal e-mails used to gather information for a future decision) are not public information. Sources: TK P 25/08 of 13.11.2013 [U]; NSA 27.01.2012, I OSK 2130/11 (expert opinions as an internal document "służącym gromadzeniu informacji, które w przyszłości mogą zostać wykorzystane w procesie decyzyjnym") [V]; NSA 14.09.2012, I OSK 1203/12 (official e-mail correspondence) [V that the judgment exists and concerns PRM; holding not re-read].
- The doctrine has no statutory basis and courts apply it narrowly; documents that were the basis of a decision, were paid for with public money or express a final position are public information. [U]
- Response form: letter "nie stanowi informacji publicznej" (T2). High risk of an inaction complaint, so legal review is mandatory.

### 2.7 Multi-question requests

One request, many items, one clock. Each item gets its own classification and outcome; the reply is one letter with numbered sections, plus separate decisions where needed. Partial release must not wait for the disputed part. The 14-day term cannot be multiplied by the number of questions; use art. 13 ust. 2 once for the items that need more time.

## 3. Classification taxonomy for the assistant

Full machine-readable version: `data/udip-taxonomy.json`. Summary:

| Code | Request type | Legal route | Response document | Deadline rule | Human approval |
|---|---|---|---|---|---|
| UDIP_SIMPLE | Simple public information held by the office | UDIP art. 10, 13, 14 | T1 release | D14 | Clerk, department head |
| UDIP_PUBLISHED | Already in BIP, portal danych, CRU JSFP | UDIP art. 10 ust. 1 | T4 pointer | D14 | Clerk |
| UDIP_NOT_PUBLIC | Not public information (private matter, opinion, legal advice, internal document) | UDIP art. 1, 6 | T2 letter | D14 | Clerk, lawyer |
| UDIP_NOT_HELD | Office does not hold it | UDIP art. 4 ust. 3 | T3 letter | D14 | Clerk, department head |
| UDIP_OTHER_REGIME | Separate access regime | UDIP art. 1 ust. 2 | T12 letter | D14 | Clerk |
| UDIP_PROCESSED | Processed information | UDIP art. 3 ust. 1 pkt 1 | T6 call, then T1 or T10 | D14 for the call, D60 limit | Department head, lawyer |
| UDIP_RESTRICTED_FULL | Art. 5 restriction on everything | UDIP art. 5, 16 | T10 decision | D14 or D60 | Lawyer, authorised signatory |
| UDIP_RESTRICTED_PARTIAL | Art. 5 restriction on a part | UDIP art. 5, 16 | T1 with anonymisation plus T10 | D14 or D60 | Lawyer, IOD on request, signatory |
| UDIP_FORM_UNAVAILABLE | Requested form or manner impossible | UDIP art. 14 ust. 2 | T8 notice, then T1 or T11 | D14, then 14 days for the applicant | Clerk, signatory for T11 |
| UDIP_FEE | Additional cost | UDIP art. 15 | T7 notice, then T1 | D14, then 14 days | Clerk, finance |
| UDIP_EXTENSION | Cannot be done in 14 days | UDIP art. 13 ust. 2 | T5 notice | D14, limit D60 | Department head |
| UDIP_ABUSE_SUSPECTED | Indicators of abuse | Case law | No automatic document | D14 | Lawyer only |
| UDIP_UNIDENTIFIED | Sender not identifiable | Case law, KPA art. 64 § 2 | T9 call or office policy | Call early | Clerk, lawyer |
| REUSE | Re-use request | Act of 11.08.2021 art. 39-43 | Own documents (offer, decision) | D14, limit D60 | Clerk, lawyer |
| KPA_FILES, COMPLAINT, PETITION, ENVIRONMENT, ARCHIVE, PRESS | Not UDIP or UDIP with a twist | See 2.2 | T12 letter or transfer | Regime-specific | Clerk |
| MIXED | Several of the above | Per item | Combined letter and decisions | One clock | Per item |

## 4. Catalogue of response documents

Polish skeletons with placeholders: `data/udip-response-templates.md`.

| ID | Document | Legal nature | Mandatory elements | Pitfalls | Label |
|---|---|---|---|---|---|
| T1 | Udostępnienie informacji | Czynność materialno-techniczna (no decision) | Case number; the information or attachments; art. 12 block: disclosing entity, author or person responsible for content, person who released it, date; form and manner as requested | Incomplete or evasive answer equals inaction; do not ask about purpose; send to the address and in the form requested | [V] art. 12-14 |
| T2 | "Nie stanowi informacji publicznej" | Ordinary letter | Which part; why (art. 1, art. 6; nature of the content); signature | Overuse of the "internal document" label; courts review the classification in an inaction complaint; a decision here is a defect | [V] BIP Bydgoszcz confirms the letter form |
| T3 | "Nie posiadamy" | Ordinary letter | Clear statement that the office does not hold the information; optionally who may hold it | No duty to forward (art. 65 KPA not applied); statement must be true and checked with the department; partially held means release the part held | [V] BIP Bydgoszcz; [U] no-forwarding rule |
| T4 | Wskazanie BIP, portalu danych, CRU JSFP | Ordinary letter | Exact URL and path to the specific information | A general "see BIP" is treated as inaction; the published data must be complete and current; information on the office's ordinary website (not BIP) does not count | [V] art. 10 ust. 1; [U] exact-link rule |
| T5 | Zawiadomienie o przedłużeniu terminu | Ordinary letter | Sent within 14 days; concrete reasons; a specific date not later than 2 months from filing | No second extension; generic reasons ("workload") are criticised; a late notice does not cure inaction | [V] art. 13 ust. 2 |
| T6 | Wezwanie do wykazania szczególnie istotnego interesu publicznego | Ordinary letter | Why the information is processed (operations, sources, effort); time limit; information that a refusal decision may follow | Not a formal-defect call: no "left without consideration"; combine with T5; the office itself must also assess the interest | [V] pattern in I OSK 977/11; [U] details |
| T7 | Zawiadomienie o opłacie | Notice (reviewable by the court as an act) | Amount; calculation of real additional costs; that release follows after 14 days from the notice unless the applicant changes or withdraws; within 14 days from filing | No fee for staff time or for searching; release cannot be made conditional on prior payment in the statute's wording | [V] art. 15; [U] case-law details |
| T8 | Zawiadomienie art. 14 ust. 2 | Written notice | Reasons why the requested form or manner is impossible; the form or manner available immediately; instruction about 14 days and discontinuance | "Technical means" only, not convenience; must be in writing | [V] art. 14 ust. 2 |
| T9 | Wezwanie do uzupełnienia braków przed decyzją | Call under KPA art. 64 § 2 | What is missing (name, address, signature); at least 7 days; consequence: left without consideration | Only when a decision is planned or under the office's identification policy; not a tool to delay simple answers | [V] III OSK 2396/25, I OSK 692/18 |
| T10 | Decyzja o odmowie udostępnienia | Administrative decision | KPA art. 107 § 1 elements: authority, date, party, legal basis, ruling, factual and legal reasoning, appeal instruction (SKO, 14 days, through the authority; right to waive the appeal), signature with name and position; plus art. 16 ust. 2 pkt 2: names, surnames and functions of persons who took a position, and the entities whose art. 5 ust. 2 interests are protected | Refusing something that is not public information is a defect; precise scope of refusal; reasons for "processed" and for "no special interest" both needed; service on an identified party | [V] art. 16; [U] KPA elements |
| T11 | Decyzja o umorzeniu postępowania | Administrative decision | As T10 without the art. 16 ust. 2 pkt 2 additions; facts: date of the art. 14 ust. 2 notice, date of its delivery, lapse of 14 days | Only for the art. 14 ust. 2 case; withdrawal of a request needs no decision; prove delivery of the notice | [V] art. 14 ust. 2, art. 16 ust. 1 |
| T12 | Pismo o innym trybie | Ordinary letter | Which regime and legal basis; where to file or that the letter was passed on internally | Check that the other act really regulates access comprehensively; for KPA art. 73 the applicant must be a party | [V] BIP Bydgoszcz lists this letter type |

Judgments checked on orzeczenia.nsa.gov.pl tonight (signature, date, link):

| Signature | Date | Topic | Link |
|---|---|---|---|
| NSA I OSK 1347/05 | 2006-10-17 | Definition of processed information | https://orzeczenia.nsa.gov.pl/doc/B08C9C5570 |
| NSA I OSK 1277/08 | 2009-03-16 | Unsigned e-mail is a written request | https://orzeczenia.nsa.gov.pl/doc/BC9662CDDB |
| NSA I OSK 977/11 | 2011-08-09 | Simple versus processed; call to show interest, then refusal | https://orzeczenia.nsa.gov.pl/doc/43B4BE205D |
| NSA I OSK 2130/11 | 2012-01-27 | Internal document | https://orzeczenia.nsa.gov.pl/doc/9B0E75BB3F |
| NSA I OSK 1203/12 | 2012-09-14 | Official e-mail correspondence (holding not re-read) | https://orzeczenia.nsa.gov.pl/doc/557F077F45 |
| NSA I OPS 7/13 (resolution) | 2013-12-09 | Request for a whole prosecutor's file is not a UDIP request | https://orzeczenia.nsa.gov.pl/doc/F4DAFD2E94 |
| NSA I OSK 1601/15 | 2016-11-23 | Abuse of the right to information | https://orzeczenia.nsa.gov.pl/doc/4856ADF275 |
| NSA I OSK 2642/16 | 2017-02-14 | Abuse argued by the office (inaction-complaint farming) | https://orzeczenia.nsa.gov.pl/doc/49B9A23901 |
| NSA I OSK 692/18 | 2019-11-14 | No formal requirements; personal data not required; art. 64 § 2 KPA dispute | https://orzeczenia.nsa.gov.pl/doc/5D0B82E6D3 |
| NSA III OSK 1602/24 | 2024-12-18 | Start of the restrictive line on anonymous requests | https://orzeczenia.nsa.gov.pl/doc/A2E39E8AEF |
| WSA Warszawa II SAB/Wa 333/25 | 2025-08-13 | Anonymous request, complaint dismissed | https://orzeczenia.nsa.gov.pl/doc/988AD3A903 |
| NSA III OSK 2396/25 | 2026-06-09 | Ombudsman's cassation dismissed; identification of the applicant | https://orzeczenia.nsa.gov.pl/doc/85C200A12E |

## 5. Statistics and pain points

### 5.1 Numbers

| Fact | Value | Source | Label |
|---|---|---|---|
| UDIP requests received by Bydgoszcz in 2022 | Between 501 and 1200; listed first (lowest) in the ascending list of cities in that band: Bydgoszcz, Siemianowice Śląskie, Katowice, Kalisz, Gdańsk, Szczecin, Wrocław, Łódź | Watchdog Polska, "Monitoring realizacji wniosków o udostępnienie informacji" (2023), footnote 31 | [V] |
| Kraków, Warszawa 2022 | 2898 and 8507 | Same report | [V] |
| All 411 gminas asked, 2022 | 51 883 requests in total; most gminas and powiats registered at most 100 | Same report | [V] |
| Ministries, 2022 | Most often above 500 each, close to 12 thousand in total | Same report | [V] |
| Wrocław | About 2 thousand requests a year | Letter of the city to councillors, 6.05.2021, BIP Wrocław | [V] |
| Exact Bydgoszcz figure for 2023-2025 | Not found | Searched: BIP Bydgoszcz sitemap, web search, Watchdog report | - |
| Court rulings, symbol 6480, 2025, nationwide | 4786 | CBOSA query | [V] |
| WSA Bydgoszcz, symbol 6480 | 15 in 2025; 41 in 2026 up to 20.11 | CBOSA query | [V] |

Planning figure for a demo: 600-1000 requests a year in Bydgoszcz, that is 3-4 per working day, spread over all departments. [inference from the band above]

### 5.2 Pain points documented in sources

- **Most frequent reasons for not releasing** reported by offices: "not public information" and "does not exist or not held"; gminas that gave one reason most often pointed to processed information. Refusal decisions, court complaints and fees are rare. [V, Watchdog 2023]
- **Organisation:** requests are answered by substantive clerks or departments, sometimes with a coordinator who watches deadlines; answering is an additional duty. [V, Watchdog 2023]
- **Late answers:** in the Watchdog test 50 of 411 gminas answered only after a reminder, an extension or a call to complete an attachment; 16 never answered. [V]
- **Publishing a register of requests and answers is rare**; Wrocław stopped doing it, citing the technical workload (anonymisation, accessibility of scans) against about 2000 requests a year and the trivial content of some requests. [V]
- **Mass and automated senders:** courts and a 2026 parliamentary question describe anonymous, duplicated and automatically generated requests; the NSA in III OSK 2396/25 quotes the risk of mail generated with AI. [V for the judgment; S for the interpelacja]
- **Watchdog's own mass requests** go through fedrowanie.siecobywatelska.pl; in 2023 the organisation reported 3695 own requests and 665 by other organisations through that system. [S]
- **Typical topics** (from art. 6 and practice; not a measured distribution for Bydgoszcz): contracts and invoices, salaries and bonuses of officials, tenders, real estate and planning, administrative decisions (building permits, tree felling), audits and inspections, complaints statistics, registers, legal services costs, promotion spending, council matters. [U]

### 5.3 Demo and evaluation data

| Source | What it gives | Access | Licence / terms | Label |
|---|---|---|---|---|
| Register of UDIP requests of UM Bydgoszcz | **Not published.** The BIP sitemap contains "Udostępnianie informacji publicznej", "Ponowne wykorzystanie informacji publicznej", many "Rejestry umów", "Rejestry decyzji, opinii, postanowień", but no register of requests | https://bip.um.bydgoszcz.pl/sitemap | - | [V] |
| Feder (Watchdog Polska) | Real requests sent to thousands of offices and the replies (letters, attachments) grouped in monitorings; 74 988 cases, 41 703 institutions | REST API https://fedrowanie.siecobywatelska.pl/api/ (cases, records, institutions, monitorings); case pages are public | Code open source (github.com/watchdogpolska/feder); **no data licence stated in the API**; ask Watchdog before redistribution; replies may contain personal data | [V] |
| The Bydgoszcz reply in the 2022 statistics monitoring | The city's own answer about the number of requests, decisions, complaints | Feder case of the monitoring "Wnioski o informacje w 2022" (cases named `wnioski-o-informacje-w-2022-<n>`); the Bydgoszcz case number was not located | As above | [U] |
| CBOSA | Anonymised judgments with full facts: what was asked, how the office answered, who was right. Best source of labelled hard cases | https://orzeczenia.nsa.gov.pl (HTML, RTF export per document) | Public; no API; no terms page checked; throttles bursts | [V] |
| BIP Bydgoszcz | The corpus the assistant must search before answering (art. 10) | HTML pages, attachments by numeric ID | Public information; robots.txt disallows `/*pdf*` and `/*szukaj*` for all agents | [V] |
| dane.gov.pl | Open data sets, including 16 hits for "Bydgoszcz" (for example lost-property lists of UM Bydgoszcz) | REST API | Per data set, mostly CC0 1.0 or CC BY 4.0 | [V] |
| Synthetic requests | Needed for a clean public demo | Generate from the taxonomy; no real personal data | Own | design |

## 6. Machine-readable legal sources for grounding

| Source | URL | Access | Terms | Verdict |
|---|---|---|---|---|
| Sejm ELI API | https://api.sejm.gov.pl/eli | REST, JSON, no key; act metadata with typed references (amending acts, consolidated texts, TK rulings), HTML and PDF texts | Terms page not checked | Primary grounding source for statutes [V] |
| ISAP | https://isap.sejm.gov.pl | Human web front end for the same data | - | Use ELI API instead [U] |
| CBOSA | https://orzeczenia.nsa.gov.pl/cbo/query | HTML form, POST `/cbo/search` with session cookie; documents at `/doc/<ID>` and `/doc/<ID>.rtf` | No API; after about 15 quick requests the server closed connections | Scrape slowly, cache, pre-build a curated set [V] |
| SAOS | https://www.saos.org.pl/api/search/judgments | REST, JSON, no key | Terms not checked | Works, but `courtType=ADMINISTRATIVE` returns no items; only common courts and others. Not useful for UDIP [V] |
| BIP Bydgoszcz | https://bip.um.bydgoszcz.pl | HTML only; `/rss` returns an empty channel; `/sitemap.xml` is 404; `/sitemap` is an HTML site map (about 160 KB); attachments `/attachments/download/<id>` | robots.txt as above | Crawl the HTML sitemap politely and build an own index [V] |
| dane.gov.pl | https://api.dane.gov.pl/1.4/datasets | REST, JSON:API style, no key | Licence per data set | Works [V] |
| Feder | https://fedrowanie.siecobywatelska.pl/api/ | REST (Django REST Framework), no key for reading | Data licence not stated | Works [V] |

### 6.1 Sample requests actually run (2026-11-20), trimmed output

Sejm ELI API - act metadata with references:

```
GET https://api.sejm.gov.pl/eli/acts/DU/2001/1198        (Accept: application/json)
-> ELI "DU/2001/1198", status "akt posiada tekst jednolity", inForce "IN_FORCE", changeDate "2026-07-28T15:40:56"
   references["Akty zmieniające"]: 20 items, newest {"id":"DU/2025/1844","date":"2026-07-01"}
   references["Inf. o tekście jednolitym"]: DU/2022/902, DU/2020/2176, DU/2019/1429, ...
```

Sejm ELI API - search and full text:

```
GET https://api.sejm.gov.pl/eli/acts/search?title=dostępie do informacji publicznej&publisher=DU&limit=50
-> count 10; DU/2022/902 "Obwieszczenie ... jednolitego tekstu" status "obowiązujący"
GET https://api.sejm.gov.pl/eli/acts/DU/2022/902/text.html     -> 169 748 bytes HTML (full consolidated text)
GET https://api.sejm.gov.pl/eli/acts/DU/2025/1844/text.pdf     -> 167 822 bytes PDF (text.html is empty for this act)
GET https://api.sejm.gov.pl/eli/acts/search?title=Kodeks postępowania administracyjnego&type=Obwieszczenie&publisher=DU&dateFrom=2023-01-01
-> DU/2025/1691 "obowiązujący" (2025-11-07), DU/2024/572 "wygaśnięcie aktu"
```

CBOSA - search by signature (Python `urllib` with a cookie jar):

```
GET  https://orzeczenia.nsa.gov.pl/cbo/query                      (sets the session cookie)
POST https://orzeczenia.nsa.gov.pl/cbo/search
     sygnatura=III OSK 2396/25&sad=dowolny&rodzaj=dowolny&wystepowanie=gdziekolwiek&odmiana=on&submit=Szukaj
-> "Znaleziono 1 orzeczeń"; <a href="/doc/85C200A12E">III OSK 2396/25 - Wyrok NSA z 2026-06-09</a>
POST ... symbole=6480&odDaty=2026-01-01&doDaty=2026-11-20&sad=Wojewódzki Sąd Administracyjny w Bydgoszczy
-> "Znaleziono 41 orzeczeń"; newest II SA/Bd 409/26 (2026-11-18)
```

Form fields: `wszystkieSlowa`, `wystepowanie` (gdziekolwiek, w sentencji, w tezach, w uzasadnieniu), `sygnatura`, `sad`, `rodzaj` (Wyrok, Postanowienie, Uchwała), `symbole` (6480 = public information and press law; 648 for older cases; 658 = inaction), `odDaty`, `doDaty` (RRRR-MM-DD), `hasla`, `akty`, `przepisy`. Multi-word and quoted-phrase queries combined with other filters returned no parsable result list in this session; signature and symbol-plus-date queries were reliable.

SAOS:

```
GET https://www.saos.org.pl/api/search/judgments?pageSize=3&all="informacja przetworzona"&sortingField=JUDGMENT_DATE&sortingDirection=DESC
-> info.totalResults 33; items: courtType "COMMON", cases "X Ka 464/20" (2020-09-25), ...
GET https://www.saos.org.pl/api/search/judgments?pageSize=2&courtType=ADMINISTRATIVE
-> "items": []
```

dane.gov.pl:

```
GET https://api.dane.gov.pl/1.4/datasets?q=Bydgoszcz&per_page=5&sort=-modified
-> meta.count 16; e.g. id 35498 "Wykaz rzeczy znalezionych - zbiór danych Urząd Miasta Bydgoszczy", licence "CC0 1.0", modified 2026-07-30
```

Feder:

```
GET https://fedrowanie.siecobywatelska.pl/api/
-> {"institutions": ".../api/institutions/", "tags": ..., "teryt": ..., "records": ..., "cases/report": ..., "cases": ..., "monitorings": ...}
GET https://fedrowanie.siecobywatelska.pl/api/cases/?page_size=1
-> {"count": 74988, "results": [{"pk": 2684, "name": "Monitoring sądów apelacyjnych #1", "institution": ".../api/institutions/2818/", "monitoring": ".../api/monitorings/5/", ...}]}
```

Note: the query parameters `search`, `name` and `regon` on `/api/institutions/` did not filter as expected (either the full set or zero rows came back); the filter syntax needs a look at the Feder source.

BIP Bydgoszcz:

```
GET https://bip.um.bydgoszcz.pl/rss          -> 200, RSS 2.0 channel with no <item>, pubDate 1970-01-01 (generator Zend_Feed)
GET https://bip.um.bydgoszcz.pl/sitemap.xml  -> 404
GET https://bip.um.bydgoszcz.pl/sitemap      -> 200, HTML, 159 560 bytes, links like /artykuly/1052/udostepnianie-informacji-publicznej
GET https://bip.um.bydgoszcz.pl/attachments/download/30900 -> 200 application/pdf, 399 215 bytes, 2 pages
GET https://bip.um.bydgoszcz.pl/attachments/download/30899 -> 200 DOCX, 29 401 bytes
```

## 7. What this means for the wider product vision

- **(D) UDIP assistant** is the part where the law gives a crisp, checkable workflow: classify, find, draft, watch deadlines. The measurable promise is "no request passes day 14 without a legally sufficient action".
- **(A) Citizen page:** a UDIP form must not force identity (the office's own form says data are optional) but should explain that a name and a signature will be needed if a decision is issued, and after III OSK 2396/25 may offer optional login (login.gov.pl) as the low-friction way to be identified. The gov.pl national service already requires login. [V]
- **(B) and (C)** do not touch UDIP directly, but any document produced there becomes public information the moment it is in the office's files; design storage with anonymisation in mind.
- **Security and legality hooks from this research:** audit trail of who "took a position" (art. 16 ust. 2 pkt 2), art. 12 metadata on every release, immutable registration (art. 23 exposure), human approval gates per taxonomy, review of the RODO clause sentence about automated processing.

## Verdicts on the previous research

| ID | Claim | Verdict | Source | One-line correction |
|---|---|---|---|---|
| C4 | No official form; Bydgoszcz offers an auxiliary template, PDF 30900 and DOCX 30899 | **CONFIRMED** | Both URLs return HTTP 200 (PDF 2 pages 399 kB; DOCX 29 kB), attached to BIP page /artykuly/1052, published 30.03.2026 | Template fields: place and date; addressee Prezydent Miasta Bydgoszczy; optional applicant block (name or entity name, street, postal code and town, e-mail, e-Doręczenia address, ePUAP address, phone) marked "Podanie danych nie jest obowiązkowe"; scope of the request based on art. 2 ust. 1; form (on-site inspection, electronic files, paper, other); manner of transfer (e-mail, e-Doręczenia, ePUAP, post, personal collection); optional date and signature; RODO clause. |
| C5 | A request may be anonymous; data and signature needed only for a decision | **PARTLY** | NSA I OSK 1277/08, I OSK 692/18 (classic line); NSA III OSK 1602/24 and III OSK 2396/25 of 9.06.2026 (restrictive line) | Still the Bydgoszcz form's position and the classic line, but since 2024-2026 the NSA accepts that an office may require the applicant's name and clarify identity when the sender is unidentifiable; treat anonymity as an office policy choice, not a guaranteed right. |
| C6 | Without undue delay, max 14 days; extension up to 2 months from filing with notice and reasons within 14 days | **CONFIRMED** | UDIP art. 13 ust. 1-2 (ELI text); BIP Bydgoszcz card | The notice must also state the new date; fee cases follow art. 15 ust. 2 timing. |
| C7 | Not public information, not held, or separate regime: ordinary letter, not a decision | **CONFIRMED** | BIP Bydgoszcz card lists exactly these three letter cases; art. 16 ust. 1 limits decisions to refusal and art. 14 ust. 2 discontinuance | Also a letter (not a decision) when the information is already in BIP, portal danych or CRU JSFP. Suspected abuse is disputed (letter or decision). |
| C8 | Requests can be sent to urzad@um.bydgoszcz.pl; valid after 1.01.2026 | **CONFIRMED** | BIP page /artykuly/1052, last updated 30.03.2026 | Channels listed: post, in person at the secretariat, fax (52) 58 58 623, e-Doręczenia address AE:PL-91453-53730-WDRHC-24, e-mail urzad@um.bydgoszcz.pl; ePUAP /umb/SkrytkaESP appears in the contact block. |
| C9 | gov.pl service "Uzyskaj informację publiczną" requires login through login.gov.pl (Profil Zaufany) | **CONFIRMED** (wording too narrow) | https://www.gov.pl/web/gov/uzyskaj-informacje-publiczna | Login goes through login.gov.pl with any supported method (profil zaufany, e-dowód and others); the same page says information can also be obtained by e-mail or phone without the online form; submission via ePUAP or e-Doręczenia. |

## Open questions and what could not be verified

1. **Exact yearly number of UDIP requests in UM Bydgoszcz for 2023-2025**, share answered late, number of refusal decisions and court cases against Prezydent Miasta Bydgoszczy. Looked in: BIP Bydgoszcz sitemap, web search, Watchdog 2023 report (band only), CBOSA (keyword queries for "Prezydent Miasta Bydgoszczy" did not return a parsable list). Best next step: ask the city during the hackathon, or find the Bydgoszcz case in the Feder monitoring "Wnioski o informacje w 2022".
2. **Who handles UDIP in Bydgoszcz internally.** The BIP card is published by Biuro Komunikacji Społecznej, which suggests a coordinating role; the internal procedure (zarządzenie Prezydenta) was not searched.
3. **TK K 1/21** outcome: not confirmed. Searched: web search only; the Tribunal's database was not opened.
4. **Whether CRU JSFP is live and its public URL and API.** Statute verified; operation only from secondary summaries. Check gov.pl/web/finanse (Aktualności CRU JSFP) and whether the register offers an API.
5. **Appeal body for re-use decisions of a city president** (art. 43 ust. 1 of the 2021 act names the minister; relation to SKO not checked).
6. **Current case law on the form of reaction to abuse** (letter versus decision) and on fee notices: stated from background knowledge, not re-verified.
7. **Texts of KPA articles** (63, 64, 107, 129), PPSA articles (53, 54, 55, 149), Prawo prasowe art. 3a, the petitions act, the environmental information act: cited from background knowledge; only the current consolidated-text numbers of KPA and PPSA were verified.
8. **TK K 17/05, TK P 25/08, SN I CSK 190/12**: not re-opened tonight.
9. **Terms of use** of the ELI API, CBOSA, SAOS and the data licence of Feder: not found or not checked.
10. **Sejm print 2721 and interpelacja 15564**: known only from a search summary.
11. Whether the Bydgoszcz office will change its "data not mandatory" position after NSA III OSK 2396/25.

## Sources

Statutes and official data (opened):

- https://api.sejm.gov.pl/eli/acts/DU/2001/1198
- https://api.sejm.gov.pl/eli/acts/DU/2022/902 and https://api.sejm.gov.pl/eli/acts/DU/2022/902/text.html
- https://api.sejm.gov.pl/eli/acts/DU/2025/1844 and https://api.sejm.gov.pl/eli/acts/DU/2025/1844/text.pdf
- https://api.sejm.gov.pl/eli/acts/DU/2023/1524/text.html
- https://api.sejm.gov.pl/eli/acts/search?title=Kodeks%20post%C4%99powania%20administracyjnego&type=Obwieszczenie&publisher=DU&dateFrom=2023-01-01 (DU/2025/1691)
- https://api.sejm.gov.pl/eli/acts/search?title=Prawo%20o%20post%C4%99powaniu%20przed%20s%C4%85dami%20administracyjnymi&type=Obwieszczenie&publisher=DU&dateFrom=2023-01-01 (DU/2026/143)

Bydgoszcz and gov.pl (opened):

- https://bip.um.bydgoszcz.pl/artykuly/1052/udostepnianie-informacji-publicznej
- https://bip.um.bydgoszcz.pl/artykuly/1053/ponowne-wykorzystanie-informacji-publicznej
- https://bip.um.bydgoszcz.pl/attachments/download/30900 and https://bip.um.bydgoszcz.pl/attachments/download/30899
- https://bip.um.bydgoszcz.pl/sitemap , https://bip.um.bydgoszcz.pl/rss , https://bip.um.bydgoszcz.pl/robots.txt
- https://www.gov.pl/web/gov/uzyskaj-informacje-publiczna

Case law (opened on CBOSA): links in the table in section 4.

Reports and other documents (opened):

- https://siecobywatelska.pl/wp-content/uploads/2023/12/Wyniki-monitoringu-realizacji-wnioskow.pdf
- https://bip.um.wroc.pl/attachments/download/99901
- https://bip.brpo.gov.pl/sites/default/files/2026-02/Do_NSA_informacja_publicznej_anonimowy_wniosek_22_10_2025_wymazany.pdf (file name as published: `Do_NSA_informacja_publiczna_anonimowy_wniosek_22_10_2025_wymazany.pdf`)
- https://fedrowanie.siecobywatelska.pl/api/ and https://github.com/watchdogpolska/feder
- https://www.saos.org.pl/api/search/judgments
- https://api.dane.gov.pl/1.4/datasets?q=Bydgoszcz

Secondary, not opened (search summaries only):

- https://www.gov.pl/web/finanse/Aktualnosci-CRU-JSFP
- https://www.gov.pl/web/finanse/najczesciej-zadawane-pytania2
- https://www.infor.pl/prawo/nowosci-prawne/7615346,centralny-rejestr-umow-rusza-1-lipca-2026-r-dla-kogo-jest-obowiazkowy-ministerstwo-finansow-wyjasnia-jak-zalozyc-konto-i-przegladac-informacje-o-umowach.html
- https://api.sejm.gov.pl/sejm/term10/interpellations/15564/body
- https://api.sejm.gov.pl/sejm/term10/prints/2721/
- https://www.sn.pl/pl/o-sadzie-najwyzszym/wnioski-pierwszego-prezesa-sadu-najwyzszego-do-trybunalu-konstytucyjnego/1-2021
- https://bip.siecobywatelska.pl/uploads/files/Sprawozdania/2023%20Sprawozdanie%20merytoryczne%20SOWP%202023.pdf
