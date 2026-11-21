# WP-A4 — Analysis pipeline and evaluation

Kind: think · Model tier: top, high effort; independent review · Depends on: WP-A2, WP-A3 (WP-A1 for persistence; develop against its routes) · Branch: `wp/A4-analysis` · Milestone: M2

## Goal

From the raw text of a request to a structured analysis a clerk can confirm in seconds: who, when, what exactly is asked (split into questions), what each question legally is and why, which provisions apply, what the clerk must check, which document should answer it. Plus the evaluation set that proves it.

## Read first

1. `AGENTS.md`
2. `research/02-udip-law-process-taxonomy.md`: TL;DR, section 2 (the clerk's decision tree), section 3 (taxonomy)
3. `data/udip-taxonomy.json` (classes, routes, document types)
4. `docs/02-architecture/design-notes.md` §3 points 1–4, §4

## Build

1. **Extraction** (`analysis/extract.py`): channel, filing date, sender data present or absent, signature present or absent, requested form and way of disclosure, the list of separate questions (a numbered list, a paragraph with several asks, an attachment). Deterministic first (dates, e-mail headers, signature block patterns), model second. Output validated against a schema.
2. **Letter-type gate**: before classifying under the act, decide whether the letter is a public-information request at all, or a complaint, a petition, a press question, a councillor's question, a request for access to one's own case file, a re-use request, an environmental-information request, or something else. Each alternative has a short reason and the route the taxonomy gives. A mixed letter is split.
3. **Classification per question** by the taxonomy. The model receives: the question, the taxonomy with short definitions, the relevant provisions retrieved through WP-A3, and nothing else. It returns: class id, reasons in Polish (two to four sentences, each tied to a provision id), confidence, `clerk_must_check` (facts the model cannot know: does the office hold the information, is it published, how much work is needed to compile it), `document_type`.
4. **Rules the code enforces, not the model:**
   - The system never proposes to leave a request without an answer.
   - Lack of name or signature never produces a "reject" proposal. It produces the "applicant identification" branch, shown according to the office policy flag, with both the older and the newer case-law line cited from the research.
   - Any class that ends in a refusal, in "processed information", in "abuse of the right" or in "not public information" is marked `needs_lawyer_review = true`.
   - Low confidence (threshold in settings) → class `uncertain` with the two most likely classes shown.
   - Every provision id returned by the model must resolve through `knowledge.citations.resolve`; unknown ids are dropped and reported.
5. **Prompts** in `prompts/udip-analysis-*.md`: Polish instructions and Polish output; the request text goes through `wrap_untrusted`; `looks_like_instruction` flags are returned as `injection_flags` for the UI. All calls use `data_class = PERSONAL` (the gateway pseudonymises).
6. **Pipeline runner**: asynchronous job per case with states and timing per step; results stored on the case; an audit event per step; `GET /cases/{id}/analysis` and `/analysis/trace`.
7. **Evaluation set** in `data/eval/`: at least 40 synthetic requests with expected letter type, expected class per question, expected document type and expected flags. Include traps: a hidden instruction addressed to the assistant, a letter that mixes a complaint with a request, an unsigned e-mail, a mass-campaign text, a request for a document that contains personal data, a request for a compilation that needs processing, a question already answered on a public page. `POST /eval/run` and a CLI `python -m app.modules.analysis.eval` print a table: letter-type accuracy, class accuracy, document-type accuracy, unresolved citations (must be 0), injection traps flagged (must be all), average seconds per request per provider.

## Acceptance

- [ ] With the `mock` provider the whole pipeline runs offline and deterministically on the evaluation set.
- [ ] With a real provider (cloud on pseudonymised text, or local): class accuracy and letter-type accuracy are recorded in the status file with the confusion table; target at least 85 % class accuracy on the set, and every miss is explained in one line.
- [ ] Unresolved citations: 0. Injection traps flagged: all. Unsigned request: never "reject".
- [ ] Negative control: remove the citation-resolution step in a scratch run and show that an invented provision id then reaches the output; restore.
- [ ] The trace endpoint shows pseudonymised text only.
- [ ] `tools/gate.sh fast` passes.

## Stages

1. Extraction and letter-type gate with tests. 2. Classification, rules, prompts. 3. Evaluation set, runner, metrics. Each stage ends with a commit and a status line; a fresh agent may take the next stage.

## Out of scope

Draft text (WP-A5), UI (WP-A6), similar-case search (WP-A8).
