# Machine notes: the owner's laptop on 21 November 2026

What on this machine helps or hinders the build agents. Everything in the first three sections was measured on 21 November between 12:30 and 13:40 by the preparing session; what was not measured is labelled. Nothing outside the repository was changed: the last section lists exact, reversible changes the owner may make.

## 1. What is there

| Thing | Measured | Consequence |
|---|---|---|
| Processor, memory | 16 logical processors; 16 GB of memory, **2.2 GB free** with the browser, Discord and the Claude app open | three agents plus tests fit only if heavy applications are closed; width two if the machine swaps |
| Disk | one disk, 59 GB free (94 % used) | worktrees and Docker images must be cleaned at milestones |
| Graphics card | present; the owner's notes say it overheats under load within half a minute | nothing in the build uses it |
| Python | 3.13.3 and 3.11; **no 3.14** | develop and test on 3.13; the image runs 3.14; the image workflow is the proof |
| Python libraries present | uvicorn, pydantic 2, pytest, PyJWT, lxml, pypdf, olefile, openpyxl, python-docx | |
| Python libraries missing | fastapi, pdfminer.six, pypdfium2, rapidfuzz, jsonata, nh3, defusedxml, filetype, simplemma | the scaffold package creates one shared environment with pinned dependencies |
| Node | 22.16 | enough for the review page, the viewer and the reference JSONata evaluator |
| Docker, WSL | **neither is installed** (`docker: command not found`; no WSL distribution) | the image cannot be built here; see section 3 |
| Tesseract | not found on the path, nor in its usual folder | the scan path is tested in the image; local tests that need it are skipped with a printed reason |
| git | 2.46, identity set, pushes work through the stored credential | |
| GitHub CLI, uv, ruff, jq | not installed | not needed; results of GitHub Actions are read with the stored credential (playbook, section 3) |
| Java | version 8 only | Apache Tika or POI would need 17 or newer: not an option on this machine without an install |
| Repository attributes | `.gitattributes` forces LF; `.worktrees/` and `.claude/worktrees/` are ignored | "CRLF will be replaced by LF" warnings are harmless |
| Variable `EDENAI_API_KEY` | set at user level by the preparing session (64 characters; the value is never printed) | `tools/eden/eden.py` works; a program started before the variable was set reads it from the user registry through the tool |
| Task sets | nine sets unpacked under `data/coi/` (seven judged, two reference), local only | `python tools/coi_paths.py` lists them |

## 2. What every session carries before the first message

Measured by the app's context meter at the start of the preparing session (opened in another folder, so without this repository's files):

| Part | Tokens |
|---|---|
| Built-in tools | 20,800 |
| Connector and MCP tools (names of deferred tools and the loaded ones) | 18,800 |
| System prompt | 13,000 |
| Listing of skills | 11,500 |
| Instructions of MCP servers | 3,600 |
| **Sum** | **about 68,000** |

This prefix is cached, so it is cheap on every reply but it is written again after every pause longer than the cache lives, and after every change of the tool set.

Where it comes from, counted on disk:

- **75 personal skills** in the user's folder (descriptions 13,800 characters, bodies 558,000 characters). Families: Facebook groups 15, 360 films 11, bookkeeping 10, outreach 5, tours 2 and about thirty single ones. Relevant to this build: `limit-safe-work`, `limit-resume`, `coop`, `gh-publish`, `project-kickoff`, `talk-deck`. The rest never applies here. The owner's setting `skillListingBudgetFraction: 0.02` already caps the listing.
- **22 personal agent types**: 9 from the plugin `understand-anything` (file-analyzer, project-scanner, architecture-analyzer, domain-analyzer, article-analyzer, assemble-reviewer, graph-reviewer, knowledge-graph-guide, tour-builder) and 13 of the owner's own (research and creative teams, `meta-skill`). None is needed for the build. **`lane-worker`, the lean type the owner's skill `limit-safe-work` names, is not on this laptop**: the repository's `wp-builder` has the same tool set and takes its place.
- **Local MCP servers** in the user settings: `filesystem`, `github`, `obsidian`. **Connectors of the account** in the desktop app: Gmail, Calendar, Drive, Docs, Sheets, Slides, Notion, Box, Semrush, Hugging Face, Claude Docs, plus the app's own browser, computer-use, terminal and scheduling tools.
- **Hooks**: one before `Grep`, one at `Stop`. The owner's reserve guard (`limit_reserve.py`, the last 2 % of the week) is **not installed on this laptop**; the owner lifted the reserve for this week anyway (STATUS, "Budget").

Not measured: the start weight of this repository's agent types on this machine. The owner's skill reports 18,000 to 28,000 tokens for an agent with shell and file tools only against 107,000 for an agent with every tool (measured on his other machine); the probe script it names is not on this laptop.

## 3. What makes agents heavy or fragile here, and the answer

| Problem | Answer (in the repository) |
|---|---|
| A general-purpose sub-agent inherits every tool, every connector and the lead's model | The four project types with explicit tool lists (`.claude/agents/`): builders and the thinker have shell and files only, the reviewer is read-only, the researcher has web and files. The wave workflow never starts a general-purpose agent |
| A long agent re-reads its own tail on every reply | Packages are cut into stages before they start (core, integration, acceptance); each stage is a fresh agent that begins from the status file |
| No Docker: the mandatory image cannot be built or run locally | Code is developed and tested natively; a GitHub Actions workflow builds and tests the image on every push and is the record. The owner's one request in `README.ru.md` installs Docker Desktop (administrator rights, about 20 minutes, one reboot). Without it the defence can show the service running natively and the green image run; whether the jury accepts that is question J8 |
| No Tesseract, no Python 3.14 | Same: the image has both; local tests skip what needs them and say so |
| 2 GB of free memory | Close the browser tabs that are not needed, Discord when not in use, any video or 3D application; never run two heavy test suites and an OCR batch at once |
| **The shell tool damages backslashes inside heredocs** (seen twice in the preparing session: a Python script arrived with a broken string, a second heredoc did not parse) | Agents write every script with the file tool and then run it. All briefs say so |
| `cd` inside a compound command can ask for permission | Stages run in native worktrees, so their working directory is already the worktree |
| The task archives cannot be unpacked in place on Windows (paths longer than 260 characters) | `tools/coi_unpack.py` reads them in memory and writes short paths |
| Anonymous GitHub API is rate-limited on the event's network (HTTP 403 seen) | Read Actions results with the stored git credential held in a shell variable (playbook, section 3) |
| A chat opened in another folder does not load this repository's agents, skills, workflow and settings | **Open the build chat in `C:\dev\shramko-asystent-urzednika`** |
| A pause longer than an hour empties the cache of a large chat | New chat from STATUS with the start phrase; do not wake the old one |
| The publishing check of the owner stops on bank accounts and phone numbers printed on the forms | The task sets stay local; code reaches them through `tools/coi_paths.py` |

## 4. Changes only the owner can make (exact and reversible)

None is required for the build. In order of value:

| # | Change | How | How to undo | Gain |
|---|---|---|---|---|
| 1 | Install WSL and Docker Desktop | steps in `README.ru.md` | uninstall Docker Desktop in Windows settings | the image is built and run on the laptop; needed if the defence runs on our machine |
| 2 | Free memory before the build | close applications | open them again | fewer stalls with three agents |
| 3 | Switch off connectors the build never uses, for the build chat only: Semrush, Box, Notion, Sheets, Slides, Docs, Drive, Calendar, Hugging Face, Claude Docs | in the chat's connector menu; or the lead does it for its own session as its very first action (a change of the tool set later would empty the cache) | switch them on again; other chats are not touched | a smaller fixed prefix for the lead; size of the gain not measured, because tool definitions are already deferred |
| 4 | Switch off the plugin `understand-anything` for the weekend | in `C:\Users\<you>\.claude\settings.json`, under `enabledPlugins`, set `"understand-anything@understand-anything": false` | set it back to `true` | nine agent types and their skills leave every session; small gain, not measured |
| 5 | Leave the 75 personal skills as they are | | | editing or unlinking them during the event risks the owner's other running work; their listing is capped and cached, and sub-agents of this repository do not depend on them |
| 6 | Optional: Python 3.14 and Tesseract on the laptop | `winget search Python.Python.3.14`, `winget search tesseract` to find the exact ids, then install; both may ask for administrator rights | uninstall in Windows settings | local runs closer to the image; not needed when item 1 is done |

What the owner asked ("correct the skills that hinder the model"): no personal skill was found that changes how the build agents behave. What costs tokens is the number of tools and agent types a session carries, and the answer to that is the lean project agent types, which is done, plus items 3 and 4 above.
