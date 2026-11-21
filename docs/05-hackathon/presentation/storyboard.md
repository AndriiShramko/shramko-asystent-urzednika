# Pitch deck storyboard: "Od wniosku do odpowiedzi"

Version 2 (21 November 2026): revised after the pitch research ([`research/10-pitch-and-presentation.md`](../../../research/10-pitch-and-presentation.md) §9): the product is named in the first sentence, every slide has at most three sentences of speech, the counter topic takes one slide instead of three, a visible "what works, what is simulated" slide was added, labels were shortened, unmeasured numbers were removed, and the Polish was corrected.

The presenter is not a confident speaker. The deck carries the story: movement on every slide, at most six words on screen, one to three short sentences to say, and a second window that shows him exactly what to read. Slides are in Polish (the jury is Polish). The reading text is in Polish; under it a Russian line gives the meaning.

Live address: <https://urzad.flyreelstudio.eu/deck/> (served from `site/deck/` of this repository; pushing to `main` updates it within two minutes). The same files open from disk without a network.

## Two artefacts from one source

| Artefact | When it is used | Form |
|---|---|---|
| **Live deck** | Talking to mentors during the event; the final pitch (5 minutes plus 5 minutes of questions) | Web page, animated, two windows: audience window and presenter window (key `P`) |
| **PDF for the first judging stage** | Uploaded to the submission platform on Sunday morning; jurors read it alone, a few minutes per project | The same slides in print mode (`?print=1`): final frame of each animation plus one caption sentence, so the PDF explains itself without a speaker; at most 10 MB |

## Rules of this deck

1. Movement on every slide: an animated infographic about exactly what is being said. No "text plus photo".
2. On screen: at most six words; labels inside a drawing: at most three words each.
3. Speech: at most three short sentences per slide; about 280 words in total, so that a five-minute limit leaves room for the demo and for a pause.
4. Slide 4 is a pause slide: the demo plays or is shown live, the presenter comments in his own words.
5. Dark theme, very large type, high contrast, readable from the back of a hall.
6. Nothing is loaded from the internet at run time.
7. Only true claims. A number appears only when the build has measured it (`site/deck/metrics.json`); until then the slide shows the claim without a number. What works and what is simulated comes from `site/deck/status.json`, which the lead keeps equal to [`../jury-qa.md`](../jury-qa.md).
8. Present tense is used only for what is built. Texts marked **(if built)** have a fallback wording.

## Slides

Fields: **Screen** (words on the slide) · **Motion** (the animated infographic) · **Say** (Polish, read from the presenter window) · **RU** (meaning, for the presenter) · **Cue** (what to do) · **Caption** (the sentence added in the PDF).

### 1. Problem

- **Screen:** 14 dni.
- **Motion:** a calendar strip counts fourteen days down, day by day; envelopes drop into an inbox faster than they leave; the last days turn red. A small label: „Bydgoszcz 2022: 501–1200”.
- **Say:** Szanowni Państwo, dzień dobry: Asystent Urzędnika pomaga odpowiedzieć na wniosek o informację publiczną. Na każdy taki wniosek urząd ma czternaście dni. Do Urzędu Miasta Bydgoszczy wpływa ich od 500 do 1200 rocznie, czyli kilka dziennie.
- **RU:** Ассистент чиновника помогает ответить на запрос о публичной информации. На каждый такой запрос у мэрии 14 дней. В мэрию Быдгоща их приходит от 500 до 1200 в год, несколько в день.
- **Cue:** дождись красных дней в календаре, потом дальше.
- **Caption:** Asystent Urzędnika pomaga odpowiedzieć na wniosek o informację publiczną; termin wynosi 14 dni, a do urzędu dużego miasta wpływa kilka wniosków dziennie (Bydgoszcz: 501–1200 w 2022 r. według monitoringu Sieci Obywatelskiej Watchdog Polska).

### 2. Why it is hard

- **Screen:** Trzy trudne kwestie
- **Motion:** three cards flip in one after another, each with an icon: „Jakie pismo?”, „Pismo czy decyzja?”, „Dane osobowe?”; a small gavel appears behind them at the end.
- **Say:** Za każdym razem urzędnik musi rozstrzygnąć trzy kwestie. Czym jest to pismo, czy odpowiedzieć pismem czy decyzją, i gdzie są dane osobowe do ochrony. Pomyłka może skończyć się skargą do sądu administracyjnego.
- **RU:** Каждый раз чиновник решает три вопроса: что это за письмо; отвечать письмом или решением; где персональные данные, которые надо защитить. Ошибка может закончиться жалобой в административный суд.
- **Cue:** карточки появятся сами; говори спокойно.
- **Caption:** Trzeba ustalić, czym jest pismo, wybrać formę odpowiedzi (pismo albo decyzja) i ochronić dane osobowe; błąd może skutkować skargą do sądu administracyjnego.

### 3. The solution in one picture

- **Screen:** Asystent przygotowuje. Urzędnik decyduje.
- **Motion:** an envelope travels along a line through four stations that light up in turn: „Analiza”, „Terminy”, „Projekt pisma”, „Zatwierdzenie”; at the last station a person icon presses a button and a document with a tick comes out.
- **Say:** Asystent czyta wniosek, mówi, czym on jest i dlaczego, i liczy terminy. Znajduje wcześniejsze odpowiedzi i przygotowuje projekt pisma. Ostatnie słowo należy zawsze do urzędnika.
- **RU:** Ассистент читает запрос, говорит, что это и почему, и считает сроки. Находит прежние ответы и готовит проект письма. Последнее слово всегда за чиновником.
- **Cue:** на последней фразе конверт дойдёт до человека.
- **Caption:** Asystent analizuje wniosek, liczy terminy, znajduje wcześniejsze odpowiedzi i przygotowuje projekt pisma; każdy projekt zatwierdza urzędnik.

### 4. Demo (pause slide)

- **Screen:** Demo
- **Motion:** the product itself. If `site/deck/media/demo.mp4` exists it plays muted in a loop; otherwise an animated mock of the desk plays: an e-mail opens, three questions get numbered highlights, three labels appear („już w BIP”, „dane z wydziału”, „dane osobowe”), a deadline badge shows two dates, a draft fills in, a button „Zatwierdź” is pressed.
- **Say:** Pokażę, jak to działa: wpływa e-mail z trzema pytaniami, a asystent rozdziela je na osobne sprawy. Pierwsza informacja jest już w BIP, druga wymaga danych z wydziału, trzecia dotyczy danych osobowych. Projekt odpowiedzi powstaje na Państwa oczach; mogą Państwo podać własny wniosek.
- **RU:** Покажу, как работает: приходит письмо с тремя вопросами, ассистент делит его на отдельные дела. Первое уже есть в BIP, для второго нужны данные отдела, третье касается персональных данных. Проект ответа появляется у вас на глазах; можете дать свой запрос.
- **Cue:** если есть живое демо, переключись на него (Alt+Tab) и вернись; если нет, комментируй ролик. Время назови, только если оно измерено.
- **Caption:** Pokaz: e-mail z trzema pytaniami zostaje rozdzielony na osobne sprawy, zakwalifikowany i opatrzony terminami, a projekt odpowiedzi powstaje od razu. Demo w przeglądarce: urzad.flyreelstudio.eu.

### 5. Secure

- **Screen:** Model widzi tylko znaczniki.
- **Motion:** a sentence „Jan Kowalski, ul. Długa 5” turns letter by letter into „[OSOBA_1], [ADRES_1]”; the tokens fly to a box „model”; a building outline „urząd” with a shield surrounds the original names, which never leave it.
- **Say:** Bezpieczeństwo: dane osobowe są zastępowane znacznikami, zanim tekst trafi do modelu. Model może działać lokalnie, w urzędzie, i nie wykonuje poleceń zapisanych we wniosku. Każdy krok jest zapisywany w dzienniku.
- **RU:** Безопасность: персональные данные заменяются метками до того, как текст попадёт в модель. Модель может работать локально, в мэрии, и не выполняет команд, записанных в запросе. Каждый шаг записывается в журнал.
- **Cue:** подожди, пока имя превратится в метку.
- **Caption:** Dane osobowe są zastępowane znacznikami przed wysłaniem tekstu do modelu; model może działać lokalnie i nie wykonuje poleceń zapisanych we wniosku; każdą czynność zapisuje dziennik.

### 6. Legal safety, measured

- **Screen:** Każdy przepis sprawdzony.
- **Motion:** a draft paragraph with citation chips; each chip („art. 13 ust. 2”, „art. 16 ust. 1”) flies to a book „tekst ustawy” and returns with a green tick; a fake chip „art. 99” bounces back red and the draft gets a stamp „zablokowano”. Counters from `metrics.json` count up underneath when present, with the size of the test set.
- **Say:** Program sprawdza każdą podstawę prawną w tekście ustawy. Projekt z nieistniejącym przepisem zostaje zablokowany.
- **RU:** Программа проверяет каждое правовое основание по тексту закона. Проект с несуществующей статьёй блокируется.
- **Cue:** если внизу есть цифры, добавь: «Na [N] wnioskach testowych: zero nieistniejących przepisów i zero wycieków danych» (на N тестовых запросах ноль несуществующих статей и ноль утечек). Если цифр нет, не говори их.
- **Caption:** Podstawy prawne w projekcie są weryfikowane programowo w tekście ustawy; projekt z nieistniejącym przepisem jest blokowany. Wyniki testów na danych syntetycznych: liczby na slajdzie.

### 7. Less work at the source

- **Screen:** Mniej wniosków. Lepsze wnioski.
- **Motion:** a PDF form icon morphs into a phone screen with a form („PDF → formularz”); a person types a question; a hint slides in: „Już w BIP” with a link; the envelope fades away unsent. Second pass: the envelope is sent and lands at the office as a tidy card with numbered questions.
- **Say (if built):** Idziemy krok dalej: ten sam silnik zamienia urzędowy wzór wniosku w formularz online. Mieszkaniec od razu widzi, że informacja jest już w BIP. A jeśli wyśle wniosek, ten trafia do urzędu w uporządkowanej postaci.
- **Say (fallback, not built):** Idziemy krok dalej: ten sam silnik może zamienić urzędowy wzór wniosku w formularz online. Mieszkaniec od razu zobaczy, że informacja jest już w BIP. A wysłany wniosek trafi do urzędu w uporządkowanej postaci.
- **RU:** Идём на шаг дальше: тот же движок превращает официальный бланк запроса в онлайн-форму. Житель сразу видит, что информация уже есть в BIP. А если отправит запрос, он придёт в мэрию в упорядоченном виде.
- **Cue:** это мост ко второму заданию (оцифровка формуляров); говори спокойно.
- **Caption:** Ten sam silnik zamienia wzór PDF w formularz online: mieszkaniec dostaje wskazanie, gdzie informacja jest już opublikowana, a wysłany wniosek trafia do urzędu w uporządkowanej postaci.

### 8. The same core, a bigger picture

- **Screen:** Dane raz. Wspólne wzory.
- **Motion:** a phone with a profile shows a QR handshake with a clerk's screen; three different forms slide in and the same fields light up and fill on all three; then the forms fly to a shelf „rejestr wzorów” connected to several office buildings; a large database icon with people silhouettes appears and is crossed out; a small badge „Opole 2022” pulses.
- **Say:** Ten sam rdzeń przyda się przy stanowisku obsługi: mieszkaniec podaje dane raz, a formularze drukują się wypełnione. Podobny system uruchomiłem w 2022 roku w punkcie pomocy uchodźcom w Opolu. Wspólny dla urzędów jest rejestr wzorów, a dane osobowe zostają u mieszkańca.
- **RU:** То же ядро пригодится на стойке обслуживания: житель вводит данные один раз, а бланки печатаются заполненными. Похожую систему я запустил в 2022 году в пункте помощи беженцам в Ополе. Общим для учреждений будет реестр образцов, а персональные данные остаются у жителя.
- **Cue:** про Ополе скажи обязательно: это твой настоящий опыт.
- **Caption:** Kolejny moduł na tym samym rdzeniu: dane podane raz wypełniają wiele urzędowych formularzy (doświadczenie z Opola, 2022). Skalowanie bez centralnej bazy danych osobowych: wspólny, otwarty rejestr wzorów.

### 9. What works, what is simulated

- **Screen:** Co działa. Co symulujemy.
- **Motion:** two columns; items from `status.json` tick in one by one: on the left with green ticks („analiza”, „terminy”, „projekt pisma”, „maskowanie danych”, „kontrola przepisów”, „dziennik”), on the right with amber dots („połączenie z EZD”, „logowanie urzędowe”); a third line fades in underneath: „dane syntetyczne”.
- **Say:** Uczciwie: to, co Państwo widzieli, działa na prawdziwym kodzie. Połączenie z systemem EZD i logowanie urzędowe są symulowane. Dane w pokazie są syntetyczne.
- **RU:** Честно: то, что вы видели, работает на настоящем коде. Подключение к системе EZD и вход через учётные записи мэрии имитируются. Данные в показе синтетические.
- **Cue:** списки на экране берутся из файла status.json; называй только то, что там в левой колонке.
- **Caption:** Co działa w prototypie, a co jest symulowane: lista na slajdzie; dane w pokazie są syntetyczne.

### 10. Ready for a pilot

- **Screen:** Gotowe do pilotażu.
- **Motion:** a timeline draws itself with four points: „Dziś: prototyp”, „Grudzień: test”, „Styczeń: pilotaż”, „Dalej: EZD”; three badges drop in: „otwarty kod”, „obok EZD”, „model lokalny”.
- **Say:** Asystent działa obok systemu EZD i niczego w nim nie zmienia, a kod jest otwarty. W grudniu możemy zrobić test na danych urzędu, w styczniu pilotaż w jednym referacie. Mieszkam w Bydgoszczy i chcę to zrobić razem z Państwem.
- **RU:** Ассистент работает рядом с системой EZD и ничего в ней не меняет, код открыт. В декабре можем сделать тест на данных мэрии, в январе пилот в одном отделе. Я живу в Быдгоще и хочу сделать это вместе с вами.
- **Cue:** последнюю фразу скажи, глядя на жюри. Если ментор города назвал другие сроки, назови его сроки.
- **Caption:** Asystent działa obok systemu EZD, kod jest otwarty, model może być lokalny; proponujemy test na danych urzędu i pilotaż w jednym referacie w ciągu kilku tygodni.

### 11. Close

- **Screen:** Od wniosku do odpowiedzi.
- **Motion:** the envelope from slide 3 makes the full loop once more, quickly, and ends as an approved document; a QR code to `urzad.flyreelstudio.eu` and the repository address fade in.
- **Say:** Od wniosku do odpowiedzi: szybciej, bezpieczniej, z człowiekiem, który decyduje. Dziękuję i zapraszam do pytań.
- **RU:** От запроса до ответа: быстрее, безопаснее, с человеком, который решает. Спасибо, жду вопросов.
- **Cue:** оставь слайд на экране на время вопросов; ответы в твоём окне, клавиши 1–9 и 0.
- **Caption:** Asystent Urzędnika: od wniosku do odpowiedzi. Demo i kod: urzad.flyreelstudio.eu · github.com/AndriiShramko/shramko-asystent-urzednika

## Answer cards for the questions (presenter window only)

Each card: a Polish answer of two or three sentences and a Russian hint. The lead agent keeps them true to what was built.

| Key | Question | Answer (PL) | RU |
|---|---|---|---|
| 1 | Gdzie trafiają dane mieszkańca? | Dane nie opuszczają kontroli urzędu. Dane osobowe są maskowane lokalnie, zanim tekst trafi do modelu, a model może działać na serwerze urzędu. Na ekranie widać, co dokładnie dostał model. | Данные не выходят из-под контроля мэрии: маскируются локально, модель может стоять в мэрии, на экране видно, что получила модель. |
| 2 | Kto odpowiada za odpowiedź? | Urzędnik, który ją zatwierdza, i organ, który ją podpisuje, tak jak dziś. Asystent tylko przygotowuje projekt. Projekt decyzji odmownej zawsze trafia do zatwierdzenia przez urzędnika, a w razie potrzeby przez prawnika. | Отвечает чиновник, который утвердил, и орган, который подписал. Ассистент только готовит проект. Проект отказа всегда утверждает чиновник, при необходимости юрист. |
| 3 | A jeśli model się pomyli? | Projekt powstaje tylko ze źródeł: tekstu ustawy, BIP i wcześniejszych odpowiedzi urzędu. Podstawy prawne sprawdza program, a nie model. Fragmenty napisane przez model są oznaczone, dopóki urzędnik ich nie zatwierdzi. | Проект строится только из источников; основания проверяет программа; текст модели помечен, пока его не утвердят. |
| 4 | Jaki model i dlaczego? | Model jest wymienny. Domyślnie używamy otwartego polskiego modelu uruchamianego lokalnie, bo wtedy dane zostają w urzędzie. Model komercyjny dostaje tylko tekst po pseudonimizacji i tylko decyzją urzędu. | Модель заменяемая; по умолчанию открытая польская локально; коммерческая получает только обезличенный текст и только по решению мэрии. |
| 5 | Ile to kosztuje? | Jeden serwer w urzędzie albo niewielka instancja w chmurze. Bez opłat licencyjnych za stanowisko, bo kod i komponenty są otwarte. | Один сервер или небольшая облачная машина; без лицензий за рабочее место. |
| 6 | Jak to połączyć z EZD? | Asystent działa obok EZD. Na początek przez eksport i import pisma, docelowo przez API, czyli interfejs programistyczny. Zatwierdzony projekt wraca do EZD do podpisu i wysyłki. | Работает рядом с EZD: сначала экспорт и импорт, потом через API; утверждённый проект возвращается в EZD. |
| 7 | Co w demo jest prawdziwe? | Powiem to wprost. Działają: analiza wniosku, terminy, projekt pisma, maskowanie danych, kontrola przepisów i dziennik. Symulowane są: połączenie z EZD i logowanie urzędowe. Dane w pokazie są syntetyczne. | Скажу прямо: работает разбор, сроки, проект письма, маскирование, проверка статей, журнал; имитируются связь с EZD и вход; данные синтетические. (Главный агент правит под то, что построено.) |
| 8 | Co z RODO i aktem o AI? | Administratorem pozostaje urząd, a podstawą jest obowiązek prawny rozpatrzenia wniosku. Asystent nie podejmuje decyzji wobec osoby: przygotowuje projekt, człowiek decyduje, wszystko jest w dzienniku. Dokumentujemy cel, nadzór i zapisy, żeby urząd mógł sam ocenić klasyfikację systemu. | Администратор данных остаётся мэрия; ассистент не решает за человека; документируем цель, надзор и журнал. |
| 9 | A wnioski anonimowe? | Asystent nigdy sam nie odrzuca wniosku z powodu braku danych. Pokazuje urzędnikowi obie linie orzecznictwa, a o wezwaniu do identyfikacji decyduje polityka urzędu. | Ассистент сам не отклоняет анонимные запросы; показывает обе линии судебной практики; решает политика мэрии. |
| 0 | Co powstało na hackathonie? | Badania i specyfikację przygotowałem wcześniej i jawnie to oznaczyłem. Kod aplikacji powstał tutaj, w ciągu 24 godzin; widać to w historii repozytorium. | Исследование и спецификация сделаны заранее и помечены; код написан здесь за 24 часа, это видно в истории. |

Phrases for difficult moments (shown at the bottom of the answer panel): „Proszę powtórzyć pytanie.” · „Czy dobrze rozumiem, że pytają Państwo o …?” · „Nie wiem. Sprawdzimy to i odpowiemy po prezentacji.” · „Dziękuję za to pytanie.”

## Technical specification of the deck

- Files: `site/deck/index.html`, `deck.css`, `deck.js` (engine), `slides.js` (all texts of this storyboard as data: the lead edits texts here without touching the engine; slide 7 carries both wordings and a flag `built`), `scenes.js` (the animated drawings as inline SVG with CSS and small scripts), `metrics.json`, `status.json` (two lists for slide 9: `works` and `simulated`), optional `media/demo.mp4`.
- Keys in the audience window: `→`, `Space`, `PageDown` next; `←`, `PageUp` previous; `Home`, `End`; `F` full screen; `P` presenter window; `M` motion on or off; a number then `Enter` jumps to a slide. Clickers that send `PageDown` and `PageUp` work.
- Presenter window: slide number of total; the Polish text very large; the Russian line smaller and dimmer; the cue; the words of the next slide; a timer that starts on the first advance and shows 5:00 counting down, yellow from 4:00 elapsed and red after zero; the answer cards as a grid of buttons and by the number keys; the phrases for difficult moments. Both windows stay in step in both directions (opener messaging, with a broadcast channel and storage events as fallbacks). It works when opened from disk.
- Print mode `?print=1`: all slides one per page, 1920 by 1080, animations at their final frame, the caption under each slide, page numbers; `tools/deck_pdf.mjs` renders `site/deck/Asystent-Urzednika.pdf` with a headless browser and reports the size.
- Motion continues gently after the entrance animation, so no slide is ever static; with `prefers-reduced-motion` the loops stop and entrances become fades.
- No external requests. System fonts. Dark background, contrast at least 7:1 for the main words.
- Smoke test: every slide renders without console errors; a screenshot of each slide goes to `docs/assets/deck/` and a contact sheet `docs/assets/deck/contact-sheet.png` is produced for review.
