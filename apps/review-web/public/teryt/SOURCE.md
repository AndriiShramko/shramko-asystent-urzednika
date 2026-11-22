# Address registers served by the page (offline)

These files are data, not code. The page reads them from its own folder when an address field of the trial fill
gets focus; no other host is called. Built by `apps/review-web/scripts/teryt-build.mjs`.

| File | What | Source | State |
|---|---|---|---|
| `miejscowosci.txt` | województwa, powiaty, gminy (TERC); 54 440 localities (SIMC, base localities; parts of localities and city districts are folded into their locality); postal codes per locality | GUS, rejestr TERYT; GeoNames postal codes | TERC and SIMC 2026-01-01, file of 2026-11-22 |
| `ulice-<WW>.txt` (16 files, one per województwo) | 308 796 street entries of 9 896 localities (ULIC) | GUS, rejestr TERYT | ULIC 2026-11-20, file of 2026-11-22 |

Size: 5.04 MB (4.81 MiB) in 17 text files (2.11 MB localities with codes, 2.93 MB streets).

## Licences (read on 2026-11-22)

**GUS, rejestr TERYT (TERC, SIMC, ULIC).** Page "Formy i zasady udostępniania" of eteryt.stat.gov.pl: "Rejestr
terytorialny TERYT jest jawny. [...] Dane te udostępniane są bezpłatnie wszystkim użytkownikom" (through the option
Baza TERYT, among others "pobieranie zbiorów pełnych"). Page stat.gov.pl/copyright: GUS "nie ma zastrzeżeń co do
kopiowania plików i stron oraz dokonywania wydruków, w tym do własnych opracowań, pod warunkiem, że będzie podane
ich źródło". Source: Główny Urząd Statystyczny, rejestr TERYT, https://eteryt.stat.gov.pl (files "TERC, SIMC, ULIC
urzędowy", pliki pełne, 2026-11-22). The compact files are our own arrangement of that data; names are unchanged.

**GeoNames postal codes (PL.zip).** readme.txt of download.geonames.org/export/zip: "This work is licensed under a
Creative Commons Attribution 4.0 License. This means you can use the dump as long as you give credit to geonames".
Credit: postal code data from GeoNames, https://www.geonames.org, CC BY 4.0. Of 72 899 rows, 71 575 were tied to
one locality of SIMC by name and gmina (else name and powiat); 49 109 localities have at least one code. An ambiguous
row is left out. The set is not the register of Poczta Polska: a code missing here is shown as a remark to check,
never as an error.

## Rebuild

1. Download the full files "TERC urzędowy", "SIMC urzędowy", "ULIC urzędowy" (CSV) from eteryt.stat.gov.pl, Baza
   TERYT, Pobieranie, Pliki pełne; and PL.zip from download.geonames.org/export/zip/.
2. `node scripts/teryt-build.mjs <TERC.csv> <SIMC.csv> <ULIC.csv> <PL.txt>` in `apps/review-web`.
3. `npx vitest run tests/w11-addr-teryt.test.ts`.
