# CLAUDE.md

Read [`AGENTS.md`](AGENTS.md): it is the single source of rules for this repository. Lead agent: start with [`START_HERE.md`](START_HERE.md).

@AGENTS.md

## Claude Code specifics

- Open the session in the folder of this repository: only then the project's agents, skills, workflow and settings load.
- Sub-agent types (`.claude/agents/`): `wp-builder` (by-spec stages, shell and files, middle tier), `wp-thinker` (core stage of packages whose design is open, the session's model), `wp-reviewer` (read-only review of one package, `opus`), `web-researcher` (one fact from the web). Never start a general-purpose agent for build work.
- Waves of packages: the saved workflow `wp-wave` (`.claude/workflows/wp-wave.js`). At most three packages at once.
- Skills (`.claude/skills/`): `track-f-lead` for the lead, `lane-work` for a builder, `coi-partner-json` for anything that writes or checks the partner's JSON, `eden-credits` for the partner's model credits.
- Compact instructions: when compacting keep the work-package ids and their stages, branch names, the state of `docs/03-plan/STATUS.md`, the run id and script path of a running wave, open questions to the owner, and the output of failing checks.
