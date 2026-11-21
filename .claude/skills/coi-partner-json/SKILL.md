---
name: coi-partner-json
description: Rules for any code or agent that writes or checks the partner's form JSON (Centralny Osrodek Informatyki, task "Cyfryzacja formularzy") - the exact shape, the conventions measured on the partner's two exports, the standard sections, the gate. Use before touching the composer, the section library, conditions, dictionaries, validators, the linter or the schema.
---

# Writing the partner's JSON

Sources, in order of authority: `docs/03-plan/DECISIONS-forms-track.md` (D1-D11, binding), `docs/02-architecture/coi-json-format.md` (the format in our words), `docs/05-hackathon/mentor-questions/reference-json-forensics.txt` (what their two exports contain), the exports (find them with `tools/coi_paths.py`). The partner's materials disagree in eight places; there the exports win: they are what their system produces.

## Shape

```
title
tabs[]:   id, title, type (MAIN; the last one FINISH), questions[]
  question (a section): x 0, y, rows, cols 3, field
    field: id, type SECTION, techName, title, description, options [], validation [], readOnly,
           repeatingSectionGrid [components], states [], questionOrder, tooltipMessage ""
      component: x 0, y n, rows 1, cols 3, field {same keys; its own repeatingSectionGrid is []}
flow.links[]: id, source (page id), target (page id), pages chained in order
```

## Rules that fail a review

1. The answer of the conversion endpoint is this object alone: top keys `title`, `tabs`, `flow`. No envelope, no key outside the list below. Evidence, confidence, proposals go to the sidecar (D1, D2).
2. Spelling `repeatingSectionGrid`. Every field carries all of: `id`, `type`, `techName`, `title`, `description`, `options`, `validation`, `readOnly`, `repeatingSectionGrid`, `states`, `questionOrder`, `tooltipMessage`. `validation` is always a list (D3).
3. Optional keys, only where they apply: `defaultValue`, `defaultValueType`, `dictionaryName`, `searchEnabled`, `multiLevelTree`, `consentSectionConfig`.
4. One column: `x = 0`, `cols = 3`; component `rows = 1`, `y` counts 0, 1, 2 and equals `questionOrder`; a section's `y` is the previous section's `y + rows`. Components live only inside sections; sections are never nested (D4).
5. `techName`: lower case, ASCII (ą→a, ć→c, ę→e, ł→l, ń→n, ó→o, ś→s, ź and ż→z), words joined by `_`, at most 60 characters, **unique in the whole form**. Repeated blocks take the partner's suffixes: `_siedziba`, `_inna_osoba`, `_zagranica` (D7). JSONata refers to these names: once published they do not change.
6. Ids: UUIDs made deterministically from meaning, `uuid5(namespace, form key / page role / section role / field key)`, never from the file bytes or from a counter (D10).
7. Options of RADIO, CHECKBOX, SELECT: `{id, name, techName}`; `id` and `name` are the visible text. A field fed by a dictionary has `options: []`.
8. Dictionaries: only `Kraje`, `TERYT_DOWODOWY`, `TERYT_4G_DOWODOWY` until the mentors give more. `Kraje` SELECT has `defaultValue: ["Polska"]`; the territorial SELECT has `multiLevelTree: true`. Any other candidate is a proposal in the sidecar (D9).
9. Initial data: `defaultValue: "MLPZ.name"` or `"PESEL.pesel"` with `defaultValueType: "EXTERNAL_SYSTEM"`. Identity (first name, surname, PESEL) is `readOnly: true`; address and contact are pre-filled and editable (D6). One source and one attribute per field. Attribute lists: coi-json-format section 6.
10. Validators by name, only from: `REQUIRED`, `EMAIL`, `PESEL`, `NIP`, `REGON`, `ZIP_CODE`, `EPUAP`, `ADE`, `SERIAL_NUMBER_ID_CARD`. Written where the paper or the standard supports them; the switch `VALIDATORS=off` gives empty lists (D8).
11. Conditions: `states: [{type: "SHOW", query}]`. The query is JSONata built by the predicate builder, never by hand. Pattern for "option O chosen in field F of section S on page P":
    `("O" in tabs['P' in title].questions['S' in field.techName].field.repeatingSectionGrid['F' in field.techName].field.__userAnswer)`.
    Every query is parsed and evaluated before the service answers; every name it mentions must exist.
12. HTML: `description` of a section is `<html><head></head><body></body></html>` when empty. Text blocks and consents are built from our templates; text from the paper is escaped and sanitised. Never pass text of a form through as markup (D11).
13. Last page: type `FINISH`, a `SECTION` with one `TEXT_BLOCK`, no input component (D5).
14. `REPEATING_SECTION`, `CHECKBOX`, `DATEPICKER`, `INFO_SECTION` appear in no export: their shape comes from the rules document only. Whenever one is written, the report says so.

## Standard sections

About four fifths of a finished form are not on the paper. They come from the library, taken from the exports as templates with names as parameters: the office or body addressed; who applies (for myself, for another person, for a legal person or unit; as pełnomocnik or reprezentant); my data; address with the Poland and abroad branches; data and seat of the entity; proof of representation; power of attorney and its stamp duty; the pages of the matter (from the paper); contact; consent; the final page. The table with conditions: coi-json-format section 7. A test rebuilds every standard section of both exports and compares, ignoring ids.

## The gate before answering

`contracts/coi/form.schema.json`, then `tools/coi_lint.py` (imported as a module), then the evaluation of every condition, then the HTML allow-list. A failure is an error with the finding: never a broken or partly valid JSON. Note: reference set 5 is looser than our schema (link ids that are not UUIDs, an option without `techName`): the gate judges what **we** write, a reader of their exports must accept both.

## Negative controls every change keeps passing

Missing FINISH page; missing or duplicate `techName`; an unreachable page; a condition naming a field that does not exist; the misspelled grid key; `validation` as an object; a key outside the list.
