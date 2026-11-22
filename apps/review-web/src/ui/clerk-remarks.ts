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
  list.forEach((w, i) => {
    const code = typeof w.code === 'string' && w.code ? w.code : 'UNKNOWN'
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
    return typeof w.candidate === 'string' && j ? j.fieldOf.get(w.candidate) ?? null : null
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
    const f = fieldOf(r)
    if (f) ef?.highlight(f)
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
          h('option', { value: '' }, t('clerk.fix.choose')), ...options.map((o, i) => h('option', { value: String(i) }, o.label + (o.current ? ' ' + t('clerk.fix.current') : ''))))
        sel.setAttribute('aria-label', t('clerk.fix.choose'))
        sel.addEventListener('change', () => { const o = options[Number(sel.value)]; if (sel.value !== '' && o) pickOption(r, o) })
        box.append(sel)
      } else {
        options.forEach((o, i) => {
          const b = h('button', { type: 'button', class: 'btn clerk-fix-btn' + (o.current ? ' clerk-fix-current' : ''), 'data-option': i }, o.label,
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
    const ok = h('button', { type: 'button', class: 'btn clerk-fix-btn', 'data-done': '1' }, r.items.length > 1 ? t('clerk.fix.checkedAll') : t('clerk.fix.checked'))
    ok.addEventListener('click', () => session.resolve(r, null))
    box.append(ok)
    return box
  }

  function card(r: Remark, n: number): HTMLElement {
    const spot = spotOf(r)
    const f = fieldOf(r)
    const node = f && ef ? ef.model.byId.get(f) : undefined
    const pv = paper?.preview()
    const page = spot?.page.n ?? placeOf(cur(r))
    const main = h('button', { type: 'button', class: 'clerk-card-main' })
    main.setAttribute('aria-label', t('clerk.card.show'))
    if (spot) {
      main.append(h('div', { class: 'clerk-card-paper' },
        h('span', { class: 'clerk-card-cap' }, spot.absent ? t('clerk.card.wouldBe') : t('clerk.card.onPaper', { page: spot.page.n })),
        cropOf(spot.page, spot.region, spot.mark)))
    } else {
      const anchor = typeof cur(r).anchor === 'string' ? (cur(r).anchor as string).trim() : ''
      const why = pv && !pv.pages.length ? (anchor ? t('clerk.card.anchor', { anchor }) : t('clerk.card.noPicture'))
        : !pv ? t('clerk.card.noPreview')
          : page !== null ? t('clerk.card.pageOnly', { page }) : t('clerk.card.notOnPaper')
      main.append(h('div', { class: 'clerk-card-paper clerk-card-nopaper' }, h('span', { class: 'clerk-card-cap' }, why)))
    }
    const fieldName = node ? nameOf(node) : r.fix.target?.label ?? null
    const fieldBtn = fieldName !== null
      ? h('button', { type: 'button', class: 'clerk-card-field', lang: 'pl' }, fieldName)
      : h('span', { class: 'clerk-card-field clerk-card-whole' }, f === null && spot && !spot.absent ? t('clerk.card.notInForm') : t('clerk.card.wholeForm'))
    if (fieldName !== null) fieldBtn.addEventListener('click', () => go(r))
    main.addEventListener('click', () => go(r))
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
    return h('li', { class: 'clerk-card' + (r.key === active ? ' clerk-card-active' : ''), 'data-remark': r.key, 'data-fix': r.fix.kind },
      h('p', { class: 'clerk-card-what' }, h('span', { class: 'clerk-num', 'aria-hidden': 'true' }, String(n)), ' ', remarkText(r),
        many ? h('span', { class: 'clerk-card-count' }, ' ' + tn('clerk.card.places', r.items.length)) : null),
      h('div', { class: 'clerk-card-body' },
        main,
        h('div', { class: 'clerk-card-side' },
          h('span', { class: 'clerk-card-cap' }, t('clerk.card.inForm')),
          fieldBtn,
          stepper,
          fixBox(r))))
  }

  function repaint(): void {
    clear(host)
    const open = remarks.filter((r) => !r.done)
    const places = open.reduce((a, r) => a + r.items.length, 0)
    const done = remarks.length - open.length
    host.setAttribute('data-open', String(places))
    // the same numbers on the cards, on the original and on the e-form fields
    const numbered = new Map(open.map((r, i) => [r.key, i + 1]))
    ef?.clearFlags()
    const marks: PaperMark[] = []
    for (const r of open) {
      const n = numbered.get(r.key) ?? 0
      const f = fieldOf(r)
      if (f) ef?.flag(f, n)
      const at = boxOf(r)
      if (at) marks.push({ key: r.key, n, page: at.page, box: at.box })
    }
    paper?.marks(marks)
    if (!open.length) {
      host.append(h('h3', { id: 'h-clerk-remarks', class: 'clerk-allgood' }, done ? t('clerk.remarks.allDone') : t('clerk.remarks.none')))
      return
    }
    host.append(
      h('h3', { id: 'h-clerk-remarks' }, t('clerk.remarks.heading', { n: places })),
      h('p', { class: 'muted clerk-remarks-intro' }, t('clerk.remarks.intro')))
    const shown = showAll ? open : open.slice(0, CARDS_SHOWN)
    host.append(h('ol', { class: 'clerk-cards' }, ...shown.map((r) => card(r, numbered.get(r.key) ?? 0))))
    if (open.length > shown.length) {
      const more = h('button', { type: 'button', class: 'btn', id: 'clerk-remarks-more' }, t('clerk.remarks.more', { n: open.length - shown.length }))
      more.addEventListener('click', () => { showAll = true; repaint() })
      host.append(more)
    }
    host.append(h('p', { id: 'clerk-remarks-live', class: 'sr-only', 'aria-live': 'polite' }))
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
