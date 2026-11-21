# Forms catalogue of Urząd Miasta Bydgoszczy (crawl of 2026-11-20/21)

Machine-readable catalogue of every service card ("karta usługi", code UMBnn) and every downloadable form template on the e-urząd portal of Miasto Bydgoszcz plus the BIP template pages. Produced by `tools/crawl_bydgoszcz_forms.py`; data in `data/forms-catalog.json` (cards with attachments) and `data/forms-catalog.csv` (one row per attachment). Access date of all sources: 2026-11-21. Crawl ran 2026-11-20 21:59 UTC, 1266 requests, 674 s, robots.txt respected.

## TL;DR for builders

- The portal https://um.bydgoszcz.pl/ is a TYPO3 site with a stable structure `/sprawa/<category-id>/<slug>/`. 465 card pages resolve to **275 unique cards** (codes UMB1 to UMB304): the same card is published under several categories. All 465 pages returned HTTP 200. VERIFIED (crawl).
- **681 unique downloadable attachments on cards + 29 on BIP pages = 710 unique URLs.** On cards: 334 PDF, 149 DOCX, 118 DOC, 77 RTF, 1 XLS, 1 XLSX, 1 JPG. Many are RODO clauses, not forms: filter by label/URL (`rodo|klauzul|obowi`).
- Forms are mostly Word/RTF/PDF templates to print and fill in by hand. File contents were not parsed, so whether PDFs have fillable fields is unknown; plan on reproducing the official templates in own PDF/DOCX layout and compare visually.
- Only **4 of 710 attachment URLs are not OK**: one real 404 (PB-5 oswiadczenie, card UMB272), one dead archive host (archiwumbip), two blocked by robots.txt so unchecked (bip /binary/Pelnomocnictwo, isap PDF). All 33 URLs listed by the previous research answer HTTP 200 with the expected type (section 6).
- 15 unique cards have **no downloadable form** (online-only, information-only or fee-schedule cards): section 5.
- Cards link to external online services (ePUAP catalogue, gov.pl, obywatel.gov.pl, biznes.gov.pl, PWPW for KKK). The JSON flag `online_handling` is a WEAK heuristic (the ePUAP logo is on every card; 173 of 275 cards are flagged). Use `external_links` and the card text; the crawler was patched so an explicit denial ("Sprawy nie załatwisz przez Internet") sets it to false (existing data files not regenerated).
- Biggest departments by card count: Spraw Obywatelskich 46, Uprawnień Komunikacyjnych 40, Administracji Budowlanej 27, Mienia i Geodezji 22, Ochrony Środowiska 22, USC 22.
- Since 1 Jan 2026 the tax department does not accept general submissions through ePUAP; only IN-1, DN-1, IR-1, DR-1, IL-1, DL-1, DT-1 may still go by ePUAP. VERIFIED on BIP /artykul/1009/9251.
- Dowód osobisty: no paper application since 29.12.2023; the clerk's system generates it from the registers. VERIFIED on card UMB19. A "pre-fill and print the ID application" feature does not apply to this procedure.
- Bank account numbers appear in the fees text of some cards (e.g. UMB83). The crawler now replaces them with `[numer rachunku: patrz aktualna karta uslugi]` before writing output; the published data files were cleaned by hand.

## 1. How the portal is structured

| Layer | Pattern | Notes |
|---|---|---|
| Home / index | https://um.bydgoszcz.pl/ | menu of life situations and departments; listing pages carry card code UMBnn and icons for online channels |
| Category | `/sprawa/<category-id>/...`, ids seen 155-224 | one category = life situation or department area (165 dowody osobiste, 166 USC, 172 prawa jazdy, 173 rejestracja pojazdów, 155/189/192/193 podatki i opłaty) |
| Card | `/sprawa/<category-id>/<slug>/` | blocks: Co musisz przygotować / Ile zapłacisz / Gdzie załatwisz / Podstawa prawna / "karta nr: UMBnn"; attachments are `/ebokfile/<unit>/...` files |
| Files | `https://um.bydgoszcz.pl/ebokfile/<unit>/...` (`wso`, `usc`, `wuk`, `wpl`, `wmg`, `wab`) | direct download, HEAD works, no login |
| | BIP page | HTTP | Attachments |
|---|---|---|
| https://bip.um.bydgoszcz.pl/artykul/1052/2/udostepnianie-informacji-publicznej | 200 | 2 |
| https://bip.um.bydgoszcz.pl/artykul/1053/1/ponowne-wykorzystanie-informacji-publicznej | 200 | 0 |
| https://bip.um.bydgoszcz.pl/artykul/1009/574/wnioski-w-sprawach-podatkow-i-oplat-lokalnych | 200 | 6 |
| https://bip.um.bydgoszcz.pl/artykul/1257/848 | 200 | 8 |
| https://bip.um.bydgoszcz.pl/artykul/1247/572/formularze-podatkowe | 200 | 10 |
| https://bip.um.bydgoszcz.pl/artykul/1372/4613/wzory-wnioskow | 200 | 0 |
| https://bip.um.bydgoszcz.pl/artykul/1482/9091/skargi-i-wnioski | 200 | 1 |
| https://bip.um.bydgoszcz.pl/artykul/1009/9251 | 200 | 0 | | https://bip.um.bydgoszcz.pl/artykul/<id>/<id>/<slug>, files `/attachments/download/<id>` | template pages for UDIP, taxes, complaints |

Robots (read first): um.bydgoszcz.pl disallows technical paths and query strings with `?id=`, `cHash`; bip.um.bydgoszcz.pl disallows `/*pdf*` and `/*szukaj*`. The crawler honours both; blocked URLs are recorded as unchecked.

## 2. Counts

| Metric | Value |
|---|---|
| Card pages crawled (HTTP 200) | 465 |
| Unique cards by code | 275 |
| Unique card attachments | 681 (pdf 334, docx 149, doc 118, rtf 77, jpg 1, xls 1, xlsx 1) |
| BIP template pages | 8 (27 attachment links) |
| Unique attachment URLs incl. BIP | 710 |
| Cards without any attachment | 15 |
| Cards with explicit "no online" text detected | 1 (UMB60; the regex is narrow) |
| Attachment URLs not OK | 4 (section 7) |

### Unique cards per department (a card may belong to several; 190 listing rows had no department)

| Department | Unique cards |
|---|---|
| Wydział Spraw Obywatelskich | 46 |
| Wydział Uprawnień Komunikacyjnych | 40 |
| Wydział Administracji Budowlanej | 27 |
| Wydział Mienia i Geodezji | 22 |
| Wydział Ochrony Środowiska | 22 |
| Urząd Stanu Cywilnego | 22 |
| Wydział Zieleni i Gospodarki Komunalnej | 16 |
| Wydział Podatków i Opłat Lokalnych | 15 |
| Wydział Edukacji i Sportu | 12 |
| Wydział Świadczeń Rodzinnych | 12 |
| Wydział Gospodarki Odpadami | 9 |
| Biuro ds. Zdrowia i Polityki Społecznej | 8 |
| Biuro Aktywności Społecznej | 5 |
| Biuro Komunikacji Społecznej | 5 |
| Wydział Księgowości | 5 |
| Biuro Promocji Miasta i Współpracy z Zagranicą | 2 |
| Wydział Windykacji | 2 |
| Wydział Organizacyjno-Administracyjny | 2 |
| Plastyk Miasta | 1 |
| Biuro Konserwatora Zabytków | 1 |
| Wydział Zarządzania Kryzysowego | 1 |

## 3. The 40 most relevant counter procedures with forms

Selection: procedures citizens most often handle at the counter (ID, residence registration, civil status, vehicle and driving licence, local tax, family benefits, waste). Links are direct file URLs with HTTP status; RODO clauses are filtered out.

| # | Card | Department | Procedure | Forms / direct URLs (non-RODO; ext, HTTP) |
|---|---|---|---|---|
| 1 | [UMB19](https://um.bydgoszcz.pl/sprawa/165/dowod-osobisty-zloz-wniosek/) | W. Spraw Obywatelskich | Dowód osobisty - złóż wniosek. | (no form; see card) |
| 2 | [UMB20](https://um.bydgoszcz.pl/sprawa/165/dowod-osobisty-dla-dziecka-lub-podopiecznego-zloz-wniosek/) | W. Spraw Obywatelskich | Dowód osobisty dla dziecka lub podopiecznego - złóż wniosek. | [pdf](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Dowodow_Osobistych/wniosek_o_wydanie_dowodu_osobistego-1_pomocniczy_obow._od_29.12.2023.pdf) 200 |
| 3 | [UMB16](https://um.bydgoszcz.pl/sprawa/165/odbior-dowodu-osobistego/) | W. Spraw Obywatelskich | Odbiór dowodu osobistego. | [doc](https://um.bydgoszcz.pl/ebokfile/wso/PELNOMOCNICTWO_SZCZEGOLNE_DO_ODBIORU_DOWODU_OSOBISTEGO.doc) 200 |
| 4 | [UMB11](https://um.bydgoszcz.pl/sprawa/165/utrata-uszkodzenie-twojego-dowodu-osobistego/) | W. Spraw Obywatelskich | Utrata / uszkodzenie Twojego dowodu osobistego. | (no form; see card) |
| 5 | [UMB53](https://um.bydgoszcz.pl/sprawa/162/numer-pesel/) | W. Spraw Obywatelskich | Numer PESEL | [pdf](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Nadanie_numeru_Pesel/Formularz_meld._-_Zgloszenie_pobytu_stalego.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Nadanie_numeru_Pesel/Formularz_meld._-_Zgloszenie_pobytu_czasowego_-.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Nadanie_numeru_Pesel/Wniosek_o_nadanie_numeru_PESEL.pdf) 200 |
| 6 | [UMB55](https://um.bydgoszcz.pl/sprawa/167/pobyt-staly-lub-czasowy/) | W. Spraw Obywatelskich | Pobyt stały lub czasowy | [doc](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Pobyt_staly_i_czasowy/oswiadczenie_wlasciciela.doc) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Pobyt_staly_i_czasowy/Formularz_meld._-_Zgloszenie_pobytu_stalego.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Pobyt_staly_i_czasowy/Formularz_meld._-_Zgloszenie_pobytu_czasowego_-.pdf) 200 |
| 7 | [UMB56](https://um.bydgoszcz.pl/sprawa/164/wymeldowanie-z-miejsca-pobytu-stalego-lub-czasowego/) | W. Spraw Obywatelskich | Wymeldowanie z miejsca pobytu stałego lub czasowego | [pdf](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Wymeldowanie_z_pobytu_stalego_lub_czasowego/Formularz_meld._-_Zgloszenie_wymeldowania_z_miejsca_pobytu_stalego.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Wymeldowanie_z_pobytu_stalego_lub_czasowego/Formularz_meld._-_Zgloszenie_wymeldowania_z_miejsca_pob._czasowego.pdf) 200<br>[doc](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Pelnomocnictwo.doc) 200 |
| 8 | [UMB58](https://um.bydgoszcz.pl/sprawa/162/zaswiadczenie-z-akt-ewidencji-ludnosci/) | W. Spraw Obywatelskich | Zaświadczenie z rejestru mieszkańców oraz rejestru PESEL | [docx](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Zaswiadczenie_z_akt_ewidencji_ludnosci/wniosek_o_wydanie_zaswiadczenia_z_rejestru_mieszkancow_oraz_rejestru_PESEL.docx) 200<br>[doc](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/wniosek_o_wydanie_wielojezycznego_formularza.doc) 200<br>[doc](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Pelnomocnictwo.doc) 200 |
| 9 | [UMB60](https://um.bydgoszcz.pl/sprawa/167/zameldowanie-na-pobyt-staly-lub-czasowy-w-drodze-postepowania-administracyjnego/) | W. Spraw Obywatelskich | Zameldowanie na pobyt stały lub czasowy w drodze postępowania adminis… | [doc](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Zameldowanie_na_pobyt_staly_lub_czasowy_w_drodze_postepowania_administracyjnego/wniosek_o_zameldowanie_w_drodze_postepowania_administracyjnego.doc) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Zameldowanie_na_pobyt_staly_lub_czasowy_w_drodze_postepowania_administracyjnego/Formularz_meld._-_Zgloszenie_pobytu_stalego.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Zameldowanie_na_pobyt_staly_lub_czasowy_w_drodze_postepowania_administracyjnego/Formularz_meld._-_Zgloszenie_pobytu_czasowego_-.pdf) 200 |
| 10 | [UMB62](https://um.bydgoszcz.pl/sprawa/162/dane-z-rejestru-mieszkancow-oraz-rejestru-pesel/) | W. Spraw Obywatelskich | Dane z rejestru mieszkańców oraz rejestru PESEL | [pdf](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Udostepnianie_danych/Wniosek_o_udostepnienie_danych_jednostkowych_z_resjestru_mieszkancow_i_rejestru_PESEL_2.pdf) 200 |
| 11 | [UMB61](https://um.bydgoszcz.pl/sprawa/171/wpis-do-stalego-rejestru-wyborcow/) | W. Spraw Obywatelskich | Wpis do stałego rejestru wyborców | [docx](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Wpis_do_stalego_rejestru_wyborcow/wniosek_o_ujecie_w_stalym_obwodzie_glosowania_2023_czesc_A.docx) 200<br>[docx](https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Wpis_do_stalego_rejestru_wyborcow/wniosek_o_ujecie_w_stalym_obwodzie_glosowania_czesc_B.docx) 200 |
| 12 | [UMB14](https://um.bydgoszcz.pl/sprawa/162/rejestr-danych-kontaktowych/) | W. Spraw Obywatelskich | Rejestr Danych Kontaktowych | [pdf](https://um.bydgoszcz.pl/ebokfile/wso/WNIOSEK_O_PRZEKAZANIE_DANYCH_KONTAKTOWYCH_O_AKTUALIZACJE_DANCYCH_KONTAKTOWYCH_O_USUNIECIE_DANYCH_KONTAKTOWYCH_Z__REJESTRU_DANYCH_KONTAKTOWYCH.PDF) 200 |
| 13 | [UMB17](https://um.bydgoszcz.pl/sprawa/165/kradziez-tozsamosci-nieuprawnione-wykorzystanie-danych-osobowych-twojego-dziecka-podopiecznego/) | W. Spraw Obywatelskich | Kradzież tożsamości / Nieuprawnione wykorzystanie danych osobowych Tw… | [doc](https://um.bydgoszcz.pl/ebokfile/wso/PELNOMOCNICTWO_SZCZEGOLNE_DO_ZGLOSZENIA_NIEUPRAWNIONEGO_WYKORZYSTANIA_DANYCH_OSOBOWYCH.doc) 200 |
| 14 | [UMB83](https://um.bydgoszcz.pl/sprawa/166/odpis-aktu-urodzenia/) | Urząd Stanu Cywilnego | Odpis aktu stanu cywilnego (urodzenia, małżeństwa, zgonu) | [rtf](https://um.bydgoszcz.pl/ebokfile/usc/wniosek_USC_poprawiony.rtf) 200 |
| 15 | [UMB124](https://um.bydgoszcz.pl/sprawa/166/zaswiadczenie-o-stanie-cywilnym/) | Urząd Stanu Cywilnego | Zaświadczenie o stanie cywilnym | [pdf](https://um.bydgoszcz.pl/ebokfile/usc/Wniosek_o_wydanie_zaswiadczenia_o_stanie_cywilnym_-_nowy.pdf) 200 |
| 16 | [UMB82](https://um.bydgoszcz.pl/sprawa/166/zaswiadczenie-do-zawarcia-zwiazku-malzenskiego-za-granica/) | Urząd Stanu Cywilnego | Zaświadczenie do zawarcia związku małżeńskiego za granicą | (no form; see card) |
| 17 | [UMB90](https://um.bydgoszcz.pl/sprawa/166/zgloszenie-urodzenie-dziecka/) | Urząd Stanu Cywilnego | Zgłoszenie urodzenia dziecka | [pdf](https://um.bydgoszcz.pl/ebokfile/usc/PELNOMOCNICTWO_WS._rejestracji_noworodka_ur_w_Bydgoszczy.pdf) 200 |
| 18 | [UMB77](https://um.bydgoszcz.pl/sprawa/163/zgloszenie-zgonu/) | Urząd Stanu Cywilnego | Zgłoszenie zgonu | (no form; see card) |
| 19 | [UMB40](https://um.bydgoszcz.pl/sprawa/166/zmiana-imienia-i-nazwiska/) | Urząd Stanu Cywilnego | Zmiana imienia i nazwiska | (no form; see card) |
| 20 | [UMB81](https://um.bydgoszcz.pl/sprawa/166/malzenstwo-cywilne-zawarcie-zwiazku-malzenskiego/) | Urząd Stanu Cywilnego | Małżeństwo cywilne - zawarcie związku małżeńskiego | (no form; see card) |
| 21 | [UMB202](https://um.bydgoszcz.pl/sprawa/173/czasowa-rejestracja-pojazdu/) | W. Uprawnień Komunikacyjnych | Czasowa rejestracja pojazdu | [pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Pelnomocnictwo1.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Rejestracja__czasowa_rejestracja__wyrejestrowanie_zbycie_UMB_202_208_213_217.pdf) 200<br>[rtf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Rejestracja__czasowa_rejestracja__wyrejestrowanie_zbycie_UMB_202_208_213_217.rtf) 200 |
| 22 | [UMB208](https://um.bydgoszcz.pl/sprawa/173/rejestracja-pojazdu/) | W. Uprawnień Komunikacyjnych | Rejestracja pojazdu | [pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Pelnomocnictwo1.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Rejestracja__czasowa_rejestracja__wyrejestrowanie_zbycie_UMB_202_208_213_217.pdf) 200<br>[rtf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Rejestracja__czasowa_rejestracja__wyrejestrowanie_zbycie_UMB_202_208_213_217.rtf) 200 |
| 23 | [UMB213](https://um.bydgoszcz.pl/sprawa/173/wyrejestrowanie-pojazdu/) | W. Uprawnień Komunikacyjnych | Wyrejestrowanie pojazdu | [pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Pelnomocnictwo1.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Rejestracja__czasowa_rejestracja__wyrejestrowanie_zbycie_UMB_202_208_213_217.pdf) 200<br>[rtf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Rejestracja__czasowa_rejestracja__wyrejestrowanie_zbycie_UMB_202_208_213_217.rtf) 200 |
| 24 | [UMB217](https://um.bydgoszcz.pl/sprawa/173/zawiadomienie-o-nabyciu-lub-zbyciu-pojazdu/) | W. Uprawnień Komunikacyjnych | Zawiadomienie o zbyciu pojazdu | [pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Pelnomocnictwo1.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Zawiadomienie_o_zbyciu_pojazdu_UMB_217-.pdf) 200<br>[rtf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Zawiadomienie_o_zbyciu_pojazdu_UMB_217.rtf) 200 |
| 25 | [UMB209](https://um.bydgoszcz.pl/sprawa/173/wtornik-lub-wymiana-dowodu-rejestracyjnego/) | W. Uprawnień Komunikacyjnych | Wtórnik lub wymiana dowodu rejestracyjnego | [pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Pelnomocnictwo1.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Wtornik_tablicy__dowodu_UMB_209_210.pdf) 200<br>[rtf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Wtornik_tablicy__dowodu_UMB_209_210.rtf) 200 |
| 26 | [UMB210](https://um.bydgoszcz.pl/sprawa/173/tablice-rejestracyjne-wydanie-zmiana-wtornik-tablica-na-bagaznik/) | W. Uprawnień Komunikacyjnych | Tablice rejestracyjne: wydanie, zmiana, wtórnik, tablica na bagażnik | [pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Pelnomocnictwo1.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Wtornik_tablicy__dowodu_UMB_209_210.pdf) 200<br>[rtf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Wtornik_tablicy__dowodu_UMB_209_210.rtf) 200 |
| 27 | [UMB180](https://um.bydgoszcz.pl/sprawa/172/prawo-jazdy-i-pozwolenie-na-kierowanie-tramwajem/) | W. Uprawnień Komunikacyjnych | Prawo jazdy i pozwolenie na kierowanie tramwajem /pkk - profil kandyd… | [pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKIII/zalacznik_WUK-III_wniosek_prawo_jazdy_2025.pdf) 200 |
| 28 | [UMB181](https://um.bydgoszcz.pl/sprawa/172/wtorniki-praw-jazdy-i-pozwolen-na-kierowanie-tramwajem-wymiana-z-powodu-zmian-w-dokumencie/) | W. Uprawnień Komunikacyjnych | Wtórniki praw jazdy i pozwoleń na kierowanie tramwajem. Wymiana z pow… | [pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKIII/pazdzernik_2022/zalacznik_WUK.III_osw_o_utracie.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKIII/zalacznik_WUK-III_wniosek_prawo_jazdy_2025.pdf) 200 |
| 29 | [UMB183](https://um.bydgoszcz.pl/sprawa/172/wymiana-zagranicznego-prawa-jazdy-na-polskie/) | W. Uprawnień Komunikacyjnych | Wymiana zagranicznego prawa jazdy na polskie | [pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKIII/zalacznik_WUK-III_wniosek_prawo_jazdy_2025.pdf) 200 |
| 30 | [UMB184](https://um.bydgoszcz.pl/sprawa/172/zwrot-zatrzymanego-prawa-jazdy-lub-pozwolenia-na-kierowanie-tramwajem/) | W. Uprawnień Komunikacyjnych | Zwrot zatrzymanego prawa jazdy lub pozwolenia na kierowanie tramwajem | [pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKIII/zalacznik_WUK-III_wniosek_prawo_jazdy_2025.pdf) 200 |
| 31 | [UMB281](https://um.bydgoszcz.pl/sprawa/172/karta-kwalifikacji-kierowcy-kkk/) | W. Uprawnień Komunikacyjnych | Karta kwalifikacji kierowcy /KKK/ | [pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKIII/pazdzernik_2022/zalacznik_WUK.III_kkk.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wuk/WUKIII/zalacznik_WUK.III.1-7_Wniosek_o_wydanie_karty_kwalifikacji_kierowcy__wydrukowac_dwustronnie_na_1_kartce_A4_.pdf) 200 |
| 32 | [UMB142](https://um.bydgoszcz.pl/sprawa/155/podatek-od-nieruchomosci-nabycie/) | W. Podatków i Opłat Lokalnych | Podatek od nieruchomości (nabycie) | [pdf](https://um.bydgoszcz.pl/ebokfile/wpl/_Podatek_od_nieruchomosci_2021___IN-1_wersja_2_.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wpl/ZIN-1__1__-_Dane_o_przedmiotach_opodatkowania_podlegajacych_opodatkowaniu__wersja_interaktywna_.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wpl/ZIN-2__1__-_Dane_o_przedmiotach_opodatkowania_zwolnionych_z_opodatkowania__wersja_interaktywna_.pdf) 200 |
| 33 | [UMB143](https://um.bydgoszcz.pl/sprawa/155/podatek-od-nieruchomosci-korekta/) | W. Podatków i Opłat Lokalnych | Podatek od nieruchomości (korekta) | [pdf](https://um.bydgoszcz.pl/ebokfile/wpl/_Podatek_od_nieruchomosci_2021___IN-1_wersja_2_.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wpl/ZIN-1__1__-_Dane_o_przedmiotach_opodatkowania_podlegajacych_opodatkowaniu__wersja_interaktywna_.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wpl/ZIN-2__1__-_Dane_o_przedmiotach_opodatkowania_zwolnionych_z_opodatkowania__wersja_interaktywna_.pdf) 200 |
| 34 | [UMB129](https://um.bydgoszcz.pl/sprawa/155/podatek-rolny-lesny-nabycie/) | W. Podatków i Opłat Lokalnych | Podatek rolny / leśny (nabycie) | [pdf](https://um.bydgoszcz.pl/ebokfile/wpl/_WPL__IR-1__1_.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wpl/_WPL__ZIR-1__1_.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wpl/_WPL__ZIR-2__1_.pdf) 200 |
| 35 | [UMB139](https://um.bydgoszcz.pl/sprawa/155/podatek-od-srodkow-transportowych-nabycie/) | W. Podatków i Opłat Lokalnych | Podatek od środków transportowych (nabycie) | [pdf](https://um.bydgoszcz.pl/ebokfile/wpl/_Podatek_od_srodkow_transportowych_2021___DT-1_.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wpl/DT-1A__6__-_Zalacznik_do_deklaracji_DT-1_na_podatek_od_srodkow_transportowych__wersja_interaktywna_.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wpl/UPL-1P_1c.pdf) 200 |
| 36 | [UMB156](https://um.bydgoszcz.pl/sprawa/211/dodatek-mieszkaniowy/) | W. Świadczeń Rodzinnych | Dodatek mieszkaniowy | [pdf](https://um.bydgoszcz.pl/ebokfile/wsr/Wniosek_o_przyznanie_dod._mieszk_zal_nr1_2021.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wsr/zalacznik_DM.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/fileadmin/multimedia/swiadczenia/informacje_o_lokalu_2024.pdf) 200 |
| 37 | [UMB166](https://um.bydgoszcz.pl/sprawa/211/zasilek-rodzinny-oraz-dodatki-do-zasilku-rodzinnego/) | W. Świadczeń Rodzinnych | Zasiłek rodzinny oraz dodatki do zasiłku rodzinnego | [pdf](https://um.bydgoszcz.pl/ebokfile/wsr/Wniosek_ZR_-_2025_2026.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/fileadmin/multimedia/swiadczenia/zr_2026_2027_drukarnia.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/fileadmin/multimedia/swiadczenia/oswiadczenie_urlop_wychowawczy.pdf) 200 |
| 38 | [UMB162](https://um.bydgoszcz.pl/sprawa/211/swiadczenie-rodzicielskie/) | W. Świadczeń Rodzinnych | Świadczenie rodzicielskie | [pdf](https://um.bydgoszcz.pl/fileadmin/multimedia/swiadczenia/wniosek_swiadczenie_rodzicielskie.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/fileadmin/multimedia/swiadczenia/WZOR_ZASWIADCZENIA_O_POBYCIE_DZIECKA_W_SZPITALU_PO_PORODZIE.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/ebokfile/wsr/WW_Swiadczenie_rodzicielskie_-_wniosek.pdf) 200 |
| 39 | [UMB158](https://um.bydgoszcz.pl/sprawa/211/stypendium-szkolne/) | W. Świadczeń Rodzinnych | Stypendium szkolne | [pdf](https://um.bydgoszcz.pl/fileadmin/multimedia/swiadczenia/stypendium_szkolne-_wniosek_1_.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/fileadmin/multimedia/WSPOLNE/2019_swiadczenia/art._75_kpa_21.04.2026.pdf) 200<br>[pdf](https://um.bydgoszcz.pl/fileadmin/multimedia/swiadczenia/stypendium_szkolne-_CHMURKI.pdf) 200 |
| 40 | [UMB204](https://um.bydgoszcz.pl/sprawa/157/oplata-za-odpady-komunalne-nieruchomosci-zamieszkale/) | W. Gospodarki Odpadami | Opłata za odpady komunalne – nieruchomości zamieszkałe | (no form; see card) |

## 4. BIP template pages (UDIP and others)

| BIP page | HTTP | Attachments |
|---|---|---|
| https://bip.um.bydgoszcz.pl/artykul/1052/2/udostepnianie-informacji-publicznej | 200 | 2 |
| https://bip.um.bydgoszcz.pl/artykul/1053/1/ponowne-wykorzystanie-informacji-publicznej | 200 | 0 |
| https://bip.um.bydgoszcz.pl/artykul/1009/574/wnioski-w-sprawach-podatkow-i-oplat-lokalnych | 200 | 6 |
| https://bip.um.bydgoszcz.pl/artykul/1257/848 | 200 | 8 |
| https://bip.um.bydgoszcz.pl/artykul/1247/572/formularze-podatkowe | 200 | 10 |
| https://bip.um.bydgoszcz.pl/artykul/1372/4613/wzory-wnioskow | 200 | 0 |
| https://bip.um.bydgoszcz.pl/artykul/1482/9091/skargi-i-wnioski | 200 | 1 |
| https://bip.um.bydgoszcz.pl/artykul/1009/9251 | 200 | 0 |

`/artykul/1052/2` (udostępnianie informacji publicznej) has 2 attachment links, `/artykul/1053/1` (ponowne wykorzystanie) none, `/artykul/1372/4613` (wzory wniosków) none in static HTML (likely an index of sub-pages). A UDIP request has no mandatory form; see `research/02-udip-law-process-taxonomy.md`.

## 5. Procedures with no downloadable form (online-only or information-only)

"Where described" lists external links found on the card (the generic ePUAP portal link is omitted); for waste-fee cards the online declaration goes through the ePUAP catalogue.

| Card | Department | Title | Where the online procedure is described |
|---|---|---|---|
| [UMB270](https://um.bydgoszcz.pl/sprawa/200/budowlane-konsultacje/) | W. Administracji Budowlanej | Budowlane konsultacje i opinie urbanistyczne | card text only |
| [UMB69](https://um.bydgoszcz.pl/sprawa/170/bydgoska-koperta-zycia-dla-seniora/) | Biuro Aktywności Społecznej | Bydgoska Koperta Życia dla seniora - skuteczna pomoc medycz… | card text only |
| [UMB265](https://um.bydgoszcz.pl/sprawa/227/bydgoski-budzet-obywatelski/) | Biuro Komunikacji Społecznej | Bydgoski Budżet Obywatelski | card text only |
| [UMB257](https://um.bydgoszcz.pl/sprawa/205/deklaracja-dotyczaca-zrodel-ciepla-i-zrodel-spalania-paliw-ceeb/) | W. Ochrony Środowiska | Deklaracja dotycząca źródeł ciepła i źródeł spalania paliw … | https://zone.gunb.gov.pl/ |
| [UMB179](https://um.bydgoszcz.pl/sprawa/172/informacje-o-podstawach-prawnych-wydzialu-uprawnien-komunikacyjnych/) | W. Uprawnień Komunikacyjnych | Informacje o podstawach prawnych Wydziału Uprawnień Komunik… | card text only |
| [UMB271](https://um.bydgoszcz.pl/sprawa/158/inicjatywa-lokalna-program-2575/) | W. Administracji Budowlanej | Inicjatywa lokalna - Program 25/75 | https://www.bydgoszcz.pl/dla-inwestora/inicjatywy-obywatelskie-program-2575/ |
| [UMB71](https://um.bydgoszcz.pl/sprawa/162/obsluga-centralnej-ewidencji-i-informacji-o-dzialalnosci-gospodarczej/) | W. Spraw Obywatelskich | Obsługa Centralnej Ewidencji i Informacji o Działalności Go… | http://www.biznes.gov.pl; https://www.biznes.gov.pl/pl/portal/0073; https://logowanie.biznes.gov.pl/login/realms/logowanie/protocol/openid-c |
| [UMB205](https://um.bydgoszcz.pl/sprawa/157/oplata-za-odpady-komunalne-nieruchomosci-niezamieszkale/) | W. Gospodarki Odpadami | Opłata za odpady komunalne – nieruchomości niezamieszkałe | https://epuap.gov.pl/wps/portal/strefa-klienta/katalog-spraw/opis-uslugi/deklaracje-o-wysokosci-oplaty-za-gospodarowanie-odpadami-komunalnym |
| [UMB95](https://um.bydgoszcz.pl/sprawa/157/oplata-za-odpady-komunalne-nieruchomosci-wykorzystywane-na-cele-rekreacyjno-wypoczynkowe/) | W. Gospodarki Odpadami | Opłata za odpady komunalne – nieruchomości wykorzystywane n… | https://epuap.gov.pl/wps/portal/strefa-klienta/katalog-spraw/opis-uslugi/deklaracje-o-wysokosci-oplaty-za-gospodarowanie-odpadami-komunalnym |
| [UMB204](https://um.bydgoszcz.pl/sprawa/157/oplata-za-odpady-komunalne-nieruchomosci-zamieszkale/) | W. Gospodarki Odpadami | Opłata za odpady komunalne – nieruchomości zamieszkałe | https://epuap.gov.pl/wps/portal/strefa-klienta/katalog-spraw/opis-uslugi/deklaracje-o-wysokosci-oplaty-za-gospodarowanie-odpadami-komunalnym |
| [UMB232](https://um.bydgoszcz.pl/sprawa/175/oplaty-referat-nadzoru-komunikacyjnego/) | W. Uprawnień Komunikacyjnych | Opłaty Referat Nadzoru Komunikacyjnego | card text only |
| [UMB253](https://um.bydgoszcz.pl/sprawa/172/oplaty-referat-praw-jazdy/) | W. Uprawnień Komunikacyjnych | Opłaty Referat Praw Jazdy | card text only |
| [UMB250](https://um.bydgoszcz.pl/sprawa/173/oplaty-referat-rejestracji-pojazdow/) | W. Uprawnień Komunikacyjnych | Opłaty Referat Rejestracji Pojazdów | card text only |
| [UMB91](https://um.bydgoszcz.pl/sprawa/157/reklamacja-uslugi-odbioru-odpadow-komunalnych-z-nieruchomosci-reklamacja-odbioru-w-pszok/) | W. Gospodarki Odpadami | Reklamacja usługi odbioru odpadów komunalnych z nieruchomoś… | card text only |
| [UMB304](https://um.bydgoszcz.pl/sprawa/175/usuwanie-i-przechowywanie-pojazdow-usunietych-z-drogi-w-trybie-art-130a-ustawy-prawo-o-ruchu-drogowym/) | W. Uprawnień Komunikacyjnych | Usuwanie i przechowywanie pojazdów usuniętych z drogi w try… | card text only |

## 6. Direct URLs from the previous research (status of 2026-11-21)

| URL (tail) | HTTP | Content-Type | Bytes |
|---|---|---|---|
| bip.um.bydgoszcz.pl/attachments/download/30900 | 200 | pdf | 399215 |
| bip.um.bydgoszcz.pl/attachments/download/30899 | 200 | vnd.openxmlformats-officedocum | 29401 |
| www.gov.pl/attachment/5952a029-e82c-4f08-812a-b065a0392722 | 200 | pdf | 593988 |
| um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Pobyt_staly_i_czasowy/Formularz_meld._- | 200 | pdf | 228401 |
| um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Pobyt_staly_i_czasowy/Formularz_meld._- | 200 | pdf | 224008 |
| um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Pobyt_staly_i_czasowy/oswiadczenie_wlas | 200 | msword | 23040 |
| um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Pelnomocnictwo.doc | 200 | msword | 36864 |
| um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Zaswiadczenie_z_akt_ewidencji_ludnosci/ | 200 | vnd.openxmlformats-officedocum | 16618 |
| um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/wniosek_o_wydanie_wielojezycznego_formu | 200 | msword | 32768 |
| um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Zameldowanie_na_pobyt_staly_lub_czasowy | 200 | msword | 30720 |
| um.bydgoszcz.pl/ebokfile/usc/wniosek_USC_poprawiony.rtf | 200 | rtf | 104897 |
| um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Rejestracja__czasowa_rejestracja__wyrejestr | 200 | pdf | 210031 |
| um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Pelnomocnictwo1.pdf | 200 | pdf | 201384 |
| um.bydgoszcz.pl/ebokfile/wuk/WUKI/2026/UMB173_WNIOSEK_-LICENCJA_POSREDNICTWO.pdf | 200 | pdf | 548769 |
| um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Zawiadomienie_o_zbyciu_pojazdu_UMB_217-.pdf | 200 | pdf | 463484 |
| bip.um.bydgoszcz.pl/attachments/download/1747 | 200 | pdf | 420953 |
| bip.um.bydgoszcz.pl/attachments/download/1013 | 200 | pdf | 419828 |
| bip.um.bydgoszcz.pl/attachments/download/1749 | 200 | pdf | 434716 |
| bip.um.bydgoszcz.pl/attachments/download/1012 | 200 | pdf | 33384 |
| bip.um.bydgoszcz.pl/attachments/download/1748 | 200 | pdf | 476421 |
| bip.um.bydgoszcz.pl/attachments/download/1014 | 200 | pdf | 35386 |
| bip.um.bydgoszcz.pl/attachments/download/1838 | 200 | pdf | 723661 |
| bip.um.bydgoszcz.pl/attachments/download/27416 | 200 | pdf | 744463 |
| bip.um.bydgoszcz.pl/attachments/download/1834 | 200 | pdf | 239458 |
| bip.um.bydgoszcz.pl/attachments/download/1837 | 200 | pdf | 586151 |
| bip.um.bydgoszcz.pl/attachments/download/1833 | 200 | pdf | 607185 |
| bip.um.bydgoszcz.pl/attachments/download/1832 | 200 | pdf | 85747 |
| bip.um.bydgoszcz.pl/attachments/download/1836 | 200 | pdf | 280682 |
| bip.um.bydgoszcz.pl/attachments/download/1835 | 200 | pdf | 857254 |
| um.bydgoszcz.pl/ebokfile/wpl/ZIN-1__1__-_Dane_o_przedmiotach_opodatkowania_podlegajacych_opodat | 200 | pdf | 68221 |
| um.bydgoszcz.pl/ebokfile/wpl/DN-1__1__-_Deklaracja_na_podatek_od_nieruchomosci__wersja_do_druku | 200 | pdf | 75269 |
| um.bydgoszcz.pl/ebokfile/wso/Referat_Zezwolen_Alkoholowych/wniosek_oswiadczenie_o_wartosci_sprz | 200 | pdf | 165578 |
| www.bydgoszcz.pl/fileadmin/multimedia/swiadczenia/Karta_Uslugi_od_VI_2026r__1_.pdf | 200 | pdf | 246008 |

All 33 return HTTP 200 and a plausible content type. `attachments/download/30899` is DOCX, `30900` PDF. `Formularz_meld._-_Zgloszenie_pobytu_stalego.pdf` is published both under `/Pobyt_staly_i_czasowy/` and under the UMB60 folder (same size, 228401 bytes).

## 7. Broken or unchecked links

| URL | HTTP / error | Seen on card |
|---|---|---|
| https://archiwumbip.um.bydgoszcz.pl/binary/237-2011_tcm30-98416.pdf | None ConnectionError: HTTPSConnectionPool(host='archiwu | UMB263 |
| https://bip.um.bydgoszcz.pl/binary/Pelnomocnictwo_tcm30-7703.pdf | None blocked by robots.txt | UMB173 |
| https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20250001338/T/D20251338L.pdf | None blocked by robots.txt | UMB300 |
| https://um.bydgoszcz.pl/ebokfile/wab/PB-5-_oswiadczenie_o_posiadanym_prawie_do_dysponowania_nieruchomoscia_na_cele_budowlane.doc | 404  | UMB272 |

## 8. Verdicts on the previous research

| Claim | Verdict | Evidence and correction |
|---|---|---|
| C10 no paper ID application since 29.12.2023 | PARTLY | Card UMB19 (https://um.bydgoszcz.pl/sprawa/165/dowod-osobisty-zloz-wniosek/): "Od dnia 29.12.2023 roku nie złożysz już papierowego wniosku o wydanie dowodu osobistego. Wniosek jest generowany automatycznie na podstawie danych pobranych z rejestrów państwowych." CORRECTION: the gov.pl online path exists for adults too, followed by a visit within 30 days for fingerprints and signature specimen; the child exception was not checked on UMB20. |
| C12 tax department and ePUAP from 1.1.2026 | PARTLY | BIP https://bip.um.bydgoszcz.pl/artykul/1009/9251 confirms: general submissions via ePUAP have no legal effect from 1 Jan 2026; still allowed by ePUAP: IN-1, DN-1, IR-1, DR-1, IL-1, DL-1, DT-1; use the ADE of the tax authority; decisions are no longer sent to ePUAP. CORRECTIONS: the article does not mention ordinary e-mail; `AE:PL-91453-53730-WDRHC-24` appears in the site-wide contact block (UM Bydgoszcz in general) and the article only says "ADE organu podatkowego"; confirm whether the tax department has a separate address. |
| C13 UMB60 cannot be handled online, gov.pl has an online path | PARTLY | Card UMB60 (https://um.bydgoszcz.pl/sprawa/167/zameldowanie-na-pobyt-staly-lub-czasowy-w-drodze-postepowania-administracyjnego/): "Uwaga! Sprawy nie załatwisz przez Internet." (CONFIRMED). The gov.pl online path for this procedure was NOT checked (UNVERIFIED). Our own `online_handling` flag wrongly said true for UMB60 before the patch. |
| C14 double-sided printing at Wydział Uprawnień Komunikacyjnych | CONFIRMED | UMB184 zwrot zatrzymanego prawa jazdy: "proszę wniosek drukować dwustronnie przy ustawieniu jak najmniejszego marginesu na drukarce laserowej o minimalnej rozdzielczości 600" (https://um.bydgoszcz.pl/sprawa/172/zwrot-zatrzymanego-prawa-jazdy-lub-pozwolenia-na-kierowanie-tramwajem/); UMB281 (KKK) attachment file name: "wydrukowac dwustronnie na 1 kartce A4". |
| C15 fees | PARTLY | UMB83 (https://um.bydgoszcz.pl/sprawa/166/odpis-aktu-urodzenia/): odpis skrócony 22 zł (also multilingual paper), odpis zupełny 33 zł, pełnomocnictwo 17 zł: CONFIRMED. UMB58 (zaświadczenie z rejestru mieszkańców i PESEL): 17 zł; pełnomocnictwo 17 zł, exempt for spouse, ascendants, descendants, siblings: CONFIRMED. CORRECTION: fees differ per card, e.g. zaświadczenie o stanie cywilnym (UMB124) 38 zł. Never hard-code a fee; read it from the card or the current stamp-duty law. |

## 9. Re-running the crawler

```
python tools/crawl_bydgoszcz_forms.py                   # full crawl, about 11 minutes, writes data/forms-catalog.json and .csv
python tools/crawl_bydgoszcz_forms.py --max-cards 20    # quick test
python tools/crawl_bydgoszcz_forms.py --postprocess     # re-read the existing JSON, dedup and rewrite outputs
python tools/crawl_bydgoszcz_forms.py --download DIR    # optional local file cache; binaries must stay out of git
```
Politeness: robots.txt first, at most 2 requests/s, timeout 20 s, 2 retries, User-Agent `Mozilla/5.0 (compatible; forms-catalog-research)`. Fees, legal basis and department text pass through `mask_accounts()`, which replaces any 26-digit bank account (NRB, optional PL prefix, any spacing) with `[numer rachunku: patrz aktualna karta uslugi]`; tested on sample strings only (no re-crawl after the patch).

## 10. Limitations

- `online_handling` is a keyword heuristic and over-reports; `fees` is empty for most cards (the section extractor is narrow); `last_update` is rarely present.
- 190 listing rows had no department in the index; the department is taken from other occurrences of the same code, otherwise "(none listed)".
- Attachments were checked by HEAD/GET status only; file contents were not parsed, so field structure and template versions are unknown.
- Two URLs on bip.um.bydgoszcz.pl and one on isap.sejm.gov.pl could not be checked (robots.txt).
- The portal changes: re-run before relying on a URL; file names carry year stamps (e.g. `.../WUKI/2026/UMB173_...`).

## Open questions and what could not be verified

- Whether the tax department has its own ADE address (C12).
- The gov.pl online path for the administrative meldunek procedure (C13).
- The child exception for dowód osobisty (C10): card UMB20 not read.
- Whether the Word/PDF templates carry fillable fields.

## Sources

- https://um.bydgoszcz.pl/ (all `/sprawa/` cards, see `data/forms-catalog.json`)
- https://um.bydgoszcz.pl/sprawa/165/dowod-osobisty-zloz-wniosek/
- https://um.bydgoszcz.pl/sprawa/166/odpis-aktu-urodzenia/
- https://um.bydgoszcz.pl/sprawa/162/zaswiadczenie-z-akt-ewidencji-ludnosci/
- https://um.bydgoszcz.pl/sprawa/167/zameldowanie-na-pobyt-staly-lub-czasowy-w-drodze-postepowania-administracyjnego/
- https://um.bydgoszcz.pl/sprawa/172/zwrot-zatrzymanego-prawa-jazdy-lub-pozwolenia-na-kierowanie-tramwajem/
- https://um.bydgoszcz.pl/sprawa/172/karta-kwalifikacji-kierowcy-kkk/
- https://bip.um.bydgoszcz.pl/artykul/1009/9251/
- https://bip.um.bydgoszcz.pl/artykul/1052/2/udostepnianie-informacji-publicznej
