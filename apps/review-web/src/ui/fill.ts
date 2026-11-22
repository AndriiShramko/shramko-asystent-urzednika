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
import { FP } from '../lib/fp/text'
import type { Converted } from '../lib/api'

export interface FillBlock { el: HTMLElement; eform: EForm; citizen: Citizen; check: Check; where: Where; print: PrintStep }

export function mountFill(res: Converted, preview: Promise<unknown> = Promise.resolve(null)): FillBlock {
  const model = readForm(res.form)
  const eform = renderEForm(model)
  const where = renderWhere(eform, res.sidecar, preview)
  // the check also says how many filled values have no place on the blank (they go to the extra page)
  const check = renderCheck(eform, () => {
    const s = buildSheets(eform, where, citizen.record())
    return s && s.extra.length ? h('p', { id: 'fp-check-noplace' }, FP.noPlace(s.extra.length)) : null
  })
  const citizen = renderCitizen(eform, () => check.reset())
  const print = renderPrint(eform, where, () => citizen.record())
  const banner = h('p', { id: 'fp-banner', class: 'fp-banner', role: 'note' }, FP.banner)
  const el = h('div', { id: 'fp', class: 'fp', lang: 'pl' }, banner, where.el, eform.el, citizen.el, check.el, print.el)
  return { el, eform, citizen, check, where, print }
}
