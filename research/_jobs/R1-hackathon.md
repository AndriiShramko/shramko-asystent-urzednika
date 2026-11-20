
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

TASK R1 - HackNation 2026: the task, the rules, the jury, last year's winners.
Output file: C:/dev/shramko-asystent-urzednika/research/01-hacknation-2026-task-rules-jury.md

Answer with evidence:
1. Everything official on hacknation.pl (home page, /zadania, /przewodnik-uczestnika, regulamin, FAQ, agenda, partners, mentors, jury, any PDF): dates, venue, hour-by-hour schedule (when tasks are revealed, when coding starts and ends, submission deadline and form, pitch format and length, finals), team size limits, what exactly must be submitted (repository? video? slides? description form?), evaluation criteria and weights (general and per task if published), prizes, IP and licence rules for solutions (who owns the code, must it be open source), whether AI coding assistants are allowed, what infrastructure is provided (LLM access such as PLLuM or cloud credits, API keys, data sets), remote participation rules.
2. The full published text of the Miasto Bydgoszcz task "Inteligentny asystent urzędnika" and every extra hint: partner page, city news (bydgoszcz.pl, um.bydgoszcz.pl), social media posts of the city and the organisers, press. Who in the city owns the topic (which unit handles UDIP requests, who might be the mentor)?
3. HackNation 2025 (first edition): how tasks were specified (find the task cards, e.g. on GitHub or archived pages), deliverables and criteria with weights, how winners were selected, links to winning and finalist repositories; analyse 3-5 of them (README structure, demo, what convinced the jury). Note any 2025 task similar to ours (administration assistants, anonymisation "Dane bez twarzy", legal text assistants) and what can be reused.
4. A list of 25 questions a GovTech hackathon jury is likely to ask about OUR project, each with a strong 2-3 sentence answer (security and RODO, real deployment in an urząd, integration with EZD, cost, model choice and digital sovereignty, hallucinations and legal liability, accessibility, vendor lock-in, maintenance, what is real versus mocked in the demo, scalability to other offices).
5. Strategy note: given the published challenge is specifically about UDIP requests, how risky is it to present the wider "form prefill at the counter" product? Base the answer on the rules and last year's judging; recommend how to frame it.

CLAIMS OF THE PREVIOUS RESEARCH TO VERIFY (give a verdict for each: CONFIRMED, PARTLY, WRONG or UNVERIFIABLE, with source and a one-line correction):
- C1: HackNation 2026 takes place on 21-22 November 2026 at BCTW (Bydgoskie Centrum Targowo-Wystawiennicze), ul. Gdańska 187, Bydgoszcz; 24 hours; 15 tasks from 15 partners.
- C2: The full task requirements and evaluation criteria are not published before the start; they appear on hacknation.pl/zadania on Saturday 21 November at 11:00 when coding starts.
- C3: An "AES-GCM plus checksum envelope" pattern appears directly in HackNation technical materials (suspicious: check whether any official HackNation material says anything like this).

FINAL ANSWER FORMAT: after writing the files, reply with at most 25 lines:
FILES: list of files written;
KEY FINDINGS: up to 10 one-sentence bullets;
VERDICTS: one line per claim id (CONFIRMED / PARTLY / WRONG / UNVERIFIABLE, with the correction);
SURPRISES: findings that change the plan;
NOT DONE: what is missing and why.
