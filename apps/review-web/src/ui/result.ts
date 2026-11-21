// The answer of the service as a page: summary, fields of the matter first, warnings in plain words, standard
// sections collapsed, the form JSON. Every text of ours goes through t(); the form's own labels and the Polish
// `detail` of the service are shown as they are, in elements marked lang="pl".
import { t } from '../lib/i18n'
import { buildView, type FieldRow, type ViewModel } from '../lib/model'
import { groupWarnings, placeOf, type HeaderWarnings, type RawWarning } from '../lib/warnings'
import type { Converted, Problem } from '../lib/api'
import { h } from './dom'

const PL = { lang: 'pl' }

function fieldItem(r: FieldRow): HTMLElement {
  const meta: (Node | string)[] = []
  if (r.page !== null) meta.push(h('span', { class: 'chip' }, t('matter.page', { page: r.page })))
  else if (r.anchor) meta.push(h('span', { class: 'chip' }, r.anchor))
  if (r.required) meta.push(h('span', { class: 'chip chip-req' }, t('matter.required')))
  meta.push(h('span', { class: 'chip chip-type' }, r.type))
  const body: (Node | null)[] = [
    h('div', { class: 'field-title', ...PL }, r.title),
    h('div', { class: 'chips', 'aria-label': t('matter.type') }, ...meta)
  ]
  if (r.section) body.push(h('div', { class: 'muted', ...PL }, t('matter.section', { name: r.section })))
  if (r.options.length) body.push(h('div', { class: 'muted', ...PL }, t('matter.options', { list: r.options.join('; ') })))
  if (r.origin === 'paper' || r.origin === 'reviewer') {
    body.push(
      r.quote
        ? h('figure', { class: 'snippet' }, h('figcaption', {}, t('matter.snippet')), h('blockquote', PL, r.quote))
        : h('p', { class: 'muted' }, t('matter.noSource'))
    )
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
    w.detail ? h('span', { class: 'detail', ...PL }, ' ' + w.detail) : null)
}

export function warningsSection(view: ViewModel, header: HeaderWarnings | null): HTMLElement {
  const sec = h('section', { 'aria-labelledby': 'h-warnings' }, h('h2', { id: 'h-warnings' }, t('warnings.heading')))
  const total = view.hasSidecar ? view.warnings.length : header?.count ?? 0
  if (header) {
    const shown = [header.count !== null ? String(header.count) : '', ...header.codes].filter(Boolean).join(', ')
    sec.append(h('p', { class: 'muted' }, t('warnings.header', { value: shown || header.raw })))
  } else {
    sec.append(h('p', { class: 'muted' }, t('warnings.headerNone')))
  }
  if (view.hasSidecar && view.warnings.length === 0) {
    sec.append(h('p', {}, t('warnings.none')))
    return sec
  }
  if (!view.hasSidecar && total === 0 && !header?.codes.length) {
    sec.append(h('p', {}, t('warnings.none')))
    return sec
  }
  const groups = view.hasSidecar
    ? groupWarnings(view.warnings)
    : groupWarnings((header?.codes ?? []).map((code) => ({ code })))
  for (const g of groups) {
    const explain = g.known ? t(g.key) : t('warnings.unknown')
    const places = g.items.filter((w) => w.detail || placeOf(w) !== null)
    sec.append(h('article', { class: 'warning' },
      h('h3', {}, explain),
      h('p', { class: 'muted' }, h('code', {}, g.code), view.hasSidecar ? ' · ' + t('warnings.times', { n: g.items.length }) : ''),
      places.length
        ? h('details', {}, h('summary', {}, t('warnings.detail')), h('ul', { class: 'plain' }, ...places.map(warningDetail)))
        : null))
  }
  return sec
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
  return h('section', { 'aria-labelledby': 'h-json' },
    h('h2', { id: 'h-json' }, t('json.heading')),
    h('p', { class: 'muted' }, t('json.intro')),
    h('p', { class: res.hash === 'bad' ? 'bad' : 'muted' }, t(hashKey, { hash: (res.formSha256 ?? '').slice(0, 12) + '…' })),
    h('p', { class: 'muted' }, t('json.bytes', { n: res.formBytes.length })),
    h('div', { class: 'actions' }, copy, link),
    h('p', {}, pretty, h('label', { for: 'json-pretty' }, ' ' + t('json.pretty'))),
    status,
    area)
}

export function renderConverted(res: Converted): HTMLElement {
  const view = buildView(res.form, res.sidecar)
  const root = h('div', { class: 'result' })
  root.append(h('h2', { id: 'h-done', tabindex: -1, class: 'result-title' }, t('status.done', { title: view.title })))
  root.querySelector('#h-done')?.setAttribute('lang', 'pl')
  if (!view.hasSidecar) {
    root.append(h('section', { class: 'notice', role: 'note', 'aria-labelledby': 'h-nosidecar' },
      h('h2', { id: 'h-nosidecar' }, t('sidecar.missing.heading')),
      h('p', {}, t('sidecar.missing.body'))))
  }
  root.append(summary(view, res.header?.count ?? null))
  if (view.hasSidecar) {
    root.append(h('section', { 'aria-labelledby': 'h-matter' },
      h('h2', { id: 'h-matter' }, t('matter.heading')),
      h('p', { class: 'muted' }, t('matter.intro')),
      view.matter.length ? fieldList(view.matter) : h('p', {}, t('matter.empty'))))
  }
  root.append(warningsSection(view, res.header))
  if (view.hasSidecar && view.standardCount) {
    const details = h('details', { class: 'standard' },
      h('summary', {}, t('standard.summary', { n: view.standardCount })),
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

export function renderProblem(p: Problem): HTMLElement {
  const key = 'problem.' + p.code
  const known = t(key) !== key
  const reason = known ? t(key) : p.code === 'HTTP' ? t('problem.HTTP') : t('problem.UNKNOWN')
  return h('div', { class: 'result' },
    h('section', { class: 'error', role: 'alert', 'aria-labelledby': 'h-error' },
      h('h2', { id: 'h-error', tabindex: -1 }, t('error.heading')),
      h('p', { class: 'reason' }, t('error.reason') + ': ' + reason),
      p.detail ? h('p', { class: 'muted', ...PL }, t('error.serverDetail') + ': ' + p.detail) : null,
      h('p', { class: 'muted' }, t('error.code', { code: p.code }) + (p.status ? ' · ' + t('error.status', { status: p.status }) : '')),
      h('p', {}, t('error.retry'))))
}
