/*
 * slides.js — ALL TEXTS OF THE DECK "Od druku do usługi online" (data only, no logic).
 *
 * Source of truth: docs/05-hackathon/presentation/storyboard-formularze.md
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
 * Slide 6 has two wordings: say (if built) and sayFallback (not built).
 * The presenter window shows "say" when built === true, else "sayFallback".
 *
 * Answer cards (presenter window only): key = keyboard key (1–9, 0).
 * Labels inside the drawings are in scenes.js (at most three words each).
 */
window.DECK = {
  title: 'Od druku do usługi online',
  footer: 'Od druku do usługi · formularze.flyreelstudio.eu',
  durationSec: 300,  // presenter timer: 5:00
  warnAfterSec: 240, // timer turns yellow from 4:00 elapsed, red after 5:00

  slides: [
    {
      scene: 'scale',
      screen: '710 plików. Jedno miasto.',
      say: 'Szanowni Państwo, dzień dobry. W jednym mieście policzyliśmy 275 kart usług i 710 plików formularzy. Połowa to pliki Word i RTF, a w próbie 32 druków tylko jeden miał pola do wypełnienia.',
      ru: 'В одном городе мы насчитали 275 карточек услуг и 710 файлов бланков. Половина это файлы Word и RTF, а в выборке из 32 бланков только один имел поля для заполнения.',
      cue: 'дождись, пока один лист загорится зелёным.',
      caption: 'Skala: w jednym urzędzie miasta 275 kart usług i 710 plików formularzy, z czego połowa to pliki DOC, DOCX i RTF; w próbie 32 formularzy tylko 1 miał pola do wypełnienia. Dane: katalog w repozytorium projektu.'
    },
    {
      scene: 'solution',
      screen: 'Od druku do usługi.',
      say: 'Nasze rozwiązanie zamienia urzędowy druk w usługę online: AI rozpoznaje pola i proponuje ich znaczenie, a człowiek zatwierdza. Z jednego opisu powstają formularz na telefon, wydruk na oryginalnym wzorze i reguły kontroli.',
      ru: 'Наше решение превращает официальный бланк в онлайн-услугу: ИИ распознаёт поля и предлагает их значение, человек утверждает. Из одного описания получаются форма для телефона, печать на оригинальном образце и правила проверки.',
      cue: 'три результата выедут сами; сразу переходи к показу. Если спросят про Generator Formularzy, ответ в карточке 4.',
      caption: 'AI rozpoznaje pola urzędowego druku i proponuje ich znaczenie, człowiek zatwierdza; z jednego opisu powstają formularz online, wydruk na oryginalnym wzorze i reguły kontroli.'
    },
    {
      scene: 'demo1',
      screen: 'Demo: nowy formularz',
      say: 'Pokażę to na żywo: wgrywam druk pobrany ze strony urzędu. AI proponuje pola, ja poprawiam to, co trzeba, i publikuję. Formularz online jest gotowy.',
      ru: 'Покажу вживую: загружаю бланк, скачанный с сайта мэрии. ИИ предлагает поля, я поправляю, что нужно, и публикую. Онлайн-форма готова.',
      cue: 'переключись на программу (Alt+Tab), сделай оцифровку одного бланка и вернись. Время назови, только если оно измерено.',
      caption: 'Pokaz 1: druk pobrany ze strony urzędu zostaje rozpoznany przez AI, poprawiony przez człowieka i opublikowany jako formularz online.'
    },
    {
      scene: 'demo2',
      screen: 'Demo: interesant i urzędnik',
      say: 'Teraz interesant: skanuje kod i podaje dane raz, na swoim telefonie. Urzędnik widzi je od razu, a AI wskazuje błąd przed wydrukiem. Wniosek drukuje się na urzędowym wzorze, gotowy do podpisu.',
      ru: 'Теперь посетитель: сканирует код и вводит данные один раз, на своём телефоне. Чиновник видит их сразу, а ИИ указывает на ошибку до печати. Заявление печатается на официальном образце, готовое к подписи.',
      cue: 'дай члену жюри отсканировать код своим телефоном, если сеть позволяет; иначе покажи на своём телефоне.',
      caption: 'Pokaz 2: interesant podaje dane raz na telefonie, urzędnik widzi je od razu, AI wskazuje błędy, a wniosek drukuje się na urzędowym wzorze.'
    },
    {
      scene: 'queue',
      screen: 'Z kolejki. Opole 2022.',
      say: 'To nie teoria, tylko moje doświadczenie: w 2022 roku w punkcie pomocy uchodźcom w Opolu ludzie wpisywali dane na telefonach, stojąc w kolejce. Wolontariusze drukowali gotowe wnioski, zamiast przepisywać dokumenty ręcznie. Z tamtych doświadczeń pochodzą reguły tego systemu.',
      ru: 'Это не теория, а мой опыт: в 2022 году в пункте помощи беженцам в Ополе люди вводили данные на телефонах, стоя в очереди. Волонтёры печатали готовые заявления вместо того, чтобы переписывать документы вручную. Из того опыта взяты правила этой системы.',
      cue: 'это твой настоящий опыт; скажи спокойно и коротко.',
      caption: 'Rozwiązanie wyrosło z praktyki: w 2022 r. w punkcie pomocy uchodźcom w Opolu interesanci wpisywali dane na telefonach w kolejce, a wolontariusze drukowali gotowe wnioski.'
    },
    {
      scene: 'once',
      screen: 'Dane zostają u mieszkańca.',
      built: false, // true = the mObywatel adapter is built: presenter reads "say"; false: "sayFallback"
      say: 'Dane zostają na telefonie mieszkańca: do urzędu trafiają tylko pola potrzebne w tej sprawie, zaszyfrowane, na kilka minut. Na tej samej zasadzie działa przekazywanie danych w mObywatelu: instytucja pokazuje kod QR, a mieszkaniec zatwierdza. Wspólny dla urzędów jest katalog opisów formularzy, a nie baza danych o ludziach.',
      sayFallback: 'Dane zostają na telefonie mieszkańca: do urzędu trafiają tylko pola potrzebne w tej sprawie, zaszyfrowane, na kilka minut. Na tej samej zasadzie działa przekazywanie danych w mObywatelu: instytucja pokazuje kod QR, a mieszkaniec zatwierdza. Wspólny dla urzędów jest katalog opisów formularzy, a nie baza danych o ludziach.',
      ru: 'Данные остаются на телефоне жителя: в мэрию уходят только поля, нужные для этого дела, зашифрованные, на несколько минут. По тому же принципу работает передача данных в mObywatel: учреждение показывает QR-код, житель подтверждает. Общим для учреждений будет каталог описаний бланков, а не база данных о людях.',
      cue: 'это слайд для людей из COI: про mObywatel скажи обязательно.',
      caption: 'Dane pozostają na telefonie mieszkańca; do urzędu trafiają tylko potrzebne pola, zaszyfrowane, na kilka minut, na tej samej zasadzie co przekazywanie danych instytucji w mObywatelu. Wspólny jest katalog opisów formularzy, nie baza danych osobowych.'
    },
    {
      scene: 'status',
      screen: 'Co działa. Co symulujemy.',
      say: 'Uczciwie: to, co Państwo widzieli, działa na prawdziwym kodzie. Połączenie z mObywatelem, czytnik dokumentów i logowanie przez login.gov.pl są symulowane. Dane w pokazie są syntetyczne.',
      ru: 'Честно: то, что вы видели, работает на настоящем коде. Подключение к mObywatel, сканер документов и вход через login.gov.pl имитируются. Данные в показе синтетические.',
      cue: 'называй только то, что стоит в левой колонке на экране.',
      caption: 'Co działa w prototypie, a co jest symulowane: lista na slajdzie; dane w pokazie są syntetyczne.'
    },
    {
      scene: 'offer',
      screen: 'Każdy druk może być usługą.',
      say: 'Proponujemy pilotaż: dziesięć najczęstszych druków jednego urzędu jako usługi online, z otwartym opisem gotowym do wprowadzenia do platform państwowych. Dziękuję i zapraszam do pytań.',
      ru: 'Предлагаем пилот: десять самых частых бланков одного учреждения как онлайн-услуги, с открытым описанием, готовым для государственных платформ. Спасибо, жду вопросов.',
      cue: 'оставь слайд на экране на время вопросов; ответы в твоём окне, клавиши 1–9 и 0.',
      caption: 'Propozycja: pilotaż dziesięciu najczęstszych druków jednego urzędu jako usług online, z otwartym opisem gotowym do wprowadzenia do platform państwowych. Demo i kod: formularze.flyreelstudio.eu · github.com/AndriiShramko/shramko-asystent-urzednika'
    }
  ],

  answers: [
    { key: '1', q: 'Jak AI rozpoznaje pola?',
      a: 'Analizujemy układ druku: linie, kratki i podpisy pól, a model proponuje nazwę, typ i powiązanie z danymi mieszkańca. Człowiek zatwierdza każde pole. Na końcu automat porównuje wydruk z oryginałem.',
      ru: 'Разбираем разметку бланка, модель предлагает название, тип и связь с данными жителя; человек утверждает каждое поле; в конце автомат сравнивает печать с оригиналом.' },
    { key: '2', q: 'Ile trwa cyfryzacja jednego druku?',
      a: 'Pokazaliśmy to na żywo na jednym druku. Podaję tylko czas zmierzony w pokazie; większe formularze wymagają więcej poprawek człowieka.',
      ru: 'Показали вживую на одном бланке; называю только измеренное время; большие бланки требуют больше правок.' },
    { key: '3', q: 'Co z dostępnością?',
      a: 'Formularz online powstaje z opisu pól według jednego szablonu, więc każdy ma etykiety, obsługę klawiatury i kontrast zgodny z WCAG 2.1 AA. Testy automatyczne wykrywają tylko część problemów, dlatego szablon sprawdza też człowiek.',
      ru: 'Онлайн-форма строится из описания по одному шаблону: подписи, клавиатура, контраст по WCAG 2.1 AA; автоматические тесты ловят только часть проблем, шаблон проверяет и человек.' },
    { key: '4', q: 'Jak to się ma do usług na gov.pl i w mObywatelu?',
      a: 'Nie zastępujemy platform centralnych ani planowanego Generatora Formularzy. Dajemy szybkie przejście od papierowego druku do opisu w otwartym formacie, który może być dla nich wejściem. Eksport do formatów repozytorium wzorów to kolejny krok, do ustalenia z Państwem.',
      ru: 'Не заменяем центральные платформы и планируемый Generator Formularzy: даём быстрый переход от бумажного бланка к описанию в открытом формате, которое может быть для них входом; экспорт в форматы репозитория образцов это следующий шаг.' },
    { key: '5', q: 'A mObywatel?',
      a: 'Przekazywanie danych instytucji kodem QR już w aplikacji istnieje, ale wymaga porozumienia. W pokazie używamy własnego, szyfrowanego przekazania kodem QR i nie twierdzimy, że jesteśmy zintegrowani.',
      ru: 'Передача данных по QR в приложении уже есть, но нужен договор; в показе свой шифрованный обмен, интеграцию не заявляем.' },
    { key: '6', q: 'Gdzie są dane mieszkańca?',
      a: 'Na jego telefonie. Do urzędu trafiają tylko pola potrzebne w danej sprawie, zaszyfrowane od telefonu do urzędu, i znikają po wydruku albo po kilku minutach.',
      ru: 'На его телефоне; в учреждение уходят только нужные поля, зашифрованные, и исчезают после печати или через несколько минут.' },
    { key: '7', q: 'Co, gdy urząd zmieni wzór druku?',
      a: 'Opis formularza jest związany z konkretnym plikiem wzoru. Gdy plik się zmieni, system to wykrywa i wstrzymuje formularz do ponownego sprawdzenia.',
      ru: 'Описание привязано к конкретному файлу образца; при изменении файла система это видит и останавливает форму до перепроверки.' },
    { key: '8', q: 'Jaki model i dlaczego?',
      a: 'Puste druki są publiczne, więc do ich analizy można użyć dowolnego modelu, także otwartego polskiego. Dane osobowe sprawdzają najpierw zwykłe reguły, a model działa lokalnie albo na danych po pseudonimizacji.',
      ru: 'Пустые бланки публичны: для их разбора годится любая модель, в том числе открытая польская; персональные данные сначала проверяют правила, модель локальная или на обезличенных данных.' },
    { key: '9', q: 'Co w demo jest prawdziwe?',
      a: 'Powiem to wprost. Działają: rozpoznanie pól, formularz online, przekazanie kodem QR, kontrola i wydruk na wzorze. Symulowane są: mObywatel, czytnik dokumentów i login.gov.pl. Dane są syntetyczne.',
      ru: 'Работает распознавание полей, онлайн-форма, обмен по QR, проверка и печать; имитируются mObywatel, сканер и вход; данные синтетические. (Главный агент правит под то, что построено.)' },
    { key: '0', q: 'Co powstało na hackathonie?',
      a: 'Badania, katalog formularzy i specyfikację przygotowałem wcześniej i jawnie to oznaczyłem. Kod aplikacji powstał tutaj, w ciągu 24 godzin; widać to w historii repozytorium.',
      ru: 'Исследование, каталог бланков и спецификация сделаны заранее и помечены; код написан здесь за 24 часа.' }
  ],

  /* Phrases for difficult moments (bottom of the answer panel). */
  phrases: [
    'Proszę powtórzyć pytanie.',
    'Czy dobrze rozumiem, że pytają Państwo o …?',
    'Nie wiem. Sprawdzimy to i odpowiemy po prezentacji.',
    'Dziękuję za to pytanie.'
  ],

  /* Labels for the measured numbers on the demo slides. Values come from
     metrics.json (null = not measured yet = number hidden). Max three words.
     Slide 3 shows digitise_seconds, fields_detected_pct, forms_digitised;
     slide 4 shows fill_seconds. */
  metricLabels: {
    digitise_seconds: { label: 'sekund na druk', suffix: '' },
    fields_detected_pct: { label: 'pól rozpoznanych', suffix: '%' },
    forms_digitised: { label: 'druków online', suffix: '' },
    fill_seconds: { label: 'sekund na wniosek', suffix: '' }
  }
};
