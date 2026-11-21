# Warnings: known traps

Short list of things that already cost time or would cost trust. Each has a source in this repository.

## Law and claims

- **Anonymous requests.** The older case law accepted unsigned e-mail requests without personal data; rulings of 2024–2026 allow an office to require the applicant's name. Never hard-code either line; it is the office's policy. ([`research/02`](../research/02-udip-law-process-taxonomy.md))
- **Letter or decision.** Only refusal and discontinuance are administrative decisions. A letter sent late loses in court even when its content is right. ([`research/02`](../research/02-udip-law-process-taxonomy.md))
- **"Legally identical print".** No primary source says a non-identical printout of a statutory template is invalid, and none says it is fine. Say "printed on the original template file, without re-typesetting". ([`research/03b`](../research/03b-form-anatomy-and-canonical-profile.md))
- **mObywatel.** A QR-based data-sharing flow exists for selected partners; there is no public interface or sandbox for it. Never claim an integration. ([`research/04`](../research/04-mobywatel-identity-once-only.md))
- **Savings.** Nobody measured time or money saved in the real office. Show measured numbers from the synthetic evaluation and say what they are.
- **The city's privacy notice** says data is not processed in an automated way; it must be reviewed with the data protection officer before real cases. ([`research/02`](../research/02-udip-law-process-taxonomy.md))

## Data

- **Fees and bank accounts** must be read from the live service card. The catalogue's `fees` field is mostly empty and account numbers were removed on purpose.
- **`online_handling` in the catalogue is a weak heuristic.** Read the card text and `external_links`.
- **Templates change.** A form descriptor is bound to the hash of the template file; a different hash disables it.
- **The residence-registration PDFs have a broken text layer.** Positions come from vector geometry, not from text search.
- **One civil-registry form is Letter-sized, not A4.** Printing it scaled moves the margins.
- **Only one of 32 analysed forms has fillable fields.** Plan for overlay, not for form-field filling.

## Software

- **Licences.** The Polish spaCy model is GPL-3.0 and PyMuPDF is AGPL-3.0: keep both out of the core. Some PLLuM model variants are non-commercial. ([`research/06`](../research/06-tech-stack-pdf-ocr-qr-scanner.md), [`research/07`](../research/07-landscape-existing-solutions-and-reuse.md))
- **Local models do not guarantee valid JSON.** Validate against the schema and retry in our code.
- **Citations and structured output cannot be combined in one request** of the commercial model's API; use separate calls. ([`research/08`](../research/08-claude-code-multi-agent-token-economy.md))
- **Browsers cannot read identity-document chips.** The web NFC interface handles only simple tags. ([`research/06`](../research/06-tech-stack-pdf-ocr-qr-scanner.md))
- **The machine-readable zone has no address, no parents' names and no place of birth,** and it transliterates Polish letters.
- **The document reader's licence gates software versions.** Do not upgrade the vendor software before checking the licence in its licence manager; a newer version may refuse to run. Product use needs the manufacturer's consent.
- **A QR code carries about one kilobyte in practice,** not the theoretical maximum.

## Working with agents

- **Native worktrees start from the remote default branch** unless the project setting says otherwise: push `main` after every merge. ([`docs/04-orchestration/git-workflow.md`](04-orchestration/git-workflow.md))
- **A wave of web-research agents on the top model tier emptied a five-hour usage window in 25 minutes.** Research and data gathering go to the middle tier; the top tier is for the lead and for reviews.
- **Shell here-documents corrupt backslashes and non-ASCII text on Windows.** Write files with the file tool.
- **Real identifiers in bug reports** happened in 2022. Synthetic data only, everywhere. ([`research/09`](../research/09-lessons-from-2022-prototype.md))
- **Material prepared before the event must be disclosed** in the presentation and the code, or it breaks the event rules. ([`research/01`](../research/01-hacknation-2026-task-rules-jury.md))
