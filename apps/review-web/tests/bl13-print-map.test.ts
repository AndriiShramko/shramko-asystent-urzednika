// BL13 PRINT-MAP: a picked field of the e-form always answers: its place on the original lights, or one plain line
// next to the field says the program did not point its place out. Synthetic data only.
import { beforeEach, describe, expect, it } from 'vitest'
import { setLang } from '../src/lib/i18n'
import { interpretResponse, type Converted } from '../src/lib/api'
import { renderConverted } from '../src/ui/result'
import { mountFill } from '../src/ui/fill'
import { setView } from '../src/ui/clerk-view'
import { FP } from '../src/lib/fp/text'
import { printNote } from '../src/ui/print'
import { canonical, multipartBody } from './helpers'
import { fpForm, fpLedgerSidecar, fpPreview } from './fp-fixture'

async function page() {
  const res = await interpretResponse(200, new Headers({ 'content-type': 'multipart/mixed; boundary=formularze-abc123' }),
    multipartBody(canonical(fpForm()), canonical(fpLedgerSidecar()))) as Converted
  const view = renderConverted(res)
  const fill = mountFill(res, Promise.resolve(fpPreview()))
  view.insertBefore(fill.el, view.querySelector('section[aria-labelledby="h-json"]'))
  document.body.append(view)
  await fill.where.ready
  return fill
}
const all = (s: string) => [...document.querySelectorAll<HTMLElement>(s)]

beforeEach(() => { setLang('pl'); setView('clerk'); document.body.innerHTML = '' })

describe('BL13 PRINT-MAP: every picked field answers', () => {
  it('a pick lights a place of the original or shows one line next to the field, never nothing', async () => {
    await page()
    const fields = all('.fp-field[data-node]')
    expect(fields.length).toBeGreaterThan(3)
    let lit = 0
    let lines = 0
    let silent = 0
    for (const w of fields) {
      const id = w.getAttribute('data-node')!
      w.dispatchEvent(new Event('focusin', { bubbles: true }))
      const box = all('.fp-box-active').length
      const line = all('.fp-noplace')
      if (box) {
        lit++
        expect(line.length).toBe(0)
      } else if (line.length === 1 && line[0].getAttribute('data-for') === id && w.contains(line[0])) {
        lines++
        expect([FP.noPlaceStandard, FP.noPlaceOther]).toContain(line[0].textContent)
        expect(document.querySelector('#fp-where-boxlive')?.textContent).toBe(line[0].textContent)
        expect(document.querySelector('#fp-where-boxlive')?.getAttribute('aria-live')).toBe('polite')
      } else silent++
    }
    expect(silent).toBe(0)
    expect(lit).toBeGreaterThan(0)
    expect(lines).toBeGreaterThan(0)
  })

  it('the line goes away when a field with a place is picked next; only one line at a time', async () => {
    await page()
    const fields = all('.fp-field[data-node]')
    const pick = (w: HTMLElement) => w.dispatchEvent(new Event('focusin', { bubbles: true }))
    const without = fields.filter((w) => { pick(w); return all('.fp-noplace').length === 1 })
    const withBox = fields.filter((w) => { pick(w); return all('.fp-box-active').length > 0 })
    expect(without.length).toBeGreaterThan(0)
    expect(withBox.length).toBeGreaterThan(0)
    pick(without[0])
    expect(all('.fp-noplace').length).toBe(1)
    pick(withBox[0])
    expect(all('.fp-noplace').length).toBe(0)
  })
})

describe('BL13 PRINT-MAP: an empty blank is never shown without a word', () => {
  it('the line above the preview by what landed on the blank', () => {
    const one = [{ name: 'Imię', value: 'Anna' }]
    expect(printNote(null)).toBe('')
    expect(printNote({ placed: 3, extra: [] })).toBe('')
    expect(printNote({ placed: 3, extra: one })).toBe(FP.noPlace(1))
    expect(printNote({ placed: 0, extra: one })).toBe(FP.blankEmptyExtra(1))
    expect(printNote({ placed: 0, extra: one })).toContain('na dodatkowej stronie')
    expect(printNote({ placed: 0, extra: [] })).toBe(FP.blankEmptyNothing)
  })

  it('the preview of a form nobody filled says why the blank is empty; the line is a status for the screen reader', async () => {
    await page()
    const btn = document.querySelector<HTMLButtonElement>('#fp-print-preview-btn')!
    btn.click()
    const note = document.querySelector<HTMLElement>('#fp-print-extra')!
    expect(note.getAttribute('role')).toBe('status')
    expect(document.querySelectorAll('#fp-print-preview .fp-sheet').length).toBeGreaterThan(0)
    const glyphs = document.querySelectorAll('#fp-print-preview .fp-glyph').length
    if (!glyphs) expect(note.textContent).not.toBe('')
  })
})
