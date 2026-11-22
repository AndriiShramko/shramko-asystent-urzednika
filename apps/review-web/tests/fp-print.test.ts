// FP step 6: the print on the original blank and the print of the electronic form. Synthetic places and data.
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { interpretResponse, type Converted } from '../src/lib/api'
import { mountFill } from '../src/ui/fill'
import { buildEformPrint, buildSheets, paperText } from '../src/ui/print'
import { BASE } from '../src/lib/fp/places'
import { canonical, multipartBody } from './helpers'
import { fpForm, fpLedgerSidecar, fpPreview } from './fp-fixture'

beforeEach(() => { document.body.innerHTML = ''; document.body.className = '' })

async function block(pv: unknown) {
  const res = await interpretResponse(200, new Headers({ 'content-type': 'multipart/mixed; boundary=formularze-abc123' }),
    multipartBody(canonical(fpForm()), canonical(fpLedgerSidecar())))
  const b = mountFill(res as Converted, Promise.resolve(pv))
  document.body.append(b.el)
  await b.where.ready
  await Promise.resolve()
  return b
}
const q = <T extends HTMLElement>(s: string) => document.querySelector<T>(s)!
const glyphAt = (sheet: HTMLElement, text: string) => [...sheet.querySelectorAll<HTMLElement>('.fp-glyph')].find((g) => g.textContent === text)

describe('FP print on the original', () => {
  it('places values in pt: a leader on its line, standard cells by their label, an X on the chosen option', async () => {
    const b = await block(fpPreview())
    q('#fp-scan').click(); q('[data-person="0"]').click(); q('#fp-fill').click()
    const inna = q<HTMLInputElement>('[id="fpf-r-kto-o1"]'); inna.checked = true; inna.dispatchEvent(new Event('change'))
    const s = buildSheets(b.eform, b.where, b.citizen.record())!
    expect(s.sheets.length).toBe(2) // the page and the extra page
    const page = s.sheets[0]
    expect(parseFloat(page.style.width)).toBe(595)
    expect(page.querySelector('img')!.getAttribute('src')).toBe('data:image/png;base64,AAAA')
    const nip = [...page.querySelectorAll<HTMLElement>('.fp-glyph')].find((g) => /^\d{10}$/.test(g.textContent ?? ''))!
    expect(parseFloat(nip.style.left)).toBe(260)
    const top = parseFloat(nip.style.top); const size = parseFloat(nip.style.fontSize)
    expect(top + size * BASE).toBeCloseTo(437, 1) // baseline 1 pt above the leader's bottom (438)
    expect(glyphAt(page, 'Tomasz Przykładowski')).toBeTruthy()
    expect(parseFloat(glyphAt(page, '12')!.style.left)).toBeCloseTo(55 + 3 + 'Nr domu'.length * 4.2 + 6, 1) // a low cell: after its label
    const x = glyphAt(page, 'X')!
    expect(parseFloat(x.style.left) + parseFloat(x.style.width) / 2).toBeCloseTo(406.5)
    expect(page.textContent).toContain('Dane demonstracyjne.')
    expect(s.extra.map((e) => e.name)).toContain('Kod pocztowy')
    expect(s.extra.map((e) => e.name)).not.toContain('Numer budynku')
    expect(s.extra.map((e) => e.name)).not.toContain('NIP')
    expect(s.sheets[1].textContent).toContain('pól nie ma miejsca na blankiecie; są wydrukowane na dodatkowej stronie.')
  })

  it('the buttons: preview on screen, print puts only the sheets into #fp-print and calls the browser print', async () => {
    await block(fpPreview())
    const print = vi.fn()
    window.print = print
    expect(q<HTMLButtonElement>('#fp-print-sheet').disabled).toBe(false)
    expect(q('#h-print').textContent).toBe('Krok 6 z 6. Wydruk')
    expect(document.body.textContent).toContain('Przed drukiem ustaw skalę 100 % (bez dopasowania do strony).')
    q('#fp-print-preview-btn').click()
    expect(q('#fp-print-preview').hidden).toBe(false)
    expect(q('#fp-print-preview').querySelectorAll('.fp-sheet').length).toBeGreaterThan(0)
    q('#fp-print-sheet').click()
    expect(print).toHaveBeenCalledOnce()
    expect(document.body.classList.contains('fp-printing')).toBe(true)
    expect(q('#fp-print').querySelector('.fp-sheet')).not.toBeNull()
    window.dispatchEvent(new Event('afterprint'))
    expect(document.body.classList.contains('fp-printing')).toBe(false)
    q('#fp-print-eform').click()
    expect(q('#fp-print').querySelector('.fp-eprint')).not.toBeNull()
    expect(q('#fp-print').querySelector('.fp-sheet')).toBeNull()
  })

  it('office formats and a failed preview: only the electronic form prints, with the honest line', async () => {
    await block(fpPreview(false))
    expect(q<HTMLButtonElement>('#fp-print-sheet').disabled).toBe(true)
    expect(q('#fp-print-note').textContent).toBe('Dla tego formatu nie ma obrazu strony. Dostępny jest wydruk formularza elektronicznego.')
    document.body.innerHTML = ''
    await block(null)
    expect(q('#fp-print-note').textContent).toBe('Podgląd druku niedostępny')
    expect(q<HTMLButtonElement>('#fp-print-eform').disabled).toBe(false)
  })

  it('the e-form print lists visible fields with values; dates as on paper', async () => {
    const b = await block(fpPreview())
    b.eform.set('f-data', '1984-03-15')
    const el = buildEformPrint(b.eform)
    expect(el.textContent).toContain('Data urodzenia: 15.03.1984')
    expect(el.textContent).toContain('Cel wydania: —')
    expect(el.textContent).not.toContain('Dane innej osoby')
    expect(paperText(b.eform.model.byId.get('f-cel')!, '2026-01-01')).toBe('2026-01-01')
  })

  it('the check names the values that have no place on the blank', async () => {
    await block(fpPreview())
    q('#fp-scan').click(); q('[data-person="0"]').click(); q('#fp-fill').click()
    q('#fp-check').click()
    expect(q('#fp-check-noplace').textContent).toMatch(/^\d+ pól nie ma miejsca na blankiecie/)
  })
})
