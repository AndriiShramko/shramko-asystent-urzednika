// Wave 11, lane CLERK-P: two views of one result, remarks as cards on the document, one-click fixes of the
// clerk-contract v1. Synthetic data only.
import { beforeEach, describe, expect, it } from 'vitest'
import { setLang } from '../src/lib/i18n'
import { interpretResponse, type Converted } from '../src/lib/api'
import { fixOf, nodeAt, setPointer } from '../src/lib/warnings'
import { renderConverted } from '../src/ui/result'
import { mountFill } from '../src/ui/fill'
import { getView, setView } from '../src/ui/clerk-view'
import { pointerOfNode, sessionOf, CARDS_SHOWN } from '../src/ui/clerk-remarks'
import { canonical, multipartBody } from './helpers'
import { fpForm, fpLedgerSidecar, fpPreview } from './fp-fixture'

const GRID = '/tabs/1/questions/0/field/repeatingSectionGrid'

function requiredChoice() {
  return { code: 'REQUIRED_INFERRED', field: 'data_urodzenia', page: 1, detail: 'the paper does not say whether this is required',
    fix: { kind: 'choice', rule: 'required.usually_optional', text: 'Druk nie mówi, czy pole „Data urodzenia” jest obowiązkowe.',
      target: { id: 'f-data', pointer: GRID + '/1/field', label: 'Data urodzenia', tab: 'Szczegóły sprawy' },
      options: [
        { label: 'Obowiązkowe', value: 'required', current: true, set: [{ pointer: GRID + '/1/field/validation', value: ['REQUIRED'] }], source: { type: 'rule', name: 'unmarked-blank-is-required' } },
        { label: 'Nieobowiązkowe', value: 'optional', current: false, set: [{ pointer: GRID + '/1/field/validation', value: [] }], source: { type: 'dictionary', name: 'optional-concepts' } }] } }
}
const applied = () => ({ code: 'CLAUSE_LINK_MISSING', detail: 'no https address of the information clause is known',
  fix: { kind: 'applied', rule: 'clause.as_partner_exports', text: 'Na druku nie ma klauzuli informacyjnej; zgoda ma brzmienie z wzorcowych formularzy.', source: { type: 'rule', name: 'partner-exports' } } })
const typeIn = () => ({ code: 'ADDRESSEE_MISSING', detail: 'the brief names no addressee',
  fix: { kind: 'input', rule: 'addressee.none', text: 'Na druku nie ma nazwy urzędu. Wpisz adresata.',
    target: { id: 'f-nip', pointer: GRID + '/0/field', label: 'NIP', tab: 'Szczegóły sprawy' },
    input: { label: 'Nazwa urzędu', set: [{ pointer: GRID + '/0/field/defaultValue', from: 'input' }] } } })
const raw = () => ({ code: 'LABEL_RAW', page: 1, candidate: 'c4', evidence: [], detail: 'label kept as the paper\'s words' })
const note = () => ({ code: 'INFERRED_SHAPE', detail: 'DATEPICKER: no export shows one', field: 'f-data' })
const blank = (i: number) => ({ code: 'LABEL_NOT_FOUND', page: 1, box: [80, 600 + i * 20, 300, 612 + i * 20], candidate: 'x' + i, evidence: [], detail: 'no text that this place belongs to' })

async function page(warnings: unknown[], preview: unknown = fpPreview(), extra: Record<string, unknown> = {}) {
  const sidecar = fpLedgerSidecar() as unknown as { warnings: unknown[]; meta: Record<string, unknown> }
  sidecar.warnings = warnings
  Object.assign(sidecar.meta, extra)
  const res = await interpretResponse(200, new Headers({ 'content-type': 'multipart/mixed; boundary=formularze-abc123' }),
    multipartBody(canonical(fpForm()), canonical(sidecar))) as Converted
  // composed as the page composes it: the result, then the fill block before the JSON section
  const view = renderConverted(res)
  const fill = mountFill(res, Promise.resolve(preview))
  view.insertBefore(fill.el, view.querySelector('section[aria-labelledby="h-json"]'))
  document.body.append(view)
  await fill.where.ready
  return { res, view, fill, session: sessionOf(res.sidecar) }
}
const q = <T extends HTMLElement>(s: string) => document.querySelector<T>(s)!
const all = (s: string) => [...document.querySelectorAll<HTMLElement>(s)]
const formAt = (form: unknown, i: number) => (form as ReturnType<typeof fpForm>).tabs[1].questions[0].field.repeatingSectionGrid[i].field as Record<string, unknown>

beforeEach(() => { setLang('pl'); setView('clerk'); document.body.innerHTML = '' })

describe('W11 two views', () => {
  it('the clerk view is the default; the switch writes data-view and keeps the choice for the next render', async () => {
    const { view, res } = await page([requiredChoice(), applied()])
    expect(view.children[0].id).toBe('h-done')
    expect(view.getAttribute('data-view')).toBe('clerk')
    expect(q('.headline-clerk').textContent).toBe('E-formularz jest gotowy. Porównaj go z oryginałem.')
    const [clerk, jury] = all('.view-btn')
    expect([clerk.textContent, jury.textContent]).toEqual(['Widok urzędnika', 'Widok dla jury'])
    expect(clerk.getAttribute('aria-pressed')).toBe('true')
    jury.click()
    expect(view.getAttribute('data-view')).toBe('jury')
    expect(jury.getAttribute('aria-pressed')).toBe('true')
    expect(getView()).toBe('jury')
    expect(renderConverted(res).getAttribute('data-view')).toBe('jury')
  })

  it('what is technical is marked for the jury only; the clerk blocks carry no code and no English', async () => {
    await page([requiredChoice(), applied(), note(), raw()])
    for (const id of ['h-summary', 'h-matter', 'h-warnings', 'h-json', 'h-jury-done']) {
      expect(document.getElementById(id)!.closest('.jury-only'), id).not.toBeNull()
    }
    for (const sel of ['#clerk-top', '#clerk-final']) {
      const el = q(sel)
      expect(el.classList.contains('clerk-only')).toBe(true)
      expect(el.querySelector('.code')).toBeNull()
      expect(el.textContent).not.toMatch(/REQUIRED_INFERRED|LABEL_RAW|kod:|the paper/)
    }
    expect(q('#h-where').classList.contains('jury-only')).toBe(true)
    expect(q('#fp-where .clerk-col-title').textContent).toBe('Oryginał')
    expect(q('#fp-eform .clerk-col-title').textContent).toBe('E-formularz')
    // the jury sees what the converter settled itself, with the code and the rule
    expect(q('#jury-applied').textContent).toContain('Naprawione automatycznie (1)')
    expect(q('#jury-applied').textContent).toContain('CLAUSE_LINK_MISSING')
    expect(q('#jury-applied').textContent).toContain('clause.as_partner_exports')
  })
})

describe('W11 the list of the clerk', () => {
  it('counts only what is open: applied fixes and notes of the run are not there; many places of one kind share a card', async () => {
    const { session } = await page([requiredChoice(), applied(), typeIn(), raw(), note(), ...[0, 1, 2, 3, 4].map(blank)])
    expect(session.applied).toHaveLength(1)
    expect(session.notes).toHaveLength(1)
    expect(session.openCount()).toBe(7)
    expect(q('#h-clerk-remarks').textContent).toBe('Do sprawdzenia (7)')
    expect(q('#clerk-final-state').textContent).toBe('Do sprawdzenia: 7.')
    expect(session.remarks).toHaveLength(7) // choice, input, raw, three blanks, one card for the other two blanks
    expect(session.remarks[0].fix.kind).toBe('choice') // ready choices first
    expect(session.remarks[6].items).toHaveLength(2)
    expect(all('.clerk-card')).toHaveLength(CARDS_SHOWN)
    q('#clerk-remarks-more').click()
    expect(all('.clerk-card')).toHaveLength(7)
    expect(all('.clerk-card')[6].textContent).toContain('(2 miejsca)')
    expect(all('.clerk-card')[6].querySelector('.clerk-stepper')!.textContent).toContain('1 z 2')
  })

  it('nothing open: one calm line', async () => {
    await page([applied(), note()])
    expect(q('#h-clerk-remarks').textContent).toBe('Nic do sprawdzenia. Program nie znalazł miejsc, które wymagają Twojej decyzji.')
    expect(q('#clerk-final-state').textContent).toBe('Wszystko sprawdzone.')
    expect(all('.clerk-card')).toHaveLength(0)
  })
})

describe('W11 remarks on the document', () => {
  it('a card shows a crop of the original and the e-form field; a click lights both; a mark on the original lights the card', async () => {
    await page([raw(), blank(0)])
    const [rawCard, blankCard] = all('.clerk-card')
    expect(rawCard.querySelector('.clerk-crop img')!.getAttribute('src')).toBe('data:image/png;base64,AAAA')
    expect(rawCard.querySelector('.clerk-crop-mark')).not.toBeNull()
    expect(rawCard.querySelector('.clerk-card-cap')!.textContent).toBe('Na oryginale, strona 1:')
    expect(rawCard.querySelector('.clerk-card-field')!.textContent).toBe('NIP') // candidate c4 became the field f-nip
    // BL13 CLERK-T: the sentence says plainly why there is no field; no separate "not in the e-form" line
    expect(blankCard.querySelector('.clerk-card-what')!.textContent).toContain('Program nie zrobił tu pola, bo druk nie mówi, co tu wpisać.')
    expect(blankCard.querySelector('.clerk-card-field')).toBeNull()
    expect(blankCard.querySelector('.clerk-fix button')!.textContent).toBe('Pomiń to miejsce (nie będzie polem)')
    // the same numbers on the cards, on the original and on the e-form field
    expect(all('#fp-papers .clerk-mark').map((m) => m.textContent)).toEqual(['1', '2'])
    expect(q('[id="fpw-f-nip"] .clerk-flag').textContent).toBe('1do sprawdzenia')
    rawCard.querySelector<HTMLElement>('.clerk-card-main')!.click()
    expect(rawCard.classList.contains('clerk-card-active')).toBe(true)
    expect(all('#fp-papers .clerk-spot')).toHaveLength(1)
    expect(q('[id="fpw-f-nip"]').classList.contains('clerk-hl')).toBe(true)
    all('#fp-papers .clerk-mark')[1].click()
    expect(blankCard.classList.contains('clerk-card-active')).toBe(true)
    expect(rawCard.classList.contains('clerk-card-active')).toBe(false)
    // a box of the original shows its field in the e-form and lights the card of that field
    q('.fp-box[data-cid="c4"]').click()
    expect(rawCard.classList.contains('clerk-card-active')).toBe(true)
  })

  it('a remark without a place says so: the top of page 1 where it would be, or plainly that the paper has no such place', async () => {
    await page([{ code: 'TITLE_MISSING', detail: 'no title' }, { code: 'NO_MATTER', detail: 'nothing' }])
    const [title] = all('.clerk-card')
    const matter = q('#clerk-rest-line')
    expect(title.querySelector('.clerk-card-cap')!.textContent).toBe('Na oryginale tego nie ma. Zwykle jest tutaj, u góry pierwszej strony:')
    expect(title.querySelector('.clerk-crop')).not.toBeNull()
    expect(title.querySelector('.clerk-crop-mark')).toBeNull()
    expect(all('.clerk-card')).toHaveLength(1)
    expect(matter.textContent).toContain('Uwagi techniczne bez miejsca na oryginale: 1')
    expect(matter.textContent).not.toContain('cały formularz')
  })

  it('a format without page pictures: the card names the place in the file, the e-form takes the whole width', async () => {
    await page([{ code: 'LABEL_NOT_FOUND', page: 1, anchor: 'p[12]', candidate: 'c4', evidence: [], detail: 'x' }], fpPreview(false))
    // BL13 CLERK-T: the paper's own words at that place, never the cell or paragraph address
    expect(q('.clerk-card .clerk-card-cap').textContent).toBe('W pliku, w tym miejscu jest tekst:')
    expect(q('.clerk-card .clerk-quote').textContent).toBeTruthy()
    expect(q('.clerk-card').textContent).not.toContain('p[12]')
    expect(q('#fp-where').getAttribute('data-pages')).toBe('0')
  })

  it('a doubtful field carries a quiet mark; a sure one carries none', async () => {
    await page([], fpPreview(), { confidence: { 'f-nip': { band: 'check', signals: ['ocr_low'] }, 'f-data': { band: 'sure', signals: ['text_layer'] }, 'f-cel': { band: 'unsure', signals: ['label_missing'] } } })
    expect(q('[id="fpw-f-nip"] .clerk-doubt').textContent).toBe('do sprawdzenia')
    expect(q('[id="fpw-f-cel"] .clerk-doubt').textContent).toBe('niepewne')
    expect(document.querySelector('[id="fpw-f-data"] .clerk-doubt')).toBeNull()
    expect(q('#jury-done').textContent).toContain('pewne 1, do sprawdzenia 1, niepewne 1')
  })
})

describe('W11 fix by click', () => {
  it('a ready choice: one click writes it into the form, the e-form redraws the field, the remark leaves the list', async () => {
    const { session, res } = await page([requiredChoice(), raw()])
    const card = q('.clerk-card[data-fix="choice"]')
    expect(card.querySelector('.clerk-card-what')!.textContent).toContain('Dotyczy to pól: „Data urodzenia”.')
    expect(all('.clerk-card[data-fix="choice"] .clerk-fix-btn').map((b) => b.textContent)).toEqual(['Ustaw to pole jako obowiązkowe (tak jest teraz)', 'Zostaw to pole jako nieobowiązkowe'])
    expect(document.querySelector('[id="fpw-f-data"] .fp-req')).not.toBeNull()
    expect(session.changedForm()).toBeNull()
    card.querySelector<HTMLElement>('[data-option="1"]')!.click()
    expect(document.querySelector('.clerk-card[data-fix="choice"]')).toBeNull()
    expect(q('#h-clerk-remarks').textContent).toBe('Do sprawdzenia (1)')
    expect(document.querySelector('[id="fpw-f-data"] .fp-req')).toBeNull()
    expect(formAt(session.changedForm(), 1).validation).toEqual([])
    expect(formAt(res.form, 1).validation).toEqual(['REQUIRED']) // the answer of the service is not touched
    expect(q('#clerk-final-state').textContent).toBe('Do sprawdzenia: 1. Twoja poprawka: 1.')
    expect(q('#jury-applied').textContent).toContain('Poprawki urzędnika (1)')
    expect(q('#jury-applied').textContent).toContain('Data urodzenia: Nieobowiązkowe')
  })

  it('the option that is the current state confirms and changes nothing', async () => {
    const { session } = await page([requiredChoice()])
    q('.clerk-card [data-option="0"]').click()
    expect(session.openCount()).toBe(0)
    expect(session.changedForm()).toBeNull()
    expect(q('#h-clerk-remarks').textContent).toBe('Wszystko sprawdzone. Możesz pobrać e-formularz.')
  })

  it('input is the last resort and happens in the e-form field itself', async () => {
    const { session } = await page([typeIn()])
    const card = q('.clerk-card[data-fix="input"]')
    expect(card.querySelector('.clerk-card-what')!.textContent).toContain('Na druku nie ma nazwy urzędu. Wpisz adresata.')
    card.querySelector<HTMLElement>('[data-type-in]')!.click()
    const field = q('[id="fpw-f-nip"]')
    expect(field.querySelector('.clerk-ask-label')!.textContent).toBe('Nazwa urzędu')
    expect(document.querySelector('#clerk-top input')).toBeNull() // never a separate form
    const input = q<HTMLInputElement>('[id="fpf-f-nip"]')
    field.querySelector<HTMLElement>('.clerk-ask .btn-main')!.click() // empty: nothing is saved
    expect(session.openCount()).toBe(1)
    input.value = 'Urząd Gminy Przykładowo'
    field.querySelector<HTMLElement>('.clerk-ask .btn-main')!.click()
    expect(session.openCount()).toBe(0)
    expect(formAt(session.changedForm(), 0).defaultValue).toBe('Urząd Gminy Przykładowo')
    expect(q<HTMLInputElement>('[id="fpf-f-nip"]').value).toBe('Urząd Gminy Przykładowo')
  })

  it('FIX-UI: a field in a hidden section is renamed inside the card', async () => {
    const { session } = await page([raw()])
    const wrapper = q('[id="fpw-f-nip"]')
    const sec = document.createElement('div'); sec.hidden = true
    wrapper.parentElement!.insertBefore(sec, wrapper); sec.appendChild(wrapper)
    const card = q('.clerk-card')
    card.querySelector<HTMLElement>('[data-type-in]')!.click()
    const name = card.querySelector<HTMLInputElement>('.clerk-edit-inline .clerk-edit-input')!
    expect(name.value).toBe('NIP')
    name.value = 'Numer NIP firmy'
    card.querySelector<HTMLElement>('.clerk-edit-inline .btn-main')!.click()
    expect(formAt(session.changedForm(), 0).title).toBe('Numer NIP firmy')
    expect(session.openCount()).toBe(0)
  })

  it('a remark without a fix is input too: the name of the field is corrected in place', async () => {
    const { session } = await page([raw()])
    const card = q('.clerk-card')
    expect(card.getAttribute('data-fix')).toBe('input')
    expect(all('.clerk-card .clerk-fix button').map((b) => b.textContent)).toEqual(['Popraw nazwę pola', 'Sprawdzone, zostaw bez zmian'])
    card.querySelector<HTMLElement>('[data-type-in]')!.click()
    const name = q<HTMLInputElement>('[id="fpw-f-nip"] .clerk-edit-input')
    expect(name.value).toBe('NIP')
    name.value = 'Numer NIP firmy'
    q('[id="fpw-f-nip"] .clerk-edit .btn-main').click()
    expect(q('[id="fpw-f-nip"] > label').textContent).toBe('Numer NIP firmy')
    expect(formAt(session.changedForm(), 0).title).toBe('Numer NIP firmy')
    expect(session.openCount()).toBe(0)
  })

  it('"Jest dobrze" closes a remark that needs no change; a card of many places closes them all', async () => {
    const { session } = await page([0, 1, 2, 3, 4].map(blank))
    expect(session.openCount()).toBe(4)
    all('.clerk-card')[3].querySelector<HTMLElement>('[data-done]')!.click()
    expect(session.openCount()).toBe(3)
    expect(session.changedForm()).toBeNull()
  })
})

describe('W11 contract helpers', () => {
  it('fixOf reads the three kinds, treats a missing fix as input and a broken choice as input', () => {
    expect(fixOf(applied() as never).kind).toBe('applied')
    expect(fixOf(requiredChoice() as never).kind).toBe('choice')
    expect(fixOf(raw() as never)).toMatchObject({ kind: 'input', stated: false })
    expect(fixOf(note() as never).kind).toBe('note')
    expect(fixOf({ code: 'X', fix: { kind: 'choice', text: 'q', options: [{ label: 'only one', set: [] }] } } as never)).toMatchObject({ kind: 'input', stated: true })
    expect(fixOf({ code: 'X', fix: 'nonsense' } as never).kind).toBe('input')
  })

  it('setPointer replaces an existing place and never builds a path; nodeAt names the node and its key', () => {
    const form = fpForm()
    expect(setPointer(form, GRID + '/1/field/validation', [])).toBe(true)
    expect(formAt(form, 1).validation).toEqual([])
    expect(setPointer(form, GRID + '/99/field/validation', [])).toBe(false)
    expect(setPointer(form, '/nowhere/deep/key', 1)).toBe(false)
    expect(setPointer(form, '/tabs/0/__proto__', 1)).toBe(false)
    expect(nodeAt(form, GRID + '/1/field/validation')).toEqual({ id: 'f-data', key: 'validation' })
    expect(pointerOfNode(form, 'f-cel')).toBe(GRID + '/2/field')
    expect(pointerOfNode(form, 'missing')).toBeNull()
  })
})
