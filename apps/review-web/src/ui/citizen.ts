// Step 4: test fill with demo data. The "scan" is simulated (FP-A variant c): the button opens the list of the
// invented household; the chosen record goes through the same parser a decoded QR would (only zrodlo DEMO passes).
// One click fills empty fields; the page then lists what was filled from the record and what stays empty.
import { h, clear } from './dom'
import { nameOf, type ENode } from '../lib/fp/form'
import { HOUSEHOLD, parseDemoRecord, type DemoRecord } from '../lib/fp/family'
import { planFill } from '../lib/fp/fill'
import { FP } from '../lib/fp/text'
import type { EForm } from './eform'

const ROLES = ['ojciec, jednoosobowa firma', 'matka', 'córka, 15 lat, pływaczka', 'syn, 8 lat', 'babcia, właścicielka psa']

export interface Citizen { el: HTMLElement; record(): DemoRecord | null }

/** Fields a person would still have to fill by hand: visible, taking an answer, empty (attachments excluded). */
export function stillEmpty(ef: EForm): ENode[] {
  return ef.inputs().filter((n) => n.type !== 'FILE_UPLOADER' && ef.isVisible(n) && !ef.textOf(n.id).trim())
}

export function renderCitizen(ef: EForm, onCleared?: () => void): Citizen {
  let record: DemoRecord | null = null
  const status = h('p', { id: 'fp-scan-status', role: 'status', class: 'status' })
  const result = h('p', { id: 'fp-fill-result', role: 'status', class: 'status' })
  const lists = h('div', { id: 'fp-fill-lists' })
  const fillBtn = h('button', { type: 'button', class: 'btn btn-main', id: 'fp-fill', disabled: true }, FP.fillOne)
  const clearBtn = h('button', { type: 'button', class: 'btn', id: 'fp-clear' }, FP.clear)
  const people = h('fieldset', { class: 'fp-people', id: 'fp-people', hidden: true },
    h('legend', {}, FP.pickFromList))
  const scan = h('button', { type: 'button', class: 'btn', id: 'fp-scan', 'aria-expanded': 'false', 'aria-controls': 'fp-people' }, FP.scanSim)

  scan.addEventListener('click', () => {
    people.hidden = !people.hidden
    scan.setAttribute('aria-expanded', String(!people.hidden))
    if (!people.hidden) people.querySelector<HTMLButtonElement>('button')?.focus()
  })

  HOUSEHOLD.forEach((p, i) => {
    const label = `${p.PESEL.name} ${p.PESEL.surname} (${ROLES[i] ?? ''}${p.wrongOnPurpose ? '; ' + FP.wrongOnPurpose : ''})`
    const b = h('button', { type: 'button', class: 'btn fp-person', 'data-person': i }, label)
    b.addEventListener('click', () => load(JSON.stringify(p)))
    people.append(b)
  })

  /** What a decoded QR hands over: text. Only the demo schema is accepted. */
  function load(text: string): void {
    const r = parseDemoRecord(text)
    if (!r) { record = null; status.textContent = FP.refused; status.className = 'status bad'; fillBtn.disabled = true; return }
    record = r
    status.className = 'status'
    status.textContent = FP.loaded(r.PESEL.name ?? r.MLPZ.name ?? '', r.PESEL.surname ?? r.MLPZ.surname ?? '')
    fillBtn.disabled = false
    people.hidden = true
    scan.setAttribute('aria-expanded', 'false')
    fillBtn.focus()
  }

  function goButton(n: ENode): HTMLElement {
    const b = h('button', { type: 'button', class: 'linkish', 'data-go': n.id }, nameOf(n))
    b.addEventListener('click', () => ef.focus(n.id))
    return b
  }

  fillBtn.addEventListener('click', () => {
    if (!record) return
    const plan = planFill(ef.model, record, (id) => !ef.textOf(id).trim())
    for (const it of plan) ef.set(it.id, it.value, it.tag)
    const k = plan.filter((p) => p.tag !== 'proposal').length
    const m = plan.length - k
    const empty = stillEmpty(ef)
    result.textContent = FP.filled(plan.length, k, m, empty.length)
    clear(lists)
    const filledNodes = plan.map((p) => ef.model.byId.get(p.id)).filter((n): n is ENode => !!n)
    lists.append(
      h('details', { open: true, id: 'fp-filled-list' }, h('summary', {}, `${FP.filledList} (${filledNodes.length})`),
        h('ul', { class: 'plain' }, ...filledNodes.map((n) => h('li', {}, goButton(n), ' – ', h('span', { class: 'muted' }, FP.tag[ef.tagOf(n.id) ?? 'proposal']))))),
      h('details', { open: true, id: 'fp-empty-list' }, h('summary', {}, `${FP.emptyList} (${empty.length})`),
        h('ul', { class: 'plain' }, ...empty.map((n) => h('li', {}, goButton(n))))))
  })

  clearBtn.addEventListener('click', () => {
    ef.reset()
    record = null
    fillBtn.disabled = true
    result.textContent = ''
    clear(lists)
    status.className = 'status'
    status.textContent = FP.cleared
    onCleared?.()
  })

  const el = h('section', { id: 'fp-citizen', class: 'fp-step', 'aria-labelledby': 'h-citizen' },
    h('h2', { id: 'h-citizen' }, FP.step(4), ' ', FP.fillHeading),
    h('p', { class: 'muted' }, FP.qrStory),
    h('div', { class: 'actions' }, scan),
    people,
    status,
    h('div', { class: 'actions' }, fillBtn, clearBtn),
    result,
    lists)
  return { el, record: () => record }
}
