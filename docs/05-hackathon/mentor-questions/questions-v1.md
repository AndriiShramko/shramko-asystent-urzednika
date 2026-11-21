# Questions prepared for the partner's mentors (version 1, 21 November 2026, 12:45)

Two sets: `T` for the technical mentor (the JSON format), `B` for the business side. Polish text is what the owner reads aloud; options are one-tap answers.
Version 1 was written before the research of this afternoon. The goal now: answer as many as possible ourselves, with evidence, and keep for the mentors only what nobody outside the partner can know.

## TECHNIKA (format JSON)

| Id | Question (Polish) | Options |
|---|---|---|
| T1 | Klucz sekcji: przy imporcie poprawny jest „repeatingSectionGrid” (jak w przykładzie), a nie „repetingSectionGrid” (jak w schemacie)? | repeatingSectionGrid / repetingSectionGrid / Oba działają |
| T2 | Jak będzie oceniany nasz JSON? | Import do Waszego systemu / Porównanie ze wzorcem / Ocena ekspercka |
| T3 | Czy import odrzuci plik, w którym są dodatkowe, nieznane klucze (nasze metadane)? | Odrzuci / Zignoruje klucze / Nie wiem |
| T4 | W przykładzie żadne pole nie ma REQUIRED. Czy mamy ustawiać REQUIRED w „validation”? | Tak / Nie / Tylko gdy papier wymaga |
| T5 | Czy dostaniemy dokładne nazwy słowników do „dictionaryName”, poza „Kraje” i „TERYT_DOWODOWY”? | Tak, podadzą / Nie ma listy / Tylko te dwa |
| T6 | Ostatnia strona: „INFO_SECTION” (jak w regułach) czy „SECTION” z „TEXT_BLOCK” (jak w przykładzie)? | INFO_SECTION / SECTION + TEXT_BLOCK / Oba poprawne |
| T7 | Pola z danych inicjalnych MLPZ, adres i kontakt: tylko do odczytu czy edytowalne? | Zawsze readOnly / Adres i kontakt edytowalne / Zależy od pola |
| T8 | Czy otwarty model językowy uruchomiony lokalnie w kontenerze jest dozwolony? | Tak / Nie / Tylko bez GPU |
| T9 | Na jakim sprzęcie uruchomimy rozwiązanie na obronie? | Nasz laptop / Wasz serwer / Bez GPU / Z GPU |
| T10 | Czy LibreOffice (licencja MPL 2.0) w kontenerze do konwersji DOC i ODS jest dopuszczalny? | Tak / Nie / Nie wiem |
| T11 | Czy odpowiedź REST ma być wyłącznie JSON-em formularza, czy może mieć kopertę z raportem (ostrzeżenia, pewność)? | Wyłącznie JSON formularza / Koperta jest OK / Raport osobnym endpointem |
| T12 | Limit plików w FILE_UPLOADER i walidacja wzorcem (regex): czy jest na to klucz w JSON? | Tak / Nie / W planach |
| T13 | Python 3.14 i obraz Alpine: wymóg czy preferencja? | Wymóg / Preferencja |
| T14 | JWT na obronie: jaki algorytm i skąd klucz? | HS256, sekret w zmiennej / RS256, klucz publiczny / JWKS z adresu URL / Dowolnie, byle konfigurowalne |
| T15 | Nowe pliki na obronie: te same formaty co w materiałach, także skany? | Tak, także skany / Bez skanów / Nie wiadomo |
| T16 | Czy materiały zadania możemy trzymać w publicznym repozytorium? | Tak / Nie |
| T17 | Czy aplikacja pokazująca e-usługę z JSON (wizualizacja) jest punktowana? | Tak / Nie |
| T18 | „techName”: unikalny w sekcji czy w całym formularzu? | W sekcji / W całym formularzu |
| T19 | Układ: zawsze jedna kolumna (x = 0, cols = 3), czy możemy używać kilku kolumn? | Zawsze jedna / Można kilka |
| T20 | Identyfikatory „id”: dowolne UUID, czy stabilne między wersjami tego samego formularza? | Dowolne UUID / Stabilne między wersjami |
| T21 | Sekcja powtarzalna: czy jest limit powtórzeń albo klucz na minimum i maksimum? | Jest / Nie ma |

## BIZNES (potrzeby)

| Id | Question (Polish) | Options |
|---|---|---|
| B1 | Kto będzie głównym użytkownikiem narzędzia? | Urzędnik w gminie / Analityk COI / Obaj |
| B2 | Ile dziś trwa ręczna cyfryzacja jednego formularza? | Do 1 godziny / Kilka godzin / Dzień lub więcej |
| B3 | Co zabiera najwięcej czasu? | Analiza treści / Podział na strony i sekcje / Walidacje i słowniki / Zależności (JSONata) / Poprawki po testach |
| B4 | Co jest ważniejsze w wyniku: wierność papierowi czy zgodność ze standardem? | Wierność papierowi / Zgodność ze standardem / Jedno i drugie |
| B5 | Czy narzędzie ma samo dodawać standardowe sekcje, których nie ma na papierze (podmiot wniosku, pełnomocnictwo, kontakt)? | Tak, zawsze / Tylko gdy pasują / Nie |
| B6 | Czy każdy formularz ma mieć trzy warianty wnioskodawcy: w swoim imieniu, za inną osobę, za firmę lub instytucję? | Zawsze trzy / Tylko te z papieru / Zależy od sprawy |
| B7 | Czy urzędnik ma zatwierdzić wynik przed importem do systemu? | Tak, zawsze / Tylko pola niepewne / Nie trzeba |
| B8 | Czy przydałby się raport: czego nie przeniesiono z papieru i dlaczego (podpis, data, „wypełnia urząd”)? | Tak / Nie / Nie wiem |
| B9 | Czy wzory formularzy często się zmieniają (nowelizacje, nowe wersje)? | Często / Kilka razy w roku / Rzadko |
| B10 | Czy porównanie dwóch wersji formularza (co doszło, co znikło, co zmieniło nazwę) byłoby dla Was wartością? | Tak, bardzo / Trochę / Nie |
| B11 | Czy dla firm przydałyby się dane inicjalne z rejestrów (CEIDG, KRS, REGON)? | Tak, bardzo / Kiedyś / Nie |
| B12 | Jednoosobowa działalność: traktować jak osobę fizyczną z NIP, czy jak podmiot? | Osoba z NIP / Podmiot / Zależy od sprawy |
| B13 | Pełnomocnik: czy zawsze dodawać załącznik z pełnomocnictwem i opłatę skarbową 17 zł? | Tak / Tylko gdy papier o tym mówi / Nie |
| B14 | Których walidacji brakuje Wam najbardziej? | Rachunek bankowy / Telefon / Numer KRS / Zakres dat / Wzorzec (regex) / Księga wieczysta / Numer działki |
| B15 | Jakie nowe słowniki byłyby najcenniejsze? | Dokument tożsamości / Typ ulicy / Forma prawna / Urzędy i organy / Banki / Kody PKD |
| B16 | Propozycja nowego słownika: w osobnym pliku czy w JSON formularza? | Osobny plik / W JSON formularza / Obojętnie |
| B17 | Ile formularzy czeka na cyfryzację? | Dziesiątki / Setki / Tysiące |
| B18 | Czy przetwarzanie wsadowe (cały folder formularzy naraz) jest dla Was ważne? | Tak, bardzo / Mile widziane / Nie |
| B19 | Czy narzędzie musi działać w sieci urzędu bez dostępu do internetu? | Tak / Nie / Zależy od urzędu |
| B20 | Gdy ktoś wgra wypełniony formularz z danymi osobowymi, co robić? | Odrzucić plik / Ostrzec i przetworzyć / Usunąć dane i przetworzyć |
| B21 | Czy potrzebny jest dziennik zdarzeń: kto, kiedy i jaki plik cyfryzował? | Tak / Nie / Nie wiem |
| B22 | Czy formularze tej samej sprawy z różnych urzędów warto sprowadzać do jednego wspólnego wzoru? | Tak / Nie / Nie wiem |
| B23 | Czy formularze mają być kiedyś wypełniane także przez asystentów AI obywateli? Czy opis „dla agentów” z tego samego JSON byłby wartością? | Tak / Może w przyszłości / Nie |
| B24 | Jedna rzecz, która zrobiłaby na Was największe wrażenie? | (open) |
| B25 | Najczęstszy błąd, którego nie chcecie widzieć w rozwiązaniach? | (open) |
