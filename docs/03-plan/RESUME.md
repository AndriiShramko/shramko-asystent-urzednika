# RESUME: continue the build from here, on any subscription

One file for a lead that starts cold: after a limit stopped the previous lead, or beside it from another subscription.
It holds the start prompt, the rules of parallel work through git, the board of lanes and the queue.
The merge lead keeps the board current: after every merge, every start or stop of an agent, and before every wait.

Board updated: 2026-11-22 00:19 CET by `build7`.

## 0. For the owner (по-русски)

Чтобы продолжить работу после остановки по лимиту или подключить вторую подписку, откройте НОВУЮ сессию в папке
`C:\dev\shramko-asystent-urzednika` и вставьте одну строку:

`Прочитай файл docs/03-plan/RESUME.md и выполняй раздел 1 как мою инструкцию. Моя метка: buildN.`

(вместо `buildN` следующий свободный номер: `build8`, `build9`). Больше ничего делать не нужно.

## 1. Start prompt for a lead

You are a build lead of the forms converter (HackNation 2026, task COI "Cyfryzacja formularzy"; freeze Sunday
22 November 08:30, merges by 06:30, submission 11:00, finals 15:15 with a live run on new files).
The truth is in git. Take the time only from the shell command `date`.

1. Read [`AGENTS.md`](../../AGENTS.md) (hard rules), then this file to the end, then the live block at the top of
   "Build log" in [`STATUS.md`](STATUS.md). Skill `track-f-lead` for how a lead works; skill `lane-work` for builders.
2. `git fetch origin --prune`; `git log --oneline -6 origin/main`; `git branch -r --list "origin/wp/*"`;
   `git worktree list`; usage tool `get_usage` (5-hour window, week).
3. Find your role in section 2: are you the **merge lead** (the one writer of `main`) or a **lane lead**
   (you build lanes on branches and never touch `main`)? If the board names a merge lead whose heartbeat is younger
   than 45 minutes, you are a lane lead.
4. Take the first free lane of section 4 that is not claimed (section 3 says how to claim), work it as its status
   file says under "## Left for the next stage", push after every commit.
5. Report to the program lead if one runs (its session id is in the live block of STATUS), else to the owner in
   Russian, short, no commands for him to run.

## 2. Parallel work from several subscriptions: everything through git

Sessions of different subscriptions cannot see each other. They meet only in git, so git carries every claim.

**Roles.**
- **Merge lead**: exactly one. Only it commits to `main`, merges, pushes `main`, rebuilds `eval/chain/baseline.json`
  and `results/`, edits `STATUS.md` and this file. It works in the main checkout `C:/dev/shramko-asystent-urzednika`.
  Named in the line "Merge lead" below with a heartbeat; it refreshes the heartbeat at every push of `main`.
- **Lane lead**: any number. Works only in worktrees `.claude/worktrees/<lane>` on lane branches `wp/<id>-<slug>`.
  Never commits to `main`, never runs anything that writes in the main checkout (`eval.chain` without a worktree,
  `snapshot_results.py`, `merge.sh`). A finished lane is marked `ready_to_merge` in its status file and pushed;
  the merge lead merges it.
- Taking over the merge role: only when the line below is older than 45 minutes AND the program lead or the owner
  says yes. Record it by one commit on `main` that changes the line, push; if the push is rejected, the old merge
  lead is alive: stop and stay a lane lead.

**Merge lead: `build7`, heartbeat 2026-11-22 00:19 CET.**

**A lane is claimed by its branch on origin.**
- Claim: `git worktree add .claude/worktrees/<lane> -b wp/<id>-<slug> origin/main`, create the status file
  `docs/03-plan/wip/WP-<id>.status.md` whose second line is
  `Claimed by: <label>; heartbeat: <date> <HH:MM>; state: running`, commit, `git push origin wp/<id>-<slug>`.
  Creating the remote branch is the lock: if the push is rejected, another lead took the lane; remove your worktree
  and take the next lane.
- Heartbeat: every commit of the lane updates that line and is pushed. A lane whose heartbeat is older than
  45 minutes, or whose state is `stopped` or `released`, may be taken over: `git fetch`, add a worktree on the
  existing branch (git refuses a branch that is checked out in another worktree on this laptop: then look at that
  worktree first, `git -C <worktree> status --short`, commit loose sound work by file name, and continue THERE),
  change the line to your label, push. A rejected push means the old owner is alive: back off.
- Two lanes never own the same paths. Owned paths of each lane are in the board; the general table is
  [`ownership.md`](ownership.md). A change outside your paths is a line under "## Requests to lead".

**Nothing is lost at a limit.** A 5-hour limit kills agents in the middle of a step, without warning (seen
21 November 23:10: three agents died mid-step). Therefore:
- A builder commits after every finished step AND pushes the lane branch after every commit.
- The section "## Left for the next stage" of the status file is kept current in EVERY commit (not written at the
  end): the items left, the exact next commands, the checks that already passed with the commit they ran on.
- The lead reads `get_usage` before every launch and at least every 20 minutes while agents run, and writes the
  numbers with the time into the live block of STATUS. Measured burn: five agents on the top model plus the lead
  spent about 94 points of the 5-hour window in 43 minutes (22:27 to 23:10). Plan with about half a point per
  agent-minute on the top model.
- 5-hour window at 80 %: start no new agent; message the running ones "commit, push, write the next commands".
  At 90 %: the merge lead updates this board and STATUS, pushes, and launches nothing more; shell work without a
  model goes on. Week: steps at 94, 96 and 98 % of [`subscription-cutoff.md`](../04-orchestration/subscription-cutoff.md).
- A stage without a decision (gate, chain, image wait, acceptance script) is a shell command with a log under
  `tmp/`, never an agent. Mechanical work goes to the middle model; the top model only for design and hard code.

**Shared things on this laptop.**
- The Python environment `.venv` of the main checkout is shared and read-only: never `pip install`.
- Docker: at most two heavy jobs at once in total; name your containers `<label>-<what>` and remove them. Ports:
  the merge lead uses 18000 to 18099, `build8` 18100 to 18199, `build9` 18200 to 18299, and so on. The owner's test
  page is on 8080: never take it.
- Logs go to `tmp/` of YOUR checkout or worktree, with your label in the name.
- The partner's task sets and the archive of unseen forms are read-only. In a worktree the chain needs
  `--archive C:/dev/shramko-asystent-urzednika/data/archive`.
- The image is built by GitHub Actions: a push of `main` (not of `docs/**` or `research/**` alone) builds and
  publishes; a push of a branch `wp/F20-*` builds a test image `test-<sha>`. Wait with
  `bash tools/gate.sh py tools/ci/wait_run.py <full hash> --timeout 2400`, digests with
  `bash tools/gate.sh py tools/ci/image_digest.py <full hash> --target core` (and `plus`).

**Merging (merge lead only), one branch at a time:**
`bash tools/lead/merge.sh <branch> "<message>" '<regex of owned paths>'` (publishing check, fast gate, push), then
`bash tools/gate.sh py -m eval.chain --compare > tmp/chain-<hash>.log 2>&1` (a "worse" line is read by hand before
the baseline is rebuilt with `--update-baseline`), then the board and STATUS in one commit.

## 3. State of `main` and of the test builds

| What | Value |
|---|---|
| `main` code | `9e095ab` (F3c review fix `14170bf`, service fixes `9e095ab`); later commits are documents |
| **Test build V1** (rules only; starts with no flags; no cold-start race; F3c review blockers fixed) | core `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:061fce4b1c7d4dc9ef8f3e6cc30890f5362f6190e377f44fc79e9b3e88d4982b`, plus `...@sha256:0c04df42b396e8c7b78ad1f4381ba15923b49cfc7392ca74a8c1a7fb5ddbbb1f`; image workflow of `9e095ab` green |
| Chain on `main` `9e095ab` | 158 files: 152 converted, 6 refused (hostile), 0 failed, 0 gate failures, 0 lint errors; 0 worse, 0 better against the baseline of `14170bf` |
| Start for a manual test | `docker run --rm -p 127.0.0.1:8080:8080 --read-only --cap-drop ALL <core>`; page `http://127.0.0.1:8080/ui/`, state `/status` |
| Jury acceptance on the V1 core digest (`jury_accept.sh`, 22 November 00:18, log `tmp/jury-accept-v1.log`) | ALL PASS: CLI to stdout three identical runs offline and read-only; `--out` as the caller; unwritable output is exit 4; no-flags start up in 4 s; two simultaneous first calls both 200; REST three times equal to the CLI bytes; the log warns that no token is asked; explicit `AUTH_MODE=jwt` without a key exits 3 |
| Fallback digests | `59319f4`: core `sha256:e8205af582bc9a5da0d4ee987d19560d9786429367ce87258ab354b8e7eb4641` (needs `-e AUTH_MODE=off` for REST) |

## 4. Board of lanes (first free lane from the top is the next to take)

State words: `running` (claimed, alive), `stopped` (claimed, its agent died or stopped: free to take over by the
rule of section 2), `ready_to_merge`, `merged`, `free` (no branch yet).

| # | Lane, branch | Owned paths | State, claimed by | What is left, exactly |
|---|---|---|---|---|
| 1 | Validators and REQUIRED, `wp/F-val-validators`, worktree `.claude/worktrees/agent-a93ecdbb74987c1c9`, status `wip/WP-F-val.status.md` | `app/compose/**`, `app/lexicon/*.json`, `tests/compose/**`, `tests/validators/**`; by the lead: `config.py` (`REQUIRED_POLICY`), one line of `pipeline.py` | `running`, `build7` (shell) | Stages 1 and 2 of the builder are committed (`3f748eb`, pushed). The lead wires `REQUIRED_POLICY` with default `paper` (completeness decision R-1) and the stale-warning filter: uncommitted in that worktree at 00:19, fast gate running (`tmp/fast-lead.log` there). Then: fix tests that assumed inferred REQUIRED, commit, chain compare, merge, `bash tools/gate.sh py tools/lead/snapshot_results.py .`, tell the program lead the REQUIRED counts (146 to 13 on the seven results) |
| 2 | Jury documents, `wp/F-jury-docs` (tip `ebd89f4`, pushed), status `wip/WP-F-jurydocs.status.md` | `README*.md`, `apps/converter/README.md`, documents that named the self-test | `ready_to_merge` after the digest, `build7` | In a worktree of the branch: `git merge --no-edit main`; `sed -i 's/REPLACE_WITH_FINAL_DIGEST/061fce4b1c7d4dc9ef8f3e6cc30890f5362f6190e377f44fc79e9b3e88d4982b/g'` over the files its status file lists; run its "Not verified" list on the V1 image (no-flags start, `/status`, exit 4 on an unwritable `--out`); link check; merge. Add `REQUIRED_POLICY` to the configuration table if lane 1 merged first |
| 3 | Image checks, `wp/F20-image-checks` (tip `c070d95`, pushed), worktree `.claude/worktrees/agent-a7edc5f96805bd34c`, status `wip/WP-F20i.status.md` | `apps/converter/Dockerfile`, `docker-compose.yml`, `.github/workflows/**`, `tools/ci/**` | `stopped` (builder died 23:10 at "commit the stage 1 code, then the fast gate"; its tree is clean) | Stage 1 green in CI (actions/runs/44953569833, 57 of 57 checks in both targets). Stage 2 (the jury's first run as a check) is committed and merged with `main`: find the run of `c070d95` (`wait_run.py`), read it; still to do: one recorded RED run on a throw-away commit, final green run of the head, then `ready_to_merge`. Shell work plus one small decision: the middle model is enough |
| 4 | Visible engine H4, `wp/H4-engine-visible` (tip `26fb3e9`, pushed: work in progress saved by the lead), worktree `.claude/worktrees/agent-aaec4ba24d1deb0e5`, status `wip/WP-H4.status.md` | `app/engine.py` (new), `app/main.py`, `app/cli.py`, `app/config.py` (settings names only), three warning codes in `app/model/**`, `apps/review-web/**` (badge), `tests/shell/test_engine_visible.py` | `stopped` (builder died 23:10 after writing `engine.py` and settings fields; nothing wired, nothing tested) | Header `X-Converter-Engine: rules` on conversion answers, `/status` extended, CLI line on stderr, log line, badge on the review page, codes `MODEL_USED`, `MODEL_FALLBACK`, `MODEL_SKIPPED`; no model call. Acceptance: form and sidecar byte-identical to `main` on the synthetic fixtures and the nine task sets, `/healthz` unchanged, no key or URL in any output, one negative control. Brief: the model-placement decision of the leads' folder, section 3 row 1 (default AUTO by the owner's override) |
| 5 | Floor: set 08 and the release proof (backlog B4) | `results/**` (merge lead only) | `free`, merge lead only | After lanes 1 to 3 merge: rebuild the seven results and set 08 from the image; proof on the exact digest: `--network none --read-only --cpus 2 --memory 4g`, cold start, `/status`, REST convert, three byte-identical runs; script `jury_accept.sh` of the private preparation folder; name the fallback digest |
| 6 | Wide run on V1 (L1) | none (reads only; logs in `tmp/`) | `free` | The 584 other archive files and the hold-out forms through the V1 image: 0 failed, 0 gate, no plain 500; counts only |
| 7 | Rules mined from the model H0, `wp/H0-model-mined-rules` | `app/lexicon/concepts.json` and the cue lists | `free`, only AFTER lane 1 merges (same files) | The model-placement decision, section 3 row 2; chain no worse; not green by 03:00: drop |
| 8 | Honest tests, `wp/F-tests-honest` (one commit `1998872`) | `apps/converter/tests/**` except compose, validators and the files of lanes 1 and 4; `apps/review-web/scripts/**`; `eval/chain/report.py`, `eval/chain/tests/**` | `free` | Section "F-TESTS" of [`NEXT-WAVE.md`](NEXT-WAVE.md); new tests proposed by the audit arrive as new files from the program lead |
| 9 | Scans: `SCAN_PREP` packages S0 to S7 | `app/readers/**` image path | `free`, needs the program lead's order and the scan-fix consensus of the leads' folder | Scale from the dpi tag, upscale below 170 dpi, orientation by OCR confidence; measured on paper-field recall; 158 born-digital files byte-equal |
| 10 | Model step H1, then H2 and H3, then `wp/F20-model-step` | as the decision says | `free`, only on the program lead's order, after lane 4 | Not green by 01:00 was the kill line of the decision: ask the program lead before starting |

Small open items (merge lead): a wait for a free slot instead of an immediate 429 (`QUEUE_WAIT_S`, about 15 lines in
`main.py`, after lane 4); a warning code of its own for "validator not written" (after lane 4, same file);
`docs/03-plan/NEXT-WAVE.md:21` and `wip/WP-F20.status.md` still name the self-test endpoint; D19 M2 decision line
(G5 stays a warning); documents of `converter-design.md` and `coi-json-format.md` must say the same about REQUIRED.

## 5. Never

`git add -A`, stash, rebase, force push, history rewriting; a commit to `main` by a lane lead; two leads in one
worktree; a key, real personal data, the partner's task sets or notes of the leads' folder in git; anything in the
product that calls out of the container; "done" before the result was checked where the jury will see it.
