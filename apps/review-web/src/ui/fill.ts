// The fill-and-print block under the conversion result: where on the paper (step 2 addition), the electronic form
// (step 3) and the steps built on it. Built once per conversion and kept across a change of language (its texts
// are Polish by design), so a typed value is never lost by a refresh. The demo-data banner stays on top.
import { h } from './dom'
import { readForm } from '../lib/fp/form'
import { renderEForm, type EForm } from './eform'
import { renderCitizen, type Citizen } from './citizen'
import { renderCheck, type Check } from './check'
import { renderWhere, type Where } from './where'
import { buildSheets, renderPrint, type PrintStep } from './print'
import { attachAddressHints, type AddressHints } from './address'
import type { TerytSource } from '../lib/fp/teryt'
import { FP } from '../lib/fp/text'
import type { Converted } from '../lib/api'

export interface FillBlock { el: HTMLElement; eform: EForm; citizen: Citizen; check: Check; where: Where; print: PrintStep; address: AddressHints }

export function mountFill(res: Converted, preview: Promise<unknown> = Promise.resolve(null), teryt?: TerytSource): FillBlock {
  const model = readForm(res.form)
  const eform = renderEForm(model)
  const where = renderWhere(eform, res.sidecar, preview)
  // the check also says how many filled values have no place on the blank (they go to the extra page)
  const check = renderCheck(eform, () => {
    const s = buildSheets(eform, where, citizen.record())
    const box = h('div', { id: 'fp-check-more' })
    if (s && s.extra.length) box.append(h('p', { id: 'fp-check-noplace' }, FP.noPlace(s.extra.length)))
    // a postal code that is not among the codes of its locality: a remark, not an error (the open set may lack a code)
    void address.postalRemarks().then((list) => {
      if (!list.length) return
      box.append(h('ul', { class: 'plain fp-address-remarks', id: 'fp-check-address' }, ...list.map((r) => {
        const b = h('button', { type: 'button', class: 'linkish', 'data-go': r.node.id }, r.node.title || r.node.techName)
        b.addEventListener('click', () => eform.focus(r.node.id))
        return h('li', {}, b, ': ', h('span', { class: 'fp-warn' }, r.msg))
      })))
    })
    return box
  }, (r) => {
    // the print opens after the check; with nothing missing the focus goes to its first action, else it stays here
    print.el.hidden = false
    if (r.ok) [...print.el.querySelectorAll<HTMLButtonElement>("button")].find((b) => !b.hidden)?.focus()
    else check.el.querySelector<HTMLElement>("#fp-check-result")?.focus() // what is missing comes into sight
  })
  // BL13 TRY-F: the check opens after the fill, the print after the check; going back closes what follows
  const citizen = renderCitizen(eform, () => check.reset(), (s) => {
    check.el.hidden = s !== 'filled'
    print.el.hidden = true
    if (s !== 'filled') check.reset()
    else check.el.querySelector<HTMLButtonElement>('#fp-check')?.focus()
  })
  const print = renderPrint(eform, where, () => citizen.record())
  const address = attachAddressHints(eform, teryt)
  const banner = h('p', { id: 'fp-banner', class: 'fp-banner', role: 'note' }, FP.banner)
  check.el.hidden = true
  print.el.hidden = true
  const el = h('div', { id: 'fp', class: 'fp', lang: 'pl' }, banner, where.el, eform.el, citizen.el, check.el, print.el)
  return { el, eform, citizen, check, where, print, address }
}
