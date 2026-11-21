# WP-A5 — Draft generator and citation check

Kind: think (legal form) · Model tier: top, high effort; independent review · Depends on: WP-A3, WP-A4 · Branch: `wp/A5-drafts` · Milestone: M2

## Goal

For each analysed question the right document, with every mandatory element in place, written in correct official Polish, with the model allowed to write only where a human would otherwise write boilerplate, and with every legal basis verified by code.

## Read first

1. `AGENTS.md`
2. `research/02-udip-law-process-taxonomy.md`: section 4 (catalogue of response documents, mandatory elements, pitfalls)
3. `data/udip-response-templates.md` (Polish skeletons) and `data/udip-taxonomy.json` (document type ids)
4. `docs/02-architecture/design-notes.md` §3 points 6, 7, 9

## Build

1. **Document types** as data in `data/templates/udip/<type>/`: `template.docx` (letterhead placeholders, fixed legal wording, slots), `spec.json` (mandatory elements with a detector each, slots with `origin` allowed: `clerk` only, or `model` allowed, legal basis ids, who must approve). Types: reply with the information; pointer to the place of publication; not public information; not held; another access regime; extension notice; call to show a special public interest; fee notice; notice about another form or way of disclosure; call to complete data before a decision; refusal decision; discontinuance decision.
2. **Generation**: the fixed skeleton comes from the template; slots marked `model` are filled by the model from the analysis and retrieved passages; facts that only the office knows (the information itself, amounts, names of officials, file references) stay as visible placeholders `[[DO UZUPEŁNIENIA: …]]`. The model is instructed and checked never to produce a number, a date or a proper name that is not in its input. Every model-written section carries `origin = model` until a clerk accepts or edits it.
3. **Citation check** (`drafts/check.py`, code only): extract all citations from the draft with `knowledge.citations.resolve`; unknown → blocker; quotation that does not match the stored text → blocker; a document type whose required legal basis is missing → blocker.
4. **Mandatory-element check**: for each element of `spec.json` a detector (regular expression, section presence, or a field); missing → blocker. For decisions: designation of the authority, date, party, legal basis, ruling, factual and legal reasons, instruction on appeal with the right body and time limit, signature block of an authorised person, and for refusals the names and functions of the persons who took a position and the entities whose interests are protected, as the act requires.
5. **Deadline sanity**: an extension notice whose new date exceeds two months from filing, or that is created after day 14, raises a blocker with the explanation.
6. **Approval flow**: `submit` → reviewer (mandatory for decisions and for anything marked `needs_lawyer_review`) → signer; each step an audit event with the diff hash. Export is possible only after approval, except a watermarked preview.
7. **Export**: DOCX from the template; PDF through a local converter if present, otherwise a simple PDF renderer; the exported file's hash is recorded in the audit trail.

## Acceptance

- [ ] For each document type a generated draft on a synthetic case passes both checks; removing each mandatory element in turn makes the check fail with a message that names the element (table in the status file).
- [ ] A draft with an invented citation and a draft with a misquoted provision are both blocked (negative controls, recorded).
- [ ] No draft produced from the evaluation set contains a number, date or proper name absent from its inputs (automatic comparison; list of violations must be empty).
- [ ] Refusal and discontinuance drafts cannot be exported without a reviewer's approval.
- [ ] Exported DOCX opens in LibreOffice or Word with Polish characters intact; the PDF has selectable text.
- [ ] `tools/gate.sh fast` passes.

## Stages

1. Template data and deterministic assembly for four letter types. 2. Checks. 3. Model-written slots and the remaining types. 4. Approval and export.

## Out of scope

The editor UI (WP-A6), redaction of attachments (WP-A7). Legal wording of templates must be marked "draft wording: to be reviewed by the office's lawyer" in the template footer metadata and in the README.
