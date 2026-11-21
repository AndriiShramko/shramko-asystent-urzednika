# Questions the jury of the forms task will ask, and our answers

Written on 21 November 2026 at 13:50, before the build, from [`../03-plan/DECISIONS-forms-track.md`](../03-plan/DECISIONS-forms-track.md), the research files 14 to 18 and the model reports in `research/eden/`. The jury is named by the partner: expect a product owner, UX people, Java and automation programmers, a data scientist. They know their platform; they will test what we claim.

How to use it: the owner reads the Polish answer aloud or says it in his own words. Each answer is two sentences. The column "True only if" names what must exist; **an answer whose condition is not met is not given**: say the fallback instead. Before the final the lead strikes out what the build did not reach.

## Fifteen questions

### 1. „Czy zaimportowali Państwo te pliki do Generatora Formularzy?”

> Nie mieliśmy dostępu do importera, więc nie twierdzimy, że import przechodzi. Każdy plik przechodzi naszą kontrolę zgodną z Państwa schematem, regułami i dwoma eksportami wzorcowymi, a w raporcie odróżniamy „sprawdzone w Generatorze” od „zgodne ze wzorcem”.

*(Доступа к их импортёру у нас не было, поэтому не утверждаем, что импорт проходит. Каждый файл проходит нашу проверку по их схеме, правилам и двум эталонным экспортам, а в отчёте мы различаем «проверено в Генераторе» и «соответствует образцу».)*

True only if: the pre-import gate runs on every output. If a mentor imported a file with us (question J13), say instead: „Tak: jeden plik zaimportowaliśmy z mentorem w sobotę, wynik jest w repozytorium. Pozostałe przechodzą tę samą kontrolę, którą przeszedł tamten.”

### 2. „Dlaczego z jednej strony papieru powstały cztery strony e-usługi?”

> Papier wnosi sprawę, a standard COI wnosi stałe części: wnioskodawcę, reprezentację, kontakt, zgody i stronę końcową. Na ekranie przeglądu jednym przełącznikiem pokazujemy tylko to, co przyszło z papieru, razem z dowodem dla każdego takiego pola.

*(Бумага приносит суть дела, а стандарт COI приносит постоянные части: заявителя, представительство, контакт, согласия и последнюю страницу. На экране проверки одним переключателем показываем только то, что пришло с бумаги, с доказательством для каждого такого поля.)*

True only if: origin tags and the toggle exist. Fallback: show the tree of the partner's own export, where the same proportion is visible.

### 3. „Co chroni firmę przed pytaniem o PESEL obywatela?”

> Rozróżniamy zalogowanego człowieka, stronę, w której imieniu działa, i jego rolę: pole należy do roli, nie do strony formularza. Sześć odtwarzanych ścieżek sprawdza, które sekcje widzi każda rola i które dane inicjalne są zablokowane.

*(Мы различаем вошедшего человека, сторону, от имени которой он действует, и его роль: поле принадлежит роли, а не странице. Шесть воспроизводимых маршрутов проверяют, какие секции видит каждая роль и какие начальные данные заблокированы.)*

True only if: the journeys test runs. Fallback: the conditions of the standard sections are taken from the partner's own export, unchanged.

### 4. „Które źródło wygrywa, gdy schemat i oba eksporty mówią co innego?”

> Decydujemy osobno dla każdego z ośmiu miejsc i zapisujemy dowód oraz przełącznik; domyślnie idziemy za eksportem, bo to on pokazuje, co system naprawdę zapisuje. Odpowiedź mentora albo test importu ma pierwszeństwo przed naszą interpretacją.

*(Решаем отдельно по каждому из восьми мест, записываем доказательство и переключатель; по умолчанию идём за экспортом, потому что он показывает, что система пишет на самом деле. Ответ ментора или тест импорта важнее нашего толкования.)*

True only if: always. The register is on slide 8 and in the README.

### 5. „Jaka jest dokładność na pliku, którego Państwo nie widzieli?”

> Nie podajemy jednej liczby dokładności, bo siedem znanych formularzy i nieopisane archiwum jej nie uzasadniają. Pokazujemy osobno, ile rubryk wykryto, ile zamieniono na pola, ile pominięto z powodem i ile czeka na decyzję.

*(Одного числа точности не называем: семь известных бланков и неразмеченный архив его не обосновывают. Показываем отдельно, сколько граф найдено, сколько превращено в поля, сколько пропущено с причиной и сколько ждёт решения.)*

True only if: the ledger exists. If a held-out sample was scored by hand, add its counts, never a percentage of the whole archive.

### 6. „Czy mogli Państwo po cichu zmienić treść oświadczenia?”

> Nie: treść oświadczeń i przepisów przenosimy dosłownie, z adresem miejsca na druku. Prostym językiem piszemy tylko podpowiedzi, a niejednoznaczne oświadczenie czeka na decyzję urzędnika.

*(Нет: текст заявлений и норм переносим дословно, с адресом места на бланке. Простым языком пишем только подсказки, а неоднозначное заявление ждёт решения чиновника.)*

True only if: declarations are copied verbatim into the consent section and carry their source place. For a scan add: „Przy skanie to jest odczyt OCR, dlatego oświadczenia ze skanu zawsze trafiają do przeglądu.”

### 7. „Jak obsługują Państwo sześciostronicową deklarację odpadową z tabelami i wyliczeniami?”

> Rozpoznajemy składniki wyliczenia, jednostki oraz nagłówki wierszy i kolumn, a tabele o równych wierszach zamieniamy na sekcje powtarzalne. Wzoru nie zapisujemy w JSON-ie, bo w znanych nam eksportach nie ma pola obliczanego: trafia do raportu jako brakujące zachowanie.

*(Распознаём слагаемые расчёта, единицы и заголовки строк и столбцов, а таблицы с одинаковыми строками превращаем в повторяющиеся секции. Формулу в JSON не пишем: в известных нам экспортах нет вычисляемого поля, она попадает в отчёт как недостающее поведение.)*

True only if: judged set 8 converts with a report. If repeating sections were not built: „Tabele zapisujemy jako zwykłe pola i oznaczamy w raporcie, że powinny być sekcją powtarzalną.”

### 8. „A szesnastostronicowy wniosek sportowy, w którym są trzy wnioski?”

> Wykrywamy powtórzone tytuły i zakresy stron, czyli trzy wnioski w jednym pliku. Urzędnik podejmuje jedną decyzję: jedna e-usługa z wyborem rodzaju wniosku i rozłącznymi sekcjami albo informacja, że plik trzeba podzielić na trzy usługi.

*(Находим повторяющиеся заголовки и диапазоны страниц, то есть три заявления в одном файле. Чиновник принимает одно решение: одна услуга с выбором вида заявления и раздельными секциями или сообщение, что файл нужно разделить на три услуги.)*

True only if: judged set 9 converts and the split is detected. Fallback: „Dziś traktujemy go jako jedną usługę z trzema stronami sprawy i mówimy to w raporcie.”

### 9. „Co się stanie, gdy plik zawiesi parser albo okaże się złośliwy?”

> Każdy plik czyta osobny, krótko żyjący proces z limitem czasu, pamięci i rozmiaru wyniku, bez dostępu do klucza i do sieci. Zawieszone zadanie jest przerywane z kodem przyczyny, a następny plik przechodzi normalnie: mamy na to test.

*(Каждый файл читает отдельный короткоживущий процесс с лимитом времени, памяти и размера результата, без доступа к ключу и к сети. Зависшее задание прерывается с кодом причины, а следующий файл проходит нормально: на это есть тест.)*

True only if: the worker process and the over-budget test exist. Fallback: say honestly that parsing runs in the service process with a time limit, and that isolation is the first step before any deployment.

### 10. „Ile kosztuje wdrożenie w skali kraju?”

> Mierzymy osobno pliki tekstowe i skany na nazwanym sprzęcie: sekundy procesora i pamięć na formularz, bez GPU. Do tego doliczamy czas urzędnika na decyzje i pokazujemy założenia; nie mnożymy najlepszego wyniku przez liczbę gmin.

*(Меряем отдельно текстовые файлы и сканы на названном железе: секунды процессора и память на форму, без видеокарты. К этому добавляем время чиновника на решения и показываем допущения; лучший результат на число гмин не умножаем.)*

True only if: `eval/metrics.json` holds the measurements. Have the two numbers ready (median seconds for a text file, for a scan).

### 11. „Dlaczego nie lokalny model językowy albo wizyjny?”

> Wykrycie rubryk to nie to samo, co sprawdzalne złożenie formularza w Państwa gramatyce, a model na samym procesorze wydłuża czas i odbiera powtarzalność. Ścieżka domyślna nie potrzebuje żadnych wag poza danymi OCR; lokalny model może kiedyś podpowiadać odpowiedź z zamkniętej listy, ale nie pisze JSON-u.

*(Найти графы и собрать проверяемую форму в их грамматике это разные задачи, а модель на одном процессоре удлиняет время и лишает повторяемости. Основной путь не требует никаких весов, кроме данных OCR; локальная модель когда-нибудь может подсказывать ответ из закрытого списка, но JSON она не пишет.)*

True only if: always (decision D12).

### 12. „Karta zakazuje modeli dostępnych tylko przez API. Jak korzystali Państwo z AI?”

> Modele hostowane pisały, testowały i recenzowały kod, na co karta pozwala; w produkcie nie ma żadnego modelu, klucza ani wywołania sieciowego. Dowodem jest kontener uruchomiony bez sieci i punkt `GET /v1/selftest`.

*(Облачные модели писали, тестировали и проверяли код, что карточка разрешает; в продукте нет ни модели, ни ключа, ни сетевого вызова. Доказательство: контейнер, запущенный без сети, и точка `GET /v1/selftest`.)*

True only if: the offline run passed on the submitted image. Without the self-test endpoint say only the first sentence and show the offline run.

### 13. „Jakie licencje mają zależności i jak czytają Państwo pliki DOC bez LibreOffice?”

> Bramka licencji przepuszcza tylko licencje bez copyleft i tworzy listę wszystkich zależności; odrzuciliśmy między innymi PyMuPDF (AGPL) i python-stdnum (LGPL). Stary format DOC czyta nasz własny czytnik binarnego tekstu Worda, a LibreOffice (MPL 2.0) jest tylko opcją w drugim obrazie, jeśli Państwo ją dopuszczą.

*(Проверка лицензий пропускает только лицензии без копилефта и строит список всех зависимостей; мы отказались, в частности, от PyMuPDF (AGPL) и python-stdnum (LGPL). Старый формат DOC читает наш собственный читатель двоичного текста Word, а LibreOffice (MPL 2.0) это только опция во втором образе, если вы её допустите.)*

True only if: the licence gate ran and the own DOC reader converts the DOC files of the judged sets. If the DOC reader is not ready: „Pliki DOC odrzucamy dziś z jasnym komunikatem; czytnik jest w planie, bo nie chcieliśmy sięgać po bibliotekę z licencją copyleft.” A follow-up may come about the base image (Alpine ships GPL tools such as BusyBox): „Mówimy o bibliotekach produktu; obraz bazowy to oficjalny Alpine, który karta sama wskazuje.”

### 14. „Co ze skanami i zdjęciami, gdy OCR się pomyli?”

> Każdy odczytany wyraz ma poziom pewności, a pola z niską pewnością trafiają na początek listy do sprawdzenia, z wycinkiem skanu obok. W obrazie rozszerzonym drugi, niezależny silnik OCR potwierdza odczyt, a rozbieżność pokazujemy, zamiast wybierać po cichu.

*(У каждого распознанного слова есть уровень уверенности, и поля с низкой уверенностью идут в начало списка на проверку, с вырезкой скана рядом. В расширенном образе второй, независимый движок OCR подтверждает чтение, а расхождение мы показываем, а не выбираем молча.)*

True only if: the image reader works on the JPG and PNG files of the judged sets. The second sentence only if the `plus` image was built.

### 15. „Ministerstwo zmienia wzór. Czy urzędnik zaczyna od zera?”

> Identyfikatory powstają ze znaczenia pola, a nie z pliku, więc zmiana jednego zdania nie zmienia stu identyfikatorów. Dwie konwersje dwóch wersji druku dają listę zmian: kwota, obowiązek, załącznik, brzmienie albo sam układ.

*(Идентификаторы строятся из смысла поля, а не из файла, поэтому изменение одной фразы не меняет сотню идентификаторов. Две конвертации двух версий бланка дают список изменений: сумма, обязанность, приложение, формулировка или только вёрстка.)*

True only if: the first sentence needs the test "one changed label, ids of the other fields unchanged"; the second needs the comparison of two conversions. If only the first exists, say only the first and add: „Porównanie wersji jest następnym krokiem.”

## Reserve questions

### R1. „Co, gdy urzędnik wgra wypełniony wniosek z danymi osobowymi?”

> Rozpoznajemy wypełnienie (poprawny PESEL w rubryce, wpisane wartości, ślady pisma) i ostrzegamy; niczego nie zapisujemy, a wartości z rubryk nie trafiają do JSON-u. Zdarzenia audytowe zawierają tylko skróty i kody przyczyn, bez treści.

*(Распознаём заполнение (верный PESEL в графе, вписанные значения, следы почерка) и предупреждаем; ничего не сохраняем, значения из граф в JSON не попадают. События аудита содержат только хеши и коды причин, без содержимого.)*

True only if: the filled-form alarm exists. Fallback: „Plik żyje tylko w pamięci, a treść nie trafia do logów; wykrywanie wypełnionych druków jest w planie.”

### R2. „Czy tekst z druku może wstrzyknąć skrypt do Generatora?”

> Opisy i zgody budujemy wyłącznie z własnych szablonów HTML; tekst z papieru zamieniamy na zwykły tekst i przepuszczamy przez listę dozwolonych znaczników. Mamy test z drukiem, który zawiera znaczniki skryptu.

*(Описания и согласия строим только из собственных HTML-шаблонов; текст с бумаги превращаем в обычный текст и пропускаем через список разрешённых тегов. Есть тест с бланком, содержащим теги скрипта.)*

True only if: the injection test passes.

### R3. „Czy to jest gotowe dla asystentów AI, o których mówi karta?”

> Z tego samego modelu formularza tworzymy pliki: JSON Schema, opis narzędzia i krótki opis tekstowy, z warunkami widoczności i oznaczeniem pól, które wymagają decyzji człowieka. To są pliki, nie serwer: nic nie wysyła wniosku i nic nie łączy się z siecią.

*(Из той же модели формы делаем файлы: JSON Schema, описание инструмента и короткое текстовое описание, с условиями видимости и пометкой полей, требующих решения человека. Это файлы, а не сервер: ничто не отправляет заявление и не выходит в сеть.)*

True only if: the agent pack was built. Otherwise: „Stabilne identyfikatory, typy i warunki są już w JSON-ie; eksport dla asystentów to następny krok.”

### R4. „Co powstało przed hackathonem?”

> Przed wydarzeniem powstały badania, katalog i spis 661 dokumentów jednego miasta oraz specyfikacja: są oznaczone w repozytorium. Kod produktu powstał podczas hackathonu.

*(До события сделаны исследования, каталог и перепись 661 документа одного города и спецификация: они помечены в репозитории. Код продукта написан во время хакатона.)*

True only if: always; the tag and the NOTICE file prove it.

## When a question was not understood, or the mind goes blank

| Situation | Say (Polish) | Meaning (Russian) |
|---|---|---|
| The question was too fast | „Przepraszam, czy mogę prosić o powtórzenie pytania?” | Простите, можно повторить вопрос? |
| Not sure what was asked | „Czy dobrze rozumiem, że pytają Państwo o …?” | Правильно ли я понимаю, что вы спрашиваете о …? |
| We do not know | „Tego nie sprawdziliśmy. Wiemy tylko, że …” | Этого мы не проверяли. Знаем только, что … |
| Blank | repeat the last sentence, then: „Czy to jest zgodne z tym, jak Państwo pracują z Generatorem?” | Это совпадает с тем, как вы работаете с Генератором? |
| The question is outside the task | „To jest poza zakresem zadania; w rozwiązaniu tego nie ma.” | Это вне задания; в решении этого нет. |

Never answer with a number that is not in `eval/metrics.json`, the forensics file or the census. "Nie mierzyliśmy tego" is a good answer.
