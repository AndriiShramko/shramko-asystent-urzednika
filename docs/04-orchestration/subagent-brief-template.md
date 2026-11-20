# Sub-agent brief template

A sub-agent knows only what its brief says and what it reads from the repository. A good brief is short and points to files; it does not retell them. Copy the block below, fill the angle brackets, and send it as the whole prompt.

```
You are the builder of work package <WP-id> "<title>" in the repository <absolute path of the worktree>.
Your branch: wp/<id>-<slug>. Work only inside this worktree.

RESUME-FIRST: before anything run `git log main..HEAD --oneline`, `git status --short` and read
"## Status" in docs/03-plan/wip/WP-<id>.status.md. If work exists, you are continuing it: never redo
committed steps or re-run checks that passed for unchanged inputs; uncommitted files are your
predecessor's work in progress: inspect the diff, finish or revert it, commit first.
CHECKPOINTS: commit after every finished step and update the Status checklist in the same commit;
commit before any run longer than 2 minutes.

READ (in this order, only these):
1. AGENTS.md  (rules; 5 minutes)
2. docs/03-plan/work-packages/WP-<id>-<slug>.md  (your task, acceptance list, owned paths)
3. <1-3 specific sections, for example docs/02-architecture/ai-layer.md#triage and contracts/openapi.yaml paths /cases*>

DO: exactly what the work package says. Paths you may edit are listed in it; do not touch anything else.
If you need a change outside your paths (API contract, shared schema, another module), do not make it:
write it under "## Requests to lead" in your status file and continue against a mock.

DONE means: every item of the acceptance list passes, shown by the command output; `tools/gate.sh fast`
passes; one negative control (break the behaviour, see the test fail, restore) is recorded in the status file.

COST: every reply re-reads your whole context. Read a file by the needed part, once. Batch independent
reads and commands in one message. Keep command output under 3,000 tokens (tail, counts, logs to a file).
Write files with the file-writing tool, never a shell heredoc. Use synthetic test data only
(tools/testdata). Before returning add one line to "## Cost notes": what took the most turns and what
would make it cheaper.

REPORT (your final message, at most 15 lines): what is done with commit hashes; what is proven, with
numbers; what is not verified and why; requests to lead; next step if you ran out of budget.
```

## Choosing the agent type, model and effort

| Kind of stage | Agent type | Model tier | Effort |
|---|---|---|---|
| Implementation from a ready work package (code, tests, wiring) | slim builder: shell and files only | middle tier | medium |
| Design of something not yet specified, hard debugging, security-sensitive code (crypto, auth, PII) | builder | top tier | high |
| Independent review of a diff against an acceptance list | reviewer: read-only + shell | top tier | high |
| Web research (new facts from the hackathon briefing, library checks) | researcher: web + files | top tier or middle | medium–high |
| Bulk mechanical work (rename, format, generate fixtures, run and summarise) | slim builder or a plain script with no model | small or middle tier | low–medium |

Name models by alias (the tier name without a version number) so the brief stays valid when versions change. A small model does selection and labelling, never judgement.

## Size limits

- One stage = one kind of work on named files, planned for at most about 30 replies. Larger work is split into stages; each ends with a commit and a status line, and the next stage starts in a fresh agent.
- An agent is worth starting for at least about 10 replies of work or a large read. Anything smaller the lead does itself.
- At most 3 builders run at the same time unless the owner raises the limit.
