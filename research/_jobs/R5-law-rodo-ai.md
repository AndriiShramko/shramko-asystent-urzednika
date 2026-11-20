
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

TASK R5 - Data protection, AI and security law for (a) AI-assisted handling of UDIP requests and (b) collecting citizen data by phone, QR or ID scan and printing pre-filled forms in a city office.
Output file: C:/dev/shramko-asystent-urzednika/research/05-rodo-ai-act-security-requirements.md

1. Legal bases and roles under RODO for a city office (art. 6(1)(c) and (e), art. 9, art. 86; controller, processor, art. 28 agreement), DPIA (art. 35 and the UODO list of operations requiring a DPIA), retention, records, privacy by design. The owner wants visitors to enter "all data that might ever be needed" up front: analyse the conflict with data minimisation and propose a compliant design (data stays on the citizen's device; only the fields required by the chosen forms are transmitted; ephemeral processing).
2. Copying, photographing and scanning identity documents: UODO positions and decisions (verify numbers, parties, amounts), any 2025-2026 decisions, ustawa o dokumentach publicznych (art. 58), whether on-the-fly reading of the MRZ or chip without storing the image is defensible for a public office, and the legal basis for an authenticity check with a document reader.
3. AI in public administration as of November 2026: AI Act timeline (what already applies; was the delay of Annex III obligations adopted - exact legal state and dates); is an assistant that drafts answers to UDIP requests or checks forms a high-risk system (Annex III analysis, art. 6(3) derogations); art. 4, art. 27, art. 50; the Polish implementing act (status); art. 22 RODO and human-in-the-loop; who signs decisions under KPA; official guidance (UODO on AI, Ministerstwo Cyfryzacji and ai.gov.pl material for offices, PLLuM guidance).
4. Security and accessibility duties: KRI (rozporządzenie of 21 May 2024), ustawa o krajowym systemie cyberbezpieczeństwa and the NIS2 amendment (status, are gminas covered), ustawa o dostępności cyfrowej (WCAG level) for the citizen page and the clerk app, logging and audit expectations, cloud standards for public administration (SCCO) and data-residency expectations.
5. LLM provider options for THIS use case, verified in current official documentation: Anthropic first-party API (retention defaults, zero data retention, training use, data residency options in 2026, DPA and SCCs); Claude through AWS Bedrock, Google Vertex AI or Microsoft Foundry in EU regions; sovereign options (PLLuM: who offers access and under what licence; Bielik: licences and sizes; local serving needs); the pseudonymisation gateway pattern - is pseudonymised text still personal data for the recipient (EDPB guidelines on pseudonymisation, CJEU EDPS v SRB C-413/23 P) and what follows for sending tokenised text to a cloud LLM.
6. A compliance checklist builders can implement and show to the jury: 20-30 controls, each mapped to its legal source and marked MUST (legal), SHOULD (good practice) or DEMO (can be demonstrated within 24 hours).

CLAIMS OF THE PREVIOUS RESEARCH TO VERIFY (give a verdict for each: CONFIRMED, PARTLY, WRONG or UNVERIFIABLE, with source and a one-line correction):
- C18: UODO decisions with numbers "5112.33.2022" and "DKN.5112.6.2020" imposed fines for excessive photographing or scanning of ID documents (verify numbers, parties, amounts, what exactly was penalised).
- C19: UODO published that 95.9% of surveyed organisations do not consider themselves prepared to deploy AI in compliance with RODO (https://uodo.gov.pl/pl/138/4533).
- C20: UODO published a "lista pytań inicjalnych" for AI tools in the public sector, referenced by ai.gov.pl article "AI w urzędzie: od czego zacząć".
- C21: AI Act: FRIA under art. 27; obligations for Annex III high-risk systems were postponed to 2 December 2027 (Digital Omnibus); art. 4 AI literacy already applies.
- C22: A public authority must appoint an Inspektor Ochrony Danych (art. 37(1)(a) RODO) and must involve the IOD in such a deployment.
- C23: Anthropic first-party API: no EU data residency (only global and US processing); default retention 30 days; Zero Data Retention needs separate approval and does not cover Files API and Batch; some "Covered Models" have mandatory 30-day retention; content flagged by safety filters may be kept up to 2 years even under ZDR; EU residency is available through AWS Bedrock EU or Google Vertex AI EU endpoints.

FINAL ANSWER FORMAT: after writing the files, reply with at most 25 lines:
FILES: list of files written;
KEY FINDINGS: up to 10 one-sentence bullets;
VERDICTS: one line per claim id (CONFIRMED / PARTLY / WRONG / UNVERIFIABLE, with the correction);
SURPRISES: findings that change the plan;
NOT DONE: what is missing and why.
