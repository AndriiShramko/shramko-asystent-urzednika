// Where the ink of the paper is inside a field's place (wave 11, FPOS). The finder gives a box per place; for a
// dotted leader that box is the box of the dot CHARACTERS, so the dots themselves sit about a third of its height
// above its bottom, and a place read from a scan has whatever box the OCR gave. A hand writes just above the
// line, so the print measures the line on the very page picture it prints: thin rows of ink that run across the
// place (dotted or solid rules), the free height above each of them, the vertical separators of character boxes
// and the ink of a label inside a table cell. Pure functions on a bitmap (tested with synthetic bitmaps) and one
// browser-only loader that decodes the page pictures of the preview answer. No network call, nothing is stored.
import type { Box, Place, Preview } from './places'

/** A page picture as ink: 1 = dark pixel. `scale` = pixels per pt. */
export interface Bitmap { w: number; h: number; scale: number; data: Uint8Array }
/** A horizontal run of ink, top and bottom in pt from the top of the page. */
export interface Band { top: number; bottom: number }
export interface PlaceInk {
  /** thin rules across the place (dotted or solid), top to bottom */
  rules: Band[]
  /** free height in pt above each rule (no ink over the width of the place), at most CLEAR_MAX */
  clear: number[]
  /** character boxes of a comb, left to right: [x0, x1] in pt; empty when they were not seen */
  cells: [number, number][]
  /** the ink inside a table cell away from its borders (its printed label): box and the baseline of its last line */
  label?: { box: Box; baseline: number }
  /** the printed square of a tick box as it stands on the picture (the finder's box is that of its character) */
  mark?: Box
}

export const DARK = 160
const PAD = 3          // pt searched above and below the box for its rule
const RULE_MAX = 3.2   // pt: a thicker band of ink is text or a filled area, not a rule
export const CLEAR_MAX = 18

const px = (bm: Bitmap, pt: number): number => Math.round(pt * bm.scale)
const clampX = (bm: Bitmap, x: number): number => Math.max(0, Math.min(bm.w, x))
const clampY = (bm: Bitmap, y: number): number => Math.max(0, Math.min(bm.h, y))

function rowHasInk(bm: Bitmap, y: number, x0: number, x1: number): boolean {
  const o = y * bm.w
  for (let x = x0; x < x1; x++) if (bm.data[o + x]) return true
  return false
}

/** Is row y a rule row: ink in at least three quarters of the equal parts of [x0, x1)? */
function ruleRow(bm: Bitmap, y: number, x0: number, x1: number, parts: number): boolean {
  const o = y * bm.w
  let hit = 0
  for (let i = 0; i < parts; i++) {
    const a = x0 + Math.floor(((x1 - x0) * i) / parts)
    const b = x0 + Math.floor(((x1 - x0) * (i + 1)) / parts)
    for (let x = a; x < b; x++) if (bm.data[o + x]) { hit++; break }
  }
  return hit >= Math.ceil(parts * 0.75)
}

/** Thin bands of ink that run across [x0, x1] pt between y0 and y1 pt (rows in px, inclusive ends). */
export function rulesIn(bm: Bitmap, x0: number, y0: number, x1: number, y1: number): Band[] {
  const ax = clampX(bm, px(bm, x0) + 1); const bx = clampX(bm, px(bm, x1) - 1)
  const ay = clampY(bm, px(bm, y0)); const by = clampY(bm, px(bm, y1))
  if (bx - ax < 8) return []
  const parts = Math.max(3, Math.min(12, Math.floor((bx - ax) / 14)))
  const bands: [number, number][] = []
  for (let y = ay; y < by; y++) {
    if (!ruleRow(bm, y, ax, bx, parts)) continue
    const last = bands[bands.length - 1]
    if (last && y - last[1] <= 1) last[1] = y
    else bands.push([y, y])
  }
  return bands.map(([a, b]) => ({ top: a / bm.scale, bottom: (b + 1) / bm.scale })).filter((b) => b.bottom - b.top <= RULE_MAX)
}

/** Free height above y (pt) over [x0, x1] pt: rows without ink, counted upwards, at most CLEAR_MAX. */
export function clearAbove(bm: Bitmap, x0: number, x1: number, y: number): number {
  const ax = clampX(bm, px(bm, x0) + 2); const bx = clampX(bm, px(bm, x1) - 2)
  const from = clampY(bm, Math.floor(y * bm.scale)) - 1
  const stop = Math.max(0, from - Math.round(CLEAR_MAX * bm.scale))
  let r = from
  while (r > stop && !rowHasInk(bm, r, ax, bx)) r--
  return (from - r) / bm.scale
}

/** Vertical separators inside a comb and the boxes between them: [x0, x1] pt of every box that has the common width. */
export function combCells(bm: Bitmap, box: Box): [number, number][] {
  const [x0, y0, x1, y1] = box
  const h = y1 - y0
  if (h <= 2) return []
  const ay = clampY(bm, px(bm, y0 + h * 0.25)); const by = clampY(bm, px(bm, y1 - h * 0.25))
  const ax = clampX(bm, px(bm, x0) - 3); const bx = clampX(bm, px(bm, x1) + 3)
  if (by - ay < 3) return []
  const seps: [number, number][] = []
  for (let x = ax; x < bx; x++) {
    let dark = 0
    for (let y = ay; y < by; y++) if (bm.data[y * bm.w + x]) dark++
    if (dark < (by - ay) * 0.8) continue
    const last = seps[seps.length - 1]
    if (last && x - last[1] <= 1) last[1] = x
    else seps.push([x, x])
  }
  if (seps.length < 2) return []
  const gaps: [number, number][] = []
  for (let i = 0; i + 1 < seps.length; i++) gaps.push([(seps[i][1] + 1) / bm.scale, seps[i + 1][0] / bm.scale])
  const widths = gaps.map(([a, b]) => b - a).sort((a, b) => a - b)
  const median = widths[Math.floor(widths.length / 2)]
  // a box is a gap of the common width (a dash between two groups of boxes is narrower or has no box around it)
  return gaps.filter(([a, b]) => Math.abs(b - a - median) <= Math.max(1.5, median * 0.25) && b - a >= 4)
}

/** The ink inside a cell, 2 pt away from its borders: its box and the baseline of its last text line. */
export function labelIn(bm: Bitmap, box: Box): PlaceInk['label'] {
  const [x0, y0, x1, y1] = box
  const ax = clampX(bm, px(bm, x0 + 2)); const bx = clampX(bm, px(bm, x1 - 2))
  const ay = clampY(bm, px(bm, y0 + 2)); const by = clampY(bm, px(bm, y1 - 2))
  if (bx - ax < 4 || by - ay < 4) return undefined
  let minX = bx; let maxX = -1; let minY = by; let maxY = -1
  const perRow: number[] = []
  for (let y = ay; y < by; y++) {
    let n = 0
    const o = y * bm.w
    for (let x = ax; x < bx; x++) if (bm.data[o + x]) { n++; if (x < minX) minX = x; if (x > maxX) maxX = x }
    perRow.push(n)
    if (n) { if (y < minY) minY = y; maxY = y }
  }
  if (maxX < 0) return undefined
  // the baseline: the lowest row that still carries a good share of the ink of the fullest row (descenders are thin)
  const most = Math.max(...perRow)
  let base = maxY
  for (let y = maxY; y >= minY; y--) if (perRow[y - ay] >= most * 0.3) { base = y; break }
  return { box: [minX / bm.scale, minY / bm.scale, (maxX + 1) / bm.scale, (maxY + 1) / bm.scale], baseline: (base + 1) / bm.scale }
}

/** The printed square of a tick box: the first run of inked columns from the left edge of the finder's box (it
 * ends at the white gap before the option's text) and the inked rows inside those columns. */
export function markIn(bm: Bitmap, box: Box): Box | undefined {
  const [x0, y0, x1, y1] = box
  const ay = clampY(bm, px(bm, y0 - 1.5)); const by = clampY(bm, px(bm, y1 + 1.5))
  const ax = clampX(bm, px(bm, x0 - 1.5)); const bx = clampX(bm, px(bm, x0 + Math.max(x1 - x0, y1 - y0) + 4))
  const colHasInk = (x: number): boolean => { for (let y = ay; y < by; y++) if (bm.data[y * bm.w + x]) return true; return false }
  let a = ax
  while (a < bx && !colHasInk(a)) a++
  if (a >= bx) return undefined
  let b = a
  let gap = 0
  for (let x = a; x < bx; x++) { if (colHasInk(x)) { b = x; gap = 0 } else if (++gap > Math.max(1, bm.scale * 0.7)) break }
  let top = -1; let bottom = -1
  for (let y = ay; y < by; y++) if (rowHasInk(bm, y, a, b + 1)) { if (top < 0) top = y; bottom = y }
  if (top < 0) return undefined
  const out: Box = [a / bm.scale, top / bm.scale, (b + 1) / bm.scale, (bottom + 1) / bm.scale]
  const w = out[2] - out[0]; const h = out[3] - out[1]
  return w >= 4 && w <= 18 && h >= 4 && h <= 18 && w / h > 0.6 && w / h < 1.67 ? out : undefined
}

/** Everything the print needs to know about the ink of one place. */
export function measurePlace(bm: Bitmap, place: Place): PlaceInk | null {
  const b = place.box
  if (!b) return null
  const [x0, y0, x1, y1] = b
  const rules = rulesIn(bm, x0, y0 - PAD, x1, y1 + PAD)
  const out: PlaceInk = { rules, clear: rules.map((r) => clearAbove(bm, x0, x1, r.top)), cells: [] }
  if (place.kind === 'comb') out.cells = combCells(bm, b)
  if (place.kind === 'cell') out.label = labelIn(bm, b)
  if (place.kind === 'box') out.mark = markIn(bm, b)
  return out
}

/** The ink of a decoded picture: 1 where the red channel is darker than DARK (the pictures are greyscale). */
export function bitmapOfRgba(rgba: Uint8ClampedArray | Uint8Array, w: number, h: number, widthPt: number): Bitmap {
  const data = new Uint8Array(w * h)
  for (let i = 0; i < data.length; i++) data[i] = rgba[i * 4] < DARK ? 1 : 0
  return { w, h, scale: w / widthPt, data }
}

/** Can this browser read the pixels of a picture (a canvas with a 2D context)? Test pages cannot. */
export function canReadInk(): boolean {
  try {
    return typeof document !== 'undefined' && typeof Image !== 'undefined' && typeof Image.prototype.decode === 'function' &&
      !!document.createElement('canvas').getContext('2d')
  } catch {
    return false
  }
}

async function decode(src: string, widthPt: number): Promise<Bitmap | null> {
  try {
    if (typeof document === 'undefined' || typeof Image === 'undefined') return null
    const el = new Image()
    el.src = src
    if (typeof el.decode !== 'function') return null
    await el.decode()
    const w = el.naturalWidth; const h = el.naturalHeight
    if (!w || !h) return null
    const c = document.createElement('canvas')
    c.width = w; c.height = h
    const ctx = c.getContext('2d', { willReadFrequently: true })
    if (!ctx) return null
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, w, h)
    ctx.drawImage(el, 0, 0)
    return bitmapOfRgba(ctx.getImageData(0, 0, w, h).data, w, h, widthPt)
  } catch {
    return null // a browser without canvas or a picture that does not decode: the print falls back to the box alone
  }
}

/** The ink of every boxed place of the preview, by candidate id. Empty where a page picture cannot be read. */
export async function measureInk(pv: Preview | null): Promise<Map<string, PlaceInk>> {
  const out = new Map<string, PlaceInk>()
  if (!pv) return out
  for (const page of pv.pages) {
    if (!page.img) continue
    const mine = Object.entries(pv.places).filter(([, p]) => p.page === page.n && p.box)
    if (!mine.length) continue
    const bm = await decode(`data:${page.img.media_type};base64,${page.img.data}`, page.w)
    if (!bm) continue
    for (const [cid, p] of mine) {
      const ink = measurePlace(bm, p)
      if (ink) out.set(cid, ink)
    }
  }
  return out
}
