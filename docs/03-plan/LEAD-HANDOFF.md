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

## 4. What comes next, in order

1. Merge WP-F3 (finder) and WP-F2b (sheets, binary Word) when they report; extend the ready formats (section 2).
2. WP-F4 (understanding: the brief) on top of the finder. Then a wiring stage: finder and understanding replace `app/interim.py`; `assemble_ledger` gets the inverse of `ComposeResult.brief_keys`; `UploadInfo` reaches the pipeline.
3. In parallel, as slots allow: WP-F8 (validators), WP-F2c (images and OCR; Tesseract only in CI), WP-F7 (conditions from the paper's wording), WP-F6 (dictionaries, initial data, proposals), WP-F15 (accounting sidecar), WP-F16 (airlock and hostile corpus), WP-F9 with WP-F10 (one front end, two views).
4. The open follow-ups of merged packages listed in STATUS (composer, readers, shell).
5. Milestone (b): all eight formats, validators, dictionaries and initial data, conditions, the review page. Then WP-F11 (evaluation run, `results/`, metrics), WP-F12 (README, architecture document, licences), the jury-style critique of the seven outputs on the partner's credits (`verification-plan.md`, section 4), the run on unseen forms of the city archive (section 2 there).
6. Milestone (c), then WP-P1: ten slides as PDF and the script of the three-minute film. Submission by Sunday 10:30.

At every milestone: full gate, a tag `track-f-<letter>`, the seven results refreshed in `results/`, the milestone row of STATUS with the commit and the image digest (`bash tools/gate.sh py tools/ci/image_digest.py <commit>`), the budget numbers, and the owner's ten-minute page (`verification-plan.md`, section 3).

## 5. The owner

Standing instructions are in STATUS. In one line: decide and act; involve him only for a physical step; show plain proof at milestones; messages in Russian, short. His two deadlines on 21 November: register the task with the partner by 19:00; send the HackTribe draft by 20:00 (`docs/05-hackathon/hacktribe-draft-formularze.md`; re-read it against what is built before he sends it).
