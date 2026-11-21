# New presentation concept: the deck is an official document, and the product processes it

Owner, 21 November 2026, 11:08 and 11:11: the current presentations do not please him; he wants something more unusual and clearer, with humour where it fits, that names the pains the partner stated and those it did not. This file replaces the visual direction of `storyboard-pakiet.md` and `storyboard-formularze.md` (their facts and sources stay valid; their layout and page count do not). Both cards allow **at most ten slides** as PDF and a film of at most three minutes.

## The idea

The jury reads paper all day. So the presentation **is** a piece of official paper, and our product does to it, slide by slide, what it does to every form.

- For the forms task the deck is an application form: **„WNIOSEK o zamianę formularza w e-usługę"**. Each slide is one part of the form (A, B, C …). On the left the paper: printed labels, boxes, dotted lines, a blue pen filling them in, a red stamp. On the right what the converter made of that very part: the field in the e-service, or the fragment of JSON. The reader watches the product work on the slide they are reading.
- The last slide is the part every Polish form has: **„ADNOTACJE URZĘDOWE (wypełnia jury)"**. It is the partner's own criteria table, already filled in with ticks and the place where the proof is. The jury's scoring sheet arrives pre-filled.
- The proof that it is not a costume: **the deck's own PDF goes through our service**, and the resulting JSON is in `results/` next to the judged forms. One line on the last slide says so. Anyone can repeat it.
- For the city's task the same concept takes the other document: the deck is a **request for public information addressed to the jury** („Czy da się odpowiedzieć na wniosek w kilka minut?"), with the statutory clock running in the corner, names that turn grey and then black as the anonymiser passes, and a last slide that is the answer letter the tool drafted, containing the eight things the card requires.

Why it is clear and not only odd: a form is the most familiar structure in the room. Numbered parts, one question per part, the answer written in. Nobody has to learn how to read the slide.

## Humour: where and how much

Dry, kind, bureaucratic. The paper is the comic character; officials and residents never are. One small joke per slide at most, always in the margin (a pen note, a footnote, a stamp), never in the claim itself.

| Device | Example (Polish, as printed) |
|---|---|
| The form's own instruction | „Wypełnić drukowanymi literami." and under it, in pen: „Już nie trzeba." |
| Strike out what does not apply | „Czas cyfryzacji jednego formularza: ~~dni~~ / sekundy (niepotrzebne skreślić)", with the measured seconds next to it |
| Stamp | „ZATWIERDZAM. Człowiek" on the slide about approval; „WPŁYNĘŁO 22.11.2026" on the title |
| Footnote in tiny print | the sources of the numbers, set as „Pouczenie" |
| Declarations with tick boxes | „Oświadczam, że rozwiązanie nie korzysta z modeli dostępnych wyłącznie przez API ☑", one line per hard rule of the card |
| Attachments list | „Załączniki: 1) pliki JSON, 2) film, 3 minuty, 3) repozytorium" |
| Decision box for the jury | „Decyzja: ☐ pozytywna ☐ bardzo pozytywna" |

Not allowed: jokes about slow offices, about people who cannot use computers, about the partner's products; any number that was not measured; any joke on the slide that states what is simulated.

## The ten slides for the forms task

Every slide: the letter of the part, one question as the headline, the paper on the left, the result on the right, at most forty words outside the drawing.

| # | Part of the form | The question it answers | What the right side shows |
|---|---|---|---|
| 1 | Nagłówek: „WNIOSEK o zamianę formularza w e-usługę" | Who we are, what we ask for | the same title as an e-service header; stamp „WPŁYNĘŁO" |
| 2 | A. Opis problemu | What hurts today (the partner's words: many formats, no standard, every form analysed by hand) | one paper form and its long way to an e-service, as crossed-out steps |
| 3 | B. Czego wnioskodawca nie napisał | The pains nobody spelled out (coi-replan §3: trust, paper habits, cost, scale) | four pen notes in the margin of the form, each pointing at the part that answers it |
| 4 | C. Rozwiązanie | One file in, their JSON out; the steps | the pipeline as the form's own route through the office: wpływ, odczyt, znaczenie, zapis |
| 5 | D. Dowód: jedno pole | A row of boxes becomes one field with a length and a check | zoom on one field: paper, JSON, e-service, side by side |
| 6 | E. Dowód: cały formularz | Review by exception: the official looks only where the system is unsure | the review screen (real screenshot) |
| 7 | F. Dowód: cały urząd | Batch: a whole city's forms, with measured numbers | the funnel with the numbers of `eval/metrics.json` and of the census |
| 8 | G. Oświadczenia | The hard rules of the card, each ticked: no external calls, open licences, Docker, token, temporary files | the ticks, each with the test that proves it |
| 9 | H. Co dalej | Deployment and cost; forms ready for AI assistants (the card's own sentence about agents) | cost per form; the agent-readable export as one small picture |
| 10 | ADNOTACJE URZĘDOWE (wypełnia jury) | The criteria table pre-filled; attachments; the line about the deck's own JSON | ticks per criterion with the slide or file that proves each; QR to repository and film |

Slide 3 is where the owner's wish "solve what they forgot to say" is visible. Slide 10 is where a tired juror can score in one minute.

## The web version and the film

- Web: the same ten parts on one scrolling page. A scanner line passes over each paper part as it enters the screen; the found places light up and slide to the right as form fields. The motion is the product, not decoration. Reduced-motion users get the final state.
- Film (three minutes at most, captions only, no voice needed): 0:00 the paper form on a desk and the question; 0:20 upload; 0:35 the review screen, two corrections; 1:10 the e-service viewer with a condition and a validation; 1:40 batch over a folder; 2:10 the container started without network; 2:30 the criteria slide; 2:50 addresses.

## Look

Paper white (#fbfaf6) with a faint grain, black print in a typewriter face, the pen in one blue, the stamp in one red, one yellow marker for the single thing to notice per slide. No gradients, no dark panels. Fonts are open-licensed files kept in the repository and embedded, so the PDF looks the same everywhere. Contrast and text size meet WCAG 2.1 AA; the pen font is never used for anything that must be read to understand the slide.

## Rules that stay from the earlier storyboards

Only true claims; numbers only from `eval/metrics.json`, `data/forms-census.json` and the sources in `research/`; what is simulated is said on the slide; the draft mark stays until the build equals the claims; pre-event material is named as such on slide 10.

## Work package WP-P1

Build `tools/build_deck.py` (one source, three outputs: `index.html` with motion, the ten-slide PDF, a Russian-annotated page for the owner), reusing the mechanics of `tools/build_pakiet.py` (16:9 pages, print rules, `?static=1`, number counters). First deliverable, before any other slide: **slides 1 and 10 as a PDF for the owner to judge the look**; continue only after his yes or his correction.

Acceptance: ten slides, PDF under 10 MB; every number equals its source file; the deck's own PDF converts through the service and the JSON is committed; the film is at most three minutes and shows the product, not slides; the owner has seen slides 1 and 10 and agreed to the look; a reader who sees only slides 1, 3 and 10 can say what the product does, which pains it answers and how it scores.
