// BL13 CLERK-T: plain remark cards, a target for every box of the original, the signature line. Synthetic data only.
import { beforeEach, describe, expect, it } from 'vitest'
import { setLang } from '../src/lib/i18n'
import { interpretResponse, type Converted } from '../src/lib/api'
import { renderConverted } from '../src/ui/result'
import { mountFill } from '../src/ui/fill'
import { setView } from '../src/ui/clerk-view'
import { sessionOf } from '../src/ui/clerk-remarks'
import { readForm } from '../src/lib/fp/form'
import { ledgerRows, parsePreview } from '../src/lib/fp/places'
import { answers, attrsOfLabel, boxTargets, stackedOn } from '../src/lib/fp/targets'
import { pl } from '../src/i18n/pl'
import { en } from '../src/i18n/en'
import { es } from '../src/i18n/es'
import { canonical, multipartBody } from './helpers'
import { fpForm, fpLedgerSidecar, fpPreview } from './fp-fixture'

const GRID = '/tabs/1/questions/0/field/repeatingSectionGrid'

async function page(warnings: unknown[], preview: unknown = fpPreview(), rows?: unknown[]) {
  const sidecar = fpLedgerSidecar() as unknown as { warnings: unknown[]; meta: Record<string, unknown> }
  sidecar.warnings = warnings
  if (rows) (sidecar.meta.ledger as { rows: unknown[] }).rows.push(...rows)
  const res = await interpretResponse(200, new Headers({ 'content-type': 'multipart/mixed; boundary=formularze-abc123' }),
    multipartBody(canonical(fpForm()), canonical(sidecar))) as Converted
  const view = renderConverted(res)
  const fill = mountFill(res, Promise.resolve(preview))
  view.insertBefore(fill.el, view.querySelector('section[aria-labelledby="h-json"]'))
  document.body.append(view)
  await fill.where.ready
  return { res, view, fill, session: sessionOf(res.sidecar) }
}
const q = <T extends HTMLElement>(s: string) => document.querySelector<T>(s)!
const all = (s: string) => [...document.querySelectorAll<HTMLElement>(s)]

beforeEach(() => { setLang('pl'); setView('clerk'); document.body.innerHTML = '' })

describe('BL13 box targets', () => {
  it('one label may name two things; a name in one label stays one thing', () => {
    expect(attrsOfLabel('nr telefonu/adres e-mail')).toEqual(['phone', 'email'])
    expect(attrsOfLabel('imię i nazwisko/nazwa wnioskodawcy')).toEqual(['fullname'])
    expect(attrsOfLabel('Adres zamieszkania/siedziby')).toEqual(['address'])
  })

  it('standard places lead to the fields of their section, left-out places carry a note', () => {
    const model = readForm(fpForm())
    const pv = parsePreview(fpPreview())!
    const rows = ledgerRows(fpLedgerSidecar() as never)
    const tg = boxTargets(rows, pv, model)
    expect(tg.get('c2')!.fields).toEqual(['f-imie', 'f-nazwisko'])
    expect(tg.get('c3')!.fields).toEqual(['f-bud'])
    expect(tg.get('c1')!.kind).toBe('out')
    expect(tg.get('c6')!.fields).toEqual(['r-kto'])
    expect([...tg.values()].filter((t) => t.place.box).every(answers)).toBe(true)
  })

  it('a click on a box merged into "Twoje dane" lights both Imię and Nazwisko; a field focus lights the box back', async () => {
    const { fill } = await page([])
    q('.fp-box[data-cid="c2"]').click()
    expect(q('[id="fpw-f-imie"]').classList.contains('clerk-hl')).toBe(true)
    expect(q('[id="fpw-f-nazwisko"]').classList.contains('clerk-hl')).toBe(true)
    // the reverse way: a pick of the field lights the box
    fill.eform.highlight('f-bud')
    q('[id="fpw-f-bud"]').dispatchEvent(new Event('focusin', { bubbles: true }))
    expect(document.querySelector('.fp-box[data-cid="c3"]')).not.toBeNull()
  })

  it('a box that is on purpose no field answers with a plain note instead of silence', async () => {
    await page([])
    const box = q('.fp-box[data-cid="c1"]')
    expect(box.classList.contains('fp-box-out')).toBe(true)
    box.click()
    expect(q('.clerk-boxnote').textContent).toBe('To wypełnia urząd, nie wnioskodawca, dlatego nie ma tego w e-formularzu.')
    expect(q('#fp-where-boxlive').textContent).toContain('wypełnia urząd')
  })
})

describe('BL13 owner round two', () => {
  it('an unlabelled line right under a labelled place is part of it: its click leads there and it has no card', async () => {
    expect(stackedOn([55, 198, 539, 224], [60, 228, 530, 240])).toBe(true)
    expect(stackedOn([55, 198, 539, 224], [60, 300, 530, 312])).toBe(false)
    expect(stackedOn([55, 198, 200, 224], [300, 228, 530, 240])).toBe(false)
    const pv = fpPreview() as { places: Record<string, unknown> }
    pv.places.u1 = { page: 1, kind: 'leader', box: [60, 228, 530, 236] }
    const blank = (box: number[] | null) => ({ code: 'LABEL_NOT_FOUND', page: 1, candidate: 'u1', ...(box ? { box } : {}), evidence: [], detail: 'x' })
    await page([blank([60, 228, 530, 236]), blank(null)], pv, [{ candidate: 'u1', fate: 'AWAITING_DECISION' }])
    expect(document.querySelector('.clerk-card')).toBeNull()
    q('.fp-box[data-cid="u1"]').click()
    expect(q('[id="fpw-f-imie"]').classList.contains('clerk-hl')).toBe(true)
  })

  it('two remarks of one kind on the same place make one card', async () => {
    const at = (c: string) => ({ code: 'LABEL_NOT_FOUND', page: 1, candidate: c, box: [80, 600, 300, 612], evidence: [], detail: 'x' })
    await page([at('x1'), at('x2')])
    expect(all('.clerk-card').length).toBe(1)
    expect(q('#clerk-remarks h3').textContent).toBe('Do sprawdzenia (1)')
  })

  it('the name of a field is edited in its own place: no second copy, Escape gives it back', async () => {
    const { fill } = await page([])
    const label = q('[id="fpw-f-nip"] > label')
    fill.eform.edit('f-nip', () => {})
    const inp = q<HTMLInputElement>('[id="fpw-f-nip"] .clerk-edit-input')
    expect(inp.getAttribute('aria-label')).toBe('Nazwa pola')
    expect(label.hidden).toBe(true)
    expect(document.querySelectorAll('[id="fpw-f-nip"] .clerk-edit label').length).toBe(0)
    inp.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(document.querySelector('[id="fpw-f-nip"] .clerk-edit')).toBeNull()
    expect(label.hidden).toBe(false)
  })
})

describe('BL13 paper-only places', () => {
  it('the server\'s paper-only note is the text of the click; without a ledger row a signature place still answers', async () => {
    const pv = fpPreview() as { places: Record<string, unknown> }
    pv.places.c9 = { page: 1, kind: 'signature', box: [400, 700, 520, 712], label: 'podpis wnioskodawcy' }
    await page([{ code: 'INPUT_NOTE', page: 1, candidate: 'c1', detail: 'paper-only place left out',
      fix: { kind: 'applied', rule: 'paper_only.office_use', text: 'Część „wypełnia urząd” zostaje na papierze.', source: { type: 'paper', page: 1 } } }], pv)
    q('.fp-box[data-cid="c1"]').click()
    expect(q('.clerk-boxnote').textContent).toBe('Część „wypełnia urząd” zostaje na papierze.')
    const sig = q('.fp-box[data-cid="c9"]')
    expect(sig.classList.contains('fp-box-out')).toBe(true)
    sig.click()
    expect(q('.clerk-boxnote').textContent).toContain('wnioskodawca podpisuje wniosek w e-usłudze')
    // an applied note makes no card
    expect(document.querySelector('.clerk-card')).toBeNull()
  })
})

describe('BL13 cards and the signature line', () => {
  it('the signature line is visible without a click when the paper had a signature and date', async () => {
    await page([], fpPreview(), [{ candidate: 'c9', fate: 'LEFT_OUT', reason: 'SIGNATURE_AND_DATE' }])
    expect(q('#clerk-signature-note').textContent).toContain('wnioskodawca podpisuje wniosek w e-usłudze na końcu, po podglądzie')
    document.body.innerHTML = ''
    await page([])
    expect(document.querySelector('#clerk-signature-note')).toBeNull()
  })

  it('"which fields are required" names the fields and its buttons say what they do', async () => {
    const opt = (value: string, current: boolean, v: string[]) => ({ label: value, value, current,
      set: [0, 1].map((i) => ({ pointer: `${GRID}/${i}/field/validation`, value: v })), source: { type: 'rule', name: 'x' } })
    await page([{ code: 'REQUIRED_INFERRED', detail: 'x', fix: { kind: 'choice', rule: 'required.paper_is_silent', text: 'Druk nie mówi (dotyczy 2).',
      options: [opt('optional', true, []), opt('required', false, ['REQUIRED'])] } }])
    const card = q('.clerk-card[data-fix="choice"]')
    expect(card.querySelector('.clerk-card-what')!.textContent).toContain('Dotyczy to pól: „NIP”, „Data urodzenia”.')
    expect(all('.clerk-card[data-fix="choice"] .clerk-fix-btn').map((b) => b.textContent))
      .toEqual(['Zostaw te 2 pola jako nieobowiązkowe (tak jest teraz)', 'Ustaw te 2 pola jako obowiązkowe'])
    expect(all('.clerk-card[data-fix="choice"] .clerk-card-field').map((b) => b.textContent)).toEqual(['NIP', 'Data urodzenia'])
    expect(card.textContent).not.toContain('cały formularz')
    expect(card.querySelector('.clerk-card-main')).toBeNull()
  })

  it('a file without page pictures: words of the paper, no cell address; places with nothing to show share one card', async () => {
    const blank = (c: string, anchor: string) => ({ code: 'LABEL_NOT_FOUND', page: 1, anchor, candidate: c, evidence: [], detail: 'x' })
    await page([blank('c4', 'Formularz!A43'), blank('z1', 'Formularz!A229'), blank('z1', ''), blank('z2', 'Formularz!B229')], fpPreview(false))
    const text = q('#clerk-remarks').textContent!
    expect(text).not.toMatch(/Formularz!|A229|p\[3\]/)
    expect(text).not.toContain('Dla tego formatu pliku nie ma obrazu strony')
    expect(q('.clerk-card .clerk-quote').textContent).toBe('NIP')
    expect(document.querySelector('.clerk-card-rest')).toBeNull()
    // z1 reported twice is one place; the rest is a muted line, not a card, and not in the count
    expect(q('#clerk-rest-line').textContent).toBe('Uwagi techniczne bez miejsca na oryginale: 2. Szczegóły są w widoku dla jury.')
    expect(q('#h-clerk-remarks').textContent).toContain('(1)')
    expect(q('#clerk-final').textContent).toContain('1')
  })

  it('every BL13 text exists in Polish, English and Spanish', () => {
    const keys = Object.keys(pl).filter((k) => k.startsWith('clerk.'))
    for (const k of keys) {
      expect(en, k).toHaveProperty([k])
      expect(es, k).toHaveProperty([k])
    }
  })
})
