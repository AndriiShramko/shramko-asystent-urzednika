// Wave 11 KEY: the block "Model AI (opcjonalnie)". Synthetic data only; every key here is invented.
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { checkModel, fetchAiState, forgetSession, masked, parseCheck, parseState, typedOf, useInSession, CODES,
  type AiState, type Changed, type CheckResult, type Typed } from '../src/lib/aimodel'
import { hasKey, LANGS, setLang } from '../src/lib/i18n'
import { modeOf } from '../src/lib/verdict'
import { mountApp } from '../src/ui/app'
import { attachModelKey, mountModelKey, type ModelKeyDeps } from '../src/ui/modelkey'

const PAGE_KEY = 'FAKE-PAGE-KEY-do-not-show-tailP'
const ENV: AiState = { state: 'on', source: 'environment', pageConfig: true, model: 'open-lab/Open-Model-3B',
  address: 'https://models.example.test/v1', used: false, keySet: true, keyOrigin: 'environment-variable', keyTail: 'ailE', keyFull: '', problem: '' }
const OFF: AiState = { state: 'off', source: 'none', pageConfig: true, model: '', address: '', used: false, keySet: false,
  keyOrigin: '', keyTail: '', keyFull: '', problem: '' }

const tick = async (): Promise<void> => { for (let i = 0; i < 6; i++) await Promise.resolve() }
const $ = <T extends HTMLElement>(root: HTMLElement, sel: string): T => root.querySelector(sel) as T

function deps(first: AiState | null, over: Partial<ModelKeyDeps> = {}) {
  let current = first
  const calls = { check: [] as Typed[], use: [] as Typed[], forget: 0, state: 0 }
  const d: ModelKeyDeps = {
    token: () => '',
    state: async () => { calls.state++; return current },
    check: async (typed): Promise<CheckResult> => { calls.check.push(typed); return { ok: true, code: 'ok', http: 200, ms: 1234 } },
    use: async (typed): Promise<Changed> => {
      calls.use.push(typed)
      current = { ...(current ?? OFF), state: 'on', source: 'session', keySet: true, keyOrigin: 'session', keyTail: '',
        address: typed.base_url ?? current?.address ?? '', model: typed.model ?? current?.model ?? '' }
      return { ok: true, code: 'ok', state: current }
    },
    forget: async (): Promise<Changed> => { calls.forget++; current = first; return { ok: true, code: 'ok', state: first } },
    ...over
  }
  return { d, calls, set: (s: AiState | null) => { current = s } }
}

async function mounted(first: AiState | null, over: Partial<ModelKeyDeps> = {}) {
  const made = deps(first, over)
  const block = mountModelKey(made.d)
  document.body.append(block.el)
  await tick()
  return { ...made, block, el: block.el }
}

function type(input: HTMLInputElement, value: string): void {
  input.value = value
  input.dispatchEvent(new Event('input'))
}

beforeEach(() => { setLang('pl'); document.body.innerHTML = '' })

describe('what the service says is read defensively', () => {
  it('reads the state and never invents one', () => {
    expect(parseState(null)).toBeNull()
    expect(parseState({ state: 'maybe' })).toBeNull()
    expect(parseState({ state: 'off', source: 'none', page_config: true })).toEqual(OFF)
    const s = parseState({ state: 'fallback', source: 'environment', page_config: true, model: 'm', address: 'https://a.test/v1',
      used: true, reason: 'http_401', problem: 'bad_key', key: { set: true, origin: 'environment-variable', tail: 'ab12' } })!
    expect([s.state, s.problem, s.keyTail, s.keyOrigin]).toEqual(['fallback', 'bad_key', 'ab12', 'environment-variable'])
  })

  it('takes at most four characters as a tail, whatever arrives', () => {
    const s = parseState({ state: 'on', key: { set: true, tail: 'a-whole-key-by-mistake' } })!
    expect(s.keyTail).toBe('')
  })

  it('an unknown code is the general sentence, and every code has a sentence in every language', () => {
    expect(parseCheck({ ok: false, code: 'something-new' }).code).toBe('server_error')
    expect(parseCheck({ ok: true, code: 'bad_key' }).ok).toBe(false)
    for (const lang of LANGS) for (const code of CODES) expect(hasKey(lang, 'ai.check.' + code), `${lang} ${code}`).toBe(true)
  })

  it('sends only what the person changed', () => {
    expect(typedOf(ENV, ENV.address, ENV.model, '')).toEqual({})
    expect(typedOf(ENV, ENV.address, 'other-model', '')).toEqual({ model: 'other-model' })
    expect(typedOf(ENV, ENV.address, ENV.model, ' k ')).toEqual({ key: 'k', model: ENV.model })
    expect(typedOf(ENV, 'http://localhost:8000/v1', ENV.model, 'k')).toEqual({ base_url: 'http://localhost:8000/v1', model: ENV.model, key: 'k' })
    expect(masked()).toBe('•'.repeat(16))
    expect(masked('ab12')).toBe('•'.repeat(12) + 'ab12')
  })
})

describe('the calls', () => {
  const answer = (status: number, body: unknown) => async () => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } })

  it('GET /v1/model carries the access token of the service when one is typed, and no key ever', async () => {
    const seen: RequestInit[] = []
    const s = await fetchAiState('tok-1', async (u, i) => { seen.push(i); expect(u).toBe('../v1/model'); return new Response(JSON.stringify({ state: 'off', source: 'none', page_config: true })) })
    expect(s).toEqual(OFF)
    expect((seen[0].headers as Record<string, string>).Authorization).toBe('Bearer tok-1')
    expect(await fetchAiState('', async () => { throw new Error('down') })).toBeNull()
    expect(await fetchAiState('', async () => new Response('nope', { status: 404 }))).toBeNull()
  })

  it('a check, a use and a forget name what went wrong', async () => {
    expect(await checkModel({}, '', answer(200, { ok: false, code: 'bad_key', http: 401, ms: 80 }))).toEqual({ ok: false, code: 'bad_key', http: 401, ms: 80 })
    expect((await checkModel({}, '', answer(401, { code: 'TOKEN_MISSING' }))).code).toBe('token')
    expect((await checkModel({}, '', answer(403, { code: 'SCOPE' }))).code).toBe('token')
    expect((await checkModel({}, '', answer(403, { ok: false, code: 'locked' }))).code).toBe('locked')
    expect((await checkModel({}, '', async () => { throw new Error('down') })).code).toBe('no_service')
    expect((await checkModel({}, '', answer(404, { code: 'NOT_FOUND' }))).code).toBe('no_service')
    const sent: string[] = []
    const used = await useInSession({ key: PAGE_KEY }, '', async (u, i) => { sent.push(`${i.method} ${u} ${String(i.body)}`); return new Response(JSON.stringify({ ok: true, code: 'ok', model: { state: 'on', source: 'session', page_config: true, key: { set: true, origin: 'session' } } })) })
    expect(used.ok && used.state?.source).toBe('session')
    expect(sent[0]).toBe(`PUT ../v1/model/session {"key":"${PAGE_KEY}"}`)
    expect((await useInSession({ base_url: 'x' }, '', answer(400, { ok: false, code: 'bad_url' }))).code).toBe('bad_url')
    expect((await forgetSession('', answer(200, { ok: true, code: 'ok', model: { state: 'off', source: 'none', page_config: true } }))).state).toEqual(OFF)
  })
})

describe('the block', () => {
  it('is not shown when the service does not know the block (an older build)', async () => {
    const { el } = await mounted(null)
    expect(el.hidden).toBe(true)
  })

  it('off: one quiet closed line in plain Polish', async () => {
    const { el } = await mounted(OFF)
    expect(el.hidden).toBe(false)
    expect($<HTMLDetailsElement>(el, '#ai-details').open).toBe(false)
    expect($(el, '#h-ai').textContent).toBe('Model AI (opcjonalnie)')
    expect($(el, '#ai-badge').textContent).toBe('wyłączony')
    expect($(el, '#ai-state').textContent).toContain('Konwersja działa na regułach i lokalnym OCR')
    expect($<HTMLButtonElement>(el, '#ai-reveal').disabled).toBe(true)
    expect($<HTMLButtonElement>(el, '#ai-reset').hidden).toBe(true)
  })

  it('a key of the server: dots, where it comes from, and "show" gives only the last four characters', async () => {
    const { el } = await mounted(ENV)
    const key = $<HTMLInputElement>(el, '#ai-key')
    expect($<HTMLDetailsElement>(el, '#ai-details').open).toBe(true)
    expect($(el, '#ai-badge').textContent).toBe('włączony')
    expect($(el, '#ai-source').textContent).toContain('z konfiguracji serwera')
    expect([key.type, key.value, key.placeholder]).toEqual(['password', '', '•'.repeat(16)])
    expect($(el, '#ai-key-hint').textContent).toContain('VISION_API_KEY')
    expect($<HTMLInputElement>(el, '#ai-url').value).toBe(ENV.address)
    expect($<HTMLInputElement>(el, '#ai-model').value).toBe(ENV.model)
    $(el, '#ai-reveal').click()
    expect([key.type, key.value, key.placeholder]).toEqual(['password', '', '•'.repeat(12) + 'ailE'])
    expect($(el, '#ai-key-hint').textContent).toContain('tylko 4 ostatnie znaki (ailE)')
    expect($(el, '#ai-reveal').textContent).toBe('Ukryj klucz')
    $(el, '#ai-reveal').click()
    expect(key.placeholder).toBe('•'.repeat(16))
  })

  it('a key typed in this tab can be shown in full here and hidden again', async () => {
    const { el } = await mounted(ENV)
    const key = $<HTMLInputElement>(el, '#ai-key')
    type(key, PAGE_KEY)
    expect(key.type).toBe('password')
    expect($(el, '#ai-key-hint').textContent).toContain('tylko w pamięci tej karty')
    $(el, '#ai-reveal').click()
    expect([key.type, key.value]).toEqual(['text', PAGE_KEY])
    $(el, '#ai-reveal').click()
    expect(key.type).toBe('password')
  })

  it('"show" pressed for the dots of a server key does not uncover a key typed afterwards', async () => {
    const { el } = await mounted(ENV)
    const key = $<HTMLInputElement>(el, '#ai-key')
    $(el, '#ai-reveal').click()
    expect(key.placeholder).toContain('ailE')
    type(key, PAGE_KEY)
    expect(key.type).toBe('password')
    expect($(el, '#ai-reveal').textContent).toBe('Pokaż klucz')
  })

  it('a failure of the step: what is wrong, what to do, and that conversion goes on', async () => {
    const { el } = await mounted({ ...ENV, state: 'fallback', used: true, problem: 'no_credit' })
    expect($(el, '#ai-badge').textContent).toBe('awaria: działa bez modelu')
    const line = $(el, '#ai-state').textContent!
    expect(line).toContain('skończyły się środki')
    expect(line).toContain('Doładuj konto albo wpisz inny klucz')
    expect(line).toContain('Konwersja działa dalej')
  })

  it('"Sprawdź połączenie" with a wrong key answers in plain Polish and keeps the page working', async () => {
    const { el, calls } = await mounted(ENV, { check: async (typed) => { calls.check.push(typed); return { ok: false, code: 'bad_key', http: 401, ms: 90 } } })
    type($<HTMLInputElement>(el, '#ai-key'), 'wrong-key')
    $(el, '#ai-check').click()
    expect($(el, '#ai-result').textContent).toBe('Sprawdzam połączenie z serwerem modelu…')
    await tick()
    expect(calls.check).toEqual([{ key: 'wrong-key', model: ENV.model }])
    const line = $(el, '#ai-result')
    expect(line.textContent).toBe('Serwer modelu odrzucił klucz. Wpisz poprawny klucz i sprawdź ponownie. Konwersja działa dalej bez modelu. (odpowiedź serwera modelu: HTTP 401)')
    expect(line.className).toContain('ai-bad')
    expect(calls.use).toEqual([])   // a check changes nothing
  })

  it.each([
    ['no_credit', 'skończyły się środki'], ['rate_limit', 'limit zapytań'], ['unreachable', 'Nie udało się połączyć'],
    ['model_not_found', 'nie zna modelu'], ['timeout', 'nie odpowiedział na czas'], ['not_api', 'API zgodne z OpenAI']
  ])('%s has its own sentence and says conversion goes on', async (code, words) => {
    const { el } = await mounted(ENV, { check: async () => ({ ok: false, code, http: null, ms: 0 }) })
    $(el, '#ai-check').click()
    await tick()
    const text = $(el, '#ai-result').textContent!
    expect(text).toContain(words)
    expect(text).toContain('Konwersja działa dalej bez modelu.')
  })

  it('a good check of untouched settings sends nothing typed and says how long the model took', async () => {
    const { el, calls } = await mounted(ENV)
    $(el, '#ai-check').click()
    await tick()
    expect(calls.check).toEqual([{}])
    expect($(el, '#ai-result').textContent).toBe('Połączenie działa: model odpowiedział w 1,2 s.')
    expect($(el, '#ai-result').className).toContain('ai-good')
  })

  it('"Użyj w tej sesji": the settings go to the service once, are checked at once, and can be taken back', async () => {
    const { el, calls } = await mounted(OFF)
    const use = $<HTMLButtonElement>(el, '#ai-use')
    expect(use.disabled).toBe(true)   // nothing typed yet
    type($<HTMLInputElement>(el, '#ai-url'), 'http://localhost:8000/v1')
    type($<HTMLInputElement>(el, '#ai-model'), 'qwen3-local')
    type($<HTMLInputElement>(el, '#ai-key'), PAGE_KEY)
    expect(use.disabled).toBe(false)
    use.click()
    await tick(); await tick()
    expect(calls.use).toEqual([{ base_url: 'http://localhost:8000/v1', model: 'qwen3-local', key: PAGE_KEY }])
    expect(calls.check).toEqual([{}])   // the service checks what it now uses; the key is not sent a second time
    expect($(el, '#ai-result').textContent).toContain('Ustawienia przyjęte. Połączenie działa')
    expect($(el, '#ai-source').textContent).toContain('wpisano na tej stronie')
    // the key stays in the field of this tab (it can be looked at), is not "new" any more and is not sent again
    expect($<HTMLInputElement>(el, '#ai-key').value).toBe(PAGE_KEY)
    expect($(el, '#ai-key-hint').textContent).toContain('jest już używany przez usługę')
    expect(use.disabled).toBe(true)
    expect(el.dataset.source).toBe('session')
    const reset = $<HTMLButtonElement>(el, '#ai-reset')
    expect(reset.hidden).toBe(false)
    reset.click()
    await tick()
    expect(calls.forget).toBe(1)
    expect($<HTMLInputElement>(el, '#ai-key').value).toBe('')
    expect($(el, '#ai-result').textContent).toContain('Usługa wróciła do ustawień serwera')
    expect(reset.hidden).toBe(true)
  })

  it('a refused change says why', async () => {
    const { el } = await mounted(ENV, { use: async () => ({ ok: false, code: 'key_needed', state: null }) })
    type($<HTMLInputElement>(el, '#ai-url'), 'http://other.example.test/v1')
    $(el, '#ai-use').click()
    await tick()
    expect($(el, '#ai-result').textContent).toContain('Dla innego adresu wpisz też klucz')
  })

  it('an operator who forbids changes: fields are read only, the check still works', async () => {
    const { el } = await mounted({ ...ENV, pageConfig: false })
    expect($<HTMLInputElement>(el, '#ai-key').disabled).toBe(true)
    expect($<HTMLButtonElement>(el, '#ai-use').hidden).toBe(true)
    expect($<HTMLButtonElement>(el, '#ai-check').disabled).toBe(false)
    const off = await mounted({ ...OFF, state: 'disabled', pageConfig: false })
    expect($(off.el, '#ai-form').hidden).toBe(true)
    expect($(off.el, '#ai-state').textContent).toContain('wyłączony przez operatora')
  })

  it('writes nothing to the storage of the browser', async () => {
    const set = vi.spyOn(Storage.prototype, 'setItem')
    const { el } = await mounted(OFF)
    type($<HTMLInputElement>(el, '#ai-url'), 'http://localhost:8000/v1')
    type($<HTMLInputElement>(el, '#ai-key'), PAGE_KEY)
    $(el, '#ai-use').click()
    await tick(); await tick()
    expect(set).not.toHaveBeenCalled()
    expect(document.cookie).toBe('')
    expect(document.body.innerHTML).not.toContain(PAGE_KEY)   // the key is a value of the field, never markup
    set.mockRestore()
  })
})

describe('on the page', () => {
  it('sits right under the upload panel and follows the language switch', async () => {
    document.body.innerHTML = '<div id="app"></div>'
    const root = document.getElementById('app')!
    mountApp(root, { convert: async () => ({ kind: 'error', code: 'NETWORK', status: 0, detail: null, title: null }), store: null, status: async () => null })
    const made = deps({ ...ENV, state: 'fallback', used: true, problem: 'bad_key' })
    const block = attachModelKey(root, made.d)
    await tick()
    expect(root.querySelector('#main section.panel')!.nextElementSibling).toBe(block.el)
    expect($(root, '#ai-badge').textContent).toBe('awaria: działa bez modelu')
    const lang = $<HTMLSelectElement>(root, '#lang')
    lang.value = 'en'
    lang.dispatchEvent(new Event('change'))
    expect($(root, '#h-ai').textContent).toBe('AI model (optional)')
    expect($(root, '#ai-badge').textContent).toBe('failure: working without the model')
    expect($(root, '#ai-state').textContent).toContain('The model server refused the key')
    expect($(root, '#ai-check').textContent).toBe('Check connection')
  })
})

describe('the badge of the header knows the open-model step (/status key `vision`)', () => {
  const base = { service: 'x', version: '1', engine: 'rules', auth: 'off', formats: [], limits: {} }
  it('nothing configured is still "rules"', () => {
    expect(modeOf(base)).toBe('rules')
  })
  it('a configured step is "model on" before the first conversion, never "rules, nothing leaves"', () => {
    expect(modeOf({ ...base, vision: { state: 'ON', model: 'm', calls: 'none yet' } })).toBe('model-on')
    expect(modeOf({ ...base, vision: { state: 'ON', model: 'm' } })).toBe('model-on')
  })
  it('a step that fell back is "model unavailable"', () => {
    expect(modeOf({ ...base, vision: { state: 'FALLBACK', model: 'm', reason: 'http_401' } })).toBe('model-fallback')
    expect(modeOf({ ...base, engine: 'rules-fallback', vision: { state: 'ON', model: 'm' } })).toBe('model-fallback')
  })
  it('a `vision` the page does not understand changes nothing', () => {
    expect(modeOf({ ...base, vision: 'ON' })).toBe('rules')
    expect(modeOf({ ...base, vision: { state: 'OFF' } })).toBe('rules')
    expect(modeOf({ ...base, vision: { state: 7 } })).toBe('rules')
  })
})

describe('W11 BL12: the whole key only when the operator allows it', () => {
  it('reads key.full only as a printable string, else empty', async () => {
    const { parseState } = await import('../src/lib/aimodel')
    const base = { state: 'on', source: 'environment', page_config: true, model: 'm', used: false }
    expect(parseState({ ...base, key: { set: true, origin: 'environment-variable', tail: 'abcd' } })?.keyFull).toBe('')
    expect(parseState({ ...base, key: { set: true, origin: 'environment-variable', full: 'FAKE-full-key-0000abcd' } })?.keyFull)
      .toBe('FAKE-full-key-0000abcd')
    expect(parseState({ ...base, key: { set: true, full: 'two words' } })?.keyFull).toBe('')
  })
})
