# Converter service

A blank official form (PDF, DOC, DOCX, ODS, XLSX, JPG, JPEG, PNG) in, the JSON configuration of an electronic form out. This folder is the service shell (work package WP-F1): configuration, guard, token check, HTTP endpoints, command line, image. The reading pipeline is behind one function, `app/pipeline.py: run(data, filename, settings)`; until the reader packages land it returns a fixed valid form and one warning `PIPELINE_STUB` in the sidecar. Design: [`docs/02-architecture/converter-design.md`](../../docs/02-architecture/converter-design.md).

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

For local work the check of the bearer can be switched off with `AUTH_MODE=off` (logged as a warning at start).

## Run in a container

The image is built by CI (`.github/workflows`, WP-F20) and published to `ghcr.io/andriishramko/shramko-asystent-urzednika`. To build it yourself (needs Docker; the build context is the repository root):

```bash
docker build -f apps/converter/Dockerfile -t converter:core .                 # core: Alpine, the default
docker build -f apps/converter/Dockerfile --target plus -t converter:plus .   # plus: Debian slim, second OCR engine
docker compose up --build                                                     # needs secrets/jwt_secret, see docker-compose.yml
```

Both images run as a dedicated user (uid 10001), expose port 8080, hold no secret, pin their bases by digest and install Python packages with `--require-hashes --only-binary=:all:`. Conversion without a network, as CI does it:

```bash
docker run --rm --network none --read-only --cap-drop ALL --user 10001 \
  -v "$PWD/forms:/in:ro" -v "$PWD/out:/out" converter:core convert /in/form.pdf --out /out/form.json
```

The front end (`apps/review-web`) is built in a Node stage if that folder exists, and served at `/ui/`; without it the image is built and the API works the same.

## Configuration

Everything comes from the environment; the service refuses to start on an inconsistent set and lists every problem. Keys come as files. Full list with meanings: design section 4. The ones that matter first:

| Variable | Default | Meaning |
|---|---|---|
| `AUTH_MODE` | `jwt` | `off` only for local work |
| `JWT_ALG` | `HS256` | `HS256`, `HS384`, `HS512`, `RS256`, `ES256`, `EdDSA`; never read from the token, `none` is refused |
| `JWT_SECRET_FILE` / `JWT_PUBLIC_KEY_FILE` / `JWT_JWKS_FILE` | none | the key, by file (no key fetching) |
| `JWT_ISSUER`, `JWT_AUDIENCE` | none | required equal when set |
| `JWT_REQUIRED_CLAIMS`, `JWT_LEEWAY_S` | `exp`, `30` | `exp` cannot be removed; leeway at most 120 |
| `MAX_UPLOAD_BYTES` | `20971520` | largest upload |
| `CONCURRENCY` | `2` | uploads processed at once; more get `429 BUSY` at once |
| `RATE_LIMIT_PER_MIN` | `60` | per token subject; over it `429 BUSY` with `Retry-After` |
| `STRICT_EXTENSIONS` | `false` | `false` accepts `.jpe` as JPEG by content; `true` accepts exactly the eight extensions |
| `DOC_READER` | `native` | `off` refuses binary Word with `415 DOC_READER_OFF` |
| `ACTIVE_CONTENT` | `warn` | `strict` refuses files with macros |
| `MAX_PAGES` | `60` | pages per document; more is `413 TOO_LARGE` |
| `MAX_CELLS` | `200000` | cells with content per sheet file (XLSX, ODS); more is `413 TOO_LARGE` |
| `OCR_MIN_CHARS` | `20` | a PDF page with fewer characters takes the image way |
| `FINISH_STYLE` | `export` | `export`: `SECTION` with `TEXT_BLOCK`; `info_section` |
| `VALIDATORS` | `on` | `off` writes empty validator lists, as in the exports |
| `REPEATING_STYLE` | `native` | `native`: `REPEATING_SECTION`; `flat`: one plain section |
| `STATUTORY_REPRESENTATIVE` | `true` | path for a parent, guardian or curator (D16) |
| `POA_EXEMPTION` | `false` | reason of exemption from stamp duty for a power of attorney (D17) |
| `FORM_KEY` | empty | fixed key for ids; empty: the slug of the title |
| `ID_NAMESPACE` | fixed UUID | namespace of the ids; must be a UUID |

Until the understanding step is wired in (WP-F4; the finder WP-F3 is merged) the form holds the title of the file and the standard sections; the sidecar carries the warning `BRIEF_NOT_READ`. Formats without a reader yet (JPEG, PNG; images and OCR are WP-F2c) answer `422 UNREADABLE`, never a made-up form.
| `UI_ENABLED`, `UI_DIR` | `true`, empty | serve the front end; folder of a build |
| `LOG_LEVEL` | `info` | logs are content-free at every level |

Guard facts worth knowing: the file kind is judged by content, never by extension alone; a name is refused when longer than 250 characters or holding `; : > < / \ | ' * % $`; a `.doc` holding a DOCX package is read as DOCX (two forms of the partner's sets are named so); a legacy Word file that merely contains a zip package in a stream is still a Word file, a zip appended at its end is refused.

## API

Token in `Authorization: Bearer ...`, scope `convert`. Errors are `application/problem+json` with a stable `code` (design section 3).

```bash
curl -s http://127.0.0.1:8080/healthz
curl -s -H "Authorization: Bearer $TOKEN" -F "file=@form.pdf" http://127.0.0.1:8080/v1/forms/convert -o form.json
curl -s -H "Authorization: Bearer $TOKEN" -F "file=@form.pdf" "http://127.0.0.1:8080/v1/forms/convert?report=1"   # multipart/mixed: form.json and meta.json
curl -s -H "Authorization: Bearer $TOKEN" -F "file=@form.pdf" http://127.0.0.1:8080/v1/forms/report              # the sidecar alone
curl -s -H "Authorization: Bearer $TOKEN" -F "file=@form.pdf" http://127.0.0.1:8080/v1/forms/inspect            # what the guard sees
curl -s -H "Authorization: Bearer $TOKEN" -F "file=@a.pdf" -F "file=@b.docx" http://127.0.0.1:8080/v1/batches   # one JSON line per file; or one ZIP
```

The answer of `convert` is the partner's object (`title`, `tabs`, `flow`) and nothing else. The same input gives the same `X-Form-SHA256`.

| Status | `code` | When |
|---|---|---|
| 400 | `BAD_NAME` | forbidden or too long name |
| 401 / 403 | `TOKEN_MISSING`, `TOKEN_INVALID`, `TOKEN_EXPIRED` / `SCOPE` | token check |
| 413 | `TOO_LARGE`, `ARCHIVE_LIMIT`, ... | limits |
| 415 | `EXTENSION`, `TYPE_MISMATCH`, `DOC_READER_OFF` | not one of the eight formats, or the content is another type |
| 422 | `UNREADABLE`, `ACTIVE_CONTENT` | nothing readable; macros under `strict` |
| 429 | `BUSY` | all slots busy, or the rate limit; with `Retry-After` |
| 500 / 504 | `GATE_FAILED` / `TIMEOUT` | the result failed our own gate and is never sent |

Not yet in the shell (later packages): `/v1/forms/diff`, `/v1/forms/export`, `/v1/selftest`, `/about/*`, the worker airlock.
