// Wave 10 DICT: the page shows the dictionaries of the report (meta.proposals, meta.dictionary_links) and explains
// INPUT_NOTE. The sidecar shapes follow the converter (`app/compose/dictionaries.py`, `app/model/meta.py`
// ProposedDictionary, `app/model/sidecar.py` DictionaryLink). Synthetic data only.
import { beforeEach, describe, expect, it } from 'vitest'
import { renderConverted } from '../src/ui/result'
import { setLang } from '../src/lib/i18n'
import { readDictionaries } from '../src/lib/dictionaries'
import { interpretResponse, type Converted } from '../src/lib/api'
import { canonical, multipartBody, syntheticForm, syntheticSidecar } from './helpers'

const MP = { 'content-type': 'multipart/mixed; boundary=formularze-abc123' }
const ENTRIES = Array.from({ length: 20 }, (_, i) => `Dyscyplina ${i + 1}`)

async function answerOf(form: unknown, sidecar: unknown | null): Promise<Converted> {
  const res = await interpretResponse(200, new Headers(MP), multipartBody(canonical(form), sidecar ? canonical(sidecar) : null))
  if (res.kind !== 'ok') throw new Error('fixture failed')
  return res
}

function withDictionaries(extra: Record<string, unknown>) {
  const s = syntheticSidecar() as ReturnType<typeof syntheticSidecar> & { meta: Record<string, unknown> }
  s.meta = { ...(s.meta ?? {}), ...extra }
  return s
}

const PROPOSAL = {
  proposals: {
    dictionaries: [{
      name: 'Dyscypliny sportowe', entries: ENTRIES, pages: [2], field: 'f-2', fields: ['f-2'],
      why: 'Zamknięta lista 20 krótkich pozycji wydrukowana na formularzu (dane referencyjne).',
      use: 'Pole „Rodzaj sprawy” brałoby pozycje z tego słownika zamiast z listy opcji wpisanej w formularz.',
      evidence: [{ page: 2, quote: 'Dyscyplina 1' }]
    }]
  }
}
const LINKS = {
  dictionary_links: [
    { field: 'f-1', label: 'Kraj', dictionary: 'Kraje', written: true, why: 'Etykieta wskazuje kraj.' },
    { field: 'f-9', label: 'Miejscowość', dictionary: 'TERYT', written: false, why: 'Pasuje słownik partnera.' }
  ]
}

beforeEach(() => { setLang('pl'); document.body.innerHTML = '<div id="app"></div>' })

describe('DICT: reading the report', () => {
  it('reads proposals and links in the converter shape, skips malformed rows', () => {
    const d = readDictionaries(withDictionaries({
      ...PROPOSAL,
      dictionary_links: [...LINKS.dictionary_links, { label: 'bez słownika' }, 7, null]
    }))
    expect(d.proposals).toHaveLength(1)
    expect(d.proposals[0]).toMatchObject({ name: 'Dyscypliny sportowe', fields: ['f-2'], pages: [2] })
    expect(d.proposals[0].entries).toHaveLength(20)
    expect(d.links.map((l) => [l.label, l.dictionary, l.written])).toEqual([['Kraj', 'Kraje', true], ['Miejscowość', 'TERYT', false]])
  })

  it('no sidecar, no meta, or a proposals object without dictionaries gives two empty lists', () => {
    expect(readDictionaries(null)).toEqual({ proposals: [], links: [] })
    expect(readDictionaries(syntheticSidecar())).toEqual({ proposals: [], links: [] })
    expect(readDictionaries(withDictionaries({ proposals: { fee: { amount: 1 } } }))).toEqual({ proposals: [], links: [] })
  })

  it('a proposal with only `field` (no `fields`) still names that field', () => {
    const d = readDictionaries(withDictionaries({ proposals: { dictionaries: [{ name: 'X', entries: ['a'], field: 'f-2' }] } }))
    expect(d.proposals[0].fields).toEqual(['f-2'])
  })
})

describe('DICT: the block "Słowniki" on the page', () => {
  it('shows the proposed dictionary: name, purpose, field label, first 8 entries, the rest behind "pokaż wszystkie"', async () => {
    const root = renderConverted(await answerOf(syntheticForm(), withDictionaries({ ...PROPOSAL, ...LINKS })))
    const sec = root.querySelector('section.dictionaries') as HTMLElement
    expect(sec).not.toBeNull()
    expect(sec.querySelector('#h-dict')!.textContent).toBe('Słowniki')
    expect(sec.querySelector('#h-dict-new')!.textContent).toBe('Proponowany nowy słownik')
    const text = sec.textContent!
    expect(text).toContain('Nazwa słownika: Dyscypliny sportowe')
    expect(text).toContain('Do czego służy:')
    expect(text).toContain('dane referencyjne')
    expect(text).toContain('Pole formularza: „Rodzaj sprawy”')
    expect(text).toContain('Pozycje słownika (20):')
    const lists = sec.querySelectorAll('.dict-proposal ul.dict-entries')
    expect(lists[0].querySelectorAll('li')).toHaveLength(8)
    const more = sec.querySelector('.dict-proposal details.dict-more') as HTMLDetailsElement
    expect(more.open).toBe(false)
    expect(more.querySelector('summary')!.textContent).toBe('pokaż wszystkie (20)')
    expect(more.querySelectorAll('li')).toHaveLength(12)
    expect(more.querySelector('li:last-child')!.textContent).toBe('Dyscyplina 20')
  })

  it('lists the dictionaries linked to fields of the paper with label, name and whether the form carries it', async () => {
    const root = renderConverted(await answerOf(syntheticForm(), withDictionaries(LINKS)))
    const sec = root.querySelector('section.dictionaries') as HTMLElement
    expect(sec.querySelector('#h-dict-new')).toBeNull()
    expect(sec.querySelector('#h-dict-links')!.textContent).toBe('Słowniki przypisane do pól z druku')
    const items = [...sec.querySelectorAll('li.dict-link')].map((li) => li.textContent)
    expect(items).toEqual([
      '„Kraj” → Kraje zapisano w formularzu',
      '„Miejscowość” → TERYT tylko w raporcie, formularz bez zmian'
    ])
  })

  it('with neither list, one calm line that this form needs no dictionaries', async () => {
    const root = renderConverted(await answerOf(syntheticForm(), syntheticSidecar()))
    const sec = root.querySelector('section.dictionaries') as HTMLElement
    expect(sec.querySelectorAll('p')).toHaveLength(1)
    expect(sec.querySelector('#dict-none')!.textContent).toMatch(/^Ten formularz nie wymaga słowników/)
  })

  it('without the report there is no block (the page cannot know)', async () => {
    const root = renderConverted(await answerOf(syntheticForm(), null))
    expect(root.querySelector('section.dictionaries')).toBeNull()
  })

  it('stands between the fields of the paper and the remarks', async () => {
    const root = renderConverted(await answerOf(syntheticForm(), withDictionaries(PROPOSAL)))
    const order = [...root.querySelectorAll('section')].map((s) => s.getAttribute('aria-labelledby'))
    expect(order.indexOf('h-dict')).toBe(order.indexOf('h-matter') + 1)
    expect(order.indexOf('h-warnings')).toBeGreaterThan(order.indexOf('h-dict'))
  })

  it('text from the paper is shown as text, never as markup', async () => {
    const evil = { proposals: { dictionaries: [{ name: '<img src=x onerror=alert(1)>', entries: ['<b>a</b>'] }] } }
    const root = renderConverted(await answerOf(syntheticForm(), withDictionaries(evil)))
    expect(root.querySelector('section.dictionaries img')).toBeNull()
    expect(root.querySelector('section.dictionaries b')).toBeNull()
    expect(root.querySelector('section.dictionaries')!.textContent).toContain('<img src=x onerror=alert(1)>')
  })

  it('English page uses English headings', async () => {
    setLang('en')
    const root = renderConverted(await answerOf(syntheticForm(), syntheticSidecar()))
    expect(root.querySelector('#h-dict')!.textContent).toBe('Dictionaries')
  })
})

describe('DICT: INPUT_NOTE is described in Polish and the service sentence is shown', () => {
  it('a known explanation, never "kod, którego ta strona jeszcze nie opisuje", and the guard sentence once', async () => {
    const s = syntheticSidecar()
    const note = 'Rozszerzenie .pdf nie zgadza się z zawartością; plik odczytano jako obraz PNG.'
    s.warnings = [{ code: 'INPUT_NOTE', detail: note }, { code: 'INPUT_NOTE', detail: note }] as typeof s.warnings
    const root = renderConverted(await answerOf(syntheticForm(), s))
    const box = root.querySelector('section.remarks') as HTMLElement
    const text = box.textContent!
    expect(text).not.toContain('jeszcze nie opisuje')
    expect(text).toContain('Uwaga o samym pliku, nie o treści druku')
    expect(text).toContain('Treść uwagi usługi:')
    expect(text.split(note)).toHaveLength(2)
  })
})
