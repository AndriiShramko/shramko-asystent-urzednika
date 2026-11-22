// The answer of the service as a page: a headline that says plainly how much was read from the form, fields from
// the form first, remarks for the clerk in one calm collapsed block, standard sections collapsed, the form JSON.
// Every text of ours goes through t(); the form's own labels are shown as they are, in elements marked lang="pl".
// The service's own `detail` of a remark is English today, so it is shown only for codes the page cannot explain,
// inside "Szczegóły techniczne".
import { getLang, hasKey, t, tn } from '../lib/i18n'
import { buildView, type FieldRow, type ViewModel } from '../lib/model'
import { groupWarnings, placeOf, type HeaderWarnings, type RawWarning } from '../lib/warnings'
import { adviceKey, causeOf, chooseHeadline, type Headline } from '../lib/verdict'
import type { Converted, Engine, Problem } from '../lib/api'
import { h } from './dom'

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

function summary(view: ViewModel, headerCount: number | null): HTMLElement {
  const items = [
    t('summary.pages', { n: view.counts.pages }),
    t('summary.fields', { n: view.counts.fields }),
    view.hasSidecar ? t('summary.matter', { n: view.matter.length }) : null,
    view.counts.sourcePages !== null ? t('summary.sourcePages', { n: view.counts.sourcePages }) : null,
    view.hasSidecar || headerCount !== null ? t('summary.warnings', { n: view.hasSidecar ? view.warnings.length : (headerCount ?? 0) }) : null
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

/** Remarks for the clerk: one collapsed block with the count, a human sentence each, the code small and grey. */
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
    h('summary', { id: 'h-warnings' }, t('warnings.heading', { n: total })),
    h('p', { class: 'muted' }, t('warnings.intro')))
  for (const g of groups) {
    const explain = g.known ? t(g.key) : t('warnings.unknown')
    const pages = [...new Set(g.items.map(placeOf).filter((p): p is number => p !== null))].sort((a, b) => a - b)
    const where: string[] = []
    if (view.hasSidecar) where.push(tn('warnings.times', g.items.length))
    if (pages.length) where.push(tn('warnings.pages', pages.length, { list: pages.join(', ') }))
    const withText = g.known ? [] : g.items.filter((w) => w.detail || placeOf(w) !== null)
    details.append(h('article', { class: 'remark' },
      h('h3', {}, explain),
      h('p', { class: 'code-line' },
        where.length ? '(' + where.join('; ') + ') · ' : '',
        t('warnings.code', { code: '' }), h('code', { class: 'code' }, g.code)),
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

/** The engine of this conversion as a band with words: the label, the token of the header, what it means. The
 * colour (grey, green, amber) only repeats what the text already says. */
export function engineBadge(engine: Engine | null): HTMLElement {
  const kind = engine === 'rules+model' ? 'model' : engine === 'rules-fallback' ? 'fallback' : engine === 'rules' ? 'rules' : 'unknown'
  return h('p', { id: 'engine', class: `engine engine-${kind}`, 'data-engine': engine ?? 'unknown' },
    h('span', { class: 'engine-label' }, t('engine.label')), ' ',
    engine ? h('code', { class: 'engine-token' }, engine) : null, engine ? ' — ' : null,
    h('span', { class: 'engine-meaning' }, t(`engine.${kind}`)))
}

/** The words of the headline: a success only when fields were read from the form; never "Gotowe". */
export function headlineText(hl: Headline): string {
  const fields = tn('count.fields', hl.fields)
  const sections = tn('count.sectionsIn', hl.sections)
  if (hl.kind === 'partial') {
    return t('result.partial', { paper: tn('count.fields', hl.paper ?? 0), standard: tn('count.stdFields', hl.standard) })
  }
  return t(hl.kind === 'ok' ? 'result.ok' : 'result.neutral', { fields, sections })
}

/** The status line (aria-live) after a conversion: names the form, says "częściowo" when nothing was read. */
export function doneStatus(res: Converted): string {
  const view = buildView(res.form, res.sidecar)
  const hl = chooseHeadline(view, res.header)
  return t(hl.kind === 'partial' ? 'status.partial' : 'status.done', { title: view.title })
}

export function renderConverted(res: Converted): HTMLElement {
  const view = buildView(res.form, res.sidecar)
  const hl = chooseHeadline(view, res.header)
  const root = h('div', { class: 'result' })
  root.append(h('h2', { id: 'h-done', tabindex: -1, class: `result-title result-${hl.kind}`, 'data-kind': hl.kind },
    h('span', { class: 'headline' }, headlineText(hl)),
    h('span', { class: 'form-name' }, t('result.formName') + ' ', h('span', PL, '„' + view.title + '”'))))
  root.append(engineBadge(res.engine))
  if (!view.hasSidecar) {
    root.append(h('section', { class: 'notice', role: 'note', 'aria-labelledby': 'h-nosidecar' },
      h('h2', { id: 'h-nosidecar' }, t('sidecar.missing.heading')),
      h('p', {}, t('sidecar.missing.body'))))
  }
  root.append(summary(view, res.header?.count ?? null))
  if (view.hasSidecar) {
    const noSource = view.matter.filter((r) => !r.quote).length
    root.append(h('section', { 'aria-labelledby': 'h-matter' },
      h('h2', { id: 'h-matter' }, t('matter.heading')),
      h('p', { class: 'muted' }, t('matter.intro')),
      view.matter.length && noSource ? h('p', { class: 'muted', id: 'matter-nosource' }, t('matter.noSource', { n: noSource, total: view.matter.length })) : null,
      view.matter.length ? fieldList(view.matter) : h('p', {}, t('matter.empty'))))
  }
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

/** One red block: what failed, why, what to do (chosen by the code's cause), the code small and grey, one button. */
export function renderProblem(p: Problem, actions: ProblemActions = {}): HTMLElement {
  const key = 'problem.' + p.code
  const known = hasKey('pl', key)
  const reason = known ? t(key) : p.code === 'HTTP' ? t('problem.HTTP') : t('problem.UNKNOWN')
  const advice = t(adviceKey(p.code, (k) => hasKey('pl', k)), { code: p.code })
  const cause = causeOf(p.code)
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
