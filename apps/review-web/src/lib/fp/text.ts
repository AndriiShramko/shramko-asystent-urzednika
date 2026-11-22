// The Polish texts of the fill-and-print steps, word for word from the product design (FP-B, wave 10). These
// steps are a check of a Polish form by a Polish clerk, so they stay Polish whatever the page language; the
// containing elements carry lang="pl".
import type { Tag } from '../../ui/eform'

export const FP = {
  step: (n: number): string => `Krok ${n} z 6.`,
  eformHeading: 'Podgląd formularza elektronicznego',
  controlPreview: 'Podgląd kontrolny. Formularz produkcyjny wyświetla Generator Formularzy.',
  prevPage: 'Poprzednia strona',
  nextPage: 'Następna strona',
  pageOf: (i: number, n: number, title: string): string => `Strona ${i} z ${n}${title ? ': ' + title : ''}`,
  pageN: (i: number): string => `Strona ${i}`,
  choose: '– wybierz –',
  consents: 'Oświadczenia i zgody',
  consentGiven: (k: number, n: number): string => `zaznaczono ${k} z ${n}`,
  fileNote: 'Załącznik dodaje mieszkaniec w e-usłudze; w podglądzie pole jest nieaktywne.',
  required: 'wymagane',
  dictionary: (name: string): string => `Słownik: ${name}`,
  initialData: (key: string): string => `Dane inicjalne: ${key}`,
  validator: (v: string): string => `Walidacja: ${v}`,
  because: (answer: string): string => `Sekcja widoczna, ponieważ wybrano: „${answer}”.`,
  condUnread: 'Warunku pokazania nie odczytano; pole jest pokazane zawsze.',

  // step 4
  fillHeading: 'Próbne wypełnienie danymi demonstracyjnymi',
  banner: 'Dane demonstracyjne. Osoby są fikcyjne, wymyślone na potrzeby pokazu. Nie wpisuj tu prawdziwych danych.',
  qrStory: 'Kod QR zawiera wyłącznie dane demonstracyjne fikcyjnych osób. W prawdziwej e-usłudze dane pochodzą z rejestru PESEL i z danych zalogowanego użytkownika; tego połączenia w tej wersji nie ma.',
  scanSim: 'Zeskanuj kod QR (symulacja)',
  pickFromList: 'Wybierz osobę z listy demonstracyjnej',
  loaded: (first: string, last: string): string => `Wczytano dane demonstracyjne: ${first} ${last}.`,
  refused: 'Ten kod nie zawiera danych demonstracyjnych w znanym formacie. Strona przyjmuje tylko kody oznaczone jako demonstracyjne.',
  fillOne: 'Wypełnij formularz jednym kliknięciem',
  filled: (n: number, k: number, m: number, r: number): string =>
    `Wypełniono ${n} pól: ${k} z rejestru (tylko do odczytu), ${m} jako propozycja do sprawdzenia. Do uzupełnienia ręcznie: ${r}.`,
  tag: {
    pesel: 'Z rejestru PESEL – tylko do odczytu',
    mlpz: 'Z danych zalogowanego użytkownika – tylko do odczytu',
    proposal: 'Propozycja z danych demonstracyjnych – sprawdź'
  } as Record<Tag, string>,
  filledList: 'Wypełnione z danych demonstracyjnych',
  emptyList: 'Do uzupełnienia ręcznie',
  clear: 'Wyczyść dane',
  cleared: 'Dane usunięto z tej karty przeglądarki.',
  wrongOnPurpose: 'celowo błędna cyfra kontrolna PESEL – do pokazu walidacji',

  // step 5
  checkHeading: 'Sprawdzenie przed wydrukiem',
  checkButton: 'Sprawdź poprawność',
  missing: (n: number, list: string): string => `Brakuje ${n} wymaganych pól: ${list}.`,
  allGood: 'Wszystkie wymagane pola są wypełnione, a numery przeszły kontrolę.',
  notReady: 'Przed wydrukiem popraw pola z listy.',
  goTo: 'Przejdź do pola',
  noPlace: (n: number): string => `${n} pól nie ma miejsca na blankiecie; są wydrukowane na dodatkowej stronie.`,

  // step 2 addition: where on the paper
  whereHeading: 'Gdzie na papierze',
  whereToggle: 'Pokaż miejsca pól na papierze',
  pageChip: (p: number): string => `strona ${p}`,
  noBox: 'Miejsca na papierze nie ustalono',
  previewMissing: 'Podgląd druku niedostępny',

  // step 6
  printHeading: 'Wydruk',
  printPreview: 'Podgląd wydruku na oryginalnym blankiecie',
  printSheet: 'Drukuj na blankiecie',
  printEform: 'Drukuj formularz elektroniczny',
  printHint: 'Przed drukiem ustaw skalę 100 % (bez dopasowania do strony).',
  noPageImage: 'Dla tego formatu nie ma obrazu strony. Dostępny jest wydruk formularza elektronicznego.',

  // BL13 TRY-F: the progressive trial fill (one step open at a time, finished steps as one line)
  scanDone: 'Kod QR zeskanowany (symulacja).',
  scanAgain: 'Zeskanuj ponownie',
  changePerson: 'Zmień osobę',
  printNext: 'Formularz sprawdzony. Następny krok: wydruk.'
}
