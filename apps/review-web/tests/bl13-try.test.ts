// BL13 TRY-F: the progressive trial fill (one step open, never a disabled button) and the day of filing (today's
// date for the filing date only, never for a birth date). Synthetic forms, places and people only.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { interpretResponse, type Converted } from '../src/lib/api'
import { mountFill } from '../src/ui/fill'
import { buildSheets } from '../src/ui/print'
import { filingKind, todayIso, todayPl } from '../src/lib/fp/today'
import { filingValue } from '../src/lib/fp/fill'
import { joinPlaces, parsePreview } from '../src/lib/fp/places'
import type { ENode } from '../src/lib/fp/form'
import { canonical, multipartBody } from './helpers'
import { fpForm, fpLedgerSidecar, fpPreview } from './fp-fixture'

const DAY = new Date(2026, 10, 22, 0, 30) // half past midnight: a UTC date would still say the 21st

beforeEach(() => { document.body.innerHTML = ''; document.body.className = '' })
afterEach(() => { vi.useRealTimers() })

const node = (type: string, title: string, techName = ''): ENode => ({ type, title, techName } as unknown as ENode)

describe('BL13 the day of filing', () => {
  it('today by the local calendar, in the form format and in the Polish paper format', () => {
    expect(todayIso(DAY)).toBe('2026-11-22')
    expect(todayPl(DAY)).toBe('22.11.2026')
  })

  it('only labels that name the filing or signing date count', () => {
    for (const l of ['Data', 'data:', 'Data wypełnienia', 'data złożenia wniosku', 'Dnia', 'Data sporządzenia', '(data)', 'data_wypelnienia'])
      expect(filingKind(l), l).toBe('date')
    for (const l of ['Miejscowość i data', 'miejscowość, data', 'Miejscowość, dnia'])
      expect(filingKind(l), l).toBe('placeDate')
    for (const l of ['Data urodzenia', 'Data urodzenia psa', 'Data szczepienia', 'Data zdarzenia', 'Podpis', 'Miejscowość', 'Data ważności dowodu', ''])
      expect(filingKind(l), l).toBeNull()
  })

  it('a filing-date field takes today; a birth date or a signature never does', () => {
    vi.useFakeTimers(); vi.setSystemTime(DAY)
    expect(filingValue(node('DATEPICKER', 'Data wypełnienia'))).toBe('2026-11-22')
    expect(filingValue(node('TEXT_FIELD', 'Data'))).toBe('') // a bare 'Data' field outside a signing section is content
    const signing = { ...node('SECTION', 'Oświadczenie i podpis'), parent: null } as unknown as ENode
    expect(filingValue({ ...node('TEXT_FIELD', 'Data'), parent: signing } as unknown as ENode)).toBe('22.11.2026')
    const events = { ...node('SECTION', 'Wykaz szczepień'), parent: null } as unknown as ENode
    expect(filingValue({ ...node('DATEPICKER', 'Data'), parent: events } as unknown as ENode)).toBe('')
    expect(filingValue(node('TEXT_FIELD', 'Miejscowość i data'), 'Bydgoszcz')).toBe('Bydgoszcz, 22.11.2026')
    expect(filingValue(node('TEXT_FIELD', 'Pole', 'data_zlozenia'))).toBe('22.11.2026')
    expect(filingValue(node('DATEPICKER', 'Data urodzenia'))).toBe('')
    expect(filingValue(node('TEXT_FIELD', 'Podpis wnioskodawcy'))).toBe('')
    expect(filingValue(node('CHECKBOX', 'Data'))).toBe('')
  })

  it("the paper's own date place (left out of the form) is a date place; a signature place is not", () => {
    const pv = parsePreview({ ...fpPreview(), places: {
      d1: { page: 1, kind: 'leader', box: [380, 68, 524, 80], label: 'data' },
      d2: { page: 1, kind: 'signature', box: [404, 477, 524, 489], label: 'data i podpis' },
      d3: { page: 1, kind: 'leader', box: [71, 140, 230, 152], label: 'data urodzenia' }
    } })!
    const j = joinPlaces([
      { candidate: 'd1', fate: 'LEFT_OUT', reason: 'SIGNATURE_AND_DATE' },
      { candidate: 'd2', fate: 'LEFT_OUT', reason: 'SIGNATURE_AND_DATE' },
      { candidate: 'd3', fate: 'LEFT_OUT', reason: 'OTHER' }
    ], pv)
    expect(j.dates?.map((d) => d.cid)).toEqual(['d1'])
  })

  it("the print writes today's date above the paper's date line; the birth date stays the person's", async () => {
    vi.useFakeTimers({ toFake: ['Date'] }); vi.setSystemTime(DAY)
    const sc = fpLedgerSidecar() as unknown as { meta: { ledger: { rows: unknown[] } } }
    sc.meta.ledger.rows.push({ candidate: 'c9', fate: 'LEFT_OUT', reason: 'SIGNATURE_AND_DATE' })
    const pv = fpPreview() as unknown as { places: Record<string, unknown> }
    pv.places.c9 = { page: 1, kind: 'leader', box: [380, 68, 524, 80], label: 'data' }
    const res = await interpretResponse(200, new Headers({ 'content-type': 'multipart/mixed; boundary=formularze-abc123' }),
      multipartBody(canonical(fpForm()), canonical(sc)))
    const b = mountFill(res as Converted, Promise.resolve(pv))
    document.body.append(b.el)
    await b.where.ready
    ;(document.querySelector('#fp-scan') as HTMLElement).click()
    ;(document.querySelector('[data-person="0"]') as HTMLElement).click()
    ;(document.querySelector('#fp-fill') as HTMLElement).click()
    expect((document.querySelector('[id="fpf-f-data"]') as HTMLInputElement).value).not.toBe('2026-11-22')
    const s = buildSheets(b.eform, b.where, b.citizen.record())!
    const dated = [...s.sheets[0].querySelectorAll<HTMLElement>('.fp-glyph[data-cid="c9"]')].map((g) => g.textContent)
    expect(dated).toEqual(['22.11.2026'])
  })
})

describe('BL13 the trial fill opens one step at a time', () => {
  async function block() {
    const res = await interpretResponse(200, new Headers({ 'content-type': 'multipart/mixed; boundary=formularze-abc123' }),
      multipartBody(canonical(fpForm()), canonical(fpLedgerSidecar())))
    const b = mountFill(res as Converted, Promise.resolve(fpPreview()))
    document.body.append(b.el)
    await b.where.ready
    await Promise.resolve()
    return b
  }
  const shown = (): HTMLButtonElement[] => [...document.querySelectorAll<HTMLButtonElement>('#fp-citizen button, #fp-check-step button, #fp-print-step button')]
    .filter((x) => !x.closest('[hidden]') && !x.hidden)
  const ids = (): string[] => shown().filter((x) => !x.closest('details')).map((x) => x.id || x.getAttribute('data-person') || '?')
  const click = (s: string): void => { (document.querySelector(s) as HTMLElement).click() }

  it('start: one button; each step opens the next; no disabled button on screen at any step', async () => {
    await block()
    expect(ids()).toEqual(['fp-scan'])
    click('#fp-scan')
    expect(ids()).toEqual(['0', '1', '2', '3', '4'])
    expect(document.activeElement?.getAttribute('data-person')).toBe('0')
    expect((document.querySelector('#fp-done-scan') as HTMLElement).hidden).toBe(false)
    click('[data-person="0"]')
    expect(ids()).toEqual(['fp-scan-again', 'fp-change', 'fp-fill'])
    expect(document.activeElement?.id).toBe('fp-fill')
    click('#fp-fill')
    expect(ids()).toEqual(['fp-scan-again', 'fp-change', 'fp-clear', 'fp-check'])
    expect(document.activeElement?.id).toBe('fp-check')
    expect((document.querySelector('#fp-print-step') as HTMLElement).hidden).toBe(true)
    expect(document.querySelectorAll('.fp-field.fp-just-filled').length).toBeGreaterThan(0) // what was filled lights up
    expect(document.querySelector('#fp-fill-result')?.textContent).toMatch(/Następny krok: sprawdź poprawność\.$/)
    click('#fp-check')
    expect((document.querySelector('#fp-print-step') as HTMLElement).hidden).toBe(false)
    expect(document.querySelector('#fp-check-next')?.textContent).toMatch(/wydruk/)
    expect(document.activeElement?.closest('#fp-print-step')).not.toBeNull() // the next action has the focus
    expect(ids()).toContain('fp-print-sheet')
    for (const b of shown()) expect(b.disabled, b.id).toBe(false)
    click('#fp-clear')
    expect(ids()).toEqual(['fp-scan'])
    expect((document.querySelector('#fp-check-step') as HTMLElement).hidden).toBe(true)
    expect((document.querySelector('#fp-check-result') as HTMLElement).textContent).toBe('')
  })

  it('change the person: back to the list, the check and the print close again', async () => {
    await block()
    click('#fp-scan'); click('[data-person="1"]'); click('#fp-fill'); click('#fp-check')
    click('#fp-change')
    expect(ids()).toEqual(['0', '1', '2', '3', '4'])
    expect((document.querySelector('#fp-check-step') as HTMLElement).hidden).toBe(true)
    expect((document.querySelector('#fp-print-step') as HTMLElement).hidden).toBe(true)
  })
})
