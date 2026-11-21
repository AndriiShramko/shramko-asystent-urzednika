### 1. Thirty Unconventional Ideas (Ranked by Jury Impact ÷ Effort)

*Effort is measured in agent-hours (one human directing parallel coding agents). Every library listed is MIT, Apache-2.0, BSD, or ISC; zero external calls at runtime.*

---

#### 1. COI Dialect Switch & Spec-Errata Generator
- **Pitch (PL):** *Obsługujemy rozbieżności między dokumentacją a plikami wzorcowymi jednym przełącznikiem i oddajemy COI gotową listę errat.*
- **What it does:** Exposes a runtime profile (`reference_export_compat` vs. `strict_spec`) handling all eight measured contradictions (misspelled schema key, last tab `FINISH` vs. `MAIN`, read-only flags on `EXTERNAL_SYSTEM` defaults, `REQUIRED` emission, undocumented keys `multiLevelTree`, `searchEnabled`, `minItemRows`). Emits a structured `dialect_notes[]` block in the report explaining every reconciliation choice.
- **How to build:** Pydantic v2 (`MIT`) serializer aliases + profile config map; deterministic serializer hooks.
- **Scoring criterion:** Completeness (30%), Code Quality (20%), Deployment Potential (20%).
- **Effort:** 1.0 h.
- **Risk:** Tone could sound pedantic if phrased as criticism; frame neutrally as *"compatibility profiles for seamless import into current and next Generator releases."*

#### 2. 100% Ink-Accounting Coverage Ledger ("Bilans Tuszu")
- **Pitch (PL):** *Każdy napis i kratka z papieru dostaje status: zmapowany, przejęty przez standard COI lub usunięty jako artefakt papierowy — zero cichych strat.*
- **What it does:** Accounts for 100% of extracted text runs, checkboxes, and fillable slots on the input form by assigning every bounding box one of four states: `MAPPED_TO_FIELD`, `ABSORBED_BY_COI_STANDARD` (linked to exact standard section), `DROPPED_PAPER_ARTIFACT` (e.g., handwritten signature line, *"wypełnia urząd"*, *"miejscowość i data"*), or `UNACCOUNTED` (triggers mandatory reviewer warning).
- **How to build:** Tag every element in the unified page IR with a unique `element_id`; run a post-composition set-difference check (`input_ids - accounted_ids`) in pure Python.
- **Scoring criterion:** Intuitiveness (20%), Originality (10%), Completeness (30%).
- **Effort:** 2.0 h.
- **Risk:** Noisy OCR fragments (specks, page footers) can inflate `UNACCOUNTED`; filter running headers/footers and page numbers (`Strona X z Y`) into `DROPPED_LAYOUT_CHROME`.

#### 3. JSONata Static Analyser, Dead-Branch Prover & Title-Rename Refactor
- **Pitch (PL):** *Statyczny analizator JSONata wykrywa martwe warunki przed importem i automatycznie naprawia reguły, gdy urzędnik zmieni tytuł strony.*
- **What it does:** Parses every `states[].query` AST, verifies that every referenced `tab.title` and `techName` exists, checks for circular `SHOW`/`READ_ONLY` cycles and unsatisfiable clauses, and automatically rewrites affected JSONata expressions whenever the reviewer edits a page title or `techName` in the UI.
- **How to build:** `jsonata-python` (`MIT`) AST traversal + NetworkX (`BSD-3`) cycle check; mirror check with browser JS `jsonata` (`MIT`) in the frontend.
- **Scoring criterion:** Completeness (30%), Code Quality (20%), Intuitiveness (20%).
- **Effort:** 2.5 h.
- **Risk:** Subtle parser divergences between `jsonata-python` and JS `jsonata` on Polish backticked identifiers; keep generated JSONata inside a strict, tested grammar subset.

#### 4. Proposal-Ready Statutory Dictionaries Pack (with Legal Basis)
- **Pitch (PL):** *Dołączamy gotowe słowniki dziedzinowe z podstawą prawną — od 11 ras psów agresywnych po kategorie pasa drogowego i frakcje odpadów.*
- **What it does:** Detects domain triggers in the paper form and attaches ready-to-import COI dictionary proposals (JSON + code/label/legal citation): 11 aggressive dog breeds (Dz.U. 2003 nr 77 poz. 687), road-lane occupation types, municipal waste fee property types, Polish sports disciplines, and NBP bank sort-code prefixes for stamp-duty refunds.
- **How to build:** Static curated JSON fixtures derived from Polish statutory acts (exempt from copyright under Art. 4 Polish Copyright Act) + RapidFuzz (`MIT`) trigger matching; outputs both `dictionaryName` binding and a `proposed_dictionaries[]` sidecar artifact.
- **Scoring criterion:** Completeness — explicit bonus for *"proposal of a new dictionary"* (30%), Originality (10%).
- **Effort:** 1.5 h.
- **Risk:** Over-triggering on unrelated forms; require ≥2 domain anchors (e.g., *"rasa"* + *"agresywn"* or statute citation) before binding.

#### 5. National Scale Benchmark & TCO Calculator ("Kalkulator 2 477 Gmin")
- **Pitch (PL):** *Na bazie testu 661 formularzy wyliczamy realny czas i koszt cyfryzacji wszystkich 2 477 polskich gmin bez ani jednego wywołania płatnego API.*
- **What it does:** Instruments batch runs over the 661-form municipal corpus (p50/p95 latency, peak RSS, CPU-seconds per page) and generates an interactive slide/report tab extrapolating on-prem COI cluster requirements and electricity/compute cost to digitize ~150,000 municipal forms nationwide versus manual authoring hours.
- **How to build:** `psutil` (`BSD-3`) + Python `time.perf_counter` telemetry aggregator over batch JSONL output; pure static calculation chart in the frontend.
- **Scoring criterion:** Deployment Potential including cost (20%), Originality (10%).
- **Effort:** 1.5 h.
- **Risk:** Jury will challenge manual review time assumptions; separate *compute cost* (measured) from *official review time* (parameterized slider, e.g., 3 vs. 10 min/form).

#### 6. Document Polyglot, Zip-Bomb, Macro & Angular-XSS Security Gate
- **Pitch (PL):** *Wielowarstwowa brama bezpieczeństwa neutralizuje bomby ZIP, makra VBA, skrypty PDF, formuły Excela i wstrzyknięcia szablonów Angular/Quill.*
- **What it does:** Goes far beyond `MIME == extension`: enforces ZIP decompression ratios and entry counts on `.docx`/`.xlsx`/`.ods`, rejects `vbaProject.bin`/macros, disables XML external entities (`defusedxml`), strips PDF `/JavaScript`/`/OpenAction`/`/Launch`, neutralizes spreadsheet formula prefixes (`=`, `+`, `-`, `@`), and sanitizes all Quill HTML against XSS and Angular `{{...}}` template injection.
- **How to build:** `puremagic` (`MIT`) + custom ZIP-manifest check, `defusedxml` (`PSF`), `nh3` (`MIT`, Rust-backed HTML sanitizer), and regex strip for Angular interpolation tokens.
- **Scoring criterion:** Code Quality (20%), Deployment Potential (20%).
- **Effort:** 2.0 h.
- **Risk:** Over-strict PDF filtering could reject benign forms saved with Adobe AcroForm helper scripts; strip/ignore interactive JS actions with a warning rather than hard-failing clean forms.

#### 7. Paper-Only Boilerplate Shredder with Audit Mapping
- **Pitch (PL):** *Automatycznie wycinamy relikty papieru — rubryki podpisu, PESEL i „wypełnia urząd” — i dokumentujemy, który element mObywatela je zastępuje.*
- **What it does:** Recognizes paper-only blocks (applicant identity duplicated by `MLPZ`/`PESEL`, wet-ink signature boxes, *"miejscowość i data"*, *"adnotacje urzędowe"*, *"wypełnić drukowanymi literami"*) and strips them from the matter pages while logging the exact digital equivalent (e.g., Profil Zaufany signature on `FINISH` page, `MLPZ.name` autofill).
- **How to build:** Layout zone rules (header/footer bands, boxed *"Wypełnia urząd"* tables) + Polish inflection-aware regexes using stem tables; strict scope guard so non-applicant persons (coach, co-owner, witness) are **never** shredded.
- **Scoring criterion:** Completeness (30%), Intuitiveness (20%).
- **Effort:** 2.0 h.
- **Risk:** False absorption of a third party's PESEL/address (e.g., minor athlete in the 16-page sports form); gate absorption strictly to the *applicant* section.

#### 8. 16-Page Mega-Form Splitter & Conditional Router ("Rozdzielacz Wniosków")
- **Pitch (PL):** *Gdy urząd scalił trzy różne wnioski w jeden 16-stronicowy PDF, system wykrywa podwnioski i buduje inteligentnego kreatora albo osobne e-usługi.*
- **What it does:** Detects multi-application bundles (repeated title/signature/attachment blocks, e.g., sports scholarship + award + distinction) and offers two one-click modes: (a) unified e-service with a top-level `RADIO` selector gating mutually exclusive sections via `states[].SHOW` JSONata, or (b) N independent COI JSONs sharing common preamble/metadata.
- **How to build:** Page-level structural segmentation (detecting repeated *"WNIOSEK O..."* headers and signature footers) + namespaced `techName` prefixing (`stypendium_*`, `nagroda_*`, `wyroznienie_*`).
- **Scoring criterion:** Completeness (30%), Originality (10%), Intuitiveness (20%).
- **Effort:** 3.0 h.
- **Risk:** False splitting of a single long form with appendix tables (like the 6-page waste declaration); require repeated applicant/signature/title triad to trigger split mode.

#### 9. Zero-Hallucination Bounding-Box Provenance Sidecar
- **Pitch (PL):** *Każde pole w wygenerowanym JSON-ie pamięta dokładny prostokąt na stronie źródłowej — jedno kliknięcie pokazuje urzędnikowi dowód.*
- **What it does:** Emits a sibling `provenance.json` (never polluting COI's schema) linking every `techName`, label, option, and validation rule to `{page, bbox_norm, source_sha256, rule_id, confidence}`. Clicking any field in the review UI scrolls and highlights the exact source region.
- **How to build:** Carry `(page, x0, y0, x1, y1)` through the entire pipeline into composer metadata; strip into sidecar before serializing COI JSON; render SVG overlay over rasterized page PNG (`pypdfium2`, `Apache-2.0`).
- **Scoring criterion:** Intuitiveness (20%), Originality (10%).
- **Effort:** 2.0 h.
- **Risk:** Legacy `.docx`/`.xlsx` lack exact visual coordinates; for reflowable office formats emit structural provenance (`paragraph_idx`, `table_idx`, `cell_ref: "B14"`).

#### 10. Comb-Box & Micro-Grid Vision Detector for Polish Identifiers
- **Pitch (PL):** *Rozpoznajemy polskie kratki formularzowe po geometrii — 11 kratek to PESEL, 10 to NIP, 26 to numer konta — nawet gdy etykieta jest urwana.*
- **What it does:** Uses vector line geometry (on PDFs) and morphological image analysis (on JPG/PNG scans) to count evenly spaced comb cells, inferring `PESEL` (11), `NIP` (10), `REGON` (9/14), `ZIP_CODE` (2+3 split), `SERIAL_NUMBER_ID_CARD` (3+6), and Polish `NRB/IBAN` (26) — automatically binding COI `validation[]` rules and format hints.
- **How to build:** `pdfplumber` (`MIT`) vertical-tick spacing on vector PDFs; OpenCV (`Apache-2.0`) `MORPH_RECT` kernels + SciPy (`BSD-3`) `find_peaks` autocorrelation on scans.
- **Scoring criterion:** Completeness (30%), Originality (10%).
- **Effort:** 2.5 h.
- **Risk:** Broken scan lines split an 11-box comb into 6+5; add horizontal baseline continuity check and combine with neighbouring label keywords for high confidence.

#### 11. Live JSONata Journey Simulator & Minimal Test-Path Generator
- **Pitch (PL):** *Automatycznie wyliczamy wszystkie ścieżki warunkowe e-usługi i pozwalamy przeklikać je jednym przyciskiem zamiast ręcznie testować kombinacje.*
- **What it does:** Extracts the boolean/enum branching variables from `states[]`, computes a compact covering set of valid user journeys (e.g., *"Osoba fizyczna + Pełnomocnik + Stypendium"*, *"Podmiot gospodarczy + Reprezentant + Nagroda"*), and provides 1-click preset pills in the live e-service previewer that auto-fill valid test personas.
- **How to build:** Extract branch predicates from JSONata AST, run pairwise covering generation in pure Python (~60 lines), export synthetic Polish test fixtures (valid synthetic PESEL/NIP/REGON) to the previewer.
- **Scoring criterion:** Intuitiveness (20%), Completeness (30%).
- **Effort:** 2.5 h.
- **Risk:** Combinatorial explosion on forms with 15+ toggles; cap with pairwise (2-way) interaction sampling rather than Cartesian product.

#### 12. Dual-Mode Person vs. Entity Branch Auto-Inference
- **Pitch (PL):** *System czyta kontekst prawny formularza i włącza tylko te warianty wnioskodawcy ze standardu COI, które faktycznie dopuszcza przepis.*
- **What it does:** Analyses who may legally file (e.g., aggressive-breed dog permits -> natural person; road-lane occupation -> natural person OR business/unit; village hall rental -> person OR NGO/KGW/entity) and prunes impossible COI applicant branches instead of blindly pasting all four combinations.
- **How to build:** Scored cue classifier over title, preamble, and entity fields (`KRS`, `NIP`, `REGON`, *"osoba fizyczna"*, *"przedsiębiorca"*, *"klub sportowy"*, *"właściciel nieruchomości"*) with explicit override toggles in the review UI.
- **Scoring criterion:** Completeness (30%), Intuitiveness (20%).
- **Effort:** 1.5 h.
- **Risk:** Wrongly disabling business mode on an ambiguous form; default to *"both enabled + low-confidence review prompt"* whenever cues are weak.

#### 13. Deterministic Reproducible Builds + CycloneDX Licence-Gate SBOM
- **Pitch (PL):** *Identyczny plik wejściowy zawsze daje bitowo powtarzalny JSON, a automatyczny SBOM gwarantuje zero zależności GPL/LGPL/MPL.*
- **What it does:** Generates deterministic component IDs (UUIDv5 over canonical structural path), canonical key ordering, and ships a CycloneDX 1.6 SBOM + automated CI policy gate that fails the build if any direct or transitive package uses GPL, AGPL, LGPL, or MPL.
- **How to build:** Python `uuid.uuid5` + `cyclonedx-bom` (`Apache-2.0`) + `pip-licenses` (`MIT`) allow-list script in Dockerfile build stage.
- **Scoring criterion:** Code Quality (20%), Deployment Potential (20%).
- **Effort:** 1.5 h.
- **Risk:** Python 3.14 wheel metadata sometimes omits SPDX tags in favour of trove classifiers; parse both `License-Expression` and `Classifier` fields.

#### 14. Smart Attachment & 17 PLN Stamp-Duty Auto-Wirer
- **Pitch (PL):** *Wykrywamy listę załączników, odróżniamy obowiązkowe od warunkowych i automatycznie podpinamy moduł pełnomocnictwa z opłatą skarbową.*
- **What it does:** Parses *"Załączniki:"* bullets, creates typed `FILE_UPLOADER` components with `REQUIRED` where unconditional, detects conditional clauses (*"w przypadku działania przez pełnomocnika"*, *"jeżeli dotyczy"*) and wires `states[].SHOW` JSONata plus COI's standard power-of-attorney & stamp-duty exemption logic.
- **How to build:** Polish conditional marker rules (*"jeżeli"*, *"w przypadku"*, *"gdy"*, *"o ile"*) mapped against existing boolean/radio `techName`s via stem overlap.
- **Scoring criterion:** Completeness (30%), Intuitiveness (20%).
- **Effort:** 2.0 h.
- **Risk:** Unlinked condition (*"jeżeli nieruchomość jest współwłasnością"*) has no preceding checkbox; auto-synthesize a gating `RADIO` (*"Czy dotyczy...?"*) and flag it for reviewer confirmation.

#### 15. WCAG 2.1 AA / Polish Digital Accessibility Act Linter
- **Pitch (PL):** *Zanim formularz trafi na mObywatel, sprawdzamy go pod kątem Ustawy o dostępności cyfrowej: etykiety, nagłówki, linki i kontrast strukturalny.*
- **What it does:** Audits the generated COI JSON against Polish *Ustawa z 4 kwietnia 2019 r. o dostępności cyfrowej*: catches generic radio options without question context, empty labels, skipped heading levels in Quill `TEXT_BLOCK`s, non-descriptive link texts (*"kliknij tutaj"*), and walls of text > 120 words inside `INFO_SECTION`.
- **How to build:** Pure-Python rule engine over the COI JSON + `html.parser` (stdlib) inspection of Quill blocks; emits WCAG criterion codes (`1.3.1`, `2.4.4`, `3.3.2`).
- **Scoring criterion:** Deployment Potential (20%), Intuitiveness (20%), Originality (10%).
- **Effort:** 1.5 h.
- **Risk:** Officials may ignore long warning lists; group into `BLOCKER` (missing label) vs. `ADVISORY` (long text) with 1-click autofix where safe.

#### 16. Plain Polish ("Prosty Język" / FOG-PL) Rewriter Hints
- **Pitch (PL):** *Mierzymy indeks czytelności FOG-PL każdego opisu i podpowiadamy urzędnikowi proste zamienniki zgodne ze standardem KPRM.*
- **What it does:** Computes Polish Pisarek / FOG-PL readability on every label, declaration, and `INFO_SECTION`, highlights *"urzędolisz"* (nominalizations and passive constructions like *"dokonać zwrotu opłaty"* -> *"zwrócić opłatę"*, *"niniejszym wnoszę o wydanie"* -> *"proszę o wydanie"*), and offers 1-click plain-Polish suggestions without silently altering statutory declarations.
- **How to build:** Pure-Python Polish syllable counter + FOG-PL formula + curated offline dictionary of ~250 KPRM *Prosty Język* phrase substitutions; never auto-modifies legal declarations (`CONSENT_SECTION`).
- **Scoring criterion:** Intuitiveness (20%), Originality (10%).
- **Effort:** 2.0 h.
- **Risk:** Modifying legally binding declaration wording breaks administrative validity; hard-lock `CONSENT_SECTION` to read-only advisory mode.

#### 17. Inter-Municipality Golden-Template Clustering ("Wspólny Mianownik Gmin")
- **Pitch (PL):** *Na archiwum 661 formularzy wykrywamy rodziny bliźniaczych wniosków i wyznaczamy jeden szablon bazowy z małą łatką dla danej gminy.*
- **What it does:** Indexes converted Form Briefs using MinHash/LSH over lemmatized field sets, clustering near-duplicate forms across offices (or within a city's departments) and computing a canonical "core template" + minimal per-municipality diff (office name, bank account, local rates).
- **How to build:** `datasketch` (`MIT`) MinHashLSH + set intersection/difference over normalized `FormBrief` field signatures; visualized as cluster cards in the batch view.
- **Scoring criterion:** Deployment Potential (20%), Originality (10%), Completeness — batch helper (30%).
- **Effort:** 2.5 h.
- **Risk:** Two different forms sharing COI's 80% standard boilerplate will look 80% identical if you hash the output JSON! Hash **only the 20% paper-specific Form Brief**.

#### 18. Ministry Amendment Impact Diff ("Analiza Nowelizacji")
- **Pitch (PL):** *Po zmianie ustawy porównujemy starą i nową wersję druku i klasyfikujemy zmiany na bezpieczne oraz łamiące działającą e-usługę.*
- **What it does:** Computes a tree-level semantic diff between two conversions of the same form (v1 vs. v2), classifying edits into `SAFE_COPY_CHANGE`, `ADDITIVE_OPTIONAL`, `BREAKING_VALIDATION_OR_LOGIC`, and `REMOVED_FIELD`, plus flags whether existing JSONata rules or saved drafts are impacted.
- **How to build:** `zss` (`BSD-3`) Zhang-Shasha tree edit distance on `(tab -> section -> component)` trees keyed by normalized lemma similarity + rule classifier.
- **Scoring criterion:** Deployment Potential (20%), Originality (10%).
- **Effort:** 2.5 h.
- **Risk:** If a field moves to a new section and gets slightly renamed, naive diff shows delete+add; match moved nodes via RapidFuzz (`MIT`) label similarity > 0.82 before diffing.

#### 19. AI-Agent & Multiportal RP Tool-Contract Compiler
- **Pitch (PL):** *Z tego samego formularza generujemy gotowy kontrakt narzędzia dla asystentów AI HUB — bez halucynacji i bez scrapowania UI.*
- **What it does:** Compiles the COI JSON into an offline JSON Schema (Draft 2020-12) + tool specification (function name, typed parameters, Polish descriptions, conditional `if/then` dependencies, validation regexes) so COI's future AI HUB voice/chat agents can collect citizen answers deterministically and hand off a valid payload to Generator Formularzy.
- **How to build:** Pure-Python transpiler from COI JSON components + `validation[]` + `states[]` to JSON Schema (`Draft 2020-12`) + OpenAPI/tool JSON; validated offline with `jsonschema` (`MIT`).
- **Scoring criterion:** Originality (10%), Deployment Potential (20%).
- **Effort:** 2.0 h.
- **Risk:** Complex JSONata expressions don't map 1:1 to JSON Schema `if/then`; emit exact schema for simple equality predicates and preserve raw JSONata in `x-coi-visibility` extension.

#### 20. Table Arithmetic & Fee-Formula Extractor ("Kalkulator Opłat")
- **Pitch (PL):** *Rozpoznajemy wzory w tabelach opłat za odpady i pas drogowy, walidujemy typy liczbowe i zapisujemy gotowe wyrażenia JSONata dla przyszłych wersji Generatora.*
- **What it does:** Detects arithmetic patterns in municipal fee tables (waste: `liczba osób × stawka = kwota`, exemptions for `kompostownik`; road lane: `powierzchnia m² × liczba dni × stawka`), assigns `NUMBER` types with unit hints (`m²`, `zł`, `dni`), synthesizes verified JSONata calculation expressions in the report/sidecar, and warns officials where COI's current schema lacks native calculated fields.
- **How to build:** Table header & column-symbol parser (`a × b`, `kol. 3 × kol. 4`, `Razem / Suma`) + unit regexes; dry-run evaluates the extracted JSONata formula in `jsonata-python` (`MIT`) on synthetic inputs.
- **Scoring criterion:** Completeness (30%), Originality (10%).
- **Effort:** 3.0 h.
- **Risk:** Inventing unsupported keys inside COI's JSON could break import; keep formula expressions strictly in the sidecar report and `INFO_SECTION` helper notes unless enabled via experimental flag.

#### 21. Keyboard-First Confidence-Triage Reviewer Workbench
- **Pitch (PL):** *Urzędnik nie czyta 69 pól po kolei — system podsuwa najpierw 4 niepewne miejsca z podglądem wycinka PDF i obsługą skrótów klawiszowych.*
- **What it does:** Sorts review items strictly by lowest confidence and active warnings first, shows a cropped high-res source snippet beside each control, supports `J`/`K` navigation, `A` approve, `D` drop, `E` edit, and tracks live time-to-verify and approval completion percentage.
- **How to build:** Lightweight React/Preact (`MIT`) or vanilla TypeScript + Vite (`MIT`) static bundle served by FastAPI (`MIT`), consuming the provenance sidecar and page thumbnails.
- **Scoring criterion:** Intuitiveness (20%).
- **Effort:** 3.0 h.
- **Risk:** Scope creep into building a full clone of COI's Generator Formularzy; restrict UI strictly to *triage, approve, tweak metadata, and preview*.

#### 22. Semantic Digitalization Quality Index ("Indeks Jakości 0–100")
- **Pitch (PL):** *Jeden syntetyczny wskaźnik 0–100 mówi kierownikowi projektu, czy formularz nadaje się do publikacji, czy wymaga ręcznej korekty.*
- **What it does:** Aggregates five measurable sub-scores into a 0–100 release-gate score: Ink Coverage (30%), Schema & JSONata Health (25%), Standard-Section Alignment (20%), WCAG Accessibility (15%), and Plain Polish Readability (10%), with configurable CI/batch thresholds (e.g., `>=85` green, `70–84` review, `<70` manual).
- **How to build:** Weighted deterministic scorer over linter + coverage + readability outputs; rendered as a compact radar/bar breakdown in UI and batch CSV.
- **Scoring criterion:** Deployment Potential (20%), Intuitiveness (20%).
- **Effort:** 1.0 h.
- **Risk:** Arbitrary weights invite debate; expose exact raw sub-metrics right next to the aggregate score so nothing is a black box.

#### 23. Strict Polish Identity & Bank Check-Digit Harness in Live Previewer
- **Pitch (PL):** *Podgląd e-usługi sprawdza prawdziwe sumy kontrolne PESEL, NIP, REGON, IBAN i serii dowodu — urzędnik testuje walidacje od razu po konwersji.*
- **What it does:** Runs full offline algorithmic check-digit validators (PESEL century-encoded date + gender + checksum, NIP weights, REGON 9/14, Polish 26-digit NRB/IBAN mod-97, ID card 3-letter+6-digit weighted checksum, ePUAP/ADE syntax) directly inside the live form previewer and backend test runner.
- **How to build:** Pure TypeScript (`MIT`) + Python mirror (~180 lines total, zero external libraries) with unit tests covering edge cases (2000s PESEL months `+20`, 14-digit REGON).
- **Scoring criterion:** Completeness — field validations (30%), Intuitiveness (20%).
- **Effort:** 1.5 h.
- **Risk:** Officials testing with fake numbers like `11111111111` get blocked if they don't know valid test numbers; add a *"Wstaw poprawne dane testowe"* button in the previewer.

#### 24. Printable Administrative Sign-Off Sheet ("Karta Zgodności Urzędnika")
- **Pitch (PL):** *Generujemy jednostronicową kartę zgodności papier–cyfra gotową do podpisu sekretarza gminy lub radcy prawnego.*
- **What it does:** Exports a clean, printable HTML/PDF-print view mapping every section of the paper form to its electronic tab/section, listing stripped paper artifacts, legal citations, active dictionaries, and quality score — fitting directly into Polish municipal approval workflows.
- **How to build:** Jinja2 (`BSD-3`) server-rendered print-CSS HTML template (`@media print`) — zero headless browser or PDF generator bloat required.
- **Scoring criterion:** Intuitiveness (20%), Deployment Potential (20%), Originality (10%).
- **Effort:** 1.5 h.
- **Risk:** None significant; keep strictly to 1–2 printable pages so it looks executive, not like a debug dump.

#### 25. RODO / GDPR Notice Deduplicator & IOD Contact Extractor
- **Pitch (PL):** *Odsiewamy powtarzalną klauzulę RODO pokrytą przez mObywatel, zachowując unikalne dane administratora i kontakt do IOD danej gminy.*
- **What it does:** Detects Art. 13 RODO blocks via structural legal n-grams (*"administrator danych"*, *"inspektor ochrony danych"*, *"Prezes UODO"*), flags standard legal boilerplate as collapsible `INFO_SECTION` (avoiding 2-page scroll walls), and specifically extracts the municipality's IOD email/address so local legal obligations are never lost.
- **How to build:** Block-level n-gram detector + email/address extraction + Polish regexes; emits `rodo_extracted` summary in the brief.
- **Scoring criterion:** Completeness (30%), Intuitiveness (20%).
- **Effort:** 1.5 h.
- **Risk:** Legal teams are cautious about trimming RODO text; collapse it cleanly into a single dedicated `INFO_SECTION` rather than deleting it outright.

#### 26. Legal Citation Normalizer & ELI Linker
- **Pitch (PL):** *Automatycznie wyłapujemy podstawy prawne z formularza i zamieniamy je w ustandaryzowane identyfikatory ELI Dziennika Ustaw.*
- **What it does:** Extracts Polish statutory references (*"ustawa z dnia 16 listopada 2006 r. o opłacie skarbowej"*, *"Dz.U. z 2023 r. poz. 2111"*), normalizes them into official Polish ELI tuples (`DU/2023/2111`), displays them in form metadata, and flags pre-2020 consolidated text citations as *"Sprawdź aktualność tekstu jednolitego"*.
- **How to build:** Multi-pattern Polish legal regex parser (~100 lines, pure Python); zero network calls, purely deterministic normalization and age heuristic.
- **Scoring criterion:** Originality (10%), Deployment Potential (20%).
- **Effort:** 1.5 h.
- **Risk:** Local council resolutions (*"Uchwała Rady Gminy nr..."*) shouldn't be mislabelled as `Dz.U.`; classify separately as `AKT_PRAWA_MIEJSCOWEGO`.

#### 27. Multi-Format Quality Guard ("Wykrywacz Złej Jakości Skanu")
- **Pitch (PL):** *Gdy urząd wrzuci krzywy skan zamiast pliku DOCX, system wylicza jakość OCR i ostrzega, które pola wymagają źródła tekstowego.*
- **What it does:** Measures scan DPI, skew angle, blur variance (Laplacian), OCR token confidence, and Polish diacritic validity; if quality drops below threshold, still outputs best-effort JSON but raises a prominent intake recommendation (*"Wykryto skan 110 DPI ze skośnością 3,2° — zalecane wgranie pliku DOCX/PDF tekstowego"*).
- **How to build:** OpenCV (`Apache-2.0`) Laplacian blur + Hough deskew estimator + RapidOCR (`Apache-2.0`) per-word confidence stats.
- **Scoring criterion:** Intuitiveness (20%), Deployment Potential (20%).
- **Effort:** 1.5 h.
- **Risk:** Deskewing a slightly crooked table helps OCR dramatically; apply automatic deskew (`±8°`) before OCR, not just measurement.

#### 28. Gridster Geometry & Quill Structural Pre-Import Gate
- **Pitch (PL):** *Bramka przedimportowa weryfikuje siatkę angular-gridster2, unikalność slugów i poprawność Quill HTML, chroniąc Generator przed uszkodzonym JSON-em.*
- **What it does:** Validates undocumented runtime invariants of COI's Angular frontend: `x=0, cols=3, rows=1`, zero overlapping/negative `y` coordinates within every `repeatingSectionGrid[]`, strictly valid `flow.links[]` chain ending at the `FINISH` tab, globally unique ASCII-safe `techName` slugs, and valid Quill DOM structure.
- **How to build:** Pure-Python invariant suite run automatically before every HTTP 200 response; returns `gate_passed: true/false` + exact JSONPath pointers for any violation.
- **Scoring criterion:** Code Quality (20%), Completeness (30%).
- **Effort:** 1.5 h.
- **Risk:** Hard-failing the whole conversion on a minor warning blocks the official; split into `FATAL_IMPORT_BREAKERS` (auto-repaired or blocked) and `NON_FATAL_WARNINGS`.

#### 29. Legacy ePUAP / nForms IR Bridge Architecture
- **Pitch (PL):** *Nasz pośredni model „Form Brief” rozdziela odczyt od generatora — dodanie migracji starych wzorów ePUAP/XSD wymaga tylko jednego adaptera.*
- **What it does:** Keeps the 10-question `FormBrief` IR strictly schema-documented and format-agnostic, shipping a clean `BaseReader` protocol + a documented architectural stub showing how legacy ePUAP XML/XSD templates plug directly into the same COI Composer.
- **How to build:** Clean Python `Protocol` + JSON Schema export of `FormBrief` + architectural diagram in `ARCHITECTURE.md` (no speculative half-baked XSD parser).
- **Scoring criterion:** Deployment Potential (20%), Code Quality (20%).
- **Effort:** 1.0 h.
- **Risk:** Don't oversell a stub as a shipped feature; present honestly as *"documented extensibility boundary for COI's ePUAP migration backlog."*

#### 30. Zero-PII Prometheus/JSONL Ops Telemetry Bundle
- **Pitch (PL):** *Gotowe metryki operacyjne bez danych osobowych — COI może wpiąć usługę w monitoring klastra od pierwszego dnia.*
- **What it does:** Exposes `/healthz`, `/readyz`, and `/metrics` (request latency histograms, format distribution, OCR fallback counts, gate failures, quality score buckets) plus structured JSONL audit logs containing SHA-256 file hashes only — zero form content or PII ever written to logs.
- **How to build:** `prometheus-client` (`Apache-2.0`) + `structlog` (`MIT`/`Apache-2.0`) in FastAPI (`MIT`).
- **Scoring criterion:** Code Quality (20%), Deployment Potential (20%).
- **Effort:** 1.0 h.
- **Risk:** Unauthenticated `/metrics` is a security finding in gov-cloud; gate behind configurable auth/internal port flag or bind-address setting.

---

### 2. Top 5 to Build Tonight vs. 3 Deliberately NOT to Build

#### Build First Tonight (Highest Leverage Before 11:00)
1. **#1 COI Dialect Switch & Spec-Errata Generator (1.0 h):** Instant insider credibility. It proves you reverse-engineered their exact export mechanics instead of skimming the task card, and it immunizes you if their live importer expects either the strict schema or the reference-export quirks.
2. **#2 100% Ink-Accounting Coverage Ledger + #9 Provenance Sidecar (combined ~3.5 h):** This is your single strongest differentiator. Every jury member's #1 fear with automated form conversion is *"what did it silently drop on page 4?"* Showing 100% ink accounting with click-to-highlight bounding boxes turns skepticism into trust in 10 seconds.
3. **#3 JSONata Static Analyser + #28 Gridster/Quill Pre-Import Gate (combined ~3.5 h):** COI's `states[]` referencing *page titles* is a landmine. Proving mathematically that every generated JSON has valid `angular-gridster2` geometry, zero dangling JSONata references, and working conditional branches on the 16-page sports form directly dominates Completeness (30%) and Code Quality (20%).
4. **#4 Statutory Dictionaries Pack + #10 Comb-Box Detector (combined ~3.5 h):** Directly nails three judged forms (aggressive dog breeds, stamp-duty refund IBAN, road lane/waste) AND explicitly captures the bonus scoring items (*"proposal of a new dictionary"* and *"field validations"*) with unmistakable Polish e-gov depth.
5. **#6 Polyglot/Macro/Angular-XSS Security Gate + #13 CycloneDX Licence-Gate SBOM (combined ~3.0 h):** A government architect can kill a brilliant prototype in 30 seconds over an AGPL library (`PyMuPDF`!), an XXE bug, or Angular template injection. Making security and licence hygiene airtight locks in Code Quality (20%) and Deployment Potential (20%).

#### Deliberately NOT to Build Tonight
1. **An Offline Legal Statute Repeal / Currency Database:** Scraping or shipping a local corpus of Polish *Dziennik Ustaw* amendments to judge whether a cited statute is repealed is a trap. One false positive (*"this statute is repealed"* when only an amendment updated it) in front of a COI legal/PO juror will wreck your credibility. Extract ELI identifiers cleanly and flag old consolidated texts for human check instead.
2. **A Local Quantized LLM/VLM Fallback (e.g., `llama.cpp` + 7B model):** On 8 CPU cores and 16 GB RAM, a local 7B model blows Docker image size by 4–6 GB, adds 30–90 seconds per page, introduces nondeterministic hallucinations on unseen defence files, and sabotages your Deployment Cost (20%) story. A crisp deterministic rules + CV + OCR pipeline is faster, auditable, reproducible, and cheap at 2,477-municipality scale.
3. **Custom Formula-Execution Extensions Inside COI's JSON:** Waste and road-lane forms have arithmetic tables, and it is tempting to invent custom `"formula": "..."` properties inside COI components. Do not pollute their proprietary schema with unverified keys that could crash Generator Formularzy's deserializer; emit validated JSONata calculation expressions strictly in your report/sidecar and `INFO_SECTION` guidance.

---

### 3. Ten Hard Questions from a Senior COI Architect / PO (and Honest 2-Sentence Answers)

**1. "Our spec and our two reference exports disagree in several places—how do you know your JSON will actually import into Generator Formularzy tomorrow?"**
We mapped all eight discrepancies between the specification and reference exports and exposed them as an explicit, testable dialect profile (`reference_export_compat` by default, switchable to `strict_spec`). Before returning HTTP 200, every output passes our pre-import gate validating schema keys, `angular-gridster2` geometry, `flow.links[]`, and Quill HTML against the chosen profile.

**2. "At the defence we will upload an unseen scanned PDF from a random municipality. What happens when OCR mangles a checkbox or misses a line?"**
Every extracted glyph, line, and checkbox enters our 100% Ink-Accounting Ledger, so anything the parser cannot map or attribute to a standard COI section is surfaced explicitly as an `UNACCOUNTED` bounding box rather than silently dropped. Our confidence-ordered review UI jumps the official straight to those low-confidence regions with the cropped scan beside the field for one-click repair.

**3. "Four-fifths of our e-service is standard COI sections that aren't on the paper. How do you avoid duplicating PESEL and address fields—without accidentally deleting a witness's or coach's data?"**
Our boilerplate shredder absorbs paper identity and address blocks only when they sit inside the scoped *applicant* zone and maps each absorbed box to its exact `MLPZ`/`PESEL` or standard-section counterpart in the audit ledger. Any identity block tagged to a secondary actor—such as a minor athlete, coach, or co-owner—is explicitly protected from absorption and preserved as domain fields.

**4. "You didn't use an LLM at runtime. Won't a rules-first pipeline collapse on the chaotic MS Word layouts municipal officials actually create?"**
Officials' Word forms are visually chaotic, yet legally repetitive: 80% maps to COI's standard skeleton, and the remaining 20% follows strong geometric signals (comb boxes, dotted leaders, tables, Polish legal section headings) that deterministic layout analysis parses reliably in under two seconds. Where layouts are genuinely ambiguous, the pipeline degrades transparently via confidence scores and ink-coverage warnings instead of hallucinating plausible-looking wrong fields.

**5. "You banned GPL, LGPL, and MPL. How on earth are you parsing legacy `.doc` and complex PDFs without LibreOffice or PyMuPDF?"**
For PDFs we combine `pdfplumber`/`pdfminer.six` (MIT) for exact vector geometry with Google's `pypdfium2` (Apache-2.0) for rasterization and `RapidOCR` on ONNX Runtime (Apache-2.0/MIT) for scans. For legacy Word 97–2003 `.doc`, we avoid LibreOffice (MPL-2.0) and `antiword` (GPL) entirely by using either an isolated Apache POI HWPF extractor (Apache-2.0) or pure-Python `olefile` (BSD-2-Clause) stream parsing, verified by our CycloneDX licence gate.

**6. "Our JSONata `states[]` reference page titles, which officials routinely edit in Generator Formularzy. Won't generated conditional logic rot immediately?"**
Our static JSONata analyser parses every condition AST to guarantee zero dangling page-title or `techName` references and tests every generated expression against both `jsonata-python` and the real browser JS `jsonata` engine. Whenever an official renames a tab or field in our review UI, the analyser automatically refactors all dependent JSONata queries before export.

**7. "How does your system cope with the 16-page sports form that merges three separate applications, or the 6-page waste declaration full of tariff matrices?"**
When the segmenter detects multiple complete application triads inside one document, it can either generate a unified wizard gated by a top-level `RADIO` and `states[].SHOW` rules with namespaced `techName`s, or split them into separate COI JSONs. For 2D waste-fee tables, we preserve compound row-and-column headers during flattening into COI's 1-column grid and emit extracted arithmetic formulas in the report sidecar without injecting unsupported keys into COI's schema.

**8. "This container will ingest untrusted Office and PDF files from 2,477 municipalities inside COI's infrastructure. What stops a weaponized file from compromising the pod or injecting XSS into mObywatel?"**
The hardened non-root container processes files strictly in memory or ephemeral tmpfs behind a security gate that checks real file signatures and ZIP-manifest ratios, rejects VBA macros and XXE, neutralizes Excel formulas, and strips PDF active scripts. Every rich-text fragment passes through `nh3` (Rust-backed strict allow-list sanitization) plus Angular `{{...}}` template-token stripping so no executable payload can survive into Quill or mObywatel.

**9. "Ministries amend forms every year. Does an official have to throw away their customized e-service and start over when v2 of a paper form arrives?"**
Our amendment diff engine computes a tree edit distance between v1 and v2 conversions, separating harmless copy edits from breaking field or logic changes while preserving deterministic IDs for unchanged fields. That gives the official a targeted checklist of deltas to patch in Generator Formularzy instead of re-authorizing all 69 components from scratch.

**10. "What is the real TCO and licensing risk if COI adopts this into Multiportal RP and AI HUB next quarter?"**
Every direct and transitive dependency is audited by an automated CycloneDX SBOM gate allowing only permissive non-copyleft licences (MIT, Apache-2.0, BSD, ISC), eliminating legal blockers for government deployment. Because the default pipeline runs on standard CPU nodes with zero per-token API spend, our 661-form benchmark shows nationwide processing of 2,477 municipalities costs negligible on-prem compute while also outputting JSON Schema contracts ready for AI HUB agents.

---

### 4. Harsh Blind Spots & Failure Modes (and the Cheapest Early Test for Each)

| # | Blind Spot / Failure Mode | Why It Will Bite You Tomorrow | Cheapest Early Test (Run Tonight) |
|---|---|---|---|
| **1** | **Legacy `.doc` Licence / Parser Gap** | Banning GPL/LGPL/MPL kills LibreOffice (`MPL-2.0`), `antiword` (`GPL`), and `catdoc` (`GPL`). If `.doc` is a stub or secretly invokes `soffice`, you either crash on a defence `.doc` file or violate the licence constraint. | Save one judged `.docx` (with tables + Polish `ą ć ę ł ń ó ś ź ż`) as Word 97–2003 `.doc`, POST it to your Docker container, and inspect both extracted Polish text and `cyclonedx` licence list. |
| **2** | **Broken PDF `ToUnicode` CMaps (Polish Diacritic Rot)** | Municipal PDFs from legacy Windows print drivers often look sharp visually while `pdfminer.six` extracts `(cid:123)` or garbled `ł`/`ś`/`ć`. Your rules silently miss `"Załączniki"` or `"Opłata"`. | Run a script across all 7 judged forms + 661 archive PDFs checking for `(cid:`, `\ufffd`, or abnormal Polish vowel/diacritic ratio (<1.5% on >2