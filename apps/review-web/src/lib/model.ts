// The view model of the review page: the partner's form tree plus the sidecar, flattened to rows. Nothing here
// edits the form; a missing sidecar or a missing key is shown as absent, never filled with a guess.
import type { RawWarning } from './warnings'

export type Origin = 'paper' | 'standard' | 'reviewer' | 'unknown'

export interface FieldRow {
  id: string
  title: string
  type: string
  techName: string
  required: boolean
  options: string[]
  origin: Origin
  tab: string
  section: string | null
  page: number | null
  anchor: string | null
  quote: string | null
}

export interface Sidecar {
  warnings?: RawWarning[]
  counts?: { pages?: number; fields?: number; source_pages?: number }
  meta?: SidecarMeta
  // The contract's own shape keeps these at the top level; both are read.
  origins?: Record<string, string>
  evidence?: Record<string, unknown>
  [k: string]: unknown
}

interface SidecarMeta {
  origins?: Record<string, string>
  evidence?: Record<string, unknown>
  [k: string]: unknown
}

export interface ViewModel {
  title: string
  rows: FieldRow[]
  matter: FieldRow[]
  standard: Map<string, FieldRow[]>
  standardCount: number
  unknown: FieldRow[]
  hasSidecar: boolean
  warnings: RawWarning[]
  counts: { pages: number; fields: number; sourcePages: number | null }
}

/** Types that are not blanks to fill: containers and fixed texts. */
const NOT_A_FIELD = new Set(['SECTION', 'TEXT_BLOCK', 'INFO_SECTION'])

interface RawField {
  id?: string
  type?: string
  techName?: string
  title?: string
  options?: { name?: string }[]
  validation?: unknown[]
  repeatingSectionGrid?: { field?: RawField }[]
}

interface RawForm {
  title?: string
  tabs?: { title?: string; questions?: { field?: RawField }[] }[]
}

function asOrigin(x: unknown): Origin | null {
  return x === 'paper' || x === 'standard' || x === 'reviewer' ? x : null
}

function pickEvidence(raw: unknown): { page: number | null; anchor: string | null; quote: string | null } {
  const list = Array.isArray(raw) ? raw : raw ? [raw] : []
  let page: number | null = null
  let anchor: string | null = null
  let quote: string | null = null
  for (const e of list) {
    if (!e || typeof e !== 'object') continue
    const r = e as { page?: unknown; anchor?: unknown; quote?: unknown }
    if (page === null && typeof r.page === 'number') page = r.page
    if (anchor === null && typeof r.anchor === 'string') anchor = r.anchor
    if (quote === null && typeof r.quote === 'string' && r.quote) quote = r.quote
  }
  return { page, anchor, quote }
}

export function buildView(form: unknown, sidecar: Sidecar | null): ViewModel {
  const f = (form ?? {}) as RawForm
  const origins: Record<string, string> = sidecar?.meta?.origins ?? sidecar?.origins ?? {}
  const evidence: Record<string, unknown> = sidecar?.meta?.evidence ?? sidecar?.evidence ?? {}
  const rows: FieldRow[] = []

  const walk = (field: RawField, tab: string, section: string | null, inherited: Origin | null): void => {
    const own = field.id ? asOrigin(origins[field.id]) : null
    const origin = own ?? inherited
    const type = field.type ?? ''
    if (!NOT_A_FIELD.has(type)) {
      const ev = pickEvidence(field.id ? evidence[field.id] : undefined)
      rows.push({
        id: field.id ?? '',
        title: field.title ?? field.techName ?? '',
        type,
        techName: field.techName ?? '',
        required: Array.isArray(field.validation) && field.validation.includes('REQUIRED'),
        options: (field.options ?? []).map((o) => o.name ?? '').filter(Boolean),
        origin: sidecar && origin ? origin : 'unknown',
        tab,
        section,
        ...ev
      })
    }
    const nextSection = type === 'SECTION' ? (field.title ?? field.techName ?? section) : section
    for (const child of field.repeatingSectionGrid ?? []) if (child.field) walk(child.field, tab, nextSection, origin)
  }

  for (const tab of f.tabs ?? []) {
    const tabTitle = tab.title ?? ''
    for (const q of tab.questions ?? []) if (q.field) walk(q.field, tabTitle, null, null)
  }

  const matter = rows.filter((r) => r.origin === 'paper' || r.origin === 'reviewer')
  const standardRows = rows.filter((r) => r.origin === 'standard')
  const standard = new Map<string, FieldRow[]>()
  for (const r of standardRows) {
    const list = standard.get(r.tab) ?? []
    list.push(r)
    standard.set(r.tab, list)
  }
  const warnings = Array.isArray(sidecar?.warnings) ? sidecar.warnings : []
  return {
    title: typeof f.title === 'string' ? f.title : '',
    rows,
    matter,
    standard,
    standardCount: standardRows.length,
    unknown: rows.filter((r) => r.origin === 'unknown'),
    hasSidecar: sidecar !== null,
    warnings,
    counts: {
      pages: (f.tabs ?? []).length,
      fields: rows.length,
      sourcePages: typeof sidecar?.counts?.source_pages === 'number' ? sidecar.counts.source_pages : null
    }
  }
}
