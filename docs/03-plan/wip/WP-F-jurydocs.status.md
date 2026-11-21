# WP-F-jurydocs README commands the jury can paste, and no promise without code: status

Branch: wp/F-jury-docs   Stage now: core (documents only)

## Status
- [x] J2: jury section in `README.md`, `README.pl.md` (Polish), pointer in `README.ru.md`, matching part of `apps/converter/README.md`; stale digest `de661b01...` removed from all READMEs
- [x] Item 2: commands 1, 2, loop and 3 run in Git Bash and Windows PowerShell 5.1 against the current core image (see Evidence)
- [x] Item 4: configuration table (`AUTH_MODE` auto with three values, `JOB_TIMEOUT_S` 600, honest note on the open default); stale rows and the misplaced paragraph inside the table removed
- [ ] J3: every `v1/selftest` mention replaced
- [ ] Item 5: link check

## Decisions
- Every bash command starts with `MSYS_NO_PATHCONV=1` (except the Linux `--user` line) / measured: without it Git Bash rewrites `/in/form.pdf` into a Windows path and `convert` exits 4 "Cannot read the file" / harmless env variable on Linux and macOS, so one line serves all three bash hosts.
- PowerShell command 1 is `cmd /c '... > form.json'` with `%cd%` / measured: PowerShell 5.1 `>` writes UTF-16 LE with BOM (69408 bytes instead of 34702, `FF FE`, not parseable as UTF-8); `cmd` keeps the bytes / rules out showing PowerShell's own `>` anywhere.
- `--platform linux/amd64` on every `docker run` / harmless on amd64, lets an ARM Mac run the amd64 image without a mismatch.
- Full image reference in every command, no `$IMAGE` variable / a pasted line must work alone.
- "What works" lines rewritten to what the code has (readers for all eight formats incl. OCR, tested here on a PNG: exit 0); no accuracy claims.

## Evidence
Scratch folder `C:\Users\andri\AppData\Local\Temp\jurydocs` (outside the repository): synthetic `forms/form.pdf` (reportlab, labels only: "WNIOSEK O WYDANIE ZASWIADCZENIA", Imie, Nazwisko, ...), copy `forms/form2.pdf`, synthetic `img/form.png` (PIL). Test image: core `@sha256:e8205af582bc9a5da0d4ee987d19560d9786429367ce87258ab354b8e7eb4641` in place of the placeholder. Docker Desktop 29.9.3. Scripts `t_bash.sh`, `t_ps.ps1`, `t_rest.sh` there run the README lines verbatim. At most one container at a time; after the REST test `docker ps -q | wc -l` = 0.

| Item | Command (as in README) | Result |
|---|---|---|
| 1 bash, Git Bash, without the prefix | `docker run ... -v "$PWD/forms:/in:ro" IMG convert /in/form.pdf > form.json` | FAIL: exit 4 "Cannot read the file" (MSYS path conversion), hence the prefix |
| 1 bash, Git Bash | `MSYS_NO_PATHCONV=1 docker run --rm --platform linux/amd64 --network none --read-only --cap-drop ALL -v "$PWD/forms:/in:ro" IMG convert /in/form.pdf > form.json` | exit 0, 34702 bytes, no BOM, keys flow,tabs,title |
| 2 bash, Git Bash (no `--user`) | `mkdir -p out && MSYS_NO_PATHCONV=1 docker run ... -v "$PWD/out:/out" IMG convert /in/form.pdf --out /out/form.json` | exit 0, 34701 bytes, no BOM, keys flow,tabs,title |
| 2 bash, `--user` line | `... --user "$(id -u):$(id -g)" ...` (Git Bash, uid 197609, with the prefix) | exit 0, 34701 bytes; proves the syntax only, not a Linux host |
| loop bash | `mkdir -p out && for f in forms/*; do n="${f##*/}"; MSYS_NO_PATHCONV=1 docker run ... convert "/in/$n" > "out/${n%.*}.json"; done` | exit 0, out/form.json and out/form2.json, 34702 bytes each, no BOM, keys ok |
| trap PS 5.1 (5.1.26100) | `docker run ... -v "${PWD}/forms:/in:ro" IMG convert /in/form.pdf > form_naive.json` | 69408 bytes, starts FF FE (UTF-16 LE BOM), UTF-8 parse fails: not shown in README |
| 1 PS 5.1 | `cmd /c 'docker run ... -v "%cd%\forms:/in:ro" IMG convert /in/form.pdf > form.json'` | exit 0, 34702 bytes, starts 7B 22, no BOM, keys flow,tabs,title |
| 2 PS 5.1 | `mkdir -Force out \| Out-Null; docker run ... -v "${PWD}/forms:/in:ro" -v "${PWD}/out:/out" IMG convert /in/form.pdf --out /out/form.json` | exit 0, 34701 bytes, no BOM, keys ok; `${PWD}` (C:\...\jurydocs/forms) accepted by Docker Desktop |
| loop PS 5.1 | `mkdir -Force out \| Out-Null; Get-ChildItem forms -File \| ForEach-Object { docker run ... convert "/in/$($_.Name)" --out "/out/$($_.BaseName).json" }` | exit 0, out\form.json and out\form2.json 34701 bytes, no BOM, keys ok |
| 3 REST | `docker run --rm --platform linux/amd64 -p 127.0.0.1:8080:8080 --read-only --cap-drop ALL -e AUTH_MODE=off IMG` (`-e` only for this test) | `/healthz` up after 4 s: `{"status":"ok","version":"0.1.0"}`; `/ui/` 200; `/status` 404 on this image (expected, new route) |
| 3 curl bash | `curl -F "file=@form.pdf" http://127.0.0.1:8080/v1/forms/convert -o form.json` | 200, 34701 bytes, no BOM, keys ok; equal to the CLI bytes minus the final newline |
| 3 curl.exe PS 5.1 | `curl.exe -F "file=@form.pdf" http://127.0.0.1:8080/v1/forms/convert -o form.json` | exit 0, 34701 bytes, no BOM, keys ok |
| PNG offline | command 1 on `img/form.png` | exit 0, 33788 bytes; OCR labels Nazwisko, telefonu found in the JSON |

## Not verified
- exit 4 with one line for an unwritable `--out` path, `GET /status`, the no-flags start (`AUTH_MODE=auto`), `JOB_TIMEOUT_S` 600: behaviour of `wp/F-service-fixes`, not in the tested image. The lead tests them on the new image.
- The Linux `--user "$(id -u):$(id -g)"` line on a real Linux host, and an ARM Mac: no such machine here.
- The final digest: the lead replaces `REPLACE_WITH_FINAL_DIGEST` after the CI build.

## Placeholder `REPLACE_WITH_FINAL_DIGEST`
Listed by `git grep -n REPLACE_WITH_FINAL_DIGEST` (filled in below at the end of the stage).

## Negative control
Documents only. The control is the Git Bash run without `MSYS_NO_PATHCONV=1` (exit 4) and the PowerShell `>` run (UTF-16 BOM): each breaks what the README promises, both are recorded above, the README lines avoid both.

## Requests to lead
- After CI builds `wp/F-service-fixes`: replace the placeholder in the files listed above, then run on the new image the PowerShell command 3 without `-e AUTH_MODE=off`, `curl.exe http://127.0.0.1:8080/status`, and command 2 into a read-only folder (expect exit 4, one line).

## Cost notes
- core: the Git Bash path conversion and PowerShell redirect traps took the test turns; a ready scratch test script per shell would make it cheaper.
