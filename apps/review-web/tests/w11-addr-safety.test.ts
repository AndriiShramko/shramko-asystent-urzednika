// W11 ADDR step 1: labels, option texts, remarks and names come from files that strangers upload. Whatever a
// document says, the page shows it as text: no element, no handler, no link target and no selector is ever built
// from it. Synthetic data only.
import { beforeEach, describe, expect, it } from 'vitest'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { renderConverted } from '../src/ui/result'
import { mountFill } from '../src/ui/fill'
import { setLang } from '../src/lib/i18n'
import { interpretResponse, type Converted } from '../src/lib/api'
import { canonical, cell, field, multipartBody } from './helpers'

const MP = { 'content-type': 'multipart/mixed; boundary=formularze-abc123' }
const X = '<img src=x onerror="globalThis.__pwned=1"><script>globalThis.__pwned=1</script><svg onload="globalThis.__pwned=1">'
const LINK = '<a href="javascript:globalThis.__pwned=1" onclick="globalThis.__pwned=1">kliknij</a>'
const HTML = `<html><head><script>globalThis.__pwned=1</script></head><body><p>Opis ${X}</p>${LINK}<iframe src="javascript:globalThis.__pwned=1"></iframe></body></html>`
/** An id no honest service sends: it would close the attribute selector the page looks a field up by. */
const BAD_ID = 'x"] , body , [id="y'

function hostileForm() {
  const sec = field('s-1', 'SECTION', `Sekcja ${X}`, {
    techName: `sekcja${X}`, description: HTML,
    repeatingSectionGrid: [
      cell(field(BAD_ID, 'TEXT_FIELD', `Miejscowość ${X}`, { techName: `miejscowosc"${X}`, description: HTML,
        validation: ['REQUIRED', `PESEL${X}`], tooltipMessage: X, defaultValue: `MLPZ.${X}`, defaultValueType: 'EXTERNAL_SYSTEM' })),
      cell(field('f-2', 'RADIO', `Wybór ${X}`, { options: [{ id: X, name: `Tak ${X}`, techName: X }, { id: 'n', name: `Nie ${LINK}`, techName: 'n' }] }), 1),
      cell(field('f-3', 'SELECT', `Lista ${X}`, { dictionaryName: `Słownik ${X}`, options: [] }), 2),
      cell(field('f-4', 'SELECT', `Lista 2 ${X}`, { options: [{ id: 'a', name: `A ${X}`, techName: 'a' }] }), 3),
      cell(field('f-5', 'CHECKBOX', `Pola ${X}`, { options: [{ id: 'a', name: `B ${X}`, techName: 'a' }] }), 4),
      cell(field('f-6', 'CONSENT_SECTION', `Zgody ${X}`, { consentSectionConfig: { consents: [{ description: HTML, required: true }] } }), 5),
      cell(field('f-7', 'TEXT_BLOCK', `Tekst ${X}`, { description: HTML }), 6),
      cell(field('f-8', 'TEXTAREA', `Uwagi ${LINK}`, { states: [{ type: 'SHOW', query: `"${X}" in nothing` }] }), 7),
      cell(field('f-9', 'DATEPICKER', `Data ${X}`), 8),
      cell(field('f-10', 'FILE_UPLOADER', `Plik ${X}.pdf`), 9)
    ]
  })
  return { title: `Wniosek ${X}`, tabs: [{ id: 't-1', title: `Strona ${X}`, type: 'MAIN', questions: [cell(sec)] }], flow: { links: [] } }
}

function hostileSidecar() {
  return {
    version: 1,
    converter: { version: X, pipeline: X, reader: X },
    counts: { pages: 1, fields: 9, source_pages: 1 },
    warnings: [
      { code: 'LABEL_NOT_FOUND', page: 1, box: [1, 2, 3, 4], candidate: X, evidence: [X], detail: X, field: BAD_ID, label: X },
      { code: `NEW${X}`, detail: HTML, message: X, title: X },
      { code: 'INPUT_NOTE', detail: `Nazwa pliku: ${X}.pdf` }
    ],
    checks: [{ code: X, detail: X, ok: false }],
    meta: {
      origins: { 's-1': 'paper', [BAD_ID]: 'paper', 'f-2': 'paper', 'f-3': 'paper' },
      evidence: { [BAD_ID]: { page: 1, quote: X, candidate: X }, 'f-2': [{ page: 1, anchor: X }, { quote: LINK }] },
      proposals: { dictionaries: [{ name: X, entries: [X, LINK], pages: [1], field: X, fields: [X], why: X, use: X, evidence: [X] }] },
      dictionary_links: [{ field: BAD_ID, label: X, dictionary: X, written: true, why: X }]
    }
  }
}

async function answer(): Promise<Converted> {
  const res = await interpretResponse(200, new Headers({ ...MP, 'x-converter-warnings': `2; LABEL_NOT_FOUND, NEW${X}` }),
    multipartBody(canonical(hostileForm()), canonical(hostileSidecar())))
  if (res.kind !== 'ok') throw new Error('fixture failed')
  return res
}

/** Elements a text of a document must never become, and attributes it must never set. */
function offences(root: Element): string[] {
  const out: string[] = []
  for (const el of [root, ...root.querySelectorAll('*')]) {
    const tag = el.tagName.toLowerCase()
    if (['script', 'iframe', 'object', 'embed', 'svg', 'style', 'link', 'meta', 'base', 'form', 'math', 'video', 'audio'].includes(tag)) out.push(`<${tag}>`)
    for (const a of [...el.attributes]) {
      if (/^on/i.test(a.name)) out.push(`${tag}[${a.name}]`)
      if (/^(href|src|action|formaction|xlink:href)$/i.test(a.name) && /^\s*(javascript|vbscript|data:text\/html)/i.test(a.value)) out.push(`${tag}[${a.name}=${a.value.slice(0, 30)}]`)
    }
    if (tag === 'img' && !/^data:image\//.test(el.getAttribute('src') ?? '')) out.push('img with a foreign source')
    if (tag === 'a' && !/^(#|blob:)/.test(el.getAttribute('href') ?? '')) out.push('a with a foreign target')
  }
  return out
}

beforeEach(() => { setLang('pl'); document.body.innerHTML = '<div id="app"></div>'; delete (globalThis as { __pwned?: number }).__pwned })

describe('W11 ADDR: a document cannot put markup or script on the page', () => {
  it('renders hostile labels, options, descriptions, remarks and dictionary names as text only', async () => {
    const res = await answer()
    const app = document.getElementById('app')!
    app.append(renderConverted(res))
    const fill = mountFill(res)
    app.append(fill.el)
    expect(offences(app)).toEqual([])
    expect((globalThis as { __pwned?: number }).__pwned).toBeUndefined()
    // the text is there, as text
    expect(app.textContent).toContain('<img src=x onerror=')
    // descriptions: read through a parser, shown as text; neither the script body nor a tag survives as an element
    expect(fill.eform.el.querySelectorAll('.fp-desc img, .fp-desc a, .fp-desc script').length).toBe(0)
  })

  it('an id that would break a selector does not break the trial fill (set, error, focus, reset)', async () => {
    const res = await answer()
    const fill = mountFill(res)
    document.getElementById('app')!.append(fill.el)
    const node = fill.eform.model.all.find((n) => n.title.startsWith('Miejscowość'))!
    expect(node.id).toMatch(/^[A-Za-z0-9][A-Za-z0-9_.:-]*$/)
    expect(() => {
      fill.eform.set(node.id, 'Bydgoszcz')
      fill.eform.showError(node.id, 'Błąd')
      fill.eform.focus(node.id)
      fill.check.run()
      fill.eform.reset()
    }).not.toThrow()
    fill.eform.set(node.id, 'Bydgoszcz')
    // the value landed in this field's own control, not in whatever a broken selector would have matched
    const own = [...fill.eform.el.querySelectorAll<HTMLInputElement>('input')].filter((i) => i.value === 'Bydgoszcz')
    expect(own.length).toBe(1)
    expect(own[0].closest('[data-node]')?.querySelector('label')?.textContent).toContain('Miejscowość')
    // every id and every id reference the page wrote is free of quotes, brackets and spaces
    for (const el of fill.el.querySelectorAll('[id]')) expect(el.id).toMatch(/^[A-Za-z0-9_.:-]+$/)
  })
})

describe('W11 ADDR: the page itself', () => {
  const html = readFileSync(join(__dirname, '..', 'index.html'), 'utf8')
  const csp = /http-equiv="Content-Security-Policy"\s+content="([^"]+)"/.exec(html)?.[1] ?? ''
  const directive = (name: string): string[] => (csp.split(';').map((d) => d.trim().split(/\s+/)).find((d) => d[0] === name) ?? []).slice(1)

  it('declares a content security policy: own script only, no inline script, no eval, own requests only', () => {
    expect(csp).not.toBe('')
    expect(directive('default-src')).toEqual(["'none'"])
    expect(directive('script-src')).toEqual(["'self'"])
    expect(directive('connect-src')).toEqual(["'self'"])
    expect(directive('object-src')).toEqual(["'none'"])
    expect(directive('base-uri')).toEqual(["'none'"])
    expect(directive('form-action')).toEqual(["'none'"])
    expect(csp).not.toMatch(/unsafe-eval|\*|https?:/)
  })

  it('has no call in its source that turns a string into markup or code', () => {
    const files: string[] = []
    const walk = (dir: string): void => {
      for (const f of readdirSync(dir)) {
        const p = join(dir, f)
        if (statSync(p).isDirectory()) walk(p)
        else if (/\.ts$/.test(f)) files.push(p)
      }
    }
    walk(join(__dirname, '..', 'src'))
    expect(files.length).toBeGreaterThan(10)
    const banned = /\b(innerHTML|outerHTML|insertAdjacentHTML|document\.write|srcdoc|createContextualFragment)\b|\beval\s*\(|new Function\b|setTimeout\s*\(\s*['"`]/
    const hits = files.filter((p) => banned.test(readFileSync(p, 'utf8')))
    expect(hits).toEqual([])
  })
})
