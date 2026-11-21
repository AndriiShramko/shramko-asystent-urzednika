# AGENT_SETUP.md

How an AI agent (or a person) installs, checks, updates and removes this project. The repository is a brief plus a static site at this stage; application code arrives during the event and extends the "Run" section.

## Install

```bash
git clone https://github.com/AndriiShramko/shramko-asystent-urzednika
cd shramko-asystent-urzednika
```

Requirements for the tools that exist now: Python 3.11 or newer (standard library only), Node 20 or newer (for the deck PDF export), a Chromium-based browser. Nothing needs keys or accounts.

On Windows keep line endings as they are: `git config core.autocrlf false` in the clone.

## Check

```bash
python tools/check_links.py .                 # every relative link in the documents resolves
python tools/crawl_bydgoszcz_forms.py --help  # the catalogue crawler
python tools/collect_forms.py --help          # slow downloader of the form files (writes to a git-ignored cache)
node tools/deck_pdf.mjs                        # renders site/deck/Asystent-Urzednika.pdf from the deck's print mode
```

Open `site/deck/index.html` in a browser: arrow keys change slides, `P` opens the presenter window, `?print=1` shows the print layout.

## Run the product

Not built yet. The first work package (`docs/03-plan/work-packages/WP-00-scaffold.md`) creates one start command and `tools/gate.sh fast|full`; this section is then replaced by the exact commands, tested on a clean clone.

## Update

```bash
git pull --ff-only
```

Read [`CHANGELOG.md`](CHANGELOG.md) and [`docs/03-plan/STATUS.md`](docs/03-plan/STATUS.md) after pulling. The public site updates itself from `site/` within two minutes of a push to `main` ([`docs/04-orchestration/deploy.md`](docs/04-orchestration/deploy.md)).

## Rules before changing anything

[`AGENTS.md`](AGENTS.md) (hard rules), [`SECURITY.md`](SECURITY.md) (what must never be committed), [`docs/warnings.md`](docs/warnings.md) (known traps).

## Remove

Delete the folder. Nothing is installed outside it. The downloader's cache is inside the folder (`data/forms-cache/`).
