# Research Brief: COI "Cyfryzacja formularzy" (HackNation 2026)

**Date:** 21 November 2026  
**Scope:** Public intelligence on Centralny Ośrodek Informatyki (COI) form-generation ecosystem, schema forensics, Polish e-government form publishing landscape, public design standards, prior govtech hackathons, and technical evaluation criteria.

---

## TL;DR

* **Generator Formularzy e-Usług** is an official COI product designed to replace legacy ePUAP and nForms form builders, allowing public bodies (especially local governments / JST) to build responsive forms published on `mobywatel.gov.pl` and `gov.pl`, pre-filled from public registers and integrated with e-Doręczenia.
* **Multiportal RP (MPRP)** is a ~186.3M PLN (165.6–165.7M PLN FERC-funded) replacement for the monolithic `gov.pl` / `samorzad.gov.pl` ecosystem (>2,000 sites, >10,000 editors), launching implementation in Autumn 2026 through 2029, with a shared CMS, public-register module, file repository, and **Generator Formularzy**.
* **AI HUB dla administracji publicznej** secured 151M PLN in FERC funding (announced November 2026, running to June 2029) to build a national AI implementation and standardisation centre (building on PLLuM / HIVE AI), complemented by COI's 290M PLN investment in GPU/IT infrastructure for AI Hub and EZD RP SaaS.
* **MLPZ** is the live authentication path `https://serwis.epuap.gov.pl/mlpz/login` used across ePUAP, Profil Zaufany, `mobywatel.gov.pl`, and e-Doręczenia; its exact official acronym expansion is **unverified**.
* **TERYT_DOWODOWY** and **TERYT_4G_DOWODOWY** have no public documentation (**unverified**), though COI's System Rejestrów Państwowych (SRP) uses GUS TERYT (including 4th-level INSPIRE gmina/delegatura codes) for PESEL and RDO (Rejestr Dowodów Osobistych).
* **Schema Forensics:** Distinctive JSON keys (`repeatingSectionGrid`, `consentSectionConfig`, `__userAnswer`, `$repeatingSectionIndex`, `tooltipMessage`+`questionOrder`) return zero public matches on code hosts/package registries, indicating a **COI-proprietary schema** built on open-source UI libraries—notably `angular-gridster2` (which natively uses `x`, `y`, `cols`, `rows`, and `minItemRows`) and Quill/`ngx-quill`.
* **Current Local-Gov Landscape:** Over 14,000 sequential template IDs exist in ePUAP's CRWDE (reaching `2025/12/19/14090` in Dec 2025); municipalities suffer from months-long CRWDE publication waits, XML/XSD skill gaps, and fragmented vendor e-office portals (e.g., eBOI, SEKAP/PeUP, eUrząd).
* **Regulatory & UX Standards:** Public forms must comply with the Digital Accessibility Act (WCAG 2.1 AA + PN-EN 301 549), the updated 2024 Krajowe Ramy Interoperacyjności (KRI), GDPR/RODO consent rules, and Polish plain-language (*prosty język*) guidelines. An official Polish gov.pl design-system rule mandating "one thing per page" is **unverified**.
* **HackNation Precedent:** At HackNation 2025 (6–7 Dec 2025, Bydgoszcz; 1,500+ participants, 16 challenges), COI's challenge *"Prawda w sieci"* (25,000 PLN) was won by team **no signal** with `mZaufanaStrona` (QR-based out-of-band government website verification). At HackNation 2026 (21–22 Nov 2026), COI's *"Cyfryzacja formularzy"* carries a 25,000 PLN top prize.
* **What Evaluators Check First (Inference):** Valid schema/UUID uniqueness, non-overlapping gridster coordinates, syntactically valid JSONata in `states[]`, accurate mapping to `MLPZ`/`PESEL` pre-fill tokens and official validators (`PESEL`, `NIP`, `REGON`, `ADE`, etc.), and clean Quill-safe HTML free of XSS vectors.

---

## 1. COI's "Generator Formularzy", "Multiportal", "AI HUB", "MLPZ", and TERYT Dictionaries

### Generator Formularzy / Generator Formularzy e-Usług
* **Purpose & Scope:** Presented on COI's official portfolio (*Realizacje*, updated 22 June 2026) as an online tool enabling public entities—especially local government units (JST)—to create, edit, and publish mobile-responsive electronic forms on `mobywatel.gov.pl` and in the unified `gov.pl` service catalogue.
* **Replacement of Legacy Tools:** COI explicitly states that Generator Formularzy will replace existing e-form creation tools in **ePUAP** and **nForms**. It integrates with public registers for citizen data auto-fill, with **e-Doręczenia** for delivery, and in the future with EZD (electronic document management) systems.
* **Relation to ePUC & Strategy:** In a March 2025 interview in *ITwiz*, Anna Durmaj (Deputy Director of COI's Digital Channels Department) linked the form generator to the **ePUC (elektroniczna Platforma Usług Cyfrowych)** initiative, designed to let one municipality create a form (e.g., waste fees) and share it as a generic template with other municipalities, with cost-free automated e-Doręczenia dispatch. The *Strategia Cyfryzacji Państwa* (published in *Monitor Polski*, June 2026) lists equipping public bodies with a unified form generator as a core action, tracking digitalisation milestones from 8.1% (2026) to 100% (2035) based on COI data.
* **Production Status & Team:** Generator Formularzy is already live in production alongside `mObywatel.gov.pl`—for example, it appeared in the Ministry of Digital Affairs' 30 December 2025 maintenance notice (`mObywatel.gov.pl / Generator Formularzy`) ahead of the 1 January 2026 e-Doręczenia transition. COI job postings on Pracuj.pl show it is developed internally by COI's **Zespół Rozwoju Aplikacji Webowych (ZRAW)** alongside `gov.pl` and `mObywatel.gov.pl`.
* **Public Tenders (OPZ) & Architecture Specs:** No public procurement tender (OPZ) specifically detailing the internal software architecture of COI's Generator Formularzy was found (**unverified**).

### Multiportal RP (MPRP)
* **Purpose:** A unified replacement for the aging, monolithic Portal RP (`gov.pl` and `samorzad.gov.pl`, built 2018–2020), which currently hosts over 2,000 websites (~1,000 central government and ~300 local government entities) managed by >10,000 editors.
* **Core Components:** According to the Ministry of Digital Affairs (26 October 2026) and FERC project listings, Multiportal RP's deliverables include: the citizen portal, Multiportal CMS, Public Registers Module (*Moduł rejestrów publicznych*), File Repository, **Generator formularzy**, server/network infrastructure, and IT/editorial training. COI leadership also stated it will act as an AI-assisted "citizen dashboard" guiding users through official procedures.
* **Budget & Timeline (2025–2029):** The project assumptions (OZPI) were submitted to the Committee for Digital Affairs (*Komitet do spraw Cyfryzacji*) with consultation closing 9 December 2025. Total project cost is ~186.33M PLN, with >165.6M PLN (reported as 165.6–165.7M PLN) co-financed from FERC. Funding was approved in March 2026, the agreement with CPPC was signed in June 2026, implementation begins in Autumn 2026, and the schedule runs through 2029.

### AI HUB ("AI HUB dla administracji publicznej")
* **Purpose & Governance:** A national hybrid, multi-sector centre for developing, testing, standardising, and scaling AI solutions across central and local public administration. It is led by the Ministry of Digital Affairs in collaboration with NASK-PIB, IDEAS Research Institute, PCSS, AGH Cyfronet, Wrocław University of Science and Technology, Adam Mickiewicz University, MRiT, and MSZ.
* **Architecture & Standards:** AI HUB continues NASK's **HIVE AI** work using Polish **PLLuM** language models for mObywatel and EZD. In a January 2026 PFR interview, COI described AI HUB as setting standards for agentic models and acting as a repository of vetted architectures/models bearing a COI/MC "stamp" for local governments—explicitly noting that **automatic form-filling with personal data (name, surname, PESEL)** is an often-discussed use case currently constrained by legislation rather than technology. Reportedly, the architecture is hybrid: GPU servers in Rządowa Chmura Obliczeniowa (RChO, operated by COI) and academic supercomputing centres (PCSS, Cyfronet, WCSS), with containerised application logic on RChO or MS Azure, Linux OS where possible, API filtering gateways, and red-teaming.
* **Budget & Timeline (2026–2029):** CPPC opened the non-competitive FERC call on 18 February 2026 (deadline 20 May 2026) and awarded **151M PLN** in funding (announced 4–5 November 2026), with project completion scheduled for **June 2029**. Separately, COI announced in January 2026 that it is allocating **290M PLN** to GPU and IT infrastructure for AI Hub and EZD RP SaaS. Post-2029 annual maintenance is estimated at 11–12M PLN/year through 2034.

### What does "MLPZ" stand for?
* **Verified Usage:** `mlpz` appears in the production authentication URL `https://serwis.epuap.gov.pl/mlpz/login` (e.g., with parameters `ORIGIN=EU2_PROD_IAM` or `ORIGIN=nforms_MojeDaneWRDP`), which serves as the login/identity endpoint for ePUAP, Profil Zaufany, `mObywatel.gov.pl`, and e-Doręczenia mailbox activation.
* **Acronym Expansion:** The exact official Polish expansion of `MLPZ` (commonly conjectured as *Moduł Logowania Profilu Zaufanego*) could not be confirmed in any public government or COI document (**unverified**).

### Origin of `TERYT_DOWODOWY` and `TERYT_4G_DOWODOWY`
* **Exact Identifiers:** Neither `TERYT_DOWODOWY` nor `TERYT_4G_DOWODOWY` appears in publicly indexed Polish government documentation or code (**unverified**).
* **Related Verified Context:** COI's **System Rejestrów Państwowych (SRP)**—which integrates PESEL, **RDO (Rejestr Dowodów Osobistych)**, and BUSC—uses GUS's **TERYT** territorial register as its sole external dictionary, imported via a COI-built dictionary application. In SRP's PESEL/RDO model, a *Gmina* (including Warsaw districts and delegaturas of Kraków, Łódź, Poznań, and Wrocław) is defined as an INSPIRE **level-4** administrative unit. *(Inference: `TERYT_DOWODOWY` and `TERYT_4G_DOWODOWY` likely denote SRP/RDO-scoped TERYT dictionaries used for ID-card/authority selection, with `4G` referring to the 4-level/gmina hierarchy—unverified.)*

---

## 2. Open-Source Lineage, Library Signatures, and Import Behaviour

### Is the JSON Format Based on an Open-Source Form Builder?
* **Search Results:** Exact searches across public code hosts and package registries for the schema's distinctive keys (`repeatingSectionGrid`, `consentSectionConfig`, `$repeatingSectionIndex`, `__userAnswer` with JSONata, `questionOrder` + `tooltipMessage`, `techName` + `defaultValueType`) returned **zero matches**.
* **Conclusion:** The JSON schema and form engine are **COI-proprietary** (custom-built in-house rather than a white-labeled open-source form builder like SurveyJS or Form.io), though the frontend clearly composes standard open-source UI libraries.

### Underlying Library Signatures
1. **Grid Layout (`angular-gridster2`):**
   * The item coordinates (`x`, `y`, `rows`, `cols`) and the undocumented export key `minItemRows` match **`angular-gridster2`** (MIT-licensed Angular library by `tiberiuzuld`). Specifically, `angular-gridster2`'s source code checks `item.minItemRows === undefined ? this.$options.minItemRows : item.minItemRows`.
   * This strongly corroborates an **Angular** frontend stack (consistent with COI's existing `moj.gov.pl/nforms/engine/ng/index` Angular engine).
2. **Rich-Text Descriptions (`Quill` / `ngx-quill`):**
   * `ngx-quill` is the standard Angular wrapper for the Quill rich-text editor.
   * **Sanitisation Behaviour (Verified):** Quill's own `dangerouslyPasteHTML` API explicitly warns that Quill does not guarantee client-side XSS protection and that pasted HTML is parsed through Clipboard matchers into Delta ops, which may alter or drop unsupported markup. Furthermore, `ngx-quill` does not automatically apply Angular's `DomSanitizer` unless explicitly configured/enabled. Conversely, when rendered outside the editor via Angular's `[innerHTML]` binding, Angular's built-in `DomSanitizer` strips `<script>`, `javascript:` URLs, inline styles, and unknown attributes.

### Implications for JSON Import Behaviour *(Analyst Inference)*
* **Unknown / Undocumented Keys (`multiLevelTree`, `searchEnabled`, `minItemRows`):** On the Angular frontend (`angular-gridster2`), extra properties on grid items (like `minItemRows`) are either consumed by Gridster's item config or ignored at runtime; however, if the backend uses a strict Java/Spring Jackson DTO (`FAIL_ON_UNKNOWN_PROPERTIES = true`), emitting unexpected keys could reject the entire import. **Safest strategy:** emit only documented keys from the task specification (or keys proven present in valid export samples) and avoid inventing custom keys.
* **ID Formats (`id` UUID):** Since `id` fields are UUIDs and `flow.links[]` reference `source`/`target` IDs, the importer likely validates UUID v4 syntax and referential integrity (broken links or duplicate UUIDs across tabs/questions/options will either crash the renderer or corrupt conditional logic).
* **HTML Sanitising in `description`:** Emit only minimal, Quill-native semantic HTML (`<p>`, `<br>`, `<strong>`, `<em>`, `<ul>`, `<ol>`, `<li>`, `<a href="https://...">`). Avoid inline CSS styles, `<table>`, `<script>`, or event handlers, which will either be stripped by Angular's `DomSanitizer` / backend OWASP sanitizer or mangled by Quill's Delta clipboard matchers.

---

## 3. How Electronic Forms for Local Government Are Published in Poland Today

### Current Publishing Channels
1. **ePUAP & CRWDE (Centralne Repozytorium Wzorów Dokumentów Elektronicznych):**
   * Under Art. 19b of the Act on Informatisation of Entities Performing Public Tasks (17 Feb 2005) and the 2011 PM Regulation, publishing an electronic document template (XML/XSD schema + XSLT visualisation) in **CRWDE** gives it legal force equivalent to publication in the Journal of Laws.
   * ePUAP forms are XML-based applications (historically XForms or XDP) bound to a CRWDE template URL. To publish a new local form, an authority must submit a signed application to the Ministry of Digital Affairs' CRWDE inbox (`/g3c2s09dyd/skrytka`).
2. **`mObywatel.gov.pl`, `nForms`, and `gov.pl` Service Catalogue:**
   * Central services and newer digital forms are published in the `gov.pl` service catalogue and executed via `mObywatel.gov.pl` / `moj.gov.pl/nforms` (and increasingly via COI's new **Generator Formularzy**).
3. **Regional & Commercial Vendor e-Office Platforms:**
   * Many municipalities rely on third-party platforms integrated with ePUAP and/or e-Doręczenia, such as **eBOI (Elektroniczne Biuro Obsługi Interesanta)** by Alfa TV / Elektroniczny Samorząd (serving 1,285 JSTs, offering ~90 interactive forms deliverable via e-Doręczenia), **SEKAP / PeUP** (Silesian regional platform), and **eUrząd** by Rekord SI.

### Known Pain Points & Numbers
* **Template Volume:** Sequential CRWDE template numbers reached **`2025/12/19/14090`** in December 2025 (e.g., for JPK_V7M(3)), indicating **over 14,000 templates** published in CRWDE over its lifetime (the exact number of currently active vs. deprecated local-gov templates is **unverified**).
* **Duplication:** Because early legal frameworks allowed individual local authorities to publish their own templates, CRWDE accumulated many divergent templates for the exact same administrative procedure.
* **Publication Bottlenecks & Skill Gaps:** Supreme Audit Office (NIK) audits highlighted **months-long waiting times** for Ministry of Digital Affairs verification/publication in CRWDE—during which a municipality cannot launch the e-service—as well as complex legal/technical XML requirements that local-government staff lack the skills to build in-house.
* **Costs & Digitisation Time:** Because municipalities outsource ePUAP/CRWDE form creation, commercial providers sell pre-built ePUAP form bundles (referencing existing CRWDE templates) at around **3,000 PLN for 10 forms (250 PLN per additional form)** without modifications, while custom PDF/Word-to-ePUAP+CRWDE digitisation is quoted individually. Official nationwide averages for the time or cost to digitise a single custom form are **unverified**.
* **Fragmentation & Paper Fallback:** Citizens struggle to know which portal to use, and uneven back-office digitisation means some municipalities still print incoming electronic forms into paper workflows.

### Published Plans (2025–2035)
* **e-Doręczenia Transition:** The transition period ended on **1 January 2026**, making e-Doręczenia the default legal channel for electronic correspondence with public authorities, restricting ePUAP to cases explicitly specified by statute.
* **Unified Form Generation & Sharing:** COI's **Generator Formularzy** (embedded in **ePUC** and **Multiportal RP**) will replace ePUAP forms and nForms, enabling municipalities to build accessible forms themselves and reuse shared templates across JSTs.
* **Strategic Target:** The *Strategia Cyfryzacji Państwa* (June 2026) mandates integrating e-services with e-Doręczenia and targets 100% electronic case handling by 2035.

---

## 4. Polish Public Design Standards Applicable to Electronic Forms

### Applicable Legal & Policy Frameworks
1. **Digital Accessibility Act (*Ustawa z dnia 4 kwietnia 2019 r. o dostępności cyfrowej stron internetowych i aplikacji mobilnych podmiotów publicznych*):** Mandates **WCAG 2.1 Level AA** compliance for all public-sector websites and mobile apps, plus clauses 9, 10, and 11 of **PN-EN 301 549 V3.2.1:2021**.
2. **Polish Accessibility Act (*Ustawa z dnia 26 kwietnia 2024 r.*, transposing the European Accessibility Act):** In force since **28 June 2025**; primarily targets private-sector consumer services, but also intersects with public procurement (Art. 100(2) Pzp).
3. **Krajowe Ramy Interoperacyjności (KRI):** Updated by the **Regulation of the Council of Ministers of 21 May 2024 (Dz.U. 2024 poz. 773)**, in force since 23 May 2024. Governs technical data formats (XML, PDF), electronic signatures (XAdES, PAdES), register object models (natural person, entity, spatial object), and information security management (SZBI).
4. **Plain Language (*Prosty język*):** Promoted via the *Deklaracja Prostego Języka* ("Prosto i kropka"), `gov.pl` Digital Accessibility guidelines, and the 11 rules developed by the Pracownia Prostej Polszczyzny (University of Wrocław) for `obywatel.gov.pl`.
5. **Gov.pl / mObywatel Design System:** Public-sector UX practices reference a "Gov Design System" and Multiportal RP's User-Centered Design mandate, though a publicly downloadable gov.pl form design-system specification codifying a "one thing per page" rule is **unverified**.

### Exact Rules That Matter for Form Structure
* **One Thing Per Page / Logical Ordering:**
  * A formal Polish gov.pl rule mandating strict "one thing per page" (as in UK GOV.UK) is **unverified**. However, Polish plain-language rules require putting the most important information first, arranging content in logical order, and using clear headings/subheadings so users always know which section they are in.
* **Grouping (`SECTION` / `<fieldset>` & `<legend>`):**
  * `gov.pl` accessibility guidelines explicitly require grouping related fields (e.g., radio/checkbox options for a single question, or distinct address blocks like residence vs. correspondence address) both visually and programmatically (`<fieldset>` + `<legend>`), so screen readers announce the group context alongside repeated field names like "ulica".
* **Labels (`title`):**
  * Every field must have an unambiguous, programmatically associated label (`<label for/id>`) stating clearly what to enter.
  * **Mandatory fields:** `gov.pl` explicitly states that an asterisk (`*`) alone is **insufficient**; mandatory status should be stated clearly in text/label.
  * Use plain Polish: address the user directly (active voice, personal forms), avoid passive voice, verbal nouns (*rzeczowniki odczasownikowe*), participles, unexplained acronyms, and sentences over 15–20 words.
* **Hints & Format Instructions (`description`, `tooltipMessage`):**
  * If a field requires a specific format (e.g., date as `YYYY-MM-DD`), format instructions and examples must be provided visibly and linked programmatically (e.g., `aria-describedby`, not `aria-labelledby`, which overrides the label).
* **Error Messages & Error Prevention (WCAG 3.3.1, 3.3.3, 3.3.4, 4.1.3):**
  * Generic messages like *"Błąd"* are non-compliant. Errors must identify the specific field in text, explain how to fix it (correction suggestions where safe), and be exposed to screen readers via ARIA live regions.
  * For forms creating legal or financial commitments (typical of official applications), WCAG 3.3.4 requires reversibility, error checking, or a **review/confirmation step before final submission**.
* **Consents & GDPR/RODO (`CONSENT_SECTION`):**
  * Wherever personal data is collected, forms must include explicit GDPR/RODO information clauses and distinct, clearly worded consent checkboxes where legally required.

---

## 5. HackNation 2025, Polish GovTech Hackathons, and Public Form-Digitisation Repositories

### HackNation 2025 & 2026
* **HackNation 2025 (6–7 December 2025, Bydgoszcz):** The first implementation-oriented Polish government hackathon, organised by the Ministry of Digital Affairs, attracting 1,500+ participants who built 430+ prototypes across 16 challenges.
  * **COI's Challenge — *"Prawda w sieci"* (25,000 PLN):** Won by team **no signal** with **`mZaufanaStrona`**, a QR-code widget embedded on government websites that lets an app like mObywatel query a central backend to independently verify the domain, TLS certificate, and security configuration. Finalists included team **Sigmion** (ArgonAuths × Human Colossus).
  * **Other Notable 2025 Winners:** *Ścieżka prawa* (MC + AI Working Group) — **Code Casimir**; *Zgrany budżet* (MC) — **kurki**; *ZUS Accident Notification Tool* — **kanapowcy**; *Dane bez twarzy* (NASK) — **Habanero Code**.
* **HackNation 2026 (21–22 November 2026, Bydgoszcz):** 15 challenges from 14 public-sector partners. COI's challenge **"Cyfryzacja formularzy"** offers a **25,000 PLN** top prize (alongside structurally similar document-to-JSON tasks such as UZP's *"Odwołania2JSON"* at 20,000 PLN).

### Similar Polish GovTech Hackathons
* **HackYeah (Kraków, ~2,000+ participants):** Regularly features Ministry of Digital Affairs, Ministry of Finance, and UKNF tracks. For example, at HackYeah 2024, **KN Solvro** (Wrocław University of Science and Technology) won the AI category by building a tool to navigate and extract information from complex, non-transparent websites.
* **Ministry of Digital Affairs "Nowa strona danych" (2018):** Won by team **SLAVIC** (geolocation/contract data visualisation for `dane.gov.pl`), with **Bill Gates Kids** 2nd (intent-based search) and **Appsilon** 3rd (open-source data validation).

### Public Repositories for Form Digitisation into JSON
While no public repo targets COI's proprietary JSON schema, several open-source projects demonstrate relevant PDF/document-to-JSON-form pipelines:
* **`kamilstanuch/doc2form`** (MIT) — Converts PDF/Word documents into structured form data using Gemini AI and publishes to Google Forms.
* **Optimajet FormEngine AI Form Builder** (MIT) — Generates portable JSON form schemas (for React/FormEngine Core) from screenshots, PDFs, HTML, or prompts.
* **`tstevenson-3000/pdf-form-builder`** — Detects boxes, lines, combs, and date fields in flat PDFs with an optional Claude vision pass and review UI to output fillable AcroForms.
* **`digital-land/form-generator`** (UK MHCLG/DLUHC) — Transforms YAML/schema specs into web forms, PDFs, and JSON payload validators.
* **`MetaConfigurator/meta-configurator`** — Open-source JSON Schema editor and AI-assisted form generator.
* **`surveyjs/survey-pdf` & SurveyJS Creator** — Reference ecosystem for JSON-defined multi-page forms with conditional logic and PDF round-tripping.

---

## 6. What Platform Specialists Will Check First — and What Will Impress Them *(Analyst Inference)*

*(All items in this section are labeled **Analyst Inference** based on the JSON schema in the task context, COI's product architecture, and Polish e-gov standards.)*

### What COI Specialists Will Check First (Pass/Fail Gates)
1. **Importability Without Errors:** Does the JSON import cleanly into Generator Formularzy on the first try? Specifically: valid UUIDs on every `field.id`, `tab`, and `flow.links[]`; exact `MAIN` and `FINISH` tab types; valid `flow.links[]` forming a connected DAG without orphan tabs or cycles.
2. **Grid Geometry Integrity (`angular-gridster2`):** No overlapping `(x, y, cols, rows)` bounding boxes, no out-of-bounds `x + cols` exceeding the grid column limit, and sensible `questionOrder` matching visual top-to-bottom, left-to-right reading order (critical for WCAG keyboard/screen-reader tab order).
3. **Strict Enum & Schema Fidelity:** Exact field `type` values (`TEXT_FIELD`, `DATEPICKER`, `REPEATING_SECTION`, `CONSENT_SECTION`, etc.), exact validator names (`PESEL`, `NIP`, `REGON`, `ZIP_CODE`, `EPUAP`, `ADE`, `SERIAL_NUMBER_ID_CARD`), and unique, clean `techName` identifiers (no spaces/Polish diacritics that break JSONata or downstream XML/EZD mapping).
4. **JSONata Expression Validity in `states[]`:** Every `SHOW` / `READ_ONLY` query must parse cleanly in JSONata, reference existing `tab.title` and `field.techName` values, and correctly use `__userAnswer` (and `$repeatingSectionIndex` inside repeating grids). One broken JSONata string can break form runtime evaluation.
5. **Safe, Clean HTML in `description`:** Minimal Quill-compatible HTML (`<p>`, `<ul>`, `<strong>`) with zero broken tags, inline styles, or XSS payloads.

### What Will Truly Impress COI Specialists (Differentiators)
1. **Smart Pre-Fill Mapping (`EXTERNAL_SYSTEM`):** Automatically recognising citizen identity/address fields on paper forms and wiring `defaultValueType: "EXTERNAL_SYSTEM"` with `MLPZ.*`, `PESEL.*`, and `PESEL_ADDRESS.*` (plus setting `readOnly: true` where legally appropriate) — directly delivering Generator Formularzy's flagship "once-only" value proposition.
2. **Automatic Polish Validator & Dictionary Binding:** Inferring `PESEL`, `NIP`, `REGON`, `ZIP_CODE`, `ADE`, `EPUAP`, `SERIAL_NUMBER_ID_CARD`, and `dictionaryName` (`"Kraje"`, `"TERYT_DOWODOWY"`, `"TERYT_4G_DOWODOWY"`) from Polish field labels and paper-form comb boxes (e.g., 11 boxes → `PESEL`, 10 boxes → `NIP`, `XX-XXX` → `ZIP_CODE`).
3. **True Conditional Logic & Repeating Sections (Not Flat Dumps):** Converting paper instructions like *"Jeśli zaznaczono TAK, wypełnij część B"* into actual `states[]` JSONata rules, and converting multi-row paper tables (e.g., list of children, vehicles, real estate parcels) into `REPEATING_SECTION` with `repeatingSectionGrid[]` instead of 10 hardcoded duplicate rows.
4. **Paper-to-Digital UX & Plain-Language Upgrade:** Splitting dense 4-page paper forms into logical thematic `tabs[]` (ending with a `FINISH` tab), separating RODO/oświadczenia into `CONSENT_SECTION` / `INFO_SECTION`, moving dense footnotes into `tooltipMessage` or `description`, and offering an optional *prosty język* + WCAG 2.1 AA lint/rewrite pass (flagging ambiguous labels or missing format hints).
5. **Deterministic Validation Loop + Human-in-the-Loop Confidence Report:** Running a post-generation validator (JSON Schema + JSONata AST parser + grid overlap checker + link graph checker) that self-repairs errors before returning JSON, and surfacing low-confidence OCR/mapping spots for the municipal clerk to review.

---

## Table of Sources

| Citation | Source / Title (URL if verbatim in source) | What It Supports |
| :--- | :--- | :--- |
|,, | COI — *Generator Formularzy e-Usług* (`coi.gov.pl`) | Purpose of Generator Formularzy, target users (JST), `mobywatel.gov.pl` publishing, register auto-fill, replacement of ePUAP & nForms, e-Doręczenia/EZD integration. |
|,,, | *Strategia Cyfryzacji Państwa* (*Monitor Polski*, June 2026; consultation draft) | Strategic mandate for unified form generator, e-Doręczenia replacing ePUAP, COI digitalisation trajectory 2026–2035 (8.1% → 100%). |
|, | *ITwiz* — "Jak działa system e-Doręczeń w kontakcie z administracją publiczną" (20 Mar 2025) | COI Deputy Director Anna Durmaj on Generator Formularzy, ePUC (elektroniczna Platforma Usług Cyfrowych), cross-municipality form sharing, paper fallback pain points. |
| | Pracuj.pl — COI Product Owner job ad | Generator Formularzy developed by COI's Zespół Rozwoju Aplikacji Webowych (ZRAW) alongside `gov.pl` and `mObywatel.gov.pl`. |
|,,,,, | Gov.pl (MC, KdsC), *testerzy.pl*, *CRN Polska*, PAP/press (2025–2026) | Multiportal RP scope (>2,000 sites, >10,000 editors), components (CMS, Generator formularzy, registers), budget (~186.3M PLN total / 165.6–165.7M PLN FERC), timeline (2025–2029). |
|,,,, | Gov.pl (CPPC), *CRN Polska*, *TELKO.in* (Feb–Nov 2026) | AI HUB dla administracji publicznej: 151M PLN FERC funding, June 2029 end date, consortium partners, PLLuM / HIVE AI continuation. |
| | PFR S.A. — "Start z polskim AI – od pomysłu do wdrożenia #COI" (21 Jan 2026) | COI vision for AI HUB agentic standards, vetted repository for JSTs, and legal barriers to AI auto-filling forms with personal data (PESEL/name). |
|, | *ITwiz* (7 Jan 2026), *TMT.EXPERT* (17 Aug 2026) | COI 290M PLN GPU/IT infrastructure budget for AI Hub & EZD RP SaaS; hybrid RChO/academic GPU/Azure architecture; post-2029 11–12M PLN/yr maintenance. |
|,,, | Gov.pl (WSSE Łódź), Gmina Stare Babice, Gmina Wróblew, NIK | Production usage of `https://serwis.epuap.gov.pl/mlpz/login` across ePUAP, Profil Zaufany, `mObywatel.gov.pl`, and e-Doręczenia. |
|,,,, | Gov.pl (SRP instruction, Portal Interoperacyjności), NIK SRP audit, KRD Rastin 2.0, *Prawo.pl* | SRP integration of PESEL/RDO/BUSC, GUS TERYT as sole external dictionary, INSPIRE level-4 gmina/delegatura codes. |
|,, | `angular-gridster2` docs, UNPKG source, FOSS statement (`https://github.com/tiberiuzuld/angular-gridster2`) | `x`, `y`, `cols`, `rows`, and `minItemRows` item properties in MIT-licensed `angular-gridster2`. |
|,,,,, | Gov.pl (MC, Portal Interoperacyjności), *e-mentor*, *Rzeczpospolita*, Newton ePUAP spec | Legal status of CRWDE (Art. 19b), XML/XForms/XDP ePUAP forms, CRWDE submission procedure, template duplication problem. |
| | Grzegorz Woźniak — *formularze ePUAP dla urzędów* | Commercial pricing for ready-made ePUAP forms (3,000 PLN / 10 forms, 250 PLN each additional) and custom CRWDE workflow. |
| | Ministerstwo Finansów (Gov.pl, 23 Dec 2025) | CRWDE sequential template number `2025/12/19/14090` (>14,000 templates published). |
|,,, | Elektroniczny Samorząd / Alfa TV, Ledziny.pl, Ratusz24 (Rekord SI) | Vendor e-office platforms: eBOI (1,285 JSTs, ~90 forms), SEKAP/PeUP, Rekord SI eUrząd. |
|,,, | Gov.pl (*Prosty język*), KSAP, Fundusze Europejskie, BIP Poznań | Polish plain-language rules (15–20 word sentences, active voice, no verbal nouns/participles, Pracownia Prostej Polszczyzny 11 rules). |
|,,, | Accessibility guides, Wilki Dostępności, Vertes Design | Digital Accessibility Act (4 Apr 2019, WCAG 2.1 AA, PN-EN 301 549 V3.2.1:2021) and Polish Accessibility Act (26 Apr 2024, effective 28 Jun 2025). |
|,,, | Gov.pl, *IT w Administracji*, Inforlex, OSKKO | Updated Krajowe Ramy Interoperacyjności (Dz.U. 2024 poz. 773, effective 23 May 2024), XML/PDF/XAdES/PAdES standards. |
|,,,,,, | Gov.pl (MC), ChallengeRocket, ArgonAuths, *CHIP*, *ITReseller*, *Gazeta Wyborcza* | HackNation 2025 stats & winners (COI *"Prawda w sieci"* won by **no signal** / `mZaufanaStrona`); HackNation 2026 challenge list & prizes (COI *"Cyfryzacja formularzy"*, 25,000 PLN). |
|,,, | Gov.pl (MC), Politechnika Wrocławska, *PurePC*, ngo.pl | HackYeah (KN Solvro 2024 AI win) and MC "Nowa strona danych" (SLAVIC win) comparisons. |
| | Centrum e-Zdrowia OPZ | RODO/GDPR consent and information-clause requirements on public-sector forms. |
|–, | GitHub (`digital-land/form-generator`, `surveyjs/survey-pdf`, `tstevenson-3000/pdf-form-builder`, `kamilstanuch/doc2form`, FormEngine, `MetaConfigurator/meta-configurator`) | Open-source repositories for PDF/document-to-form and JSON-schema form generation. |
|, | Gov.pl (MC, 30 Dec 2025), Prefettura Como | Live `mObywatel.gov.pl / Generator Formularzy` & `nFORMS` maintenance; 1 Jan 2026 e-Doręczenia cutover; Angular URL `moj.gov.pl/nforms/engine/ng/index`. |
|,,, | Quill docs, `ngx-quill` (GitHub/npm), Angular `DomSanitizer` guide | Quill `dangerouslyPasteHTML` XSS warning, Delta matchers, `ngx-quill` sanitisation caveat, Angular `[innerHTML]` stripping. |
| | INFORLEX Freemium (citing NIK audit) | NIK findings on months-long CRWDE verification/publication delays and municipal XML skill gaps. |
|,,,, | Gov.pl (*Dostępność cyfrowa — Formularze*, WCAG 2.1 AA checklist), NAWA | Exact Polish form accessibility rules: `<label for/id>`, required-field text beyond `*`, `aria-describedby` hints, `<fieldset>`/`<legend>` grouping, WCAG 3.3.1/3.3.3/3.3.4/4.1.3 error handling. |

---

## Could Not Verify

1. **Official expansion of the acronym `MLPZ`** (while `https://serwis.epuap.gov.pl/mlpz/login` is verified as the live authentication endpoint, no public document confirmed the exact Polish words behind `MLPZ`).
2. **Exact origin and schema definition of `TERYT_DOWODOWY` and `TERYT_4G_DOWODOWY`** (only SRP's general use of GUS TERYT and INSPIRE level-4 gmina/delegatura codes for PESEL/RDO was verified).
3. **Public procurement tender (OPZ) or published internal architecture specification for COI's Generator Formularzy** (including its backend language/framework and whether its JSON deserializer rejects unknown properties).
4. **Official count of currently active local-government templates in CRWDE** (only the cumulative sequential ID >14,090 as of December 2025 was verified) and **nationwide average time/cost to digitise a single custom municipal form**.
5. **A publicly accessible Polish `gov.pl` Design System rule mandating "one thing per page"** for electronic forms (unlike the UK GOV.UK Design System, no verified public Polish gov.pl guideline with that exact rule was found).
6. **Public GitHub repositories from HackNation 2025 winners (e.g., team `no signal`) or any public repository specifically targeting COI's Generator Formularzy JSON schema.**