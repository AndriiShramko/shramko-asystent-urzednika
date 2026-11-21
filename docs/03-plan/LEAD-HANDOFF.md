# Lead handoff: how the build is run (read after STATUS, before the first action)

Written by the first lead session of the build on 21 November 2026. [`STATUS.md`](STATUS.md) says where things stand; this page says how the work is done here, what was learned the hard way, and what comes next. Keep it short and true.

## 1. The loop

1. A notification says a wave or an agent finished. Read its `ready_to_merge` and `requests_to_lead`, nothing else.
2. Merge with one command (it runs the publishing check on everything the branch brings, the fast gate, the push):
   `bash tools/lead/merge.sh wp/<id>-<slug> "Merge branch 'wp/<id>-<slug>' (WP-<id>): <what>; reviewed, verdict merge" '<regex of owned paths>'`
3. Start the next packages at once (at most three agents at any moment, wave agents included).
4. Rewrite the running block of STATUS: write the block to a file and run `python tools/lead/status_block.py docs/03-plan/STATUS.md <block file> $(date +%H:%M)`, commit, push. **Take every time from the clock or from `git log`, never from memory**: the first lead was half an hour off within forty minutes.
5. End the turn. Notifications wake the lead; never poll.

## 2. Starting work

- A package of the plan: the saved workflow `wp-wave`, `Workflow({ name: 'wp-wave', args: { packages: [{ id, slug, file, section, kind, model, read: [three items] }] } })`. `kind: 'think'` with `model: 'opus'` gives a strong core stage without touching the top-model week; `kind: 'think'` without `model` runs the core on the session's model (used for the composer and the finder; planned for the understanding step while the top-model week is under 85 %). The three `read` items carry everything the stage brief lacks: (1) the design sections and what exactly is in scope, (2) the entry point and the files that must not be edited, (3) fixtures, drills of `verification-plan.md`, the project's Python. A wave of one package takes 15 to 21 minutes: three stages and an independent review.
- Lead-owned work of one stage (contracts, wiring, a follow-up): a direct agent, `wp-builder` on sonnet or `wp-thinker` on opus, `isolation: 'worktree'`, with its own branch `wp/F0<letter>-<slug>` and status file. No review agent; ask a hosted model for a second opinion when the change is a contract.
- Anything that changes the image (Dockerfile, workflow, `tools/ci/**`): the branch is named `wp/F20-<letter>-<slug>`, because the image workflow runs for `wp/F20-**`; that agent alone may push its own branch, after the publishing check, and waits with `bash tools/gate.sh py tools/ci/wait_run.py <commit>`. A change is merged into `main` only after its branch run is green. Pushes that change only `docs/**` or `research/**` start no run.
- When readers for more formats are merged: extend `READY_FORMATS` in `.github/workflows/image.yml` and the list of formats without a reader in `app/pipeline.py` (through such a `wp/F20-…` branch).

## 3. What was learned

- **The lead's conversation is the largest cost.** Nine packages cost about half a point of the week each; the lead cost as much as all of them together, because every step re-reads a conversation that had grown to half a million tokens. Rules: read no large file; let scripts print counts and tails; one message with several tool calls; no status prose in the chat beyond what the owner needs; hand the lead role to a fresh session when the conversation passes about 300 thousand tokens.
- **Hosted reasoning models need room.** With 14,000 output tokens two of three calls returned an empty text (billed). Use `--max-tokens 40000` or a lower reasoning effort through `--extra`, and check that the output file is not empty. `openai/gpt-6.2-astra` answered well at 14,000.
- **The publishing check** stops (exit 4) on: a literal identifier with a valid check digit; a bare eleven-digit number that happens to pass the PESEL check (a run id); `token: VALUE` in a comment. Exit 1 lists the bare words token and secret in authentication code: read that there is nothing else, then go on. `python tools/lead/scan_lines.py FILE…` shows which line is flagged without printing the value.
- **Nothing of the partner's sets is in git**, so the image workflow proves the container on synthetic forms only. The seven judged forms are converted natively (`tools/lead/snapshot_results.py`) and, once Docker is on the laptop, by the published image.
- **Additive contract changes only.** Revision 1.1 of the models was made while two packages coded against 1.0, and nothing broke because no existing field changed.
- **An agent that finds a fact about the partner's materials** (a typo in the exports, a wrong form name in a standard text) reports it; the lead adds a row to `docs/02-architecture/contradiction-docket.md`. These rows are slide material.
- One worktree could not be removed (`.claude/worktrees/agent-a272afdf3fc7f8677`: permission denied, a process held it). Remove it after the reboot: `git worktree remove <path>`; then `git worktree prune`.

### Learned by the second build lead (21 November, 16:10 to 17:04)

- **`tools/lead/status_block.py` replaces everything from the "Running" line down to the "Budget, measured" line**, including the merged table and the open follow-ups. Edit STATUS with a small script or the file tool instead, and keep lines 1 to 70 true: the program lead's agents read them as the truth about the build.
- **Take times from `date`.** The second lead's reports ran half an hour fast until the program lead noticed.
- **The publishing check refuses any identifier with a valid check digit, even a public one**: the office's bank account printed on the paper of set 8 reaches the briefs and the result. Hence `eval/briefs/*.json` and `results/judged-08-…/form.json` are git-ignored and regenerated locally; never commit form text of the partner's sets.
- **`tools/ci/image_digest.py` needs the full commit hash** (the image tags are full SHAs); `--tag latest-main` gives the newest image. Docker from an old shell: call `"/c/Program Files/Docker/Docker/resources/bin/docker.exe"`; mount absolute Windows paths (`cygpath -w`) with `MSYS_NO_PATHCONV=1`.
- **Small finishing work goes to a direct `wp-builder` on the package branch** (stale tests of other packages, review findings): about five minutes each, much cheaper than a new wave. A wave reports `fix_first` when the review blocks; the lead may still merge when the blockers are gaps rather than regressions (WP-F4), and turns them into a named follow-up package.
- **A worktree agent's downloads stay in its worktree**: the city archive was moved to `data/archive/` of the main checkout.
- **The program lead is the only one who talks to the owner.** Its decisions and the audit's tickets arrive by message; record decisions in the decisions file (section 6c) and tickets in `audit-tickets-2026-11-21.md` with the package that takes each.

### Learned by the third build lead (21 November, 17:07 to 17:25)

- **A lead that hands over still acts on its own agents' notices.** The second lead's session merged F20e at 17:14 while the third lead was merging it too (merge.sh said "Already up to date"). Before a merge, `git log -3 main` and `git log origin/main -1`; tell the old session in one message that it merges nothing more.
- **Agents report to the session that started them.** A new lead learns nothing from them: watch the package branches with one background loop (`git rev-parse` every 30 s, exit when a branch moves) and read the status file on the branch; never read an agent's output file.
- **Check Actions after every code merge**: `bash tools/gate.sh py tools/ci/wait_run.py <full hash> --timeout 540`. `main` was red for 17 minutes (F2c made JPG and PNG readable while the image check still expected a refusal) and nobody saw it; `latest-main` silently stayed on an older commit. Which commit an image is: compare `image_digest.py --tag latest-main` with `image_digest.py <full hash>` of recent first-parent commits.
- **The chain's baseline keeps no reason for a refusal**; the reasons came from a read-only agent converting the eight files natively. Worth adding the problem code to `baseline.json` (WP-F11b).
- **Context:** the first turn of a lead costs about 120 thousand tokens (prompt, tools, skills); the program lead's rule hands over at that start plus about 100 thousand. Two agent reports and one STATUS rewrite fill most of it: delegate every read over 10 KB, keep reports to 15 lines.
- **The owner may write to the build lead directly.** Answer him in Russian (rule 13), record what he decides (D25 came this way) and tell the program lead.

### Learned by the fourth build lead (21 November, 17:26 to 17:55)

- **The publishing check flags password-like shapes, not only identifiers.** "second pass): status" in a status title stopped a merge with exit 4 (`secret_like`, masked as a hash with the match length). `python tools/lead/scan_lines.py FILE` gives the line; reword it, `git add`, re-run the same `merge.sh` (the merge stays staged).
- **A branch checked out in a stopped agent's worktree cannot be moved** (`git branch -f` is refused): brief the next agent to work inside that worktree path and commit there. Restore `eval/chain/summary.json` first: every chain run overwrites it.
- **OCR in the image needs a writable `/tmp`.** With `--read-only` and no `--tmpfs /tmp` every image is refused as UNREADABLE in 2 to 3 s; with it a set PNG converts in 10 s. CI had the flag, the README did not (fixed in `9e5638a`); the image fix (`VOLUME /tmp` or equal, plus a check without the flag) is in WP-F20f stage 2. `eval.chain --image` fails on every file because it runs `python -m converter` past the image's entry point: use `tmp/image_run_all.sh <ref>` (add `--tmpfs /tmp`) until WP-F11b fixes it.
- **The chain counts fields, not labels.** The independent review of F3b found two regressions the chain could not see (a one-word label glued to a heading; "osobiście" turning a company applicant into a person). Keep one review per package; a direct `wp-builder` fixes such findings in 7 minutes.
- **The wave workflow failed twice on F3b** (opus stages commit but return no structured report). Direct agents per stage work: `wp-thinker` on opus for a core, `wp-builder` on sonnet for acceptance and fixes, `wp-reviewer` for the review.
- **Context:** this lead started at 129 thousand tokens and reached the limit in 30 minutes: two reviews, four agent launches, a dozen peer messages and notices. Answer peer messages in one line and read no report twice.

### Learned by the fifth build lead (21 November, 18:02 to 18:18)

- **Parallel opus stages plus two lead sessions burn about 9 points of the week an hour.** At 18:10 the week rose 3 points in 20 minutes (an opus core, a wave review, a sonnet builder, the old and the new lead). A core continuation can run on sonnet when the previous stage wrote its cases and rules into "Left for the next core stage".
- **A cancelled main run is not a red main.** A newer push to `main` cancels the running image run; the newer commit's image carries the code (`de4acbe` cancelled, `4ab9689` published). `wait_run.py` then shows `cancelled` on a build step. Only `docs/**` and `research/**` start no run: `README.md` and `eval/chain/baseline.json` do.
- **A model runtime fits only the `plus` target.** onnxruntime 1.32.0 (MIT) ships cp314 x86_64 wheels for glibc only (checked 18:05), none for musl: Alpine `core` cannot carry it.
- **Every sidecar reports G11 and G12 `not_applicable`.** Say "10 of 12 checks passed, 2 not applicable" until the wiring hands the ledger and the fill-area values to the gate.
- **`rm -rf` outside the repository is refused** by the permission settings: `tools/lead/pitch_run.py` names its folders by the second and never cleans up.
- **Context:** this lead started at about 95 thousand tokens and reached start plus 115 thousand in 15 minutes (three peer reports, two agent launches, one merge, the model answer). The program lead wants the model answer in five lines.

### Learned by the seventh build lead (21 November 22:26 to 22 November, new subscription)

- **The 5-hour window is the real limit of the night, not the week.** Five agents on the top model plus the lead spent about 94 points of the window in 43 minutes (22:27: 6 %; 23:10: every agent killed with "5-hour limit"). The window is shared with the program lead and its audit agents: with one builder of ours running it still rose from 9 % to 28 % in 12 minutes (00:16 to 00:28). Read `get_usage` every 15 minutes while anything runs; at most one or two top-model builders beside the audit; everything without a decision is a shell command.
- **A limit kills an agent in the middle of a step.** What saved the work: commits after every step and status files written as the work went. What was nearly lost: three loose files of H4 (committed by the lead by name, `git branch -f`, pushed). Since then builders push the package branch after every commit and keep "## Left for the next stage" current in every commit ([`RESUME.md`](RESUME.md) section 2, skill `lane-work`).
- **A killed or finished agent is continued with a message, not replaced.** `SendMessage` to its name resumes it with its context. Agents also stop at their 70-turn cap and often end "without delivering a report": read the package branch and the status file instead of asking; both were complete every time.
- **One file to continue from: [`RESUME.md`](RESUME.md).** Start prompt, one merge lead for `main`, lane leads on branches, the remote branch as the lock of a lane, the board with what is left. The owner asked for exactly this (22 November, about 00:15: another agent on another subscription must be able to continue, everything through git).
- **`eval.chain` in a worktree needs `--archive C:/dev/shramko-asystent-urzednika/data/archive`**, else it fails with "80 of 80 files of the sample are not in archive/". After a run in a worktree restore `eval/chain/summary.json` there; only the merge lead commits it, on `main`.
- **A "worse" line of the chain is read by hand before it is believed.** The F3c review fix showed four files with fewer fields: all were false required uploads removed (a sentence, a section heading, "Przedkładam"). A scratch script that dumps type and label per field with the code of each checkout and diffs the two lists settles it in two minutes.
- **The clock.** `date` in Git Bash prints the label CEST but the hour is local (CET). The lead's own feeling of elapsed time ran about 20 minutes ahead of the clock twice: write times only from `date`.
- **What starts an image build.** A push of `main` that touches only `docs/**` or `research/**` builds nothing; `README*`, `AGENTS.md`, `.claude/**`, `eval/**` do, and a newer push cancels the running build. Batch such commits with a code merge. A branch `wp/F20-*` builds a test image: the cheap way to prove a check red (`wp/F20-red-proof`, never merged).
- **`merge.sh` printing "publishing check: exit 1; findings other than bare words: 0" is normal** (bare words like token in tests); exit 4 is the one that stops.
- **Docker on this laptop.** Git Bash rewrites `/in/form.pdf` into a Windows path unless `MSYS_NO_PATHCONV=1` is set; PowerShell 5.1 `>` writes UTF-16 with a BOM; `curl` there is an alias (use `curl.exe`). The jury commands of the README avoid all three. Containers named `a8-*` and `sau-v1` (port 8080) belong to the program lead and the owner's test: never touch them.
- **The desktop app follows `cd`.** After a `cd` into a worktree the session's working directory moves there; start every command with an explicit `cd /c/dev/shramko-asystent-urzednika` (or the worktree you mean).
- **REQUIRED.** With the default `REQUIRED_POLICY=paper` (completeness decision R-1) the seven judged results carry 13 REQUIRED instead of 146 (per set 0, 0, 1, 6, 3, 0, 3); `inferred` restores the old behaviour. The partner's two exports carry none.

## 4. What comes next, in order

1. (Second lead, 17:04) Merge WP-F3b and WP-F20e when they report; the rest of the order is in the STATUS handoff block, which wins over this list.
2. WP-F4 (understanding: the brief) on top of the finder. Then a wiring stage: finder and understanding replace `app/interim.py`; `assemble_ledger` gets the inverse of `ComposeResult.brief_keys`; `UploadInfo` reaches the pipeline.
3. In parallel, as slots allow: WP-F8 (validators), WP-F2c (images and OCR; Tesseract only in CI), WP-F7 (conditions from the paper's wording), WP-F6 (dictionaries, initial data, proposals), WP-F15 (accounting sidecar), WP-F16 (airlock and hostile corpus), WP-F9 with WP-F10 (one front end, two views).
4. The open follow-ups of merged packages listed in STATUS (composer, readers, shell).
5. Milestone (b): all eight formats, validators, dictionaries and initial data, conditions, the review page. Then WP-F11 (evaluation run, `results/`, metrics), WP-F12 (README, architecture document, licences), the jury-style critique of the seven outputs on the partner's credits (`verification-plan.md`, section 4), the run on unseen forms of the city archive (section 2 there).
6. Milestone (c), then WP-P1: ten slides as PDF and the script of the three-minute film. Submission by Sunday 10:30.

At every milestone: full gate, a tag `track-f-<letter>`, the seven results refreshed in `results/`, the milestone row of STATUS with the commit and the image digest (`bash tools/gate.sh py tools/ci/image_digest.py <commit>`), the budget numbers, and the owner's ten-minute page (`verification-plan.md`, section 3).

## 5. The owner

Standing instructions are in STATUS. In one line: decide and act; involve him only for a physical step; show plain proof at milestones; messages in Russian, short. His two deadlines on 21 November: register the task with the partner by 19:00; send the HackTribe draft by 20:00 (`docs/05-hackathon/hacktribe-draft-formularze.md`; re-read it against what is built before he sends it).
