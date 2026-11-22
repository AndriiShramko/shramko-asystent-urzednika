// BL13 TRY-F: the day of filing. A trial fill happens on a certain day, so the date of filing or signing takes
// today's date (local calendar, Polish form DD.MM.RRRR on paper). Only labels that name the filing date count;
// any other date (birth, vaccination, event) is content and never gets today's date.

const norm = (s: string): string => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ł/g, 'l')
  .replace(/[()*:._…]+/g, ' ').replace(/\s+/g, ' ').trim()

const pad = (n: number): string => String(n).padStart(2, '0')

/** Today in the form's own value format (yyyy-mm-dd), by the local calendar (not UTC: after midnight it is today). */
export function todayIso(now: Date = new Date()): string {
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

/** Today as written on Polish paper: DD.MM.RRRR. */
export function todayPl(now: Date = new Date()): string {
  return `${pad(now.getDate())}.${pad(now.getMonth() + 1)}.${now.getFullYear()}`
}

export type FilingKind = 'date' | 'placeDate'

/** Does this label (or techName) name the date of filling, filing or signing? `placeDate` = "miejscowość i data".
 * A label about a signature only, or about any other date, is null. */
export function filingKind(label: string): FilingKind | null {
  const t = norm(label).replace(/_/g, ' ')
  if (!t) return null
  if (/^(miejscowosc|miejsce)( i|,)? data$|^(miejscowosc|miejsce),? dnia$/.test(t)) return 'placeDate'
  if (/^(data|dnia|w dniu|dzien)$/.test(t)) return 'date'
  if (/^data (wypelnienia|zlozenia|sporzadzenia|podpisania|podpisu)( (wniosku|formularza|oswiadczenia|deklaracji|zgloszenia))?$/.test(t)) return 'date'
  if (/^data (wniosku|zgloszenia|oswiadczenia)$/.test(t)) return 'date'
  return null
}

/** BL13 review: a label that is only "data", "dnia", "w dniu" or "dzień". As the title of a FIELD it is more often a
 * content date (a column of a list, an event) than the day of filing: the converter leaves the paper's filing date
 * out of the e-form. Such a field takes today's date only inside a section about the signature or the declaration. */
export function isBareDate(label: string): boolean {
  return /^(data|dnia|w dniu|dzien)$/.test(norm(label).replace(/_/g, ' '))
}

/** Is this section title about signing or declaring (where a bare "Data" is the day of filing)? */
export function isSigningContext(title: string): boolean {
  return /(podpis|oswiadcz|data i miejsce|miejsce i data|miejscowosc i data)/.test(norm(title))
}
