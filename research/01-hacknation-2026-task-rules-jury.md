# R1 - HackNation 2026: the task, the rules, the jury, last year's winners

Research date: 2026-11-20 (evening, the day before the event). Status labels: **VERIFIED** = primary source opened and read; **SECONDARY** = reliable secondary source only; **UNVERIFIED** = inference or not confirmed. All hacknation.pl pages and PDFs were downloaded and read on 2026-11-20; 2025 materials come from the Internet Archive (Wayback Machine).

## TL;DR for builders

- **The full task card does not exist publicly yet.** Only a three-sentence teaser is published. Full text, requirements, criteria with weights, IP clause and submission rules appear on Saturday **21.11.2026 at 11:00** on hacknation.pl/zadania (and in HackTribe "Challenges"). First job at 11:00: read the card and re-map this repository to its criteria. (VERIFIED)
- **Hard deadlines:** draft in HackTribe by **Sat 20:00** (project name, team name, task choice, repo link, table number, short description, approach, progress). Task choice is frozen after 20:00. Final submission **Sun 11:00**: all fields, presentation **PDF, max 10 MB**, working links, short demo (organisers recommend **up to 2 minutes**). No changes after 11:00. (VERIFIED)
- **Two-stage judging.** Stage 1: jurors score each criterion 0-10 in HackTribe, weights from the task rules, "only a few minutes" per project; **top 5 per task** go to the final. Stage 2 (Sun 15:15): **5 min live pitch + 5 min Q&A**, scored independently of stage 1, winner by simple majority vote of the task jury. (VERIFIED)
- **The jury is the partner's jury** (min. 3 people chosen by Miasto Bydgoszcz, published on day two at the latest). Expect city officials, not ML researchers: speak about clerk time saved, legal safety, deployability and cost. (VERIFIED rule; composition unpublished)
- **Prize for our task: 15 000 PLN** (second lowest of 15 tasks; the range is 11 111-33 333 PLN). Lower prize probably means fewer competing teams. (VERIFIED amount; competition level UNVERIFIED)
- **Stay on UDIP.** In 2025 "Związek z wyzwaniem" (fit to the challenge) weighed 20-30 % in most cards and 30 % in the Bydgoszcz card; "Potencjał wdrożeniowy" 20-40 %. The demo's first screen must be an access-to-public-information request being analysed and answered. The wider counter/forms product is one slide of "what the same engine does next". (VERIFIED 2025 weights; 2026 weights unknown)
- **Best predictor of tomorrow's card:** the 2025 task "AI w służbie decyzji" (Ministerstwo Sportu i Turystyki), an AI assistant for officials. It required: repo, PDF max 10 slides, video max 3 min, description of **guardrails**, architecture, **justified model choice for public administration**, integration plan, declared response time, QA/evaluation methodology, security and data protection, deployment plan. Open-source or free models were "preferred". Prepare all of these as ready sections. (VERIFIED for 2025)
- **Pre-made material must be disclosed.** FAQ: earlier or external resources, tools and repositories are allowed only if honestly cited in the presentation and code. This public brief repository is such a resource: cite it in README and on a slide; write the product code during the 24 hours. (VERIFIED)
- **AI coding assistants are not banned** by the Regulamin, the guide or the FAQ; the guide only says doubts about "korzystanie z AI" must be clarified before submission. Ask on Discord `#zapytaj-organizatora` once and keep the answer. (VERIFIED absence of a ban; explicit permission UNVERIFIED)
- **IP:** expect transfer of economic copyright (autorskie prawa majątkowe) of the *winning* project to the city, or an open-source obligation; the exact clause is in the task's own rules at 11:00. Do not copy code from 2025 repos: the ones checked have **no licence file**. (VERIFIED)
- **No LLM access, cloud credits or data sets are promised** anywhere in the published materials; only Wi-Fi, RJ45, power, table. Bring your own model access and an offline fallback; ask the city's stand for sample requests. (VERIFIED absence)
- **On-site only**, adults, EU citizens or EU residents, teams of 1-6, max two tasks per team with one separate project per task. (VERIFIED)

---

## 1. Official facts from hacknation.pl (2026 edition)

Sources read: home page, `/zadania`, `/przewodnik-uczestnika`, `/faq`, `/mentorzy`, `/media`, Regulamin PDF (file dated 19.11, in force from 28.09.2026), Przewodnik Uczestnika PDF (22 pages), Tutorial HackTribe PDF (9 pages). Pages `/regulamin`, `/agenda`, `/partnerzy`, `/jury`, `/sitemap.xml` return 404; the agenda is a section of the home page; no jury page exists yet.

### 1.1 Basic facts

| Item | Value | Status |
|---|---|---|
| Dates | 21-22 November 2026, coding Sat 11:00 - Sun 11:00 (24 h) | VERIFIED (home, guide PDF) |
| Venue | Bydgoskie Centrum Targowo-Wystawiennicze (BCTW), ul. Gdańska 187, 85-674 Bydgoszcz; coding in Hala 2, mentors in Hala 1 | VERIFIED (FAQ, guide PDF) |
| Organisers | Ministerstwo Cyfryzacji, Departament GovTech Polska, Miasto Bydgoszcz; legal Organizator = Ministerstwo Cyfryzacji; an external Operator runs registration and platforms | VERIFIED (home, Regulamin 1.1) |
| Scale | "15 wyzwań od 14 partnerów"; prize pool "+370 000 PLN" (sum of the 15 published main prizes = 382 000 PLN, own addition) | VERIFIED |
| Previous edition | "blisko 1500 uczestników na miejscu i 437 zgłoszonych rozwiązań" | VERIFIED (home) |
| Participation | on-site only ("udział jest tylko stacjonarny"); free; adults; EU citizens or third-country citizens with an EU residence card; ID checked at entry | VERIFIED (FAQ, Regulamin 1.1 j, 3.4) |
| Team | 1 to 6 people; one person can be in one team only; composition is final at submission | VERIFIED (FAQ, Regulamin 4.6) |
| Tasks per team | max two tasks, one project per task; a second project needs a different Team Leader; same project in two tasks is "zdecydowanie odradzane" | VERIFIED (guide, HackTribe tutorial) |
| Infrastructure | table, chair, power, Wi-Fi, wired RJ45 (bring an adapter), 5 meals, rest zone with camp beds, showers | VERIFIED |
| LLM access, cloud credits, API keys, data sets | **not mentioned** in any published document; data may come with the task card or from the partner's stand (2025 practice) | VERIFIED absence |
| Communication | Discord is the main channel; one channel per task for booking mentors; `#zapytaj-organizatora`, `#faq` | VERIFIED |
| Submission platform | **HackTribe** (new in 2026, English UI); login through a special link posted in the Discord announcements channel; a partner may name a different platform in its task rules | VERIFIED |

### 1.2 Hour-by-hour schedule (home page agenda + guide)

| When | What |
|---|---|
| Sat 21.11, 08:00 | Registration opens, breakfast |
| Sat 10:30 | Opening ceremony |
| **Sat 11:00** | **"Publikacja pełnych treści zadań - Start Kodowania"**; HackTribe opens for uploads; team building in the coding zone |
| Sat 13:00 | Lunch |
| Sat 16:00 | Talk |
| Sat 18:00 | Pizza |
| **Sat 20:00** | **Draft checkpoint**: project must exist in HackTribe; no new projects and no change of task afterwards |
| Sun 22.11, 07:00 | Breakfast |
| **Sun 11:00** | **End of coding, final submission deadline, stage 1 judging starts** |
| Sun 11:30 | Talk |
| Sun 13:00 | Lunch |
| **Sun 14:45** | Finalists announced (Discord); order of pitches announced; stage 1 scores visible around 15:00 |
| **Sun 15:15** | Pitching, stage 2 |
| Sun 17:15 | Awards and closing |

### 1.3 What must be submitted

Draft (Sat 20:00), mandatory HackTribe fields: project name, team name, **partner task**, table number, short description of the solution, approach, progress so far, **repository where the team works**. A few sentences are enough; everything except the task can be edited until Sun 11:00.

Final (Sun 11:00): "Uzupełnij wszystkie wymagane pola oraz dodaj prezentację i materiały umożliwiające sprawdzenie projektu, zgodnie z wymaganiami zadania." The presentation must be **PDF, max 10 MB**; there is an extra field for other materials; presentation fields become mandatory on Sunday. The guide's pre-submission checklist: correct task, correct team data, all required fields, **the reviewer can run or see the project**, links work, description matches the final version, no draft text left.

Task-specific deliverables (video length, slide limit, repo requirements) are defined by the task card. In 2025 the usual set was: title and description, PDF up to 10 slides, video up to 3 minutes hosted at an open link, code repository, screenshots, demo link (section 3).

Quote to remember: "Jurorzy mają tylko kilka minut na ocenę rozwiązania. Przygotuj konkretny opis, działające linki i krótkie demo (zalecamy do 2 minut)."

### 1.4 Judging rules (Regulamin point 5 + guide)

- Each task (Konkurs) has its own jury of **at least three members**, chosen by the task's organiser, i.e. the partner. Composition is published "najpóźniej drugiego dnia Wydarzenia".
- Criteria differ per task and are published with the full task description "najpóźniej w dniu rozpoczęcia Wydarzenia o godz. 11:00".
- **Stage 1**: jurors score each criterion **0-10** in HackTribe; HackTribe applies the weights from the task rules; **five** best teams per task qualify (all teams if fewer than five were scored).
- **Stage 2**: live presentation before the task jury, "maksymalnie 5 minut na prezentację rozwiązania (pitch), po której następuje maksymalnie 5 minut na pytania jury". Stage 1 results are not carried over. Jurors decide jointly by simple majority; the chair breaks ties. Presentations are not recorded.
- The jury may refuse to pick a winner if no solution reaches an adequate level, "w szczególności, gdy opracowane rozwiązania nie zdobędą co najmniej 50% maksymalnej liczby punktów".
- Decisions are final. Changes made after the deadline are ignored.
- What finalists must explain (guide): what problem you solve and what you built, how it works, why it is valuable or different, **what you implemented during HackNation**.

### 1.5 Prizes, tax, IP, AI tools, earlier work

- Prize pool per task 11 000-34 000 PLN gross (Regulamin 4.19). Prizes go only to winning teams; partners may add distinctions and small in-kind prizes. The party promising the prize (often the partner) acts as tax payer. (VERIFIED)
- **IP**, Regulamin point 6: each participant declares authorship of their contribution and that it does not infringe third-party rights; task rules "mogą przewidywać zasady nabycia przez organizatora danego Konkursu autorskich praw majątkowych". FAQ: "Przewiduje się przeniesienie autorskich praw majątkowych do zwycięskich projektów na instytucje zgłaszające wyzwania. W niektórych przypadkach mogą jednak obowiązywać inne rozwiązania, np. udostępnienie projektu na licencji open source." Details come with each task's rules by 21.11, 11:00. (VERIFIED)
- **Consequence for a public, openly licensed repository:** publishing the brief before the event does not prevent a later transfer of rights by the authors, but exclusivity cannot be granted for parts already released under an open licence. Keep third-party code out, record licences of every dependency, and be ready to state this to the jury. (own analysis, UNVERIFIED against the 2026 Bydgoszcz clause)
- **AI coding assistants:** no rule mentions them. The only reference is in the web guide: "Wątpliwości dotyczące korzystania z AI, wcześniej przygotowanego kodu czy praw autorskich wyjaśnij przed zgłoszeniem projektu." The 2025 card of the closest task allowed paid models and tools while preferring open or free ones. (VERIFIED)
- **Earlier work:** FAQ, question about pseudocode and UI prepared before the event: "Jeśli chcesz skorzystać z wcześniej ukończonych lub zewnętrznych zasobów, narzędzi, repozytoriów itp., musisz je rzetelnie zacytować lub wymienić, że użyłeś ich w swojej prezentacji, kodzie itp." (VERIFIED)
- **Winning does not mean deployment.** Press summary of the organisers' message (18.11.2026): winning teams may continue with the institution; projects then go through verification, tests and adaptation to organisational, legal and technological requirements. (SECONDARY, eska.pl)

### 1.6 A curiosity that explains claim C3

The home page has a decorative animated code background. It contains fragments such as `cipher = AESGCM(key)`, `nonce = os.urandom(NONCE_LENGTH_BYTES)`, `dst.write(MAGIC_HEADER)` and `if compute_digest(decrypted_bytes) != envelope.get("checksum"): raise ValueError("Payload integrity checksum mismatch")`. It is page decoration, not a technical guideline. No official HackNation document recommends any encryption pattern. (VERIFIED)

---

## 2. The Miasto Bydgoszcz task "Inteligentny asystent urzędnika"

### 2.1 Everything that is published (verbatim, hacknation.pl/zadania)

| Field | Text |
|---|---|
| Inicjator projektu | MIASTO BYDGOSZCZ |
| Kampania | Inteligentny asystent urzędnika |
| Opis | "Jak usprawnić obsługę wniosków o dostęp do informacji publicznej i odciążyć urzędników od powtarzalnych zadań? Wyzwanie polega na stworzeniu inteligentnego i bezpiecznego asystenta, który wesprze pracowników urzędu w analizie wniosków i przygotowywaniu odpowiedzi. Celem jest skrócenie czasu obsługi spraw i usprawnienie codziennej pracy administracji" |
| Nagroda Główna | 15 000,00 |

Reading of the teaser (own analysis):

- User = "pracownicy urzędu" (clerks), not citizens.
- Two named functions: "analiza wniosków" (analyse requests) and "przygotowywanie odpowiedzi" (draft answers).
- Two named qualities: "inteligentny" and **"bezpieczny"**. Security is in the task sentence itself, so it will very likely be a criterion.
- Two named outcomes: "skrócenie czasu obsługi spraw" and "odciążenie od powtarzalnych zadań". Measure both in the demo (minutes per request before and after, share of repeated requests answered from earlier answers).
- "codzienna praca administracji" leaves a door open for reuse beyond UDIP, but only as a side effect.

No other hint was found: the city is named as co-organiser on the home page and in the press, but no city news item, press article or ministry communiqué describing the task content was found (searched: web search for the task name with "Bydgoszcz", gov.pl/web/cyfryzacja communiqué of 16.06.2026, eska.pl article of 18.11.2026, bydgoszcz.pl site search, hacknation.pl/media). Social media of the city and of HackNation (Facebook, Instagram, LinkedIn) and the Discord server were not read (login walls). (UNVERIFIED what they contain)

### 2.2 Who in the city owns the topic

- The official mentor list on hacknation.pl includes two Urząd Miasta Bydgoszczy officials: the **Dyrektor Biura Rady Miasta** (Jacek Rosół) and the **Kierownik Referatu Komunikacji Społecznej** (Łukasz Okoński). These are the only city hall mentors on the list. It is a reasonable guess that they mentor the city's task and may sit on or advise its jury; the page does not link mentors to tasks. (names and functions VERIFIED; link to the task UNVERIFIED)
- What this suggests about the real workload: Biuro Rady Miasta handles councillors' interpellations and questions and council documents; a communication unit handles incoming questions from residents and media. Requests under the access-to-information act often arrive mixed with such letters. A feature that classifies an incoming letter ("is this an UDIP request at all, a press question, a complaint, an interpellation?") would speak directly to these two people. (own inference, UNVERIFIED)
- In 2025 the city's task ("Bydgoszcz - Ścieżki Pamięci 2.0") named as contacts the president's plenipotentiary for historical memory and the director of Bydgoskie Centrum Informacji, available at the city's stand and on the task's Discord channel. Expect the same pattern: **a city stand in the partner zone plus a Discord channel**. (VERIFIED for 2025)

### 2.3 How the city handles UDIP requests today (BIP UM Bydgoszczy, page "Udostępnianie informacji publicznej")

| Topic | What the BIP page says (VERIFIED) |
|---|---|
| Legal basis cited | ustawa z 6 września 2001 r. o dostępie do informacji publicznej, cited there as "t.j. Dz. U. 2022, poz. 902" |
| Deadline | "bez zbędnej zwłoki", not later than 14 days from filing; if impossible, the office notifies within that time about the reasons and a new date, not longer than 2 months from filing |
| Form | in the way and form requested, unless technical means make it impossible; then written notice with an alternative; if the applicant does not respond within 14 days the proceeding is discontinued |
| Letter-type answers | the office may answer by letter that the information "nie dotyczy spraw publicznych", that the office "nie dysponuje żądaną informacją", or that other provisions set a different access procedure |
| Channels | post to ul. Jezuicka 1; in person at the sekretariat; fax; e-Doręczenia address; e-mail to the general office address |
| Fees | free, unless extra costs arise from the requested way or form; then notice of the fee within 14 days |
| Refusal | refusal and discontinuation are issued as a **decyzja Prezydenta Miasta**; appeal to Samorządowe Kolegium Odwoławcze w Bydgoszczy; inaction can be challenged before Wojewódzki Sąd Administracyjny w Bydgoszczy |
| Personal data | controller: Gmina Miasto Bydgoszcz; a data protection officer is named; processors under entrustment agreements include IT companies maintaining the office's systems |

Design consequences: the request can arrive by e-mail with no form and no signature; the assistant must (1) recognise an UDIP request in free text, (2) start the 14-day clock from the filing date, (3) propose one of the outcome types listed above, and (4) never issue a refusal by itself, because a refusal is an administrative decision signed for the President of the City. The page does not name a single unit that answers requests; requests enter through the general office and are routed to the unit holding the information. (routing VERIFIED only as "no unit named on the page")

---

## 3. HackNation 2025 (first edition, 6-7 December 2025, BCTW Bydgoszcz)

### 3.1 How tasks were specified

Each of the 16 tasks had a PDF card at `hacknation.pl/zadania/<NAME>.pdf` (now 404 on the live site, 15 of 16 recovered from the Internet Archive). Every card follows one ten-point template:

1. Wprowadzenie - organisation, situation, current state
2. Wyzwanie
3. Oczekiwany rezultat
4. Wymagania formalne (what the submission must contain)
5. Wymagania techniczne
6. Sposób testowania i/lub walidacji
7. Dostępne zasoby (data, where to get it)
8. Kryteria oceny (five criteria, weights sum to 100 %)
9. Dodatkowe uwagi / kontekst wdrożeniowy
10. Kontakt (stand, Discord channel, mentors)

The template text itself says: "W tej części należy przedstawić kryteria oceny – powinno ich być pięć, z przypisanymi wagami, których suma wynosi 100%". Expect the 2026 card to use the same or a similar template. Submissions in 2025 went through ChallengeRocket; 2026 uses HackTribe.

### 3.2 Criteria and deliverables in 2025 (all VERIFIED from the cards)

| Task (partner) | Criteria and weights | Must submit |
|---|---|---|
| **AI w służbie decyzji** (Ministerstwo Sportu i Turystyki) | Związek z wyzwaniem 30; Efektywność i szybkość działania 20; Bezpieczeństwo i ochrona danych 20; Kompletność projektu 10; Potencjał wdrożeniowy 20 | title, detailed description of assistant functions, PDF max 10 slides, video max 3 min at an open link, screenshots or clickable model, demo links; technical: repo, guardrails, architecture, model choice, integration plan, response time, QA methodology, security, deployment plan, compliance |
| **Bydgoszcz - Ścieżki Pamięci 2.0** (Urząd Miasta Bydgoszcz) | Związek z wyzwaniem 30; Pomysł 10; Oryginalność 10; Kompletność projektu 20; Potencjał wdrożeniowy 30 | presentation of the prototype with a **1-minute film**, link to an open repository; card stresses ease of use, stability, low cost, safety, readiness for deployment |
| **Dane bez twarzy** (NASK, PLLuM consortium) | Skuteczność anonimizacji (F1) 35; Wydajność, jakość kodu, łatwość wdrożenia 20; Moduł danych syntetycznych 20; Rozróżnianie kontekstu 15; Pomysłowość 10 | repo with full source runnable in the organisation's environment, README with install and run instructions, PDF max 5 slides; Python required |
| **Ścieżka prawa** (Ministerstwo Cyfryzacji + GRAI) | Związek 30; Pomysł 10; Oryginalność 10; Kompletność 20; Potencjał wdrożeniowy 30 | description, PDF max 10 slides, video max 3 min; open source preferred; gov.pl accessibility and security standards |
| **ZUS Accident Notification Tool** (ZUS) | Związek 10; Pomysł 10; Oryginalność 20; Potencjał wdrożeniowy 20; **Jakość odpowiedzi na próbę testową nowych zgłoszeń 40** | description, PDF showing the assistant working, a web link where the jury can upload test cases ("Nie rekomendowane są rozwiązania wymagające od jury zainstalowania jakichkolwiek programów") |
| Zgrany budżet (MC) and Prawda w sieci (COI) | Związek 25; Wdrożeniowy potencjał 25; Walidacja i bezpieczeństwo danych 20; UX i ergonomia pracy 15; Innowacyjność i prezentacja 15 | description, PDF max 10 slides, video max 3 min |
| Scenariusze jutra (MSZ) | Związek 30; Pomysł 10; Oryginalność 5; Kompletność 15; **Potencjał wdrożeniowy 40**; explainability stressed | description, video max 3 min, architecture, generated text |
| Kontrola zakładów wzajemnych (KAS) | Związek 20; Pomysł 30; Oryginalność 20; Kompletność 10; Potencjał wdrożeniowy 20 | description, PDF max 10 slides, video max 3 min, repo; only open-source components |
| Odnalezione zguby (MC) | Zgodność z dane.gov.pl 35; Kreatywność 25; UX & UI 20; Wzorcowy zakres danych 15; Prezentacja 5 | presentation min 5 slides with screenshots as evidence, working prototype, data schema file, source code; "max. 5 kroków" for the clerk |
| Zobacz to, czego nie widać (JSW IT Systems) | Zgodność z wyzwaniem 30; Kompletność i działanie prototypu 25; Zgodność danych 20; Potencjał wdrożeniowy i bezpieczeństwo 15; Innowacyjność 10 | description, PDF max 10 slides, **API with documentation**, repo with run instructions |

Patterns that matter for us:

- "Związek z wyzwaniem" is present in almost every card, usually **20-30 %**.
- "Potencjał wdrożeniowy" is present in almost every card, **10-40 %**, and it is what the final jury is told to pick: the gov.pl summary says the jury chose from the finalists "rozwiązanie o największym potencjale wdrożeniowym w administracji publicznej". (SECONDARY wording via page summary)
- Where the partner had test data, a large weight went to **measured quality on unseen cases** (ZUS 40 %, NASK 35 %, KAS anomalies 40 %). If the city brings sample UDIP requests, expect a live test on requests the team has never seen.
- Security and data protection appeared as an explicit 20 % criterion in the administration-assistant card.
- Partners repeatedly asked for solutions the jury can open **in a browser without installing anything**.

### 3.3 The closest 2025 task in detail: "AI w służbie decyzji"

Card title: "Asystent AI dla administracji — precyzja i tempo decyzji administracyjnych w służbie państwa." Expected functions (verbatim headings): "Wsparcie w analizie i rozstrzyganiu spraw" (automatic summary of case files, proposing possible decisions with justification), "Ułatwienia procesowe i usprawnienia workflow" (drafting documents and decisions, deadline management, status monitoring, integration with public registers), "Zapewnienie zgodności z przepisami i zasadami etyki", "Interaktywna komunikacja i wsparcie decyzyjne", "Bezpieczeństwo i prywatność" ("Zachowanie poufności danych stron postępowania", compliance with personal data regulations).

Other points worth copying into our plan:

- "rozwiązanie to winno być uniwersalne i przenaszalne do dowolnego urzędu administracji rządowej lub samorządowej".
- "Uczestnicy mogą korzystać z płatnych modeli lub narzędzi, jednak preferowane będą rozwiązania oparte na technologiach otwartych (open-source) lub dostępnych bezpłatnie."
- Validation: concept versus goals, usability and speed, qualitative and quantitative tests of generated answers with experts and end users, simulated real scenarios for accuracy and completeness, "ewaluacja bezpieczeństwa danych i zgodności z wymaganiami RODO oraz przepisów administracyjnych".
- Resources: about 300 archived decisions, anonymised and scanned, **handed out at the partner's stand** ("będzie możliwość zgrania plików"). Bring a USB drive and an OCR path.

### 3.4 How winners were selected in 2025

- 16 tasks, more than 1 500 participants, more than 250 mentors, 437 submitted solutions (about 27 per task on average, own division). (VERIFIED gov.pl 08.12.2025 and 2026 home page)
- The jury assessed all submissions; for each task **three** best teams presented prototypes; one winner per task was picked for the greatest deployment potential. Each winner got 25 000 PLN and "możliwość dalszej współpracy z instytucją". In 2026 the final has **five** teams per task. (VERIFIED)
- ChallengeRocket shows a voting window of 13:00-14:20 on the second day. (VERIFIED)
- June 2026 ministry communiqué: "Zwycięskie zespoły otrzymały nagrody finansowe, a instytucje partnerskie wprowadzają rozwiązania w życie"; the PSP and ZUS tasks were shown as model challenges. No public evidence of a specific production deployment was found. (SECONDARY)

Winners per task (gov.pl list; team names only, personal names and e-mail addresses that appear on that list as "team names" are omitted here): Cyfrowy nieśmiertelnik - WiWav; Gaming - All ink; Odnalezione zguby - OneMoreFix; Zobacz to, czego nie widać - CombAIns; Wyszukiwarka anomalii - MEWA; Kontrola zakładów wzajemnych - Extempore; **AI w służbie decyzji - Programiści PWR**; ZUS Accident Notification Tool - kanapowcy; Chmura pod kontrolą - HackStorm; Ścieżka prawa - Code Casimir; Prawda w sieci - no signal; Zgrany budżet - kurki; **Dane bez twarzy - Habanero Code**; three tasks (Scenariusze jutra, Bydgoszcz - Ścieżki Pamięci 2.0, Indeks Branż) were won by entries listed under an individual's name or e-mail.

### 3.5 Repositories from 2025 (GitHub search, 183 repositories created in December 2025 that mention "hacknation")

No official list of winning repositories exists. Mapping a repository to a winning team is certain only where the README says so. Depth of analysis: README structure and first paragraphs were read for five repositories; code was not reviewed.

| Repository | Task | Status in the contest | What the README shows |
|---|---|---|---|
| `kubamilcarz/hacknation2025` (ZANT) | ZUS Accident Notification Tool | unknown (UNVERIFIED) | The most complete README seen: Key Outcomes, Solution Overview, System Architecture, Prerequisites, Quick Start (Django backend, Next.js frontend), **Using the Platform: citizen wizard + caseworker dashboard**, Sample data and demos, REST API Surface, AI/OCR and Document Automation, Project Structure, Quality Gates, Deployment Notes, Roadmap. The two-sided design (citizen wizard feeding a clerk dashboard with recommendations and ready-to-send documents) is the same shape as our product vision. |
| `qamarq/wypadkownik` | ZUS Accident Notification Tool | entry of team SolvroGen (UNVERIFIED placement) | Minimal README that works for a juror in one minute: live website link, three screenshots, embedded video, authors, links. |
| `00200200/anonimownik` | Dane bez twarzy | entry of team SolvroGen, not the winner | HerBERT NER model plus RegEx, synthetic replacement using spaCy morphology; README is honest about limits (states that quality metrics are not published and that the pipeline may miss data). Still maintained in October 2026. |
| `Mlynek4/Data_without_Face` | Dane bez twarzy | unknown | Two approaches (fine-tuned HerBERT-Large NER and a rule system), demo video and a before/after comparison image at the top; openly says the model was not wired to the frontend in time. |
| `Solvro/web-hacknation-decyzai` | AI w służbie decyzji | Solvro is a Wrocław University of Science and Technology group and the winner is "Programiści PWR"; whether this is the winning repo is UNVERIFIED | Six-line README: pnpm, docker compose, DB migration, an API key in `.env.local`. Shows that a thin README did not prevent a strong result when demo and pitch carried the project. |
| `Solvro/backend-hacknation-prawo-dla-ciebie` | Ścieżka prawa | unknown | Legislation aggregator and analyser backend. |
| Self-declared finalists: `MaciejMomot/Anomaly-Vision---HackNation-finalist-solution-` (top 3, Wyszukiwarka anomalii), `Maikonroonie/Hacknation` (top 3, Indeks Branż) | | finalist per repo description (SECONDARY) | not opened |
| Other anonymisation entries: `LachPawel/Lethe`, `piotrmaciejbednarski/pii-anonymizer`, `NikodemNowak/hacknation-2025-NASK` | Dane bez twarzy | unknown | not opened |
| `KGPSP/hack_2025_psp` | Cyfrowy nieśmiertelnik | the partner's own task materials | shows that partners may publish task data on GitHub |

Licence warning: the six repositories checked through the GitHub API report **no licence**. Without a licence the code may not be copied. Reuse ideas and architecture only.

### 3.6 What convinced juries (evidence, not opinion)

- A finalist team's own account (Solvro blog, KAS task): they reached the final with the second-highest stage 1 score; in the final the jury asked for "a live demo showing a specific use case" instead of the prepared slide deck; the winning argument of their product was one concrete pain point (monitoring outside the clerk's working hours) and full automation where competitors were semi-automatic; their dashboard followed a "3-30-300" rule (key information in 3 seconds, analysis in 30, full details in 300). They did not win; the two top teams were close. (SECONDARY, first-hand report)
- The official summary says the final choice was about **deployment potential in public administration**.
- 2026 guide repeats twice that jurors have only a few minutes per project in stage 1.

### 3.7 What can be reused for our project

| From 2025 | Reuse for the UDIP assistant |
|---|---|
| "Dane bez twarzy" class list and approach (NER model for Polish + regular expressions for PESEL, phone, e-mail, account numbers; inflection-aware replacement) | The anonymisation step before an answer or attached document leaves the office, and before any text is sent to a model. Build our own; treat the 2025 repos as reading material. |
| "AI w służbie decyzji" required sections | Ready-made headings for our documentation: guardrails, model choice, integration plan, response time, QA methodology, security, deployment plan, compliance. |
| ZANT architecture (citizen wizard + caseworker dashboard + REST API + OCR) | Confirms that a two-sided system can be presented coherently; for our task show the clerk side first. |
| ZUS and NASK judging on unseen test cases | Prepare a public test endpoint or upload screen where a juror can paste a new request and get the analysis in under a minute. |
| Bydgoszcz 2025 card language | The city writes for non-technical readers and values "łatwe w użyciu", "stabilny", "bezpieczny", cheap and available technology, "gotowy do wdrożenia". Mirror these words. |

---

## 4. Twenty-five questions the jury is likely to ask, with strong short answers

The answers describe the position this project should be able to defend. Legal details must match the legal research reports in this repository; anything marked (check) has to be confirmed there before it is said on stage.

**Security and RODO (GDPR)**

1. *Where does the citizen's data go when the assistant analyses a request?* Nowhere outside the office's control. Personal data is detected and masked locally before any text reaches a language model, and the default deployment runs the model on the office's own server or in a Polish/EU government cloud. The demo shows the masked text that the model actually receives.
2. *Who is the data controller and what is the legal basis?* The controller stays the same as today, Gmina Miasto Bydgoszcz, and the basis is the legal obligation to handle the request under the access-to-information act. The tool is a processing instrument inside the office; an external supplier would act only under an entrustment agreement, exactly as the city's own information clause already describes for IT companies.
3. *Could the model leak what it saw in one case into another?* No training or fine-tuning happens on case data, and each request is processed in a separate context. Earlier answers are reused only through an explicit search over the office's own archive, with access rights and a visible link to the source document.
4. *How do you stop a refusal-worthy secret or personal data from being disclosed in an answer?* The assistant marks every fragment that may fall under privacy, business secret or other statutory limits and blocks sending until a clerk resolves each mark. It can only propose anonymisation; the decision stays with a human and is recorded.
5. *What about prompt injection hidden in a request or an attachment?* Request text is treated as data, never as instructions; the assistant has no tools that send, delete or publish anything by itself. Every outgoing action needs a clerk's click, and the audit log keeps the input, the draft and the final text.
6. *Who can see what?* Role-based access through the API only, no direct database access, every read and write logged with user, time and case number. The log is exportable for the data protection officer and for an audit.

**Legal correctness and liability**

7. *What if the assistant invents a legal basis or a fact?* Drafts are built only from retrieved sources: the statute text, the office's own BIP and its archive of earlier answers. Each sentence in the draft carries a reference the clerk can open, and a sentence without a source is highlighted as unverified. The assistant never sends anything by itself.
8. *Who is responsible for the answer?* The clerk who approves it and the authority that signs it, exactly as today. The tool prepares, a human decides, and a refusal remains an administrative decision issued for the President of the City (check: article numbers in the legal report).
9. *Does it handle deadlines?* Yes. It starts the 14-day clock at the filing date, warns before it expires, and drafts the notice about a new date within the statutory two-month limit when more time is needed. These are the rules the city publishes on its own BIP page.
10. *Can it tell whether a letter is an access-to-information request at all?* That is the first step: it classifies the incoming text as public information, information already in BIP, a matter governed by another procedure, processed information that needs a public-interest justification, or not public information, and shows the reasons (check: categories in the legal report). The clerk confirms or changes the class with one click.
11. *Is this a high-risk AI system under the EU AI Act?* The tool supports a clerk in preparing letters and does not decide about a person's rights by itself; a human reviews every output. We document the intended purpose, human oversight and logging so the office can make its own classification (check: AI Act analysis in the legal report).

**Deployment in a real office**

12. *How does it fit into EZD (electronic document management)?* It works next to EZD, not instead of it: a request registered in EZD is passed to the assistant through an API or, as a first step, by export and import of the document. The approved draft returns to EZD for signature and dispatch, so the official record stays in one place (check: available EZD RP interfaces in the integration report).
13. *What exactly is real in this demo and what is mocked?* Say it plainly on one slide. Real: classification, deadline calculation, retrieval over public BIP content, draft generation, masking, audit log. Mocked: the EZD connection, login with the office's identity system, and the archive of past answers, which is a synthetic set written for the demo.
14. *How long would a pilot take?* A pilot on one unit with exported, anonymised historical requests can start in weeks, because it needs no change to existing systems. Production use needs a security review, a data protection impact assessment and an integration with EZD; the plan is in the repository.
15. *What does the clerk have to learn?* One screen: the request on the left, the analysis and the draft on the right, three buttons (accept, edit, reject). No prompt writing.
16. *What happens when the system is down or wrong?* The clerk works as before; nothing in the legal process depends on the tool. Every suggestion can be rejected, and rejected suggestions are collected as feedback.

**Cost, model choice, digital sovereignty, lock-in**

17. *Which model and why?* A Polish-language open model that can run on the office's own hardware is the default (PLLuM was presented by its consortium at HackNation 2025 as sovereign technology meant to support administration); the model sits behind one interface and can be swapped. A commercial model can be used only on masked text and only if the office decides so.
18. *What does it cost to run?* The answer must be a number per month for a city office: one mid-range server or a modest cloud instance, no per-seat licence, open-source components. Show the calculation on a slide (check: cost table in the architecture report).
19. *Are we locked to you or to a vendor?* No. Open code, open standards, data stays in the office's database in documented formats, the model is replaceable, and the API is documented so another supplier can maintain it.
20. *Who maintains it after the hackathon?* The code is documented and built from common components, so the city's IT unit or any contractor can take it over. The team is ready to continue with the city in the follow-up cooperation that HackNation offers to winners.

**Quality, accessibility, scale**

21. *How do you know the answers are good?* A test set of requests with expected classification and required elements of the answer is run automatically; the demo shows the score and the failures. The jury can paste a new request and watch the result.
22. *How much time does it save?* Show measured minutes per request with and without the assistant on the test set, split into reading, searching for an earlier answer, and drafting. State clearly that the numbers come from a demo set, not from the office.
23. *Is it accessible?* The clerk interface follows WCAG 2.1 AA: keyboard operation, contrast, scalable text, labelled controls; generated answers are plain text documents readable by screen readers (check: accessibility report).
24. *Can another office use it?* Yes. Office-specific parts are configuration: the BIP address, templates, signature block, organisational units. The legal logic is the same statute everywhere in Poland.
25. *Why do you also talk about forms and the service counter?* Because the same building blocks (one verified profile, document understanding, drafting from approved templates, a checking agent, an API with an audit log) serve the next processes in the same office. Today we deliver the UDIP assistant; the rest is the roadmap, and it is why the investment pays off beyond one procedure.

---

## 5. Strategy note: how risky is the wider "form prefill at the counter" product?

**Evidence**

- The published challenge names one process (UDIP requests), one user (the clerk) and two functions (analysis, drafting answers).
- Stage 1 is a weighted score per criterion by jurors who have a few minutes per project. In 2025 the fit criterion weighed 30 % in both the Bydgoszcz card and the administration-assistant card, and completeness another 10-20 %.
- The guide warns teams directly: if the concept is "zbyt szeroka, nierealistyczna lub słabo dopasowana do wyzwania", narrow it early; and "Technologia powinna wspierać rozwiązanie - a nie definiować problem".
- Organisers discourage one project for two tasks and say one universal project cannot meet two sets of criteria.
- The final jury is the city's own, picking the solution it could deploy for the stated problem.
- Two other 2026 tasks sit closer to the forms vision: **"Cyfryzacja formularzy" (Centralny Ośrodek Informatyki, 25 000 PLN)**, about AI that shortens the path from a need to a convenient online service, and **"Przewodnik przyszłego rodzica" (ZUS, 30 000 PLN)**, about guiding people through benefits and formalities around a life event. Their full cards are also unknown until 11:00.

**Assessment**

| Option | Risk | Why |
|---|---|---|
| Present the counter/forms platform as the product and UDIP as one module | **High** | Loses points on fit and completeness in stage 1; jurors may not reach the UDIP part in the minutes they have; handling ID documents and family data in a demo invites hard privacy questions that have nothing to do with the task |
| Present a complete UDIP assistant; show the platform as a roadmap slide and as architecture ("same engine") | **Low** | Full marks available on fit; the roadmap strengthens "potencjał wdrożeniowy" and scalability |
| Enter two tasks with two separate projects (UDIP for Bydgoszcz, forms for COI) | Medium to high | Allowed (max two tasks, different Team Leader, both drafts by Sat 20:00), but splits a small team across two juries and two sets of deliverables; consider only if the COI card at 11:00 matches existing work closely |

**Recommended framing**

1. Product name and first sentence are about UDIP: an assistant that reads an access-to-information request, tells the clerk what it is and what the deadline is, finds whether it was already answered, and drafts the reply with sources.
2. Demo order: incoming e-mail request, classification and deadline, earlier similar answer found, draft with masked personal data, clerk edits and approves, audit entry. Under two minutes.
3. Use the city's own words from the teaser on slide one: "inteligentny i bezpieczny asystent", "analiza wniosków", "przygotowywanie odpowiedzi", "skrócenie czasu obsługi spraw", "odciążenie od powtarzalnych zadań".
4. One slide near the end: the same components serve other processes at the counter (profile entered once, forms pre-filled from approved templates, checking agent). Label it "next modules", show no personal-document scanning in the live demo.
5. In the repository keep the wider vision in a clearly separated roadmap document, so a juror opening the README sees the UDIP assistant first.
6. At 11:00 re-check this recommendation against the real criteria. If the card explicitly rewards breadth ("codzienna praca administracji" beyond UDIP), add one small second use case built on the same engine, for example recognising that an incoming letter is not an UDIP request and routing it.

---

## Verdicts on the previous research

| Claim | Verdict | Evidence and correction |
|---|---|---|
| **C1**: HackNation 2026 takes place on 21-22 November 2026 at BCTW, ul. Gdańska 187, Bydgoszcz; 24 hours; 15 tasks from 15 partners | **PARTLY** | Dates, venue, address and 24 hours confirmed (FAQ, guide PDF, home page). Correction: the home page says **"15 wyzwań od 14 partnerów"** (two Ministerstwo Cyfryzacji units each submitted a task). Source: https://hacknation.pl/ and https://hacknation.pl/faq |
| **C2**: Full task requirements and criteria are not published before the start; they appear on hacknation.pl/zadania on Saturday 21 November at 11:00 when coding starts | **CONFIRMED** | Agenda: "11:00 Publikacja pełnych treści zadań - Start Kodowania"; guide: "Zadania wraz z ich wytycznymi zostaną opublikowane w sobotę 21.11. o godz: 11:00"; Regulamin 5.5: criteria published with the full description "najpóźniej w dniu rozpoczęcia Wydarzenia o godz. 11:00". Nuance: short teasers and prize amounts are already public; criteria may be in the task's own rules or in its detailed description; IP rules also arrive then. Sources: https://hacknation.pl/przewodnik-uczestnika and the Regulamin PDF |
| **C3**: An "AES-GCM plus checksum envelope" pattern appears directly in HackNation technical materials | **WRONG** | The only occurrence is the **decorative animated code background of the hacknation.pl home page** (`cipher = AESGCM(key)`, "Payload integrity checksum mismatch"). It is page decoration. The Regulamin, the participant guide, the HackTribe tutorial, the FAQ and the task page contain no encryption guidance. Do not cite it as an organiser requirement. Source: https://hacknation.pl/ (page source) |

Additional corrections found on the way:

- Finalists per task: **5 in 2026** (Regulamin 5.6), 3 in 2025.
- Pitch: **5 minutes + 5 minutes Q&A** (Regulamin 5.6 c).
- Submission platform in 2026 is **HackTribe**, not ChallengeRocket (used in 2025).
- Prize for the Bydgoszcz task is **15 000 PLN**, not 25 000 PLN as for every task in 2025.

---

## Open questions and what could not be verified

1. **The full 2026 task card** for "Inteligentny asystent urzędnika": requirements, deliverables, criteria and weights, data provided, IP clause, platform. Not published before 21.11 11:00. Looked at: hacknation.pl/zadania, home page, guide, FAQ, Regulamin, media page.
2. **Jury composition** for the task: not published (rule: by day two at the latest). No `/jury` page exists.
3. **Which mentors serve the Bydgoszcz task.** The mentor list does not map mentors to tasks; mentor schedules will be in the task's Discord channel.
4. **Whether the city will provide sample UDIP requests or an answer archive**, and in what form (in 2025 partners handed out files at their stands).
5. **Whether any LLM access, API keys or cloud credits are provided.** Nothing in published materials; could be announced on Discord or at partner stands.
6. **Explicit rule on AI coding assistants and on a pre-published public brief repository.** Not regulated in writing; ask on `#zapytaj-organizatora` and keep a screenshot of the answer.
7. **Which unit of Urząd Miasta Bydgoszczy coordinates UDIP answers** and the yearly number of requests. The BIP procedure page names no unit; the Regulamin Organizacyjny of the office and BIP statistics were not searched.
8. **City and organiser social media and Discord content** about the task: not read (login walls; Discord not joined in this research).
9. **Winning repositories of 2025**: no official list; the link between `Solvro/web-hacknation-decyzai` and the winning team "Programiści PWR" is not confirmed; the repository of "Habanero Code" (winner of Dane bez twarzy) was not found on GitHub by search for "hacknation" plus task keywords.
10. **The 2025 Regulamin** (archived copies exist) was not opened; 2025 rules here come from the task cards, the archived site, ChallengeRocket and gov.pl.
11. **Real deployments of 2025 winners**: the ministry says institutions are implementing them; no independent confirmation found.
12. Article numbers of the access-to-information act and the AI Act classification used in section 4 are stated from general knowledge and must be confirmed by the legal reports of this repository.

---

## Sources

HackNation 2026 (opened 2026-11-20):

- https://hacknation.pl/ (home: description, agenda, tasks, mentors, partners, decorative code background)
- https://hacknation.pl/zadania (15 task teasers and prizes)
- https://hacknation.pl/przewodnik-uczestnika (web guide)
- https://hacknation.pl/faq
- https://hacknation.pl/mentorzy
- https://hacknation.pl/media
- https://hacknation.pl/api/public/dokumenty/fb319d79-dc61-4bbe-bb33-1c085c25b567/regulamin-hacknation_19.11.pdf (Regulamin)
- https://hacknation.pl/api/public/przewodnik/54d496f6-4f5c-49a6-938b-d6777e41e0c2?asset=0db52dc1-292e-425c-8c4b-f87816b6ec3f (Przewodnik Uczestnika PDF)
- https://hacknation.pl/api/public/przewodnik/1f73a661-0852-4e9e-b3ed-58c93bce6456?asset=aa346c52-8bd9-44ac-9499-364e44c4b6b4 (Tutorial HackTribe PDF)
- https://www.gov.pl/web/cyfryzacja/hacknation-2026-zaczyna-sie-od-dobrego-wyzwania-za-nami-warsztaty-dla-instytucji-publicznych (16.06.2026)
- https://www.eska.pl/news/programisci-ruszaja-na-pomoc-administracji-przed-nami-hacknation-2026-aa-Mhrm-19fu-oeAZ.html (18.11.2026, secondary)

Miasto Bydgoszcz:

- https://bip.um.bydgoszcz.pl/artykuly/1052/udostepnianie-informacji-publicznej (procedure page; reached via https://bip.um.bydgoszcz.pl/contents/content/7/2)
- https://bip.um.bydgoszcz.pl/
- https://www.bydgoszcz.pl/szukaj/?q=hacknation (site search, no usable result)

HackNation 2025:

- https://www.gov.pl/web/cyfryzacja/tysiace-pomyslow-24-godziny-i-jeden-cel--usprawnic-panstwo-w-bydgoszczy-zakonczyl-sie-hacknation-2025 (08.12.2025, winners)
- http://web.archive.org/web/20251208110304/https://hacknation.pl/zadania_hacknation/ (task list with links to cards)
- http://web.archive.org/web/20251202174437/https://hacknation.pl/zadania/
- http://web.archive.org/web/20251208172542/https://hacknation.pl/przewodnik-uczestnika/
- Task cards, Internet Archive copies of `https://hacknation.pl/zadania/<NAME>.pdf`, for example:
  - http://web.archive.org/web/2025/https://hacknation.pl/zadania/AI_W_SLUZBIE_DECYZJI.pdf
  - http://web.archive.org/web/2025/https://hacknation.pl/zadania/DANE_BEZ_TWARZY.pdf
  - http://web.archive.org/web/2025/https://hacknation.pl/zadania/BYDGOSZCZ%E2%80%93SCIEZKI_PAMIECI_2_0.pdf
  - http://web.archive.org/web/2025/https://hacknation.pl/zadania/SCIEZKA_PRAWA.pdf
  - http://web.archive.org/web/2025/https://hacknation.pl/zadania/ZUS_ACCIDENT_NOTIFICATION_TOOL.pdf
  - http://web.archive.org/web/2025/https://hacknation.pl/zadania/ZGRANY_BUDZET.pdf
  - http://web.archive.org/web/2025/https://hacknation.pl/zadania/PRAWDA_W_SIECI.pdf
  - http://web.archive.org/web/2025/https://hacknation.pl/zadania/SCENARIUSZE_JUTRA.pdf
  - http://web.archive.org/web/2025/https://hacknation.pl/zadania/KONTROLA_ZAKLADOW_WZAJEMNYCH.pdf
  - http://web.archive.org/web/2025/https://hacknation.pl/zadania/ODNALEZIONE_ZGUBY.pdf
  - http://web.archive.org/web/2025/https://hacknation.pl/zadania/ZOBACZ_TO-CZEGO_NIE_WIDAC.pdf
  - (also read: CHMURA_POD_KONTROLA, GAMING_LOS_DECYDUJE, INDEKS_BRANZ, WYSZUKIWARKA_ANOMALII; CYFROWY_NIESMIERTELNIK has no text layer)
- https://challengerocket.com/hacknation (2025 submission platform page)
- https://solvro.pwr.edu.pl/en/blog/hacknation-2025/ (finalist's report, secondary)
- GitHub: https://github.com/kubamilcarz/hacknation2025 , https://github.com/qamarq/wypadkownik , https://github.com/00200200/anonimownik , https://github.com/Mlynek4/Data_without_Face , https://github.com/Solvro/web-hacknation-decyzai , https://github.com/Solvro/backend-hacknation-prawo-dla-ciebie , https://github.com/KGPSP/hack_2025_psp ; GitHub repository search `hacknation created:2025-12-01..2025-12-31`
