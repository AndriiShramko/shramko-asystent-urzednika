# Сдача на HackTribe: что вставить и что исправить (для Андрея)

Написано 22.11.2026 около 06:15 для финальной сдачи задания COI «Cyfryzacja formularzy». Дедлайн HackTribe **11:00**; последний Save **не позже 10:45**. Польский текст в блоках вставлять как есть; русская строка над блоком только для вас.

Метки, которые главный агент заменит перед сдачей (если он не успеет, замените сами):
- `<<FINAL_DIGEST>>` — дайджест финального образа (строка `sha256:...` из `docs/03-plan/RESUME.md`, верхний блок, «verified»). Пока финального нет, годится последний проверенный: на 05:44 это `sha256:82cab5c3e798a167b7bead7d2c3d908b0959629ca8f722a684658cfeafbd0445`.
- `<<FILM_LINK>>` — ссылка на фильм YouTube (публичный или «по ссылке»).
- `<<TIME>>` — время состояния, по часам (например `10:10`).

Строки с пометкой **«проверить после финальной сборки»** описывают то, что на 06:15 ещё сливается (вид урзендника, блок ключа модели, подсказки адреса TERYT). Если к 08:30 это не вошло в образ, удалите эти строки.

**Решение владельца 06:20 (окончательное): ключа в образе НЕТ.** Карточка задания требует секреты только при запуске контейнера (пункт C-TECH-DOCKER), за нарушение были бы минус-баллы. Модель по умолчанию выключена; в вашем контейнере и на видео ключ подставлен при запуске: на странице блок «Model AI (opcjonalnie)», ключ точками, глазик показывает его целиком (переключатель `VISION_KEY_REVEAL=on` только в вашем контейнере).

---

## 0. Порядок на утро (коротко)

| Когда | Что делаете вы |
|---|---|
| до 10:00 | Прочитать этот файл; записать фильм по `FILM-script-owner.md`; загрузить на YouTube (публичный или по ссылке) |
| 10:15 | Первый Save в HackTribe с тем, что готово (это безопасная точка, править можно и потом) |
| 10:15–10:40 | Вставить финальные тексты, PDF презентации, ссылку на фильм, дайджест |
| **не позже 10:45** | Финальный Save |
| 10:50 | Открыть свой проект (`/my/`) и прочитать глазами: название, задание COI, стол, ссылки, PDF на месте |

Ловушки формы (были в субботу): при открытии формы всплывает «Restore unsaved draft?» — жать **Discard** (иначе подтянется старый текст); «Challenges» должен остаться **COI**; галочки «Needed skills» не снимать (в субботу без них сервер не сохранял); нажатая кнопка не доказательство — после Save открыть проект и прочитать.

Запасной путь, если у жюри не скачивается образ: архив образа (около 100 МБ, `docs/03-plan/SUBMISSION.md` §5) в релизе GitHub и на флешке; на финале — наш ноутбук запускает образ и конвертирует их файлы; последний вариант — сборка из исходников командой из README.

---

## 1. Поля формы HackTribe по порядку

### 1. Project Name (обязательное, до 255 знаков)
*Название проекта. Если в субботу сохранили другое, можно заменить на это.*
```text
Shramko Asystent Urzędnika: z papierowego druku do e-formularza (JSON dla Generatora Formularzy COI)
```

### 2. Problem (обязательное)
*Почему это нужно. HackTribe прямо просит статистику; цифры ниже из файлов репозитория (`data/forms-census.json`, перепись 21.11; `research/13`, MSWiA на 01.01.2026; `docs/05-hackathon/mentor-questions/reference-json-forensics.txt`).*
```text
Urzędy publikują swoje wnioski jako PDF, DOC, DOCX, arkusze i skany. Tylko jedno miasto, Bydgoszcz, ma na 224 kartach usług 661 różnych dokumentów-formularzy (2107 stron): 322 PDF, 142 DOCX, 117 DOC, 77 RTF i inne. Gmin w Polsce jest 2479. Każdy taki druk trzeba dziś ręcznie przenieść do Generatora Formularzy: pole po polu, z walidacją, słownikami i warunkami. Wzorcowy eksport partnera pokazuje skalę: jednostronicowy wniosek papierowy staje się e-usługą z 69 komponentami. Przy ręcznym przepisywaniu nikt nie rozlicza, co zginęło po drodze: opłata, oświadczenie, załącznik, warunek „wypełnij, jeśli...”. A rozwiązanie dla administracji nie może wysyłać dokumentów poza infrastrukturę urzędu.
```

### 3. Solution (обязательное)
*Что делает решение и какая польза урзендинку. Абзац про модель — по решению владельца 06:20 (ключа в образе нет, модель по умолчанию выключена).*
```text
Shramko Asystent Urzędnika to usługa REST w jednym obrazie Dockera. Na wejściu pusty formularz w jednym z ośmiu formatów karty zadania (PDF, DOC, DOCX, ODS, XLSX, JPG, JPEG, PNG), na wyjściu JSON dokładnie w strukturze Generatora Formularzy (title, tabs, flow), sprawdzony schematem i regułami partnera przed wysłaniem.

Kompilator z księgowym, nie skaner: formularz budują reguły i biblioteka standardowych sekcji COI, a obok JSON-u usługa oddaje raport. Każde pole ma źródło (druk albo standard COI), znalezione na papierze miejsca do wypełnienia są rozliczone w raporcie, a opłat, podstawy prawnej i uprawnień nie zgadujemy: jest cytat z druku albo uwaga dla urzędnika. Zły plik dostaje odmowę z powodem po polsku, nie zmyślony formularz.

Co dostaje urzędnik:
- stronę /ui/: wczytuje druk i widzi, ile pól jest z papieru, a ile standardowych; przy każdym polu jego miejsce na oryginale;
- słowniki przypisane do pól (kraje, TERYT) i propozycję nowego słownika, np. „Dyscypliny sportowe” z druku stypendium;
- warunki pokazania sekcji w JSONata, walidatory PESEL, NIP, REGON, kodu pocztowego, e-mail, dowodu osobistego;
- podgląd e-formularza, próbne wypełnienie fikcyjną osobą, sprawdzenie i wydruk na oryginalnym blankiecie;
- wiele plików naraz przez REST (/v1/batches) albo jedną komendą dla całego folderu.
[проверить после финальной сборки] Widok urzędnika: oryginał obok gotowego e-formularza, uwagi jako karty na dokumencie i poprawka jednym kliknięciem; osobny widok dla jury.
[проверить после финальной сборки] Podpowiedzi adresu bez sieci z rejestru TERYT (miejscowość, ulica, gmina).

Wdrożenie: CPU, bez GPU, obraz python:3.14-alpine przypięty skrótem, użytkownik bez uprawnień, plik tylko w pamięci i katalogu tymczasowym, konfigurowalny limit rozmiaru, JWT, licencje bez copyleftu. Polecenia dla jury działają z --network none.

Model pomocniczy, domyślnie wyłączony: dla słabych stron skanów administrator może wskazać własny serwer z modelem o otwartych wagach (np. Qwen3). Model nie pisze pól: wskazuje tylko numery linii, które nasz OCR już odczytał, a dalej działają te same reguły. Adres i klucz podaje się przy uruchomieniu kontenera albo na stronie w bloku „Model AI (opcjonalnie)” (klucz widać jako kropki). W obrazie nie ma żadnego klucza; bez modelu wynik budują same reguły, co do bajtu powtarzalnie.
```
*Перед вставкой: убрать квадратные скобки с русскими пометками. Если вид урзендника или TERYT не вошли в образ — удалить эти две строки целиком.*

### 4. Challenges
*Задание партнёра. Менять нельзя с субботы 20:00; просто проверить, что стоит COI.*
```text
[Centralny Ośrodek Informatyki]: Cyfryzacja Formularzy
```

### 5. Cover image (необязательное)
*Обложка, .png/.jpg/.webp, 4:3, до 5 МБ.* Файл, подготовленный ночью: `C:\ShramkoU\HackNation2026\cover\cover-1600x1200.png` (проверить, что открывается и меньше 5 МБ). Если уже загружена в субботу — не трогать.

### 6. Idea stage
*Новый проект или работа над существующим.* `Work on progress project` (исследования и спецификация сделаны до события и так помечены в репозитории; код продукта написан на событии).

### 7. What's done so far and goal of your project
*Что сделано. Числа только измеренные, с указанием, на чём мерили. Источники для вас: перепись — `data/forms-census.json`; точность — `quality-gate/VJ1-vision-judge.md` в хранилище; время — README, раздел «Koszt i wymagania»; тесты — журнал лида 10, 02:14; цепочка 158 файлов — `docs/03-plan/RESUME.md`.*
```text
Stan na 22.11.2026, godz. <<TIME>>. Obraz: ghcr.io/andriishramko/shramko-asystent-urzednika@<<FINAL_DIGEST>> (linux/amd64, publiczny, bez logowania).

Przed wydarzeniem (oznaczone w repozytorium jako materiał sprzed hackathonu): analiza obu eksportów wzorcowych partnera pole po polu, spis 661 dokumentów-formularzy Bydgoszczy, badania i specyfikacja. Na wydarzeniu: cały kod produktu.

Działa i jest zmierzone:
- REST (/v1/forms/convert, /v1/batches, /v1/forms/report, /status), wiersz poleceń i strona /ui/ w jednym obrazie; dokładnie osiem formatów z karty zadania, z kontrolą zawartości pliku względem rozszerzenia i nazwy pliku.
- Każdy wynik przechodzi schemat JSON i reguły partnera przed wysłaniem; wynik zawiera tylko title, tabs, flow, a raport z pochodzeniem pól jest osobnym plikiem.
- Każde scalenie kodu przechodzi ponad 1000 testów i porównanie na 158 plikach (zadania i archiwum miasta): 0 awarii.
- Niezależna kontrola po obrazie strony (sędzia wypisał miejsca do wypełnienia, nie widząc naszego wyniku; pomiar 21.11 wieczorem, przed nocnymi poprawkami): na 14 nieznanych formularzach z archiwum Bydgoszczy znaleźliśmy poprawnie 70 % miejsc z PDF i 69 % ze zdjęć; na zestawach zadania PDF 81 %, DOCX 68 %, ODS 64 %, XLSX 60 %, zdjęcia 55 %, DOC 50 %. W nocy stary DOC nauczył się czytać ramki tekstu: zestaw 08 DOC z 8 do 34 pól z papieru.
- Czas jednej konwersji przez REST (108 plików, obciążony laptop, 2 rdzenie): mediana poniżej 2 s dla PDF, DOC, DOCX, ODS i XLSX; skany 12–17 s, bo czyta je lokalny OCR. Szczyt pamięci 577 MiB.
- Pliki JSON siedmiu ocenianych formularzy są w katalogu results/ repozytorium.

Słabe miejsca, mówimy wprost: stare DOC i zdjęcia (około połowy miejsc), listy załączników bez linii, warunki „wypełnij, jeśli...” zachowane w około połowie przypadków.

Cel: urzędnik dostaje gotowy, sprawdzony szkic e-usługi obok oryginału i tylko zatwierdza, zamiast przepisywać druk pole po polu.
```

### 8. Team status
`Full team`

### 9. Current team size (обязательное)
`1`

### 10. Needed skills
*Не снимать то, что сохранено в субботу (без галочек сервер не сохранял).*

### 11. Skills comment
Пусто.

### 12. Your video presentation (YouTube, публичный или по ссылке)
*Фильм до 3 минут (карточка), HackTribe советует до 2. Сценарий: `docs/05-hackathon/FILM-script-owner.md`.*
```text
<<FILM_LINK>>
```

### 13. Website
*Сайт `formularze.flyreelstudio.eu` сделан до события и описывает старый план. Если он не показывает текущее состояние — оставить поле пустым.* Рекомендую: **пусто**.

### 14. [Obowiązkowe] Link do repozytorium z kodem
```text
https://github.com/AndriiShramko/shramko-asystent-urzednika
```

### 15. [Opcjonalne] Instrukcje jak otworzyć projekt
*Команды для жюри. Совпадают с README; перед вставкой сверить с README на GitHub после финальной сборки.*
```text
Potrzebny tylko Docker. Obraz: ghcr.io/andriishramko/shramko-asystent-urzednika@<<FINAL_DIGEST>>

1) Usługa i strona dla urzędnika (Linux, macOS, Windows):
docker run --rm --platform linux/amd64 -p 127.0.0.1:8080:8080 ghcr.io/andriishramko/shramko-asystent-urzednika@<<FINAL_DIGEST>>
Potem w przeglądarce: http://127.0.0.1:8080/ui/ (wczytaj pusty formularz). Stan usługi: http://127.0.0.1:8080/status

2) REST z drugiego okna:
curl -F "file=@formularz.pdf" http://127.0.0.1:8080/v1/forms/convert -o form.json
(w PowerShell: curl.exe)

3) Bez sieci, wynik na standardowe wyjście (dowód, że nic nie wychodzi z kontenera); formularz w folderze forms/:
docker run --rm --platform linux/amd64 --network none --read-only --cap-drop ALL -v "$PWD/forms:/in:ro" ghcr.io/andriishramko/shramko-asystent-urzednika@<<FINAL_DIGEST>> convert /in/form.pdf > form.json
(Git Bash: dodaj MSYS_NO_PATHCONV=1 na początku; PowerShell: polecenie w README, sekcja „For the jury”.)

Pliki konwertujcie po kolei: usługa pracuje na dwóch plikach naraz i na więcej odpowiada 429. Limit: 20 MiB i 60 stron na plik (zmienne środowiskowe w README).
Wyniki dla siedmiu ocenianych formularzy: katalog results/ w repozytorium.
Dane osób na stronie w próbnym wypełnieniu są fikcyjne; „skan kodu QR” jest symulacją.
```
*Ключа в образе нет, поэтому про модель здесь ничего добавлять не нужно: команды для жюри работают на правилах.*

### 16. [Obowiązkowe] Nazwa zespołu
```text
Shramko
```

### 17. [Obowiązkowe] Numer stolika
*По журналу сдачи стол **1C**; проверьте на месте.*
```text
1C
```

### 18. [Opcjonalne] Prezentacja (PDF, до 10 МБ, до 10 слайдов)
*Только файл PDF. Старый `deck-v1.pdf` НЕ отправлять: в нём устаревшие числа.* План 10 слайдов (из отчёта SUBMIT): 1 проблема и статистика; 2 путь урзендника одной картинкой; 3 минимум (REST, 8 форматов, структура, тематические страницы); 4 словари I и новый словарь II; 5 условия III; 6 страница IV и e-форма; 7 проверки V и пакетная обработка; 8 что мы предусмотрели сверх карточки (источник каждого поля, отказ вместо выдумки, не угадываем оплату); 9 внедрение и стоимость (CPU, секунды, лицензии, безопасность; модель одной строкой); 10 честные пределы с числами и ссылки.

### 19. [Opcjonalne] Dodatkowe pole na materiały
```text
Film: <<FILM_LINK>> | Kod: https://github.com/AndriiShramko/shramko-asystent-urzednika | Wyniki JSON wszystkich 7 formularzy (także zestaw 08) i archiwum obrazu: https://github.com/AndriiShramko/shramko-asystent-urzednika/releases/tag/v1.0-hacknation | Obraz: ghcr.io/andriishramko/shramko-asystent-urzednika@<<FINAL_DIGEST>>
```

### Файлы JSON семи оцениваемых форм (требование карточки)
Все 7 файлов (наборы 02, 03, 04, 06, 07, 08, 09) лежат в публичном релизе GitHub: https://github.com/AndriiShramko/shramko-asystent-urzednika/releases/tag/v1.0-hacknation — вместе с архивом образа (запасной путь). В git (`results/`) лежат 6 из 7: набор 08 цитирует банковский счёт учреждения с бумаги, проверка публикации такое в git не пускает. Если HackTribe позволяет приложить файлы — приложите и сами JSON из релиза; ссылка на релиз стоит в поле 19.

---

## 2. Где жюри увидит каждый пункт оценки карточки

| Пункт карточки | Где увидеть | Статус |
|---|---|---|
| Минимум: REST, 8 форматов, JSON в структуре, тематические страницы | `POST /v1/forms/convert`; `results/`; `/status` (список форматов) | в образе |
| I. Словари и начальные данные на полях | страница `/ui/`, блок «Słowniki» («Słowniki przypisane do pól z druku»); в JSON `dictionaryName` у полей Kraj, Województwo, Gmina | в коде с `d1c66c8`; блок страницы — проверить после финальной сборки |
| II. Предложение нового словаря | блок «Słowniki» → «Proponowany nowy słownik»; пример: набор 09 (стипендия), «Dyscypliny sportowe», 20 позиций | то же |
| III. Зависимости и условия | в JSON `states` с запросами JSONata (SHOW); на странице — предпросмотр e-формы, выбор открывает секцию | в образе |
| IV. Страница загрузки и просмотра, визуализация e-формы | `http://127.0.0.1:8080/ui/`: результат, «Gdzie na papierze», e-форма, «Podgląd wydruku na oryginalnym blankiecie» | в образе; вид урзендника — проверить после финальной сборки |
| V. Проверки полей и UX (пакеты, макеты) | валидаторы PESEL, NIP, REGON, кода, e-mail, удостоверения в JSON; «Sprawdź poprawność» на странице; `POST /v1/batches` и команда для папки в README | в образе; телефон и номер счёта не проверяются (честно) |

---

## 3. Что ИСПРАВИТЬ против черновика 21.11 (20:00)

Черновик лежит в `docs/05-hackathon/hacktribe-draft-formularze.md`; ночная версия полей — в хранилище `pitch/final-0430/04-hacktribe-fields.md`. Если в HackTribe сейчас сохранён текст оттуда, замените так:

| Было (в сохранённом тексте) | Почему неверно сейчас | Стало |
|---|---|---|
| «Budujemy usługę REST w Dockerze…» | услуга уже работает | «Shramko Asystent Urzędnika to usługa REST w jednym obrazie Dockera…» (поле 3) |
| «(PDF, DOC, DOCX, ODS, XLSX, JPG, PNG)» | пропущен JPEG; карточка называет восемь | «(PDF, DOC, DOCX, ODS, XLSX, JPG, JPEG, PNG)» |
| «bez modelu językowego i bez połączeń na zewnątrz» | верно только по умолчанию: есть необязательный шаг модели | «domyślnie bez modelu językowego i bez połączeń na zewnątrz; opcjonalny model o otwartych wagach włącza administrator» |
| «w produkcie nie ma żadnego modelu ani klucza» | модель есть как опция | «w obrazie nie ma żadnego klucza; model jest opcjonalny i domyślnie wyłączony» |
| «kontener działa z --network none, bez klucza API i bez GPU» (поле 15 ночной версии) | верно, ключа в образе нет | оставить |
| «Jeden obraz Dockera, działa bez sieci, bez GPU i bez klucza API» (питч) | верно | оставить |
| «A new dictionary (criterion II) is not delivered» / «Nowego słownika nie dostarczamy» (карточка вопросов 14) | новый словарь есть: «Dyscypliny sportowe», 20 позиций, набор 09 | «Proponujemy nowy słownik, np. „Dyscypliny sportowe” (20 pozycji) z druku stypendium; to propozycja do zatwierdzenia przez urząd» |
| «Optional model step… off by default» | верно | оставить |
| «Measured on 27 task photos: 172 -> 199 of 651…» | число про пользу модели нельзя давать: та же проверка показала много лишних полей (замер MODELQ: добавлено 186, верных 40, лишних 146) | не называть пользу модели вообще |
| Все пометки «(plan)» | так нельзя сдавать | удалить; оставить только то, что работает |
| «porównanie wyników z ośmiu formatów», «sześć ścieżek wnioskodawcy… KRS, CEIDG», «dwie wersje druku dają listę zmian» | не построено | удалить пункты |
| Список библиотек с pypdf, python-docx, openpyxl | эти библиотеки убраны ночью (DC-2) | «pdfplumber, pdfminer.six, pypdfium2, lxml, olefile, xlrd, Tesseract, jsonata-python, jsonschema, FastAPI, PyJWT, nh3; tylko MIT, BSD, Apache-2.0» |
| «obraz rozszerzony na Debianie (drugi silnik OCR)», «integracja trwa» | не подтверждено / устарело | удалить |
| «Mediana 0,8 s na formularz cyfrowy» | число из ночной карточки (584 файла), в README другое измерение | можно оставить, но надёжнее README: «mediana poniżej 2 s dla PDF, DOC, DOCX, ODS, XLSX» |
| «Bez modelu ten sam PDF daje ten sam JSON co do bajtu» | верно только без модели и без сети | оставить с оговоркой «polecenia bez sieci dają ten sam JSON co do bajtu» |
| Поле «Postęp» субботы («Nie twierdzimy dziś, że konwersja działa») | устарело | текст поля 7 выше |

Абсолютные утверждения: в текстах для сдачи не должно быть «100 %», «bez sieci neuronowych», «bez AI», «bez modelu» (как общее утверждение о продукте), «w pełni deterministyczny», «LSTM», «poprawia dokładność». Проверка перед Save — поиск этих слов в каждом вставляемом тексте. README уже говорит, что верно по умолчанию (модель выключена, ключа в образе нет).

**Риск, который надо знать (одна фраза):** карточка, раздел 5, говорит «rozwiązanie nie może używać modeli LLM dostępnych wyłącznie przez API» и «sekrety… wyłącznie na etapie uruchamiania kontenera». Поэтому: в образе ключа нет, модель по умолчанию выключена; про модель везде говорим «model o otwartych wagach na własnym serwerze urzędu»; шлюз Eden в вашем контейнере — только способ показать блок на видео. На видео не говорите, что модель улучшает результат.

---

## 4. Ответы на два вероятных вопроса жюри (для финала 15:15)

*Где ключ модели?*
```text
W obrazie nie ma żadnego klucza: karta zadania wymaga, żeby sekrety podawać dopiero przy uruchomieniu kontenera. Administrator podaje adres własnego serwera z modelem o otwartych wagach i klucz przy starcie (VISION_BASE_URL, VISION_API_KEY_FILE) albo wpisuje je na stronie w bloku „Model AI”. Bez tego usługa działa na samych regułach i daje ten sam wynik co do bajtu.
```
*Что делает модель.*
```text
Model jest opcjonalnym pomocnikiem tylko dla słabych stron skanów i domyślnie jest wyłączony. Formularz budują reguły i biblioteka sekcji COI. Model nie pisze pól: wskazuje tylko, które linie odczytane przez OCR są etykietami, a dalej działają te same reguły. Stan kroku widać w /status.
```
