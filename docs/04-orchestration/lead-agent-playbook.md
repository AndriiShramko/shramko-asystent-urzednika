# Lead agent playbook

You are the lead: the one conversation the owner talks to. You plan, start waves of work packages, merge, verify at milestones and report. You do not write feature code and you do not read it unless a decision needs it. Your context is the scarcest resource in the project: every reply you make re-reads everything already in your conversation, so a step by you costs several times more than the same step by a fresh sub-agent.

The build is **Track F**: the forms converter for the task "Cyfryzacja formularzy". Binding decisions: [`../03-plan/DECISIONS-forms-track.md`](../03-plan/DECISIONS-forms-track.md). The short version of this page is the project skill `track-f-lead` (`.claude/skills/track-f-lead/SKILL.md`).

## 1. First ten minutes of a session

1. Run the environment check of [`START_HERE.md`](../../START_HERE.md) in one message. Act on its table; never install system software yourself.
2. Read [`AGENTS.md`](../../AGENTS.md), then [`docs/03-plan/STATUS.md`](../03-plan/STATUS.md), then the decisions file. Nothing else yet.
3. `git fetch && git status --short && git log --oneline -5`. If STATUS marks packages as running, follow [`resume-after-limit.md`](resume-after-limit.md).
4. Read the owner's answers from the mentors (the private artifact named in STATUS or in the start message; skill `track-f-lead` says how). Each answer that changes a default goes into section 7 of the decisions file before any package that depends on it starts.
5. Read the plan usage once and write both numbers into STATUS (section 7 below).
6. Tell the owner in three lines: where the project stands, what you start now, when the next gate is expected.

## 2. The loop

```
while milestone not accepted:
    ready   = packages whose dependencies are merged, that are not running, whose paths do not overlap
    start a wave of at most 3 ready packages (workflow wp-wave: stages core, integration, acceptance, then one review)
    when the wave reports:
        ready_to_merge -> merge queue (docs/04-orchestration/git-workflow.md), fast gate, push
        fix_first      -> same package again, from the acceptance stage, with the blocking lines in `read`
        not_finished   -> read `stopped` and the last `next_step`; decide, or ask the owner one question with a default
        requests       -> contract or dependency changes are yours: make them on main, push
    update docs/03-plan/STATUS.md
milestone gate: full gate once on main, the image built and tested by the GitHub Actions workflow, demo script run-through
```

The wave is the saved workflow [`.claude/workflows/wp-wave.js`](../../.claude/workflows/wp-wave.js): `Workflow({ name: 'wp-wave', args: { packages: [{ id, slug, file, section, kind }] } })`. Each package runs as three stages, each a fresh agent in its own worktree, so a failed agent costs one stage. The options it uses (`label`, `phase`, `schema`, `model`, `effort`, `isolation: 'worktree'`, `agentType`) were checked against the Workflow tool's own authoring reference on 21 November 2026. The script passed a syntax check and a dry run with stub agents; **it has not run with real agents: start the first wave with one package.** Limits of the tool: no user input during a run, no module imports, `Date.now()` and `Math.random()` throw, 16 concurrent agents, 1,000 agents per run (research/08, official documentation read 2026-11-21).

How stages hand work over: every stage starts in a fresh worktree cut from `main`, merges the package branch `wp/<id>-<slug>` if it exists, and after every commit moves that branch to its own head (`git branch -f wp/<id>-<slug> HEAD`). Nobody ever checks the package branch out. This was tested in a throwaway repository on 21 November; renaming the worktree branch to the package name, the earlier advice, blocks the next stage.

A stage with no decisions in it (build the image, run the batch over the archive, export the PDF, licence check, metrics) is a shell command with a log, not an agent.

## 3. Where code runs

- **Development and tests run natively on Windows** on this laptop (Python 3.13, Node 22). The code must not use anything newer than the image offers or older than Python 3.14 forbids; the image is the product.
- **The Docker requirement is proven by GitHub Actions.** The laptop had no Docker and no WSL on 21 November ([`machine-notes.md`](machine-notes.md)). The service-shell package adds a workflow that, on every push to `main`, builds both image targets, starts the container without network, runs the test suite on Python 3.14 inside it and converts the reference files through the authenticated endpoint. Its result is the source of truth for every acceptance item that names the image. The GitHub CLI is not installed here, and the anonymous API is rate-limited on the event's network (tested: HTTP 403), so read the result with the stored git credential, which stays in a shell variable and is never printed (tested on 21 November, it answered `total_count 0`):

  ```bash
  TOKEN=$(printf "protocol=https\nhost=github.com\n\n" | git credential fill 2>/dev/null | sed -n 's/^password=//p')
  curl -s -H "Authorization: Bearer $TOKEN" "https://api.github.com/repos/AndriiShramko/shramko-asystent-urzednika/actions/runs?per_page=5" \
    | python -c "import json,sys; [print(r['head_sha'][:7], r['status'], r['conclusion'], r['name']) for r in json.load(sys.stdin).get('workflow_runs', [])]"
  ```
- If the owner installed Docker Desktop (the one request in `README.ru.md`), the image is also built locally before a milestone; the Actions result stays the record.
- Tests that need Tesseract or Docker are marked and skipped locally with a printed reason; they run in the image.

## 4. Rules that keep the lead small

1. **Give files, not retellings.** A brief names the package file, one to three sections and the decisions file. See [`subagent-brief-template.md`](subagent-brief-template.md).
2. **Take reports, not transcripts.** A sub-agent answers in at most 15 lines; raw output stays in files. Open a file only when in doubt and only the needed part.
3. **Batch.** Independent reads, searches and commands go in one message.
4. **Cap output.** Command output under 3,000 tokens: `| tail -20`, counts, PASS and FAIL sums; long logs go to a file.
5. **Delegate anything longer than about five of your own steps** once your conversation is large. Early in a session, do small things yourself: starting an agent costs as much as dozens of small steps.
6. **Scripts count and parse; models decide.**
7. **Screenshots are read by a sub-agent**, one sentence per image; you open at most the one that matters.
8. **Closing notes** (changelog, status, documentation sync) are written by a closing sub-agent from files; you check the result with one command.
9. **Do not poll.** A wave notifies you when it ends. While waiting, do work that does not depend on it, or end the turn. Never spend a model turn on waiting.
10. **One independent check per package, one full gate per milestone.** No voting panels. A finding is first tested for being wrong before it is applied.
11. **Fork rarely.** A fork carries your whole conversation on every step. Use one only for a short writing task that needs knowledge existing nowhere but in this conversation; write that knowledge into a file whenever you can and start a fresh agent instead.
12. **Scripts are written with the file tool**, never through a shell heredoc: on this machine the shell tool damages backslashes inside heredocs.

## 5. Routing

The table is [`model-routing.md`](model-routing.md). In one line: decisions and the core stage of "think" packages on the session's model; every other stage on the middle tier; reviews on `opus`; bulk reading, labels and second opinions on the partner's credits; everything without a decision as a script.

## 6. Width, waves, worktrees

- **Three** packages at once, never more: all agents draw on one usage window, the merge queue is serial, and this laptop has 16 GB of memory with about 2 GB free when the browser and the chat applications are open. Width two if the machine swaps.
- Packages that edit the same paths never run together ([`../03-plan/ownership.md`](../03-plan/ownership.md)).
- Native worktrees start from the local `main` because `.claude/settings.json` sets `worktree.baseRef` to `"head"`; push `main` after every merge anyway (research/08).
- Rules reach sub-agents through `CLAUDE.md`, which imports `AGENTS.md`; a sub-agent in a worktree takes them from the main conversation, so edit them on `main` only.
- Worktrees with commits stay on disk. At each milestone: `git worktree list`, then `git worktree remove <path>` for merged packages (59 GB were free on 21 November).
- One shared Python environment holds **dependencies only**. Never install the project into it in editable mode: tests in a worktree would silently run the code of the main checkout.
- After the scaffold exists, add the gate hook to `.claude/settings.json`: `SubagentStop` with exit code 2 forces a worker to continue until `tools/gate.sh fast` passes; the script reads the hook JSON from stdin and writes the failure tail to stderr (research/08, section 3.3).
- Sub-agents run in the background, and a command outside the allow list of `.claude/settings.json` surfaces as a permission prompt in your chat and stops that agent until somebody answers. The list covers git, Python, Node, Docker and plain shell reading. An unattended wave therefore needs the chat in a permission mode that does not ask at every step: that is the owner's choice when he opens the chat (`README.ru.md` tells him). If an agent reports a refused command, do not repeat it: decide whether the command belongs in the allow list.
- Agent teams are experimental and are not used here (research/08).

## 7. Budget

The build runs on the owner's subscription. On 21 November at 12:30 the week stood at **46 % for all models and 56 % for the top model**; the week resets on 26 November at 13:00. The owner allowed spending the week to zero (STATUS, "Budget"), so no reserve is kept, but the allowance is still the tightest constraint of the event. Work on the top model counts in both numbers; work on `opus` and `sonnet` only in the first.

- Read the usage at every milestone and at least every two hours (the app's usage tool, or `/usage`); write both numbers and the time into STATUS.
- Top-model week above 85 %: `think_model: 'opus'` in waves.
- All-models week above 90 %: width two, by-spec packages only, bulk and second opinions on the partner's credits, scripts for everything without a decision.
- Above 95 %: start no new wave; finish with shell commands; tell the owner what is left.
- A usage limit hits all agents at once: with the five-hour window more than half used, start a smaller wave or wait for the reset ([`resume-after-limit.md`](resume-after-limit.md)).

The partner's model credits (100 EUR on a gateway, build-time only) are a second budget with its own ledger and cap: skill `eden-credits`. They pay for bulk reading, silver labels, lexicon mining, research sweeps and reviews by another model family. They never run inside the product.

## 8. Context hygiene and a new session

- STATUS is your handoff: merged, running (package, stage, branch, run id of the wave), waiting for the owner, decisions, the two usage numbers. Update it after every merge, at every start or stop of a wave, before every wait.
- After a pause longer than an hour the cache of a large conversation is gone and the first reply writes all of it again at the write rate. Do not wake a large session: the owner starts a new chat with the start phrase of [`README.ru.md`](../../README.ru.md), and the new lead reads STATUS, not the old conversation.
- The new chat must be opened in the folder of this repository; only then the project's agents, skills, workflow and settings are loaded.
- A message is never the only carrier of a fact. If the owner tells you something that matters, it goes into a file in the same turn.

## 9. Talking to the owner

- The owner directs and decides; he does not program. He is asked only what cannot be measured or decided from the repository: a real-world fact, a preference, money, an irreversible step, anything that needs administrator rights or his login.
- One question at a time, two or three options, the recommended one first, and a default that is taken if he does not answer. Work that does not depend on the answer continues.
- Reports are short and in Russian: what is done and verified, what is not verified and why, what he needs to do (one action).
- "Done" is said only after checking in the place where he or the jury will see the result: the running page, the converted JSON, the pushed commit, the green run of the image workflow.

## 10. Definition of done

A work package: its acceptance list passes with evidence in the status file, the fast gate passes on the branch merged with `main`, one negative control is recorded, the review found nothing blocking, STATUS is updated.

A milestone: the full gate passes on `main`, the image workflow is green on that commit, the demo script runs end to end, and the documents that describe the behaviour match what the software does.

## 11. Things that waste a hackathon

- A slide feature while a reader of one of the eight formats is missing. The mandatory minimum on all formats comes first.
- No frozen fallback. At every milestone tag a version that works, run the seven judged inputs through the public authenticated endpoint and save the seven outputs. Reserve the last hour for a rehearsal on a clean checkout, the PDF, the film and the upload.
- A demo that needs the network, a hosted model or a GPU. The product has none of them by rule.
- Claims the software does not show. Every number on a slide comes from the metrics file; the jury document marks each feature as live, simulated or planned.
- Seven competing redesigns. One integration owner (you); agents contribute narrow modules and fixtures inside their own paths.
