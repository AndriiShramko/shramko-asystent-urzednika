// Step 6: print. On the original blank (PDF inputs, where the preview gave page pictures and boxes): one sheet per
// page in pt, the page picture as an <img> (it prints even with "background graphics" off), each value placed at
// its field's place. Values with no place go to an extra page. Inputs without page pictures print the electronic
// form as a list. Printing is the browser's own print; the screen UI is hidden by @media print.
import { h, clear } from './dom'
import { INPUT_TYPES, nameOf, type ENode } from '../lib/fp/form'
import { fullAddress, peselOf, type DemoRecord } from '../lib/fp/family'
import { layoutMark, layoutText, standardPrints, type Attr, type Glyph, type Place } from '../lib/fp/places'
import { FP } from '../lib/fp/text'
import type { EForm } from './eform'
import type { Where } from './where'

const norm = (s: string): string => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ł/g, 'l').replace(/\s+/g, ' ').trim()

/** A date of the form (yyyy-mm-dd) as it is written on Polish paper (dd.mm.yyyy); other text unchanged. */
export function paperText(n: ENode, text: string): string {
  const m = n.type === 'DATEPICKER' ? text.match(/^(\d{4})-(\d{2})-(\d{2})$/) : null
  return m ? `${m[3]}.${m[2]}.${m[1]}` : text
}

const KEYS: Record<Exclude<Attr, 'fullname' | 'fullname_rev' | 'address'>, string[]> = {
  name: ['PESEL.name', 'MLPZ.name'], surname: ['PESEL.surname', 'MLPZ.surname'], pesel: ['PESEL.pesel', 'MLPZ.pesel'],
  postCode: ['MLPZ.postCode'], street: ['MLPZ.street'], building: ['MLPZ.building'], apartment: ['MLPZ.apartment'],
  place: ['MLPZ.place'], phone: ['MLPZ.phoneNumber'], email: ['MLPZ.email']
}
const RECORD: Record<keyof typeof KEYS, (r: DemoRecord) => string> = {
  name: (r) => r.MLPZ.name ?? '', surname: (r) => r.MLPZ.surname ?? '', pesel: peselOf, postCode: (r) => r.MLPZ.postCode ?? '',
  street: (r) => r.MLPZ.street ?? '', building: (r) => r.MLPZ.building ?? '', apartment: (r) => r.MLPZ.apartment ?? '',
  place: (r) => r.MLPZ.place ?? '', phone: (r) => r.MLPZ.phoneNumber ?? '', email: (r) => r.MLPZ.email ?? ''
}

/** The value of a person's attribute: from the form field that carries its partner key (so a clerk's edit prints),
 * else from the loaded demo record when the form has no such field. Returns the field ids it read. */
function attrValue(ef: EForm, attr: Attr, record: DemoRecord | null): { text: string; ids: string[] } {
  if (attr === 'fullname' || attr === 'fullname_rev') {
    const a = attrValue(ef, 'name', record); const b = attrValue(ef, 'surname', record)
    const parts = attr === 'fullname' ? [a.text, b.text] : [b.text, a.text]
    return { text: parts.filter(Boolean).join(' '), ids: [...a.ids, ...b.ids] }
  }
  if (attr === 'address') {
    const parts = (['street', 'building', 'apartment', 'postCode', 'place'] as const).map((k) => attrValue(ef, k, record))
    const [st, bu, ap, pc, pl] = parts.map((p) => p.text)
    const text = st || bu ? `ul. ${st} ${bu}${ap ? ' m. ' + ap : ''}${pc || pl ? ', ' + [pc, pl].filter(Boolean).join(' ') : ''}`.trim()
      : record ? fullAddress(record) : ''
    return { text, ids: parts.flatMap((p) => p.ids) }
  }
  const keys = KEYS[attr]
  const node = ef.inputs().find((n) => typeof n.defaultValue === 'string' && n.defaultValueType === 'EXTERNAL_SYSTEM' && keys.includes(n.defaultValue))
    ?? (attr === 'pesel' ? ef.inputs().find((n) => n.validation.includes('PESEL')) : undefined)
  if (node) return { text: ef.isVisible(node) ? ef.textOf(node.id) : '', ids: [node.id] }
  return { text: record ? RECORD[attr](record) : '', ids: [] }
}

export interface Sheets { sheets: HTMLElement[]; extra: { name: string; value: string }[]; overflow: string[]; placed: number }

function glyphEl(g: Glyph): HTMLElement {
  const style = [`left:${g.left.toFixed(2)}pt`, `top:${g.top.toFixed(2)}pt`, `font-size:${g.size}pt`]
  if (g.width !== undefined) style.push(`width:${g.width.toFixed(2)}pt`)
  if (g.center) style.push('text-align:center')
  return h('div', { class: 'fp-glyph', style: style.join(';') }, g.text)
}

/** The sheets of the print on the original, or null when the input has no page pictures. */
export function buildSheets(ef: EForm, where: Where, record: DemoRecord | null): Sheets | null {
  const pv = where.preview()
  const j = where.joined()
  if (!pv || !j || !pv.pages.length) return null
  const byPage = new Map<number, Glyph[]>()
  const add = (page: number, g: Glyph[]): void => { byPage.set(page, [...(byPage.get(page) ?? []), ...g]) }
  const used = new Set<string>()
  const overflow: string[] = []
  let placed = 0

  for (const [fid, { place }] of j.byField) {
    const n = ef.model.byId.get(fid)
    if (!n || !ef.isVisible(n) || !place.box) continue
    const v = ef.get(fid)
    const chosen = Array.isArray(v) ? v : typeof v === 'string' && v ? [v] : []
    if (!chosen.length) continue
    if (place.options?.length && (n.type === 'RADIO' || n.type === 'CHECKBOX' || n.type === 'SELECT')) {
      let any = false
      for (const c of chosen) {
        const o = place.options.find((op) => norm(op.text) === norm(c)) ?? place.options.find((op) => norm(op.text).startsWith(norm(c)) || norm(c).startsWith(norm(op.text)))
        const mark: Place | undefined = o?.mark ? pv.places[o.mark] : undefined
        const g = mark ? layoutMark(mark) : null
        if (g && mark) { add(mark.page, [g]); any = true }
      }
      if (any) { used.add(fid); placed++ }
      continue
    }
    if (n.type === 'CHECKBOX' && !n.options.length) {
      const g = layoutMark(place)
      if (g) { add(place.page, [g]); used.add(fid); placed++ }
      continue
    }
    let text = paperText(n, ef.textOf(fid))
    if (place.kind === 'comb' && place.cells && text.replace(/\s/g, '').length > place.cells) text = text.replace(/[.\-\s]/g, '')
    const r = layoutText(place, text)
    if (!r.fits) overflow.push(nameOf(n))
    add(place.page, r.glyphs); used.add(fid); placed++
  }

  for (const s of j.standard) {
    if (!s.attr || !standardPrints(s.section) || !s.place.box) continue
    const { text, ids } = attrValue(ef, s.attr, record)
    if (!text) continue
    const r = layoutText(s.place, text)
    if (!r.fits) overflow.push(s.place.label ?? s.attr)
    add(s.place.page, r.glyphs)
    for (const id of ids) used.add(id)
    placed++
  }

  const sheets = pv.pages.map((p) => {
    const sheet = h('section', { class: 'fp-sheet', 'data-page': p.n,
      style: `width:${Math.min(p.w, 595).toFixed(2)}pt;height:${Math.min(p.h, 841.5).toFixed(2)}pt` })
    if (p.img) sheet.append(h('img', { class: 'fp-sheet-img', alt: '', src: `data:${p.img.media_type};base64,${p.img.data}`,
      style: `width:${p.w}pt;height:${p.h}pt` }))
    for (const g of byPage.get(p.n) ?? []) sheet.append(glyphEl(g))
    sheet.append(h('div', { class: 'fp-sheet-demo', style: `left:20pt;top:${(Math.min(p.h, 841.5) - 16).toFixed(2)}pt` }, FP.banner))
    return sheet
  })

  const extra: Sheets['extra'] = []
  for (const n of ef.inputs()) {
    if (n.type === 'FILE_UPLOADER' || used.has(n.id) || !ef.isVisible(n)) continue
    const text = ef.textOf(n.id)
    if (text.trim()) extra.push({ name: nameOf(n), value: paperText(n, text) })
  }
  if (extra.length) {
    sheets.push(h('section', { class: 'fp-sheet fp-extra', style: 'width:595pt;height:841.5pt' },
      h('div', { class: 'fp-extra-body' },
        h('h1', {}, ef.model.title),
        h('p', {}, FP.noPlace(extra.length)),
        h('p', { class: 'fp-extra-demo' }, FP.banner),
        h('dl', {}, ...extra.flatMap((e) => [h('dt', {}, e.name), h('dd', {}, e.value)])))))
  }
  return { sheets, extra, overflow, placed }
}

/** The electronic form as a printable list: visible sections and fields with their values. */
export function buildEformPrint(ef: EForm): HTMLElement {
  const root = h('section', { class: 'fp-eprint' }, h('h1', {}, ef.model.title), h('p', { class: 'fp-extra-demo' }, FP.banner))
  const walk = (n: ENode, into: HTMLElement): void => {
    if (!ef.isVisible(n)) return
    if (n.children.length || n.type === 'SECTION' || n.type === 'REPEATING_SECTION') {
      const box = h('div', { class: 'fp-eprint-sec' }, h('h3', {}, nameOf(n)))
      for (const c of n.children) walk(c, box)
      into.append(box)
    } else if (INPUT_TYPES.has(n.type) && n.type !== 'FILE_UPLOADER') {
      into.append(h('p', {}, h('strong', {}, nameOf(n) + ': '), paperText(n, ef.textOf(n.id)) || '—'))
    }
  }
  for (const tab of ef.model.tabs) {
    const sec = h('div', {}, h('h2', {}, tab.title))
    for (const n of tab.nodes) walk(n, sec)
    root.append(sec)
  }
  return root
}

export interface PrintStep { el: HTMLElement; refresh(): void }

export function renderPrint(ef: EForm, where: Where, record: () => DemoRecord | null): PrintStep {
  const note = h('p', { id: 'fp-print-note', class: 'muted' })
  const extraNote = h('p', { id: 'fp-print-extra' })
  const preview = h('div', { id: 'fp-print-preview', class: 'fp-print-preview', hidden: true })
  const pvBtn = h('button', { type: 'button', class: 'btn', id: 'fp-print-preview-btn', disabled: true, 'aria-expanded': 'false', 'aria-controls': 'fp-print-preview' }, FP.printPreview)
  const sheetBtn = h('button', { type: 'button', class: 'btn btn-main', id: 'fp-print-sheet', disabled: true }, FP.printSheet)
  const eBtn = h('button', { type: 'button', class: 'btn', id: 'fp-print-eform' }, FP.printEform)

  function fillNotes(s: Sheets | null): void {
    extraNote.textContent = s && s.extra.length ? FP.noPlace(s.extra.length) : ''
  }

  function showPreview(): void {
    const s = buildSheets(ef, where, record())
    clear(preview)
    fillNotes(s)
    if (s) preview.append(...s.sheets)
  }

  function doPrint(content: HTMLElement[]): void {
    document.getElementById('fp-print')?.remove()
    const area = h('div', { id: 'fp-print', lang: 'pl' }, ...content)
    document.body.append(area)
    document.body.classList.add('fp-printing')
    const done = (): void => { document.body.classList.remove('fp-printing'); window.removeEventListener('afterprint', done) }
    window.addEventListener('afterprint', done)
    if (typeof window.print === 'function') { try { window.print() } catch { /* a test page without print */ } }
  }

  pvBtn.addEventListener('click', () => {
    const open = preview.hidden
    if (open) showPreview()
    preview.hidden = !open
    pvBtn.setAttribute('aria-expanded', String(open))
  })
  sheetBtn.addEventListener('click', () => {
    const s = buildSheets(ef, where, record())
    fillNotes(s)
    if (s) doPrint(s.sheets)
  })
  eBtn.addEventListener('click', () => doPrint([buildEformPrint(ef)]))

  function refresh(): void {
    const pv = where.preview()
    const geometry = !!pv && pv.pages.length > 0 && !!where.joined()
    pvBtn.disabled = !geometry
    sheetBtn.disabled = !geometry
    note.textContent = geometry ? '' : pv ? FP.noPageImage : FP.previewMissing
    if (!preview.hidden) showPreview()
  }
  void where.ready.then(refresh)
  ef.onChange(() => { if (!preview.hidden) showPreview() })

  const el = h('section', { id: 'fp-print-step', class: 'fp-step', 'aria-labelledby': 'h-print' },
    h('h2', { id: 'h-print' }, FP.step(6), ' ', FP.printHeading),
    h('p', {}, FP.printHint),
    note,
    h('div', { class: 'actions' }, pvBtn, sheetBtn, eBtn),
    extraNote,
    preview)
  refresh()
  return { el, refresh }
}
