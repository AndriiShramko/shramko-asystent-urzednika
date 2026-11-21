# Continuing after a usage limit, a crash or a restart

Work that cannot be resumed from the middle is paid for twice. In this repository every unit of work is resumable by construction; this page says how.

## What survives and what does not

| Survives | Does not survive |
|---|---|
| Commits. Every stage moves the package branch `wp/<id>-<slug>` to its own head after each commit, so the branch always holds the latest finished step | Uncommitted edits in the worktree of a stage that died: the next stage starts in a fresh worktree and does not see them |
| Status files (`docs/03-plan/wip/WP-<id>.status.md` on the package branch, `docs/03-plan/STATUS.md` on `main`) | Anything that existed only in a chat message |
| Results of finished agents inside a Workflow run (see below) | A sub-agent stopped by the user with `x` in `/tasks` (it does not resume by itself); a sub-agent whose lead session is gone (resuming from a new session is unverified) |
| A stopped sub-agent's history, in the same lead session: the lead sends it a message (`SendMessage` by agent id or name) and it continues with its full context. Transcripts stay in `~/.claude/projects/<project>/<session>/subagents/` for `cleanupPeriodDays` (30) (research/08, official documentation read 2026-11-21) | |
| Files written to disk before the stop, in the main checkout | |

Fallback that always works: start the same stage again with a fresh agent. Its brief begins with RESUME-FIRST, the package branch carries the commits, the status file says what is left.

## Rules that make resuming cheap

1. **A checkpoint is a commit, and the package branch follows it.** After each finished step: commit, the status checklist in the same commit, `git branch -f wp/<id>-<slug> HEAD`. Before any run longer than two minutes: commit first.
2. **The status file is the input for continuation, not a report.** `[x]` done (with commit), `[~]` in progress (what exactly), `[ ]` left.
3. **Every brief starts with RESUME-FIRST** (see [`subagent-brief-template.md`](subagent-brief-template.md)). Re-sending the same brief then costs minutes, not a restart.
4. **Stages are small.** A package is three agents in sequence (core, integration, acceptance), not one. A dead agent costs one stage.
5. **Heavy checks are keyed on their inputs.** A check writes its evidence with the commit it ran on; if the branch still points at that commit, nobody runs it again.
6. **The lead keeps a handoff.** Before any long wait the lead writes in `docs/03-plan/STATUS.md`: what is merged, what is running (package, stage, branch, the run id and the script path of the wave), what waits for the owner, which decisions were taken, the two usage numbers. After a stop the lead reads this file, not the conversation.

## When the limit hits

What continues by itself and what does not (research/08, official documentation read 2026-11-21):

| Situation | Native behaviour | What we do |
|---|---|---|
| Interactive session on a claude.ai subscription | Claude waits for the reset and continues itself (`autoContinueAtUsageLimit`, `/rate-limit-options`), at most 3 times, reset under 24 h away | Nothing; keep the app open. A weekly limit is usually more than 24 h away: then see "After the reset" |
| Workflow in the same interactive terminal or the local Desktop Code tab | The run pauses and continues (at most 2 waits) | After a third hit: relaunch the wave (below) |
| Workflow in `claude -p`, a background session, Remote Control, a scheduled-task session | Not paused; the agents fail | Relaunch after the reset |

## After the reset

The lead, in the same chat or in a new one, does only this:

1. `git fetch`, read `docs/03-plan/STATUS.md`.
2. For every package marked running: `git log main..wp/<id>-<slug> --oneline`, then the "## Status" part of its status file (`git show wp/<id>-<slug>:docs/03-plan/wip/WP-<id>.status.md`).
3. **Relaunch the wave.** Either call the Workflow tool with the script path and the run id that the first launch printed (`scriptPath`, `resumeFromRunId`, the same `args`): agents that finished answer from the saved results, the first failed or unfinished one and everything after it run live. Or start a new wave with `from` set to the stage where each package stopped. Do not edit the prompts of finished agents before a resume: an edited call and every later call run again. A relaunch never repeats work that is committed, because every stage reads the branch and the status file first.
4. If the lead session is the same and a single sub-agent was stopped, `SendMessage` to it is the cheapest continuation.
5. If the pause was long and the lead's conversation is large, the owner starts a **new** lead chat with the start phrase of `README.ru.md`. Cache facts: the main conversation keeps its prompt cache for 1 hour on a subscription within plan usage, sub-agents and workflow agents for 5 minutes. After that a miss is billed at the cache-write rate (1.25 times the base price for 5 minutes, 2 times for 1 hour), not the read rate (0.05 times on Opus 5.5 and Sonnet 5.5, 0.025 times on Fable 5.2) (research/08).

## Automatic continuation

The protocol guarantees that a single message "continue from STATUS.md" is enough, and that a scheduled reminder or an external watcher can send exactly that message without knowing anything else. Details of the native mechanisms: [`research/08-claude-code-multi-agent-token-economy.md`](../../research/08-claude-code-multi-agent-token-economy.md), section 2.9.

A watcher must never poll with the model (`/loop` and cron cost a full-context turn per tick). A watcher is a script that sleeps, checks a cheap condition (reset time reached, a branch has a new commit, a file appeared), and only then wakes the lead.
