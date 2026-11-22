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

export interface Where { el: HTMLElement; ready: Promise<void>; preview(): Preview | null; joined(): Joined | null }

interface Row { key: string; name: string; cid: string | null; place: Place | null }

const pct = (a: number, b: number): string => `${((a / b) * 100).toFixed(3)}%`

/** One page picture with outlined boxes, in % of the page (so it scales with the column). */
export function paperPage(page: PreviewPage, boxes: { cid: string; place: Place; label: string }[]): HTMLElement {
  const sheet = h('div', { class: 'fp-paper', 'data-page': page.n, style: `aspect-ratio: ${page.w} / ${page.h}` })
  if (page.img) sheet.append(h('img', { src: `data:${page.img.media_type};base64,${page.img.data}`, alt: `Strona ${page.n} oryginału`, class: 'fp-paper-img' }))
  const layer = h('div', { class: 'fp-paper-layer', 'aria-hidden': 'true' })
  for (const b of boxes) {
    const box = b.place.box
    if (!box || b.place.page !== page.n) continue
    const [x0, y0, x1, y1] = box
    layer.append(h('div', { class: 'fp-box', 'data-cid': b.cid, title: b.label,
      style: `left:${pct(x0, page.w)};top:${pct(y0, page.h)};width:${pct(Math.max(x1 - x0, 2), page.w)};height:${pct(Math.max(y1 - y0, 2), page.h)}` }))
  }
  sheet.append(layer)
  return sheet
}

export function renderWhere(ef: EForm, sidecar: Sidecar | null, pending: Promise<unknown>): Where {
  let pv: Preview | null = null
  let joined: Joined | null = null
  const body = h('div', { id: 'fp-where-body' }, h('p', { class: 'muted' }, '…'))
  const el = h('section', { id: 'fp-where', class: 'fp-step', 'aria-labelledby': 'h-where' },
    h('h2', { id: 'h-where' }, FP.step(2), ' ', FP.whereHeading), body)

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
    if (!pv || !rows0.length) { body.append(h('p', { id: 'fp-where-missing' }, FP.previewMissing)); return }
    joined = joinPlaces(rows0, pv)
    const rows = rowsOf(joined, pv)
    const live = h('p', { id: 'fp-where-live', 'aria-live': 'polite', class: 'muted' })
    const list = h('ul', { class: 'plain fp-where-list', id: 'fp-where-list' })
    const papers = h('div', { class: 'fp-papers', id: 'fp-papers' })
    const geometry = pv.pages.length > 0

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
      list.append(h('li', {}, btn, ' ', h('span', { class: hasBox ? 'chip' : 'chip chip-req' }, chip)))
    }

    if (!geometry) {
      body.append(h('p', { class: 'muted', id: 'fp-where-nogeo' }, FP.noPageImage), list)
      return
    }
    const boxes = rows.filter((r) => r.cid && r.place?.box).map((r) => ({ cid: r.cid!, place: r.place!, label: r.name }))
    // the marks of choice groups, so a ticked option can be seen too
    for (const r of rows) for (const o of r.place?.options ?? []) {
      const m = o.mark ? pv.places[o.mark] : undefined
      if (m?.box) boxes.push({ cid: o.mark!, place: m, label: `${r.name}: ${o.text}` })
    }
    for (const page of pv.pages) papers.append(paperPage(page, boxes))
    papers.addEventListener('click', (e) => {
      const t = (e.target as HTMLElement).closest<HTMLElement>('.fp-box')
      if (!t) return
      const cid = t.dataset.cid ?? ''
      const fid = joined?.fieldOf.get(cid)
      const btn = list.querySelector<HTMLButtonElement>(`[data-cid="${cid}"]`) ?? (fid ? list.querySelector<HTMLButtonElement>(`[data-where="${fid}"]`) : null)
      btn?.focus()
      btn?.click()
    })
    const toggle = h('input', { type: 'checkbox', id: 'fp-where-toggle', checked: true })
    toggle.addEventListener('change', () => papers.classList.toggle('fp-boxes-off', !toggle.checked))
    body.append(h('p', {}, toggle, h('label', { for: 'fp-where-toggle' }, ' ' + FP.whereToggle)),
      h('div', { class: 'fp-where-grid' }, h('div', {}, list, live), papers))
  }

  const ready = pending.then((raw) => { pv = parsePreview(raw); paint() }, () => { pv = null; paint() })
  return { el, ready, preview: () => pv, joined: () => joined }
}
