# R11 - COI "Cyfryzacja formularzy": what the task, the platform and the jury imply for our product

Research date: 2026-11-21 (morning of the event). Labels: **VERIFIED** = primary page opened and read; **SECONDARY** = reliable secondary source or a search-result summary of a primary page that I did not open in full; **UNVERIFIED** = inference or not found. Tool budget was limited (38 calls), so several items are SECONDARY or UNVERIFIED and are listed in the last section.

## TL;DR for builders and for the pitch

- **The task card is still only the teaser.** At the time of research hacknation.pl/zadania shows for "CYFRYZACJA FORMULARZY" (initiator CENTRALNY OŚRODEK INFORMATYKI) only the three sentences quoted in the brief and "Nagroda główna: 25 000,00"; no criteria, no deliverables. Re-read it at 11:00 and re-map. (VERIFIED, https://hacknation.pl/zadania)
- **The ministry is building exactly the thing we sit next to: "Generator Formularzy" in the platform ePUC.** The Plan działalności Ministra Cyfryzacji na 2026 lists "Udostępnienie funkcjonalności wytworzenia i publikacji formularzy elektronicznych (w ramach Generatora Formularzy systemu Platformy Usług Cyfrowych (ePUC)) dla podmiotów realizujących zadania publiczne (m.in. JST)", indicator "Liczba unikalnych podmiotów publicznych typu JST, które przy użyciu Generatora ... utworzyły co najmniej jeden formularz elektroniczny", target **30-50**, tied to Strategia Cyfryzacji Cel 2.1.2. Pitch the product as the AI front door that feeds such a generator (paper or PDF in, approved field description out), not as a competing platform. (VERIFIED, plan PDF)
- **COI has 14 mentors on the list and they are the likeliest source of jurors:** a Product Owner, an UX/UI expert, a UX researcher, the director of the "Departament Badań i Projektowania Doświadczeń", a "CAIO", a senior data scientist, an ML engineer, a head of the "Zespół Usług Cyfrowych", the director of "Departament Komunikacji Elektronicznej" and automation/Java programmers. Expect questions on UX, accessibility, data science rigour and integration, not on slogans. (VERIFIED list; link to the task and to the jury UNVERIFIED)
- **COI's 2025 task was "Prawda w sieci" (disinformation), winner "no signal"; criteria (from R01): Związek 25, Wdrożeniowy potencjał 25, Walidacja i bezpieczeństwo danych 20, UX i ergonomia pracy 15, Innowacyjność i prezentacja 15.** The jury's declared selection rule in 2025 was "największy potencjał do wdrożenia w administracji publicznej". Deployability plus validation/security weigh 45 of 100 in the proxy. (VERIFIED winner and rule; criteria VERIFIED in R01)
- **Hard facts for the problem slide that a COI expert already knows and will not dispute:** 179 of 344 mapped public services for citizens are digitised (Mapa Życia, COI + MC, 13.05.2026); the e-service share is not the problem, the long tail of local forms is. Do not claim "most services are paper". (VERIFIED)
- **The mObywatel assistant (PLLuM, since 31.12.2025) finds applications and forms and explains formalities; it does not fill forms, has no register access and tells users not to enter personal data.** Our product complements it on the other side: it produces the form and the filled application. Do not call it "the assistant that fills forms". (VERIFIED, gov.pl 30.12.2025; one secondary headline claims it helps "przy wypełnianiu wniosków", which the primary page does not say)
- **mObywatel already has "Przekaż instytucji": the institution shows a QR code, the user scans it, sees which institution gets which data and confirms.** Joining requires an institution to write to mobywatel@mc.gov.pl; the first partner was mojePZU. Our storyboard's QR story must say the direction and that integration is not done. (SECONDARY, search summaries of gov.pl guides; the gov.pl page itself was not opened)
- **Foreign evidence supports "AI proposes, human approves":** Tim Paul (GDS) built an LLM PDF-to-web-form prototype; JSON valid 100 % of the time only with a schema, content never 100 % accurate, conditional routing not handled, and he recommends human correction afterwards. GDS estimated 70 years for 11 teams to convert existing PDF forms by hand, and document forms are on average 8 minutes slower to process. No measured accuracy of an AI converter in government was found anywhere. (VERIFIED)
- **Ukraine 2022 facts safe for one slide:** applications for PESEL opened 16.03.2022; over 250 000 numbers in the first week; ZUS's dedicated online form for the child benefit drew almost 217 000 applications for about 330 000 children within a month. Queues and multi-month waits are documented (Ombudsman, 6.04.2022). Nothing sourced about volunteers or phone data entry: that stays the owner's own testimony. (VERIFIED)
- **Biggest storyboard risks:** "710 druków" (it is 710 files, not forms); "rejestr opisów formularzy" sounds like a duplicate of the existing Centralne Repozytorium Wzorów Dokumentów Elektronicznych and of Katalogi Administracji Publicznej; "Bez wspólnej bazy" clashes with the state's central platforms; the QR claim; the accessibility answer without naming WCAG 2.1 AA. Details in section 8.

---

## 1. COI and the task

### 1.1 What the task card says

| Field | Content | Status |
|---|---|---|
| Initiator | CENTRALNY OŚRODEK INFORMATYKI | VERIFIED, https://hacknation.pl/zadania |
| Campaign | CYFRYZACJA FORMULARZY | VERIFIED |
| Text | "Jak sztuczna inteligencja może wspierać rozwój nowoczesnych usług publicznych? Zadaniem uczestników będzie znalezienie rozwiązania, które pomoże usprawnić proces cyfryzacji i sprawić, że droga od potrzeby do wygodnej usługi online będzie prostsza i szybsza." | VERIFIED |
| Prize | 25 000,00 (currency not printed on the page) | VERIFIED |
| Criteria, deliverables | none published as of this research | VERIFIED absence |

Reading (own analysis): the object is "proces cyfryzacji", the ends are "od potrzeby do wygodnej usługi online", the qualities are "prostsza i szybsza". The word is "usług publicznych", wider than "formularz". A jury will therefore accept a solution that shortens the path from need to service; the form is the carrier. Measure "prostsza" (fewer steps, fewer typed fields) and "szybsza" (time per form digitised, time per application filled).

### 1.2 What COI is and builds

- COI and the Ministerstwo Cyfryzacji run Mapa Życia: 42 life events in 10 areas, "179 z 344 zmapowanych usług publicznych dla obywateli" digitised, priorities by stress level, number of people affected and scale of formalities. Planned: step-by-step event pages, proactive services, "jednolity standard lokalnych usług cyfrowych" (kindergarten and school enrolment, property matters, local benefits), simpler language, offline office access kept. (VERIFIED, https://www.gov.pl/web/cyfryzacja/panstwo-ktore-rozumie-obywatela-mapa-zycia-porzadkuje-cyfrowe-uslugi, 13.05.2026)
- Scale figures in the same article: mObywatel "blisko 12 mln użytkowników", Profil Zaufany "ponad 14,5 mln osób", e-Doręczenia "ponad 78 mln przesyłek", ePłatności nearly 1.2 million transactions. (VERIFIED, same page)
- COI runs the technical help desk for ePUAP and the INT environment acceptance for e-Doręczenia registration. (SECONDARY, https://warszawa19115.pl/en/-/epuap-elektroniczna-platforma via search summary)
- Plan działalności Ministra Cyfryzacji 2026 targets: 10 new services or documents in the mObywatel app; Generator Formularzy ePUC for 30-50 JST; BLIK in the passport application; campaigns "Online jest łatwiej" and for e-Doręczenia. (VERIFIED, https://www.gov.pl/attachment/3b014cc3-3674-4390-a832-9e8f0dadce07; the PDF names the Ministry as owner; the plan says nothing about COI as implementer, so who builds the Generator is UNVERIFIED)

### 1.3 Mentors from COI (hacknation.pl/mentorzy)

| Name | Role as printed | Why it matters |
|---|---|---|
| Piotr Lasko | Ekspert Projektowania UX/UI w COI | design system, form UX |
| Mikołaj Mroszczak | CAIO w COI | AI policy, model choice |
| Marek Fabiński | Starszy Programista Automatyzacji Procesów Biznesowych | process automation |
| Tomasz Łuczak | Starszy Programista Java | integration with Java back ends |
| Magda Kołba-Górna | Dyrektorka Dep. Badań i Projektowania Doświadczeń | user research |
| Eliza Fijołek | Dyrektor Departamentu Komunikacji Elektronicznej | e-Doręczenia, ePUAP |
| Krzysztof Wysocki | Product Owner w COI | product fit |
| Dawid Czaja | Starszy programista automatyzacji | automation |
| Jędrzej Szpygiel | Senior Data Scientist | evaluation methodology |
| Bartosz Krajewski | Inżynier uczenia maszynowego | model quality |
| Stella Chwedoruk | Badaczka UX | usability testing |
| Emilian Duda | Kierownik Zespołu Usług Cyfrowych | e-service catalogue |
| Damian Abramczyk | Analityk IT | analysis |
| Agnieszka Głodek-Stefanowska | Główna Analityczka IT | analysis |

All VERIFIED (https://hacknation.pl/mentorzy); the page gives titles only, no task assignment. Ministerstwo Cyfryzacji has 14 further mentors (mostly "Radca", two "Naczelnik wydziału"); none is labelled mObywatel. Ask for the COI mentors at the task's table early: the Product Owner and the Zespół Usług Cyfrowych head can tell what "usługa" must contain.

### 1.4 COI in HackNation 2025

- Task "Prawda w sieci", partner Centralny Ośrodek Informatyki, winner team "no signal". All 16 tasks of 2025 had a 25 000 PLN prize for the winner. (VERIFIED, https://www.gov.pl/web/cyfryzacja/tysiace-pomyslow-24-godziny-i-jeden-cel--usprawnic-panstwo-w-bydgoszczy-zakonczyl-sie-hacknation-2025)
- Selection: jurors picked three best per task, then one per task "o największym potencjale do wdrożenia w administracji publicznej". Winners keep working with the institutions. (VERIFIED, same page)
- Criteria of COI's 2025 card and of "Zgrany budżet": Związek 25; Wdrożeniowy potencjał 25; Walidacja i bezpieczeństwo danych 20; UX i ergonomia pracy 15; Innowacyjność i prezentacja 15; deliverables description, PDF max 10 slides, video max 3 min. (VERIFIED in R01 section 3.2 from the cards; not re-opened here)
- What it implies: a COI jury scores UX and "ergonomia pracy" (the clerk's work) as a separate item and "Walidacja" as a separate item. Both are where our two-sided product is strongest, provided validation is shown with a measured result, not an adjective. The 2026 weights are UNVERIFIED until 11:00.
- The 2026 preparation workshops told partners a good challenge must be "konkretne, zrozumiałe i możliwe do opracowania w czasie trwania hackathonu" and that the prototype can be "dalej analizowany, testowany lub rozwijany". (VERIFIED, https://www.gov.pl/web/cyfryzacja/hacknation-2026-zaczyna-sie-od-dobrego-wyzwania-za-nami-warsztaty-dla-instytucji-publicznych, 16.06.2026)
- No COI or ministry social-media post about this task was found; social networks were not read. (UNVERIFIED)

---

## 2. How a paper form becomes an online public service in Poland today

### 2.1 The route, step by step (national model)

The official "model realizacji e-usług" for a form-based service on gov.pl (VERIFIED, https://www.gov.pl/web/ia/model-realizacji-e-uslug-zlozenie-dokumentu-przez-formularz):

1. The user is redirected to central authentication if not logged in.
2. The system fetches the document template definition from **Katalogi Administracji Publicznej** ("Obsługa katalogu wzorów dokumentów"). Template markers can control field defaults, allowed values, validation and form flow.
3. An interactive web form is generated from the template; fields are pre-filled from other systems and from the authentication token ("użytkownik wpisuje tylko dane, których administracja nie posiada").
4. Each entry is validated; the user accepts the form.
5. The user is sent to a signing system ("Obsługa podpisów elektronicznych osób fizycznych").
6. The signed document goes to the address in the template: e-mail, e-delivery box, EZD mailbox or API.
7. Publishing interactive forms requires meeting a "standard w zakresie aspektów technicznych, UI i UX".

Who does what (own synthesis from the model page and the sources below): the office (or its ministry) owns the matter and the legal basis; whoever holds the template catalogue registers the wzór; a vendor or IT unit builds the form; the central platform provides identity, signature and delivery. Page says nothing on payment or on UPP/UPO.

Consequence for us: our "one description" should be able to export (a) a template with markers for the form generator (field, type, validation, default from profile), (b) the print layout. That is the interface where AI helps, because step 2 starts with a human writing the template. (Own analysis.)

### 2.2 Central pieces and their status

- **Centralne Repozytorium Wzorów Dokumentów Elektronicznych (CRWDE)** runs within ePUAP under the ustawa o informatyzacji; public bodies pass electronic document templates to it and publish them in the BIP; a published template has a unique identifier and the repository does not accept copies. A later regulation limited publishing to ministers heading government departments, which stopped competing forms for one procedure (older article, check whether still in force). (SECONDARY, https://arslege.pl/centralne-repozytorium-wzorow-dokumentow-elektronicznych/k834/a59902/ and https://lexlege.pl/ustawa-o-informatyzacji-dzialalnosci-podmiotow-realizujacych-zadania-publiczne/art-19b/ via search summary). **Number of templates and typical publication time: not found.** (UNVERIFIED)
- **Generator Formularzy ePUC**: planned for external entities in 2026, 30-50 JST (VERIFIED, plan PDF). Strategia Cyfryzacji Cel 2.1.2 quoted there: "Wyposażenie podmiotów świadczących e-usługi publiczne w generator formularzy - intuicyjne narzędzie do wsparcia samodzielnego wdrażania e-usług publicznych w jednym wspólnym standardzie, dzięki czemu będą one użyteczniejsze i bardziej przyjazne dla użytkownika". (VERIFIED, plan PDF) Current status of the Generator is UNVERIFIED.
- **ePUAP**: from 1.01.2026 e-Doręczenia replace ePUAP mailbox correspondence; ePUAP correspondence is effective only where special law says so. (SECONDARY, https://www.gov.pl/web/cyfryzacja/ankieta-epuap via search summary)
- **Local platforms**: commercial form builders for JST exist (e.g. Symfonia Public, formerly Nefeni, forms signed with login.gov.pl; regional platforms such as Mazowieckie e-Usługi). (SECONDARY, https://symfonia.pl/public/programy/eformularze/)

### 2.3 Documented pain points and numbers

| Fact | Source | Status |
|---|---|---|
| 179 of 344 mapped citizen services digitised (May 2026) | Mapa Życia page above | VERIFIED |
| Central e-services on ePUAP: 72 (1.01.2016) to 148 (30.06.2020), +105.6 % | NIK audit P/20/004, https://www.nik.gov.pl/kontrole/wyniki-kontroli-nik/pobierz,kap~p_20_004_202006150914271592205267~id0~01,typ,kj.pdf | SECONDARY (search summary) |
| NIK: some documents had to be delivered on paper, so some matters could not be handled "bez wizyty w urzędzie" | same | SECONDARY |
| NIK 2015: e-services used little, some not at all; one cause: no effective information to citizens | NIK P/15/003, https://www.nik.gov.pl/kontrole/wyniki-kontroli-nik/pobierz,kap~p_15_003_201506250902111435222931~id1~01,typ,kj.pdf | SECONDARY |
| NIK recommendation: publish first the forms of the matters most often handled in offices | NIK 2020, same URL as row 2 | SECONDARY |
| Ministry did not study demand for e-services other than ad hoc in 2017-mid-2020 | same | SECONDARY |
| Forms submitted online by individuals in Poland: 25 % (2019 factsheet); newer value not found | https://interoperable-europe.ec.europa.eu/sites/default/files/inline-files/Digital_Government_Infographic_Poland_2019_1.pdf | SECONDARY, old |
| Share of matters handled online, number of templates in CRWDE, number of local e-services | not found | UNVERIFIED |

The pilot "dziesięć najczęstszych druków jednego urzędu" in the storyboard matches the NIK recommendation; mention it in speech or answer card 2 (own analysis). Use no number from this table on a slide except the 179 of 344.

---

## 3. Requirements a generated form must meet

| Requirement | What is established | Status |
|---|---|---|
| Digital accessibility | ustawa z 4.04.2019 o dostępności cyfrowej stron internetowych i aplikacji mobilnych podmiotów publicznych; its annex corresponds to WCAG level AA; gov.pl procurement guidance says the subject must meet "wszystkie wytyczne WCAG 2.1" of the annex; a public body must publish a "deklaracja dostępności". A gov.pl FAQ notes KRI mention WCAG 2.0 while the act refers to 2.1. gov.pl has a self-check list with a "Formularze" section mapped to WCAG 2.1 | SECONDARY (search summaries of https://www.gov.pl/web/baza-wiedzy/wcag-na-skroty , https://www.gov.pl/web/dostepnosc-cyfrowa/podmioty-publiczne , https://www.gov.pl/web/dostepnosc-cyfrowa/formularze) |
| Design system | the model page requires forms to meet a "standard ... UI i UX"; the gov.pl design system itself (components, licence) **was not found** | UNVERIFIED |
| Plain language | not researched; Mapa Życia announces "prostszy język" | UNVERIFIED for the standard, VERIFIED for the intent |
| Identification | central authentication; Profil Zaufany, mObywatel, bank login; signature in a signing system | VERIFIED (model page) |
| Delivery | e-mail, e-Doręczenia address, EZD mailbox or API | VERIFIED (model page) |
| Payment | ePłatności platform exists (about 1.2 million transactions); BLIK for passports planned 2026 | VERIFIED (Mapa Życia page, plan PDF) |
| Legal basis, KRI, template registration | an e-service needs a legal basis and a registered template; KRI not read | UNVERIFIED |

What an "e-usługa" needs beyond a form (from the model page): authentication, signature, delivery, case forwarding, template in the catalogue. Our prototype has none of the first three; the status slide already marks them "symulowane". Keep that honest, and show the form as a **front end that outputs a template description and a signed-ready print**, not as a finished e-usługa. (Own analysis.)

Practical for the demo: the generated form must show labels, keyboard operation, visible focus (gov.pl uses a black frame), error text tied to the field, and pass an automated check (axe or Lighthouse) shown on screen; say honestly that automated checks cover part of WCAG. (Focus detail VERIFIED in search summary of gov.pl; automated-coverage statement is general knowledge, UNVERIFIED here.)

---

## 4. What the state already does with AI around forms and services

- **mObywatel virtual assistant**: launched in the app on 31.12.2025 after a pilot of almost two months; model PLLuM; sources: info.mobywatel.gov.pl, gov.pl ministry pages, prezydent.pl. It "pomaga znaleźć interesujące użytkownika wnioski, formularze" and explains formalities. Limits stated by the ministry: do not enter personal data; no access to state registers, so no individual case; no interpretation of law; may be imprecise; needs app 4.71.1 or later; not for mObywatel Junior. Improvement planned from conversations, ratings and surveys. (VERIFIED, https://www.gov.pl/web/cyfryzacja/nowa-usluga-w-mobywatelu-wirtualny-asystent-ulatwi-korzystanie-z-uslug-publicznych)
- Usage reported in a 2026 article: over 1.17 million messages and 730 thousand conversations. (SECONDARY, via search summary, original not opened)
- PLLuM is a Polish model family; code and weights were planned to be open. (SECONDARY)
- **Mapa Życia** plans "strony wydarzeń życiowych" and proactive services. (VERIFIED)
- **Generator Formularzy ePUC** (section 2.2): a tool for the office side without AI mention in the plan lines I read. (VERIFIED for what the plan says; any AI feature in it UNVERIFIED)
- The ministry's plan for 2026 also lists AI Act implementation and an AI regulatory sandbox, which means AI governance questions are live. (VERIFIED, plan PDF)
- No public announcement of an AI form-digitising tool at COI or the ministry was found. (UNVERIFIED absence; only a few searches)

How the product complements them (usable sentence): "The assistant helps a resident find the right form. We turn the office's own paper form into the service the resident then opens, and the filled application the clerk prints. The description we produce is meant to feed the Generator Formularzy." Claim "feeds" only if an export exists by Sunday; otherwise say "can be exported".

---

## 5. Comparable work abroad

| Case | What it shows | Status |
|---|---|---|
| **GOV.UK Forms (GDS)**: July 2021 post: almost all forms on GOV.UK use PDFs or other document formats; the number grows about 6 % a year; "it would take the 11 existing form-building service teams around 70 years just to convert existing PDF forms into HTML forms"; document forms are "on average, 8 minutes slower to process compared to online forms"; target services with fewer than 10 000 transactions a year | VERIFIED, https://gds.blog.gov.uk/2021/07/06/making-all-forms-on-gov-uk-accessible-easy-to-use-and-quick-to-process/ |
| **Tim Paul, GDS (13.05.2024)**: prototype that sends page images to an LLM with a JSON schema and builds a multi-page GOV.UK-styled form. "Worked better than I'd anticipated"; JSON valid 100 % with the Claude API and a schema, but not always correct; mistook number fields for checkboxes on an ambiguous form; cannot do conditional routing or unusual question types; "unlikely to ever be 100% accurate"; AI part was quick, the surrounding UI and templating slower; recommends a human to correct afterwards and pairing AI with a rule-based design system. No count of forms tested, no cost | VERIFIED, https://www.timpaul.co.uk/posts/using-ai-to-generate-web-forms-from-pdfs ; repo https://github.com/timpaul/form-extractor-prototype (SECONDARY) |
| Tim Paul follow-up (5.05.2025): "what it would be like" to convert all document forms on GOV.UK; findings not retrieved | SECONDARY, https://conffab.com/elsewhere/could-ai-convert-all-the-pdf-forms-on-gov-uk-into-web-forms/ |
| **Code for America, asap_pdf**: open-source tool for auditing PDFs on city and state sites (crawler, classifier incl. type "form", summaries, "AI exception checker"); reviewer decides; partners Salt Lake City and the State of Georgia; "71% of PDFs" from federal agencies have at least one accessibility issue; no performance numbers given | VERIFIED, https://codeforamerica.org/news/our-ai-solution-to-governments-pdf-problem/ |
| US vendors: SimpliGov "SimpliAI Forms" (April 2026), Adobe-based federal exchange case, Cadmus white paper | vendor claims, no independent results | SECONDARY, https://www.newswire.com/news/simpligov-introduces-simpliai-forms-to-help-government-agencies-turn-22768372 |
| Estonia: once-only principle legally in force and being extended to AI automation; about 200 AI applications; Eesti.ai programme from January 2026; no source on PDF-to-service conversion | SECONDARY, https://www.oecd.org/en/publications/digital-government-outlook-2026_d46c0555-en/estonia_f5640fed-en.html |
| Denmark and others | nothing relevant found | UNVERIFIED |

Lessons to carry: (1) valid structure is cheap, correct meaning is not, so approval by a human is the design, not a weakness; (2) routing and conditions are where converters fail, so show one conditional rule handled by the person in the editor; (3) no measured accuracy exists publicly, so our own measurement on the 32 analysed forms (fields found, fields corrected) would be a rare number: report it only if measured (`metrics.json` rule).

---

## 6. Mass registration of refugees from Ukraine, spring 2022

Only sourced facts; each line can go on a slide.

- Applications for PESEL by Ukrainian citizens opened **Wednesday 16 March 2022**; in the **first week over 250 000** numbers were given ("ponad 250 tysięcy"). Applications could be filed at any gmina office. Extra points opened, among them the National Stadium in Warsaw with "ponad 1100 osób" served on the first day. The state sent 732 computer sets, 258 fingerprint scanners and about 2 000 mobile stations to gminas. Almost 100 000 Ukrainian citizens had created a Profil Zaufany since the start. Published 23.03.2022. (VERIFIED, https://www.gov.pl/web/cyfryzacja/cwierc-miliona-numerow-pesel-dla-obywateli-ukrainy)
- Legal basis: the act on assistance to Ukrainian citizens adopted by the Sejm on 9 March 2022, art. 4 allowing a PESEL application; symbol "UKR" in the register. (SECONDARY, kadry.infor.pl and the ministry's later reply on the Ombudsman page)
- Queues: queues formed before opening and numbered tickets were issued; in Olsztyn tickets for a whole week were given out in under an hour; in Wrocław the longest waiting list led to dates as far as 27 May; one person took 30-40 minutes at an Olsztyn counter, language being one reason; elsewhere "kilka-kilkanaście minut". (SECONDARY, https://www.gazetaprawna.pl/wiadomosci/kraj/artykuly/8387253,kolejki-po-pesel-terminy-dodatkowy-sprzet.html and https://www.se.pl/olsztyn/dlugie-kolejki-pod-ratuszem-w-olsztynie-uchodzcy-z-ukrainy-stoja-po-numer-pesel-aa-U34W-6enp-QGtY.html via search summaries; dated late March 2022; the pages were not opened)
- Ombudsman (6.04.2022) reported "długotrwałym, nawet kilkumiesięcznym, okresie oczekiwania" for PESEL and warned that it endangered benefit payment. (VERIFIED, https://bip.brpo.gov.pl/pl/content/rpo-ukraina-pesel-przepisy-dot-swiadczen-socjalnych-do-poprawy; "reports of", not a measured figure)
- Ministry's reply (29.04.2022): ZUS launched a dedicated online form on 26 March; within a month almost 217 000 applications for about 330 000 children for 2021/2022. (VERIFIED, same page)
- Simplified process: a document with a photo was enough (SECONDARY, search summary). A Diia.pl document: **not found in any source; do not mention.** (UNVERIFIED)
- Volunteers printing applications from data typed on phones: no public source; this is the owner's own experience and must be presented as such ("w moim punkcie pomocy w Opolu"), with no numbers unless he has records (see R09).

Safe sentence for the slide: "W marcu 2022 w pierwszym tygodniu nadano ponad 250 tysięcy numerów PESEL; kolejki pod urzędami trwały tygodnie." The second half is SECONDARY: soften to "pod urzędami tworzyły się kolejki".

---

## 7. Mapping to the likely COI criteria

Proxy: 2025 weights (Związek 25, Wdrożeniowy potencjał 25, Walidacja i bezpieczeństwo danych 20, UX i ergonomia pracy 15, Innowacyjność i prezentacja 15). Re-map at 11:00.

| Criterion | Part of the product that answers it | Show live | Evidence to prepare |
|---|---|---|---|
| Związek z zadaniem (25) | AI proposes fields, meaning, validation from a paper or PDF form; human approves; one description gives online form, print, rules: the "droga od potrzeby do usługi" | Demo 1: a real form from the Bydgoszcz catalogue in, a published phone form out; one visible mapping of a field to a profile field | numbers measured on the 32 analysed forms; time of one digitisation, labelled as measured |
| Wdrożeniowy potencjał (25) | description in an open format; export to a generator or template catalogue; no new database of people; pilot of ten most frequent forms of one office (NIK logic); open source | a JSON or XML description opened next to the form; the "rejestr" as files in a repository | one slide-length integration plan with Generator Formularzy ePUC, CRWDE/KAP, login.gov.pl, e-Doręczenia, marked "planned"; licence and dependencies list |
| Walidacja i bezpieczeństwo danych (20) | human approval gate; description bound to the template file hash; rules check before print; E2E encrypted QR handoff with a short lifetime; synthetic data; local or pseudonymised model | a deliberately wrong date flagged amber before print; the handoff packet expiring on the clerk screen; hash mismatch stops a changed template | test table: seeded errors caught versus missed; no real personal data; threat list in one table; AI Act note (clerk assistant, human decides) |
| UX i ergonomia pracy (15) | resident phone form entered once; clerk sees large-type data with ticks; one click print on the original template | a jury member scans the QR and fills a short form; clerk screen reacts; keyboard-only and screen-reader pass of the generated form | automated accessibility report (WCAG 2.1 AA) screenshot; time to fill versus the paper form, measured on at least three people |
| Innowacyjność i prezentacja (15) | two-sided flow from one description; print on the original template | the sheet sliding out of a printer with the dotted signature line | clean 10-slide PDF within 10 MB, video under the limit stated on the card at 11:00 |

---

## 8. Critique of the storyboard

Rules kept: at most six words on screen, at most three sentences of speech, two live demo slides.

### 8.1 Eight concrete improvements

1. **Slide 1, claim "710 druków"**. Problem: 710 are files (PDF, DOC, RTF, attachments, versions), not distinct forms; the screen words say "druków". Change: screen "710 plików. Jedno miasto." and say "710 plików formularzy w 275 kartach usług". A COI analyst will ask how many distinct forms; have the number ready or avoid it.
2. **Slide 1, last sentence**. Problem: "Każdy z tych druków czeka na swoją usługę online" is an overclaim; 179 of 344 national services are already digital and some local ones too. Change: "Większość z nich nie ma jeszcze formularza online" only if the catalogue supports it; otherwise "Tylko jeden z 32 zbadanych ma pola do wypełnienia" is enough. Say "w próbie 32", not "wszystkie".
3. **Slide 2, no link to what the state is building**. Problem: a COI jury knows Generator Formularzy ePUC; silence reads as ignorance. Change: speech sentence 2 becomes "Z jednego opisu powstają formularz na telefon, wydruk i reguły kontroli, a opis może zasilić Generator Formularzy." Keep screen "Od druku do usługi." Say "może zasilić" until an export exists.
4. **Slide 5, "Sprawdzone w kolejce"**. Problem: "sprawdzone" implies measured validation; there is no data from 2022 in the repository or in public sources. Change: screen "Z kolejki. Opole 2022." and add to speech "To moje doświadczenie, nie badanie." (flag, then continue). Keep the facts to what R09 supports.
5. **Slide 6, "Dane raz. Bez wspólnej bazy."**. Problem: the state's model is central (Profil Zaufany, mObywatel, registers); "bez wspólnej bazy" reads as an attack on it, and "rejestr opisów formularzy" duplicates CRWDE and Katalogi Administracji Publicznej. Change: screen "Dane zostają u mieszkańca."; speech: "Wspólny dla urzędów może być otwarty katalog opisów formularzy, zgodny z istniejącym repozytorium wzorów, a nie baza danych o ludziach."
6. **Slide 6, QR claim**. Problem: the real mObywatel flow is the institution showing a QR and the resident confirming which data go; institutions must apply to the ministry (mobywatel@mc.gov.pl). The slide 4 motion (phone scans a QR, form fills itself) shows our own channel. Change: in the "fallback" wording keep "przewiduje adapter" and add "kod pokazuje urząd, mieszkaniec zatwierdza dane"; never use the "built" wording unless the adapter was shown to work with a real or documented mObywatel flow.
7. **Slide 7, "logowanie urzędowe"**. Problem: vague; the experts say "login.gov.pl" or "Profil Zaufany". Change: right column "mObywatel", "login.gov.pl", "podpis kwalifikowany lub zaufany", "czytnik dokumentów"; the screen already limits labels to three words.
8. **Slide 8, pilot offer**. Problem: "otwarty rejestr, z którego skorzysta każdy urząd" is a promise beyond a 24-hour build and again competes with CRWDE. Change: "Proponujemy pilotaż: dziesięć najczęstszych druków jednego urzędu, wynik jako otwarty opis, gotowy do wprowadzenia do platform państwowych." Add the NIK reasoning only in the answer card.

### 8.2 Polish corrections ("was -> should be")

- Slide 1 screen: "710 druków. Jedno miasto." -> "710 plików. Jedno miasto."
- Slide 1 say: "tylko jeden z 32 zbadanych ma pola do wypełnienia" -> "tylko jeden z 32 przeanalizowanych jest formularzem z polami do wypełnienia" (the repository's analysis is of "pliki", and "pola" alone is ambiguous).
- Slide 3 say: "wgrywam druk pobrany ze strony urzędu" -> "wczytuję druk pobrany ze strony urzędu" ("wgrywam" is colloquial).
- Slide 4 say: "Teraz interesant: skanuje kod i podaje dane raz" -> "Teraz mieszkaniec: skanuje kod i podaje dane tylko raz" (the clerk calls the visitor "interesant", but the deck speaks to the jury and to "mieszkaniec" elsewhere; keep one word; "interesant" is acceptable in office slang, choose consistently).
- Slide 5 screen: "Sprawdzone w kolejce. Opole 2022." -> "Z kolejki. Opole 2022."
- Slide 6 screen: "Dane raz. Bez wspólnej bazy." -> "Dane zostają u mieszkańca."
- Slide 6 say: "przekazywanie danych instytucji kodem QR" -> "przekazywanie danych instytucji przez kod QR (funkcja „Przekaż instytucji”)".
- Slide 6 say: "Wspólny dla urzędów jest rejestr opisów formularzy" -> "Wspólny dla urzędów może być katalog opisów formularzy".
- Slide 7 caption: "przekazanie kodem QR" -> "przekazanie przez kod QR".
- Slide 8 caption: "druków jednego urzędu jako usług online w otwartym rejestrze" -> "druków jednego urzędu jako usług online, z opisem w otwartym formacie".
- Answer card 4: "do ustalenia z Państwem" -> "do uzgodnienia z COI i Ministerstwem Cyfryzacji"; add "w szczególności z Generatorem Formularzy ePUC".
- Answer card 3: "odpowiedni kontrast" -> "kontrast zgodny z WCAG 2.1 poziom AA"; add "automat sprawdza część wymagań, resztę przeglądamy ręcznie".
- Answer card 8: add "np. PLLuM albo Bielik" only if the model really tested is one of them; otherwise leave generic.

### 8.3 Claims a COI expert could dispute

- "Każdy z tych druków czeka na swoją usługę online" (see 8.1 item 2).
- "710 druków" (files, not forms).
- "tylko jeden z 32 zbadanych" (sample of one city hall; not representative of all offices, say so).
- "Dane raz" (once-only is a state principle; the claim is about our channel; clarify that registers still hold the master data).
- "Wspólny jest rejestr opisów formularzy" (duplicates CRWDE, KAP; ask: who may publish, how is it governed?).
- "W mObywatelu istnieje już przekazywanie danych ... nasz adapter jest na to przygotowany" (no access to the mObywatel institution programme was verified; "przygotowany" overstates).
- "zaszyfrowane od telefonu do urzędu" (end-to-end from a browser phone to a clerk's browser; the expert will ask who holds the key and how the key reaches the clerk; have a one-sentence answer).
- "znikają po wydruku albo po kilku minutach" (retention and logging obligations of an office: an application that was printed and signed becomes a document in the case file; say "dane tymczasowe znikają, wniosek podpisany zostaje w aktach urzędu").
- "AI wskazuje błąd" (a clerk assistant may be a high-risk system under the AI Act only in listed uses; say "wskazuje, urzędnik decyduje").
- "Formularz powstaje z jednego opisu ... każdy ma etykiety, obsługę klawiatury" (WCAG compliance of the output must be tested; show the report).
- "Wydruk identyczny z oryginałem" ("na oryginalnym wzorze": in public administration a template is binding only in the form published in the register; the expert may ask whether the print uses the official wzór or a re-typeset copy).
- "Czas digitalizacji" (only if measured; the card says so already).
- Slide 5: any claim about queue shortening in Opole without records.

---

## Open questions and what could not be verified

- Full task card, criteria and weights, deliverables, IP clause: appear 21.11 at 11:00. Everything in section 7 uses the 2025 proxy.
- Jury composition for this task (published by day two); whether COI mentors sit on it.
- Which COI or ministry team builds the Generator Formularzy ePUC, its current status, whether it has an import or API, and whether it contains AI features. Contact path: ask the COI Product Owner at the table.
- Number of templates in CRWDE, typical time to publish a wzór, who may publish today (only an older article was found), and the number of local e-services: not found.
- Share of matters handled online in Poland in 2024-2026; Eurostat value for Poland in "sending filled forms" for 2024 not retrieved (dataset isoc_ciegi_ac).
- gov.pl design system (name, components, licence), KRI text, plain-language standard, e-Doręczenia requirements for form-based services: not opened. The accessibility law was read only through search summaries.
- NIK figures come from search summaries of the audit PDFs; the PDFs were not opened.
- Queue figures for spring 2022 are from two news items seen only as search summaries; the date and city should be re-checked before they go on a slide. Diia.pl and any "simplified form" fact: not found.
- Number of forms Tim Paul tested and the findings of his 2025 follow-up: not available.
- Denmark and other countries; any measured accuracy of an AI converter in government: not found.
- COI, ministry and HackNation social-media posts; the Discord: not read.
- The Plan działalności PDF was parsed as text; its exact title of Part A/B for the Generator item was not confirmed; the document may have been amended after 29.12.2025.

## Sources

All accessed 2026-11-21.

1. https://hacknation.pl/zadania (VERIFIED) - task teaser, prize
2. https://hacknation.pl/mentorzy (VERIFIED) - COI and ministry mentors
3. https://www.gov.pl/web/cyfryzacja/tysiace-pomyslow-24-godziny-i-jeden-cel--usprawnic-panstwo-w-bydgoszczy-zakonczyl-sie-hacknation-2025 (VERIFIED) - 2025 tasks, winners, selection rule
4. https://www.gov.pl/web/cyfryzacja/hacknation-2026-zaczyna-sie-od-dobrego-wyzwania-za-nami-warsztaty-dla-instytucji-publicznych (VERIFIED) - challenge preparation
5. https://www.gov.pl/web/cyfryzacja/panstwo-ktore-rozumie-obywatela-mapa-zycia-porzadkuje-cyfrowe-uslugi (VERIFIED) - Mapa Życia, 179 of 344
6. https://www.gov.pl/attachment/3b014cc3-3674-4390-a832-9e8f0dadce07 (VERIFIED, parsed) - Plan działalności Ministra Cyfryzacji 2026, Generator Formularzy ePUC
7. https://www.gov.pl/web/ia/model-realizacji-e-uslug-zlozenie-dokumentu-przez-formularz (VERIFIED) - form-based e-service model
8. https://www.gov.pl/web/cyfryzacja/nowa-usluga-w-mobywatelu-wirtualny-asystent-ulatwi-korzystanie-z-uslug-publicznych (VERIFIED) - mObywatel assistant
9. https://www.gov.pl/web/cyfryzacja/cwierc-miliona-numerow-pesel-dla-obywateli-ukrainy (VERIFIED) - PESEL first week
10. https://bip.brpo.gov.pl/pl/content/rpo-ukraina-pesel-przepisy-dot-swiadczen-socjalnych-do-poprawy (VERIFIED) - Ombudsman, ZUS form figures
11. https://gds.blog.gov.uk/2021/07/06/making-all-forms-on-gov-uk-accessible-easy-to-use-and-quick-to-process/ (VERIFIED) - 70 years, 8 minutes
12. https://www.timpaul.co.uk/posts/using-ai-to-generate-web-forms-from-pdfs (VERIFIED) - AI PDF to web form experiment
13. https://codeforamerica.org/news/our-ai-solution-to-governments-pdf-problem/ (VERIFIED) - asap_pdf
14. https://conffab.com/elsewhere/could-ai-convert-all-the-pdf-forms-on-gov-uk-into-web-forms/ (SECONDARY) - follow-up summary
15. https://github.com/timpaul/form-extractor-prototype (SECONDARY) - prototype repo
16. https://www.gov.pl/web/baza-wiedzy/wcag-na-skroty , https://www.gov.pl/web/dostepnosc-cyfrowa/podmioty-publiczne , https://www.gov.pl/web/dostepnosc-cyfrowa/formularze (SECONDARY) - accessibility requirements
17. https://arslege.pl/centralne-repozytorium-wzorow-dokumentow-elektronicznych/k834/a59902/ , https://lexlege.pl/ustawa-o-informatyzacji-dzialalnosci-podmiotow-realizujacych-zadania-publiczne/art-19b/ (SECONDARY) - CRWDE
18. https://www.nik.gov.pl/kontrole/wyniki-kontroli-nik/pobierz,kap~p_20_004_202006150914271592205267~id0~01,typ,kj.pdf , https://www.nik.gov.pl/kontrole/wyniki-kontroli-nik/pobierz,kap~p_15_003_201506250902111435222931~id1~01,typ,kj.pdf (SECONDARY) - NIK audits
19. https://www.gov.pl/web/cyfryzacja/nowe-funkcjonalnosci-mobywatela and https://www.gov.pl/web/mobywatel-w-aplikacji/zalacznik-mobywatel (SECONDARY) - "Przekaż instytucji" (search summary)
20. https://www.gazetaprawna.pl/wiadomosci/kraj/artykuly/8387253,kolejki-po-pesel-terminy-dodatkowy-sprzet.html , https://www.se.pl/olsztyn/dlugie-kolejki-pod-ratuszem-w-olsztynie-uchodzcy-z-ukrainy-stoja-po-numer-pesel-aa-U34W-6enp-QGtY.html (SECONDARY) - queues 2022
21. https://symfonia.pl/public/programy/eformularze/ (SECONDARY) - commercial JST form builder
22. https://www.newswire.com/news/simpligov-introduces-simpliai-forms-to-help-government-agencies-turn-22768372 (SECONDARY) - vendor product
23. https://www.oecd.org/en/publications/digital-government-outlook-2026_d46c0555-en/estonia_f5640fed-en.html (SECONDARY) - Estonia
24. https://interoperable-europe.ec.europa.eu/sites/default/files/inline-files/Digital_Government_Infographic_Poland_2019_1.pdf (SECONDARY, old) - Poland form submission 2019
25. https://www.gov.pl/web/cyfryzacja/ankieta-epuap and https://warszawa19115.pl/en/-/epuap-elektroniczna-platforma (SECONDARY) - ePUAP and e-Doręczenia, COI help desk
