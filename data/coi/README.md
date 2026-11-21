# Materials of the task "Cyfryzacja formularzy" (Centralny Ośrodek Informatyki)

Downloaded on 21 November 2026 from the event's Discord, channel of the task, section "materiały-dodatkowe" (posted there at 11:11 by a mentor of the partner). Put here at the owner's instruction so that the building agents can work with them.

**These files are not ours.** They belong to the partner and to the offices that issued the forms, and the licence of this repository does not cover them. They are kept only to build and test the solution of the task. Remove them if the partner asks.

| Folder | What | State |
|---|---|---|
| `materials/` | the partner's schema file, the description of the JSON fields, the technical rules for configuring forms, the design standard, the dictionaries note, the initial-data note, two visualisations of finished e-services | complete (8 files) |
| `reference-01-numer-porzadkowy/` | reference set 1: one paper form in eight formats (PDF, DOC, DOCX, ODS, XLSX, JPG, JPEG, PNG), the JSON the partner made from it, the visualisation | complete (10 files) |
| `reference-05-…` | reference set 5 (refund of overpaid tax): the second form that comes with its JSON | **not downloaded yet** |
| `judged-02 … judged-09` | seven sets of forms "do cyfryzacji": the converter's outputs for these are judged (sets 2, 3, 4, 6, 7, 8, 9; about 30 MB together) | **not downloaded yet** |

`INDEX.json` lists every file with its size and the first 16 characters of its SHA-256.

Our own description of the format, written from these files: [`../../docs/02-architecture/coi-json-format.md`](../../docs/02-architecture/coi-json-format.md). Check a JSON file against the partner's rules: `python tools/coi_lint.py FILE.json`.

How to add the missing sets: in Discord download the archives numbered 2 to 9 from the same channel, unpack each into a folder named as in the table, and commit them with explicit paths.
