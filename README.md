# Shramko Asystent Urzędnika

**Open brief and reference design for an AI assistant for Polish public offices (urząd): it helps clerks analyse access-to-public-information requests (wnioski o udostępnienie informacji publicznej, UDIP) and draft answers, and it pre-fills official forms from data a visitor enters once.** Prepared for HackNation 2026 (21–22 November 2026, Bydgoszcz), challenge "Inteligentny asystent urzędnika" by Miasto Bydgoszcz.

Site and pitch deck: <https://urzad.flyreelstudio.eu> · Polski: [README.pl.md](README.pl.md) · Русский (для владельца проекта): [README.ru.md](README.ru.md) · For AI agents: [START_HERE.md](START_HERE.md), [AGENTS.md](AGENTS.md), [AGENT_SETUP.md](AGENT_SETUP.md), [llms.txt](llms.txt) · Known traps: [docs/warnings.md](docs/warnings.md)

> **Status: pre-event brief (tag `pre-event`).** This repository contains research, requirements, a scope decision, a build plan and an orchestration playbook written before the hackathon. It contains no application code yet. Application code is written during the 24 hours of the event and will be recognisable by commits after the tag. Live state: [`docs/03-plan/STATUS.md`](docs/03-plan/STATUS.md).

## Questions this answers

- How can AI help a Polish city office answer an access-to-public-information request within the 14-day deadline, and what may it never decide by itself?
- Which outcomes of a UDIP request are administrative decisions and which are ordinary letters? What must each contain?
- May an office still accept an anonymous UDIP request sent by e-mail? (Short answer: the case law changed in 2024–2026; see the research.)
- Where is a machine-readable list of all service cards and application forms of Urząd Miasta Bydgoszczy with direct download links?
- How do I fill an official Polish PDF form by program so that the printout is identical to the approved template?
- Can a resident share their data with an office by scanning a QR code, and what does mObywatel offer for that today?
- How does one lead Claude Code agent run several sub-agents on one repository through git worktrees without them overwriting each other, and without burning its own context?
- What does a HackNation jury score, what must be submitted and when?

## What is inside

| Path | What it is |
|---|---|
| [`docs/00-brief/requirements.md`](docs/00-brief/requirements.md) | The owner's requirements R1–R32 |
| [`docs/01-product/scope-decision.md`](docs/01-product/scope-decision.md) | What to build for the jury and why; the wider platform; "one database for many institutions?" |
| [`docs/01-product/gaps-and-additions.md`](docs/01-product/gaps-and-additions.md) | 38 things the original idea did not cover |
| [`docs/02-architecture/`](docs/02-architecture/) | Design decisions and trust zones, API contract, security and privacy with a threat table, the AI layer (guardrails, model choice, quality, integration, deployment) |
| [`docs/03-plan/`](docs/03-plan/) | Roadmap with event clock times, 18 work packages with acceptance lists, ownership table, live status |
| [`docs/04-orchestration/`](docs/04-orchestration/), [`.claude/`](.claude/) | Lead-agent playbook, sub-agent brief template, git workflow for parallel agents, resume after a usage limit, publishing; agent definitions, project settings and a wave workflow |
| [`docs/05-hackathon/`](docs/05-hackathon/) | Onsite intake procedure, pitch storyboard, demo script, the "what is real" table, a plain guide to the event for the owner (Russian) |
| [`site/`](site/) | The public site <https://urzad.flyreelstudio.eu>: landing page and the animated pitch deck with a presenter window |
| [`research/`](research/) | Ten research reports with sources and labels: hackathon rules and judging, UDIP law and the clerk's decision tree, forms catalogue and form anatomy, mObywatel and once-only, data protection and the AI regulation, technology, landscape, multi-agent orchestration, lessons from a 2022 production prototype, pitching |
| [`data/`](data/) | Catalogue of 275 service cards and 710 form files of Urząd Miasta Bydgoszczy (links and metadata), request taxonomy, Polish response skeletons, canonical profile schema, a measured form descriptor |
| [`prompts/`](prompts/) | Runtime instructions (Polish) for the product's AI steps |
| [`tools/`](tools/) | The polite crawler that rebuilds the catalogue, a slow downloader of form files, a link checker |
| [`docs/06-audit/`](docs/06-audit/) | Point-by-point check of an earlier research draft (Russian) |

## The idea in five lines

1. **Module A, the hackathon answer:** a case desk for public-information requests. The assistant reads the request, says what it legally is, starts the 14-day clock, finds earlier answers and published information, drafts the reply or the notice with a checked legal basis, masks personal data, and waits for a clerk's approval.
2. **Module B, the next process on the same core:** the visitor types their data once on their own phone (or the clerk reads the document), the clerk picks a life situation, the forms come out filled on the approved templates, a checker flags mistakes.
3. **Security is part of the task sentence** ("inteligentny i bezpieczny"): data stays under the office's control, a human approves every output, every step is logged, a local Polish model is a first-class option.
4. **Centralise forms, not people:** an open registry of form descriptions can serve every office; personal data stays with the person and with the office that handles the case.
5. **Built by AI agents under one lead**, through git, with small contexts and resumable steps.

## Quick start for an AI agent

```bash
git clone https://github.com/AndriiShramko/shramko-asystent-urzednika
```

Open the folder in Claude Code and say: `Read START_HERE.md and act as the lead agent.` Everything else is in that file.

## Honest limits

- Research is dated and labelled (verified, secondary, unverified) in each file; laws and products change. It is not legal advice.
- The full task card of the challenge is published only at the start of the event; the plan has a gate for re-checking the scope against it.
- Integrations with state systems (mObywatel, registers, document management) are proposals. This project is independent and is not affiliated with any institution named here.
- No real personal data is used anywhere; tests and demos use synthetic persons and requests.

## Disclosure for HackNation

This brief (research, specification, catalogue, crawler) was prepared before the event and is cited as an external resource, as the event rules require. Product code is written during the event.

## Author & working together

<img src="docs/assets/andrii-shramko.webp" alt="Andrii Shramko" width="120" height="120" align="left">

**Andrii Shramko** — I build tools with AI agents. In 2022 I ran a volunteer service in a refugee help centre in Opole that pre-filled Polish benefit applications for people arriving from Ukraine: visitors typed their data once on their phones, volunteers printed ready forms. This project brings that experience to city offices and adds an assistant for the clerk.

**Open to interesting people and ready to help teams build ambitious projects** — pilots with public offices, partnerships, licensing or funding. Get in touch:

- 📅 Book a call: <https://calendar.app.google/Ff729HqGk4RpzPNDA>
- 💼 LinkedIn: <https://www.linkedin.com/in/andrii-shramko/>
- ✉️ Email: zmei116@gmail.com
- 🐙 GitHub: <https://github.com/AndriiShramko>

<br clear="left">

## License

Code and tools: MIT. Documentation and research: CC BY 4.0. See [`LICENSE`](LICENSE), [`NOTICE`](NOTICE), [`CITATION.cff`](CITATION.cff). Security policy: [`SECURITY.md`](SECURITY.md).
