# Continuing after a usage limit, a crash or a restart

Work that cannot be resumed from the middle is paid for twice. In this repository every unit of work is resumable by construction; this page says how.

## What survives and what does not

| Survives | Does not survive |
|---|---|
| Commits on work-package branches | Uncommitted edits in a worktree that is deleted |
| Status files (`docs/03-plan/wip/*.status.md`, `docs/03-plan/STATUS.md`) | A sub-agent stopped by the user with `x` in `/tasks` (it does not resume by itself); a sub-agent whose lead session is gone (resuming from a new session is unverified) |
| A stopped sub-agent's history: the lead sends it a message (`SendMessage` by agent id or name) in the same session and it continues with its full context; a sub-agent stopped at `maxTurns` returns partial output and can be resumed the same way. Transcripts stay in `~/.claude/projects/<project>/<session>/subagents/` for `cleanupPeriodDays` (30) (research/08, official documentation read 2026-11-21) | Anything that existed only in a chat message |
| Results of finished agents inside a Workflow run (see below) | |
| Files written to disk before the stop | |

Fallback that always works: replace the sub-agent with a fresh one, same brief, RESUME-FIRST block.

## Rules that make resuming cheap

1. **A checkpoint is a commit.** After each finished step: commit plus the status checklist in the same commit. Before any run longer than two minutes: commit first.
2. **Status file is the input for continuation, not a report.** `[x]` done (with commit), `[~]` in progress (what exactly), `[ ]` left.
3. **Every brief starts with RESUME-FIRST** (see [`subagent-brief-template.md`](subagent-brief-template.md)). Re-sending the same brief then costs minutes, not a restart.
4. **Stages are small.** "Implement the whole module" is two or three agents in sequence (core, integration, acceptance), not one.
5. **Heavy checks are keyed on their inputs.** A check writes its evidence with the commit hash it ran on; if the hash matches, nobody runs it again.
6. **The lead keeps a handoff.** Before any long wait the lead writes in `docs/03-plan/STATUS.md`: what is merged, what is running (branch, package, agent), what waits for the owner, which decisions were taken. After a stop the lead reads this file, not the conversation.

## When the limit hits

What continues by itself and what does not (research/08, official documentation read 2026-11-21):

| Situation | Native behaviour | What is scripted |
|---|---|---|
| Interactive session on a claude.ai subscription (v2.1.234+) | Claude waits for the reset and continues itself (`autoContinueAtUsageLimit`, `/rate-limit-options`), at most 3 times, reset under 24 h away | Nothing; keep the app open. Weekly limits usually exceed 24 h |
| Workflow in the same interactive terminal or local Desktop Code tab (v2.1.271+) | The run pauses and continues (at most 2 waits) | After a third hit: relaunch the workflow |
| Workflow in `claude -p`, background session (`claude --bg`), Remote Control, teammate, scheduled-task session | Not paused; the agent fails. Behaviour of `--bg` at the limit: unverified | Relaunch after the reset by a script |
| Headless `claude -p` | Non-zero exit and a JSON result; `--resume <session_id>` continues | A script finds the reset time (field names unverified: capture one real sample), sleeps, then `claude -p --resume <id> "continue from STATUS.md"`; or a `StopFailure` hook with matcher `rate_limit` writes a marker file for the watcher |

After the reset the lead (same chat or a new one) does only this:

1. `git fetch`, read `docs/03-plan/STATUS.md`.
2. For every package marked running: `git log main..wp/<id> --oneline`, read its status file.
3. Try to resume the stopped sub-agent with `SendMessage` if the lead session is the same; otherwise restart each unfinished package with the same brief. Do not re-run finished packages.
4. If a Workflow run was interrupted, relaunch the same script: finished agents return their saved results. An edited prompt re-runs from the first changed agent and every later one; a failed agent in the middle re-runs everything after it; "nothing to resume" means the results are gone. After "Exit and stop tasks" run `claude --resume` first. Do not edit the prompts of finished agents.
5. If the pause was long and the lead's conversation is large, start a **new** lead session from `START_HERE.md` and `STATUS.md`. Cache facts: the main conversation keeps its prompt cache for 1 hour only on a subscription within plan usage, otherwise 5 minutes; sub-agents and workflow agents 5 minutes unless `subagentPromptCacheTtl` is `"1h"`. After the time to live a miss is billed at the cache-write rate (1.25x base for 5 minutes, 2x for 1 hour), not the read rate (0.05x on Opus 5.5 and Sonnet 5.5, 0.025x on Fable 5.2). Settings: `promptCacheTtl`, `subagentPromptCacheTtl`; `/usage` shows a `Prompt cache (main)` line, warm or cold (research/08, official documentation read 2026-11-21).

## Automatic continuation

The protocol guarantees that a single message "continue from STATUS.md" is enough, and that a scheduled reminder or an external watcher can send exactly that message without knowing anything else. Details of the native mechanisms: [`research/08-claude-code-multi-agent-token-economy.md`](../../research/08-claude-code-multi-agent-token-economy.md), section 2.9.

A watcher must never poll with the model (`/loop` and cron cost a full-context turn per tick). A watcher is a script that sleeps, checks a cheap condition (reset time reached, branch has a new commit, file appeared), and only then wakes the lead.
