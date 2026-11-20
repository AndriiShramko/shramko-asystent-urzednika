
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

TASK R8 - Verified playbook: how one lead Claude Code agent (model Fable 5.2 "claude-fable-5-2" or Opus 5.5 "claude-opus-5-5") should run sub-agents through git to build this project fast and cheaply, as of November 2026.
Output file: C:/dev/shramko-asystent-urzednika/research/08-claude-code-multi-agent-token-economy.md

Read the CURRENT official documentation before writing (features change; do not rely on memory): Claude Code docs at https://code.claude.com/docs/en/ (start from the docs index or llms.txt: sub-agents, agent teams, workflows or orchestration, git worktrees, headless mode and the Agent SDK, hooks, skills, memory and CLAUDE.md, settings and permissions, model configuration and effort, costs, checkpointing, background tasks and sessions, MCP and tool search, plugins, scheduled tasks, cloud sessions) and the developer platform docs at https://platform.claude.com/docs/en/ (models and pricing, prompt caching including the 1-hour TTL, context windows, context editing, compaction, memory tool, effort, thinking, tool search, programmatic tool calling, structured outputs, citations, batch, token counting, data residency), plus Anthropic engineering articles on multi-agent systems, context engineering and long-running agent harnesses.

Deliver:
1. A table of every token-saving and orchestration mechanism that exists today: name, what it does, exactly how to enable it (setting, flag, frontmatter, API parameter), when it helps, pitfalls, documentation URL, VERIFIED or UNVERIFIED.
2. A recommended operating model for THIS repository: lead keeps a small context; work packages as files; one package = one branch + one git worktree + one sub-agent; status files and a resume-after-limit protocol; ownership table so that two agents never edit the same file; merge queue; one integration and verification pass per milestone; model and effort routing by task type; maximum parallel width and why; sub-agent report format (at most 15 lines plus a file); how to write sub-agent briefs; commit conventions; what Claude Code offers natively for continuing after the 5-hour usage limit versus what must be scripted.
3. Ready-to-copy artefacts inside the report (fenced code blocks): .claude/agents definitions for a slim worker (shell and files only) and a web researcher, a .claude/settings.json permissions sketch for unattended work, CLAUDE.md and AGENTS.md skeleton sections, and a sample orchestration script (Workflow tool script if documented, otherwise a headless "claude -p" pipeline).
4. API-side guidance for the PRODUCT's own LLM calls: current model IDs and prices, prompt-caching layout for a large static legal knowledge block, structured outputs, citations for grounding in legal text, batch for offline evaluation, effort settings, and a cost estimate per processed UDIP request for each model tier.

FINAL ANSWER FORMAT: after writing the files, reply with at most 25 lines:
FILES: list of files written;
KEY FINDINGS: up to 10 one-sentence bullets;
VERDICTS: one line per claim id (CONFIRMED / PARTLY / WRONG / UNVERIFIABLE, with the correction);
SURPRISES: findings that change the plan;
NOT DONE: what is missing and why.
