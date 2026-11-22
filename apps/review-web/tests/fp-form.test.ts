// FP step 3: the electronic form from the JSON. Conditions in the composer's real shapes, validators with values
// built from a stem plus a computed digit, the DOM of the form. Synthetic data only.
import { beforeEach, describe, expect, it } from 'vitest'
import { evaluate, parseCondition, reasons } from '../src/lib/fp/conditions'
import { readForm, refKey, htmlText } from '../src/lib/fp/form'
import { validate, peselCheck, nipCheck, regonCheck, idCardCheck } from '../src/lib/fp/validators'
import { renderEForm } from '../src/ui/eform'
import { mountApp } from '../src/ui/app'
import { setLang } from '../src/lib/i18n'
import { interpretResponse, type Outcome } from '../src/lib/api'
import { canonical, multipartBody } from './helpers'
import { fpForm, fpSidecar } from './fp-fixture'

const REF = (t: string, s: string, f: string) =>
  `tabs['${t}' in title].questions['${s}' in field.techName].field.repeatingSectionGrid['${f}' in field.techName].field.__userAnswer`

beforeEach(() => { setLang('pl'); document.body.innerHTML = '<div id="app"></div>' })

describe('FP conditions', () => {
  const look = (answers: Record<string, string[]>) => (k: string) => answers[k] ?? []
  const kraj = refKey('Dane', 'adres_zamieszkania', 'kraj')

  it('reads the positive, negated and joined shapes of the composer', () => {
    const pos = parseCondition(`("Polska" in ${REF('Dane', 'adres_zamieszkania', 'kraj')})`)!
    const neg = parseCondition(`$not("Polska" in ${REF('Dane', 'adres_zamieszkania', 'kraj')})`)!
    expect(pos).not.toBeNull()
    expect(evaluate(pos, look({ [kraj]: ['Polska'] }))).toBe(true)
    expect(evaluate(neg, look({ [kraj]: ['Polska'] }))).toBe(false)
    expect(evaluate(neg, look({}))).toBe(true)
    const joined = parseCondition(`("A" in ${REF('T', 's', 'f')}) and $not("B" in ${REF('T', 's', 'g')} or "C" in ${REF('T', 's', 'g')})`)!
    const kf = refKey('T', 's', 'f'); const kg = refKey('T', 's', 'g')
    expect(evaluate(joined, look({ [kf]: ['A'] }))).toBe(true)
    expect(evaluate(joined, look({ [kf]: ['A'], [kg]: ['C'] }))).toBe(false)
    expect(reasons(joined, look({ [kf]: ['A'] }))).toEqual(['A'])
  })

  it('accepts the repeating-section index suffix and refuses unknown shapes', () => {
    expect(parseCondition(`"X" in ${REF('T', 's', 'f')}[$repeatingSectionIndex]`)).not.toBeNull()
    expect(parseCondition('$count(x) > 1')).toBeNull()
    expect(parseCondition('')).toBeNull()
    expect(parseCondition(`"X" in ${REF('T', 's', 'f')} and`)).toBeNull()
  })
})

describe('FP validators (values built from stems at run time)', () => {
  const pesel = (stem: string) => stem + peselCheck(stem)
  it('PESEL: computed check digit passes, a changed digit fails with the design sentence', () => {
    const good = pesel('8403150001')
    expect(validate(good, ['PESEL'])).toBeNull()
    const bad = good.slice(0, 10) + ((Number(good[10]) + 1) % 10)
    expect(validate(bad, ['PESEL'])).toBe('Numer PESEL ma błędną cyfrę kontrolną.')
    expect(validate('123', ['PESEL'])).toMatch(/11 cyfr/)
  })
  it('NIP, REGON, ID card, ZIP, e-mail, ePUAP, ADE', () => {
    const nipStem = '554000010'
    expect(nipCheck(nipStem)).not.toBe(10)
    expect(validate(nipStem + nipCheck(nipStem), ['NIP'])).toBeNull()
    expect(validate(nipStem + ((nipCheck(nipStem) + 1) % 10), ['NIP'])).toBe('Numer NIP ma błędną cyfrę kontrolną.')
    expect(validate('34000001' + regonCheck('34000001'), ['REGON'])).toBeNull()
    expect(validate('ZZZ' + idCardCheck('ZZZ', '00101') + '00101', ['SERIAL_NUMBER_ID_CARD'])).toBeNull()
    expect(validate('ZZZ' + ((idCardCheck('ZZZ', '00101') + 1) % 10) + '00101', ['SERIAL_NUMBER_ID_CARD'])).toMatch(/cyfrę kontrolną/)
    expect(validate('85-999', ['ZIP_CODE'])).toBeNull()
    expect(validate('85999', ['ZIP_CODE'])).toBe('Kod pocztowy powinien mieć postać 00-000.')
    expect(validate('a@example.com', ['EMAIL'])).toBeNull()
    expect(validate('a@', ['EMAIL'])).not.toBeNull()
    expect(validate('/przykladowska/SkrytkaESP', ['EPUAP'])).toBeNull()
    expect(validate('AE:PL-00000-00000-ABCDE-00', ['ADE'])).toBeNull()
    expect(validate('', ['REQUIRED'])).toBe('To pole jest wymagane.')
    expect(validate('', ['PESEL'])).toBeNull()
  })
})

describe('FP electronic form', () => {
  it('reads the tree with answer keys of direct children; descriptions only as text', () => {
    const m = readForm(fpForm())
    expect(m.tabs.map((t) => t.title)).toEqual(['Dane', 'Szczegóły sprawy', 'Kontakt'])
    expect(m.byRef.get(refKey('Dane', 'adres_zamieszkania', 'kraj'))?.id).toBe('f-kraj')
    expect(m.byId.get('f-info')?.description).toBe('Opłata 17 zł.')
    expect(htmlText('<p>a</p><p>b</p>')).toBe('a\nb')
  })

  it('renders pages, required marks, dictionary chip, and the choice reveals a section with its reason', () => {
    const ef = renderEForm(readForm(fpForm()))
    document.body.append(ef.el)
    const q = (s: string) => ef.el.querySelector<HTMLElement>(s)
    expect(q('#h-eform')?.textContent).toContain('Krok 3 z 6.')
    expect(ef.el.textContent).toContain('Podgląd kontrolny. Formularz produkcyjny wyświetla Generator Formularzy.')
    expect(q('#fp-page-0')?.hidden).toBe(false)
    expect(q('#fp-page-1')?.hidden).toBe(true)
    expect(q('[id="fpw-f-kraj"]')?.textContent).toContain('Słownik: Kraje')
    expect((q('[id="fpf-f-kraj"]') as HTMLInputElement).value).toBe('Polska')
    // Polska: the Polish postal code shows, the foreign street hides
    expect(q('[id="fpw-f-kod"]')?.hidden).toBe(false)
    expect(q('[id="fpw-f-ulica-z"]')?.hidden).toBe(true)
    // "Innej osoby" reveals the section and says why
    expect(q('[id="fpw-s-inna"]')?.hidden).toBe(true)
    const inna = q('[id="fpf-r-kto-o1"]') as HTMLInputElement
    inna.checked = true
    inna.dispatchEvent(new Event('change'))
    expect(q('[id="fpw-s-inna"]')?.hidden).toBe(false)
    expect(q('[id="fpb-s-inna"]')?.textContent).toBe('Sekcja widoczna, ponieważ wybrano: „Innej osoby”.')
    // a changed country flips the address fields
    const kraj = q('[id="fpf-f-kraj"]') as HTMLInputElement
    kraj.value = 'Niemcy'; kraj.dispatchEvent(new Event('input'))
    expect(q('[id="fpw-f-kod"]')?.hidden).toBe(true)
    expect(q('[id="fpw-f-ulica-z"]')?.hidden).toBe(false)
    // an unknown condition keeps the field visible and says so
    expect(q('[id="fpw-f-dziwny"]')?.hidden).toBe(false)
    expect(q('[id="fpw-f-data"]')?.querySelector('.chip-req')?.textContent).toBe('wymagane')
    expect(q('[id="fpf-f-imie"]')?.hasAttribute('readonly')).toBe(true)
    expect(ef.el.querySelector('script')).toBeNull()
  })

  it('pages move with the buttons and focus() jumps to the page of a field', () => {
    const ef = renderEForm(readForm(fpForm()))
    document.body.append(ef.el)
    const next = ef.el.querySelector<HTMLButtonElement>('#fp-next')!
    expect(ef.el.querySelector<HTMLButtonElement>('#fp-prev')!.disabled).toBe(true)
    next.click()
    expect(ef.el.querySelector<HTMLElement>('#fp-page-1')!.hidden).toBe(false)
    expect(ef.el.querySelector('#fp-pageline')!.textContent).toBe('Strona 2 z 3: Szczegóły sprawy')
    ef.focus('f-mail')
    expect(ef.el.querySelector<HTMLElement>('#fp-page-2')!.hidden).toBe(false)
    expect(document.activeElement?.id).toBe('fpf-f-mail')
  })

  it('set() writes a value and a tag; pesel/mlpz lock the field; reset() clears', () => {
    const ef = renderEForm(readForm(fpForm()))
    document.body.append(ef.el)
    ef.set('f-tel', '+48 000 000 101', 'mlpz')
    const tel = ef.el.querySelector<HTMLInputElement>('[id="fpf-f-tel"]')!
    expect(tel.value).toBe('+48 000 000 101')
    expect(tel.readOnly).toBe(true)
    expect(ef.el.querySelector('[id="fpt-f-tel"]')!.textContent).toBe('Z danych zalogowanego użytkownika – tylko do odczytu')
    ef.reset()
    expect(tel.value).toBe('')
    expect(tel.readOnly).toBe(false)
    expect(ef.textOf('f-kraj')).toBe('Polska')
  })
})

describe('FP block in the page', () => {
  it('appears after a conversion between the review and the JSON, keeps #h-done, survives a language change', async () => {
    const res = await interpretResponse(200, new Headers({ 'content-type': 'multipart/mixed; boundary=formularze-abc123' }),
      multipartBody(canonical(fpForm()), canonical(fpSidecar())))
    const app = mountApp(document.getElementById('app')!, { convert: async (): Promise<Outcome> => res, store: null, status: async () => null })
    const input = document.getElementById('file') as HTMLInputElement
    Object.defineProperty(input, 'files', { value: [new File(['x'], 'a.pdf')], configurable: true })
    input.dispatchEvent(new Event('change'))
    await new Promise((r) => setTimeout(r, 0))
    expect(document.getElementById('h-done')).not.toBeNull()
    const fp = document.getElementById('fp')!
    expect(fp).not.toBeNull()
    const json = document.querySelector('section[aria-labelledby="h-json"]')!
    expect(fp.compareDocumentPosition(json) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    const cel = document.querySelector<HTMLTextAreaElement>('[id="fpf-f-cel"]')!
    cel.value = 'do banku'; cel.dispatchEvent(new Event('input'))
    setLang('en'); app.refresh()
    expect(document.querySelector<HTMLTextAreaElement>('[id="fpf-f-cel"]')!.value).toBe('do banku')
  })
})
