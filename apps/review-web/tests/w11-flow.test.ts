// W11 FLOW: progress by the stages the service reports, the service's queue, several files at once. Synthetic data.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mountApp } from '../src/ui/app'
import { setLang } from '../src/lib/i18n'
import {
  CANCELLED, FULL_TRIES_MAX, JOB_LOST, POLL_FAILS_MAX, convertQueued, interpretResponse, parseJobStatus,
  type Answer, type ConvertHooks, type Converted, type JobIo, type JobStatus, type Outcome
} from '../src/lib/api'
import { MAX_FILES, newItem, percentOf, stageText, aliveText, tally } from '../src/ui/queue-model'
import { canonical, multipartBody, syntheticForm, syntheticSidecar } from './helpers'

const MP = 'multipart/mixed; boundary=formularze-abc123'
const enc = new TextEncoder()
const json = (o: unknown): Uint8Array => enc.encode(JSON.stringify(o))

function running(done: number, stage: Record<string, unknown>, extra: Record<string, unknown> = {}): Record<string, unknown> {
  return { id: 'j1', state: 'running', queue: { running: 1, waiting: 0, waiting_max: 20 }, stage, units: { done, total: 100 }, stage_s: 4.2, ...extra }
}

async function okOutcome(): Promise<Converted> {
  const res = await interpretResponse(200, new Headers({ 'content-type': MP }), multipartBody(canonical(syntheticForm()), canonical(syntheticSidecar())))
  if (res.kind !== 'ok') throw new Error('fixture failed')
  return res
}

/** A service made of a script: what POST answers (in order) and what each GET of the state answers (in order). */
function fakeIo(posts: Answer[], states: Array<Record<string, unknown> | 'fail' | 404>, result?: { status: number; type: string; body: Uint8Array }) {
  const calls: string[] = []
  const io: JobIo = {
    submit: async (_f, _t, onSent) => { calls.push('POST'); onSent(5, 10); onSent(10, 10); return posts.shift()! },
    fetcher: async (url, init) => {
      calls.push(`${init.method} ${url}`)
      if (init.method === 'DELETE') return new Response('{}', { status: 200 })
      if (url.endsWith('/result?report=1')) {
        return new Response(result!.body as BodyInit, { status: result!.status, headers: { 'content-type': result!.type } })
      }
      const next = states.shift()
      if (next === 'fail' || next === undefined) throw new Error('down')
      if (next === 404) return new Response('{"code":"NOT_FOUND"}', { status: 404, headers: { 'content-type': 'application/problem+json' } })
      return new Response(JSON.stringify(next), { status: 200, headers: { 'content-type': 'application/json' } })
    },
    sleep: async () => undefined,
    direct: async () => { calls.push('DIRECT'); return { kind: 'error', code: 'OLD', status: 0, detail: null, title: null } }
  }
  return { io, calls }
}

const taken = (body: Record<string, unknown> = { id: 'j1', state: 'queued', position: 2, queue: { running: 2, waiting: 2, waiting_max: 20 }, units: { done: 0, total: 100 } }): Answer =>
  ({ status: 202, headers: new Headers({ 'content-type': 'application/json' }), bytes: json(body) })
const file = (name = 'wniosek.pdf', size = 2048): File => new File([new Uint8Array(size)], name)

beforeEach(() => { setLang('pl'); document.body.innerHTML = '<div id="app"></div>' })
afterEach(() => { vi.useRealTimers() })

describe('W11 FLOW: the answer about a job', () => {
  it('is read field by field; what is missing is null, what is not a job is null', () => {
    const s = parseJobStatus(running(31.5, { name: 'reading', step: 'ocr', page: 3, pages: 7 }))!
    expect(s.stage).toEqual({ name: 'reading', step: 'ocr', page: 3, pages: 7 })
    expect(s.units).toEqual({ done: 31.5, total: 100 })
    expect(s.stageS).toBe(4.2)
    expect(parseJobStatus({ id: 'x', state: 'queued', position: 4 })!.units).toBeNull()
    expect(parseJobStatus({ id: 'x', state: 'flying' })).toBeNull()
    expect(parseJobStatus('text')).toBeNull()
    expect(parseJobStatus({ id: 'x', state: 'running', units: { done: 5, total: 0 } })!.units).toBeNull()
  })
})

describe('W11 FLOW: percent and words come from the service, never from a clock', () => {
  it('percent is the finished parts over all parts; unknown stays unknown', () => {
    const item = newItem(1, file())
    expect(percentOf(item)).toBeNull()
    item.phase = 'sending'
    item.sent = { loaded: 5, total: 10 }
    expect(percentOf(item)).toBeNull() // bytes sent are not work done on the form
    expect(stageText(item, 0)).toBe('Wysyłam plik do usługi: 50%.')
    item.phase = 'taken'
    expect(percentOf(item)).toBeNull() // a service that tells no state: no number
    item.status = parseJobStatus({ id: 'j', state: 'queued', position: 3, units: { done: 0, total: 100 } })
    expect(percentOf(item)).toBe(0)
    expect(stageText(item, 0)).toBe('Czeka w kolejce na miejscu 3: przed nim 2.')
    item.status = parseJobStatus(running(31.5, { name: 'reading', step: 'ocr', page: 3, pages: 7 }))
    expect(percentOf(item)).toBe(31)
    expect(stageText(item, 0)).toBe('Czytam stronę 3 z 7: rozpoznaję tekst ze skanu.')
    expect(stageText(item, 999_999)).toBe(stageText(item, 0)) // time changes nothing
    expect(percentOf(item)).toBe(31)
    item.status = parseJobStatus(running(40, { name: 'reading', step: 'shapes', page: 2 }))
    expect(stageText(item, 0)).toBe('Szukam linii i kratek na stronie 2.')
    item.status = parseJobStatus(running(90, { name: 'checks' }))
    expect(stageText(item, 0)).toBe('Sprawdzam e-formularz.')
    item.status = parseJobStatus(running(90, { name: 'a-stage-of-tomorrow' }))
    expect(stageText(item, 0)).toBe('Usługa przetwarza plik.')
  })

  it('the sign of life says how long the stage lasts and when the service last answered', () => {
    const item = newItem(1, file())
    item.phase = 'taken'
    item.status = parseJobStatus(running(31.5, { name: 'reading', step: 'ocr', page: 1, pages: 1 }, { stage_s: 42.7 }))
    item.answeredAt = 10_000
    expect(aliveText(item, 11_000)).toBe('Ten etap trwa 42 s. Usługa pracuje: ostatnio odpowiedziała 1 s temu.')
    item.silent = 3
    expect(aliveText(item, 14_000)).toBe('Usługa nie odpowiada od 4 s. Czekam i pytam dalej.')
  })
})

describe('W11 FLOW: one file through the queue of the service', () => {
  it('sends, is told its place, follows the stages and returns the result of /convert', async () => {
    const body = multipartBody(canonical(syntheticForm()), canonical(syntheticSidecar()))
    const { io, calls } = fakeIo([taken()], [
      { id: 'j1', state: 'queued', position: 1, units: { done: 0, total: 100 } },
      running(4, { name: 'reading', step: 'ocr', page: 1, pages: 2 }),
      { id: 'j1', state: 'done', units: { done: 100, total: 100 } }
    ], { status: 200, type: MP, body })
    const seen: string[] = []
    const hooks: ConvertHooks = {
      onSent: (l, t) => seen.push(`sent ${l}/${t}`), onUploaded: () => seen.push('uploaded'),
      onStatus: (s: JobStatus) => seen.push(`${s.state}:${s.position ?? '-'}:${s.units?.done ?? '-'}`)
    }
    const out = await convertQueued(file(), '', hooks, io)
    expect(out.kind).toBe('ok')
    expect(seen).toEqual(['sent 5/10', 'sent 10/10', 'uploaded', 'queued:2:0', 'queued:1:0', 'running:-:4', 'done:-:100'])
    expect(calls.at(-1)).toBe('GET ../v1/jobs/j1/result?report=1')
  })

  it('a full queue is not a failure: the file is offered again after the time the service names', async () => {
    const full: Answer = { status: 429, headers: new Headers({ 'content-type': 'application/problem+json', 'retry-after': '10' }), bytes: json({ code: 'QUEUE_FULL', status: 429 }) }
    const body = multipartBody(canonical(syntheticForm()), null)
    const { io, calls } = fakeIo([full, full, taken({ id: 'j1', state: 'done', units: { done: 100, total: 100 } })], [], { status: 200, type: MP, body })
    const waits: number[] = []
    const out = await convertQueued(file(), '', { onFull: (s) => waits.push(s) }, io)
    expect(out.kind).toBe('ok')
    expect(waits).toEqual([10, 10])
    expect(calls.filter((c) => c === 'POST').length).toBe(3)
    expect(FULL_TRIES_MAX).toBeGreaterThan(10)
  })

  it('a refusal of the file comes back at once with the code of the service', async () => {
    const refused: Answer = { status: 415, headers: new Headers({ 'content-type': 'application/problem+json' }), bytes: json({ code: 'EXTENSION', status: 415, title: 'x' }) }
    const { io, calls } = fakeIo([refused], [])
    const out = await convertQueued(file('a.exe'), '', {}, io)
    expect(out).toMatchObject({ kind: 'error', code: 'EXTENSION', status: 415 })
    expect(calls).toEqual(['POST'])
  })

  it('a job that failed returns its problem; a service without jobs gets the old request', async () => {
    const { io } = fakeIo([taken()], [{ id: 'j1', state: 'error', error: { code: 'UNREADABLE', status: 422 } }],
      { status: 422, type: 'application/problem+json', body: json({ code: 'UNREADABLE', status: 422, detail: 'd' }) })
    expect(await convertQueued(file(), '', {}, io)).toMatchObject({ kind: 'error', code: 'UNREADABLE', status: 422, detail: 'd' })
    const old = fakeIo([{ status: 404, headers: new Headers(), bytes: new Uint8Array() }], [])
    expect(await convertQueued(file(), '', {}, old.io)).toMatchObject({ code: 'OLD' })
    expect(old.calls).toEqual(['POST', 'DIRECT'])
  })

  it('silence is counted and ends as NETWORK; a job the service forgot is JOB_LOST; stopping tells the service', async () => {
    const silent: number[] = []
    const down = fakeIo([taken()], Array(POLL_FAILS_MAX).fill('fail'))
    expect(await convertQueued(file(), '', { onSilent: (n) => silent.push(n) }, down.io)).toMatchObject({ code: 'NETWORK' })
    expect(silent.length).toBe(POLL_FAILS_MAX)
    const lost = fakeIo([taken()], [404])
    expect(await convertQueued(file(), '', {}, lost.io)).toMatchObject({ code: JOB_LOST })
    const stop = new AbortController()
    const gone = fakeIo([taken()], [running(4, { name: 'reading' })])
    gone.io.sleep = async () => { stop.abort() }
    expect(await convertQueued(file(), '', { signal: stop.signal }, gone.io)).toMatchObject({ code: CANCELLED })
    expect(gone.calls).toContain('DELETE ../v1/jobs/j1')
  })
})

function choose(files: File[]): void {
  const input = document.getElementById('file') as HTMLInputElement
  Object.defineProperty(input, 'files', { value: files, configurable: true })
  input.dispatchEvent(new Event('change'))
}

describe('W11 FLOW: the page, one file', () => {
  it('fills the bar only as far as the service reported and names the stage; time alone moves nothing', async () => {
    vi.useFakeTimers()
    let hooks: ConvertHooks | undefined
    let finish: (o: Outcome) => void = () => undefined
    mountApp(document.getElementById('app')!, {
      store: null, status: async () => null,
      convert: (_f, _t, hk) => { hooks = hk; return new Promise<Outcome>((r) => { finish = r }) }
    })
    choose([file('skan.png')])
    const bar = document.getElementById('progress-bar')!
    expect(bar.hasAttribute('aria-valuenow')).toBe(false) // nothing reported yet: no number
    hooks!.onSent!(512, 2048)
    expect(document.getElementById('progress-stage')!.textContent).toBe('Wysyłam plik do usługi: 25%.')
    expect(bar.hasAttribute('aria-valuenow')).toBe(false)
    hooks!.onUploaded!()
    hooks!.onStatus!(parseJobStatus({ id: 'j', state: 'queued', position: 2, units: { done: 0, total: 100 } })!)
    expect(bar.getAttribute('aria-valuenow')).toBe('0')
    expect(document.getElementById('status')!.textContent).toBe('Czeka w kolejce na miejscu 2: przed nim 1.')
    hooks!.onStatus!(parseJobStatus(running(31.5, { name: 'reading', step: 'ocr', page: 3, pages: 7 }))!)
    expect(bar.getAttribute('aria-valuenow')).toBe('31')
    expect((bar.querySelector('.bar-fill') as HTMLElement).style.width).toBe('31%')
    expect(document.getElementById('progress-stage')!.textContent).toBe('Czytam stronę 3 z 7: rozpoznaję tekst ze skanu. Wykonano 31% pracy.')
    expect(document.getElementById('status')!.textContent).toBe('Czytam stronę 3 z 7: rozpoznaję tekst ze skanu.')
    expect(document.getElementById('progress-alive')!.textContent).toContain('Ten etap trwa 4 s.')
    vi.advanceTimersByTime(60_000) // a minute passes and the service reports nothing new
    expect(bar.getAttribute('aria-valuenow')).toBe('31')
    expect(document.getElementById('progress-elapsed')!.textContent).toBe('Czas: 60 s')
    expect(document.getElementById('progress-alive')!.textContent).toContain('ostatnio odpowiedziała 60 s temu')
    finish(await okOutcome())
    await vi.runAllTimersAsync()
    expect(document.getElementById('progress')!.hidden).toBe(true)
    expect(document.querySelector('#h-done')).not.toBeNull()
    expect(document.getElementById('queue')!.hidden).toBe(true)
  })
})

describe('W11 FLOW: the page, several files', () => {
  it('takes them all, shows each with its own state, keeps every result openable; one failure stops nothing', async () => {
    const ok = await okOutcome()
    const ends: Array<(o: Outcome) => void> = []
    const hooksOf: ConvertHooks[] = []
    const names: string[] = []
    mountApp(document.getElementById('app')!, {
      store: null, status: async () => null,
      convert: (f, _t, hk) => { names.push(f.name); hooksOf.push(hk!); return new Promise<Outcome>((r) => { ends.push(r) }) }
    })
    expect((document.getElementById('file') as HTMLInputElement).multiple).toBe(true)
    choose([file('a.pdf'), file('b.jpg'), file('c.docx')])
    const tick = (): Promise<void> => new Promise((r) => setTimeout(r, 0))
    expect(document.getElementById('queue')!.hidden).toBe(false)
    expect(document.getElementById('progress')!.hidden).toBe(true)
    const rows = (): HTMLElement[] => [...document.querySelectorAll<HTMLElement>('#queue-list .q-row')]
    expect(rows().length).toBe(3)
    expect(names).toEqual(['a.pdf']) // the next file is sent when the service has taken this one
    expect(rows().map((r) => r.dataset.phase)).toEqual(['sending', 'pending', 'pending'])
    hooksOf[0].onUploaded!()
    await tick()
    hooksOf[1].onUploaded!()
    await tick()
    expect(names).toEqual(['a.pdf', 'b.jpg', 'c.docx'])
    hooksOf[0].onStatus!(parseJobStatus(running(50, { name: 'reading', step: 'native', page: 2, pages: 4 }))!)
    hooksOf[1].onStatus!(parseJobStatus({ id: 'k', state: 'queued', position: 1, units: { done: 0, total: 100 } })!)
    expect(rows()[0].querySelector('.q-stage')!.textContent).toBe('Czytam stronę 2 z 4.')
    expect(rows()[0].querySelector('.q-pct')!.textContent).toBe('50%')
    expect(rows()[0].querySelector('.bar')!.getAttribute('aria-valuenow')).toBe('50')
    expect(rows()[1].querySelector('.q-stage')!.textContent).toBe('Czeka w kolejce: jest następny.')
    // the second file fails: the others go on
    ends[1]({ kind: 'error', code: 'UNREADABLE', status: 422, detail: null, title: null })
    await tick()
    expect(rows()[1].dataset.phase).toBe('failed')
    expect(rows()[1].querySelector('.q-stage')!.textContent).toContain('Nie udało się: Nie udało się odczytać pliku')
    expect(document.querySelector('#h-error')).toBeNull() // a failure in the list is not thrown over the page
    ends[0](ok)
    await tick()
    expect(rows()[0].dataset.phase).toBe('done')
    expect(document.querySelector('#h-done')).not.toBeNull() // the first finished file is shown
    expect(document.getElementById('result-which')!.textContent).toBe('Wynik pliku: a.pdf')
    expect((document.getElementById('pick') as HTMLButtonElement).disabled).toBe(true) // the third still works
    ends[2](ok)
    await tick()
    expect(rows().map((r) => r.dataset.phase)).toEqual(['done', 'failed', 'done'])
    expect(document.getElementById('status')!.textContent).toBe('Zakończono: przetworzone 2 z 3, nieudane 1.')
    expect((document.getElementById('pick') as HTMLButtonElement).disabled).toBe(false)
    // every result stays openable
    rows()[2].querySelector<HTMLButtonElement>('.q-open')!.click()
    expect(document.getElementById('result-which')!.textContent).toBe('Wynik pliku: c.docx')
    expect(rows()[2].classList.contains('selected')).toBe(true)
    rows()[1].querySelector<HTMLButtonElement>('.q-open')!.click()
    expect(document.querySelector('#h-error')).not.toBeNull()
    expect(document.getElementById('result-which')!.textContent).toBe('Wynik pliku: b.jpg')
    rows()[0].querySelector<HTMLButtonElement>('.q-open')!.click()
    expect(document.querySelector('#h-done')).not.toBeNull()
  })

  it('more files than the page takes at once: the rest are named as skipped, nothing is silently dropped', async () => {
    const ok = await okOutcome()
    mountApp(document.getElementById('app')!, { store: null, status: async () => null, convert: async (_f, _t, hk) => { hk?.onUploaded?.(); return ok } })
    choose(Array.from({ length: MAX_FILES + 2 }, (_, i) => file(`f${i}.pdf`)))
    await new Promise((r) => setTimeout(r, 20))
    const phases = [...document.querySelectorAll<HTMLElement>('#queue-list .q-row')].map((r) => r.dataset.phase)
    expect(phases.filter((p) => p === 'done').length).toBe(MAX_FILES)
    expect(phases.filter((p) => p === 'skipped').length).toBe(2)
    expect(document.querySelector('#queue-list .q-row[data-phase="skipped"] .q-stage')!.textContent).toContain(`najwyżej ${MAX_FILES} plików`)
    expect(tally([newItem(1, file()), newItem(2, file(), 'skipped')])).toEqual({ all: 2, done: 0, failed: 0, active: 1, other: 1 })
  })

  it('a waiting file can be given up before it is sent; the others are sent', async () => {
    const ok = await okOutcome()
    const ends: Array<(o: Outcome) => void> = []
    const names: string[] = []
    mountApp(document.getElementById('app')!, {
      store: null, status: async () => null,
      convert: (f) => { names.push(f.name); return new Promise<Outcome>((r) => { ends.push(r) }) }
    })
    choose([file('a.pdf'), file('b.pdf'), file('c.pdf')])
    const rows = [...document.querySelectorAll<HTMLElement>('#queue-list .q-row')]
    rows[1].querySelector<HTMLButtonElement>('.q-cancel')!.click()
    expect(rows[1].dataset.phase).toBe('cancelled')
    ends[0](ok)
    await new Promise((r) => setTimeout(r, 0))
    expect(names).toEqual(['a.pdf', 'c.pdf'])
    ends[1](ok)
    await new Promise((r) => setTimeout(r, 0))
    expect(rows.map((r) => r.dataset.phase)).toEqual(['done', 'cancelled', 'done'])
  })
})

describe('W11 FLOW: the access-token row', () => {
  it('is hidden when the service says it asks for no token, and comes back when a request is refused for the token', async () => {
    mountApp(document.getElementById('app')!, {
      store: null, status: async () => ({ auth: 'off' }),
      convert: async () => ({ kind: 'error', code: 'TOKEN_MISSING', status: 401, detail: null, title: null })
    })
    await new Promise((r) => setTimeout(r, 0))
    expect(document.getElementById('token-row')!.hidden).toBe(true)
    choose([file()])
    await new Promise((r) => setTimeout(r, 0))
    expect(document.getElementById('token-row')!.hidden).toBe(false)
  })

  it('stays when the service asks for a token or says nothing', async () => {
    mountApp(document.getElementById('app')!, { store: null, status: async () => ({ auth: 'jwt' }), convert: async () => okOutcome() })
    await new Promise((r) => setTimeout(r, 0))
    expect(document.getElementById('token-row')!.hidden).toBe(false)
    document.body.innerHTML = '<div id="app"></div>'
    mountApp(document.getElementById('app')!, { store: null, status: async () => null, convert: async () => okOutcome() })
    await new Promise((r) => setTimeout(r, 0))
    expect(document.getElementById('token-row')!.hidden).toBe(false)
  })
})
