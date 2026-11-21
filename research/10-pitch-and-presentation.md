# R10 - Pitch and presentation: how to win with a non-technical city jury (solo, first hackathon, non-native Polish)

Research date: 2026-11-21 (event day, before the 11:00 task card). Labels: **VERIFIED** = primary page opened and read (for web pages: fetched, content read through the fetch tool; JetBrains page read through curl); **SECONDARY** = search-result snippet or second-hand account only; **UNVERIFIED** = not confirmed. Anything labelled **ADVICE** is my own synthesis, not a documented fact.

**Honest limit of this report.** First-hand accounts of how Polish public-sector hackathon jurors score are almost absent online. I found one participant report on HackNation 2025 (Solvro), the official wording of the 2025 final, and general hackathon-judging articles by Western jurors. I found no first-hand material on HackYeah public-sector tracks, on the GovTech Polska festival, or on EU Datathon pitch lessons (see section 1). Where the evidence is general, I say so, and the specific advice is marked ADVICE.

## TL;DR for the presenter

1. **Say what the product is in the first sentence, before any story.** Jurors repeat the same rule: problem first, one plain sentence, no market size or backstory. Source: JetBrains judges, dev.to (VERIFIED).
2. **Show something working within about 90 seconds** of the pitch start (a juror's rule) and keep one complete path: e-mail in, analysis, deadline, draft, approval. Do not demo five features. (VERIFIED, JetBrains)
3. **The 2025 final was about deployment potential in public administration, "a nie tylko efektowny pitch".** Talk about clerk time, legal safety, EZD, cost, and a pilot, not about models. (VERIFIED gov.pl for deployment criterion; the "not only a flashy pitch" wording SECONDARY via CHIP)
4. **Expect the final jury to ask for a live demo on a concrete case instead of the slides** (a 2025 finalist report). Have the live demo ready as the plan, the slides as the backup. (SECONDARY, one first-hand report)
5. **Read the criteria on the 11:00 task card and address each one by name** on a slide and in the description. Being vague about criteria is a documented reason for losing. (VERIFIED, dev.to)
6. **Be direct about what is real, simulated, planned.** Judges can tell when you talk around a feature that does not exist; honesty "reads as confidence". The storyboard hides this in a caption; give it a visible moment. (VERIFIED, JetBrains)
7. **Do not memorise 350 words in Polish. Map the talk, read the 11 key lines from the presenter window, and rehearse three times aloud.** Memorising raises nerves (Stanford GSB). Pause after every slide change. (VERIFIED for "map, do not memorise"; the rest ADVICE)
8. **If you blank out: repeat your last sentence, then ask the back-pocket question** ("Czy to jest zgodne z tym, jak Państwo pracują na co dzień?"). (VERIFIED technique, Stanford GSB)
9. **If you did not understand a question: ask politely, then paraphrase it back** ("Czy dobrze rozumiem, że pytają Państwo o ...?"). Phrases in section 4. (ADVICE)
10. **Use the city's mentors on Saturday as a source for the pitch**: one real number from their workload, one real constraint, their own words. Quote it on slide 1 or 10. (ADVICE; mentors named as official mentors, link to the task UNVERIFIED)
11. **The storyboard needs three structural fixes** (section 9): slides 7-9 take about 27 percent of the speech on material outside the task; no visible "what is real" moment; slide 10 has no concrete pilot offer with dates; plus Polish corrections.
12. **Submit by 10:00 on Sunday, not 10:59.** Export the PDF and check size (max 10 MB) and links at 09:30. (ADVICE; deadline VERIFIED in R1)

---

## 1. How judging works in practice (question 1)

### 1.1 What is documented

| Fact | Source | Label |
|---|---|---|
| In 2025 the jury assessed all submissions, picked three finalists per task, then from the three chose one winner "najwiekszy potencjal do wdrozenia w administracji publicznej" | https://www.gov.pl/web/cyfryzacja/tysiace-pomyslow-24-godziny-i-jeden-cel--usprawnic-panstwo-w-bydgoszczy-zakonczyl-sie-hacknation-2025 | VERIFIED |
| Finalists presented prototypes, explaining assumptions, how they worked and development paths; over 250 mentors, including representatives of the institutions that set the challenges, were available during the 24 hours | same page | VERIFIED |
| Organisers said the aim is usefulness in the public sector and real deployment "a nie tylko efektowny pitch"; teams could ask officials about procedures and legal limits during the event | https://www.chip.pl/2025/11/hacknation-2025-ogolnopolski-hackathon-wdrozeniowy (as paraphrased in a search snippet; page not read in full) | SECONDARY |
| 2026 stage 1: jurors score each criterion 0-10 in HackTribe; "only a few minutes" per project; top 5 go to a 5+5 minute final | R1 (research/01-hacknation-2026-task-rules-jury.md), Regulamin and guide | VERIFIED |
| Institutions are told to write challenges that are "konkretne, zrozumiale" and feasible in the time, so prototypes are easy to analyse, test or develop; the jury looks for "najwiekszy potencjal dalszego rozwoju" | https://www.gov.pl/web/cyfryzacja/hacknation-2026-zaczyna-sie-od-dobrego-wyzwania-za-nami-warsztaty-dla-instytucji-publicznych | VERIFIED |
| A 2025 finalist (Solvro, KAS task): second-highest stage 1 score; in the final the jury expected "a live demo showing a specific use case" instead of the prepared slides; both finalists were close in quality; they did not win; their dashboard used the 3-30-300 rule (key info in 3 s, more in 30 s, full in 300 s) | https://solvro.pwr.edu.pl/en/blog/hacknation-2025/ | VERIFIED (first-hand, one team) |

### 1.2 What is not documented (searched, not found)

- **What jurors open first in an asynchronous stage, how long they spend, what makes them stop reading.** No source for HackNation or any Polish public-sector hackathon. Closest evidence: MLH plans 2-4 minutes per project in person (2 min presentation and demo, 1 min questions, 1 min travel), and says a 2-minute video should be "a demo of their hack, not a presentation" (https://guide.mlh.com/general-information/judging-and-submissions/judging-plan, VERIFIED). A judge-turned-writer says that by mid-block "the demos start blurring together" and that a judge who spends a third of the slot not knowing what they look at is lost (https://dev.to/kurbaitaev/what-judges-actually-score-notes-from-a-year-of-hackathon-judging-3p4l, VERIFIED, general hackathons, not Polish).
- **HackYeah public-sector tracks, GovTech Polska competitions and festival, other ministry or city hackathons in Poland:** web searches returned only winner lists and press releases, no first-hand pitch accounts. (Not found.)
- **EU Datathon:** final = finalists first present ideas in videos, then pitch to a jury of 14 open-data experts (2022); the scoring criteria and any pitch lessons are not in the article (https://data.europa.eu/en/news-events/news/meet-winners-eu-datathon-2022, VERIFIED page, nothing on pitch technique).
- **GovHack (Australia, comparable public-data event):** teams submit a three-minute video; winners get invited to develop ideas with agencies (https://www.data.nsw.gov.au/blog/govhack-2023, https://www.finance.gov.au/about-us/news/2025/celebrating-innovation-govhack-2025, SECONDARY from search snippets).

### 1.3 Working model for stage 1 (ADVICE, derived from the above)

Because nothing says what jurors open first, design for every order:

1. Title and the first two sentences of the description must carry the whole idea (a juror who stops there still scores "Zwiazek z wyzwaniem" correctly).
2. PDF page 1 and page 2 must work alone (section 3.1).
3. The video must show the product in the first 10 seconds (section 3.2).
4. Every link must work without login and without installation (2025 partners repeatedly asked for that: R1 section 3.2).
5. Assume 3-5 minutes in total per project, the guide says "tylko kilka minut" (VERIFIED, R1), so everything beyond the first screen of each artefact is a bonus.

---

## 2. Structures that win with non-technical public-administration juries (question 2)

### 2.1 What is documented

I found no published winning deck or pitch video of a HackNation or other Polish public-sector task, and no write-up that describes a winning pitch structure at such an event. What exists is general guidance from jurors at other events, plus the one Polish first-hand report. Treat the "examples" below as evidence about juror behaviour, not as proof about HackNation.

| # | Example or source | What it documents | Link | Label |
|---|---|---|---|---|
| 1 | JetBrains x Codex hackathon, judges interviewed | Start with the problem so judges "share your frustration"; show something working in about 90 s; demo is the pitch; mock slow parts and pre-fill forms; be "very direct about what works, what doesn't"; rehearse aloud and time it; "a strong project with a confusing demo loses to a simpler project that the judges understand" | https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/ | VERIFIED |
| 2 | Solvro, HackNation 2025 KAS task, finalist | In the final the jury wanted a live use case, not slides; winning argument of their product was one concrete pain point plus full automation | https://solvro.pwr.edu.pl/en/blog/hacknation-2025/ | VERIFIED |
| 3 | dev.to, "5 reasons why you are losing hackathons" | Start with what and why, not how; address every criterion explicitly; use the judges' language; show "what could be" honestly; polish (animations, no dead links) beats extra features | https://dev.to/code42cate/5-reasons-why-you-are-losing-hackathons-4k70 | VERIFIED |
| 4 | dev.to, "What judges actually score" | Open with "a plain declarative" sentence of what the product is; one working path; a short capture as fallback; state a known weakness; avoid market size or backstory at the start | https://dev.to/kurbaitaev/what-judges-actually-score-notes-from-a-year-of-hackathon-judging-3p4l | VERIFIED |
| 5 | MLH judging plan | A demo video is "a demo of their hack, not a presentation"; 2 minutes | https://guide.mlh.com/general-information/judging-and-submissions/judging-plan | VERIFIED |

### 2.2 Distilled structure for 5 minutes (ADVICE, consistent with the sources above)

| Time | Content | Proportion |
|---|---|---|
| 0:00-0:10 | Greeting and one sentence naming the product and the user: "Asystent Urzędnika przygotowuje projekt odpowiedzi na wniosek o informację publiczną; urzędnik zatwierdza." | 3 % |
| 0:10-0:50 | The problem in the city's own numbers (14 days; requests per day) | 13 % |
| 0:50-2:30 | Demo of one complete path (the live product, not slides) | 33 % |
| 2:30-3:30 | Why it is safe (masking, sources checked by a program, human decides, log) and "what is real, what is simulated" | 20 % |
| 3:30-4:30 | Deployable: next to EZD, open code, local model, cost, pilot with dates | 20 % |
| 4:30-5:00 | One roadmap sentence (forms, counter), the ask, thanks | 10 % |

How to quantify the problem: use numbers a juror can check in their own office. Candidates in this repository: the 14-day statutory term; the Watchdog Polska monitoring range for Bydgoszcz in 2022 (501-1200 requests, from the storyboard caption; source not re-opened in this research, so UNVERIFIED here). Ask the mentors for the real 2025 count and the share of repeated requests; a real number from them beats any estimate.

How to prove deployability: "works next to EZD", "open code", "local model", "pilot in one referat in weeks", plus a table of what is real and what is simulated. The 2025 jury picked for "potencjal do wdrozenia" (VERIFIED, gov.pl above).

"Big vision" lines that are safe: the same engine serves forms and the counter (storyboard slides 7-9). Keep it to one sentence and one slide, because the guide warns against concepts that are too wide (R1 section 5, VERIFIED).

---

## 3. The first-stage package (question 3)

All Polish text below uses only facts present in this repository (storyboard, R1). Numbers not yet measured are in [square brackets] and must be filled from `metrics.json` or deleted. Do not paste a bracket into the submission.

### 3.1 The PDF (read without a speaker, max 10 MB)

Rule (ADVICE): page 1 = the entire project in one image; page 2 = proof; the rest = detail. The storyboard's print mode already gives one slide per page with a caption. Recommended page order, mapped to storyboard slides:

| PDF page | Content | Why there |
|---|---|---|
| 1 | Title page: name, one-sentence promise, QR/links (demo, repo), team of one, "Hackathon HackNation 2026, zadanie: Inteligentny asystent urzędnika" | A juror who stops here still knows what and where |
| 2 | Before/after timeline of one request (14 days; clerk steps with and without the assistant), with caption | Fit and time saved on one page |
| 3 | Storyboard slide 3 (four stations) + caption | The product in one picture |
| 4 | Demo still frames (6 numbered frames of the demo) + link to the video | A juror who does not press play still sees it |
| 5 | Security (slide 5) | "Bezpieczny" is in the task sentence |
| 6 | Legal safety with measured counters (slide 6) | Proof, only if measured |
| 7 | **What is real, simulated, planned** (new page, section 9 item 4) | Honesty page |
| 8 | Deployment: next to EZD, cost, pilot with dates (slide 10) | "Potencjal wdrozeniowy" |
| 9 | Roadmap: forms and counter on the same core (slides 7-9 merged) | Vision after proof |
| 10 | Credits and what was built during the hackathon (cite the pre-made research honestly) | FAQ rule on earlier resources (VERIFIED, R1) |

Check at 09:30 on Sunday: file under 10 MB, text selectable, links clickable, no draft text.

### 3.2 The 2-minute demo video, second by second

Organisers recommend up to 2 minutes (VERIFIED, R1). Record on screen, no talking head, captions in Polish, calm voice or captions only (ADVICE: captions only avoids pronunciation risk; a short voice-over line at the start is optional).

| Time | Show | Caption (Polish, at most 6 words) |
|---|---|---|
| 0:00-0:08 | Title card with the product name, then straight to an e-mail opening in the clerk's inbox | "Wniosek wpłynął. Termin: 14 dni." |
| 0:08-0:25 | The e-mail contains three questions; the assistant highlights them with numbers 1, 2, 3 | "Trzy pytania. Trzy ścieżki." |
| 0:25-0:45 | Three labels appear: "już w BIP", "dane z wydziału", "dane osobowe"; a link opens the BIP page | "Pierwsza odpowiedź już w BIP." |
| 0:45-1:00 | Deadline badge with two dates (statutory 14 days and the extended date if needed) | "Termin liczony automatycznie." |
| 1:00-1:15 | The masked text the model receives: names turn into [OSOBA_1], [ADRES_1] | "Model widzi tylko znaczniki." |
| 1:15-1:35 | The draft fills in; citation chips turn green; a fake "art. 99" chip is rejected and the draft is stamped "zablokowano" | "Program sprawdza każdy przepis." |
| 1:35-1:48 | The clerk edits one sentence and presses "Zatwierdź"; an audit log line appears | "Urzędnik zatwierdza. Dziennik zapisuje." |
| 1:48-2:00 | Closing frame: what is real / simulated in one line, link and QR | "Dane syntetyczne. Kod otwarty." |

(All elements are in the storyboard's demo and slide 5/6 motion; the order is an editorial proposal, ADVICE. The "art. 99" rejection only goes in if the product really does it.)

### 3.3 The short written description

First two sentences (the juror may read only these). Paste-ready, adjust only if the task card (11:00) uses different words:

> **Asystent Urzędnika** czyta wniosek o informację publiczną, mówi urzędnikowi, czym on jest i jaki jest termin, oraz przygotowuje projekt odpowiedzi ze sprawdzonymi podstawami prawnymi. Dane osobowe są maskowane przed wysłaniem tekstu do modelu, a każdy projekt zatwierdza urzędnik.

Full short description (about 90 words):

> Asystent Urzędnika wspiera pracowników urzędu w analizie wniosków o informację publiczną i w przygotowaniu odpowiedzi. Rozdziela pytania z jednego e-maila, wskazuje informacje już opublikowane w BIP, liczy terminy i znajduje wcześniejsze odpowiedzi urzędu. Projekt pisma powstaje wyłącznie ze źródeł: tekstu ustawy, BIP i archiwum odpowiedzi; podstawy prawne sprawdza program, nie model. Działa obok EZD, kod jest otwarty, model może pracować lokalnie. Pokaz używa danych syntetycznych; lista elementów działających i symulowanych jest w repozytorium. [Wyniki testów: LICZBA z metrics.json.]

How to title the project (ADVICE; naming rule from the owner's CLAUDE.md: new products carry "Shramko"): **"Shramko Asystent Urzędnika: od wniosku do odpowiedzi"**. The first half is the repository name and uses the task's own word ("asystent urzędnika"); the second half is the storyboard's tagline.

---

## 4. Advice for a low-confidence, non-native presenter (question 4)

Documented techniques (Stanford GSB, https://www.gsb.stanford.edu/insights/how-manage-public-speaking-anxiety, VERIFIED): map the content instead of memorising it (memorising can raise nerves); keep a back-pocket question; if you blank, repeat your last point or ask the question; belly breathing; hold a cold bottle of water; move before speaking; use broad gestures; do not drink or chew while speaking. A general source on pauses for non-native speakers says anxiety speeds speech and deliberately slow speech sounds natural to listeners (found via search snippets only: SECONDARY, https://www.italki.com/en/post/g1QF0d98SyVYAzzTMfaIAl). JetBrains judges add: enthusiasm does work, rehearse aloud and time it (VERIFIED).

Practical rules (ADVICE built on these):

| Topic | Rule |
|---|---|
| Notes or memory | Read from the presenter window; memorise only the first sentence of the pitch and the last two. Your eyes go to the screen, then up at the jury at the end of each sentence. |
| Pace | One sentence, then a full stop of two seconds while the animation plays. The deck is designed so silence looks like a deliberate pause. |
| Where to look | Slides 1-9: alternate screen and jury; slide 10 last sentence and slide 11: only the jury. One person (the chair) first, then the person who looked most interested. |
| Hands | Hold the clicker or rest one hand on the table; the other makes one broad gesture per slide (open palm towards the screen on "decyduje"). No pockets, no pen. |
| Start | Stand still for two breaths. "Szanowni Państwo, dzień dobry. Nazywam się Andrii Shramko, mieszkam w Bydgoszczy." Then slide 1. |
| End | Last sentence on slide 11, then three seconds silence, then "Dziękuję. Zapraszam do pytań." Do not apologise at the end. |
| Language | Say once at the start of Q&A: "Polski nie jest moim językiem ojczystym, więc proszę o chwilę cierpliwości." Jurors in this setting are likely to be kind; it removes the pressure. |
| Hard words | Practise aloud ten times: "pseudonimizacja", "informacja publiczna", "rozstrzygnąć", "uprawdopodobnić", "referat", "Samorządowe Kolegium Odwoławcze". Replace any word you cannot say by a simpler one ("zamaskowane" for "spseudonimizowane"). |

Demo failure (ADVICE):

1. Before the pitch, start the recorded `demo.mp4` in a second tab and keep the live demo in a first tab.
2. If the live demo hangs for more than five seconds: "Pokażę to na nagraniu. Dane są te same." Switch (Alt+Tab) and keep talking at the same pace.
3. Never debug in front of the jury. A broken live demo with a ready recording is survivable; a silent debugging minute is not.

Question you did not understand (ADVICE):

1. "Przepraszam, nie jestem pewien, czy dobrze zrozumiałem pytanie. Czy mogą Państwo je powtórzyć?"
2. Then paraphrase: "Czy dobrze rozumiem, że pytają Państwo o ..."
3. If you still do not know the answer: "Nie znam dokładnej odpowiedzi. Sprawdzę to i odpowiem Państwu na piśmie." (A short honest line beats a long guess.)

Polite formulas (checked for register; male speaker):

| Situation | Polish |
|---|---|
| Opening | "Szanowni Państwo, dzień dobry." |
| Before an answer | "Dziękuję za to pytanie." |
| Asking to repeat | "Czy mogę prosić o powtórzenie pytania?" (softer than "Proszę powtórzyć pytanie") |
| Buying time | "Chwileczkę, zastanowię się." / "To ważne pytanie, odpowiem krok po kroku." |
| Out of scope | "To wykracza poza prototyp; zapisałem to jako następny krok." |
| Disagreeing | "Rozumiem tę obawę. Odpowiem, jak to rozwiązaliśmy." |
| Closing | "Dziękuję za uwagę. Zapraszam do pytań." |

---

## 5. Visual explanation (question 5)

Evidence level: no study found specific to officials. Sources only support the general rule (visuals make technical points accessible; "a well-designed diagram can make technical details more accessible to a non-technical audience", from a search snippet of https://medium.com/circleslife/creating-a-5-minute-kickass-hackathon-pitch-17cdcb42c3bc, SECONDARY; "3-30-300" dashboard rule, VERIFIED, Solvro). Everything below is ADVICE.

| Use | Why it works for officials | In this project |
|---|---|---|
| Before/after timeline of one request | Officials think in terms of terms and steps | Calendar strip with 14 days, with and without the assistant (slide 1 + PDF page 2) |
| One flow diagram, four stations | Process, not architecture | Slide 3 as is |
| Masked-text example | Makes "ochrona danych" visible in two seconds | Slide 5: "Jan Kowalski" becomes [OSOBA_1] |
| Green tick / red "zablokowano" on a citation | Makes "no invented law" tangible | Slide 6 |
| Counters (only measured) | Numbers feel factual | `metrics.json` counters |
| Crossed-out big database | Answers the typical scaling fear | Slide 9 |

Avoid: architecture diagrams (boxes of components), logo walls (look like marketing), dense text, a long bullet list, a model leaderboard, charts without a unit, any animation that moves without carrying meaning. The storyboard already forbids most of these; keep the "at most three words per label" rule honest (section 9 item 7 lists violations).

---

## 6. Hooks that make a jury remember (question 6)

For each hook: evidence level and how this project uses it in one sentence.

| Hook | Evidence | Use in this project |
|---|---|---|
| A local fact about their own city | Task framing: jurors are the city's officials (VERIFIED, R1); advice "use their language, address their pains" (VERIFIED, dev.to) | Slide 1 states the Bydgoszcz 14-day and requests-per-day numbers, and slide 8-10 mention living in Bydgoszcz. |
| A number about their own workload | ADVICE (no documented case); supported by "be specific" (dev.to) | Ask a city mentor Saturday for the real yearly count of requests and put it on slide 1 with "według Państwa danych". |
| Let a juror test it with their own example | 2025 ZUS and NASK tasks tested on unseen cases (VERIFIED, R1); a 2025 final asked for a live specific case (VERIFIED, Solvro) | At the end of the demo: "Proszę podać dowolny wniosek; zobaczymy analizę" with a pasted request, ready fallback in a prepared file. |
| Quote what a mentor said earlier | ADVICE, no documented case | Slide 10: "Dziś rano pani/pan z urzędu powiedział(a): '...'" only with the speaker's consent and exact words. |
| An honest "what is simulated" slide | VERIFIED: judges prefer being "very direct about what works, what doesn't" (JetBrains); FAQ requires citing earlier resources (R1) | A visible page listing real / simulated / planned, aligned with answer card 7. |
| A concrete pilot offer with dates | 2025 selection by "potencjal wdrozenia" (VERIFIED); no documented example of dated offers | Slide 10: "Pilotaż w jednym referacie: start [data], przegląd po [data], decyzja o dalszym ciągu [data]" with dates agreed with the mentor. |

---

## 7. The day itself for a solo participant (question 7)

Schedule facts from R1 (VERIFIED). Checklist items are ADVICE. Dates: Saturday 21.11, Sunday 22.11.

### Saturday 21.11

| Time | Do |
|---|---|
| 08:00 | Registration, breakfast; ID is checked at entry (R1). Find the table (Hala 2), power, Wi-Fi; plug in with your own power strip and RJ45 adapter. |
| 08:30-10:30 | Open the deck from disk; check second window (presenter) on your screen. Join Discord channel of the task; read `#zapytaj-organizatora`. Ask once there about AI coding assistants and the pre-published brief repository, screenshot the answer (R1 recommendation). |
| 10:30 | Opening ceremony. Do not code; listen for rule changes. |
| 11:00 | Task card published. **First 30 minutes: read it twice. Write the criteria and weights on paper. Re-map this repository to each criterion.** Note IP clause and deliverables (video length, slide limit). |
| 11:30 | Visit the city's stand in Hala 1 (partner zone). Ask for sample requests or an archive. Book mentor slots on the task's Discord channel (R1: one channel per task for booking). |
| 13:00 | Lunch; do not skip. |
| 13:30-16:00 | Build the one end-to-end demo path. Freeze scope at 16:00. |
| 16:00 | Talk (optional). |
| 17:00 | Second mentor round (feedback on the demo, see questions below). |
| 18:00 | Pizza; rehearse the pitch once aloud, timed. |
| 20:00 | **Draft in HackTribe is mandatory**: project name, team name, task, table number, short description, approach, progress, repository. Submit by 19:30. Task choice is frozen after 20:00 (VERIFIED, R1). |
| 21:00-23:30 | Polish the demo; record `demo.mp4` backup; update `metrics.json` only with measured values. |
| 00:00-06:30 | Sleep in the rest zone (camp beds; VERIFIED, R1) in one block of at least 5 hours. Set two alarms. ADVICE: a clear head in the final is worth more than three extra hours of code. |

### Sunday 22.11

| Time | Do |
|---|---|
| 07:00 | Breakfast. Run the full demo once from a clean start. |
| 08:00-09:30 | Final bug fixes only; no new features after 09:00. |
| 09:30 | Export PDF (`tools/deck_pdf.mjs`): check size under 10 MB, links, readable page 1. |
| 10:00 | **Upload everything to HackTribe**: PDF, links, demo video, repository. Open every link in a private window. |
| 11:00 | Hard deadline; nothing counts afterwards (VERIFIED, R1). |
| 11:30 | Talk; rehearse the pitch aloud two times, timed (the presenter window timer counts 5:00). |
| 13:00 | Lunch; light, no sugar peak. |
| 14:45 | Finalists and order announced on Discord. If not finalist: go to the partner's stand and ask for feedback; it is a source of real information. |
| 15:00 | Stage 1 scores visible (VERIFIED, R1 schedule). Read any remarks. |
| 15:15 | Pitch (stage 2): 5 + 5 minutes. Arrive 20 minutes before your turn; test cables and the second window. |
| 17:15 | Awards and closing. Thank the mentors you used. |

### Questions for the city's mentors (ask in Polish, short; ADVICE)

1. "Ile wniosków o informację publiczną wpływa do urzędu rocznie i w jakim kanale (e-mail, poczta, e-Doręczenia)?"
2. "Który moment w obsłudze takiego wniosku zajmuje urzędnikowi najwięcej czasu?"
3. "Jak często odpowiadacie na te same pytania i gdzie szukacie wcześniejszych odpowiedzi?"
4. "Kto decyduje, czy odpowiedź jest pismem, a kto, czy to decyzja?"
5. "Czy w urzędzie jest zasada, że dane osobowe nie mogą opuścić serwera urzędu?"
6. "Gdyby ten asystent działał jutro, czego by Państwu brakowało, żeby zacząć pilotaż?"
7. "Czy mogę przytoczyć Państwa odpowiedź w prezentacji? Czy może Pan/Pani podać dokładne brzmienie?"

Use each answer: a number goes on slide 1; a constraint goes to the answer card; a missing feature goes to the roadmap page; the "can I quote you" answer decides the quote on slide 10.

### What to bring (ADVICE)

Laptop and charger; power strip; RJ45 adapter (R1: wired RJ45 on site); phone hotspot; USB drive (2025 partners handed out files on drives; R1); offline copy of the deck and `demo.mp4`; presentation clicker (optional); second display adapter; earplugs and eye mask for the rest zone; water bottle; ID; printed one-page leaflet with QR links and your name for jurors; printed answer cards (backup if the second window fails); snacks for stage 2.

---

## 8. Why strong projects lose (question 8)

| Reason | Source | Label |
|---|---|---|
| Demo does not work end to end; too much scope | JetBrains; dev.to (kurbaitaev) | VERIFIED |
| Opening with technology or market size instead of the problem | JetBrains; code42cate | VERIFIED |
| Not addressing each criterion explicitly | https://dev.to/code42cate/5-reasons-why-you-are-losing-hackathons-4k70 | VERIFIED |
| Ignoring who the judges are (non-technical judges do not care about the stack) | same | VERIFIED |
| No vision beyond the prototype, or an unhonest vision | same | VERIFIED |
| Dead links, no polish | same | VERIFIED |
| Vague claims about what was built during the event | dev.to (kurbaitaev); HackNation guide asks finalists to say what was implemented during HackNation (R1) | VERIFIED |
| Several features with no single identity | dev.to (kurbaitaev) | VERIFIED |
| Prepared slides when the jury wants a live use case; being unable to improvise | Solvro report | VERIFIED |
| Concept too wide or weakly tied to the challenge | HackNation guide (R1 section 5) | VERIFIED |
| Two close finalists: the jury picks the competitor | Solvro report (no reason given) | VERIFIED |
| No information on whether a pilot is realistic | ADVICE (deployment potential is the stated 2025 decision criterion) | ADVICE |

---

## 9. Critique of the storyboard (question 9)

Source: `docs/05-hackathon/presentation/storyboard.md`. Rules kept: at most six words on screen, movement on every slide, one to three sentences of speech.

### 9.1 Ten improvements

| # | Slide | Problem | Proposed change |
|---|---|---|---|
| 1 | 7, 8, 9 | Three slides (about 27 percent of the spoken words) on forms and the counter, which is outside the stated task and costs "Zwiazek z wyzwaniem" and time (R1 section 5 rates this high risk if prominent) | Merge into one slide "Ten sam rdzeń" with one sentence; move the Opole experience to slide 10 or the answer card; use the saved 60 seconds for the demo and "what is real". |
| 2 | 1 | The range "od kilkuset do ponad tysiąca" is evasive and has no source on screen or in speech | Say the source and the year, or ask the mentor for the real 2025 number; show "Bydgoszcz 2022: 501-1200" as a label. |
| 3 | 4 | Demo has no moment where a juror's own input is used; it says "w minutę" without a measurement (rule 7 forbids unmeasured numbers) | Add a last beat "Proszę podać własny wniosek"; replace "w minutę" with the measured time or "w kilkadziesiąt sekund" only if measured. |
| 4 | new, after 6 | No visible "what is real, simulated, planned" page; it is only in a caption and answer card 7, but judges reward directness (JetBrains) | Add a short slide (or merge into 6) with three words per column: "Działa / Symulacja / Plan". |
| 5 | 5 | Screen text "Dane zostają w urzędzie." is a claim that is true only if the demo uses a local model | Make the demo use the local model or change the screen to "Dane osobowe są maskowane." |
| 6 | 6 | "Zero zmyślonych przepisów i zero wycieków" without N sounds like marketing | Say "Na [N] przypadkach testowych: zero ..." only with the measured N, otherwise drop the second sentence (the cue already says that). |
| 7 | 2, 7, 10 | Label length breaks the three-word rule: "Co to za pismo?" (4), "To już jest w BIP" (5), "Tydzień: test na danych urzędu" (5), "Miesiąc: pilotaż w referacie" (4), "Dalej: integracja z EZD" (4) | Shorten: "Jakie pismo?", "Już w BIP", "Tydzień: test", "Miesiąc: pilotaż", "Dalej: EZD". |
| 8 | 1, 3, 4, 5, 8 | Speech has 4-6 sentences per slide (rule says 1-3), at about 360 words total; with a stage walk-on and a 5:00 hard limit there is no buffer for a demo problem | Cut to about 280 words; each slide at most three sentences; set the timer to warn at 4:00. |
| 9 | 10 | The pilot offer is vague ("w kilka tygodni"); no dates, no named partner | Replace by a dated line agreed with the mentor, or by "Proponuję pilotaż w jednym referacie: [data] start, [data] przegląd"; end the slide with the ask. |
| 10 | 3, 11 | Opening line of the whole pitch does not name the product and the user in the first ten seconds; slide 1 starts with a greeting and a statute | Open: "Szanowni Państwo, dzień dobry. Asystent Urzędnika pomaga w odpowiedzi na wniosek o informację publiczną. Zacznijmy od terminu: czternaście dni." |

Minor technical points: RU lines use the transliteration "урзенник" and "урзенд"; the natural Russian forms are "чиновник" and "мэрия/учреждение". Caption of slide 2 "błąd oznacza skargę do sądu" overstates; "błąd może skutkować skargą" is accurate.

### 9.2 Polish corrections, "was -> should be"

Slide "Say" texts:

| Slide | Was | Should be | Reason |
|---|---|---|---|
| 1 | "Dzień dobry." | "Szanowni Państwo, dzień dobry." | Register for an official jury |
| 1 | "Do Urzędu Miasta Bydgoszczy trafia ich od kilkuset do ponad tysiąca rocznie." | "Do Urzędu Miasta Bydgoszczy wpływa takich wniosków od 500 do 1200 rocznie." | Name the thing (not "ich"); "wpływa" is the clerk's verb; be precise |
| 1 | "To kilka wniosków każdego dnia roboczego." | "To kilka wniosków dziennie." | Shorter; "robocze" adds nothing |
| 2 | "Urzędnik za każdym razem odpowiada na trzy pytania." | "Za każdym razem urzędnik musi rozstrzygnąć trzy kwestie." | "odpowiada na pytania" means answering someone, not deciding |
| 2 | "Pomyłka może skończyć się w sądzie." | "Pomyłka może skończyć się skargą do sądu administracyjnego." | Accurate and matches the caption |
| 3 | "Ale decyduje zawsze urzędnik." | "Ostatnie słowo należy zawsze do urzędnika." | "decyduje" echoes "decyzja" (formal act) and confuses; clearer |
| 4 | "Asystent je rozdziela." | "Asystent rozdziela je na osobne sprawy." | Complete sentence |
| 4 | "Pierwsza informacja jest już opublikowana." | "Pierwsza informacja jest już w BIP." | Matches the label |
| 4 | "Projekt odpowiedzi jest gotowy w minutę." | "Projekt odpowiedzi jest gotowy po [zmierzony czas]." | Rule 7 (measured) |
| 5 | "Treść wniosku jest dla modelu danymi, nigdy poleceniem." | "Model nie wykonuje poleceń zapisanych we wniosku." | Plain language for officials |
| 5 | "Każdy krok zostaje w dzienniku." | "Każdy krok jest zapisywany w dzienniku." | Natural |
| 6 | "Każdą podstawę prawną sprawdza program, w tekście ustawy." | "Program sprawdza każdą podstawę prawną w tekście ustawy." | Word order |
| 6 | "Zmyślony przepis blokuje projekt." | "Projekt z nieistniejącym przepisem zostaje zablokowany." | "zmyślony" is colloquial; "nieistniejący" is neutral |
| 7 | "Ten sam silnik zamienił papierowy wzór wniosku w formularz online." | "Ten sam silnik może zamienić papierowy wzór wniosku w formularz online." | Past tense claims it exists; use only if built |
| 7 | "A jeśli wyśle wniosek, trafia on do urzędu uporządkowany." | "A jeśli wyśle wniosek, ten trafia do urzędu w uporządkowanej postaci." | Matches caption; avoids "on" |
| 8 | "Taki system prowadziłem w 2022 roku w punkcie pomocy uchodźcom w Opolu." | "Podobny system uruchomiłem w 2022 roku w punkcie pomocy uchodźcom w Opolu." | "prowadzić system" is ambiguous; "podobny", not "taki" (honest) |
| 8 | "przy okienku" | "przy stanowisku obsługi" | Register |
| 10 | "Pilotaż w jednym referacie można zacząć w kilka tygodni." | "Pilotaż w jednym referacie można zacząć w ciągu kilku tygodni." | Correct preposition; matches caption |
| 10 | "razem z Państwem" | (correct, keep) | Verified: "z Państwem" is right |

Answer cards:

| Card | Was | Should be |
|---|---|---|
| 1 | "Nigdzie poza kontrolę urzędu." | "Dane nie opuszczają kontroli urzędu." |
| 2 | "Decyzję odmowną zawsze sprawdza prawnik." | "Projekt decyzji odmownej zawsze trafia do zatwierdzenia przez urzędnika, w razie potrzeby przez prawnika." (do not claim the office's process) |
| 4 | "Domyślnie otwarty polski model uruchamiany lokalnie, bo dane zostają w urzędzie." | "Domyślnie używamy otwartego polskiego modelu uruchamianego lokalnie, bo dane zostają w urzędzie." (missing verb) |
| 6 | "przez interfejs programistyczny" | "przez API (interfejs programistyczny)" |
| 7 | "Mówimy to wprost: lista jest na slajdzie i w repozytorium." | "Powiem to wprost. Działają: [lista]. Symulowane są: [lista]. Dane w pokazie są syntetyczne." (the card must answer, not point) |
| 0 | "Kod aplikacji powstał tutaj, w 24 godziny" | "Kod aplikacji powstał tutaj, w ciągu 24 godzin" |

Captions: slide 2 "błąd oznacza skargę do sądu administracyjnego" -> "błąd może skutkować skargą do sądu administracyjnego". Slide 1 caption: "kilka dziennie" is fine only if the range is quoted in the same sentence (it is).

---

## 10. What could not be verified

- Any first-hand juror account of asynchronous stage-1 scoring at HackNation or other Polish public-sector hackathons (not found).
- HackYeah public-sector tracks, GovTech Polska festival and competitions, other Polish city or ministry hackathons: nothing usable found.
- A published winning deck or pitch video of a public-administration hackathon with a non-technical jury (not found; examples in section 2 are general-hackathon evidence).
- EU Datathon scoring criteria and pitch lessons (page opened, not stated).
- Visual-explanation evidence specific to officials (none found; section 5 is advice).
- The city's mentors and jurors for this task, the 2026 criteria and weights, and the real request counts (the card appears at 11:00).
- The Watchdog Polska figure (501-1200 requests in Bydgoszcz in 2022): taken from the storyboard caption, not re-opened.
- Pages of CHIP (2025/11) read only through a search snippet; the Stanford GSB and JetBrains pages were read fully through the fetch tools.

## Sources

HackNation (official and press):

- https://www.gov.pl/web/cyfryzacja/tysiace-pomyslow-24-godziny-i-jeden-cel--usprawnic-panstwo-w-bydgoszczy-zakonczyl-sie-hacknation-2025 (VERIFIED, 2025 judging process)
- https://www.gov.pl/web/cyfryzacja/hacknation-2026-zaczyna-sie-od-dobrego-wyzwania-za-nami-warsztaty-dla-instytucji-publicznych (VERIFIED)
- https://www.chip.pl/2025/12/hacknation-2025-relacja (VERIFIED, winners list, no judging detail)
- https://www.chip.pl/2025/11/hacknation-2025-ogolnopolski-hackathon-wdrozeniowy (SECONDARY, snippet)
- https://solvro.pwr.edu.pl/en/blog/hacknation-2025/ (VERIFIED, one finalist's first-hand report)
- research/01-hacknation-2026-task-rules-jury.md (R1, rules, schedule, jury, VERIFIED there)
- docs/05-hackathon/presentation/storyboard.md (reviewed fully)

Judging and pitching advice:

- https://blog.jetbrains.com/ai/2026/06/how-to-win-a-hackathon-notes-from-the-judging-table/ (VERIFIED via curl)
- https://dev.to/code42cate/5-reasons-why-you-are-losing-hackathons-4k70 (VERIFIED)
- https://dev.to/kurbaitaev/what-judges-actually-score-notes-from-a-year-of-hackathon-judging-3p4l (VERIFIED)
- https://guide.mlh.com/general-information/judging-and-submissions/judging-plan (VERIFIED)
- https://medium.com/circleslife/creating-a-5-minute-kickass-hackathon-pitch-17cdcb42c3bc (SECONDARY, snippet)
- https://www.gsb.stanford.edu/insights/how-manage-public-speaking-anxiety (VERIFIED)
- https://www.italki.com/en/post/g1QF0d98SyVYAzzTMfaIAl (SECONDARY, snippet)

Comparable events:

- https://data.europa.eu/en/news-events/news/meet-winners-eu-datathon-2022 (VERIFIED, format only)
- https://www.data.nsw.gov.au/blog/govhack-2023 (SECONDARY, snippet)
- https://www.finance.gov.au/about-us/news/2025/celebrating-innovation-govhack-2025 (SECONDARY, snippet)
