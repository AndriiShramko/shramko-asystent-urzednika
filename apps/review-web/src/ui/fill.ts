// The fill-and-print block under the conversion result: the electronic form (step 3) and the steps built on it.
// Built once per conversion and kept across a change of language (its texts are Polish by design), so a typed
// value is never lost by a refresh. The demo-data banner stays on top of the block, always visible.
import { h } from './dom'
import { readForm } from '../lib/fp/form'
import { renderEForm, type EForm } from './eform'
import { renderCitizen, type Citizen } from './citizen'
import { renderCheck, type Check } from './check'
import { FP } from '../lib/fp/text'
import type { Converted } from '../lib/api'

export interface FillBlock { el: HTMLElement; eform: EForm; citizen: Citizen; check: Check }

export function mountFill(res: Converted): FillBlock {
  const model = readForm(res.form)
  const eform = renderEForm(model)
  const check = renderCheck(eform)
  const citizen = renderCitizen(eform, () => check.reset())
  const banner = h('p', { id: 'fp-banner', class: 'fp-banner', role: 'note' }, FP.banner)
  const el = h('div', { id: 'fp', class: 'fp', lang: 'pl' }, banner, eform.el, citizen.el, check.el)
  return { el, eform, citizen, check }
}
