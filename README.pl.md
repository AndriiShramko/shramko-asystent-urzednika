# Shramko Asystent Urzędnika

**Otwarty opis i projekt referencyjny asystenta AI dla urzędu: wspiera pracowników w analizie wniosków o udostępnienie informacji publicznej i w przygotowywaniu odpowiedzi, a w kolejnym module wypełnia urzędowe formularze danymi, które interesant podaje tylko raz.** Przygotowany na HackNation 2026, zadanie Miasta Bydgoszczy „Inteligentny asystent urzędnika”.

English: [README.md](README.md) · Dla agentów AI: [START_HERE.md](START_HERE.md)

> **Stan: materiał przygotowany przed wydarzeniem (znacznik `pre-event`).** Repozytorium zawiera badania, wymagania, decyzję o zakresie, plan budowy i zasady pracy agentów. Kod aplikacji powstaje w czasie 24 godzin hackathonu i będzie widoczny w historii zmian po tym znaczniku.

## Co robi asystent

1. Czyta wniosek, który wpłynął (e-mail, e-Doręczenia, pismo), i wskazuje, czym on jest prawnie, z uzasadnieniem.
2. Od razu liczy termin 14 dni i najpóźniejszy termin po przedłużeniu; przypomina przed upływem.
3. Szuka wcześniejszych odpowiedzi na podobne wnioski i miejsca, gdzie informacja jest już opublikowana.
4. Przygotowuje projekt odpowiedzi albo zawiadomienia z podstawą prawną, którą program sprawdza w tekście ustawy.
5. Maskuje dane osobowe, zanim jakikolwiek tekst trafi do modelu językowego, i pomaga zanonimizować dokumenty do udostępnienia.
6. Niczego nie wysyła sam: każdy projekt zatwierdza urzędnik, a każda czynność zostaje w dzienniku.

## Bezpieczeństwo

- Dane pozostają pod kontrolą urzędu; domyślnie model działa lokalnie, a model zewnętrzny dostaje wyłącznie tekst po pseudonimizacji.
- Treść wniosku jest dla modelu danymi, nigdy poleceniem.
- Asystent proponuje, człowiek decyduje; decyzję odmowną podpisuje upoważniona osoba.
- W repozytorium i w pokazie nie ma prawdziwych danych osobowych, tylko dane syntetyczne.

## Dokumenty

| Co | Gdzie |
|---|---|
| Decyzja o zakresie i szersza platforma | [`docs/01-product/scope-decision.md`](docs/01-product/scope-decision.md) |
| Prawo i ścieżka postępowania urzędnika | [`research/02-udip-law-process-taxonomy.md`](research/02-udip-law-process-taxonomy.md) |
| Zasady i ocena HackNation | [`research/01-hacknation-2026-task-rules-jury.md`](research/01-hacknation-2026-task-rules-jury.md) |
| Katalog kart usług i formularzy Urzędu Miasta Bydgoszczy | [`data/forms-catalog.csv`](data/forms-catalog.csv) |
| Stan prac | [`docs/03-plan/STATUS.md`](docs/03-plan/STATUS.md) |

## Zastrzeżenia

Projekt niezależny, niezwiązany z Miastem Bydgoszcz, Ministerstwem Cyfryzacji ani inną instytucją. Analizy prawne są materiałem badawczym z podanymi źródłami i datami; nie zastępują opinii radcy prawnego ani inspektora ochrony danych.

Autor: Andrii Shramko · kontakt i licencja w [README.md](README.md).
