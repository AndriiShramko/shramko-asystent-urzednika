# RESUME: continue the build from here, on any subscription

One file for a lead that starts cold: after a limit stopped the previous lead, or beside it from another subscription.
It holds the start prompt, the rules of parallel work through git, the board of lanes and the queue.
The merge lead keeps the board current: after every merge, every start or stop of an agent, and before every wait.

Board updated: 2026-11-22 01:32 CET by `build7`. Report to program lead 9 (session `local_fba1e498-2f81-4cd1-9cc2-ebba7c37471b`), which replaced program lead 8 about 00:30. Common rule of every gate of ORDER C: no judged set loses a matched element in any format; nothing merges without the seven-set diff.

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

**Merge lead: `build7`, heartbeat 2026-11-22 01:24 CET, then STOPPED at a clean point (nothing running, nothing unmerged, nothing uncommitted). The 5-hour window is expected to run out about 01:40 and to return at 05:00: whoever starts then takes the merge role. Its context is at the hand-over size (about 310 thousand tokens): when the 5-hour window returns or another subscription joins, the NEXT lead takes the merge role by the rule above.**

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
| `main` code | `7cdcbfc` (pushed 01:24): everything of the row below plus ORDER C1 (required and optional by the paper's words) |
| Build V1.1 (superseded by V1.2; V1 plus validators, REQUIRED by paper, image environment, 504 wording) | commit `2837867` (code `7fedaed`): core `...@sha256:e8765c4f31bdc8f8f50a70c26716f22eae1c281148ae89799834f1dfc6d92f48`, plus `...@sha256:a4c2f09d798bebd3524142dce8e458f686101107917f47bd035e43cddc3bb580`; image workflow green (actions/runs/44963353407), `jury_accept.sh` ALL PASS (9 of 9, log `tmp/jury-accept-v11.log`). The program lead ran it for the owner on port 8080 |
| **Build V1.2** (V1.1 plus the visible engine H4 and the DOCX numbering C3) | commit `bd71323`: core `...@sha256:ad20729d0f54f1c4ed8b9a8db852538df7fb925c28c9ad6d28c884df03b21078`, plus `...@sha256:b7ce5c09ee734bdcaa5230502554454710f2c751b13559f4bf98be09836abe39`; image workflow green (actions/runs/44965539827), `jury_accept.sh` ALL PASS (log `tmp/jury-accept-bd71323.log`); superseded by V1.3 |
| **Build V1.3** (V1.2 plus ORDER C1) | commit `7cdcbfc`: core `...@sha256:eeb31c0f8816d8d298abfe26b6aa193f935bbbb02f619fe277ac7ef7540cceca`, plus `...@sha256:69124465204a66a85193e2eaa3e10295fa607d9329327390c32e522b95838e4b`; image workflow green (actions/runs/44966422665), `jury_accept.sh` ALL PASS (log `tmp/jury-accept-7cdcbfc.log`). **Last digest verified end to end: every code commit of `main` up to `7cdcbfc` is in it** |
| Test build V1 (superseded by V1.1) (rules only; starts with no flags; no cold-start race; F3c review blockers fixed) | core `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:061fce4b1c7d4dc9ef8f3e6cc30890f5362f6190e377f44fc79e9b3e88d4982b`, plus `...@sha256:0c04df42b396e8c7b78ad1f4381ba15923b49cfc7392ca74a8c1a7fb5ddbbb1f`; image workflow of `9e095ab` green |
| Chain on `main` `9e095ab` | 158 files: 152 converted, 6 refused (hostile), 0 failed, 0 gate failures, 0 lint errors; 0 worse, 0 better against the baseline of `14170bf` |
| Start for a manual test | `docker run --rm -p 127.0.0.1:8080:8080 --read-only --cap-drop ALL <core>`; page `http://127.0.0.1:8080/ui/`, state `/status` |
| Jury acceptance on the V1 core digest (`jury_accept.sh`, 22 November 00:18, log `tmp/jury-accept-v1.log`) | ALL PASS: CLI to stdout three identical runs offline and read-only; `--out` as the caller; unwritable output is exit 4; no-flags start up in 4 s; two simultaneous first calls both 200; REST three times equal to the CLI bytes; the log warns that no token is asked; explicit `AUTH_MODE=jwt` without a key exits 3 |
| Fallback digests | `59319f4`: core `sha256:e8205af582bc9a5da0d4ee987d19560d9786429367ce87258ab354b8e7eb4641` (needs `-e AUTH_MODE=off` for REST) |

## 4. Board of lanes (first free lane from the top is the next to take)

State words: `running` (claimed, alive), `stopped` (claimed, its agent died or stopped: free to take over by the
rule of section 2), `ready_to_merge`, `merged`, `free` (no branch yet).

| # | Lane, branch | Owned paths | State, claimed by | What is left, exactly |
|---|---|---|---|---|
| 1 | Validators and REQUIRED, `wp/F-val-validators` | `app/compose/**`, `app/lexicon/*.json`, `tests/compose/**`, `tests/validators/**` | **`merged` 00:36, `a7f2cee`** | Nothing. Proof: fast gate green; chain 158 files 0 failed, 0 worse; with the service default the seven judged results carry 13 REQUIRED (0, 0, 1, 6, 3, 0, 3) instead of 146, PESEL validator present in sets 03 and 08. Open requests of its status file: a warning code of its own for "validator not written" (after lane 4), REGON and TERYT defaults of memo V-1 (decision of the program lead) |
| 2 | Jury documents, `wp/F-jury-docs` | `README*.md`, `apps/converter/README.md`, documents that named the self-test | **`merged` 00:41, `ee7ceaa`** | Nothing. The READMEs carry the V1 core digest `061fce4b...`; replace it by the digest of the FINAL code commit in the last documents commit before the freeze (one `sed` over `README.md`, `README.pl.md`, `README.ru.md`, `apps/converter/README.md`) |
| 3 | Image checks, `wp/F20-image-checks` | `apps/converter/Dockerfile`, `docker-compose.yml`, `.github/workflows/**`, `tools/ci/**` | **`merged` 00:25, `4e1439a`** | Nothing. Branch run of the head green in both targets; recorded RED run: actions/runs/44961782575 (throw-away branch `wp/F20-red-proof` with `AUTH_MODE=jwt` baked in: the first-run check failed 4 of 65 in core). That branch is still on origin: NEVER merge it; deleting it needs the owner's permission |
| 4 | Visible engine H4, `wp/H4-engine-visible` | `app/engine.py`, `app/main.py`, `app/cli.py`, `app/config.py`, three warning codes, `apps/review-web/**` badge | **`merged` 01:07, `40e1876`** | Nothing in code. Proof: form and sidecar byte-identical to `main` on 158 of 158 chain files and 79 of 79 fixtures and set files; fast gate green. Its status commit `cbd097d` (status file only) came after the merge: `git merge --no-edit wp/H4-engine-visible` brings it. Open: the document lines with proposed text in `wip/WP-H4.status.md` under "Requests to lead" (jury Q and A "domyślnie", D12, D13, D14 exception, design line 154, README table rows `MODEL_STEP`, `MODEL_BASE_URL`, `MODEL_NAME`, `MODEL_API_KEY_FILE`); the badge was not seen in a real browser; `MODEL_STEP` defaults to `auto` and does nothing until a model step is built |
| 5 | Floor: set 08 and the release proof (backlog B4) | `results/**` (merge lead only) | `free`, merge lead only | After lanes 1 to 3 merge: rebuild the seven results and set 08 from the image; proof on the exact digest: `--network none --read-only --cpus 2 --memory 4g`, cold start, `/status`, REST convert, three byte-identical runs; script `jury_accept.sh` of the private preparation folder; name the fallback digest |
| 6 | Wide run on V1 (L1) | none (reads only; logs in `tmp/`) | `free` | The 584 other archive files and the hold-out forms through the V1 image: 0 failed, 0 gate, no plain 500; counts only |
| 7 | Rules mined from the model H0, `wp/H0-model-mined-rules` | `app/lexicon/concepts.json` and the cue lists | `free`, only AFTER lane 1 merges (same files) | The model-placement decision, section 3 row 2; chain no worse; not green by 03:00: drop |
| 8 | Honest tests, `wp/F-tests-honest` (one commit `1998872`) | `apps/converter/tests/**` except compose, validators and the files of lanes 1 and 4; `apps/review-web/scripts/**`; `eval/chain/report.py`, `eval/chain/tests/**` | `free` | Section "F-TESTS" of [`NEXT-WAVE.md`](NEXT-WAVE.md); new tests proposed by the audit arrive as new files from the program lead |
| 9 | Scans: `SCAN_PREP` packages | `app/readers/image.py`, `app/readers/_raster.py` | **NOT OURS**: the program lead's scan lab (agents SL0, SL1 on the API key, private copy) writes them as patches; decision 05:00, merge of the GO packages by 06:30 | Do not change `readers/image.py` and `readers/_raster.py` before 05:00 without one line to the program lead |
| 10 | Model: ORDER M2 (`wp/M-weak-page-reader`, `wp/M-title`) | as the council chair's note says | `free`, **only after the program lead writes "M2 PROBE GO"** (its probe had 0 complete answers of 5; kill line 01:30) | Nothing until then; on KILL the model stays a slide and the window goes to completeness |
| 11 | ORDER C1, `wp/C1-required-cues` | `app/mean/_fields.py`, `app/lexicon/habits.json`, `tests/mean/**` | **`merged` 01:24, `7cdcbfc`** | Nothing. Proof: fast gate green; chain 158 files 0 failed, 0 worse, 0 better; 28 fields of the briefs of sets 08 and 09 go from "required, inferred" to optional ("Adres do korespondencji ... jeśli różni się", "Ewentualne dodatkowe informacje", the section "(pola nieobowiązkowe)"); no REQUIRED and no validator of any of the 70 set inputs changes. C2 may now start on `origin/main` (the program lead's agent CX) |
| 12 | ORDER C3, `wp/C3-docx-numbering` | `app/readers/docx.py`, `tests/readers/test_docx_numbering.py` | **`merged` 01:13, `bd71323`** | Proof: chain 158 files 0 worse, 4 better; set 03 DOCX gains the checkbox group, set 06 DOCX uploaders 6 to 11 and a RADIO. NOT met: set 04 DOCX four consents (the reader now gives "1)" to "4)", but a later step drops them; the builder's unchecked guess is the `NOTE` pattern of `app/find/_core.py` reading "1) " as a footnote): request in `wip/WP-C3.status.md`, passed to the program lead for its agent CX |
| 13 | ORDER C2, C4, C5, C6 | `app/mean/**`, `app/find/**`, sheet readers | **NOT OURS**: the program lead's agent CX (API key, private copy) writes them as patches with tests and the seven-set comparison | At 05:00 apply the patch stacks that their reports mark READY or GO, in this order: CX (completeness), SL1 (scans), verified audit patches, ML1 (model, only after the program lead's GO at about 05:45), the patch of the review page `/ui/`. One at a time: `git apply --check`, a branch per stack, fast gate, chain compare, merge. Merges by 06:30. Do not change `apps/review-web/**` before the page patch arrives |

Small open items (merge lead): a wait for a free slot instead of an immediate 429 (`QUEUE_WAIT_S`, about 15 lines in
`main.py`, after lane 4); a warning code of its own for "validator not written" (after lane 4, same file);
`docs/03-plan/NEXT-WAVE.md:21` and `wip/WP-F20.status.md` still name the self-test endpoint; D19 M2 decision line
(G5 stays a warning); documents of `converter-design.md` and `coi-json-format.md` must say the same about REQUIRED.

## 5. Never

`git add -A`, stash, rebase, force push, history rewriting; a commit to `main` by a lane lead; two leads in one
worktree; a key, real personal data, the partner's task sets or notes of the leads' folder in git; anything in the
product that calls out of the container; "done" before the result was checked where the jury will see it.
