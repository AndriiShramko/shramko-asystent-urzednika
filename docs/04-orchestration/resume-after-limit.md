# Continuing after a usage limit, a crash or a restart

Work that cannot be resumed from the middle is paid for twice. In this repository every unit of work is resumable by construction; this page says how.

## What survives and what does not

| Survives | Does not survive |
|---|---|
| Commits on work-package branches | Uncommitted edits in a worktree that is deleted |
| Status files (`docs/03-plan/wip/*.status.md`, `docs/03-plan/STATUS.md`) | A sub-agent's context: a stopped sub-agent cannot be "continued", only replaced |
| Results of completed sub-agents inside an orchestration run that supports resume | A running sub-agent's partial result |
| Files written to disk before the stop | Anything that existed only in a chat message |

## Rules that make resuming cheap

1. **A checkpoint is a commit.** After each finished step: commit plus the status checklist in the same commit. Before any run longer than two minutes: commit first.
2. **Status file is the input for continuation, not a report.** `[x]` done (with commit), `[~]` in progress (what exactly), `[ ]` left.
3. **Every brief starts with RESUME-FIRST** (see [`subagent-brief-template.md`](subagent-brief-template.md)). Re-sending the same brief then costs minutes, not a restart.
4. **Stages are small.** "Implement the whole module" is two or three agents in sequence (core, integration, acceptance), not one.
5. **Heavy checks are keyed on their inputs.** A check writes its evidence with the commit hash it ran on; if the hash matches, nobody runs it again.
6. **The lead keeps a handoff.** Before any long wait the lead writes in `docs/03-plan/STATUS.md`: what is merged, what is running (branch, package, agent), what waits for the owner, which decisions were taken. After a stop the lead reads this file, not the conversation.

## When the limit hits

- Usage limits arrive for everything at once: all running sub-agents stop together. That is why the pool is at most three wide and why a half-used window gets a smaller next wave.
- After the reset the lead (same chat or a new one) does only this:
  1. `git fetch`, read `docs/03-plan/STATUS.md`.
  2. For every package marked running: `git log main..wp/<id> --oneline`, read its status file.
  3. Restart each unfinished package with the same brief. Do not re-run finished packages.
  4. If an orchestration run was interrupted and the tool supports resuming a run, resume it rather than starting a new one: finished agents return their cached results.
- If the pause was long (an hour or more) and the lead's conversation is large, start a **new** lead session from `START_HERE.md` and `STATUS.md` instead of waking the old one: after the prompt cache expires, the first step of a large session re-sends the whole conversation at full price.

## Automatic continuation

Whether the application resumes an interrupted turn by itself depends on the surface and its version. Check [`research/08-claude-code-multi-agent-token-economy.md`](../../research/08-claude-code-multi-agent-token-economy.md) for what exists today. Independently of that, this protocol guarantees that a single message "continue from STATUS.md" is enough, and that a scheduled reminder or an external watcher can send exactly that message without knowing anything else.

A watcher must never poll with the model. A watcher is a script that sleeps, checks a cheap condition (reset time reached, branch has a new commit, file appeared), and only then wakes the lead.
