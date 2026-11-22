// Places of the fields on the paper: the answer of POST /v1/forms/preview (FP-contract.md, wave 10) joined with
// the ledger of /convert?report=1 by candidate id. Boxes are in pt, origin top left. Nothing is guessed: a field
// whose row or place is missing has no place.
import type { Sidecar } from '../model'

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
}

export function joinPlaces(rows: LedgerRow[], pv: Preview): Joined {
  const byField = new Map<string, { cid: string; place: Place }>()
  const standard: Joined['standard'] = []
  const fieldOf = new Map<string, string>()
  for (const r of rows) {
    const place = pv.places[r.candidate]
    if (!place) continue
    if (r.fate === 'FIELD' && r.field) {
      if (!byField.has(r.field)) byField.set(r.field, { cid: r.candidate, place })
      fieldOf.set(r.candidate, r.field)
      for (const o of place.options ?? []) if (o.mark) fieldOf.set(o.mark, r.field)
    } else if (r.fate === 'STANDARD' && r.section) {
      standard.push({ cid: r.candidate, section: r.section, place, attr: place.label ? attrOfLabel(place.label) : null })
    }
  }
  return { byField, standard, fieldOf }
}

// ---- print math (pt): where a value goes in its place

export interface Glyph { left: number; top: number; text: string; size: number; width?: number; center?: boolean }

/** Where the baseline sits below the top of a line box of line-height 1 (Arial/Liberation), in em. */
export const BASE = 0.85
const clampSize = (s: number): number => Math.max(7, Math.min(11, s))
/** A rough width of a text in pt at a size (average glyph of Arial ≈ 0.5 em). */
export const textWidth = (text: string, size: number): number => text.length * size * 0.5

/** Glyphs that print `text` in a place; `fits` false when even 7 pt does not fit the box. */
export function layoutText(place: Place, text: string): { glyphs: Glyph[]; fits: boolean } {
  const b = place.box
  if (!b || !text) return { glyphs: [], fits: true }
  const [x0, y0, x1, y1] = b
  const w = Math.max(1, x1 - x0)
  const hgt = Math.max(0, y1 - y0)
  if (place.kind === 'comb' && place.cells && place.cells > 0) {
    const cw = w / place.cells
    const chars = [...text.replace(/\s/g, '')]
    const size = clampSize(Math.min(hgt || 10, cw) * 0.8)
    const base = (y0 + y1) / 2 + size * 0.35
    const glyphs = chars.slice(0, place.cells).map((c, i) => ({ left: x0 + i * cw, top: base - size * BASE, text: c, size, width: cw, center: true }))
    return { glyphs, fits: chars.length <= place.cells }
  }
  if (place.kind === 'line_block' && place.lines && place.lines > 1) {
    const lh = hgt / place.lines
    const size = clampSize(lh * 0.9)
    // words wrapped to the lines by the rough width
    const words = text.split(/\s+/)
    const lines: string[] = []
    let cur = ''
    for (const word of words) {
      const next = cur ? cur + ' ' + word : word
      if (textWidth(next, size) > w && cur) { lines.push(cur); cur = word } else cur = next
    }
    if (cur) lines.push(cur)
    const glyphs = lines.slice(0, place.lines).map((ln, i) => ({ left: x0 + 2, top: y0 + (i + 1) * lh - 2 - size * BASE, text: ln, size }))
    return { glyphs, fits: lines.length <= place.lines }
  }
  // leader, blank in sentence, cell, widget: one line; a tall cell writes in its lower part, a line sits on y1
  const tall = hgt > 16
  // A low table cell holds its own label in the top line: the value then starts after the label (label width
  // estimated at 8 pt type), so the two do not touch; a taller cell writes under the label.
  let left = x0 + 2
  if (place.kind === 'cell' && place.label && hgt < 24) {
    const after = x0 + 3 + place.label.length * 4.2 + 6
    if (x1 - after >= Math.max(40, textWidth(text, 8))) left = after
  }
  const room = x1 - left - 2
  let size = clampSize(10)
  while (size > 7 && textWidth(text, size) > room) size -= 0.5
  const top = (tall ? y1 - 4 : y1 - 1) - size * BASE
  return { glyphs: [{ left, top, text, size }], fits: textWidth(text, size) <= room }
}

/** An X centred on a mark box. */
export function layoutMark(place: Place): Glyph | null {
  const b = place.box
  if (!b) return null
  const [x0, y0, x1, y1] = b
  const size = clampSize(Math.min(x1 - x0, y1 - y0, 11) * 1.1)
  // a wide centred box, so a glyph wider than a tiny mark still centres on it
  return { left: (x0 + x1) / 2 - 10, top: (y0 + y1) / 2 - size * 0.5, text: 'X', size, width: 20, center: true }
}
