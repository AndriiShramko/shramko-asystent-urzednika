// The clerk's frame around the two columns (wave 11): the headline in plain words, the strip "Do sprawdzenia" above
// the documents, one final action below them; and, for the jury view, the block that says what was done and by
// what. Rebuilt with the result on a language change; the cards themselves live in the session (clerk-remarks.ts).
import { t, tn } from '../lib/i18n'
import type { ViewModel } from '../lib/model'
import { modeOfEngine, type Headline } from '../lib/verdict'
import { fixOf, type RawWarning } from '../lib/warnings'
import type { Converted } from '../lib/api'
import { h } from './dom'
import { sessionOf, type Session } from './clerk-remarks'

/** The headline for the clerk: ready, read in part, or not read; a scan adds that names may be misread. */
export function clerkHeadline(hl: Headline, view: ViewModel): string {
  const key = hl.kind !== 'partial' ? 'clerk.head.ok' : hl.why === 'none' ? 'clerk.head.none' : 'clerk.head.few'
  const scan = view.warnings.some((w) => w.code === 'OCR_USED')
  return t(key) + (scan && hl.kind !== 'partial' ? ' ' + t('clerk.head.scan') : '')
}

/** Above the documents: the strip of open remarks (the session's own element, moved into each new result). */
export function clerkTop(res: Converted, view: ViewModel): HTMLElement {
  const session = sessionOf(res.sidecar)
  session.setForm(res.form)
  session.repaint()
  const top = h('div', { class: 'clerk-top clerk-only', id: 'clerk-top' })
  // a new result comes into sight once (the upload panel above it is tall); a language change does not scroll again
  if (!shown.has(res)) {
    shown.add(res)
    queueMicrotask(() => { if (top.isConnected) top.closest<HTMLElement>('.result')?.scrollIntoView?.({ block: 'start', behavior: 'smooth' }) })
  }
  if (view.hasSidecar) top.append(session.host)
  else {
    // no report: the service named only the kinds of remarks, the page cannot show their places
    const n = res.header?.count ?? res.header?.codes.length ?? 0
    top.append(h('section', { class: 'clerk-remarks', id: 'clerk-remarks' },
      h('h3', { id: 'h-clerk-remarks' }, n ? t('clerk.remarks.noReport', { n }) : t('clerk.remarks.none'))))
  }
  return top
}

let tryOpen = false
const shown = new WeakSet<object>()

/** Below the documents: how much is left to look at, the one final action, and the door to the trial fill. */
export function clerkFinal(res: Converted, root: HTMLElement): HTMLElement {
  const session = sessionOf(res.sidecar)
  const state = h('p', { id: 'clerk-final-state', class: 'clerk-final-state', role: 'status' })
  const link = h('a', { class: 'btn btn-main', id: 'clerk-download', href: '#', download: 'e-formularz.json' }, t('clerk.final.download'))
  link.addEventListener('click', () => {
    const changed = session.changedForm()
    const bytes: BlobPart = changed ? JSON.stringify(changed) : res.formBytes as BlobPart
    const url = URL.createObjectURL(new Blob([bytes], { type: 'application/json' }))
    link.setAttribute('href', url)
    setTimeout(() => URL.revokeObjectURL(url), 10000)
  })
  const tryBtn = h('button', { type: 'button', class: 'btn', id: 'clerk-try', 'aria-controls': 'fp' })
  const paintTry = (): void => {
    if (tryOpen) root.setAttribute('data-try', '1'); else root.removeAttribute('data-try')
    tryBtn.setAttribute('aria-expanded', String(tryOpen))
    tryBtn.textContent = t(tryOpen ? 'clerk.final.tryHide' : 'clerk.final.try')
  }
  tryBtn.addEventListener('click', () => {
    tryOpen = !tryOpen
    paintTry()
    if (!tryOpen) return
    // BL13 TRY-F: the banner and the step come into sight under no sticky element; the focus goes to the one action
    const at = root.querySelector<HTMLElement>('#fp-banner') ?? root.querySelector<HTMLElement>('#fp-citizen')
    at?.scrollIntoView?.({ block: 'start' })
    const next = [...root.querySelectorAll<HTMLButtonElement>('#fp-citizen button, #fp-check-step button')].find((b) => !b.closest('[hidden]') && !b.disabled)
    next?.focus({ preventScroll: true })
  })
  const paint = (): void => {
    const open = session.openCount()
    const changed = session.changes.length
    state.textContent = (open ? t('clerk.final.open', { n: open }) : t('clerk.final.clear'))
      + (changed ? ' ' + tn('clerk.final.changed', changed) : '')
    state.classList.toggle('clerk-final-clear', open === 0)
  }
  session.onChange = () => { paint(); paintApplied(root, session) }
  paint()
  paintTry()
  return h('div', { class: 'clerk-final clerk-only', id: 'clerk-final' },
    state,
    h('div', { class: 'actions' }, link, tryBtn),
    h('p', { class: 'muted small clerk-final-hint' }, t('clerk.final.hint')))
}

const row = (name: string, value: string | Node): HTMLElement => h('tr', {}, h('th', { scope: 'row' }, name), h('td', {}, value))

function sourceText(w: RawWarning): string {
  const s = fixOf(w).source
  if (!s) return ''
  if (s.type === 'paper') return t('jury.src.paper', { page: s.page ?? '?' }) + (s.quote ? ': „' + s.quote + '”' : '')
  return t(s.type === 'dictionary' ? 'jury.src.dictionary' : 'jury.src.rule', { name: s.name ?? '' })
}

function appliedList(session: Session): HTMLElement {
  const box = h('div', { id: 'jury-applied' })
  if (session.applied.length) {
    box.append(h('h3', {}, t('jury.applied', { n: session.applied.length })),
      h('ul', { class: 'plain jury-list' }, ...session.applied.map((w) => {
        const fix = fixOf(w)
        const src = sourceText(w)
        return h('li', {}, h('span', { lang: 'pl' }, fix.text || t('warn.' + (w.code ?? ''))),
          h('span', { class: 'code-line' }, t('warnings.code', { code: '' }), h('code', { class: 'code' }, String(w.code ?? '')),
            fix.rule ? ' · ' + t('jury.rule') + ' ' : '', fix.rule ? h('code', { class: 'code' }, fix.rule) : null,
            src ? ' · ' + src : ''))
      })))
  }
  if (session.changes.length) {
    box.append(h('h3', {}, t('jury.changes', { n: session.changes.length })),
      h('ul', { class: 'plain jury-list' }, ...session.changes.map((c) => h('li', { lang: 'pl' }, `${c.what}: ${c.answer}`))))
  }
  return box
}

function paintApplied(root: HTMLElement, session: Session): void {
  root.querySelector('#jury-applied')?.replaceWith(appliedList(session))
}

/** For the jury: what was done and by what. Only facts the answer carries; a missing fact is a missing row. */
export function juryDone(res: Converted, view: ViewModel): HTMLElement {
  const session = sessionOf(res.sidecar)
  const sc = (res.sidecar ?? {}) as Record<string, unknown>
  const conv = (sc.converter ?? {}) as Record<string, unknown>
  const meta = (sc.meta ?? {}) as Record<string, unknown>
  const ledger = (meta.ledger ?? {}) as Record<string, unknown>
  const rows: HTMLElement[] = []
  const mode = modeOfEngine(res.engine)
  if (mode) rows.push(row(t('jury.mode'), t('mode.' + mode)))
  if (typeof conv.reader === 'string') rows.push(row(t('jury.reader'), h('code', { class: 'code' }, conv.reader)))
  if (typeof conv.pipeline === 'string') rows.push(row(t('jury.pipeline'), h('code', { class: 'code' }, conv.pipeline)))
  if (typeof conv.version === 'string') rows.push(row(t('jury.version'), conv.version))
  const num = (k: string): number | null => (typeof ledger[k] === 'number' ? ledger[k] as number : null)
  if (num('blanks_found') !== null) {
    rows.push(row(t('jury.ledger'), t('jury.ledger.line', {
      found: num('blanks_found') ?? 0, field: num('became_field') ?? 0, merged: num('merged') ?? 0,
      standard: num('covered_by_standard') ?? 0, out: num('left_out') ?? 0, waiting: num('awaiting_decision') ?? 0 })))
  }
  if (view.hasSidecar) rows.push(row(t('jury.origins'), t('jury.origins.line', { paper: view.matter.length, standard: view.standardCount })))
  const timings = (sc.timings ?? meta.timings) as Record<string, unknown> | undefined
  if (timings && typeof timings === 'object') {
    const parts = Object.entries(timings).filter(([, v]) => typeof v === 'number').map(([k, v]) => `${k}: ${Math.round(v as number)} ms`)
    if (parts.length) rows.push(row(t('jury.timings'), parts.join(', ')))
  }
  const conf = meta.confidence
  if (conf && typeof conf === 'object') {
    const bands: Record<string, number> = {}
    for (const c of Object.values(conf as Record<string, { band?: unknown }>)) if (typeof c?.band === 'string') bands[c.band] = (bands[c.band] ?? 0) + 1
    rows.push(row(t('jury.confidence'), t('jury.confidence.line', { sure: bands.sure ?? 0, check: bands.check ?? 0, unsure: bands.unsure ?? 0 })))
  }
  rows.push(row(t('jury.remarks'), t('jury.remarks.line', { clerk: session.remarks.reduce((a, r) => a + r.items.length, 0), applied: session.applied.length, notes: session.notes.length })))
  const checks = Array.isArray(sc.checks) ? sc.checks as Record<string, unknown>[] : []
  const checkList = checks.length
    ? h('details', { class: 'tech', id: 'jury-checks' },
      h('summary', {}, t('jury.checks', { n: checks.length, passed: checks.filter((c) => c.status === 'passed').length })),
      h('ul', { class: 'plain jury-list' }, ...checks.map((c) => h('li', {},
        h('code', { class: 'code' }, String(c.id ?? '')), ' ', String(c.name ?? ''), ': ',
        h('strong', {}, String(c.status ?? '')), typeof c.reason === 'string' ? h('span', { class: 'muted' }, ' (' + c.reason + ')') : null))))
    : null
  return h('section', { 'aria-labelledby': 'h-jury-done', id: 'jury-done' },
    h('h2', { id: 'h-jury-done' }, t('jury.heading')),
    h('p', { class: 'muted' }, t('jury.intro')),
    h('table', { class: 'jury-table' }, h('tbody', {}, ...rows)),
    checkList,
    appliedList(session))
}
