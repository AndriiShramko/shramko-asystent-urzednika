
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

TASK R6 - Engineering options verified against current (November 2026) libraries and documentation.
Output file: C:/dev/shramko-asystent-urzednika/research/06-tech-stack-pdf-ocr-qr-scanner.md

1. Pixel-exact PDF filling and printing: detection of AcroForm versus XFA versus flat PDFs; libraries (pypdf, PyMuPDF, pdf-lib, pdfcpu, pdfme, ReportLab overlay, qpdf) with licences (flag AGPL), font embedding for Polish diacritics, comb fields, flattening, PDF/A; DOC/DOCX/RTF to PDF fidelity (LibreOffice headless pitfalls); duplex and per-person copies; printing from a web app on Windows office PCs (browser print with exact scale, IPP, silent printing options); automated visual regression.
2. ID capture in the browser: MRZ reading on a phone (Tesseract.js with OCR-B data, other WASM or JS MRZ libraries, their accuracy and licences), parsing and check digits (ICAO 9303 TD1, TD3), which Polish documents carry an MRZ (dowód osobisty back side, passport, karta pobytu) and which do not (mDowód, older documents, prawo jazdy), what data is NOT in the MRZ (address, parents' names, birth place), barcode or QR content on Polish documents if any, Web NFC limits for reading e-dowód or e-passport chips, getUserMedia capture versus file input capture (what really gets stored on Android and iOS), large-print verification UI.
3. Secure QR handoff phone to clerk: session bootstrap from a QR code, end-to-end encryption with WebCrypto (ECDH P-256 with HKDF and AES-GCM, or HPKE), where keys live, replay and phishing protections, TTL and deletion, in-memory stores versus encrypted persistence, real-time delivery (WebSocket or SSE), QR capacity limits for a purely offline transfer, working when the visitor is on mobile data and the clerk PC is in an isolated office network.
4. Hardware document reader: the owner has an Adaptive Recognition (ARH, Hungary) "Osmond" passport and ID reader (R variant with RFID) received in 2022 with the "Passport Reader" software package (drivers, FullPageReader demo, SDK, version 2.1.10.x) and the "Autofill / Digital Reception" middleware (Autofill Windows, App Form Filler, Web Form Filler, Chrome extension "ARH Digital Reception"). From public documentation establish: current SDK generation and names, supported languages, licensing model (licences stored in the device, engine licences for MRZ, VIZ, barcode, authentication), whether current software still supports a 2022 Osmond, how the Autofill web form filler delivers data to a web page, what the device returns (fields, white/IR/UV images, RFID data groups, authenticity checks), and how to wrap it as a localhost bridge. Also assess WebUSB, WebHID and Web Serial as alternatives. Link only public pages.
5. A stack recommendation that AI coding agents can build in 24 hours and that runs fully on-premise or on one laptop: compare two concrete options (TypeScript monorepo versus Python FastAPI backend with a TypeScript front end), database for UDIP cases (PostgreSQL with row-level security and field encryption, or SQLite with SQLCipher for the demo), OpenAPI-first contracts, authentication for clerks (OIDC, passkeys), audit log as an append-only hash chain, containerisation, test tooling (Playwright, pytest or vitest), accessibility tooling.
6. LLM integration layer: provider abstraction (Anthropic API, Bedrock EU, OpenAI-compatible local endpoint for Bielik or PLLuM through Ollama or vLLM), PII pseudonymisation before any cloud call and re-identification after, structured outputs, grounding with citations to legal sources, evaluation harness with a golden set, prompt-injection defences for requests that arrive by e-mail.
7. Risks and what to mock in a 24-hour demo.

CLAIMS OF THE PREVIOUS RESEARCH TO VERIFY (give a verdict for each: CONFIRMED, PARTLY, WRONG or UNVERIFIABLE, with source and a one-line correction):
- C25: A standard QR code holds about 2.9 KB of binary data, enough for a gzip-compressed encrypted profile of one or two persons (offline QR transfer phone to clerk).
- C26: Using <input type="file" capture> saves the ID photo into the phone gallery and cloud backup, therefore camera capture must use WebRTC getUserMedia with an in-memory canvas.
- C27: An ephemeral RAM-only buffer (Redis with RDB/AOF persistence disabled, TTL 15-30 minutes) with client-side AES-GCM encryption keyed from the QR code is the right store for walk-in data.
- C28: A browser cannot talk to a USB passport reader; a "Local Device Bridge" service on 127.0.0.1 (HTTP/WebSocket with a pairing token) is required.
- C29: pypdf or pdf-lib can fill AcroForm fields with embedded Polish fonts and flatten; flat PDFs need a coordinate overlay (ReportLab/PDFKit); forms with one-character boxes need per-character stepping.

FINAL ANSWER FORMAT: after writing the files, reply with at most 25 lines:
FILES: list of files written;
KEY FINDINGS: up to 10 one-sentence bullets;
VERDICTS: one line per claim id (CONFIRMED / PARTLY / WRONG / UNVERIFIABLE, with the correction);
SURPRISES: findings that change the plan;
NOT DONE: what is missing and why.
