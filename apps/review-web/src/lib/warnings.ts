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

// ---- Wave 11: the ready fix a remark carries (clerk-contract v1, written by the server lane CLERK-S).
// `applied`: the converter settled it itself, the clerk never sees it. `choice`: ready options, one click.
// `input`: the last resort, the clerk types. A remark without `fix` is treated as `input` (stated: false), except
// the kinds the contract plans as `applied` (NOTE_CODES): notes about how the conversion ran, nothing to settle.

export interface FixSet { pointer: string; value?: unknown; from?: string }
export interface FixSource { type: string; name?: string; page?: number; box?: [number, number, number, number]; anchor?: string; quote?: string }
export interface FixTarget { id: string; pointer?: string; label?: string; tab?: string }
export interface FixOption { label: string; value: string; current: boolean; set: FixSet[]; source?: FixSource }
export interface FixInput { label: string; set: FixSet[] }

interface FixBase { rule: string; text: string; target?: FixTarget; source?: FixSource }
export type Fix =
  | (FixBase & { kind: 'applied'; value?: string })
  | (FixBase & { kind: 'choice'; options: FixOption[]; input?: FixInput })
  | (FixBase & { kind: 'input'; input?: FixInput; stated: boolean })
  | (FixBase & { kind: 'note' })

/** Kinds the contract names as decided by the converter (planned `applied`): shown only in the jury view. */
export const NOTE_CODES: ReadonlySet<string> = new Set(['INFERRED_SHAPE', 'SECTION_SPLIT', 'STEP_NOTE_ADDED', 'OCR_USED',
  'MODEL_USED', 'MODEL_SKIPPED', 'MODEL_FALLBACK', 'INPUT_NOTE', 'MARKUP_IN_LABEL', 'APPLICANTS_ASSUMED',
  'SOLE_TRADER_AS_ENTITY', 'REPEATING_FLATTENED', 'HIDDEN_SHEET', 'ACTIVE_CONTENT'])

export function isNote(code: string): boolean { return NOTE_CODES.has(code) }

const isObj = (x: unknown): x is Record<string, unknown> => !!x && typeof x === 'object' && !Array.isArray(x)
const str = (x: unknown): string => (typeof x === 'string' ? x : '')

function setsOf(x: unknown): FixSet[] {
  if (!Array.isArray(x)) return []
  return x.filter(isObj).filter((s) => typeof s.pointer === 'string' && s.pointer.startsWith('/'))
    .map((s) => ({ pointer: s.pointer as string, value: s.value, from: typeof s.from === 'string' ? s.from : undefined }))
}

function sourceOf(x: unknown): FixSource | undefined {
  if (!isObj(x) || typeof x.type !== 'string') return undefined
  const b = x.box
  const box = Array.isArray(b) && b.length === 4 && b.every((n) => typeof n === 'number' && Number.isFinite(n)) ? (b as FixSource['box']) : undefined
  return { type: x.type, name: str(x.name) || undefined, page: typeof x.page === 'number' ? x.page : undefined, box,
    anchor: str(x.anchor) || undefined, quote: str(x.quote) || undefined }
}

function inputOf(x: unknown): FixInput | undefined {
  if (!isObj(x)) return undefined
  const set = setsOf(x.set)
  return set.length ? { label: str(x.label), set } : undefined
}

/** The fix of a remark in the contract's shape; anything the page cannot read safely falls back to `input`. */
export function fixOf(w: RawWarning): Fix {
  const code = typeof w.code === 'string' ? w.code : ''
  const raw = w.fix
  if (!isObj(raw)) return isNote(code) ? { kind: 'note', rule: '', text: '' } : { kind: 'input', rule: '', text: '', stated: false }
  const t = raw.target
  const target: FixTarget | undefined = isObj(t) && typeof t.id === 'string' && t.id
    ? { id: t.id, pointer: str(t.pointer) || undefined, label: str(t.label) || undefined, tab: str(t.tab) || undefined } : undefined
  const base: FixBase = { rule: str(raw.rule), text: str(raw.text), target, source: sourceOf(raw.source) }
  if (raw.kind === 'applied') return { ...base, kind: 'applied', value: str(raw.value) || undefined }
  const input = inputOf(raw.input)
  if (raw.kind === 'choice') {
    const options: FixOption[] = (Array.isArray(raw.options) ? raw.options : []).filter(isObj)
      .filter((o) => typeof o.label === 'string' && o.label.trim())
      .map((o) => ({ label: (o.label as string).trim(), value: str(o.value), current: o.current === true, set: setsOf(o.set), source: sourceOf(o.source) }))
    if (options.length >= 2) return { ...base, kind: 'choice', options, input }
  }
  return { ...base, kind: 'input', input, stated: true }
}

const unescapeToken = (s: string): string => s.replace(/~1/g, '/').replace(/~0/g, '~')

/** RFC 6901: replace the value at `pointer` inside `doc`. The path must exist up to the last step (a `set` never
 * builds containers); returns false, changing nothing, when it does not. */
export function setPointer(doc: unknown, pointer: string, value: unknown): boolean {
  const tokens = pointer.split('/').slice(1).map(unescapeToken)
  if (!tokens.length) return false
  let cur: unknown = doc
  for (const tok of tokens.slice(0, -1)) {
    if (Array.isArray(cur)) cur = /^\d+$/.test(tok) ? cur[Number(tok)] : undefined
    else if (isObj(cur)) cur = Object.prototype.hasOwnProperty.call(cur, tok) ? cur[tok] : undefined
    else return false
    if (cur === undefined || cur === null) return false
  }
  const last = tokens[tokens.length - 1]
  if (last === '__proto__' || last === 'constructor' || last === 'prototype') return false
  if (Array.isArray(cur)) {
    if (!/^\d+$/.test(last) || Number(last) >= cur.length) return false
    cur[Number(last)] = value
    return true
  }
  if (!isObj(cur)) return false
  cur[last] = value
  return true
}

/** The node a pointer writes into: the id of the deepest object on the path that has a string `id`, and the key of
 * that object the pointer changes. Null when the path does not exist. */
export function nodeAt(doc: unknown, pointer: string): { id: string; key: string } | null {
  const tokens = pointer.split('/').slice(1).map(unescapeToken)
  let cur: unknown = doc
  let found: { id: string; key: string } | null = null
  for (let i = 0; i < tokens.length; i++) {
    if (isObj(cur) && typeof cur.id === 'string' && cur.id && typeof cur.type === 'string') found = { id: cur.id, key: tokens[i] }
    const tok = tokens[i]
    if (Array.isArray(cur)) cur = /^\d+$/.test(tok) ? cur[Number(tok)] : undefined
    else if (isObj(cur)) cur = Object.prototype.hasOwnProperty.call(cur, tok) ? cur[tok] : undefined
    else break
    if (cur === undefined || cur === null) break
  }
  return found
}
