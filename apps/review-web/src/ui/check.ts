// Step 5: the check before print. Only visible fields count (a hidden section is not asked). Each failure and
// each missing required field links to its field; the inline message sits under the field (aria-invalid).
import { h, clear } from './dom'
import { nameOf, type ENode } from '../lib/fp/form'
import { REQUIRED_MSG, validate } from '../lib/fp/validators'
import { FP } from '../lib/fp/text'
import type { EForm } from './eform'

export interface CheckResult {
  failures: { node: ENode; msg: string }[]
  missing: ENode[]
  filled: number
  total: number
  ok: boolean
}

export function checkForm(ef: EForm): CheckResult {
  const failures: CheckResult['failures'] = []
  const missing: ENode[] = []
  let filled = 0
  let total = 0
  for (const n of ef.inputs()) {
    if (n.type === 'FILE_UPLOADER') continue
    if (!ef.isVisible(n)) continue
    total++
    const text = ef.textOf(n.id)
    if (text.trim()) filled++
    if (n.type === 'CONSENT_SECTION') {
      const v = ef.get(n.id)
      const chosen = new Set(Array.isArray(v) ? v : [])
      if (n.consents.some((c, i) => c.required && !chosen.has(String(i)))) missing.push(n)
      continue
    }
    const msg = validate(text, n.validation)
    if (msg === REQUIRED_MSG) missing.push(n)
    else if (msg) failures.push({ node: n, msg })
  }
  return { failures, missing, filled, total, ok: !failures.length && !missing.length }
}

export interface Check { el: HTMLElement; run(): CheckResult; reset(): void }

export function renderCheck(ef: EForm, extra?: () => HTMLElement | null, onRun?: (r: CheckResult) => void): Check {
  const out = h('div', { id: 'fp-check-result', role: 'status' })
  const btn = h('button', { type: 'button', class: 'btn btn-main', id: 'fp-check' }, FP.checkButton)

  const go = (n: ENode): HTMLElement => {
    const b = h('button', { type: 'button', class: 'linkish', 'data-go': n.id }, nameOf(n))
    b.addEventListener('click', () => ef.focus(n.id))
    return b
  }

  function run(): CheckResult {
    const r = checkForm(ef)
    for (const n of ef.inputs()) ef.showError(n.id, null)
    for (const f of r.failures) ef.showError(f.node.id, f.msg)
    for (const n of r.missing) ef.showError(n.id, REQUIRED_MSG)
    clear(out)
    out.className = r.ok ? 'fp-ready' : 'fp-notready'
    out.setAttribute('data-ok', String(r.ok))
    out.append(h('p', {}, `Wypełnione pola: ${r.filled} z ${r.total}.`))
    if (r.failures.length) {
      out.append(h('ul', { class: 'plain fp-failures' }, ...r.failures.map((f) => h('li', {}, go(f.node), ': ', h('span', { class: 'bad' }, f.msg)))))
    }
    if (r.missing.length) {
      out.append(h('p', { class: 'bad' }, FP.missing(r.missing.length, r.missing.map(nameOf).join(', '))),
        h('ul', { class: 'plain fp-missing' }, ...r.missing.map((n) => h('li', {}, go(n)))))
    }
    if (r.ok) out.append(h('p', { class: 'fp-ok' }, FP.allGood))
    const more = extra?.()
    if (more) out.append(more)
    return r
  }
  btn.addEventListener('click', () => { const r = run(); onRun?.(r) })

  const el = h('section', { id: 'fp-check-step', class: 'fp-step', 'aria-labelledby': 'h-check' },
    h('h2', { id: 'h-check' }, FP.step(5), ' ', FP.checkHeading),
    h('div', { class: 'actions' }, btn),
    out)
  return {
    el,
    run,
    reset() { clear(out); out.className = ''; out.removeAttribute('data-ok'); for (const n of ef.inputs()) ef.showError(n.id, null) }
  }
}
