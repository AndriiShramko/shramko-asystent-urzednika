# Materials of the task "Cyfryzacja formularzy" (Centralny Ośrodek Informatyki)

Downloaded on 21 November 2026 from the event's Discord, channel of the task, section "materiały-dodatkowe" (posted there at 11:11 by a mentor of the partner). Put here at the owner's instruction so that the building agents can work with them.

**These files are not ours.** They belong to the partner and to the offices that issued the forms, and the licence of this repository does not cover them. They are kept only to build and test the solution of the task. Remove them if the partner asks.

| Folder | What | In git |
|---|---|---|
| `materials/` | the partner's schema file, the description of the JSON fields, the technical rules for configuring forms, the design standard, the dictionaries note, the initial-data note, two visualisations of finished e-services | yes (8 files) |
| `reference-01-numer-porzadkowy/` | reference set 1: one paper form in eight formats (PDF, DOC, DOCX, ODS, XLSX, JPG, JPEG, PNG), the JSON the partner made from it, the visualisation | yes (10 files) |
| `reference-05-nadplata-podatku/` | reference set 5 (refund of overpaid tax): the second form that comes with its JSON; seven formats, the JSON, the visualisation | **no, local only** |
| `judged-02-zwrot-oplaty-skarbowej/`, `judged-03-wydanie-zaswiadczenia/`, `judged-04-wynajecie-swietlicy/`, `judged-06-zajecie-pasa-drogowego/`, `judged-07-psy-rasy-agresywne/`, `judged-08-deklaracja-odpady/`, `judged-09-stypendium-sportowe/` | the seven forms "do cyfryzacji": **the converter's outputs for these are judged**. Eight formats each (set 7 has six) | **no, local only** |
| `text/` | plain text of every DOCX, PDF and XLSX above, made by `tools/coi_unpack.py`, for quick reading | **no, local only** |

Why some sets are local only: the forms print bank accounts, phone numbers and e-mail addresses of offices, the publishing check of this repository stops on them, and the partner has not yet said whether the task materials may be public (question J11 in `docs/05-hackathon/mentor-questions/`). If the answer is yes, the lead removes the three ignore rules at the end of `.gitignore` and commits the sets.

`INDEX.json` lists **every** file, also the local ones, with its size and the first 16 characters of its SHA-256, so a local copy can be verified.

## Getting the local sets on a machine

1. In Discord (server HackNation, category "CYFRYZACJA FORMULARZY", channel "materiały-dodatkowe") download the ten archives into one folder. Renaming them is fine.
2. `python tools/coi_unpack.py "<that folder>"`. The tool recognises each set by the folder inside the archive, writes short paths (Windows cannot unpack these archives in place: the paths are too long), extracts the text and rebuilds `INDEX.json`.
3. Code never builds a path to these sets by hand: `from tools.coi_paths import coi_dir, sets`. It finds them from a git worktree too, and honours `COI_DATA_DIR`.

Facts measured on the two reference JSON files: [`../../docs/05-hackathon/mentor-questions/reference-json-forensics.txt`](../../docs/05-hackathon/mentor-questions/reference-json-forensics.txt). Our description of the format: [`../../docs/02-architecture/coi-json-format.md`](../../docs/02-architecture/coi-json-format.md). Check a JSON file against the partner's rules: `python tools/coi_lint.py FILE.json` (reference set 5 shows that the partner's own exports are looser than our schema: link ids that are not UUIDs, an option without `techName`).
