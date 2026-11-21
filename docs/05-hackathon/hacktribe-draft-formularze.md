# HackTribe texts for the forms task, version 2 (21 November 2026, 13:30)

Follows [`../03-plan/DECISIONS-forms-track.md`](../03-plan/DECISIONS-forms-track.md). Replaces version 1, which described the counter product. Fields and deadlines: [`research/01`](../../research/01-hacknation-2026-task-rules-jury.md) (draft by Saturday 20:00: project name, team name, task, table number, short description, approach, progress, repository; final by Sunday 11:00).

## Для Андрея: что и куда вставлять

1. Это тексты для HackTribe по заданию COI «Cyfryzacja formularzy». Черновик должен существовать **сегодня до 20:00**: после этого задание сменить нельзя.
2. Вставляй по порядку полей: название, команда, задание, номер стола, краткое описание, подход, прогресс, репозиторий. Польский текст идёт в поле, русская строка под ним только для тебя.
3. Название: два варианта ниже, выбери один. Я бы взял вариант A: по нему сразу понятно, что это.
4. Поле «Postęp» честное. Сейчас в нём план и измеренные факты. Перед отправкой главный агент заменит его тем, что реально работает к этому часу (из `docs/03-plan/STATUS.md`).
5. Всё, что помечено словом **(plan)**, ещё не построено: сервис, чтение восьми форматов, экран проверки, просмотрщик формы, файлы JSON для семи оцениваемых бланков, фильм, PDF.
6. К воскресенью 11:00 (лучше к 10:00) нужны: финальные тексты, PDF не больше 10 слайдов и 10 МБ, фильм не длиннее 3 минут по открытой ссылке, файлы JSON, репозиторий.
7. Номер стола впиши сам: в репозитории его нет.
8. Числа в текстах только измеренные: 69 компонентов из одной страницы, восемь расхождений в материалах, 661 документ одного города. Гмин в Польше 2 479 (источник в `research/13`), а не 2 477, как в некоторых черновиках. «Сколько длится ручная оцифровка» не называем, пока нет ответа менторов.
9. До финальной отправки прочитай образец договора о передаче прав (приложение 1 к регламенту задания): победитель передаёт права на сделанное для задания.
10. Материалы, сделанные до события, названы в тексте прямо: этого требуют правила хакатона.

## Draft fields

| Field | Text |
|---|---|
| Project name, variant A (recommended) | **Shramko Formularze: od druku do e-usługi** |
| Project name, variant B | **Shramko Formularze: kompilator z księgowym** |
| Team name | Shramko |
| Task | Cyfryzacja formularzy (Centralny Ośrodek Informatyki) |
| Table number | the owner fills it in |
| Repository | https://github.com/AndriiShramko/shramko-asystent-urzednika |

*(Вариант A: «от бланка до электронной услуги». Вариант B: «компилятор с бухгалтером».)*

### One sentence (first line of the description, the deck and the film)

> Kompilator z księgowym, nie skaner z AI: z pustego druku urzędowego powstaje JSON e-usługi w strukturze Generatora Formularzy, a każde pole, każda pominięta rubryka i każda niepewność mają swoje rozliczenie.

*(Компилятор с бухгалтером, а не сканер с ИИ: из пустого бланка получается JSON электронной услуги в структуре их Генератора форм, и у каждого поля, каждой пропущенной графы и каждой неопределённости есть отчёт.)*

### Short description (at most 500 characters; checked: under the limit)

> Budujemy usługę REST w Dockerze: jeden pusty formularz (PDF, DOC, DOCX, ODS, XLSX, JPG, PNG) na wejściu, JSON e-usługi w strukturze Generatora Formularzy na wyjściu. Opiera się na regułach i bibliotece sekcji standardu COI, bez modelu językowego i bez połączeń na zewnątrz. Rozlicza wszystko: skąd wzięło się każde pole, co stało się z każdą rubryką papieru, co pominięto i dlaczego, czego nie zgadujemy. Urzędnik zatwierdza znaczenie, nie przepisuje rubryk.

*(Строим REST-сервис в Docker: на входе один пустой бланк в любом из восьми форматов, на выходе JSON услуги в структуре Генератора форм. Основа: правила и библиотека стандартных секций COI, без языковой модели и без соединений наружу. Ведёт учёт всего: откуда взялось каждое поле, что стало с каждой графой бумаги, что пропущено и почему, чего не угадываем. Чиновник утверждает смысл, а не переписывает графы.)*

For the final submission change „Budujemy usługę” to „Usługa” and keep only what the build really does.

### Full description

> **Problem.** Urzędy publikują formularze jako PDF, DOC, DOCX, ODS, XLSX i skany. Każdy wygląda inaczej, nawet gdy dotyczy tej samej sprawy. Cyfryzacja jednego formularza wymaga dziś ręcznej analizy: jaka to procedura, jakie dane, jakie zależności, co uprościć, jak sprawdzać poprawność. To trwa i kosztuje.
>
> **Co zmierzyliśmy przed pierwszą linią kodu.** W eksporcie wzorcowym partnera jednostronicowy wniosek papierowy staje się czterostronicową e-usługą z 69 komponentami. Około czterech piątych z nich to sekcje standardu, których na papierze nie ma. Przeanalizowaliśmy oba eksporty wzorcowe pole po polu. W materiałach znaleźliśmy osiem miejsc, w których schemat, opis pól, reguły i eksporty mówią co innego: dla każdego mamy decyzję, dowód i przełącznik. Do testów odporności mamy 661 prawdziwych dokumentów z kart usług jednego miasta.
>
> **Pomysł: kompilator z księgowym, nie skaner z AI.** Formularz papierowy kompilujemy do gramatyki Generatora Formularzy: regułami i biblioteką sekcji standardu COI. Księgowy pilnuje, żeby nic nie zginęło: każde pole ma źródło, każda rubryka papieru ma dalszy los, a czego nie da się ustalić z druku, tego nie zgadujemy.
>
> **Jak to działa: sześć kroków.**
> 1. Bramka. Sprawdzamy rozszerzenie, zgodność zawartości z typem pliku, nazwę, rozmiar i token JWT. Plik istnieje tylko w pamięci albo w katalogu tymczasowym.
> 2. Odczyt. Osiem formatów sprowadzamy do jednego modelu strony: tekst z położeniem, linie, kratki, tabele. Skany czyta OCR z polskimi danymi.
> 3. Rubryki. Znajdujemy miejsca do wypełnienia: wykropkowania, podkreślenia, rzędy kratek, pola wyboru, komórki tabel. Każde dostaje etykietę i adres na stronie.
> 4. Znaczenie. Odpowiadamy na dziesięć pytań o druk: tytuł, adresat, kto może wnioskować, pola sprawy, wybory i zależności, załączniki, oświadczenia, opłata, co jest wyłącznie papierowe.
> 5. Kompozycja. Z biblioteki sekcji standardu i z pól sprawy składamy JSON dokładnie w strukturze partnera: strony, sekcje, walidatory, słowniki, dane inicjalne, warunki JSONata.
> 6. Kontrola przed importem i rozliczenie. Wynik musi przejść schemat, reguły partnera i wykonanie każdego warunku. Obok JSON-u powstaje raport: pochodzenie pól, bilans rubryk, ostrzeżenia.
>
> Usługa odpowiada czystym JSON-em partnera, bez dodatkowych kluczy. Raport jest osobnym plikiem.
>
> **Czego nie było w zadaniu, a rozwiązujemy.**
> - Zaufanie do wyniku: każde pole ma kolor pochodzenia (z papieru albo ze standardu COI); bilans rubryk pokazuje los każdego miejsca do wypełnienia; opłat, uprawnień i obowiązkowych załączników nie zgadujemy, tylko pokazujemy cytat z druku albo „nie ustalono”. (plan)
> - Bezpieczeństwo komponentu państwowego: każdy plik czyta osobny proces z limitami; kontener nie łączy się z siecią i sam to potwierdza; tekst z druku nie może stać się kodem w Generatorze; zdarzenia audytowe nie zawierają treści. (plan)
> - Poprawność rozpoznanych danych: własne cyfry kontrolne (PESEL, NIP, REGON, rachunek bankowy, dowód osobisty), długość pola z liczby kratek, wykonanie każdego warunku JSONata przed oddaniem pliku, porównanie wyników z ośmiu formatów tego samego druku. (plan)
> - Osoba, pełnomocnik, firma: odtwarzamy sześć ścieżek wnioskodawcy i sprawdzamy, które sekcje widzi każda rola; dla firm proponujemy nowe źródła danych inicjalnych (KRS, CEIDG, REGON, adres do e-Doręczeń) w osobnym pliku. (plan)
> - Zmiany wzorów: identyfikatory powstają ze znaczenia pola, nie z pliku; dwie wersje druku dają listę zmian: kwota, obowiązek, załącznik, brzmienie, układ. (plan)
> - Koszt: bez GPU i bez modelu językowego; mierzymy sekundy procesora i pamięć na formularz, a przeliczenie na skalę kraju pokazujemy razem z założeniami. (plan)
>
> **Technologia i licencje** (stos wybrany i sprawdzony pod kątem licencji oraz Pythona 3.14; integracja trwa). Python 3.14, FastAPI, Docker: obraz podstawowy na Alpine, rozszerzony na Debianie (drugi silnik OCR, opcje). Odczyt: pypdfium2, pdfminer.six, pypdf, lxml, python-docx, openpyxl, olefile, Tesseract 5 z polskimi danymi. Warunki: jsonata-python. Biblioteki produktu mają licencje bez copyleft (MIT, BSD, Apache 2.0). Odrzuciliśmy między innymi PyMuPDF (AGPL) i python-stdnum (LGPL). Modele językowe dostępne przez API pomagają pisać i testować kod, zgodnie z kartą zadania; w produkcie nie ma żadnego modelu ani klucza.
>
> **Materiały sprzed wydarzenia.** Badania, katalog i spis 661 dokumentów jednego miasta oraz specyfikacja powstały przed hackathonem i są oznaczone w repozytorium. Kod produktu powstaje podczas wydarzenia.

*(Проблема: учреждения публикуют бланки в разных форматах, оцифровка каждого требует ручного анализа. Что измерили до кода: одна страница бумаги у партнёра превращается в 4 страницы и 69 компонентов, около четырёх пятых берётся из стандарта; разобраны оба экспорта; найдено восемь расхождений в материалах; есть 661 реальный документ одного города для проверки устойчивости. Идея: компилятор с бухгалтером. Шесть шагов: шлюз, чтение, графы, смысл, сборка, контроль перед импортом с отчётом. Ответ сервиса: чистый JSON партнёра, отчёт отдельным файлом. Сверх задания: доверие к результату, безопасность, правильность данных, человек/представитель/фирма, изменения бланков, стоимость: всё помечено как план. Технологии и лицензии без копилефта. Материалы до события названы прямо.)*

Before the final submission: delete every „(plan)” whose feature works, delete every bullet whose feature was not built, and remove the bracket after „Technologia i licencje”. Never submit the word „(plan)” on Sunday.

For the draft at 20:00 the short description, the approach and the progress field are enough; the full description (about 620 words) is the "detailed description" that the task card asks for in the final submission. Paste it on Saturday only if the field takes it.

### Approach

> 1. Najpierw fakty: przeanalizowaliśmy oba eksporty wzorcowe partnera i reguły. Osiem rozbieżności ma decyzję, dowód i przełącznik.
> 2. Reguły przed modelem: ścieżka domyślna nie używa modelu językowego ani usług zewnętrznych. Ten sam plik daje ten sam JSON.
> 3. Biblioteka sekcji standardu COI: około czterech piątych e-usługi pochodzi ze standardu, więc piszemy te sekcje raz i sprawdzamy na eksportach partnera.
> 4. Czysty wynik: usługa odpowiada wyłącznie JSON-em partnera. Pochodzenie pól, pewność, bilans rubryk i propozycje (nowe słowniki, nowe źródła danych inicjalnych) są w osobnym pliku.
> 5. Księgowość zamiast obietnic: każda rubryka papieru ma dalszy los, a opłat, uprawnień i obowiązkowych załączników nie zgadujemy.
> 6. Bezpieczeństwo jak dla komponentu państwowego: osobny proces dla każdego pliku, brak sieci, tekst z druku nie staje się kodem, licencje bez copyleft.
> 7. Człowiek zatwierdza: urzędnik dostaje kilka decyzji zamiast kilkudziesięciu ostrzeżeń.

*(1. Сначала факты: разобраны оба экспорта и правила, у восьми расхождений есть решение, доказательство и переключатель. 2. Правила раньше модели: без языковой модели и внешних сервисов, один и тот же файл даёт один и тот же JSON. 3. Библиотека стандартных секций COI. 4. Чистый результат, всё остальное отдельным файлом. 5. Учёт вместо обещаний. 6. Безопасность как для государственного компонента. 7. Утверждает человек: несколько решений вместо десятков предупреждений.)*

### Progress (true on 21 November at 13:30; the lead rewrites it from STATUS just before 20:00)

> Stan na 21 listopada, godz. 20:00. Gotowe i zmierzone: opis formatu partnera, nasz schemat i kontroler reguł, analiza obu eksportów wzorcowych, lista ośmiu rozbieżności z decyzjami, opracowania źródłowe (biblioteki i licencje dla Pythona 3.14, platforma partnera, bezpieczeństwo, rodzaje wnioskodawców, zmiany wzorów), decyzje architektoniczne i plan pakietów roboczych. W budowie od soboty po południu: usługa REST, czytniki ośmiu formatów, kompozytor JSON, ekran przeglądu, podgląd e-usługi, pliki JSON dla siedmiu formularzy ocenianych. Nie twierdzimy dziś, że konwersja działa: pokażemy ją w niedzielę, z pomiarami.

*(Состояние на 20:00. Готово и измерено: описание формата партнёра, наша схема и проверка правил, разбор обоих экспортов, восемь расхождений с решениями, исследования, архитектурные решения и план пакетов. Строится с субботы после обеда: сервис, чтение форматов, сборщик JSON, экран проверки, просмотрщик, файлы JSON для семи бланков. Сегодня не утверждаем, что конвертация работает: покажем в воскресенье, с замерами.)*

Rules for the lead when rewriting this field: name only what a command or a test in the repository proves at that hour; keep the last sentence until the judged forms convert through the public endpoint; mention the applicant-kinds research only if `research/17-*.md` exists.

## Final submission (Sunday, by 10:00; the system closes at 11:00)

| Item | Where it comes from |
|---|---|
| Title, descriptions, approach, progress | this file, with every „(plan)” resolved |
| Presentation, PDF, at most ten slides, at most 10 MB | [`presentation/storyboard-coi-v2.md`](presentation/storyboard-coi-v2.md) |
| Film, at most three minutes, open link | the shot list in the same file |
| The JSON files of the seven judged forms | `results/`, written by the evaluation run |
| Repository with README and the architecture document | task card, C-TECH-DOC and C-MIN-2 |
| Answers prepared for the jury | [`jury-qa-formularze.md`](jury-qa-formularze.md) |

Every number in the final texts comes from `eval/metrics.json` (our product), from [`mentor-questions/reference-json-forensics.txt`](mentor-questions/reference-json-forensics.txt) (the partner's exports) or from `data/forms-census.json` (the city's archive). The share „około czterech piątych” is the estimate of [`../02-architecture/coi-json-format.md`](../02-architecture/coi-json-format.md) §1: replace it by the measured share of standard-origin components when the origin tags exist.
