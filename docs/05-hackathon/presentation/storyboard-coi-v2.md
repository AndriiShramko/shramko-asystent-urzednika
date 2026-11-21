# Storyboard for the forms task, version 2: „WNIOSEK o zamianę formularza w e-usługę”

Written on 21 November 2026 at 13:40, before the build. Content follows [`../../03-plan/DECISIONS-forms-track.md`](../../03-plan/DECISIONS-forms-track.md); the look and the idea "the deck is an official form that the product processes" follow [`concept-document-deck.md`](concept-document-deck.md). This file replaces the table "The ten slides for the forms task" of the concept; everything else in the concept stays valid. Package: WP-P1.

The first judging stage reads the PDF alone, for a few minutes per project. So every slide must make its point without the speaker: one question as the headline, the paper on the left, the result on the right, at most forty words outside the drawing. The speaker's text is for the final (five minutes of talk, five of questions).

## Rules that bind every slide and every second of the film

1. **A number has one of three sources.** About our product: `eval/metrics.json`. About the partner's exports: [`../mentor-questions/reference-json-forensics.txt`](../mentor-questions/reference-json-forensics.txt). About the city's archive: `data/forms-census.json`. A number without a source is deleted, not rounded.
2. **Only what was built.** A slide or shot whose feature does not work is replaced by its fallback from the column "True only if", or removed. Nothing is re-worded into a promise.
3. **We never say "accuracy".** The ledger counts what was found and what happened to it. It does not know what the finder missed.
4. **Import status is stated as it is**: "sprawdzone w Generatorze" only after a real import with a mentor (question J13); otherwise "zgodne z eksportami wzorcowymi, import niesprawdzony".
5. **Humour**: one small pen note per slide at most, always in the margin, never about the partner's products or about officials.
6. **Polish**: short sentences, active voice, second person only where a form would use it. Before export a second reader checks the Polish (a native speaker if one is at hand, otherwise a review by a model of another family through `tools/eden/eden.py`).
7. **Pre-event material is named** on slide 10.

## The ten slides

### Slide 1. Nagłówek: „WNIOSEK o zamianę formularza w e-usługę”

| | |
|---|---|
| Printed on the slide | „WNIOSEK o zamianę formularza w e-usługę”. „Wnioskodawca: Shramko Formularze (Andrii Shramko)”. „Adresat: Centralny Ośrodek Informatyki, zadanie „Cyfryzacja formularzy””. „Przedmiot wniosku: kompilator z księgowym, nie skaner z AI.” |
| Visual | Left: the paper header with boxes and a dotted line. The form's own instruction „Wypełnić drukowanymi literami.” and under it, in pen: „Już nie trzeba.” Red stamp „WPŁYNĘŁO 22.11.2026”. Right: the same header as the first page of an e-service |
| Speaker (Polish) | „Dzień dobry. Składamy wniosek o zamianę formularza w e-usługę. Zbudowaliśmy kompilator z księgowym, nie skaner z AI: z pustego druku powstaje JSON dla Generatora Formularzy, a każde pole i każda pominięta rubryka są rozliczone.” |
| Russian gloss | Здравствуйте. Подаём заявление о превращении бланка в электронную услугу. Мы построили компилятор с бухгалтером, а не сканер с ИИ: из пустого бланка получается JSON для Генератора форм, и каждое поле и каждая пропущенная графа учтены. |
| Numbers | none |
| True only if | the right side is the real output for this deck's own PDF; otherwise show the paper header alone |

### Slide 2. A. „Stan faktyczny: jedna strona papieru, 69 komponentów”

| | |
|---|---|
| Printed on the slide | „Druk: 1 strona.” „E-usługa w eksporcie partnera: 4 strony, 16 sekcji, 53 pola i bloki.” „Około czterech piątych nie ma na papierze: pochodzi ze standardu COI.” Legend: „niebieski atrament: z papieru”, „czarny druk: ze standardu”. |
| Visual | Left: the one-page paper form of reference set 1. Right: the tree of the partner's own export drawn in two inks. The few blue nodes stand out: title, addressee, the four fields of the matter, contact |
| Speaker (Polish) | „To jest przykład wzorcowy partnera. Jedna strona papieru staje się czterostronicową e-usługą z 69 komponentami, a około czterech piątych z nich pochodzi ze standardu COI, nie z druku. Dlatego nie przepisujemy rubryk: kompilujemy druk do gramatyki Generatora.” |
| Russian gloss | Это эталонный пример партнёра. Одна страница бумаги становится услугой на четыре страницы из 69 компонентов, и около четырёх пятых берётся из стандарта COI, а не с бланка. Поэтому мы не переписываем графы: мы компилируем бланк в грамматику Генератора. |
| Numbers | 1 page, 4 pages, 16 sections + 53 components = 69: the forensics file. „Około czterech piątych”: estimate of `docs/02-architecture/coi-json-format.md` §1 until the origin tags give the measured share (`eval/metrics.json`, reference set 1) |
| True only if | always true: it shows the partner's export, not our output. Do not imply that our conversion reproduces the count unless the comparison of the evaluation run says so |

### Slide 3. B. „Czego wnioskodawca nie napisał”

| | |
|---|---|
| Printed on the slide | In print, the partner's own statement: „Wiele formatów. Brak wspólnego standardu. Każdy formularz analizowany ręcznie.” In pen, in the margin: „Skąd wiem, że nic nie zginęło? → D”. „Kto wnioskuje: osoba, pełnomocnik, firma? → E”. „A trudne druki? → F”. „Co, gdy materiały mówią dwie rzeczy? → G”. „Czy plik z urzędu może zaszkodzić? Ile to kosztuje? → H”. |
| Visual | The part "A. Opis problemu" of a form, filled in print; five pen notes with arrows to the letters of the following parts |
| Speaker (Polish) | „Karta zadania mówi o wielu formatach i braku standardu. Na marginesie dopisaliśmy to, czego nikt nie napisał: zaufanie do wyniku, role wnioskodawcy, trudne druki, sprzeczne materiały, bezpieczeństwo i koszt. Każda notatka prowadzi do części wniosku, która na nią odpowiada.” |
| Russian gloss | Карточка задания говорит о множестве форматов и отсутствии стандарта. На полях мы дописали то, чего никто не написал: доверие к результату, роли заявителя, трудные бланки, противоречия в материалах, безопасность и стоимость. Каждая заметка ведёт к части заявления, которая на неё отвечает. |
| Numbers | none. If the partner's team answered question P15 (how long one form takes today), add in pen „dziś: … (wg zespołu COI, 21.11.2026)” |
| True only if | each arrow points to a slide that survived rule 2 |

### Slide 4. C. „Sposób załatwienia sprawy”

| | |
|---|---|
| Printed on the slide | Six stamps in a row: „WPŁYW: bramka”, „ODCZYT: 8 formatów”, „RUBRYKI”, „ZNACZENIE: 10 pytań”, „ZAPIS: JSON partnera”, „KONTROLA: przed importem”. Under them: „Odpowiedź usługi: wyłącznie title, tabs, flow.” „Rozliczenie: osobny plik.” „Model językowy: brak. Połączenia na zewnątrz: brak.” |
| Visual | The route of a document through an office, drawn as the form's circulation slip; the last stamp is green |
| Speaker (Polish) | „Plik przechodzi przez sześć okienek: bramka, odczyt, rubryki, znaczenie, zapis i kontrola. Usługa odpowiada czystym JSON-em w strukturze partnera, a całe rozliczenie jedzie obok, w osobnym pliku. W kontenerze nie ma modelu językowego i nic nie wychodzi do sieci.” |
| Russian gloss | Файл проходит шесть окошек: шлюз, чтение, графы, смысл, запись и контроль. Сервис отвечает чистым JSON в структуре партнёра, а весь учёт едет рядом, отдельным файлом. В контейнере нет языковой модели, и ничего не уходит в сеть. |
| Numbers | 8 formats: the task card. 10 questions: `coi-json-format.md` §8 |
| True only if | the judged forms convert through the public endpoint; the offline test passed on the submitted image |

### Slide 5. D. „Dowód: bilans rubryk”

| | |
|---|---|
| Printed on the slide | „Rubryk na papierze: N. Pola: a. Połączone z innym polem: b. Pominięte z powodem: c. Do decyzji urzędnika: d.” One receipt: „rząd 11 kratek → jedno pole PESEL z kontrolą cyfry”. One omission: „(podpis wnioskodawcy): tylko na papierze”. One refusal: „Opłata: nie ustalono, brak na druku”. |
| Visual | A real screenshot of the review page: the source page with every found blank outlined, beside the form tree; the ledger line under it. In pen, next to „niepotrzebne skreślić”: „Skreślone. Z uzasadnieniem.” |
| Speaker (Polish) | „Każde miejsce do wypełnienia z papieru ma u nas dalszy los: staje się polem, łączy się z innym, zostaje pominięte z podanym powodem albo czeka na decyzję urzędnika. Opłat, uprawnień i obowiązkowych załączników nie zgadujemy: pokazujemy cytat z druku albo „nie ustalono”. To jest bilans, nie miara dokładności.” |
| Russian gloss | У каждого места для заполнения на бумаге есть судьба: оно становится полем, сливается с другим, пропускается с названной причиной или ждёт решения чиновника. Сборы, права и обязательные приложения не угадываем: показываем цитату с бланка или «не установлено». Это баланс, а не мера точности. |
| Numbers | N, a, b, c, d: `eval/metrics.json`, ledger of the form on the screenshot. The receipt, the omission and the refusal are real rows of that form's report |
| True only if | the ledger and the origin tags exist. Fallback: the screenshot of the review page with one field and its source crop, without the ledger line |

### Slide 6. E. „Dowód: kto wnioskuje”

| | |
|---|---|
| Printed on the slide | „Trzy osoby w jednej sprawie: zalogowany człowiek, strona, w której imieniu działa, i jego rola.” „Sześć ścieżek, każdy warunek wykonany.” „Pole należy do roli, nie do strony.” |
| Visual | A small diagram of the three actors. A table of the six journeys (w swoim imieniu; pełnomocnik innej osoby; reprezentant podmiotu; pełnomocnik podmiotu; adres w Polsce; adres za granicą) with the sections each one sees. A seventh row in pen: „nic nie zaznaczono: sekcje warunkowe ukryte”. One real line of `states[].query` |
| Speaker (Polish) | „Osoba, pełnomocnik i firma nie przechodzą tej samej ścieżki. Odtwarzamy sześć ścieżek i wykonujemy każdy warunek JSONata, zanim oddamy plik: także wtedy, gdy obywatel jeszcze niczego nie zaznaczył. Pole należy do roli, nie do strony, więc firma nie zobaczy pytania o PESEL obywatela.” |
| Russian gloss | Человек, представитель и фирма идут разными маршрутами. Мы воспроизводим шесть маршрутов и исполняем каждое условие JSONata до выдачи файла: в том числе когда гражданин ещё ничего не отметил. Поле принадлежит роли, а не странице, поэтому фирма не увидит вопрос о PESEL гражданина. |
| Numbers | six journeys: DECISIONS §5 item 4. Count of evaluated conditions and of visible sections per journey: `eval/metrics.json` |
| True only if | the journeys test and the zero-answer test run on our output. Fallback: the same table computed on the partner's reference export in our viewer, labelled as such |

### Slide 7. F. „Dowód: trudne druki”

| | |
|---|---|
| Printed on the slide | „Deklaracja odpadowa: 6 stron, tabele, wyliczenia.” „Wniosek sportowy: 16 stron, trzy wnioski w jednym pliku.” „Zielone: zamienione na pola. Czerwone: czeka na decyzję urzędnika.” |
| Visual | Two page thumbnails with green and red outlines. For the declaration: the operands and units of one calculation in green, the formula in red with the note „format partnera nie pokazuje pola obliczanego: wzór jest w raporcie”. For the sports form: three coloured page ranges and one question „jedna usługa z wyborem czy trzy osobne?” |
| Speaker (Polish) | „Nie pokazujemy tylko łatwych przykładów. W deklaracji odpadowej rozpoznajemy składniki i jednostki wyliczenia, ale nie wymyślamy klucza na wzór, którego w formacie partnera nie widzieliśmy. W szesnastostronicowym wniosku sportowym wykrywamy trzy wnioski w jednym pliku i zostawiamy urzędnikowi jedną decyzję.” |
| Russian gloss | Мы показываем не только лёгкие примеры. В декларации об отходах распознаём слагаемые и единицы расчёта, но не выдумываем ключ для формулы, которого в формате партнёра не видели. В шестнадцатистраничном спортивном заявлении находим три заявления в одном файле и оставляем чиновнику одно решение. |
| Numbers | 6 and 16 pages: the PDF files of judged sets 8 and 9. Counts of green and red items: `eval/metrics.json` |
| True only if | both forms convert with a report. Fallback: one of the two; never a form that was not run |

### Slide 8. G. „Rozbieżności w materiałach: osiem decyzji”

| | |
|---|---|
| Printed on the slide | A register with the columns „Lp.”, „Gdzie”, „Reguły lub schemat”, „Eksport”, „Nasza decyzja”, „Przełącznik”, eight rows (below). Under it: „Zmiana interpretacji to jedna linia konfiguracji.” |
| Visual | The register as a form's "wykaz". A magnifier on row 8 (the last page). No joke on this slide |
| Speaker (Polish) | „W materiałach znaleźliśmy osiem miejsc, w których schemat, opis i eksporty mówią co innego. Każde ma u nas decyzję, dowód i przełącznik, więc zmiana interpretacji to jedna linia konfiguracji, nie przebudowa. Tę listę oddajemy partnerowi jako gotową erratę.” |
| Russian gloss | В материалах мы нашли восемь мест, где схема, описание и экспорты говорят разное. У каждого есть наше решение, доказательство и переключатель, поэтому смена толкования это одна строка настройки, а не переделка. Этот список мы отдаём партнёру как готовый перечень исправлений. |
| Numbers | eight: `coi-json-format.md` §10. 34 of 34 occurrences of the key: the forensics file |
| True only if | always true. Update the rows with the mentors' answers (questions J3, J4, J5, J6, J10) before export |

Rows of the register (Polish, as printed):

| Lp. | Gdzie | Reguły lub schemat | Eksport | Nasza decyzja |
|---|---|---|---|---|
| 1 | klucz siatki sekcji | „repetingSectionGrid” | „repeatingSectionGrid”, 34 z 34 | jak w eksporcie |
| 2 | obowiązkowość pola | każde pole ma atrybut | brak REQUIRED w obu eksportach | REQUIRED tam, gdzie wynika z druku lub standardu |
| 3 | dane inicjalne | zawsze tylko do odczytu | tożsamość zablokowana, adres i kontakt edytowalne | jak w eksporcie |
| 4 | kształt „validation” | lista | w trzech polach obiekt {} | zawsze lista |
| 5 | nazwy słowników | Województwo, Powiat, Gmina, Miejscowość, Kraje, Numery kierunkowe | „Kraje”, „TERYT_DOWODOWY”, „TERYT_4G_DOWODOWY” | tylko nazwy z eksportów; reszta jako propozycje w raporcie |
| 6 | limity plików | opisane w standardzie | brak klucza | nie wymyślamy klucza; propozycja w raporcie |
| 7 | klucze spoza opisu | brak | „multiLevelTree”, „searchEnabled”, „minItemRows” | tylko tam, gdzie widać je w eksporcie |
| 8 | strona końcowa | INFO_SECTION | SECTION z TEXT_BLOCK | jak w eksporcie, z przełącznikiem |

### Slide 9. H. „Oświadczenia”

| | |
|---|---|
| Printed on the slide | Tick boxes, each with its proof in small print: „☑ Rozwiązanie nie korzysta z modeli dostępnych wyłącznie przez API ani z usług zewnętrznych. Dowód: kontener uruchomiony bez sieci, GET /v1/selftest.” „☑ Biblioteki mają otwarte licencje bez copyleft. Dowód: bramka licencji, LICENCES.md, SBOM.” „☑ Każdy plik czyta osobny proces z limitami. Dowód: zawieszone zadanie przerwane, następne przechodzi.” „☑ Tekst z druku nie staje się kodem w Generatorze. Dowód: test z drukiem zawierającym skrypt.” „☑ Plik żyje tylko w pamięci, treść nie trafia do logów. Dowód: test ze znacznikiem, którego w logach nie może być.” „☑ Token JWT: algorytmy z konfiguracji, wymagane exp, iss, aud. Dowód: testy negatywne.” Box „Koszt jednego formularza”: seconds of CPU and megabytes, by class of input, „bez GPU”. |
| Visual | The declarations part of a Polish form. First line in print: „Jestem świadomy odpowiedzialności za złożenie fałszywego oświadczenia.” and in pen: „Dlatego każde ma test.” |
| Speaker (Polish) | „To są nasze oświadczenia, każde z testem, który można uruchomić. Usługa działa bez GPU i bez modelu językowego: koszt jednego formularza to zmierzone sekundy procesora. Największym kosztem pozostaje czas urzędnika, a ten skracamy do kilku decyzji.” |
| Russian gloss | Это наши заявления, у каждого есть тест, который можно запустить. Сервис работает без видеокарты и без языковой модели: стоимость одной формы это измеренные секунды процессора. Самой дорогой остаётся работа чиновника, и её мы сокращаем до нескольких решений. |
| Numbers | seconds and memory per form, by class (text file, scan): `eval/metrics.json`, with the hardware named. Any extrapolation to the country is shown with its assumptions; the number of municipalities is 2 479 (state on 1 January 2026, Ministry of the Interior and Administration: `research/13`), not the 2,477 that appears in some drafts |
| True only if | each tick has a passing test in the repository at that hour; a declaration without a test is deleted from the slide |

### Slide 10. „ADNOTACJE URZĘDOWE (wypełnia jury)”

| | |
|---|---|
| Printed on the slide | The partner's criteria as a table, each with a tick and the place of the proof: „Kompletność 30 %: minimum; słowniki i dane inicjalne; propozycja nowego słownika; zależności dynamiczne; front do importu; walidacje”. „Intuicyjność 20 %: ekran przeglądu, slajd D, film od 0:18”. „Oryginalność 10 %: bilans rubryk, dwa kolory atramentu, rejestr rozbieżności”. „Jakość kodu 20 %: testy, kontrola przed importem, README”. „Potencjał wdrożeniowy 20 %: bez GPU, koszt na formularz, Docker”. „Załączniki: 1) siedem plików JSON, 2) film, 3 minuty, 3) repozytorium, 4) raporty rozliczeń.” „Import do Generatora: …” (rule 4). „Prośba do COI: zestaw testów zgodności importu z przykładowymi odpowiedziami.” „Decyzja: ☐ pozytywna ☐ bardzo pozytywna”. Small print: „Badania, spis 661 dokumentów jednego miasta i specyfikacja powstały przed wydarzeniem.” |
| Visual | The part every Polish form has, already filled in with ticks; QR codes to the repository and the film; the stamp „ZATWIERDZAM. Człowiek” left empty for the jury |
| Speaker (Polish) | „Ostatnia część jest dla Państwa: tabela kryteriów z miejscem, w którym leży dowód. Mówimy też otwarcie, czego nie wiemy: importu do Generatora nie mogliśmy sprawdzić sami, dlatego prosimy o zestaw testów zgodności. Dziękuję.” |
| Russian gloss | Последняя часть для вас: таблица критериев с местом, где лежит доказательство. Говорим открыто и о том, чего не знаем: импорт в Генератор мы сами проверить не могли, поэтому просим набор тестов совместимости. Спасибо. |
| Numbers | weights: the task card. 661: `data/forms-census.json`. Seven files: `results/` |
| True only if | a tick stands only next to an extension that the evaluation run shows. If a mentor imported one of our files (J13), the second sentence of the speech becomes: „Jeden z naszych plików zaimportowaliśmy z mentorem do Generatora: wynik jest w repozytorium.” If the deck's own PDF went through the service, add the line „Ten wniosek przeszedł przez naszą usługę: wynik leży w results/.” |

## The film: three minutes at most, target 2:52

Screen recording of the running product. Captions only, in Polish, at most eight words each; no voice is needed. The timer on the screen is never accelerated; waiting may be cut only with a visible mark „cięcie”. Only blank forms appear. No slides inside the film.

| Seconds | Shot | Caption (Polish) | If the feature is missing |
|---|---|---|---|
| 0:00–0:18 | The paper page of reference set 1 beside the tree of the partner's own export, opened in our viewer | „Jedna strona papieru. 69 komponentów.” then „Większości nie ma na druku.” | open the export as text; keep the captions |
| 0:18–0:48 | A file that was not used during the build is uploaded to the local container. The real elapsed time is visible. The toggle „tylko z papieru”. A click on one field lights up its place on the source page | „Plik, którego nie znaliśmy.” then „Niebieskie: z papieru. Czarne: ze standardu.” | without the toggle: show the field and its source place only |
| 0:48–1:18 | In the viewer the choice changes from „w swoim imieniu” to an entity through a representative. The read-only identity field and the entity's data stay in frame; the proof-of-representation block appears | „Osoba, pełnomocnik, firma: różne ścieżki.” | show the same switch on the partner's reference export, labelled „eksport wzorcowy” |
| 1:18–1:48 | A real unresolved item: an ambiguous attachment or a merged table heading of the waste declaration. A click on the warning jumps to the page | „Nie zgadujemy. Pokazujemy, czego nie wiemy.” | show the list of warnings of the report |
| 1:48–2:20 | The ledger of blanks and the green zero-answer test. The plain JSON is downloaded; zoom on one real `states[].query` and the `techName` it points to. Import into the Generator only if it really happened with a mentor | „Bilans rubryk. Każdy warunek wykonany.” | show the pre-import gate passing in the terminal |
| 2:20–2:52 | One terminal: the image tag, the container started without network and its self-test, the seven output files, the count of failures, seconds and memory for a text file and for a scan | „Bez sieci. Bez GPU. Siedem plików JSON.” then the end card „Urzędnik zatwierdza znaczenie, nie przepisuje rubryk.” with the repository address | show only the lines that are true |

Eight seconds stay free. Recording rules: 1080p, interface zoom large enough to read on a phone, one take per shot, the mouse moves slowly, no private windows or notifications on the screen (record in a clean browser profile).

## What the mentors' answers change here

| Answer | Change |
|---|---|
| J13 yes (an import was tried) | slide 10 import line and speech; film shot 1:48–2:20 shows the import |
| J2 (how the JSON is judged) | order of the proofs on slide 10: import first, or closeness to the reference, or the design rules |
| J11 no (materials not public) | no page of the partner's sets is recognisable in the public PDF or film: use our own synthetic form for close-ups and only tree views for the judged forms |
| P15 (time of manual digitisation today) | one pen note on slide 3, with the attribution |
| P17 (what would impress them) | which of slides 5, 6, 7 comes first after the pipeline |

## Checklist before export

- [ ] Ten slides or fewer; PDF under 10 MB; fonts embedded.
- [ ] Every number equals its source file; the hardware is named next to every time.
- [ ] No „(plan)”, no square bracket, no placeholder letter (N, a, b, c, d) left.
- [ ] The stamp „próbka wyglądu” is gone only if the build equals the claims.
- [ ] Film at most 3:00, opens from an open link in a private browser window.
- [ ] Polish read by a second reader (rule 6); the speaker read all ten texts aloud three times.
- [ ] A reader who sees only slides 1, 3 and 10 can say what the product does, which pains it answers and how it scores.
