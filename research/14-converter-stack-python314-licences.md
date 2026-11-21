## TL;DR for builders

- **Alpine works for the core, not for everything.** `python:3.14-alpine` is 17 MB compressed against 41 MB for `python:3.14-slim` (Docker Hub, opened 2026-11-21). Pillow, pypdfium2, numpy, scipy, lxml, cryptography, pydantic-core, uvloop, httptools, rapidfuzz and tesserocr all ship cp314 musllinux wheels. **onnxruntime, opencv-python-headless, pyclipper, morfeusz2, onnxruntime-genai, torch and paddlepaddle do not.** That kills RapidOCR on Alpine via pip.
- **Verdict: two build targets from one Dockerfile.** `core` on Alpine (rules, PDF/DOCX/XLSX/ODS readers, Tesseract from apk) is the default and honours "Alpine preferred". `plus` on `python:3.14-slim-trixie` adds RapidOCR (second OCR engine), Morfeusz and optional LibreOffice. Evidence in section 3.
- **Tesseract 5.5.2 and `pol` data are in the Alpine repo** (`tesseract-ocr`, `tesseract-ocr-data-pol`, both Apache-2.0). Engine code is Apache-2.0. `tessdata_fast` `pol` is 4.8 MB, `tessdata_best` `pol` is 12.0 MB.
- **PDF stack: pypdfium2 (render, char boxes) + pdfminer.six / pdfplumber (lines, rects, tables) + pypdf (AcroForm).** All permissive. PyMuPDF is AGPL-3.0 (or paid Artifex): excluded, confirmed from its `COPYING`.
- **DOC (binary Word) is the one licence question.** LibreOffice is MPL-2.0 ("ask first" in our rule). Running it as an unmodified, separately executed program does not put our code under MPL (inference, not legal advice). Make it a build switch, off in `core`. Fallback: Apache Tika/POI (Apache-2.0, needs Java 17+).
- **Write our own ODS and OOXML readers on lxml.** odfpy is 2020 and its metadata says Apache-2.0 *and* GPL/LGPL; ezodf is 2015. An ODS file is a zip with `content.xml`. This also gives checkbox and content-control support that the libraries hide.
- **Surprise: spaCy's Polish models are GPL-3.0** (model metadata and HF card). Excluded. Use Morfeusz2 (BSD-2-Clause incl. inflection data) in `plus`, simplemma (MIT) in `core`.
- **Surya: the brief says GPL; today the code is Apache-2.0 but the weights are modified OpenRAIL-M with a funding/revenue cap and the layout weights are CC-BY-NC-SA-4.0.** Not open source in the task's sense; also its PyPI metadata now depends on the `openai` client. Excluded.
- **JSONata: `jsonata-python` 0.7.2 (Apache-2.0) claims 100% of the language; reference JS `jsonata` 2.2.2 (MIT) for the viewer.** Use the Python one to *evaluate every generated condition* against synthetic data before returning JSON.
- **Local LLM stays optional and off.** Apache-2.0 open weights exist: Bielik 1.5B / 4.5B / 11B v3.0, PLLuM-12B-2412, Qwen3-4B; MIT: Phi-4-mini. Gemma is a custom licence with a remote-restriction clause: not open source. Run via the Alpine `llama.cpp` package (MIT); `llama-cpp-python` has no wheel at all.
- **Best cross-checks are free:** Tesseract word confidence, Tesseract-vs-RapidOCR agreement (rapidfuzz), agreement of the eight formats of the sample form (scipy assignment), `jsonschema` (draft 2020-12) on the output, JSONata evaluation, own PESEL/NIP/REGON check digits.
- **Method note.** I used PyPI JSON file lists instead of `pip download` for every package: the wheel filenames are the same evidence and cost nothing. I did not install anything. Pitfalls marked "inference" are not tested by running code.

Source conventions (all opened 2026-11-21): **[PyPI]** = `https://pypi.org/pypi/<name>/json`; **[HF]** = `https://huggingface.co/<repo>` card metadata; **[APK]** = `https://dl-cdn.alpinelinux.org/alpine/v3.24/{main,community}/x86_64/APKINDEX.tar.gz` (computed by me); **[DH]** = `https://hub.docker.com/v2/repositories/library/python/tags`. "cp314 many/musl" means a wheel installable on CPython 3.14 (cp314, abi3 with cp3x ≤ 14, or pure `py3-none-any`) exists for that libc, x86_64.

## 1. Project facts used (from the repo)

- Card: Python 3.14+ or Java 21+ preferred; no copyleft (GPL, AGPL named); no external API/SaaS/MCP; local-weight models are not forbidden (only models "available only through an API"); Alpine "named" as preferred light base; pinned versions; non-root user; JWT parameters configurable; MIME must match extension (`docs/05-hackathon/intake/coi-task-card.md`, read 2026-11-21).
- Our schema contract is JSON Schema **draft 2020-12** (`contracts/coi/form.schema.json`, `$schema` line). This matters for the validator choice.
- Reference exports spell the key `repeatingSectionGrid` in 16/16 and 18/18 grids; no field uses `REQUIRED` (`reference-json-forensics.txt`, lines 12-15, 113-116).

## 2. Recommended stack

Versions and dates from [PyPI] unless stated. "Wheel" columns: x86_64.

| Job | Primary | Fallback | Licence (SPDX) | Latest, date | cp314 many / musl | Size effect and pitfalls |
|---|---|---|---|---|---|---|
| PDF render + text + char boxes | **pypdfium2** | pdfplumber render (uses pypdfium2) | BSD-3-Clause AND Apache-2.0 (+ bundled PDFium notices) | 5.15.2, 2026-11-09 | yes / yes (3.9 / 5.1 MB wheel) | No Python deps. Ship notices of bundled third-party code. |
| PDF vector lines, rects, tables | **pdfplumber** on **pdfminer.six** | pdfminer.six alone | MIT / MIT | 0.11.11 (uploaded 2026-11-21, today), 20260107 | pure / pure | Pure Python, slow on big pages. pdfplumber 0.11.11 is a release from the day of the defence: pin the previous release if it misbehaves (unverified which). pdfminer.six pulls cryptography. |
| PDF AcroForm fields | **pypdf** | pdfminer.six + own parse | BSD-3-Clause | 7.1.1, 2026-11-18 | pure | 0.4 MB. Read `/Fields`, `/FT`, `/Ff` flags, `/Opt`. |
| PDF excluded | PyMuPDF | - | AGPL-3.0 or commercial (PyPI: "Dual Licensed - GNU AFFERO GPL 3.0 or Artifex"; repo `COPYING` is the AGPL text) | 2.1 | many only | **Excluded.** Confirmed. |
| DOCX | **python-docx** + own lxml for `w:sdt` content controls, `FORMCHECKBOX` legacy fields | docx2python | MIT / MIT | 1.2.0 (2025-06-16); 3.7.2 (2026-10-28) | pure | python-docx ignores checkbox content controls and many headers: parse the XML ourselves. docx2python is better for footnotes/headers/text of nested tables. |
| XLSX | **openpyxl** | own lxml on `sheet*.xml` | MIT | 3.1.5, **2024-06-28** | pure | Old release, still the standard; needs `et-xmlfile`. Open with `read_only=True` and a size cap; install `defusedxml` so it hardens parsing. Not tested on 3.14 by me (unverified). |
| ODS | **own reader: zip + lxml on `content.xml`** | pyexcel-ods3 (BSD, 0.6.1, 2022) | BSD-3-Clause (lxml) | lxml 6.1.3 | yes / yes | odfpy 1.4.1 (2020-01-18): classifiers list Apache + GPL + LGPL; its README says "GPL v2 or later **or** Apache v2" (raw GitHub README, 2026-11-21). Usable under Apache, but unmaintained and no wheel: avoid. ezodf 0.3.2 (MIT, 2015) abandoned. |
| DOC (binary) | **LibreOffice headless `soffice --convert-to docx`** then DOCX path | Apache Tika 4.2.0 server (POI) | MPL-2.0 / Apache-2.0 | LO 25.8.7.3 in Alpine 3.24 [APK]; Tika 4.2.0, 2026-10-28 (tika.apache.org, "requires Java 17") | Alpine apk: yes | See section 4. `olefile` 0.47 (BSD, 2023-12-01) only reads the OLE container, not the Word text. antiword 0.37 (GPL-2.0-only [APK]) and catdoc (GPL): **excluded**. unoserver 3.7 (MIT, 2026-06-10) keeps one LO process warm: 25x faster per file, but needs LO's own python; optional. |
| OCR engine 1 (CPU, Polish) | **Tesseract 5.5.2 + `pol`** via apk, driven by **pytesseract** (subprocess, TSV output) | tesserocr | Apache-2.0 / Apache-2.0 / pytesseract Apache-2.0 / tesserocr MIT | 5.5.2 [APK]; pytesseract 0.3.13 (2024-08-16); tesserocr 2.13.0 (2026-11-12) | tesserocr: yes / yes | `tessdata_fast` licence: "All data in the repository are licensed under the Apache-2.0 License" (github.com/tesseract-ocr/tessdata_fast). `pol` 4.77 MB fast, 11.98 MB best (HTTP Content-Length, raw.githubusercontent.com, 2026-11-21). apk closure 56 MB installed incl. data (my computation, inference). tesserocr wheels are 5-7 MB: they seem to bundle libtesseract (unverified); either way pytesseract is the simpler, safer path. |
| OCR engine 2 (agreement, layout of text lines) | **RapidOCR 3.10.0 on onnxruntime 1.32.0** with PP-OCRv5 **latin** recogniser | none on Alpine | Apache-2.0 / MIT / weights Apache-2.0 | 3.10.0 (2026-10-08); onnxruntime 1.32.0 (2026-11-13) | onnxruntime: yes / **no**; opencv-headless 5.1.0.95: yes / **no**; pyclipper 1.4.0: yes / **no** | `plus` image only. Wheels: onnxruntime 27 MB, opencv 62 MB (compressed). PaddleOCR docs list Polish under `latin_PP-OCRv5_mobile_rec`, 84.7% on their Latin benchmark, no Polish-only score (paddleocr.ai multi-language page via web search, 2026-11-21). RapidOCR's own README did not state languages in PyPI text (unverified for Polish on its model zoo): test on a Polish form first. |
| OCR engines not chosen | PaddleOCR 3.7.0 (Apache-2.0): its runtime `paddlepaddle` 3.3.1 has **no cp314 wheel** (largest file cp312). docTR 1.1.0 (Apache-2.0) and EasyOCR 1.7.2 (Apache-2.0): both need `torch` (no musllinux wheel; manylinux 526 MB with CUDA packages). Docling 2.151.1 (MIT): see below. | | | | | PaddleOCR weights can run through RapidOCR in ONNX: same models, no Paddle. |
| Layout/vision models | **none by default** | Docling layout "heron" (Apache-2.0, 42.9 M params, [HF]) | MIT code; model weights Apache-2.0 / CDLA-permissive-2.0 | docling 2.151.1 (2026-11-19); docling-parse 7.27.0 many only, no musl | many / **no** | granite-docling-258M: Apache-2.0, 257.5 M params, **English only** (Japanese, Arabic, Chinese "experimental"; Polish not listed) [HF]. SmolDocling-256M-preview: CDLA-permissive-2.0, English [HF]. Both wrong for Polish forms. Weights are downloaded from HF at first run: we would have to bake them at build time. Treat Docling as optional, not core. |
| Surya | excluded | - | code Apache-2.0 (README + PyPI 0.24.0); weights "modified AI Pubs Open Rail-M" with free use only below USD 5M funding/revenue (README); `surya_layout` weights CC-BY-NC-SA-4.0 [HF] | 0.24.0, 2026-11-13 | - | **Excluded**: weights are not open source; the brief's "GPL" label is out of date. PyPI dependency list now includes `openai`: possible hosted-LLM path, a red flag for C-TECH-NOEXT (inference). |
| Line, box, checkbox detection on scans | **numpy + Pillow + scipy.ndimage** (own run-length and connected-component code) | opencv-python-headless (Apache-2.0) in `plus`; scikit-image 0.26.0 | MIT-CMU (Pillow 13.0.0), BSD (numpy, scipy: unverified SPDX here), Apache-2.0 | Pillow wheels 7 MB; numpy 15-17 MB; scipy 34-37 MB; opencv 62 MB | Pillow, numpy, scipy, scikit-image: yes / yes | OpenCV is not available on Alpine via pip. Born-digital PDFs need no raster detection (pdfplumber gives rects and lines). For scans: threshold, horizontal and vertical run-lengths, then small square components = checkboxes. About 150 lines. scikit-image adds 14 MB and gains little. |
| MIME sniffing | **own signature + container check (stdlib `zipfile`, `olefile`)** cross-checked by **puremagic** | python-magic + libmagic | MIT; MIT; BSD-2-Clause (libmagic 5.47 [APK]) | puremagic 2.3.0 (2026-11-16, py>=3.12); python-magic 0.4.27 (2022-06-07); filetype 1.2.0 (2022-11-02) | pure | docx, xlsx, ods are all zip: a generic sniffer says "zip". Distinguish by `[Content_Types].xml` and `word/` or `xl/` entries, and for ODS by the first stored entry `mimetype` text. `.doc` = OLE magic `D0CF11E0` plus a `WordDocument` stream (olefile). python-magic needs the C library (`libmagic` 10 MB installed on Alpine). filetype is old and has no ODS rule (unverified). |
| XML safety | **defusedxml** + lxml parser flags `resolve_entities=False, no_network=True, huge_tree=False` | - | PSF-2.0 | 0.7.1, **2021-03-08** | pure | Old but stable; PSF is permissive. Add zip-bomb limits (entries, ratio, total size) ourselves. |
| JWT | **PyJWT** | joserfc | MIT / BSD-3-Clause | 2.15.1 (2026-09-28); 1.8.0 (2026-11-03, py>=3.11) | pure; cryptography 50.0.2 yes / yes | HS256 needs nothing else; RS/ES needs `cryptography`. Pitfalls: pass `algorithms=[...]` explicitly, never accept `none`, require `exp`, configurable `iss`, `aud`, `leeway`. JWKS from a file path or a URL (URL is an integration parameter, not a service dependency). joserfc handles JWK sets natively; Authlib 1.9.10 (BSD-3-Clause) is a whole OAuth framework: too big. |
| JSON Schema | **jsonschema** (+ `referencing`) | - | MIT | 4.26.0, 2026-01-07 | pure (rpds-py wheel: unverified for musl) | fastjsonschema 2.22.3 (BSD-3-Clause) is faster but, as far as I recall, supports drafts 04/06/07 only: **unverified**, and our contract is 2020-12. |
| JSONata evaluate | **jsonata-python** | JS `jsonata` via the viewer only | Apache-2.0 / MIT | 0.7.2 (2026-11-13); npm `jsonata` 2.2.2 (2026-07-16) | pure | PyPI README: port of the reference implementation, "supports 100% of the language features", no dependencies. The older `jsonata` 0.2.5 (2023, BSD, has C parts) is a different, stale package: do not install it by mistake. |
| Web | **FastAPI** + **uvicorn** + **python-multipart** + **pydantic v2** | Starlette alone | MIT / BSD-3-Clause / Apache-2.0 / MIT | 0.165.0 (2026-11-18); 0.54.0; 0.0.34; 2.14.4 | pydantic-core: yes / yes; uvloop, httptools: yes / yes | python-multipart 0.0.34 requires py>=3.11. Set `--limit-concurrency`, body size limit at both uvicorn/proxy and our check. Keep `--no-server-header`. |
| Polish lemmas, light | **simplemma** | - | MIT | 2.0.0, 2026-08-12 | pure | Polish data coverage not verified by me (unverified). |
| Polish morphology, full | **Morfeusz2 + SGJP inflection data** (`plus` only) | none | BSD-2-Clause (program and the inflection data; the full SGJP dictionary is *not* BSD) | 1.99.15, 2026-06-01 | many x86_64 only (abi3, 9 MB); **no musl, no arm64** | morfeusz.sgjp.pl/doc/license (2026-11-21). The BSD grant covers the inflected-forms data needed for analysis. Keep the copyright notice in the image. Whether the PyPI wheel embeds the dictionary: unverified. |
| Polish tools excluded | **spaCy `pl_core_news_*`: GPL-3.0** (HF card and model meta `pl_core_news_md-3.8.0`, source Explosion, 2026-11-21). stanza 1.15.1 code Apache-2.0, `stanfordnlp/stanza-pl` Apache-2.0 [HF] but needs torch. | | | | | spaCy code is MIT but the models are the copyleft part. |
| Spelling suggestions | **symspellpy** + frequency list we build ourselves | - | MIT | 6.10.2, 2026-11-07 | pure | The Polish frequency list licence is the open point: public lists derive from subtitles or web crawls with unclear terms (unverified). Build the list from our own dictionaries (Kraje, TERYT names, field labels of the sample forms). |
| Validators | **own code** for PESEL, NIP, REGON, KRS format, postal code; **schwifty** for IBAN; **phonenumbers**; **email-validator** | - | -; MIT; Apache-2.0; Unlicense | schwifty 2026.11.3; phonenumbers 9.0.44 (2026-11-20); email-validator 2.4.0 | pure | **python-stdnum 2.2 is LGPL** ([PyPI] classifier "LGPLv2+"): excluded; we implement the public check-digit rules ourselves. phonenumbers adds a big metadata package (inference: tens of MB installed). email-validator: set `check_deliverability=False` (no DNS). |
| Open LLM runtime (optional) | **`llama-server` from Alpine `llama.cpp` 0.0.9564 (MIT)** | ONNX Runtime GenAI 0.20.0 (MIT, manylinux only) | MIT | [APK] | llama-cpp-python 0.3.37: **no wheel at all** (sdist only: needs a compiler); onnxruntime-genai: many only | Alpine package is 5 MB (14 MB installed). Talk to it on localhost inside the container. Off by default. |

## 3. Alpine versus slim: verdict with evidence

**Base image sizes [DH]:** `python:3.14.10-alpine` 17 MB, `python:3.14.10-slim-trixie` 41 MB (compressed, amd64, updated 2026-11-08/12). Alpine 3.24 is what `3.14-alpine` points to; Alpine ships Python 3.14.10 itself [APK].

**Wheel matrix on musllinux (cp314-compatible, x86_64) [PyPI]:**

| Present | Missing |
|---|---|
| pillow 13.0.0, numpy 2.5.5, scipy 1.18.1, scikit-image 0.26.0, shapely 2.2.0, lxml 6.1.3, pydantic-core 2.50.5, cryptography 50.0.2, cffi, orjson, uvloop, httptools, watchfiles, pyyaml, rapidfuzz, pypdfium2, tesserocr, pikepdf, tokenizers, spacy | **onnxruntime 1.32.0, opencv-python-headless 5.1.0.95, pyclipper 1.4.0, morfeusz2, onnxruntime-genai, torch, python-bidi (present, LGPL), PyMuPDF (excluded), docling-parse, onnx** |

Pure-Python packages (pypdf, pdfminer.six, pdfplumber, python-docx, openpyxl, jsonschema, PyJWT, fastapi, jsonata-python, symspellpy and so on) install anywhere.

**What Alpine's own repository can give (Alpine 3.24, x86_64) [APK], closure sizes are my computation from the `D:` dependency fields, so inference:**

| apk package | Version | Licence | Installed incl. dependencies |
|---|---|---|---|
| tesseract-ocr + tesseract-ocr-data-pol | 5.5.2 | Apache-2.0 | about 56 MB |
| libreoffice-writer + libreoffice-calc | 25.8.7.3 | MPL-2.0 | about 960 MB (285 packages) |
| openjdk21-jre-headless (for Tika) | 21.0.13 | GPL-2.0 with Classpath exception | about 197 MB |
| py3-opencv | 4.12.0 | Apache-2.0 | about 550 MB (pulls GUI and video libraries) |
| py3-onnxruntime | 1.24.4 | MIT | about 183 MB |
| llama.cpp | 0.0.9564 | MIT | about 14 MB |
| libmagic | 5.47 | BSD-2-Clause | 10 MB |

Caveat: apk `py3-*` packages live under `/usr/lib/python3.14` for the *system* Python; the official `python:3.14-alpine` image keeps its own Python in `/usr/local`. Mixing them needs `PYTHONPATH` tricks and is fragile: do not rely on it. (Apt-based `libmagic` on slim: standard Debian package, not checked.)

**Verdict.**
1. **`core` = `python:3.14-alpine` (pin the digest).** Rules, readers, Tesseract (apk), pypdfium2, numpy/Pillow detection, JWT, validation. No ONNX, no OpenCV. Smallest image and satisfies "Alpine preferred" with evidence.
2. **`plus` = `python:3.14-slim-trixie`.** Adds RapidOCR (+ onnxruntime + opencv-headless + pyclipper), Morfeusz2, optional Docling, optional LibreOffice. Larger by roughly 150 MB of wheels (onnxruntime 27 + opencv 62 + shapely + models) plus LibreOffice if enabled.
3. If a mentor says "Alpine is a requirement" (question T13): keep `core` as the submission, show `plus` as an option. Nothing in the minimum needs `plus`.
4. LibreOffice on Alpine installs fine via apk, so the Alpine-only submission can still convert DOC if the mentors allow MPL. It makes the image about 1 GB installed. Prefer a *second container* (`converter-doc`) in `docker-compose` rather than bloating the main image: the main one stays small and the licence boundary becomes a process boundary.
5. musl pitfalls to test (inference): slower `malloc` under heavy Pillow/numpy load; locale and font differences when LibreOffice renders (install `font-dejavu`, Polish glyphs); `tesseract` child processes need `OMP_THREAD_LIMIT=1` to avoid oversubscription.

## 4. LibreOffice and the MPL: what it means here

- Licence: MPL-2.0 per Alpine package metadata [APK] (LibreOffice also bundles third-party components under other licences: check the NOTICE inside the package before saying "only MPL").
- MPL-2.0 is *file-level* copyleft: changes to MPL files must be shared under MPL; it does not reach separate files or separate programs. Our service only *executes* `soffice` as a child process on temp files and reads the output. No linking, no modification. Inference, not legal advice; the mentors or the partner's legal team own this decision (question T10).
- If we **distribute the image**, we distribute LibreOffice binaries: keep the licence texts and tell where the source is (upstream, Alpine aports). That is a notice duty, not a "share our code" duty.
- Our task rule says MPL is "ask first". So: build argument `WITH_LIBREOFFICE=0` by default; `.doc` then answers HTTP 415 with a clear message, or falls back to Tika if the Java variant is chosen.
- Apache Tika 4.2.0 (2026-10-28) is Apache-2.0 and requires Java 17+ (tika.apache.org news, 2026-11-21); the card allows Java 21. It extracts text and structure from `.doc` via POI but does not give us layout or checkbox glyphs as faithfully as a LibreOffice conversion to DOCX (inference). Needs a JVM: 197 MB installed on Alpine [APK].
- **Hybrid that costs little:** for `.doc`, first try LibreOffice if present; if not, Tika if present; else a clear "unsupported in this build" error. The report lists which path was used.

## 5. Open models, optional and switched off

| Model | Licence | Size | Polish | Notes |
|---|---|---|---|---|
| Bielik-11B-v3.0-Instruct | Apache-2.0 [HF] | 11.17 B | native Polish, multilingual | 2.6 M downloads; **gated** on HF (accept conditions to download); technical report arXiv 2601.11579 |
| Bielik-4.5B-v3.0-Instruct | Apache-2.0 [HF] | 4.76 B | Polish | gated; updated 2026-01-28 |
| Bielik-1.5B-v3.0-Instruct | Apache-2.0 [HF] | 1.60 B | Polish | gated; the only one that is realistic on a laptop CPU (inference) |
| PLLuM-12B-instruct-2412 | Apache-2.0 [HF] | 12.25 B (Mistral base) | Polish | CYFRAGOVPL, the government line: a credibility point for COI |
| Llama-PLLuM-8B-instruct-2412 | **llama3.1 licence** [HF] | 8.03 B | Polish | custom licence, not OSI: do not pick for this task |
| Qwen3-4B | Apache-2.0 [HF] | 4.02 B | multilingual | Polish quality not verified |
| Phi-4-mini-instruct | MIT [HF] | 3.84 B | Polish listed in the card tags | 128k context claimed elsewhere, not checked |
| Gemma 3 (4B-it) | licence `gemma` [HF] | 4.30 B | yes | **Custom terms, not an OSI licence.** The Terms say Google may restrict use "remotely or otherwise" if it believes the terms are breached; a Prohibited Use Policy is incorporated by reference; redistributors must flow the restrictions down; hosted access counts as distribution (ai.google.dev/gemma/terms via search, 2026-11-21). One search snippet says Gemma 4 has its own licence: not checked. A request for `ai.google.dev/gemma/terms` redirected to `gemma.ai`: an unverified host, I ignored it. Answer for the mentors: weights are available locally, but the terms are not open source, so avoid. |

- Runtime: `llama-server` from Alpine `llama.cpp` 0.0.9564 (MIT) on localhost inside the container; GGUF weights baked in at build time (the HF page for Bielik-11B shows 24 quantised derivatives; which exact GGUF files exist and their licence status: unverified). ONNX Runtime GenAI 0.20.0 has a manylinux wheel only.
- RAM in practice (inference): 1.5B at 4-bit about 1 GB, 4.5B about 3 GB, 11B about 7 GB. The owner's laptop has 16 GB RAM and Intel graphics by default (memory note): 1.5B or 4.5B only.
- Uses: wording of labels, naming sections, guessing the concept of a field. Every answer is validated by rules and the JSONata evaluator. Never needed for the minimum.

## 6. Risks and the early test for each

| Risk | Early test (minutes) |
|---|---|
| A needed wheel is missing on Alpine/cp314 | CI step 1: `docker build --target core .` with `pip install --only-binary=:all:`; fails loudly on any sdist. Run `pip download --only-binary=:all: --python-version 3.14 --platform musllinux_1_2_x86_64 --no-deps` for each pinned name. |
| RapidOCR Polish quality unknown | Render 5 Polish forms at 200 and 300 dpi, compare against Tesseract `pol` on diacritics (ą ć ę ł ń ó ś ź ż); count words below confidence 60. Decide the vote rule from numbers. |
| LibreOffice conversion changes layout or hangs | `timeout 60`, separate user profile dir per call (`-env:UserInstallation=file:///tmp/lo-<uuid>`), kill the process group; run the sample `.doc` through it and diff against the DOCX of the same form. |
| MPL not accepted by the partner | Build switch; `.doc` returns 415 in `core`; show Tika path as proof of an Apache alternative. |
| Surprise on defence day: new file in an odd format variant | Fuzz with the eight sample formats re-saved by Word, LibreOffice and Google Docs; a catch-all that returns a minimal valid JSON plus a report instead of HTTP 500. |
| Image runs as root or is writable | Read-only root filesystem, `USER 10001`, tmpfs `/tmp`, `cap_drop: ALL`, one port. Test with `docker run --read-only`. |
| Zip bomb or XML entity bomb in docx/xlsx/ods | Test files with 1 GB of zeros, nested entities; assert 413/422 inside 2 s and memory under the cap. |
| New pdfplumber 0.11.11 published today | Run our PDF test set on 0.11.11 and the previous one; pin the one that passes. |
| Gated Bielik weights need an HF click-through | Owner accepts conditions once before the defence and bakes weights into a build cache; document it. |
| JWT misuse (algorithm confusion) | Unit tests: `alg=none`, HS256 token against an RS256 key, expired, wrong `aud`; all rejected. |

## 7. Library-backed checks

Every row is an independent signal about the recognised content. Each can set a `confidence` or a warning in an optional report (not in the form JSON unless the mentors allow extra keys: T3, T11).

| Check | Library | Licence | How |
|---|---|---|---|
| OCR word and line confidence | Tesseract TSV `conf` via pytesseract | Apache-2.0 | Flag lines with mean conf below a threshold; fields built from them get `needsReview`. |
| Two OCR engines agree | RapidOCR vs Tesseract; rapidfuzz `fuzz.ratio` / `Levenshtein` | Apache-2.0; MIT | Normalised edit distance per aligned line; disagreement above 15% = low confidence. Plus image only. |
| Eight formats of one form agree | rapidfuzz + `scipy.optimize.linear_sum_assignment` | MIT; BSD | The sample comes as eight formats of the same form (`docs/02-architecture/coi-json-format.md`). Convert each, match fields by label similarity, report the match rate. This is both a regression test and a defence demo. |
| Dictionary look-ups | symspellpy (+ own frequency list), Morfeusz2 lemma check in `plus`, simplemma in `core` | MIT; BSD-2-Clause; MIT | Fix OCR typos in labels; map "Obywatelstwo" to the `Kraje` dictionary by lemma. |
| Schema validation of our output | jsonschema 4.26 with draft 2020-12 | MIT | Validate against `contracts/coi/form.schema.json` before returning. |
| Parse and evaluate generated JSONata | jsonata-python 0.7.2 | Apache-2.0 | For each `states[].query`, evaluate on synthetic answers (each option chosen in turn); assert it returns a boolean and that SHOW changes for the intended option. Catches a wrong `techName` in a path. |
| JSONata in the viewer | JS `jsonata` 2.2.2 | MIT | Bundled locally in the front end (no CDN): same results as the Python check. |
| Check digits | own PESEL, NIP, REGON, KRS rules; schwifty for IBAN mod-97 | -; MIT | Used both for field validators and to scan an uploaded filled form for personal data (B20). python-stdnum is LGPL: excluded. |
| Phone and e-mail format | phonenumbers; email-validator (`check_deliverability=False`) | Apache-2.0; Unlicense | Field validation presets. |
| Readability index of Polish text | **own** Gunning-FOG-style (Pisarek "Indeks Fog-PL": words with more than 4 syllables; Polish syllables = vowels, with "i" before vowels handled) | ours | textstat 0.7.13 (MIT) exists but I could not confirm Polish support, and I believe it depends on pyphen (GPL/LGPL/MPL tri-licence, classifiers on [PyPI]): unverified, avoid. |
| Accessibility of the generated form | own JSON-level rules: every field has label and `tooltipMessage`, titles under 255 chars, no empty options, logical `questionOrder`, no colour-only meaning | ours | For the HTML viewer: axe-core is MPL-2.0 (axe-selenium-python 3.0.0 is MPL-2.0 on [PyPI]): "ask first", dev-time only. Lighthouse (licence not checked here) is also dev-time. |
| Structural sanity | stdlib | PSF | Unique `techName` per section, unique UUIDs, flow links reference existing pages, no section inside a section (rules in `coi-json-format.md` section 2). |
| PDF vector vs raster geometry | pdfplumber rects vs own raster detection | MIT; ours | On scanned versions of a born-digital form, compare found boxes with the vector ones: gives a measured recall of the detector. |
| File type truth | puremagic + own container checks | MIT; ours | Content must match extension (C-TECH-MIME). |

## Questions of questions-v1.md answered here

| id | our answer | confidence | evidence |
|---|---|---|---|
| T1 | Write `repeatingSectionGrid` | high | Reference exports use it in 16 of 16 and 18 of 18 grids (`reference-json-forensics.txt` lines 14, 115); the schema file spells it differently, so mention both in the README. |
| T4 | Set `REQUIRED` only when the paper says the field is mandatory; the validator list stays supported | low | Zero fields use it in the two reference exports (same file); nothing in my research changes that. |
| T8 | Yes in principle: only models "available only through an API" are forbidden; local weights are fine. We keep it off by default and say so. | high on the card text, medium on the mentors' reading | Task card C-TECH-NOEXT (`coi-task-card.md`, 2026-11-21); Apache-2.0 Polish models exist (section 5). |
| T10 | Make LibreOffice a build option, off by default; Tika/POI (Apache-2.0) as the permissive path; ask the mentors only to confirm MPL is acceptable. | medium | Section 4; MPL-2.0 for LibreOffice [APK]; Tika 4.2.0 (tika.apache.org). |
| T13 | A preference ("Preferred", "Alpine named"), not a hard requirement, by the card's wording; we still deliver Alpine for the core and slim for the extras. | medium | `coi-task-card.md` table row C-TECH-LANG and C-TECH-DOCKER; section 3 wheel evidence. |
| T14 | Support all three: HS256 secret from the environment, RS256/ES256 PEM public key, JWKS from a file or URL; everything configurable (issuer, audience, algorithms, leeway). | medium | C-TECH-CONF requires configurable JWT parameters; PyJWT and joserfc cover all three (section 2). |
| T15 | Yes, scans too: JPG, JPEG, PNG are listed inputs. | high | C-TECH-FMT in the card. |
| B19 | Yes, by construction: no call leaves the container; models and OCR data are baked in at build time. | high | C-TECH-NOEXT; Tesseract, RapidOCR and LLM weights all run locally (sections 2, 5). |
| B14 | Offer IBAN (schwifty), phone (phonenumbers), PESEL/NIP/REGON/KRS (own), date range and regex; KRS, land register and plot number checks are ours to write. | medium | Section 7; python-stdnum LGPL forces our own implementation. |
| B20 | Process in memory, never write personal data to disk or logs, warn when PESEL-like values are found. | medium | C-TECH-TEMP; check digits give a reliable detector (section 7). |

## Only the partner can answer

- **Whether MPL-2.0 is acceptable for LibreOffice in a container (T10).** The card says "copyleft (their examples: GPL, AGPL)" and does not mention MPL; only the partner's legal and architecture people can say how they read it.
- **The exact form of "Alpine preferred" at the defence (T13).** The card text is public, the scoring practice is not.
- **Which hardware runs the defence (T9) and whether GPU is available.** Decides whether the optional 4.5B or 11B model is demo-able.
- **Whether extra keys or an envelope with a report are accepted (T3, T11).** Only their importer knows.
- **How the JSON is scored (T2) and whether scans are included in the hidden defence files (T15).** Internal grading plan.
- **The full list of dictionary names (T5) beyond "Kraje" and "TERYT_DOWODOWY".** Not in the public materials.
- **Whether the partner's internal image scanners reject a given base image or licence.** Internal policy.

## Proposals beyond what the partner asked

| proposal | why it matters to them | effort S/M/L | libraries and licences | risk |
|---|---|---|---|---|
| Cross-format consistency check: convert all eight formats of one form and report the match rate | Proves the converter is stable across formats; a unique demo; becomes the regression test | M | rapidfuzz (MIT), scipy (BSD) | Low: needs the eight sample files only |
| Two-image build: `core` Alpine (~small, Tesseract) and `plus` slim (RapidOCR, Morfeusz) | Concrete answer to "deployment potential including cost" with measured sizes | M | as in section 3; all permissive | Medium: Alpine wheel gaps must stay under CI watch |
| Own ODS and OOXML readers on lxml (checkboxes, content controls, merged cells) | Fewer dependencies, no odfpy licence ambiguity, better form fidelity | S | lxml (BSD-3-Clause), defusedxml (PSF-2.0) | Low |
| JSONata self-check: every generated condition evaluated before output | Their forms depend on JSONata; wrong paths are silent bugs in their generator | M | jsonata-python (Apache-2.0), jsonata JS (MIT) | Low |
| Confidence report next to the JSON (OCR confidence, engine agreement, unresolved fields) | Official can review only what is uncertain (B7, B8); honest about scans | M | Tesseract, RapidOCR (Apache-2.0), rapidfuzz (MIT) | Medium: depends on T3/T11 for where it lives |
| Licence and SBOM gate in CI (inventory of all wheels, fail on GPL/AGPL/LGPL) plus a `NOTICE` file | Government IT cares about supply chain; shows the copyleft rule is enforced, not just claimed | S | pip-licenses, CycloneDX tools, Trivy or Grype (licences not checked here: unverified) | Low |
| Hardened container profile: digest-pinned base, non-root, read-only rootfs, tmpfs `/tmp`, dropped capabilities, healthcheck | Matches every line of C-TECH-DOCKER and is easy to demonstrate | S | none | Low |
| Optional Polish helper model (Bielik-1.5B or 4.5B-v3.0, Apache-2.0) behind `llama-server`, switched off | Wording of labels and sections; Polish-made, government-linked ecosystem (PLLuM is CYFRAGOVPL) | L | llama.cpp (MIT), Bielik (Apache-2.0) | High: laptop RAM, gated download, quality unmeasured |
| Zip-bomb and XML-entity hardening with tests | Uploads from outside; shows security thinking beyond the minimum | S | stdlib zipfile, defusedxml | Low |
| Morfeusz-based label normalisation to match dictionaries by lemma | Links free-text labels to dictionaries (C-OPT-1/2) better than string match | M | Morfeusz2 + SGJP data (BSD-2-Clause) | Medium: no musl or arm64 wheel, `plus` only |
