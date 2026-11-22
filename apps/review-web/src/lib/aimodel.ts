// Wave 11 KEY: what the page knows about the optional AI model step, and the three calls of its block
// ("Model AI (opcjonalnie)"). The service never sends a key: at most the last four characters of one. A key typed
// here lives in the memory of this tab and of the service; nothing is written to localStorage or a cookie.
// (This is not lib/model.ts: that file is the view model of the FORM.)
import type { Fetcher } from './api'

export const MODEL_URL = '../v1/model'
export const SESSION_URL = '../v1/model/session'
export const CHECK_URL = '../v1/model/check'

export type AiStateName = 'off' | 'on' | 'fallback' | 'disabled'
export type AiSource = 'none' | 'environment' | 'session'

export interface AiState {
  state: AiStateName
  source: AiSource
  /** may this page change the settings (the operator can forbid it) */
  pageConfig: boolean
  model: string
  /** shown only to a caller who may convert; '' otherwise */
  address: string
  /** has the step been used since the settings were set */
  used: boolean
  keySet: boolean
  keyOrigin: 'environment-variable' | 'environment-file' | 'session' | ''
  /** the last four characters of the key, or '' when the service does not show them */
  keyTail: string
  /** the code of what is wrong in a fallback (bad_key, no_credit, ...), or '' */
  problem: string
}

export interface CheckResult {
  ok: boolean
  code: string
  http: number | null
  ms: number
}

export interface Typed {
  base_url?: string
  model?: string
  key?: string
}

const STATES: readonly string[] = ['off', 'on', 'fallback', 'disabled']
const SOURCES: readonly string[] = ['none', 'environment', 'session']
const ORIGINS: readonly string[] = ['environment-variable', 'environment-file', 'session']
/** The codes the page has a sentence for; any other code is shown as `server_error`. */
export const CODES: readonly string[] = ['ok', 'bad_key', 'no_credit', 'rate_limit', 'unreachable', 'timeout',
  'model_not_found', 'not_api', 'server_error', 'bad_url', 'bad_model', 'bad_key_form', 'key_needed', 'not_configured',
  'locked', 'disabled', 'busy', 'bad_request', 'token', 'no_service']

function str(x: unknown, max = 200): string {
  return typeof x === 'string' ? x.slice(0, max) : ''
}

/** The answer of GET /v1/model, read defensively: anything unexpected is "unknown" (null), never a guess. */
export function parseState(raw: unknown): AiState | null {
  if (!raw || typeof raw !== 'object') return null
  const r = raw as Record<string, unknown>
  if (typeof r.state !== 'string' || !STATES.includes(r.state)) return null
  const key = (r.key && typeof r.key === 'object' ? r.key : {}) as Record<string, unknown>
  const origin = str(key.origin)
  const tail = str(key.tail, 8)
  return {
    state: r.state as AiStateName,
    source: (typeof r.source === 'string' && SOURCES.includes(r.source) ? r.source : 'none') as AiSource,
    pageConfig: r.page_config === true,
    model: str(r.model),
    address: str(r.address, 300),
    used: r.used === true,
    keySet: key.set === true,
    keyOrigin: (ORIGINS.includes(origin) ? origin : '') as AiState['keyOrigin'],
    keyTail: /^[\x21-\x7e]{1,4}$/.test(tail) ? tail : '',
    problem: codeOf(r.problem, '')
  }
}

export function codeOf(raw: unknown, fallback = 'server_error'): string {
  return typeof raw === 'string' && CODES.includes(raw) ? raw : fallback
}

export function parseCheck(raw: unknown): CheckResult {
  const r = (raw && typeof raw === 'object' ? raw : {}) as Record<string, unknown>
  const code = codeOf(r.code)
  return {
    ok: r.ok === true && code === 'ok',
    code,
    http: typeof r.http === 'number' && Number.isInteger(r.http) ? r.http : null,
    ms: typeof r.ms === 'number' && r.ms >= 0 ? Math.round(r.ms) : 0
  }
}

/** Dots for a key the page does not know; with `tail`, the dots end with the last characters the service gave. */
export function masked(tail = ''): string {
  return '•'.repeat(tail ? 12 : 16) + tail
}

/** What to send: only what the person changed. An untouched field is completed by the service from its settings
 * (a key only for the address it belongs to). */
export function typedOf(state: AiState | null, url: string, model: string, key: string): Typed {
  const out: Typed = {}
  const u = url.trim()
  const m = model.trim()
  const k = key.trim()
  if (u && u !== (state?.address ?? '')) out.base_url = u
  if (m && m !== (state?.model ?? '')) out.model = m
  if (k) out.key = k
  // A changed address or key travels with the model name on the screen, so the check uses what the person sees.
  if ((out.base_url || out.key) && m) out.model = m
  return out
}

export function isTyped(x: Typed): boolean {
  return Boolean(x.base_url || x.model || x.key)
}

function headers(token: string, json: boolean): Record<string, string> {
  const h: Record<string, string> = { Accept: 'application/json' }
  if (json) h['Content-Type'] = 'application/json'
  if (token.trim()) h['Authorization'] = 'Bearer ' + token.trim()
  return h
}

const real: Fetcher = (u, i) => fetch(u, i)

/** GET /v1/model; null on any failure. Never throws. */
export async function fetchAiState(token = '', fetcher: Fetcher = real): Promise<AiState | null> {
  try {
    const res = await fetcher(MODEL_URL, { method: 'GET', headers: headers(token, false), cache: 'no-store' })
    if (!res.ok) return null
    return parseState(await res.json())
  } catch {
    return null
  }
}

async function call(url: string, method: string, token: string, body: Typed | null, fetcher: Fetcher): Promise<{ status: number; json: unknown }> {
  try {
    const res = await fetcher(url, { method, headers: headers(token, body !== null), body: body === null ? undefined : JSON.stringify(body), cache: 'no-store' })
    let json: unknown = null
    try { json = await res.json() } catch { json = null }
    return { status: res.status, json }
  } catch {
    return { status: 0, json: null }
  }
}

/** A call that did not reach the rules of the block: no service, or the token of this service was refused. */
function failed(status: number, json: unknown): CheckResult | null {
  if (status === 0) return { ok: false, code: 'no_service', http: null, ms: 0 }
  const code = (json && typeof json === 'object' ? (json as Record<string, unknown>).code : null)
  const known = typeof code === 'string' && CODES.includes(code)
  if (status === 401 || (status === 403 && !known)) return { ok: false, code: 'token', http: null, ms: 0 }
  if (status >= 500 || (status >= 400 && !known)) return { ok: false, code: 'no_service', http: null, ms: 0 }
  return null
}

/** POST /v1/model/check: one small real call made by the service. */
export async function checkModel(typed: Typed, token = '', fetcher: Fetcher = real): Promise<CheckResult> {
  const { status, json } = await call(CHECK_URL, 'POST', token, typed, fetcher)
  return failed(status, json) ?? parseCheck(json)
}

export interface Changed {
  ok: boolean
  code: string
  state: AiState | null
}

function changed(status: number, json: unknown): Changed {
  const bad = failed(status, json)
  if (bad) return { ok: false, code: bad.code, state: null }
  const r = (json && typeof json === 'object' ? json : {}) as Record<string, unknown>
  const code = codeOf(r.code)
  return { ok: status === 200 && r.ok === true, code, state: parseState(r.model) }
}

/** PUT /v1/model/session: use these settings until the service restarts. */
export async function useInSession(typed: Typed, token = '', fetcher: Fetcher = real): Promise<Changed> {
  const { status, json } = await call(SESSION_URL, 'PUT', token, typed, fetcher)
  return changed(status, json)
}

/** DELETE /v1/model/session: back to the settings of the server. */
export async function forgetSession(token = '', fetcher: Fetcher = real): Promise<Changed> {
  const { status, json } = await call(SESSION_URL, 'DELETE', token, null, fetcher)
  return changed(status, json)
}
