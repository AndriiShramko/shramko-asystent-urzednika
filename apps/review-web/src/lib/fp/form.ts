// The returned form JSON read as a tree of nodes the electronic form can render: tabs, sections, fields, with the
// key each field answers under in the partner's conditions (`tab | section techName | field techName`).
// Nothing here changes the form; unknown keys are ignored, missing ones get empty defaults.

export interface Consent { text: string; required: boolean }

export interface ENode {
  id: string
  type: string
  techName: string
  title: string
  /** The description as plain text (the JSON holds HTML; it is read as text, never inserted as markup). */
  description: string
  options: string[]
  validation: string[]
  readOnly: boolean
  defaultValue: unknown
  defaultValueType: string | null
  dictionaryName: string | null
  /** SHOW conditions (JSONata strings) of this node. */
  shows: string[]
  consents: Consent[]
  children: ENode[]
  tab: string
  tabIndex: number
  /** techName of the top question this node sits in (its own when it is the top one). */
  top: string
  /** The answer key the partner's conditions read, for direct children of a top question; else null. */
  refKey: string | null
  parent: ENode | null
}

export interface ETab { title: string; nodes: ENode[] }

export interface FormModel {
  title: string
  tabs: ETab[]
  /** every node in document order */
  all: ENode[]
  byId: Map<string, ENode>
  byRef: Map<string, ENode>
}

/** Types that hold an answer of the person (not containers, not fixed text). */
export const INPUT_TYPES = new Set(['TEXT_FIELD', 'TEXTAREA', 'NUMBER', 'DATEPICKER', 'CHECKBOX', 'RADIO', 'SELECT',
  'CONSENT_SECTION', 'FILE_UPLOADER'])
export const CONTAINER_TYPES = new Set(['SECTION', 'REPEATING_SECTION'])

export function refKey(tab: string, section: string, field: string): string {
  return tab + '\u0000' + section + '\u0000' + field
}

/** HTML of a description as plain text, through DOMParser (no markup reaches the page). */
export function htmlText(html: unknown): string {
  if (typeof html !== 'string' || !html.trim()) return ''
  if (!/[<&]/.test(html)) return html.trim()
  try {
    const doc = new DOMParser().parseFromString(html, 'text/html')
    const blocks = [...doc.body.querySelectorAll('p, li')]
    const text = blocks.length ? blocks.map((b) => (b.textContent ?? '').trim()).filter(Boolean).join('\n') : (doc.body.textContent ?? '')
    return text.trim()
  } catch {
    return ''
  }
}

interface Raw {
  id?: unknown; type?: unknown; techName?: unknown; title?: unknown; description?: unknown
  options?: { name?: unknown }[]; validation?: unknown[]; readOnly?: unknown; defaultValue?: unknown
  defaultValueType?: unknown; dictionaryName?: unknown; states?: { type?: unknown; query?: unknown }[]
  consentSectionConfig?: { consents?: { description?: unknown; required?: unknown }[] }
  repeatingSectionGrid?: { field?: Raw }[]
}

const str = (x: unknown): string => (typeof x === 'string' ? x : '')

/** The service writes UUID ids. An id goes into element ids and into selectors of the page, so one that is not a
 * plain token (a quote, a bracket, a space) never reaches them: the node gets a neutral id and still works. */
const SAFE_ID = /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/

export function readForm(form: unknown): FormModel {
  const f = (form ?? {}) as { title?: unknown; tabs?: { title?: unknown; questions?: { field?: Raw }[] }[] }
  const all: ENode[] = []
  const byId = new Map<string, ENode>()
  const byRef = new Map<string, ENode>()
  const tabs: ETab[] = []

  const build = (raw: Raw, tab: string, tabIndex: number, top: string | null, depth: number, parent: ENode | null): ENode => {
    const techName = str(raw.techName)
    const own = top ?? techName
    const rawId = str(raw.id)
    const node: ENode = {
      id: !rawId || SAFE_ID.test(rawId) ? rawId : `fp-node-${all.length}`,
      type: str(raw.type),
      techName,
      title: str(raw.title),
      description: htmlText(raw.description),
      options: Array.isArray(raw.options) ? raw.options.map((o) => str(o?.name)).filter(Boolean) : [],
      validation: Array.isArray(raw.validation) ? raw.validation.filter((v): v is string => typeof v === 'string') : [],
      readOnly: raw.readOnly === true,
      defaultValue: raw.defaultValue,
      defaultValueType: typeof raw.defaultValueType === 'string' ? raw.defaultValueType : null,
      dictionaryName: typeof raw.dictionaryName === 'string' && raw.dictionaryName ? raw.dictionaryName : null,
      shows: Array.isArray(raw.states)
        ? raw.states.filter((s) => s?.type === 'SHOW' && typeof s.query === 'string').map((s) => s.query as string)
        : [],
      consents: Array.isArray(raw.consentSectionConfig?.consents)
        ? raw.consentSectionConfig.consents.map((c) => ({ text: htmlText(c?.description), required: c?.required === true }))
        : [],
      children: [],
      tab,
      tabIndex,
      top: own,
      refKey: depth === 1 ? refKey(tab, own, techName) : null,
      parent
    }
    all.push(node)
    if (node.id) byId.set(node.id, node)
    if (node.refKey) byRef.set(node.refKey, node)
    for (const cell of raw.repeatingSectionGrid ?? []) {
      if (cell?.field) node.children.push(build(cell.field, tab, tabIndex, own, depth + 1, node))
    }
    return node
  }

  ;(f.tabs ?? []).forEach((t, i) => {
    const title = str(t?.title)
    const nodes: ENode[] = []
    for (const q of t?.questions ?? []) if (q?.field) nodes.push(build(q.field, title, i, null, 0, null))
    tabs.push({ title, nodes })
  })
  return { title: str(f.title), tabs, all, byId, byRef }
}

/** The display name of a field: its title, else the techName. */
export function nameOf(n: ENode): string {
  // a consent block has no title of its own: its section's title names it
  return n.title || (n.type === 'CONSENT_SECTION' ? n.parent?.title : '') || n.techName || n.type
}
