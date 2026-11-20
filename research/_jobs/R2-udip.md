
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

TASK R2 - Access to public information (UDIP) in a Polish city office: law, real process, taxonomy, response templates, data sources.
Output files: C:/dev/shramko-asystent-urzednika/research/02-udip-law-process-taxonomy.md , C:/dev/shramko-asystent-urzednika/data/udip-taxonomy.json (valid JSON) , C:/dev/shramko-asystent-urzednika/data/udip-response-templates.md

1. Law as of November 2026: ustawa z dnia 6 września 2001 r. o dostępie do informacji publicznej (current consolidated text, Dz.U. reference from ISAP); every article relevant to handling a request with its operational meaning (art. 1-6, 10-17, 21-23); amendments 2024-2026; Centralny Rejestr Umów (did it start on 1 January 2026? impact); ustawa z 11 sierpnia 2021 r. o otwartych danych i ponownym wykorzystywaniu informacji sektora publicznego (how re-use requests differ); relation to RODO (anonymisation of personal data in disclosed documents, art. 5 ust. 2 privacy and the exception for persons performing public functions, tajemnica przedsiębiorcy); when KPA applies (art. 16 ust. 2); skarga na bezczynność to WSA and its consequences; art. 23 criminal liability.
2. The real decision tree of the clerk, step by step with inputs, outputs and deadlines: is it a UDIP request at all (versus skarga/wniosek/petycja, access to own case files art. 73 KPA, press inquiry, re-use request, environmental information, archives); does the office hold the information; is it already in BIP (art. 10); simple versus processed information (informacja przetworzona, art. 3 ust. 1 pkt 1, "szczególnie istotne dla interesu publicznego": wezwanie, then decision); restrictions (art. 5); form and manner (art. 14) and the 14-day reaction of the applicant, then umorzenie; fee (art. 15); extension (art. 13 ust. 2); decisions (art. 16) and their mandatory elements; signature and personal data needed before a decision (case law on art. 64 KPA); abuse of the right to information (nadużycie prawa) in case law; dokument wewnętrzny doctrine; multi-question requests.
3. A classification taxonomy an AI assistant can output: request types and sub-types, legal route, response document type, deadline rule, required human approvals, typical evidence. Save as data/udip-taxonomy.json.
4. Catalogue of response document types with mandatory elements and pitfalls (cite judgments by signature with links to orzeczenia.nsa.gov.pl where possible): udostępnienie; "nie stanowi informacji publicznej"; "nie posiadamy"; wskazanie BIP; zawiadomienie o przedłużeniu terminu; wezwanie do wykazania szczególnie istotnego interesu publicznego; zawiadomienie o opłacie; zawiadomienie art. 14 ust. 2; wezwanie do uzupełnienia braków przed decyzją; decyzja o odmowie; decyzja o umorzeniu; pismo o innym trybie. Save Polish skeleton templates with placeholders (no invented facts) as data/udip-response-templates.md.
5. Statistics and pain points: number of UDIP requests received by Urząd Miasta Bydgoszczy (BIP registers, reports, council interpellations, press) or comparable cities; typical topics; late answers; court cases; mass and automated senders; any published register of requests and answers of UM Bydgoszcz (URL, format) usable as demo or evaluation data; public data sets of real requests and answers (e.g. Sieć Obywatelska Watchdog Polska tools, dane.gov.pl, registers of other cities) with licences.
6. Machine-readable legal sources for grounding: Sejm ELI API (api.sejm.gov.pl/eli), ISAP, CBOSA (orzeczenia.nsa.gov.pl), SAOS API, BIP Bydgoszcz (API, RSS, sitemap?), dane.gov.pl API. For each: URL, access method, terms, and a sample request you actually ran with trimmed output.

CLAIMS OF THE PREVIOUS RESEARCH TO VERIFY (give a verdict for each: CONFIRMED, PARTLY, WRONG or UNVERIFIABLE, with source and a one-line correction):
- C4: A UDIP request needs no official form; Urząd Miasta Bydgoszczy offers an auxiliary template: PDF https://bip.um.bydgoszcz.pl/attachments/download/30900 and DOCX https://bip.um.bydgoszcz.pl/attachments/download/30899 (check both URLs and describe the template fields).
- C5: A UDIP request may be anonymous (e.g. only an e-mail address); personal data and a signature become necessary only when an administrative decision (refusal, discontinuance) must be issued under KPA.
- C6: Deadline: without undue delay, max 14 days; may be extended up to 2 months from filing if the applicant is notified within the 14 days with reasons (art. 13).
- C7: If the information is not public information, is not held by the office, or is subject to a separate access regime, the office answers with an ordinary letter, not an administrative decision.
- C8: Per the Bydgoszcz BIP card, UDIP requests can be sent to the general e-mail urzad@um.bydgoszcz.pl; this stayed valid after 1 January 2026.
- C9: The gov.pl online service "Uzyskaj informację publiczną" requires logging in through login.gov.pl (Profil Zaufany).

FINAL ANSWER FORMAT: after writing the files, reply with at most 25 lines:
FILES: list of files written;
KEY FINDINGS: up to 10 one-sentence bullets;
VERDICTS: one line per claim id (CONFIRMED / PARTLY / WRONG / UNVERIFIABLE, with the correction);
SURPRISES: findings that change the plan;
NOT DONE: what is missing and why.
