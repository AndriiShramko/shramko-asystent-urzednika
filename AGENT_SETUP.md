# AGENT_SETUP.md

How an AI agent (or a person) installs, checks, updates and removes this project. The product code (the forms converter, Track F) is written during the event; the scaffold package extends the "Run" section.

## Install

```bash
git clone https://github.com/AndriiShramko/shramko-asystent-urzednika
cd shramko-asystent-urzednika
```

Line endings are fixed by `.gitattributes` (LF); a warning that CRLF will be replaced by LF is harmless.

Requirements for the tools that exist now: Python 3.11 or newer, Node 20 or newer (deck export; later the review page and the viewer), git. Text extraction in `tools/coi_unpack.py` uses `python-docx`, `pypdf` and `openpyxl` when they are installed.

The product itself targets **Python 3.14 in a Docker image**. A machine without Docker and without Python 3.14 can still develop and test: the GitHub Actions workflow added by the scaffold package builds and tests the image on every push. State of the owner's laptop: [`docs/04-orchestration/machine-notes.md`](docs/04-orchestration/machine-notes.md).

## The task sets (not in git)

The partner's forms and the second reference export are kept out of the repository. Download the ten archives from the task's Discord channel into one folder (renaming them is fine), then:

```bash
python tools/coi_unpack.py "<folder with the downloaded archives>"
python tools/coi_paths.py        # lists nine sets: seven judged, two reference
```

Code reaches them only through `tools/coi_paths.py` (it also works from a git worktree and honours `COI_DATA_DIR`).

## The partner's model credits (optional, build-time only)

`tools/eden/eden.py` reads the key from the environment variable `EDENAI_API_KEY` (on Windows also from the user-level variable). The owner sets it; an agent never prints it, never passes it and never looks for it. Check without revealing it:

```bash
powershell -NoProfile -Command "[bool][Environment]::GetEnvironmentVariable('EDENAI_API_KEY','User')"
python tools/eden/eden.py budget
```

Nothing in the product uses this key. Rules: skill `eden-credits`.

## Check

```bash
python tools/check_links.py .                              # every relative link in the documents resolves
python tools/coi_lint.py "data/coi/reference-01-numer-porzadkowy/<the JSON file>"   # the partner's sample passes the rule checker
python tools/eden/eden.py models --grep haiku              # the gateway catalogue (no key needed)
```

The environment check of the lead (Docker, WSL, Python, Tesseract, Node, git identity, the variable, the sets) is in [`START_HERE.md`](START_HERE.md), step 0.

## Run the product

Not built yet. The scaffold package of Track F creates the start command, `tools/gate.sh fast|full`, the Dockerfile with two targets and the image workflow; this section is then replaced by the exact commands, tested on a clean clone.

## Update

```bash
git pull --no-rebase
```

Read [`CHANGELOG.md`](CHANGELOG.md) and [`docs/03-plan/STATUS.md`](docs/03-plan/STATUS.md) after pulling. The public sites update themselves from `site/` and `site-formularze/` within two minutes of a push to `main` ([`docs/04-orchestration/deploy.md`](docs/04-orchestration/deploy.md)).

## Rules before changing anything

[`AGENTS.md`](AGENTS.md) (hard rules), [`SECURITY.md`](SECURITY.md) (what must never be committed), [`docs/warnings.md`](docs/warnings.md) (known traps), [`docs/04-orchestration/git-workflow.md`](docs/04-orchestration/git-workflow.md).

## Remove

Delete the folder. Nothing is installed outside it. Local state inside it: `data/coi/` (the task sets), `data/forms-cache/` (the downloader's cache), `.eden/` (the spending ledger), `.worktrees/` and `.claude/worktrees/` (work-package worktrees: remove them with `git worktree remove` first). The variable `EDENAI_API_KEY` is the owner's: remove it in the Windows settings when the event is over.
