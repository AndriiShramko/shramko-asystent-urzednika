// Step 4: test fill with demo data. The "scan" is simulated (FP-A variant c): the button opens the list of the
// invented household; the chosen record goes through the same parser a decoded QR would (only zrodlo DEMO passes).
// One click fills empty fields; the page then lists what was filled from the record and what stays empty.
// BL13 TRY-F: progressive. One step is open at a time and shows only its own action (never a disabled button):
// scan -> choose a person -> fill -> (check and print, opened by fill.ts). A finished step stays as one short line
// with a way back (scan again, change the person, clear and start over).
import { h, clear } from './dom'
import { nameOf, type ENode } from '../lib/fp/form'
import { HOUSEHOLD, parseDemoRecord, type DemoRecord } from '../lib/fp/family'
import { planFill } from '../lib/fp/fill'
import { FP } from '../lib/fp/text'
import type { EForm } from './eform'

const ROLES = ['ojciec, jednoosobowa firma', 'matka', 'córka, 15 lat, pływaczka', 'syn, 8 lat', 'babcia, właścicielka psa']

/** The steps of the citizen block: what is open now. `filled` = the form is filled, the check comes next. */
export type Stage = 'scan' | 'person' | 'fill' | 'filled'

export interface Citizen { el: HTMLElement; record(): DemoRecord | null; stage(): Stage }

/** Fields a person would still have to fill by hand: visible, taking an answer, empty (attachments excluded). */
export function stillEmpty(ef: EForm): ENode[] {
  return ef.inputs().filter((n) => n.type !== 'FILE_UPLOADER' && ef.isVisible(n) && !ef.textOf(n.id).trim())
}

export function renderCitizen(ef: EForm, onCleared?: () => void, onStage?: (s: Stage) => void): Citizen {
  let record: DemoRecord | null = null
  let stage: Stage = 'scan'
  let built = false
  const status = h('p', { id: 'fp-scan-status', role: 'status', class: 'status' })
  const result = h('p', { id: 'fp-fill-result', role: 'status', class: 'status' })
  const lists = h('div', { id: 'fp-fill-lists' })
  const fillBtn = h('button', { type: 'button', class: 'btn btn-main', id: 'fp-fill' }, FP.fillOne)
  const clearBtn = h('button', { type: 'button', class: 'btn', id: 'fp-clear' }, FP.clear)
  const people = h('fieldset', { class: 'fp-people', id: 'fp-people', hidden: true },
    h('legend', {}, FP.pickFromList))
  const scan = h('button', { type: 'button', class: 'btn btn-main', id: 'fp-scan', 'aria-expanded': 'false', 'aria-controls': 'fp-people' }, FP.scanSim)
  const scanAgain = h('button', { type: 'button', class: 'linkish', id: 'fp-scan-again' }, FP.scanAgain)
  const change = h('button', { type: 'button', class: 'linkish', id: 'fp-change' }, FP.changePerson)
  const scanLine = h('p', { class: 'fp-done-line', id: 'fp-done-scan' }, FP.scanDone + ' ', scanAgain)
  const personLine = h('p', { class: 'fp-done-line', id: 'fp-done-person' }, status, ' ', change)
  const scanRow = h('div', { class: 'actions', id: 'fp-scan-row' }, scan)
  const fillRow = h('div', { class: 'actions', id: 'fp-fill-row' }, fillBtn)
  const doneRow = h('div', { class: 'fp-done-line', id: 'fp-done-fill' }, result, h('div', { class: 'actions' }, clearBtn))

  /** Show only what the current step needs; move the focus to its one action. */
  function go(s: Stage, focus = true): void {
    stage = s
    scanRow.hidden = s !== 'scan'
    scanLine.hidden = s === 'scan'
    people.hidden = s !== 'person'
    scan.setAttribute('aria-expanded', String(s === 'person'))
    personLine.hidden = s === 'scan' ? !status.textContent : s === 'person' ? !status.classList.contains('bad') : false
    change.hidden = s === 'scan' || s === 'person'
    scanAgain.hidden = s === 'person'
    fillRow.hidden = s !== 'fill'
    doneRow.hidden = s !== 'filled'
    lists.hidden = s !== 'filled'
    if (focus) {
      const target = s === 'scan' ? scan : s === 'person' ? people.querySelector<HTMLButtonElement>('button') : s === 'fill' ? fillBtn : null
      target?.focus()
    }
    if (built) onStage?.(s)
  }

  scan.addEventListener('click', () => go('person'))
  scanAgain.addEventListener('click', () => go('person'))
  change.addEventListener('click', () => go('person'))

  HOUSEHOLD.forEach((p, i) => {
    const label = `${p.PESEL.name} ${p.PESEL.surname} (${ROLES[i] ?? ''}${p.wrongOnPurpose ? '; ' + FP.wrongOnPurpose : ''})`
    const b = h('button', { type: 'button', class: 'btn fp-person', 'data-person': i }, label)
    b.addEventListener('click', () => load(JSON.stringify(p)))
    people.append(b)
  })

  /** What a decoded QR hands over: text. Only the demo schema is accepted. */
  function load(text: string): void {
    const r = parseDemoRecord(text)
    if (!r) { record = null; status.textContent = FP.refused; status.className = 'status bad'; go('person', false); return }
    record = r
    status.className = 'status'
    status.textContent = FP.loaded(r.PESEL.name ?? r.MLPZ.name ?? '', r.PESEL.surname ?? r.MLPZ.surname ?? '')
    go('fill')
  }

  function goButton(n: ENode): HTMLElement {
    const b = h('button', { type: 'button', class: 'linkish', 'data-go': n.id }, nameOf(n))
    b.addEventListener('click', () => ef.focus(n.id))
    return b
  }

  fillBtn.addEventListener('click', () => {
    if (!record) return
    // a filled choice can reveal a field (the chip number after "mikroprocesor"): plan again until nothing new
    const plan: ReturnType<typeof planFill> = []
    for (let pass = 0; pass < 4; pass++) {
      const more = planFill(ef.model, record, (id) => !ef.textOf(id).trim(), (n) => ef.isVisible(n))
      if (!more.length) break
      for (const it of more) ef.set(it.id, it.value, it.tag)
      plan.push(...more)
    }
    const k = plan.filter((p) => p.tag !== 'proposal').length
    const m = plan.length - k
    const empty = stillEmpty(ef)
    result.textContent = FP.filled(plan.length, k, m, empty.length)
    clear(lists)
    const filledNodes = plan.map((p) => ef.model.byId.get(p.id)).filter((n): n is ENode => !!n)
    lists.append(
      h('details', { id: 'fp-filled-list' }, h('summary', {}, `${FP.filledList} (${filledNodes.length})`),
        h('ul', { class: 'plain' }, ...filledNodes.map((n) => h('li', {}, goButton(n), ' – ', h('span', { class: 'muted' }, FP.tag[ef.tagOf(n.id) ?? 'proposal']))))),
      h('details', { open: empty.length > 0, id: 'fp-empty-list' }, h('summary', {}, `${FP.emptyList} (${empty.length})`),
        h('ul', { class: 'plain' }, ...empty.map((n) => h('li', {}, goButton(n))))))
    go('filled', false)
    showFilled(plan.map((p) => p.id))
  })

  /** The filled fields light up for a few seconds; the e-form panel scrolls (inside itself) to the first of them,
   * so the page stays where the next button is. */
  function showFilled(ids: string[]): void {
    const boxes = ids.map((id) => ef.el.querySelector<HTMLElement>(`[id^="fpf-${id}"]`)?.closest<HTMLElement>('.fp-field'))
      .filter((b): b is HTMLElement => !!b)
    for (const b of boxes) b.classList.add('fp-just-filled')
    setTimeout(() => { for (const b of boxes) b.classList.remove('fp-just-filled') }, 4000)
    const first = boxes[0]
    if (first && ef.el.scrollHeight > ef.el.clientHeight) {
      ef.el.scrollTop += first.getBoundingClientRect().top - ef.el.getBoundingClientRect().top - 80
    }
  }

  clearBtn.addEventListener('click', () => {
    ef.reset()
    record = null
    result.textContent = ''
    clear(lists)
    status.className = 'status'
    status.textContent = FP.cleared
    onCleared?.()
    go('scan')
  })

  const el = h('section', { id: 'fp-citizen', class: 'fp-step', 'aria-labelledby': 'h-citizen' },
    h('h2', { id: 'h-citizen' }, FP.step(4), ' ', FP.fillHeading),
    h('p', { class: 'muted' }, FP.qrStory),
    scanRow,
    scanLine,
    people,
    personLine,
    fillRow,
    doneRow,
    lists)
  go('scan', false)
  built = true
  return { el, record: () => record, stage: () => stage }
}
