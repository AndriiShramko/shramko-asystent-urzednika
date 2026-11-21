# Konwerter formularzy: od pustego druku do JSON e-usługi

Usługa REST w Dockerze dla zadania „Cyfryzacja formularzy” (Centralny Ośrodek Informatyki, HackNation 2026). Na wejściu jeden pusty formularz urzędowy (PDF, DOC, DOCX, ODS, XLSX, JPG, JPEG, PNG), na wyjściu konfiguracja JSON formularza elektronicznego w strukturze partnera („Generator Formularzy e-Usług”). Dostęp chroni token. Obok formularza powstaje plik poboczny (sidecar) z dowodami: skąd wzięło się każde pole, co się stało z każdym pustym miejscem druku, co pominięto i czego usługa odmówiła zgadywać.

Idea w jednym zdaniu: **kompilator z księgowym, a nie skaner ze sztuczną inteligencją.** Reguły i biblioteka standardowych sekcji partnera składają formularz, a usługa się z niego rozlicza. W czasie działania nie pracuje żaden model językowy i nie ma żadnego połączenia z siecią.

> **Stan na 21.11.2026:** budowa trwa; dokładny stan i rozbieżności opisuje [`docs/03-plan/STATUS.md`](docs/03-plan/STATUS.md). Kamień milowy (a), commit `920dbf1`, znacznik `track-f-a`.

## Uruchomienie opublikowanego obrazu

Obraz: `ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:de661b017a6d950e9362f73ad3c49f555f59ad55a09823c5f067cab932be6acf`

Konwersja bez sieci i na systemie plików tylko do odczytu (polecenie z [`apps/converter/README.md`](apps/converter/README.md)):

```bash
docker run --rm --network none --read-only --cap-drop ALL --user 10001 \
  -v "$PWD/forms:/in:ro" -v "$PWD/out:/out" \
  ghcr.io/andriishramko/shramko-asystent-urzednika@sha256:de661b017a6d950e9362f73ad3c49f555f59ad55a09823c5f067cab932be6acf \
  convert /in/form.pdf --out /out/form.json
```

Kody wyjścia: 0 gotowe, 2 plik odrzucony, 3 niespójna konfiguracja, 4 plik nieczytelny. Uruchomienie jako usługa HTTP (`serve`, port 8080, token JWT) i pełna lista ustawień: [`apps/converter/README.md`](apps/converter/README.md).

## Co działa, a co jeszcze nie

- **Konwertują się dziś:** PDF, DOCX, XLSX, ODS, binarny Word (.doc).
- **W toku:** JPG, JPEG, PNG (obrazy i OCR).
- **Jeszcze nie zrobione:** dziś wytworzony formularz zawiera tytuł i standardowe sekcje partnera. Pola sprawy każdego druku pojawią się wraz z krokiem rozumienia treści (WP-F4) i jego podłączeniem, w toku. Nie ma jeszcze walidatorów, słowników, warunków, strony przeglądu dla urzędnika ani podglądu e-usługi.

## Dokumenty

| Co | Gdzie |
|---|---|
| Stan budowy | [`docs/03-plan/STATUS.md`](docs/03-plan/STATUS.md) |
| Usługa: uruchomienie, ustawienia | [`apps/converter/README.md`](apps/converter/README.md) |
| Projekt konwertera | [`docs/02-architecture/converter-design.md`](docs/02-architecture/converter-design.md) |
| Ujawnienie materiałów sprzed wydarzenia | [`NOTICE`](NOTICE) |

English: [README.md](README.md) · Dla agentów AI: [START_HERE.md](START_HERE.md)

---

# Materiały sprzed wydarzenia (wizja, nie budowane w tym zadaniu)

Poniższy opis przygotowano przed hackathonem (znacznik `pre-event`, patrz [`NOTICE`](NOTICE)). Dotyczy innego produktu, asystenta urzędnika w Bydgoszczy, który jest odłożoną wizją.

**Otwarty opis i projekt referencyjny asystenta AI dla urzędu: wspiera pracowników w analizie wniosków o udostępnienie informacji publicznej i w przygotowywaniu odpowiedzi, a w kolejnym module wypełnia urzędowe formularze danymi, które interesant podaje tylko raz.** Przygotowany na HackNation 2026, zadanie Miasta Bydgoszczy „Inteligentny asystent urzędnika”.

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

## Dokumenty wizji

| Co | Gdzie |
|---|---|
| Decyzja o zakresie i szersza platforma | [`docs/01-product/scope-decision.md`](docs/01-product/scope-decision.md) |
| Prawo i ścieżka postępowania urzędnika | [`research/02-udip-law-process-taxonomy.md`](research/02-udip-law-process-taxonomy.md) |
| Zasady i ocena HackNation | [`research/01-hacknation-2026-task-rules-jury.md`](research/01-hacknation-2026-task-rules-jury.md) |
| Katalog kart usług i formularzy Urzędu Miasta Bydgoszczy | [`data/forms-catalog.csv`](data/forms-catalog.csv) |

## Zastrzeżenia

Projekt niezależny, niezwiązany z Miastem Bydgoszcz, Ministerstwem Cyfryzacji ani inną instytucją. Analizy prawne są materiałem badawczym z podanymi źródłami i datami; nie zastępują opinii radcy prawnego ani inspektora ochrony danych.

Autor: Andrii Shramko · kontakt i licencja w [README.md](README.md).
