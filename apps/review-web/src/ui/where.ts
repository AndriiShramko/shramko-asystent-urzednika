// Step 2 addition: "where on the paper". The page pictures of the original with the place of each field outlined;
// a click on a field in the list shows and pulses its box, a click on a box goes back to its row. Formats without
// page pictures show the anchor the service gave (a paragraph, a cell). Any failure of the preview call leaves the
// rest of the page as it is and says „Podgląd druku niedostępny”.
import { h, clear } from './dom'
import { nameOf } from '../lib/fp/form'
import { joinPlaces, ledgerRows, parsePreview, type Joined, type Place, type Preview, type PreviewPage } from '../lib/fp/places'
import { FP } from '../lib/fp/text'
import type { Sidecar } from '../lib/model'
import type { EForm } from './eform'
import { clerkText, inClerkView } from './clerk-view'
import { boxTargets, fieldBoxes, paperOnlyNotes, type BoxTarget } from '../lib/fp/targets'
import { t as tr, hasKey, getLang } from '../lib/i18n'
import { sessionOf, type PaperMark } from './clerk-remarks'

export interface Where { el: HTMLElement; ready: Promise<void>; preview(): Preview | null; joined(): Joined | null; targets?(): Map<string, BoxTarget> | null }

/** The plain note a click on a box that is not a field answers with (BL13 CLERK-T). */
export function boxNote(tg: BoxTarget): string | null {
  if (tg.kind === 'out') {
    if (tg.text && getLang() === 'pl') return tg.text
    const key = 'clerk.box.out.' + (tg.reason ?? 'OTHER')
    return hasKey(getLang(), key) ? tr(key) : tr('clerk.box.out.OTHER')
  }
  if (tg.kind === 'wait') return tr('clerk.box.wait')
  if (!tg.fields.length) return tr('clerk.box.none')
  return null
}

interface Row { key: string; name: string; cid: string | null; place: Place | null }

const pct = (a: number, b: number): string => `${((a / b) * 100).toFixed(3)}%`

/** One page picture with outlined boxes, in % of the page (so it scales with the column). */
export function paperPage(page: PreviewPage, boxes: { cid: string; place: Place; label: string; cls?: string }[]): HTMLElement {
  const sheet = h('div', { class: 'fp-paper', 'data-page': page.n, style: `aspect-ratio: ${page.w} / ${page.h}` })
  if (page.img) sheet.append(h('img', { src: `data:${page.img.media_type};base64,${page.img.data}`, alt: `Strona ${page.n} oryginału`, class: 'fp-paper-img' }))
  const layer = h('div', { class: 'fp-paper-layer', 'aria-hidden': 'true' })
  for (const b of boxes) {
    const box = b.place.box
    if (!box || b.place.page !== page.n) continue
    const [x0, y0, x1, y1] = box
    layer.append(h('div', { class: 'fp-box' + (b.cls ? ' ' + b.cls : ''), 'data-cid': b.cid, title: b.label,
      style: `left:${pct(x0, page.w)};top:${pct(y0, page.h)};width:${pct(Math.max(x1 - x0, 2), page.w)};height:${pct(Math.max(y1 - y0, 2), page.h)}` }))
  }
  sheet.append(layer)
  return sheet
}

export function renderWhere(ef: EForm, sidecar: Sidecar | null, pending: Promise<unknown>): Where {
  let pv: Preview | null = null
  let joined: Joined | null = null
  let targets: Map<string, BoxTarget> | null = null
  const body = h('div', { id: 'fp-where-body' }, clerkText('p', 'clerk.col.loading', { class: 'muted' }))
  // Wave 11: in the clerk view this block is the left column, "the original"; the list of places is for the jury.
  const el = h('section', { id: 'fp-where', class: 'fp-step', 'aria-labelledby': 'h-where' },
    clerkText('h3', 'clerk.col.original', { class: 'clerk-only clerk-col-title' }),
    clerkText('p', 'clerk.col.originalHint', { class: 'clerk-only muted clerk-col-hint' }),
    h('h2', { id: 'h-where', class: 'jury-only' }, FP.step(2), ' ', FP.whereHeading), body)
  const session = sessionOf(sidecar)
  let papersEl: HTMLElement | null = null
  let lastMarks: PaperMark[] = []

  const pageLayer = (n: number): HTMLElement | null => papersEl?.querySelector<HTMLElement>(`.fp-paper[data-page="${n}"] .fp-paper-layer`) ?? null
  const place = (box: [number, number, number, number], page: { w: number; h: number }): string =>
    `left:${pct(box[0], page.w)};top:${pct(box[1], page.h)};width:${pct(Math.max(box[2] - box[0], 2), page.w)};height:${pct(Math.max(box[3] - box[1], 2), page.h)}`

  function drawMarks(): void {
    if (!papersEl || !pv) return
    for (const m of papersEl.querySelectorAll('.clerk-mark')) m.remove()
    for (const m of lastMarks) {
      const page = pv.pages.find((x) => x.n === m.page)
      const layer = pageLayer(m.page)
      if (!page || !layer) continue
      const mark = h('button', { type: 'button', class: 'clerk-mark clerk-only', 'data-remark': m.key, style: place(m.box, page) },
        h('span', { class: 'clerk-num' }, String(m.n)))
      mark.addEventListener('click', (e) => {
        e.stopPropagation()
        session.pick({ key: m.key })
        spot(m.page, m.box)
        // BL13 CLERK-T: the mark of a remark sits on a box; that box's explanation shows too
        const same = (b?: number[]): boolean => !!b && b.every((x, i) => Math.abs(x - m.box[i]) < 1)
        const tg = targets ? [...targets.values()].find((x) => x.place.page === m.page && same(x.place.box)) : undefined
        if (tg && !tg.fields.length) showNote(tg, layer)
      })
      layer.append(mark)
    }
  }

  /** BL13 CLERK-T: the plain note of a box that is no field, under the box and for the screen reader. */
  function showNote(tg: BoxTarget, layer: HTMLElement | null): void {
    const note = boxNote(tg)
    if (!note) return
    for (const x of papersEl?.querySelectorAll('.clerk-boxnote') ?? []) x.remove()
    const page = pv?.pages.find((p) => p.n === tg.place.page)
    const b = tg.place.box
    if (page && b && layer) {
      const top = Math.min(b[3] + 4, page.h - 40)
      layer.append(h('div', { class: 'clerk-boxnote', style: `left:${pct(Math.min(b[0], page.w * 0.55), page.w)};top:${pct(top, page.h)}` }, note))
    }
    const live = el.querySelector('#fp-where-boxlive')
    if (live) live.textContent = note
  }

  /** Light a place of the original (a box in pt on a page) and bring it into view. */
  function spot(pageNo: number, box: [number, number, number, number]): boolean {
    if (!papersEl || !pv) return false
    const page = pv.pages.find((x) => x.n === pageNo)
    const layer = pageLayer(pageNo)
    if (!page || !layer) return false
    for (const x of papersEl.querySelectorAll('.clerk-spot')) x.remove()
    const mark = h('div', { class: 'clerk-spot', style: place(box, page) })
    layer.append(mark)
    mark.scrollIntoView?.({ block: 'center', behavior: 'smooth' })
    return true
  }

  const origins: Record<string, string> = (sidecar?.meta?.origins ?? sidecar?.origins ?? {}) as Record<string, string>

  function rowsOf(j: Joined, p: Preview): Row[] {
    const rows: Row[] = []
    const seen = new Set<string>()
    for (const r of ledgerRows(sidecar)) {
      const place = p.places[r.candidate] ?? null
      if (r.fate === 'FIELD' && r.field) {
        if (seen.has(r.field)) continue
        seen.add(r.field)
        const n = ef.model.byId.get(r.field)
        rows.push({ key: r.field, name: n ? nameOf(n) : r.field, cid: r.candidate, place })
      } else if (r.fate === 'STANDARD') {
        rows.push({ key: r.candidate, name: place?.label ?? r.section ?? r.candidate, cid: r.candidate, place })
      }
    }
    // matter fields of the form that no ledger row places
    for (const n of ef.inputs()) {
      if (origins[n.id] === 'paper' && !seen.has(n.id) && !j.byField.has(n.id)) rows.push({ key: n.id, name: nameOf(n), cid: null, place: null })
    }
    return rows
  }

  function paint(): void {
    clear(body)
    const rows0 = ledgerRows(sidecar)
    papersEl = null
    el.setAttribute('data-pages', String(pv?.pages.length ?? 0))
    if (!pv || !rows0.length) {
      // without the ledger there are no places, but the clerk still compares with the pictures when they are there
      if (pv?.pages.length) {
        papersEl = h('div', { class: 'fp-papers', id: 'fp-papers' }, ...pv.pages.map((page) => paperPage(page, [])))
        body.append(h('p', { id: 'fp-where-missing', class: 'jury-only' }, FP.previewMissing), papersEl)
      } else body.append(h('p', { id: 'fp-where-missing' }, FP.previewMissing))
      return
    }
    joined = joinPlaces(rows0, pv)
    targets = boxTargets(rows0, pv, ef.model, paperOnlyNotes(sidecar?.warnings))
    const rows = rowsOf(joined, pv)
    const live = h('p', { id: 'fp-where-live', 'aria-live': 'polite', class: 'muted' })
    const list = h('ul', { class: 'plain fp-where-list', id: 'fp-where-list' })
    const papers = h('div', { class: 'fp-papers', id: 'fp-papers' })
    const geometry = pv.pages.length > 0
    fieldBox.clear()

    for (const r of rows) {
      const hasBox = geometry && !!r.place?.box
      const chip = hasBox ? FP.pageChip(r.place!.page) : r.place?.anchor && !geometry ? r.place.anchor : FP.noBox
      const btn = h('button', { type: 'button', class: 'linkish', 'data-where': r.key, 'data-cid': r.cid ?? '', disabled: hasBox ? undefined : true }, r.name)
      btn.addEventListener('click', () => {
        for (const b of papers.querySelectorAll('.fp-box-active')) b.classList.remove('fp-box-active')
        const box = r.cid ? papers.querySelector<HTMLElement>(`.fp-box[data-cid="${r.cid}"]`) : null
        if (box) {
          box.classList.add('fp-box-active')
          box.scrollIntoView?.({ block: 'center', behavior: 'smooth' })
          live.textContent = `„${r.name}”: ${FP.pageChip(r.place!.page)}`
        }
      })
      if (hasBox && r.cid && ef.model.byId.has(r.key)) fieldBox.set(r.key, r.cid)
      list.append(h('li', {}, btn, ' ', h('span', { class: hasBox ? 'chip' : 'chip chip-req' }, chip)))
    }

    if (!geometry) {
      body.append(h('p', { class: 'muted', id: 'fp-where-nogeo' }, FP.noPageImage), list)
      return
    }
    const boxes: { cid: string; place: Place; label: string; cls?: string }[] = rows.filter((r) => r.cid && r.place?.box).map((r) => ({ cid: r.cid!, place: r.place!, label: r.name }))
    // the marks of choice groups, so a ticked option can be seen too
    for (const r of rows) for (const o of r.place?.options ?? []) {
      const m = o.mark ? pv.places[o.mark] : undefined
      if (m?.box) boxes.push({ cid: o.mark!, place: m, label: `${r.name}: ${o.text}` })
    }
    // BL13 CLERK-T: the places that did not become a field of their own get a frame too (signature and date,
    // merged blanks, blanks waiting for a decision), so a click on them answers instead of being silent
    const drawn = new Set(boxes.map((b) => b.cid))
    for (const tg of targets.values()) {
      if (drawn.has(tg.cid) || !tg.place.box) continue
      drawn.add(tg.cid)
      boxes.push({ cid: tg.cid, place: tg.place, label: tg.place.label ?? boxNote(tg) ?? '', cls: tg.kind === 'out' ? 'fp-box-out' : tg.kind === 'wait' ? 'fp-box-wait' : undefined })
    }
    for (const page of pv.pages) papers.append(paperPage(page, boxes))
    papers.addEventListener('click', (e) => {
      const t = (e.target as HTMLElement).closest<HTMLElement>('.fp-box')
      if (!t) return
      const cid = t.dataset.cid ?? ''
      const fid = joined?.fieldOf.get(cid)
      const btn = list.querySelector<HTMLButtonElement>(`[data-cid="${cid}"]`) ?? (fid ? list.querySelector<HTMLButtonElement>(`[data-where="${fid}"]`) : null)
      if (inClerkView(el)) {
        // the clerk's view has no list: the box lights itself, the e-form shows its field, the card of the place lights
        for (const b of papers.querySelectorAll('.fp-box-active')) b.classList.remove('fp-box-active')
        for (const x of papers.querySelectorAll('.clerk-boxnote')) x.remove()
        t.classList.add('fp-box-active')
        const tg = targets?.get(cid)
        const ids = tg?.fields.length ? tg.fields : fid ? [fid] : []
        if (ids.length) {
          ef.highlight(ids[0])
          for (const id of ids.slice(1)) ef.el.querySelector(`[id="fpw-${id}"]`)?.classList.add('clerk-hl')
          session.pick({ fieldId: ids[0] })
          return
        }
        if (tg) showNote(tg, t.parentElement)
        else { const live = el.querySelector('#fp-where-boxlive'); if (live) live.textContent = tr('clerk.box.none') }
        return
      }
      btn?.focus()
      btn?.click()
    })
    papersEl = papers
    body.append(h('p', { id: 'fp-where-boxlive', class: 'sr-only', 'aria-live': 'polite' }))
    const toggle = h('input', { type: 'checkbox', id: 'fp-where-toggle', checked: true })
    toggle.addEventListener('change', () => papers.classList.toggle('fp-boxes-off', !toggle.checked))
    body.append(h('p', { class: 'jury-only' }, toggle, h('label', { for: 'fp-where-toggle' }, ' ' + FP.whereToggle)),
      h('div', { class: 'fp-where-grid' }, h('div', { class: 'jury-only' }, list, live), papers))
  }

  /** form field id -> the candidate whose box is drawn for it */
  const fieldBox = new Map<string, string>()
  /** BL13 PRINT-MAP: a picked field without a place on the original says so in one line next to it, never silence. */
  function noPlaceLine(id: string): void {
    for (const x of ef.el.querySelectorAll('.fp-noplace')) x.remove()
    const w = ef.el.querySelector<HTMLElement>(`[id="fpw-${id}"]`)
    if (!w) return
    let standard = false
    for (let n = ef.model.byId.get(id) ?? null; n; n = n.parent) {
      const o = n.id ? origins[n.id] : undefined
      if (o) { standard = o === 'standard'; break }
    }
    const text = standard ? FP.noPlaceStandard : FP.noPlaceOther
    w.append(h('p', { class: 'fp-noplace muted', lang: 'pl', 'data-for': id }, text))
    const live = el.querySelector('#fp-where-boxlive')
    if (live) live.textContent = text
    else w.lastElementChild?.setAttribute('role', 'status')
  }
  // a focus in the e-form lights the place of that field on the original (clerk view only: side by side)
  ef.onPick((id) => {
    if (!inClerkView(el)) return
    // BL13 PRINT-MAP: an original without page pictures (or a preview that failed) still answers the pick
    if (!papersEl) { if (painted) { noPlaceLine(id); session.pick({ fieldId: id }) } return }
    for (const b of papersEl.querySelectorAll('.fp-box-active')) b.classList.remove('fp-box-active')
    for (const x of ef.el.querySelectorAll('.fp-noplace')) x.remove()
    const cid = fieldBox.get(id) ?? joined?.byField.get(id)?.cid ?? (targets ? fieldBoxes(targets).get(id) : undefined)
    const box = cid ? papersEl.querySelector<HTMLElement>(`.fp-box[data-cid="${cid}"]`) : null
    if (box) { box.classList.add('fp-box-active'); box.scrollIntoView?.({ block: 'nearest', behavior: 'smooth' }) }
    else noPlaceLine(id)
    session.pick({ fieldId: id })
  })
  session.attach(ef, {
    preview: () => pv,
    joined: () => joined,
    targets: () => targets,
    show: (page, box) => spot(page, box),
    marks: (list) => { lastMarks = list; drawMarks() }
  })

  let painted = false
  const done = (): void => { paint(); painted = true; session.ready(); drawMarks() }
  const ready = pending.then((raw) => { pv = parsePreview(raw); done() }, () => { pv = null; done() })
  return { el, ready, preview: () => pv, joined: () => joined, targets: () => targets }
}
