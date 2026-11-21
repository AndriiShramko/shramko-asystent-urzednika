# TL;DR

- COI’s **Generator Formularzy e‑Usług** is a state form builder for public bodies—especially local authorities—whose forms will be published on `mobywatel.gov.pl`, pre-filled from public registers and eventually replace the ePUAP and nForms builders. ([COI](https://www.coi.gov.pl/realizacje/rozwoj-cyfrowej-tozsamosci)) [2]
- **Multiportal RP** is the planned replacement for today’s gov.pl estate: a common architecture and CMS covering the main government portal and thousands of public-body sites, with a public-register module, file repository and form generator. Its published budget is PLN 165.66 million. ([Ministry of Digital Affairs](https://redakcja.www.gov.pl/web/cyfryzacja/multiportal-rp-mprp)) [586]
- The published transition model envisaged piloting the new mObywatel service generator, migrating ePUAP services and making mObywatel/e‑Doręczenia the primary channels in **2027**. ([government presentation](https://www.gov.pl/attachment/feee86d3-07f0-4ada-ac5c-de9df6754b80)) [550]
- **AI HUB for public administration** received approval in November 2026: PLN 151 million, with completion planned for 30 June 2029, to provide shared infrastructure, procedures and environments for testing and scaling public-sector AI. ([CPPC](https://www.gov.pl/web/cppc/zakonczenie-oceny-FERC0204IP0100326)) [39]
- I could not verify the expansion of **MLPZ**. “Moduł Logowania Profilem Zaufanym” is a plausible internal expansion but is **unverified**.
- `TERYT_DOWODOWY` and `TERYT_4G_DOWODOWY` appear to be internal COI dictionary identifiers derived from Poland’s TERYT territorial/address register; the meanings of the suffixes are **unverified**. ([Statistics Poland](https://api.stat.gov.pl/Home/TerytApi?lang=en)) [490]
- No public code or package was found containing the distinctive schema combination. The exact `x/y/rows/cols` and `minItemRows` vocabulary is, however, a strong fingerprint of **angular-gridster2**, whereas React Grid Layout uses `w/h`, not `rows/cols`. ([angular-gridster2](https://www.npmjs.com/package/angular-gridster2)) ([React Grid Layout](https://www.npmjs.com/package/react-grid-layout)) [181][195]
- HTML descriptions are compatible with Quill, but HTML alone does not prove Quill; this attribution remains **unverified**. ([Quill API](https://quilljs.com/docs/api)) [165]
- Today, local forms are published through ePUAP/CRWDE, gov.pl/mObywatel catalogues and commercial e-office platforms; CRWDE publication still involves schema, descriptor and stylesheet files plus formal/legal and technical review. ([ePUAP instructions](https://epuap.gov.pl/wps/wcm/connect/50ad409b-ffe3-4715-8e4d-7e3a2fbfad70/Instrukcja+administratora+-+Opublikowanie+wzoru+w+CRD.pdf?MOD=AJPERES)) [209]
- Applicable public-form rules include WCAG 2.1 AA-equivalent statutory requirements, explicit labels, programmatic hint/error associations, text—not colour alone—for errors, review before submission, plain language and active, non-preselected consent. ([accessibility guidance](https://www.gov.pl/web/dostepnosc-cyfrowa/formularze)) ([UODO](https://bip.uodo.gov.pl/pl/701/4467)) [299][381]
- HackNation 2025’s COI challenge, **Prawda w sieci**, was won by **no signal** with *mZaufanaStrona*, a QR-based government-site verification concept. ([GovTech results](https://www.gov.pl/web/govtech/tysiace-pomyslow-24-godziny-i-jeden-cel---usprawnic-panstwo-w-bydgoszczy-zakonczyl-sie-hacknation-2025)) ([project description](https://itreseller.pl/hacknation-2025-czyli-kodowanie-pod-patronatem-ministerstwa-cyfryzacji)) [444][445]
- The first specialist review of imported JSON would be schema/reference integrity, deterministic identifiers, layout collisions, conditional-expression safety, validation semantics, accessibility, sanitisation and register-prefill minimisation; this is an **inference** from the schema and public standards.

---

# 1. Generator Formularzy, Multiportal, AI HUB, MLPZ and TERYT dictionaries

## 1.1 Publicly documented products and timeline

| Product / period | Publicly known purpose, architecture and status |
|---|---|
| **Generator Formularzy e‑Usług** | COI describes it as an online tool with which public bodies—particularly local-government units—can create, edit and publish citizen forms. Forms are to be published on `mobywatel.gov.pl`, be responsive, and obtain pre-fill data from public registers. COI says it will ultimately replace ePUAP and nForms form-creation solutions and integrate with e‑Doręczenia and, later, electronic document-management systems. ([COI product page](https://www.coi.gov.pl/realizacje/rozwoj-cyfrowej-tozsamosci)) [2] |
| **Earlier ePUC framing, 2024–2025** | COI previously presented the generator as one part of the *Elektroniczna Platforma Usług Cyfrowych* ecosystem, alongside `mObywatel.gov.pl`, emphasising interoperable, standardised central and local services and integration with electronic delivery and document-management systems. ([COI ePUC page](https://coi.gov.pl/realizacje/ekosystem-e-uslug)) [79] |
| **Transition to 2027** | A government presentation described a preparation/pilot period for the new mObywatel service generator, followed by gradual migration of services from ePUAP; its target model showed e‑Doręczenia and mObywatel as the main channels and complete ePUAP shutdown in 2027. This is a published plan, not proof that every migration milestone has been achieved. ([government presentation](https://www.gov.pl/attachment/feee86d3-07f0-4ada-ac5c-de9df6754b80)) [550] |
| **Multiportal RP** | The Ministry describes Multiportal as the new `www.gov.pl`: a central ecosystem encompassing the main government portal and thousands of ministry, central-office and local-government sites. Published deliverables are the user portal, common CMS, public-register module, file repository, form generator, server/network infrastructure and editor/IT training. ([Ministry project page](https://redakcja.www.gov.pl/web/cyfryzacja/multiportal-rp-mprp)) [586] |
| **Multiportal architecture** | The official description confirms a uniform architecture and common components. A report based on the project assumptions describes a modular architecture with CMS, task-flow management, repository, administration, service catalogue, communication, APIs and integrations with the National Node, Catalogue of Public Entities and mObywatel; treat that component-level account as secondary reporting rather than a final implementation specification. ([official project page](https://redakcja.www.gov.pl/web/cyfryzacja/multiportal-rp-mprp)) ([project-assumptions report](https://testerzy.pl/baza-wiedzy/artykuly/multiportal-rp-zalozenia-projektu-informatycznego)) [586][582] |
| **Multiportal timeline and finance** | FERC planning documents put the original project window at Q3 2025–Q4 2028. The current official project page gives total cost of PLN 165,662,533.39 and an EU contribution of up to PLN 132,049,605.36, or 79.71%. ([FERC project list](https://rozwojcyfrowy.gov.pl/wp-content/uploads/2025/09/FERC_Lista_projektow_wybor_niekonkurencyjny_01092025.docx)) ([official project page](https://redakcja.www.gov.pl/web/cyfryzacja/multiportal-rp-mprp)) [73][586] |
| **Multiportal public launch statements, 2026** | COI director Daniel Maćkiewicz said work would begin in autumn 2026 and described the product as an AI-supported citizen dashboard that would guide users through government business and give institutions a modern publishing CMS. ([PAP/WNP interview](https://www.wnp.pl/tech/dyrektor-coi-multiportal-rp-pomoze-zalatwiac-sprawy-urzedowe-prace-nad-nim-rusza-jesienia,1067709.html)) [47] |
| **AI HUB, concept stage** | In January 2026 COI described AI HUB as a planned central facility with infrastructure, procedures and a testing sandbox, developed with the Ministry and NASK, particularly for Polish language models such as PLLuM and Bielik. COI also discussed buying GPU servers, with fewer than 500 GPUs envisaged at that point. ([ITwiz interview](https://itwiz.pl/coi-przeznaczy-290-mln-zl-na-rozbudowe-infrastruktury-it-i-gpu/)) [36] |
| **AI HUB, approved project** | On 4 November 2026 CPPC announced approval of the PLN 151 million *AI HUB dla administracji publicznej*. It is to be a collaboration platform for administration, science and technology experts to develop, test, deploy and scale reusable AI solutions; the published completion date is 30 June 2029. ([CPPC decision](https://www.gov.pl/web/cppc/zakonczenie-oceny-FERC0204IP0100326)) [39] |
| **AI HUB operating model** | COI has said it wants the Hub to develop standards for models—especially agentic models—and eventually maintain a repository of verified implementations, architectures, models and datasets carrying COI/Ministry endorsement. ([PFR interview](https://pfr.pl/artykul/start-z-polskim-ai-od-pomyslu-do-wdrozenia-centralny-osrodek-informatyki)) [45] |

The three projects are therefore related but not identical: the **Generator** authors and publishes transactions, **Multiportal** supplies the shared content/service-discovery estate, and **AI HUB** supplies AI infrastructure, standards and reusable solutions. That relationship is an **inference** from their published scopes, not a published system-context diagram. ([Generator](https://www.coi.gov.pl/realizacje/rozwoj-cyfrowej-tozsamosci)) ([Multiportal](https://redakcja.www.gov.pl/web/cyfryzacja/multiportal-rp-mprp)) ([AI HUB](https://www.gov.pl/web/cppc/zakonczenie-oceny-FERC0204IP0100326)) [2][586][39]

## 1.2 Tenders, OPZs, presentations, jobs and press

| Evidence type | Finding |
|---|---|
| **OPZ / tender for the exact form-builder JSON** | **Unverified.** I did not locate a publicly indexed OPZ or contract that defines the supplied JSON schema, its importer or its front-end dependencies. |
| **Multiportal procurement assumptions** | A project-assumptions article reports a modular CMS/API architecture and milestones of information architecture by mid-2026 and system architecture by the end of 2026, but the underlying full OPZ was not recovered in this search. ([report](https://testerzy.pl/baza-wiedzy/artykuly/multiportal-rp-zalozenia-projektu-informatycznego)) [582] |
| **Presentation** | The most consequential located presentation is the government transition deck showing the new mObywatel generator, migration from ePUAP and a 2027 target model. ([presentation](https://www.gov.pl/attachment/feee86d3-07f0-4ada-ac5c-de9df6754b80)) [550] |
| **Job advertisements tied specifically to these components** | **Unverified.** Generic COI recruitment links exist, but I did not find an indexed advertisement that reliably disclosed the Generator’s framework, JSON classes or importer implementation. |
| **Press** | The June 2026 PAP interview supplies the clearest public description of Multiportal as an AI-assisted citizen dashboard and shared CMS. ([WNP/PAP](https://www.wnp.pl/tech/dyrektor-coi-multiportal-rp-pomoze-zalatwiac-sprawy-urzedowe-prace-nad-nim-rusza-jesienia,1067709.html)) [47] |

## 1.3 MLPZ and the dictionary identifiers

| Identifier | Best-supported conclusion |
|---|---|
| `MLPZ` | The expansion is **unverified**. It clearly behaves in the supplied exports as a logged-in-user identity source, but I found no public COI glossary defining the acronym. “Moduł Logowania Profilem Zaufanym” is a plausible internal expansion, not a verified name. Public sources establish only that Profil Zaufany confirms identity in public systems. ([Profil Zaufany](https://www.gov.pl/web/cyfryzacja/profil-zaufany)) [514] |
| `PESEL` / `PESEL_ADDRESS` | The PESEL register supplies identity data and address-related public-register data; the mObywatel statute permits user-requested retrieval of current data from public registers for a service. ([mObywatel Act text](https://orka.sejm.gov.pl/proc9.nsf/ustawy/3050_u.htm)) [515] |
| `TERYT_DOWODOWY` | The `TERYT` part almost certainly denotes the National Official Register of Territorial Division, which contains TERC territorial units, SIMC localities and ULIC streets. The meaning of `_DOWODOWY` is **unverified** and may be a product/domain-specific projection used in identity-document or address forms. ([Statistics Poland TERYT API](https://api.stat.gov.pl/Home/TerytApi?lang=en)) [490] |
| `TERYT_4G_DOWODOWY` | The source register is likewise probably TERYT, but `4G` and the complete internal dictionary contract are **unverified**. It should not be assumed that `4G` means mobile networking; it may denote a hierarchy/version used by COI. |

---

# 2. Is the JSON based on an open-source builder?

## 2.1 Attribution results

| Candidate / fingerprint | Assessment |
|---|---|
| **A complete open-source product defining the whole schema** | **Not found.** Searches for `repeatingSectionGrid`, `consentSectionConfig`, `__userAnswer`, `$repeatingSectionIndex` and the combined uncommon keys did not identify a public repository or package containing the schema. The safest conclusion is that the domain model is COI/custom or non-public. |
| **angular-gridster2** | **Strongly indicated for the layout layer.** Its serialisable item model uses exactly `x`, `y`, `rows`, `cols`; its interface also contains `minItemRows`. ([npm](https://www.npmjs.com/package/angular-gridster2)) ([older interface showing `minItemRows`](https://www.npmjs.com/package/angular-gridster2/v/4.6.3)) [181][183] |
| **react-grid-layout** | **Less likely.** It uses `x`, `y`, `w`, `h` and an item identifier `i`, not `rows`, `cols` and `minItemRows`. ([npm API](https://www.npmjs.com/package/react-grid-layout)) [195] |
| **Quill** | **Possible but unverified.** Quill can export semantic HTML and many applications persist `root.innerHTML`, but an HTML-valued `description` is not a unique Quill fingerprint. ([Quill API](https://quilljs.com/docs/api)) [165] |
| **JSONata** | The state expressions have JSONata-like path, predicate and `in` syntax, as stated in the task materials, but the exact evaluator/version and allowed function set are **unverified**. |
| **Form.io / SurveyJS / GOV.UK Forms** | No direct schema match was found. Public projects do exist that turn PDFs or images into other form JSON dialects—for example GOV.UK Forms JSON—but not into this COI format. ([GOV.UK form-extractor prototype](https://github.com/timpaul/form-extractor-prototype)) [432] |

The likely architecture is therefore a **custom form domain model layered over commodity UI components**, with angular-gridster2 a plausible layout dependency. This is an **inference**, not proof of the deployed dependency tree.

## 2.2 What follows for importer behaviour?

Nothing definitive follows without the importer’s schema and code. The safe expectations are:

| Issue | Likely behaviour and required test |
|---|---|
| **Unknown properties** | In JSON Schema, extra properties are allowed unless the schema sets `additionalProperties: false`; an application may nevertheless strip them while mapping JSON to typed DTOs. Therefore test separately whether an unknown key is rejected, retained through import/export, or silently dropped. ([JSON Schema object reference](https://json-schema.org/understanding-json-schema/reference/object)) [576] |
| **Undocumented `multiLevelTree`, `searchEnabled`, `minItemRows`** | Their presence in an export does not prove that all import paths accept them. `minItemRows` may be passed directly to Gridster; the other two may be component-specific UI flags. This is **inference**. |
| **IDs** | RFC 9562 UUIDs are 128-bit values. Generate standard textual UUIDs consistently, ensure uniqueness across fields, tabs and flow links, and do not infer that arbitrary strings are accepted merely because JSON itself permits them. ([RFC 9562](https://datatracker.ietf.org/doc/html/rfc9562/)) [563] |
| **Cross-references** | `flow.links[].source/target`, condition paths and repeated-grid references should point to stable objects after import. Whether links use tab IDs, field IDs or another identifier is **unverified** and should be established with a minimal round-trip fixture. |
| **HTML descriptions** | If the front end is Angular, normal `innerHTML` binding sanitises untrusted HTML; bypassing sanitisation is explicitly hazardous. The importer may instead reject, clean or preserve markup before rendering, so submit only a small allowed subset such as paragraphs, lists, emphasis and links until tested. ([Angular security guidance](https://angular.dev/best-practices/security)) [564] |
| **Quill round-trip** | Even if Quill is used, HTML may be normalised when converted into Quill’s Delta representation and exported again. Exact source HTML preservation is therefore **unverified**. ([Quill API](https://quilljs.com/docs/api)) [165] |
| **JSONata expressions** | Treat expressions as code-like input: validate syntax, cap complexity, prohibit unexpected functions if the evaluator allows extensions, and test null/missing/repeating-section values. This is a security **inference**. |
| **Import confidence** | The minimum useful experiment is a “golden” form containing one instance of every field, dictionary, validation, prefill, consent, state and repeating section; export it, alter one feature at a time, import it and diff the resulting export. This is an **inference**. |

---

# 3. How Polish local-government forms are published today

## 3.1 Current channels

| Channel | Publication model and role |
|---|---|
| **ePUAP service and form** | ePUAP is the nationwide communications platform on which central and local bodies can publish electronic services without building an entire platform themselves. Local-government bodies can create local services and central authorities nationwide ones. ([Ministry ePUAP description](https://www.gov.pl/web/cyfryzacja/serwis-epuap)) [542] |
| **CRWDE** | Electronic documents used in administrative proceedings are created from templates published in the Central Repository of Electronic Document Templates. Public authorities submit templates, which undergo formal/legal and technical verification. ([government CRWDE page](https://www.gov.pl/web/ia/centralne-repozytorium-wzorow-dokumentow-elektronicznych)) [214] |
| **Traditional CRWDE package** | Publication requires a request plus, in order, descriptor, schema and stylesheet files, with an optional example document. ([ePUAP publication instructions](https://epuap.gov.pl/wps/wcm/connect/50ad409b-ffe3-4715-8e4d-7e3a2fbfad70/Instrukcja+administratora+-+Opublikowanie+wzoru+w+CRD.pdf?MOD=AJPERES)) [209] |
| **Full ePUAP publication sequence** | The official model requires the electronic-document template in CRWDE, a service description in the service catalogue, and an electronic form on ePUAP or another ICT system that generates the document for electronic submission. ([Ministry guidance](https://www.gov.pl/web/cyfryzacja/rodzaje-uslug-na-epuap)) [223] |
| **gov.pl / mObywatel web catalogue** | `mObywatel.gov.pl` provides a catalogue of matters and service categories, with most listed matters available online; gov.pl remains a discovery and information layer linking to transactional services. ([mObywatel browser guide](https://www.gov.pl/web/mobywatel/mobywatel-w-przegladarce1)) [541] |
| **mObywatel mobile application** | The public service directory listed 37 app services at the time of retrieval. Local authorities can also add local digital documents such as resident or benefit cards. ([mObywatel services](https://info.mobywatel.gov.pl/uslugi)) ([local documents announcement](https://redakcja.www.gov.pl/web/cyfryzacja/nowa-jakosc-cyfrowych-uslug-publicznych--startuje-mobywatel-20)) [544][536] |
| **Commercial e-office / eBOI platforms** | Local authorities also buy portals that provide local forms, payment, case-status and back-office integration, often submitting through ePUAP. Examples include Rekord SI’s eUrząd, Symfonia eFormularze, Madkom SIDAS and eBOI; these examples show a fragmented supplier market, not an exhaustive vendor list. ([Rekord SI](https://www.ratusz24.pl/eurzad)) ([Symfonia](https://symfonia.pl/public/programy/eformularze/)) ([Madkom](https://madkom.pl/cyfrowy-urzad/)) ([eBOI](https://eboi.elektronicznysamorzad.pl/)) [519][520][531][528] |

## 3.2 Numbers, time and cost

| Metric | Verified figure and limitation |
|---|---|
| **CRWDE templates** | No authoritative current aggregate count was located, so the number is **unverified**. Template identifiers reached at least `13829` in August 2025, but identifiers are not proof that 13,829 live, distinct templates existed. ([Ministry list containing CRWDE identifiers](https://www.gov.pl/web/kas/struktury-e-sprawozdan)) [244] |
| **Central service catalogue snapshot** | A Ministry catalogue described 185 citizen-facing services offered by ministries and a separate sheet of 107 ZUS form services; these are catalogue entries, not a count of CRWDE templates or all local services. ([catalogue](https://www.gov.pl/web/cyfryzacja/katalog-cyfrowych-uslug-polskiej-administracji)) [538] |
| **mObywatel app services** | The current public directory showed 37 services. ([mObywatel](https://info.mobywatel.gov.pl/uslugi)) [544] |
| **Cost of a reusable/prebuilt ePUAP form** | One commercial offer prices a minimum pack of ten adapted forms at PLN 3,000 and each further form at PLN 250. This is a supplier price for prebuilt/adapted forms, not the government-wide cost of analysing and digitising a unique complex form. ([supplier offer](https://gwozniak.com.pl/formularze-epuap/)) [227] |
| **Project-scale cost** | A study of municipal digitisation estimated PLN 2.3 million for twenty e-services within a PLN 9.3 million programme; this implies substantial surrounding analysis/integration costs but does not isolate a standard “per form” price. ([municipal digitisation report](https://obserwatorium.miasta.pl/wp-content/uploads/2022/10/Cyfryzacja-urzedow-miast.pdf)) [230] |
| **Time to digitise one unique official form** | **Unverified.** No authoritative Polish government benchmark giving a generally applicable number of hours or days per form was located. |
| **Commercial platform scale** | One supplier advertises roughly 90 ePUAP-compatible interactive forms; another advertises more than 500 public-sector deployments and 5–7-day platform activation. These are vendor claims and do not measure bespoke form digitisation. ([eBOI offer](https://alfatv.pl/elektroniczne-biuro-obslugi-interesanta)) ([eUrząd offer](https://eurzad.com.pl/)) [532][518] |

## 3.3 Known pain points and plans

| Area | Evidence |
|---|---|
| **Fragmentation and duplication** | Research on CRWDE found many different templates for the same procedure because multiple competent authorities could publish their own versions. ([standardisation study](https://www.e-mentor.edu.pl/artykul/index/numer/63/id/1229)) [257] |
| **Long formal path** | A 2022 NIK audit recorded an authority’s explanation that developing and implementing e-services was lengthy because forms had to follow the formal CRWDE approval/publication path. ([NIK report](https://www.nik.gov.pl/kontrole/wyniki-kontroli-nik/pobierz,kap~i_22_002_202205250750281653457828~id5~01,typ,k.pdf)) [258] |
| **Discoverability and reliability** | NIK reported incomplete information and difficulty finding e-services on municipal sites, while earlier audits documented availability and peak-load problems. ([NIK](https://www.nik.gov.pl/aktualnosci/spojnosc-i-infrastruktura/platforma-epuap.html)) ([earlier report](https://redakcja.www.gov.pl/attachment/b9f9bcd0-d7bb-4f7b-a3d7-c227abc0fe65)) [263][254] |
| **Accessibility and inconsistent quality** | COI explicitly positions the new Generator as a way to standardise quality, responsiveness and accessibility and reduce dependence on paid local solutions. ([COI](https://www.coi.gov.pl/realizacje/rozwoj-cyfrowej-tozsamosci)) [2] |
| **Published direction** | The 2035 state digitisation strategy calls for one access point for each user group through mObywatel web/mobile, wider e‑Doręczenia and new forms made with the Generator, supported by user research and usability testing. ([strategy](https://www.gov.pl/web/cyfryzacja/strategia-cyfryzacji-panstwa)) [551] |
| **ePUAP replacement** | The published target is gradual migration of ePUAP e-services to mObywatel’s ecosystem and replacement of ePUAP correspondence by e‑Doręczenia. The earlier deck’s full-closure target was 2027, but current execution status is **unverified**. ([transition deck](https://www.gov.pl/attachment/feee86d3-07f0-4ada-ac5c-de9df6754b80)) [550] |

---

# 4. Applicable public design and legal standards

## 4.1 Standards and exact form rules

| Standard / authority | Rules that matter for this JSON and renderer |
|---|---|
| **Polish Digital Accessibility Act** | Public websites and mobile applications must meet the Act’s accessibility table, equivalent to WCAG 2.1 level AA with limited exceptions, and provide an accessibility declaration. ([government legal summary](https://www.gov.pl/web/dostepnosc-cyfrowa/jakie-akty-prawne-dotycza-dostepnosci-cyfrowej)) [351] |
| **Labels** | Every field must have a comprehensible label/title explaining what to enter and whether it is required. On the web, use a real `<label>` associated through matching `for` and `id`; nearby visual text alone is insufficient. ([general form guidance](https://www.gov.pl/web/dostepnosc-cyfrowa/formularze)) ([web implementation guidance](https://www.gov.pl/web/dostepnosc-cyfrowa/formularze-na-stronach-internetowych)) [299][301] |
| **Hints** | Put the hint in the label or associate separate hint text with the control using `aria-describedby`; required format/length instructions must be available to all users. ([web-form guidance](https://www.gov.pl/web/dostepnosc-cyfrowa/formularze-na-stronach-internetowych)) [301] |
| **Grouping** | Related controls, such as radio buttons answering one question, must be programmatically grouped; the W3C pattern is `<fieldset>` plus `<legend>`. ([Polish web-form guidance](https://www.gov.pl/web/dostepnosc-cyfrowa/formularze-na-stronach-internetowych)) ([W3C forms concepts](https://www.w3.org/WAI/EO/Drafts/tutorials/forms/)) [301][359] |
| **Required versus optional** | Required status must be communicated, not merely shown visually; the native `required` attribute helps assistive technology distinguish required controls. ([web-form guidance](https://www.gov.pl/web/dostepnosc-cyfrowa/formularze-na-stronach-internetowych)) [350] |
| **Error content** | “Error” alone is inadequate. A message must identify the problem and explain how to correct it, in text beside the field and/or in a summary at the start. Colour cannot be the sole indicator. ([form guidance](https://www.gov.pl/web/dostepnosc-cyfrowa/formularze)) [299] |
| **Dynamic errors** | Dynamic error messages or summaries should be exposed to assistive technology—for example with `role="alert"`—so a screen reader announces them. ([web-form guidance](https://www.gov.pl/web/dostepnosc-cyfrowa/formularze-na-stronach-internetowych)) [301] |
| **Review and correction** | Before submission, users should be able to review their entered data, correct it or abandon submission. ([form guidance](https://www.gov.pl/web/dostepnosc-cyfrowa/formularze)) [299] |
| **Plain language** | Start with what matters to the user; use logical order, descriptive headings and lists; address the user directly; avoid passive voice, nominalisations and jargon; explain acronyms; and normally keep sentences to roughly 15–20 words. ([Ministry plain-language guidance](https://www.gov.pl/web/cyfryzacja/prosty-jezyk)) [316] |
| **Consent** | GDPR consent must be freely given, specific, informed and unambiguous, expressed through an affirmative action. Default/pre-ticked consent boxes are impermissible, and distinct purposes should not be hidden in one bundled consent. ([UODO consent guidelines](https://www.uodo.gov.pl/file/3714)) ([UODO default-settings guidance](https://bip.uodo.gov.pl/pl/701/4467)) [384][381] |
| **KRI** | Public ICT systems and registers must comply with KRI’s organisational, semantic and technical interoperability requirements. The current regulation is the Council of Ministers’ regulation of 21 May 2024. ([KRI overview](https://www.gov.pl/web/ia/kri-a-systemy-teleinformatyczne-i-rejestry-publiczne)) ([regulation](https://www.dziennikustaw.gov.pl/DU/2024/773)) [367][362] |

## 4.2 “One thing per page”

I did not find an indexed Polish statutory or gov.pl design-system rule making **one thing per page** mandatory, so its status as a specifically Polish rule is **unverified**. It is, however, a well-established government service-design pattern: GOV.UK recommends starting by splitting a form so each page contains one piece of information, one decision or one question, merging only where user research supports it. ([GOV.UK service manual](https://www.gov.uk/service-manual/design/form-structure)) [334]

For COI’s JSON, a defensible interpretation is therefore:

| Structure | Recommended application |
|---|---|
| `tabs[]` | Use a tab/page for one coherent user task or decision, not automatically one field. This is an **inference** from the one-thing-per-page pattern. |
| `SECTION` | Group closely related inputs with a meaningful heading and programmatic relationship. ([W3C](https://www.w3.org/WAI/EO/Drafts/tutorials/forms/)) [359] |
| `description` / `tooltipMessage` | Put essential instructions visibly next to the field; do not place indispensable information only in a hover tooltip. This is an accessibility **inference** from the requirement that every hint be available to all users. ([gov.pl forms guidance](https://www.gov.pl/web/dostepnosc-cyfrowa/formularze)) [299] |
| `FINISH` | Provide answer review, correction links or controls, legal information where needed, and a clear description of what happens after submission. The review requirement is explicit in the government accessibility guidance. ([gov.pl](https://www.gov.pl/web/dostepnosc-cyfrowa/formularze)) [299] |
| `CONSENT_SECTION` | Separate each genuinely consent-based purpose, default every consent to unchecked and do not use consent when processing rests on a statutory/public-task basis. The last point is a legal-design **inference** requiring case-specific legal review. ([UODO](https://www.uodo.gov.pl/file/3714)) [384] |

---

# 5. HackNation 2025, comparable hackathons and repositories

## 5.1 COI’s HackNation 2025 challenge

| Event / task | Team | What was built | Result / public code |
|---|---|---|---|
| HackNation 2025 — **Prawda w sieci**, commissioned by COI | **no signal** | *mZaufanaStrona*: a widget places a QR code on an official site; scanning it in an mObywatel-style application queries a central backend that independently checks the domain, TLS certificate and security configuration. ([description](https://itreseller.pl/hacknation-2025-czyli-kodowanie-pod-patronatem-ministerstwa-cyfryzacji)) [445] | **Winner.** The official results name no signal as the COI-task winner. A public repository was not located, so repository availability is **unverified**. ([GovTech results](https://www.gov.pl/web/govtech/tysiace-pomyslow-24-godziny-i-jeden-cel---usprawnic-panstwo-w-bydgoszczy-zakonczyl-sie-hacknation-2025)) [444] |
| Same task | **Sigmion**, combining Argonauths and Human Colossus | A cryptographic approach binding trust to information rather than only to a site, intended to authenticate official content even after copying into screenshots, PDFs, print or other channels. ([team account](https://humancolossus.foundation/blog/congrats-to-our-team-)) [458] | One of three finalists. A public repository was not located, so repository availability is **unverified**. ([team account](https://humancolossus.foundation/blog/congrats-to-our-team-)) [443] |
| Same task | Third finalist | **Unverified** | **Unverified** |

HackNation 2025 had more than 1,500 participants, more than 430 submissions and 16 thematic categories according to Sigmion’s account; the official 2026 event publicity similarly stated that 437 projects and 16 winners emerged in 2025. ([Sigmion](https://humancolossus.foundation/blog/congrats-to-our-team-)) ([Bydgoszcz announcement](https://www.bydgoszcz.pl/kategoria/tresc/bydgoszcz-gospodarzem-hacknation/)) [458][429]

## 5.2 Relevant public form-conversion repositories

| Repository | Relevance to the COI challenge |
|---|---|
| [`timpaul/form-extractor-prototype`](https://github.com/timpaul/form-extractor-prototype) | Extracts structure from PDFs or images using Gemini, emits the schema used by GOV.UK Forms and renders a multi-page GOV.UK-style form. It is the closest located public analogue, but does **not** emit COI’s schema. [432] |
| [`lukinov/ai-form-builder`](https://github.com/lukinov/ai-form-builder) | Generates FormEngine JSON and React forms from screenshots, PDFs, HTML or text; useful as a pipeline reference, not a COI-compatible importer. [431] |
| [`surveyjs/ai-form-response-extractor`](https://github.com/surveyjs/ai-form-response-extractor) | Extracts answers from scanned or digital paper forms against an existing SurveyJS definition; it addresses paper/digital response capture rather than converting a blank official form into COI builder configuration. [434] |
| [`umershahzeb02/pdf-to-json`](https://github.com/umershahzeb02/pdf-to-json) | General PDF text/form/OCR extraction into structured JSON, but not COI form JSON. [435] |
| Polish HackNation 2026 form-digitisation repository | **Unverified.** No public repository for the live 21–22 November 2026 COI task was located as of the stated research date. |

---

# 6. What platform specialists would check—and what would impress them

The following is an **inference**, informed by the observed schema, the public product scope and accessibility/security requirements.

## 6.1 First-pass acceptance checks

| Priority | Check | Likely rejection condition |
|---|---|---|
| 1 | **Parse and schema integrity** | Invalid JSON; missing `title`, `tabs` or `flow`; wrong types; unsupported enum values; nulls where arrays are expected. |
| 2 | **ID and reference integrity** | Duplicate/non-UUID field IDs; dangling `flow` endpoints; conditions referring to renamed tabs or `techName`s; unstable IDs between repeated generations. UUID format is standardised by RFC 9562. ([RFC](https://datatracker.ietf.org/doc/html/rfc9562/)) [563] |
| 3 | **Deterministic output** | The same input produces different IDs, ordering, coordinates or technical names without a controlled seed/version. |
| 4 | **Grid validity** | Negative coordinates, zero dimensions, overlaps, content wider than the grid, impractically small controls or desktop-only placement. The `x/y/rows/cols` model matches Gridster’s layout vocabulary. ([angular-gridster2](https://www.npmjs.com/package/angular-gridster2)) [181] |
| 5 | **Reading and focus order** | Visual grid order conflicts with `questionOrder`, DOM order or keyboard focus order. This would make a visually plausible form inaccessible. |
| 6 | **Field semantics** | Text areas used for short codes, free text used where a dictionary exists, checkbox used for exclusive choice, radio used for multi-choice, or date/number data represented as unrestricted text. |
| 7 | **Validation accuracy** | `REQUIRED` added to optional fields; incorrect PESEL/NIP/REGON/ZIP semantics; error messages that say only “invalid”; validation run against hidden/inapplicable questions. Government guidance requires understandable correction instructions. ([gov.pl](https://www.gov.pl/web/dostepnosc-cyfrowa/formularze)) [299] |
| 8 | **Conditions and repeated sections** | Invalid JSONata; ambiguous title matching; references to the wrong repeated row; conditions that hide previously entered data without warning; loops or expensive expressions. |
| 9 | **Prefill provenance and editability** | `MLPZ`, `PESEL` and `PESEL_ADDRESS` mappings point to the wrong attribute; externally sourced data are editable when they should be read-only, or read-only when the user must correct/report discrepancies. |
| 10 | **Dictionary correctness** | Wrong dictionary for the legal field, missing “foreign address” path, mismatched stored code/display label or an undocumented dictionary name unsupported by the target environment. |
| 11 | **Accessibility** | Missing visible labels, essential content only in tooltips, ungrouped radios/checkboxes, colour-only errors, no error summary/focus movement, inaccessible repeating-section controls. ([gov.pl web-form guidance](https://www.gov.pl/web/dostepnosc-cyfrowa/formularze-na-stronach-internetowych)) [301] |
| 12 | **HTML safety** | Scripts, event handlers, unsafe links or unsupported markup in descriptions. Angular recommends sanitising untrusted HTML and avoiding trust-bypass APIs. ([Angular](https://angular.dev/best-practices/security)) [564] |
| 13 | **Consent legality** | Preselected consent, bundled purposes, consent used for mandatory statutory processing, or no record of consent wording/version. UODO rejects pre-ticked defaults. ([UODO](https://bip.uodo.gov.pl/pl/701/4467)) [381] |
| 14 | **Finish and submission path** | No review/correction stage, no confirmation, no description of next steps, or a `flow` graph with dead ends/unreachable pages. Government guidance requires review and correction before sending. ([gov.pl](https://www.gov.pl/web/dostepnosc-cyfrowa/formularze)) [299] |
| 15 | **Round-trip fidelity** | Import succeeds but silently deletes unknown keys, normalises IDs, corrupts HTML, changes grid placement or rewrites expressions. |

## 6.2 What would impress the platform team

| Capability | Why it would stand out |
|---|---|
| **Evidence-linked extraction** | Every generated question points back to page number, bounding box and source text, with a confidence score, so a reviewer can audit rather than trust an opaque LLM. |
| **Deterministic, idempotent generation** | Running the converter twice produces a semantically identical configuration and stable IDs, enabling safe version control and updates. |
| **Legal-semantic transformation** | It does not merely copy the paper layout: it recognises legal alternatives, repeated persons/attachments, conditional branches, required versus optional data and review/consent requirements. |
| **Native register/dictionary mapping** | It proposes `PESEL`, `PESEL_ADDRESS`, MLPZ and TERYT mappings only where justified, distinguishes authoritative read-only values from editable declarations and explains each mapping. |
| **Accessible restructuring** | It converts dense paper pages into coherent steps, related groups, explicit labels/hints and actionable errors rather than reproducing the paper grid. This aligns with Polish accessibility guidance. ([gov.pl](https://www.gov.pl/web/dostepnosc-cyfrowa/formularze)) [299] |
| **Validated condition compiler** | Human-readable rules are compiled into a restricted JSONata subset, statically checked against actual tab/field paths and covered by generated positive/negative tests. |
| **Importer compatibility profile** | The output is validated against a machine-readable COI schema and target-version capability matrix, with unsupported keys flagged rather than guessed. |
| **Golden-form test suite** | The submission includes fixtures for every field type, validation, dictionary, prefill, consent, state, repeated section and flow shape, plus import/export diffs. |
| **Security controls** | HTML allow-listing, formula-injection protection for spreadsheet inputs, archive/decompression limits, malware scanning, OCR/LLM isolation, file-size/page limits and prompt-injection-resistant document processing. |
| **Human-in-the-loop workflow** | Low-confidence or legally ambiguous elements are marked for review; the tool never presents uncertain legal interpretation as final. |
| **Plain-language assistance** | It proposes a source-faithful version and a plain-language alternative, highlights legal terms that cannot safely be simplified and applies the government’s direct-address/short-sentence rules. ([plain-language guidance](https://www.gov.pl/web/cyfryzacja/prosty-jezyk)) [316] |
| **Metrics** | Field-level precision/recall, import success, reviewer correction time, accessibility defects and time saved are measured on a representative Polish-form corpus rather than demonstrated on one favourable PDF. |

---

# Sources

| URL | What it supports |
|---|---|
| https://www.coi.gov.pl/realizacje/rozwoj-cyfrowej-tozsamosci | Generator purpose, target users, mObywatel publication, register prefill, ePUAP/nForms replacement and integrations. |
| https://coi.gov.pl/realizacje/ekosystem-e-uslug | Earlier ePUC ecosystem and Generator positioning. |
| https://redakcja.www.gov.pl/web/cyfryzacja/multiportal-rp-mprp | Official Multiportal scope, components, architecture concept, budget and EU funding. |
| https://www.gov.pl/web/cppc/zakonczenie-oceny-wniosku-FERC0201IP0100525 | Multiportal funding decision. |
| https://rozwojcyfrowy.gov.pl/wp-content/uploads/2025/09/FERC_Lista_projektow_wybor_niekonkurencyjny_01092025.docx | Planned Multiportal project period and targets. |
| https://www.wnp.pl/tech/dyrektor-coi-multiportal-rp-pomoze-zalatwiac-sprawy-urzedowe-prace-nad-nim-rusza-jesienia,1067709.html | COI director’s description of Multiportal, AI support and autumn-2026 start. |
| https://www.gov.pl/web/cppc/zakonczenie-oceny-FERC0204IP0100326 | AI HUB purpose, PLN 151 million value and June 2029 completion date. |
| https://itwiz.pl/coi-przeznaczy-290-mln-zl-na-rozbudowe-infrastruktury-it-i-gpu/ | Earlier AI HUB concept, sandbox, infrastructure and GPU plans. |
| https://pfr.pl/artykul/start-z-polskim-ai-od-pomyslu-do-wdrozenia-centralny-osrodek-informatyki | AI standards, agents and proposed repository of verified implementations. |
| https://api.stat.gov.pl/Home/TerytApi?lang=en | TERYT constituent catalogues and address/territorial services. |
| https://www.npmjs.com/package/angular-gridster2 | `x`, `y`, `rows`, `cols` layout vocabulary. |
| https://www.npmjs.com/package/angular-gridster2/v/4.6.3 | `minItemRows` and related Gridster item options. |
| https://www.npmjs.com/package/react-grid-layout | React Grid Layout’s contrasting `x/y/w/h/i` model. |
| https://quilljs.com/docs/api | Quill’s HTML-export capability. |
| https://json-schema.org/understanding-json-schema/reference/object | Default handling of additional JSON properties. |
| https://angular.dev/best-practices/security | HTML binding, XSS risk and sanitisation. |
| https://datatracker.ietf.org/doc/html/rfc9562/ | UUID format. |
| https://www.gov.pl/web/ia/centralne-repozytorium-wzorow-dokumentow-elektronicznych | CRWDE purpose and verification. |
| https://epuap.gov.pl/wps/wcm/connect/50ad409b-ffe3-4715-8e4d-7e3a2fbfad70/Instrukcja+administratora+-+Opublikowanie+wzoru+w+CRD.pdf?MOD=AJPERES | CRWDE publication package and process. |
| https://www.gov.pl/web/cyfryzacja/rodzaje-uslug-na-epuap | Three-part publication model: template, service description and form. |
| https://www.gov.pl/web/cyfryzacja/serwis-epuap | ePUAP’s role for central and local electronic services. |
| https://www.gov.pl/web/cyfryzacja/katalog-cyfrowych-uslug-polskiej-administracji | Published catalogue counts. |
| https://www.e-mentor.edu.pl/artykul/index/numer/63/id/1229 | CRWDE duplication and standardisation problems. |
| https://www.nik.gov.pl/aktualnosci/spojnosc-i-infrastruktura/platforma-epuap.html | Discoverability and management problems found by NIK. |
| https://www.gov.pl/attachment/feee86d3-07f0-4ada-ac5c-de9df6754b80 | ePUAP migration, Generator pilot and 2027 target model. |
| https://www.gov.pl/web/cyfryzacja/strategia-cyfryzacji-panstwa | Long-term one-stop-service, Generator and user-research plans. |
| https://www.gov.pl/web/dostepnosc-cyfrowa/formularze | Accessible labels, required status, errors and review. |
| https://www.gov.pl/web/dostepnosc-cyfrowa/formularze-na-stronach-internetowych | Programmatic labels, hints, grouping and live errors. |
| https://www.gov.pl/web/dostepnosc-cyfrowa/jakie-akty-prawne-dotycza-dostepnosci-cyfrowej | Digital Accessibility Act and WCAG AA equivalence. |
| https://www.gov.pl/web/cyfryzacja/prosty-jezyk | Polish government plain-language rules. |
| https://www.uodo.gov.pl/file/3714 | GDPR consent requirements. |
| https://bip.uodo.gov.pl/pl/701/4467 | Prohibition on preselected/default consent. |
| https://www.dziennikustaw.gov.pl/DU/2024/773 | Current KRI regulation. |
| https://www.gov.pl/web/govtech/tysiace-pomyslow-24-godziny-i-jeden-cel---usprawnic-panstwo-w-bydgoszczy-zakonczyl-sie-hacknation-2025 | Official HackNation 2025 winners. |
| https://itreseller.pl/hacknation-2025-czyli-kodowanie-pod-patronatem-ministerstwa-cyfryzacji | Description of no signal’s winning COI prototype. |
| https://humancolossus.foundation/blog/congrats-to-our-team- | Sigmion finalist and its cryptographic-content concept. |
| https://github.com/timpaul/form-extractor-prototype | Public PDF/image-to-GOV.UK-form-JSON analogue. |
| https://github.com/lukinov/ai-form-builder | Public screenshot/PDF/text-to-FormEngine JSON project. |

# Could not verify

1. The official expansion of **MLPZ**.
2. The precise semantics and owning service of `TERYT_DOWODOWY`.
3. The meaning of `4G` in `TERYT_4G_DOWODOWY`.
4. A public JSON Schema/OpenAPI specification for the supplied COI form format.
5. A public repository or package containing the full distinctive key set.
6. Whether the deployed builder actually uses Quill.
7. The exact JSONata implementation, version and permitted function set.
8. Whether unknown imported properties are rejected, preserved or silently stripped.
9. Which UUID versions the importer accepts and exactly what `flow.source/target` reference.
10. A public OPZ/tender defining the Generator’s importer or front-end architecture.
11. A job advertisement conclusively identifying the Generator’s production technology stack.
12. An authoritative current total of live CRWDE templates.
13. A government-wide benchmark for the time or cost of digitising one unique official form.
14. A Polish mandatory design-system rule requiring exactly one thing per page.
15. The identity and project of the third `Prawda w sieci` finalist.
16. Public repositories for the 2025 no signal or Sigmion prototypes.
17. A public HackNation 2026 repository already emitting the COI JSON dialect as of 21 November 2026.
18. Whether the published 2027 full-ePUAP-shutdown target remains the operative delivery date.