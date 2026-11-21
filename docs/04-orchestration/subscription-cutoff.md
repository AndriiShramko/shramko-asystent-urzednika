# Subscription limit cutoff: finish clean, hand over to a new subscription

The whole team (program lead, build lead, sub-agents, workflow agents) runs on ONE Claude subscription. When the weekly allowance is nearly used, everything stops, and the owner buys a new subscription, opens new sessions and gives them the repository. Nothing may be lost in between: a brand-new lead must be able to continue from the repository alone, without asking anyone. This page is the full protocol; the short versions are in the skills `track-f-lead` (lead) and `lane-work` (builders, thinkers, reviewers). The ordinary pause after a reset, on the same subscription, is [`resume-after-limit.md`](resume-after-limit.md).

## 1. The hook this protocol is aligned with

The owner's machine runs a user-level reserve hook, `limit_reserve.py` (documented in his skill `limit-safe-work`, file `~/.claude/skills/limit-safe-work/references/reserve.md`; not part of this repository and not changed by us):

- Threshold **98 %** of the weekly window **"Weekly · all models"**. From there sub-agents and workflow agents may only write files (Write, Edit), stop tasks and finish; a chat turn started before the pause is held the same way. Shell commands, and therefore `git commit` and `git push`, are not available to an agent in that state.
- A new message from the owner in his own chat still passes (normal tools, but no Agent, no Workflow, no new sessions). The lead can commit and push then.
- 99 % and above: the subscription itself stops.
- Not verified on 2026-11-21: the hook file was not found in `~/.claude/hooks/` of this machine when this page was written (only `grep_glob_fix.py` and `stop_promise_guard.py`). Treat 98 % as binding either way. Status, if present: `python -X utf8 ~/.claude/hooks/limit_reserve.py status`.

The protocol therefore finishes **before** 98 %: all commits and pushes happen at 96 to 97 %, because at 98 % an agent can no longer run git.

## 2. Where the number comes from, and how often

- Source: the tool `mcp ccd_session_mgmt get_usage`, row **"Weekly all models"** (the percent used and the reset time). The row "Weekly Fable" (top model) is read too, but only "all models" decides the cutoff.
- Check: at the start of every work block, and **before launching any agent or wave**. A block is one lead turn that does work. Write the number and the clock time (`date`) into the next STATUS line.
- If the number rises faster than 2 points in 20 minutes, check before every launch and at least every 15 minutes (parallel opus stages plus two lead sessions burned about 9 points an hour on 21 November; [`LEAD-HANDOFF.md`](../03-plan/LEAD-HANDOFF.md)).
- Economy mode from **80 %**: no new waves without the program lead's word, agents on sonnet, short briefs, one package at a time.

## 3. Thresholds (week, all models)

| Week | Lead | Every running agent |
|---|---|---|
| below 94 % | normal work, economy rules above 80 % | normal |
| **94 % and above** | No new agent, no new wave, no Workflow. Tell every running agent (SendMessage, one line): "week at N %: reach a clean point within about 15 minutes, commit, update your status file". Start no merge that is not finished in 10 minutes. | Finish the step in hand; do not start a new step. |
| **96 % and above** | Collect reports; write the handoff (section 5); push `main`; send the line to the program lead. | Section 4: commit the stage, push the branch, write "Left for the next stage", send the report, stop. |
| **98 % and above** | Nothing but committing and the handoff. Agents are stopped by the hook. | Stopped. Work of a stopped agent is recovered by the next lead (section 6). |
| **99 % and above** | Everything stops. | Everything stops. |

Order of work at 94 and above is always: **commit, then status, then report**. A report without a commit is worth nothing.

## 4. Every agent (builder, thinker, reviewer) at 96 % or on the lead's order

1. Stop the step in hand at the first clean point. Do not start any run longer than two minutes (tests of the whole suite, image build, batch); if one is running, let it finish only if it ends in under two minutes, else stop it and write its exact command into "Left for the next stage".
2. `git status --short` must be empty at the end. No uncommitted work in a worktree, ever: a dead worktree's loose edits are lost to the next stage.
3. Commit by file name (never `git add -A`), message `WP-<id>: <what> (stopped for the subscription limit)`, then `git branch -f wp/<id>-<slug> HEAD`.
4. Push the package branch: `git push origin wp/<id>-<slug>` (the publishing check runs; if it refuses, fix the cause, never bypass). This is the one case where a builder pushes. A branch named `wp/F20-*` starts the image workflow on push: say in the status file "CI run started, run id N, nobody waited for it" (or "not started") and do not wait.
5. In the status file `docs/03-plan/wip/WP-<id>.status.md` write `## Left for the next stage` with exact next commands: the checklist items still `[ ]` or `[~]` (what is half done and where), the commands to run, the checks that already passed with the commit they ran on, requests to lead. Commit and push that too.
6. Send the report in the usual format (at most 15 lines) with `status: out_of_budget`, the branch, the commit hash, the worktree path.
7. Stop. Do not use the remaining minutes for "one more thing".

A reviewer commits nothing and pushes nothing; it writes its findings so far into the report and to `docs/03-plan/wip/WP-<id>.review.md` only if the lead named that file.

## 5. The lead at 96 % and above

1. Wait for the agent reports no longer than 15 minutes from the 94 % order; whatever is silent after that is recovered from its branch (section 6).
2. Do not merge a package whose review is not finished. A merge that is not complete is aborted with `git merge --abort`; the main checkout must end clean.
3. Write the **HANDOFF block** in `docs/03-plan/STATUS.md` (file, then `bash tools/gate.sh py tools/lead/status_block.py docs/03-plan/STATUS.md <block file> $(date +%H:%M)`). It states, with the clock time:
   - what is merged (commits, tags) and the last green `main` run;
   - what runs or stopped: package, stage, package branch, worktree path, run id and script path of a wave, whether a CI run of a branch is open;
   - what waits for the owner (a decision, a physical step) with the default for each;
   - open questions and requests to lead, answered or not;
   - the image digests (`bash tools/gate.sh py tools/ci/image_digest.py <full commit>`) and the commit they belong to;
   - the budget state: week % and Fable % with the time, the economy mode in force, any reserve rule of the program lead;
   - "Not to redo" (section 7);
   - the next steps in order, each with the command.
4. Add a section "Learned by the Nth build lead" to `docs/03-plan/LEAD-HANDOFF.md`: measurements, traps, rules found, what cost the most.
5. `git add` the two files by name, commit, `git push origin main`. Do not start a merge, an image wait or a wave after this; if `main` needs a CI check, record the run id in the block and leave the waiting to the next lead.
6. One line to the program lead (SendMessage to the `from` of its messages):
   `СБОРКА ЧЧ:ММ | ПЕРЕДАЧА НА НОВУЮ ПОДПИСКУ | слито: ... | идёт/остановлено: пакеты и ветки | неделя A % / Fable F % | нужно: новая подписка, новый лид; промт старта у владельца`
7. If the owner is in the chat, tell him in Russian in three lines: everything is saved, what to open next, nothing else to do.

## 6. Recovery by the next lead (work of agents stopped by the limit)

Run in the main checkout `C:\dev\shramko-asystent-urzednika` on `main`, after `git fetch`:

1. `git worktree list`: every `.claude/worktrees/*` is a stopped stage or an old merged one.
2. `git branch --list "wp/*"` and, for each, `git log main..wp/<id>-<slug> --oneline`: commits beyond `main` are unmerged work.
3. The status file of each: `git show wp/<id>-<slug>:docs/03-plan/wip/WP-<id>.status.md` (the part `## Status` and `## Left for the next stage`); also read `docs/03-plan/wip/` on `main`.
4. For each worktree: `git -C <path> status --short` and `git -C <path> log main..HEAD --oneline`. A non-empty status is work that died uncommitted: read the diff, commit what is sound by file name on the worktree's branch, run `git branch -f wp/<id>-<slug> HEAD`, and only then continue. Never `git worktree remove` or `git clean` before this.
5. The last CI run: `bash tools/gate.sh py tools/ci/wait_run.py <full hash of main> --timeout 540`. A cancelled run of an older commit is not red; the newer commit's run counts ([`LEAD-HANDOFF.md`](../03-plan/LEAD-HANDOFF.md)).
6. A stopped Workflow is not resumed from a new session (unverified in [`resume-after-limit.md`](resume-after-limit.md)): start a new wave with `from` set to the stage where each package stopped, only on the program lead's word and only below the economy line.
7. Then the usual: the HANDOFF block orders the work.

## 7. What the new lead does NOT redo

- Merged packages, their reviews, tags and the results already recorded in STATUS and in `results/`.
- Checks that passed for unchanged inputs: the status file records the commit each ran on; if the branch still points at it, do not run it again.
- The machine check of `START_HERE.md` step 0, unless the HANDOFF says something changed.
- Decisions of `docs/03-plan/DECISIONS-forms-track.md` and answers of the owner already written there or in STATUS.
- Any step the HANDOFF block lists under "Not to redo".

## 8. Never at the cutoff

- Never leave uncommitted work in a worktree or in the main checkout.
- Never start an operation that cannot be finished or safely left: a merge, a rebase-like step, a wait for an image build, a long batch, a wave. Start none at 94 % and above unless it ends in minutes and is safe to abort.
- Never bypass the publishing check, force-push, stash, or rewrite history to "save time".
- Never write a secret, a key or personal data into the handoff.
- Never claim "all saved" before `git status --short` is empty and the push printed no error.

## 9. Checklists

Agent: [ ] clean point; [ ] `git status --short` empty; [ ] committed by file name; [ ] `git branch -f wp/...`; [ ] branch pushed (CI run noted); [ ] `Left for the next stage` with commands; [ ] report sent with `out_of_budget`; [ ] stopped.

Lead: [ ] week % read and timed; [ ] running agents told (94 %); [ ] reports collected or recovered from branches; [ ] no half merge; [ ] HANDOFF block in STATUS (merged, running with branches, worktrees and run ids, waiting for the owner, open questions, image digests, budget); [ ] `Learned by the Nth build lead` in LEAD-HANDOFF; [ ] both committed and `main` pushed; [ ] line `СБОРКА ... ПЕРЕДАЧА НА НОВУЮ ПОДПИСКУ` sent; [ ] owner told in three lines.

Owner (after buying the new subscription): open a new session in the folder of this repository; paste the start prompt for the new build lead; the new lead recovers state by section 6 and reports to the program lead.
