# Questions the jury of the forms task will ask, and our answers

Written on 21 November 2026 at 13:50, before the build, from [`../03-plan/DECISIONS-forms-track.md`](../03-plan/DECISIONS-forms-track.md), the research files 14 to 18 and the model reports in `research/eden/`. The jury is named by the partner: expect a product owner, UX people, Java and automation programmers, a data scientist. They know their platform; they will test what we claim.

How to use it: the owner reads the Polish answer aloud or says it in his own words. Each answer is two sentences. The column "True only if" names what must exist; **an answer whose condition is not met is not given**: say the fallback instead. Before the final the lead strikes out what the build did not reach.

## Fifteen questions

### 1. „Czy zaimportowali Państwo te pliki do Generatora Formularzy?”

> Nie mieliśmy dostępu do importera, więc nie twierdzimy, że import przechodzi. Każdy wynik sprawdza nasza bramka zgodna z Państwa schematem i regułami: cztery kontrole (schemat, reguły, siatka, identyfikatory i połączenia) blokują wynik, a pozostałe trafiają do raportu jako ostrzeżenia.

*(Доступа к их импортёру у нас не было, поэтому не утверждаем, что импорт проходит. Каждый результат проверяет наш шлюз по их схеме и правилам: четыре проверки (схема, правила, сетка, идентификаторы и связи) блокируют результат, остальные попадают в отчёт как предупреждения.)*

True only if: the pre-import gate runs on every output (`app/pipeline.py` `BLOCKING_CHECKS` = G1 to G4; a failed G5 to G10 is a warning of a 200; G11 and G12 report `not_applicable` in the service: run of `/v1/forms/report` on the V0 image). If a mentor imported a file with us (question J13), say instead: „Tak: jeden plik zaimportowaliśmy z mentorem w sobotę, wynik jest w repozytorium. Pozostałe przechodzą tę samą kontrolę, którą przeszedł tamten.”

### 2. „Dlaczego z jednej strony papieru powstały cztery strony e-usługi?”

> Papier wnosi sprawę, a standard COI wnosi stałe części: wnioskodawcę, reprezentację, kontakt, zgody i stronę końcową. Na ekranie przeglądu jednym przełącznikiem pokazujemy tylko to, co przyszło z papieru, razem z dowodem dla każdego takiego pola.

*(Бумага приносит суть дела, а стандарт COI приносит постоянные части: заявителя, представительство, контакт, согласия и последнюю страницу. На экране проверки одним переключателем показываем только то, что пришло с бумаги, с доказательством для каждого такого поля.)*

True only if: origin tags and the toggle exist. Fallback: show the tree of the partner's own export, where the same proportion is visible.

### 3. „Co chroni firmę przed pytaniem o PESEL obywatela?”

> Rozróżniamy zalogowanego człowieka, stronę, w której imieniu działa, i jego rolę: pole należy do roli, nie do strony formularza. Siedem odtwarzanych ścieżek sprawdza, które sekcje widzi każda rola i które dane inicjalne są zablokowane; niezaliczona ścieżka jest ostrzeżeniem w raporcie, nie blokadą wyniku.

*(Мы различаем вошедшего человека, сторону, от имени которой он действует, и его роль: поле принадлежит роли, а не странице. Семь воспроизводимых маршрутов проверяют, какие секции видит каждая роль и какие начальные данные заблокированы; непройденный маршрут это предупреждение в отчёте, а не блокировка результата.)*

True only if: the journeys test runs (`app/gate/journeys/standard.json` holds seven journeys; check G8 does not block). Fallback: the conditions of the standard sections are taken from the partner's own export, unchanged.

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

> Deklarację czytamy na zwykłe pola, część z nich jako pola liczbowe; tabel tej deklaracji w tej wersji nie zamieniamy na sekcje powtarzalne. Wzoru nie zapisujemy w JSON-ie, bo w znanych nam eksportach nie ma pola obliczanego.

*(Декларацию читаем как обычные поля, часть из них как числовые; таблицы этой декларации в этой версии не превращаем в повторяющиеся секции. Формулу в JSON не пишем: в известных нам экспортах нет вычисляемого поля.)*

True only if: judged set 8 converts with a report (run on the V0 image: PDF and DOCX answer 200 with `NUMBER` fields and no `REPEATING_SECTION`; no warning says a table was flattened). Never say that tables become repeating sections before a run of set 8 shows one.

### 8. „A szesnastostronicowy wniosek sportowy, w którym są trzy wnioski?”

> Trzy wnioski w jednym pliku stają się jedną e-usługą: na początku wnioskodawca wybiera rodzaj wniosku, a sekcje danego rodzaju pokazują się dopiero po tym wyborze. Podziału pliku na trzy osobne usługi konwerter sam nie proponuje.

*(Три заявления в одном файле становятся одной услугой: в начале заявитель выбирает вид заявления, а секции этого вида появляются только после выбора. Разделить файл на три отдельные услуги конвертер сам не предлагает.)*

True only if: judged set 9 converts with the selector (run on the V0 image: PDF answers 200, page „Rodzaj wniosku” with one `RADIO` of three kinds, 13 `SHOW` conditions name it).

### 9. „Co się stanie, gdy plik zawiesi parser albo okaże się złośliwy?”

> Plik czyta proces usługi w osobnym wątku z limitem czasu, a wejście ma limity rozmiaru, liczby stron i pikseli. Po przekroczeniu czasu odpowiadamy kodem 504 TIMEOUT (mamy na to test), ale porzucone zadanie kończy się w tle samo: izolacja w osobnym procesie to pierwszy krok przed wdrożeniem.

*(Файл читает процесс сервиса в отдельном потоке с лимитом времени, а у входа есть лимиты размера, числа страниц и пикселей. При превышении времени отвечаем кодом 504 TIMEOUT (на это есть тест), но брошенное задание само доходит до конца в фоне: изоляция в отдельном процессе это первый шаг перед внедрением.)*

True only if: always for this version (`app/pipeline.py` `run_limited`: a daemon thread; `WORKER_MEMORY_MB` is read by nothing; test `tests/shell/test_d19.py`). Never say „osobny proces” or „limit pamięci” before a worker process exists.

### 10. „Ile kosztuje wdrożenie w skali kraju?”

> Nie mierzyliśmy tego na nazwanym sprzęcie, więc nie podajemy kosztu w skali kraju. Ścieżka domyślna działa na samym procesorze, bez GPU i bez płatnego API; do kosztu trzeba doliczyć czas urzędnika na decyzje, a najlepszego wyniku nie mnożymy przez liczbę gmin.

*(Мы не мерили это на названном железе, поэтому не называем стоимость в масштабе страны. Путь по умолчанию работает на одном процессоре, без видеокарты и без платного API; к стоимости надо добавить время чиновника на решения, а лучший результат на число гмин мы не умножаем.)*

True only if: always while `eval/metrics.json` does not exist (it is absent at `c9bd241`). When it holds the measurements, replace the first sentence by the two numbers (median seconds for a text file, for a scan) and the machine.

### 11. „Dlaczego nie lokalny model językowy albo wizyjny?”

> Wykrycie rubryk to nie to samo, co sprawdzalne złożenie formularza w Państwa gramatyce, a model na samym procesorze wydłuża czas i odbiera powtarzalność. Ścieżka domyślna nie potrzebuje żadnych wag poza danymi OCR; lokalny model może kiedyś podpowiadać odpowiedź z zamkniętej listy, ale nie pisze JSON-u.

*(Найти графы и собрать проверяемую форму в их грамматике это разные задачи, а модель на одном процессоре удлиняет время и лишает повторяемости. Основной путь не требует никаких весов, кроме данных OCR; локальная модель когда-нибудь может подсказывать ответ из закрытого списка, но JSON она не пишет.)*

True only if: always (decision D12).

### 12. „Karta zakazuje modeli dostępnych tylko przez API. Jak korzystali Państwo z AI?”

> Modele hostowane pisały, testowały i recenzowały kod, na co karta pozwala; w produkcie nie ma żadnego modelu, klucza ani wywołania sieciowego. Dowodem jest konwersja w kontenerze uruchomionym z `--network none` (polecenie 1 w README), a `GET /status` pokazuje `engine: "rules"`.

*(Облачные модели писали, тестировали и проверяли код, что карточка разрешает; в продукте нет ни модели, ни ключа, ни сетевого вызова. Доказательство: конвертация в контейнере, запущенном с `--network none` (команда 1 в README), а `GET /status` показывает `engine: "rules"`.)*

True only if: the offline run (command 1 of the README) passed on the submitted image. If `GET /status` is not in the submitted image, drop the second half of the sentence.

### 13. „Jakie licencje mają zależności i jak czytają Państwo pliki DOC bez LibreOffice?”

> Bramka licencji przepuszcza w zależnościach Pythona tylko licencje bez copyleftu i tworzy ich listę; jedyny składnik LGPL w obrazie (libheif, tylko dla HEIC, spoza listy formatów zadania) działa jako osobny, niezmieniony program, więc żadna licencja nie wymaga upublicznienia naszego kodu (karta, rozdział 5); odrzuciliśmy między innymi PyMuPDF (AGPL) i python-stdnum (LGPL). Stary format DOC czyta nasz własny czytnik binarnego tekstu Worda; LibreOffice nie ma w żadnym z naszych obrazów.

*(Проверка лицензий пропускает только лицензии без копилефта и строит список всех зависимостей; мы отказались, в частности, от PyMuPDF (AGPL) и python-stdnum (LGPL). Старый формат DOC читает наш собственный читатель двоичного текста Word; LibreOffice нет ни в одном из наших образов.)*

True only if: the licence gate ran and the own DOC reader converts the DOC files of the judged sets. If the DOC reader is not ready: „Pliki DOC odrzucamy dziś z jasnym komunikatem; czytnik jest w planie, bo nie chcieliśmy sięgać po bibliotekę z licencją copyleft.” A follow-up may come about the base image (Alpine ships GPL tools such as BusyBox): „Mówimy o bibliotekach produktu; obraz bazowy to oficjalny Alpine, który karta sama wskazuje.”

### 14. „Co ze skanami i zdjęciami, gdy OCR się pomyli?”

> Każdy wyraz z OCR ma poziom pewności, który wchodzi do oceny pola, a miejsca niepewne raport oznacza ostrzeżeniem `LOW_CONFIDENCE` ze stroną i prostokątem na druku; ekran przeglądu prosi, by sprawdzić je na papierze. Drugiego silnika OCR w tej wersji nie ma: odczytuje jeden Tesseract.

*(У каждого слова из OCR есть уровень уверенности, который входит в оценку поля, а неуверенные места отчёт отмечает предупреждением `LOW_CONFIDENCE` со страницей и прямоугольником на бланке; экран проверки просит сверить их с бумагой. Второго движка OCR в этой версии нет: читает один Tesseract.)*

True only if: the image reader works on the JPG and PNG files of the judged sets (run on the V0 image, set 8: JPG and PNG answer 200, `reader: image.ocr`, `LOW_CONFIDENCE` warnings with `page` and `box`). `OCR_SECOND_ENGINE` is read by nothing, and the review screen draws no crop of the scan: never promise either.

### 15. „Ministerstwo zmienia wzór. Czy urzędnik zaczyna od zera?”

> Identyfikatory powstają z tytułu formularza i ze znaczenia pola, więc ten sam druk przy powtórnej konwersji daje te same identyfikatory, a nowy tytuł zmienia wszystkie, chyba że ustawimy stały klucz `FORM_KEY`. Porównanie dwóch wersji druku jest następnym krokiem.

*(Идентификаторы строятся из заголовка формы и смысла поля, поэтому тот же бланк при повторной конвертации даёт те же идентификаторы, а новый заголовок меняет все, если не задать постоянный ключ `FORM_KEY`. Сравнение двух версий бланка это следующий шаг.)*

True only if: always for this version (`app/compose/__init__.py`: the form key is the slug of the title; run on synthetic DOCX: same title, 68 of 68 ids equal; new title, 0 of 68; with `FORM_KEY`, 68 of 68). There is no diff route and no diff command.

## Reserve questions

### R1. „Co, gdy urzędnik wgra wypełniony wniosek z danymi osobowymi?”

> Ostrzeżenia o wypełnionym druku w tej wersji nie ma; wykrywanie wypełnionych druków jest w planie. Pliku nie zapisujemy na stałe (OCR używa plików tymczasowych w `/tmp` kontenera), a logi usługi nie zawierają nazwy ani treści pliku.

*(Предупреждения о заполненном бланке в этой версии нет; распознавание заполненных бланков в плане. Файл мы не сохраняем навсегда (OCR использует временные файлы в `/tmp` контейнера), а логи сервиса не содержат ни имени, ни содержимого файла.)*

True only if: always for this version (`FILLED_FORM` is declared in `app/model/common.py` and emitted nowhere; `FILLED_FORM=reject` is read by nothing; the Dockerfile says OCR writes to `/tmp`; the V0 container log after eight conversions holds no file name). When the alarm exists, say what it detects, from its test.

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
