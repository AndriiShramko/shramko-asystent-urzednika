# START HERE (lead agent)

You are the lead agent of the project "Shramko Asystent Urzędnika". The owner, Andrii Shramko, directs and decides; you do the work through sub-agents and git. He is not a programmer. Talk to him in Russian, briefly. Write code, commits and agent-facing documents in English; texts for the jury in Polish.

## What the owner pastes to start you

```
Ты главный агент проекта Shramko Asystent Urzędnika. Открой репозиторий
https://github.com/AndriiShramko/shramko-asystent-urzednika (клонируй, если его нет),
прочитай START_HERE.md и действуй по нему. Отвечай по-русски, коротко.
```

## Your first 30 minutes

1. Read [`AGENTS.md`](AGENTS.md) (rules and map) and [`docs/03-plan/STATUS.md`](docs/03-plan/STATUS.md) (where the project stands). Do not read anything else yet.
2. Read [`docs/04-orchestration/lead-agent-playbook.md`](docs/04-orchestration/lead-agent-playbook.md). It is how you work.
3. Check the machine: `git --version`, `gh auth status`, Python 3.11+, Node 20+. Missing tools: install them yourself; a login is the only thing you ask the owner for (open the page, tell him in one line what to press).
4. If `STATUS.md` lists unfinished preparation items (research jobs, missing documents), finish those that block the build first. Research job prompts are ready in [`research/_jobs/`](research/_jobs/): run each as one web-research sub-agent, three at a time at most.
5. If the event has started (Saturday 21 November 2026, 11:00): open hacknation.pl/zadania, save the full task cards of **"Inteligentny asystent urzędnika" (Miasto Bydgoszcz)** and **"Cyfryzacja formularzy" (Centralny Ośrodek Informatyki)** into `docs/05-hackathon/intake/`, and follow [`docs/05-hackathon/ONSITE-INTAKE.md`](docs/05-hackathon/ONSITE-INTAKE.md). Then confirm the track with the owner according to [`docs/01-product/scope-decision.md`](docs/01-product/scope-decision.md) §0 (one question, recommended option first). **The default is Track B: the forms product for "Cyfryzacja formularzy"**, built as a working two-sided product (visitor on a phone, clerk on the laptop) following "Timeline for Track B" in the roadmap and [`docs/05-hackathon/demo-script-formularze.md`](docs/05-hackathon/demo-script-formularze.md). The owner wants the jury to see the product work, not slides of theory.
6. Report to the owner in three lines and start the first milestone of [`docs/03-plan/roadmap.md`](docs/03-plan/roadmap.md).

What is already prepared for you: 18 work packages with acceptance lists (`docs/03-plan/work-packages/`), agent definitions and settings (`.claude/agents/`, `.claude/settings.json`), a wave workflow (`.claude/workflows/wp-wave.js`, untested: try it on one package first), runtime instructions for the product (`prompts/`), the pitch deck with a presenter window (`site/deck/`, live at <https://urzad.flyreelstudio.eu/deck/>) and the publishing path: commit into `site/` and push ([`docs/04-orchestration/deploy.md`](docs/04-orchestration/deploy.md)). Keep `site/deck/metrics.json`, `site/deck/status.json` and [`docs/05-hackathon/jury-qa.md`](docs/05-hackathon/jury-qa.md) equal to what the software really does.

## Deadlines you must not miss (verified on 20 November 2026, see [`research/01`](research/01-hacknation-2026-task-rules-jury.md))

| When | What |
|---|---|
| Sat 21.11, 11:00 | Full task cards published; coding starts |
| Sat 21.11, **20:00** | Draft of the project must exist in HackTribe (project name, team, **task choice**, repository link, table number, short description, approach, progress). The task cannot be changed afterwards. Do it by 18:00. |
| Sun 22.11, **11:00** | Final submission: all fields, presentation as **PDF up to 10 MB**, working links, a short demo (up to 2 minutes recommended). Nothing can be changed afterwards. Submit by 10:30. |
| Sun 22.11, 15:15 | Finals for the five best teams per task: 5 minutes pitch and 5 minutes questions |

The owner is on site and does everything that needs a person: registration, the HackTribe account, talking to mentors, the pitch. You prepare every text and file he needs, ready to paste.

## Non-negotiable rules

- No real personal data in the repository, in prompts to cloud models, in logs or in screenshots. Synthetic data only.
- No secrets in git. Keys live in `.env` (git-ignored) on the machine.
- Everything goes through git: one work package, one branch, one worktree, one sub-agent. `main` stays green. See [`docs/04-orchestration/git-workflow.md`](docs/04-orchestration/git-workflow.md).
- At most three sub-agents at the same time unless the owner raises the limit.
- Say "done" only after checking the result where the owner or the jury will see it.
- Material prepared before the event is disclosed as such (README, slide). Product code is written during the event.
- If a usage limit stops you: [`docs/04-orchestration/resume-after-limit.md`](docs/04-orchestration/resume-after-limit.md).
