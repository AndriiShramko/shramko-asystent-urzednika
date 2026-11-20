
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

TASK R3b - Anatomy of the most common forms: fields, repetition across forms, statutory status of templates, and what "print exactly like the approved template" requires.
Output files: C:/dev/shramko-asystent-urzednika/research/03b-form-anatomy-and-canonical-profile.md , C:/dev/shramko-asystent-urzednika/data/canonical-profile.schema.json (JSON Schema draft 2020-12) , C:/dev/shramko-asystent-urzednika/data/form-descriptor.example.json

Work on real files. Download into C:/dev/shramko-asystent-urzednika/data/forms-cache/ (this folder is git-ignored; never reference its binaries as repo content) about 12 forms covering different departments, starting from this list (verify each URL first; replace dead ones using the card pages on um.bydgoszcz.pl or bip.um.bydgoszcz.pl):

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

Analyse with Python (check which of pypdf, pdfplumber, PyMuPDF "fitz" are importable; you may run "python -m pip install --user pypdf pdfplumber pymupdf" if none is available; for DOC/RTF use LibreOffice "soffice --headless --convert-to pdf" if installed, otherwise extract text another way and say so).
1. Per form: pages, page size, whether it has AcroForm fields (names, types, comb or max length), XFA, embedded fonts, one-character boxes, checkboxes, signature places, instructions on the form about how to fill it (capital letters, black ink), duplex needs.
2. Field inventory per form and an overlap matrix: which data items repeat across forms. Quantify the owner's hypothesis "almost every form asks for the same data": for each form the share of fields that can be filled from one canonical profile, the share that is case-specific, and the share that only the clerk can fill.
3. Canonical profile: design the JSON Schema (applicant, identity document, addresses, contact, family and household members with relation, proxy, property owner, business, vehicle, real estate, case parameters), with Polish field labels as titles and validation rules (PESEL checksum and birth-date consistency, NIP, REGON, postal code, ID card number checksum, IBAN). Save it as data/canonical-profile.schema.json.
4. Statutory status: for each analysed form state whether its layout is prescribed by law ("wzór określony w rozporządzeniu", cite the act in ISAP with Dz.U. reference, e.g. forms for obowiązek meldunkowy, vehicle registration, tax declarations IN-1/DN-1, pełnomocnictwo) or is only a local auxiliary template; and what legally matters for the printout (identical content and layout versus free form with required content; legible handwritten signature; originals).
5. What "100% identical print" needs technically for each class of source (AcroForm PDF, flat vector PDF, scanned PDF, DOC/DOCX/RTF): recommended fill method, fonts with Polish diacritics, comb fields, overflow handling, multi-person duplication, duplex flags, and an automated visual regression test (render filled PDF to raster and compare with the blank template outside the field boxes).
6. Propose the "form descriptor" JSON format (form id, source URL, sha256 of the template, legal basis, pages, fields: id, label_pl, canonical_path, page, bbox in PDF points, kind text/comb/checkbox/date-parts/signature, font, size, max_chars, transform, required, validation, who_fills) and save one fully worked example for the permanent-residence registration form (at least its first page, with real coordinates measured from the file) as data/form-descriptor.example.json.

CLAIMS OF THE PREVIOUS RESEARCH TO VERIFY (give a verdict for each: CONFIRMED, PARTLY, WRONG or UNVERIFIABLE, with source and a one-line correction):
- C29: pypdf or pdf-lib can fill AcroForm fields with embedded Polish fonts and flatten; flat PDFs need a coordinate overlay (ReportLab/PDFKit); forms with one-character boxes need per-character stepping.

FINAL ANSWER FORMAT: after writing the files, reply with at most 25 lines:
FILES: list of files written;
KEY FINDINGS: up to 10 one-sentence bullets;
VERDICTS: one line per claim id (CONFIRMED / PARTLY / WRONG / UNVERIFIABLE, with the correction);
SURPRISES: findings that change the plan;
NOT DONE: what is missing and why.
