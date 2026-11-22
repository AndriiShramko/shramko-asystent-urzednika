// Wave 10, UX2: the page tells the truth about the paper (live check TU2, 22.11.2026). Synthetic data only.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mountApp, LONG_MS } from '../src/ui/app'
import { renderConverted, renderProblem } from '../src/ui/result'
import { setLang } from '../src/lib/i18n'
import { formatsOf, titleLooksRead } from '../src/lib/verdict'
import { interpretResponse, type Converted, type Outcome, type ConvertHooks } from '../src/lib/api'
import { canonical, cell, field, multipartBody, syntheticForm, syntheticSidecar } from './helpers'

const MP = { 'content-type': 'multipart/mixed; boundary=formularze-abc123' }

async function answerOf(form: unknown, sidecar: unknown | null): Promise<Converted> {
  const res = await interpretResponse(200, new Headers(MP), multipartBody(canonical(form), sidecar ? canonical(sidecar) : null))
  if (res.kind !== 'ok') throw new Error('fixture failed')
  return res
}

/** A photo of a blank as the service answers it today: one field from the paper, many standard ones (set 03 JPG). */
function photoAnswer(title = 'Wniosek o wydanie zaświadczenia') {
  const std = Array.from({ length: 12 }, (_, i) => field(`st-${i}`, 'TEXT_FIELD', `Pole standardowe ${i}`))
  const form = {
    title,
    tabs: [
      { id: 't-1', title: 'Dane', type: 'MAIN', questions: [cell(field('s-std', 'SECTION', 'Dane wnioskodawcy', { repeatingSectionGrid: std.map((f, i) => cell(f, i)) }))] },
      { id: 't-2', title: 'Sprawa', type: 'MAIN', questions: [cell(field('s-m', 'SECTION', 'Szczegóły sprawy', { repeatingSectionGrid: [cell(field('m-1', 'TEXT_FIELD', 'Cel zaświadczenia'))] }))] }
    ],
    flow: { links: [] }
  }
  const origins: Record<string, string> = { 's-std': 'standard', 's-m': 'paper', 'm-1': 'paper' }
  for (const f of std) origins[f.id] = 'standard'
  const sidecar = { version: 1, counts: { pages: 2, fields: 13, source_pages: 1 }, warnings: [{ code: 'LABEL_RAW', page: 1 }], meta: { origins, evidence: {} } }
  return { form, sidecar }
}

beforeEach(() => { setLang('pl'); document.body.innerHTML = '<div id="app"></div>' })
afterEach(() => { vi.useRealTimers() })

describe('UX2 1: the headline tells the truth about the paper', () => {
  it('one field from the paper among many standard ones is amber, with both numbers', async () => {
    const { form, sidecar } = photoAnswer()
    const root = renderConverted(await answerOf(form, sidecar))
    const h2 = root.querySelector('#h-done') as HTMLElement
    expect(h2.dataset.kind).toBe('partial')
    const line = h2.querySelector('.headline')!.textContent!
    expect(line).toContain('z druku: 1, standardowych: 12')
    expect(line).toContain('częściowo')
    expect(line).toContain('Sprawdź druk ręcznie')
  })

  it('a normal result stays green and still shows both numbers', async () => {
    const root = renderConverted(await answerOf(syntheticForm(), syntheticSidecar()))
    const h2 = root.querySelector('#h-done') as HTMLElement
    expect(h2.dataset.kind).toBe('ok')
    expect(h2.querySelector('.headline')!.textContent).toBe('Formularz przetworzony: 4 pola w 2 sekcjach (z druku: 2, standardowych: 2)')
  })

  it('the service warning NO_MATTER (patch DX-3) alone makes the line amber, even with fields of origin "paper"', async () => {
    const s = syntheticSidecar()
    s.warnings = [{ code: 'NO_MATTER', detail: 'Z dokumentu nie odczytano żadnego pola sprawy' }] as typeof s.warnings
    const root = renderConverted(await answerOf(syntheticForm(), s))
    const h2 = root.querySelector('#h-done') as HTMLElement
    expect(h2.dataset.kind).toBe('partial')
    expect(h2.querySelector('.headline')!.textContent).toContain('z druku: 2, standardowych: 2')
  })

  it('the status line says how few fields were read', async () => {
    const { form, sidecar } = photoAnswer()
    const outcome = await answerOf(form, sidecar)
    mountApp(document.getElementById('app')!, { store: null, status: async () => null, convert: async () => outcome })
    const file = document.getElementById('file') as HTMLInputElement
    Object.defineProperty(file, 'files', { value: [new File([new Uint8Array([1])], 'zdjecie.jpg')], configurable: true })
    file.dispatchEvent(new Event('change'))
    await new Promise((r) => setTimeout(r, 0))
    expect(document.getElementById('status')!.textContent).toBe('Formularz „Wniosek o wydanie zaświadczenia” przetworzony częściowo: z druku odczytano tylko 1 pole.')
  })
})

describe('UX2 2: the waiting text', () => {
  it('never promises "do 60 s"; the long state says large scans take minutes; seconds and Przerwij stay', async () => {
    vi.useFakeTimers()
    let hooks: ConvertHooks | undefined
    mountApp(document.getElementById('app')!, {
      store: null, status: async () => null,
      convert: (_f, _t, hk) => { hooks = hk; return new Promise<Outcome>(() => undefined) }
    })
    const file = document.getElementById('file') as HTMLInputElement
    Object.defineProperty(file, 'files', { value: [new File([new Uint8Array(4096)], 'skan.pdf')], configurable: true })
    file.dispatchEvent(new Event('change'))
    hooks!.onUploaded!()
    vi.advanceTimersByTime(LONG_MS + 1000)
    const all = (document.getElementById('progress')!.textContent ?? '') + (document.getElementById('status')!.textContent ?? '')
    expect(all).not.toContain('60 s')
    expect(document.getElementById('progress-long')!.textContent).toContain('kilka minut')
    expect(document.getElementById('progress-elapsed')!.textContent).toBe(`Czas: ${LONG_MS / 1000 + 1} s`)
    expect(document.getElementById('progress-cancel')!.textContent).toBe('Przerwij')
  })
})

describe('UX2 3: thousands of remarks of one kind do not alarm', () => {
  it('kinds in the heading, each kind collapsed with its count and only the first few places', async () => {
    const s = syntheticSidecar()
    const many = Array.from({ length: 2030 }, (_, i) => ({ code: 'LABEL_NOT_FOUND', page: 1, anchor: `Formularz!B${i + 3}`, candidate: `c${i}`, evidence: [], detail: 'no text' }))
    s.warnings = [...many, { code: 'REQUIRED_INFERRED', detail: 'x' }] as typeof s.warnings
    const root = renderConverted(await answerOf(syntheticForm(), s))
    const box = root.querySelector('details.remarks-box') as HTMLDetailsElement
    expect(box.open).toBe(false)
    const head = box.querySelector('summary')!.textContent!
    expect(head).toBe('Uwagi do sprawdzenia przez urzędnika (2 rodzaje)')
    expect(head).not.toContain('2031')
    const kinds = box.querySelectorAll('details.remark')
    expect(kinds.length).toBe(2)
    const first = kinds[0] as HTMLDetailsElement
    expect(first.open).toBe(false)
    expect(first.querySelector('summary')!.textContent).toContain('2030 miejsc')
    expect(first.querySelectorAll('.places li').length).toBe(5)
    expect(first.querySelector('.places')!.textContent).toContain('Formularz!B3')
    expect(first.textContent).toContain('i jeszcze 2025 miejsc')
    expect(root.textContent).toContain('Uwagi: 2 rodzaje (2031 miejsc)')
  })

  it('remarks that name only a page get no list of "strona 1, strona 1" (the page is on the code line)', async () => {
    const root = renderConverted(await answerOf(syntheticForm(), syntheticSidecar()))
    const first = root.querySelector('details.remark')!
    expect(first.querySelector('.places')).toBeNull()
    expect(first.querySelector('.code-line')!.textContent).toContain('strona 1')
  })
})

describe('UX2 4: wording', () => {
  it('"(n z n)" is never shown: all fields without a place say so plainly', async () => {
    const s = syntheticSidecar()
    s.meta.evidence = {} as typeof s.meta.evidence
    const root = renderConverted(await answerOf(syntheticForm(), s))
    const line = root.querySelector('#matter-nosource')!.textContent!
    expect(line).toBe('Dla żadnego z tych pól nie ustalono miejsca na druku.')
    expect(line).not.toContain('2 z 2')
  })

  it('some fields without a place: "Dla 1 z 2 pól"', async () => {
    const s = syntheticSidecar()
    s.meta.evidence = { 'f-1': { page: 2, quote: 'Nazwa ulicy' } } as unknown as typeof s.meta.evidence
    const root = renderConverted(await answerOf(syntheticForm(), s))
    expect(root.querySelector('#matter-nosource')!.textContent).toBe('Dla 1 z 2 pól nie ustalono miejsca na druku.')
  })

  it('an empty file is called empty, whatever code the service gave', () => {
    const p = renderProblem({ kind: 'error', code: 'TYPE_MISMATCH', status: 415, detail: 'Rozszerzenie .pdf, a zawartość nie jest rozpoznanym formatem.', title: null },
      { pickOther: () => undefined }, { fileSize: 0 })
    expect(p.querySelector('.reason')!.textContent).toBe('Plik jest pusty (0 bajtów).')
    expect(p.querySelector('.todo')!.textContent).toContain('zapisz lub pobierz formularz ponownie')
    expect(p.textContent).not.toContain('nie zgadza się z jego rozszerzeniem')
    expect(p.querySelector('.code-line')!.textContent).toContain('TYPE_MISMATCH')
  })

  it('a non-empty file with the same code keeps the type advice', () => {
    const p = renderProblem({ kind: 'error', code: 'TYPE_MISMATCH', status: 415, detail: null, title: null }, {}, { fileSize: 10 })
    expect(p.querySelector('.reason')!.textContent).toBe('Zawartość pliku nie zgadza się z jego rozszerzeniem.')
  })

  it('the formats line and the picker come from /status, not from the page', async () => {
    const status = { engine: 'rules', formats: ['pdf', 'docx', 'rtf', 'jpeg', 'tiff', 'odt'] }
    mountApp(document.getElementById('app')!, { store: null, status: async () => status, convert: async () => ({ kind: 'error', code: 'X', status: 0, detail: null, title: null }) })
    await new Promise((r) => setTimeout(r, 0))
    const line = document.getElementById('formats')!.textContent!
    expect(line).toBe('Obsługiwane formaty: PDF, DOCX, RTF, JPEG (JPG), TIFF (TIF), ODT.')
    const accept = (document.getElementById('file') as HTMLInputElement).accept
    for (const ext of ['.pdf', '.rtf', '.jpg', '.jpeg', '.tif', '.tiff', '.odt']) expect(accept.split(',')).toContain(ext)
  })

  it('no /status: no invented list, the picker takes any file and the service decides', async () => {
    mountApp(document.getElementById('app')!, { store: null, status: async () => null })
    await new Promise((r) => setTimeout(r, 0))
    expect(document.body.textContent).not.toContain('PDF, DOC, DOCX, ODS, XLSX')
    expect((document.getElementById('file') as HTMLInputElement).getAttribute('accept')).toBeNull()
  })

  it('EXTENSION advice names the formats of /status', () => {
    const p = renderProblem({ kind: 'error', code: 'EXTENSION', status: 415, detail: null, title: null }, {}, { formats: ['pdf', 'rtf'] })
    expect(p.querySelector('.todo')!.textContent).toContain('PDF, RTF')
  })

  it('formatsOf keeps only plain extension names', () => {
    expect(formatsOf({ formats: ['PDF', ' docx ', '<b>', 7, 'toolongext'] })).toEqual(['pdf', 'docx'])
    expect(formatsOf(null)).toEqual([])
    expect(formatsOf({ formats: 'pdf' })).toEqual([])
  })

  it('a garbage OCR title is not shown as the title; the raw text stays small and grey', async () => {
    const { form, sidecar } = photoAnswer('zdnia')
    const root = renderConverted(await answerOf(form, sidecar))
    const name = root.querySelector('.form-name')!
    expect(name.textContent).toContain('Tytuł nie został odczytany z druku')
    expect(name.querySelector('.title-raw')!.textContent).toContain('zdnia')
    expect(name.textContent).not.toContain('Tytuł formularza:')
  })

  it('which titles look read', () => {
    expect(titleLooksRead('zdnia')).toBe(false)
    expect(titleLooksRead('Xqrtzp Wkrst')).toBe(false)
    expect(titleLooksRead('')).toBe(false)
    expect(titleLooksRead('Wniosek o wydanie zaświadczenia')).toBe(true)
    expect(titleLooksRead('zaswiadczenia')).toBe(true)
    expect(titleLooksRead('PIT-37')).toBe(true) // a form code is a title
  })

  it('LABEL_NOT_FOUND reads as a whole sentence', async () => {
    const root = renderConverted(await answerOf(syntheticForm(), syntheticSidecar()))
    expect(root.textContent).toContain('Znaleziono miejsce do wpisania, ale nie znaleziono jego opisu.')
  })
})
