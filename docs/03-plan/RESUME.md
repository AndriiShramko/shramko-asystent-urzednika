# RESUME: continue the build from here, on any subscription

One file for a lead that starts cold: after a limit stopped the previous lead, or beside it from another subscription.
It holds the start prompt, the rules of parallel work through git, the board of lanes and the queue.
The merge lead keeps the board current: after every merge, every start or stop of an agent, and before every wait.

**Board updated: 2026-11-22 04:44 CET by `build8`** (build lead 8, the only writer of `main`; reports to program lead 10, session `local_02a98ca6-87e0-4b58-bfe8-7d70c96bf32d`). The owner may close every session about 04:50: **a lead that starts cold continues from THIS block; the 04:16 block under it is history.**

- **`main` = `4d84187`** (code; this documents commit sits on top). In it since the 04:16 block: ML1-4 (`ac153b9`), DC-2 (`696f9c0`), and the group CX-7, CX-8, REV-1, REV-3 (`4d84187`, merged and pushed 04:42 after its fast gate; if `git log origin/main` does not show `4d84187`, the merge did not finish: run `bash tools/lead/merge.sh wp/A10-g4 "<message>"` again from a clean main checkout).
- **UPDATE 04:58 (newest; where this line and an older one differ, this line wins): `main` code = `8db2183`** = `4d84187` + scan preparation behind the switch `SCAN_PREP` (SL1-0, SL1-3, SL1-1, SL1-2, SL1-4, SL1-6; default OFF, so nothing changes unless the operator sets `SCAN_PREP=on`). **Build V1.11 of `8db2183` is verified end to end**: core `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:1b0e032bf2a9d058442b51978d0f5fae016bee30316741f64225d3a1e86f5870` (plus `...@sha256:761b7bdf921cc47dc5131e65b4a16a240a4ee7127cb641e5b1ae7fec7b75debb`), image workflow green, `jury_accept.sh` ALL PASS 04:57 (log `tmp/jury-accept-sl1s6.log`), PDF and PNG of set 03 convert with 200 in the container. **The owner's container `sau-v1` on 127.0.0.1:8080 runs V1.11 since 04:58. Every commit of `main` is in a verified image.** One thing is open: SL1-7 (scan preparation ON by default), branch `wp/A10-sl1` `af9d50a` (= `wp/A10-sl1-s6` + one commit; pushed also as `wp/F20-sl1-default-on`, test image `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:2552ea2414d88b69d310a772167bbe2207ca3817763eb097019775a8b5698eca`). Its A/B run on the 27 images of the seven sets was running at 04:58 (`tmp/scan-ab-bl8.log`; counts with `python C:/dev/sau-private/audit8/cx/bl8_scan_count.py C:/dev/sau-private/audit8/cx/bl8-scan-ab`); merge it (`bash tools/lead/merge.sh wp/A10-sl1 "<message>"`) only if no set image loses paper fields with the default AND the program lead says yes; then image, jury acceptance, container. The build lead `build8` hands over here: its context is full. The next lead starts with section 1 of this file.
- At 04:49 it was build V1.10 of `4d84187` (everything merged tonight up to CX-7, CX-8, REV-1, REV-3) = core `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:1ac0727e7ed3ce7a14ce02d7c28061fe81afd4907f6abde0bcf8b42e57d04323` (plus `...@sha256:c819e9140ceb9e27a98973da4c7236ddb2dd45be56a8f1c84945c99a44fc1cb6`): image workflow green (actions/runs/44981824204), `jury_accept.sh` ALL PASS 04:47 (log `tmp/jury-accept-g4.log`), sets 02 and 09 as PDF, XLSX, DOCX convert with 200 in the container. **The owner's container `sau-v1` on 127.0.0.1:8080 runs V1.10 since 04:48; nothing merged before 04:45 is left unverified.** Scan preparation since then: `wp/A10-sl1-s6` (switch `SCAN_PREP`, default OFF) was being merged at 04:49 (log `tmp/merge-bl8-sl1s6.log`; if `git log origin/main` shows no merge of `wp/A10-sl1-s6`, run it again; after it: image, jury acceptance, container). The default-on variant is the pushed test-image branch `wp/F20-sl1-default-on` `af9d50a`: the native chain cannot measure it (no OCR on the laptop: its 158 lines were identical), so the 27 images of the seven sets go through its test image with `SCAN_PREP=off` and with the default (`bash C:/dev/sau-private/audit8/cx/bl8_scan_ab.sh <test image digest> C:/dev/sau-private/audit8/cx/bl8-scan-ab`, then `python C:/dev/sau-private/audit8/cx/bl8_scan_count.py <the same folder>`; a job of the build lead was doing it, result `tmp/scan-ab-bl8-count.txt`). SL1-7 (default on) merges only if no set image loses paper fields there AND the program lead says yes.
- At 04:43 it was build V1.9 of `696f9c0` (V1.8 plus ML1-4 and DC-2; the first image without the seven removed libraries) = core `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:d8c04e106173db9798fe61fa7692308f4d0a347d19e545c12562c951f6b097cd` (plus `...@sha256:5b926c76a8e2d4432ec57b3858bfbc54e683c1e2988511c306f1fc35e5147725`): image workflow green in three jobs (actions/runs/44981374052), `jury_accept.sh` ALL PASS 04:41 (log `tmp/jury-accept-696f9c0.log`); live in the container: `/status` engine rules and no `vision` key, all eight formats of set 03 convert with 200, `/v1/forms/preview` 200. **The owner's container `sau-v1` on 127.0.0.1:8080 runs V1.9 since 04:42.** Only the image of `4d84187` (adds CX-7, CX-8, REV-1, REV-3) is still to verify.
- Before that: build V1.8 of `0a6f122` = core `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:04f9ba36b838ab50d968712d2a4977b47ac4811a77d6ff9d585bf8dffa30ca3f` (plus `...@sha256:bfa8b1217a108003307201339fab6a8893e3de1e6d7d86389cb6ea94430fc14c`): image workflow green, `jury_accept.sh` ALL PASS 04:25 (log `tmp/jury-accept-fp2.log`), `/v1/forms/preview` 200 in the container, the fill-and-print page seen in a browser. **The owner's container `sau-v1` on 127.0.0.1:8080 runs it.** It does NOT hold ML1-4, DC-2 and the CX-7/CX-8/REV group.
- **To verify next, in this order** (each: `bash tools/gate.sh py tools/ci/wait_run.py $(git rev-parse <sha>) --timeout 540`; `bash tools/gate.sh py tools/ci/image_digest.py <full sha> --target core`; `bash C:/dev/sau-private/prep/c2/jury_accept.sh <core digest> "$(pwd)/tmp/bl8-form03.pdf"`; then replace the container with the command of section 3 and check `/healthz`, `/status`, one conversion, `/ui/`): the image of `4d84187` (it is the first image WITHOUT pypdf, python-docx, openpyxl, defusedxml, filetype, rapidfuzz, simplemma: the workflow's container tests must be green; the test image of DC-2 alone was). Logs of the jobs that were running at 04:44: `tmp/ci-bl8-g4.log`, `tmp/jury-accept-g4.log`, `tmp/ci-bl8-dc2main.log`.
- **In flight, not merged: scan preparation SL1** (the scan lab's report says GO for all steps but S5 orient). Branches in worktree `.claude/worktrees/a10-sl1`: `wp/A10-sl1-s6` `f66b272` = `wp/A10-g4` + SL1-0, SL1-3, SL1-1, SL1-2, SL1-4, SL1-6 (`git am --3way`, this order; the product does not change unless `SCAN_PREP=on`); `wp/A10-sl1` `af9d50a` = the same + SL1-7 (scan preparation ON by default: the only patch that changes what the jury sees on scans). The fast gate and the chain compare of `wp/A10-sl1` started 04:38 (`tmp/bl8.status`, `tmp/bl8-gate.log`, `tmp/bl8-chain.log` in that worktree). Decision asked from the program lead at 04:38: merge SL1-7 or not; default without an answer: merge `wp/A10-sl1-s6` only (after a fast gate of its own) and leave SL1-7 out. With default on, the chain lines of the set images and scans WILL differ from the baseline: read them (fewer fields on an image = stop).
- **Chain reference**: baseline of `0ba96ce` (commit `968e079`). Expected lines against it on `4d84187`: the six of `tmp/chain-bl8-g3-44c5ca2.log` plus the six of the group (`tmp/chain-bl8-g4.log`: sets 09 XLSX/ODS 78 -> 85, sets 02 XLSX/ODS 56 -> 55, unseen `123b1988b1860959` 143 -> 149, unseen `c4a4ae01f133b7fd` 81 -> 80; all read by hand). Rebuild the baseline on the final `main` (`bash tools/gate.sh py -m eval.chain --update-baseline`, commit both files of `eval/chain/`).
- **Not done**: the README paragraph about the model step (text in the private `wave-10/reports/ML1R.md`); the final digest in README (V1 `061fce4b` in 9 places); the seven `results/` JSON plus set 08 from the final image; `integration.mjs` (no `playwright` on the laptop).

Board at 04:16 by `build8` (the only writer of `main`). The owner may close every session about 04:50: a lead that starts cold continues from this block.

- **`main` = `0a6f122`** (pushed 04:14). **Last digest verified end to end: build V1.7 of `67d5b0e`** (section 3); the owner's container `sau-v1` on 127.0.0.1:8080 runs it. The image of `0a6f122` (adds fill and print) was being built at 04:16: wait with `bash tools/gate.sh py tools/ci/wait_run.py $(git rev-parse 0a6f122) --timeout 540`, digest with `tools/ci/image_digest.py <hash> --target core`, then `bash C:/dev/sau-private/prep/c2/jury_accept.sh <core digest> tmp/bl8-form03.pdf`, then replace the container (command in section 3) and look at `/ui/` in a browser (upload a PDF: the fill-and-print block must appear under the result).
- **Merged tonight by `build8`**, each with the fast gate on the branch and on the merge commit and a chain run of 158 files with 0 failed: ORDER 3 part A (`b867cf8`, 19 audit patches) and part B (`8cf1145`, 6); the review page ORDER UI with one mode badge (`864c0c9`); ORDER C4, C5, C6, C2 from the head of `a8/CX` (`9bfe33d`); RC-1 to RC-5, EM-1, DX-1 to DX-3, DC-1 (`0ba96ce`); RC-6, RC-7, VJF-1 to VJF-3 (`0bc88a8`); UX2-1 (`67d5b0e`); fill and print FP-1 to FP-6 with the read-only `POST /v1/forms/preview` (`0a6f122`). The chain baseline was rebuilt on `0ba96ce` (commit `968e079`); against it `0bc88a8` and later show exactly "1 worse, 5 better" (six unseen files changed by VJF, read by hand): any other line is a new difference.
- **In flight, not merged** (local branches with worktrees under `.claude/worktrees/`):
  - `wp/A10-ml4` `df84cde` = `0a6f122`'s content + ML1-4 (optional model step for weak scan pages; off unless `VISION_BASE_URL` and a key are set). Independent security review: MERGE (notes in the private `wave-10/BUILD-STATUS.md`). Its fast gate and chain compare were running at 04:16 in `.claude/worktrees/a10-ml4` (`tmp/bl8.status`, `tmp/bl8-gate.log`, `tmp/bl8-chain.log`). Merge only if the gate passed AND the compare lines equal those of `tmp/chain-bl8-g3-44c5ca2.log` (nothing configured = no difference): `bash tools/lead/merge.sh wp/A10-ml4 "<message>"`.
  - `wp/F20-dc2-deps` `a060715` = `0bc88a8` + DC-2 (four unused libraries removed, three moved to the dev extra). Pushed as a test-image branch: workflow green in all three jobs (actions/runs/44978317040). Merge LAST, then wait for the image of `main` and run the jury acceptance.
  - CX-7 and CX-8 (follow-ups of ORDER C in the private patches folder): not applied, their author had not marked them READY.
- **Held or returned**: `SL1-*` (scan preparation: no GO, the measurement did not prove a gain); ML1-3 (replaced by ML1-4); the stale local branch `wp/A8-cx` (built from old patch files, never merge it; `wp/A8-cx2` is the merged one); `wp/F20-red-proof` is never merged.
- **Not verified**: `apps/review-web/scripts/integration.mjs` and `devices.mjs` were not run tonight (the `playwright` package is in no local `node_modules`); the page is looked at in a browser on each built image instead. `/v1/forms/preview` was called live only on a natively started service, not yet in a container (the FP-S author's script: `C:/dev/sau-private/audit8/logs/FP-S/live.sh`).
- **How this night's merges were done** (repeat it): a branch `wp/...` in a worktree from `main`, patches with `git apply --index` (or `--3way`), `SLOTS=4 bash C:/dev/sau-private/audit8/slot.sh BL8 bash tools/gate.sh fast`, then `bash tools/gate.sh py -m eval.chain --compare --archive C:/dev/shramko-asystent-urzednika/data/archive` (restore `eval/chain/summary.json` afterwards), a dump of the seven sets with `C:/dev/sau-private/audit8/cx/dump.py` and `diff.py` when the converter's output may change, `bash tools/lead/merge.sh <branch> "<message>"` from the main checkout, wait for the image, jury acceptance, container swap, one line in the private `wave-10/BUILD-STATUS.md`.
- **After the last feature merge (06:30)**: the final digest into README (V1 `061fce4b` is named in 9 places), the seven `results/` JSON plus set 08 rebuilt from the final image (`tools/lead/snapshot_results.py`), the chain baseline rebuilt on the final `main`, documents. Freeze 08:30.

Board at 03:15 by `build8` (it replaced `build7`, whose session and every earlier session are closed since about 02:05). It reports to program lead 10 (session `local_02a98ca6-87e0-4b58-bfe8-7d70c96bf32d`). State at 03:15: `main` = `864c0c9`, build V1.5 verified end to end (section 3). Merged tonight by `build8`: ORDER 3 part A (`wp/A8-stack-1`, 19 audit patches, `b867cf8`), part B (`wp/A8-stack-2`, 6 patches, `8cf1145`), the review page ORDER UI with one mode badge (`wp/A8-ux`, `864c0c9`). Checked and waiting on local branches, in this order: `wp/A8-cx2` (ORDER C4, C5, C6, C2 from the head of the author's branch `a8/CX`; fast gate passed, the field-by-field reading of the set diff decides), `wp/A10-g2m` (RC-1 to RC-5, EM-1, DX-1 to DX-3, DC-1), `wp/A10-rc67` (RC-6, RC-7), then ML1-3, VJF, DC-2 (needs a full gate and an image build), FP-1 to FP-6 last. `SL1-*` is held: no GO. `wp/F20-red-proof` is never merged. Patches arrive in the program lead's private folder `audit-8/patches/`; the journal of merges with digests is its `wave-10/BUILD-STATUS.md`. Heavy commands on this laptop go through `SLOTS=4 bash C:/dev/sau-private/audit8/slot.sh BL8 <command>`. Last feature merge 06:30, freeze 08:30. The chain baseline `eval/chain/baseline.json` is still the one of `14170bf`: compare lists are read against the previous run's list (logs `tmp/chain-bl8-*.log`); rebuild it on the final `main`.

Board before that: 2026-11-22 01:32 CET by `build7`. Report to program lead 9 (session `local_fba1e498-2f81-4cd1-9cc2-ebba7c37471b`), which replaced program lead 8 about 00:30. Common rule of every gate of ORDER C: no judged set loses a matched element in any format; nothing merges without the seven-set diff.

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
| `main` code | `4d84187`: build V1.8 plus ML1-4 (`ac153b9`), DC-2 (`696f9c0`) and CX-7, CX-8, REV-1, REV-3 (`4d84187`); its image is NOT verified yet (see the block at the top) |
| **Build V1.8** (V1.7 plus fill and print FP-1 to FP-6) | commit `0a6f122`: core `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:04f9ba36b838ab50d968712d2a4977b47ac4811a77d6ff9d585bf8dffa30ca3f`, plus `...@sha256:bfa8b1217a108003307201339fab6a8893e3de1e6d7d86389cb6ea94430fc14c`; image workflow green, `jury_accept.sh` ALL PASS 04:25 (log `tmp/jury-accept-fp2.log`); live in the container: convert 200, `POST /v1/forms/preview` 200 (set 03 PDF: one page picture, 16 places boxed); the fill-and-print page seen in a browser. **Last digest verified end to end; the owner's container `sau-v1` on 127.0.0.1:8080 runs it** (`docker run -d --name sau-v1 -p 127.0.0.1:8080:8080 --cpus 2 --memory 2g -e JOB_TIMEOUT_S=600 <core>`) |
| Build V1.7 (V1.6 plus RC-6, RC-7, VJF-1 to VJF-3, UX2-1) | commit `67d5b0e`: core `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:2e29aa03c8da7a8a7c0add95f6ffc06087986d522899a135857df009d67ec743`, plus `...@sha256:ad2fced9e9a09f30b067aa2cb5e2c3aa12b103f95283bc664d56fefd6153ecf1`; image workflow green (actions/runs/44978775714), `jury_accept.sh` ALL PASS 04:11 (log `tmp/jury-accept-ux2.log`); the page seen in a browser: headline "Formularz przetworzony: 52 pola w 17 sekcjach (z druku: 6, standardowych: 46)", remarks grouped by kind, one mode badge; `/v1/forms/report` carries `meta.evidence`; superseded by V1.8 |
| Build V1.6 (V1.5 plus ORDER C4, C5, C6, C2, RC-1 to RC-5, EM-1, DX-1 to DX-3, DC-1) | commit `0ba96ce`: core `...@sha256:f8d8b8042711a8acb54b0cd06e5399b413d5963533ce80afd1510e151cfca28e`, plus `...@sha256:78b8430059f55703d7bab4b054023968a32d33c9ac353927edbeed7ba8b63f0e`; image workflow green (actions/runs/44976534202), `jury_accept.sh` ALL PASS 03:41 (log `tmp/jury-accept-0ba96ce.log`) |
| Build V1.5 (V1.4 plus ORDER 3 part B and the review page ORDER UI; superseded) | commit `864c0c9`: core `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:2148c8fc9ee9f0e35b1b4cb170484aa63e687fa46feac5d77bc97d352aa1a100`, plus `...@sha256:e43b4457c32d229915fbf236222920fd0a1632b53cac96b2654065b247492151`; image workflow green (actions/runs/44974012714), `jury_accept.sh` ALL PASS 03:14 (log `tmp/jury-accept-864c0c9.log`); the page seen in a browser on this image: one badge "Tryb: reguły i lokalny OCR, bez modelu AI", a conversion gives "Formularz przetworzony: N pól w M sekcjach". superseded by V1.6 and V1.7 |
| Build V1.4 (V1.3 plus ORDER 3 part A, 19 audit patches) | commit `b867cf8`: core `...@sha256:d8a6e5ab3ff044ef64f4c6eb958dfbbeea0d4b020d9e95adc3e2d3af62a5b506`, plus `...@sha256:18b1e286efb26b9ac8446f244b6e522225b72bfda1a42158016f351786cb6c93`; image workflow green (actions/runs/44972114495), `jury_accept.sh` ALL PASS 02:46 (log `tmp/jury-accept-b867cf8.log`); chain 158 files 0 worse |
| `main` code before `build8` | `7cdcbfc` (pushed 01:24): everything of the row below plus ORDER C1 (required and optional by the paper's words) |
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
