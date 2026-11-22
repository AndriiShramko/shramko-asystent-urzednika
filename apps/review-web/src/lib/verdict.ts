// Small pure decisions of the page, kept apart from the DOM so they can be tested on canned answers:
// the headline of a result, the advice after a failure, the service mode badge fed from GET /status.
import type { ViewModel } from './model'
import type { HeaderWarnings, RawWarning } from './warnings'

/** Codes that say nothing was read from the paper: the result holds only the title and standard sections. */
const NOTHING_READ = new Set(['BRIEF_NOT_READ', 'NO_MATTER'])

export type HeadlineKind = 'ok' | 'partial' | 'neutral'

export interface Headline {
  kind: HeadlineKind
  /** fields of the electronic form (all origins) */
  fields: number
  /** SECTION nodes of the form */
  sections: number
  /** fields read from the paper; null when the report is missing and nobody knows */
  paper: number | null
  standard: number
}

function codesOf(view: ViewModel, header: HeaderWarnings | null): string[] {
  const fromSidecar = view.warnings.map((w: RawWarning) => (typeof w.code === 'string' ? w.code : ''))
  return [...fromSidecar, ...(header?.codes ?? [])]
}

/** "Formularz przetworzony" only when fields were read from the paper; with zero of them (or a warning that says
 * the paper was not read) the result is partial and must never look like a success. Without the report the page
 * cannot tell, so the line is neutral: neither a success nor an alarm. */
export function chooseHeadline(view: ViewModel, header: HeaderWarnings | null): Headline {
  const nothingRead = codesOf(view, header).some((c) => NOTHING_READ.has(c))
  const base = { fields: view.counts.fields, sections: view.sectionCount, standard: view.standardCount }
  if (view.hasSidecar) {
    const paper = view.matter.length
    return { ...base, paper, kind: paper === 0 || nothingRead ? 'partial' : 'ok' }
  }
  return { ...base, paper: null, kind: nothingRead ? 'partial' : 'neutral' }
}

/** Who can fix a failure: the file (choose or save another file), the token, or the service (try again). */
export type FailureCause = 'file' | 'token' | 'service'

const FILE_CODES = new Set(['TOO_LARGE', 'TOO_MANY_PAGES', 'TOO_MANY_PIXELS', 'ARCHIVE_LIMIT', 'EXTENSION',
  'UNSUPPORTED_FORMAT', 'TYPE_MISMATCH', 'BAD_NAME', 'DOC_READER_OFF', 'UNREADABLE', 'NOT_A_FORM', 'ACTIVE_CONTENT'])
const TOKEN_CODES = new Set(['TOKEN_MISSING', 'TOKEN_INVALID', 'TOKEN_EXPIRED', 'SCOPE'])

export function causeOf(code: string): FailureCause {
  if (FILE_CODES.has(code)) return 'file'
  if (TOKEN_CODES.has(code)) return 'token'
  return 'service' // GATE_FAILED, TIMEOUT, BUSY, NETWORK, BAD_ANSWER, HTTP, BAD_REQUEST and any unknown code
}

/** The dictionary key of the "Co zrobić" line. A code without its own line gets the advice of its cause, so a
 * service fault never says "choose another file". */
export function adviceKey(code: string, has: (key: string) => boolean): string {
  const own = 'todo.' + code
  if (has(own)) return own
  const cause = causeOf(code)
  return cause === 'file' ? 'todo.file' : cause === 'token' ? 'todo.token' : 'todo.service'
}

/** The badge in the header. Only what /status says: no answer, or an answer the page does not understand, is no
 * badge at all (null), never a guess. */
export type Mode = 'rules' | 'model-on' | 'model-fallback'

export function modeOf(status: unknown): Mode | null {
  if (!status || typeof status !== 'object' || Array.isArray(status)) return null
  const s = status as { engine?: unknown; model?: unknown }
  const engine = typeof s.engine === 'string' ? s.engine.trim().toLowerCase() : null
  let state: string | null = null
  if (s.model !== undefined && s.model !== null) {
    if (typeof s.model !== 'object' || Array.isArray(s.model)) return null
    const raw = (s.model as { state?: unknown }).state
    state = typeof raw === 'string' ? raw.trim().toUpperCase() : null
    if (state === null) return null
  }
  if (engine === 'rules-fallback' || state === 'UNAVAILABLE' || state === 'FALLBACK') return 'model-fallback'
  if (state === 'ON' || engine === 'rules+model') return 'model-on'
  if (engine === 'rules' && (state === null || state === 'OFF')) return 'rules'
  return null
}
