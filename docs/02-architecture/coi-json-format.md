# The partner's form format: what the converter must write

Written on 21 November 2026 (event time) from the partner's materials for the task "Cyfryzacja formularzy": their schema file, their description of the JSON fields, their technical rules for configuring forms, their design standard (29 pages), the dictionaries note, the initial-data note, and one complete sample (a paper form in eight formats with the JSON the partner made from it). The originals are in [`data/coi/`](../../data/coi/README.md). Everything below is our own description; where the materials disagree with each other it says so.

Executable form of this document: [`contracts/coi/form.schema.json`](../../contracts/coi/form.schema.json) and `python tools/coi_lint.py FILE.json` (the partner's first sample passes both; five negative controls fail as they should; the second sample does not pass the schema as it stands, see section 11).

**Later decisions that change statements below:** [`../03-plan/DECISIONS-forms-track.md`](../03-plan/DECISIONS-forms-track.md). The design built on this format: [`converter-design.md`](converter-design.md).

## 1. What a conversion really is

The sample makes it plain. The paper form "Wniosek o ustalenie numeru porządkowego nieruchomości" is one page: applicant, address, phone or e-mail, the addressee, one sentence with four blanks, a signature, two footnotes, and a data-protection clause on page two. The JSON made from it has four pages and 69 components.

**About four fifths of the result is not on the paper.** It comes from the partner's design standard: the same pages and sections for every form. From the paper come only: the title, the addressee, who may apply, the fields about the matter itself, attachments, declarations, fees.

So the converter is two things: a **library of standard sections** written once, and an **understanding step** that answers a short list of questions about the paper (section 8). It is not a field-by-field copy.

## 2. Structure

```
title                       name of the service as the citizen sees it, at most 255 characters
tabs[]                      pages
  id (UUID), title, type    MAIN, or FINISH for the last page
  questions[]               on a page: sections only
    x, y, rows, cols        place in a grid (CSS grid-area: y+1 / x+1 / span rows / span cols)
    field
      id (UUID), type, techName, title, description, tooltipMessage, questionOrder
      options[]             {id, name, techName} for RADIO, CHECKBOX, SELECT without a dictionary
      validation[]          names of predefined validators
      dictionaryName        instead of options
      readOnly
      defaultValue, defaultValueType
      states[]              {type: SHOW | READ_ONLY, query: JSONata}
      consentSectionConfig  only for CONSENT_SECTION
      repeatingSectionGrid  for SECTION and REPEATING_SECTION: the components inside, same shape as questions
flow.links[]                {id (UUID), source: page id, target: page id}
```

Conventions seen in the sample (follow them; they are what their system exports):

- Every component sits in a section; sections sit on a page; no section inside a section.
- One column: `x = 0`, `cols = 3` everywhere. Inside a section `rows = 1` and `y` counts 0, 1, 2 …; `questionOrder` equals `y`. On the page a section's `y` is the previous section's `y + rows`, and `questionOrder` equals `y`; `rows` of a section is roughly its number of components plus one.
- `techName`: lower case, ASCII, words joined by `_`, made from the label (`numer_ewidencyjny_dzialki`). In both exports it is unique across the whole form: repeated blocks carry suffixes (`_siedziba`, `_inna_osoba`, `_zagranica`), the longest name has 53 characters. We keep that (decision D7). JSONata refers to them, so they must be stable.
- `description` of a section is an HTML string, empty as `<html><head></head><body></body></html>`; text blocks and consents carry their text as HTML in `description`.
- Option: `id` and `name` are the visible text, `techName` its slug.
- Keys present on every component in the sample, even when empty: `options: []`, `validation: []`, `readOnly`, `repeatingSectionGrid: []`, `states: []`, `tooltipMessage: ""`. Write them all.
- SELECT fed by a dictionary also carries `searchEnabled` and, for the territorial dictionary, `multiLevelTree: true`, and `defaultValue` as a list (`["Polska"]`).
- The pages are chained in order by `flow.links`.

## 3. Components and validators

| `type` | Use |
|---|---|
| `SECTION`, `REPEATING_SECTION` | grouping; the repeating one for the same data about several persons, properties, vehicles |
| `TEXT_FIELD` | one short line |
| `TEXTAREA` | longer text: description, justification |
| `NUMBER` | numbers only |
| `DATEPICKER` | dates |
| `RADIO` | one of a few options |
| `CHECKBOX` | several options |
| `SELECT` | more than five options; search when more than fifteen |
| `FILE_UPLOADER` | attachments |
| `CONSENT_SECTION` | consents and declarations (never a lone checkbox) |
| `TEXT_BLOCK` | fixed text that is not the description of one field |
| `INFO_SECTION` | information for the user; the only kind the rules name for the last page (the sample uses a `TEXT_BLOCK` inside a `SECTION` there) |

Validators (names as written into `validation`): `REQUIRED`, `EMAIL`, `PESEL`, `NIP`, `REGON`, `ZIP_CODE`, `EPUAP`, `ADE`, `SERIAL_NUMBER_ID_CARD`. The design standard also mentions a pattern validator with a regular expression and a message (ten digits for the court-register number); the list of validators does not contain it: ask.

## 4. The partner's rules (each is a check in `tools/coi_lint.py`)

1. At least two pages; the last is `FINISH`, all others `MAIN`.
2. Every page has at least one component.
3. Every component is inside a section or a repeating section, which is on a page; sections are not nested.
4. The last page has no input component.
5. Every field states whether it is required.
6. Pages are connected by flow links.
7. A component whose presence depends on an answer carries a state with a JSONata condition.
8. A dictionary may feed only SELECT, CHECKBOX, RADIO; then `options` is empty.
9. A field fed from a register: `readOnly`, `defaultValue` = `SOURCE.attribute`, `defaultValueType` = `EXTERNAL_SYSTEM`.

## 5. Conditions (JSONata)

The pattern used throughout the sample, for "show when option O was chosen in field F of section S on page P":

```
("O" in tabs['P' in title].questions['S' in field.techName].field.repeatingSectionGrid['F' in field.techName].field.__userAnswer)
```

Conditions are joined with `and`, `or` and brackets. For a field inside a repeating section the rules give a second form with `__userAnswer[$repeatingSectionIndex]`. Write conditions from a small builder function, never by hand; the checker resolves every reference.

## 6. Dictionaries and initial data

Dictionaries named in the note: Województwo, Powiat, Gmina, Miejscowość (addresses; SELECT only), Kraje (SELECT only), Numery kierunkowe (phone prefix). The sample and the standard use other identifiers: `Kraje`, `TERYT_DOWODOWY`, `TERYT_4G_DOWODOWY` (one multi-level select for województwo, powiat, gmina, miejscowość). **The exact `dictionaryName` strings for the four separate territorial dictionaries and for the phone prefixes are not given anywhere: ask.** Where no dictionary fits, the task rewards proposing one: name, structure, where it is used.

Initial data: `defaultValue` is `SOURCE.attribute`.

| Source | Attributes |
|---|---|
| `MLPZ` (the logged-in user) | name, secondName, surname, pesel, phoneNumber, email, country, voivodeship, district, community, place, postCode, street, building, apartment, institutionName, descriptiveOrganizationName |
| `PESEL` (the register) | pesel, name, secondName, surname, familyName, birthDate, birthPlace, birthCountry, foreignBirthUSC, citizenship, sex, maritalStatus, motherName, motherSurname, fatherName, fatherSurname |
| `PESEL_ADDRESS` (registered address) | `permanentAddress…` and `temporaryAddress…` with Voivodeship, District, Community, Place, StreetType, Street, HouseNumber, ApartmentNumber, PostalCode |

## 7. The standard pages and sections (the library)

Order of every form: parties, then the matter, then contact and declarations, then summary. Take the sections below **from the partner's sample JSON as templates** (they are there complete, with conditions) and make the names parameters.

| Page | Section | When | Content |
|---|---|---|---|
| 1 "Dane" | Urząd / Organ, do którego jest składany wniosek | always | read-only text field with the addressee as default; "Organ" and "Nazwa organu" when the paper addresses a body such as "Wójt", otherwise "Urząd" and "Nazwa urzędu" |
| 1 | Podmiot wniosku | when someone may apply for another person or for an entity | radio "Wybierz, w czyim imieniu wnioskujesz": Swoim, Innej osoby, Osoby prawnej lub jednostki organizacyjnej (only the options the paper allows); radio "Wybierz, jako kto wnioskujesz": Pełnomocnik, Reprezentant, shown for the entity option |
| 1 | Twoje dane | always | read-only identity: Imię, Nazwisko from `MLPZ` in export 1; Imię, Nazwisko, Numer PESEL from `PESEL` in export 5 (the paper of export 5 asks for PESEL) |
| 1 | Adres zamieszkania (or zameldowania, korespondencyjny) | when the paper asks for it | Kraj (dictionary, default Polska); for Poland: territorial select, Kod pocztowy (`ZIP_CODE`), Ulica, Numer budynku, Numer lokalu from `MLPZ`; for abroad: Miejscowość, Kod pocztowy, Ulica as free text; each group shown by the country chosen |
| 1 | Dane podmiotu, Adres siedziby | entity option | Nazwa, NIP, REGON, Numer KRS; the address pattern again |
| 1 | Potwierdzenie, że jesteś reprezentantem | entity and Reprezentant | file |
| 1 | Dane innej osoby, Adres zamieszkania innej osoby | other-person option | Imię, Nazwisko (PESEL in the standard); the address pattern |
| 1 | Pełnomocnictwo | other person, or entity and Pełnomocnik | file |
| 1 | Opłata skarbowa (two variants) | with Pełnomocnictwo | question whether the fee is due, text block with the amount and where to pay, file with the proof |
| 2 … n | the matter ("Przedmiot wniosku" or a name taken from the content) | always | the fields found on the paper, grouped in thematic sections; alternative pages when a whole stage depends on an answer |
| last but one "Kontakt z urzędem" | Dane do kontaktu | always | Numer telefonu, Adres e-mail (`EMAIL`) from `MLPZ`, optional, editable |
| last but one | Oświadczenie / Zgody i oświadczenia | when the paper has declarations or a data-protection clause | one CONSENT_SECTION; the clause itself is not copied into the form, only linked |
| last "Strona końcowa" (`FINISH`) | Podsumowanie (optional), Podgląd | always | text only: check the data on the preview before signing or sending |

Language of every label and hint follows the standard's part on voice: short sentences, active voice, second person, no gendered forms, no legal jargon without an explanation, title starting with "Wniosek", "Zgłoszenie", "Deklaracja" or "Oświadczenie" and without references to legal acts.

## 8. The questions the understanding step must answer about a paper form

| # | Question | Evidence on paper | Goes to |
|---|---|---|---|
| D1 | What is the title? | the largest heading; drop legal references | `title` |
| D2 | Who is the addressee, an office or a body? | "Adresat", "Do", a name and address block | section 1 and its default value |
| D3 | Who may apply? | "imię i nazwisko / nazwa", NIP or REGON fields, "pełnomocnik" | which standard sections exist and their conditions |
| D4 | Which data about the applicant does the paper want beyond the standard? | PESEL, date of birth, document number | extra fields with initial data from `PESEL` where an attribute exists |
| D5 | What are the fields of the matter? | blanks in sentences, boxes, tables, tick lists | pages 2 … n: label, type, options, required or not, hint |
| D6 | Which choices are there, and do options depend on each other? | tick boxes, "niepotrzebne skreślić", "jeżeli … to", "dotyczy" | RADIO, CHECKBOX, SELECT; states |
| D7 | Which attachments? | "Załączniki" | FILE_UPLOADER fields |
| D8 | Which declarations, consents, clause? | "Oświadczam", the data-protection clause | CONSENT_SECTION |
| D9 | Is a fee mentioned? | "opłata skarbowa" | text block and proof upload |
| D10 | What is paper-only and must not be carried over? | signature line, place and date, "wypełnia urząd", stamps, footnotes that explain the signature | dropped, each one named in the report |

Footnote marks matter: in the sample "1) Dane nieobowiązkowe" makes street and phone optional.

## 9. The sample, side by side

| On the paper | In the partner's JSON |
|---|---|
| "WNIOSEK O USTALENIE NUMERU PORZĄDKOWEGO" | title "Wniosek o ustalenie numeru porządkowego nieruchomości" (sentence case, completed) |
| "Adresat: Wójt Gminy Elbląg" and the address | section "Organ, do którego jest składany wniosek", field "Nazwa organu", default "Wójt Gminy Elbląg" |
| "(imię i nazwisko / nazwa wnioskodawcy)" | all three applicant options, hence twelve sections on page "Dane" |
| "(adres)" | the address pattern, three times |
| "w miejscowości … przy ulicy … nr ewidencyjny działki … w obrębie …" | page "Informacje o budynku", section "Lokalizacja budynku": Miejscowość, Ulica, Numer ewidencyjny działki, Obręb |
| "(nr telefonu / adres e-mail)" | page "Kontakt z urzędem", section "Dane do kontaktu" |
| the clause on page two | a consent with a link, not the text |
| "(podpis wnioskodawcy)", the date | nothing; the last page says to check the preview |

## 10. Where the materials disagree (questions for the mentors, in `coi-replan.md` §7)

1. The schema file and the field description spell the key `repetingSectionGrid`; the sample export and every JSONata path spell it `repeatingSectionGrid`. We write the second.
2. The rules ask for a required-or-not attribute on every field; the sample has no `REQUIRED` anywhere. We write `REQUIRED` where the paper or the standard says so and report the rest as optional.
3. The initial-data note asks for read-only; the sample leaves address and contact fields editable, as the standard describes. We follow the standard per section.
4. Three fields of the sample have `validation: {}` instead of a list. We always write a list.
5. Dictionary identifiers: see section 6.
6. File limits (count, size, formats) are in the standard but have no key in the schema or the sample.
7. `multiLevelTree`, `searchEnabled`, `selectAllEnabled`, a placeholder and the "checkbox that switches a field off" are in the standard or the sample but not in the schema.
8. The last page: rules say only `INFO_SECTION`; the sample has `SECTION` with `TEXT_BLOCK`. Both exports do, and the design standard (pages 28 and 29) also describes sections "Podsumowanie" and "Podgląd" holding a text block. Decision D5: we write what the exports have; a switch gives the other form.

## 11. What reference set 5 and the forensics added (21 November, afternoon)

Measured with a script on both exports; the full output is [`../05-hackathon/mentor-questions/reference-json-forensics.txt`](../05-hackathon/mentor-questions/reference-json-forensics.txt). "Export 1" is the form of reference set 1, "export 5" the one of reference set 5 (in `data/coi/reference-05-nadplata-podatku/`, local only).

### 11.1 Both exports agree

| Fact | Export 1 | Export 5 |
|---|---|---|
| Top keys | `title`, `tabs`, `flow` | the same |
| Pages | Dane; Informacje o budynku; Kontakt z urzędem; Strona końcowa | Dane; Informacje o nadpłacie; Kontakt i zgody; Strona końcowa |
| Sections on the page "Dane" | 12 | 12 |
| Sections, components | 16, 53 | 18, 55 |
| Grid key | `repeatingSectionGrid` (16 times) | the same (18 times) |
| Layout | `x = 0`, `cols = 3`, component `rows = 1`, no nested section | the same |
| `techName` | unique in the whole form, longest 53, slugs only | the same |
| Ids of components | UUID version 4 | the same |
| Validators | none anywhere | none anywhere |
| `tooltipMessage` | never filled | never filled |
| States | 29, all `SHOW` | 31, all `SHOW` |
| Dictionaries | `Kraje` (3), `TERYT_DOWODOWY` (1), `TERYT_4G_DOWODOWY` (2) | the same counts |
| Initial data, editable | postal code, street, building, apartment, phone, e-mail from `MLPZ` | the same |
| Last page | one `SECTION` with one `TEXT_BLOCK` | the same |
| Flow | three links in a chain | the same |

### 11.2 Where the exports differ from each other or from the written material

| # | Observation | What we do |
|---|---|---|
| 1 | Export 5 has link ids that are **not UUIDs** (`a16ec`, `aa405`, `a0icc`) | we write UUIDs; the schema gets a `tolerant` profile for reading the partner's files (WP-F0) |
| 2 | In export 5 one option of the first `RADIO` in "Podmiot wniosku" has no `techName` | we always write it; `tolerant` allows its absence |
| 3 | Export 1 has three fields with `validation: {}` (`numer_krs`, `ulica_siedziba_zagranica`, `nazwisko_inna_osoba`) | always a list (D3) |
| 4 | Identity: export 1 takes Imię and Nazwisko from `MLPZ`; export 5 takes Imię, Nazwisko and Numer PESEL from `PESEL`. Read-only in both | the builder of "Twoje dane" takes the source as a parameter; `PESEL` when the paper asks for a PESEL number |
| 5 | "Dane podmiotu": Nazwa, NIP, REGON, Numer KRS in export 1; only Nazwa and NIP in export 5 | fields follow what the paper names; Nazwa and NIP always |
| 6 | The territorial dictionary of the three address sections is assigned differently: export 1 has `TERYT_DOWODOWY` on the applicant's address, export 5 on the other person's address; the remaining ones have `TERYT_4G_DOWODOWY` | `TERYT_4G_DOWODOWY` on all three, as a parameter; question J5 |
| 7 | The territorial `SELECT` carries the dictionary's name as its **title** ("TERYT_4G_DOWODOWY") in both exports | we write a label a citizen can read ("Województwo, powiat, gmina, miejscowość") and note it in the docket |
| 8 | Section titles that look unfinished: "Zgoda_sekcja" (export 1), "Opłata skarbowa za pełnomonictwo" (both) | we write "Zgoda" and the correct spelling; the comparison test knows these two strings |
| 9 | Keys outside the schema and the field description: `multiLevelTree` (3 and 5 uses) and `searchEnabled` (1 and 5 uses) on `SELECT` with a dictionary; `minItemRows: 2` once, on the wrapper of the consent section of export 1 | `multiLevelTree` and `searchEnabled` are written where the exports write them; `minItemRows` is not written |
| 10 | The third page is "Kontakt z urzędem" in export 1 and "Kontakt i zgody" in export 5 | "Kontakt i zgody" when the page holds a consent section, otherwise "Kontakt z urzędem" |

### 11.3 New component examples

Export 5 adds `NUMBER` (`kwota`) and `TEXTAREA` (`uzasadnienie`). Both carry exactly the keys of a `TEXT_FIELD` (the always-present ones of section 2), empty `options`, empty `validation`. A two-way choice whose branches own a field is shown too: `RADIO` "Wybierz, co mamy zrobić z nadpłatą" with two options, then "Nazwa podatku" and "Numer rachunku", each with one `SHOW` state on its option.

### 11.4 What no export shows

`REPEATING_SECTION`, `CHECKBOX`, `DATEPICKER`, `INFO_SECTION`; any validator; a `READ_ONLY` state; a condition inside a repeating section; a page or a flow link that depends on an answer; file limits; a pattern validator. Most judged sets need at least one of them: dates in sets 2, 4, 6, 7, 8 and 9; repeating rows in sets 6, 7 and 9; possibly several-of-many in set 3. Their shapes are inferred from the rules document until question J1 is answered; every use is flagged `INFERRED_SHAPE` in the sidecar.

### 11.5 How a condition selects its target

In JSONata `'x' in y` is membership, and for one string it means **equals**, not "contains". `tabs['Dane' in title]` is the page titled exactly "Dane"; `questions['adres_zamieszkania' in field.techName]` is the section with exactly that techName, and not also `adres_zamieszkania_osoby_…`. Consequences for us: page titles must be unique in a form; techNames must be unique (they are, D7); a renamed page breaks every condition that names it, so page titles and conditions come from one function. `__userAnswer` is read as the chosen option's visible name, or a list of names *(inference from `"Polska" in … __userAnswer`)*.
