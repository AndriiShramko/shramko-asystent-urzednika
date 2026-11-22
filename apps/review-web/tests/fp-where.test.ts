// FP "where on the paper": the preview contract (FP-contract.md) joined with the ledger. Synthetic places only.
import { beforeEach, describe, expect, it } from 'vitest'
import { attrOfLabel, joinPlaces, layoutMark, layoutText, ledgerRows, parsePreview, standardPrints, BASE } from '../src/lib/fp/places'
import { readForm } from '../src/lib/fp/form'
import { renderEForm } from '../src/ui/eform'
import { renderWhere } from '../src/ui/where'
import { mountApp } from '../src/ui/app'
import { setLang } from '../src/lib/i18n'
import { interpretResponse, type Outcome } from '../src/lib/api'
import { canonical, multipartBody } from './helpers'
import { fpForm, fpSidecar } from './fp-fixture'

export function fpLedgerSidecar() {
  const s = fpSidecar() as ReturnType<typeof fpSidecar> & { converter: unknown }
  s.converter = { pipeline: 'brief' }
  s.meta.ledger = { rows: [
    { candidate: 'c1', fate: 'LEFT_OUT', reason: 'OFFICE_USE' },
    { candidate: 'c2', fate: 'STANDARD', section: 'standard/twoje_dane' },
    { candidate: 'c3', fate: 'STANDARD', section: 'standard/adres' },
    { candidate: 'c4', fate: 'FIELD', field: 'f-nip' },
    { candidate: 'c5', fate: 'FIELD', field: 'r-kto' },
    { candidate: 'c8', fate: 'FIELD', field: 'f-data' }
  ] } as never
  return s
}

export function fpPreview(geometry = true) {
  const page = { n: 1, w: 595.32, h: 842.04, source: 'native', img: { media_type: 'image/png', dpi: 150, width_px: 1241, height_px: 1755, data: 'AAAA' } }
  const place = (o: Record<string, unknown>) => geometry ? o : { ...o, box: undefined, anchor: 'p[3]' }
  return {
    version: 1, format: geometry ? 'pdf' : 'docx', units: 'pt', origin: 'top-left',
    page_images: geometry ? 'OK' : 'NO_PAGE_IMAGE',
    pages: geometry ? [page] : [],
    places: {
      c1: place({ page: 1, kind: 'office_use', box: [384, 30, 544, 38], label: 'Nr sprawy' }),
      c2: place({ page: 1, kind: 'cell', box: [55, 198, 539, 224], label: 'Imię i nazwisko', section: 's1' }),
      c3: place({ page: 1, kind: 'cell', box: [55, 224, 346, 245], label: 'Nr domu', section: 's1' }),
      c4: place({ page: 1, kind: 'leader', box: [258, 430, 365, 438], label: 'NIP', section: 's2' }),
      c5: place({ page: 1, kind: 'choice_group', box: [255, 489, 409, 499], label: 'W czyim imieniu', options: [{ text: 'Swoim', mark: 'c6' }, { text: 'Innej osoby', mark: 'c7' }] }),
      c6: place({ page: 1, kind: 'box', box: [255, 489, 261, 499], group: 'c5' }),
      c7: place({ page: 1, kind: 'box', box: [404, 489, 409, 499], group: 'c5' }),
      c8: { page: 1, kind: 'leader', anchor: 'p[9]', label: 'Data urodzenia' }
    },
    counts: { pages: 1, places: 8, boxed: 7, anchored: 1 }
  }
}

beforeEach(() => { setLang('pl'); document.body.innerHTML = '<div id="app"></div>' })

describe('FP places: contract and join', () => {
  it('parses the contract shape, refuses others, joins every row by candidate id', () => {
    expect(parsePreview(null)).toBeNull()
    expect(parsePreview({ pages: 'x' })).toBeNull()
    const pv = parsePreview(fpPreview())!
    expect(pv.pages[0].w).toBeCloseTo(595.32)
    const rows = ledgerRows(fpLedgerSidecar() as never)
    expect(rows).toHaveLength(6)
    const j = joinPlaces(rows, pv)
    expect(j.byField.get('f-nip')?.cid).toBe('c4')
    expect(j.fieldOf.get('c7')).toBe('r-kto')
    expect(j.standard.map((s) => s.attr)).toEqual(['fullname', 'building'])
  })

  it('label table and the sections that print', () => {
    expect(attrOfLabel('Nr domu')).toBe('building')
    expect(attrOfLabel('Kod pocztowy')).toBe('postCode')
    expect(attrOfLabel('Nazwisko, imię / Nazwa pełna')).toBe('fullname_rev')
    expect(attrOfLabel('nr telefonu')).toBe('phone')
    expect(attrOfLabel('Rasa psa')).toBeNull()
    expect(standardPrints('standard/twoje_dane')).toBe(true)
    expect(standardPrints('standard/adres_zamieszkania')).toBe(true)
    expect(standardPrints('standard/pelnomocnictwo')).toBe(false)
    expect(standardPrints('standard/dane_podmiotu')).toBe(false)
  })

  it('print math: a leader writes on its line, a comb one letter per cell, a mark is centred', () => {
    const lead = layoutText({ page: 1, kind: 'leader', box: [56, 692, 300, 700] }, 'Przykładowa')
    expect(lead.glyphs[0].left).toBe(58)
    expect(lead.glyphs[0].top + lead.glyphs[0].size * BASE).toBeCloseTo(699)
    const comb = layoutText({ page: 1, kind: 'comb', box: [100, 200, 210, 214], cells: 11 }, '12345678901')
    expect(comb.glyphs).toHaveLength(11)
    expect(comb.glyphs[1].left - comb.glyphs[0].left).toBeCloseTo(10)
    expect(comb.fits).toBe(true)
    const mark = layoutMark({ page: 1, kind: 'box', box: [255, 489, 261, 499] })!
    expect(mark.left + (mark.width ?? 0) / 2).toBeCloseTo(258)
    const long = layoutText({ page: 1, kind: 'leader', box: [0, 0, 20, 8] }, 'bardzo długi tekst który się nie zmieści')
    expect(long.fits).toBe(false)
    expect(long.glyphs[0].size).toBe(7)
  })
})

describe('FP where-on-paper panel', () => {
  async function panel(pv: unknown) {
    const ef = renderEForm(readForm(fpForm()))
    const w = renderWhere(ef, fpLedgerSidecar() as never, Promise.resolve(pv))
    document.body.append(w.el)
    await w.ready
    return w
  }
  const q = <T extends HTMLElement>(s: string) => document.querySelector<T>(s)!

  it('outlines boxes on the page picture; a click on a field pulses its box, a click on a box focuses the row', async () => {
    await panel(fpPreview())
    expect(q('#h-where').textContent).toBe('Krok 2 z 6. Gdzie na papierze')
    expect(q('.fp-paper img').getAttribute('src')).toBe('data:image/png;base64,AAAA')
    expect(document.querySelectorAll('.fp-box').length).toBe(6) // c2 c3 c4 c5 and the marks c6 c7 (c1 left out, c8 no box)
    const nip = q<HTMLButtonElement>('[data-where="f-nip"]')
    expect(nip.parentElement!.textContent).toContain('strona 1')
    nip.click()
    expect(q('.fp-box[data-cid="c4"]').classList.contains('fp-box-active')).toBe(true)
    expect(q('#fp-where-live').textContent).toBe('„NIP”: strona 1')
    q('.fp-box[data-cid="c7"]').click()
    expect(document.activeElement).toBe(q('[data-where="r-kto"]'))
    expect(q('[data-where="f-data"]').parentElement!.textContent).toContain('Miejsca na papierze nie ustalono')
    expect(q('[data-where="f-cel"]').parentElement!.textContent).toContain('Miejsca na papierze nie ustalono')
    const box = q('.fp-box[data-cid="c4"]')
    expect(box.style.left).toMatch(/%$/)
  })

  it('no preview: one line, nothing else breaks; office formats: the anchor and the honest line', async () => {
    await panel(null)
    expect(q('#fp-where-missing').textContent).toBe('Podgląd druku niedostępny')
    document.body.innerHTML = ''
    await panel(fpPreview(false))
    expect(q('#fp-where-nogeo').textContent).toBe('Dla tego formatu nie ma obrazu strony. Dostępny jest wydruk formularza elektronicznego.')
    expect(q('[data-where="f-nip"]').parentElement!.textContent).toContain('p[3]')
  })

  it('the page calls the preview with the same file after a conversion', async () => {
    const res = await interpretResponse(200, new Headers({ 'content-type': 'multipart/mixed; boundary=formularze-abc123' }),
      multipartBody(canonical(fpForm()), canonical(fpLedgerSidecar())))
    const seen: string[] = []
    mountApp(document.getElementById('app')!, {
      convert: async (): Promise<Outcome> => res, store: null, status: async () => null,
      preview: async (f) => { seen.push(f.name); return fpPreview() }
    })
    const input = document.getElementById('file') as HTMLInputElement
    Object.defineProperty(input, 'files', { value: [new File(['x'], 'druk.pdf')], configurable: true })
    input.dispatchEvent(new Event('change'))
    await new Promise((r) => setTimeout(r, 0))
    await new Promise((r) => setTimeout(r, 0))
    expect(seen).toEqual(['druk.pdf'])
    expect(document.querySelectorAll('.fp-paper').length).toBe(1)
  })
})
