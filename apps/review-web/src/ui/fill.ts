// The fill-and-print block under the conversion result: the electronic form (step 3) and the steps built on it.
// Built once per conversion and kept across a change of language (its texts are Polish by design), so a typed
// value is never lost by a refresh.
import { h } from './dom'
import { readForm } from '../lib/fp/form'
import { renderEForm, type EForm } from './eform'
import type { Converted } from '../lib/api'

export interface FillBlock { el: HTMLElement; eform: EForm }

export function mountFill(res: Converted): FillBlock {
  const model = readForm(res.form)
  const eform = renderEForm(model)
  const el = h('div', { id: 'fp', class: 'fp', lang: 'pl' }, eform.el)
  return { el, eform }
}
