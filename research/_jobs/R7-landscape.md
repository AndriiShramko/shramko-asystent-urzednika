
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

TASK R7 - Landscape: existing Polish and international solutions, reusable open-source components, and numbers for the pitch.
Output file: C:/dev/shramko-asystent-urzednika/research/07-landscape-existing-solutions-and-reuse.md

1. Polish public sector: EZD RP (NASK) - what it is, adoption, integration points and API, any AI functions announced or delivered; which document management system Urząd Miasta Bydgoszczy uses (EZD RP, EZD PUW, Mdok, other) and its e-services stack; the mObywatel virtual assistant and PLLuM; other ministry or NASK AI projects for officials in 2025-2026; city chatbots.
2. Automation of public-information requests: anything built for UDIP in Poland (BIP vendors, registers of requests, legal-tech tools, NGO tools) and FOIA automation abroad (United States federal pilots and vendors, United Kingdom, Alaveteli-based sites): which functions proved valuable (triage, detection of duplicates and mass requests, search in previously released answers, redaction support, deadline tracking) and which failed or were criticised.
3. HackNation 2025 outputs that can be reused, especially anonymisation tasks and administrative assistants: open-source repositories and licences.
4. Polish-language building blocks with licences: PII detection and NER (spaCy Polish models, HerBERT-based NER, GLiNER multilingual PII, Microsoft Presidio with Polish recognisers), Polish LLMs (Bielik versions and licence, PLLuM models and licence, availability on Hugging Face and Ollama), embeddings and rerankers suitable for Polish legal text, Polish legal corpora.
5. Front-desk and form-prefill prior art: queue systems and e-services in Polish offices, kiosks, digital reception with ID scanners in hotels and clinics, bank onboarding, once-only implementations in Estonia and Denmark, GOV.UK prefill; what they prove and what went wrong.
6. Numbers for a pitch, each with a source: volume of UDIP requests in Polish cities, handling time, cost and penalties of delays; counter visits and form volumes in a city of about 325 thousand residents such as Bydgoszcz; time saved per form by prefill; error and return rates of paper applications.
7. Differentiation table: what exists versus what this project adds.

FINAL ANSWER FORMAT: after writing the files, reply with at most 25 lines:
FILES: list of files written;
KEY FINDINGS: up to 10 one-sentence bullets;
VERDICTS: one line per claim id (CONFIRMED / PARTLY / WRONG / UNVERIFIABLE, with the correction);
SURPRISES: findings that change the plan;
NOT DONE: what is missing and why.
