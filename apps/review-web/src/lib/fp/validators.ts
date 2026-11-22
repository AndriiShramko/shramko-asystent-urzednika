// The partner's validators (app/model/form.py Validator) checked on the page. Each returns null when the value
// passes, else a Polish sentence. An empty value is judged only by REQUIRED. Check digits are computed here; no
// identifier is written in this file.

export const digitsOf = (s: string): number[] => [...s].map((c) => c.charCodeAt(0) - 48)

/** PESEL check digit of the first 10 digits (weights 1-3-7-9). */
export function peselCheck(stem: string): number {
  const w = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
  const sum = digitsOf(stem.slice(0, 10)).reduce((a, d, i) => a + d * w[i], 0)
  return (10 - (sum % 10)) % 10
}

/** NIP check digit of the first 9 digits (weights 6-5-7-2-3-4-5-6-7, mod 11); 10 means no valid NIP exists. */
export function nipCheck(stem: string): number {
  const w = [6, 5, 7, 2, 3, 4, 5, 6, 7]
  return digitsOf(stem.slice(0, 9)).reduce((a, d, i) => a + d * w[i], 0) % 11
}

/** REGON check digit for a 9-digit (stem 8) or 14-digit (stem 13) number; 10 counts as 0. */
export function regonCheck(stem: string): number {
  const w = stem.length >= 13 ? [2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8] : [8, 9, 2, 3, 4, 5, 6, 7]
  const r = digitsOf(stem.slice(0, w.length)).reduce((a, d, i) => a + d * w[i], 0) % 11
  return r === 10 ? 0 : r
}

const charValue = (c: string): number => (/[0-9]/.test(c) ? c.charCodeAt(0) - 48 : c.toUpperCase().charCodeAt(0) - 55)

/** Check digit (4th character) of a Polish ID card number from its 3 letters and the 5 digits after the check. */
export function idCardCheck(letters: string, digits5: string): number {
  const chars = [...(letters + digits5)]
  const w = [7, 3, 1, 7, 3, 1, 7, 3]
  return chars.reduce((a, c, i) => a + charValue(c) * w[i], 0) % 10
}

/** The remainder mod 97 of a long digit string. */
export function mod97(s: string): number {
  let r = 0
  for (const c of s) r = (r * 10 + (c.charCodeAt(0) - 48)) % 97
  return r
}

const compact = (v: string): string => v.replace(/[\s-]/g, '')

export type Check = (value: string) => string | null

export const CHECKS: Record<string, Check> = {
  PESEL: (v) => {
    const s = compact(v)
    if (!/^\d{11}$/.test(s)) return 'Numer PESEL powinien mieć 11 cyfr.'
    return peselCheck(s) === Number(s[10]) ? null : 'Numer PESEL ma błędną cyfrę kontrolną.'
  },
  NIP: (v) => {
    const s = compact(v).replace(/^PL/i, '')
    if (!/^\d{10}$/.test(s)) return 'Numer NIP powinien mieć 10 cyfr.'
    const c = nipCheck(s)
    return c !== 10 && c === Number(s[9]) ? null : 'Numer NIP ma błędną cyfrę kontrolną.'
  },
  REGON: (v) => {
    const s = compact(v)
    if (!/^(\d{9}|\d{14})$/.test(s)) return 'Numer REGON powinien mieć 9 albo 14 cyfr.'
    if (s.length === 14 && regonCheck(s.slice(0, 8)) !== Number(s[8])) return 'Numer REGON ma błędną cyfrę kontrolną.'
    return regonCheck(s.slice(0, s.length - 1)) === Number(s[s.length - 1]) ? null : 'Numer REGON ma błędną cyfrę kontrolną.'
  },
  ZIP_CODE: (v) => (/^\d{2}-\d{3}$/.test(v.trim()) ? null : 'Kod pocztowy powinien mieć postać 00-000.'),
  EMAIL: (v) => (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()) ? null : 'Adres e-mail powinien mieć postać nazwa@domena.pl.'),
  EPUAP: (v) => (/^\/[^/\s]+\/[^/\s]+$/.test(v.trim()) ? null : 'Adres skrzynki ePUAP powinien mieć postać /nazwa/skrytka.'),
  ADE: (v) => (/^AE:PL-\d{5}-\d{5}-[A-Z]{5}-\d{2}$/i.test(v.trim()) ? null
    : 'Adres do doręczeń elektronicznych powinien mieć postać AE:PL-00000-00000-AAAAA-00.'),
  SERIAL_NUMBER_ID_CARD: (v) => {
    const s = compact(v).toUpperCase()
    if (!/^[A-Z]{3}\d{6}$/.test(s)) return 'Seria i numer dowodu osobistego powinny mieć postać ABC123456.'
    return idCardCheck(s.slice(0, 3), s.slice(4)) === Number(s[3]) ? null : 'Seria i numer dowodu osobistego mają błędną cyfrę kontrolną.'
  }
}

export const REQUIRED_MSG = 'To pole jest wymagane.'

/** The first failing message for a value under the field's validators, or null. */
export function validate(value: string, validation: string[]): string | null {
  const empty = !value.trim()
  if (empty) return validation.includes('REQUIRED') ? REQUIRED_MSG : null
  for (const v of validation) {
    const check = CHECKS[v]
    if (check) {
      const msg = check(value)
      if (msg) return msg
    }
  }
  return null
}
