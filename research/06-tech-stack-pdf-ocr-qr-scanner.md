# R6 - Engineering options: PDF forms and printing, ID capture, QR handoff, hardware reader, stack, LLM layer, risks

Access date for all sources: 2026-11-21. Status tags: VERIFIED = I opened the primary source and read the statement; SECONDARY = reliable secondary source or a search summary only; UNVERIFIED = general engineering knowledge, not checked in this session (check before relying on it). Polish terms are kept verbatim with an English gloss.

Method note: the research budget was about 45 tool calls. The Adaptive Recognition (ARH) Osmond user manual (668 pages, PDF) was downloaded and read locally, so the hardware section is much firmer than the rest. Library versions are NOT pinned here; pin them from PyPI/npm at scaffold time.

## TL;DR for builders

- Keep the lead's stack: Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy 2, React + TypeScript + Vite, SQLite default and PostgreSQL profile. Reason: the document, NLP and PII ecosystems are in Python; share types through the generated OpenAPI TypeScript client, not through a TS monorepo (section 5).
- PDF forms: detect first (AcroForm, XFA, flat). pypdf (BSD) and pdf-lib (MIT, VERIFIED) fill and flatten AcroForms; flat PDFs need a coordinate overlay merged onto the original page. Avoid PyMuPDF in the core: AGPL-3.0 or paid Artifex licence (VERIFIED). Base-14 fonts lack most Polish letters, so always embed a TTF (DejaVu Sans, Noto Sans or Liberation).
- Print by sending the finished PDF to the printer from a local helper or the PDF viewer at 100% scale ("Actual size"); never print HTML when exact geometry matters. Chrome has a `SilentPrintingEnabled` policy only from Chrome 144 on Windows and it prints with default options (SECONDARY).
- Browser OCR of the MRZ is feasible (Tesseract.js is Apache-2.0, SECONDARY) but no accuracy benchmark was found. Make check digits (ICAO 9303 weights 7-3-1) the accuracy engine: correct O/0, I/1, B/8 confusions until all check digits pass, vote across frames, and always keep manual entry. Write your own 40-line parser.
- The MRZ never contains: address, parents' names, place of birth. Since 2015 the Polish dowód osobisty carries no address at all (SECONDARY). MRZ transliterates Polish letters (Ł becomes L), so the visual zone must be confirmed by the clerk.
- Web NFC cannot read e-dowód or e-passport chips: NDEF only, no ISO-DEP (VERIFIED, MDN and Chrome docs). Chip reading needs a native Android app or the desktop Osmond R (which exposes PC/SC for RFID on Windows 10/11, VERIFIED in the manual).
- QR handoff: ECDH (P-256 for universal support, X25519 if feature-detected; VERIFIED that WebCrypto lists X25519) + HKDF + AES-GCM, public key in the URL fragment, one-shot upload, TTL 10 minutes, short authentication string (SAS) shown on both screens. HPKE is not in WebCrypto (not mentioned in MDN; UNVERIFIED beyond that). The phone page must be served from a host the office trusts, otherwise a malicious relay can ship modified JavaScript.
- Hardware reader: a localhost bridge is the right design (C28 mostly confirmed). Zero-SDK fallback that works tonight: the vendor Full Page Reader saves JSON/XML/ZIP into a folder (VERIFIED); the bridge watches that folder.
- Licence trap: ARH licences carry an expiry date that controls the update period; every software version issued before that date keeps running, newer ones may not (VERIFIED). Keep the installed 2.1.10.x package; do not upgrade to 2.2.0.x for the demo.
- Mock tonight: the reader (canned JSON), real printing (export PDF + one real print on the day), chip/NFC, OIDC (local accounts), cloud LLM (recorded answers). Do for real: PDF overlay accuracy, check-digit parser, hash-chained audit log, pseudonymisation canary test, deadline clock.

## 1. Pixel-exact PDF filling and printing

### 1.1 Detect what kind of PDF it is

| Kind | How to detect (pypdf) | Consequence |
|---|---|---|
| AcroForm | `/Root /AcroForm` exists and `reader.get_fields()` returns fields | Fill fields, generate appearance streams, optionally flatten |
| XFA (dynamic or static) | `/AcroForm /XFA` key present | XFA overrides page content in viewers; pypdf docs state this explicitly (VERIFIED, pypdf forms page). Strip the `/XFA` key and use the AcroForm fallback if one exists; otherwise treat as flat |
| Hybrid (AcroForm + XFA) | both | Remove `/XFA`, then fill AcroForm; verify visually in two viewers |
| Flat | no fields | Overlay at measured coordinates (1.3) |
| Scanned image | no text layer | Overlay on the raster; coordinates measured in rendered pixels at known DPI |

Detection script (UNVERIFIED as written, trivial to test): open with `pypdf.PdfReader`, read `reader.trailer["/Root"]`, check `"/AcroForm"` and `"/XFA"`, count `reader.get_fields()`, check `page.extract_text()` empty (scan). Store the verdict per template in `data/forms/<form>/template.json`.

### 1.2 Libraries and licences

| Library | Language | Licence | Use here | Notes |
|---|---|---|---|---|
| pypdf | Python | BSD-3-Clause (UNVERIFIED in this session) | AcroForm fill, flatten, page merge for overlays | Docs: `update_page_form_field_values(page, {...}, auto_regenerate=False)`; `flatten=True` then `remove_annotations(subtypes="/Widget")`; `add_page()` does not copy field structure, use `append()` (all VERIFIED, pypdf forms page). Local environment has pypdf 6.12.2 |
| pdf-lib | TypeScript | MIT (VERIFIED, GitHub README) | Browser or Node fill + flatten + overlay | `form.flatten()` supported; custom fonts need `@pdf-lib/fontkit`; README warns subsetting "does not work for all fonts"; Releases page empty, 279 open issues: treat as stable but unmaintained |
| PyMuPDF / MuPDF | Python / C | AGPL-3.0 or commercial from Artifex (VERIFIED, Artifex licensing page) | Do not use in the core | AGPL applies to software offered as a network service; fine only for throwaway developer scripts that are not shipped |
| pdfcpu | Go | Apache-2.0 (VERIFIED, GitHub) | CLI for validate, optimise, merge, stamp, form commands | Its form documentation and UTF-8 font handling were not verifiable from the README |
| ReportLab | Python | BSD for the open-source edition (UNVERIFIED) | Generate the overlay page (text at x, y) | Register TTF with `pdfmetrics.registerFont(TTFont(...))` |
| PDFKit | Node | MIT (UNVERIFIED) | Generates new PDFs only, cannot open an existing template | Overlay must still be merged by pypdf, pdf-lib or qpdf |
| pdfme | TypeScript | MIT (UNVERIFIED) | Template designer plus generator | Re-typesets, so it violates "print exactly as the official template"; skip |
| qpdf | C++ CLI | Apache-2.0 (UNVERIFIED) | `--overlay`, `--underlay`, linearise, repair, remove XFA | Excellent for byte-safe overlay merge in a pipeline |
| pdfplumber | Python | MIT (UNVERIFIED) | Measure text and box coordinates of a flat template | Replaces PyMuPDF for coordinate extraction |
| pypdfium2 | Python | BSD/Apache (UNVERIFIED) | Render PDF to PNG for visual regression | Pure wheels, no system poppler needed |

Recommendation: pypdf for AcroForm fill and merge; ReportLab for overlay generation; qpdf as the merge fallback; pypdfium2 for rendering; pdf-lib only if filling must happen in the browser.

### 1.3 Polish diacritics, fonts, comb fields, flattening

- The 14 standard PDF fonts use WinAnsi/Standard encodings; of the Polish letters only "o with acute" exists there, so ą ć ę ł ń ś ź ż (and capitals) cannot be shown without an embedded font (UNVERIFIED, standard encoding knowledge). Embed a TTF with full Latin Extended-A: DejaVu Sans, Noto Sans, Liberation Sans (open licences, UNVERIFIED here). Embed as a subset to keep size small.
- AcroForm text fields: set the field's `/DA` font to an embedded font resource in `/DR`, or let pypdf generate the appearance with the form's default font and then check glyphs. Do not rely on viewer regeneration (`NeedAppearances true` triggers "save changes?" dialogs, VERIFIED pypdf docs). For guaranteed output flatten after fill.
- Comb fields (one character per box): the PDF has the comb flag in `/Ff` (bit 25) plus `/MaxLen`; whether the generated appearance spaces characters evenly depends on the library (UNVERIFIED for pypdf and pdf-lib). Safe rule for the hackathon: for comb fields and for one-box-per-character flat layouts, draw each character yourself at `x0 + i*pitch` in an overlay; the pitch and `x0` come from the widget `/Rect` and `MaxLen`.
- Flatten only the final print copy; keep the editable filled PDF (fields intact) for the clerk to correct.
- Checkboxes and radio buttons: set on-state names exactly as in `/AP /N` keys; `get_fields()` returns the radio parent while `page.annotations` has the children (VERIFIED pypdf docs).
- PDF/A: PDF/A forbids features such as XFA and encryption and requires embedded fonts (UNVERIFIED). Flatten first, embed all fonts, then convert/validate with Ghostscript or veraPDF (UNVERIFIED). Do not promise PDF/A for filled official forms in the demo; offer it for letters generated from DOCX.
- Overlay tooling: for each flat template store a `fields.yaml` (field id, page, x, y in points from bottom-left, font size, max width, comb pitch). Provide a debug mode that draws coloured boxes over the template.

### 1.4 DOC, DOCX, RTF to PDF fidelity (LibreOffice headless)

Command shape: `soffice --headless --convert-to pdf --outdir out in.docx` (UNVERIFIED, standard). Known pitfalls, all UNVERIFIED in this session but widely reproduced:
1. Missing fonts cause silent substitution and reflow (Calibri, Times New Roman, Arial). Ship metric-compatible fonts (Carlito, Liberation) in the container and use them in templates.
2. One profile directory means one concurrent instance; use `-env:UserInstallation=file:///tmp/lo_<worker>` per worker or a single queue.
3. Cold start of several seconds: keep a warm listener (unoserver) or batch conversions.
4. Complex Word features (text boxes, tracked changes, field codes, some tables) may differ from Word; keep letter templates simple, test the golden file with the visual regression in 1.6.
5. RTF and legacy DOC are less faithful than DOCX; convert them once to DOCX at import.
6. Do not run it on untrusted macro-enabled input without disabling macros.
Letters: build DOCX from a template with marked slots (python-docx or docxtpl; licences UNVERIFIED), export PDF via LibreOffice in the container, and let the clerk also download the DOCX.

### 1.5 Printing from a web app on Windows office PCs

| Option | Exactness | Silent | Verdict |
|---|---|---|---|
| Browser `window.print()` on HTML | Poor: margins and scaling vary per browser and driver | No | Only for drafts |
| Open the PDF in the browser or viewer and print at "Actual size/100%" | Good if scaling is "none" | No | Acceptable manual path; document the exact dialog settings |
| Chrome `SilentPrintingEnabled` policy | Prints with default options | Yes, Chrome 144+ on Windows (SECONDARY, Samsung browser-policy page) | Useful for counter PCs, but options (duplex, scale) are not controllable; verify before relying on it |
| `--kiosk --kiosk-printing` flag | Historic behaviour, reports of dialogs still appearing (SECONDARY, Chromium bug threads) | Mostly | Do not depend on it |
| Local print helper (the same localhost bridge as the document reader) that sends the PDF with explicit settings through a PDF-capable CLI or Windows print API | Best | Yes | Recommended for production; set duplex, paper size, copies, no scaling per job (tooling choice UNVERIFIED; SumatraPDF CLI supports `-print-to` and `-print-settings` but verify its GPL terms) |
| IPP (Internet Printing Protocol) direct to the printer or a CUPS server | Good | Yes | Needs printer support and network access; mention as option (UNVERIFIED) |

Per-person copies and duplex: generate one PDF per person per form ("print job" = person x form x copies); the job ticket carries `duplex: long-edge|none` and `copies`. If an official template is a front/back sheet, keep the page order of the template and insert blank pages rather than altering it. Print the signature page(s) separately when the law requires an original signature on a particular page.

### 1.6 Automated visual regression

- Render with pypdfium2 (or pdftoppm) at 150 DPI; compare to a golden PNG with a pixel diff (pixelmatch, odiff or Playwright's `toHaveScreenshot`; all UNVERIFIED here). Fail above a tolerance of e.g. 0.1% differing pixels.
- Template-integrity test: render the blank template and the filled output; mask the declared field rectangles; the remaining pixels must be identical. This proves "exactly as the official template".
- Text-fit test: for each field compute string width with the embedded font and fail if it exceeds the box (long Polish surnames and street names).
- Golden persons: a synthetic set containing the longest surname, all diacritics (ą ć ę ł ń ó ś ź ż), empty optional fields, two-person forms.

## 2. ID capture in the browser

### 2.1 Which Polish documents carry an MRZ

| Document | MRZ | Format | Source / status |
|---|---|---|---|
| Dowód osobisty (ID card) wzór 2015 and wzór 2019 (e-dowód) | Yes, on the back | TD1, 3 x 30 characters | The official gov.pl authenticity-check leaflet tells staff to check that personal data and document number are repeated in "Pole MRZ" for the 2015, 2013 and 2001 patterns (VERIFIED text extraction of the gov.pl PDF); TD1 format is the ICAO standard for ID cards (SECONDARY) |
| Paszport | Yes | TD3, 2 x 44 | ICAO 9303 (UNVERIFIED for Poland specifically, standard) |
| Karta pobytu (residence card) | Yes | TD1 (UNVERIFIED) | Not opened |
| mDowód (in the mObywatel app) | No MRZ | digital; verified by the app/QR flow (UNVERIFIED) | Not a physical card: nothing for the camera or reader; clerk uses the app's verification screen |
| Prawo jazdy (driving licence) | No MRZ | EU card with numbered fields 1-12 (UNVERIFIED) | Not suitable as identity proof for most office flows; capture by manual entry |
| Older dowód (pre-2015 books and cards) | Older patterns carry a machine-readable pattern only on some (UNVERIFIED) | | Treat as manual entry |

Back side of the 2019 card (SECONDARY, Wikipedia "Polish identity card"): place of birth, date of issue, card number, issuing authority, names of parents, PESEL, repeated photo; the CAN (card access number, needed to open the chip) is printed on the front lower right (the same article places a barcode with the CAN at the top of the back; this conflicts with the gov.pl leaflet showing only an MRZ field, so UNVERIFIED which is right). The registered address was removed from the card in 2015 (SECONDARY). The 2021 amendment of the law lists parents' names, date and place of birth, sex and PESEL in the electronic layer (chip) (SECONDARY, search summary of the ustawa o dowodach osobistych; the Sejm ELI text was not opened).

### 2.2 What is NOT in the MRZ

Address (not even printed on the card since 2015), parents' names, place of birth (TD3 and TD1 have none), PESEL as such is not a standard MRZ field (Polish cards may place it in optional data: UNVERIFIED). Name fields are transliterated to A-Z and truncated: Polish diacritics are lost (Ł to L, Ż to Z), so the MRZ name must be compared with the visual zone (VIZ) which the clerk confirms.

Consequence for the product: the MRZ gives surname, given names, document number, nationality, date of birth, sex, expiry. Everything else (address, parents, birth place) is self-declared by the visitor or read from the VIZ or the chip, with per-field provenance.

### 2.3 Parsing and check digits (ICAO 9303)

- Check digit: map characters to numbers (0-9 face value, A-Z = 10-35, `<` = 0), multiply by repeating weights 7, 3, 1, sum, modulo 10. Worked example: document number L898902C3 gives 6 (SECONDARY, summaries of Part 3; ICAO Part 3 and Part 5 PDFs are the normative sources but could not be downloaded with curl tonight, the server returned an HTML page).
- TD1 line 2: birth date positions 1-6 with check digit at 7, sex at 8, expiry 9-14 with check digit at 15, nationality 16-18, optional data 19-29, composite check digit at 30 (SECONDARY, matches the layout summary). The composite covers line 1 positions 6-30, and line 2 positions 1-7, 9-15 and 19-29 (UNVERIFIED here; confirm in ICAO Doc 9303 Part 5 before shipping; it is the standard definition I know, but the secondary sources I opened disagreed in wording).
- TD3 (passport): two lines of 44; check digits for document number, birth date, expiry, personal number and a composite (SECONDARY).
- Write the parser yourself with unit tests; the characters `O`/`0`, `I`/`1`, `B`/`8`, `S`/`5`, `Z`/`2` are corrected only in numeric fields (the `mrz` npm package does the same, SECONDARY). Two-digit years need a century rule: birth dates use "if year > current two-digit year then 19xx else 20xx"; expiry uses 20xx.

### 2.4 MRZ OCR in the browser

| Option | Licence | Status |
|---|---|---|
| Tesseract.js (WASM) | Apache-2.0 (SECONDARY) | Default English model struggles with OCR-B; an MRZ-trained model helps (SECONDARY, dev.to write-up); no measured accuracy found |
| `web-mrz-reader` npm bundles a custom MRZ traineddata with Tesseract.js v5 | Licence of the model not confirmed | Check before shipping |
| `newtondev-mrz-parser` | MIT, v1.1.0 (SECONDARY) | Parser only |
| `mrz` npm | Licence not confirmed | Parser with OCR-confusion correction (SECONDARY) |
| Dynamsoft MRZ SDK | Proprietary, paid | Excluded by the open-source rule |
| PassportEye (Python) | Not checked | Server-side alternative; images would have to leave the phone |

Recommended pipeline (all in the phone browser; image never uploaded): getUserMedia video, crop to the lower third of the card guide frame, greyscale and adaptive threshold, OCR each frame at about 3 fps, run the check-digit validator, accept only when all check digits pass in two consecutive frames or after voting per character across frames, then show the result for confirmation. No accuracy number is claimed here: measure on at least 20 real or synthetic card photos before the pitch and report the measured rate.

### 2.5 Camera capture: getUserMedia versus file input

- `<input type="file" accept="image/*" capture="environment">` opens the OS camera or a picker; MDN states only that the UI allows selecting an existing file or creating a new one, and it says nothing about gallery storage (VERIFIED: the page is silent). The attribute is "Limited availability", not Baseline (VERIFIED, MDN). Behaviour differs by platform: on Android the capture attribute removes the option to pick an existing picture (SECONDARY, web.dev); iOS Safari has had bugs where each capture replaces the previous selection (SECONDARY, Apple developer forum report).
- Whether the OS camera app stores the file in the gallery and cloud backup is decided by the OS and the camera app, not by the page; I found no primary source (UNVERIFIED). Test on one Android and one iPhone before claiming it.
- getUserMedia gives the page a live stream; drawing a frame to an in-memory canvas keeps pixels inside the page's memory, never passing through the camera app, and it also enables live MRZ scanning. Costs: needs HTTPS, permission prompt every session on iOS, resolution and autofocus control varies, some in-app browsers block it. Offer both: getUserMedia first, file input as fallback with a warning "photo may remain in your gallery".
- Never write images to localStorage, IndexedDB or Cache; revoke object URLs; release tracks (`track.stop()`); the profile data itself stays on the phone only as the visitor decides.

### 2.6 Chip reading (NFC)

Web NFC is NDEF-only; the Chrome documentation states that ISO-DEP, NFC-A/B/F, peer-to-peer and host card emulation are not supported (SECONDARY, Chrome developer docs via search summary), and MDN says low-level operations are not currently supported and the API is Limited availability and Experimental (VERIFIED). It runs only in secure top-level contexts and in practice only Chrome on Android (SECONDARY). A 2016 W3C list reply said ePassport/ICAO 9303 use cases are not in the Web NFC group's scope (SECONDARY). Therefore reading an e-passport or e-dowód chip in a browser (BAC or PACE over ISO-DEP) is not possible; do not build it. Options: the desktop reader (Osmond R), or a later native Android app (out of scope for 24 hours). Legal basis for clerks reading the chip layer (not only the visual data) was not researched; list as an open question.

### 2.7 Large-print verification UI

- One field per row or card, label above value, value at 32-40 px minimum, bold sans-serif with a slashed or dotted zero (for example a monospaced face for document numbers) to separate 0/O and 1/I/l.
- Confirmation per field: "Zgodne z dokumentem" (matches the document) and "Popraw" (correct). Highlight fields whose check digits failed in the red-and-icon style (never colour alone).
- Show MRZ-derived value beside the visual-zone value typed by the clerk; flag differences (transliteration of ł, ż).
- WCAG 2.1 AA: contrast 4.5:1, text resize to 200%, keyboard-operable (UNVERIFIED here, well-known criteria).

## 3. Secure QR handoff, phone to clerk

### 3.1 Capacity (verification of C25)

Version 40 at error correction L holds 7,089 numeric, 4,296 alphanumeric and 2,953 binary characters (VERIFIED, Wikipedia QR code). The M, Q and H capacities were not in the part of the article I could read; from the standard they are lower (roughly 2.3 KB, 1.7 KB, 1.3 KB; UNVERIFIED). A version-40 symbol is 177 x 177 modules (VERIFIED, qrcode.com). Practical scanning of dense codes from a phone screen with a PC webcam is unreliable; plan on at most about 1 KB per code (engineering estimate, UNVERIFIED) and chunk with a sequence header if more is needed.

Encrypted data does not compress, so compress (CBOR or gzip) before encrypting. A compact profile of one or two persons (names, dates, document numbers, addresses) is typically 300-800 bytes after compression (estimate, UNVERIFIED) and encryption adds about 28 bytes (12-byte nonce + 16-byte tag).

### 3.2 Online protocol (recommended)

1. The clerk workstation creates a session: random 128-bit `sid`, ephemeral ECDH key pair `(a, A)` (WebCrypto, non-extractable private key kept in memory). It registers `sid` and a hash of `A` with the relay (outbound HTTPS from the isolated office; no inbound port).
2. QR on the clerk screen encodes `https://<office-host>/v/#sid.A_b64u.exp` in the URL fragment: fragments are not sent to servers (design note in docs/02-architecture). Include an expiry and a version.
3. The phone opens the page, generates an ephemeral key pair `(b, B)`, derives `K = HKDF(ECDH(b, A), salt = sid, info = "asystent-v1")` and encrypts the profile with AES-GCM using a random 96-bit nonce and AAD = `sid || B || version`.
4. The phone POSTs `{sid, B, nonce, ciphertext}` once. Relay stores it in RAM with TTL 10 minutes and accepts exactly one upload per `sid` (replay and overwrite protection).
5. The clerk side receives it by SSE or WebSocket (long-poll fallback), derives `K`, decrypts, deletes on read.
6. Short authentication string: both screens show 3 words or 4 digits derived from `hash(A || B || sid)`; the clerk confirms verbally with the visitor. This defeats someone who photographs the QR and uploads first.

Algorithms: WebCrypto supports ECDH, HKDF and AES-GCM; MDN `deriveKey` lists X25519, HKDF and PBKDF2 and the AES variants (VERIFIED); its examples use P-384, and X25519 availability must be feature-detected per browser. Use P-256 as the baseline for wide device support and X25519 when present (UNVERIFIED for browser matrix). HPKE (RFC 9180) is not part of WebCrypto (not mentioned on MDN; UNVERIFIED as a negative); a JavaScript implementation could be added, but the manual ECDH+HKDF+AES-GCM scheme above is the same construction and fits a 24-hour build.

### 3.3 Threats and mitigations

| Threat | Mitigation |
|---|---|
| Relay operator or compromise reads data | Ciphertext only; relay never sees `K`. Caveat: the relay that serves the phone page could ship altered JavaScript; serve the page from the office's own domain or a static host separate from the relay, with SRI on assets and a strict CSP |
| QR photographed and used by a third party | One-shot upload, TTL 10 minutes, SAS confirmation, session bound to the clerk desk |
| Phishing (fake QR at the counter) | QR printed on the desk shows only the office URL; the dynamic per-visitor QR appears only on the clerk screen; the page shows the office name and the SAS |
| Replay of a captured upload | One upload per `sid`, nonce and AAD binding, deletion on read |
| Data left on the phone | Page keeps nothing by default; "remember me" is opt-in and encrypted with a user passphrase (out of scope for the demo) |
| Server memory forensics | RAM-only store; disable swap on the relay host; no request-body logging (log sizes only) |

### 3.4 Store: in-memory versus Redis (verification of C27)

Redis documents a "no persistence" mode and RDB/AOF options (VERIFIED, Redis persistence docs), so disabling persistence is legitimate. But for one process a Python dict with `expires_at` and a background sweeper is simpler and safer for the demo; Redis adds a network hop, replica and backup copies, and a RAM copy still can reach swap or core dumps. If Redis is used: `save ""`, `appendonly no`, no replicas, `maxmemory` with `volatile-ttl`, bind to a private interface with ACL password. Redis licensing for current versions (server-side licence changes since 2024) is UNVERIFIED here; Valkey is a drop-in alternative to evaluate. The client-side AES-GCM encryption keyed from the QR is the key design element, and it holds regardless of the store.

### 3.5 Delivery and network layouts

- SSE (EventSource) is one-way, passes HTTP proxies and reconnects automatically; WebSocket is two-way. For one-shot delivery SSE with long-poll fallback is enough (design choice).
- Visitor on mobile data, clerk PC in an isolated office network: both connect outbound to a public relay (cloud or DMZ). The office server pulls; nothing needs to reach into the office. If the office has no internet at all: use the offline QR variant below or an in-office Wi-Fi VLAN hosting the relay.
- Offline QR (no relay): the clerk shows QR-1 (session `sid` + `A`, about 50 bytes); the phone shows QR-2 with `B + nonce + ciphertext` (target at most 1 KB, chunk if larger); the clerk scans with a webcam or the Osmond's barcode reader (the Osmond recognises QR Code, VERIFIED in the manual). Works with no network on either side.

## 4. Hardware document reader (Adaptive Recognition "Osmond")

All statements below come from the official Osmond User Manual and the vendor pages (links in Sources), unless marked.

### 4.1 Product line and software generation

- Models: Osmond L (USB, UV illumination), Osmond R (USB, UV and built-in RFID module), Osmond N (network device with RFID, dual USB/network mode) (VERIFIED, manual). The device reads visible white, infrared and UV images, the MRZ, VIZ and 1D/2D barcodes from the full page, and digital data from the contactless chip and optional contact chip (VERIFIED).
- Software: "Passport Reader (PR) Software Package". For Osmond devices version 2.1.10.2 or higher is required (VERIFIED). The new generation Osmond V2, manufactured from August 2024 (serial 1244012 and up), requires 2.1.11.3.o3 or higher; the SDK/API is unchanged and applications for earlier Osmond models keep working (VERIFIED). The vendor page currently lists API version pr-2.2.0.8 with licence date 2026-05-18 (VERIFIED) and an earlier listing of pr-2.2.0.4 from 2025-08-05 (SECONDARY). From 2.2.0.7 drivers ship only in the 64-bit installer and 32-bit operating systems are no longer supported (VERIFIED).
- Package contents: drivers, SDK for C/C++, Visual Basic, Delphi, C#, VB.NET, Java and Python (with HTML/CHM manual and samples), Full Page Reader application, Authentication Checker application, utilities (License Manager, PRDTool), and the NetAPI SDK (from 2.1.11.1) (VERIFIED, manual section 2). The installer component list includes `pcsc`, `tools`, `fpsdemo`, `license_tools`, `ocr`, `prdt`, `prwebsrv`, `qtgx` (VERIFIED); the function of `prwebsrv` is not described (the manual mentions it next to a "procr-ip" OCR engine setting).
- Applications on the manual's list for integration: Full Page Reader and Authentication Checker (end-user), "Autofill application (sold separately)" for quick integration, and API, Twain and NAI for developers (VERIFIED).
- Operating systems: 64-bit Windows 7/8.1/10/11 and Linux (kernel 3.2+) for USB models (VERIFIED). On Windows 7/8 the PC/SC interface for RFID and the contact chip is not available on Osmond R V2; on Windows 10/11 it is (VERIFIED).
- Support for a 2022 unit: the vendor page lists Osmond L and R USB manuals under the current package (VERIFIED), and the manual states SDK/API are the same as in earlier versions and applications written for earlier models keep working (VERIFIED). The 2.1.10.x package the owner holds is consistent with the minimum requirement of 2.1.10.2. Downloads are behind a form that asks for the device serial number (VERIFIED), so newer packages require a vendor request.

### 4.2 Licensing model

- Each software module has its own licence file holding issue date, expiry date and device serial number; "The update service period of the given software module is controlled by the expiry date. All software versions that are issued prior to this date, will run on the device" (VERIFIED, manual chapter 8). For scanners manufactured in 2014 or later the licences are stored on the scanner (VERIFIED). A default licence for the basic functions is pre-installed; VIZ OCR and VIZ AUTH OCR engines and the authentication add-on are separate purchases with their own licences (VERIFIED, manual). Authentication software: one year licence included, yearly subscription optional (SECONDARY, authentication datasheet via search). Autofill: one year of free updates for new document types, optional subscription after (VERIFIED, Autofill page).
- Practical consequence: a 2022 purchase likely has update licences that expired in 2023 (UNVERIFIED for the owner's unit; check with License Manager). Software released after that date, such as 2.2.0.8 (2026), may not run. Keep the installed 2.1.10.x for the demo; do not update. Licence upload can be automated by MSI or done with License Manager (VERIFIED).
- Supported languages of the VIZ OCR engine (Polish diacritics, Polish ID layouts) were not found on public pages; verify by scanning a real dowód and a passport with Full Page Reader before the event.

### 4.3 What the device returns

- Fields parsed from MRZ and VIZ, barcode contents, document images (white, IR, UV, and photo), RFID data (e.g. ePassport data groups and chip photo) when the device is R or N, authentication check results when an authentication licence is present (VERIFIED in general terms; field-by-field list is in the SDK manual, which is behind the download form, UNVERIFIED).
- Barcode types recognised: EAN, Code39, Code128, Interleaved 2 of 5, PDF417, Data Matrix, QR Code, Aztec (VERIFIED, manual section 23).
- Save formats in Full Page Reader: ZIP, PDF, XML, JSON, CSV, ECZ; typing a filename with the extension selects the format; a JSON output template exists (manual chapter 32) (VERIFIED).
- Whether the chip of a Polish e-dowód can be read by the PR software (PACE with CAN) is not documented on public pages; the Polish card's chip application and data groups are UNVERIFIED. Test with the owner's own card; the CAN is printed on the card.

### 4.4 Autofill / "Digital Reception"

- Public page: "Autofill" connects an Adaptive Recognition ID scanner to any system, captures ID data and populates forms of PMS or other registration systems; data can be sent through a web browser or a separate application; it includes an SDK with API documentation and sample code; requirements Windows and Linux, 1 GB RAM, USB 2.0; one year of free updates (VERIFIED, adaptiverecognition.com/products/autofill).
- Not found publicly: the components "Autofill Windows", "App Form Filler", "Web Form Filler", the Chrome extension "ARH Digital Reception", and the delivery mechanism to a web page. Searches for "Digital Reception" with the vendor name returned nothing (UNVERIFIED). A likely mechanism is a browser extension that talks to a local service, comparable with third-party extensions such as GuestBan PMS IDfill, which pairs with a desktop scanner app (SECONDARY, Chrome Web Store listing); this is an inference, not documented for ARH. The owner has the real package locally: inspect the extension's `manifest.json` (does it use native messaging or `localhost` connections?) before deciding whether to reuse it. Reusing a proprietary extension is a distraction for the demo; prefer own bridge.

### 4.5 Localhost bridge design (verification of C28)

Browsers cannot talk to the Osmond directly in practice: it is a vendor-driver device (the SDK and PC/SC are the supported interfaces). WebUSB gives raw access only to USB devices not claimed by an OS driver; WebHID covers HID-class devices; Web Serial covers serial ports, USB CDC-ACM and Bluetooth SPP, is "Limited availability" and requires a secure context (VERIFIED, MDN Web Serial page, which also states WebUSB and WebHID are distinct APIs). None of these is a fit for a driver-managed scanner; they are Chromium-only (SECONDARY) and the Osmond's USB descriptors were not checked (UNVERIFIED).

Bridge design (recommended):
- Process: a small service bound to `127.0.0.1` only. Language: Python with the vendor Python SDK, or a C# service (the SDK has C#). Alternative with zero SDK code: watch the folder where Full Page Reader saves JSON/XML/ZIP (VERIFIED save formats) and expose the newest result.
- API: `GET /v1/status`, `POST /v1/scan` (trigger), `GET /v1/result/{id}` or `WS /v1/events`. Returns the parsed fields, optionally images, and chip data if present; images remain in memory until fetched once.
- Security: pairing token generated per session and shown in the tray or console, sent as `Authorization`; exact `Origin` allowlist (the office app origin); `Host` header must equal `127.0.0.1:<port>` (DNS-rebinding defence); no wildcard CORS; per-record TTL of 60 seconds; no writes to disk except by explicit option; log metadata only. Browsers treat loopback as a potentially trustworthy origin so an HTTPS page can call `http://127.0.0.1` in current Chrome and Firefox (UNVERIFIED); Chrome's newer local-network access prompts may apply (UNVERIFIED), so test on the target browser.
- Fallback when no device: the bridge ships a `mock` mode that returns canned scans.
- Provenance tag for every value delivered: `source: "reader-mrz" | "reader-viz" | "reader-chip"`.

## 5. Stack recommendation (24 hours, on-premise or one laptop)

### 5.1 Two options compared

| Criterion | A. Python FastAPI backend + TypeScript front ends (recommended) | B. TypeScript monorepo (NestJS or Next + shared Zod) |
|---|---|---|
| PDF forms, DOCX, OCR, NLP, PII (Presidio-style tooling, pypdf, python-docx) | Native Python ecosystem | Weaker: pdf-lib and docx libraries exist, PII tooling thin |
| Contracts | FastAPI generates OpenAPI 3.1 from Pydantic; commit `contracts/openapi.json`; generate TS client with `openapi-typescript` or `orval` (UNVERIFIED versions) | Zod schemas shared natively, OpenAPI via adapters |
| AI coding agents | Strong on both; agents handle Python typing well | Single language reduces context switching |
| Packaging | uv or venv + one start script; Docker optional | pnpm workspace; one runtime |
| Risk | Two toolchains | Hardest parts (PII, legal text, DOCX fidelity) lack libraries |

Verdict: A confirmed. Mitigation for two toolchains: one `make dev` or `./start.ps1` that starts API (uvicorn), clerk web and visitor PWA; a CI-free contract test that fails if `contracts/openapi.json` is out of date.

### 5.2 Database

- Demo: SQLite in WAL mode, application-level field encryption for the personal fields (AES-GCM with a key from an env var or OS keystore; Python `cryptography`, UNVERIFIED version) so a copied `.db` file is useless without the key. SQLCipher Community Edition is BSD-style, usable in closed and open source commercial software, with notice and trademark conditions (VERIFIED, Zetetic page) but needs a native build of the Python binding; on Windows that is a time sink, so use field encryption tonight and name SQLCipher as the production-hardening option.
- Production profile: PostgreSQL with row-level security by team or case, `pgcrypto` or application-level field encryption, TDE or disk encryption at the host (UNVERIFIED general practice). The same SQLAlchemy models; Alembic migrations (UNVERIFIED).
- Counter sessions (walk-in data) are not stored in either database: RAM with TTL only.

### 5.3 Authentication, audit, containers, tests

- Clerks: OIDC against the city's identity provider in production (Keycloak or Entra ID, UNVERIFIED which the city uses); passkeys (WebAuthn) as the phishing-resistant factor; hackathon demo uses local accounts with Argon2 hashes and a role claim (clerk, reviewer, signer, admin) behind the same interface so the swap is configuration.
- Audit log: append-only table; each row stores `prev_hash` and `hash = SHA-256(prev_hash || canonical_json(record))`; DB trigger (PostgreSQL) or code path forbids UPDATE and DELETE; a `/audit/verify` endpoint recomputes the chain; export the head hash to the printed handover sheet so tampering is detectable (design, UNVERIFIED as an implementation).
- Containers: `docker compose` with services api, clerk-web, visitor-pwa, relay, optional ollama; also a no-Docker path for the clerk's Windows PC (many offices block Docker).
- Tests: pytest + httpx for the API; Playwright for end-to-end and for PDF/screenshot visual regression; vitest for front ends; axe-core (via `@axe-core/playwright`) for accessibility (UNVERIFIED versions; the tools are standard). Target WCAG 2.1 AA (the Polish public-sector standard, UNVERIFIED here).

## 6. LLM integration layer

### 6.1 Provider abstraction

One interface `complete(messages, schema, data_class) -> StructuredResult` with implementations: `mock` (recorded answers, tests, offline demo), `local` (OpenAI-compatible endpoint), `cloud` (Anthropic API, or Bedrock in an EU region; Bedrock EU availability and model list UNVERIFIED, check the region catalogue).

Ollama's OpenAI-compatible API supports `/v1/chat/completions` (streaming, vision, tools), a stateless `/v1/responses`, `/v1/embeddings`, and JSON mode via `response_format`; the page does not mention JSON Schema enforcement and `tool_choice` is unsupported on chat completions (VERIFIED, Ollama docs). So do not rely on server-side schema enforcement: validate with Pydantic, retry once with the error message, then fail visibly. vLLM is the alternative for GPU servers (UNVERIFIED).

Polish open models (SECONDARY, Hugging Face cards and a hosting guide): Bielik models by SpeakLeash/Cyfronet are Apache-2.0 plus separate terms of use at bielik.ai/terms (read both), with GGUF builds importable into Ollama; PLLuM (CYFRAGOVPL) has mixed licences: some variants Apache-2.0, Llama-based variants carry the Llama 3.1 licence, and `-nc-` variants are non-commercial; no official Ollama entry was found, only community GGUFs. Chat templates differ (PLLuM `[INST]`, Bielik ChatML), so check `ollama show --template`. Evaluate on the golden set rather than assuming Polish-legal competence.

### 6.2 PII pseudonymisation before any cloud call

- Detectors: Presidio has a `PlPeselRecognizer` (checksum, languages en and pl, enabled by default, entity `PL_PESEL`); Polish named-entity recognition needs a separately installed spaCy model (`pl_core_news_md` or `_lg`) with label mapping (persName to PERSON, placeName to LOCATION) (SECONDARY, Presidio docs and third-party guides; no official page named the best model size). Add custom regex recognizers for NIP, REGON, Polish phone and bank-account (IBAN PL), dowód number, car plates, land-register numbers (księga wieczysta) and checksum-validate where a checksum exists.
- Reversible tokens: `[OSOBA_1]`, `[ADRES_2]`, `[PESEL_1]` stored in a per-request map in memory; re-identify after the response; reject any output token not in the map.
- Policy enforced in the gateway, not in callers: data class `PUBLIC` goes to any provider; `PERSONAL` goes only to `local`, or to `cloud` after pseudonymisation; names inflect in Polish, so pseudonymise inflected forms by lemma-aware matching or by NER spans, not exact string.
- Canary test (blocking gate): plant synthetic PESEL, name and address in inputs; assert none occurs in any outbound request body to an external provider.
- Redaction for disclosure is a separate feature: burn masks into raster output.

### 6.3 Structured outputs, grounding, evaluation, injection

- Structured outputs: Pydantic models per task (classification, deadline facts, draft sections); JSON mode or tool-use schema on cloud providers; validation plus one retry.
- Grounding: every legal citation must resolve in a local snapshot of the act text fetched from the Sejm ELI API; a code check rejects citations or quotations not found verbatim (design note step 7); the model gets only retrieved passages with ids and must answer with passage ids.
- Evaluation harness: a golden set of about 40 synthetic requests (taxonomy classes plus traps: hidden instruction, mixed letter, mass request); metrics: classification accuracy, citation validity (must be 100%), deadline-calculation exactness, leak-canary pass, time per case; run on `mock`, `local` and `cloud`; show numbers in the UI and the pitch. Do not claim any accuracy until measured on this set.
- Prompt injection from incoming e-mail: request text and attachments are untrusted data in a delimited block; system prompt states that nothing inside it is an instruction; no tools with side effects reachable during analysis; a heuristic and model-based detector flags instruction-like content and shows it to the clerk; outputs are never sent automatically; strip HTML, hidden text, zero-width characters and PDF metadata before the model sees them.

## 7. Risks and what to mock in 24 hours

| Item | Risk | Demo decision |
|---|---|---|
| Osmond reader | Driver, licence expiry, USB on the demo PC | Mock mode by default; real device as a bonus through the Full Page Reader folder watcher; rehearse once tonight with the owner's unit |
| Chip reading | Not possible in browser; PACE undocumented for e-dowód | Do not build; show as roadmap |
| MRZ OCR accuracy | No benchmark; lighting and glare | Check-digit-driven correction, manual entry always available; show measured rate from a small test set |
| QR crypto | Subtle mistakes | Implement the 6-step flow once, with a unit test using two simulated parties; SAS in UI |
| Relay on the internet | Needs public host and TLS | Run on the laptop and tunnel only if the phone must be off the Wi-Fi; otherwise phone and laptop on one hotspot |
| PDF templates | Wrong coordinates, XFA, missing fonts | Pick 3 forms, detect type, embed DejaVu, run template-integrity test |
| Printing | Driver scaling, duplex | Export print-ready PDF plus one tested real print; do not depend on silent printing |
| LibreOffice fidelity | Reflow | Use DOCX only for letters; keep templates plain |
| LLM | Rate limits, offline venue, PII leakage | `mock` provider default with recorded answers; `local` optional; cloud only on synthetic data |
| Legal | Chip data and ID scanning basis, retention | State the assumptions in the docs; no real personal data in the repository or demo |
| Redis | Unneeded service | Use in-process TTL store |
| Authentication | OIDC setup time | Local accounts behind the OIDC interface |

Build for real: deadline clock, request classification with citation check, PDF overlay accuracy test, hash-chained audit with verify endpoint, pseudonymisation gateway with canary test, QR session crypto, check-digit parser.

## Verdicts on the previous research

| Claim | Verdict | Source | Correction |
|---|---|---|---|
| C25: standard QR holds about 2.9 KB binary, enough for gzip-compressed encrypted profile of one or two persons | PARTLY | Wikipedia QR code (2,953 bytes, version 40 level L); qrcode.com (177 x 177 modules) | The figure is the maximum at the lowest error correction and the largest symbol; M/Q/H hold less and big codes scan poorly from a phone screen to a webcam. Compress BEFORE encrypting (ciphertext does not compress), and plan on about 1 KB per code with chunking. One or two compact profiles plausibly fit, unverified |
| C26: `<input type=file capture>` saves the photo into the gallery and cloud backup, so camera capture must use getUserMedia | PARTLY | MDN capture attribute (silent on storage); web.dev (SECONDARY) | The premise is not documented: MDN says nothing about the gallery and behaviour belongs to the OS camera app. The conclusion (prefer getUserMedia with an in-memory canvas) is still sound, mainly because it enables live MRZ scanning; keep the file input as fallback with a warning. Test on real phones |
| C27: RAM-only buffer (Redis without RDB/AOF, TTL 15-30 min) with client-side AES-GCM keyed from the QR is the right store | PARTLY | Redis persistence docs (no-persistence mode exists) | The design is right, the product choice is optional: an in-process dict with TTL is simpler and smaller attack surface for one relay; use Redis only with persistence off, no replicas, and check its current licence. Prefer TTL of 10 minutes and one-shot reads. The crypto must be ECDH-derived, not a key placed raw in the QR |
| C28: a browser cannot talk to a USB passport reader; a Local Device Bridge on 127.0.0.1 with pairing token is required | PARTLY | MDN Web Serial; Osmond manual | Directionally right: the Osmond is driven through vendor SDK and PC/SC, and Web Serial/WebUSB/WebHID target serial, raw-USB and HID devices (and are Chromium-only), so a bridge is the practical route. But "cannot" is unproven for the Osmond (descriptors not checked), and a SDK-free route exists: Full Page Reader saves JSON/XML/ZIP to a folder the bridge can watch. Add Origin allowlist and Host check, not only a pairing token |
| C29: pypdf or pdf-lib can fill AcroForm fields with embedded Polish fonts and flatten; flat PDFs need coordinate overlay (ReportLab/PDFKit); one-character boxes need per-character stepping | PARTLY | pypdf forms docs; pdf-lib README | Both fill and flatten (VERIFIED); pdf-lib needs fontkit and its subsetting fails on some fonts (VERIFIED). Overlay is right, but ReportLab and PDFKit only generate the overlay page: merging onto the original needs pypdf, pdf-lib or qpdf (PDFKit cannot open templates). XFA is a third case that overrides page content (VERIFIED). Comb-field spacing by library is unverified: step characters yourself |

## Open questions and what could not be verified

- ICAO Doc 9303 Part 3/5 PDFs: the icao.int URLs returned an HTML page to curl and an HTTP error through the fetch tool; check digits and the TD1 composite range are from secondary summaries plus my knowledge. Verify against the normative text or against a real card before shipping.
- Exact printed layout of the 2019 dowód back (CAN barcode versus MRZ only): the official gov.pl leaflet confirms the MRZ field; the Sejm ELI regulation annex (Dz.U. 2019 poz. 224) was not opened.
- Which Polish documents (karta pobytu, older dowód patterns) carry an MRZ, and PESEL in MRZ optional data: not verified.
- mDowód verification flow: not researched.
- Osmond: field-by-field SDK output, VIZ OCR language list including Polish, behaviour of the PR software with the Polish e-dowód chip, the owner's current licence expiry dates, whether `prwebsrv` is a local web service, and the content of the "Autofill" manuals and Chrome extension (download centre is gated by serial number). Check inside the owner's own installed package.
- Browser behaviour: loopback-from-HTTPS rules and Chrome local-network access prompts, X25519 support matrix, getUserMedia on iOS standalone PWAs, gallery saving by camera capture: test on real devices.
- Library licences and versions marked UNVERIFIED (pypdf, ReportLab, qpdf, pdfme, pypdfium2, python-docx, docxtpl, SumatraPDF, Keycloak). PyMuPDF/pdf-lib/pdfcpu/SQLCipher are verified.
- Chrome `SilentPrintingEnabled` (Chrome 144 on Windows) is from a Samsung browser-policy page seen through search results; confirm on chromeenterprise.google.
- Bedrock EU model availability, Bielik terms of use text, PLLuM licence per variant, Presidio Polish accuracy on names: not measured.
- Legal: basis and retention rules for scanning ID documents and reading chip data in a city office (UODO, RODO art. 5 and 6, ustawa o dowodach osobistych): not researched here.

## Sources

- https://www.qrcode.com/en/about/version.html (QR version 40 size)
- https://en.wikipedia.org/wiki/QR_code (capacity 7,089 / 4,296 / 2,953 at version 40-L)
- https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/capture
- https://web.dev/articles/media-capturing-images
- https://developer.mozilla.org/en-US/docs/Web/API/Web_NFC_API
- https://developer.chrome.com/docs/capabilities/nfc
- https://developer.mozilla.org/en-US/docs/Web/API/Web_Serial_API
- https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/deriveKey
- https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
- https://adaptiverecognition.com/doc/id-scanners-readers/passport-reader-software/
- https://adaptiverecognition.com/doc/?p=1986
- https://adaptiverecognition.com/products/autofill/
- https://adaptiverecognition.com/osmond/
- https://adaptiverecognition.com/app/uploads/DOC/ID_Scanners_and_Readers/Osmond_L_and_R_ID_Scanners_with_USB_Interface/Osmond_L_andR_ID_Scanner_with_USB_Interface_Consolidation/Osmond_User_Manual.pdf (668 pages, read locally)
- https://adaptiverecognition.com/app/uploads/DOC/ID_Scanners_and_Readers/Authentication_Software_Add_Ons_for_AR_ID_Reading/authentication_software_datasheet.pdf
- https://chromewebstore.google.com/detail/guestban-pms-idfill/hgabpmhlkjgedjcndcemipdagagnfbdk
- https://www.gov.pl/documents/1963407/2777240/Weryfikacja_autentycznosci_dowodu_osobistego.pdf (MRZ field on dowód)
- https://en.wikipedia.org/wiki/Polish_identity_card
- https://api.sejm.gov.pl/eli/acts/DU/2019/224/text.html (regulation with the card pattern; not opened)
- https://icao.int/publications/Documents/9303_p3_cons_en.pdf and https://www.icao.int/publications/Documents/9303_p5_cons_en.pdf (normative, not read)
- https://github.com/Hopding/pdf-lib (MIT)
- https://pypdf.readthedocs.io/en/stable/user/forms.html
- https://github.com/pdfcpu/pdfcpu (Apache-2.0)
- https://artifex.com/licensing and https://pymupdf.readthedocs.io/en/latest/about.html (AGPL or commercial)
- https://www.zetetic.net/sqlcipher/open-source/ (SQLCipher Community Edition)
- https://docs.ollama.com/api/openai-compatibility
- https://huggingface.co/CYFRAGOVPL/PLLuM-12B-chat and https://huggingface.co/speakleash/Bielik-11B-v2.3-Instruct-GGUF (model licences, SECONDARY)
- https://microsoft.github.io/presidio/supported_entities (PL_PESEL, SECONDARY)
- https://developer.samsung.com/browser/policy/silent-printing-enabled.html (SilentPrintingEnabled, SECONDARY)
- https://dev.to/ilhannegis/browser-based-passport-mrz-reader-with-tesseractjs-655 and https://www.npmjs.com/package/mrz (MRZ OCR and parser, SECONDARY)
