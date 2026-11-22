// FP step 4: the invented household, identifiers completed at run time, the one-click fill. Synthetic data only;
// no identifier with a valid check digit is written here: every one is computed from a stem.
import { beforeEach, describe, expect, it } from 'vitest'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { HOUSEHOLD, accountOf, idCardOf, nipOf, parseDemoRecord, peselOf, regonOf } from '../src/lib/fp/family'
import { planFill } from '../src/lib/fp/fill'
import { readForm } from '../src/lib/fp/form'
import { mod97, nipCheck, peselCheck, validate } from '../src/lib/fp/validators'
import { renderEForm } from '../src/ui/eform'
import { renderCitizen } from '../src/ui/citizen'
import { mountFill } from '../src/ui/fill'
import { interpretResponse, type Converted } from '../src/lib/api'
import { canonical, multipartBody } from './helpers'
import { fpForm, fpSidecar } from './fp-fixture'

beforeEach(() => { document.body.innerHTML = '' })
const tomasz = HOUSEHOLD[0]
const kacper = HOUSEHOLD.find((p) => p.wrongOnPurpose)!

describe('FP household', () => {
  it('completes identifiers at run time; all pass their checks except the one wrong on purpose', () => {
    for (const p of HOUSEHOLD) {
      const pesel = peselOf(p)
      expect(pesel).toMatch(/^\d{11}$/)
      expect(validate(pesel, ['PESEL']) === null).toBe(!p.wrongOnPurpose)
    }
    expect(validate(peselOf(kacper), ['PESEL'])).toBe('Numer PESEL ma błędną cyfrę kontrolną.')
    expect(validate(nipOf(tomasz), ['NIP'])).toBeNull()
    expect(validate(regonOf(tomasz), ['REGON'])).toBeNull()
    expect(validate(idCardOf(tomasz), ['SERIAL_NUMBER_ID_CARD'])).toBeNull()
    const nrb = accountOf(tomasz).replace(/\s/g, '')
    expect(nrb).toMatch(/^\d{26}$/)
    expect(mod97(nrb.slice(2) + '2521' + nrb.slice(0, 2))).toBe(1)
  })

  it('accepts only the demo schema with zrodlo DEMO', () => {
    expect(parseDemoRecord(JSON.stringify(tomasz))?.PESEL.name).toBe('Tomasz')
    expect(parseDemoRecord(JSON.stringify({ ...tomasz, zrodlo: 'PESEL' }))).toBeNull()
    expect(parseDemoRecord('not json')).toBeNull()
    expect(parseDemoRecord('{"schemat":"x"}')).toBeNull()
  })

  it('no source file of the page holds a full identifier with a valid check digit', () => {
    const files: string[] = []
    const walk = (d: string) => { for (const f of readdirSync(d)) { const p = join(d, f); if (statSync(p).isDirectory()) walk(p); else if (/\.(ts|css|html)$/.test(f)) files.push(p) } }
    walk(join(__dirname, '..', 'src'))
    walk(__dirname)
    let found = 0
    for (const f of files) {
      const text = readFileSync(f, 'utf8')
      for (const m of text.matchAll(/(?<!\d)\d{11}(?!\d)/g)) if (peselCheck(m[0]) === Number(m[0][10])) found++
      for (const m of text.matchAll(/(?<!\d)\d{10}(?!\d)/g)) { const c = nipCheck(m[0]); if (c !== 10 && c === Number(m[0][9])) found++ }
    }
    expect(found).toBe(0)
  })
})

describe('FP one-click fill', () => {
  it('partner keys first and locked, proposals checked, other person untouched, nothing overwritten', () => {
    const model = readForm(fpForm())
    const filled = new Set(['f-cel'])
    const plan = planFill(model, tomasz, (id) => !filled.has(id))
    const by = Object.fromEntries(plan.map((p) => [p.id, p]))
    expect(by['f-imie']).toEqual({ id: 'f-imie', value: 'Tomasz', tag: 'pesel' })
    expect(by['f-pesel'].value).toBe(peselOf(tomasz))
    expect(by['f-tel']).toEqual({ id: 'f-tel', value: '+48 000 000 101', tag: 'mlpz' })
    expect(by['f-kod'].tag).toBe('mlpz')
    expect(by['f-nip']).toEqual({ id: 'f-nip', value: nipOf(tomasz), tag: 'proposal' })
    expect(by['f-data']).toEqual({ id: 'f-data', value: '1984-03-15', tag: 'proposal' })
    expect(by['f-imie-inna']).toBeUndefined()
    expect(by['f-cel']).toBeUndefined()
    expect(by['f-kraj']).toBeUndefined()
  })

  it('the panel: banner, simulated scan list, loaded line, result sentence, filled and empty lists, clear', () => {
    const ef = renderEForm(readForm(fpForm()))
    const c = renderCitizen(ef)
    document.body.append(ef.el, c.el)
    const q = <T extends HTMLElement>(s: string) => document.querySelector<T>(s)!
    expect(q('#h-citizen').textContent).toBe('Krok 4 z 6. Próbne wypełnienie danymi demonstracyjnymi')
    expect(q<HTMLButtonElement>('#fp-fill').disabled).toBe(true)
    q('#fp-scan').click()
    expect(q('#fp-people').hidden).toBe(false)
    expect(q('#fp-people').textContent).toContain('celowo błędna cyfra kontrolna PESEL')
    q('[data-person="0"]').click()
    expect(q('#fp-scan-status').textContent).toBe('Wczytano dane demonstracyjne: Tomasz Przykładowski.')
    q('#fp-fill').click()
    expect(q('#fp-fill-result').textContent).toMatch(/^Wypełniono \d+ pól: \d+ z rejestru \(tylko do odczytu\), \d+ jako propozycja do sprawdzenia\. Do uzupełnienia ręcznie: \d+\.$/)
    expect(q('[id="fpt-f-imie"]').textContent).toBe('Z rejestru PESEL – tylko do odczytu')
    expect(q('[id="fpt-f-nip"]').textContent).toBe('Propozycja z danych demonstracyjnych – sprawdź')
    expect(q<HTMLInputElement>('[id="fpf-f-pesel"]').readOnly).toBe(true)
    expect(q('#fp-empty-list').textContent).toContain('Cel wydania')
    q<HTMLButtonElement>('#fp-empty-list [data-go="f-cel"]').click()
    expect(document.activeElement?.id).toBe('fpf-f-cel')
    q('#fp-clear').click()
    expect(q('#fp-scan-status').textContent).toBe('Dane usunięto z tej karty przeglądarki.')
    expect(q<HTMLInputElement>('[id="fpf-f-imie"]').value).toBe('')
  })

  it('the block carries the permanent demo banner', async () => {
    const res = await interpretResponse(200, new Headers({ 'content-type': 'multipart/mixed; boundary=formularze-abc123' }),
      multipartBody(canonical(fpForm()), canonical(fpSidecar())))
    const b = mountFill(res as Converted)
    expect(b.el.querySelector('#fp-banner')?.textContent).toBe('Dane demonstracyjne. Osoby są fikcyjne, wymyślone na potrzeby pokazu. Nie wpisuj tu prawdziwych danych.')
  })
})
