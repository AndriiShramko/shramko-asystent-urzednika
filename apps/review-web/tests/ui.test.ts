import { beforeEach, describe, expect, it } from 'vitest'
import { mountApp } from '../src/ui/app'
import { renderConverted, renderProblem } from '../src/ui/result'
import { setLang, t, LANGS, dictionaryKeys } from '../src/lib/i18n'
import { interpretResponse, type Converted, type Outcome } from '../src/lib/api'
import { canonical, multipartBody, syntheticForm, syntheticSidecar } from './helpers'

async function converted(withSidecar: boolean, headerWarnings?: string): Promise<Converted> {
  const hdr: Record<string, string> = { 'content-type': 'multipart/mixed; boundary=formularze-abc123' }
  if (headerWarnings) hdr['x-converter-warnings'] = headerWarnings
  const res = await interpretResponse(200, new Headers(hdr),
    multipartBody(canonical(syntheticForm()), withSidecar ? canonical(syntheticSidecar()) : null))
  if (res.kind !== 'ok') throw new Error('fixture failed')
  return res
}

beforeEach(() => { setLang('pl'); document.body.innerHTML = '<div id="app"></div>' })

describe('result page', () => {
  it('shows the matter first with page and snippet, standard sections collapsed, warnings in plain words', async () => {
    const root = renderConverted(await converted(true, '3; LABEL_NOT_FOUND'))
    document.body.append(root)
    const heads = [...root.querySelectorAll('h2')].map((h) => h.textContent)
    expect(heads.indexOf(t('matter.heading'))).toBeGreaterThan(-1)
    expect(heads.indexOf(t('matter.heading'))).toBeLessThan(heads.indexOf(t('standard.heading')))
    const first = root.querySelector('.fields .field')!
    expect(first.textContent).toContain('Nazwa ulicy')
    expect(first.textContent).toContain('strona 2')
    expect(first.querySelector('blockquote')!.textContent).toContain('Nazwa ulicy')
    const std = root.querySelector('details.standard') as HTMLDetailsElement
    expect(std.open).toBe(false)
    expect(root.textContent).toContain(t('warn.LABEL_NOT_FOUND'))
    expect(root.textContent).toContain(t('warnings.unknown')) // SOMETHING_NEW is not in the dictionary
    expect(root.querySelector('#json-text')!.textContent).toBe(JSON.stringify(syntheticForm()))
  })

  it('negative control: sidecar missing, the form is still shown and the page says what is absent', async () => {
    const root = renderConverted(await converted(false, '2; LOW_CONFIDENCE'))
    document.body.append(root)
    expect(root.textContent).toContain(t('sidecar.missing.heading'))
    expect(root.textContent).toContain(t('sidecar.missing.body'))
    expect(root.querySelector('#json-text')!.textContent).toBe(JSON.stringify(syntheticForm()))
    expect(root.textContent).toContain('Nazwa ulicy') // the fields are listed, without origin
    expect(root.querySelector('.fields .field blockquote')).toBeNull() // no invented snippet
    expect(root.textContent).toContain(t('warn.LOW_CONFIDENCE')) // the header's code is still explained
  })

  it('shows a refusal as its plain reason in each language and never as a raw key', () => {
    for (const lang of LANGS) {
      setLang(lang)
      const p = renderProblem({ kind: 'error', code: 'TOKEN_MISSING', status: 401, detail: 'Brak tokenu.', title: null })
      expect(p.textContent).toContain(t('problem.TOKEN_MISSING'))
      expect(p.textContent).not.toMatch(/problem\./)
      expect(p.querySelector('[role="alert"]')).not.toBeNull()
    }
    const unknown = renderProblem({ kind: 'error', code: 'NEW_ONE', status: 422, detail: null, title: null })
    expect(unknown.textContent).toContain(t('problem.UNKNOWN'))
  })

  // WP-H4 showed the engine of the conversion as a band `#engine` inside the result. The page now has ONE
  // indicator, the badge `#mode` of the header; the same truth is asserted there. /status is silent in this test,
  // so the badge can only come from the engine the conversion stated.
  it('shows the engine of the conversion in words on the one badge of the header, in every language', async () => {
    const base = await converted(true)
    const cases: [NonNullable<Converted['engine']>, string][] = [
      ['rules', 'rules'], ['rules+model', 'model-on'], ['rules-fallback', 'model-fallback']
    ]
    const texts = new Set<string>()
    for (const lang of LANGS) {
      for (const [engine, mode] of cases) {
        document.body.innerHTML = '<div id="app"></div>'
        mountApp(document.getElementById('app')!, {
          store: { getItem: () => lang, setItem: () => undefined }, status: async () => null,
          convert: async () => ({ ...base, engine })
        })
        await new Promise((r) => setTimeout(r, 0))
        expect(document.getElementById('mode')!.hidden).toBe(true) // before a conversion, without /status: no badge
        const file = document.getElementById('file') as HTMLInputElement
        Object.defineProperty(file, 'files', { value: [new File([new Uint8Array([1])], 'x.pdf')], configurable: true })
        file.dispatchEvent(new Event('change'))
        await new Promise((r) => setTimeout(r, 0))
        const badge = document.getElementById('mode')!
        expect(badge.hidden).toBe(false)
        expect(badge.closest('header')).not.toBeNull()
        expect(badge.classList.contains(`mode-${mode}`)).toBe(true)
        expect(badge.getAttribute('data-mode')).toBe(mode)
        expect(badge.getAttribute('data-engine')).toBe(engine)
        // the meaning is text, not colour alone: a sentence of the dictionary, different for every engine
        const key = `mode.${mode}`
        expect(t(key)).not.toBe(key)
        expect(badge.textContent).toBe(t(key))
        expect(badge.textContent!.split(' ').length).toBeGreaterThanOrEqual(3)
        texts.add(`${lang}|${badge.textContent}`)
        // not a control: nothing to focus, the keyboard order of the page is unchanged
        expect(badge.querySelector('a, button, input, [tabindex]')).toBeNull()
        expect(badge.hasAttribute('tabindex')).toBe(false)
        // one indicator only: the result carries no second band
        expect(document.querySelector('#engine, .engine, [class*="engine-"]')).toBeNull()
        expect(document.querySelectorAll('[data-engine]').length).toBe(1)
      }
    }
    expect(texts.size).toBe(LANGS.length * cases.length)
    setLang('pl')
    expect(['rules', 'model-on', 'model-fallback'].map((m) => t(`mode.${m}`))).toEqual([
      'Tryb: reguły i lokalny OCR, bez modelu AI', 'Model AI: włączony', 'Model AI: niedostępny, działają reguły'])
    for (const engine of [...cases.map((c) => c[0]), null]) {
      const root = renderConverted({ ...base, engine })
      expect(root.children[0]?.id).toBe('h-done')
      expect(root.querySelector('#engine, [data-engine], [class*="engine"]')).toBeNull()
    }
    for (const lang of LANGS) expect(dictionaryKeys(lang).filter((k) => k.startsWith('engine.'))).toEqual([])
  })

  it('renders without a leaked dictionary key in every language', async () => {
    const res = await converted(true, '3; LABEL_NOT_FOUND')
    for (const lang of LANGS) {
      setLang(lang)
      const text = renderConverted(res).textContent ?? ''
      for (const key of dictionaryKeys('pl')) if (key.includes('.')) expect(text.includes(`${key}`), `${lang} leaks ${key}`).toBe(false)
    }
  })

  it('uses text nodes only: markup in a label stays text', async () => {
    const form = syntheticForm()
    form.tabs[1].questions[0].field.repeatingSectionGrid[0].field.title = '<img src=x onerror=alert(1)>'
    const res = await interpretResponse(200, new Headers({ 'content-type': 'multipart/mixed; boundary=formularze-abc123' }),
      multipartBody(canonical(form), canonical(syntheticSidecar())))
    const root = renderConverted(res as Converted)
    expect(root.querySelector('img')).toBeNull()
    expect(root.textContent).toContain('<img src=x')
  })
})

describe('application', () => {
  const store = (init: string | null = null) => {
    const m = new Map<string, string>(init ? [['review.lang', init]] : [])
    return { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v), m }
  }

  it('starts in Polish, switches the whole page to English and Spanish and remembers the choice', () => {
    const s = store()
    mountApp(document.getElementById('app')!, { store: s, status: async () => null })
    expect(document.documentElement.lang).toBe('pl')
    expect(document.querySelector('h1')!.textContent).toBe('Przegląd formularza')
    const sel = document.getElementById('lang') as HTMLSelectElement
    sel.value = 'en'; sel.dispatchEvent(new Event('change'))
    expect(document.documentElement.lang).toBe('en')
    expect(document.querySelector('h1')!.textContent).toBe('Form review')
    expect(document.querySelector('label[for="token"]')!.textContent).toContain('Access token')
    sel.value = 'es'; sel.dispatchEvent(new Event('change'))
    expect(document.querySelector('h1')!.textContent).toBe('Revisión del formulario')
    expect(s.m.get('review.lang')).toBe('es')
    document.body.innerHTML = '<div id="app"></div>'
    mountApp(document.getElementById('app')!, { store: s, status: async () => null })
    expect(document.documentElement.lang).toBe('es')
  })

  it('has labelled controls, a skip link and a live status; the token is never stored', async () => {
    const s = store()
    let got: { name: string; token: string } | null = null
    const outcome: Outcome = await converted(true)
    mountApp(document.getElementById('app')!, { store: s, status: async () => null, convert: async (f, tok) => { got = { name: f.name, token: tok }; return outcome } })
    const input = document.getElementById('token') as HTMLInputElement
    expect(input.type).toBe('password')
    expect(document.querySelector('label[for="token"]')).not.toBeNull()
    expect(document.querySelector('label[for="lang"]')).not.toBeNull()
    expect(document.querySelector('a.skip')!.getAttribute('href')).toBe('#main')
    expect(document.getElementById('status')!.getAttribute('role')).toBe('status')
    input.value = 'tok-123'
    const file = document.getElementById('file') as HTMLInputElement
    Object.defineProperty(file, 'files', { value: [new File([new Uint8Array([1])], 'x.pdf')], configurable: true })
    file.dispatchEvent(new Event('change'))
    await new Promise((r) => setTimeout(r, 0))
    expect(got).toEqual({ name: 'x.pdf', token: 'tok-123' })
    expect(document.getElementById('result')!.textContent).toContain('Wniosek próbny')
    expect(document.getElementById('status')!.textContent).toContain('Wniosek próbny')
    expect([...s.m.values()].join('')).not.toContain('tok-123')
    // every button and input reachable by keyboard has an accessible name
    for (const el of document.querySelectorAll('button, select, input:not([type="file"]):not([type="checkbox"])')) {
      const named = el.textContent?.trim() || document.querySelector(`label[for="${el.id}"]`)?.textContent || el.getAttribute('aria-label')
      expect(named, el.outerHTML).toBeTruthy()
    }
  })
})
