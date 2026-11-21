# R8 - Claude Code multi-agent playbook and token economy (state of 2026-11-21)

Access date for every source below: 2026-11-21. Status labels: VERIFIED = I opened the primary page (official docs) and read the statement; UNVERIFIED = not found or only inferred. Prices are USD per million tokens (MTok).

## TL;DR for builders

- Native orchestration exists in three forms: subagents (`.claude/agents/*.md`), **dynamic workflows** (a JavaScript script run by the Workflow tool, `/workflows`, keyword `ultracode`), and **agent teams** (experimental, off by default). For this repo use subagents or a workflow for build packages; do not use agent teams for parallel implementation (same-file overwrite risk, about 7x tokens in plan mode). VERIFIED.
- `worktree.baseRef` defaults to `"fresh"` = the REMOTE default branch, not your local `main`. A subagent worktree will not contain unpushed merges. Either push `main` after every merge or set `{"worktree":{"baseRef":"head"}}`. This contradicts `docs/04-orchestration/git-workflow.md` assumptions. VERIFIED.
- Subagents CAN be resumed with their full history (`SendMessage` to the agent ID/name; `maxTurns` stop returns partial output that can be resumed). `resume-after-limit.md` says the opposite. VERIFIED.
- Native limit handling exists but is narrow: in an interactive claude.ai-subscription session (v2.1.234+) Claude waits for the reset and continues itself (up to 3 times, reset must be under 24 h away). It does NOT work in `claude -p`, background sessions, Remote Control or agent-team teammates. Workflows pause at the limit instead of failing (v2.1.271+, interactive terminal or local Desktop Code tab only, max 2 waits). Everything else must be scripted. VERIFIED.
- Concurrency limits: 20 subagents (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`), 16 workflow agents (`CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS`), 1,000 agents per workflow run. Our width of 3 is a policy for cost and merge bandwidth, not a platform limit. VERIFIED.
- Cache economics changed: cache read is 0.025x base on Fable 5.2 and 0.05x on Opus 5.5 / Sonnet 5.5 (0.1x elsewhere). Default TTL in Claude Code: 1 h for the main conversation only on a subscription within plan usage; 5 min for API key and for ALL subagents/workflow agents unless `subagentPromptCacheTtl: "1h"`. VERIFIED.
- Model routing aliases: `fable` (=Fable 5.2, `claude-fable-5-2`), `opus` (Opus 5.5, `claude-opus-5-5`), `sonnet` (Sonnet 5.5 on the Anthropic API only), `haiku` (Haiku 5.5 on the Anthropic API only). Effort levels `low|medium|high|xhigh|max`; thinking cannot be switched off on Fable/Opus 5.5/Sonnet 5.5/Haiku 5.5 in Claude Code. VERIFIED.
- Product API: Opus 5.5 $4/$20, Sonnet 5.5 $2/$10, Haiku 5.5 $0.10/$0.50 (up to 100k prompt), Fable 5.2 $8/$40. Estimated warm-cache cost per UDIP request: Haiku about $0.0015, Sonnet about $0.025, Opus about $0.05, Fable about $0.09 (assumptions in section 5). ESTIMATE.
- Citations and structured outputs (`output_config.format`) cannot be combined in one request; plan two calls or pick citations for grounded drafting and JSON schema for triage. VERIFIED.
- First-party API data residency offers only `inference_geo` = `"us"` or `"global"`; workspace geo is `"us"` only. There is no EU inference option on the Claude API; EU-region serving would have to come from a partner cloud endpoint (not verified here, see R5). VERIFIED for the first-party API.
- Hackathon-night rule: encode the loop in files and shell scripts first (status files, `gate.sh`, worktree creation); use the Workflow tool only for fan-out stages whose result is a JSON report. A stage without decisions is a shell command, not an agent. Consistent with Anthropic's own harness advice (progress file, feature list JSON, git commits as checkpoints, one feature per session). VERIFIED.

## 1. Mechanism table

Columns: mechanism | what it does | how to enable | when it helps | pitfalls | doc | status.

### 1.1 Claude Code orchestration

| Mechanism | What it does | Enable | When it helps | Pitfalls | Doc | Status |
|---|---|---|---|---|---|---|
| Subagents | Own context window, own tool set; only the final result returns to the lead | `.claude/agents/<name>.md` with frontmatter (`name`, `description` required); or `--agents '<json>'` for one session | Isolating verbose work; routing cheap models to mechanical work | Each invocation is a NEW instance unless resumed; description budget warns above 15,000 tokens of combined descriptions | https://code.claude.com/docs/en/sub-agents | VERIFIED |
| Subagent frontmatter | `tools`, `disallowedTools`, `model` (alias, full ID or `inherit`), `effort`, `maxTurns`, `isolation: worktree`, `background`, `memory`, `skills`, `hooks`, `permissionMode`, `omitClaudeMd`, `autoCompactWindow` (min 100000), `mcpServers`, `initialPrompt` | In the agent file; unknown fields are silently ignored; names are camelCase and case-sensitive | Slim builders: `tools` allowlist | Plugin subagents ignore `hooks`, `mcpServers`, `permissionMode` | same | VERIFIED |
| Model resolution for subagents | Order: per-invocation `model` (alias only) > agent `model` > `CLAUDE_CODE_SUBAGENT_MODEL` > parent model | Env `CLAUDE_CODE_SUBAGENT_MODEL`, force with `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` (v2.1.257+) | One cheap model for all helpers | Explore/Plan/general-purpose inherit the parent (Opus/Fable lead = expensive explorers) | same | VERIFIED |
| Background subagents | Subagents spawned from the main conversation start in the background by default; completion arrives as a notification | Default; `Ctrl+B` moves a running task; `CLAUDE_CODE_FORK_SUBAGENT=0` makes Claude wait; `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` disables | Lead stays free; no polling | Background subagents have a smaller tool set; permission prompts surface in the main session; `/tasks` lists them | same | VERIFIED |
| Resume subagent | Continue a finished or `maxTurns`-stopped subagent with full history | Claude uses `SendMessage` with agent ID or name (no agent teams needed) | Continuing after a limit, a stop or a review round | A subagent stopped by you with `x` in `/tasks` does not auto-resume; transcripts live in `~/.claude/projects/<project>/<session>/subagents/agent-<id>.jsonl` and are deleted after `cleanupPeriodDays` (30) | same | VERIFIED |
| Nesting and concurrency | Subagents may spawn subagents, 3 layers by default | `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (`1` disables nesting); concurrent cap 20, override `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` | Keep the tree flat: omit `Agent` from workers' `tools` | Resumes ignore the concurrency check | same | VERIFIED |
| Worktrees | Own checkout and branch per session | `claude --worktree <name>` (or `-w`) creates `.claude/worktrees/<name>` on branch `worktree-<name>`; `isolation: worktree` in agent frontmatter; `EnterWorktree` tool; manual `git worktree add` | The core of "one package = one branch = one worktree" | Branch name is not selectable with `--worktree` (use manual `git worktree add -b wp/...`, or let the worker `git branch -m`); base is remote default branch unless `worktree.baseRef: "head"`; `-p` worktrees are never auto-cleaned; subagent worktrees with changes stay until the `cleanupPeriodDays` sweep; `.worktreeinclude` copies gitignored files (`.env`); a subagent in its own worktree takes CLAUDE.md and rules from the MAIN conversation, not from the worktree | https://code.claude.com/docs/en/worktrees | VERIFIED |
| Dynamic workflows (Workflow tool) | A JS script orchestrates up to hundreds of agents; intermediate results stay in script variables; lead context holds only the final answer | Ask "use a workflow", include keyword `ultracode`, or `/effort ultracode`; run saved ones as `/<name>`; `/workflows` to watch (`p` pause, `x` stop, `r` restart agent, `s` save to `.claude/workflows/`) | Fan-out audits, migrations, cross-checked research; resumable in the same session | No mid-run user input; no module imports; `Date.now()`/`Math.random()` throw; 16 concurrent agents, 4,096 items per `parallel()`/`pipeline()`, 1,000 agents per run; `Large workflow` warning above 25 agents or 1.5M projected tokens; `claude -p` does not pause at usage limits | https://code.claude.com/docs/en/workflows | VERIFIED |
| Workflow script API | `agent(prompt,{schema,label,stallMs})`, `pipeline(items,fn)`, `parallel([...])`, `phase(title)`, `log()`, global `args`, `export const meta={name,description}` | In the script; `/workflow-authoring` bundled skill loads the reference | Structured JSON returns | `agent()` returns `null` if stopped; schema retried 5 times (`MAX_STRUCTURED_OUTPUT_RETRIES`); a per-agent `model` option and an `isolation` option are implied by the docs but their exact names were NOT shown on the page I read: UNVERIFIED, check `/workflow-authoring` before relying on them | same | VERIFIED (core) / UNVERIFIED (model, isolation option names) |
| Workflow permissions | Workflow start is itself a permission-checked tool call | Allow rule `Workflow` or `Workflow(<name>)`; auto mode; bypass mode; PreToolUse hook returning allow | Unattended runs | In plan mode a hook alone does not start it | same | VERIFIED |
| Workflow size and disable | Advice to Claude on agent count | `workflowSizeGuideline`: `small` (<5), `medium` (<10, default), `large` (<50), `unrestricted`; `disableWorkflows: true` or `CLAUDE_CODE_DISABLE_WORKFLOWS=1` | Keep cost bounded | Advice, not a cap; the runtime caps still apply | same | VERIFIED |
| Ultracode | Session setting: Claude plans a workflow for each substantive task | `/effort ultracode`, `claude --effort ultracode` (also sets `xhigh`), setting `"ultracode": true` | Not for us tonight | Uses far more tokens; exempts the 20-subagent cap and the large-workflow warning | https://code.claude.com/docs/en/model-config | VERIFIED |
| Workflow prompt-cache sharing | Same-prefix agents in one fan-out read the first agent's cache; others are held up to 5 s | `CLAUDE_CODE_WORKFLOW_PREFIX_STAGGER_MS` (default 5000, `0` disables); give agents identical model, effort, tools, schema, cwd | Cheap fan-out | Agents with different tool sets or schemas do not share a prefix | same | VERIFIED |
| Agent teams | Peer sessions with shared task list and mailbox | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `env`; `teammateMode` (`auto`, `tmux`, `iterm2`) | Research and review debates | Experimental; no `/resume` of in-process teammates; teammates inherit the lead's permission mode (even bypass); while enabled, a NAMED subagent launches as a teammate; start with 3-5 | https://code.claude.com/docs/en/agent-teams | VERIFIED |
| Agent view / background sessions | `claude --bg "<prompt>"`, `claude agents`, `claude attach|logs|stop|respawn <id>`; sessions run under a supervisor and survive terminal exit; each moves into its own worktree before editing | Commands as listed; `worktree.bgIsolation: "none"` turns isolation off | Many independent sessions without a lead holding them | Research preview; each session spends subscription quota independently; machine shutdown stops them (restart with `respawn`); behaviour at usage limit not read (UNVERIFIED) | https://code.claude.com/docs/en/agent-view | VERIFIED / UNVERIFIED (limits) |
| `claude -p` headless | Non-interactive runs; JSON result with `session_id`, `total_cost_usd`, per-model cost | `claude -p "<prompt>" --output-format json [--json-schema ...] --allowedTools ... --permission-mode dontAsk|acceptEdits|auto --permission-prompts none --resume <session_id> --continue --append-system-prompt ... --bare` | Scripted pipeline; shell holds the loop | `--bare` skips hooks, skills, CLAUDE.md, subagents and does not use the subscription login (needs `ANTHROPIC_API_KEY`) - do NOT use `--bare` if you want CLAUDE.md and the subscription; `-p` runs start in Manual mode (v2.1.302+) so unlisted tools are denied; SIGTERM = exit 143; piped stdin cap 10 MB; the run waits for background work only 10 min (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`) | https://code.claude.com/docs/en/headless | VERIFIED |
| Hooks | Deterministic gates and preprocessing | `settings.json` `hooks`; events include `PreToolUse`, `PostToolUse`, `PostToolBatch`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `Stop`, `StopFailure` (matcher includes `rate_limit`), `PreCompact`, `WorktreeCreate/Remove`, `PreModelSwitch`; handlers `command`, `http`, `mcp_tool`, `prompt`, `agent` | `exit 2` on `SubagentStop`/`TaskCompleted`/`Stop` forces the agent to continue (use for a gate run); `StopFailure` with `rate_limit` can write a marker for a watcher; `PreToolUse` can cut `npm test` output to the last 100 lines | Only exit code 2 blocks; exit 1 is non-blocking; there is no dedicated rate-limit event | https://code.claude.com/docs/en/hooks | VERIFIED |
| Skills | On-demand instructions; only the description sits in context | `.claude/skills/<name>/SKILL.md`; fields `description`, `disable-model-invocation`, `context: fork`, `agent`, `model`, `effort`, `allowed-tools`, `paths` | Move rarely used instructions out of CLAUDE.md | Description plus `when_to_use` truncated at 1,536 characters; invoked skill body stays in context | https://code.claude.com/docs/en/skills | VERIFIED |
| CLAUDE.md / AGENTS.md / rules | Persistent instructions | `./CLAUDE.md`; AGENTS.md is read natively (v2.1.277+) ONLY when no CLAUDE.md or CLAUDE.local.md exists; otherwise import with `@AGENTS.md`; `.claude/rules/*.md` with `paths:` frontmatter; `claudeMdExcludes` | Short root file; target under 200 lines | If both files exist, AGENTS.md is ignored unless imported; `omitClaudeMd: true` on a subagent skips it | https://code.claude.com/docs/en/memory | VERIFIED |
| Auto memory | Claude-written notes, first 200 lines or 25 KB of `MEMORY.md` loaded | On by default; subagent `memory: project|user|local` | Personal agents | Per repository, shared across worktrees; not a place for the plan | same | VERIFIED |
| Effort | Controls thinking depth and token spend | `/effort <level>`, `claude --effort`, `CLAUDE_CODE_EFFORT_LEVEL`, `effortLevel` (no `max`), `modelSettings.<model>.effortLevel`, `effort:` in skill/subagent frontmatter | The main per-task cost knob | `max` applies to the session only; changing effort keeps the cache only on Fable 5.1+, Opus 5.5, Sonnet 5.5, Haiku 5.5 | https://code.claude.com/docs/en/model-config | VERIFIED |
| Context hygiene | Keep conversation small | `/clear` between tasks, `/compact <focus>`, "Compact instructions" section in CLAUDE.md, `autoCompactWindow` (>= 100000), `idleCompaction: false`, `/context`, `/usage` | Lead session | `/compact` reads the whole conversation (large request after a cold gap); a model switch or MCP/tool change invalidates the cache | https://code.claude.com/docs/en/costs | VERIFIED |
| Prompt-cache TTL in Claude Code | Choose 5 m or 1 h | `promptCacheTtl` / `CLAUDE_CODE_PROMPT_CACHE_TTL` (main), `subagentPromptCacheTtl` / `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL` (subagents, workflows, teammates, compaction), `ENABLE_PROMPT_CACHING_1H=1`, `FORCE_PROMPT_CACHING_5M=1` | Idle gaps over 5 min; API-key billing | 1 h writes cost 2x base; defaults described in TL;DR | https://code.claude.com/docs/en/prompt-caching | VERIFIED |
| MCP tool search | MCP tool definitions deferred by default; only names enter context | Default on supported models; `/mcp` to disable servers; prefer CLI (`gh`) over MCP | Keeps the system prefix stable | Tool-set changes mid-session invalidate cache when tools are loaded up front | https://code.claude.com/docs/en/costs | VERIFIED |
| Usage limit auto-continue | Wait in the open session and continue after the reset | `autoContinueAtUsageLimit` (user or managed settings), `/rate-limit-options`; v2.1.234+ | Interactive lead on a subscription | See TL;DR; stops after 3 continuations; permissions still prompt | https://code.claude.com/docs/en/interactive-mode | VERIFIED |
| Scheduled tasks | `/loop` and cron tools inside a session; cloud "scheduled tasks" (formerly routines); Desktop scheduled tasks | `/loop 10m <prompt>`; docs `scheduled-tasks`, `routines`, `desktop-scheduled-tasks` | Wake-ups | A session-scoped task fires while idle and re-sends the full context each time; a workflow does not pause at the limit in a scheduled-task session | https://code.claude.com/docs/en/scheduled-tasks | PARTLY read (index and costs page; details UNVERIFIED) |
| Checkpointing | `/rewind` restores conversation and code edits | `/rewind` or double Esc | Backing out of a wrong path | Not a substitute for git commits | https://code.claude.com/docs/en/checkpointing | index only, UNVERIFIED details |
| Cloud sessions | Run in Anthropic's cloud from browser or `--cloud`, `--teleport` | https://code.claude.com/docs/en/claude-code-on-the-web | Not planned for the hackathon (needs the repo on GitHub) | not read | - | UNVERIFIED |

### 1.2 Developer-platform mechanisms (for the product's own LLM calls)

| Mechanism | What it does | Parameter | Notes | Doc | Status |
|---|---|---|---|---|---|
| Prompt caching | Reuse a processed prefix | top-level `"cache_control":{"type":"ephemeral"}` (automatic) or on blocks; `"ttl":"1h"` | Order tools > system > messages; up to 4 explicit breakpoints (automatic uses 1); minimum cacheable 512 tokens on Fable 5.x, Opus 5/5.5, Sonnet 5.5, Haiku 5.5; cache is available only after the first response starts (send one request, wait, then fan out); 1 h write 2x, 5 m write 1.25x, read 0.1x (0.05x Opus 5.5 / Sonnet 5.5, 0.025x Fable 5.2); isolated per workspace | https://platform.claude.com/docs/en/build-with-claude/prompt-caching | VERIFIED |
| Structured outputs | Schema-constrained JSON | `output_config.format = {"type":"json_schema","schema":{...}}`; `strict: true` on tools | Stable; no recursive schemas, no `oneOf`, no numeric or string length constraints, `additionalProperties:false` required; grammar cached 24 h; changing `output_config.format` invalidates the prompt cache for the thread; first call per schema is slower | https://platform.claude.com/docs/en/build-with-claude/structured-outputs | VERIFIED |
| Citations | Passage-level grounding | `document` blocks with `"citations":{"enabled":true}` (types include char and page locations, search results) | `cited_text` does not count toward output tokens; document blocks can carry `cache_control`; citation blocks themselves are not cached; INCOMPATIBLE with structured outputs (400) | https://platform.claude.com/docs/en/build-with-claude/citations | VERIFIED |
| Effort (API) | Thinking depth and all output tokens | `output_config.effort` = low, medium, high, xhigh, max | API defaults: Fable 5.2 high, Opus 5.5 medium, Sonnet 5.5 high, Haiku 5.5 medium; per-message effort changes keep the cache on supported models; changing the top-level value can invalidate cache; thinking cannot be disabled on Fable 5.2 / Opus 5.5 (400); Sonnet 5.5 accepts `thinking:{"type":"between_tools"}` at low-high | https://platform.claude.com/docs/en/build-with-claude/effort | VERIFIED |
| Batch API | Async, 50% off | Message Batches endpoint; each request has `custom_id` (1-64 chars) | 100,000 requests or 256 MB per batch; most finish within 1 h, hard expiry 24 h; results kept 29 days; not ZDR-eligible; use the 1 h cache TTL inside batches; discounts stack with caching and `inference_geo` | https://platform.claude.com/docs/en/build-with-claude/batch-processing | VERIFIED |
| Context editing and compaction | Server-side clearing of old tool results and thinking; `compact_20260112` edit for compaction | beta header `context-management-2025-06-27`; `context_management.edits` with `clear_tool_uses_20250919`, `clear_thinking_20251015` | Only for long agent loops; clearing invalidates the cache (use `clear_at_least`) | https://platform.claude.com/docs/en/build-with-claude/context-editing | VERIFIED (compaction detail UNVERIFIED) |
| Memory tool | Client-implemented file memory | tool type `memory_20250818`, name `memory` | Not needed for stateless UDIP calls | same page | VERIFIED |
| Tool search | Load tools on demand | `tool_search_tool_regex_20251119` or `tool_search_tool_bm25_20251119` plus `defer_loading:true` on tools | Worth it above about 10 tools or 10k tokens of definitions; a deferred tool cannot carry `cache_control` | https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool | VERIFIED |
| Programmatic tool calling | Code calls tools from the sandbox | not read | UNVERIFIED | https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling | UNVERIFIED |
| Token counting | Pre-flight counts (also reports pre-clearing tokens) | `count_tokens` endpoint | New tokenizer yields about 30% more tokens than Sonnet 4.6 and earlier: re-measure Polish legal text | https://platform.claude.com/docs/en/about-claude/pricing | VERIFIED |
| Data residency | Where inference runs | `inference_geo: "us"` or `"global"`; workspace `allowed_inference_geos`; 1.1x price for `"us"` | No EU value; workspace geo `us` only | https://platform.claude.com/docs/en/manage-claude/data-residency | VERIFIED |
| Fast mode | Up to 2.5x output speed at premium | Fable 5.2 $16/$80, Opus 5.5 $8/$40 | No batch; switching invalidates cache | https://platform.claude.com/docs/en/about-claude/pricing | VERIFIED |

## 2. Recommended operating model for this repository

### 2.1 Principles

1. The lead keeps a small context: it reads `AGENTS.md`, `docs/03-plan/STATUS.md`, the package list; it never reads feature code unless deciding. Every lead turn re-reads the whole conversation (cache read is cheap but not free; a cold cache re-writes everything).
2. Work packages are files (`docs/03-plan/work-packages/WP-<id>-<slug>.md`), status is files (`docs/03-plan/wip/WP-<id>.status.md`), truth is git. A message is never the only carrier of a fact (Anthropic's multi-agent article: workers write artifacts to the filesystem and pass references back to avoid the telephone game; harness article: progress file + JSON feature list + commits).
3. One package = one branch = one worktree = one worker. A worker edits only paths listed in `docs/03-plan/ownership.md`.
4. Anything without a decision is a script: `tools/gate.sh fast|full`, link checks, formatting, fixtures.
5. Multi-agent systems cost about 15x the tokens of a chat (Anthropic, multi-agent research system): spend them only where parallelism removes wall-clock time, i.e. 3 independent packages.

### 2.2 Choose the mode (decide once, tonight)

| Mode | How | Use when | Cost of a mistake |
|---|---|---|---|
| A. Interactive lead + subagents (recommended default) | Lead session spawns workers from `.claude/agents/builder.md` with `isolation: worktree`; workers run in the background; notifications return reports | Owner watches; 3 workers; simplest | Branches are named `worktree-<x>`: worker runs `git branch -m wp/<id>-<slug>` first; set `worktree.baseRef: "head"` or push `main` |
| B. Headless pipeline | A shell script creates worktrees with proper branch names and starts one `claude -p` per package, with a log and a status file; lead is a short interactive session that only merges | Overnight or when the lead session must stay tiny | Needs your own limit handling (section 2.9) |
| C. Workflow script | One workflow fans out N builders and returns JSON reports (section 3.5) | Fan-out of independent items (fixtures, form templates, UDIP test cases, review per file) | Cannot ask the owner mid-run; `claude -p` will not pause at limits |

Agent teams are not used.

### 2.3 Work package file (what a brief points to)

```
# WP-<id> <title>
Branch: wp/<id>-<slug>     Depends on: <ids merged>     Model/effort: sonnet/medium
Owned paths: <globs>       Forbidden: contracts/**, AGENTS.md, docs/03-plan/STATUS.md
Acceptance list: 1..N, each a command and expected output
Read: <1-3 sections>       Mock policy: use tools/testdata, no real PII
```

### 2.4 Ownership table (file `docs/03-plan/ownership.md`, one path pattern to exactly one owner)

| Path pattern | Owner | Rule |
|---|---|---|
| `contracts/**`, `data/*.schema.json` | lead | change on `main` only; builders write "Requests to lead" |
| `AGENTS.md`, `CLAUDE.md`, `README*`, `docs/03-plan/STATUS.md`, `.claude/**`, `tools/gate.sh` | lead | builders never edit |
| `backend/modules/<m>/**` | WP of module `<m>` | routes self-register; no central list |
| `frontend/features/<f>/**` | WP of feature `<f>` | own route file |
| `docs/03-plan/wip/WP-<id>.status.md` | that WP | the only shared-folder write |
| `package manifests` | the WP that adds the dependency to its OWN manifest | shared manifests lead-only |

Enforce with a hook, not with trust: a `PreToolUse` command hook on `Edit|Write` that reads `cwd` and the target path, looks up the owner in a generated `ownership.tsv` and exits 2 if the path is not owned by the current branch's WP. (The mechanism - PreToolUse exit 2 blocks - is VERIFIED; the script itself is yours to write, about 20 lines.)

### 2.5 Merge queue and gates

Lead or a merge worker, per ready branch, in order of `roadmap.md`: `git merge main` inside the worktree, `tools/gate.sh fast`, one independent reviewer on `git diff main...wp/<id>` against the acceptance list, `git merge --no-ff` into `main`, gate again, push. One `tools/gate.sh full` per milestone. Use `TaskCompleted` or `SubagentStop` hooks (exit 2) to make a worker run `gate.sh fast` before it may stop, so the lead never merges a red branch.

### 2.6 Routing and effort

| Work | Subagent type | Model | Effort | Why |
|---|---|---|---|---|
| Scope, contracts, ADRs | lead | `fable` or `opus` (session model) | medium to high | few steps, high value |
| Package from a ready spec | `builder` (slim) | `sonnet` | medium | Anthropic: start agentic coding at medium on Sonnet 5.5 |
| Crypto, auth, PII, legal-text generation | `builder-hard` | `opus` | high | always followed by review |
| Review against acceptance list | `reviewer` (read-only + Bash) | `opus` | high | independent check |
| Web research | `web-researcher` | `sonnet` (or `opus` for legal nuance) | medium | |
| Rename, format, fixtures, run-and-summarise | script, else `builder` | `haiku` | low-medium | Haiku 5.5 at `low` may skip checks in long prompts; do not use it for judgement |
| Product LLM calls | see section 5 | | | |

Set `CLAUDE_CODE_SUBAGENT_MODEL` only if you want everything on one model; otherwise name `model:` in each agent file. Do not change model or effort inside a running session unless needed: a model switch invalidates the cache (effort changes do not on 5.x models).

### 2.7 Width

Default 3 concurrent builders; 4-5 only for pure fan-out workflows. Reasons: (1) all agents draw on one subscription window and hit the limit together; (2) the merge queue is serial and the lead's review attention is the bottleneck; (3) Anthropic's research system itself launches 3-5 subagents in parallel for complex work; the docs recommend 3-5 teammates; (4) three cache-warm prefixes are cheaper than ten cold ones. The platform allows far more (20 subagents, 16 workflow agents).

### 2.8 Sub-agent report format and brief

Report (final message, at most 15 lines plus the status file): done items with commit hashes; evidence with numbers; not verified and why; "Requests to lead"; next step if budget ended. Brief: use `docs/04-orchestration/subagent-brief-template.md` with these additions: name the exact output (file path), the stop condition (acceptance list), the tool and source guidance, and the boundary (owned paths). Anthropic found briefs without objective, output format, tool guidance and boundaries caused duplicated work and gaps. Add an effort-scaling sentence ("one package, at most about 30 replies").

Commit convention (keep): `WP-<id>: <what>`; same commit updates the status checklist; never `git add -A`; no stash, rebase or force push; `git merge main` to catch up. Add trailer lines only if the owner wants attribution.

### 2.9 Continuing after the 5-hour limit: native versus scripted

| Situation | Native support | What you script |
|---|---|---|
| Interactive lead, claude.ai subscription | Auto-continue after reset (`autoContinueAtUsageLimit`, `/rate-limit-options`), max 3 times, reset < 24 h | Nothing; keep the app open; weekly limits usually exceed 24 h |
| Workflow running in the same interactive session | Run pauses and continues by itself (max 2 waits) | After a third hit or in `-p`: relaunch the workflow; finished agents return cached results (edited prompts re-run from the first changed agent) |
| Workflow in `claude -p`, background session, Remote Control, teammate, Dispatch, scheduled-task session | NOT paused; the agent fails | Relaunch after the reset; the saved results live under the session directory in `~/.claude/projects/`; exiting the app with "Exit and stop tasks" means `claude --resume`, then ask to relaunch |
| Subagent stopped by the limit | Resume with `SendMessage` (same session) | If the lead session died: restart the package from its status file and branch (this repo's protocol); resuming a subagent from a NEW lead session is UNVERIFIED |
| Headless `claude -p` | Exit code non-zero; JSON result; `--resume <session_id>` continues the conversation | Parse the result for the rate-limit error and reset time (field names UNVERIFIED - capture one real sample), sleep until reset, `claude -p --resume <id> "continue from STATUS.md"`; or a `StopFailure` hook (matcher `rate_limit`) that writes `limit-hit.json` for the watcher |
| Idle waits | `/loop` and cron cost a full-context turn each tick | A shell watcher (no model) that sleeps and wakes the lead only on a condition |

Do not pay for waiting: set the watcher to sleep, not poll with the model. After a gap over the cache TTL (5 min API key or subagent; 1 h subscription main) the next turn re-writes the conversation at the cache-write rate; for a big lead conversation start a fresh lead from `STATUS.md`.

## 3. Ready-to-copy artefacts

### 3.1 `.claude/agents/builder.md` (slim worker, shell and files only)

```markdown
---
name: builder
description: Implements one work package from a ready spec inside its own git worktree. Use for any package listed in docs/03-plan/work-packages. Files and shell only, no web.
tools: Read, Write, Edit, Glob, Grep, Bash
model: sonnet
effort: medium
maxTurns: 60
isolation: worktree
permissionMode: acceptEdits
---
You are a builder for ONE work package. Start with RESUME-FIRST: run `git log --oneline -5`, `git status --short`,
and read the "## Status" block of the status file named in your brief. First action in a fresh worktree:
`git branch -m wp/<id>-<slug>` (the id and slug are in your brief).
Edit only the paths your work package owns. Never edit contracts/, AGENTS.md, CLAUDE.md, .claude/, docs/03-plan/STATUS.md.
Commit after each finished step with message "WP-<id>: <what>" and update the Status checklist in the same commit.
Never run `git add -A`, stash, rebase or push --force. Use synthetic data only (tools/testdata).
Keep command output short (tail, counts, logs to a file). Write files with the file tools, not shell heredocs.
Finish only when `tools/gate.sh fast` passes. Final message: at most 15 lines (done with hashes, proof with numbers,
not verified, requests to lead, next step).
```

### 3.2 `.claude/agents/web-researcher.md`

```markdown
---
name: web-researcher
description: Researches one question on the open web and official sources, writes a note into research/, returns verdicts. Use for new facts (hackathon briefing, library or law questions).
tools: Read, Write, Glob, Grep, WebSearch, WebFetch, Bash
model: sonnet
effort: medium
maxTurns: 40
omitClaudeMd: false
---
Answer only the question in your brief. Prefer primary sources (gov.pl, isap.sejm.gov.pl, uodo.gov.pl, vendor docs).
Open every page you cite; a search snippet is never a fact. Label each claim VERIFIED (read the primary source),
SECONDARY or UNVERIFIED and give the URL. Write the note to the file path given in the brief (English; Polish legal
terms verbatim with a short gloss). No personal data of private individuals. Final message: at most 15 lines.
```

(A reviewer is the same file with `tools: Read, Glob, Grep, Bash`, `model: opus`, `effort: high`, and no Write/Edit.)

### 3.3 `.claude/settings.json` sketch for unattended work

```json
{
  "worktree": { "baseRef": "head" },
  "subagentPromptCacheTtl": "1h",
  "workflowSizeGuideline": "small",
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Workflow",
      "Bash(git status *)", "Bash(git diff *)", "Bash(git log *)", "Bash(git add *)",
      "Bash(git commit *)", "Bash(git merge *)", "Bash(git branch *)", "Bash(git worktree *)",
      "Bash(bash tools/gate.sh *)", "Bash(python -X utf8 tools/*)", "Bash(npm run *)", "Bash(pytest *)"
    ],
    "deny": [
      "Bash(git push --force*)", "Bash(git reset --hard*)", "Bash(git stash*)", "Bash(git rebase*)",
      "Bash(git add -A*)", "Bash(git add .)", "Bash(rm -rf *)",
      "Read(./.env)", "Read(./.env.*)"
    ]
  },
  "hooks": {
    "SubagentStop": [
      { "hooks": [ { "type": "command", "command": "bash tools/hooks/gate-on-stop.sh" } ] }
    ],
    "StopFailure": [
      { "matcher": "rate_limit", "hooks": [ { "type": "command", "command": "bash tools/hooks/mark-limit.sh" } ] }
    ]
  }
}
```

Notes: `permissions.allow/deny/defaultMode`, `worktree.baseRef`, `subagentPromptCacheTtl`, `workflowSizeGuideline` are documented keys; the exact rule strings above follow the documented `Bash(cmd *)` syntax (the space before `*` matters). `gate-on-stop.sh` must read the hook JSON from stdin and `exit 2` with the failure tail on stderr (VERIFIED semantics). The 1 h subagent TTL costs 2x on writes; drop it if packages finish within 5 minutes of each other. For unattended `claude -p` add `--permission-mode dontAsk --permission-prompts none` so nothing waits for a human. `defaultMode` value names (`acceptEdits`, `dontAsk`, `auto`, `bypassPermissions`, `plan`) are VERIFIED from the subagent page; whether `defaultMode` accepts all of them: UNVERIFIED.

### 3.4 `CLAUDE.md` and `AGENTS.md` skeletons

Because AGENTS.md is ignored when a CLAUDE.md exists, keep ONE source of truth in `AGENTS.md` and make `CLAUDE.md` a stub:

```markdown
# CLAUDE.md
@AGENTS.md

## Claude Code specifics
- Subagents: .claude/agents/builder.md, web-researcher.md, reviewer.md. Width 3.
- Compact instructions: when compacting keep the work-package id, branch, STATUS.md state and failing test output.
```

```markdown
# AGENTS.md  (keep under 200 lines)
## What this repo is        (3 lines; link docs/00-overview)
## Read order for any agent (AGENTS.md -> docs/03-plan/STATUS.md -> your work-package file)
## Rules that never bend
- Edit only paths you own (docs/03-plan/ownership.md). Contract changes: request in your status file.
- Commit "WP-<id>: ..." after each step; status checklist in the same commit; never `git add -A`.
- No stash, no rebase, no force push; catch up with `git merge main`.
- Synthetic data only; no secrets; no real personal data.
- Done = acceptance list passes + `tools/gate.sh fast` + one negative control in the status file.
## Commands                 (gate.sh fast|full, run backend, run frontend, one line each)
## Report format            (at most 15 lines: done+hashes, proof, not verified, requests, next step)
## Cost rules               (read a file by the needed part once; batch independent calls; cap output; delegate steps beyond ~5)
```

### 3.5 Sample orchestration script (Workflow tool, documented API only)

Worktrees are created by a shell step BEFORE the workflow (reliable names, `baseRef` irrelevant), the workflow only coordinates agents and collects JSON. Save as `.claude/workflows/build-wave.js` (`meta` must be the first statement and a plain literal; no `import`, no `Date.now()`); run as `/build-wave` or "run /build-wave on packages A2 A3 A4". Per-agent model and isolation options are not shown in the docs I read, so the model comes from the `builder` agent file and the cwd from the prompt (UNVERIFIED that `agent()` accepts an agent type; if not, paste the builder instructions into the prompt).

```javascript
export const meta = {
  name: 'build-wave',
  description: 'Run up to 3 work packages in pre-made worktrees and return one JSON report each',
}

const reportSchema = {
  type: 'object',
  required: ['wp', 'done', 'commits', 'gate_fast', 'not_verified', 'requests_to_lead'],
  additionalProperties: false,
  properties: {
    wp: { type: 'string' },
    done: { type: 'array', items: { type: 'string' } },
    commits: { type: 'array', items: { type: 'string' } },
    gate_fast: { type: 'string' },
    not_verified: { type: 'array', items: { type: 'string' } },
    requests_to_lead: { type: 'array', items: { type: 'string' } },
  },
}

const packages = args.packages // e.g. [{id:'A2', slug:'triage'}, ...]  (max 3)

phase('Build')
const reports = await pipeline(packages, p =>
  agent(
    `You are the builder of work package ${p.id}. Work ONLY in the worktree .claude/worktrees/${p.id} ` +
    `(branch wp/${p.id}-${p.slug}); run every command with that directory as cwd and use absolute paths. ` +
    `RESUME-FIRST: git log main..HEAD, git status, Status block of docs/03-plan/wip/WP-${p.id}.status.md. ` +
    `Task file: docs/03-plan/work-packages/WP-${p.id}-${p.slug}.md. Follow AGENTS.md. ` +
    `Finish when tools/gate.sh fast passes. Return the JSON report.`,
    { label: `WP-${p.id}`, schema: reportSchema },
  ),
)

phase('Review')
const ready = reports.filter(r => r && r.gate_fast === 'pass')
const reviews = await pipeline(ready, r =>
  agent(
    `Review git diff main...wp/${r.wp} against the acceptance list in its work-package file. ` +
    `Read-only. Return blocking findings only, each with file:line, or an empty list.`,
    { label: `review ${r.wp}`, schema: { type: 'object', required: ['wp', 'blocking'], additionalProperties: false,
        properties: { wp: { type: 'string' }, blocking: { type: 'array', items: { type: 'string' } } } } },
  ),
)

return { reports: reports.filter(Boolean), reviews: reviews.filter(Boolean) }
```

Prelude (shell, run by the lead or a hook before the workflow; Git Bash):

```bash
for wp in "A2 triage" "A3 drafting" "A4 forms"; do set -- $wp
  git worktree add ".claude/worktrees/$1" -b "wp/$1-$2" main 2>/dev/null || true
done
```

### 3.6 Headless pipeline (Mode B) with limit-aware resume

```bash
#!/usr/bin/env bash
# tools/run_wp.sh <id> <slug> ; one package per call, run up to 3 in parallel from the shell
set -u
id=$1; slug=$2; wt=".claude/worktrees/$id"; log="logs/wp-$id.log"; mkdir -p logs
git worktree add "$wt" -b "wp/$id-$slug" main 2>/dev/null || true
brief="Builder of WP-$id. RESUME-FIRST per AGENTS.md. Task: docs/03-plan/work-packages/WP-$id-$slug.md. Report <=15 lines."
sid_file="logs/wp-$id.session"
while :; do
  if [ -s "$sid_file" ]; then args=(--resume "$(cat "$sid_file")"); else args=(); fi
  ( cd "$wt" && claude -p "$brief" "${args[@]}" --model sonnet --effort medium \
      --permission-mode acceptEdits --permission-prompts none \
      --allowedTools "Bash(git *),Bash(bash tools/gate.sh *),Read,Edit,Write" \
      --output-format json ) > "logs/wp-$id.json" 2>> "$log"
  jq -r '.session_id // empty' "logs/wp-$id.json" > "$sid_file"
  # finished?  gate result is recorded by the builder in its status file with the commit hash
  grep -q '^\[x\] ACCEPTED' "$wt/docs/03-plan/wip/WP-$id.status.md" 2>/dev/null && break
  # limit hit?  sample real output once to learn the field; then sleep until the reset time
  if jq -e '(.result // "") | test("limit|rate")' "logs/wp-$id.json" >/dev/null; then sleep 900; else break; fi
done
```

Caveat: `--output-format json` with `session_id`, `--resume`, `--permission-prompts none`, `--allowedTools`, `--effort` are documented (VERIFIED); the string match for the limit message and the sleep interval are placeholders (UNVERIFIED): capture one real limit sample, and compute the sleep from the reset time in it.

## 4. What to do tonight (checklist)

1. Add `.claude/agents/*.md`, `.claude/settings.json`, `.gitignore` entry `.claude/worktrees/`, `CLAUDE.md` stub importing `AGENTS.md`.
2. Decide Mode A (default). Push `main` after every merge or keep `worktree.baseRef: "head"`.
3. Create `tools/gate.sh`, `tools/hooks/gate-on-stop.sh`, `tools/hooks/mark-limit.sh`, `ownership.tsv` generator.
4. Dry-run one tiny package end to end (spawn builder, branch rename, commit, gate, merge) before the 11:00 start; measure `/usage` Prompt-cache line afterwards.
5. Keep the lead conversation under a few hundred lines of context; at each milestone write `STATUS.md` and `/clear`.

## 5. API-side guidance for the product's own LLM calls

### 5.1 Models and prices (Anthropic API, USD/MTok; VERIFIED on pricing page)

| Model | API ID | Input | 5 m write | 1 h write | Cache read | Output | Batch in/out | Context / max out |
|---|---|---|---|---|---|---|---|---|
| Claude Fable 5.2 | `claude-fable-5-2` | 8 | 10 | 16 | 0.20 | 40 | 4 / 20 | 1M / 128K |
| Claude Opus 5.5 | `claude-opus-5-5` | 4 | 5 | 8 | 0.20 | 20 | 2 / 10 | 1M / 128K |
| Claude Sonnet 5.5 | `claude-sonnet-5-5` | 2 | 2.50 | 4 | 0.10 | 10 | 1 / 5 | 1M / 128K |
| Claude Haiku 5.5 (prompt up to 100k) | `claude-haiku-5-5` | 0.10 | 0.125 | 0.20 | 0.01 | 0.50 | 0.05 / 0.25 | 1M / 128K |
| Haiku 5.5 (prompt over 100k) | same | 0.50 | 0.625 | 1 | 0.05 | 2.50 | 0.25 / 1.25 | |

Other facts: Mythos 5.2 is limited availability (verification program); Fable 5.1/5 and Opus 5 are older and dearer; full 1M context is at standard price except Haiku 5.5 over 100k tokens; `inference_geo:"us"` costs 1.1x; tool-use system prompt adds 286 tokens; the bash tool adds 325. Retirement commitments: Opus 5.5 not before 2027-09-22, Sonnet 5.5 2027-09-28, Haiku 5.5 2027-10-07, Fable 5.2 2027-11-09 (models overview page). Anthropic recommends Opus 5.5 as the default start and Fable 5.2 for demanding reasoning.

### 5.2 Prompt layout for a large static legal knowledge block

```
tools  (stable, no per-request change)                      -- cached with system
system (instructions, output rules, refusal rules)          -- cached
document blocks: the legal corpus (ustawa o dostepie do informacji publicznej, art. 5 ust. 1-2 on limits,
   art. 6 on forms, art. 16 on refusal, art. 14 on deadlines, UODO guidance, the city's own decision templates)
   each as its own document block with title + citations enabled; LAST block carries cache_control {"type":"ephemeral","ttl":"1h"}
messages: [ one user turn: the incoming UDIP request text + case metadata ]   -- NEVER cached, always last
```

Rules: (1) one breakpoint after the corpus, optionally a second after the system prompt; at most 4. (2) Freeze corpus text byte for byte (sorted, no timestamps); any change rebuilds it. (3) Use `ttl:"1h"` for the corpus because office traffic is bursty (cache read refreshes the entry for free; a 1 h write pays back after 2 reads). (4) On a cold start send one warm-up request and wait for the first response to begin before fanning out parallel requests. (5) Keep `tool_choice`, effort and the `citations` toggle constant between calls; changing them invalidates the cache. (6) Different models never share a cache: pick one model per stage. (7) Minimum cacheable prefix is 512 tokens on the current 5.x models. (8) Cache is isolated per workspace and per organisation; do not expect sharing between dev and prod keys.

### 5.3 Structured output, citations, batch, effort

- Triage (classify the request: UDIP or not, subject, exemptions candidates, deadline, redirect to other authority): `output_config.format` JSON schema with enums; Haiku 5.5 or Sonnet 5.5 at `low`-`medium`. Schemas: `additionalProperties:false`, no `oneOf`, no numeric bounds; validate ranges in code.
- Drafting the answer with grounding: Messages call with `document` blocks, `citations.enabled:true`, no `output_config.format` (incompatible). Convert citations to footnotes in code; reject drafts whose legal claims lack a citation. `cited_text` is not billed as output.
- Extract machine fields from the draft in a SECOND small call (JSON schema, no documents), or have the clerk-facing UI render prose + citation list directly.
- Review step (does the draft cite the right article, are exemptions justified, is a personal-data redaction missed): Opus 5.5 at `high`, with the same cached corpus.
- Batch API: offline evaluation sets (synthetic requests x models x prompts), 50% off, up to 100,000 requests per batch, most done within 1 h, results kept 29 days; put `cache_control` with 1 h TTL in each request; not available for the live clerk flow and not ZDR-eligible.
- Effort: Haiku 5.5 low-medium; Sonnet 5.5 medium (start) to high; Opus 5.5 medium default, high for review; Fable 5.2 high (API default), `xhigh`/`max` only where an eval shows a gain. Set `max_tokens` generously at high effort (thinking counts toward it). Run an effort sweep on a labelled set before the demo.
- Do not use: context editing, memory tool, tool search (stateless, few tools) unless the assistant becomes a long agent loop.

### 5.4 Cost estimate per processed UDIP request (ESTIMATE, computed from the verified price table)

Assumptions (all assumed, not measured; the new tokenizer yields about 30% more tokens, Polish legal text may tokenise worse): static corpus 40,000 tokens (cached); dynamic input 3,000 tokens (request text plus retrieved extras); output 1,500 tokens including thinking, at `medium`. Single call, standard (non-batch) pricing.

| Model | Warm cache read (40k) | Cold, 1 h cache write | No caching | Batch + warm cache |
|---|---|---|---|---|
| Haiku 5.5 | $0.0015 | $0.0091 | $0.0051 | $0.0007 |
| Sonnet 5.5 | $0.025 | $0.181 | $0.101 | $0.0125 |
| Opus 5.5 | $0.050 | $0.362 | $0.202 | $0.025 |
| Fable 5.2 | $0.092 | $0.724 | $0.404 | $0.046 |

Arithmetic (Sonnet 5.5, warm): 40,000 x 0.10 / 1e6 = $0.004; 3,000 x 2 / 1e6 = $0.006; 1,500 x 10 / 1e6 = $0.015; total $0.025. Recommended pipeline per request: Haiku triage (about $0.0015) + Sonnet draft with citations (about $0.025) + Opus review of the draft (cache read $0.008 + 5k input $0.020 + 0.5k output $0.010 = about $0.038) = about $0.065 per request warm; about 1,000 requests per month = about $65 plus cache re-writes. Cold writes dominate when traffic is sparse: with a 1 h TTL and fewer than one request per hour you pay the cold column every time, so for a low-volume office either accept it (Sonnet cold about $0.18) or skip caching and shrink the corpus via retrieval. A request that adds web search costs $10 per 1,000 searches extra (not planned: closed corpus).

## Corrections to docs/04-orchestration

Every item cites the current doc. "Fix" is the suggested replacement.

| # | File and statement | What current docs say | Fix |
|---|---|---|---|
| C1 | `resume-after-limit.md`: "A sub-agent's context: a stopped sub-agent cannot be 'continued', only replaced" | Subagents can be resumed with full history via `SendMessage` (agent ID or name); a subagent stopped at `maxTurns` returns partial output and can be resumed; only one stopped by you with `x` in `/tasks` does not auto-resume. Transcripts persist under `~/.claude/projects/<project>/<session>/subagents/` for `cleanupPeriodDays` (30). https://code.claude.com/docs/en/sub-agents (VERIFIED) | Say: "resume in the same lead session with SendMessage; if the lead session is gone, restart the package from branch + status file (resuming from a new session is UNVERIFIED)". |
| C2 | `resume-after-limit.md`: "Usage limits arrive for everything at once: all running sub-agents stop together" and "Whether the application resumes ... depends on the surface" | In an interactive subscription session (v2.1.234+) Claude waits for the reset and continues itself (`autoContinueAtUsageLimit`, `/rate-limit-options`), max 3 continuations, reset under 24 h; workflows pause instead of failing (v2.1.271+, max 2 waits); none of this applies to `claude -p`, background sessions, Remote Control, teammates, Dispatch or scheduled sessions. https://code.claude.com/docs/en/interactive-mode, https://code.claude.com/docs/en/workflows (VERIFIED) | Replace the vague sentence by the table in section 2.9. |
| C3 | `resume-after-limit.md`: "If an orchestration run was interrupted and the tool supports resuming a run" | Name it: Workflow tool; relaunch with the same script replays saved results; an edited prompt re-runs from the first changed agent and every later agent; a Failed agent in the middle re-runs everything after it; `nothing to resume` if results are gone; after "Exit and stop tasks" use `claude --resume` first. https://code.claude.com/docs/en/workflows#resume-after-a-pause (VERIFIED) | Use these exact terms and warn against editing prompts of finished agents. |
| C4 | `resume-after-limit.md`: cache sentence "first step of a large session re-sends the whole conversation at full price" | Main-conversation TTL is 1 h only on a subscription within plan usage, otherwise 5 min; subagents/workflows 5 min unless `subagentPromptCacheTtl`; a miss is billed at the cache-WRITE rate (1.25x or 2x base), reads are 0.025x (Fable 5.2) / 0.05x (Opus 5.5, Sonnet 5.5). `/usage` shows a `Prompt cache (main)` line with warm/cold. https://code.claude.com/docs/en/prompt-caching, https://platform.claude.com/docs/en/about-claude/pricing (VERIFIED) | State the TTLs and the settings `promptCacheTtl` / `subagentPromptCacheTtl`. |
| C5 | `git-workflow.md`: worktrees in `.worktrees/<id>` created by hand; "If the harness offers worktree isolation for sub-agents, use that instead" | Native location is `.claude/worktrees/<name>`, branch `worktree-<name>`, created by `claude --worktree <name>` or `isolation: worktree`; `--worktree` cannot take a branch name; base is the REMOTE default branch unless `worktree.baseRef: "head"`; `-p` worktrees are not auto-removed; the sweep removes subagent/background worktrees after `cleanupPeriodDays` unless they hold work. https://code.claude.com/docs/en/worktrees (VERIFIED) | Move to `.claude/worktrees/<id>` (add to `.gitignore`), set `worktree.baseRef: "head"` or push `main` after each merge, rename the branch to `wp/<id>-<slug>` on first step. This is the highest-risk item. |
| C6 | `git-workflow.md` / `lead-agent-playbook.md`: agents read `AGENTS.md` ("Read AGENTS.md, then STATUS.md") | Claude Code reads AGENTS.md natively only if no CLAUDE.md/CLAUDE.local.md exists (v2.1.277+); with both, only CLAUDE.md is loaded unless it contains `@AGENTS.md`. A subagent in its own worktree takes CLAUDE.md and `.claude/rules/` from the MAIN conversation, not from the worktree's branch, so edits to them on a branch do not reach it. https://code.claude.com/docs/en/memory, https://code.claude.com/docs/en/worktrees (VERIFIED) | Add a CLAUDE.md stub `@AGENTS.md`; keep rules edits on `main`; also keep "read AGENTS.md" in every brief. |
| C7 | `lead-agent-playbook.md` section 2: "If the harness provides a deterministic orchestration tool" | It does: dynamic workflows (Workflow tool, `/workflows`, `ultracode`, saved in `.claude/workflows/`, `workflowSizeGuideline`, `disableWorkflows`). Script API: `agent`, `pipeline`, `parallel`, `phase`, `log`, `args`; `schema` on `agent()`. https://code.claude.com/docs/en/workflows (VERIFIED) | Name it and link section 3.5 of this report. |
| C8 | `lead-agent-playbook.md` section 5: "Default pool 3 ... a script (not the model) holds the width" | Platform caps: 20 concurrent subagents (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`), 16 workflow agents (`CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS`, 1-256), 1,000 agents per run, 4,096 items per call; ultracode is exempt from the subagent cap. https://code.claude.com/docs/en/sub-agents, workflows (VERIFIED) | Keep 3 as a cost/merge policy; say so; for Workflows the width is a script/`args` choice. |
| C9 | `subagent-brief-template.md`: "Name models by alias (the tier name without a version number)" and the tier table | Aliases are `fable`, `opus`, `sonnet`, `haiku`, `opusplan`, `default`, `best`; `sonnet` and `haiku` resolve to the 5.5 models only on the Anthropic API (4.6/4.5 on Bedrock, Foundry, Agent Platform); the per-invocation `model` parameter accepts aliases only; full IDs go in the agent file; `CLAUDE_CODE_SUBAGENT_MODEL(_FORCE=1)` overrides. https://code.claude.com/docs/en/model-config (VERIFIED) | Add the resolution order and the provider caveat; add the frontmatter keys `model`, `effort`, `maxTurns`, `tools`. |
| C10 | `subagent-brief-template.md`: effort column low/medium/high | Valid levels are `low`, `medium`, `high`, `xhigh`, `max`; Claude Code defaults to `medium` on Fable 5.2, Opus 5.5, Sonnet 5.5, Haiku 5.5; API defaults differ (Fable 5.2 high, Opus 5.5 medium, Sonnet 5.5 high, Haiku 5.5 medium); `xhigh` is for 30-minute-plus agentic runs; thinking cannot be disabled on these models in Claude Code. https://code.claude.com/docs/en/model-config, https://platform.claude.com/docs/en/build-with-claude/effort (VERIFIED) | Use the exact names; mark `xhigh`/`max` as "only with a measured gain". |
| C11 | `lead-agent-playbook.md` rule 9 "Do not poll. Wait for completion notifications" | Correct: subagents from the main conversation run in the background and send completion notices. Add: `CLAUDE_CODE_FORK_SUBAGENT=0` makes Claude wait; `/tasks` lists them; in `claude -p` the run waits for background work at most 10 min (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`). | Add the setting names. |
| C12 | `lead-agent-playbook.md` section 3 rule 10 / section 7: "one independent check ... no voting panels" | Consistent with docs, but the bundled `/deep-research` workflow does vote on claims; fine for research, not for builds. Hooks give a cheaper deterministic gate: `SubagentStop`/`TaskCompleted` exit 2 forces a worker to continue until `gate.sh fast` passes. https://code.claude.com/docs/en/hooks (VERIFIED) | Add the hook gate to the definition of done. |
| C13 | `git-workflow.md`: "Never run git add -A ... No stash, no rebase" etc. | No doc contradicts; enforce with `permissions.deny` rules and a PreToolUse hook rather than prose (deny rules shown in section 3.3). | Add the deny list. |
| C14 | General: no mention of agent teams or `claude --bg` | Agent teams are experimental, off by default (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`); while on, a named subagent launches as a teammate; teammates cannot resume in-process; agent view `claude --bg` sessions auto-isolate in worktrees. | Add "not used for implementation" and the agent-view alternative. |

## Verdicts on the previous research

The job file lists no claim ids. The corrections C1-C14 above are the verdicts on `docs/04-orchestration`.

## Open questions and what could not be verified

- Exact option names of the Workflow `agent()` call for per-agent model, agent type and worktree isolation: not shown on the workflows page; check `/workflow-authoring` in the session. Where I looked: https://code.claude.com/docs/en/workflows (first 100k characters read in full).
- Whether a subagent can be resumed after the lead session is replaced (`claude --resume` of the lead, then SendMessage): documented only within one session; UNVERIFIED.
- Exact field names of the `claude -p` JSON result when a usage limit is hit (the docs show `session_id`, `total_cost_usd`, `permission_denials`, API retry events with `error: rate_limit`); capture a real sample. The user context mentions a `rate_limit_event` in streams; I did not find it in the docs I read.
- Behaviour of `claude --bg` sessions at a usage limit (agent view page, "Limitations" section, beyond the 100k characters read).
- Programmatic tool calling, scheduled tasks/routines details, checkpointing, cloud sessions: only index-level; not needed for the plan.
- Server-side compaction (`compact_20260112`) request format: only the type name was visible.
- Whether `settings.json` `permissions.defaultMode` accepts every mode listed; deny-rule string forms for Windows paths.
- EU data residency: the Claude API offers only `us`/`global`; whether a partner cloud (Bedrock, Google Cloud, Foundry) region in the EU satisfies a Polish city office is a legal and procurement question outside this report (see R5).
- Token counts for Polish legal text on the new tokenizer: run `count_tokens` on the real corpus before trusting the cost table.
- The workflow `/deep-research` bundled command is documented on the workflows page but not listed among bundled skills on the skills page (minor inconsistency).

## Sources

- https://code.claude.com/docs/llms.txt
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/workflows
- https://code.claude.com/docs/en/worktrees
- https://code.claude.com/docs/en/agent-teams
- https://code.claude.com/docs/en/agent-view
- https://code.claude.com/docs/en/headless
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/model-config
- https://code.claude.com/docs/en/costs
- https://code.claude.com/docs/en/prompt-caching
- https://code.claude.com/docs/en/interactive-mode
- https://code.claude.com/docs/en/settings-reference
- https://platform.claude.com/docs/en/about-claude/pricing
- https://platform.claude.com/docs/en/models/overview
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- https://platform.claude.com/docs/en/build-with-claude/citations
- https://platform.claude.com/docs/en/build-with-claude/effort
- https://platform.claude.com/docs/en/build-with-claude/batch-processing
- https://platform.claude.com/docs/en/build-with-claude/context-editing
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool
- https://platform.claude.com/docs/en/manage-claude/data-residency
- https://www.anthropic.com/engineering/multi-agent-research-system
- https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
