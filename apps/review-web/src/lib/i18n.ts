import { pl } from '../i18n/pl'
import { en } from '../i18n/en'
import { es } from '../i18n/es'
import type { Dict } from '../i18n/pl'

export type Lang = 'pl' | 'en' | 'es'
export const LANGS: readonly Lang[] = ['pl', 'en', 'es']
export const DEFAULT_LANG: Lang = 'pl'

const dictionaries: Record<Lang, Record<string, string>> = { pl: pl as unknown as Dict, en, es }

export type Params = Record<string, string | number>

export function isLang(x: unknown): x is Lang {
  return typeof x === 'string' && (LANGS as readonly string[]).includes(x)
}

export function hasKey(lang: Lang, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(dictionaries[lang], key)
}

/** Our own text by code. A key missing in a language falls back to Polish, a key missing everywhere to the key. */
export function translate(lang: Lang, key: string, params?: Params): string {
  const raw = dictionaries[lang][key] ?? dictionaries.pl[key] ?? key
  if (!params) return raw
  return raw.replace(/\{(\w+)\}/g, (m, name: string) => (name in params ? String(params[name]) : m))
}

let current: Lang = DEFAULT_LANG

export function getLang(): Lang {
  return current
}

export function setLang(lang: Lang): void {
  current = lang
}

export function t(key: string, params?: Params): string {
  return translate(current, key, params)
}

/** Which of the three forms "one|few|many" a number takes. Polish: 1 pole, 2-4 pola (not 12-14), 5 pól. English
 * and Spanish: one, else many (their "few" form repeats "many"). */
export function pluralIndex(lang: Lang, n: number): 0 | 1 | 2 {
  const a = Math.abs(Math.trunc(n))
  if (a === 1) return 0
  if (lang !== 'pl') return 2
  const d = a % 10
  const dd = a % 100
  return d >= 2 && d <= 4 && !(dd >= 12 && dd <= 14) ? 1 : 2
}

/** A counted phrase: the key holds "one|few|many", each with {n}. */
export function tn(key: string, n: number, params: Params = {}): string {
  const forms = t(key, { ...params, n }).split('|')
  return forms[Math.min(pluralIndex(current, n), forms.length - 1)]
}

/** The language to start with: a stored choice, else Polish. The browser's own language is not used on purpose:
 * the specification fixes Polish as the default. */
export function initialLang(stored: string | null | undefined): Lang {
  return isLang(stored) ? stored : DEFAULT_LANG
}

export function dictionaryKeys(lang: Lang): string[] {
  return Object.keys(dictionaries[lang])
}
