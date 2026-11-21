# Forms for the demo and for tests

All 676 form files of the city hall's service cards were mirrored on 21 November 2026 and are attached to the release [`pre-event`](https://github.com/AndriiShramko/shramko-asystent-urzednika/releases/tag/pre-event) as `bydgoszcz-forms-2026-11-21.zip` (183 MB) with `bydgoszcz-forms-manifest-2026-11-21.json` (source address, service card, size and SHA-256 of every file). Download the archive once and unpack it into `data/forms-cache/all/` (git-ignored); the paths below are inside it.

## What the mirror shows (measured on the 676 files)

| Fact | Number |
|---|---|
| Files fetched / not found | 676 / 2 |
| PDF | 329 |
| Word-processor files (DOCX 149, DOC 115, RTF 77) | 341, about half |
| Byte-identical copies published under several service cards | 15 (for example the two residence-registration forms appear under four cards each) |
| Total size | 211 MB |

Together with [`research/03b`](../research/03b-form-anatomy-and-canonical-profile.md) (one fillable PDF among 32 analysed forms) this is the measured starting point of any "digitise the forms" effort in one city.

## Candidates

| Use | Form | Path in the archive | SHA-256 (first 16) | Notes |
|---|---|---|---|---|
| Part two of the demo; golden test of field recognition | Zgłoszenie pobytu stałego (ministry's template EL/ZPS/1) | `UMB55/Formularz_meld._-_Zgloszenie_pobytu_stalego.pdf` | `4bf2818f2c0c927d` | Flat PDF, one character per box, broken text layer; page 1 measured in [`form-descriptor.example.json`](form-descriptor.example.json) |
| Second person or second situation in the bundle | Zgłoszenie pobytu czasowego | `UMB55/Formularz_meld._-_Zgloszenie_pobytu_czasowego_-.pdf` | `95b42c5928501dc5` | Same family of templates |
| Part one of the demo (digitise live); the bridge to the city's task | Wniosek o udostępnienie informacji publicznej (city's auxiliary template) | not in the archive: download from <https://bip.um.bydgoszcz.pl/attachments/download/30900> (PDF) | check after download | Two pages, few fields, no personal data required |
| Spare for "pick any form" | Pełnomocnictwo (vehicle department) | `UMB202/Pelnomocnictwo1.pdf` | `68804a398948c919` | One page |
| Spare, harder | Wniosek o rejestrację pojazdu | `UMB202/Rejestracja__czasowa_rejestracja__wyrejestrowanie_zbycie_UMB_202_208_213_217.pdf` | `561c80cb44688b50` | Several case variants on one form |
| The only fillable PDF found | ZIN-1 (tax attachment, ministry's template) | `UMB143/ZIN-1__1__-_Dane_o_przedmiotach_opodatkowania_podlegajacych_opodatkowaniu__wersja_interaktywna_.pdf` | `4eee983a2af9028a` | 156 form fields; use it to test the "form fields present" path |
| Word-processor source | Wniosek o wydanie zaświadczenia z rejestru mieszkańców oraz rejestru PESEL | `UMB96/wniosek_o_wydanie_zaswiadczenia_z_rejestru_mieszkancow_oraz_rejestru_PESEL.docx` | `d0d1eab491c9f4f0` | DOCX: needs conversion to PDF and a human check of the result |

Rules: a descriptor is bound to the full SHA-256 of its template; take the full value from the manifest. Before the demo, compare the hash of each chosen file with the live file on the city's site: if it differs, the office has published a new version.
