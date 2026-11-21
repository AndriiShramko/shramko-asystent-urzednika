# Results for the seven judged forms

One folder per judged set of the task: `form.json` is the form in the partner's structure (exactly `title`, `tabs`, `flow`), `meta.json` is our sidecar beside it.

**State of these files: snapshot of milestone (a), 21 November 2026, 15:14, commit `920dbf1`.** At this milestone the converter reads the PDF of each set and composes the title and the partner's standard pages. **The fields of the matter are not in these files yet**: the finder and the understanding step are being built, and every sidecar says so in the warning `BRIEF_NOT_READ`. Known weak spots of the interim title rule: set 6 gives only „WNIOSEK"; set 9 carries a stray „II." at the end; set 4 keeps the footnote mark of the paper.

The files are replaced at every milestone by the evaluation run (WP-F11). They are kept in git from the first milestone on, so that a valid set of seven always exists.

Each `form.json` here passes `python tools/coi_lint.py --profile strict` and `contracts/coi/form.schema.json`.

Set 8 (`judged-08-deklaracja-odpady/form.json`) is not in git: the form quotes the office's bank account for the stamp fee from the paper, and the publishing check refuses any identifier with a valid check digit. Regenerate it with `bash tools/gate.sh py tools/lead/snapshot_results.py .`; it is uploaded with the submission.
