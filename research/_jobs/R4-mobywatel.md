
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

TASK R4 - mObywatel, mDowód, login.gov.pl, state registers, EUDI Wallet and the once-only principle: what can legally and technically feed citizen data into a city-office form-prefill system in November 2026.
Output file: C:/dev/shramko-asystent-urzednika/research/04-mobywatel-identity-once-only.md

1. mObywatel today: documents and services; legal status of mDowód (ustawa z dnia 26 maja 2023 r. o aplikacji mObywatel, article references), where it cannot be used; the verification methods (wizualna, funkcjonalna, kryptograficzna) and exactly how each works; the verification service for institutions (QR code shown by the institution, citizen confirms in the app): who may integrate (public offices? private companies?), under what agreement with the Minister of Digital Affairs or COI, which attributes come back, cost, onboarding time, sandbox, public technical documentation (URLs). Is there already a flow where the citizen scans the institution's QR code and shares a data set that the institution's system receives? This is exactly what the owner imagined - establish whether it exists, for whom, and how it works.
2. login.gov.pl (Węzeł Krajowy): who can integrate, returned attributes, protocol, onboarding; Profil Zaufany; e-dowód (electronic layer, CAN, NFC) - can an office read the chip with a document reader and is that provided for by law.
3. State registers a gmina clerk already uses (Rejestr PESEL, Rejestr Dowodów Osobistych, BUSC, CEPiK through the ŹRÓDŁO application / System Rejestrów Państwowych): what may be reused across departments of the same office, is there an API for a gmina's own systems.
4. The once-only principle: art. 220 KPA, ustawa o informatyzacji działalności podmiotów realizujących zadania publiczne, Single Digital Gateway Regulation (EU) 2018/1724 art. 14 (Once-Only Technical System, status in Poland), Interoperable Europe Act. Legal feasibility of "one shared citizen database for many institutions" that the owner asks about; why a new central database is not the lawful route; the lawful alternatives (citizen-held data shared on demand, register look-ups with a legal basis, ephemeral processing).
5. EUDI Wallet (Regulation (EU) 2024/1183): deadlines, Poland's implementation inside mObywatel as of November 2026, protocols (OpenID4VP, OpenID4VCI, ISO 18013-5), how a relying party requests attributes with a QR code, and how to design an "identity source adapter" so mObywatel or EUDI can be plugged in later; concrete open-source verifier libraries and reference implementations.
6. Existing QR data-exchange precedents in mObywatel (mStłuczka, hotel check-in pilots, document checks) and the status of e-Doręczenia, ePUAP and Rejestr Danych Kontaktowych for city offices in 2026.
7. Conclusion for tomorrow's demo: what can be shown without any agreement, what to present as integration-ready, and a concrete proposal to the Ministry of Digital Affairs (the hackathon organiser) such as a "Wypełnij wniosek z mObywatela" relying-party flow, with suggested wording.

CLAIMS OF THE PREVIOUS RESEARCH TO VERIFY (give a verdict for each: CONFIRMED, PARTLY, WRONG or UNVERIFIABLE, with source and a one-line correction):
- C11: mDowód (mObywatel) cannot be used to confirm identity when applying for a new dowód osobisty.
- C16: From 14 July 2023 mDowód is legally equal to a physical ID card inside Poland (except applying for a new ID card and crossing borders) and officials must accept it.
- C17: mDowód has three verification methods: visual, QR-code (functional) and cryptographic.
- C24: The ePUAP transition period ended on 1 January 2026 and e-Doręczenia became the main official electronic delivery channel for public offices.

FINAL ANSWER FORMAT: after writing the files, reply with at most 25 lines:
FILES: list of files written;
KEY FINDINGS: up to 10 one-sentence bullets;
VERDICTS: one line per claim id (CONFIRMED / PARTLY / WRONG / UNVERIFIABLE, with the correction);
SURPRISES: findings that change the plan;
NOT DONE: what is missing and why.
