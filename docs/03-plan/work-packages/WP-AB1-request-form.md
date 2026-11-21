# WP-AB1 — The bridge: the public-information request as a digitised online form

Kind: by spec (the onboarding step may be done by hand for this one form if WP-B6 is not built) · Model tier: middle · Depends on: milestone M2 (Module A works end to end), WP-A3 (search) · Branch: `wp/AB1-request-form` · Milestone: M3 or M4

## Goal

Close the loop "from request to answer" in one demo and join the two matching hackathon tasks honestly: the city's own PDF template for a public-information request becomes an online form; a resident who uses it is shown where the information is already published; a request that is still sent arrives at the clerk's desk already structured.

## Read first

1. `docs/01-product/scope-decision.md` §1a
2. `research/02-udip-law-process-taxonomy.md`: the verdict on the city's template (what fields it has) and the rule that no form is mandatory
3. `docs/02-architecture/api-contract.md` (`POST /cases`, `GET /kb/search`, `POST /public/analyse`)

## Build

1. A public page `apps/clerk-web/src/features/public/request-form` (or a tiny separate app): fields mirror the city's auxiliary template: what information is requested (free text, with "add another question"), the form and way of disclosure (options from the template), optional contact data with a plain statement that giving personal data is not required to ask, consent texts exactly as the template has them. Polish, accessible, phone-first, one field per row.
2. **"Already published" hint**: while the resident types a question (debounced) the page calls the knowledge search limited to public sources and shows up to three places where the answer may already be (title, short passage, address). Buttons: "this answers my question" (nothing is sent; a counter increases) and "I still want to send the request".
3. On sending: the request is registered through `POST /cases` with `channel = online_form`, the questions already separated, the requested form of disclosure filled; the resident gets a confirmation with the two deadline dates and a case number.
4. The clerk's desk shows such a case with a badge "structured" and skips extraction.
5. A printable PDF of the filled request on the city's template (overlay on the original file) for a resident who wants paper: uses the forms engine if WP-B1 exists, otherwise a simple overlay for this one template.
6. A small statistic on the dashboard: questions answered by the hint without a request, and requests received structured.
7. Abuse limits: rate limit per address, size limits, the same pseudonymisation and injection flags as any other intake.

## Acceptance

- [ ] End-to-end test: a question whose answer is in the stored public pages shows the hint with the right address; choosing "this answers my question" creates no case.
- [ ] A sent request appears at the desk with separated questions and both dates; the analysis runs without the extraction step.
- [ ] The page passes the accessibility scan and works at 320 px width with the keyboard only.
- [ ] No request is refused for lack of personal data; the page says so.
- [ ] Negative control: with the knowledge search switched off the hint area says "search unavailable" and sending still works.

## Why it matters for the pitch

It is the slide "Mniej wniosków. Lepsze wnioski." and the answer to "why do you also talk about forms": the same engine digitised the city's own form, and the result removes repeated work before it reaches a clerk.
