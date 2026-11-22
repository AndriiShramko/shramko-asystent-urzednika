// FP step 5: the check before print. Synthetic data; identifiers computed from stems.
import { beforeEach, describe, expect, it } from 'vitest'
import { HOUSEHOLD } from '../src/lib/fp/family'
import { readForm } from '../src/lib/fp/form'
import { renderEForm } from '../src/ui/eform'
import { renderCitizen } from '../src/ui/citizen'
import { checkForm, renderCheck } from '../src/ui/check'
import { fpForm } from './fp-fixture'

beforeEach(() => { document.body.innerHTML = '' })

function setup() {
  const ef = renderEForm(readForm(fpForm()))
  const check = renderCheck(ef)
  const c = renderCitizen(ef, () => check.reset())
  document.body.append(ef.el, c.el, check.el)
  return { ef, check }
}
const q = <T extends HTMLElement>(s: string) => document.querySelector<T>(s)!

describe('FP check', () => {
  it('empty form: required fields and the required consent are missing, with links', () => {
    const { ef } = setup()
    const r = checkForm(ef)
    expect(r.ok).toBe(false)
    expect(r.missing.map((n) => n.id).sort()).toEqual(['f-cel', 'f-data', 'f-zgoda'])
    q('#fp-check').click()
    expect(q('#fp-check-result').textContent).toContain('Brakuje 3 wymaganych pól: ')
    expect(q('[id="fpe-f-cel"]').textContent).toBe('To pole jest wymagane.')
    expect(q('[id="fpf-f-cel"]').getAttribute('aria-invalid')).toBe('true')
    q<HTMLButtonElement>('#fp-check-result [data-go="f-cel"]').click()
    expect(document.activeElement?.id).toBe('fpf-f-cel')
  })

  it('the person with the wrong digit gets the PESEL message; a good person and the required fields give ready', () => {
    const { ef } = setup()
    const wrong = HOUSEHOLD.findIndex((p) => p.wrongOnPurpose)
    q('#fp-scan').click(); q(`[data-person="${wrong}"]`).click(); q('#fp-fill').click()
    q('#fp-check').click()
    expect(q('#fp-check-result').textContent).toContain('Numer PESEL ma błędną cyfrę kontrolną.')
    q('#fp-clear').click()
    expect(q('#fp-check-result').textContent).toBe('')
    q('#fp-scan').click(); q('[data-person="0"]').click(); q('#fp-fill').click()
    ef.set('f-cel', 'do banku')
    const consent = q<HTMLInputElement>('[id="fpf-f-zgoda-c0"]'); consent.checked = true; consent.dispatchEvent(new Event('change'))
    q('#fp-check').click()
    expect(q('#fp-check-result').getAttribute('data-ok')).toBe('true')
    expect(q('#fp-check-result').textContent).toContain('Wszystkie wymagane pola są wypełnione, a numery przeszły kontrolę.')
  })

  it('a hidden section is not asked; a bad postal code gives the design sentence', () => {
    const { ef } = setup()
    ef.set('f-kod', '85999')
    q('#fp-check').click()
    expect(q('#fp-check-result').textContent).toContain('Kod pocztowy powinien mieć postać 00-000.')
    ef.set('f-kraj', 'Niemcy')
    expect(checkForm(ef).failures.length).toBe(0)
  })
})
