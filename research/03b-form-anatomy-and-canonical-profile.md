# R3b - Anatomy of the most common forms, the canonical profile, and what "print exactly like the approved template" requires

Access date for all sources: 2026-11-21. Method: 32 real files from um.bydgoszcz.pl / bip.um.bydgoszcz.pl / gov.pl were downloaded into `data/forms-cache/` (git-ignored) with an HTTP status, content-type and size check (all 33 URLs of the previous research returned HTTP 200 with the stated content type). PDFs were analysed with PyMuPDF 1.2x and pypdf (pdfplumber not installed); DOC/RTF could not be converted to PDF because LibreOffice (`soffice`) is NOT installed on this machine, so the six DOC/RTF files were analysed from their extracted text only (no geometry). Legal status was read from the ELI/ISAP API (`api.sejm.gov.pl/eli/acts/...`, field `status`) on 2026-11-21.

Legend: VERIFIED = I opened the primary source or measured the file; SECONDARY = reliable secondary source only; ESTIMATE = my own manual classification (not machine-measured).

## TL;DR for builders

- **The Bydgoszcz meldunek forms are the official ministerial template, not a local copy**: first page header shows `EL/ZPS/1` and the form is annex 1 to the MSWiA regulation of 13.12.2017 (Dz.U. 2017 poz. 2411, amended Dz.U. 2020 poz. 930, consolidated Dz.U. 2022 poz. 2070). ISAP status `IN_FORCE` on 2026-11-21. [VERIFIED status; identity of the Bydgoszcz PDF with the gov.pl one was matched by header/layout, not byte-compared]
- **Only a minority of the forms have a layout fixed by law.** Of 14 form families analysed: 5 are prescribed by regulation (meldunek stały/czasowy, vehicle registration application, DN-1, ZIN-1, de minimis information form), 1 has prescribed content but free form (pełnomocnictwo - KPA art. 33; wniosek UDIP), the rest are local auxiliary templates (Bydgoszcz WSO/WUK/WPL/USC cards). The print engine must treat the two classes differently: prescribed = pixel-faithful template, local = content-faithful.
- **The vehicle registration form changed legal base twice**: Dz.U. 2022 poz. 1847 and its 2023 amendment are "uznany za uchylony"; the current base is **Dz.U. 2024 poz. 1709** (in force 2024-11-30), amended by Dz.U. 2025 poz. 939 and Dz.U. 2026 poz. 891; the wzór is annex 1 ("format A5 lub A4"). [VERIFIED via API]
- **The pełnomocnictwo has no prescribed layout** (KPA art. 33; the Bydgoszcz DOC/PDF are auxiliary). It must be signed by hand; stamp duty 17 zl unless the proxy is spouse/ascendant/descendant/sibling. [SECONDARY for fee and exemption: gov.pl/web/uzp/oplata-skarbowa-od-pelnomocnictwa]
- **Text extraction from the official meldunek PDFs returns garbage** (Identity-H subsets without ToUnicode). Never anchor field positions on extracted text; anchor on vector geometry. Coordinates for page 1 of EL/ZPS/1 were measured and are in `data/form-descriptor.example.json`.
- **Method per class**: AcroForm PDF -> fill widgets with an embedded font (only ZIN-1 is an AcroForm, 156 text widgets, only 2 comb); flat vector PDF (all meldunek, DN-1, vehicle, local) -> coordinate overlay with embedded Lato/DejaVu; DOC/DOCX/RTF -> content-fill a copy of the document (python-docx) and print via a real office engine, or rebuild as PDF and mark as "local template".
- **Overlay test passed**: three fields (surname with ŻÓŁĆ, given names with ĄĘŚŹ, 11 PESEL digits one per cell) were overlaid on page 1 with Lato-Regular; raster diff at 150 dpi: 3521 changed pixels inside the field boxes, **0 outside**. This is the regression test to ship.
- **The owner's hypothesis "almost every form asks for the same data" is PARTLY true** (ESTIMATE): the identity+address+contact block appears on 14 of 14 person-submitted forms and covers 50-60 % of fields on simple one- and three-page forms, but only 25-45 % on tax and subsidy forms, where the bulk is case-specific property or business data. Overall about 45 % of all fields (field-weighted) are fillable from one profile, about 40 % are case-specific, about 15 % only a human (signature) or the clerk (office section, case number) can complete.
- **Signatures and the clerk block stay human**: meldunek page 3 has two signature boxes, an owner-confirmation box and a "Sekcja dla urzędnika" with stamp; the system pre-fills around them and leaves them blank.
- **Bydgoszcz's de minimis form is outdated**: the 2024 form in the city's BIP predates Dz.U. 2025 poz. 1489 and Dz.U. 2026 poz. 523 (amendments of the regulation; consolidated text Dz.U. 2026 poz. 449). Do not ship it as "current" without a check. [VERIFIED status via API; content gap UNVERIFIED]
- **The USC wniosek RTF is US Letter (612x792 pt), not A4**: scaling to A4 without a flag silently changes margins; the descriptor must carry `page_size_pt` and printing must be "actual size".

## 1. Form inventory and technical anatomy

Measured from the files (pages/size/fonts/AcroForm from PyMuPDF; "boxes" = small square vector rectangles or path cells; "dots" = lines of dotted blanks in text). One-character boxes are drawn as separate rectangles (meldunek) or as typographic characters `└────┴────┘` in the text layer (DN-1, ZIN-1), not as AcroForm comb fields.

| # | Form (department) | File | Pages / size | Class | AcroForm / XFA | Boxes / blanks | Fonts embedded | Notes |
|---|---|---|---|---|---|---|---|---|
| 00 | Wniosek o dostęp do informacji publicznej (BIP, UDIP) | PDF 399 kB (+ DOCX 29 kB) | 2 / A4 | flat vector (Word 2016) | none | 10 boxes (checkboxes), ~30 dotted lines | yes (Times, Calibri, Arial) | fields: applicant, e-mail, e-Doręczenia, ePUAP, request text, form of access, delivery; signature |
| 02 | Wzór wniosku UDIP (gov.pl attachment) | PDF 594 kB | 1 / A4 | flat vector | none | 13 dotted | yes | same data, generic gov.pl version |
| 03 | Zgłoszenie pobytu stałego `EL/ZPS/1` (WSO, ewidencja ludności) | PDF 228 kB | 3 / A4 (595x842) | flat vector (PDFCreator 2.3) | none | 98 cells (PESEL 11, phone 20, dates 3x8, house 9, flat 7, postal 5 ...) + 9 images | yes, Lato + Times, Identity-H | text layer garbled; PL+EN bilingual; 3 pages, signatures on p3 |
| 04 | Zgłoszenie pobytu czasowego (WSO) | PDF 224 kB | 3 / A4 | flat vector | none | 115 cells | yes | as 03 plus period of stay |
| 05 | Oświadczenie właściciela lokalu (WSO) | DOC 23 kB | 1 | DOC (no geometry) | n/a | 3 blanks | n/a | name+PESEL of the registrant, owner's handwritten signature |
| 06 | Pełnomocnictwo (WSO) | DOC 37 kB | 1 | DOC | n/a | 8 dotted | n/a | cites KPA art. 32-33 (t.j. Dz.U. 2025 poz. 1691) |
| 07 | Wniosek o zaświadczenie z rejestru mieszkańców / PESEL (WSO) | DOCX 17 kB | 1 / A4 | DOCX | n/a | checkboxes `□` | n/a | case no. `WSO-I.5345` printed in header |
| 08 | Wniosek o wielojęzyczny formularz (WSO) | DOC 33 kB | 1 | DOC | n/a | | n/a | EU multilingual standard form request |
| 09 | Wniosek o zameldowanie w drodze postępowania administracyjnego (WSO) | DOC 31 kB | 1 | DOC | n/a | dotted | n/a | |
| 10 | Wniosek USC (Urząd Stanu Cywilnego) | RTF 105 kB | 1-2 / **Letter** 612x792 | RTF | n/a | dotted | n/a | header `USC.III.5362.1.   .2026` |
| 11 | Wniosek rejestracja / czasowa / wyrejestrowanie / zbycie `UMB202,208,213,217` (WUK) | PDF 210 kB | 1 / A4 | flat vector | none | 167 rects (table lines), dotted | yes | footnotes cite Prawo o ruchu drogowym art. 73 |
| 12 | Pełnomocnictwo (WUK) | PDF 201 kB | 1 | flat vector | none | dotted | yes | PESEL only (no ID number) vs 06 which asks ID + PESEL |
| 13 | Wniosek o licencję - pośrednictwo (WUK `UMB173`) | PDF 549 kB | 2 | flat vector | none | numbered sections | yes | business-heavy |
| 14 | Zawiadomienie o zbyciu pojazdu `UMB217` | PDF 463 kB | 1 | flat vector | none | dotted | yes | owner + vehicle |
| 15/16 | Wniosek o zaświadczenie o niezaleganiu (osoby fiz./prawne, WPL) | PDF 420 kB / 420 kB | 1 / A4 | flat vector | none | dotted | yes | name, address, PESEL (+ ID for non-residents) |
| 17-20 | Zwrot/stwierdzenie nadpłaty podatku; opłata skarbowa (WPL) | PDF 33-476 kB | 1-2 | flat vector | none | dotted | yes | PESEL, tel., "karta konta", property location |
| 21-24 | Ulga w spłacie zobowiązań (wniosek os. fiz./prawna + załączniki 1-4, WPL) | PDF 586-744 kB | 3-8 | flat vector | none | 600+ rects (tables) | yes | financial tables; art. 67a Ordynacji podatkowej |
| 25 | Formularz informacji przy ubieganiu się o pomoc de minimis (2024) | PDF 607 kB | 12 | flat vector (Excel export) | none | 100 small boxes | yes | beneficiary data + aid history |
| 29 | **ZIN-1** załącznik do informacji o nieruchomościach (WPL) | PDF 68 kB | 2 | **AcroForm** | **yes, 156 text widgets, no XFA**, 2 comb | NIP/PESEL printed as `└────┴`; widgets rotated (tall rects) | yes | `Helv 0 Tf` default appearance, no Polish font |
| 30 | **DN-1** deklaracja na podatek od nieruchomości (WPL) | PDF 75 kB | 5 | flat vector | none | NIP/PESEL 11, year 4 boxes as text | yes | "WYPEŁNIĆ DUŻYMI, DRUKOWANYMI LITERAMI, CZARNYM LUB NIEBIESKIM" |
| 31 | Oświadczenie o wartości sprzedaży alkoholu (WSO zezwolenia) | PDF 166 kB | 1 | flat vector | none | dotted | yes | cites art. 111 ust. 4 ustawy o wychowaniu w trzeźwości |
| 32 | Karta usługi - świadczenia (dodatki mieszkaniowe, stypendia) | PDF 246 kB | 7 | information leaflet | none | none | yes | NOT a form: lists legal basis incl. uchwała RM Bydgoszczy XL/884/21 setting the wzór wniosku about dodatek mieszkaniowy |

Signature places: every form has a printed "podpis" line or box; EL/ZPS/1 has two boxes (owner of premises, applicant) plus an official-use box. Instructions printed on forms: EL/ZPS/1 "Wypełniaj wielkimi literami / Fill in capital letters", "Wypełniaj kolorem czarnym lub niebieskim", checkbox marks `V` or `X`; DN-1/ZIN-1 the same wording. Duplex: only the 3-page forms (03, 04, 30 at 5 pages, 25 at 12 pages) are plausibly duplex; the descriptor carries `print.duplex` per form because the ministry templates number pages "strona 1/3", so a duplex sheet pair must never separate a signature page from the page it certifies.

**Surprise on quality of the Bydgoszcz publication**: forms 03/04 are PDFCreator 2.3.2.6 files of May-June 2020 while the PDF producer of the gov.pl copy is not known; therefore when the ministry republishes the annex, Bydgoszcz's copy can silently diverge. The descriptor stores `sha256` of the template and the loader must refuse to print a form whose current file hash differs from the descriptor (SHA-256 of the permanent-residence PDF used here: `4bf2818f2c0c927d77ed89142388e7385a835cd4357a0b6b921621d930df779a`, 228,401 bytes).

## 2. Field inventory, overlap matrix and the "same data" hypothesis

### 2.1 EL/ZPS/1, permanent residence (fully inventoried; 31 fields over 3 pages) [VERIFIED by rendering and geometry]
Page 1: surname, given names, PESEL (11 cells), country of birth, country of previous residence, date of birth (8 cells, only if no PESEL), place of birth (only if no PESEL), mobile phone (20 cells), e-mail, consent to transfer contact data to the register (3 checkboxes). Page 2: street, house number (9 cells), flat number (7 cells), postal code (2+3 cells), city/district, gmina, voivodeship, "unregister from temporary residence" checkbox, proxy surname and given name, confirmation place and date. Page 3: owner-of-premises signature box, place, date, applicant signature box, official section (place, date, stamp+signature).

Classification: from the canonical profile 18 fields (58 %); case decision or case value 8 (26 %: consents, wymeldowanie checkbox, places and dates); human-only 2 (signatures) and clerk-only 3 (official block) = 5 (16 %). [ESTIMATE of classification, count VERIFIED]

### 2.2 Overlap matrix (which canonical items each form asks for)
`X` = asked as personal data of the applicant; `p` = asked for another person (proxy/owner/registrant); `b` = business; `v` = vehicle; `r` = real estate. ESTIMATE from extracted text and rendering.

| Canonical item | 00/02 UDIP | 03/04 meld. | 05 owner | 06/12 pełn. | 07 zaśw. EL | 11/14 vehicle | 15-20 podatki | 21-24 ulga | 25 de min. | 29/30 ZIN/DN | 31 alkohol | 13 licencja |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| surname + given names | X | X, p | p | X, p | X | X | X | X | b/p | X | b/p | b/p |
| PESEL | | X | p | X, p | X | X | X | X | | X (or NIP) | | |
| NIP | | | | | | | | | b | X | b | b |
| REGON | | | | | | b | | | b | | | b |
| ID document no. | | | | X, p (06) | | | (non-resident) | | | | | |
| birth date / place | | X (no PESEL) | | | | | | | | | | |
| address (street, no., postal, city) | X | X (new address) | p | X, p | X | X | X | X | b | X | b | b |
| phone | | X | | | X | X | X | X | | | | |
| e-mail | X | X | | | | X | | | | | | |
| e-Doręczenia / ePUAP address | X | | | | | | | | | | | |
| family / household | | | | (relation) | | | | X (household income) | | | | |
| proxy | | X | | (is the form) | | | | | | | | |
| property owner | | X (p) | X | | | | | | | | | |
| business data | | | | | | | | | X | | X | X |
| vehicle | | | | | | X | | | | | | |
| real estate | | | | | | | X (location) | X | | X | | |
| place + date of letter | X | X | X | X | X | X | X | X | | | X | X |
| signature | X | X, X | X | X | X | X | X | X | X | X | X | X |

Reading: surname/given names/address/phone appear on 11-12 of 12 columns; PESEL on 8; NIP/REGON only in business and tax columns. A profile therefore removes most retyping for the citizen flows (meldunek, zaświadczenia, pełnomocnictwo, podatki, vehicles) and much less for subsidy and licence forms.

### 2.3 Quantification per form (ESTIMATE, manual classification of the extracted fields; use as order-of-magnitude, to be replaced by the field-level audit the builders produce from descriptors)
Share of fields by who can fill them: P = from the canonical profile (incl. proxy/owner/business/vehicle/real-estate sections), C = case-specific (decision, amount, purpose, date, free text), H = only a human (signature) or the clerk (case number, stamp, office block).

| Form | Approx. fields | P | C | H |
|---|---|---|---|---|
| UDIP wniosek (00) | 11 | 55 % | 36 % | 9 % |
| EL/ZPS/1 (03) | 31 | 58 % | 26 % | 16 % |
| Zgłoszenie czasowe (04) | 33 | 55 % | 30 % | 15 % |
| Oświadczenie właściciela (05) | 4 | 25 % | 25 % | 50 % |
| Pełnomocnictwo (06) | 8 | 62 % | 25 % | 13 % |
| Zaświadczenie z rejestru (07) | 14 | 29 % | 57 % | 14 % |
| Vehicle wniosek (11) | 22 | 59 % | 27 % | 14 % |
| Zaświadczenie podatkowe (15) | 9 | 60 % | 30 % | 10 % |
| Zwrot nadpłaty (17) | 10 | 50 % | 40 % | 10 % |
| DN-1 | about 60 | 42 % | 47 % | 11 % |
| ZIN-1 (156 widgets) | about 150 | 3 % | 90 % | 7 % |
| Alcohol statement (31) | 10 | 55 % | 35 % | 10 % |
| Licencja pośrednictwo (13) | about 30 | 40 % | 50 % | 10 % |
| de minimis (25) | about 80 | 25 % | 65 % | 10 % |

Simple unweighted mean of P over the 14 forms: about 44 %; field-weighted mean (ZIN-1, DN-1, de minimis dominate): about 36 %. The reasonable claim for the hackathon pitch: "the same identity block is asked on every form; on the five most common citizen forms a single profile fills 55-60 % of all fields and 100 % of the personal block; the remainder is the specific request and the signature". Do not claim "almost every field".

## 3. Canonical profile

### 3.1 Design (file `data/canonical-profile.schema.json`, JSON Schema draft 2020-12, metaschema-validated)
Sections: `applicant` (person: names, family name at birth, parents, PESEL, NIP, sex, birth, citizenship, marital status, `id_document`, residence and correspondence addresses with TERYT SIMC/ULIC, contact incl. e-Doręczenia and ePUAP), `household_members[]` (relation enum + person), `proxy` (person, relation, basis, scope, stamp-duty exemption), `property_owner`, `business`, `vehicles[]`, `real_estate[]`, `case` (life situation, place/date of letter, subject text, period, consents, delivery channel, attachments), `provenance` (per path: source `citizen_form|clerk_typed|id_scan_ocr|mrz_reader|mobywatel|registry_lookup|previous_case`, time, `verified_by_clerk`, confidence). Polish titles are in `title`. `case` is deliberately inside the same document but must not be persisted in the long-lived profile store.

Design decisions: (1) the schema holds patterns only; checksum rules are named in `x-validator` and described in `x-validators` so any language can implement them (JSON Schema cannot compute a checksum). (2) `\p{L}` was avoided; names use the explicit range `A-Za-zÀ-ɏ` so the same patterns work in Python, JS and Java regex dialects. (3) `pesel` may be `null` (persons without PESEL): then `birth.*` becomes required, mirroring the form instruction. (4) `disability_degree` is special-category data (art. 9 RODO) and is annotated as consent-only.

### 3.2 Validation rules (all in `x-validators`; PESEL and NIP self-tested)
- PESEL: weights 1,3,7,9,1,3,7,9,1,3, control = (10 - sum mod 10) mod 10; birth date from digits 1-6 with century code in the month field (01-12 = 1900s, 21-32 = 2000s, 41-52 = 2100s, 61-72 = 2200s, 81-92 = 1800s); digit 10 odd = male. The test value [the textbook example number from the public description of the PESEL algorithm] (a well-known public example) passes.
- NIP: weights 6,5,7,2,3,4,5,6,7, mod 11, remainder 10 invalid (test 5260250995 passes).
- REGON 9 and 14 digits: weights 8,9,2,3,4,5,6,7 and 2,4,8,5,0,9,7,3,6,1,2,4,8.
- Postal code `^[0-9]{2}-[0-9]{3}$`.
- Dowód osobisty: 3 letters + 6 digits; letters A=10..Z=35; weights 7,3,1,(check digit),7,3,1,7,3; control mod 10. Passport: use MRZ ICAO 9303 check digits instead of a number-only check.
- IBAN: move first four characters to the end, letters to numbers, mod 97 == 1; Polish NRB 26 digits with optional `PL`.
- Księga wieczysta: court code + 8 digits + control digit, weights 1,3,7 repeated.
These algorithms are public knowledge; I did not find them in a single primary source, so treat them as [SECONDARY] and keep the unit tests with at least 3 known-good and 3 known-bad values per rule.

## 4. Statutory status of each form

Method: ELI API `status` field for each act (VERIFIED 2026-11-21), plus the form's own printed legal basis. "Prescribed" = a regulation contains a wzór (template) as annex. "Content only" = statute lists required elements but no layout. "Local" = Bydgoszcz auxiliary template.

| Form | Status | Legal base (Dz.U.) | What legally matters for the printout |
|---|---|---|---|
| EL/ZPS/1 and czasowy | **Prescribed** wzór (annex 1) | Rozporządzenie MSWiA z 13.12.2017 w sprawie określenia wzorów i sposobu wypełniania formularzy stosowanych przy wykonywaniu obowiązku meldunkowego, Dz.U. 2017 poz. 2411; zm. Dz.U. 2020 poz. 930; t.j. Dz.U. 2022 poz. 2070; delegation art. 39 ust. 1 ustawy z 24.09.2010 o ewidencji ludności (t.j. Dz.U. 2026 poz. 384). `IN_FORCE`. | Use the annex layout and wording; the regulation also defines how to fill it. gov.pl pages say it may be filled by computer or by hand and that the clerk may print a form from the system in the applicant's presence [SECONDARY: gov.pl/web/gov/zamelduj-sie-na-pobyt-staly-lub-czasowy-dluzszy-niz-3-miesiace, samorzad.gov.pl Lutomiersk]. Signature by hand. |
| Oświadczenie właściciela lokalu | **Local** | ustawa o ewidencji ludności requires the owner's/holder's confirmation of stay (article number UNVERIFIED, not read); the template is Bydgoszcz's | Content required (name+PESEL of the registrant, owner's handwritten legible signature); layout free. Owner confirmation can alternatively be written on page 3 of EL/ZPS/1. |
| Pełnomocnictwo (06, 12) | **Content only / free form** | KPA art. 32-33 (t.j. Dz.U. 2025 poz. 1691, `obowiązujący`) | Proxy shall prove authority with a written power of attorney (or one recorded in the office's protocol); layout free; **handwritten signature**; stamp duty 17 zl per document unless spouse, ascendant, descendant or sibling (ustawa o opłacie skarbowej, t.j. Dz.U. 2026 poz. 1395, part IV of the annex) [SECONDARY]. Original (or certified copy) is filed. |
| Wniosek UDIP (00/02) | **Content only** | ustawa z 6.09.2001 o dostępie do informacji publicznej, t.j. Dz.U. 2022 poz. 902, zm. Dz.U. 2025 poz. 1844 | No form prescribed; a request needs only to identify the requester and the information. Letter may arrive by any channel; art. 10 ust. 1 was rewritten from 1.07.2026 (see R2). Bydgoszcz's form is optional. |
| Wniosek rejestracja/wyrejestrowanie/zbycie (11, 14) | **Prescribed** wzór (annex 1, format A5 or A4) | Rozp. MI z 8.11.2024 w sprawie rejestracji i oznaczania pojazdów..., **Dz.U. 2024 poz. 1709**, `obowiązujący` from 2024-11-30; amended Dz.U. 2025 poz. 939 and Dz.U. 2026 poz. 891; repeals Dz.U. 2022 poz. 1847 and 2023 poz. 1255 (both "uznany za uchylony"). Annex 2 is the form for vehicles of art. 73 ust. 2a PoRD. | Bydgoszcz's `UMB202,208,213,217` is the combined card/form (it matches the title of annex 1 "wniosek o rejestrację, czasową rejestrację, wyrejestrowanie pojazdu lub zawiadomienie o zbyciu pojazdu"); I did not diff it against the ISAP image because ISAP publishes annexes as an image ("patrz oryginał"). The prescribed layout is binding. |
| DN-1, ZIN-1 (and IN-1) | **Prescribed** wzór | Rozp. MF z 30.05.2019 w sprawie wzorów informacji o nieruchomościach i obiektach budowlanych oraz deklaracji na podatek od nieruchomości, **Dz.U. 2019 poz. 1104**, `obowiązujący`, no amending acts listed in ELI on 2026-11-21 | Form must follow the annex (field numbering "1. Identyfikator podatkowy" etc.); instruction "wypełnić dużymi drukowanymi literami czarnym lub niebieskim". The Bydgoszcz files DN-1(1)/ZIN-1(1) carry the 2019 layout and an old legal basis footer (Dz.U. 2018 poz. 1445); this is the annex's own footer and does not make them non-current. |
| Formularz de minimis | **Prescribed** content/wzór | Rozp. RM w sprawie zakresu informacji przedstawianych przez podmiot ubiegający się o pomoc de minimis; consolidated text Dz.U. 2026 poz. 449 (obwieszczenie PRM of 19.03.2026); amended Dz.U. 2026 poz. 523 (8.04.2026) | Bydgoszcz form dated 2024 may be stale after Dz.U. 2025 poz. 1489 and 2026 poz. 523. [status VERIFIED, content diff NOT done] |
| Wniosek o zaświadczenie (07, 15) | **Local** | Ordynacja podatkowa art. 306a-306d (zaświadczenia podatkowe); for 07 the ustawa o ewidencji ludności | Content: requester, what to certify, purpose. Stamp duty for the zaświadczenie. |
| Zwrot nadpłaty (17-20) | **Local** | Ordynacja podatkowa art. 72-80 | Written request; no wzór. |
| Ulga w spłacie (21-24) | **Local** (annex 1-4 to the city's own "Instrukcja") | art. 67a Ordynacji podatkowej | Content defined by the city's instruction, not by a regulation. |
| Alcohol statement (31) | **Local template of a statutory duty** | art. 111 ust. 4 ustawy o wychowaniu w trzeźwości i przeciwdziałaniu alkoholizmowi (t.j. Dz.U. 2023 poz. 2151) | Content required by statute; layout free. |
| Licencja pośrednictwo (13) | **Unverified** | ustawa o transporcie drogowym | I did not establish whether a wzór is prescribed; treat as local until checked. |

**What "print exactly like the approved template" means legally** (synthesis; not legal advice, to be confirmed by the city's legal adviser): for prescribed forms the office must accept and issue the form in the shape of the annex, so a deviation in wording, field order or numbering is a risk of the application being treated as defective (KPA art. 64 wezwanie do uzupełnienia) or the declaration being treated as not filed in the prescribed form; pixel-identity is not required by any text I found, but identical content, field labels, order and legible entries are. For local templates and "content only" documents, the content and the signature matter; layout can change. Signatures: a handwritten signature in ink is required on the printout; the system must never print a facsimile signature. Originals: the paper form signed by hand is the original; scans are copies. I found no requirement for duplex or paper weight in the sources read (UNVERIFIED for city-specific rules).

## 5. "100 % identical print": technical requirements per source class

| Source class | Where in sample | Recommended fill method | Fonts | Comb / boxes | Overflow | Risks |
|---|---|---|---|---|---|---|
| AcroForm PDF | ZIN-1 (29) | PyMuPDF `Widget.update()` or pdf-lib `form.getTextField().setText()` with a **registered embedded TTF**; set DA to the embedded font; then flatten (PyMuPDF `bake()` or pdf-lib `form.flatten()`) before printing | Default appearance `Helv 0 Tf` is WinAnsi: no Polish `ł ś ć ń ź ż ą ę ó` glyph guaranteed -> override with Lato/DejaVu/Liberation | only NIP/PESEL are comb (`MaxLen 11`, flag 24); other widgets are plain multiline | auto-size (`Tf 0`) works; cap at 6 pt and flag | widgets are rotated: apply the page rotation to the bbox; viewers differ in regenerating appearance (`NeedAppearances`) |
| Flat vector PDF | 00, 03, 04, 11-17, 30, 31 | **Coordinate overlay**: draw into a copy of the page with PyMuPDF `insert_text` or ReportLab/pdf-lib `drawText`, merge into the original page content; do not re-render the template | embed Lato-Regular (SIL OFL) - it is the template's own typeface; DejaVu Sans as fallback; subset-embed | one glyph centred per cell: x = cell0 + i*pitch + (cell_w - glyph_w)/2 | `shrink_to_9pt_then_flag` for single-line boxes; continuation sheet for free text | text layer unusable; measure from vector rectangles (done) |
| Scanned PDF | none in sample; will occur for old forms | overlay on a deskewed raster at known dpi; calibrate with 3 anchor points | same | measure boxes by image processing | same | any scaling changes output; run the regression test |
| DOC/DOCX/RTF | 05-10 | content-fill a copy via python-docx (DOCX) or convert to DOCX first; render with a real engine (LibreOffice/Word) to PDF for the print job; treat as local template | fonts of the document (Times New Roman) must be installed on the print host | tables or dotted lines: replace the dots, never overlay | text reflows: check page count unchanged | **LibreOffice is not installed on this machine**; USC RTF is Letter size |

Multi-person duplication: most forms are per person; for a household render one document per person from the same descriptor with `subject = household_members[i]`; the proxy block is filled only if `proxy` exists. Duplex flag: descriptor `print.duplex` plus `print.sheet_breaks`; never print a signature page alone. Page scaling must be "none".

**Regression test (implemented and passed)**: render blank template and filled PDF at 150 dpi; compute per-pixel sum of absolute RGB differences > 30; build a mask from the union of the descriptor bboxes expanded by 1.5 pt; assert zero differing pixels outside the mask. Result for the three-field test above: 3,521 pixels inside, 0 outside. Add: (a) each field's text bbox (font metrics) must be inside its box (fail on overflow), (b) hash of the template equals the descriptor `sha256`, (c) for AcroForm sources, fields not in the descriptor must stay empty. Optional second test: render the filled PDF, OCR the fields (Tesseract is not installed here; use any OCR) and compare to the profile.

## 6. Form descriptor format

Worked example: `data/form-descriptor.example.json` (EL/ZPS/1, page 1 fully measured: 12 fields, three of them comb or date-parts, with real coordinates in PDF points, top-left origin; the example also lists pages 2-3 as summaries and points to the 8-cell date and 9/7-cell house/flat comb structure).

Fields of the format: `form_id`, `title_pl`, `source{url, accessed, sha256, bytes, content_type}`, `legal_basis{status, act, dz_u, annex, delegation, isap_status_checked}`, `template_class`, `fill_method`, `pages`, `page_size_pt`, `coordinate_system`, `acroform`, `overlay_font{name,file,license,embed}`, `print{paper,duplex,color}`, `instructions_on_form`, `fields[]{id, label_pl, canonical_path, page, bbox{x0,y0,x1,y1}, kind(text|comb|checkbox|date-parts|signature), comb{cells[],cell_w,y0,y1,groups,separators}, font, size, max_chars, transform, required, required_if, validation, who_fills(applicant_profile|applicant_decision|human_signature|clerk), overflow, depends_on, note}`, `regression_test`.

Measured geometry (page 595x842 pt; the same numbers are in the JSON): surname box 184.0,281.8-514.7,299.3; given names 184.3,310.0-515.0,327.4; PESEL 11 cells starting x=184.9, pitch 12.26, y 337.5-354.9; country of birth 183.9,365.3-514.5,382.7; previous country 183.9,395.4-514.5,412.8; date of birth cells x = 185.9, 198.2 | 225.1, 237.4 | 267.6, 279.9, 292.1, 304.4 at y 449.0-466.4; place of birth 183.3,481.7-514.0,499.1; mobile phone 20 cells from x=184.9, pitch 12.25, y 538.2-555.6; e-mail 184.8,574.4-515.5,591.9; checkboxes 76.8,626.7 (10.5 pt), 98.9,674.6, 335.2,675.3. Page-2/3 structure is described but not measured (budget).

Open design choices left to builders: whether to print the e-mail in capitals (the form says capital letters; an upper-cased e-mail is still a valid address, but a reviewer might object), and what to enter in "Kraj poprzedniego miejsca zamieszkania" for a move within Poland (the descriptor note says "to be confirmed").

## Verdicts on the previous research

- **C29** (pypdf or pdf-lib can fill AcroForm fields with embedded Polish fonts and flatten; flat PDFs need a coordinate overlay (ReportLab/PDFKit); forms with one-character boxes need per-character stepping): **PARTLY**.
  - AcroForm: only 1 of 32 sampled files is an AcroForm (ZIN-1, 156 text widgets, 2 comb, default font `Helv` with no Polish glyphs); PyMuPDF filled and read back `Łódź żółć ĄĘŚ` in a widget, but pypdf's own appearance generation is weak (no automatic embedded-font appearance), so use PyMuPDF or pdf-lib with a registered font and flatten.
  - Flat PDFs need a coordinate overlay: CONFIRMED - tested (0 pixels differ outside the field boxes, Lato with Polish letters).
  - One-character boxes need per-character stepping: CONFIRMED for the meldunek forms (cells are separate rectangles, pitch about 12.26 pt, not AcroForm comb); in DN-1/ZIN-1 boxes are text characters, so stepping is also needed there.
  - The claim omits text-layer garbage in the official PDFs (position must come from vector geometry), DOC/RTF sources, and legal status of the layout.

## Open questions and what could not be verified

- Byte-level identity of Bydgoszcz's EL/ZPS/1 with the gov.pl official PDF (`gov.pl/attachment/fac08267-59f8-4a09-bbe5-07ac653e0eb3`): the gov.pl file was not downloaded; only layout and header `EL/ZPS/1` were matched.
- Whether the ISAP annex of Dz.U. 2024 poz. 1709 equals the Bydgoszcz vehicle form: ISAP gives the annex as an image; not diffed.
- Legal consequence of a non-pixel-identical printout of a prescribed form: no primary source was found stating a rule; the synthesis in section 4 is my reading. A legal opinion is needed before promising "legally identical".
- KPA art. 33 and the stamp-duty annex were not read from the act text (the API `text.html` returned no article text for the consolidated acts); fee and exemption rest on gov.pl/web/uzp and infor.pl pages [SECONDARY].
- Checksum algorithms for ID card and księga wieczysta: from general knowledge, unit-test them before use.
- Licencja `UMB173`: whether the wzór is prescribed was not established.
- DOC/RTF forms (05-10) were not rendered (no LibreOffice); geometry unknown. Page 2-3 coordinates of EL/ZPS/1 and all other forms were not measured. Field counts and P/C/H shares are my manual estimates, not machine measurements.
- Whether the meldunek forms changed after the t.j. of 2022 (ELI lists only Dz.U. 2020 poz. 930 as amendment as of 2026-11-21), and whether the 2026 consolidated text of the ewidencja act (Dz.U. 2026 poz. 384) changed the delegation article: article text could not be read through the API.

## Sources

- https://api.sejm.gov.pl/eli/acts/DU/2017/2411 (meldunek regulation, status IN_FORCE, amended by DU/2020/930)
- https://api.sejm.gov.pl/eli/acts/DU/2022/2070 (t.j. obwieszczenie)
- https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20170002411/O/D20172411.pdf
- https://api.sejm.gov.pl/eli/acts/DU/2024/1709 and https://api.sejm.gov.pl/eli/acts/DU/2024/1709/text.html (vehicle registration regulation, annexes list)
- https://api.sejm.gov.pl/eli/acts/DU/2022/1847 and /2023/1255 (repealed), /2026/891, /2025/939 (amendments, via search listing)
- https://api.sejm.gov.pl/eli/acts/DU/2019/1104 (DN-1/ZIN-1/IN-1 regulation, IN_FORCE)
- https://api.sejm.gov.pl/eli/acts/DU/2022/1849 (vehicle approval procedures and document templates, amended 2026/998)
- https://api.sejm.gov.pl/eli/acts/search?title=... (de minimis regulation: DU/2026/449, DU/2026/523, DU/2025/1489; ewidencja ludności t.j. DU/2026/384; opłata skarbowa t.j. DU/2026/1395; KPA t.j. DU/2025/1691)
- https://www.gov.pl/web/uzp/oplata-skarbowa-od-pelnomocnictwa
- https://www.gov.pl/web/gov/zamelduj-sie-na-pobyt-staly-lub-czasowy-dluzszy-niz-3-miesiace
- https://www.gov.pl/attachment/fac08267-59f8-4a09-bbe5-07ac653e0eb3 (official EL/ZPS/1, not downloaded)
- https://samorzad.gov.pl/web/gmina-lutomiersk/zameldowanie-na-pobyt-staly-lub-czasowy
- https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Pobyt_staly_i_czasowy/Formularz_meld._-_Zgloszenie_pobytu_stalego.pdf (and the 32 other files listed in `data/forms-cache/_manifest.json`)
- Local measurement artefacts (not repo content): `data/forms-cache/_analysis.json`, `_meld_overlay_test.pdf`
