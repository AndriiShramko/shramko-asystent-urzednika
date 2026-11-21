import { hasKey, getLang } from './i18n'

export interface RawWarning {
  code?: string
  page?: number
  detail?: string
  field?: string
  candidate?: string
  [k: string]: unknown
}

export interface HeaderWarnings {
  count: number | null
  raw: string
  codes: string[]
}

/** `X-Converter-Warnings` carries "the count and the codes" (decision D19). The exact spelling is not fixed
 * yet, so the reader takes the first whole number as the count and every UPPER_CASE word as a code. */
export function parseWarningsHeader(value: string | null | undefined): HeaderWarnings | null {
  if (value === null || value === undefined || value.trim() === '') return null
  const num = /\b(\d+)\b/.exec(value)
  const codes: string[] = []
  for (const m of value.matchAll(/\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*\b/g)) {
    if (m[0].length >= 3 && !codes.includes(m[0])) codes.push(m[0])
  }
  return { count: num ? Number(num[1]) : null, codes, raw: value.trim() }
}

export interface WarningGroup {
  code: string
  known: boolean
  key: string
  items: RawWarning[]
}

/** Warnings grouped by code, in the order of first appearance. Groups of the same code are one explanation and
 * a list of places, so that eighty warnings of one kind are not eighty paragraphs. */
export function groupWarnings(list: readonly RawWarning[]): WarningGroup[] {
  const map = new Map<string, WarningGroup>()
  for (const w of list) {
    const code = typeof w.code === 'string' && w.code ? w.code : 'UNKNOWN'
    let g = map.get(code)
    if (!g) {
      const key = 'warn.' + code
      g = { code, known: hasKey(getLang(), key), key, items: [] }
      map.set(code, g)
    }
    g.items.push(w)
  }
  return [...map.values()]
}

export function placeOf(w: RawWarning): number | null {
  return typeof w.page === 'number' ? w.page : null
}
