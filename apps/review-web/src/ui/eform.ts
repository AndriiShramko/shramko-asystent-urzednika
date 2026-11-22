// Step 3: the returned JSON as a fillable electronic form. Tabs are pages (Poprzednia / Następna strona), sections
// and fields follow the JSON's order; types, required marks, choice groups, dictionaries and SHOW conditions act as
// the JSON declares them. Every text from the form is set as text (descriptions are read through DOMParser).
import { h } from './dom'
import { INPUT_TYPES, CONTAINER_TYPES, nameOf, type ENode, type FormModel } from '../lib/fp/form'
import { evaluate, parseCondition, reasons, type Cond } from '../lib/fp/conditions'
import { dictionaryEntries } from '../lib/fp/dictionaries'
import { FP } from '../lib/fp/text'

export type Val = string | string[]
/** Where a value came from: the PESEL register block, the logged-in user block, or a proposal from demo data. */
export type Tag = 'pesel' | 'mlpz' | 'proposal'

export interface EForm {
  el: HTMLElement
  model: FormModel
  get(id: string): Val | undefined
  /** Set a value as if typed; with a tag the field shows where it came from (pesel/mlpz also lock it). */
  set(id: string, v: Val, tag?: Tag): void
  tagOf(id: string): Tag | null
  /** The value as one line of text (choices joined by ", "). */
  textOf(id: string): string
  isVisible(n: ENode): boolean
  /** Fields that take an answer, in document order. */
  inputs(): ENode[]
  focus(id: string): void
  showError(id: string, msg: string | null): void
  /** Back to the state right after conversion: values, tags, errors. */
  reset(): void
  onChange(fn: () => void): void
  /** Show every page at once (for the print of the electronic form) or back to one page. */
  showAll(on: boolean): void
}

const PL = { lang: 'pl' }
const ctlId = (id: string): string => 'fpf-' + id
const wrapId = (id: string): string => 'fpw-' + id

function initialOf(n: ENode): Val | undefined {
  const d = n.defaultValue
  if (n.defaultValueType === 'EXTERNAL_SYSTEM') return undefined
  if (n.type === 'CHECKBOX') return Array.isArray(d) ? d.filter((x): x is string => typeof x === 'string') : undefined
  if (Array.isArray(d)) return typeof d[0] === 'string' ? d[0] : undefined
  return typeof d === 'string' && d ? d : undefined
}

export function renderEForm(model: FormModel): EForm {
  const values = new Map<string, Val>()
  const tags = new Map<string, Tag>()
  const listeners: (() => void)[] = []
  const conds = new Map<string, (Cond | null)[]>()
  for (const n of model.all) if (n.shows.length) conds.set(n.id, n.shows.map(parseCondition))
  let page = 0
  let all = false

  const look = (key: string): string[] => {
    const n = model.byRef.get(key)
    if (!n) return []
    const v = values.has(n.id) ? values.get(n.id) : initialOf(n)
    if (v === undefined) return []
    return Array.isArray(v) ? v : v ? [v] : []
  }
  const ownVisible = (n: ENode): boolean => (conds.get(n.id) ?? []).every((c) => c === null || evaluate(c, look))
  const isVisible = (n: ENode): boolean => {
    for (let p: ENode | null = n; p; p = p.parent) if (!ownVisible(p)) return false
    return true
  }

  const root = h('section', { id: 'fp-eform', class: 'fp-step', 'aria-labelledby': 'h-eform' })
  const pageLine = h('p', { class: 'fp-pageline', id: 'fp-pageline', 'aria-live': 'polite' })
  const prev = h('button', { type: 'button', class: 'btn', id: 'fp-prev' }, FP.prevPage)
  const next = h('button', { type: 'button', class: 'btn', id: 'fp-next' }, FP.nextPage)
  const pages: HTMLElement[] = []

  const emit = (): void => { update(); for (const fn of listeners) fn() }

  function control(n: ENode): { box: HTMLElement; label: HTMLElement | null } {
    const id = ctlId(n.id)
    const dis = n.readOnly ? true : undefined
    const describedBy = `fpe-${n.id} fpt-${n.id}`
    switch (n.type) {
      case 'TEXTAREA': {
        const el = h('textarea', { id, rows: 3, readonly: dis, 'aria-describedby': describedBy, ...PL })
        el.addEventListener('input', () => { values.set(n.id, el.value); emit() })
        return { box: el, label: h('label', { for: id, ...PL }, nameOf(n)) }
      }
      case 'RADIO':
      case 'CHECKBOX': {
        if (n.type === 'CHECKBOX' && !n.options.length) {
          const el = h('input', { type: 'checkbox', id, disabled: dis, 'aria-describedby': describedBy })
          el.addEventListener('change', () => { values.set(n.id, el.checked ? ['true'] : []); emit() })
          return { box: h('div', { class: 'fp-choice' }, el, h('label', { for: id, ...PL }, ' ' + nameOf(n))), label: null }
        }
        const fs = h('fieldset', { id, class: 'fp-group', 'aria-describedby': describedBy },
          h('legend', PL, nameOf(n), n.validation.includes('REQUIRED') ? h('span', { class: 'fp-req', 'aria-hidden': 'true' }, ' *') : null))
        n.options.forEach((o, i) => {
          const oid = `${id}-o${i}`
          const inp = h('input', { type: n.type === 'RADIO' ? 'radio' : 'checkbox', id: oid, name: id, value: o, disabled: dis })
          inp.addEventListener('change', () => {
            if (n.type === 'RADIO') values.set(n.id, o)
            else values.set(n.id, [...fs.querySelectorAll<HTMLInputElement>('input:checked')].map((x) => x.value))
            emit()
          })
          fs.append(h('div', { class: 'fp-choice' }, inp, h('label', { for: oid, ...PL }, ' ' + o)))
        })
        return { box: fs, label: null }
      }
      case 'SELECT': {
        if (n.dictionaryName || !n.options.length) {
          const listId = `fpd-${n.id}`
          const el = h('input', { type: 'text', id, list: listId, readonly: dis, autocomplete: 'off', 'aria-describedby': describedBy, ...PL })
          el.addEventListener('input', () => { values.set(n.id, el.value); emit() })
          const dl = h('datalist', { id: listId }, ...dictionaryEntries(n.dictionaryName ?? '').map((x) => h('option', { value: x })))
          return { box: h('div', {}, el, dl), label: h('label', { for: id, ...PL }, nameOf(n)) }
        }
        const el = h('select', { id, disabled: dis, 'aria-describedby': describedBy, ...PL },
          h('option', { value: '' }, FP.choose), ...n.options.map((o) => h('option', { value: o }, o)))
        el.addEventListener('change', () => { values.set(n.id, el.value); emit() })
        return { box: el, label: h('label', { for: id, ...PL }, nameOf(n)) }
      }
      case 'CONSENT_SECTION': {
        const fs = h('fieldset', { id, class: 'fp-group', 'aria-describedby': describedBy },
          h('legend', {}, n.title ? h('span', PL, n.title) : FP.consents))
        n.consents.forEach((c, i) => {
          const oid = `${id}-c${i}`
          const inp = h('input', { type: 'checkbox', id: oid, value: String(i) })
          inp.addEventListener('change', () => {
            values.set(n.id, [...fs.querySelectorAll<HTMLInputElement>('input:checked')].map((x) => x.value)); emit()
          })
          fs.append(h('div', { class: 'fp-choice' }, inp, h('label', { for: oid, ...PL }, ' ' + c.text),
            c.required ? h('span', { class: 'fp-req' }, ' *') : null))
        })
        return { box: fs, label: null }
      }
      case 'FILE_UPLOADER': {
        const el = h('input', { type: 'file', id, disabled: true, 'aria-describedby': describedBy })
        return { box: h('div', {}, el, h('p', { class: 'muted small' }, FP.fileNote)), label: h('label', { for: id, ...PL }, nameOf(n)) }
      }
      default: {
        const type = n.type === 'DATEPICKER' ? 'date' : n.type === 'NUMBER' ? 'number' : 'text'
        const el = h('input', { type, id, readonly: dis, autocomplete: 'off', 'aria-describedby': describedBy, ...PL })
        el.addEventListener('input', () => { values.set(n.id, el.value); emit() })
        return { box: el, label: h('label', { for: id, ...PL }, nameOf(n)) }
      }
    }
  }

  function renderNode(n: ENode): HTMLElement {
    if (CONTAINER_TYPES.has(n.type)) {
      const box = h('div', { class: 'fp-section', id: wrapId(n.id), 'data-node': n.id },
        h('h4', PL, nameOf(n)),
        n.description ? h('p', { class: 'muted fp-desc', ...PL }, n.description) : null,
        h('p', { class: 'fp-because', id: `fpb-${n.id}`, hidden: true }))
      for (const c of n.children) box.append(renderNode(c))
      return box
    }
    if (!INPUT_TYPES.has(n.type)) {
      return h('div', { class: 'fp-text', id: wrapId(n.id), 'data-node': n.id },
        n.title ? h('p', { class: 'field-title', ...PL }, n.title) : null,
        n.description ? h('p', PL, n.description) : null)
    }
    const { box, label } = control(n)
    const chips: (HTMLElement | null)[] = [
      n.validation.includes('REQUIRED') ? h('span', { class: 'chip chip-req' }, FP.required) : null,
      n.dictionaryName ? h('span', { class: 'chip' }, FP.dictionary(n.dictionaryName)) : null,
      n.defaultValueType === 'EXTERNAL_SYSTEM' && typeof n.defaultValue === 'string'
        ? h('span', { class: 'chip' }, FP.initialData(n.defaultValue)) : null,
      ...n.validation.filter((v) => v !== 'REQUIRED').map((v) => h('span', { class: 'chip chip-type' }, FP.validator(v)))
    ]
    if (label && n.validation.includes('REQUIRED')) label.append(h('span', { class: 'fp-req', 'aria-hidden': 'true' }, ' *'))
    return h('div', { class: 'fp-field', id: wrapId(n.id), 'data-node': n.id, 'data-type': n.type },
      label,
      box,
      h('div', { class: 'chips' }, ...chips),
      n.description ? h('p', { class: 'muted fp-desc', ...PL }, n.description) : null,
      h('p', { class: 'fp-tag', id: `fpt-${n.id}`, hidden: true }),
      h('p', { class: 'fp-err', id: `fpe-${n.id}`, hidden: true }))
  }

  model.tabs.forEach((tab, i) => {
    const sec = h('div', { class: 'fp-page', 'data-page': i, id: `fp-page-${i}` },
      h('h3', PL, tab.title || FP.pageN(i + 1)))
    for (const n of tab.nodes) sec.append(renderNode(n))
    pages.push(sec)
  })

  const wrap = (id: string): HTMLElement | null => root.querySelector<HTMLElement>(`[id="${wrapId(id)}"]`)

  function paintPage(): void {
    pages.forEach((p, i) => { p.hidden = !all && i !== page })
    const n = pages.length
    pageLine.textContent = n ? FP.pageOf(page + 1, n, model.tabs[page]?.title ?? '') : ''
    prev.disabled = page <= 0
    next.disabled = page >= n - 1
  }
  prev.addEventListener('click', () => { if (page > 0) { page--; paintPage(); pages[page].querySelector('h3')?.setAttribute('tabindex', '-1'); pages[page].querySelector<HTMLElement>('h3')?.focus() } })
  next.addEventListener('click', () => { if (page < pages.length - 1) { page++; paintPage(); pages[page].querySelector('h3')?.setAttribute('tabindex', '-1'); pages[page].querySelector<HTMLElement>('h3')?.focus() } })

  function update(): void {
    for (const n of model.all) {
      if (!n.shows.length) continue
      const w = wrap(n.id)
      if (!w) continue
      const cs = conds.get(n.id) ?? []
      const visible = ownVisible(n)
      w.hidden = !visible
      w.classList.toggle('fp-unread-cond', cs.some((c) => c === null))
      const because = root.querySelector<HTMLElement>(`[id="fpb-${n.id}"]`)
      if (because) {
        const why = visible ? [...new Set(cs.flatMap((c) => (c ? reasons(c, look) : [])))] : []
        const unread = cs.some((c) => c === null)
        because.hidden = !why.length && !unread
        because.textContent = unread ? FP.condUnread : why.length ? FP.because(why.join('”, „')) : ''
      }
    }
  }

  function paintValue(n: ENode): void {
    const v = values.get(n.id)
    const el = root.querySelector<HTMLElement>(`[id="${ctlId(n.id)}"]`)
    if (!el) return
    if (el instanceof HTMLInputElement && el.type === 'checkbox') el.checked = Array.isArray(v) && v.length > 0
    else if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement || el instanceof HTMLSelectElement) {
      el.value = typeof v === 'string' ? v : Array.isArray(v) ? v.join(', ') : ''
    } else {
      const chosen = Array.isArray(v) ? v : typeof v === 'string' ? [v] : []
      for (const inp of el.querySelectorAll<HTMLInputElement>('input')) inp.checked = chosen.includes(inp.value)
    }
  }

  function paintTag(n: ENode): void {
    const tag = tags.get(n.id) ?? null
    const p = root.querySelector<HTMLElement>(`[id="fpt-${n.id}"]`)
    const w = wrap(n.id)
    if (p) { p.hidden = !tag; p.textContent = tag ? FP.tag[tag] : ''; p.className = 'fp-tag' + (tag ? ' fp-tag-' + tag : '') }
    w?.setAttribute('data-filled', tag ?? '')
    const lock = tag === 'pesel' || tag === 'mlpz' || n.readOnly
    const el = root.querySelector<HTMLElement>(`[id="${ctlId(n.id)}"]`)
    if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
      if (el.type === 'checkbox') el.disabled = lock
      else el.readOnly = lock
    } else if (el instanceof HTMLSelectElement) el.disabled = lock
    else if (el) for (const inp of el.querySelectorAll<HTMLInputElement>('input')) inp.disabled = lock
  }

  function reset(): void {
    values.clear(); tags.clear()
    for (const n of model.all) {
      const v = initialOf(n)
      if (v !== undefined && INPUT_TYPES.has(n.type)) values.set(n.id, v)
    }
    for (const n of model.all) if (INPUT_TYPES.has(n.type)) { paintValue(n); paintTag(n); api.showError(n.id, null) }
    emit()
  }

  const api: EForm = {
    el: root,
    model,
    get: (id) => values.get(id),
    set(id, v, tag) {
      const n = model.byId.get(id)
      if (!n) return
      values.set(id, v)
      if (tag) tags.set(id, tag); else tags.delete(id)
      paintValue(n); paintTag(n); emit()
    },
    tagOf: (id) => tags.get(id) ?? null,
    textOf(id) {
      const v = values.get(id)
      const n = model.byId.get(id)
      if (n?.type === 'CONSENT_SECTION') return Array.isArray(v) && v.length ? FP.consentGiven(v.length, n.consents.length) : ''
      if (n?.type === 'CHECKBOX' && !n.options.length) return Array.isArray(v) && v.length ? '✓' : ''
      return Array.isArray(v) ? v.join(', ') : v ?? ''
    },
    isVisible,
    inputs: () => model.all.filter((n) => INPUT_TYPES.has(n.type)),
    focus(id) {
      const n = model.byId.get(id)
      if (!n) return
      if (!all) { page = n.tabIndex; paintPage() }
      const el = root.querySelector<HTMLElement>(`[id="${ctlId(id)}"]`)
      const target = el?.matches('fieldset') ? el.querySelector<HTMLElement>('input') : el
      target?.focus()
      wrap(id)?.scrollIntoView?.({ block: 'center' })
    },
    showError(id, msg) {
      const p = root.querySelector<HTMLElement>(`[id="fpe-${id}"]`)
      const el = root.querySelector<HTMLElement>(`[id="${ctlId(id)}"]`)
      if (p) { p.hidden = !msg; p.textContent = msg ?? '' }
      if (el) { if (msg) el.setAttribute('aria-invalid', 'true'); else el.removeAttribute('aria-invalid') }
    },
    reset,
    onChange: (fn) => { listeners.push(fn) },
    showAll(on) { all = on; paintPage() }
  }

  root.append(
    h('h2', { id: 'h-eform', tabindex: -1 }, FP.step(3), ' ', FP.eformHeading),
    h('p', { class: 'notice fp-notice', role: 'note' }, FP.controlPreview),
    h('div', { class: 'fp-pager' }, prev, pageLine, next),
    ...pages)
  reset()
  paintPage()
  return api
}
