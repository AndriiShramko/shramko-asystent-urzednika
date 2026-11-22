# Results for the seven judged forms

One folder per judged set of the task: `form.json` is the form in the partner's structure (exactly `title`, `tabs`, `flow`), `meta.json` is our report beside it (where each field came from, remarks for the clerk, proposed dictionaries).

**State of these files: 22 November 2026, 07:36, produced by the submitted image `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:77f29937c49dbbfbe20bcfd820c37816cafc2d2c6da71a238aac65f91a87a97a` (code commit `a9fef20`)** with the jury's own flags: `docker run --rm --network none --read-only --cap-drop ALL ... convert /in/<file> --out /out/form.json --report /out`. One input per set: the PDF of the set.

| Set | Input | Pages (`tabs`) | Remarks in `meta.json` |
|---|---|---|---|
| judged-02-zwrot-oplaty-skarbowej | PDF | 4 | 4 |
| judged-03-wydanie-zaswiadczenia | PDF | 4 | 5 |
| judged-04-wynajecie-swietlicy | PDF | 4 | 4 |
| judged-06-zajecie-pasa-drogowego | PDF | 6 | 13 |
| judged-07-psy-rasy-agresywne | PDF | 6 | 5 |
| judged-08-deklaracja-odpady | PDF | 9 | 57 |
| judged-09-stypendium-sportowe | PDF | 11 | 59 |

Each `form.json` here passes `python tools/coi_lint.py --profile strict` (schema and the partner's rules). The same input gives the same bytes on every run without a network.

**Set 08** (`judged-08-deklaracja-odpady`): the form quotes the office's bank account printed on the paper, and this repository's publishing check refuses any identifier with a valid check digit, so its `form.json` is not in git. All seven files, set 08 included, are attached to the release [`v1.0-hacknation`](https://github.com/AndriiShramko/shramko-asystent-urzednika/releases/tag/v1.0-hacknation). To make it yourself: the command above on `data/coi/judged-08-deklaracja-odpady/*.pdf` of the task set.

**Honest limits.** The forms are drafts for the clerk to confirm, not finished e-services: the remarks in `meta.json` say what the program could not decide on its own (for example a place on the paper without a label, or checkboxes it could not tie to a question). The weakest inputs are old DOC files and photos.
