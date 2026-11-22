# Фильм для сдачи: сценарий записи экрана с голосом (для Андрея)

Написано 22.11.2026 около 06:20. Фильм до **3 минут** (требование карточки), цель 2:30–2:50. Голос по-польски: короткие фразы, читать спокойно, около 130 слов в минуту. Под каждой сценой перевод курсивом — чтобы вы знали, что говорите. Ниже есть короткая версия на 60 секунд (HackTribe советует демо до 2 минут) и идеи инфографики для полного видео позже.

Сцены с пометкой **«проверить после финальной сборки»** зависят от того, что на 06:20 ещё сливается: вид урзендника (CLERK-P), блок ключа модели (KEY), подсказки адреса TERYT (ADDR). Ключа в образе НЕТ (решение 06:20): модель по умолчанию выключена; в вашем контейнере `sau-v1` ключ подставлен при запуске, поэтому блок «Model AI» показывает точки. Перед записью откройте страницу и посмотрите: если кнопки нет — берите вариант «ЕСЛИ НЕТ» этой сцены.

---

## Перед записью (10 минут)

1. Контейнер с финальным образом на `http://127.0.0.1:8080/ui/` (главный агент ставит его в `sau-v1`). Проверить: страница открывается, в `http://127.0.0.1:8080/status` есть ответ.
2. Экран 1920×1080, браузер на весь экран, масштаб 110 %, все лишние вкладки закрыты, уведомления Windows выключены.
3. Файлы (пустые бланки задания, без чьих-либо данных):
   - набор 07, PDF: `data/coi/judged-07-psy-rasy-agresywne/Wniosek o wydanie zezwolenia na hodowanie lub utrzymywanie psów ras uznawanychza agresywne.PDF`
   - набор 09, PDF и JPG: `data/coi/judged-09-stypendium-sportowe/Wniosek o przyznanie stypendium.pdf` и `.jpg`
   - для терминала: папка `forms` с копией PDF набора 03 под именем `form.pdf`, пустая папка `out`.
4. Заранее, до записи, откройте две вкладки и загрузите в них: вкладка 2 — набор 09 PDF (для блока «Słowniki»), вкладка 3 — набор 09 JPG (скан идёт до 1,5 минут, ждать в кадре нельзя).
5. **Никогда не нажимайте «глазик» ключа модели во время записи.** В вашем контейнере глазик показывает ключ целиком (`VISION_KEY_REVEAL=on`), а фильм публичный: ключ должен быть виден только точками. Адрес сервера модели тоже не показывать. Если сомневаетесь — запишите сцену 8 без раскрытия блока «Model AI».
6. Не снимать: набор 03 как JPEG и PNG (поля с бумаги не находятся), набор 07 как JPG (мусорное поле «Eeee…»), гербы и логотипы госорганов.
7. Жёлтая плашка «Dane demonstracyjne…» должна быть видна в сценах с заполнением: люди и номера выдуманы.

---

## Полная версия, около 2:45

| # | Время | Что на экране (точные действия) |
|---|---|---|
| 1 | 0:00–0:12 | Открыт сам PDF набора 07 (пустой бланк про собак) в просмотрщике PDF. Медленно прокрутить страницу. Поверх (при монтаже или крупным текстом в окне) надпись: «661 formularzy jednego miasta» |
| 2 | 0:12–0:27 | Вкладка 1: `http://127.0.0.1:8080/ui/` → «Wybierz plik» → PDF набора 07. Видно ожидание, затем заголовок «Formularz przetworzony: N pól w M sekcjach (z druku: …, standardowych: …)» |
| 3 | 0:27–0:45 | **Проверить после финальной сборки.** Страница открывается в «Widok urzędnika»: слева картинка оригинала, справа e-форма, сверху «Do sprawdzenia (N)». Нажать первую карточку замечания: место мигает на оригинале, поле подсвечено в форме. На карточке с готовым выбором нажать кнопку выбора: замечание уходит из списка. **ЕСЛИ НЕТ:** блок «Gdzie na papierze»: нажать в списке два поля, их рамки загораются на картинке страницы |
| 4 | 0:45–1:00 | **Проверить после финальной сборки.** Переключатель «Widok dla jury» → блок «Jak powstał ten wynik»: число полей с бумаги и из стандарта, замечания по видам. **ЕСЛИ НЕТ:** прокрутить к заголовку с двумя числами и к списку «Uwagi do sprawdzenia» |
| 5 | 1:00–1:13 | Блок «Formularz w formacie JSON»: видны ключи `title`, `tabs`, `flow`; медленно прокрутить; кнопка «Pobierz form.json» |
| 6 | 1:13–1:26 | Вкладка 2 (набор 09 PDF, загружен заранее): блок «Słowniki» → «Proponowany nowy słownik»: «Dyscypliny sportowe» и его позиции |
| 7 | 1:26–1:50 | Вкладка 1 (набор 07): e-форма («Następna strona»); в поле выбора отметить вариант — открывается следующая секция (если в наборе 07 выбор ничего не открывает, фразу про warunki в голосе пропустить). Затем «Zeskanuj kod QR (symulacja)» → «Helena Przykładowska» → «Wypełnij formularz jednym kliknięciem». В поле PESEL изменить последнюю цифру → «Sprawdź poprawność» → красное сообщение про PESEL. Затем «Podgląd wydruku na oryginalnym blankiecie». **Проверить после финальной сборки:** в поле адреса набрать «Byd» → подсказка «Bydgoszcz» из TERYT (если подсказки нет — пропустить) |
| 8 | 1:50–2:07 | Вкладка 3 (набор 09 JPG, загружен заранее): заголовок результата, список полей. Затем прокрутить вверх к строке «Model AI (opcjonalnie)» под загрузкой файла и раскрыть её одним кликом: состояние модели, ключ точками. «Глазик» НЕ нажимать |
| 9 | 2:07–2:27 | Окно PowerShell, крупный шрифт. Две команды из раздела «Команды для сцены 9» ниже (вторая — с `b.json`), потом `Get-FileHash` двух файлов: одинаковые хэши |
| 10 | 2:27–2:45 | Финальная карточка (слайд или окно с крупным текстом): «Shramko Asystent Urzędnika · 8 formatów · JSON Generatora Formularzy · raport pochodzenia pól · słowniki · warunki · walidacje · REST, CLI, wiele plików · jeden obraz Dockera, CPU · licencje MIT/BSD/Apache · github.com/AndriiShramko/shramko-asystent-urzednika» |

### Голос по сценам

**1 (0:00–0:12)**
> Do urzędu trafia nowy druk. Trzeba z niego zrobić e-usługę. Samo miasto Bydgoszcz publikuje sześćset sześćdziesiąt jeden takich formularzy. Dziś przepisuje się je ręcznie, pole po polu.

*В учреждение приходит новый бланк. Из него нужно сделать электронную услугу. Один только город Быдгощ публикует 661 такой бланк. Сегодня их переписывают вручную, поле за полем.*

**2 (0:12–0:27)**
> To jest Shramko Asystent Urzędnika. Wczytuję pusty druk. Może to być PDF, Word, arkusz albo skan. Po kilku sekundach mam e-formularz w strukturze Generatora Formularzy.

*Это Shramko Asystent Urzędnika. Загружаю пустой бланк. Это может быть PDF, Word, таблица или скан. Через несколько секунд у меня e-форма в структуре Генератора форм.*

**3 (0:27–0:45)**
> Po lewej oryginał, po prawej gotowy e-formularz. Wątpliwości są kartami na dokumencie. Klikam kartę i widzę to miejsce na papierze. Gotową poprawkę wybieram jednym kliknięciem.

*Слева оригинал, справа готовая e-форма. Сомнения — это карточки на документе. Нажимаю карточку и вижу это место на бумаге. Готовое исправление выбираю одним кликом.*

(ЕСЛИ НЕТ вида урзендника: «Przy każdym polu widzę jego miejsce na papierze. Wątpliwości trafiają na listę do sprawdzenia.» — *У каждого поля вижу его место на бумаге. Сомнения попадают в список на проверку.*)

**4 (0:45–1:00)**
> To kompilator z księgowym, nie skaner. Każde pole ma źródło: druk albo standard COI. Raport rozlicza miejsca, które znalazł na papierze. Opłat i podstawy prawnej nie zgadujemy.

*Это компилятор с бухгалтером, а не сканер. У каждого поля есть источник: бланк или стандарт COI. Отчёт учитывает места, которые нашёл на бумаге. Оплату и правовое основание мы не угадываем.*

**5 (1:00–1:13)**
> Wynik to czysty JSON partnera: title, tabs i flow. Strony tematyczne i standardowe sekcje dodaje biblioteka COI. Przed wysłaniem JSON przechodzi schemat i reguły partnera.

*Результат — чистый JSON партнёра: title, tabs и flow. Тематические страницы и стандартные секции добавляет библиотека COI. Перед отправкой JSON проходит схему и правила партнёра.*

**6 (1:13–1:26)**
> Słowniki są przypisane do pól. A z druku stypendium usługa proponuje nowy słownik: dyscypliny sportowe. To propozycja do zatwierdzenia przez urząd.

*Словари привязаны к полям. А из бланка стипендии сервис предлагает новый словарь: спортивные дисциплины. Это предложение, его утверждает учреждение.*

**7 (1:26–1:50)**
> Tak zobaczy go mieszkaniec. Wybór odsłania kolejną sekcję: to warunki z JSON-u. Próbnie wypełniam formularz fikcyjną osobą. Błędny PESEL od razu zatrzymuje walidacja. A dla urzędów, które przyjmują papier: wydruk na oryginalnym blankiecie.

*Так её увидит житель. Выбор открывает следующую секцию: это условия из JSON. Пробно заполняю форму вымышленным человеком. Неверный PESEL сразу останавливает проверка. А для учреждений, которые принимают бумагу: печать на оригинальном бланке.*

(Если подсказка TERYT есть, добавить: «Adres podpowiada rejestr TERYT, bez internetu.» — *Адрес подсказывает реестр TERYT, без интернета.*)

**8 (1:50–2:07)**
> Skany i zdjęcia czyta lokalny OCR, w kontenerze. Dla słabych stron skanu można włączyć pomocniczy model o otwartych wagach, na własnym serwerze urzędu. Domyślnie jest wyłączony, a klucz podaje się dopiero przy uruchomieniu.

*Сканы и фото читает локальный OCR, внутри контейнера. Для слабых страниц скана можно включить вспомогательную модель с открытыми весами, на собственном сервере учреждения. По умолчанию она выключена, а ключ задаётся только при запуске.*

(Про пользу модели не говорить ничего: замер показал много лишних полей. Не говорить, что ключ «внутри»: карточка требует секреты только при запуске.)

**9 (2:07–2:27)**
> Całość to jeden obraz Dockera, na procesorze, bez GPU. Polecenia dla jury działają bez sieci. Ten sam plik daje ten sam JSON, co do bajtu. Jest REST, wiersz poleceń i wiele plików naraz.

*Всё это один образ Docker, на процессоре, без GPU. Команды для жюри работают без сети. Один и тот же файл даёт тот же JSON, байт в байт. Есть REST, командная строка и много файлов сразу.*

**10 (2:27–2:45)**
> Plik sprawdzamy po typie i nazwie, a trzymamy tylko tymczasowo. Biblioteki mają otwarte licencje bez copyleftu. Strona ma kontrast zgodny z WCAG. Urzędnik nie przepisuje druku. Sprawdza i zatwierdza.

*Файл проверяем по типу и имени, а храним только временно. Библиотеки с открытыми лицензиями без копилефта. У страницы контраст по WCAG. Урзендник не переписывает бланк. Он проверяет и утверждает.*

Слов в голосе около 300: при 130 словах в минуту это около 2:20 речи, с паузами на действия — около 2:45.

### Команды для сцены 9 (PowerShell, из папки, где лежат `forms` и `out`)

```powershell
docker run --rm --platform linux/amd64 --network none --read-only --cap-drop ALL -v "${PWD}/forms:/in:ro" -v "${PWD}/out:/out" ghcr.io/andriishramko/shramko-asystent-urzednika@<<FINAL_DIGEST>> convert /in/form.pdf --out /out/a.json
```

```powershell
docker run --rm --platform linux/amd64 --network none --read-only --cap-drop ALL -v "${PWD}/forms:/in:ro" -v "${PWD}/out:/out" ghcr.io/andriishramko/shramko-asystent-urzednika@<<FINAL_DIGEST>> convert /in/form.pdf --out /out/b.json
```

```powershell
Get-FileHash out\a.json, out\b.json
```

`<<FINAL_DIGEST>>` — строка `sha256:...` финального образа (из `docs/03-plan/RESUME.md`). Перед записью прогнать один раз: хэши должны совпасть (с `--network none` модель не вызывается). Проверить после финальной сборки.

### Откуда числа (не читать вслух)
- 661 формуляр одного города: `data/forms-census.json` (перепись 21.11.2026: 661 уникальный документ на 224 карточках услуг).
- «Po kilku sekundach»: README, раздел «Koszt i wymagania», медиана PDF 1,9 с на нагруженном ноутбуке; скан набора 09 JPG шёл около 100 с — поэтому скан загружается заранее.
- 20 позиций «Dyscypliny sportowe»: `api-analyses/81-score-recheck-0400.md` (на экране видно само).
- Одинаковые байты двух запусков без сети: проверка жюри `jury_accept.sh` (ALL PASS) в `docs/03-plan/RESUME.md`.
- Контраст WCAG 2.1 AA: тесты `apps/review-web/tests/contrast*.test.ts`.
- Чисел про пользу модели в фильме нет специально.

---

## Короткая версия, около 60 секунд

| # | Время | Экран | Голос (PL) |
|---|---|---|---|
| 1 | 0:00–0:08 | PDF набора 07 в просмотрщике | „Urząd ma nowy druk i musi zrobić z niego e-usługę. Dziś przepisuje się go ręcznie.” |
| 2 | 0:08–0:18 | `/ui/` → «Wybierz plik» → PDF набора 07 → заголовок результата | „Wczytuję pusty druk: PDF, Word, arkusz albo skan. Po kilku sekundach mam JSON dla Generatora Formularzy.” |
| 3 | 0:18–0:32 | Вид урзендника: карточка → место мигает → выбор одним кликом (**проверить после финальной сборки**; ЕСЛИ НЕТ — «Gdzie na papierze») | „Oryginał obok e-formularza. Każde pole ma źródło, a wątpliwości poprawiam jednym kliknięciem.” |
| 4 | 0:32–0:46 | Вкладка 2: «Słowniki» → «Dyscypliny sportowe»; вкладка 1: «Wypełnij formularz jednym kliknięciem» → неверный PESEL → «Sprawdź poprawność» | „Słowniki, propozycja nowego słownika, warunki i walidacja PESEL są w JSON-ie.” |
| 5 | 0:46–0:60 | PowerShell: команда с `--network none`, затем финальная карточка | „Jeden obraz Dockera, bez GPU i bez sieci. Urzędnik nie przepisuje druku. Sprawdza i zatwierdza.” |

*Перевод: 1) У учреждения новый бланк, из него надо сделать e-услугу; сегодня его переписывают вручную. 2) Загружаю пустой бланк: PDF, Word, таблица или скан; через несколько секунд у меня JSON для Генератора форм. 3) Оригинал рядом с e-формой; у каждого поля есть источник, а сомнения исправляю одним кликом. 4) Словари, предложение нового словаря, условия и проверка PESEL — в JSON. 5) Один образ Docker, без GPU и без сети; урзендник не переписывает бланк, он проверяет и утверждает.*

Около 75 слов — ровно на минуту с паузами.

---

## Идеи инфографики для полного видео (позже, если хватит времени)

1. **Воронка «бумага → e-услуга»:** 661 бланк одного города → 2479 гмин в Польше → каждый бланк сегодня переписывают вручную (источники: `data/forms-census.json`, `research/13`).
2. **«Компилятор с бухгалтером»:** слева бланк с местами для заполнения, справа JSON; между ними «бухгалтерская книга»: у каждого места стрелка к полю или пометка «pominięte, bo…».
3. **Один бланк → 69 компонентов:** как одностраничный бланк у партнёра становится четырёхстраничной e-услугой, где большую часть дают стандартные секции COI (`reference-json-forensics.txt`).
4. **Восемь форматов в одну воронку:** иконки PDF, DOC, DOCX, ODS, XLSX, JPG, JPEG, PNG → один REST-вызов → `title / tabs / flow`.
5. **Карта пяти пунктов оценки:** минимум, I словари, II новый словарь, III условия, IV страница, V проверки — у каждого скриншот места на странице.
6. **Время на формат:** столбики медианы секунд из README (DOC 0,9; DOCX 0,9; ODS 1,2; XLSX 1,4; PDF 1,9; JPG 12,2; JPEG 15,6; PNG 16,7) с подписью «obciążony laptop, 2 rdzenie».
7. **Безопасность одним кадром:** контейнер-сейф: `--network none`, только чтение, пользователь без прав, проверка типа и имени файла, лицензии без копилефта.
8. **Честность:** «чего мы не угадываем» — оплата, правовое основание, полномочия: вместо догадки цитата с бланка или замечание урзендинку.
