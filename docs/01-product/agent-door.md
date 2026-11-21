# Two doors: for people, and for people's AI agents

Answers requirements R44–R50 (the owner's fourth brief, 21 November 2026, 10:29–10:33; [`../00-brief/requirements.md`](../00-brief/requirements.md) section G). It extends [`one-visit-package.md`](one-visit-package.md): the need can now arrive through a second entrance, and a digitised form can be filled before any visit. Work package: [`../03-plan/work-packages/WP-B10-agent-door.md`](../03-plan/work-packages/WP-B10-agent-door.md). Facts: [`research/12`](../../research/12-one-visit-package-addendum.md) items 14–16.

## 0. The idea in one paragraph

More and more people let a personal AI assistant run their errands; the owner and his daughter already do. Today such an assistant has to click through the office's web pages in a browser, like a person, which is slow and breaks easily (the owner's own experience). The office should offer a **door for agents**: an official interface (MCP, and the same functions as a documented API) through which any assistant can find the right matter, get the complete set of forms with attachments and fees, reserve a visit, and **fill the digitised forms with the data its owner keeps**, inside a permission the owner gives for that one matter. The person who does not use an assistant keeps the first door: the phone page and the counter. **Both doors lead to the same set and the same rules.** In Polish, for the jury: **„Dwa wejścia, jeden komplet: sam albo przez własnego asystenta AI. Asystent wypełnia, człowiek zatwierdza."**

Why it belongs to the forms task: a form that exists only as a file stays invisible to an assistant. A form that went through stage 0 has a description (fields, validation, the set it belongs to), and that description is exactly what an agent can read and fill. Digitising a form makes it a service for people and, at no extra cost, for their agents.

## 1. Two kinds of forms, two endings

The owner's distinction: some documents are still signed on paper in the office, others are digitised. The set returned to a person or to an assistant says for every form which it is (`channel`).

| Form | What the assistant can do | How it ends |
|---|---|---|
| **Digitised** (`online`): has a description and may be filed electronically | fills a draft of the online form with its owner's data, inside the owner's permission; gets the checker's findings and fixes them | the person opens the draft on their phone, reads it, and **submits and signs themselves** with the state's means; no visit |
| **Paper with a signature in the office** (`counter`): statutory template, or the law wants the person present | prepares the set, "co zabrać" and the visit; fills the person's profile | the visit of `one-visit-package.md`: handoff by QR code, check by exception, print, signature |

One matter can mix both: the assistant files what can be filed and books a visit for the rest.

## 2. What the agent does and what stays with people

| Step | Without an assistant (door 1) | With an assistant (door 2) | Who must act in person |
|---|---|---|---|
| Find the matter | the page "Przygotuj wizytę", or the clerk | `find_matter` with the person's sentence | nobody |
| Complete set | one to three questions on the page | the assistant answers from what it knows and asks only what it does not know; `get_set` | nobody |
| Visit time | the city's booking calendar | `list_slots`, compared by the assistant with the person's own calendar; `hold_slot` | **the person confirms on their own phone**; otherwise the hold expires |
| Calendar | the person writes it down | the assistant adds the visit with "co zabrać" | nobody |
| Filling | typed once into the profile, forms filled from it | the assistant fills the draft of each digitised form from its owner's notes; `fill_draft` | **the person gives the permission first** and reads the result |
| Submitting a digitised form | the person, online | **the person**, never the assistant | the person |
| Handoff for paper forms, identity, signature | at the counter | at the counter | the person and the clerk |

The assistant saves the person's time. It never signs, never submits and never stands in front of the clerk.

## 3. Seven rules that make the door safe

1. **One source of truth, two doors.** The agent interface calls the same catalogue, set resolver, form descriptions and checker as the phone page and the clerk's screen. An assistant can never get a different set or a different rule than a person.
2. **Public tools are read-only and carry no personal data.** Finding a matter, resolving a set and listing slots need no login and accept no identifying data; inputs that look like identifiers are rejected. This is the pattern administrations already use for open data (research/12 item 14).
3. **Whatever binds the person needs the person.** An agent can hold a slot for minutes and fill a draft; the booking exists and the application is filed only when the person confirms on their own device. Identity and signature stay with the person.
4. **Personal data pass only inside a permission the person gave.** The person approves, on their own phone, a permission for one matter, for a limited time, with one right: to fill the draft. With it the assistant may send the fields that the set needs and nothing else; the schema refuses any other field. The draft is stored encrypted, can be opened only by that person, and is destroyed when it is submitted, taken to a visit, withdrawn or expired.
5. **Answers are data with sources.** Every item returned (form, attachment, fee, rule, finding) carries the address and date of the service card or the rule it comes from, and a version. Free text that could read as an instruction to an assistant is not returned.
6. **Fair use and a trail.** Rate limits; few open holds and drafts per permission; everything expires; every call is logged with the permission's id and without the values. The office knows it is talking to an agent, which browser automation never tells it.
7. **The permission grows into a mandate.** In the prototype the permission is a short-lived code approved on the phone (the pattern of approving a device on a second screen). In a real deployment it is an identity-bound authorisation through the state's login or wallet, which the protocol provides for (research/12 item 15), and it can then cover more: filing, paying, collecting. The owner's earlier open project applies the same idea to purchases: the agent acts inside a mandate signed once, within limits, with an audit log, and hands every strong authentication back to the person.

## 4. The interface

One small service; MCP tools and the same functions under a documented HTTP API.

| Tool | Needs a permission | Input | Output |
|---|---|---|---|
| `find_matter` | no | a sentence or keywords, language | up to five matters: id, Polish title, one line, service-card address |
| `get_set` | no | matter id, answers, composition (roles and counts) | forms with `channel` and copies per person; attachments to bring; fees; open questions with closed answers; the profile fields the set needs; notes; source and date of every item |
| `list_slots` | no | matter id, date range | free slots of the demo calendar |
| `hold_slot` | no | slot id, matter id, answers | hold id, expiry, a confirmation address and QR code for the person |
| `get_visit` | no | hold id | state, time and place, "co zabrać", a calendar entry, the address of "Przygotuj wizytę" with the set pre-selected |
| `form_schema` | no | form id | the fields of a digitised form: path, Polish label, format, validation, who fills it |
| `request_permission` | no | matter id, the forms to fill | request id and an approval address and QR code for the person; the person sees the matter, the forms and the lifetime, and approves or refuses |
| `fill_draft` | **yes** | permission, form id, person role, values by field path | the checker's findings (blockers, warnings, proposed fixes), the share of fields filled, the address where the person reads the draft |
| `draft_status` | **yes** | permission | `filled`, `read`, `submitted`, `taken_to_visit`, `withdrawn`, `expired` |

On the phone (visitor app): „Potwierdź rezerwację"; „Pozwól asystentowi wypełnić wniosek" with the list of forms and "ważne 30 minut"; „Mój wniosek": the filled online form generated from the description, editable, with the findings; then „Wyślij" for a digitised form (in the prototype a simulated filing, labelled as such) or „Zabierz na wizytę" (the draft moves into the phone's profile and leaves the server).

## 5. What the jury sees (optional third part of the demo, about forty seconds)

1. On the laptop, an ordinary AI assistant with the office's interface connected. The owner says: „Chcę zameldować siebie i córkę. Przygotuj wszystko i umów wizytę, kiedy mam wolne."
2. The assistant finds the matter, asks the one thing it cannot know, lists the set with "co zabrać", proposes a slot that is free in the owner's calendar and holds it.
3. The phone shows one screen: „Potwierdź rezerwację" and „Pozwól asystentowi wypełnić wnioski". The owner taps.
4. The assistant fills the drafts from the owner's (synthetic) notes; the checker returns one finding; the assistant fixes it and reports: "gotowe, sprawdź na telefonie".
5. Cut to the counter of part two: the session opens with the set marked „przygotowane przez asystenta mieszkańca"; check by exception, print, signature. For a form with the `online` channel the phone shows „Wyślij" instead, and the owner presses it himself.

Say on stage: „Ten sam komplet, te same reguły. Asystent wypełnia, człowiek zatwierdza." If the package is not built, this stays one page of the reading version marked as planned, and nothing is said about it in the live demo.

A second example for conversation, from the catalogue: the need "change my daughter's first name" matches two service cards (UMB40 and UMB41, the second only within six months of registering the child). An assistant that asks one question picks the right one; a person browsing the portal has to work it out alone.

## 6. Why this speaks to the partner

- The partner's generator publishes digitised forms and pre-fills them from registers for a logged-in citizen (research/12 item 11). An agent interface over the same form definitions is the next channel for those forms, not a competing product.
- The government app already has a virtual assistant that finds services and explains formalities but cannot prepare a case (research/11). The same interface would let **that** assistant return a complete set and a filled draft. The door is for every assistant, the state's own included.
- Administrations have started to publish official interfaces of this kind for open data (France's national data portal, February 2026; research/12 item 14). For the **services** of a local office none was found. The step from "data for agents" to "services for agents" is the new part.
- Today assistants operate public websites through a browser, as a person would. An official door is faster for the resident and better for the office: it knows who is an agent, limits it, logs it, and gives it only structured data.

## 7. What we do not claim

- No connection to the city's real booking system, to electronic delivery or to the state's signature: slots are a demo calendar, filing is simulated and labelled.
- No assistant submits, signs, pays or proves identity. It fills a draft; the person does the rest.
- No statement that the state supports or plans such an interface.
- No claim about which assistants work with it beyond the one shown; the interface follows an open protocol and a plain HTTP API.
- No claim about how many people use assistants; "coraz więcej osób" and the owner's own practice, nothing else.

## 8. Order of value

After the set resolver of WP-B7 exists: `find_matter` and `get_set` first (they already make a live conversation possible); then the demo calendar with hold and confirmation; then permission, `fill_draft` and „Mój wniosek"; then `draft_status` and the calendar entry. Nothing here precedes the M2 gate.
