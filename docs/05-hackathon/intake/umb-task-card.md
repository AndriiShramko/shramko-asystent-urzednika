# Task card digest: "Inteligentny asystent urzędnika" (Miasto Bydgoszcz)

Subtitle of the card: a generator of answers to public-information requests with a calendar (organiser) of requests. Source: the two PDFs in the organisers' task folder, read 21 November 2026, 11:15. Digest in our words; ids are ours. Prize: 15,000 PLN gross.

## What they ask for, in one sentence

A simple, safe application for the officials who handle public-information requests in the city hall: a calendar of requests with deadlines, a module that drafts the answer, and a module that proposes and applies anonymisation. Their stated aim: preparing an answer in minutes instead of days.

## Assumptions the prototype must meet (U-REQ)

| Id | Requirement |
|---|---|
| U-1 | Model and environment: during the hackathon an openly available AI may be used; the target program must run on a closed model without internet access and be able to learn from the data put in (acts, their updates, requests, answers) |
| U-2 | Input is uploaded by the official by hand, as a file (PDF or Word) |
| U-3 | Calendar of requests: a table tied to a calendar, ordered from the oldest, with the days left to answer; requests due today and tomorrow highlighted. Suggested columns and states: answer in preparation; "kwerenda" (extra time); answer sent; initials of the handler; running number; request number; short subject; date received; deadline; date answered; choice of the year |
| U-4 | Anonymisation: the module suggests what should be hidden in the finished answer, for example grey first and black after the official accepts; it proposes and then removes excess data such as personal data |
| U-5 | Automation of routine, repeated steps |
| U-6 | Search of the archive of earlier answers to find similar requests |
| U-7 | Hints on the best path to get the answer from particular departments |
| U-8 | Draft of the answer: after the official uploads the departments' replies the program prepares a draft letter that the official checks (against errors and hallucinations) |
| U-9 | Nothing is ever sent automatically, neither to departments nor outside |
| U-10 | It supports decisions, generates drafts, anonymises and, through the calendar, keeps deadlines |
| U-11 | No integration with any office system is needed (the card names SIDAS) |
| U-12 | A support tool only: the official always decides |

## The flow they sketch (U-FLOW)

1. The tool "learns" from uploaded acts, archived answers, orders. 2. The official uploads a request. 3. The tool analyses it and lists similar requests of the last year. 4. It proposes the departments to ask (lists: <https://bip.um.bydgoszcz.pl/artykuly/198/wydzialy>, <https://bip.um.bydgoszcz.pl/artykuly/1158/biura>). 5. The request enters the list; the official accepts deadline, initials, dates, number. 6. Outside the tool the departments reply; the official uploads the replies into the case. 7. The tool prepares a draft with places marked for possible anonymisation. 8. The official accepts or unmarks them. 9. The tool produces the answer as DOC or TXT. 10. The official checks the substance and corrects. 11. At every step the status of the case is updated: no action; questions sent to departments; "kwerenda" with days; answer prepared; answer sent.

## Submission (U-SUB)

A film of at most 3 minutes and a presentation of **at most 10 slides** that contains: project name and team; the problem and why it matters (faster work, protected data); how the solution works and which technology it uses; proof that the prototype works (upload, processing, draft); for whom; how it could run permanently in the city hall; the main tools used; **a statement whether the prototype will run in a closed system without internet and large language models, naming a specific model that can run there**.

## Technical expectations (U-TECH)

Easy for any official; takes a PDF or Word file, searches a local base, suggests the department, generates a draft, anonymises. The calendar shows **10 test requests** from oldest to newest and highlights the most urgent. Stable and working, not a plan; technology that is available and not expensive. Concept must show fully local operation later; safe (no leaks); easy to install and run in the city; works for hundreds of archived documents.

## How the jury tests (U-TEST)

They upload a sample request and check that similar cases are found; give a department's reply and check the draft; **upload a file with personal data and check that it is hidden**; judge ease of use, stability and real usefulness; look at the ordering and marking in the calendar; judge how easily data, updated acts and archived answers are loaded.

## Criteria (U-CRIT; the card calls them "example criteria")

Fit with the challenge 30 %; security and effective anonymisation 20 %; ease of use and usefulness for the official 20 %; completeness and quality of the working prototype 30 %. The card adds that the highest marks go to solutions that are new, inventive, safe and likely to be really used in Bydgoszcz.

## Regulations (U-REG)

Jury of at least three; **at most three teams present**, the winner is chosen among them. Winners sign a transfer of economic copyrights and hand over the source code with a description; external solutions used must be named in the presentation. **The owner reads the template before submitting; this file is not legal advice.**

## Fit with our Track A (Module A, packages WP-A1…A10)

| Card | Our specification | Gap to close |
|---|---|---|
| U-2 upload PDF or Word | WP-A4 intake, WP-A6 desk | none |
| U-3 calendar table with deadlines and highlights | WP-A1 deadline calculator, WP-A6 inbox with clocks, WP-A8 dashboard | add the exact columns and the five statuses of U-FLOW 11; year filter; ten synthetic test requests; highlight "today" and "tomorrow" |
| U-4 anonymisation grey then black | WP-A7 redaction helper, WP-A2 personal-data service | make the two-step colour the visible behaviour; the jury uploads its own file with personal data: test on unseen text |
| U-6 similar requests | WP-A3 knowledge base, WP-A8 similar cases | limit the first list to the last year, as the card says |
| U-7 which departments to ask | not specified | **new**: load the two public lists of departments and offices; propose departments per question with a reason; small package |
| U-8 draft from the departments' replies | WP-A5 draft generator | input is the uploaded replies of departments, not only the knowledge base; export DOC or TXT |
| U-9, U-12 nothing sent, the official decides | rule 7 of `AGENTS.md`, WP-A6 approve | none |
| U-1 closed model later, learning from uploaded data | WP-A2 gateway with `local` provider; ai-layer §2 names open Polish models | slide with the named model; "learning" shown as loading acts and archive into the local knowledge base |
| U-TEST loading of acts and archive | WP-A3 ingest | a visible "Baza wiedzy" screen: upload an act or an archived answer and see it used |
| U-SUB ten slides, three-minute film | deck of 11 slides in `site/deck/` | cut to ten; add the mandatory contents list |

Cloud models are allowed for the prototype by U-1 because the test requests hold no real data; `AGENTS.md` rule 1 still applies (synthetic data only).
