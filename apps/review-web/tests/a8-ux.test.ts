// ORDER UI (audit 8, UX): clear result, calm remarks, visible progress, mode badge. Synthetic data only.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mountApp, LONG_MS } from '../src/ui/app'
import { renderConverted, renderProblem } from '../src/ui/result'
import { setLang, pluralIndex } from '../src/lib/i18n'
import { modeOf, adviceKey, causeOf } from '../src/lib/verdict'
import { interpretResponse, type Converted, type Outcome } from '../src/lib/api'
import type { ConvertHooks } from '../src/lib/api'
import { pl } from '../src/i18n/pl'
import { canonical, multipartBody, syntheticForm, syntheticSidecar } from './helpers'

const MP = { 'content-type': 'multipart/mixed; boundary=formularze-abc123' }

async function answer(sidecar: unknown | null, header?: string): Promise<Converted> {
  const hdr: Record<string, string> = { ...MP }
  if (header) hdr['x-converter-warnings'] = header
  const res = await interpretResponse(200, new Headers(hdr), multipartBody(canonical(syntheticForm()), sidecar ? canonical(sidecar) : null))
  if (res.kind !== 'ok') throw new Error('fixture failed')
  return res
}

/** What the service sends for a scan or a sheet it could not read: only standard sections, BRIEF_NOT_READ. */
function nothingReadSidecar() {
  const s = syntheticSidecar()
  s.meta.evidence = {} as typeof s.meta.evidence
  s.warnings = [
    { code: 'BRIEF_NOT_READ', detail: 'the brief was not read' },
    { code: 'NO_MATTER', detail: 'no matter fields' }
  ] as typeof s.warnings
  // two of the six fields stay "standard", the rest have no origin of the paper either
  s.meta.origins = { 's-2': 'standard', 'f-4': 'standard', 'f-5': 'standard' }
  return s
}

beforeEach(() => { setLang('pl'); document.body.innerHTML = '<div id="app"></div>' })
afterEach(() => { vi.useRealTimers() })

describe('ORDER UI 1: the headline', () => {
  it('fields read from the form: a success line with counts and the title, never "Gotowe"', async () => {
    const root = renderConverted(await answer(syntheticSidecar()))
    const h2 = root.querySelector('#h-done') as HTMLElement
    expect(h2.dataset.kind).toBe('ok')
    expect(h2.classList.contains('result-ok')).toBe(true)
    expect(h2.querySelector('.headline')!.textContent).toBe('Formularz przetworzony: 4 pola w 2 sekcjach')
    expect(h2.textContent).toContain('Wniosek próbny')
    expect(h2.querySelector('[lang="pl"]')!.textContent).toBe('„Wniosek próbny”') // lang only on the form's title
    expect(h2.getAttribute('lang')).toBeNull()
    expect(root.textContent).not.toContain('Gotowe')
  })

  it('zero fields read from the form: the amber line, not the success line', async () => {
    const root = renderConverted(await answer(nothingReadSidecar()))
    const h2 = root.querySelector('#h-done') as HTMLElement
    expect(h2.dataset.kind).toBe('partial')
    expect(h2.classList.contains('result-partial')).toBe(true)
    expect(h2.classList.contains('result-ok')).toBe(false)
    expect(h2.querySelector('.headline')!.textContent).toBe(
      'Formularz przetworzony częściowo: odczytano 0 pól z druku, dodano 2 pola standardowe. Sprawdź druk ręcznie.')
    expect(root.textContent).not.toContain('Gotowe')
    expect(root.textContent).not.toContain('Formularz przetworzony: ')
  })

  it('without the report and with a header that says nothing was read: still amber', async () => {
    const root = renderConverted(await answer(null, '2; BRIEF_NOT_READ, OCR_USED'))
    expect((root.querySelector('#h-done') as HTMLElement).dataset.kind).toBe('partial')
  })

  it('without the report and nothing alarming: neutral, neither green nor amber', async () => {
    const root = renderConverted(await answer(null, '1; OCR_USED'))
    const h2 = root.querySelector('#h-done') as HTMLElement
    expect(h2.dataset.kind).toBe('neutral')
    expect(h2.textContent).toContain('Bez raportu nie wiadomo')
  })

  it('the live status line says "częściowo" for the zero answer', async () => {
    const outcome = await answer(nothingReadSidecar())
    mountApp(document.getElementById('app')!, { store: null, status: async () => null, convert: async () => outcome })
    const file = document.getElementById('file') as HTMLInputElement
    Object.defineProperty(file, 'files', { value: [new File([new Uint8Array([1])], 'skan.png')], configurable: true })
    file.dispatchEvent(new Event('change'))
    await new Promise((r) => setTimeout(r, 0))
    expect(document.getElementById('status')!.textContent).toBe('Formularz „Wniosek próbny” przetworzony częściowo: nie odczytano pól z druku.')
  })
})

describe('ORDER UI 2: progress', () => {
  it('shows file, size, a moving bar, seconds and the stage at once; locks the drop zone; long state with Przerwij', async () => {
    vi.useFakeTimers()
    let hooks: ConvertHooks | undefined
    let finish: (o: Outcome) => void = () => undefined
    mountApp(document.getElementById('app')!, {
      store: null, status: async () => null,
      convert: (_f, _t, hk) => { hooks = hk; return new Promise<Outcome>((r) => { finish = r }) }
    })
    expect(document.getElementById('progress')!.hidden).toBe(true)
    const file = document.getElementById('file') as HTMLInputElement
    Object.defineProperty(file, 'files', { value: [new File([new Uint8Array(2048)], 'wniosek.pdf')], configurable: true })
    file.dispatchEvent(new Event('change'))
    // synchronously, i.e. well within 300 ms of the choice
    expect(document.getElementById('progress')!.hidden).toBe(false)
    expect(document.getElementById('progress-file')!.textContent).toBe('Plik: wniosek.pdf (2 KB)')
    const bar = document.getElementById('progress-bar')!
    expect(bar.getAttribute('role')).toBe('progressbar')
    expect(bar.hasAttribute('aria-valuenow')).toBe(false) // no fake percentage
    expect(bar.querySelector('.bar-run')).not.toBeNull()
    expect(document.getElementById('progress-elapsed')!.textContent).toBe('Czas: 0 s')
    expect(document.getElementById('status')!.getAttribute('aria-live')).toBe('polite')
    expect(document.getElementById('status')!.textContent).toBe('Wysyłanie pliku „wniosek.pdf”…')
    expect((document.getElementById('pick') as HTMLButtonElement).disabled).toBe(true)
    expect(file.disabled).toBe(true)
    expect(document.getElementById('drop')!.getAttribute('aria-disabled')).toBe('true')
    hooks!.onUploaded!()
    expect(document.getElementById('status')!.textContent).toBe('Przetwarzanie pliku „wniosek.pdf” (skany i zdjęcia mogą potrwać do 60 s).')
    vi.advanceTimersByTime(3000)
    expect(document.getElementById('progress-elapsed')!.textContent).toBe('Czas: 3 s')
    expect(document.getElementById('progress-longbox')!.hidden).toBe(true)
    vi.advanceTimersByTime(LONG_MS - 3000)
    expect(document.getElementById('progress-longbox')!.hidden).toBe(false)
    expect(document.getElementById('progress-long')!.textContent).toBe('To trwa dłużej niż zwykle. Możesz poczekać albo przerwać.')
    // the live line says it once and keeps it; it does not flip back every second
    const line = document.getElementById('status')!.textContent
    expect(line).not.toContain('To trwa dłużej') // said once, by the panel's own live text, not twice on screen
    expect(document.getElementById('progress-long')!.getAttribute('aria-live')).toBe('polite')
    vi.advanceTimersByTime(2000)
    expect(document.getElementById('status')!.textContent).toBe(line)
    expect(document.getElementById('progress-elapsed')!.textContent).toBe(`Czas: ${LONG_MS / 1000 + 2} s`)
    const cancel = document.getElementById('progress-cancel') as HTMLButtonElement
    expect(cancel.textContent).toBe('Przerwij')
    cancel.click()
    expect(hooks!.signal!.aborted).toBe(true)
    finish({ kind: 'error', code: 'CANCELLED', status: 0, detail: null, title: null })
    await vi.runAllTimersAsync()
    expect(document.getElementById('progress')!.hidden).toBe(true)
    expect((document.getElementById('pick') as HTMLButtonElement).disabled).toBe(false)
    expect(document.querySelector('.error')).toBeNull() // stopping is not a failure
    expect(document.getElementById('status')!.textContent).toContain('Przerwano')
  })
})

describe('ORDER UI 3-5, 8: remarks', () => {
  it('one collapsed calm block with the total, human sentences, codes small, no header line, no English', async () => {
    const root = renderConverted(await answer(syntheticSidecar(), '3; LABEL_NOT_FOUND, SOMETHING_NEW'))
    const box = root.querySelector('details.remarks-box') as HTMLDetailsElement
    expect(box.open).toBe(false)
    expect(box.querySelector('summary')!.textContent).toBe('Uwagi do sprawdzenia przez urzędnika (3)')
    expect(root.querySelectorAll('details.remarks-box').length).toBe(1)
    const text = root.textContent ?? ''
    expect(text).not.toContain('X-Converter-Warnings')
    expect(text).not.toContain('Ostrzeżenia')
    expect(text).not.toContain('×')
    expect(text).not.toContain('po polsku')
    expect(text).toContain('Uwagi: 3')
    expect(text).toContain('Uzupełnij nazwę pola ręcznie w edytorze.')
    const first = box.querySelector('.remark')!
    expect(first.querySelector('.code-line')!.textContent).toBe('(2 miejsca; strona 1) · kod: LABEL_NOT_FOUND')
    expect(first.querySelector('.code')!.textContent).toBe('LABEL_NOT_FOUND')
    // the English detail of a known code is not on the page; the unknown code keeps it under "Szczegóły techniczne"
    expect(text).not.toContain('a box without words beside it')
    const tech = box.querySelectorAll('.remark')[1].querySelector('details.tech') as HTMLDetailsElement
    expect(tech.open).toBe(false)
    expect(tech.querySelector('summary')!.textContent).toBe('Szczegóły techniczne')
  })

  it('"no place on the form" is said once under "Pola z druku", not under every field', async () => {
    const s = syntheticSidecar()
    s.meta.evidence = {} as typeof s.meta.evidence
    const root = renderConverted(await answer(s))
    expect(root.querySelector('#matter-nosource')!.textContent).toBe('Dla części pól (2 z 2) nie ustalono miejsca na druku.')
    for (const li of root.querySelectorAll('.fields .field')) expect(li.textContent).not.toContain('nie ustalono')
  })

  it('field types in words, standard sections named for the e-service', async () => {
    const root = renderConverted(await answer(syntheticSidecar()))
    root.querySelector('#json-text')!.remove() // the JSON itself carries the partner's codes, as it must
    const text = root.textContent ?? ''
    expect(text).not.toContain('TEXT_FIELD')
    expect(text).toContain('jedna odpowiedź')
    expect(text).toContain('Sekcje standardowe e-usługi (2 pola) — kliknij, aby rozwinąć')
    expect(text).not.toContain('partnera')
  })
})

describe('ORDER UI 6, 9: a real failure', () => {
  it('service fault: retry the same file, report the code, never "choose another file"', () => {
    let retried = 0
    const p = renderProblem({ kind: 'error', code: 'GATE_FAILED', status: 500, detail: null, title: null }, { retry: () => { retried++ }, pickOther: () => undefined })
    expect(p.querySelectorAll('.error').length).toBe(1)
    expect(p.querySelector('h2')!.textContent).toBe('Nie udało się przetworzyć pliku')
    expect(p.textContent).toContain('Co zrobić: To błąd usługi, nie pliku. Spróbuj ponownie; jeśli się powtarza, zgłoś kod: GATE_FAILED.')
    expect(p.textContent!.split('To błąd usługi').length - 1).toBe(1) // said once, not in the reason and the advice
    expect(p.textContent).not.toContain('Wybierz inny plik')
    const btn = p.querySelector('#error-action') as HTMLButtonElement
    expect(btn.textContent).toBe('Spróbuj ponownie')
    btn.click()
    expect(retried).toBe(1)
    expect(p.querySelector('.code-line')!.textContent).toBe('Kod: GATE_FAILED · Status HTTP: 500')
  })

  it('file fault: what to do with the file and a button to choose another', () => {
    let picked = 0
    const p = renderProblem({ kind: 'error', code: 'TYPE_MISMATCH', status: 415, detail: 'Rozszerzenie .pdf, a zawartość to plik tekstowy.', title: null },
      { retry: () => undefined, pickOther: () => { picked++ } })
    expect(p.textContent).toContain('Zawartość pliku nie zgadza się z jego rozszerzeniem.')
    expect(p.textContent).toContain('Co zrobić: Otwórz plik w programie, w którym powstał')
    const btn = p.querySelector('#error-action') as HTMLButtonElement
    expect(btn.textContent).toBe('Wybierz inny plik')
    btn.click()
    expect(picked).toBe(1)
  })

  it('every code the backend sends has its own reason; advice falls back by cause', () => {
    for (const code of ['BAD_REQUEST', 'BAD_NAME', 'TOKEN_MISSING', 'TOKEN_INVALID', 'TOKEN_EXPIRED', 'SCOPE', 'TOO_LARGE', 'TOO_MANY_PAGES',
      'TOO_MANY_PIXELS', 'ARCHIVE_LIMIT', 'EXTENSION', 'TYPE_MISMATCH', 'DOC_READER_OFF', 'UNREADABLE', 'NOT_A_FORM', 'ACTIVE_CONTENT', 'BUSY',
      'GATE_FAILED', 'TIMEOUT']) {
      expect(Object.prototype.hasOwnProperty.call(pl, 'problem.' + code), code).toBe(true)
    }
    const has = (k: string) => Object.prototype.hasOwnProperty.call(pl, k)
    expect(adviceKey('GATE_FAILED', has)).toBe('todo.service')
    expect(adviceKey('NEW_CODE', has)).toBe('todo.service')
    expect(adviceKey('ARCHIVE_LIMIT', has)).toBe('todo.file')
    expect(adviceKey('SCOPE', has)).toBe('todo.token')
    expect(causeOf('TIMEOUT')).toBe('service')
  })

  it('the status line for a service fault does not blame the file', async () => {
    const outcome: Outcome = { kind: 'error', code: 'GATE_FAILED', status: 500, detail: null, title: null }
    let calls = 0
    mountApp(document.getElementById('app')!, { store: null, status: async () => null, convert: async () => { calls++; return outcome } })
    const file = document.getElementById('file') as HTMLInputElement
    Object.defineProperty(file, 'files', { value: [new File([new Uint8Array([1])], 'x.docx')], configurable: true })
    file.dispatchEvent(new Event('change'))
    await new Promise((r) => setTimeout(r, 0))
    expect(document.getElementById('status')!.textContent).toBe('Nie udało się przetworzyć pliku.')
    ;(document.getElementById('error-action') as HTMLButtonElement).click()
    await new Promise((r) => setTimeout(r, 0))
    expect(calls).toBe(2) // the same file was sent again
  })
})

describe('ORDER UI 7: the mode badge from GET /status', () => {
  it('maps today and the future states of /status, and is absent when unsure', () => {
    const today = { service: 'x', version: '1', engine: 'rules', auth: 'off', formats: [], limits: {} }
    expect(modeOf(today)).toBe('rules')
    expect(modeOf({ engine: 'rules', model: { state: 'OFF', reason: 'MODEL_STEP=off' } })).toBe('rules')
    expect(modeOf({ engine: 'rules+model', model: { state: 'ON' } })).toBe('model-on')
    expect(modeOf({ engine: 'rules', model: { state: 'UNAVAILABLE' } })).toBe('model-fallback')
    expect(modeOf({ engine: 'rules', model: { state: 'FALLBACK' } })).toBe('model-fallback')
    expect(modeOf({ engine: 'rules-fallback', model: { state: 'ON' } })).toBe('model-fallback')
    for (const bad of [null, undefined, 'rules', [], {}, { engine: 'quantum' }, { engine: 'rules', model: 'on' }, { engine: 'rules', model: {} },
      { engine: 'rules', model: { state: 'MAYBE' } }]) {
      expect(modeOf(bad), JSON.stringify(bad)).toBeNull()
    }
  })

  it('shows the words in the header next to the language switch; a failed /status shows no badge', async () => {
    mountApp(document.getElementById('app')!, { store: null, status: async () => ({ engine: 'rules' }) })
    await new Promise((r) => setTimeout(r, 0))
    const badge = document.getElementById('mode')!
    expect(badge.closest('header')).not.toBeNull()
    expect(badge.hidden).toBe(false)
    expect(badge.textContent).toBe('Tryb: reguły i lokalny OCR, bez modelu AI')
    expect(badge.getAttribute('title')).toBe('Plik przetwarza tylko ta usługa; nic nie jest wysyłane do usług zewnętrznych.')

    document.body.innerHTML = '<div id="app"></div>'
    mountApp(document.getElementById('app')!, { store: null, status: async () => ({ engine: 'rules', model: { state: 'UNAVAILABLE' } }) })
    await new Promise((r) => setTimeout(r, 0))
    expect(document.getElementById('mode')!.textContent).toBe('Model AI: niedostępny, działają reguły')
    expect(document.getElementById('mode')!.hasAttribute('title')).toBe(false)

    document.body.innerHTML = '<div id="app"></div>'
    mountApp(document.getElementById('app')!, { store: null, status: async () => { throw new Error('down') } })
    await new Promise((r) => setTimeout(r, 0))
    expect(document.getElementById('mode')!.hidden).toBe(true)
    expect(document.getElementById('mode')!.textContent).toBe('')
  })
})

describe('Polish wording', () => {
  it('plural forms', () => {
    expect([1, 2, 4, 5, 12, 14, 22, 25, 112, 0].map((n) => pluralIndex('pl', n))).toEqual([0, 1, 1, 2, 2, 2, 1, 2, 2, 2])
    expect([1, 2, 5].map((n) => pluralIndex('en', n))).toEqual([0, 2, 2])
  })

  it('the Polish dictionary carries no "Gotowe", no header name, no "(po polsku)", no "papier"', () => {
    const all = Object.values(pl).join('\n')
    expect(all).not.toMatch(/Gotowe|X-Converter-Warnings|X-Converter-Engine|po polsku|\bpapier(u|ze|em)?\b/i)
  })
})
