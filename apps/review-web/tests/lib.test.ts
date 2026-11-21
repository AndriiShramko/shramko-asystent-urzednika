import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { dictionaryKeys, initialLang, translate, hasKey, LANGS } from '../src/lib/i18n'
import { boundaryOf, parseMultipart } from '../src/lib/multipart'
import { buildView } from '../src/lib/model'
import { groupWarnings, parseWarningsHeader } from '../src/lib/warnings'
import { interpretResponse, convertFile, problemFrom } from '../src/lib/api'
import { canonical, multipartBody, sha256, syntheticForm, syntheticSidecar } from './helpers'

const headersOf = (o: Record<string, string>) => new Headers(o)

describe('dictionaries (D25)', () => {
  it('carry exactly the same keys in Polish, English and Spanish', () => {
    const pl = dictionaryKeys('pl').sort()
    for (const l of LANGS) expect(dictionaryKeys(l).sort()).toEqual(pl)
  })

  it('describe every warning code of the sidecar contract and every refusal code of the service', () => {
    const schema = JSON.parse(readFileSync(resolve(process.cwd(), '../../contracts/coi/meta.schema.json'), 'utf8'))
    const codes: string[] = schema.$defs.Warning.properties.code.enum
    expect(codes.length).toBeGreaterThanOrEqual(29)
    const extra = ['BRIEF_NOT_READ', 'LEDGER_NOT_CLOSED', 'PIPELINE_STUB']
    for (const l of LANGS) for (const c of [...codes, ...extra]) expect(hasKey(l, 'warn.' + c), `${l} warn.${c}`).toBe(true)
    const problems = ['ACTIVE_CONTENT', 'ARCHIVE_LIMIT', 'BAD_NAME', 'BAD_REQUEST', 'BUSY', 'DOC_READER_OFF', 'EXTENSION', 'SCOPE',
      'TOKEN_EXPIRED', 'TOKEN_INVALID', 'TOKEN_MISSING', 'TOO_LARGE', 'TOO_MANY_PIXELS', 'TOO_MANY_PAGES', 'TYPE_MISMATCH',
      'UNREADABLE', 'UNSUPPORTED_FORMAT', 'GATE_FAILED', 'NETWORK', 'BAD_ANSWER']
    for (const l of LANGS) for (const c of problems) expect(hasKey(l, 'problem.' + c), `${l} problem.${c}`).toBe(true)
  })

  it('translates by code, fills parameters, leaves an unknown key visible', () => {
    expect(translate('en', 'matter.page', { page: 3 })).toBe('page 3')
    expect(translate('es', 'matter.page', { page: 3 })).toBe('página 3')
    expect(translate('pl', 'matter.page', { page: 3 })).toBe('strona 3')
    expect(translate('en', 'no.such.key')).toBe('no.such.key')
  })

  it('starts in Polish unless a valid language was stored', () => {
    expect(initialLang(null)).toBe('pl')
    expect(initialLang('de')).toBe('pl')
    expect(initialLang('es')).toBe('es')
  })
})

describe('multipart reader', () => {
  it('returns the form part byte for byte, with non-ASCII text and a CR LF inside the payload', () => {
    const form = new TextEncoder().encode('{"title":"Zażółć gęślą jaźń","x":"a\\r\\nb"}')
    const meta = canonical({ warnings: [] })
    const body = multipartBody(form, meta)
    const parts = parseMultipart(body, 'formularze-abc123')
    expect(parts.map((p) => p.filename)).toEqual(['form.json', 'meta.json'])
    expect(Array.from(parts[0].body)).toEqual(Array.from(form))
    expect(boundaryOf('multipart/mixed; boundary=formularze-abc123')).toBe('formularze-abc123')
    expect(boundaryOf('multipart/mixed; boundary="q q"')).toBe('q q')
  })
})

describe('view model', () => {
  const form = syntheticForm()
  it('puts fields of the paper first, standard fields apart, containers and fixed texts nowhere', () => {
    const v = buildView(form, syntheticSidecar())
    expect(v.matter.map((r) => r.id)).toEqual(['f-1', 'f-2'])
    expect(v.standardCount).toBe(2)
    expect([...v.standard.keys()]).toEqual(['Dane'])
    expect(v.rows.some((r) => r.type === 'TEXT_BLOCK' || r.type === 'SECTION')).toBe(false)
    expect(v.counts).toEqual({ pages: 2, fields: 4, sourcePages: 1 })
  })

  it('gives each field of the matter its page and snippet, or says there is none', () => {
    const v = buildView(form, syntheticSidecar())
    const [a, b] = v.matter
    expect(a).toMatchObject({ page: 2, quote: 'Nazwa ulicy ………', required: true })
    expect(b).toMatchObject({ page: 2, anchor: 'p[3]', quote: 'Rodzaj sprawy', options: ['Pierwszy', 'Drugi'] })
    const noEvidence = syntheticSidecar()
    delete (noEvidence.meta as { evidence?: unknown }).evidence
    expect(buildView(form, noEvidence).matter[0]).toMatchObject({ page: null, quote: null })
  })

  it('negative control: without a sidecar nothing is called paper or standard', () => {
    const v = buildView(form, null)
    expect(v.hasSidecar).toBe(false)
    expect(v.matter).toHaveLength(0)
    expect(v.standardCount).toBe(0)
    expect(v.unknown).toHaveLength(4)
    expect(v.warnings).toEqual([])
  })

  it('reads the contract shape (origins at the top level) too', () => {
    const sc = { origins: { 'f-1': 'paper' }, warnings: [] }
    expect(buildView(form, sc).matter.map((r) => r.id)).toEqual(['f-1'])
  })
})

describe('warnings', () => {
  it('reads the count and the codes of X-Converter-Warnings, in either spelling', () => {
    expect(parseWarningsHeader('3; LABEL_NOT_FOUND, REQUIRED_INFERRED')).toMatchObject({ count: 3, codes: ['LABEL_NOT_FOUND', 'REQUIRED_INFERRED'] })
    expect(parseWarningsHeader('count=2; codes=LOW_CONFIDENCE,LABEL_RAW')).toMatchObject({ count: 2, codes: ['LOW_CONFIDENCE', 'LABEL_RAW'] })
    expect(parseWarningsHeader('')).toBeNull()
    expect(parseWarningsHeader(null)).toBeNull()
  })

  it('groups by code and marks a code the dictionary lacks', () => {
    const g = groupWarnings(syntheticSidecar().warnings)
    expect(g.map((x) => [x.code, x.items.length, x.known])).toEqual([['LABEL_NOT_FOUND', 2, true], ['SOMETHING_NEW', 1, false]])
  })
})

describe('talking to the service', () => {
  const form = syntheticForm()
  const formBytes = canonical(form)
  const metaBytes = canonical(syntheticSidecar())

  it('keeps the form bytes and confirms X-Form-SHA256', async () => {
    const body = multipartBody(formBytes, metaBytes)
    const res = await interpretResponse(200, headersOf({
      'content-type': 'multipart/mixed; boundary=formularze-abc123',
      'x-form-sha256': await sha256(formBytes), 'x-converter-warnings': '3; LABEL_NOT_FOUND'
    }), body)
    if (res.kind !== 'ok') throw new Error('expected ok')
    expect(Array.from(res.formBytes)).toEqual(Array.from(formBytes))
    expect(res.hash).toBe('ok')
    expect(res.sidecar).not.toBeNull()
    expect(res.sidecarMissing).toBeNull()
    expect(res.header).toMatchObject({ count: 3 })
  })

  it('flags a wrong sum and an absent sum', async () => {
    const body = multipartBody(formBytes, metaBytes)
    const ct = 'multipart/mixed; boundary=formularze-abc123'
    const bad = await interpretResponse(200, headersOf({ 'content-type': ct, 'x-form-sha256': '0'.repeat(64) }), body)
    const none = await interpretResponse(200, headersOf({ 'content-type': ct }), body)
    expect(bad.kind === 'ok' && bad.hash).toBe('bad')
    expect(none.kind === 'ok' && none.hash).toBe('unchecked')
  })

  it('negative control: with the sidecar missing or broken the form is still returned', async () => {
    const ct = 'multipart/mixed; boundary=formularze-abc123'
    const missing = await interpretResponse(200, headersOf({ 'content-type': ct }), multipartBody(formBytes, null))
    const broken = await interpretResponse(200, headersOf({ 'content-type': ct }), multipartBody(formBytes, new TextEncoder().encode('{not json')))
    const plain = await interpretResponse(200, headersOf({ 'content-type': 'application/json' }), formBytes)
    expect(missing).toMatchObject({ kind: 'ok', sidecar: null, sidecarMissing: 'none' })
    expect(broken).toMatchObject({ kind: 'ok', sidecar: null, sidecarMissing: 'invalid' })
    expect(plain).toMatchObject({ kind: 'ok', sidecar: null, sidecarMissing: 'none' })
  })

  it('turns a refusal into its code, status and Polish reason', async () => {
    const body = new TextEncoder().encode(JSON.stringify({ type: 'x', title: 'T', status: 422, code: 'UNREADABLE', detail: 'Nie odczytano tekstu.' }))
    const res = await interpretResponse(422, headersOf({ 'content-type': 'application/problem+json' }), body)
    expect(res).toMatchObject({ kind: 'error', code: 'UNREADABLE', status: 422, detail: 'Nie odczytano tekstu.' })
    expect(problemFrom(502, 'text/html', '<html>')).toMatchObject({ code: 'HTTP', status: 502 })
    const garbage = await interpretResponse(200, headersOf({ 'content-type': 'application/json' }), new TextEncoder().encode('[1]'))
    expect(garbage).toMatchObject({ kind: 'error', code: 'BAD_ANSWER' })
  })

  it('sends the file and the bearer token only to the relative address, and reports a lost connection', async () => {
    let seen: { url: string; init: RequestInit } | null = null
    const ok = async (url: string, init: RequestInit) => {
      seen = { url, init }
      return new Response(multipartBody(formBytes, metaBytes) as BlobPart, { status: 200, headers: { 'content-type': 'multipart/mixed; boundary=formularze-abc123' } })
    }
    const file = new File([new Uint8Array([1, 2, 3])], 'a.pdf')
    const res = await convertFile(file, ' secret-token ', ok)
    expect(res.kind).toBe('ok')
    expect(seen!.url).toBe('../v1/forms/convert?report=1')
    expect((seen!.init.headers as Record<string, string>).Authorization).toBe('Bearer secret-token')
    const none = await convertFile(file, '', ok)
    expect(none.kind).toBe('ok')
    expect((seen!.init.headers as Record<string, string>).Authorization).toBeUndefined()
    const lost = await convertFile(file, '', async () => { throw new TypeError('offline') })
    expect(lost).toMatchObject({ kind: 'error', code: 'NETWORK' })
  })
})
