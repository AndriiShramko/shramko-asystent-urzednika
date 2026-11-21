# Research report — 21 November 2026

## TL;DR

- No permissively licensed off-the-shelf system reliably converts an unseen **blank Polish form directly into a complete electronic-form JSON definition**. Current document parsers mainly recover text, layout, tables and reading order; blank input-area detection and semantic transformation remain separate tasks. CommonForms is the most directly relevant research dataset, but the released FFDNet weights still have no explicit licence. [148][381]
- Use a **rules-first, multi-representation pipeline**: inspect native PDF widgets and Office structures first, then vector geometry, then raster morphology/OCR, and only then an optional small language model.
- The best permissive core is **PDFBox/pypdf for AcroForms, pdfplumber for lines/rectangles/tables, pypdfium2 for rendering, openpyxl for XLSX, direct ODF XML or a permissive ODS parser, and Tika/POI HWPF for legacy DOC**. [83][833][61][325][74][288]
- For scanned pages, the safest primary OCR is **PP-OCRv5 Latin through PaddleOCR or RapidOCR**, with **Tesseract Polish** as an independent verifier. Both families have permissive Apache-2.0 licensing, and PP-OCRv5 explicitly supports Polish. [47][58][1][12]
- **Docling** is the strongest permissive general layout/table/reading-order component: MIT code, permissively licensed models, CPU operation and Python 3.14 support; its published x86 benchmark averaged about 3.1 seconds/page with OCR and tables. It is not, however, a blank-field detector. [45][666][668]
- Reject **Marker and Surya** under the stated constraints because their current weights use a modified OpenRAIL licence with revenue/use conditions; reject **MinerU** because its current custom licence adds conditions beyond Apache-2.0. [16][696][659]
- For an optional Polish classifier, the cleanest licence choice is **Qwen3 1.7B or Qwen3.5 2B, Apache-2.0**. Phi-4-mini is MIT but less Polish-specialised; PLLuM licences vary; Bielik carries additional terms, including restrictions concerning personal-data processing; Gemma 1–3 uses non-open custom terms. [209][253][225][771][178]
- On a modern eight-core desktop, a Q4 model around 1.5–1.7B should process a 2,000-token prompt in roughly **8–16 seconds** and generate a short classification in another **1–4 seconds**; a 4–5B model is more likely to require **15–40 seconds**. These are hardware-sensitive estimates, not portable guarantees. [747][748]
- Published form benchmarks usually measure **entity/relation F1, key-value F1, object-detection AP and normalized tree-edit distance**. They do not fully measure whether a generated form has correct types, validation and conditional logic. [400][428][372]
- Recommended acceptance metrics are: **field detection F1, type/options/validation accuracy, label similarity, hierarchy nTED, reading-order score, condition behavioural equivalence, source-text coverage and whole-form exact success**.
- Trust should come from **independent OCR agreement, native-versus-rendered agreement, cross-format agreement, complete source-token accounting, schema validation, JSONata differential tests and Polish check-digit validation**. Open-source pieces exist for most individual checks, but not as one integrated form-conversion verifier. [613][534][561][581]

---

# 1. State of the art for blank-form understanding

## 1.1 What “state of the art” currently means

Research normally divides form understanding into at least four different problems:

1. **Form-field detection**: locate and classify input regions.
2. **Form enrichment**: associate those regions with labels and groups.
3. **Document structure analysis**: reading order, tables, sections and hierarchy.
4. **Semantic form generation**: infer field types, options, validation and conditions.

CommonForms explicitly treats blank-field detection as image object detection with three classes—text input, choice button and signature—and distinguishes this from later form enrichment. Its FFDNet-L result is 81.0 AP overall, but it does not by itself generate typed form schemas or conditions. [148][372]

The state of the art is therefore **compositional**, not a single model:

- Native widgets and spreadsheet metadata give the highest-confidence signals.
- Classical geometry is still particularly effective for underlines, dotted leaders, boxes, combs and table cells.
- OCR/layout models provide words, blocks, tables and reading order.
- Graph or spatial rules perform label association.
- A small language model may clean labels or classify ambiguous semantics, but should not invent fields.

Reading-order research increasingly models order as relations or a document graph rather than simply sorting boxes top-to-bottom. Recursive XY-cut remains a useful deterministic baseline for grid-like documents. [106][111]

## 1.2 Open-source comparison

“Polish quality” below means explicit Polish support or published Polish evidence. Where neither was found, it is marked **unverified**.

| Tool | Relevant capability and limitations | Code / weights licence | CPU performance | Polish diacritics | Python 3.14 | Fit for this project |
|---|---|---|---|---|---|---|
| **Docling** | Extracts page layout, tables, reading order and a typed document tree; it does not directly identify visually blank input areas or emit electronic-form rules. [667][670] | MIT code; individual model licences must be checked. Granite-Docling is Apache-2.0. [45][32] | Published benchmark: about 3.1 s/page on x86 CPU with OCR/tables; layout alone averaged 633 ms/page. [666] | Depends on selected OCR backend; PP-OCRv5 provides explicit Polish support. [59][47] | Supported since Docling 2.59.0. [668] | **Recommended** for layout, reading order and tables, not as the only form detector. |
| **Granite-Docling 258M** | Image-to-structured-document VLM integrated with Docling; useful as a second parser, but not specifically trained for empty form widgets. [32] | Apache-2.0 weights. [31][32] | CPU execution is supported; reliable eight-core page latency was **unverified**. [31] | Polish-specific accuracy **unverified**. | Runtime-dependent; Docling supports 3.14. [668] | Optional cross-check, not the primary deterministic path. |
| **SmolDocling 256M** | Small end-to-end document conversion VLM intended to run on laptop CPU; blank-field-schema quality is **unverified**. [44] | Apache-2.0 weights. [44] | Described as laptop-CPU capable; comparable controlled latency **unverified**. [44] | Polish accuracy **unverified**. | **Unverified**. | Experimental second opinion only. |
| **PaddleOCR PP-StructureV3** | Layout parsing, tables and document structure; not a dedicated blank-field detector. [46] | Apache-2.0 code; checked Paddle model cards use Apache-2.0 weights. [58][621] | About 3.74 s/image on an Intel 8350C in the documented lightweight CPU configuration. [46] | Use PP-OCRv5 Latin recognition, which explicitly includes Polish. [47] | Official installation support remained inconsistent: a Python 3.14 request reported wheels only through 3.12, although later repository changes mention 3.14 work; treat as **unverified**. [60][56] | **Recommended OCR/layout alternative**, preferably through ONNX/OpenVINO if Paddle wheels block 3.14. |
| **PP-OCRv5 Latin** | Text detection/recognition; no form semantics. | Apache-2.0 code and weights. [58][621] | Mobile recognizer is about 2M parameters; exact end-to-end eight-core latency is **unverified**. [628] | Explicit Polish support; aggregate Latin-script recognition accuracy reported as 84.7%, not a Polish-only score. [47][634] | See PaddleOCR caveat above. | **Recommended primary OCR**. |
| **docTR** | Two-stage OCR with selectable detectors and recognizers; no native field/section semantics. [681] | Apache-2.0 code; explicit separate licensing for every pretrained checkpoint was **unverified**. [694] | A third-party ONNX benchmark reported about 1.29 s/page for docTR and 0.15–0.57 s/page for optimized OnnxTR variants on an i7-14700K. [687] | Polish-specific model or score **unverified**. | Requires Python 3.11+, but explicit 3.14 testing/wheels **unverified**. [683] | Secondary OCR candidate only after checkpoint audit. |
| **RapidOCR** | Runs Paddle-family OCR through ONNX Runtime/OpenVINO and other backends; no high-level form semantics. [1] | Apache-2.0 code; upstream Paddle weights and converted ONNX files are documented as Apache-2.0. [1] | Designed for CPU ONNX/OpenVINO use; controlled per-page figure **unverified**. | Polish is available by selecting the Paddle Latin model; the bundled default is Chinese/English. [4][47] | **Unverified** for every backend combination. | **Recommended deployment wrapper** around PP-OCRv5. Avoid RapidOCRLite weights unless separately approved because its “lite” weights use modified OpenRAIL terms. [9] |
| **Tesseract 5** | OCR with word/character boxes and confidences; useful as an independent verifier, not a form parser. | Apache-2.0 code; Polish trained data is distributed in the tessdata ecosystem. [12][13] | Roughly 0.5 s/page in one i7-14700K benchmark. [687] | Dedicated `pol` model exists; a 2026 third-party Polish benchmark reported 26.3% aggregate CER over a deliberately mixed test set, so it should not be the only OCR engine. [13][623] | CLI is independent of Python; Python wrapper status is not material. | **Recommended independent OCR cross-check**. |
| **Unstructured** | Partitions PDFs/images/Office files into typed elements; `hi_res` uses layout models and supports tables, but does not produce complete blank-form definitions. [24][828] | Apache-2.0 code; model and optional dependency licences require a deployment-specific audit. [24][829] | Docling’s benchmark measured about 4.2 s/page on x86; `hi_res` is explicitly slower than rule-based `fast`. [666][825] | Depends on OCR backend; Polish quality **unverified**. | Current manifest was reported as `<3.14`; therefore **no** for the examined release. [816] | Not preferred over Docling under Python 3.14. |
| **MinerU** | Strong general PDF-to-Markdown/JSON pipeline with CPU support, but not a dedicated blank-form generator. [651] | Current custom “MinerU Open Source License” adds conditions to Apache-2.0; some default weight repositories lack clear licence tags. [20][659] | CPU supported; older comparative benchmark around 3.3 s/page. [651][666] | Polish-specific score **unverified**. | Current repository declares Python `>=3.11,<3.15`. [659] | **Reject**: custom licence is outside the hard constraint. |
| **Marker** | Converts documents to Markdown/JSON and handles tables/forms imperfectly; complex forms may fail. [860][861] | Apache-2.0 code; current weights use modified AI Pubs OpenRAIL-M with revenue/use conditions. [16] | Current CPU fast mode claims 23.6 pages/s on its benchmark; older pipeline benchmark measured over 16 s/page, so performance is highly mode/version dependent. [861][666] | Claims multilingual capability through Surya; Polish-specific score **unverified**. | Declares Python `>=3.10,<4`, but explicit 3.14 compatibility **unverified**. [861] | **Reject because of weights**, even though code is permissive. |
| **Surya** | OCR, layout, reading order and tables in 90+ languages. [702] | Apache-2.0 code; modified OpenRAIL-M weights with revenue/use restrictions. [696] | CPU is supported, but current controlled page latency **unverified**. [697] | Polish-specific result **unverified**. | Requires Python 3.10+; explicit 3.14 support **unverified**. [697] | **Reject because of weight licence**. |
| **LayoutParser** | Framework and model zoo for document-layout object detection; general models detect text, title, list, table and picture, not blank input fields. [637][638] | Apache-2.0 code; models submitted to its platform are assigned Apache-2.0, but each external dependency still needs auditing. [643] | Detectron2-style CPU inference is possible but usually heavy; comparable eight-core latency **unverified**. | Not an OCR engine; not applicable. | Old package metadata only required Python ≥3.6; actual 3.14 compatibility with Detectron2 is **unverified**. [644] | Useful training framework, but ageing and not turnkey. |
| **pdfplumber** | Exposes characters, words, lines, rectangles and tables with coordinates; excellent for underlines, dotted leaders, boxes and grid reconstruction. AcroForms are accessible through lower-level pdfminer objects rather than a polished form API. [831][833][839] | MIT. [68] | Fast native parsing; no model inference. Exact speed is document-dependent. | Preserves Unicode when the PDF text layer maps glyphs correctly; OCR is not included. | Reported tested on 3.10–3.14. [834] | **Strongly recommended** for vector geometry. |
| **pypdfium2** | Liberal Python binding to PDFium for rendering, text extraction and inspection; use it primarily to make canonical page images. [61][858] | Apache-2.0 or BSD-3-Clause, plus bundled PDFium dependency notices. [62] | Fast native renderer; exact page timing **unverified**. | Rendering is language-independent; text extraction depends on PDF font mappings. | Package metadata accepts Python ≥3.6, but explicit current cp314 wheel coverage **unverified**. [62] | **Recommended renderer**, with dependency notices preserved. |
| **Apache Tika** | Detects and extracts text/metadata from DOC, DOCX, XLSX, ODS, PDF and many other formats; it generally does not reconstruct PDF columns, tables or coordinates. [74][877] | Apache-2.0. [875] | Suitable for inexpensive fallback text extraction; exact speed **unverified**. | Unicode extraction depends on source encoding; no Polish-specific semantic processing. | Python wrapper publishes a 3.14 classifier; Tika itself runs on Java. [75] | **Recommended fallback and format detector**, not layout authority. |
| **Apache PDFBox** | Reads AcroForm fields, renders pages and extracts text; useful for native widgets and PDF-level validation. XFA support is limited. [83][803][804] | Apache-2.0. [79] | Java CPU library without model inference. | Unicode depends on PDF font mappings; not OCR. | Java component; Python 3.14 is irrelevant when run as a sidecar. | **Strongly recommended** for authoritative PDF inspection. |

### Important missing open-source component

CommonForms provides the best directly relevant field-detection training data: about 55,000 documents and more than 450,000 pages, with text, choice and signature annotations. FFDNet-L reports 81.0 AP. [385][372]

However, the released FFDNet model cards did not contain an explicit weight licence as of the examined issue; therefore those weights must be treated as **unverified and unusable for redistribution**. The CommonForms dataset card itself states Apache-2.0. [381][373]

A viable option is to train an in-house detector on the permissively published dataset, but its ability to distinguish Polish conventions, comb fields and office-only regions would need a separate Polish evaluation set.

## 1.3 Commercial reference points

| Commercial product | Relevant capability | Licence / deployment | Polish observations | Comparison value |
|---|---|---|---|---|
| **Adobe Acrobat Prepare Form** | Automatically looks for underlined spaces, empty boxes, checkboxes, radio buttons and adjacent text, then creates and names fields; Adobe warns that manual review is still needed. [137][145][139] | Proprietary desktop product. | Polish-specific accuracy **unverified**. | Best functional reference for static-PDF-to-widget conversion. |
| **Azure Document Intelligence** | Extracts text, tables, selection marks, sections and optional key-value pairs; returns polygons and confidence scores. [118][123][131] | Hosted commercial service; incompatible with fully offline operation. | Polish OCR may be available, but Polish blank-form KVP accuracy **unverified**. | Reference for output richness, confidence and source provenance. |
| **Google Document AI Form Parser** | Extracts KVPs, tables and checkboxes, associating a checkbox with nearby text; Form Parser 2.0 advertises 200+ languages. [163][164] | Hosted commercial service. | Polish is within the broad language claim, but a Polish-specific score is **unverified**. | Reference for label-to-checkbox association and KVP output. |
| **Amazon Textract Forms** | Returns key-value pairs and selection elements such as checkboxes and radio buttons. [89] | Hosted commercial service. | Printed OCR supports Polish, but Forms/KVP extraction is officially limited to English, French, German, Italian, Portuguese and Spanish. [92][97] | Poor Polish form benchmark, though useful as an API-schema reference. |

---

# 2. Legacy and spreadsheet formats without copyleft components

## 2.1 Recommended readers

| Format | Recommended permissive path | Licence | What must be preserved | Main pitfalls |
|---|---|---|---|---|
| Binary Word **`.doc`** | Run **Apache POI HWPF** in a Java sidecar; use **Apache Tika** for format detection and fallback text. HWPF exposes paragraphs, tables, headers, footers, notes, character properties and pictures. [283][290] | Apache-2.0. [286] | Paragraph/table order, runs, section boundaries, headers/footers, text boxes, pictures and field codes. | HWPF remains an early-stage component with limited write support; spacing and pagination are not a faithful Word layout engine. [287][284] |
| **`.doc` alternative** | Experimental permissive projects include `docboss-doc`/Docboss, `unword`, Office Oxide and `legacy-doc`. [342][346][344][349] | MIT, Apache-2.0 or dual MIT/Apache, depending on project. | Use only as a differential parser until a substantial corpus is tested. | Their unseen-form fidelity and long-term maintenance are **unverified**. |
| **`.docx`** | Parse OOXML directly or use Docling/Apache POI XWPF; direct ZIP/XML access is useful for tables, content controls, drawing anchors and styles that convenience APIs may omit. | Docling MIT; POI Apache-2.0. [45][292] | Tables, merged cells, paragraph styles, tab stops, drawing shapes, text boxes, headers/footers and section breaks. | Visual answer lines are often table borders, paragraph borders, tab leaders or drawing objects rather than underscore characters. |
| **`.ods`** | Prefer direct `content.xml`/`styles.xml` processing or a specifically audited permissive reader such as `odsslicer`; the maintained TDF ODF Toolkit is Apache-2.0 but Java-based. [274][305] | MIT for `odsslicer`; Apache-2.0 for ODF Toolkit. | Repeated rows/columns, covered cells, spans, styles, borders, row heights, column widths, validations, print ranges and hidden sheets. | ODS compresses cells using `number-columns-repeated` and `number-rows-repeated`; merged-cell shadows still consume column positions. [327][335] |
| **`.xlsx`** | Use **openpyxl** for structure and optionally Apache POI XSSF as a differential parser. openpyxl exposes merged cells, styles and data validations. [318][325] | MIT for openpyxl; Apache-2.0 for POI. [318][303] | Merges, borders, fills, alignment, widths/heights, hidden rows/columns/sheets, named ranges, validations, formulas, print areas and page setup. | Only the top-left cell of a merged range stores a value; validators are parsed but not enforced; formulas are not recalculated. [324][325][330] |
| **JPG/PNG** | Canonical image decode, orientation correction, binarisation only where beneficial, then PP-OCRv5 plus Tesseract consensus. | Apache-2.0 OCR stack. [58][12] | Original image, normalized image and all coordinate transforms. | Aggressive thresholding can erase dotted leaders, faint boxes and diacritics. |

### Components to avoid

- **antiword**, **catdoc** and **wvWare** are GPL and therefore violate the hard constraint. [350][351][356]
- `python-stdnum` is LGPL and should be avoided under the stated preference even though it supports PESEL, NIP and REGON. [576]
- `odfpy` is dual Apache/GPL according to its repository, but its mixed licence presentation and the desire to avoid licence ambiguity make direct ODF XML processing safer. [281]

## 2.2 Spreadsheet-as-layout interpretation

For XLSX and ODS, do not flatten immediately to a dataframe. Construct a **visual cell graph**:

- A node represents a visible cell or merged range.
- Edges represent adjacency, shared borders and alignment.
- Empty styled cells remain significant because they may be input regions.
- A bordered empty region adjacent to a label is a field candidate.
- A merged text cell spanning several columns is often a heading.
- Repeated similarly bordered rows are likely a repeatable group or table.
- Data-validation lists should become option sets; openpyxl exposes list validators but does not execute them. [325]
- Hidden lists and named ranges may hold option values, so hidden sheets must not be discarded before resolving validation formulas.
- Print area, manual page breaks and repeated print titles should influence generated pages and repeated headers.
- Read both formula text and cached value; openpyxl cannot calculate formulas and `data_only=True` only returns the last cached result. [330][333]
- Preserve the workbook date system because copying date serials between 1900- and 1904-based workbooks can shift dates by four years and one day. [331]

---

# 3. Paper-to-digital translation heuristics

There is no verified, comprehensive published rule set covering all the listed Polish transformations. Published material instead consists of form-design guidance, PDF auto-detection rules and individual research tasks. This section therefore distinguishes **safe deterministic rules** from **semantic suggestions requiring confidence thresholds**.

## 3.1 Proposed rule table

| Source pattern | Recommended electronic representation | Confidence and safeguards | Evidence |
|---|---|---|---|
| A true AcroForm comb or a row of equally spaced character boxes | One string field with `maxLength = number_of_cells`; optionally retain a display mask. | High when `/Comb` and `/MaxLen` exist; otherwise require regular spacing and at least three cells. A PDF comb divides one field into `/MaxLen` character positions. [456][457] | Acrobat and open implementations treat a comb as one text field, not one schema property per box. [501] |
| `dd / mm / rrrr`, postcode or other visibly separated groups | Prefer one semantic date/postcode field, while recording the source sub-box geometry. | Require nearby separators or a known Polish administrative pattern; do not merge arbitrary neighbouring boxes. | Deterministic examples split or identify date runs by separators. [501] |
| `niepotrzebne skreślić` beside two or more textual alternatives | One `radio`/single-choice field with the printed alternatives as options. | High only when the instruction governs one local option group. Keep a source note that the paper action was crossing out alternatives. | Digital-form guidance says one preferred option should use radio buttons, while multiple independent options should use checkboxes. [517] |
| Several choices with `można zaznaczyć więcej niż jedną odpowiedź` or equivalent | Multi-select/checkbox group. | Phrase dictionary plus visual grouping; never infer exclusivity solely from square versus circle shape. | Related controls should be represented as one named group with a legend. [503][513] |
| `miejscowość, data`, document-generation date, or a signature line | Drop from user fields when the digital service supplies authenticated signature/time metadata; record a deliberate-drop reason. | Do not drop if the legal process requires a separately asserted place, date, signer role or handwritten/electronic signature. | Digital signatures carry dates and may make a paper contract location/date redundant, but signature workflows still require process-specific planning. [444][522] |
| `wypełnia urząd`, `część wypełnia organ`, `adnotacje urzędowe` | Exclude from citizen-facing pages or place in a role-restricted administrative section. | Require a strong administrative phrase and a spatially bounded section; retain it in provenance rather than deleting it silently. | Digital form design should model the business process rather than merely reproduce paper. [522] |
| Footnote marker stating that a field applies only in a condition | Convert the footnote into `requiredIf`, `visibleIf` or an optionality rule; retain its original wording as a hint/provenance item. | Only generate executable logic when referenced fields/options can be resolved unambiguously; otherwise emit a hint plus `needs_semantic_review`. | Online forms can use logic pathways and should explicitly distinguish optional questions. [481][485] |
| Formatting examples, accepted documents, units or explanatory parentheses | Field hint, example, input mask or validation message. | Keep essential instructions outside placeholder text; preserve legally significant wording verbatim. | Guidance recommends contextual hint text and warns against using placeholders for essential instructions. [474][482] |
| Bold/larger text followed by several related fields | Section or group heading. | Combine typography, whitespace, shared enclosure and repeated alignment; do not use font size alone. | Accessible form guidance recommends clear logical sections and informative headings. [447] |
| Signature image area | Usually a process action, not a generic text field. | Emit a typed `signature` component only if the target platform supports the required legal signature mode; otherwise emit workflow metadata. | Electronic signatures need separate planning rather than simple text-field substitution. [522] |
| Instructional paragraph before a section | Section introduction or hint, not an input field. | Preserve every token in round-trip accounting. | Good form structure separates information given to users from questions asked of them. [519] |

## 3.2 Label-to-field association

Use a scored bipartite matching graph rather than “nearest text wins”:

\[
S(l,f)=
w_1\,\text{leftAlignment}+
w_2\,\text{aboveAlignment}+
w_3\,\text{distance}+
w_4\,\text{sameCell}+
w_5\,\text{leaderConnection}+
w_6\,\text{semanticCompatibility}
-\text{barrierPenalty}.
\]

Recommended precedence:

1. Native accessibility name, tooltip or widget name.
2. Text within the same spreadsheet/table cell.
3. Label connected by dotted leader or underline.
4. Closest text immediately to the left.
5. Closest line immediately above.
6. Row/column header for empty table cells.
7. Group heading plus local option text for radio/checkbox groups.

Adobe similarly uses adjacent text for underlines, boxes and checkboxes and group labels for radio buttons, but its own guidance acknowledges detection errors and missed fields. [142][139]

## 3.3 Reading order and section rules

- First identify columns, table regions and enclosures.
- Apply recursive XY-cut to ordinary grid-like regions.
- Traverse tables by logical row and column, respecting row/column spans.
- Put section headings before their descendants.
- Treat footnotes as attached children of the nearest referenced field or section.
- Use a directed acyclic order graph and topologically sort it; retain alternative edges when confidence is low.

Recursive XY-cut followed by depth-first traversal is an established deterministic baseline, while newer work models reading order as explicit pairwise relations. [106][111]

---

# 4. Small local language and vision-language models

## 4.1 Licence suitability

“Acceptable” here means suitable for the especially strict requirement that both code and weights be permissively licensed without copyleft or field-of-use terms.

| Family | Small useful variants | Weight licence and restrictions | Polish suitability | Decision |
|---|---|---|---|---|
| **Qwen3 / Qwen3.5** | Qwen3 0.6B, 1.7B, 4B; Qwen3.5 0.8B, 2B, 4B. [209][210] | Apache-2.0 for the cited open-weight models. [209][212] | Multilingual; Polish task accuracy should still be measured on the intended label/type taxonomy. | **Acceptable and recommended**. Start with Qwen3 1.7B or Qwen3.5 2B Q4. |
| **Phi-4 mini** | 3.8B instruction model. [711] | MIT. [253] | General multilingual capability, but Polish administrative classification quality is **unverified**. | **Acceptable**, especially where official ONNX CPU packages are valuable. |
| **PLLuM** | 4B and 12B Apache variants; 8B Llama-derived variants. [228] | Family licences vary among Apache-2.0, CC-BY-NC and Llama 3.1. [224][225] | Polish-focused. | Use **only a specific Apache-2.0 checkpoint** after auditing base-model lineage and every file. Do not approve the family by name. |
| **Bielik v3** | 1.5B and 4.5B. [238] | Model pages state Apache-2.0, but separate Bielik terms add conduct restrictions, including restrictions reported for personal-data processing. [771][772] | Strong Polish focus; the 1.5B technical report shows competitive Polish benchmark results for its size. [787] | **Reject under a literal “open-source without extra restrictions” policy**, unless counsel confirms the additional terms do not govern your use. |
| **Gemma 1–3** | 1B and 4B variants. | Custom Gemma terms require downstream use restrictions to be passed on. [178] | Multilingual quality varies. | **Reject** under the stated definition. |
| **Granite-Docling / SmolDocling** | 258M/256M document VLMs. [32][44] | Apache-2.0. [32][44] | Polish-specific field semantics **unverified**. | Acceptable as document-parser experiments, not as the semantic authority. |

An OSI-approved licence over parameters is necessary but not by itself sufficient to satisfy the full Open Source AI Definition; for this procurement decision, the narrower practical requirement is that the redistributed code and weight artefacts have permissive terms without use restrictions. [773][782]

## 4.2 Estimated CPU latency for a 2,000-token prompt

These estimates assume Q4/INT4 weights, batch one, eight modern x86 CPU cores and a short structured answer of about 50–100 tokens. They are planning ranges, not guaranteed benchmarks.

| Model size | Expected prompt processing | Expected generation | Approximate end-to-end latency | Basis |
|---|---:|---:|---:|---|
| **0.6–0.8B** | 300–1,000 tok/s | 35–100 tok/s | **2–7 s** | Qwen3 0.6B benchmarks range from roughly 328–672 prompt tok/s and about 40–177 generation tok/s depending on CPU and thread count. [747][749] |
| **1.5–2B** | 125–250 tok/s | 18–40 tok/s | **8–16 s** | An eight-thread Qwen3 1.7B result reported 208.7 prompt tok/s and 19.4 generation tok/s. [748] |
| **3.8–5B** | 50–240 tok/s | 4–25 tok/s | **15–40 s** | Qwen3 4B on a Ryzen 7 reported 241 prompt tok/s and 22.8 generation tok/s, while Phi-4-mini official ONNX laptop results were 3.5–4.9 generation tok/s. [747][716] |
| **8–12B** | 20–100 tok/s | 3–10 tok/s | **30–120 s** | CPU speed becomes strongly memory-bandwidth-bound; larger models should not be on the normal conversion path. [720] |

For this task, the model should receive only the extracted label, nearby instructions and a compact candidate list—not a full page image or all 2,000 tokens unless necessary. Constrained output should be a small enum such as:

```json
{
  "cleanLabel": "Numer PESEL",
  "type": "string",
  "semanticType": "pesel",
  "requiredness": "required",
  "confidence": 0.97
}
```

The model must not create coordinates, field counts or legal conditions without supporting source spans.

## 4.3 Runtimes

| Runtime | Licence | Strengths | Python 3.14 | Recommendation |
|---|---|---|---|---|
| **llama.cpp** | MIT. [727] | Broad GGUF support, mature CPU kernels, easy offline packaging and constrained grammar/JSON generation. | `llama-cpp-python` publishes 3.14 support. [726] | Default for Qwen GGUF and reproducible CPU deployment. |
| **ONNX Runtime GenAI** | MIT. [193] | Official optimized Phi ONNX models; CPU, CUDA, DirectML and OpenVINO execution providers. [205] | cp314 wheels exist for the cited release. [193] | Best for Phi or an already validated ONNX export. |
| **OpenVINO GenAI** | Apache-2.0. [195][197] | Strong Intel CPU optimisation and INT4 support; official benchmarks show roughly 20 tokens/s for Phi-4-mini on tested AI-PC CPUs. [712] | Core OpenVINO added Python 3.14 support; verify the matching GenAI wheel. [201] | Preferred on Intel-only deployments after benchmarking against llama.cpp. |

---

# 5. Evaluation

## 5.1 Existing datasets and metrics

| Dataset / benchmark | What it measures | Size / languages | Standard metrics | Relevance and limitation |
|---|---|---|---|---|
| **FUNSD** | OCR, semantic entities—question, answer, header, other—and entity links. [401] | 199 annotated forms, 9,707 entities and 5,304 relations; English. [402] | Entity precision/recall/F1 and relation F1. [401] | Filled/noisy forms rather than blank field generation; dataset use is commonly described as non-commercial research, so audit before training. [404] |
| **XFUND** | Multilingual semantic entity recognition and question-answer relations. | Seven non-English languages—Chinese, Japanese, Spanish, French, Italian, German and Portuguese—plus FUNSD English in common experimental setups; no Polish. [387][394] | Entity F1 and relation/linking F1. [392] | Useful for multilingual transfer but not Polish blank-form widgets. |
| **FormNet benchmarks** | Form information extraction from OCR tokens with structural encoding. [416] | FUNSD, CORD and private Payment data. | Entity F1; FormNet reported 97.28 F1 on CORD. [417] | Tests populated-value extraction, not generation of empty typed fields. |
| **DocLayNet** | Document-layout object detection over 11 classes. [357] | 80,863 pages from six document categories. [360] | COCO mAP at IoU 0.50–0.95. [358] | Good for headings, text, tables and footnotes; no input-widget class. |
| **CommonForms** | Blank form-field object detection: text, choice and signature. [374] | Roughly 55,000 documents and over 450,000 pages; about one-third non-English. [385] | Per-class and overall AP; FFDNet-L reports 81.0 AP. [372] | Most relevant dataset, but no labels/options/validation/conditions, and released weight licence is unresolved. [381] |
| **TreeForm** | End-to-end hierarchical form parsing. | Converts FUNSD/XFUND annotations into form trees. [428] | End-to-end F1 and modified normalized tree-edit distance. [428] | Good conceptual basis for page/section/field hierarchy. |
| **FormStruct-Bench** | Complete hierarchical answer-tree and diagnostic form structure. [115] | 7,000-page multilingual benchmark plus degradation and template annotations. [115] | Schema nTED, value edit similarity and component-level metrics. [431] | Newer and structurally relevant, but licence and availability of all evaluation assets should be separately audited. |
| **Reading-order benchmarks** | Pairwise or sequence order of layout elements. | A recent open subset contains 733 professionally annotated documents and includes form regions. [114] | Pairwise order accuracy/F1 or sequence correlation, depending on benchmark. | Useful for page ordering, not semantic field correctness. |

## 5.2 Recommended compact metric set

Use a fixed unseen-template test split; do not place alternate exports of the same form in both training and test.

| Metric | Definition | Weight in suggested composite |
|---|---|---:|
| **Field detection F1** | Match predicted and reference fields by page and IoU ≥0.5, then compute precision, recall and F1. Report separately for text, choice, comb, table cell and signature/action. | 20% |
| **Field semantic accuracy** | Exact accuracy for type, `required`, repeatability and semantic subtype among spatially matched fields. | 15% |
| **Option-set F1** | Normalized-string set precision/recall/F1 for radio, checkbox and select options; additionally score single-choice versus multi-choice. | 10% |
| **Label score** | One-to-one field matching followed by normalized character similarity or token F1; preserve a separate exact-label rate. | 10% |
| **Hierarchy similarity** | `1 - normalized tree-edit distance` over page → section → group → field trees, following TreeForm/FormStruct principles. [428][431] | 15% |
| **Reading-order score** | Pairwise precedence F1 over matched fields and static blocks. | 5% |
| **Validation accuracy** | Exact or behaviourally equivalent match for datatype, regex, length, numeric range, date range and checksum validator. | 10% |
| **Condition equivalence** | Execute generated and reference conditions over a generated boundary-value test set; score equal visibility/requiredness outcomes. | 10% |
| **Source coverage** | Fraction of normalized source tokens assigned to label, option, hint, static text, metadata or an explicit drop record. | 5% |

Also report, but do not hide inside the composite:

- **Whole-form exact success**: percentage of forms with no missing/extra fields, correct types/options and no failing conditions.
- **Critical error rate**: wrong legal condition, wrong exclusivity, missing required field or incorrectly exposed office-only field.
- **Runtime, peak RAM and container size** on one specified eight-core CPU.
- **Calibration**: error rate by confidence bucket.

Field-level F1 is necessary because document-level accuracy can hide omissions, while normalized tree-edit distance captures structural work that flat F1 ignores. [428][440]

---

# 6. Automated trust and cross-checks

| Cross-check | Recommended implementation | Existing open-source support | Licence / suitability |
|---|---|---|---|
| **Native text vs OCR** | For born-digital PDFs, align native words and OCR words by bounding-box overlap plus normalized Levenshtein similarity. Flag disagreements involving digits, negation or Polish diacritics. | pdfplumber/PDFBox for native text; PP-OCRv5 and Tesseract for OCR. [831][58][12] | Permissive. |
| **Several OCR engines** | Run PP-OCRv5 and Tesseract on uncertain regions; use agreement as confidence, not automatic majority truth. Add docTR only after weight audit. | OCR-D supports n-way line alignment with majority/confidence voting; OCROMORE reported error reduction from ensemble voting. [614][613] | Audit the selected OCR-D modules; OCROMORE is described as Apache-licensed. [613] |
| **Same form in several formats** | Canonicalize each source into semantic blocks and fields, then match by normalized label, option text and relative order. Require agreement for type/options; preserve source-specific geometry separately. | No complete permissive library for this exact cross-format comparison was verified. | **Bespoke component required.** |
| **Round-trip token coverage** | Assign every source token to `label`, `option`, `hint`, `staticText`, `heading`, `metadata`, `officeOnly` or `deliberatelyDropped`; fail if significant unmatched text remains. | General OCR comparison tools can align text at character/word level, but the semantic coverage categories are bespoke. [607][611] | Implement internally under your preferred licence. |
| **Schema validation** | Validate every output with JSON Schema before any semantic tests. Pin schema version and disallow unknown properties. | Python `jsonschema` supports Python 3.14 and is MIT; `fastjsonschema` is BSD-3-Clause and supports 3.14. [534][531] | Recommended. |
| **JSONata syntax and semantics** | Parse each condition, reject dynamic or disallowed functions, then run generated truth-table and boundary test cases. Differentially evaluate with two implementations during CI. | `jsonata-python` is Apache-2.0 and uses the reference tests; `jsonatapy/jsonata-core` is MIT and reports full reference-suite coverage. [561][562] | Recommended, but pin exact JSONata semantics/version. |
| **Condition dependency graph** | Extract field references; reject unknown IDs, self-dependencies and cycles; confirm hidden required fields cannot block submission. | Graph construction is straightforward bespoke code; no form-specific permissive package was verified. | Bespoke. |
| **Polish check digits** | Map labels and masks to PESEL, NIP, REGON, KRS, NRB/IBAN and ID-card validators; test valid, invalid-checksum and wrong-length examples. | `polanon` validates PESEL, NIP, REGON, ID card and IBAN checksums under MIT; `polish-company-utils` covers NIP, REGON, PESEL, NRB/IBAN and tax micro-accounts under MIT. [581][585] | Recommended; independently verify algorithms against statutory examples. |
| **Polish morphology/dictionary** | Lemmatize labels and detect administrative phrases while preserving original orthography. Maintain a small curated domain lexicon for phrases such as `wypełnia urząd`, `niepotrzebne skreślić`, `jeżeli dotyczy` and `należy podać`. | Morfeusz 2 and its SGJP data use BSD-2-Clause; PoliMorf is also BSD-style. [548][550] | Recommended. |
| **Geometry consistency** | Check no field lies outside its page, overlaps a heading unexpectedly, has zero dimensions, duplicates another field or crosses table barriers. | pdfplumber provides exact line/rectangle coordinates; PDFBox supplies widget rectangles. [831][83] | Recommended. |
| **Spreadsheet consistency** | Resolve all merged ranges and validations; ensure a field is not emitted for hidden option-list cells; compare formula and cached-value views. | openpyxl exposes merges and validations but does not calculate formulas or enforce validators. [324][325][330] | Recommended with custom rules. |
| **Render-back check** | Render an HTML preview from generated JSON and compare field/label anchors against the source image; use visual diffs only as a diagnostic because a responsive form should not reproduce paper pixel-for-pixel. | Render-back and text-coverage verification have been used in document-conversion projects. [619] | Bespoke. |

### Confidence policy

Use confidence as an auditable composition rather than a model’s uncalibrated scalar:

```text
field_confidence =
    0.30 native_or_geometry_evidence
  + 0.20 OCR_agreement
  + 0.15 label_association_margin
  + 0.10 parser_cross_agreement
  + 0.10 semantic_rule_strength
  + 0.10 source_coverage
  + 0.05 schema_and_consistency_checks
```

Hard failures should override the score: unresolved field reference, invalid schema, ambiguous exclusivity, missing high-confidence field candidate, or unmatched legally significant text.

---

# Recommended architecture

```text
                         ┌──────────────────────────────┐
Input file ─────────────▶│ MIME/signature identification│
                         └──────────────┬───────────────┘
                                        │
          ┌─────────────────────────────┼───────────────────────────┐
          │                             │                           │
        PDF                         Office/XML                   Image
          │                             │                           │
  PDFBox/pypdf widgets         DOC: POI HWPF/Tika          canonical decode
  pdfplumber text/vectors      DOCX: OOXML/Docling         orientation/deskew
  pypdfium2 render             XLSX: openpyxl              render at fixed DPI
                               ODS: direct ODF XML
          └─────────────────────────────┼───────────────────────────┘
                                        ▼
                        Unified page primitive model
       words • lines • rectangles • cells • styles • widgets • provenance
                                        │
              ┌─────────────────────────┴──────────────────────────┐
              │                                                    │
     Deterministic field candidates                         OCR where needed
 widgets → grids → combs → lines → boxes          PP-OCRv5 + Tesseract check
              └─────────────────────────┬──────────────────────────┘
                                        ▼
                    label/group/section association graph
                                        │
                          Polish semantic rule engine
                                        │
                       optional Qwen 1.7B/2B classifier
                         only for unresolved semantics
                                        │
                             canonical form IR
                                        │
          JSON Schema • JSONata tests • check digits • token coverage
                                        │
                                        ▼
                              final form JSON
```

## Recommended component choices

1. **Base container:** Python 3.14 plus a small Java runtime sidecar for PDFBox, Tika and POI HWPF. Tika’s Python wrapper and Docling advertise Python 3.14 compatibility. [75][668]
2. **PDF native layer:** PDFBox for AcroForm fields and PDF integrity; pdfplumber for coordinate-level text, rules and table geometry; pypdfium2 for canonical rendering. [83][833][61]
3. **Office layer:** openpyxl for XLSX; direct OOXML/ODF processing for features that high-level readers lose; POI HWPF for `.doc`. [325][288]
4. **Layout layer:** Docling with only permissively licensed model assets. Keep its result as one evidence stream, not ground truth. [45][667]
5. **OCR layer:** RapidOCR/OpenVINO or PaddleOCR with PP-OCRv5 Latin, plus Tesseract `pol` on low-confidence regions. [1][47][13]
6. **Field detector:** deterministic native/geometry detector first. Train a small in-house object detector on CommonForms plus a Polish-labelled set only if rules leave unacceptable recall gaps. [374]
7. **Semantic model:** Qwen3 1.7B or Qwen3.5 2B Q4 through llama.cpp; temperature zero, constrained JSON grammar and a fixed taxonomy. [209][727]
8. **Validation:** `jsonschema`, a pinned JSONata implementation plus reference tests, internal dependency-graph checks, MIT Polish identifier validators and Morfeusz/SGJP. [534][561][581][548]
9. **Offline build:** pre-download all weights, language data and fonts; checksum every artefact; disable network access at runtime; generate a software/model bill of materials containing licence, source URL, hash and version.

## Why this architecture should generalise better

- It uses source-native facts before lossy rendering.
- It does not ask an LLM to count boxes or invent coordinates.
- It keeps each inference tied to source spans and geometry.
- It allows independent parsers to disagree visibly.
- It treats deliberate omission as data, enabling complete coverage audits.
- It can abstain locally while still producing a structurally valid partial definition.
- It separates detection quality from semantic interpretation, matching the distinction made by CommonForms between field detection and form enrichment. [148]

---

# Could not verify

| Item | Status |
|---|---|
| A permissively licensed, production-ready open-source tool that directly converts arbitrary blank Polish forms into complete JSON containing fields, options, validation and conditional logic | **unverified** |
| Explicit licence for the released CommonForms FFDNet-S and FFDNet-L weight files | **unverified**; an open issue reports that the model cards and repository lacked an explicit licence. [381] |
| Polish-only OCR accuracy for PP-OCRv5, Docling, docTR, RapidOCR, Surya, Marker, MinerU, Granite-Docling or SmolDocling | **unverified** |
| Reliable Python 3.14 support for Paddle/PaddleOCR, docTR, RapidOCR, LayoutParser, Marker, Surya and every pypdfium2 platform wheel | **unverified** |
| Separate explicit licence statement covering every docTR pretrained checkpoint | **unverified** |
| Exact current model-asset licences for every optional Unstructured `hi_res` configuration | **unverified** |
| A published comprehensive rule set for Polish transformations such as `niepotrzebne skreślić`, `wypełnia urząd`, signature/date removal and footnote-to-condition conversion | **unverified** |
| A public Polish blank-form benchmark covering widgets, labels, sections, options, validation and conditions | **unverified** |
| Comparable eight-core CPU latency for Granite-Docling, SmolDocling, PP-StructureV3, RapidOCR and current Marker/Surya releases on the same Polish form corpus | **unverified** |
| Whether the Apache-labelled PLLuM 4B release is legally independent of every restriction in its stated Gemma-derived lineage | **unverified; legal review required** |
| Whether Bielik’s additional Terms of Use can be disregarded when obtaining weights solely under Apache-2.0 | **unverified; under the conservative interpretation it should be rejected** |
| A maintained permissive cross-format form-agreement library for comparing PDF, DOCX, ODS and XLSX representations of the same form | **unverified** |
| A complete open-source round-trip accounting tool that classifies every source word as label, option, hint, static text or deliberate omission | **unverified** |
| Statutory/legal correctness of automatically dropping every `miejscowość, data` or signature field | **unverified and inherently process-specific** |