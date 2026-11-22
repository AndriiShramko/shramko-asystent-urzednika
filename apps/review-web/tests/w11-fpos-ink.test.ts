// Wave 11, FPOS: a printed value stands just ABOVE the line of its place, never on it or through it. The line is
// measured on the page picture (lib/fp/ink.ts); these tests draw synthetic pictures: dotted leaders the way a PDF
// shows them (dots a third of the character box above its bottom), a block of lines, a comb with a dash, a table
// cell with its label, a tick box followed by its text. Synthetic data only.
import { describe, expect, it } from 'vitest'
import { clearAbove, combCells, labelIn, markIn, measurePlace, rulesIn, type Bitmap } from '../src/lib/fp/ink'
import { BASE, CAP, GAP, LEADER_RISE, layoutMark, layoutText, textWidth, type Glyph, type Place } from '../src/lib/fp/places'

const S = 2 // pixels per pt (the preview pictures are 150 dpi: 2.08)
function sheet(wPt = 400, hPt = 300): Bitmap & { hline(x0: number, x1: number, y: number, thick?: number): void; dots(x0: number, x1: number, y: number): void; vline(x: number, y0: number, y1: number): void; block(x0: number, y0: number, x1: number, y1: number): void } {
  const w = wPt * S; const h = hPt * S
  const data = new Uint8Array(w * h)
  const set = (x: number, y: number): void => { if (x >= 0 && x < w && y >= 0 && y < h) data[y * w + x] = 1 }
  return {
    w, h, scale: S, data,
    hline(x0, x1, y, thick = 1) { for (let t = 0; t < thick * S; t++) for (let x = x0 * S; x < x1 * S; x++) set(x, y * S + t) },
    dots(x0, x1, y) { for (let x = x0 * S; x < x1 * S; x += 6) { set(x, y * S); set(x + 1, y * S); set(x, y * S + 1); set(x + 1, y * S + 1) } },
    vline(x, y0, y1) { for (let y = y0 * S; y < y1 * S; y++) { set(x * S, y); set(x * S + 1, y) } },
    block(x0, y0, x1, y1) { for (let y = y0 * S; y < y1 * S; y++) for (let x = x0 * S; x < x1 * S; x++) if ((x + y) % 2 === 0) set(x, y) }
  }
}
const baseline = (g: Glyph): number => g.top + g.size * BASE

describe('FPOS ink: the line of a place is measured on the page picture', () => {
  it('finds a dotted and a solid rule, and does not take a line of text for a rule', () => {
    const bm = sheet()
    bm.dots(50, 250, 100)
    bm.hline(50, 250, 140)
    bm.block(50, 160, 250, 166) // a band 6 pt thick: text or a filled area
    const r = rulesIn(bm, 50, 90, 250, 170)
    expect(r.map((b) => b.top)).toEqual([100, 140])
    expect(r[0].bottom - r[0].top).toBeLessThanOrEqual(1.5)
    expect(rulesIn(bm, 50, 150, 250, 170)).toEqual([])
  })

  it('measures the free height above a rule up to the ink over it', () => {
    const bm = sheet()
    bm.dots(50, 250, 100)
    bm.block(60, 80, 120, 88)
    expect(clearAbove(bm, 50, 250, 100)).toBeCloseTo(12, 0)
    expect(clearAbove(bm, 150, 250, 100)).toBeGreaterThan(15) // nothing above this part
  })

  it('sees the boxes of a comb and leaves out the dash between two groups', () => {
    const bm = sheet()
    // NN-NNN: two boxes, a gap with a dash, three boxes; every box 12 pt wide and 16 pt high
    const xs = [100, 112, 124, 136, 148, 160, 172]
    bm.hline(100, 124, 200); bm.hline(100, 124, 216); bm.hline(136, 172, 200); bm.hline(136, 172, 216)
    for (const x of xs) bm.vline(x, 200, 216)
    bm.hline(127, 133, 208) // the dash
    const cells = combCells(bm, [100, 200, 172, 216])
    expect(cells).toHaveLength(6) // the gap of the dash is as wide as a box here, so it counts as a place
    const dashless = sheet()
    const ys = [100, 112, 124, 130, 142, 154, 166] // the dash gap is 6 pt, a box 12 pt
    for (const x of ys) dashless.vline(x, 200, 216)
    const five = combCells(dashless, [100, 200, 166, 216])
    expect(five).toHaveLength(5)
    expect(five[2][0]).toBeGreaterThanOrEqual(130)
  })

  it('reads the label of a cell (its box and baseline) and the square of a tick box', () => {
    const bm = sheet()
    bm.hline(50, 350, 100); bm.hline(50, 350, 121); bm.vline(50, 100, 121); bm.vline(349, 100, 121)
    bm.block(56, 103, 90, 109) // the label, 6 pt high
    const lab = labelIn(bm, [50, 100, 350, 121])!
    expect(lab.box[0]).toBeCloseTo(56, 0)
    expect(lab.box[2]).toBeCloseTo(90, 0)
    expect(lab.baseline).toBeCloseTo(109, 0)
    // a 9 pt square, 4 pt of white, then the option's text; the finder's box is only the character box (5.6 pt wide)
    bm.hline(200, 209, 200); bm.hline(200, 209, 208.5); bm.vline(200, 200, 209); bm.vline(208, 200, 209)
    bm.block(213, 201, 240, 208)
    const sq = markIn(bm, [200, 199, 205.6, 209.5])!
    expect(sq[0]).toBeCloseTo(200, 0)
    expect(sq[2]).toBeCloseTo(209, 0)
    const x = layoutMark({ page: 1, kind: 'box', box: [200, 199, 205.6, 209.5] }, { rules: [], clear: [], cells: [], mark: sq })!
    expect(x.left + (x.width ?? 0) / 2).toBeCloseTo(204.5, 0)
    expect(x.top + x.size * BASE - (x.size * CAP) / 2).toBeCloseTo((sq[1] + sq[3]) / 2, 1)
  })
})

describe('FPOS print math: the baseline stands just above the line', () => {
  // the measured check as a test: for every value, d = top of its rule - baseline must be GAP (never <= 0)
  it('a leader as a PDF gives it: the box is the box of the dot characters, the dots a third above its bottom', () => {
    for (const h of [8, 9, 11, 12]) {
      const bm = sheet()
      const y1 = 120
      const dotsTop = y1 - h * 0.33
      bm.dots(60, 260, dotsTop)
      const place: Place = { page: 1, kind: 'leader', box: [60, y1 - h, 260, y1] }
      const ink = measurePlace(bm, place)!
      const withInk = layoutText(place, 'Przykładowa 12', ink).glyphs[0]
      expect(dotsTop - baseline(withInk)).toBeCloseTo(GAP, 1)
      const boxOnly = layoutText(place, 'Przykładowa 12').glyphs[0] // no picture: the measured habit of the boxes
      expect(dotsTop - baseline(boxOnly)).toBeGreaterThan(1)
      expect(dotsTop - baseline(boxOnly)).toBeLessThan(2.2)
      expect(baseline(boxOnly)).toBeCloseTo(y1 - h * LEADER_RISE - GAP)
    }
  })

  it('a solid rule under a blank and a box that is only the rule itself', () => {
    const bm = sheet()
    bm.hline(60, 200, 150)
    const g = layoutText({ page: 1, kind: 'blank_in_sentence', box: [60, 150, 200, 150] }, 'Bydgoszcz', measurePlace(bm, { page: 1, kind: 'blank_in_sentence', box: [60, 150, 200, 150] })!).glyphs[0]
    expect(150 - baseline(g)).toBeCloseTo(GAP, 1)
  })

  it('a block of lines: every line of the value stands above its own row of dots (set 07: the address)', () => {
    const bm = sheet()
    const place: Place = { page: 1, kind: 'line_block', lines: 2, box: [40, 200, 380, 222.6] } // 8 pt dots, pitch 14.4
    bm.dots(40, 380, 205.6); bm.dots(40, 380, 220)
    const ink = measurePlace(bm, place)!
    const long = 'Przykładowy dłuższy opis sprawy, który zajmuje więcej niż jedną linię na papierze i sprawdza zawijanie'
    for (const r of [layoutText(place, long, ink), layoutText(place, long)]) {
      expect(r.glyphs).toHaveLength(2)
      expect(205.6 - baseline(r.glyphs[0])).toBeGreaterThan(1)
      expect(205.6 - baseline(r.glyphs[0])).toBeLessThan(2.6)
      expect(220 - baseline(r.glyphs[1])).toBeGreaterThan(1)
      expect(220 - baseline(r.glyphs[1])).toBeLessThan(2.6)
      for (const g of r.glyphs) expect(textWidth(g.text, g.size)).toBeLessThanOrEqual(340)
    }
  })

  it('a comb: every character is centred in its own box, also after a dash', () => {
    const cells: [number, number][] = [[100, 112], [112, 124], [130, 142], [142, 154], [154, 166]]
    const r = layoutText({ page: 1, kind: 'comb', cells: 5, box: [100, 200, 166, 216] }, '85-999'.replace('-', ''), { rules: [], clear: [], cells })
    expect(r.glyphs.map((g) => g.left + (g.width ?? 0) / 2)).toEqual([106, 118, 136, 148, 160])
    for (const g of r.glyphs) {
      expect(g.center).toBe(true)
      expect(baseline(g) - (g.size * CAP) / 2).toBeCloseTo(208, 1) // the middle of the box's height
    }
    expect(layoutText({ page: 1, kind: 'comb', cells: 5, box: [100, 200, 166, 216] }, '123456').fits).toBe(false)
  })

  it('a table cell: under its label when there is room, else after it on the label line; always inside the cell', () => {
    const tall: Place = { page: 1, kind: 'cell', box: [50, 100, 350, 126], label: 'Imię i nazwisko' }
    const ink = { rules: [], clear: [], cells: [], label: { box: [56, 103, 110, 110] as [number, number, number, number], baseline: 109 } }
    const under = layoutText(tall, 'Helena Przykładowska', ink).glyphs[0]
    expect(under.left).toBe(56) // aligned with the label
    expect(baseline(under) - under.size * CAP).toBeGreaterThan(110 + 1) // clear of the label
    expect(126 - baseline(under)).toBeGreaterThanOrEqual(2) // a margin above the lower border
    const low: Place = { page: 1, kind: 'cell', box: [50, 100, 350, 117], label: 'Telefon:' }
    const after = layoutText(low, '+48 000 000 105', ink).glyphs[0]
    expect(after.left).toBe(115)
    expect(baseline(after)).toBe(109) // on the label's own baseline
    expect(baseline(after) - after.size * CAP).toBeGreaterThanOrEqual(100 + 1.5)
  })

  it('a long value shrinks, and one that cannot fit is cut with an ellipsis instead of running over the next thing', () => {
    const place: Place = { page: 1, kind: 'leader', box: [100, 100, 240, 112] }
    const fits = layoutText(place, 'ul. Przykładowa 12 m. 4, 85-999 Bydgoszcz')
    expect(fits.glyphs[0].size).toBeLessThan(10)
    expect(textWidth(fits.glyphs[0].text, fits.glyphs[0].size)).toBeLessThanOrEqual(136)
    const not = layoutText(place, 'bardzo długi tekst, który nie zmieści się w tym miejscu nawet najmniejszą czcionką')
    expect(not.fits).toBe(false)
    expect(not.glyphs[0].text.endsWith('…')).toBe(true)
    expect(textWidth(not.glyphs[0].text, not.glyphs[0].size)).toBeLessThanOrEqual(136)
  })

  it('the width of a text follows the widths of Arial', () => {
    expect(textWidth('0123456789', 10)).toBeCloseTo(55.6)
    expect(textWidth('ił', 10)).toBeCloseTo(4.44)
    expect(textWidth('Żółć', 10)).toBeCloseTo((611 + 556 + 222 + 500) / 100)
  })
})
