# R7 - Landscape: existing solutions, reusable components, pitch numbers

Access date for all sources: 2026-11-21. Labels: VERIFIED = primary page or document opened and read; SECONDARY = reliable secondary or search-listing only; UNVERIFIED = not confirmed. Research budget was tight (night before the event); gaps are listed honestly in section 9.

## TL;DR for builders

- **Build on, do not compete with, EZD RP.** NASK announces an "Asystent Urzedniczy AI" for EZD RP (summaries, document comparison, legal assistant, anonymiser, letter assistant) but as plans, no delivery date (SECONDARY). Position our UDIP assistant as a pluggable module with a clean API, not a DMS replacement.
- **EZD RP public page shows no REST API.** The gov.pl "Funkcje systemu" page lists a menu item "Piaskownica API" with no details; ePUAP, e-Doreczenia and KSeF integration are mentioned without technical detail (VERIFIED). Design an adapter layer; for the hackathon use files/mock EZD.
- **Which DMS Urzad Miasta Bydgoszczy uses is NOT established** (EZD RP, EZD PUW, Mdok, other). Do not claim it in the pitch. Section 1.3 lists where I looked.
- **mObywatel assistant runs on PLLuM** since 2025-12-31, but it cannot see registers, does not interpret law, and users are told not to type personal data (VERIFIED). It is a citizen FAQ finder, not a clerk tool: no overlap with our core.
- **Licences for the model stack:** Bielik-11B-v3.0-Instruct is Apache 2.0 (gated download); PLLuM 12B and 8x7B (non-"nc") are Apache 2.0, Llama-PLLuM 8B/70B follow the Llama 3.1 licence, "nc" variants are non-commercial (VERIFIED on the model cards; the PLLuM card table I could read lists only the 2412 generation, newer 2508/2512 repos exist per HF search listing, SECONDARY).
- **PII building blocks:** Presidio (MIT) has a built-in `PL_PESEL` recogniser with checksum (SECONDARY); spaCy `pl_core_news_lg` is GPL-3.0 (copyleft trap); HerBERT derivatives are CC BY 4.0; `urchade/gliner_multi_pii-v1` is Apache 2.0 but Polish is not among its listed languages. Rule-based PL identifiers (PESEL, NIP, REGON, IBAN checksums) plus an LLM/NER pass is the safe stack.
- **HackNation 2025 has no reusable public code for our topic.** "Dane bez twarzy" (NASK, text anonymisation for PLLuM training) was won by Habanero Code; NASK signed a transfer agreement (VERIFIED, local press). The public GitHub repo found only holds task PDFs. Do not plan on borrowing 2025 code.
- **FOIA abroad: value is in triage, routing, search, first-pass; the failures are over-redaction, automation bias, no published error rates, and requester-side AI floods** (SECONDARY, mostly vendor/advocacy). Keep every decision human.
- **Numbers that are solid:** NASK survey of 6,093 officials (Oct-Nov 2025): 81% see routine-task automation as the main benefit, 67% want natural-language search in official documents, only 6% accept AI deciding about people (VERIFIED, read from NASK PDF). Watchdog 2023: only 83 of at most 384 gminas recorded any inaction complaint for 2022 (VERIFIED). Hard per-city UDIP volumes for Bydgoszcz do not exist publicly.
- **Genuine white space:** nothing found that combines a clerk's UDIP triage assistant with a citizen QR pre-registration page and a one-profile multi-form prefill that prints official templates. Each piece exists separately; the combination in a Polish city office was not found.

## 1. Polish public sector

### 1.1 EZD RP (NASK)

| Item | Finding | Status |
|---|---|---|
| What | Free electronic document management system for public administration, built by NASK, offered also as cloud SaaS | SECONDARY (gov.pl MC deck as quoted by search; EZD RP site) |
| Functions | Register incoming/outgoing correspondence (electronic, paper, scans) with metadata; build objects and documents from templates; forward for review, assign tasks (approval, signature), workflow paths; open/manage/close cases; electronic archive | VERIFIED https://www.gov.pl/web/ezd-rp/funkcje-systemu |
| Integrations | ePUAP, e-Doreczenia, KSeF mentioned; no technical detail; menu entry "Piaskownica API" (API sandbox) without content | VERIFIED same page |
| Adoption | No figures on that page. Interreg page: EZD RP fully operational since 2022, plan: all public institutions by end of 2026; EZD PUW (Bialystok, since 2011) is the base that EZD RP grew out of | VERIFIED https://www.interregeurope.eu/good-practices/ai-based-case-assignment-and-search-module-0 (published 2023-10-10) |
| Delivered AI | Optional module in EZD PUW suggesting which employee should receive incoming correspondence (NLP + case history). Users listed: Gdansk City Hall, NASK, Podlaskie Voivodship Office. No accuracy or time-saved figures published | VERIFIED same page |
| Announced AI | "Asystent Urzedniczy AI": summarising letters, comparing versions, legal assistant, anonymiser, letter assistant; also letter generator/editor, automatic dekretacja (routing decree), metadata completion, "Asystent Procedur"; SaaS EZD RP and support platform in 2026, support from 2027; stated as integrated with EZD RP and other EZD-class systems | SECONDARY (search synthesis of NASK/MC presentations of Sept 2026 and March 2026, not opened) |

Implication: NASK will likely ship a generic anonymiser and letter assistant. Our differentiator must be UDIP-specific legal workflow (classification, deadlines, art. 5/6/14 UDIP logic, duplicates) and the front-desk side, not generic summarisation.

### 1.2 mObywatel virtual assistant and PLLuM

- mObywatel assistant: available from 2025-12-31 (announced 2025-12-30), model PLLuM, pilot of about two months, app version 4.71.1+; finds forms and services, explains procedures, answers from the security guide, asks follow-up questions. Limits: no access to state registers, no case-specific answers, does not interpret law, users should not enter personal data, may be imprecise. No user counts published on the page. VERIFIED https://www.gov.pl/web/cyfryzacja/nowa-usluga-w-mobywatelu-wirtualny-asystent-ulatwi-korzystanie-z-uslug-publicznych
- mObywatel platform context (VERIFIED, voivodeship office page of 2026-05-06): over 11.5 million users; 220+ offices accept ePayments in the app; Bydgoszcz was the first Polish city to pilot ePayments (about 48.9 thousand transactions worth over 4.5 million PLN, in production since early 2026). https://www.gov.pl/web/uw-kujawsko-pomorski/bydgoszcz-pionierem-cyfryzacji-konferencja-cyfrowy-samorzad---kujawsko-pomorskie . Note: that page is about the Urzad Wojewodzki, but its statement on Bydgoszcz city ePayments is explicit.
- PLLuM for local government: gov.pl (2025-08-08) names Czestochowa as the first Polish local government to pilot PLLuM with the Ministry; uses listed: drafting official letters, summarising documents, analysing citizen inquiries; models "open and available" to administration, researchers, business. VERIFIED https://www.gov.pl/web/cyfryzacja/polski-model-jezykowy-pllum-trafi-do-samorzadu . A search result also claimed an agreement of Gdynia with a HIVE AI consortium (city chatbot and BIP search); the gov.pl page I opened does not mention it, so treat Gdynia/HIVE AI as UNVERIFIED.

### 1.3 Urzad Miasta Bydgoszczy: document system and e-services stack

- DMS used by the city hall: **not established.** Searched: web search for "Urzad Miasta Bydgoszczy EZD" (only the Voivodeship Office, which is a different body and runs EZD as main workflow with 80% of cases electronic, VERIFIED above, and old NIK audits of 2011/2015 turned up); bip.um.bydgoszcz.pl searches returned nothing on the DMS. The Watchdog monitoring PDF mentions that one gmina reviewed all requests "in EZD" (generic, not Bydgoszcz). Recommend: ask the organiser's city contact tomorrow; build with an adapter, assume a generic DMS.
- E-services known: mObywatel ePayments (above). City main office hours (aggregator, SECONDARY): Mon/Wed/Thu 8-16, Tue 8-18, Fri 8-14, ul. Jezuicka 1; paper start-of-business applications stop 2026-11-01 (CEIDG, aggregator listing dated 2026-10-21, UNVERIFIED on official BIP).
- No public UDIP register for UM Bydgoszcz was found (consistent with research file 02, point 10). Only a few gminas publish registers; the Act contains no duty to (Watchdog report, VERIFIED).

### 1.4 Other 2025-2026 AI projects for officials

- NASK survey "AI w e-administracji publicznej - perspektywa urzednikow i instytucji" (PDF, March 2026; quantitative survey Oct-Nov 2025). VERIFIED (read locally from https://nask.pl/media/2026/03/AI-w-administracji-publicznej_.pdf). Key facts: n=6,093 in some tables; 46% of respondents used GenAI for work in the prior six months (as reported by search summary; the PDF's base for task usage is n=2,823 who did use it); most used for fact/info search (59%), writing/editing (46%), documentation search (30%), summarising/translating (25%). Largest perceived potential: translation (77%), search and analysis of existing documentation (72%), analysis of large document sets (69%). Most wanted functions: working with documents in various formats (72%), natural-language search in official documents (67%). Benefit: automation of routine tasks (81%). Barriers: unclear legal rules (73%), lack of regulation (73%), no internal procedures (70%). Only 6% accept AI taking decisions about other people. 75% say national public institutions should deploy AI. 87% want AI training.
- Hackathon-derived: NASK took over the Habanero Code anonymiser used to prepare PLLuM training text (section 3).

## 2. Automation of public-information requests

### 2.1 Poland

- No dedicated UDIP triage product was found for Polish offices. BIP vendors provide a request form and publish content; the law has no register duty. Watchdog Polska (Siec Obywatelska) runs monitoring and a public "Feder" system of about 75 thousand cases (per research file 02, not re-verified here) that can serve as an evaluation corpus.
- Watchdog monitoring of 2022 data (requests sent 2023-07-11 to gminas, counties, voivodeship offices, ministries and others): VERIFIED https://siecobywatelska.pl/wp-content/uploads/2023/12/Wyniki-monitoringu-realizacji-wnioskow.pdf
  - answers took from the statutory 14 days to several months; some offices were reminded before answering;
  - many offices treated the request (or part) as "informacja przetworzona" (processed information), often only after reminders and extended deadlines;
  - at most 384 gminas answered the complaint question; only 83 recorded inaction complaints (137 in total), 18 recorded complaints against decisions (17 complaints, 5 appeals); 9 gminas had 3-9 inaction complaints;
  - respondents differ widely in data quality, and there is no register obligation.
  - Takeaway for the pitch: volumes per gmina are low and uneven (most gminas had at most two complaints), so the value story is **consistency, deadline safety and legal quality**, not mass automation.

### 2.2 Abroad

| Topic | Evidence | Status |
|---|---|---|
| US FY2025 | about 1.7 million federal FOIA requests (+13%, record); DOJ 159,743 requests, backlog 21,567 to 29,309; DHS pending 221,068 to 245,572; average wait of pending requesters over 240 days (one analysis); statutory 20 working days | SECONDARY (Nextgov commentary by a vendor employee, https://www.nextgov.com/ideas/2026/11/ai-changing-both-sides-foia-heres-how-agencies-should-prepare/417215/ ; HHS and agency reports cited by search) |
| US pilots | HHS Office of the Secretary: LLM review and redaction pilot, outputs reviewed by FOIA professionals; CMS proof of concept for exemptions (b)(4), (b)(6), (b)(7)(C); MITRE "FOIA Assistant" finds records and suggests redactions for three exemption categories (page returned 403, not read); State Department said model accuracy equals human 97-99% on declassification review and saved about half a year of work | SECONDARY (search listings) |
| Criticism | Automation bias in accepting AI redactions; no published error rates; no requester notice that AI was used; "powerful tool for secrecy" (Cuillier); over-redaction tendency; Knight Institute: OMB 2025 AI memo does not list FOIA processing as presumptive high-impact AI | SECONDARY https://knightcolumbia.org/research/pacing-foias-frontier |
| Requester-side AI | Anecdotal bursts of 50-100 requests at once; one expert claim that 83% of AI-written requests are broad enough to be "overly burdensome" (secondhand, UNVERIFIED) | SECONDARY |
| UK | Central government 2024: 83,041 requests, 76% answered in time (down from 81%); 2025: 94,526 requests, 87% in time | SECONDARY (gov.gov.uk bulletins, search snippets) https://www.gov.uk/government/statistics/freedom-of-information-statistics-annual-2025/freedom-of-information-statistics-annual-2025-bulletin |
| UK Clearing House | Cabinet Office "applicant-blind" breach criticism; tribunal criticised lack of transparency; unit reconfigured after review | SECONDARY |
| Alaveteli / WhatDoTheyKnow | 109,653 requests made in 2022 via WhatDoTheyKnow; 867,303 published at that time; Alaveteli sites exceeded one million requests (mySociety 2022-08-31); public archive lets users check existing requests before filing | SECONDARY https://www.mysociety.org/2022/08/31/more-than-a-million-public-foi-requests-have-been-made-through-alaveteli-sites/ |

**Functions that proved valuable** (convergent across sources): routing and classification of incoming requests, first-pass responsive-document search, summarisation, grouping similar or recurring requests while preserving each requester's rights and deadlines, public archive of past answers (reduces repeats), human review of every release or withhold decision, audit trails.
**Functions criticised or risky:** autonomous redaction without error rates, hidden AI use, aggregation of requests by requester identity (UK precedent: four requests in 24 hours aggregated by the Cabinet Office, ICO decision), identity-based handling ("applicant-blind" principle).
Polish note: UDIP is applicant-blind as well (anonymous requests were held admissible by NSA per RPO page, search listing, SECONDARY), so duplicate detection must work on content, not identity.

## 3. HackNation 2025 outputs

Event: held in Bydgoszcz, 6-7 December 2025 (SECONDARY: Security Ops, search listing; the GitHub repo description says November, conflicting); about 370 teams and 1.5 thousand participants; 16 tasks; prize pool 482,000 PLN, 25 thousand PLN to each winning team (SECONDARY, gov.pl summary). https://www.gov.pl/web/cyfryzacja/tysiace-pomyslow-24-godziny-i-jeden-cel--usprawnic-panstwo-w-bydgoszczy-zakonczyl-sie-hacknation-2025

Post-event status (VERIFIED from https://takajestbydgoszcz.pl/artykul/umowa-w-nask-i-inspiracja-n2582784 , status as of 2026-11-20):

| Task (owner) | Winner | Relevance to us | Code/licence |
|---|---|---|---|
| Dane bez twarzy (NASK) | Habanero Code | Text anonymisation for PLLuM training; transfer agreement signed; NASK hired one member (Mikolaj Pokrywka); credit as contributors in model docs | Not public; rights transferred by contract |
| AI w sluzbie decyzji (Ministry of Sport and Tourism) | White Hats (WIT PWr per local source; search listing said "Programisci PWR") | AI assistant: PDF extraction, summary, filling a decision template; delivered as a Word add-in; analysed as possible tool, no contract | No repo found |
| Sciezka prawa (MC) | Code Casimir (UKW) | Legal-path tool, possible pilot | none found |
| ZUS, KAS tasks | Kanapowcy, MEWA, Extempore | Copyright transfer to Ministry; KAS tools in internal testing, possible deployment 2027-01-01 | Not open |
| Others (fire service, JSW, dane.gov.pl lost-property, etc.) | various | Not relevant | Fire service required copyright transfer and code upload to a platform |

- Public GitHub repo `Ch3shireDev/hacknation-2025` contains only PDF task descriptions (for example AI_W_SLUZBIE_DECYZJI.pdf, DANE_BEZ_TWARZY.pdf), no solution code (SECONDARY, search listing). https://github.com/Ch3shireDev/hacknation-2025
- Organiser rule for 2026 (from the same article): rights are expected to pass to institutions, with exceptions such as open licences. This is why our repo should carry an explicit open licence and a note to the jury about rights.
- Conclusion: **no reusable open-source 2025 anonymiser or assistant found.** Reuse the ideas (Word add-in delivery, template-filling decision assistant) and the NASK-published model BANonymizer-PL (below), not hackathon code.

## 4. Polish-language building blocks and licences

### 4.1 LLMs

| Model | Licence | Notes | Status |
|---|---|---|---|
| Bielik-11B-v3.0-Instruct (SpeakLeash) | Apache 2.0, gated on HF (accept sharing of account info) | Paper arXiv 2601.11579 (dated 2025-12-30); native context up to 32,768 tokens per technical report; 24 quantised derivatives on HF; community Ollama pages exist for 11b-v3.0 and v3.1 (v3.1 with 32K context) | VERIFIED card https://huggingface.co/speakleash/bielik-11b-v3.0-instruct ; context and Ollama SECONDARY |
| Bielik v2.x | v2.3 GGUF card: Apache 2.0 plus Bielik Terms of Use; v2.6 not checked | Older releases are not uniform | SECONDARY |
| PLLuM-12B (base/instruct/chat), PLLuM-8x7B | Apache 2.0 | CYFRAGOVPL (Ministry of Digital Affairs) | VERIFIED https://huggingface.co/CYFRAGOVPL/PLLuM-12B-chat |
| PLLuM "nc" variants (12B-nc, 8x7B-nc) | CC-BY-NC-4.0, non-commercial | Do not use in a deployable product | VERIFIED |
| Llama-PLLuM-8B / 70B | Llama 3.1 licence | Redistribution terms of Llama apply | VERIFIED |
| Newer PLLuM generations (12B-base-2508; Llama-PLLuM-8B-instruct/chat-2512; PLLuM-4B-instruct-2512) | not read (check card) | Exist as HF repos per search listing; the card table I could read shows only 2412 | SECONDARY |

Recommendation for the build: the hackathon needs reliable output now, so use a hosted frontier or open API for development speed behind an interface; for the "deployable in an office" story run Bielik-11B-v3.0 or PLLuM-12B (Apache 2.0) locally via Ollama/vLLM. Never send real citizen data to an external API; use synthetic data in the demo.

### 4.2 PII detection and NER

| Component | Licence | Polish fitness | Status |
|---|---|---|---|
| Microsoft Presidio analyzer | MIT | Built-in `PL_PESEL` recogniser (pattern + checksum + context); other PL identifiers need custom recognisers | SECONDARY (PyPI/docs listing) |
| spaCy `pl_core_news_lg` | GPL-3.0 | Works but copyleft; avoid shipping inside a permissively licensed repo, or load as optional download | SECONDARY (HF listing) https://huggingface.co/spacy/pl_core_news_lg |
| NASK-PIB/BANonymizer-PL | Apache-2.0 | HerBERT-large-cased fine-tuned on BAN-PL (20k+ labelled examples); finds pseudonyms and surnames only; no metrics on card; about 0.4B params | VERIFIED https://huggingface.co/NASK-PIB/BANonymizer-PL |
| HerBERT-based NER (e.g. pczarnik/herbert-base-ner; lexedit/herbert-polish-legal-ner) | CC BY 4.0 (attribution; base HerBERT also CC BY 4.0 per a derivative's card) | PER/LOC/ORG (wikiann); lexedit is a Polish legal-text NER | SECONDARY |
| clarin-pl poldeepner2 / KPWr NER | KPWr corpus licence not confirmed | Strong classical Polish NER | UNVERIFIED |
| urchade/gliner_multi_pii-v1 | Apache 2.0 | Languages listed: EN, FR, DE, ES, PT, IT; Polish not listed (zero-shot may still work, test) | SECONDARY |
| GLiNER2-PII (Fastino, 0.3B, 42 entity types, 7 languages) | not shown | Polish not confirmed | SECONDARY arXiv 2605.09973 |
| flowxai/cee-pii (GLiNER fine-tune, Central/Eastern Europe, financial IDs) | not shown | Most relevant GLiNER variant; test on Polish | SECONDARY |
| llm-safe-pl (PyPI) | not checked | Writes PESEL/NIP/REGON/IBAN checksums from scratch; NER unreleased in the versions seen | SECONDARY |

Practical stack: regex plus checksum for PESEL, NIP, REGON, IBAN, ID-card numbers, phones, e-mails; BANonymizer-PL or a HerBERT NER for names; an LLM pass for context-dependent cases; every redaction proposal shown to the clerk with reason and legal basis. Do not rely on any model claiming recall; measure on synthetic data and report numbers (project rule: never ship an unmeasured number).

### 4.3 Embeddings, rerankers, corpora

Not verified in this session (budget). Candidates to check tomorrow on HF before choosing: multilingual bge-m3 and e5 families (licences MIT/Apache expected), Polish `sdadas` embedding and reranker models, and PIRB (Polish Information Retrieval Benchmark) for choosing. Polish legal sources for RAG: ISAP and Sejm API (research file 02 covers them), orzeczenia.nsa.gov.pl for administrative-court rulings (public; the search above surfaced hundreds of 2026 NSA rulings on UDIP, useful as a test corpus), Watchdog Feder cases. All UNVERIFIED here beyond NSA availability.

## 5. Front-desk and form-prefill prior art

Evidence in this session is thin; items below separate what was verified from what is background knowledge to be confirmed.

| Case | What it shows | Evidence | Status |
|---|---|---|---|
| Estonia X-Road, once-only | Savings estimates differ by year and method: 804, 1,345, 1,407, about 3,225 working years per year; "5 working days per citizen per year"; 1,800+ years with 2.7 billion queries (recent); no single authoritative method | https://cyber.ee/resources/news/saving-1407-years-of-working-time-in-estonia/ and other listings | SECONDARY; quote as "indicative" |
| Netherlands prefilled tax return | Introduced 2014, standard from 2016; shows prefill works at national scale when data comes from registers, not from the clerk | Wikipedia once-only article | SECONDARY |
| Denmark, GOV.UK prefill, German Buergeramt kiosks, hotel and clinic ID scanners, bank onboarding | No evidence found in this session | none | UNVERIFIED (searches returned only EU once-only material) |
| Poland: mObywatel documents, "zastrzez PESEL" (7.5 million users), ePayments | Citizens already hold a verified digital identity; our citizen page can accept data the citizen already has on the phone | gov.pl page above | VERIFIED |

Lessons to carry (from sources read): once-only works only with authoritative registers behind it (Estonia, NL); in Poland the clerk-side handoff and legal form templates remain paper-bound, which is the gap our (A)+(B) addresses. What went wrong elsewhere could not be established; flag as open.

## 6. Numbers for the pitch (each with source)

| Number | Value | Source | Status |
|---|---|---|---|
| Officials wanting NL search in official documents | 67% | NASK survey PDF | VERIFIED |
| Officials expecting routine-task automation as main benefit | 81% | NASK survey PDF | VERIFIED |
| Officials accepting AI deciding about people | 6% | NASK survey PDF | VERIFIED |
| Obstacle: unclear legal rules / no regulation / no internal procedures | 73% / 73% / 70% | NASK survey PDF | VERIFIED |
| Want AI training | 87% | NASK survey PDF | VERIFIED |
| GenAI use at work by officials (prior 6 months) | 46% | NASK, via search summary | SECONDARY |
| UDIP statutory deadline | 14 days (art. 13 ust. 1), extension possible; delay is bezczynnosc; art. 23 criminal exposure (fine, restriction of liberty or prison up to one year) | research file 02; NSA rulings listing | VERIFIED in file 02 |
| Gminas with any inaction complaint for 2022 | 83 of at most 384 answering (137 complaints) | Watchdog PDF | VERIFIED |
| Request handling time seen by Watchdog | from 14 days to several months | Watchdog PDF | VERIFIED |
| mObywatel users | over 11.5 million | gov.pl voivodeship page | VERIFIED |
| Bydgoszcz mObywatel ePayments | about 48.9 thousand transactions, over 4.5 million PLN | same | VERIFIED |
| US FOIA FY2025 | about 1.7 million requests; DOJ 159,743 | Nextgov | SECONDARY |
| UK central FOI | 94,526 requests in 2025; 87% in time | gov.uk bulletin | SECONDARY |
| Estonia once-only | 5 working days per citizen per year (estimate) | search listing | SECONDARY |

**Not found, do not invent:** UDIP request counts for Bydgoszcz or any named city (no register; ask via a public-information request to the city or use Watchdog's 2022 gmina answers on fedrowanie.siecobywatelska.pl), time per UDIP case, cost of delay in PLN, counter visits and form volumes for Bydgoszcz (the city's "Bydgoszcz w liczbach 2025" PDF was not opened; its excerpt shows no service volumes), time saved per form by prefill, error and return rates of paper applications. Suggested pitch wording: "We do not claim savings; we will measure on a synthetic set of N requests and report time-to-first-draft against a manual baseline."

## 7. Differentiation table

| Capability | Exists today | Who / status | What this project adds |
|---|---|---|---|
| DMS with workflow, e-Doreczenia, ePUAP | Yes | EZD RP, EZD PUW, others | Does not replace it; adapter and API |
| Auto-routing of incoming letters | Yes | AI module in EZD PUW (Gdansk, NASK, PUW) | UDIP-specific classification and legal-path suggestion |
| Generic summaries, letter drafts, anonymiser, procedure assistant | Announced | NASK "Asystent Urzedniczy AI" (plans) | UDIP legal logic: art. 5/6/14, processed information, deadlines, duplicates, fee/extension decisions as proposals with citations |
| Citizen FAQ chatbot | Yes | mObywatel assistant on PLLuM (no register access, no personal data) | Not competing; our citizen page collects structured data, not chat |
| Request register and archive of answers | Rare | A few gminas, Alaveteli abroad | Internal searchable register with duplicate and mass-request detection that is content-based (applicant-blind) |
| Redaction support | Abroad pilots; PL anonymiser inside NASK | HHS, CMS, MITRE; Habanero Code transfer | Proposal-only redaction with reason and checksum-validated PL identifiers, human confirms, audit log |
| Citizen pre-registration by QR | Not found in Polish offices | (queue and e-service systems exist, not verified) | (A) mobile page, data once, to the clerk |
| ID scan with large-print verification | Not found for Polish offices | hotels/clinics abroad unverified | (A) camera or reader, human-verified |
| One profile, chain of forms, official templates | Not found | none | (B) life-situation to form chain, prefill, print exact templates |
| AI form checking | Not found | none | (C) review agent suggesting corrections |

## 8. Verdicts on the previous research

The task listed no claim ids. Observations relevant to earlier files: file 02 point 10 (no UDIP register for UM Bydgoszcz) is consistent with what I found; the "Feder, about 75 thousand cases" figure was not re-verified.

## 9. Open questions and what could not be verified

1. DMS and e-service stack of UM Bydgoszcz (searched web, gov.pl, BIP-targeted queries; not found).
2. Content of NASK/MC presentations on "Asystent Urzedniczy AI" (only via search synthesis); check ezdrp.gov.pl and nask.pl directly.
3. Whether newer PLLuM (2508/2512) licences match the 2412 table.
4. Embeddings, rerankers, Polish legal corpora (section 4.3) not researched.
5. Prior art: Denmark, GOV.UK prefill, kiosks, hotel/clinic ID scanners, bank onboarding (searches returned nothing usable).
6. All Bydgoszcz volume, handling-time, cost, error-rate numbers (section 6).
7. MITRE FOIA Assistant page returned 403; US pilot metrics are secondary.
8. HackNation 2025 dates conflict (6-7 Dec 2025 per Security Ops vs November in a repo description); not important for the build.
9. Gdynia/HIVE AI PLLuM chatbot claim unverified.

## 10. Sources

- https://www.gov.pl/web/ezd-rp/funkcje-systemu
- https://www.interregeurope.eu/good-practices/ai-based-case-assignment-and-search-module-0
- https://nask.pl/media/2026/03/AI-w-administracji-publicznej_.pdf
- https://www.gov.pl/web/cyfryzacja/nowa-usluga-w-mobywatelu-wirtualny-asystent-ulatwi-korzystanie-z-uslug-publicznych
- https://www.gov.pl/web/cyfryzacja/polski-model-jezykowy-pllum-trafi-do-samorzadu
- https://www.gov.pl/web/uw-kujawsko-pomorski/bydgoszcz-pionierem-cyfryzacji-konferencja-cyfrowy-samorzad---kujawsko-pomorskie
- https://takajestbydgoszcz.pl/artykul/umowa-w-nask-i-inspiracja-n2582784
- https://www.gov.pl/web/cyfryzacja/tysiace-pomyslow-24-godziny-i-jeden-cel--usprawnic-panstwo-w-bydgoszczy-zakonczyl-sie-hacknation-2025
- https://github.com/Ch3shireDev/hacknation-2025
- https://hacknation.pl/zadania_hacknation/
- https://siecobywatelska.pl/wp-content/uploads/2023/12/Wyniki-monitoringu-realizacji-wnioskow.pdf
- https://huggingface.co/CYFRAGOVPL/PLLuM-12B-chat
- https://huggingface.co/speakleash/bielik-11b-v3.0-instruct
- https://huggingface.co/NASK-PIB/BANonymizer-PL
- https://huggingface.co/spacy/pl_core_news_lg
- https://pypi.org/project/pii-presidio/ (Presidio plugin listing)
- https://arxiv.org/abs/2601.11579 (Bielik v3 report)
- https://arxiv.org/pdf/2605.09973 (GLiNER2-PII)
- https://www.nextgov.com/ideas/2026/11/ai-changing-both-sides-foia-heres-how-agencies-should-prepare/417215/
- https://knightcolumbia.org/research/pacing-foias-frontier
- https://www.gov.uk/government/statistics/freedom-of-information-statistics-annual-2025/freedom-of-information-statistics-annual-2025-bulletin
- https://www.mysociety.org/2022/08/31/more-than-a-million-public-foi-requests-have-been-made-through-alaveteli-sites/
- https://cyber.ee/resources/news/saving-1407-years-of-working-time-in-estonia/
- https://www.mitre.org/news-insights/impact-story/mitre-tool-simplifies-freedom-information-act-requests (403, listing only)
