# HackTribe texts for the forms task (draft to paste by Saturday 18:00)

Closes item 1 of "Not done before the event" in [`../03-plan/STATUS.md`](../03-plan/STATUS.md) for the primary track. Written before the full task card was published: **after the 11:00 gate the lead re-reads every text against the card's own words and criteria** and replaces the square brackets with what the software really does at that hour. Never paste a bracket. Fields and deadlines: [`research/01`](../../research/01-hacknation-2026-task-rules-jury.md) (draft by Sat 20:00: project name, team name, task, table number, short description, approach, progress, repository; final by Sun 11:00).

Each Polish text is followed by its meaning in Russian for the owner.

## Draft fields

| Field | Text |
|---|---|
| Project name | **Shramko Formularze: od druku do usługi** (alternative, if the card stresses the citizen's path: „Shramko Formularze: od potrzeby do podpisu") |
| Team name | Shramko |
| Task | Cyfryzacja formularzy (Centralny Ośrodek Informatyki) |
| Table number | [the owner fills in] |
| Repository | https://github.com/AndriiShramko/shramko-asystent-urzednika |

### Short description (the first two sentences are all a juror may read)

> Narzędzie AI, które zamienia urzędowy druk (PDF, DOCX) w usługę: rozpoznaje pola, proponuje ich znaczenie, a po zatwierdzeniu przez człowieka tworzy formularz online, wydruk na oryginalnym wzorze i reguły kontroli. Pokazujemy też, jak taka usługa działa w urzędzie: mieszkaniec opisuje sprawę i dostaje komplet wniosków, dane podaje raz z telefonu, a urzędnik sprawdza tylko pola wskazane przez system.

*(Инструмент ИИ, который превращает официальный бланк (PDF, DOCX) в услугу: распознаёт поля, предлагает их смысл и после утверждения человеком создаёт онлайн-форму, печать на оригинальном образце и правила проверки. Показываем и то, как такая услуга работает в учреждении: житель описывает дело и получает комплект заявлений, данные даёт один раз с телефона, чиновник проверяет только поля, на которые указала система.)*

### Full description (about 90 words)

> Shramko Formularze skraca drogę od papierowego druku do usługi. Pracownik urzędu wczytuje pusty druk, AI rozpoznaje pola i proponuje ich powiązanie ze wspólnym profilem danych, człowiek poprawia i zatwierdza, a automat porównuje wydruk z oryginalnym wzorem. Z jednego opisu powstają formularz online, wydruk i reguły kontroli. W pokazie mieszkaniec opisuje sprawę jednym zdaniem i dostaje komplet wniosków, przekazuje dane raz przez kod QR, a urzędnik sprawdza tylko wyjątki. Kod jest otwarty (MIT) i działa lokalnie w urzędzie, także z otwartym polskim modelem. Pokaz używa danych syntetycznych. [Wyniki pomiarów z pokazu.]

*(Shramko Formularze сокращает путь от бумажного бланка до услуги. Сотрудник загружает пустой бланк, ИИ распознаёт поля и предлагает их связь с общим профилем данных, человек правит и утверждает, автомат сравнивает печать с оригинальным образцом. Из одного описания получаются онлайн-форма, печать и правила проверки. В показе житель описывает дело одной фразой и получает комплект заявлений, передаёт данные один раз по QR-коду, чиновник проверяет только исключения. Код открыт и работает локально в учреждении, в том числе с открытой польской моделью. В показе данные выдуманные.)*

### Approach

> 1. Układ druku czytamy z geometrii strony (linie, kratki, pola), a model dostaje obraz strony i listę kandydatów na pola: proponuje nazwy i znaczenie, nigdy współrzędne.
> 2. AI proponuje, człowiek zatwierdza. Każda propozycja i każde zatwierdzenie zostają w dzienniku.
> 3. Opis formularza jest związany z sumą kontrolną pliku wzoru. Test porównuje wydruk z oryginałem: poza polami nie może zmienić się ani jeden piksel.
> 4. Dane osobowe zostają u mieszkańca: profil na telefonie, przekazanie szyfrowane, tylko pola potrzebne w sprawie, na kilka minut. Model pracuje lokalnie albo na danych po pseudonimizacji.
> 5. Otwarty kod, uruchomienie w infrastrukturze urzędu jednym poleceniem, interfejs projektowany zgodnie z WCAG 2.1 AA.
> 6. Badania, katalog 275 kart usług jednego urzędu i specyfikacja powstały przed wydarzeniem i są jawnie oznaczone w repozytorium. Kod aplikacji powstaje podczas hackathonu.
> [7. Dwa wejścia do tej samej usługi: strona dla każdego i oficjalny interfejs (MCP, API) dla asystentów AI mieszkańców. Asystent wypełnia, człowiek zatwierdza. — only if WP-B10 is built; otherwise delete.]

*(1. Разметку бланка читаем из геометрии страницы, модель получает изображение и список кандидатов в поля: предлагает названия и смысл, но не координаты. 2. ИИ предлагает, человек утверждает; всё пишется в журнал. 3. Описание бланка привязано к контрольной сумме файла образца; тест сравнивает печать с оригиналом, вне полей не меняется ни один пиксель. 4. Персональные данные остаются у жителя: профиль в телефоне, шифрованная передача, только нужные поля, на несколько минут; модель локальная или на обезличенных данных. 5. Открытый код, запуск в инфраструктуре учреждения одной командой, доступность по WCAG 2.1 AA. 6. Исследование, каталог 275 карточек услуг и спецификация сделаны до события и помечены; код пишется на хакатоне.)*

### Progress (fill at the hour of submission, from STATUS)

> [Godzina.] Działa: [lista z `site-formularze/deck/status.json`, pole `works`]. W toku: [pakiety w budowie]. Symulowane: mObywatel, czytnik dokumentów, login.gov.pl, rezerwacja wizyt. Następne kroki: [dwa najbliższe kamienie milowe z planu].

*(Час. Работает: … В работе: … Имитируется: … Следующие шаги: …)*

## Demo video for the first stage (up to two minutes, captions only)

Recorded from the running product with synthetic data. Use a row only if the product does it.

| Time | Show | Caption (Polish, at most six words) |
|---|---|---|
| 0:00–0:06 | Title card | „Od druku do usługi." |
| 0:06–0:30 | A blank form from the office's site is uploaded; boxes and labels appear; one correction | „AI proponuje. Człowiek zatwierdza." |
| 0:30–0:42 | Test print compared with the original; "Opublikuj"; the phone form | „Wydruk zgodny z oryginałem." |
| 0:42–0:58 | Phone: "Przygotuj wizytę", one sentence, the set with "co zabrać" | „Jedna sprawa. Komplet wniosków." |
| 0:58–1:12 | QR code; the phone lists the fields to share; confirm | „Dane raz, z telefonu." |
| 1:12–1:32 | Clerk: document read; "zgodne" collapsed, two fields to check; identity confirmed | „Urzędnik sprawdza tylko wyjątki." |
| 1:32–1:46 | "Drukuj komplet"; forms on the original templates; "dane usunięte" | „Komplet gotowy do podpisu." |
| 1:46–2:00 | Closing frame: what works, what is simulated, links and QR | „Kod otwarty. Dane syntetyczne." |
