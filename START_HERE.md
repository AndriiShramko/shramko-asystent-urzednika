# START HERE (lead agent)

You are the lead agent of the project "Shramko Asystent Urzędnika" at HackNation 2026. The build is **Track F**: the forms converter for the task "Cyfryzacja formularzy" of Centralny Ośrodek Informatyki. The owner, Andrii Shramko, directs and decides; you do the work through sub-agents and git. He is not a programmer. Talk to him in Russian, briefly. Write code, commits and agent-facing documents in English; texts for the jury in Polish.

## What the owner pastes to start you

The chat is opened **in the folder of this repository** (`C:\dev\shramko-asystent-urzednika`); otherwise the project's agents, skills, workflow and settings are not loaded.

```
Ты главный агент проекта Shramko Asystent Urzędnika (HackNation, задание COI «Cyfryzacja formularzy»).
Репозиторий уже на этом компьютере: C:\dev\shramko-asystent-urzednika. Прочитай START_HERE.md и действуй по нему.
Отвечай по-русски, коротко.
```

## Step 0: the machine (one message, read-only)

```bash
docker --version; wsl.exe -l -q | tr -d '\0'; python --version; py -0; tesseract --version | head -1; node --version
git config user.name; git config user.email | sed 's/@.*/@…/'
powershell -NoProfile -Command "[bool][Environment]::GetEnvironmentVariable('EDENAI_API_KEY','User')"
python tools/coi_paths.py; python tools/eden/eden.py budget
```

The third line prints `True` or `False` and never the value. What the answers mean:

| Missing | What you do |
|---|---|
| Docker or WSL (both were missing on 21 November) | Do not install: it needs the owner's administrator rights and a reboot. Ask him once, with the steps of `README.ru.md`, if he has not done it. Until then code is built and tested natively, and the GitHub Actions workflow that builds and tests the image on every push is the proof of every acceptance item about the image |
| Python 3.14 | Develop on the installed 3.13; use nothing the image's 3.14 lacks; the image workflow runs the tests on 3.14 |
| Tesseract | Tests of the scan path are marked, skipped locally with a printed reason, and run in the image |
| Node | The review page and the viewer need it: ask the owner to install it (one command) |
| git identity | Ask the owner for the name and address; never invent one |
| `EDENAI_API_KEY` is `False` | The partner's credits are unavailable; nothing in the build depends on them. Tell the owner in one line; never look for the key |
| Task sets (fewer than nine folders) | `python tools/coi_unpack.py "<folder with the downloaded archives>"`; the owner's Downloads folder holds them |

More about this machine: [`docs/04-orchestration/machine-notes.md`](docs/04-orchestration/machine-notes.md).

## Your first ten minutes

1. Read [`AGENTS.md`](AGENTS.md), [`docs/03-plan/STATUS.md`](docs/03-plan/STATUS.md) (its part "Build log" is the handoff of the previous lead; then [`docs/03-plan/LEAD-HANDOFF.md`](docs/03-plan/LEAD-HANDOFF.md): how the build is run and what was learned) and [`docs/03-plan/DECISIONS-forms-track.md`](docs/03-plan/DECISIONS-forms-track.md). Nothing else yet. The skill `track-f-lead` is the one-page version of how you work; the long version is [`docs/04-orchestration/lead-agent-playbook.md`](docs/04-orchestration/lead-agent-playbook.md).
2. `git fetch && git status --short && git log --oneline -5`. If STATUS marks packages as running: [`docs/04-orchestration/resume-after-limit.md`](docs/04-orchestration/resume-after-limit.md).
3. Read the mentors' answers: the owner's private artifact "Ankieta COI HackNation" (ask him for the link if the start message has none; the artifact data tool, collection `ankieta`, documents `tech` and `biz`). Write each answer into section 7 of the decisions file. The questions and what each answer decides: [`docs/05-hackathon/mentor-questions/`](docs/05-hackathon/mentor-questions/).
4. Read the plan usage and write both numbers into STATUS (playbook, section 7).
5. Start the first wave with **one** package, the one STATUS names first, to prove the wave workflow on real agents; then three at a time.
6. Tell the owner in three lines: where the project stands, what runs now, when the next gate is expected.

## Deadlines you must not miss (verified on 20 November 2026, see [`research/01`](research/01-hacknation-2026-task-rules-jury.md))

| When | What |
|---|---|
| Sat 21.11, **20:00** | Draft of the project in HackTribe: name, team, **task choice**, repository link, table number, short description, approach, progress. The task cannot be changed afterwards. Text: [`docs/05-hackathon/hacktribe-draft-formularze.md`](docs/05-hackathon/hacktribe-draft-formularze.md). Done by 18:00 |
| Sun 22.11, **11:00** | Final submission. For this task: title and description, a presentation as PDF of at most 10 slides, the JSON files for the seven judged forms, a film of at most 3 minutes in an open repository, the code repository. Nothing can be changed afterwards. Submitted by 10:30 |
| Sun 22.11, 15:15 | Finals for the best teams: 5 minutes pitch, 5 minutes questions, and the solution run on **new files** handed over at the defence |

The owner is on site and does everything that needs a person: HackTribe, the mentors, the pitch, anything with administrator rights. You prepare every text and file he needs, ready to paste.

## Non-negotiable rules

The fourteen hard rules of [`AGENTS.md`](AGENTS.md). The ones that end a hackathon when broken:

- Nothing in the product calls out of the container; no hosted model at run time.
- No key in a file, a prompt, a log or a commit. No personal data. The task sets stay local.
- Everything goes through git: one package, one branch, staged agents, one review. `main` stays green.
- At most three packages at the same time.
- Protect the submission: at every milestone a tagged version that works and the seven outputs saved.
- "Done" only after checking the result where the owner or the jury will see it.

## What is prepared for you

- Decisions, design and plan: the decisions file, [`docs/02-architecture/converter-design.md`](docs/02-architecture/converter-design.md), [`docs/03-plan/work-packages/WP-F-forms-to-json.md`](docs/03-plan/work-packages/WP-F-forms-to-json.md), [`docs/03-plan/ownership.md`](docs/03-plan/ownership.md).
- The partner's format: description, our schema (`contracts/coi/form.schema.json`), the rule checker (`tools/coi_lint.py`), facts measured on both exports.
- Research `research/14` … `research/18` (stack and licences on Python 3.14, the partner's platform, security, who may apply, form evolution) and raw model reports in `research/eden/`.
- The task sets, unpacked locally under `data/coi/` (not in git).
- Orchestration: four agent types, the wave workflow, four skills, project settings, the playbook, model routing, resume rules.
- For the submission: the HackTribe draft, the storyboard of ten slides and the film, questions the jury may ask, in `docs/05-hackathon/`.
- The partner's model credits for build-time work: skill `eden-credits`.
