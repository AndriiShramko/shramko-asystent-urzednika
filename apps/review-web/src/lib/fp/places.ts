// Places of the fields on the paper: the answer of POST /v1/forms/preview (FP-contract.md, wave 10) joined with
// the ledger of /convert?report=1 by candidate id. Boxes are in pt, origin top left. Nothing is guessed: a field
// whose row or place is missing has no place.
import type { Sidecar } from '../model'
import type { PlaceInk } from './ink'
import { filingKind } from './today'

export type Box = [number, number, number, number]
export interface PlaceOption { text: string; mark?: string; blank?: string }
export interface Place {
  page: number
  kind: string
  box?: Box
  anchor?: string
  label?: string
  cells?: number
  lines?: number
  mask?: string
  group?: string
  section?: string
  options?: PlaceOption[]
}
export interface PreviewPage { n: number; w: number; h: number; source?: string; img?: { media_type: string; data: string; width_px?: number; height_px?: number } }
export interface Preview { page_images: string; pages: PreviewPage[]; places: Record<string, Place>; input_sha256?: string }

export interface LedgerRow { candidate: string; fate: string; field?: string; section?: string; into?: string; reason?: string }

const isBox = (b: unknown): b is Box => Array.isArray(b) && b.length === 4 && b.every((x) => typeof x === 'number' && Number.isFinite(x))

/** The preview answer, or null when it is not in the contract's shape. */
export function parsePreview(x: unknown): Preview | null {
  if (!x || typeof x !== 'object') return null
  const o = x as Record<string, unknown>
  if (!Array.isArray(o.pages) || !o.places || typeof o.places !== 'object') return null
  const pages: PreviewPage[] = []
  for (const p of o.pages as Record<string, unknown>[]) {
    if (typeof p?.n !== 'number' || typeof p.w !== 'number' || typeof p.h !== 'number') return null
    const img = p.img as PreviewPage['img'] | undefined
    pages.push({ n: p.n, w: p.w, h: p.h, source: typeof p.source === 'string' ? p.source : undefined,
      img: img && typeof img.data === 'string' && typeof img.media_type === 'string' ? img : undefined })
  }
  const places: Record<string, Place> = {}
  for (const [k, v] of Object.entries(o.places as Record<string, Record<string, unknown>>)) {
    if (!v || typeof v.page !== 'number') continue
    places[k] = {
      page: v.page,
      kind: typeof v.kind === 'string' ? v.kind : '',
      box: isBox(v.box) ? v.box : undefined,
      anchor: typeof v.anchor === 'string' ? v.anchor : undefined,
      label: typeof v.label === 'string' ? v.label : undefined,
      cells: typeof v.cells === 'number' ? v.cells : undefined,
      lines: typeof v.lines === 'number' ? v.lines : undefined,
      mask: typeof v.mask === 'string' ? v.mask : undefined,
      group: typeof v.group === 'string' ? v.group : undefined,
      section: typeof v.section === 'string' ? v.section : undefined,
      options: Array.isArray(v.options) ? (v.options as PlaceOption[]).filter((op) => typeof op?.text === 'string') : undefined
    }
  }
  return { page_images: typeof o.page_images === 'string' ? o.page_images : '', pages, places,
    input_sha256: typeof o.input_sha256 === 'string' ? o.input_sha256 : undefined }
}

export function ledgerRows(sidecar: Sidecar | null): LedgerRow[] {
  const meta = (sidecar?.meta ?? {}) as Record<string, unknown>
  const ledger = (meta.ledger ?? (sidecar as Record<string, unknown> | null)?.ledger) as { rows?: unknown } | undefined
  const rows = Array.isArray(ledger?.rows) ? ledger.rows : []
  return rows.filter((r): r is LedgerRow => !!r && typeof (r as LedgerRow).candidate === 'string' && typeof (r as LedgerRow).fate === 'string')
}

/** The attribute of the person a standard-section place stands for, read from the paper's own label. */
export type Attr = 'fullname' | 'fullname_rev' | 'name' | 'surname' | 'pesel' | 'postCode' | 'street' | 'building' | 'apartment' |
  'place' | 'address' | 'phone' | 'email'

const norm = (s: string): string => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ł/g, 'l').replace(/\s+/g, ' ').trim()

export function attrOfLabel(label: string): Attr | null {
  const t = norm(label)
  if (/nazwisko,? imie/.test(t)) return 'fullname_rev'
  if (/imie i nazwisko|imie, nazwisko|imiona i nazwisko/.test(t)) return 'fullname'
  if (/^imie/.test(t)) return 'name'
  if (/^nazwisko/.test(t)) return 'surname'
  if (/pesel/.test(t)) return 'pesel'
  if (/kod pocztowy/.test(t)) return 'postCode'
  if (/ulica/.test(t)) return 'street'
  if (/(nr|numer) (domu|budynku)/.test(t)) return 'building'
  if (/(nr|numer) (lokalu|mieszkania)/.test(t)) return 'apartment'
  if (/miejscowosc/.test(t)) return 'place'
  if (/^adres/.test(t) && !/e-?mail|ePUAP|skrzynk/i.test(t)) return 'address'
  if (/telefon|nr tel/.test(t)) return 'phone'
  if (/e-?mail/.test(t)) return 'email'
  return null
}

/** Only these standard sections print: the person and their address and contact. */
export function standardPrints(section: string): boolean {
  const s = section.replace(/^standard\//, '')
  return s === 'twoje_dane' || s.startsWith('adres') || s === 'dane_do_kontaktu'
}

export interface Joined {
  /** form field id -> its candidate and place */
  byField: Map<string, { cid: string; place: Place }>
  /** standard-section places with the attribute their label names */
  standard: { cid: string; section: string; place: Place; attr: Attr | null }[]
  /** candidate id -> form field id (for a click on a box) */
  fieldOf: Map<string, string>
  /** BL13 TRY-F: the paper's own place of the filing date (left out of the form: the e-service dates itself);
   * the print writes today's date above its line. A signature place is never one of them. */
  dates?: { cid: string; place: Place; kind: 'date' | 'placeDate' }[]
}

export function joinPlaces(rows: LedgerRow[], pv: Preview): Joined {
  const byField = new Map<string, { cid: string; place: Place }>()
  const standard: Joined['standard'] = []
  const fieldOf = new Map<string, string>()
  const dates: NonNullable<Joined['dates']> = []
  for (const r of rows) {
    const place = pv.places[r.candidate]
    if (!place) continue
    if (r.fate === 'FIELD' && r.field) {
      if (!byField.has(r.field)) byField.set(r.field, { cid: r.candidate, place })
      fieldOf.set(r.candidate, r.field)
      for (const o of place.options ?? []) if (o.mark) fieldOf.set(o.mark, r.field)
    } else if (r.fate === 'STANDARD' && r.section) {
      standard.push({ cid: r.candidate, section: r.section, place, attr: place.label ? attrOfLabel(place.label) : null })
    } else if (r.fate === 'LEFT_OUT' && place.kind !== 'signature' && place.kind !== 'office_use' && r.reason !== 'OFFICE_USE' && place.label) {
      const kind = filingKind(place.label)
      if (kind) dates.push({ cid: r.candidate, place, kind })
    }
  }
  return { byField, standard, fieldOf, dates }
}

// ---- print math (pt): where a value goes in its place
// A hand does not write ON a line, it writes just above it. So the baseline of every value sits GAP above the top
// of the rule it belongs to. Where the rule is comes from the ink of the page picture (lib/fp/ink.ts) when the
// browser could read it; without it, from the box alone with the measured habits of the finder's boxes.

export interface Glyph { left: number; top: number; text: string; size: number; width?: number; center?: boolean }

/** Where the baseline sits below the top of a line box of line-height 1 (Arial/Liberation), in em. */
export const BASE = 0.85
/** Distance between the baseline of a value and the top of the rule under it, pt. */
export const GAP = 1.5
/** Cap height of Arial in em: how far a value reaches above its baseline. */
export const CAP = 0.72
/** The dots of a leader sit this share of the height of their character box above its bottom (measured on the
 * task sets: 0.29 to 0.36, top of the ink). */
export const LEADER_RISE = 0.34
const MIN_SIZE = 7
const MAX_SIZE = 11
const clampSize = (s: number): number => Math.max(MIN_SIZE, Math.min(MAX_SIZE, s))

// Advance widths of Arial (and the metric-compatible Liberation Sans) in 1/1000 em.
const W_LOWER: Record<string, number> = { a: 556, b: 556, c: 500, d: 556, e: 556, f: 278, g: 556, h: 556, i: 222, j: 222, k: 500, l: 222,
  m: 833, n: 556, o: 556, p: 556, q: 556, r: 333, s: 500, t: 278, u: 556, v: 500, w: 722, x: 500, y: 500, z: 500 }
const W_UPPER: Record<string, number> = { A: 667, B: 667, C: 722, D: 722, E: 667, F: 611, G: 778, H: 722, I: 278, J: 500, K: 667, L: 556,
  M: 833, N: 722, O: 778, P: 667, Q: 778, R: 722, S: 667, T: 611, U: 722, V: 667, W: 944, X: 667, Y: 667, Z: 611 }
const W_OTHER: Record<string, number> = { ' ': 278, '.': 278, ',': 278, ':': 278, ';': 278, '/': 278, '\\': 278, '!': 278, '|': 260, "'": 191,
  '"': 355, '-': 333, '(': 333, ')': 333, '[': 278, ']': 278, '+': 584, '=': 584, '<': 584, '>': 584, '@': 1015, '&': 667, '%': 889,
  '#': 556, '_': 556, '*': 389, '?': 556, '…': 1000, '–': 556, '—': 1000, '„': 333, '”': 333, 'ł': 222, 'Ł': 556 }
function advance(ch: string): number {
  if (ch >= '0' && ch <= '9') return 556
  const direct = W_OTHER[ch] ?? W_LOWER[ch] ?? W_UPPER[ch]
  if (direct !== undefined) return direct
  const base = ch.normalize('NFD')[0] ?? ch // a letter with a diacritic is as wide as its base letter
  return W_LOWER[base] ?? W_UPPER[base] ?? 600
}
/** The width of a text in pt at a size, by the advance widths of Arial. */
export const textWidth = (text: string, size: number): number => { let w = 0; for (const ch of text) w += advance(ch); return (w * size) / 1000 }

/** The largest size from `start` down to MIN_SIZE (steps of 0.5) at which the text is no wider than `room`. */
function fitSize(text: string, room: number, start: number): number {
  let size = clampSize(start)
  while (size > MIN_SIZE && textWidth(text, size) > room) size -= 0.5
  return size
}
/** The longest beginning of a text that fits `room` at `size`, ending in an ellipsis. */
function cut(text: string, room: number, size: number): string {
  const chars = [...text]
  while (chars.length && textWidth(chars.join('') + '…', size) > room) chars.pop()
  return chars.join('').trimEnd() + '…'
}
/** Words wrapped into lines no wider than `room` at `size` (a single word longer than the room stays whole). */
function wrap(text: string, room: number, size: number): string[] {
  const lines: string[] = []
  let cur = ''
  for (const word of text.split(/\s+/).filter(Boolean)) {
    const next = cur ? cur + ' ' + word : word
    if (cur && textWidth(next, size) > room) { lines.push(cur); cur = word } else cur = next
  }
  if (cur) lines.push(cur)
  return lines
}

type Laid = { glyphs: Glyph[]; fits: boolean }

/** One line of text with its baseline at `baseline`: shrinks to the room; a text too long even at the smallest
 * size is cut with an ellipsis (it never runs over what stands next) and reported as not fitting. */
function oneLine(left: number, baseline: number, text: string, room: number, start: number): Laid {
  const size = fitSize(text, room, start)
  const fits = textWidth(text, size) <= room
  return { glyphs: [{ left, top: baseline - size * BASE, text: fits ? text : cut(text, room, size), size }], fits }
}

/** Lines of text on the given baselines, wrapped by words; shrinks until it fits the lines; the last line is cut
 * when even the smallest size needs more lines. */
function manyLines(left: number, baselines: number[], text: string, room: number, start: number): Laid {
  let size = clampSize(start)
  let lines = wrap(text, room, size)
  const tooWide = (): boolean => lines.some((ln) => textWidth(ln, size) > room)
  while (size > MIN_SIZE && (lines.length > baselines.length || tooWide())) { size -= 0.5; lines = wrap(text, room, size) }
  const fits = lines.length <= baselines.length && !tooWide()
  if (lines.length > baselines.length) {
    const rest = lines.slice(baselines.length - 1).join(' ')
    lines = [...lines.slice(0, baselines.length - 1), cut(rest, room, size)]
  }
  lines = lines.map((ln) => (textWidth(ln, size) > room ? cut(ln, room, size) : ln))
  return { glyphs: lines.map((ln, i) => ({ left, top: baselines[i] - size * BASE, text: ln, size })), fits }
}

/** The rule a one-line value sits on: the lowest thin band of ink inside the box (a little slack below it), else
 * the nearest one within the searched margin. */
function ruleOf(ink: PlaceInk | undefined, y0: number, y1: number): { top: number; clear: number } | null {
  if (!ink || !ink.rules.length) return null
  let best = -1
  for (let i = 0; i < ink.rules.length; i++) if (ink.rules[i].top >= y0 - 1 && ink.rules[i].top <= y1 + 0.75) best = i
  if (best < 0) {
    let d = Infinity
    for (let i = 0; i < ink.rules.length; i++) { const k = Math.abs(ink.rules[i].top - y1); if (k < d) { d = k; best = i } }
  }
  return { top: ink.rules[best].top, clear: ink.clear[best] ?? Infinity }
}

/** The size a value may have under `clear` pt of free height above its rule: its capitals stay off what is above. */
const sizeUnder = (clear: number, wish: number): number => clampSize(Math.min(wish, (clear - GAP - 0.5) / CAP))

/** Glyphs that print `text` in a place; `fits` false when the value does not fit even at the smallest size (it is
 * then cut with an ellipsis, and the caller prints the whole value on the extra page). */
export function layoutText(place: Place, text: string, ink?: PlaceInk): Laid {
  const b = place.box
  if (!b || !text) return { glyphs: [], fits: true }
  const [x0, y0, x1, y1] = b
  const w = Math.max(1, x1 - x0)
  const hgt = Math.max(0, y1 - y0)

  if (place.kind === 'comb' && place.cells && place.cells > 0) {
    // one character per box, centred in ITS box: the boxes seen on the picture when their count agrees with the
    // finder's, else equal parts of the box
    const seen = ink && ink.cells.length === place.cells ? ink.cells : null
    const cells: [number, number][] = seen ?? Array.from({ length: place.cells }, (_, i) => [x0 + (i * w) / place.cells!, x0 + ((i + 1) * w) / place.cells!])
    const cw = Math.min(...cells.map(([a, c]) => c - a))
    const chars = [...text.replace(/\s/g, '')]
    const size = clampSize(Math.min(hgt || 10, cw) * 0.8)
    const base = (y0 + y1) / 2 + (size * CAP) / 2
    const glyphs = chars.slice(0, cells.length).map((c, i) => ({ left: cells[i][0], top: base - size * BASE, text: c, size, width: cells[i][1] - cells[i][0], center: true }))
    return { glyphs, fits: chars.length <= cells.length }
  }

  if (place.kind === 'line_block' && place.lines && place.lines > 1) {
    // every line of the block has its own rule: the rules seen inside the box, else the lines the box implies (the
    // box runs from the top of the first row of dots to the bottom of the last one)
    const seen = (ink?.rules ?? []).filter((r) => r.top >= y0 - 1 && r.top <= y1 + 0.75).map((r) => r.top)
    let tops = seen
    if (tops.length < 2) {
      const row = Math.min(12, (hgt / place.lines) * 0.75)
      const pitch = (hgt - row) / (place.lines - 1)
      tops = Array.from({ length: place.lines }, (_, i) => y1 - row * LEADER_RISE - (place.lines! - 1 - i) * pitch)
    }
    const pitch = (tops[tops.length - 1] - tops[0]) / (tops.length - 1)
    const firstClear = ink && seen.length >= 2 ? ink.clear[ink.rules.findIndex((r) => r.top === seen[0])] ?? Infinity : Infinity
    const start = sizeUnder(Math.min(pitch - 1, firstClear), 10)
    return manyLines(x0 + 2, tops.map((t) => t - GAP), text, w - 4, start)
  }

  if (place.kind === 'cell') return layoutCell(place, text, ink)

  // leader, blank in a sentence, widget and the rest: one line just above its rule
  const rule = ruleOf(ink, y0, y1)
  const top = rule ? rule.top : hgt > 0 ? y1 - hgt * LEADER_RISE : y1
  const wish = hgt > 0 ? Math.max(9, Math.min(MAX_SIZE, hgt + 1)) : 10
  return oneLine(x0 + 2, top - GAP, text, w - 4, rule ? sizeUnder(rule.clear, wish) : wish)
}

/** A table cell: the value stays inside the cell with a margin and never touches the cell's own printed label.
 * With the label seen on the picture: under the label when there is room for a line, else after it on the label's
 * own baseline; a high cell takes several lines. Without the picture: under the label in the lower part. */
function layoutCell(place: Place, text: string, ink?: PlaceInk): Laid {
  const [x0, y0, x1, y1] = place.box!
  const hgt = y1 - y0
  const PADX = 3
  const bottom = y1 - Math.min(3, Math.max(2, hgt * 0.12)) // the lowest baseline: a margin above the lower border
  const lab = ink?.label
  if (lab) {
    const [lx0, , lx1, ly1] = lab.box
    const below = y1 - ly1
    const left = Math.max(x0 + PADX, Math.min(lx0, x0 + 12))
    const room = x1 - PADX - left
    if (below >= 10) {
      // under the label: one line in the middle of the free part, several lines when the cell is high
      const lines = Math.max(1, Math.floor((below - 3) / 11))
      if (lines > 1 && textWidth(text, 10) > room) {
        const first = ly1 + 2 + 10 * CAP
        return manyLines(left, Array.from({ length: lines }, (_, i) => first + i * 11.5), text, room, 10)
      }
      const size = fitSize(text, room, Math.min(10, (below - 3.5) / CAP))
      const base = Math.min(bottom, (ly1 + y1) / 2 + (size * CAP) / 2)
      return oneLine(left, base, text, room, size)
    }
    const after = lx1 + 5
    const roomAfter = x1 - PADX - after
    const sizeAfter = Math.min(10, (lab.baseline - y0 - 1.5) / CAP)
    if (roomAfter >= 24 && textWidth(text, MIN_SIZE) <= roomAfter) return oneLine(after, lab.baseline, text, roomAfter, sizeAfter)
    // no room after the label either: the lower part, as small as it must be
    return oneLine(left, bottom, text, room, Math.max(MIN_SIZE, (below - 2) / CAP))
  }
  if (ink) {
    // an empty cell (its label stands outside): the value in the middle of the cell's height, lines when it is high
    const left = x0 + PADX
    const room = x1 - PADX - left
    const lines = Math.max(1, Math.floor((hgt - 4) / 11.5))
    if (lines > 1 && textWidth(text, 10) > room) {
      const first = y0 + 3 + 10 * CAP
      return manyLines(left, Array.from({ length: lines }, (_, i) => first + i * 11.5), text, room, 10)
    }
    const size = fitSize(text, room, Math.min(10, (hgt - 4) / CAP))
    return oneLine(left, Math.min(bottom, (y0 + y1) / 2 + (size * CAP) / 2), text, room, size)
  }
  // no picture: a low cell holds its own label in the top line, so the value starts after the label (label width
  // estimated at 8 pt type); a higher cell writes under the label
  let left = x0 + PADX
  if (place.label && hgt < 24) {
    const after = x0 + 3 + place.label.length * 4.2 + 6
    if (x1 - after >= Math.max(40, textWidth(text, 8))) left = after
  }
  return oneLine(left, bottom, text, x1 - PADX - left, 10)
}

/** An X centred on a mark box: on the printed square seen on the picture, else on the finder's box. */
export function layoutMark(place: Place, ink?: PlaceInk): Glyph | null {
  const b = ink?.mark ?? place.box
  if (!b) return null
  const [x0, y0, x1, y1] = b
  const size = clampSize(Math.min(x1 - x0, y1 - y0, 11) * 1.1)
  // a wide centred box, so a glyph wider than a tiny mark still centres on it; the X is as high as a capital, so
  // its middle is half a cap height above the baseline
  return { left: (x0 + x1) / 2 - 10, top: (y0 + y1) / 2 + (size * CAP) / 2 - size * BASE, text: 'X', size, width: 20, center: true }
}
