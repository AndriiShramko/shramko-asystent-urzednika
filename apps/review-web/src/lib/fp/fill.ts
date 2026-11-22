// Which value of a demo record goes into which field. First the partner's own mechanism: a field whose
// defaultValue is an EXTERNAL_SYSTEM key (`PESEL.name`, `MLPZ.street`…) takes that attribute and is locked
// (initial data are read only). Then proposals the clerk must check: by the field's validator, its techName, or a
// few title patterns. Fields of another person, an attorney or a representative are never filled.
import { INPUT_TYPES, type ENode, type FormModel } from './form'
import { accountOf, extraOf, fullAddress, idCardOf, nipOf, peselOf, regonOf, type DemoRecord } from './family'

export type FillTag = 'pesel' | 'mlpz' | 'proposal'
export interface FillItem { id: string; value: string | string[]; tag: FillTag }

const norm = (s: string): string => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ł/g, 'l').trim()

/** Is the node about someone other than the person whose record this is? */
function otherPerson(n: ENode): boolean {
  for (let p: ENode | null = n; p; p = p.parent) {
    const t = norm(p.techName + '_' + p.title).replace(/\s+/g, '_')
    if (/inn(a|ej)_osob|pelnomoc|przedstawiciel|siedzib|urzad/.test(t)) return true
  }
  return false
}

/** The attribute of the record a partner key names (`PESEL.pesel`, `MLPZ.street`, `PESEL_ADDRESS.…`). */
export function externalValue(key: string, r: DemoRecord): string {
  const [block, attr] = key.split('.')
  if (!attr) return ''
  if (attr === 'pesel') return peselOf(r)
  const b = (r as unknown as Record<string, Record<string, string> | undefined>)[block]
  const v = b?.[attr]
  return typeof v === 'string' ? v : ''
}

const today = (): string => new Date().toISOString().slice(0, 10)

/** A proposal for a field without a partner key, or '' when the page has no honest guess. */
function proposal(n: ENode, r: DemoRecord): string | string[] {
  const t = norm(n.title)
  const tech = norm(n.techName)
  const m = r.MLPZ
  const isDate = n.type === 'DATEPICKER'
  const inDogSection = (() => { for (let p = n.parent; p; p = p.parent) if (/psa|psie|psow/.test(norm(p.techName + ' ' + p.title))) return true; return false })()
  // dog (set 07 style)
  if (/rasa psa/.test(t)) return extraOf(r, 'dog.breed')
  if (/data urodzenia psa/.test(t)) return extraOf(r, 'dog.born')
  if (/data szczepienia/.test(t)) return extraOf(r, 'dog.vaccinated')
  if (/pochodzenie psa/.test(t)) return extraOf(r, 'dog.origin')
  if (n.type === 'RADIO' && /oznakowania psa/.test(t) && extraOf(r, 'dog.chip') && n.options.includes('mikroprocesor')) return 'mikroprocesor'
  if (/oznakowania psa.*mikroprocesor/.test(t)) return extraOf(r, 'dog.chip')
  if (n.type === 'RADIO' && /^plec$/.test(t) && inDogSection) {
    const s = extraOf(r, 'dog.sex'); return s && n.options.includes(s) ? s : ''
  }
  if (/adres miejsca utrzymywania psa/.test(t)) return extraOf(r, 'dog.breed') ? fullAddress(r) : ''
  // identifiers by validator
  if (n.validation.includes('PESEL') || /^(numer )?pesel$/.test(t) || tech === 'numer_pesel' || tech === 'pesel') return peselOf(r)
  if (n.validation.includes('NIP') || /^nip$/.test(t)) return nipOf(r)
  if (n.validation.includes('REGON') || /^regon$/.test(t)) return regonOf(r)
  if (n.validation.includes('EPUAP') || /epuap/.test(t)) return extraOf(r, 'epuap')
  if (n.validation.includes('SERIAL_NUMBER_ID_CARD') || /seria i numer dowodu/.test(t)) return idCardOf(r)
  if (n.validation.includes('EMAIL') || /e-?mail/.test(t)) return m.email ?? ''
  if (/(nr|numer) rachunku/.test(t)) return accountOf(r)
  // the person
  if (/^imie i nazwisko|^nazwisko i imie/.test(t)) return `${m.name} ${m.surname}`
  if (/^nazwisko, imie/.test(t)) return `${m.surname} ${m.name}`
  if (tech === 'imie' || t === 'imie') return m.name
  if (tech === 'nazwisko' || t === 'nazwisko') return m.surname
  if (/^data urodzenia$/.test(t)) return r.PESEL.birthDate ?? ''
  if (/^miejsce urodzenia$/.test(t)) return r.PESEL.birthPlace ?? ''
  if (/data (wypelnienia|sporzadzenia)/.test(t) && isDate) return today()
  // the address
  if (tech === 'kod_pocztowy' || /^kod pocztowy$/.test(t)) return m.postCode
  if (tech === 'ulica' || /^ulica$/.test(t)) return m.street
  if (tech === 'numer_budynku' || /^(nr|numer) (domu|budynku)|^numer nieruchomosci/.test(t)) return m.building
  if (tech === 'numer_lokalu' || /^(nr|numer) (lokalu|mieszkania)$/.test(t)) return m.apartment
  if (tech === 'miejscowosc' || /^miejscowosc$/.test(t)) return m.place
  if (/^adres (zamieszkania|zameldowania|do korespondencji)$/.test(t) && (n.type === 'TEXTAREA' || n.type === 'TEXT_FIELD')) return fullAddress(r)
  if (/telefon/.test(t) || tech === 'numer_telefonu') return m.phoneNumber ?? ''
  // sport (set 09 style)
  if (/dyscyplin/.test(t) && n.type !== 'RADIO' && n.type !== 'CHECKBOX') return extraOf(r, 'discipline')
  return ''
}

/** The plan of one click: only empty fields that take text or one choice; nothing is overwritten. */
export function planFill(model: FormModel, r: DemoRecord, isEmpty: (id: string) => boolean,
  isVisible: (n: ENode) => boolean = () => true): FillItem[] {
  const out: FillItem[] = []
  for (const n of model.all) {
    // a hidden field (another country's address, another person) is not filled: the person did not choose it
    if (!isVisible(n)) continue
    if (!INPUT_TYPES.has(n.type) || n.type === 'FILE_UPLOADER' || n.type === 'CONSENT_SECTION') continue
    if (!isEmpty(n.id)) continue
    if (n.defaultValueType === 'EXTERNAL_SYSTEM' && typeof n.defaultValue === 'string') {
      const v = externalValue(n.defaultValue, r)
      if (v) out.push({ id: n.id, value: v, tag: n.defaultValue.startsWith('PESEL') ? 'pesel' : 'mlpz' })
      continue
    }
    if (otherPerson(n)) continue
    const v = proposal(n, r)
    if (n.type === 'SELECT' && typeof v === 'string' && v && n.options.length && !n.options.includes(v)) continue
    if (n.type === 'RADIO' && typeof v === 'string' && v && !n.options.includes(v)) continue
    if (v && (!Array.isArray(v) || v.length)) out.push({ id: n.id, value: v, tag: 'proposal' })
  }
  return out
}
