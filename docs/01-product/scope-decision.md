# Scope decision: what to build for the jury, and what the wider platform is

Answers requirements R26, R27, R28. Facts come from [`research/01-hacknation-2026-task-rules-jury.md`](../../research/01-hacknation-2026-task-rules-jury.md) and [`research/02-udip-law-process-taxonomy.md`](../../research/02-udip-law-process-taxonomy.md), both checked on 20 November 2026. Re-check this page at the 11:00 gate on Saturday, when the full task cards are published.

## 0. Current decision (owner, 21 November 2026, morning)

**Primary track: the forms product for the task "Cyfryzacja formularzy" (Centralny Ośrodek Informatyki).** The owner's idea fits that task directly, and he wants the jury to see a working product with two sides, visitor and clerk, not slides of theory. Therefore:

- **Module B is built first** (form onboarding with AI, the phone page with the QR handoff, the clerk's counter view, the checker, the print on the original template). Timeline: [`../03-plan/roadmap.md`](../03-plan/roadmap.md), "Timeline for Track B".
- **Module A (the city's task) stays fully specified** as the alternative submission and as the back-office example: the city's own request template is the first form digitised in the demo (work package WP-AB1), which keeps both tasks joined (§1a).
- The task is fixed in the submission draft on Saturday by 18:00, after both full task cards have been read at 11:00. If the forms task card asks for something this product cannot honestly show (§5, "Switch back to A"), the build switches to Track A; everything for it is ready.
- Two sites and two decks exist: <https://formularze.flyreelstudio.eu> (forms task) and <https://urzad.flyreelstudio.eu> (city's task).

Sections 1–3 below were written for Track A as the default and remain valid as its reasoning.

## 1. The decision in one paragraph (Track A)

Build and show **a complete assistant for access-to-public-information requests** (Module A). Present the counter product, "data entered once, forms pre-filled" (Module B), as the next process on the same core: one slide in the pitch, a separate section in the repository, and a small live slice only if Module A already passes its gate. Do not present the wide platform as the product.

## 1a. The unifying idea: from request to answer, one engine

The owner asked for one system that honestly joins the two matching tasks instead of a stretched "bonus" (follow-up brief of 21 November). The join is real, because both tasks are the same pipe seen from two ends:

| | The resident's end | The office's end |
|---|---|---|
| A letter with no form (a public-information request) | writes freely, often asks for what is already published | must read, classify, find, draft, keep the deadline: **the city's task** |
| A paper or PDF form | fills the same data again and again | must turn each form into an online service: **the task "Cyfryzacja formularzy"** |

One engine serves both: it understands documents, it keeps a registry of templates (a response document with its mandatory elements is a template in the same sense as an application form with its fields), it checks a filled template with rules and a model, it protects personal data, it waits for a person's approval and it logs.

**The bridge that makes it one demo.** The city publishes an auxiliary PDF template for public-information requests. The form-onboarding step turns that PDF into an online form in minutes. The resident who opens it sees, before sending, where the information is already published; if the request is still sent, it arrives structured (separate questions, chosen form of disclosure, contact). The clerk's assistant then starts from clean data. So the loop closes:

```
PDF template ──(digitised by the engine)──▶ online request form ──▶ fewer and cleaner requests
      ▲                                                                   │
      │                                                                   ▼
published answers ◀── approved answer ◀── draft with checked basis ◀── analysis and deadlines
```

For the city's jury this is "less repeated work at the source", a pain the task text does not even name. For the makers of the government's e-services it is "from a need to an online service in minutes" with a working back office behind it. The same build, two emphases.

**Consequence for the plan:** work package WP-AB1 (the public-information request as a digitised online form with a "already published" hint) is built after the Module A gate, before any counter work. It is the first thing shown from Module B.

## 2. Who the customer is and what hurts

The challenge names the user ("pracownicy urzędu"), two functions ("analiza wniosków", "przygotowywanie odpowiedzi"), two qualities ("inteligentny i bezpieczny") and two outcomes (shorter handling time, relief from repeated work). The jury is chosen by the city. The two city-hall mentors on the official list lead the City Council Office and the Social Communication unit: people whose desks receive letters of every kind and who must decide what each one is.

What hurts in this process (from the law and the city's own procedure page):

| Pain | Why it hurts | What the assistant does |
|---|---|---|
| The 14-day clock | Counted from filing; one extension only if announced inside those 14 days, two months at most. A late letter loses in court even when the answer is "we do not hold it". | Both dates the moment a request is registered; warnings; a ready extension notice |
| "What is this letter?" | A request needs no form, often no signature, and arrives mixed with complaints, press questions and councillors' questions | Classification with reasons; the clerk confirms with one click |
| Letter or decision | Only refusal and discontinuance are administrative decisions with full formal requirements; everything else is a letter. Mixing them up is a classic defeat. | The right document type with its mandatory elements, from templates |
| Repeated and mass requests | The same question returns; campaigns send one request to every commune | Search over earlier answers; duplicate and campaign detection |
| Where is the information | Already published, held by another unit, or not held | Search over the public bulletin and the registers; routing suggestion |
| Personal data in documents to disclose | Blacking out by hand, plus a partial refusal for the hidden part | Detection and masking proposals, a redaction log, a reminder about the decision |
| Legal risk | Wrong legal basis, missing elements, non-disclosure is a criminal offence | Every cited provision checked by code against the stored act; nothing leaves without approval; full audit trail |

Bydgoszcz reported between 501 and 1,200 such requests for 2022. That is two to five every working day, each with a statutory deadline.

## 3. Why not lead with the counter platform

- Fit with the task weighed 30 % in last year's Bydgoszcz task card and in the closest "assistant for officials" card; completeness another 10–20 %; deployment potential 20–40 %. The 2026 weights are unknown until 11:00, but the pattern is stable.
- Jurors have a few minutes per project in the first stage. They must see a public-information request being analysed and answered on the first screen.
- Scanning identity documents and showing family data in a demo invites hard privacy questions that have nothing to do with the task.
- The organisers warn against concepts that are "too broad or weakly matched to the challenge".

The platform still helps: "the same engine serves the next process" raises the deployment-potential score. It is true architecturally, not a slogan: both modules use the same intake, personal-data service, document engine, rule checks, model gateway, approval flow and audit log.

## 4. One database of everybody for many institutions? (R27)

The owner's wish: "I come with a request and the form is printed with everything already in it, in any institution." A new central database of residents' data run by a supplier is not the way to get there:

- A public body may process personal data only for a purpose and on a legal basis given by law; "it may be useful later in another office" is neither.
- The state already runs the registers (identity, civil status, vehicles). Polish administrative procedure already forbids an office to demand proof of facts it knows or can check in registers it can reach electronically. The gap is in practice and tooling, not in missing databases.
- One more copy of everybody's data is one more thing to breach.

What works instead, and what this project builds toward:

1. **The person carries the data.** The profile lives on the person's phone (later: in a government wallet). At each office the person shares only the fields that the chosen case needs, for that case, for minutes.
2. **The office checks, not collects.** Shared data is confirmed against the document or a register by the clerk; the system records where each value came from.
3. **Centralise the forms, not the people.** An open registry of form descriptions (fields, rules, coordinates on the approved template, legal basis, version hash) contains no personal data and can be shared by every office in the country. A form described once works everywhere.
4. **A standard profile.** One documented data schema that any office system can accept.

For several institutions this gives the owner's result without a shared database. The legal anchors and the state of the government wallet are in [`research/04-mobywatel-identity-once-only.md`](../../research/04-mobywatel-identity-once-only.md) (to be completed; see STATUS).

## 5. The task choice (owner decides, at the 11:00 gate)

There are 15 tasks. Two matter here. One participant alone can submit one project; a second project needs a different team leader.

| | **A. Miasto Bydgoszcz: "Inteligentny asystent urzędnika"** | **B. Centralny Ośrodek Informatyki: "Cyfryzacja formularzy"** |
|---|---|---|
| Published text | assistant for analysing public-information requests and drafting answers | "how AI can support the development of modern public services … make the path from a need to a convenient online service simpler and faster" |
| Prize | 15,000 PLN | 25,000 PLN |
| Jury | city officials; value ease of use, safety, readiness for deployment | the institution that builds the government's e-services and the mObywatel app; likely technical |
| Fit with the owner's original idea | the idea must be re-aimed at public-information requests | close: turning paper forms into online services, pre-filling, the QR handoff, the 2022 experience |
| Fit with what is prepared here | best prepared: law, decision tree, taxonomy, jury questions | forms catalogue, lessons from 2022, forms engine plan; the full card is unknown |
| Likely competition | lower prize and a legal topic: probably fewer teams | popular partner and higher prize: probably more and stronger teams |
| Side benefit | the owner lives in Bydgoszcz; a pilot with his own city hall is realistic | direct contact with the makers of mObywatel, to whom the QR prefill idea should be proposed anyway |

**Default since the owner's decision of 21 November: B** (see §0). Reasons: the idea is his own and he has run it in real life (Opole, 2022); the repository holds measured facts about forms that speak directly to the makers of e-services (275 service cards, 710 files, one fillable PDF among 32, a profile fills 55–60 % of simple forms); the demo is tangible (a phone, a clerk's screen, a printed form); and the partner builds the government app into which "fill the form from the wallet" belongs. Known risks: a higher prize attracts more and stronger teams, and the jury is technical: the demo must really work and every claim must be exact.

Likely criteria (proxy: the same partner's task card of 2025): fit with the task 25 %, deployment potential 25 %, validation and data security 20 %, user experience and ergonomics of work 15 %, innovation and presentation 15 %. The product answers them with: the form onboarding flow (fit), the open registry and the pilot offer (deployment), the checker plus end-to-end encryption and minutes-long lifetime (validation and security), the two-sided live demo (experience), the QR handoff prepared for the government wallet (innovation).

**Switch back to A** if at 11:00 the forms task card turns out to require something this product cannot honestly show within 24 hours (for example work inside a specific internal tool of the partner, or data we do not have), or if the city's card and mentors show a clearly better chance. Track A's reasoning: it was the first choice, it is equally prepared, the jury is local and practical, and competition is probably weaker. Whatever is chosen, visit the other partner's stand.

**Two tasks at once?** The rules allow a team at most two tasks, one separate project per task, and the second project needs a different team leader; the organisers "strongly discourage" one project for two tasks. A participant alone can therefore submit one project. What is possible and sensible:

1. **Build once, decide late.** Until Saturday 18:00 the build follows the unified plan (Module A plus the bridge WP-AB1), which serves both tasks. The task is fixed in the submission draft by 20:00 and cannot be changed afterwards.
2. **Show the other task's value inside the chosen one.** In the city's task the bridge is the slide "less work at the source" and the roadmap; in the forms task the clerk's assistant is the proof that a digitised form has a working back office.
3. **Talk to both partners early** (their stands and mentors): what each says about their real pain decides the emphasis better than any guess made tonight.
4. **Second submission only with a second person.** If someone joins the team and can lead a second project, the forms slice (WP-B6, WP-B1, WP-AB1) can be submitted to the forms task as its own small project with its own draft by 20:00. It doubles the submission work and the pitches may overlap in time; do it only if Module A is already safe.

## 6. What would change this decision

| Trigger at the 11:00 gate | Change |
|---|---|
| The city's card rewards breadth ("everyday work of the administration" beyond requests) | Add one second use on the same engine: recognising that a letter is not a public-information request and routing it (complaint, press question, councillor's question) |
| The city provides its own sample requests or an archive | Make "tested on unseen requests" the centre of the demo; build the paste-a-request page first |
| A criterion on open or free models | Make the local Polish model the default in the demo; cloud models only as an option |
| The card requires the jury to try the solution in a browser | A public demo address becomes a milestone deliverable, with synthetic data only |
| The intellectual-property clause demands exclusive transfer | Keep product code in a separate repository created at the event; this brief stays open and is cited |
| The city shows interest in the counter module | Build the Module B slice after the Module A gate and show it live |

## 7. What the jury sees (order of the demo)

1. An e-mail request arrives. It has three questions: one is already published, one needs data from a unit, one touches personal data.
2. The assistant splits it, classifies each part with reasons, shows both deadline dates.
3. It finds an earlier answer to a similar request and the page where the published part is.
4. It drafts the reply and the notice, each legal basis clickable and checked; text written by the model is marked.
5. Personal data is masked before anything is sent to a model; the screen shows what the model actually received. A request with a hidden instruction is flagged.
6. The clerk edits, approves; the audit entry appears; the document is exported.
7. One slide: the same core at the counter, and the proposal "centralise forms, not people".

What is real and what is simulated is said on a slide. The list is kept true in `docs/05-hackathon/jury-qa.md`.
