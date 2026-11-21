# Pitch deck storyboard for the task "Cyfryzacja formularzy": "Od druku do usługi online"

Second deck, for the task of Centralny Ośrodek Informatyki: "Jak sztuczna inteligencja może wspierać rozwój nowoczesnych usług publicznych? … usprawnić proces cyfryzacji i sprawić, że droga od potrzeby do wygodnej usługi online będzie prostsza i szybsza." The owner's instruction (21 November): as little theory on slides as possible; show a working product with the two sides, visitor and clerk, and how fast a form is filled and handed over.

Live address: <https://formularze.flyreelstudio.eu/deck/> (served from `site-formularze/deck/`; pushing to `main` updates it within two minutes). It reuses the engine of the first deck (`site/deck/deck.js`, `deck.css`): same keys, same presenter window, same print mode.

## Shape of this deck

Eight slides. Two of them are live demo slides and take most of the five minutes. The other six take ten to twenty seconds each. The same rules as the first deck apply ([`storyboard.md`](storyboard.md), "Rules of this deck"): movement on every slide, at most six words on screen, labels of at most three words, at most three short sentences of speech, only true claims, numbers only when measured (`metrics.json`), present tense only for what is built (`status.json`).

Facts used and their sources: 275 service cards and 710 form files of one city hall, and one fillable PDF among 32 analysed forms ([`research/03`](../../../research/03-forms-catalog-bydgoszcz.md), [`research/03b`](../../../research/03b-form-anatomy-and-canonical-profile.md)); the 2022 volunteer service in Opole ([`research/09`](../../../research/09-lessons-from-2022-prototype.md)); the QR data-sharing flow in the government app ([`research/04`](../../../research/04-mobywatel-identity-once-only.md)).

## Slides

Fields: **Screen** · **Motion** · **Say** (Polish) · **RU** (meaning) · **Cue** · **Caption** (for the PDF).

### 1. The size of the problem

- **Screen:** 710 druków. Jedno miasto.
- **Motion:** a map pin „Bydgoszcz”; paper icons marked PDF, DOC, RTF pour out of it and stack into a wall; two counters run up to „275 kart usług” and „710 plików”; at the end one single sheet lights up green with the label „1 z 32 z polami”.
- **Say:** Szanowni Państwo, dzień dobry. W jednym mieście policzyliśmy 275 kart usług i 710 plików formularzy, a tylko jeden z 32 zbadanych ma pola do wypełnienia. Każdy z tych druków czeka na swoją usługę online.
- **RU:** В одном городе мы насчитали 275 карточек услуг и 710 файлов бланков, и только один из 32 изученных имеет поля для заполнения. Каждый из этих бланков ждёт своей онлайн-услуги.
- **Cue:** дождись, пока один лист загорится зелёным.
- **Caption:** Skala: w jednym urzędzie miasta 275 kart usług i 710 plików formularzy (PDF, DOC, RTF); tylko 1 z 32 zbadanych formularzy ma pola do wypełnienia. Dane: katalog w repozytorium projektu.

### 2. The solution in one picture

- **Screen:** Od druku do usługi.
- **Motion:** a paper form enters from the left; a scanning line passes over it and coloured boxes appear on its fields; a person icon presses „zatwierdź”; the form splits into three results that slide to the right: a phone with a form („formularz online”), a printed sheet identical to the original („wydruk na wzorze”), a checklist with ticks („reguły kontroli”).
- **Say:** Nasze rozwiązanie zamienia urzędowy druk w usługę online: AI rozpoznaje pola i proponuje ich znaczenie, a człowiek zatwierdza. Z jednego opisu powstają formularz na telefon, wydruk na oryginalnym wzorze i reguły kontroli.
- **RU:** Наше решение превращает официальный бланк в онлайн-услугу: ИИ распознаёт поля и предлагает их значение, человек утверждает. Из одного описания получаются форма для телефона, печать на оригинальном образце и правила проверки.
- **Cue:** три результата выедут сами; сразу переходи к показу.
- **Caption:** AI rozpoznaje pola urzędowego druku i proponuje ich znaczenie, człowiek zatwierdza; z jednego opisu powstają formularz online, wydruk na oryginalnym wzorze i reguły kontroli.

### 3. Demo, part one: a new form becomes a service (pause slide)

- **Screen:** Demo: nowy formularz
- **Motion:** if `media/demo-1.mp4` exists it plays muted in a loop; otherwise an animated mock: a PDF is dropped onto a window, boxes appear on its fields one after another, labels type themselves next to them („imię”, „PESEL”, „adres”), two boxes are dragged into place by a cursor, a button „Opublikuj” is pressed and a small phone form pops up.
- **Say:** Pokażę to na żywo: wgrywam druk pobrany ze strony urzędu. AI proponuje pola, ja poprawiam to, co trzeba, i publikuję. Formularz online jest gotowy.
- **RU:** Покажу вживую: загружаю бланк, скачанный с сайта мэрии. ИИ предлагает поля, я поправляю, что нужно, и публикую. Онлайн-форма готова.
- **Cue:** переключись на программу (Alt+Tab), сделай оцифровку одного бланка и вернись. Время назови, только если оно измерено.
- **Caption:** Pokaz 1: druk pobrany ze strony urzędu zostaje rozpoznany przez AI, poprawiony przez człowieka i opublikowany jako formularz online.

### 4. Demo, part two: visitor and clerk (pause slide)

- **Screen:** Demo: interesant i urzędnik
- **Motion:** if `media/demo-2.mp4` exists it plays muted in a loop; otherwise an animated mock in two halves: on the left a phone scans a QR code and a short form fills itself; a locked packet flies to the right half, a clerk's screen, where the data appears in very large type with ticks; one field turns amber with a small note „sprawdź datę”; a button „Drukuj” is pressed and a filled sheet slides out with a dotted signature line.
- **Say:** Teraz interesant: skanuje kod i podaje dane raz, na swoim telefonie. Urzędnik widzi je od razu, a AI wskazuje błąd przed wydrukiem. Wniosek drukuje się na urzędowym wzorze, gotowy do podpisu.
- **RU:** Теперь посетитель: сканирует код и вводит данные один раз, на своём телефоне. Чиновник видит их сразу, а ИИ указывает на ошибку до печати. Заявление печатается на официальном образце, готовое к подписи.
- **Cue:** дай члену жюри отсканировать код своим телефоном, если сеть позволяет; иначе покажи на своём телефоне.
- **Caption:** Pokaz 2: interesant podaje dane raz na telefonie, urzędnik widzi je od razu, AI wskazuje błędy, a wniosek drukuje się na urzędowym wzorze.

### 5. Proven in a real queue

- **Screen:** Sprawdzone w kolejce. Opole 2022.
- **Motion:** a queue of people, each holding a phone that glows as they type; at the head of the queue a printer pushes out filled forms one after another; the queue visibly shortens; a badge „punkt pomocy uchodźcom”.
- **Say:** To nie teoria: w 2022 roku w punkcie pomocy uchodźcom w Opolu ludzie wpisywali dane na telefonach, stojąc w kolejce. Wolontariusze drukowali gotowe wnioski, zamiast przepisywać dokumenty ręcznie. Z tamtych doświadczeń pochodzą reguły tego systemu.
- **RU:** Это не теория: в 2022 году в пункте помощи беженцам в Ополе люди вводили данные на телефонах, стоя в очереди. Волонтёры печатали готовые заявления вместо того, чтобы переписывать документы вручную. Из того опыта взяты правила этой системы.
- **Cue:** это твой настоящий опыт; скажи спокойно и коротко.
- **Caption:** Rozwiązanie wyrosło z praktyki: w 2022 r. w punkcie pomocy uchodźcom w Opolu interesanci wpisywali dane na telefonach w kolejce, a wolontariusze drukowali gotowe wnioski.

### 6. Data once, without a shared database

- **Screen:** Dane raz. Bez wspólnej bazy.
- **Motion:** a phone holds a profile with a padlock; only three of its many fields light up and fly, locked, through a QR code to an office building; a small timer above them runs out and the packet dissolves; underneath, a shelf „rejestr wzorów” connects several office buildings while a big database of people is crossed out.
- **Say (if built):** Dane zostają na telefonie mieszkańca: do urzędu trafiają tylko pola potrzebne w tej sprawie, zaszyfrowane, na kilka minut. W mObywatelu istnieje już przekazywanie danych instytucji kodem QR i nasz adapter jest na to przygotowany. Wspólny dla urzędów jest rejestr opisów formularzy, a nie baza danych o ludziach.
- **Say (fallback, not built):** Dane zostają na telefonie mieszkańca: do urzędu trafiają tylko pola potrzebne w tej sprawie, zaszyfrowane, na kilka minut. W mObywatelu istnieje już przekazywanie danych instytucji kodem QR; nasz projekt przewiduje taki adapter. Wspólny dla urzędów jest rejestr opisów formularzy, a nie baza danych o ludziach.
- **RU:** Данные остаются на телефоне жителя: в мэрию уходят только поля, нужные для этого дела, зашифрованные, на несколько минут. В mObywatel уже есть передача данных учреждению по QR-коду, и наш адаптер к этому готов. Общим для учреждений будет реестр описаний бланков, а не база данных о людях.
- **Cue:** это слайд для людей из COI: про mObywatel скажи обязательно.
- **Caption:** Dane pozostają na telefonie mieszkańca; do urzędu trafiają tylko potrzebne pola, zaszyfrowane, na kilka minut. Rozwiązanie jest przygotowane na przekazywanie danych z mObywatela kodem QR. Wspólny jest rejestr opisów formularzy, nie baza danych osobowych.

### 7. What works, what is simulated

- **Screen:** Co działa. Co symulujemy.
- **Motion:** the same two-column scene as in the first deck, filled from `status.json`: left with green ticks („rozpoznanie pól”, „formularz online”, „przekazanie kodem QR”, „kontrola AI”, „wydruk na wzorze”), right with amber dots („mObywatel”, „czytnik dokumentów”, „logowanie urzędowe”); underneath „dane syntetyczne”.
- **Say:** Uczciwie: to, co Państwo widzieli, działa na prawdziwym kodzie. Połączenie z mObywatelem, czytnik dokumentów i logowanie urzędowe są symulowane. Dane w pokazie są syntetyczne.
- **RU:** Честно: то, что вы видели, работает на настоящем коде. Подключение к mObywatel, сканер документов и вход через учётные записи учреждения имитируются. Данные в показе синтетические.
- **Cue:** называй только то, что стоит в левой колонке на экране.
- **Caption:** Co działa w prototypie, a co jest symulowane: lista na slajdzie; dane w pokazie są syntetyczne.

### 8. Close: the offer

- **Screen:** Każdy druk może być usługą.
- **Motion:** the wall of paper from slide 1 returns and its sheets turn into phone screens one by one, in a wave; a QR code to `formularze.flyreelstudio.eu` and the repository address fade in.
- **Say:** Proponujemy pilotaż: dziesięć najczęstszych druków jednego urzędu jako usługi online, w otwartym rejestrze, z którego skorzysta każdy urząd. Dziękuję i zapraszam do pytań.
- **RU:** Предлагаем пилот: десять самых частых бланков одного учреждения как онлайн-услуги, в открытом реестре, которым сможет пользоваться любое учреждение. Спасибо, жду вопросов.
- **Cue:** оставь слайд на экране на время вопросов; ответы в твоём окне, клавиши 1–9 и 0.
- **Caption:** Propozycja: pilotaż dziesięciu najczęstszych druków jednego urzędu jako usług online w otwartym rejestrze. Demo i kod: formularze.flyreelstudio.eu · github.com/AndriiShramko/shramko-asystent-urzednika

## Answer cards (presenter window only)

| Key | Question | Answer (PL) | RU |
|---|---|---|---|
| 1 | Jak AI rozpoznaje pola? | Analizujemy układ druku: linie, kratki i podpisy pól, a model proponuje nazwę, typ i powiązanie z danymi mieszkańca. Człowiek zatwierdza każde pole. Na końcu automat porównuje wydruk z oryginałem. | Разбираем разметку бланка, модель предлагает название, тип и связь с данными жителя; человек утверждает каждое поле; в конце автомат сравнивает печать с оригиналом. |
| 2 | Ile trwa cyfryzacja jednego druku? | Pokazaliśmy to na żywo na jednym druku. Podaję tylko czas zmierzony w pokazie; większe formularze wymagają więcej poprawek człowieka. | Показали вживую на одном бланке; называю только измеренное время; большие бланки требуют больше правок. |
| 3 | Co z dostępnością? | Formularz online powstaje z opisu pól według jednego szablonu, więc każdy ma etykiety, obsługę klawiatury i odpowiedni kontrast. Sprawdzamy to automatycznie przy publikacji. | Онлайн-форма строится из описания по одному шаблону: подписи, клавиатура, контраст; проверяется автоматически при публикации. |
| 4 | Jak to się ma do usług na gov.pl i w mObywatelu? | Nie zastępujemy platform centralnych. Dajemy opis formularza w otwartym formacie i gotowy formularz dla urzędu; eksport do formatów platform centralnych to kolejny krok, do ustalenia z Państwem. | Не заменяем центральные платформы: даём описание в открытом формате и готовую форму для учреждения; экспорт в форматы центральных платформ это следующий шаг. |
| 5 | A mObywatel? | Przekazywanie danych instytucji kodem QR już w aplikacji istnieje, ale wymaga porozumienia. W pokazie używamy własnego, szyfrowanego przekazania kodem QR i nie twierdzimy, że jesteśmy zintegrowani. | Передача данных по QR в приложении уже есть, но нужен договор; в показе свой шифрованный обмен, интеграцию не заявляем. |
| 6 | Gdzie są dane mieszkańca? | Na jego telefonie. Do urzędu trafiają tylko pola potrzebne w danej sprawie, zaszyfrowane od telefonu do urzędu, i znikają po wydruku albo po kilku minutach. | На его телефоне; в учреждение уходят только нужные поля, зашифрованные, и исчезают после печати или через несколько минут. |
| 7 | Co, gdy urząd zmieni wzór druku? | Opis formularza jest związany z konkretnym plikiem wzoru. Gdy plik się zmieni, system to wykrywa i wstrzymuje formularz do ponownego sprawdzenia. | Описание привязано к конкретному файлу образца; при изменении файла система это видит и останавливает форму до перепроверки. |
| 8 | Jaki model i dlaczego? | Puste druki są publiczne, więc do ich analizy można użyć dowolnego modelu, także otwartego polskiego. Dane osobowe sprawdzają najpierw zwykłe reguły, a model działa lokalnie albo na danych po pseudonimizacji. | Пустые бланки публичны: для их разбора годится любая модель, в том числе открытая польская; персональные данные сначала проверяют правила, модель локальная или на обезличенных данных. |
| 9 | Co w demo jest prawdziwe? | Powiem to wprost. Działają: rozpoznanie pól, formularz online, przekazanie kodem QR, kontrola i wydruk na wzorze. Symulowane są: mObywatel, czytnik dokumentów i logowanie urzędowe. Dane są syntetyczne. | Работает распознавание полей, онлайн-форма, обмен по QR, проверка и печать; имитируются mObywatel, сканер и вход; данные синтетические. (Главный агент правит под то, что построено.) |
| 0 | Co powstało na hackathonie? | Badania, katalog formularzy i specyfikację przygotowałem wcześniej i jawnie to oznaczyłem. Kod aplikacji powstał tutaj, w ciągu 24 godzin; widać to w historii repozytorium. | Исследование, каталог бланков и спецификация сделаны заранее и помечены; код написан здесь за 24 часа. |

Phrases for difficult moments: the same four as in the first deck.

## Technical specification

- Folder `site-formularze/deck/`: `index.html`, `slides.js` (texts of this storyboard), `scenes.js` (seven new drawings and the reused status drawing), `metrics.json` + `metrics.js`, `status.json` + `status.js`, optional `media/demo-1.mp4` and `media/demo-2.mp4`. The engine files `deck.js` and `deck.css` are copied from `site/deck/` unchanged if possible (a copy, not a link: each site folder is served separately).
- `slides.js`: slide 6 carries both wordings and the flag `built` (default false).
- `metrics.json` keys shown on slide 3 when not null: `digitise_seconds`, `fields_detected_pct`, `forms_digitised`; on slide 4: `fill_seconds`.
- `tools/deck_pdf.mjs` gets an optional argument for the deck folder and renders `site-formularze/deck/Od-druku-do-uslugi.pdf`.
- Landing page `site-formularze/index.html` in Polish: the idea in three lines, buttons to the deck, the demo (`app/`, when it exists) and the repository; the same visual style as the first site.
- Smoke test, screenshots (`docs/assets/deck-formularze/`) and a contact sheet as for the first deck.
