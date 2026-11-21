# R13 — Census of the city's forms archive, and the facts behind the opening of the presentation

Written on 21 November 2026 between 10:50 and 11:30 local time, that is partly after the coding start at 11:00. It is event-time material.

Labels: **MEASURED** = produced by a script of this repository on files we hold; **VERIFIED** = read in a primary source on the date given; **SECONDARY** = a third party reports it.

## Summary for builders

1. **The whole archive was read by a program in 142 seconds.** 661 unique documents (676 files, 224 service cards with at least one file). MEASURED.
2. **In 461 of them (70 %) the places to fill can be found without looking at pixels**: 29 PDFs declare their own fields (2,319 fields), 186 PDFs have a text layer plus boxes or dotted leaders, 246 word-processor files show them after conversion. Together 1,310 pages and 18,233 leaders and boxes. MEASURED; the count of leaders and boxes follows a simple rule and is not a count of approved fields.
3. **24 documents are scans** and need reading from pixels. 173 show no places by the rule: information sheets and clauses, or forms built from table cells; they need one look. MEASURED.
4. Only 6 documents are attached to more than one service card (the data-protection clause to 7, the two residence forms to 4 each): inside one office reuse between cards is small. The reuse that matters is **between offices**, see item 6.
5. **France opened public data to AI assistants through an official interface** (an experimental MCP server of the national open-data platform, February 2026, read-only, about 74,000 datasets). VERIFIED on the platform's own page; the state's digital directorate later stressed that it opens no data that were not already public. It is the precedent for "an official door for agents"; nobody should say it covers services.
6. **The residence-registration template is fixed by a national regulation**, the same in every commune. VERIFIED. Poland has **2,479 communes** (state on 1 January 2026). VERIFIED. So a description of that template, made once, fits every commune office. Do not generalise: most of the city's documents are the city's own templates.

## 1. The census

Tool: [`tools/forms_census.py`](../tools/forms_census.py). Input: the archive attached to the release `pre-event` (templates downloaded from the city's service cards on 21 November 2026, listed in its `MANIFEST.json`). Output: [`data/forms-census.json`](../data/forms-census.json), [`data/forms-census.csv`](../data/forms-census.csv). Run on 21 November 2026, 10:55–10:58, on a machine with two cores. No model was used.

| Measure | Value |
|---|---|
| Entries in the manifest / files present | 678 / 676 |
| Unique documents (by SHA-256) | 661 |
| Service cards with at least one file | 224 (of 275 cards in the catalogue) |
| By type | 322 PDF, 142 DOCX, 117 DOC, 77 RTF, 2 spreadsheets, 1 image |
| Pages in all documents (word-processor files after conversion) | 2,107 |
| `fillable_pdf` | 29, with 2,319 declared fields |
| `vector_form` | 186 |
| `word_form` | 246 |
| First pass possible from geometry and text (the three classes above) | 461 documents, 1,310 pages, 18,233 leaders and boxes; median 19 per document |
| `scan` | 24 |
| No places found by the rule | 173 (83 PDF, 90 word-processor) |
| Named like a form ("wniosek", "zgłoszenie", "oświadczenie", …) | 379 of 661; 326 of the 461 |
| DOCX files that declare their own form fields | 4 |
| Time | 17 s conversion with LibreOffice, 125 s measurement; 142 s in total |

Limits of the method, to be said whenever the numbers are used:

- "Leaders and boxes" counts runs of dots or underscores in the text and small drawn rectangles (6 to 26 pt). A leader that wraps counts twice; every cell of a boxed field counts once (a PESEL field is 11); table cells and drawn lines are not counted at all. It shows that there is something to find, and roughly how much; it is not the number of fields.
- Classes are assigned by thresholds (three or more places; fewer than 40 characters of text per page means "scan"). A few documents sit on the wrong side; the worklist lets a person see each one.
- 29 fillable PDFs among 322 here does not contradict "1 of 32" in `research/03b`: that sample was chosen by hand from popular matters. Use the new number for the whole archive and say which is which.
- The time is the time to read geometry and text. It is not the time to make approved descriptions.

## 2. An official interface for AI assistants: the French precedent

- The national open-data platform published its own announcement "Expérimentation autour d'un serveur MCP pour datagouv" (<https://www.data.gouv.fr/posts/experimentation-autour-dun-serveur-mcp-pour-datagouv>, read 21 November 2026): an experimental MCP server lets a chatbot work with French public data; the page also warns that many servers claim a link with the platform without being official. VERIFIED.
- Launch date 25 February 2026, public endpoint without a key, read-only, open source under MIT, about 74,000 datasets: reported by several outlets (for example <https://next.ink/226931/data-gouv-lance-son-serveur-mcp-les-ia-accedent-directement-aux-donnees-publiques-francaises/>, <https://www.banquedesterritoires.fr/datagouv-facilite-lacces-des-ia-generatives-aux-donnees-publiques>; read 21 November 2026). SECONDARY, consistent with each other and with the repository `datagouv/datagouv-mcp`.
- On 28 July 2026 the interministerial digital directorate published a review of the server and corrected a common misreading: it opens no new data, only what the platform already lists (reported by <https://www.actuia.com/index.php/acteur/dinum/>, read 21 November 2026). SECONDARY.

How to say it: "France gave AI assistants an official way to public **data**. We propose the next step: an official way to public **services**, with a person confirming every act." Never: "nobody has done this", "first in the world", "France lets agents file applications".

## 3. One template, every commune

- Regulation of the Minister of the Interior and Administration on the templates and the way of filling in the forms used for the registration duty, consolidated text Dz. U. 2022 poz. 2070, issued under art. 39 ust. 1 of the Act on population records: § 1 lists the forms; "Wzór formularza zgłoszenia pobytu stałego jest określony w załączniku nr 1". <https://api.sejm.gov.pl/eli/acts/DU/2022/2070/text.html>, read 21 November 2026. VERIFIED. (The descriptor `data/form-descriptor.example.json` already records the act and its status.)
- Number of communes: "2 479 gmin" and 314 districts, state on 1 January 2026, Ministry of the Interior and Administration, <https://www.gov.pl/web/mswia/baza-jst>, read 21 November 2026. VERIFIED. Statistics Poland gives the same number for 1 January 2025 (<https://stat.gov.pl/statystyka-regionalna/jednostki-terytorialne/podzial-administracyjny-polski/>).
- Not checked: how many of the city's 661 documents are national templates and how many are the city's own. Until someone counts, say "wzory ustawowe" (templates fixed by law) for the first group and give the residence form as the example.

## 4. What these facts change

| Fact | Consequence in the repository |
|---|---|
| 461 of 661 documents can get a first pass without a model | WP-B11 part a is plain engineering and can run over the whole archive during the event; the deck may show a real funnel |
| 24 scans, 173 without places | they go last; the funnel shows them as their own group instead of hiding them |
| Reuse inside one office is small | the argument "describe once" is about other offices and national templates, not about the city's own cards |
| Public data already have an official door for agents in one EU state | page 2 of the reading version; `docs/01-product/agent-door.md` §6 |

## Sources

Listed in the sections above with the date of reading. Files of the census: `data/forms-census.json`, `data/forms-census.csv`.
