# Results for the seven judged forms

One folder per judged set of the task: `form.json` is the form in the partner's structure (exactly `title`, `tabs`, `flow`), `meta.json` is our report beside it (where each field came from, remarks for the clerk, proposed dictionaries).

**State of these files: 22 November 2026, 10:05, produced by the submitted image `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:d04875554f13ccb92fb83d223b704e62776df8a579814885794b0066b6ff441f` (code commit `97df429`)** with the jury's own flags: `docker run --rm --network none --read-only --cap-drop ALL ... convert /in/<file> --out /out/form.json --report /out`. One input per set: the PDF of the set.

| Set | Input | Pages (`tabs`) | Entries in `meta.json` (remarks for the clerk and notes of the run) |
|---|---|---|---|
| judged-02-zwrot-oplaty-skarbowej | PDF | 4 | 6 |
| judged-03-wydanie-zaswiadczenia | PDF | 4 | 7 |
| judged-04-wynajecie-swietlicy | PDF | 4 | 6 |
| judged-06-zajecie-pasa-drogowego | PDF | 6 | 15 |
| judged-07-psy-rasy-agresywne | PDF | 6 | 9 |
| judged-08-deklaracja-odpady | PDF | 9 | 57 |
| judged-09-stypendium-sportowe | PDF | 11 | 79 |

Each `form.json` here passes `python tools/coi_lint.py --profile strict` (schema and the partner's rules). The same input gives the same bytes on every run without a network.

**Set 08** (`judged-08-deklaracja-odpady`): the form quotes the office's bank account printed on the paper, and this repository's publishing check refuses any identifier with a valid check digit, so its `form.json` is not in git. All seven files, set 08 included, are attached to the release [`v1.2-hacknation`](https://github.com/AndriiShramko/shramko-asystent-urzednika/releases/tag/v1.2-hacknation). To make it yourself: the command above on `data/coi/judged-08-deklaracja-odpady/*.pdf` of the task set.

**For the clerk.** Each form comes with its remarks in `meta.json`: the decisions the program leaves to the clerk (for example a place on the paper without a label, or which fields are mandatory when the paper does not say). The review page shows the same remarks next to the original, with a ready answer to choose where the program can offer one.
