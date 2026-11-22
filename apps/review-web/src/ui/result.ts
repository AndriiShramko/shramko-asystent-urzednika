// The answer of the service as a page: a headline that says plainly how much was read from the form, fields from
// the form first, remarks for the clerk in one calm collapsed block, standard sections collapsed, the form JSON.
// Every text of ours goes through t(); the form's own labels are shown as they are, in elements marked lang="pl".
// The service's own `detail` of a remark is English today, so it is shown only for codes the page cannot explain,
// inside "Szczegóły techniczne".
import { getLang, hasKey, t, tn } from '../lib/i18n'
import { buildView, type FieldRow, type ViewModel } from '../lib/model'
import { groupWarnings, placeOf, type HeaderWarnings, type RawWarning } from '../lib/warnings'
import { adviceKey, causeOf, chooseHeadline, formatsText, titleLooksRead, type Headline } from '../lib/verdict'
import type { Converted, Problem } from '../lib/api'
import { h } from './dom'
import { readDictionaries } from '../lib/dictionaries'
import { dictionariesSection } from './dictionaries'

const PL = { lang: 'pl' }

/** The field type in words; a type the page has no word for stays as its code, small and grey. */
function typeChip(type: string): HTMLElement {
  const key = 'type.' + type
  return hasKey(getLang(), key)
    ? h('span', { class: 'chip chip-type' }, t(key))
    : h('span', { class: 'chip chip-type' }, h('code', { class: 'code' }, type))
}

function fieldItem(r: FieldRow): HTMLElement {
  const meta: (Node | string)[] = []
  if (r.page !== null) meta.push(h('span', { class: 'chip' }, t('matter.page', { page: r.page })))
  else if (r.anchor) meta.push(h('span', { class: 'chip' }, r.anchor))
  if (r.required) meta.push(h('span', { class: 'chip chip-req' }, t('matter.required')))
  if (r.type) meta.push(typeChip(r.type))
  const body: (Node | null)[] = [
    h('div', { class: 'field-title', ...PL }, r.title),
    h('div', { class: 'chips', 'aria-label': t('matter.type') }, ...meta)
  ]
  if (r.section) body.push(h('div', { class: 'muted' }, t('matter.section', { name: '' }), h('span', PL, r.section)))
  if (r.options.length) body.push(h('div', { class: 'muted' }, t('matter.options', { list: '' }), h('span', PL, r.options.join('; '))))
  if ((r.origin === 'paper' || r.origin === 'reviewer') && r.quote) {
    body.push(h('figure', { class: 'snippet' }, h('figcaption', {}, t('matter.snippet')), h('blockquote', PL, r.quote)))
  }
  return h('li', { class: 'field' }, ...body)
}

function fieldList(rows: FieldRow[]): HTMLElement {
  return h('ul', { class: 'fields' }, ...rows.map(fieldItem))
}

/** "2 rodzaje (2031 miejsc)": kinds first, so thousands of one remark read as one kind. */
function remarksCountText(kinds: number, total: number): string {
  return t('warnings.kindsTotal', { kinds: tn('warnings.kinds', kinds), places: tn('warnings.times', total) })
}

function summary(view: ViewModel, header: HeaderWarnings | null): HTMLElement {
  const headerCount = header?.count ?? null
  const kinds = view.hasSidecar ? groupWarnings(view.warnings).length : (header?.codes.length ?? 0)
  const total = view.hasSidecar ? view.warnings.length : (headerCount ?? 0)
  const items = [
    t('summary.pages', { n: view.counts.pages }),
    t('summary.fields', { n: view.counts.fields }),
    view.hasSidecar ? t('summary.matter', { n: view.matter.length }) : null,
    view.counts.sourcePages !== null ? t('summary.sourcePages', { n: view.counts.sourcePages }) : null,
    view.hasSidecar || headerCount !== null
      ? t('summary.warnings', { n: total > 0 && kinds > 0 ? remarksCountText(kinds, total) : String(total) })
      : null
  ].filter((x): x is string => x !== null)
  return h('section', { 'aria-labelledby': 'h-summary' },
    h('h2', { id: 'h-summary' }, t('summary.heading')),
    h('ul', { class: 'plain' }, ...items.map((x) => h('li', {}, x))))
}

function warningDetail(w: RawWarning): HTMLElement {
  const place = placeOf(w)
  return h('li', {},
    place !== null ? h('span', { class: 'chip' }, t('matter.page', { page: place })) : null,
    w.detail ? h('span', { class: 'detail' }, ' ' + w.detail) : null)
}

/** How many remarks there are: every occurrence, not every kind. */
export function remarkCount(view: ViewModel, header: HeaderWarnings | null): number {
  if (view.hasSidecar) return view.warnings.length
  return header?.count ?? header?.codes.length ?? 0
}

/** How many places of one kind are listed by name; the rest is a count. */
export const PLACES_SHOWN = 5

/** Where one remark points, in words a clerk can find: the page and the cell or anchor; null when it says neither. */
function placeText(w: RawWarning): string | null {
  const parts: string[] = []
  const page = placeOf(w)
  if (page !== null) parts.push(t('matter.page', { page }))
  if (typeof w.anchor === 'string' && w.anchor.trim()) parts.push(w.anchor.trim())
  return parts.length ? parts.join(', ') : null
}

/** INPUT_NOTE: the service's guard writes its own Polish sentence about the uploaded file (the extension disagreed
 * with the content, a file without an extension, a corrected file name, an image read in a reduced size); each one
 * is shown once, as the service wrote it. */
function noteList(items: readonly RawWarning[]): HTMLElement | null {
  const notes = [...new Set(items.map((w) => (typeof w.detail === 'string' ? w.detail.trim() : '')).filter(Boolean))]
  return notes.length
    ? h('div', { class: 'places' }, h('p', { class: 'muted' }, t('warnings.noteText')), h('ul', { class: 'plain', ...PL }, ...notes.map((n) => h('li', {}, n))))
    : null
}

/** Remarks for the clerk: one collapsed block counted in kinds (2044 remarks of one sheet are mostly one kind), each
 * kind collapsed too with its own count, a human sentence, the first few places and the code small and grey. */
export function warningsSection(view: ViewModel, header: HeaderWarnings | null): HTMLElement {
  const total = remarkCount(view, header)
  const groups = view.hasSidecar
    ? groupWarnings(view.warnings)
    : groupWarnings((header?.codes ?? []).map((code) => ({ code })))
  if (total === 0 && groups.length === 0) {
    return h('section', { class: 'remarks', 'aria-labelledby': 'h-warnings' },
      h('p', { id: 'h-warnings', class: 'muted' }, t('warnings.none')))
  }
  const details = h('details', { class: 'remarks-box' },
    h('summary', { id: 'h-warnings' }, t('warnings.heading', { n: tn('warnings.kinds', groups.length) })),
    h('p', { class: 'muted' }, t('warnings.intro')))
  for (const g of groups) {
    const explain = g.known ? t(g.key) : t('warnings.unknown')
    const pages = [...new Set(g.items.map(placeOf).filter((p): p is number => p !== null))].sort((a, b) => a - b)
    const where: string[] = []
    if (view.hasSidecar) where.push(tn('warnings.times', g.items.length))
    if (pages.length) where.push(tn('warnings.pages', pages.length, { list: pages.join(', ') }))
    const withText = g.known ? [] : g.items.filter((w) => w.detail || placeOf(w) !== null)
    // Places named beyond the page (a cell, an anchor), each once; pages alone are already on the code line.
    const places = g.known && g.items.some((w) => typeof w.anchor === 'string' && w.anchor.trim())
      ? [...new Set(g.items.map(placeText).filter((p): p is string => p !== null))]
      : []
    const shown = places.slice(0, PLACES_SHOWN)
    const rest = places.length - shown.length
    details.append(h('details', { class: 'remark' },
      h('summary', {},
        h('h3', {}, explain),
        h('p', { class: 'code-line' },
          where.length ? '(' + where.join('; ') + ') · ' : '',
          t('warnings.code', { code: '' }), h('code', { class: 'code' }, g.code))),
      shown.length
        ? h('div', { class: 'places' },
          h('p', { class: 'muted' }, t('warnings.firstPlaces')),
          h('ul', { class: 'plain' }, ...shown.map((p) => h('li', {}, p))),
          rest > 0 ? h('p', { class: 'muted' }, t('warnings.more', { places: tn('warnings.times', rest) })) : null)
        : null,
      g.code === 'INPUT_NOTE' ? noteList(g.items) : null,
      withText.length
        ? h('details', { class: 'tech' }, h('summary', {}, t('warnings.detail')), h('ul', { class: 'plain' }, ...withText.map(warningDetail)))
        : null))
  }
  return h('section', { class: 'remarks', 'aria-labelledby': 'h-warnings' }, details)
}

function jsonSection(res: Converted): HTMLElement {
  const area = h('pre', { class: 'json', id: 'json-text', tabindex: 0, 'aria-label': t('json.text') }, res.formText)
  const status = h('p', { role: 'status', class: 'muted', id: 'json-status' })
  const copy = h('button', { type: 'button', class: 'btn' }, t('json.copy'))
  copy.addEventListener('click', () => {
    // Always the exact text of the answer, whatever the display below does.
    const done = (ok: boolean): void => { status.textContent = t(ok ? 'json.copied' : 'json.copyFailed') }
    if (navigator.clipboard?.writeText) navigator.clipboard.writeText(res.formText).then(() => done(true), () => done(false))
    else done(false)
  })
  const link = h('a', { class: 'btn', href: '#', download: 'form.json' }, t('json.download'))
  link.addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([res.formBytes as BlobPart], { type: 'application/json' }))
    link.setAttribute('href', url)
    setTimeout(() => URL.revokeObjectURL(url), 10000)
  })
  const pretty = h('input', { type: 'checkbox', id: 'json-pretty' })
  pretty.addEventListener('change', () => {
    area.textContent = pretty.checked ? JSON.stringify(res.form, null, 2) : res.formText
  })
  const hashKey = res.hash === 'ok' ? 'json.hash.ok' : res.hash === 'bad' ? 'json.hash.bad' : 'json.hash.unchecked'
  const hashLine = h('p', { class: res.hash === 'bad' ? 'bad' : 'muted' }, t(hashKey, { hash: (res.formSha256 ?? '').slice(0, 12) + '…' }))
  const tech = h('details', { class: 'tech' }, h('summary', {}, t('json.tech')),
    res.hash === 'bad' ? null : hashLine,
    h('p', { class: 'muted' }, t('json.bytes', { n: res.formBytes.length })))
  return h('section', { 'aria-labelledby': 'h-json' },
    h('h2', { id: 'h-json' }, t('json.heading')),
    h('p', { class: 'muted' }, t('json.intro')),
    res.hash === 'bad' ? hashLine : null,
    h('div', { class: 'actions' }, copy, link),
    h('p', {}, pretty, h('label', { for: 'json-pretty' }, ' ' + t('json.pretty'))),
    tech,
    status,
    area)
}

/** The words of the headline: a success only when fields were read from the form; never "Gotowe". */
export function headlineText(hl: Headline): string {
  const fields = tn('count.fields', hl.fields)
  const sections = tn('count.sectionsIn', hl.sections)
  if (hl.paper === null) {
    // no report: the origin of the fields is unknown, so the two numbers cannot be given
    return hl.kind === 'partial' ? t('result.partialNoReport', { fields, sections }) : t('result.neutral', { fields, sections })
  }
  // with the report both numbers are always on the line: how much came from the paper, how much is standard
  const counts = { fields, sections, paper: hl.paper, standard: hl.standard }
  if (hl.kind === 'partial') return t('result.partial.' + (hl.why ?? 'none'), counts)
  return t('result.ok', counts)
}

/** The title as the status line names it: quoted, or "bez odczytanego tytułu" when OCR gave noise. */
function titleForStatus(title: string): string {
  return titleLooksRead(title) ? '„' + title + '”' : t('status.noTitle')
}

/** The status line (aria-live) after a conversion: names the form, says "częściowo" when the paper gave little. */
export function doneStatus(res: Converted): string {
  const view = buildView(res.form, res.sidecar)
  const hl = chooseHeadline(view, res.header)
  const title = titleForStatus(view.title)
  if (hl.kind !== 'partial') return t('status.done', { title })
  if (hl.why === 'few') return t('status.few', { title, paper: tn('count.fields', hl.paper ?? 0) })
  return t('status.partial', { title })
}

/** The title line of the headline: the title read from the paper, or a plain "not read" with the raw OCR text small
 * and grey (a photo of a map gave "zdnia"). */
function formName(title: string): HTMLElement {
  if (titleLooksRead(title)) {
    return h('span', { class: 'form-name' }, t('result.formName') + ' ', h('span', PL, '„' + title + '”'))
  }
  return h('span', { class: 'form-name' }, t('result.titleNotRead'),
    title.trim() ? h('span', { class: 'title-raw' }, ' ' + t('result.titleRaw') + ' ', h('span', PL, '„' + title.trim() + '”')) : null)
}

export function renderConverted(res: Converted): HTMLElement {
  const view = buildView(res.form, res.sidecar)
  const hl = chooseHeadline(view, res.header)
  const root = h('div', { class: 'result' })
  root.append(h('h2', { id: 'h-done', tabindex: -1, class: `result-title result-${hl.kind}`, 'data-kind': hl.kind },
    h('span', { class: 'headline' }, headlineText(hl)),
    formName(view.title)))
  // The engine of this conversion is not repeated here: the badge in the header (#mode) is its one indicator.
  if (!view.hasSidecar) {
    root.append(h('section', { class: 'notice', role: 'note', 'aria-labelledby': 'h-nosidecar' },
      h('h2', { id: 'h-nosidecar' }, t('sidecar.missing.heading')),
      h('p', {}, t('sidecar.missing.body'))))
  }
  root.append(summary(view, res.header))
  if (view.hasSidecar) {
    const noSource = view.matter.filter((r) => !r.quote).length
    const noSourceText = noSource === view.matter.length
      ? t('matter.noSourceAll')
      : t('matter.noSource', { n: noSource, total: view.matter.length })
    root.append(h('section', { 'aria-labelledby': 'h-matter' },
      h('h2', { id: 'h-matter' }, t('matter.heading')),
      h('p', { class: 'muted' }, t('matter.intro')),
      view.matter.length && noSource ? h('p', { class: 'muted', id: 'matter-nosource' }, noSourceText) : null,
      view.matter.length ? fieldList(view.matter) : h('p', {}, t('matter.empty'))))
  }
  const dict = dictionariesSection(readDictionaries(res.sidecar), view.rows, view.hasSidecar)
  if (dict) root.append(dict)
  root.append(warningsSection(view, res.header))
  if (view.hasSidecar && view.standardCount) {
    const details = h('details', { class: 'standard' },
      h('summary', {}, t('standard.summary', { fields: tn('count.fields', view.standardCount) })),
      h('p', { class: 'muted' }, t('standard.intro')))
    for (const [tab, rows] of view.standard) {
      details.append(h('h3', PL, tab), fieldList(rows))
    }
    root.append(h('section', { 'aria-labelledby': 'h-standard' }, h('h2', { id: 'h-standard' }, t('standard.heading')), details))
  }
  if (view.unknown.length) {
    root.append(h('section', { 'aria-labelledby': 'h-unknown' },
      h('h2', { id: 'h-unknown' }, t('unknown.heading')),
      h('p', { class: 'muted' }, t('unknown.body')),
      h('details', { open: true }, h('summary', {}, t('summary.fields', { n: view.unknown.length })), fieldList(view.unknown))))
  }
  root.append(jsonSection(res))
  return root
}

export interface ProblemActions {
  /** send the same file again (service and token faults) */
  retry?: () => void
  /** open the file picker (faults of the file) */
  pickOther?: () => void
}

/** What the page knows besides the service's answer: the size of the file sent and the formats of /status. */
export interface ProblemContext {
  fileSize?: number
  formats?: readonly string[]
}

/** One red block: what failed, why, what to do (chosen by the code's cause), the code small and grey, one button.
 * A refusal of the file for a 0-byte file is called what it is (the service says TYPE_MISMATCH for it today); the
 * EXTENSION advice names the formats of /status when the page has them. */
export function renderProblem(p: Problem, actions: ProblemActions = {}, ctx: ProblemContext = {}): HTMLElement {
  const key = 'problem.' + p.code
  const known = hasKey('pl', key)
  const cause = causeOf(p.code)
  const empty = ctx.fileSize === 0 && cause === 'file'
  const reason = empty ? t('problem.EMPTY_FILE') : known ? t(key) : p.code === 'HTTP' ? t('problem.HTTP') : t('problem.UNKNOWN')
  const advice = empty ? t('todo.EMPTY_FILE')
    : p.code === 'EXTENSION' && ctx.formats?.length ? t('todo.EXTENSION.list', { list: formatsText(ctx.formats) })
      : t(adviceKey(p.code, (k) => hasKey('pl', k)), { code: p.code })
  let button: HTMLElement | null = null
  if (cause === 'file' && actions.pickOther) {
    button = h('button', { type: 'button', class: 'btn', id: 'error-action' }, t('error.other'))
    button.addEventListener('click', actions.pickOther)
  } else if (cause !== 'file' && actions.retry) {
    button = h('button', { type: 'button', class: 'btn', id: 'error-action' }, t('error.again'))
    button.addEventListener('click', actions.retry)
  }
  return h('div', { class: 'result' },
    h('section', { class: 'error', role: 'alert', 'aria-labelledby': 'h-error', 'data-cause': cause },
      h('h2', { id: 'h-error', tabindex: -1 }, t('error.heading')),
      h('p', { class: 'reason' }, reason),
      h('p', { class: 'todo' }, h('strong', {}, t('error.todo') + ': '), advice),
      p.detail ? h('p', { class: 'small' }, t('error.serverDetail') + ': ', h('span', PL, p.detail)) : null,
      h('p', { class: 'code-line' }, t('error.code', { code: p.code }) + (p.status ? ' · ' + t('error.status', { status: p.status }) : '')),
      button))
}
