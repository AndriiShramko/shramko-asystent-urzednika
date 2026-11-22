# SUBMISSION: how this work is handed in (HackNation 2026, Sunday 22 November)

Rules for whoever builds, checks and hands in the final version. Code freeze 08:30, hand-in on HackTribe 11:00, finals 15:15, where the jury runs our image on new files. Every time below is read from the shell (`date`), never estimated. The build lead is the only writer of `main`.

## 1. What the task card and the platform ask for
- Task card, formal requirements: a detailed description and the title; a PDF presentation of at most 10 slides; the result JSON files of the forms; a film of at most 3 minutes, as a link to an open place; the code repository. Optional: screenshots, demo links, graphics.
- Task card, technical: a README with the Docker build, the run, the configuration and the REST API; official base images, explicit versions, no `latest` tag, a non-root user, only the needed ports, secrets only at run time.
- Task card, testing: the finalists run the solution on new files during the defence.
- HackTribe: the project can be edited until 11:00; the presentation is a PDF file of at most 10 MB; a short demo (at most 2 minutes recommended); jurors spend only a few minutes per project; links must work; the film is a public or listed YouTube link.

## 2. Order from the last merge to the hand-in
| When | Step | Done when |
|---|---|---|
| 08:30 | Last code merge pushed to `main` (the freeze commit) | its sha is written in `RESUME.md` |
| 08:30-08:45 | Wait for the image workflow of the freeze commit; read the `core` digest | `bash tools/gate.sh py tools/ci/wait_run.py <full sha> --timeout 540` green; `bash tools/gate.sh py tools/ci/image_digest.py <full sha> --target core` |
| 08:45-09:15 | Verification, section 4, on that digest only | every line passes, logs named in `RESUME.md` |
| 09:15-09:30 | `results/` rebuilt from the final image (`bash tools/gate.sh py tools/lead/snapshot_results.py .`), `results/README.md` rewritten with the date and the digest; the README digest replaced everywhere; README top as in section 6 | `grep -o 'sha256:[0-9a-f]*' README.md \| sort -u` prints one line, the final digest |
| 09:30-09:40 | Fallback archive made and measured (section 5) | size written in `RESUME.md` |
| 10:00-10:45 | Film link, PDF and the platform texts checked and pasted; the project saved on HackTribe (more than once is fine) | the project page read back after each save |
| 10:50 | Nothing changes any more unless something is broken | |

If the image of the freeze commit fails, the hand-in digest is the last digest that passed section 4. A digest that has not passed section 4 is never handed in.

## 3. How the final image is built
- Only CI builds the published image: `.github/workflows/image.yml` on a push to `main`, targets `core` and `plus`; the hand-in is the `core` image, by digest, never by tag.
- Trap 1: `paths-ignore` covers only `docs/**` and `research/**`. A push that changes `README.md` or `results/**` starts a new image build (new digest, same code). The verified digest stays valid and pullable, so the README names the digest of the freeze commit; do not chase the newer digest.
- Trap 2: `concurrency` with `cancel-in-progress: true` on `main`. A push while the freeze image is still building cancels that build. Push nothing to `main` between the freeze and the green, pushed freeze image.
- Build from source (only as the last fallback; needs network for the bases and wheels): `docker build -f apps/converter/Dockerfile --target core -t converter:core .` from the repository root.

## 4. How the final image is verified (`IMG=ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:<final>`)
### 4a. As a stranger, by command
1. Pull without any credentials: `E=$(mktemp -d); echo '{}' > $E/config.json; DOCKER_CONFIG=$E docker pull $IMG` (make this the first pull of the digest on the machine). If it is already cached: `DOCKER_CONFIG=$E docker manifest inspect $IMG` returns 0, and an anonymous registry token reads the manifest: `T=$(curl -s "https://ghcr.io/token?scope=repository:andriishramko/shramko-asystent-urzednika:pull" | python -c "import sys,json;print(json.load(sys.stdin)['token'])")`, then `curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $T" -H "Accept: application/vnd.docker.distribution.manifest.v2+json" https://ghcr.io/v2/andriishramko/shramko-asystent-urzednika/manifests/sha256:<final>` prints `200`.
2. The repository without login: `curl -s https://api.github.com/repos/AndriiShramko/shramko-asystent-urzednika` shows `"private": false`.
3. The manifest is single-architecture `linux/amd64`; every README command keeps `--platform linux/amd64`, so an ARM Mac runs it under emulation (OCR is slower there).

### 4b. Acceptance of the README commands
The build lead's acceptance script runs, against one image and one PDF: the offline CLI to standard output three times with `--network none --read-only --cap-drop ALL` (byte-identical); `--out` into a mounted folder as the caller's user; an unwritable output folder gives exit 4 without a traceback; the REST service started with no flags comes up, two parallel first calls both answer 200, three REST answers equal the CLI bytes, the log warns that no token is required; the server stays up under `--network none`; explicit `AUTH_MODE=jwt` without a key exits 3. CI (`tools/ci/container_check.py`, `first_run.py`, `hostile_inputs.py`) proves the same on synthetic forms of every extension.

It does not cover, so each is checked separately below: the pull from the registry; formats other than PDF; OCR; the page `/ui/`; `/status`; `/v1/forms/report`, `/preview`, `/batches`; the README commands as printed in PowerShell and Git Bash; refusals of names and contents; 413 and 429; the optional model step and `SCAN_PREP`; the README digest.

### 4c. Separate checks, all must pass
1. Start with no flags: `docker run -d --name final-check -p 127.0.0.1:18091:8080 --cpus 2 --memory 2g $IMG`; `/healthz` 200 within 30 s; `/status` shows the engine `rules` and no model configured.
2. The card's eight formats, one file each, one after another (the eight files of one judged set: `.pdf .doc .docx .ods .xlsx .jpg .jpeg .png`): `curl -s -o out.json -w "%{http_code} %{time_total}\n" -F "file=@<file>" http://127.0.0.1:18091/v1/forms/convert`, then `python -c "import json;d=json.load(open('out.json',encoding='utf-8'));assert set(d)=={'title','tabs','flow'}"`. Eight times 200, eight silent asserts; write the times.
3. Refusals: a text file renamed `.pdf` gets a refusal with a Polish reason, not a 500; a file name with a character the card forbids (`; : > < / \ | ' * % $`) is refused.
4. The page `/ui/` in a real browser on that container: upload a PDF, look at the result, the places on the paper, the fill and print steps.
5. No key in the image: `docker run --rm --entrypoint sh $IMG -c env | grep -ci key` prints 0.
6. README command 1 run exactly as printed in Git Bash and in Windows PowerShell 5.1; the output is UTF-8 without a byte-order mark.

## 5. What is handed in, and the fallback
| Item | Content |
|---|---|
| Repository | `https://github.com/AndriiShramko/shramko-asystent-urzednika` |
| Image | `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:<final core digest>` |
| Result JSON | `results/` (the judged sets). The form of set 08 quotes the office's bank account from the paper, and the publishing check refuses any identifier with a valid check digit, so that one file travels as a release asset; `results/README.md` names the command that regenerates it |
| Film | YouTube link, at most 3 minutes |
| Presentation | PDF, at most 10 slides and 10 MB |

Fallback if a machine cannot pull from ghcr.io: an image archive, attached to the GitHub release of the freeze commit and carried on a USB stick to the finals.
`docker tag $IMG shramko-asystent-urzednika:final && docker save shramko-asystent-urzednika:final | gzip -1 > sau-final-<sha7>.tar.gz && sha256sum sau-final-<sha7>.tar.gz`
Expected size about 100 MB: the registry manifest of the 22 Nov 04:58 image sums 99.5 MB of compressed layers (354 MB unpacked); the real size is measured and written. To use it: `docker load -i sau-final-<sha7>.tar.gz`, then the README commands with `shramko-asystent-urzednika:final` in place of the digest. Before publishing it: load it once, check that the loaded image id equals the digest (containerd image store) or the config digest of the manifest (classic store), convert one file.
Second fallback at the finals: our own laptop runs the image and converts the jury's files. Third: build from source (section 3).

## 6. The top of the README (a juror with five minutes)
1. The title with the product name, Shramko Asystent Urzędnika, and one line: a blank official form (PDF, DOC, DOCX, ODS, XLSX, JPG, JPEG, PNG) in, the Form Generator JSON out, one REST call, one Docker image, CPU only, no network at run time.
2. The image by digest, once, copyable.
3. One command for the service and the page (`docker run --rm --platform linux/amd64 -p 127.0.0.1:8080:8080 <image>`, then `http://127.0.0.1:8080/ui/`), the offline CLI command right under it.
4. A table: where to see each scoring point (minimum scope, I dictionaries, II new dictionary, III conditions, IV page, V validations), one file or page place each.
5. Links: `results/`, the film, the REST API, the configuration.
6. Two lines of honest limits with measured numbers (photos and old DOC are the weakest; the optional model step is off unless the operator points it at his own open-weight server).
Never at the top: pre-event material, plans, absolute claims ("100 %"), statements that contradict the code.

## 7. What failed before, and how it is checked now
| What failed | Check |
|---|---|
| The README named an old digest in several places | one `sha256:` value in the README, the final one |
| `results/` was an early snapshot with a false README; one set missing | rebuilt from the final image; set 08 as a release asset |
| An early image needed `AUTH_MODE=off` to start | acceptance: start with no flags |
| Two first calls raced on a cold start | acceptance: two parallel first calls |
| A Linux `--out` folder was not writable | acceptance: `--out` as the caller, unwritable folder exits 4 |
| PowerShell `>` writes UTF-16; Git Bash rewrites `/in/...` paths | 4c line 6, both shells |
| A draft of the model step read a developer variable for its key | 4c line 5; the product reads only `VISION_API_KEY_FILE` or `VISION_API_KEY` |
| Docker Desktop stopped and every background job died | `docker ps` before each step |
| A README or results push during an image build cancelled it | nothing pushed between the freeze and its green image |
| Platform form: required fields, a wrong default task, an old browser draft restored | read the saved project page back after every save |
| Old numbers in the presentation and absolute claims in texts | the deck rebuilt from the final numbers; texts searched for "100 %" and claims the code does not back |
| The browser test script could not run on the build laptop | the page looked at in a real browser on the final image |
| More than two parallel uploads answer 429, more than 60 pages 413 | the README says "one after another" |
