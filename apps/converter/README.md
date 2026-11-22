# Converter service

A blank official form (PDF, DOC, DOCX, ODS, XLSX, JPG, JPEG, PNG) in, the JSON configuration of an electronic form out. This folder holds the service: configuration, guard, token check, HTTP endpoints, command line, image, and the reading pipeline behind `app/pipeline.py` (readers, local OCR, layout analysis and rules, composer, gate). No language model, no API key, no GPU. Design: [`docs/02-architecture/converter-design.md`](../../docs/02-architecture/converter-design.md).

Nothing here calls out of the container: no external API, no key fetching, no download at start.

## Run natively (Windows, Linux, macOS)

Python 3.13 or newer. From the repository root, with the shared environment of the repository (`tools/env_setup.sh`):

```bash
bash tools/gate.sh py -m converter convert FORM.pdf --out form.json --report out/   # no HTTP, no token
bash tools/gate.sh py -m converter serve --port 8080                                # API and front end
bash tools/gate.sh py -m pytest apps/converter/tests -q                             # the tests
python tools/env_check.py                                                           # what the machine has: Python, Docker, WSL, Tesseract, Node
```

`convert` exits 0 when done, 2 when the file was refused (a problem JSON on stderr), 3 when the configuration is inconsistent, 4 when the file cannot be read. `serve` listens on `127.0.0.1` by default; `--host 0.0.0.0` inside a container.

A key is a file. For a first run with a token:

```bash
printf '%s' "a long random string of at least 32 characters" > secret.key     # never commit it
JWT_SECRET_FILE=secret.key bash tools/gate.sh py -m converter serve --port 8080
```

Without a key file the default `AUTH_MODE=auto` runs open and logs a warning at start; `AUTH_MODE=off` does the same on purpose; `AUTH_MODE=jwt` without a key refuses to start (exit 3).

## Run in a container

The image is built by CI (`.github/workflows`, WP-F20) and published to `ghcr.io/andriishramko/shramko-asystent-urzednika`. To build it yourself (needs Docker; the build context is the repository root):

```bash
docker build -f apps/converter/Dockerfile -t converter:core .                 # core: Alpine, the default
docker build -f apps/converter/Dockerfile --target plus -t converter:plus .   # plus: Debian slim base, same code and the same OCR (Tesseract)
docker compose up --build                                                     # needs secrets/jwt_secret, see docker-compose.yml
```

Both images run as a dedicated user (uid 10001), expose port 8080, hold no secret, pin their bases by digest and install Python packages with `--require-hashes --only-binary=:all:`. The commands for the published image, tested in bash and in Windows PowerShell 5.1, are in the jury section of the root [`README.md`](../../README.md) (Polish: [`README.pl.md`](../../README.pl.md)). The published image: `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:c257e1ffb3c207642609a55ea1eb11a4adcf3b47582b4e2981bc21d3ed283923`. With a local build, conversion without a network on Linux (on macOS drop `--user`; in Git Bash drop `--user` and put `MSYS_NO_PATHCONV=1` in front, otherwise Git Bash rewrites `/in/...` into a Windows path):

```bash
mkdir -p out && docker run --rm --network none --read-only --cap-drop ALL --user "$(id -u):$(id -g)" -v "$PWD/forms:/in:ro" -v "$PWD/out:/out" converter:core convert /in/form.pdf --out /out/form.json
```

The same in Windows PowerShell 5.1 (`--out` keeps the file UTF-8 without a BOM; PowerShell's own `>` would write UTF-16):

```powershell
mkdir -Force out | Out-Null; docker run --rm --network none --read-only --cap-drop ALL -v "${PWD}/forms:/in:ro" -v "${PWD}/out:/out" converter:core convert /in/form.pdf --out /out/form.json
```

Started with no command the image serves REST on port 8080. Publish it on loopback (`-p 127.0.0.1:8080:8080`) unless a key file is configured: without one it is open. A REST server under `--network none` cannot be reached from the host, so the offline proof is the `convert` command above, not the server.

The front end (`apps/review-web`) is built in a Node stage if that folder exists, and served at `/ui/`; without it the image is built and the API works the same.

## Configuration

Everything comes from the environment; the service refuses to start on an inconsistent set and lists every problem. Keys come as files. Full list with meanings: design section 4. The ones that matter first:

| Variable | Default | Meaning |
|---|---|---|
| `AUTH_MODE` | `auto` | `auto`: JWT when a key file is configured, otherwise open with a warning in the log; `jwt`: a token is required and the service refuses to start without a key file (exit 3); `off`: open, with the warning |
| `JOB_TIMEOUT_S` | `600` | seconds one conversion may take; over it `504 TIMEOUT` |
| `JWT_ALG` | `HS256` | `HS256`, `HS384`, `HS512`, `RS256`, `ES256`, `EdDSA`; never read from the token, `none` is refused |
| `JWT_SECRET_FILE` / `JWT_PUBLIC_KEY_FILE` / `JWT_JWKS_FILE` | none | the key, by file (no key fetching) |
| `JWT_ISSUER`, `JWT_AUDIENCE` | none | required equal when set |
| `JWT_REQUIRED_CLAIMS`, `JWT_LEEWAY_S` | `exp`, `30` | `exp` cannot be removed; leeway at most 120 |
| `MAX_UPLOAD_BYTES` | `20971520` | largest upload |
| `CONCURRENCY` | `2` | uploads processed at once; more get `429 BUSY` at once |
| `RATE_LIMIT_PER_MIN` | `60` | per token subject; over it `429 BUSY` with `Retry-After` |
| `STRICT_EXTENSIONS` | `true` | `true` accepts exactly the eight extensions of the task card (`.jpe` is read as JPEG: the partner's judged set 7 ships one), any other answers 415 `EXTENSION`; the content must match the extension, else 415 `TYPE_MISMATCH` with a Polish reason and the remedy (a `.doc` holding DOCX or RTF is read by its content; a name without an extension is refused); `false` reads every file by its content and also accepts the other formats this build reads (ODT, XLS, RTF, TXT, TIF, TIFF, BMP, GIF, WEBP, HEIC, HEIF) |
| `NAME_POLICY` | `refuse` | the task card's name rule: a name over 250 characters or holding `; : > < / \ | ' * % $` is `400 BAD_NAME` with the reason in Polish; `clean` removes such characters and says so in the report instead. The review page always sends a cleaned copy of the name, so a clerk is never asked to rename a file |
| `DOC_READER` | `native` | `off` refuses binary Word with `415 DOC_READER_OFF` |
| `ACTIVE_CONTENT` | `warn` | `strict` refuses files with macros |
| `MAX_PAGES` | `60` | pages per document; more is `413 TOO_LARGE` |
| `MAX_CELLS` | `200000` | cells with content per sheet file (XLSX, ODS); more is `413 TOO_LARGE` |
| `OCR_MIN_CHARS` | `20` | a PDF page with fewer characters takes the image way |
| `SCAN_PREP` | `off` | scan preparation of the image way (photos, scans, image-only PDF pages): `off` = the image way of before; `on` = the steps the scan lab accepted (straightening, letter counters not taken for boxes, dotted and open lines read as places to write, thick lines thinned); or a comma list of `deskew`, `glyph`, `leader`, `rules`, `thick`, `scale` (page to A4 at 200 dpi) and `orient` (turning a page read upside down or sideways); the last two are not accepted and stay off in `on`. Scaling, straightening and turning a page are each a warning in the sidecar |
| `FINISH_STYLE` | `export` | `export`: `SECTION` with `TEXT_BLOCK`; `info_section` |
| `VALIDATORS` | `on` | `off` writes empty validator lists, as in the exports |
| `REQUIRED_POLICY` | `paper` | `paper`: `REQUIRED` only where the paper or the standard says so (the partner's exports carry none); `inferred`: also where our rule calls a field the substance of the request, each reported as `REQUIRED_INFERRED` in the sidecar |
| `REPEATING_STYLE` | `native` | `native`: `REPEATING_SECTION`; `flat`: one plain section |
| `STATUTORY_REPRESENTATIVE` | `true` | path for a parent, guardian or curator (D16) |
| `POA_EXEMPTION` | `false` | reason of exemption from stamp duty for a power of attorney (D17) |
| `FORM_KEY` | empty | fixed key for ids; empty: the slug of the title |
| `ID_NAMESPACE` | fixed UUID | namespace of the ids; must be a UUID |
| `UI_ENABLED`, `UI_DIR` | `true`, empty | serve the front end; folder of a build |
| `LOG_LEVEL` | `info` | logs are content-free at every level |

**Access by default.** `AUTH_MODE=auto` makes the image start with no flags, so a juror can run it at once; without a key file anyone who reaches the port can convert. Publish the port on loopback only (`-p 127.0.0.1:8080:8080`). On a shared network use [`docker-compose.yml`](../../docker-compose.yml), which mounts a key file and runs with JWT, or set `AUTH_MODE=jwt` so that a missing key stops the start instead of opening the service.

What the service cannot read is never a made-up form: a file with nothing readable answers `422 UNREADABLE`, a place it could not read is a warning in the sidecar with the page and the place.

### Optional step: a model for weak scan pages / Opcjonalny krok: model do słabych stron skanu

**EN.** Off by default: with nothing configured the service makes no outbound call and the output is byte for byte the output of the rules path. An operator can switch it on by pointing it at their own OpenAI-compatible server (for example vLLM or Ollama serving an open-weight Qwen3 model): `VISION_BASE_URL`, the key in `VISION_API_KEY_FILE` (or `VISION_API_KEY`), and optionally `VISION_MODEL`. The model writes no field: it only names the numbers of lines our OCR already read on a weak scan or photo page, and the same rules run after it. Measured on our lab set (22 November 2026): of 27 images from the task sets, at least one paper field was found in 24 without the step and in 27 with it; matched fields 172 without and 199 with, of 651; the step also adds more unverified extra fields and about 4 s per page. This is not a promise of accuracy; the state of the step (ON, OFF, FALLBACK) is shown in `/status` and in the header `X-Converter-Engine`.

**PL.** Domyślnie wyłączony: bez konfiguracji usługa nie wykonuje żadnego połączenia wychodzącego, a wynik jest bajt w bajt taki sam jak ścieżki reguł. Operator może go włączyć, wskazując własny serwer zgodny z API OpenAI (na przykład vLLM lub Ollama z modelem Qwen3 o otwartych wagach): `VISION_BASE_URL`, klucz w `VISION_API_KEY_FILE` (albo `VISION_API_KEY`) oraz opcjonalnie `VISION_MODEL`. Model nie pisze pól: wskazuje tylko numery linii, które nasz OCR już odczytał na słabej stronie skanu lub zdjęcia, a dalej działają te same reguły. Zmierzono na naszym zestawie laboratoryjnym (22 listopada 2026): z 27 obrazów z zestawów zadania co najmniej jedno pole formularza znaleziono w 24 bez kroku i w 27 z krokiem; zgodnych pól 172 bez kroku i 199 z krokiem na 651; krok dodaje też więcej niezweryfikowanych pól nadmiarowych i około 4 s na stronę. To nie jest obietnica dokładności; stan kroku (ON, OFF, FALLBACK) widać w `/status` i w nagłówku `X-Converter-Engine`.

**Key on the page / Klucz na stronie.** The page block "Model AI (opcjonalnie)" shows the key of the service as dots. Its eye button shows only the last four characters, unless the operator starts the container with `VISION_KEY_REVEAL=on` (default off): then it shows the whole key, to a caller who may convert. Use it only on your own machine (`-p 127.0.0.1:...`). The key is never baked into the image: it is given at run time (`-e VISION_API_KEY` or `VISION_API_KEY_FILE`), as the task card asks. / Blok strony „Model AI (opcjonalnie)” pokazuje klucz usługi jako kropki; przycisk podglądu pokazuje tylko 4 ostatnie znaki, chyba że operator uruchomi kontener z `VISION_KEY_REVEAL=on` (domyślnie wyłączone) — wtedy pokazuje cały klucz. Klucz nigdy nie jest w obrazie: podaje się go przy uruchomieniu.

Guard facts worth knowing: the file kind is judged by content, never by extension alone; a name is refused when longer than 250 characters or holding `; : > < / \ | ' * % $`; a `.doc` holding a DOCX package is read as DOCX (two forms of the partner's sets are named so); a legacy Word file that merely contains a zip package in a stream is still a Word file, a zip appended at its end is refused.

## API

Token in `Authorization: Bearer ...`, scope `convert`, when the service runs with JWT; in the open mode leave the header out. Errors are `application/problem+json` with a stable `code` (design section 3). In Windows PowerShell write `curl.exe`: plain `curl` there is `Invoke-WebRequest`.

```bash
curl -s http://127.0.0.1:8080/healthz
curl -s http://127.0.0.1:8080/status       # no token: name, version, engine "rules", auth mode, accepted formats, limits
curl -s -H "Authorization: Bearer $TOKEN" -F "file=@form.pdf" http://127.0.0.1:8080/v1/forms/convert -o form.json
curl -s -H "Authorization: Bearer $TOKEN" -F "file=@form.pdf" "http://127.0.0.1:8080/v1/forms/convert?report=1"   # multipart/mixed: form.json and meta.json
curl -s -H "Authorization: Bearer $TOKEN" -F "file=@form.pdf" http://127.0.0.1:8080/v1/forms/report              # the sidecar alone
curl -s -H "Authorization: Bearer $TOKEN" -F "file=@form.pdf" http://127.0.0.1:8080/v1/forms/inspect            # what the guard sees
curl -s -H "Authorization: Bearer $TOKEN" -F "file=@form.pdf" "http://127.0.0.1:8080/v1/forms/preview?dpi=150"  # page pictures and field places, read only
curl -s -H "Authorization: Bearer $TOKEN" -F "file=@a.pdf" -F "file=@b.docx" http://127.0.0.1:8080/v1/batches   # one JSON line per file; or one ZIP
curl -s -H "Authorization: Bearer $TOKEN" -F "file=@form.pdf" http://127.0.0.1:8080/v1/jobs                     # 202: the file is taken into the queue; answers {id, state, position}
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8080/v1/jobs/$ID                                     # where the job is: place in the queue, stage, finished parts
curl -s -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:8080/v1/jobs/$ID/result?report=1"                   # the answer of convert for the finished job
```

Jobs (`/v1/jobs`, wave 11) are how the page converts, and what a script should use for many files or long scans. `POST /v1/jobs` checks the file at once (the refusals of `convert`: type, size, name) and answers `202` with the job's `id`; the file then waits its turn. Never more than `CONCURRENCY` conversions run; up to 20 files (and five single-file limits of bytes) wait, each told its `position` (1 = next); beyond that the answer is `429 QUEUE_FULL` with `Retry-After`, and nothing is dropped silently. `GET /v1/jobs/{id}` answers `state` (`queued`, `running`, `done`, `error`), `stage` (`received`, `recognised`, `reading` with `step`, `page`, `pages`, then `fields`, `meaning`, `form`, `checks`, `export`; `model` when the open model is configured) and `units {done, total}`: the finished parts of 100. A part is counted only when the conversion reports the work behind it (a page rendered, a page read by OCR, a phase ended); nothing moves with the clock. `stage_s` is the time since the last report, the sign of life during one long page. `GET /v1/jobs/{id}/result` answers the same bytes as `convert` for the same file (`?report=0` for the form alone), `202` with the state while the job is not finished, or the job's problem. `DELETE /v1/jobs/{id}` gives a job up. A finished job is kept in memory for 30 minutes (the newest 60); nothing is written to disk. `GET /v1/jobs` tells how busy the queue is.

The answer of `convert` is the partner's object (`title`, `tabs`, `flow`) and nothing else. The same input gives the same `X-Form-SHA256`.

`preview` is read only and changes nothing in `convert`: for the same file it answers `{version, input_sha256, format, units: "pt", origin: "top-left", page_images, pages, places, counts}`. `pages[]` holds `n`, `w`, `h` (points) and, for a PDF, JPG or PNG, `img` (greyscale PNG in base64 with `dpi`, `width_px`, `height_px`); `places` maps every finder candidate id (`c1`, `c2`, ...) to `page`, `kind`, `box` `[x0, y0, x1, y1]` or `anchor`, `label` and, where they apply, `cells`, `group`, `options[].mark`. Every `meta.ledger.rows[].candidate` of `convert?report=1` is a key of `places`, so a form field finds its place on the paper. DOCX, DOC, XLSX, ODS and the other formats without page geometry answer `page_images: "NO_PAGE_IMAGE"`, `pages: []` and anchors. Query: `images=0` leaves the pictures out, `dpi` 50 to 200 (default 150, lowered when a page would exceed `MAX_PIXELS`). Token, guard, slots, time limit and error codes are those of `convert`; the same file and query give the same bytes.

| Status | `code` | When |
|---|---|---|
| 400 | `BAD_NAME` | forbidden or too long name |
| 401 / 403 | `TOKEN_MISSING`, `TOKEN_INVALID`, `TOKEN_EXPIRED` / `SCOPE` | token check |
| 413 | `TOO_LARGE`, `ARCHIVE_LIMIT`, ... | limits |
| 415 | `EXTENSION`, `TYPE_MISMATCH`, `DOC_READER_OFF` | not one of the eight formats, or the content is another type |
| 422 | `UNREADABLE`, `ACTIVE_CONTENT` | nothing readable; macros under `strict` |
| 429 | `BUSY` | all slots busy, or the rate limit; with `Retry-After` |
| 429 | `QUEUE_FULL` | `POST /v1/jobs` only: 20 files (or five single-file limits of bytes) already wait; with `Retry-After` |
| 500 / 504 | `GATE_FAILED` / `TIMEOUT` | the result failed our own gate and is never sent |

Not in the service: `/v1/forms/diff`, `/v1/forms/export`, `/about/*`. The proof of working without a network is the `convert` command under `--network none`; the state of the service is `GET /status`.
