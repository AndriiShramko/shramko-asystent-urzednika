# Git workflow for many agents in one repository

Goal: several agents build at the same time and never overwrite each other; any agent can stop at any moment and another can continue from git alone.

## Branches and worktrees

| Thing | Rule |
|---|---|
| `main` | Always passes the fast gate (`tools/gate.sh fast`). Only the lead merges into it. Nobody commits feature work directly to `main`. |
| Work-package branch | `wp/<id>-<slug>`, for example `wp/A2-triage`. Created from the current `main` by the lead when the package starts. |
| Worktree | One per running package, in `.worktrees/<id>` (git-ignored): `git worktree add .worktrees/A2 -b wp/A2-triage main`. An agent works only inside its own worktree. If the harness offers worktree isolation for sub-agents, use that instead of creating worktrees by hand. |
| Contract branch | Changes to `contracts/openapi.yaml` and to `data/*.schema.json` are made by the lead on `main` (small, reviewed, announced in `docs/03-plan/STATUS.md`). A builder who needs a contract change writes a request in its status file and continues with a local mock. |

Do not create junctions or symlinks from a worktree to another worktree's `node_modules` or `.venv`; install dependencies per worktree or use the package manager's shared cache.

## Ownership

[`docs/03-plan/ownership.md`](../03-plan/ownership.md) maps every path to exactly one work package. An agent edits only paths it owns. Files that many packages would otherwise touch are designed away:

- Each backend module registers its routes in its own file; the application discovers modules by convention (no central list to edit).
- Each front-end feature lives in its own folder with its own route file.
- Dependencies: a builder may add a dependency only to its own package manifest; shared manifests are changed by the lead.
- Shared documentation (`README*`, `AGENTS.md`, `docs/03-plan/STATUS.md`) is lead-only.

## Commits

- Commit after every finished step, and always before starting anything that runs longer than two minutes.
- Message: `WP-<id>: <what changed>`; body optional; one logical step per commit.
- The same commit updates the `## Status` checklist in `docs/03-plan/wip/WP-<id>.status.md`.
- Never commit: secrets, `.env`, vendor SDK or licence files, downloaded form templates, real personal data, build output. The pre-commit check is `tools/precommit_scan.py` (secrets and identifier patterns); a hit blocks the commit.
- Never run `git add -A` or `git add .`; add the paths you changed.
- No `git stash`, no rebase, no force push, no history rewriting. To pick up new `main`: `git merge main` inside the worktree.

## Merge queue (lead)

1. Builder reports "ready" with the commit hash and the gate result.
2. Lead (or a merge agent) runs in the worktree: `git merge main` → `tools/gate.sh fast`.
3. One independent review of the diff (`git diff main...wp/<id>`) against the package's acceptance list.
4. `git checkout main && git merge --no-ff wp/<id>-<slug>` → `tools/gate.sh fast` on `main` → push.
5. Update `docs/03-plan/STATUS.md`; remove the worktree (`git worktree remove .worktrees/<id>`); keep the branch until the milestone is accepted.
6. At a milestone: `tools/gate.sh full` (end-to-end, accessibility, visual regression of forms) once, on `main`.

Merges go in dependency order from [`docs/03-plan/roadmap.md`](../03-plan/roadmap.md). When two ready branches conflict, the lead merges the one that owns the conflicting path first and sends the other back with the conflict list.

## Recovering

- Agent died mid-step: a new agent with the same brief starts with the RESUME-FIRST block (see [`subagent-brief-template.md`](subagent-brief-template.md)), inspects `git status` and the status file, finishes or reverts uncommitted work, commits, continues.
- Broken `main`: `git revert` of the merge commit, never a reset; open the package again.
- Lost worktree folder: `git worktree prune`, then add it again from the branch; nothing is lost because every step was committed.
