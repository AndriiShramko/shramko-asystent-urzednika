/*
 * slides.js — ALL TEXTS OF THE DECK (data only, no logic).
 *
 * Source of truth: docs/05-hackathon/presentation/storyboard.md (version 2)
 * To change a text, edit the string here and reload the page. The engine
 * (deck.js) and the drawings (scenes.js) do not need to be touched.
 *
 * Per slide:
 *   screen  — the words shown on the audience screen (max six words)
 *   say     — Polish text the presenter reads (presenter window, large)
 *   ru      — Russian meaning for the presenter (presenter window, small)
 *   cue     — what to do (presenter window)
 *   caption — the sentence printed under the drawing in the PDF (?print=1)
 *   scene   — key of the animated drawing in scenes.js (do not rename)
 * Slide 7 has two wordings: say (if built) and sayFallback (not built).
 * The presenter window shows "say" when built === true, else "sayFallback".
 *
 * Answer cards (presenter window only): key = keyboard key (1–9, 0).
 * Labels inside the drawings are in scenes.js (at most three words each).
 */
window.DECK = {
  title: 'Asystent Urzędnika',
  footer: 'Asystent Urzędnika · urzad.flyreelstudio.eu',
  durationSec: 300,  // presenter timer: 5:00
  warnAfterSec: 240, // timer turns yellow from 4:00 elapsed, red after 5:00

  slides: [
    {
      scene: 'problem',
      screen: '14 dni.',
      say: 'Szanowni Państwo, dzień dobry: Asystent Urzędnika pomaga odpowiedzieć na wniosek o informację publiczną. Na każdy taki wniosek urząd ma czternaście dni. Do Urzędu Miasta Bydgoszczy wpływa ich od 500 do 1200 rocznie, czyli kilka dziennie.',
      ru: 'Ассистент чиновника помогает ответить на запрос о публичной информации. На каждый такой запрос у мэрии 14 дней. В мэрию Быдгоща их приходит от 500 до 1200 в год, несколько в день.',
      cue: 'дождись красных дней в календаре, потом дальше.',
      caption: 'Asystent Urzędnika pomaga odpowiedzieć na wniosek o informację publiczną; termin wynosi 14 dni, a do urzędu dużego miasta wpływa kilka wniosków dziennie (Bydgoszcz: 501–1200 w 2022 r. według monitoringu Sieci Obywatelskiej Watchdog Polska).'
    },
    {
      scene: 'hard',
      screen: 'Trzy trudne kwestie',
      say: 'Za każdym razem urzędnik musi rozstrzygnąć trzy kwestie. Czym jest to pismo, czy odpowiedzieć pismem czy decyzją, i gdzie są dane osobowe do ochrony. Pomyłka może skończyć się skargą do sądu administracyjnego.',
      ru: 'Каждый раз чиновник решает три вопроса: что это за письмо; отвечать письмом или решением; где персональные данные, которые надо защитить. Ошибка может закончиться жалобой в административный суд.',
      cue: 'карточки появятся сами; говори спокойно.',
      caption: 'Trzeba ustalić, czym jest pismo, wybrać formę odpowiedzi (pismo albo decyzja) i ochronić dane osobowe; błąd może skutkować skargą do sądu administracyjnego.'
    },
    {
      scene: 'solution',
      screen: 'Asystent przygotowuje. Urzędnik decyduje.',
      say: 'Asystent czyta wniosek, mówi, czym on jest i dlaczego, i liczy terminy. Znajduje wcześniejsze odpowiedzi i przygotowuje projekt pisma. Ostatnie słowo należy zawsze do urzędnika.',
      ru: 'Ассистент читает запрос, говорит, что это и почему, и считает сроки. Находит прежние ответы и готовит проект письма. Последнее слово всегда за чиновником.',
      cue: 'на последней фразе конверт дойдёт до человека.',
      caption: 'Asystent analizuje wniosek, liczy terminy, znajduje wcześniejsze odpowiedzi i przygotowuje projekt pisma; każdy projekt zatwierdza urzędnik.'
    },
    {
      scene: 'demo',
      screen: 'Demo',
      say: 'Pokażę, jak to działa: wpływa e-mail z trzema pytaniami, a asystent rozdziela je na osobne sprawy. Pierwsza informacja jest już w BIP, druga wymaga danych z wydziału, trzecia dotyczy danych osobowych. Projekt odpowiedzi powstaje na Państwa oczach; mogą Państwo podać własny wniosek.',
      ru: 'Покажу, как работает: приходит письмо с тремя вопросами, ассистент делит его на отдельные дела. Первое уже есть в BIP, для второго нужны данные отдела, третье касается персональных данных. Проект ответа появляется у вас на глазах; можете дать свой запрос.',
      cue: 'если есть живое демо, переключись на него (Alt+Tab) и вернись; если нет, комментируй ролик. Время назови, только если оно измерено.',
      caption: 'Pokaz: e-mail z trzema pytaniami zostaje rozdzielony na osobne sprawy, zakwalifikowany i opatrzony terminami, a projekt odpowiedzi powstaje od razu. Demo w przeglądarce: urzad.flyreelstudio.eu.'
    },
    {
      scene: 'secure',
      screen: 'Model widzi tylko znaczniki.',
      say: 'Bezpieczeństwo: dane osobowe są zastępowane znacznikami, zanim tekst trafi do modelu. Model może działać lokalnie, w urzędzie, i nie wykonuje poleceń zapisanych we wniosku. Każdy krok jest zapisywany w dzienniku.',
      ru: 'Безопасность: персональные данные заменяются метками до того, как текст попадёт в модель. Модель может работать локально, в мэрии, и не выполняет команд, записанных в запросе. Каждый шаг записывается в журнал.',
      cue: 'подожди, пока имя превратится в метку.',
      caption: 'Dane osobowe są zastępowane znacznikami przed wysłaniem tekstu do modelu; model może działać lokalnie i nie wykonuje poleceń zapisanych we wniosku; każdą czynność zapisuje dziennik.'
    },
    {
      scene: 'legal',
      screen: 'Każdy przepis sprawdzony.',
      say: 'Program sprawdza każdą podstawę prawną w tekście ustawy. Projekt z nieistniejącym przepisem zostaje zablokowany.',
      ru: 'Программа проверяет каждое правовое основание по тексту закона. Проект с несуществующей статьёй блокируется.',
      cue: 'если внизу есть цифры, добавь: «Na [N] wnioskach testowych: zero nieistniejących przepisów i zero wycieków danych» (на N тестовых запросах ноль несуществующих статей и ноль утечек). Если цифр нет, не говори их.',
      caption: 'Podstawy prawne w projekcie są weryfikowane programowo w tekście ustawy; projekt z nieistniejącym przepisem jest blokowany. Wyniki testów na danych syntetycznych: liczby na slajdzie.'
    },
    {
      scene: 'source',
      screen: 'Mniej wniosków. Lepsze wnioski.',
      built: false, // true = the online form is built: presenter reads "say"; false: "sayFallback"
      say: 'Idziemy krok dalej: ten sam silnik zamienia urzędowy wzór wniosku w formularz online. Mieszkaniec od razu widzi, że informacja jest już w BIP. A jeśli wyśle wniosek, ten trafia do urzędu w uporządkowanej postaci.',
      sayFallback: 'Idziemy krok dalej: ten sam silnik może zamienić urzędowy wzór wniosku w formularz online. Mieszkaniec od razu zobaczy, że informacja jest już w BIP. A wysłany wniosek trafi do urzędu w uporządkowanej postaci.',
      ru: 'Идём на шаг дальше: тот же движок превращает официальный бланк запроса в онлайн-форму. Житель сразу видит, что информация уже есть в BIP. А если отправит запрос, он придёт в мэрию в упорядоченном виде.',
      cue: 'это мост ко второму заданию (оцифровка формуляров); говори спокойно.',
      caption: 'Ten sam silnik zamienia wzór PDF w formularz online: mieszkaniec dostaje wskazanie, gdzie informacja jest już opublikowana, a wysłany wniosek trafia do urzędu w uporządkowanej postaci.'
    },
    {
      scene: 'counter',
      screen: 'Dane raz. Wspólne wzory.',
      say: 'Ten sam rdzeń przyda się przy stanowisku obsługi: mieszkaniec podaje dane raz, a formularze drukują się wypełnione. Podobny system uruchomiłem w 2022 roku w punkcie pomocy uchodźcom w Opolu. Wspólny dla urzędów jest rejestr wzorów, a dane osobowe zostają u mieszkańca.',
      ru: 'То же ядро пригодится на стойке обслуживания: житель вводит данные один раз, а бланки печатаются заполненными. Похожую систему я запустил в 2022 году в пункте помощи беженцам в Ополе. Общим для учреждений будет реестр образцов, а персональные данные остаются у жителя.',
      cue: 'про Ополе скажи обязательно: это твой настоящий опыт.',
      caption: 'Kolejny moduł na tym samym rdzeniu: dane podane raz wypełniają wiele urzędowych formularzy (doświadczenie z Opola, 2022). Skalowanie bez centralnej bazy danych osobowych: wspólny, otwarty rejestr wzorów.'
    },
    {
      scene: 'status',
      screen: 'Co działa. Co symulujemy.',
      say: 'Uczciwie: to, co Państwo widzieli, działa na prawdziwym kodzie. Połączenie z systemem EZD i logowanie urzędowe są symulowane. Dane w pokazie są syntetyczne.',
      ru: 'Честно: то, что вы видели, работает на настоящем коде. Подключение к системе EZD и вход через учётные записи мэрии имитируются. Данные в показе синтетические.',
      cue: 'списки на экране берутся из файла status.json; называй только то, что там в левой колонке.',
      caption: 'Co działa w prototypie, a co jest symulowane: lista na slajdzie; dane w pokazie są syntetyczne.'
    },
    {
      scene: 'pilot',
      screen: 'Gotowe do pilotażu.',
      say: 'Asystent działa obok systemu EZD i niczego w nim nie zmienia, a kod jest otwarty. W grudniu możemy zrobić test na danych urzędu, w styczniu pilotaż w jednym referacie. Mieszkam w Bydgoszczy i chcę to zrobić razem z Państwem.',
      ru: 'Ассистент работает рядом с системой EZD и ничего в ней не меняет, код открыт. В декабре можем сделать тест на данных мэрии, в январе пилот в одном отделе. Я живу в Быдгоще и хочу сделать это вместе с вами.',
      cue: 'последнюю фразу скажи, глядя на жюри. Если ментор города назвал другие сроки, назови его сроки.',
      caption: 'Asystent działa obok systemu EZD, kod jest otwarty, model może być lokalny; proponujemy test na danych urzędu i pilotaż w jednym referacie w ciągu kilku tygodni.'
    },
    {
      scene: 'close',
      screen: 'Od wniosku do odpowiedzi.',
      say: 'Od wniosku do odpowiedzi: szybciej, bezpieczniej, z człowiekiem, który decyduje. Dziękuję i zapraszam do pytań.',
      ru: 'От запроса до ответа: быстрее, безопаснее, с человеком, который решает. Спасибо, жду вопросов.',
      cue: 'оставь слайд на экране на время вопросов; ответы в твоём окне, клавиши 1–9 и 0.',
      caption: 'Asystent Urzędnika: od wniosku do odpowiedzi. Demo i kod: urzad.flyreelstudio.eu · github.com/AndriiShramko/shramko-asystent-urzednika'
    }
  ],

  answers: [
    { key: '1', q: 'Gdzie trafiają dane mieszkańca?',
      a: 'Dane nie opuszczają kontroli urzędu. Dane osobowe są maskowane lokalnie, zanim tekst trafi do modelu, a model może działać na serwerze urzędu. Na ekranie widać, co dokładnie dostał model.',
      ru: 'Данные не выходят из-под контроля мэрии: маскируются локально, модель может стоять в мэрии, на экране видно, что получила модель.' },
    { key: '2', q: 'Kto odpowiada za odpowiedź?',
      a: 'Urzędnik, który ją zatwierdza, i organ, który ją podpisuje, tak jak dziś. Asystent tylko przygotowuje projekt. Projekt decyzji odmownej zawsze trafia do zatwierdzenia przez urzędnika, a w razie potrzeby przez prawnika.',
      ru: 'Отвечает чиновник, который утвердил, и орган, который подписал. Ассистент только готовит проект. Проект отказа всегда утверждает чиновник, при необходимости юрист.' },
    { key: '3', q: 'A jeśli model się pomyli?',
      a: 'Projekt powstaje tylko ze źródeł: tekstu ustawy, BIP i wcześniejszych odpowiedzi urzędu. Podstawy prawne sprawdza program, a nie model. Fragmenty napisane przez model są oznaczone, dopóki urzędnik ich nie zatwierdzi.',
      ru: 'Проект строится только из источников; основания проверяет программа; текст модели помечен, пока его не утвердят.' },
    { key: '4', q: 'Jaki model i dlaczego?',
      a: 'Model jest wymienny. Domyślnie używamy otwartego polskiego modelu uruchamianego lokalnie, bo wtedy dane zostają w urzędzie. Model komercyjny dostaje tylko tekst po pseudonimizacji i tylko decyzją urzędu.',
      ru: 'Модель заменяемая; по умолчанию открытая польская локально; коммерческая получает только обезличенный текст и только по решению мэрии.' },
    { key: '5', q: 'Ile to kosztuje?',
      a: 'Jeden serwer w urzędzie albo niewielka instancja w chmurze. Bez opłat licencyjnych za stanowisko, bo kod i komponenty są otwarte.',
      ru: 'Один сервер или небольшая облачная машина; без лицензий за рабочее место.' },
    { key: '6', q: 'Jak to połączyć z EZD?',
      a: 'Asystent działa obok EZD. Na początek przez eksport i import pisma, docelowo przez API, czyli interfejs programistyczny. Zatwierdzony projekt wraca do EZD do podpisu i wysyłki.',
      ru: 'Работает рядом с EZD: сначала экспорт и импорт, потом через API; утверждённый проект возвращается в EZD.' },
    { key: '7', q: 'Co w demo jest prawdziwe?',
      a: 'Powiem to wprost. Działają: analiza wniosku, terminy, projekt pisma, maskowanie danych, kontrola przepisów i dziennik. Symulowane są: połączenie z EZD i logowanie urzędowe. Dane w pokazie są syntetyczne.',
      ru: 'Скажу прямо: работает разбор, сроки, проект письма, маскирование, проверка статей, журнал; имитируются связь с EZD и вход; данные синтетические. (Главный агент правит под то, что построено.)' },
    { key: '8', q: 'Co z RODO i aktem o AI?',
      a: 'Administratorem pozostaje urząd, a podstawą jest obowiązek prawny rozpatrzenia wniosku. Asystent nie podejmuje decyzji wobec osoby: przygotowuje projekt, człowiek decyduje, wszystko jest w dzienniku. Dokumentujemy cel, nadzór i zapisy, żeby urząd mógł sam ocenić klasyfikację systemu.',
      ru: 'Администратор данных остаётся мэрия; ассистент не решает за человека; документируем цель, надзор и журнал.' },
    { key: '9', q: 'A wnioski anonimowe?',
      a: 'Asystent nigdy sam nie odrzuca wniosku z powodu braku danych. Pokazuje urzędnikowi obie linie orzecznictwa, a o wezwaniu do identyfikacji decyduje polityka urzędu.',
      ru: 'Ассистент сам не отклоняет анонимные запросы; показывает обе линии судебной практики; решает политика мэрии.' },
    { key: '0', q: 'Co powstało na hackathonie?',
      a: 'Badania i specyfikację przygotowałem wcześniej i jawnie to oznaczyłem. Kod aplikacji powstał tutaj, w ciągu 24 godzin; widać to w historii repozytorium.',
      ru: 'Исследование и спецификация сделаны заранее и помечены; код написан здесь за 24 часа, это видно в истории.' }
  ],

  /* Phrases for difficult moments (bottom of the answer panel). */
  phrases: [
    'Proszę powtórzyć pytanie.',
    'Czy dobrze rozumiem, że pytają Państwo o …?',
    'Nie wiem. Sprawdzimy to i odpowiemy po prezentacji.',
    'Dziękuję za to pytanie.'
  ],

  /* Labels for the counters on slide 6. Values come from metrics.json
     (null = not measured yet = counter hidden). Max three words each. */
  metricLabels: {
    test_set_size: { label: 'wniosków testowych', suffix: '' },
    invented_citations: { label: 'zmyślone przepisy', suffix: '' },
    leaked_identifiers: { label: 'wycieki danych', suffix: '' },
    class_accuracy_pct: { label: 'trafność klasyfikacji', suffix: '%' },
    seconds_per_request: { label: 'sekund na wniosek', suffix: '' }
  }
};
