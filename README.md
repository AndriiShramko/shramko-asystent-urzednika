# Forms converter: from a blank official form to e-service JSON

A REST service in Docker for the task "Cyfryzacja formularzy" (Centralny Ośrodek Informatyki, HackNation 2026). One blank official form goes in (PDF, DOC, DOCX, ODS, XLSX, JPG, JPEG, PNG, exactly the formats of the task card; `STRICT_EXTENSIONS=false` also accepts ODT, XLS, RTF, TXT and more image formats); the JSON configuration of an electronic form in the partner's structure ("Generator Formularzy e-Usług") comes out. A shared deployment guards access with a JWT token; started alone on one computer the service is open and says so in its log. Next to the form the service writes a sidecar of evidence: where every field came from, what happened to each blank it found on the paper, what was left out and what it refused to guess.

The idea in one line: **a compiler with an accountant, not a scanner with AI.** Rules and a library of the partner's standard sections build the form; the service accounts for it. As started by the commands below, no language model runs in the product and it makes no network call at run time. One optional step for weak scan pages can be pointed by the operator at their own server with an open-weight model; it is off unless configured ([`apps/converter/README.md`](apps/converter/README.md), "Optional step").

## For the jury: three commands

How it works inside: local OCR, layout analysis and rules. The commands below run without a language model, without an API key and without a GPU.

The image (the same reference in every command below):

`ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:8511a7f6b7e84cafed8f21a476ad5b25f661fb288713de237291b0cd85a6c621`

Put the blank form into a folder `forms` next to where you stand, as `forms/form.pdf`. Each command is one line: paste it whole. The image is built for `linux/amd64`; `--platform linux/amd64` lets an ARM Mac run it under emulation. Run conversions one after another: the service works on two uploads at a time and answers `429 BUSY` to more.

**1. Offline, the form to standard output.** This is the proof that nothing leaves the container: `--network none` gives the container no network at all.

bash (Linux, macOS, Git Bash; `MSYS_NO_PATHCONV=1` stops Git Bash from rewriting `/in/...` into a Windows path and does nothing elsewhere):

```bash
MSYS_NO_PATHCONV=1 docker run --rm --platform linux/amd64 --network none --read-only --cap-drop ALL -v "$PWD/forms:/in:ro" ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:8511a7f6b7e84cafed8f21a476ad5b25f661fb288713de237291b0cd85a6c621 convert /in/form.pdf > form.json
```

Windows PowerShell 5.1: its own `>` would write UTF-16 with a byte-order mark, so the redirect is left to `cmd`, which keeps the bytes as they are (UTF-8 without a BOM):

```powershell
cmd /c 'docker run --rm --platform linux/amd64 --network none --read-only --cap-drop ALL -v "%cd%\forms:/in:ro" ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:8511a7f6b7e84cafed8f21a476ad5b25f661fb288713de237291b0cd85a6c621 convert /in/form.pdf > form.json'
```

**2. Offline, the form written into a mounted folder with `--out`.** On Linux the container runs as your own user so that it may write into `out`:

```bash
mkdir -p out && docker run --rm --platform linux/amd64 --network none --read-only --cap-drop ALL --user "$(id -u):$(id -g)" -v "$PWD/forms:/in:ro" -v "$PWD/out:/out" ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:8511a7f6b7e84cafed8f21a476ad5b25f661fb288713de237291b0cd85a6c621 convert /in/form.pdf --out /out/form.json
```

macOS and Git Bash (Docker Desktop maps the owner of the folder itself, so no `--user`):

```bash
mkdir -p out && MSYS_NO_PATHCONV=1 docker run --rm --platform linux/amd64 --network none --read-only --cap-drop ALL -v "$PWD/forms:/in:ro" -v "$PWD/out:/out" ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:8511a7f6b7e84cafed8f21a476ad5b25f661fb288713de237291b0cd85a6c621 convert /in/form.pdf --out /out/form.json
```

Windows PowerShell 5.1 (the simplest choice there; the file is UTF-8 without a BOM):

```powershell
mkdir -Force out | Out-Null; docker run --rm --platform linux/amd64 --network none --read-only --cap-drop ALL -v "${PWD}/forms:/in:ro" -v "${PWD}/out:/out" ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:8511a7f6b7e84cafed8f21a476ad5b25f661fb288713de237291b0cd85a6c621 convert /in/form.pdf --out /out/form.json
```

If `out` cannot be written, `convert` says so in one line and exits with code 4.

**A whole folder of new forms**, one after another, every result into `out/<name>.json`:

```bash
mkdir -p out && for f in forms/*; do n="${f##*/}"; MSYS_NO_PATHCONV=1 docker run --rm --platform linux/amd64 --network none --read-only --cap-drop ALL -v "$PWD/forms:/in:ro" ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:8511a7f6b7e84cafed8f21a476ad5b25f661fb288713de237291b0cd85a6c621 convert "/in/$n" > "out/${n%.*}.json"; done
```

```powershell
mkdir -Force out | Out-Null; Get-ChildItem forms -File | ForEach-Object { docker run --rm --platform linux/amd64 --network none --read-only --cap-drop ALL -v "${PWD}/forms:/in:ro" -v "${PWD}/out:/out" ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:8511a7f6b7e84cafed8f21a476ad5b25f661fb288713de237291b0cd85a6c621 convert "/in/$($_.Name)" --out "/out/$($_.BaseName).json" }
```

**3. REST and the review page, published on this computer only (loopback).** Start the service in one window (stop it with Ctrl+C):

```bash
docker run --rm --platform linux/amd64 -p 127.0.0.1:8080:8080 --read-only --cap-drop ALL ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:8511a7f6b7e84cafed8f21a476ad5b25f661fb288713de237291b0cd85a6c621
```

The same line works in PowerShell. Then, in a second window, from the folder that holds `form.pdf`:

```bash
curl -F "file=@form.pdf" http://127.0.0.1:8080/v1/forms/convert -o form.json
```

```powershell
curl.exe -F "file=@form.pdf" http://127.0.0.1:8080/v1/forms/convert -o form.json
```

(In PowerShell `curl` is another command, `Invoke-WebRequest`; write `curl.exe`.) The review page: <http://127.0.0.1:8080/ui/>. The state of the service (name, version, `engine: "rules"`, the token mode, the accepted formats, the limits): <http://127.0.0.1:8080/status>.

Started without settings and without a key file, the service is open and writes a warning about it into its log; that is why the example publishes on `127.0.0.1` only. For a shared network use [`docker-compose.yml`](docker-compose.yml), which runs with a JWT token. A REST server under `--network none` cannot be reached from the host, so the offline proof is command 1, not the REST one. All settings: [`apps/converter/README.md`](apps/converter/README.md).

- **Reads:** PDF, DOC, DOCX, ODS, XLSX, JPG, JPEG, PNG (images and scans through local OCR). What it could not read is a warning with the page and the place, never a made-up field.
- Links: state of the build [`docs/03-plan/STATUS.md`](docs/03-plan/STATUS.md) · [`apps/converter/README.md`](apps/converter/README.md) · [`docs/02-architecture/converter-design.md`](docs/02-architecture/converter-design.md) · pre-event disclosure [`NOTICE`](NOTICE).

## Where the jury sees each criterion / Gdzie widać kryteria oceny

| Criterion of the task card | Where to see it |
|---|---|
| Minimum scope: REST, the eight formats, the partner's structure, thematic pages | `POST /v1/forms/convert` answers exactly `title`, `tabs`, `flow`; [`results/`](results/) holds the forms of the judged sets; `GET /status` lists the eight formats |
| I. Dictionaries and initial data | in the JSON, fields with `dictionaryName` (for example `Kraje` with the default value Polska); on the page `/ui/`, view "Widok dla jury", block "Słowniki" |
| II. A proposed new dictionary | page block "Słowniki" → "Proponowany nowy słownik" (set 09: sports disciplines from the paper); the same in the report `meta.json` |
| III. Dependencies and conditions | in the JSON, `states` with JSONata conditions (`SHOW`); on the page, the e-form preview: a choice opens the dependent section |
| IV. Upload and preview page | `/ui/`: the clerk view (the original next to the e-form, remarks as cards on the document), the jury view, "Gdzie na papierze", trial fill and print on the original blank, many files at once with progress by stage |
| V. Field validation and UX | validators in the JSON (`validation`: PESEL, NIP, REGON, postal code, e-mail, identity card number, ePUAP and e-Doręczenia addresses: the partner's own list); "Sprawdź poprawność" on the page; many files: `POST /v1/batches` or `POST /v1/jobs` |

The film (at most 3 minutes) and the presentation (PDF) are linked in the HackTribe submission.

## Configuration and REST API (short) / Konfiguracja i REST API

Full tables: [`apps/converter/README.md`](apps/converter/README.md), sections "Configuration" and "API". Everything is set by environment variables at run time; secrets come as files and are never in the image.

| Endpoint | What it does |
|---|---|
| `GET /healthz`, `GET /status` | liveness; name, version, engine, token mode, accepted formats, limits |
| `POST /v1/forms/convert` (multipart `file`) | the partner's JSON (`title`, `tabs`, `flow`) and nothing else; `?report=1` adds the report `meta.json` |
| `POST /v1/forms/report`, `POST /v1/forms/preview` | the report alone; page pictures and field places (read only) |
| `POST /v1/batches`, `POST /v1/jobs`, `GET /v1/jobs/{id}` | many files in one call; a queue with progress by stage |
| Errors | `application/problem+json` with a stable `code`: 400 `BAD_NAME`, 401/403 token, 413 `TOO_LARGE`, 415 `EXTENSION`/`TYPE_MISMATCH`, 422 `UNREADABLE`, 429 `BUSY`/`QUEUE_FULL`, 504 `TIMEOUT` |

| Variable | Default | Meaning |
|---|---|---|
| `AUTH_MODE`, `JWT_SECRET_FILE`, `JWT_PUBLIC_KEY_FILE`, `JWT_JWKS_FILE` | `auto`, none | JWT when a key file is given; open with a log warning otherwise (publish on `127.0.0.1`) |
| `MAX_UPLOAD_BYTES`, `MAX_PAGES`, `JOB_TIMEOUT_S`, `CONCURRENCY` | 20 MiB, 60, 600, 2 | limits |
| `STRICT_EXTENSIONS` | `true` | exactly the eight formats of the card; `false` also ODT, XLS, RTF, TXT and more image formats |
| `SCAN_PREP` | `off` | extra scan preparation for photos (operator's switch) |
| `VISION_BASE_URL`, `VISION_API_KEY_FILE`, `VISION_MODEL`, `VISION_PAGE_CONFIG`, `VISION_KEY_REVEAL` | none, none, Qwen3, `on`, `off` | the optional model step for weak scan pages, off unless the operator points it at their own server; no key is in the image |

## Koszt i wymagania / Cost and requirements

**Wymagania (PL).** Procesor, bez GPU. W czasie pracy usługa nie korzysta z sieci (polecenie 1 powyżej działa z `--network none`). Obraz: 361 551 088 bajtów po rozpakowaniu (`docker image inspect`, build `sha256:8511a7f6…`, linux/amd64; rozmiaru skompresowanego nie mierzono). Ustawienia domyślne: 2 równoległe zadania, 600 s na zadanie, 20 MiB i 60 stron na plik (`apps/converter/app/config.py`). Wywołań zewnętrznych nie ma, więc nie ma opłat za wywołanie; zużycia CPU w sekundach na formularz nie mierzono (poniżej tylko czas zegarowy).

**Requirements (EN).** CPU only, no GPU. No network at run time (command 1 above runs with `--network none`). Image: 361,551,088 bytes uncompressed (`docker image inspect`, build `sha256:8511a7f6…`, linux/amd64; the compressed size was not measured). Defaults: 2 parallel jobs, 600 s per job, 20 MiB and 60 pages per file (`apps/converter/app/config.py`). No external service is called, so there is no per-call fee; CPU-seconds per form were not measured (below is wall-clock time only).

Czas jednej konwersji przez REST, 108 plików (54 z zestawów jurorskich i 54 z archiwum), obraz `061fce4b…`, kontener `--cpus 2 --memory 4g`, pliki jeden po drugim, 22.11.2026. Komputer był współdzielony z innym zadaniem obciążającym procesor w 100 %, więc sekundy są zawyżone; liczą się rzędy wielkości. / Seconds for one conversion over REST, 108 files (54 from the judged sets, 54 from the city archive), image `061fce4b…`, container `--cpus 2 --memory 4g`, files one after another, 22 Nov 2026. The laptop was shared with another job using a CPU at 100 %, so the seconds are inflated; read the order of magnitude.

| Format | Files | Median s | Max s |
|---|---|---|---|
| DOC | 16 | 0.9 | 1.6 |
| DOCX | 17 | 0.9 | 3.1 |
| ODS | 7 | 1.2 | 5.4 |
| XLSX | 7 | 1.4 | 5.4 |
| PDF | 32 | 1.9 | 131.5 |
| JPG | 8 | 12.2 | 58.9 |
| JPEG | 7 | 15.6 | 65.0 |
| PNG | 7 | 16.7 | 54.2 |

The PDF maximum is one 16-page scan (OCR); one 130-page PDF was refused with 413 (the limit is 60 pages) and is in the 32. 107 of 108 answered 200, none 5xx, no timeout in that run. A separate run of 280 synthetic scans and photos (image `061fce4b…`, `--cpus 2`, shared laptop): median 4.7 s, maximum 17.1 s; 27 images of the judged sets: median 7.7 s, maximum 52.0 s. / Maksimum dla PDF to jeden 16-stronicowy skan (OCR); jeden PDF o 130 stronach odrzucono kodem 413 (limit to 60 stron) i jest wśród 32. 107 z 108 odpowiedzi to 200, bez błędów 5xx i bez przekroczenia czasu w tym przebiegu. Osobny przebieg 280 syntetycznych skanów i zdjęć: mediana 4,7 s, maksimum 17,1 s; 27 obrazów z zestawów jurorskich: mediana 7,7 s, maksimum 52,0 s.

Pamięć / Memory: peak 577 MiB (limit 2 GiB) over that run (280 synthetic scans and photos, 27 set images, 3 blank controls); one earlier check reports 55 to 190 MiB from idle to one OCR job (`docker stats`), one OCR job keeping one core at about 100 %. Szczyt 577 MiB w tym przebiegu (280 skanów i zdjęć, 27 obrazów, 3 puste kontrole); wcześniejszy pomiar: od 55 do 190 MiB od stanu spoczynku do jednego zadania OCR.

Build from source / Budowa ze źródeł (from the repository root, context `.`): `docker build -f apps/converter/Dockerfile -t converter:core .`

---

## Pre-event material (a parked vision, not built in this task)

Everything below was prepared before the event (tag `pre-event`, see [`NOTICE`](NOTICE)) and describes another product.

**Open brief and reference design for an AI assistant for Polish public offices (urząd): it helps clerks analyse access-to-public-information requests (wnioski o udostępnienie informacji publicznej, UDIP) and draft answers, and it pre-fills official forms from data a visitor enters once.** Prepared for HackNation 2026 (21–22 November 2026, Bydgoszcz), challenge "Inteligentny asystent urzędnika" by Miasto Bydgoszcz.

Sites and pitch decks: <https://formularze.flyreelstudio.eu> (forms: from a paper form to an online service; the primary track) and <https://urzad.flyreelstudio.eu> (public-information requests) · Polski: [README.pl.md](README.pl.md) · Русский (для владельца проекта): [README.ru.md](README.ru.md) · For AI agents: [START_HERE.md](START_HERE.md), [AGENTS.md](AGENTS.md), [AGENT_SETUP.md](AGENT_SETUP.md), [llms.txt](llms.txt) · Known traps: [docs/warnings.md](docs/warnings.md)

> **Status of this section: pre-event brief (tag `pre-event`).** What follows is research, requirements, a scope decision, a build plan and an orchestration playbook written before the hackathon, for another product. The forms converter described above is not part of it: its code is `apps/converter` (the service) and `apps/review-web` (the review page), written during the event, in commits after the tag. Live state: [`docs/03-plan/STATUS.md`](docs/03-plan/STATUS.md).

## Questions this answers

- How can AI help a Polish city office answer an access-to-public-information request within the 14-day deadline, and what may it never decide by itself?
- Which outcomes of a UDIP request are administrative decisions and which are ordinary letters? What must each contain?
- May an office still accept an anonymous UDIP request sent by e-mail? (Short answer: the case law changed in 2024–2026; see the research.)
- Where is a machine-readable list of all service cards and application forms of Urząd Miasta Bydgoszczy with direct download links?
- How do I fill an official Polish PDF form by program so that the printout is identical to the approved template?
- Can a resident share their data with an office by scanning a QR code, and what does mObywatel offer for that today?
- How does one lead Claude Code agent run several sub-agents on one repository through git worktrees without them overwriting each other, and without burning its own context?
- What does a HackNation jury score, what must be submitted and when?

## What is inside

| Path | What it is |
|---|---|
| [`docs/00-brief/requirements.md`](docs/00-brief/requirements.md) | The owner's requirements R1–R32 |
| [`docs/01-product/scope-decision.md`](docs/01-product/scope-decision.md) | What to build for the jury and why; the wider platform; "one database for many institutions?" |
| [`docs/01-product/gaps-and-additions.md`](docs/01-product/gaps-and-additions.md) | 38 things the original idea did not cover |
| [`docs/02-architecture/`](docs/02-architecture/) | Design decisions and trust zones, API contract, security and privacy with a threat table, the AI layer (guardrails, model choice, quality, integration, deployment) |
| [`docs/03-plan/`](docs/03-plan/) | Roadmap with event clock times, 18 work packages with acceptance lists, ownership table, live status |
| [`docs/04-orchestration/`](docs/04-orchestration/), [`.claude/`](.claude/) | Lead-agent playbook, sub-agent brief template, git workflow for parallel agents, resume after a usage limit, publishing; agent definitions, project settings and a wave workflow |
| [`docs/05-hackathon/`](docs/05-hackathon/) | Onsite intake procedure, pitch storyboard, demo script, the "what is real" table, a plain guide to the event for the owner (Russian) |
| [`site/`](site/) | The public site <https://urzad.flyreelstudio.eu>: landing page and the animated pitch deck with a presenter window |
| [`research/`](research/) | Ten research reports with sources and labels: hackathon rules and judging, UDIP law and the clerk's decision tree, forms catalogue and form anatomy, mObywatel and once-only, data protection and the AI regulation, technology, landscape, multi-agent orchestration, lessons from a 2022 production prototype, pitching |
| [`data/`](data/) | Catalogue of 275 service cards and 710 form files of Urząd Miasta Bydgoszczy (links and metadata), request taxonomy, Polish response skeletons, canonical profile schema, a measured form descriptor |
| [`prompts/`](prompts/) | Runtime instructions (Polish) for the product's AI steps |
| [`tools/`](tools/) | The polite crawler that rebuilds the catalogue, a slow downloader of form files, a link checker |
| [`docs/06-audit/`](docs/06-audit/) | Point-by-point check of an earlier research draft (Russian) |

## The idea in five lines

1. **Module A, the hackathon answer:** a case desk for public-information requests. The assistant reads the request, says what it legally is, starts the 14-day clock, finds earlier answers and published information, drafts the reply or the notice with a checked legal basis, masks personal data, and waits for a clerk's approval.
2. **Module B, the next process on the same core:** the visitor types their data once on their own phone (or the clerk reads the document), the clerk picks a life situation, the forms come out filled on the approved templates, a checker flags mistakes.
3. **Security is part of the task sentence** ("inteligentny i bezpieczny"): data stays under the office's control, a human approves every output, every step is logged, a local Polish model is a first-class option.
4. **Centralise forms, not people:** an open registry of form descriptions can serve every office; personal data stays with the person and with the office that handles the case.
5. **Built by AI agents under one lead**, through git, with small contexts and resumable steps.

## Quick start for an AI agent

```bash
git clone https://github.com/AndriiShramko/shramko-asystent-urzednika
```

Open the folder in Claude Code and say: `Read START_HERE.md and act as the lead agent.` Everything else is in that file.

## Honest limits

- **Weakest inputs: photos and old binary DOC.** An independent check (a judge that listed the places to fill from the page image without seeing our output; 21 November evening, before the night's fixes) found about half of the places on old DOC and photos (DOC 50 %, photos 55 %) against 81 % on PDF of the task sets. The night's work added text boxes of old DOC (set 08 DOC: 8 to 34 fields from the paper).
- **A new form can lose lines.** On a synthetic blank made for a strict review (22 November), some labelled underlined lines (PESEL, date of birth) and two attachments were not picked up, and the report did not warn about them. The output is a draft for the clerk to confirm, not a finished e-service.
- Lists of attachments without lines, and conditions of the kind "fill in if ...", are kept in about half of the cases.
- No phone number validator: the partner's own list of validators has none.
- The optional model step for weak scan pages is off by default and no key is in the image; we make no claim that it improves the result (on our lab set it found more fields and also more extra ones).
- No real personal data is used anywhere; tests and demos use fictitious persons. Research files are dated and labelled; it is not legal advice.

## Disclosure for HackNation

This brief (research, specification, catalogue, crawler) was prepared before the event and is cited as an external resource, as the event rules require. Product code is written during the event.

## Author & working together

<img src="docs/assets/andrii-shramko.webp" alt="Andrii Shramko" width="120" height="120" align="left">

**Andrii Shramko** — I build tools with AI agents. In 2022 I ran a volunteer service in a refugee help centre in Opole that pre-filled Polish benefit applications for people arriving from Ukraine: visitors typed their data once on their phones, volunteers printed ready forms. This project brings that experience to city offices and adds an assistant for the clerk.

**Open to interesting people and ready to help teams build ambitious projects** — pilots with public offices, partnerships, licensing or funding. Get in touch:

- 📅 Book a call: <https://calendar.app.google/Ff729HqGk4RpzPNDA>
- 💼 LinkedIn: <https://www.linkedin.com/in/andrii-shramko/>
- ✉️ Email: zmei116@gmail.com
- 🐙 GitHub: <https://github.com/AndriiShramko>

<br clear="left">

## License

Code and tools: MIT. Documentation and research: CC BY 4.0. See [`LICENSE`](LICENSE), [`NOTICE`](NOTICE), [`CITATION.cff`](CITATION.cff). Security policy: [`SECURITY.md`](SECURITY.md).
