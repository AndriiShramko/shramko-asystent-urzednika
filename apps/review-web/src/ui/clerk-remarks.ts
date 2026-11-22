// "Do sprawdzenia": what the software could not settle, shown on the document (wave 11). One card per open remark:
// a crop of the original at that place next to the e-form field it belongs to. A click on a card shows the place on
// the original and the field in the e-form; a click on a mark of the original or a focus in the e-form lights the
// card. A remark that has no place on the paper says so plainly. A ready choice of the server (clerk-contract v1) is
// one click: it is written into the form JSON, the e-form redraws the field, the remark leaves the list. Typing is
// the last resort and happens in the e-form field itself. Codes never appear here: they stay in the jury view.
//
// The cards of one conversion live in a session keyed by the report object, so they survive the rebuild of the
// result on a language change, and the result (built first) and the original pictures (which arrive later) can
// both reach them.
import { getLang, hasKey, t, tn } from '../lib/i18n'
import type { Sidecar } from '../lib/model'
import { fixOf, isNote, nodeAt, placeOf, setPointer, type Fix, type FixOption, type FixSet, type RawWarning } from '../lib/warnings'
import type { Box, Joined, Preview, PreviewPage } from '../lib/fp/places'
import { nameOf } from '../lib/fp/form'
import { h, clear } from './dom'
import type { EForm } from './eform'
import type { BoxTarget } from '../lib/fp/targets'

/** How many cards are shown before "Pokaż wszystkie". */
export const CARDS_SHOWN = 6
/** Remarks of one kind that carry no ready fix: this many get a card each, the rest share one card. */
export const SAME_KIND_CARDS = 3

/** Remarks about the head of the form: when the paper has no such place, it would be at the top of page 1. */
const TOP_OF_FIRST = new Set(['ADDRESSEE_MISSING', 'TITLE_MISSING'])

export interface Remark {
  key: string
  code: string
  /** every warning this card stands for (many places of one kind share one card) */
  items: RawWarning[]
  /** which of `items` the card shows now */
  at: number
  fix: Fix
  done: boolean
  /** what the clerk chose or typed, for the jury list */
  answer: string | null
}

export interface Spot { page: PreviewPage; region: Box; mark: Box | null; absent: boolean }
export interface PaperMark { key: string; n: number; page: number; box: Box }

/** What the original pictures offer to the cards (given by the "where on the paper" block). */
export interface Paper {
  preview(): Preview | null
  joined(): Joined | null
  /** light a place of the original and bring it into view; false when there is no picture of it */
  show(page: number, box: Box): boolean
  /** redraw the numbered marks of the open remarks */
  marks(list: PaperMark[]): void
  /** BL13 CLERK-T: what each box stands for in the e-form (standard sections, merged blanks) */
  targets?(): Map<string, BoxTarget> | null
}

export interface Change { what: string; answer: string }

export interface Session {
  host: HTMLElement
  remarks: Remark[]
  /** remarks the converter settled itself (fix.applied) or that are notes of the run: only the jury view lists them */
  applied: RawWarning[]
  notes: RawWarning[]
  /** how many places are still open */
  openCount(): number
  attach(ef: EForm, paper: Paper): void
  /** the preview arrived (or failed): crops can be drawn */
  ready(): void
  repaint(): void
  /** a place was picked on the original or in the e-form: light its card */
  pick(what: { key?: string | null; fieldId?: string | null }): void
  resolve(r: Remark, answer: string | null): void
  /** the form JSON of the answer, so a pick can be written into a copy of it */
  setForm(form: unknown): void
  /** the form with the clerk's picks, or null when nothing was changed */
  changedForm(): unknown | null
  changes: Change[]
  onChange: (() => void) | null
  eform(): EForm | null
}

const sessions = new WeakMap<object, Session>()

/** The sentence of a remark for the clerk: the server's ready question, else a short one of ours, else the general one. */
export function remarkText(r: Pick<Remark, 'code' | 'fix'>): string {
  if (r.fix.rule && hasKey(getLang(), 'fix.' + r.fix.rule)) return t('fix.' + r.fix.rule)
  // BL13 CLERK-T: a remark without a ready answer speaks in our plain words; a ready choice keeps the server's question
  const ready = r.fix.kind === 'choice' || (r.fix.kind === 'input' && r.fix.stated)
  if (!ready && hasKey('pl', 'clerk.warn.' + r.code)) return t('clerk.warn.' + r.code)
  if (r.fix.text) return r.fix.text
  for (const key of ['clerk.warn.' + r.code, 'warn.' + r.code]) if (hasKey('pl', key)) return t(key)
  return t('clerk.warn.other')
}

const pct = (a: number, b: number): string => `${((a / b) * 100).toFixed(3)}%`
const isBox = (b: unknown): b is Box => Array.isArray(b) && b.length === 4 && b.every((x) => typeof x === 'number' && Number.isFinite(x))

/** A crop of one page picture: `region` in pt of the page, `mark` the outlined place inside it. */
export function cropOf(page: PreviewPage, region: Box, mark: Box | null): HTMLElement {
  const [x0, y0, x1, y1] = region
  const rw = Math.max(1, x1 - x0)
  const rh = Math.max(1, y1 - y0)
  const box = h('div', { class: 'clerk-crop', style: `aspect-ratio: ${rw.toFixed(2)} / ${rh.toFixed(2)}` })
  if (page.img) {
    box.append(h('img', { src: `data:${page.img.media_type};base64,${page.img.data}`, alt: '', class: 'clerk-crop-img',
      style: `width:${pct(page.w, rw)};left:${pct(-x0, rw)};top:${pct(-y0, rh)}` }))
  }
  if (mark) {
    box.append(h('div', { class: 'clerk-crop-mark',
      style: `left:${pct(mark[0] - x0, rw)};top:${pct(mark[1] - y0, rh)};width:${pct(Math.max(mark[2] - mark[0], 4), rw)};height:${pct(Math.max(mark[3] - mark[1], 4), rh)}` }))
  }
  return box
}

/** The part of the page worth showing around a place: the place, its label to the left, a line above and below. */
export function regionAround(page: PreviewPage, b: Box): Box {
  const width = Math.min(page.w, 400)
  const bw = b[2] - b[0]
  // a place wider than the crop is shown from its left edge; a narrow one keeps its label to the left in sight
  const want = bw > width - 60 ? b[0] - 12 : b[0] - Math.min(180, width - bw - 20)
  const x0 = Math.max(0, Math.min(want, page.w - width))
  const y0 = Math.max(0, b[1] - 38)
  const y1 = Math.min(page.h, Math.max(b[3] + 22, y0 + 100))
  return [x0, y0, x0 + width, y1]
}

function buildRemarks(sidecar: Sidecar | null): { remarks: Remark[]; applied: RawWarning[]; notes: RawWarning[] } {
  const list: RawWarning[] = Array.isArray(sidecar?.warnings) ? sidecar.warnings : []
  const remarks: Remark[] = []
  const applied: RawWarning[] = []
  const notes: RawWarning[] = []
  const perKind = new Map<string, { n: number; rest: Remark | null }>()
  const seen = new Set<string>()
  list.forEach((w, i) => {
    const code = typeof w.code === 'string' && w.code ? w.code : 'UNKNOWN'
    // BL13 CLERK-T: the same place of the same kind reported twice (once with its cell, once without) is one place
    if (typeof w.candidate === 'string' && w.candidate) {
      const k = code + '|' + w.candidate
      if (seen.has(k)) return
      seen.add(k)
    }
    const fix = fixOf(w)
    if (fix.kind === 'applied') { applied.push(w); return }
    if (fix.kind === 'note') { notes.push(w); return }
    const r: Remark = { key: 'r' + i, code, items: [w], at: 0, fix, done: false, answer: null }
    if (fix.kind === 'input' && !fix.stated) {
      // no ready fix: a few cards of the kind, then one card for all the other places of that kind
      const k = perKind.get(code) ?? { n: 0, rest: null }
      perKind.set(code, k)
      k.n++
      if (k.n > SAME_KIND_CARDS) {
        if (k.rest) { k.rest.items.push(w); return }
        k.rest = r
      }
    }
    remarks.push(r)
  })
  // ready choices first, then what must be typed, then what can only be looked at
  const rank = (r: Remark): number => (r.fix.kind === 'choice' ? 0 : r.fix.kind === 'input' && r.fix.stated ? 1 : 2)
  remarks.sort((a, b) => rank(a) - rank(b))
  return { remarks, applied, notes }
}

function makeSession(sidecar: Sidecar | null): Session {
  const { remarks, applied, notes } = buildRemarks(sidecar)
  const host = h('section', { class: 'clerk-remarks', id: 'clerk-remarks', 'aria-labelledby': 'h-clerk-remarks' })
  let ef: EForm | null = null
  let paper: Paper | null = null
  let showAll = false
  let active: string | null = null
  let form: unknown = null
  let patched: unknown = null
  const changes: Change[] = []
  const evidence = (sidecar?.meta?.evidence ?? sidecar?.evidence ?? {}) as Record<string, unknown>

  const cur = (r: Remark): RawWarning => r.items[Math.min(r.at, r.items.length - 1)]

  /** The e-form field a remark belongs to: the target of the fix, the remark's own field when it is a form id, or
   * the field its candidate became. */
  const fieldOf = (r: Remark): string | null => {
    const known = (id: unknown): id is string => typeof id === 'string' && !!id && (!ef || ef.model.byId.has(id))
    if (known(r.fix.target?.id)) return r.fix.target.id
    const w = cur(r)
    if (known(w.field) && ef) return w.field
    const j = paper?.joined()
    const direct = typeof w.candidate === 'string' && j ? j.fieldOf.get(w.candidate) ?? null : null
    if (direct) return direct
    const tg = typeof w.candidate === 'string' ? paper?.targets?.()?.get(w.candidate) : undefined
    return tg?.fields[0] ?? null
  }

  /** BL13 CLERK-T: every e-form node a remark concerns: the field of the place (all fields of a standard section that
   * took it over), and for a ready choice the fields its options would change. */
  const fieldsOf = (r: Remark): string[] => {
    const ids: string[] = []
    const add = (id: string | null | undefined): void => { if (id && (!ef || ef.model.byId.has(id)) && !ids.includes(id)) ids.push(id) }
    const w = cur(r)
    const tg = typeof w.candidate === 'string' ? paper?.targets?.()?.get(w.candidate) : undefined
    add(fieldOf(r))
    for (const id of tg?.fields ?? []) add(id)
    if (r.fix.kind === 'choice') {
      for (const o of r.fix.options) for (const s of o.set) add(nodeAt(patched ?? form, s.pointer)?.id)
    }
    return ids
  }

  /** BL13 CLERK-T: the paper's own words at the place of a remark (a quote of the source, the label of the box). */
  function wordsOf(r: Remark): string | null {
    const w = cur(r)
    const srcs = [r.fix.source, ...(r.fix.kind === 'choice' ? r.fix.options.map((o) => o.source) : [])]
    const cut = (x: string): string => { const s = x.replace(/\s+/g, ' ').trim(); return s.length > 160 ? s.slice(0, 157) + '…' : s }
    for (const s of srcs) if (s?.type === 'paper' && typeof s.quote === 'string' && s.quote.trim()) return cut(s.quote)
    if (typeof w.quote === 'string' && w.quote.trim()) return cut(w.quote)
    const pv = paper?.preview()
    const place = typeof w.candidate === 'string' ? pv?.places[w.candidate] : undefined
    if (place?.label?.trim()) return cut(place.label)
    if (typeof w.label === 'string' && w.label.trim()) return cut(w.label)
    return null
  }

  const isRequiredChoice = (r: Remark): boolean => r.fix.kind === 'choice' && (r.code === 'REQUIRED_INFERRED' || r.fix.rule === 'required.paper_is_silent')
  const nameList = (ids: string[]): string => ids.map((id) => { const n = ef?.model.byId.get(id); return n ? '„' + nameOf(n) + '”' : '' }).filter(Boolean).join(', ')

  /** The sentence on the card: for the "which fields are required" choice it names the fields. */
  function cardText(r: Remark): string {
    if (isRequiredChoice(r)) {
      const ids = fieldsOf(r)
      if (ids.length && ef) return t('clerk.req.what', { fields: nameList(ids) })
    }
    return remarkText(r)
  }

  /** The label of a button of a ready choice: ours for the "required" choice, the server's otherwise. */
  function optionLabel(r: Remark, o: FixOption): string {
    if (isRequiredChoice(r)) {
      const n = fieldsOf(r).length
      if (o.value === 'optional') return tn('clerk.req.keepOptional', n)
      if (o.value === 'required') return tn('clerk.req.setRequired', n)
    }
    return o.label
  }

  /** A remark with nothing to show and nothing to decide (no picture, no words, no field): merged into one card. */
  function empty(r: Remark): boolean {
    if (r.fix.kind === 'choice' || (r.fix.kind === 'input' && r.fix.stated)) return false
    if (!paper?.preview()) return false
    return !spotOf(r) && !wordsOf(r) && !fieldsOf(r).length
  }

  /** The page and box of a remark in the units of the preview (pt, origin top left), from the most exact source. */
  function boxOf(r: Remark): { page: number; box: Box } | null {
    const w = cur(r)
    const srcs = [r.fix.source, ...(r.fix.kind === 'choice' ? r.fix.options.map((o) => o.source) : [])]
    for (const s of srcs) if (s?.type === 'paper' && typeof s.page === 'number' && isBox(s.box)) return { page: s.page, box: s.box }
    if (typeof w.page === 'number' && isBox(w.box)) return { page: w.page, box: w.box }
    for (const e of Array.isArray(w.evidence) ? w.evidence as Record<string, unknown>[] : []) {
      if (e && typeof e.page === 'number' && isBox(e.box)) return { page: e.page, box: e.box }
    }
    const pv = paper?.preview()
    const place = typeof w.candidate === 'string' ? pv?.places[w.candidate] : undefined
    if (place?.box) return { page: place.page, box: place.box }
    const f = fieldOf(r)
    const viaField = f ? paper?.joined()?.byField.get(f)?.place : undefined
    if (viaField?.box) return { page: viaField.page, box: viaField.box }
    const ev = f ? evidence[f] : undefined
    for (const e of Array.isArray(ev) ? ev as Record<string, unknown>[] : []) {
      if (e && typeof e.page === 'number' && isBox(e.box)) return { page: e.page, box: e.box }
    }
    return null
  }

  /** Where the remark is on the original, when the pictures are there. */
  function spotOf(r: Remark): Spot | null {
    const pv = paper?.preview()
    if (!pv || !pv.pages.length) return null
    const at = boxOf(r)
    if (at) {
      const page = pv.pages.find((p) => p.n === at.page)
      if (page?.img) return { page, region: regionAround(page, at.box), mark: at.box, absent: false }
    }
    if (TOP_OF_FIRST.has(r.code)) {
      const page = pv.pages[0]
      if (page?.img) return { page, region: [0, 0, page.w, Math.round(page.h * 0.2)], mark: null, absent: true }
    }
    return null
  }

  function light(key: string | null): void {
    active = key
    for (const li of host.querySelectorAll('.clerk-card')) li.classList.toggle('clerk-card-active', li.getAttribute('data-remark') === key)
  }

  function go(r: Remark): void {
    light(r.key)
    const at = boxOf(r)
    const shown = at ? paper?.show(at.page, at.box) ?? false : false
    const ids = fieldsOf(r)
    const f = ids[0] ?? null
    if (f) ef?.highlight(f)
    for (const id of ids.slice(1)) ef?.el.querySelector(`[id="fpw-${id}"]`)?.classList.add('clerk-hl')
    const live = host.querySelector('#clerk-remarks-live')
    if (live) live.textContent = shown || f ? t('clerk.card.shown') : t('clerk.card.nowhere')
  }

  /** Write the sets of a pick into a copy of the form and redraw the nodes they touch. */
  function applySets(sets: FixSet[], typed: string | null): boolean {
    if (!sets.length) return true
    if (form === null || form === undefined) return false
    patched ??= JSON.parse(JSON.stringify(form)) as unknown
    let ok = true
    for (const s of sets) {
      const value = s.from === 'input' ? typed : s.value
      if (s.from === 'input' && typed === null) { ok = false; continue }
      if (!setPointer(patched, s.pointer, value)) { ok = false; continue }
      const node = nodeAt(patched, s.pointer)
      if (node && ef) {
        // the whole property of the node as it stands now (the pointer may reach deeper than the property)
        let whole: unknown = value
        const base = s.pointer.split('/').slice(1)
        const i = base.lastIndexOf(node.key)
        if (i >= 0 && i < base.length - 1) {
          let c: unknown = patched
          for (const tok of base.slice(0, i + 1)) c = (c as Record<string, unknown>)?.[tok.replace(/~1/g, '/').replace(/~0/g, '~')]
          whole = c
        }
        ef.patch(node.id, node.key, whole)
      }
    }
    return ok
  }

  function record(r: Remark, answer: string): void {
    const f = fieldOf(r)
    const node = f && ef ? ef.model.byId.get(f) : undefined
    changes.push({ what: r.fix.target?.label || (node ? nameOf(node) : remarkText(r)), answer })
  }

  function pickOption(r: Remark, o: FixOption): void {
    if (!o.current) {
      if (!applySets(o.set, null)) { const live = host.querySelector('#clerk-remarks-live'); if (live) live.textContent = t('clerk.fix.failed'); return }
      record(r, o.label)
    }
    session.resolve(r, o.label)
  }

  /** The door "type it": the field's own control in the e-form takes the value. */
  function typeIn(r: Remark): void {
    const f = fieldOf(r)
    const input = r.fix.kind === 'choice' || r.fix.kind === 'input' ? r.fix.input : undefined
    if (!f || !ef) return
    go(r)
    if (input) {
      ef.ask(f, input.label || remarkText(r), (v) => {
        if (v === null) return
        if (!applySets(input.set, v)) return
        record(r, v)
        session.resolve(r, v)
      })
      return
    }
    // no pointer from the server: the name of the field is what the clerk can correct in place
    ef.edit(f, (title) => {
      if (title === null) return
      const ptr = pointerOfNode(patched ?? form, f)
      if (ptr) applySets([{ pointer: ptr + '/title', value: title }], null)
      record(r, title)
      session.resolve(r, title)
    })
  }

  function fixBox(r: Remark): HTMLElement {
    const box = h('div', { class: 'clerk-fix' })
    const f = fieldOf(r)
    if (r.fix.kind === 'choice') {
      const options = r.fix.options
      if (options.length > 4) {
        const sel = h('select', { class: 'clerk-fix-select' },
          h('option', { value: '' }, t('clerk.fix.choose')), ...options.map((o, i) => h('option', { value: String(i) }, optionLabel(r, o) + (o.current ? ' ' + t('clerk.fix.current') : ''))))
        sel.setAttribute('aria-label', t('clerk.fix.choose'))
        sel.addEventListener('change', () => { const o = options[Number(sel.value)]; if (sel.value !== '' && o) pickOption(r, o) })
        box.append(sel)
      } else {
        options.forEach((o, i) => {
          const b = h('button', { type: 'button', class: 'btn clerk-fix-btn' + (o.current ? ' clerk-fix-current' : ''), 'data-option': i }, optionLabel(r, o),
            o.current ? ' ' : null, o.current ? h('span', { class: 'clerk-fix-now' }, t('clerk.fix.current')) : null)
          b.addEventListener('click', () => pickOption(r, o))
          box.append(b)
        })
      }
      if (r.fix.input && f && ef) {
        const other = h('button', { type: 'button', class: 'linkish clerk-fix-other', 'data-type-in': '1' }, r.fix.input.label || t('clerk.fix.other'))
        other.addEventListener('click', () => typeIn(r))
        box.append(other)
      }
      return box
    }
    if (f && ef) {
      const stated = r.fix.kind === 'input' && r.fix.stated && r.fix.input
      const edit = h('button', { type: 'button', class: 'btn clerk-fix-btn', 'data-type-in': '1' }, stated ? t('clerk.fix.type') : t('clerk.fix.rename'))
      edit.addEventListener('click', () => typeIn(r))
      box.append(edit)
    }
    // BL13 CLERK-T: the button says what it does: a blank that is no field is skipped, anything else stays as it is
    const skip = !f && (r.code === 'LABEL_NOT_FOUND' || r.code === 'AMBIGUOUS_GROUP')
    const okText = skip ? (r.items.length > 1 ? t('clerk.fix.skipAll') : t('clerk.fix.skip'))
      : r.items.length > 1 ? t('clerk.fix.checkedAll') : t('clerk.fix.checked')
    const ok = h('button', { type: 'button', class: 'btn clerk-fix-btn', 'data-done': '1' }, okText)
    ok.addEventListener('click', () => session.resolve(r, null))
    box.append(ok)
    return box
  }

  function card(r: Remark, n: number): HTMLElement {
    // BL13 CLERK-T: (1) what the matter is, (2) where on the paper in the paper's own words or picture, never a cell
    // address and never "the whole form", (3) the fields it concerns, (4) one action whose button says what it does
    const spot = spotOf(r)
    const ids = fieldsOf(r)
    const pv = paper?.preview()
    const page = spot?.page.n ?? placeOf(cur(r))
    const words = wordsOf(r)
    const onPaper = !!spot && !spot.absent
    const main = h('button', { type: 'button', class: 'clerk-card-main' })
    main.setAttribute('aria-label', t('clerk.card.show'))
    let hasPaper = true
    if (spot) {
      main.append(h('div', { class: 'clerk-card-paper' },
        h('span', { class: 'clerk-card-cap' }, spot.absent ? t('clerk.card.wouldBe') : t('clerk.card.onPaper', { page: spot.page.n })),
        cropOf(spot.page, spot.region, spot.mark)))
    } else if (words) {
      const cap = pv && pv.pages.length && page !== null ? t('clerk.card.wordsPage', { page }) : t('clerk.card.words')
      main.append(h('div', { class: 'clerk-card-paper clerk-card-words' },
        h('span', { class: 'clerk-card-cap' }, cap), h('blockquote', { class: 'clerk-quote', lang: 'pl' }, words)))
    } else if (!pv && typeof cur(r).candidate === 'string') {
      main.append(h('div', { class: 'clerk-card-paper clerk-card-nopaper' }, h('span', { class: 'clerk-card-cap' }, t('clerk.card.noPreview'))))
    } else if (pv && pv.pages.length && page !== null && boxOf(r)) {
      main.append(h('div', { class: 'clerk-card-paper clerk-card-nopaper' }, h('span', { class: 'clerk-card-cap' }, t('clerk.card.pageOnly', { page }))))
    } else hasPaper = false
    main.addEventListener('click', () => go(r))
    let side: HTMLElement | null = null
    if (ids.length) {
      const shown = ids.slice(0, 6)
      const btns = shown.map((id) => {
        const node = ef?.model.byId.get(id)
        const b = h('button', { type: 'button', class: 'clerk-card-field', lang: 'pl' }, node ? nameOf(node) : r.fix.target?.label ?? id)
        b.addEventListener('click', () => go(r))
        return b
      })
      side = h('div', { class: 'clerk-card-fields' }, ...btns, ids.length > shown.length ? h('span', { class: 'muted' }, ' ' + t('clerk.card.moreFields', { n: ids.length - shown.length })) : null)
    } else if (onPaper || words) {
      side = h('span', { class: 'clerk-card-field clerk-card-whole' }, t('clerk.card.notInForm'))
    }
    const many = r.items.length > 1
    let stepper: HTMLElement | null = null
    if (many) {
      const prev = h('button', { type: 'button', class: 'btn clerk-step', 'data-step': '-1' }, '‹')
      const next = h('button', { type: 'button', class: 'btn clerk-step', 'data-step': '1' }, '›')
      prev.setAttribute('aria-label', t('clerk.card.prev'))
      next.setAttribute('aria-label', t('clerk.card.next'))
      const move = (d: number): void => { r.at = (r.at + d + r.items.length) % r.items.length; repaint(); go(r) }
      prev.addEventListener('click', () => move(-1))
      next.addEventListener('click', () => move(1))
      stepper = h('p', { class: 'clerk-stepper' }, prev, h('span', {}, t('clerk.card.ofMany', { i: r.at + 1, n: r.items.length })), next)
    }
    return h('li', { class: 'clerk-card' + (r.key === active ? ' clerk-card-active' : '') + (hasPaper ? '' : ' clerk-card-flat'), 'data-remark': r.key, 'data-fix': r.fix.kind },
      h('p', { class: 'clerk-card-what' }, h('span', { class: 'clerk-num', 'aria-hidden': 'true' }, String(n)), ' ', cardText(r),
        many ? h('span', { class: 'clerk-card-count' }, ' ' + tn('clerk.card.places', r.items.length)) : null),
      h('div', { class: 'clerk-card-body' },
        hasPaper ? main : null,
        h('div', { class: 'clerk-card-side' },
          side ? h('span', { class: 'clerk-card-cap' }, ids.length > 1 ? t('clerk.card.inFormMany') : t('clerk.card.inForm')) : null,
          side,
          stepper,
          fixBox(r))))
  }

  /** BL13 CLERK-T: one card for all the remarks that have nothing to show and nothing to decide. */
  function restCard(list: Remark[], n: number): HTMLElement {
    const places = list.reduce((a, r) => a + r.items.length, 0)
    const kinds = [...new Set(list.map((r) => remarkText(r)))]
    const ok = h('button', { type: 'button', class: 'btn clerk-fix-btn', 'data-done': '1' }, tn('clerk.rest.ok', places))
    ok.addEventListener('click', () => { for (const r of list) { r.done = true; r.answer = null }; if (active && list.some((r) => r.key === active)) active = null; repaint(); session.onChange?.() })
    return h('li', { class: 'clerk-card clerk-card-flat clerk-card-rest', 'data-remark': 'rest', 'data-fix': 'rest' },
      h('p', { class: 'clerk-card-what' }, h('span', { class: 'clerk-num', 'aria-hidden': 'true' }, String(n)), ' ', tn('clerk.rest.what', places)),
      h('ul', { class: 'clerk-rest-kinds' }, ...kinds.map((k) => h('li', {}, k))),
      h('p', { class: 'muted' }, t('clerk.rest.why')),
      h('div', { class: 'clerk-card-side' }, h('div', { class: 'clerk-fix' }, ok)))
  }

  function repaint(): void {
    clear(host)
    const open0 = remarks.filter((r) => !r.done)
    // BL13 CLERK-T: remarks with nothing to show or to decide share one card at the end
    const rest = open0.filter((r) => empty(r))
    const open = open0.filter((r) => !rest.includes(r))
    const places = open0.reduce((a, r) => a + r.items.length, 0)
    const done = remarks.length - open.length
    host.setAttribute('data-open', String(places))
    // the same numbers on the cards, on the original and on the e-form fields
    const numbered = new Map(open.map((r, i) => [r.key, i + 1]))
    ef?.clearFlags()
    const marks: PaperMark[] = []
    for (const r of open) {
      const n = numbered.get(r.key) ?? 0
      for (const id of fieldsOf(r).slice(1)) ef?.flag(id, n)
      const f = fieldOf(r)
      if (f) ef?.flag(f, n)
      const at = boxOf(r)
      if (at) marks.push({ key: r.key, n, page: at.page, box: at.box })
    }
    paper?.marks(marks)
    const sig = signatureNote()
    if (!open0.length) {
      if (sig) host.append(sig)
      host.append(h('h3', { id: 'h-clerk-remarks', class: 'clerk-allgood' }, done ? t('clerk.remarks.allDone') : t('clerk.remarks.none')))
      return
    }
    host.append(
      h('h3', { id: 'h-clerk-remarks' }, t('clerk.remarks.heading', { n: places })),
      h('p', { class: 'muted clerk-remarks-intro' }, t('clerk.remarks.intro')))
    if (sig) host.append(sig)
    const shown = showAll ? open : open.slice(0, CARDS_SHOWN)
    const items = shown.map((r) => card(r, numbered.get(r.key) ?? 0))
    if (rest.length && shown.length === open.length) items.push(restCard(rest, open.length + 1))
    host.append(h('ol', { class: 'clerk-cards' }, ...items))
    if (open.length > shown.length) {
      const more = h('button', { type: 'button', class: 'btn', id: 'clerk-remarks-more' }, t('clerk.remarks.more', { n: open.length - shown.length + (rest.length ? 1 : 0) }))
      more.addEventListener('click', () => { showAll = true; repaint() })
      host.append(more)
    }
    host.append(h('p', { id: 'clerk-remarks-live', class: 'sr-only', 'aria-live': 'polite' }))
  }

  /** BL13 CLERK-T: one plain line, visible without a click, when the paper's signature and date have no field. */
  function signatureNote(): HTMLElement | null {
    const meta = (sidecar?.meta ?? {}) as Record<string, unknown>
    const ledger = (meta.ledger ?? (sidecar as Record<string, unknown> | null)?.ledger) as { rows?: { fate?: unknown; reason?: unknown }[] } | undefined
    const rows = Array.isArray(ledger?.rows) ? ledger.rows : []
    if (!rows.some((x) => x?.fate === 'LEFT_OUT' && x?.reason === 'SIGNATURE_AND_DATE')) return null
    return h('p', { class: 'clerk-signature-note', id: 'clerk-signature-note' }, t('clerk.signature.note'))
  }

  const session: Session = {
    host,
    remarks,
    applied,
    notes,
    openCount: () => remarks.reduce((a, r) => a + (r.done ? 0 : r.items.length), 0),
    attach(e, p) {
      ef = e
      paper = p
      const conf = (sidecar?.meta as Record<string, unknown> | undefined)?.confidence
      if (conf && typeof conf === 'object') {
        for (const [id, c] of Object.entries(conf as Record<string, { band?: unknown }>)) {
          const band = typeof c?.band === 'string' ? c.band : ''
          if (band === 'check' || band === 'unsure') e.doubt(id, band, t('clerk.band.' + band))
        }
      }
      repaint()
    },
    ready() { repaint() },
    repaint,
    pick({ key, fieldId }) {
      const r = remarks.find((x) => !x.done && ((key && x.key === key) || (fieldId && fieldOf(x) === fieldId)))
      light(r?.key ?? null)
      if (r && key) { const f = fieldOf(r); if (f) ef?.highlight(f) }
    },
    resolve(r, answer) {
      r.done = true
      r.answer = answer
      if (active === r.key) active = null
      repaint()
      session.onChange?.()
    },
    setForm(f) { if (form === null) form = f },
    changedForm: () => (changes.length ? patched : null),
    changes,
    onChange: null,
    eform: () => ef
  }
  repaint()
  return session
}

/** RFC 6901 pointer of the `field` object with this id inside the form (tabs, questions, nested grids). */
export function pointerOfNode(form: unknown, id: string): string | null {
  const walk = (field: unknown, at: string): string | null => {
    if (!field || typeof field !== 'object') return null
    const f = field as { id?: unknown; repeatingSectionGrid?: { field?: unknown }[] }
    if (f.id === id) return at
    const grid = Array.isArray(f.repeatingSectionGrid) ? f.repeatingSectionGrid : []
    for (let i = 0; i < grid.length; i++) {
      const hit = walk(grid[i]?.field, `${at}/repeatingSectionGrid/${i}/field`)
      if (hit) return hit
    }
    return null
  }
  const tabs = (form as { tabs?: { questions?: { field?: unknown }[] }[] } | null)?.tabs
  if (!Array.isArray(tabs)) return null
  for (let ti = 0; ti < tabs.length; ti++) {
    const qs = Array.isArray(tabs[ti]?.questions) ? tabs[ti].questions! : []
    for (let qi = 0; qi < qs.length; qi++) {
      const hit = walk(qs[qi]?.field, `/tabs/${ti}/questions/${qi}/field`)
      if (hit) return hit
    }
  }
  return null
}

/** The session of one conversion. Without a report there is nothing to keep: a fresh empty one each time. */
export function sessionOf(sidecar: Sidecar | null): Session {
  if (!sidecar) return makeSession(null)
  let s = sessions.get(sidecar)
  if (!s) { s = makeSession(sidecar); sessions.set(sidecar, s) }
  return s
}

export { isNote }
