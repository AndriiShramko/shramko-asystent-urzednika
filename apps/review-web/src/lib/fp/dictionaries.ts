// Entries the page offers for the partner's dictionaries (the Generator binds the full lists itself). The field
// stays free text with these as suggestions, so an entry missing here never blocks typing.
const KRAJE = ['Polska', 'Niemcy', 'Czechy', 'Słowacja', 'Ukraina', 'Białoruś', 'Litwa', 'Łotwa', 'Estonia',
  'Austria', 'Francja', 'Hiszpania', 'Włochy', 'Holandia', 'Belgia', 'Dania', 'Szwecja', 'Norwegia', 'Irlandia',
  'Wielka Brytania', 'Stany Zjednoczone', 'Kanada']

const WOJEWODZTWA = ['dolnośląskie', 'kujawsko-pomorskie', 'lubelskie', 'lubuskie', 'łódzkie', 'małopolskie',
  'mazowieckie', 'opolskie', 'podkarpackie', 'podlaskie', 'pomorskie', 'śląskie', 'świętokrzyskie',
  'warmińsko-mazurskie', 'wielkopolskie', 'zachodniopomorskie']

export function dictionaryEntries(name: string): string[] {
  if (name === 'Kraje') return KRAJE
  if (/^TERYT/i.test(name)) return WOJEWODZTWA
  return []
}
