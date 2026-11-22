// Small pure decisions of the page, kept apart from the DOM so they can be tested on canned answers:
// the headline of a result, the advice after a failure, the mode badge fed from GET /status and from the engine
// of the last conversion.
import type { Engine } from './api'
import type { ViewModel } from './model'
import type { HeaderWarnings, RawWarning } from './warnings'

/** Codes that say nothing was read from the paper: the result holds only the title and standard sections. */
const NOTHING_READ = new Set(['BRIEF_NOT_READ', 'NO_MATTER'])

export type HeadlineKind = 'ok' | 'partial' | 'neutral'
/** Why a result is partial: no field from the paper, very few of them, or the service's own warning. */
export type PartialWhy = 'none' | 'few' | 'warning'

export interface Headline {
  kind: HeadlineKind
  /** set when kind is 'partial' */
  why: PartialWhy | null
  /** fields of the electronic form (all origins) */
  fields: number
  /** SECTION nodes of the form */
  sections: number
  /** fields read from the paper; null when the report is missing and nobody knows */
  paper: number | null
  standard: number
}

/** "A handful" of fields from the paper: at most this many AND under a tenth of all fields. A photo of a blank that
 * gave 1 field of 47 is not a success (TU2, set 03 JPG); a small real form with 2 fields of 4 is. */
export const FEW_PAPER = 2

function codesOf(view: ViewModel, header: HeaderWarnings | null): string[] {
  const fromSidecar = view.warnings.map((w: RawWarning) => (typeof w.code === 'string' ? w.code : ''))
  return [...fromSidecar, ...(header?.codes ?? [])]
}

/** "Formularz przetworzony" (green) only when the paper really gave fields; with zero of them, a handful among many
 * standard ones, or a warning of the service that says the paper was not read (BRIEF_NOT_READ, and NO_MATTER which
 * since DX-3 comes whenever no field of the paper was read) the result is partial and must never look like a
 * success. Without the report the page cannot tell, so the line is neutral: neither a success nor an alarm. */
export function chooseHeadline(view: ViewModel, header: HeaderWarnings | null): Headline {
  const nothingRead = codesOf(view, header).some((c) => NOTHING_READ.has(c))
  const base = { fields: view.counts.fields, sections: view.sectionCount, standard: view.standardCount }
  if (view.hasSidecar) {
    const paper = view.matter.length
    const why: PartialWhy | null = paper === 0 ? 'none' : nothingRead ? 'warning'
      : paper <= FEW_PAPER && paper * 10 < view.counts.fields ? 'few' : null
    return { ...base, paper, why, kind: why ? 'partial' : 'ok' }
  }
  return { ...base, paper: null, why: nothingRead ? 'warning' : null, kind: nothingRead ? 'partial' : 'neutral' }
}

const VOWEL_WORD = /[aeiouyąęó]/i
const FORM_CODE = /^[A-ZĄĆĘŁŃÓŚŹŻ]{2,}[-\s]?\d/u

/** Whether the title looks like words read from the paper and not OCR noise: at least 6 letters and at least one
 * word of 4+ letters with a vowel. A form code ("PIT-37", "CEIDG-1") counts as a title. */
export function titleLooksRead(title: string): boolean {
  const s = (title ?? '').trim()
  if (FORM_CODE.test(s)) return true
  const letters = s.match(/\p{L}/gu)?.length ?? 0
  if (letters < 6) return false
  return s.split(/[^\p{L}]+/u).some((w) => w.length >= 4 && VOWEL_WORD.test(w) && /[^aeiouyąęó]/i.test(w))
}

/** The formats the service accepts, from GET /status `formats` (extensions). Anything else is dropped; no answer is
 * an empty list, never a list the page invents. */
export function formatsOf(status: unknown): string[] {
  if (!status || typeof status !== 'object' || Array.isArray(status)) return []
  const raw = (status as { formats?: unknown }).formats
  if (!Array.isArray(raw)) return []
  const out: string[] = []
  for (const x of raw) {
    if (typeof x !== 'string') continue
    const ext = x.trim().toLowerCase().replace(/^\./, '')
    if (/^[a-z0-9]{1,5}$/.test(ext) && !out.includes(ext)) out.push(ext)
  }
  return out
}

/** Other spellings of the same extension, so the file picker and the line name what people have on disk. */
const ALIASES: Record<string, string> = { jpeg: 'jpg', tiff: 'tif' }

/** "PDF, DOCX, JPEG (JPG)": the list of /status for people. */
export function formatsText(formats: readonly string[]): string {
  return formats.map((f) => {
    const alias = ALIASES[f]
    return alias && !formats.includes(alias) ? `${f.toUpperCase()} (${alias.toUpperCase()})` : f.toUpperCase()
  }).join(', ')
}

/** The `accept` attribute of the file input; empty when the service did not say (any file, the service decides). */
export function acceptOf(formats: readonly string[]): string {
  const all: string[] = []
  for (const f of formats) {
    for (const e of [f, ALIASES[f]]) if (e && !all.includes('.' + e)) all.push('.' + e)
  }
  return all.join(',')
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

/** The badge in the header: the one indicator of the engine on the page. `modeOf` reads /status: no answer, or an
 * answer the page does not understand, is no mode at all (null), never a guess. */
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

/** The mode one engine token of `X-Converter-Engine` stands for; a conversion that did not state it is null. */
export function modeOfEngine(engine: Engine | null): Mode | null {
  if (engine === 'rules') return 'rules'
  if (engine === 'rules+model') return 'model-on'
  if (engine === 'rules-fallback') return 'model-fallback'
  return null
}

/** The one badge of the page, from two sources: the engine of the last conversion and the answer of /status that
 * came after it (`statusMode` is null until that answer arrives, and when it failed).
 * - a conversion that fell back wins over any /status, until the next conversion: the page never says "on" right
 *   after a result that the model did not take part in;
 * - otherwise /status, the later fact about the service, decides;
 * - with no /status the engine of the conversion is shown; with neither there is no badge (null), never a guess. */
export function badgeMode(lastEngine: Engine | null, statusMode: Mode | null): Mode | null {
  if (lastEngine === 'rules-fallback') return 'model-fallback'
  return statusMode ?? modeOfEngine(lastEngine)
}
