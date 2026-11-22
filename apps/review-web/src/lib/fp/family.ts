// The invented household of the demo (FP-B section 3): the Przykładowski family of Bydgoszcz. Every identifier
// with a check digit is kept as a STEM here and completed at run time (PESEL, NIP, REGON, ID card, bank account);
// no full identifier is written in any file. Addresses, phones and e-mails are not real (example.com, +48 000…).
import { idCardCheck, mod97, nipCheck, peselCheck, regonCheck } from './validators'

export interface DemoRecord {
  schemat: 'sau-demo-osoba/1'
  zrodlo: 'DEMO'
  uwaga: string
  PESEL: Record<string, string>
  PESEL_ADDRESS: Record<string, string>
  MLPZ: Record<string, string>
  extra: Record<string, unknown>
  /** this person's PESEL check digit is wrong on purpose, so step 5 can show the red message */
  wrongOnPurpose?: boolean
}

const ADDR12 = { street: 'Przykładowa', building: '12', apartment: '4' }
const ADDR14 = { street: 'Przykładowa', building: '14', apartment: '' }

function person(p: {
  stem: string; name: string; surname: string; birthDate: string; birthPlace: string; sex: string; marital: string
  familyName: string; father: [string, string]; mother: [string, string]; addr: typeof ADDR12
  phone?: string; email?: string; extra?: Record<string, unknown>; wrong?: boolean
}): DemoRecord {
  return {
    schemat: 'sau-demo-osoba/1',
    zrodlo: 'DEMO',
    uwaga: 'Dane demonstracyjne, osoba fikcyjna',
    PESEL: {
      peselStem: p.stem, name: p.name, secondName: '', surname: p.surname, birthDate: p.birthDate, birthPlace: p.birthPlace,
      birthCountry: 'Polska', citizenship: 'polskie', sex: p.sex, maritalStatus: p.marital, familyName: p.familyName,
      fatherName: p.father[0], fatherSurname: p.father[1], motherName: p.mother[0], motherSurname: p.mother[1]
    },
    PESEL_ADDRESS: {
      permanentAddressVoivodeship: 'kujawsko-pomorskie', permanentAddressDistrict: 'Bydgoszcz',
      permanentAddressCommunity: 'Bydgoszcz', permanentAddressPlace: 'Bydgoszcz', permanentAddressStreetType: 'ul.',
      permanentAddressStreet: p.addr.street, permanentAddressHouseNumber: p.addr.building,
      permanentAddressApartmentNumber: p.addr.apartment, permanentAddressPostalCode: '85-999'
    },
    MLPZ: {
      name: p.name, surname: p.surname, phoneNumber: p.phone ?? '', email: p.email ?? '', country: 'Polska',
      voivodeship: 'kujawsko-pomorskie', community: 'Bydgoszcz', place: 'Bydgoszcz', postCode: '85-999',
      street: p.addr.street, building: p.addr.building, apartment: p.addr.apartment
    },
    extra: p.extra ?? {},
    ...(p.wrong ? { wrongOnPurpose: true } : {})
  }
}

export const HOUSEHOLD: DemoRecord[] = [
  person({ stem: '8403150001', name: 'Tomasz', surname: 'Przykładowski', birthDate: '1984-03-15', birthPlace: 'Bydgoszcz',
    sex: 'mężczyzna', marital: 'żonaty', familyName: 'Przykładowski', father: ['Henryk', 'Przykładowski'], mother: ['Helena', 'Przykładowska'],
    addr: ADDR12, phone: '+48 000 000 101', email: 'tomasz.przykladowski@example.com',
    extra: { idCardStem: 'ZZZ00101', firm: { name: 'Przykładowe Usługi Brukarskie Tomasz Przykładowski', nipStem: '554000010', regonStem: '34000001' },
      bank: { sortStem: '9999000', account: '0000000000000101' }, vehicle: { plate: 'CB DEMO1', make: 'DEMO', model: 'Kombi', year: 2019 } } }),
  person({ stem: '8607220002', name: 'Anna', surname: 'Przykładowska', birthDate: '1986-07-22', birthPlace: 'Toruń',
    sex: 'kobieta', marital: 'zamężna', familyName: 'Wzorowska', father: ['Marek', 'Wzorowski'], mother: ['Ewa', 'Wzorowska'],
    addr: ADDR12, phone: '+48 000 000 102', email: 'anna.przykladowska@example.com',
    extra: { idCardStem: 'ZZZ00102', epuap: '/przykladowska/SkrytkaESP' } }),
  person({ stem: '1125090004', name: 'Zofia', surname: 'Przykładowska', birthDate: '2011-05-09', birthPlace: 'Bydgoszcz',
    sex: 'kobieta', marital: 'panna', familyName: 'Przykładowska', father: ['Tomasz', 'Przykładowski'], mother: ['Anna', 'Przykładowska'],
    addr: ADDR12, extra: { club: 'UKS Delfin Przykładowy Bydgoszcz', discipline: 'pływanie', coach: 'Jerzy Wzorek' } }),
  person({ stem: '1821120003', name: 'Kacper', surname: 'Przykładowski', birthDate: '2018-01-12', birthPlace: 'Bydgoszcz',
    sex: 'mężczyzna', marital: 'kawaler', familyName: 'Przykładowski', father: ['Tomasz', 'Przykładowski'], mother: ['Anna', 'Przykładowska'],
    addr: ADDR12, wrong: true }),
  person({ stem: '5311300006', name: 'Helena', surname: 'Przykładowska', birthDate: '1953-11-30', birthPlace: 'Inowrocław',
    sex: 'kobieta', marital: 'wdowa', familyName: 'Wzorcowa', father: ['Jan', 'Wzorcowy'], mother: ['Maria', 'Wzorcowa'],
    addr: ADDR14, phone: '+48 000 000 105', email: 'helena.przykladowska@example.com',
    extra: { idCardStem: 'ZZZ00103', dog: { breed: 'owczarek kaukaski', sex: 'suka', born: '2021-04-10', vaccinated: '2026-03-02',
      chip: '616 000 000 000 101', origin: 'hodowla Przykładowy Gród' } } })
]

/** Read a scanned or chosen record; only the demo schema with zrodlo DEMO is accepted (else null). */
export function parseDemoRecord(text: string): DemoRecord | null {
  try {
    const r = JSON.parse(text) as Partial<DemoRecord>
    if (!r || r.schemat !== 'sau-demo-osoba/1' || r.zrodlo !== 'DEMO') return null
    if (!r.PESEL || typeof r.PESEL !== 'object' || !r.MLPZ || typeof r.MLPZ !== 'object') return null
    return { PESEL_ADDRESS: {}, extra: {}, uwaga: '', ...r } as DemoRecord
  } catch {
    return null
  }
}

// ---- identifiers completed at run time
export function peselOf(r: DemoRecord): string {
  const stem = r.PESEL.peselStem ?? ''
  if (!/^\d{10}$/.test(stem)) return ''
  const d = peselCheck(stem)
  return stem + (r.wrongOnPurpose ? (d + 1) % 10 : d)
}

const ex = (r: DemoRecord, path: string): unknown =>
  path.split('.').reduce<unknown>((o, k) => (o && typeof o === 'object' ? (o as Record<string, unknown>)[k] : undefined), r.extra)
const exs = (r: DemoRecord, path: string): string => { const v = ex(r, path); return typeof v === 'string' || typeof v === 'number' ? String(v) : '' }

export function nipOf(r: DemoRecord): string {
  const s = exs(r, 'firm.nipStem')
  if (!/^\d{9}$/.test(s)) return ''
  const c = nipCheck(s)
  return c === 10 ? '' : s + c
}
export function regonOf(r: DemoRecord): string {
  const s = exs(r, 'firm.regonStem')
  return /^\d{8}$/.test(s) ? s + regonCheck(s) : ''
}
export function idCardOf(r: DemoRecord): string {
  const s = exs(r, 'idCardStem')
  return /^[A-Z]{3}\d{5}$/.test(s) ? s.slice(0, 3) + idCardCheck(s.slice(0, 3), s.slice(3)) + s.slice(3) : ''
}
/** A full NRB (26 digits, grouped) from the sort-code stem (7 digits) and the 16-digit account part. */
export function accountOf(r: DemoRecord): string {
  const sort = exs(r, 'bank.sortStem')
  const acc = exs(r, 'bank.account')
  if (!/^\d{7}$/.test(sort) || !/^\d{16}$/.test(acc)) return ''
  const w = [3, 9, 7, 1, 3, 9, 7]
  const sum = [...sort].reduce((a, c, i) => a + Number(c) * w[i], 0)
  const bban = sort + ((10 - (sum % 10)) % 10) + acc
  const check = String(98 - mod97(bban + '252100')).padStart(2, '0')
  const nrb = check + bban
  return nrb.replace(/(\d{2})(\d{4})(\d{4})(\d{4})(\d{4})(\d{4})(\d{4})/, '$1 $2 $3 $4 $5 $6 $7')
}

export function extraOf(r: DemoRecord, path: string): string { return exs(r, path) }

export function fullAddress(r: DemoRecord): string {
  const m = r.MLPZ
  const flat = m.apartment ? ` m. ${m.apartment}` : ''
  return `ul. ${m.street} ${m.building}${flat}, ${m.postCode} ${m.place}`
}
