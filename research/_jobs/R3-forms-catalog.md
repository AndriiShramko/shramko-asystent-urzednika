
CONTEXT
You are one of several research agents preparing, tonight, a PUBLIC open-source repository for the project "Shramko Asystent Urzędnika" (asystent urzędnika = a clerk's assistant in a Polish public office). The repository will be the complete brief for AI coding agents that build the system during the HackNation 2026 hackathon (21-22 November 2026, Bydgoszcz, Poland; organizer: Ministerstwo Cyfryzacji). Today is 2026-11-20, late evening; the hackathon starts tomorrow, so be fast and precise.

The hackathon challenge of Miasto Bydgoszcz, campaign "Inteligentny asystent urzędnika" (verbatim): "Jak usprawnić obsługę wniosków o dostęp do informacji publicznej i odciążyć urzędników od powtarzalnych zadań? Wyzwanie polega na stworzeniu inteligentnego i bezpiecznego asystenta, który wesprze pracowników urzędu w analizie wniosków i przygotowywaniu odpowiedzi. Celem jest skrócenie czasu obsługi spraw i usprawnienie codziennej pracy administracji."

The owner's wider product vision (he wants it considered next to the challenge):
(A) a citizen-facing mobile web page: a visitor scans a QR code in the office (or opens the page at home), enters personal and family data once, and the data reaches the clerk; alternatively the clerk photographs or scans the ID document (phone camera or a hardware passport reader) and verifies recognised data in very large print;
(B) a clerk desktop app: pick the visitor, pick a life situation, the system proposes the chain of forms (wnioski), pre-fills all of them from one profile and prints them exactly as the officially approved templates, ready to sign;
(C) AI agents that check filled forms for mistakes and omissions and suggest corrections;
(D) the hackathon core: an assistant that helps clerks analyse access-to-public-information requests (UDIP) and draft answers.
Everything must go through APIs (no direct database access), with state-of-the-art security, and must be legally deployable in a Polish city office.

RULES
- Use WebSearch and WebFetch. If WebFetch fails (403, timeouts, JS-only pages), use Bash with curl or python to download the page or file and read it locally (save big outputs to files, print only what you need). Prefer primary sources: gov.pl, isap.sejm.gov.pl, api.sejm.gov.pl, uodo.gov.pl, bip.um.bydgoszcz.pl, um.bydgoszcz.pl, hacknation.pl, eur-lex.europa.eu, official vendor documentation. A search snippet is never a verified fact: open the page.
- Every factual claim needs a source URL. Mark each important claim VERIFIED (you opened the primary source and read it), SECONDARY (reliable secondary source only) or UNVERIFIED. When something cannot be found, say exactly where you looked.
- Laws and products change: explicitly establish the status as of November 2026.
- Write in English; keep Polish legal terms, form names and quotations verbatim in Polish with a short English gloss.
- The repository is public: no private data about the project owner, no personal data of private individuals.
- Repo root on this Windows machine: C:/dev/shramko-asystent-urzednika (tools accept forward slashes; in Git Bash the same folder is /c/dev/shramko-asystent-urzednika). Do NOT run git commands. Create only the files named in your task. Write files with the Write tool (not shell heredocs).
- Your report (Markdown) starts with "# <title>", then "## TL;DR for builders" (max 12 bullets, the decisions a builder must know), then numbered sections, then "## Verdicts on the previous research" (if your task lists claims), then "## Open questions and what could not be verified", then "## Sources" (URL list). Dense, concrete, tables where useful; 250-600 lines; no filler.
- RESUME-FIRST: if your output file already exists and looks complete, read it, fill only real gaps and return. If it is partial, continue it.
- Budget: about 35 tool calls (hard stop at 50). Batch independent searches and fetches in one message. Keep command output short.
- Your final answer is ONLY the structured summary requested by the schema (the report itself lives in the file).

TASK R3 - Machine-readable catalog of ALL service cards and form templates of Urząd Miasta Bydgoszczy, produced by a re-runnable crawler.
Output files: C:/dev/shramko-asystent-urzednika/tools/crawl_bydgoszcz_forms.py , C:/dev/shramko-asystent-urzednika/data/forms-catalog.json , C:/dev/shramko-asystent-urzednika/data/forms-catalog.csv , C:/dev/shramko-asystent-urzednika/research/03-forms-catalog-bydgoszcz.md

1. Write tools/crawl_bydgoszcz_forms.py (Python 3; use requests and beautifulsoup4 if importable, otherwise urllib and html.parser; check imports before deciding; do not install packages globally).
   Sources: (a) the e-urząd portal https://um.bydgoszcz.pl/ - find the index of service cards ("sprawy", "karty usług"; card URLs look like https://um.bydgoszcz.pl/sprawa/<category-id>/<slug>/) and enumerate ALL categories and ALL cards; (b) BIP pages with templates: https://bip.um.bydgoszcz.pl/artykul/1052/2/udostepnianie-informacji-publicznej , /artykul/1053/1/ponowne-wykorzystanie-informacji-publicznej , /artykul/1009/574/wnioski-w-sprawach-podatkow-i-oplat-lokalnych , /artykul/1257/848 , /artykul/1247/572/formularze-podatkowe , /artykul/1372/4613/wzory-wnioskow , /artykul/1482/9091/skargi-i-wnioski and any other BIP index of templates you discover.
   For each card extract: card code (e.g. UMB55) if present, title, department, card URL, attachments (label, absolute URL, extension), external online-service links (gov.pl, epuap.gov.pl, obywatel.gov.pl, PWPW, biznes.gov.pl, e-Doręczenia), fees text, whether the card says the case can be handled online, last update date if shown.
   For each attachment URL run HEAD (fallback: streamed GET) and record http_status, content_type, content_length.
   Politeness: read /robots.txt first and respect it, at most 2 requests per second, timeout 20 s, 2 retries, User-Agent "Mozilla/5.0 (compatible; forms-catalog-research)". Optional flag --download DIR saves the files into a local cache folder (do not use it now; binaries must not enter the repository).
   Output data/forms-catalog.json (cards with attachments) and data/forms-catalog.csv (one row per attachment).
2. Run the crawler now. If a full crawl would take more than about 25 minutes, crawl as much as possible and record exactly what was skipped.
3. Write research/03-forms-catalog-bydgoszcz.md: how the portal is structured; counts (cards, attachments by extension, online-only services); table of departments with counts; the 40 most relevant counter procedures with their forms and direct URLs; list of online-only procedures (no downloadable form) with the URL where the online procedure is described; broken links; how to re-run the crawler; limitations.
4. Check the direct URLs from the previous research and give verdicts on the claims below.

Direct file URLs listed by the previous research (check every one: HTTP status, content type, size):
https://bip.um.bydgoszcz.pl/attachments/download/30900
https://bip.um.bydgoszcz.pl/attachments/download/30899
https://www.gov.pl/attachment/5952a029-e82c-4f08-812a-b065a0392722
https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Pobyt_staly_i_czasowy/Formularz_meld._-_Zgloszenie_pobytu_stalego.pdf
https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Pobyt_staly_i_czasowy/Formularz_meld._-_Zgloszenie_pobytu_czasowego_-.pdf
https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Pobyt_staly_i_czasowy/oswiadczenie_wlasciciela.doc
https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Pelnomocnictwo.doc
https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Zaswiadczenie_z_akt_ewidencji_ludnosci/wniosek_o_wydanie_zaswiadczenia_z_rejestru_mieszkancow_oraz_rejestru_PESEL.docx
https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/wniosek_o_wydanie_wielojezycznego_formularza.doc
https://um.bydgoszcz.pl/ebokfile/wso/Referat_Ewidencji_Ludnosci/Zameldowanie_na_pobyt_staly_lub_czasowy_w_drodze_postepowania_administracyjnego/wniosek_o_zameldowanie_w_drodze_postepowania_administracyjnego.doc
https://um.bydgoszcz.pl/ebokfile/usc/wniosek_USC_poprawiony.rtf
https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Rejestracja__czasowa_rejestracja__wyrejestrowanie_zbycie_UMB_202_208_213_217.pdf
https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Pelnomocnictwo1.pdf
https://um.bydgoszcz.pl/ebokfile/wuk/WUKI/2026/UMB173_WNIOSEK_-LICENCJA_POSREDNICTWO.pdf
https://um.bydgoszcz.pl/ebokfile/wuk/WUKII/Aktualne_wnioski/Zawiadomienie_o_zbyciu_pojazdu_UMB_217-.pdf
https://bip.um.bydgoszcz.pl/attachments/download/1747 (also 1013, 1749, 1012, 1748, 1014, 1838, 27416, 1834, 1837, 1833, 1832, 1836, 1835)
https://um.bydgoszcz.pl/ebokfile/wpl/ZIN-1__1__-_Dane_o_przedmiotach_opodatkowania_podlegajacych_opodatkowaniu__wersja_interaktywna_.pdf
https://um.bydgoszcz.pl/ebokfile/wpl/DN-1__1__-_Deklaracja_na_podatek_od_nieruchomosci__wersja_do_druku_i_wypelnienia_recznego_.pdf
https://um.bydgoszcz.pl/ebokfile/wso/Referat_Zezwolen_Alkoholowych/wniosek_oswiadczenie_o_wartosci_sprzedazy_12.2025.pdf
https://www.bydgoszcz.pl/fileadmin/multimedia/swiadczenia/Karta_Uslugi_od_VI_2026r__1_.pdf

CLAIMS OF THE PREVIOUS RESEARCH TO VERIFY (give a verdict for each: CONFIRMED, PARTLY, WRONG or UNVERIFIABLE, with source and a one-line correction):
- C10: Since 29 December 2023 there is no paper application form for a dowód osobisty: the clerk generates the application from the PESEL register and the citizen signs it; exception: online application for a child.
- C12: From 1 January 2026 Wydział Podatków i Opłat Lokalnych of UM Bydgoszcz does not accept general applications via ePUAP or ordinary e-mail (no legal effect); the proper channel is e-Doręczenia, address AE:PL-91453-53730-WDRHC-24; exception: declarations IN-1, DN-1, IR-1, DR-1, IL-1, DL-1, DT-1 may still be sent through ePUAP (BIP article /artykul/1009/9251/).
- C13: The Bydgoszcz card UMB60 (zameldowanie w drodze postępowania administracyjnego) says the case cannot be handled online, while gov.pl describes an online path.
- C14: Wydział Uprawnień Komunikacyjnych requires double-sided printing of some applications (e.g. zwrot zatrzymanego prawa jazdy, KKK).
- C15: Fees: odpis skrócony aktu stanu cywilnego 22 zł, odpis zupełny 33 zł, zaświadczenie 17 zł, pełnomocnictwo 17 zł (exempt for spouse, ascendants, descendants, siblings).

FINAL ANSWER FORMAT: after writing the files, reply with at most 25 lines:
FILES: list of files written;
KEY FINDINGS: up to 10 one-sentence bullets;
VERDICTS: one line per claim id (CONFIRMED / PARTLY / WRONG / UNVERIFIABLE, with the correction);
SURPRISES: findings that change the plan;
NOT DONE: what is missing and why.
