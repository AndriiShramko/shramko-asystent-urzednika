// The one call the page makes: POST /v1/forms/convert?report=1 with the file and an optional bearer token.
// The address is relative to the page (served under /ui/), so nothing leaves the origin it came from.
import { boundaryOf, parseMultipart } from './multipart'
import { parseWarningsHeader, type HeaderWarnings } from './warnings'
import type { Sidecar } from './model'

// BL12: the service refuses a name the task card forbids (over 250 characters, or holding ; : > < / \ | ' * % $) with
// 400 BAD_NAME. The page never asks the clerk to rename a file: it sends a cleaned copy of the name; the bytes are the same.
const NAME_FORBIDDEN = /[;:><\\/|'*%$\u0000-\u001f\u007f\u200e\u200f\u202a-\u202e\u2066-\u2069]/g
export function uploadName(raw: string): string {
  let name = raw.normalize('NFC').replace(NAME_FORBIDDEN, '').trim()
  const dot = name.lastIndexOf('.')
  const ext = dot > 0 && name.length - dot <= 11 ? name.slice(dot) : ''
  if (name.length > 250) name = name.slice(0, 250 - ext.length) + ext
  if (!name || !name.replace(/\./g, '')) name = 'plik' + ext
  return name
}

export interface Problem {
  kind: 'error'
  code: string
  status: number
  detail: string | null
  title: string | null
}

export type HashCheck = 'ok' | 'bad' | 'unchecked'

export interface Converted {
  kind: 'ok'
  formBytes: Uint8Array
  formText: string
  form: unknown
  sidecar: Sidecar | null
  /** Why the sidecar is absent, when it is: 'none' (not sent), 'invalid' (not JSON), or null when present. */
  sidecarMissing: 'none' | 'invalid' | null
  header: HeaderWarnings | null
  formSha256: string | null
  hash: HashCheck
  /** The engine this conversion ran on, from `X-Converter-Engine`; null when the service did not state it. */
  engine: Engine | null
}

export type Engine = 'rules' | 'rules+model' | 'rules-fallback'
const ENGINES: readonly string[] = ['rules', 'rules+model', 'rules-fallback']

/** `X-Converter-Engine` names one of three engines. No header, or any other value, is "not stated": never a guess. */
export function parseEngine(raw: string | null): Engine | null {
  const value = (raw ?? '').trim().toLowerCase()
  return ENGINES.includes(value) ? (value as Engine) : null
}

export type Outcome = Converted | Problem

export const CONVERT_URL = '../v1/forms/convert?report=1'

export async function sha256Hex(bytes: Uint8Array): Promise<string | null> {
  const subtle = globalThis.crypto?.subtle
  if (!subtle) return null
  const digest = await subtle.digest('SHA-256', bytes as BufferSource)
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('')
}

export function problemFrom(status: number, contentType: string | null, text: string): Problem {
  if (contentType && /json/i.test(contentType)) {
    try {
      const body = JSON.parse(text) as { code?: unknown; detail?: unknown; title?: unknown }
      const code = typeof body.code === 'string' && body.code ? body.code : null
      return {
        kind: 'error',
        code: code ?? 'HTTP',
        status,
        detail: typeof body.detail === 'string' ? body.detail : null,
        title: typeof body.title === 'string' ? body.title : null
      }
    } catch {
      /* fall through to the plain status */
    }
  }
  return { kind: 'error', code: 'HTTP', status, detail: null, title: null }
}

export async function interpretResponse(
  status: number,
  headers: Pick<Headers, 'get'>,
  bytes: Uint8Array
): Promise<Outcome> {
  const contentType = headers.get('content-type')
  if (status < 200 || status >= 300) {
    return problemFrom(status, contentType, new TextDecoder().decode(bytes))
  }
  const bad = (): Problem => ({ kind: 'error', code: 'BAD_ANSWER', status, detail: null, title: null })
  let formBytes: Uint8Array | null = null
  let sidecarBytes: Uint8Array | null = null
  const boundary = boundaryOf(contentType)
  if (boundary && /multipart/i.test(contentType ?? '')) {
    for (const p of parseMultipart(bytes, boundary)) {
      if (p.filename === 'form.json') formBytes = p.body
      else if (p.filename === 'meta.json') sidecarBytes = p.body
    }
  } else if (contentType && /json/i.test(contentType)) {
    formBytes = bytes // an answer without the report: the form alone
  }
  if (!formBytes) return bad()
  const formText = new TextDecoder().decode(formBytes)
  let form: unknown
  try {
    form = JSON.parse(formText)
  } catch {
    return bad()
  }
  if (!form || typeof form !== 'object' || Array.isArray(form)) return bad()

  let sidecar: Sidecar | null = null
  let sidecarMissing: Converted['sidecarMissing'] = 'none'
  if (sidecarBytes) {
    try {
      const parsed: unknown = JSON.parse(new TextDecoder().decode(sidecarBytes))
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        sidecar = parsed as Sidecar
        sidecarMissing = null
      } else sidecarMissing = 'invalid'
    } catch {
      sidecarMissing = 'invalid'
    }
  }
  const formSha256 = headers.get('x-form-sha256')
  const actual = await sha256Hex(formBytes)
  const hash: HashCheck = !formSha256 || !actual ? 'unchecked' : actual === formSha256.toLowerCase() ? 'ok' : 'bad'
  return {
    kind: 'ok',
    formBytes,
    formText,
    form,
    sidecar,
    sidecarMissing,
    header: parseWarningsHeader(headers.get('x-converter-warnings')),
    formSha256,
    hash,
    engine: parseEngine(headers.get('x-converter-engine'))
  }
}

export type Fetcher = (input: string, init: RequestInit) => Promise<Response>

export async function convertFile(file: File, token: string, fetcher: Fetcher = (u, i) => fetch(u, i)): Promise<Outcome> {
  const body = new FormData()
  body.append('file', file, uploadName(file.name))
  const headers: Record<string, string> = {}
  if (token.trim()) headers['Authorization'] = 'Bearer ' + token.trim()
  let res: Response
  try {
    res = await fetcher(CONVERT_URL, { method: 'POST', body, headers })
  } catch {
    return { kind: 'error', code: 'NETWORK', status: 0, detail: null, title: null }
  }
  const bytes = new Uint8Array(await res.arrayBuffer())
  return interpretResponse(res.status, res.headers, bytes)
}

/** What the page wants to know while a conversion runs: the moment the file has left the browser (the stage
 * changes from sending to processing) and a way to stop waiting. */
export interface ConvertHooks {
  onUploaded?: () => void
  signal?: AbortSignal
  /** W11 FLOW (convertQueued): bytes of the file that left the browser. */
  onSent?: (loaded: number, total: number) => void
  /** W11 FLOW: every answer of the service about the job (place in the queue, stage, finished parts). */
  onStatus?: (status: JobStatus) => void
  /** W11 FLOW: the queue of the service had no room; the file is offered again in `retryS` seconds. */
  onFull?: (retryS: number) => void
  /** W11 FLOW: how many questions about the job in a row got no answer. */
  onSilent?: (questions: number) => void
}

/** The code of an outcome the person chose (Przerwij): not an error of the file nor of the service. */
export const CANCELLED = 'CANCELLED'

/** The same request as convertFile, through XMLHttpRequest, because only it reports the end of the upload; the
 * stage text of the page is then true, not a timer. Same URL, same body, same headers: the REST contract is
 * unchanged. Cancelling stops the page waiting; the service may still finish the job on its side. */
export function convertWithProgress(file: File, token: string, hooks: ConvertHooks = {}): Promise<Outcome> {
  return new Promise<Outcome>((resolve) => {
    const fail = (code: string): void => resolve({ kind: 'error', code, status: 0, detail: null, title: null })
    if (typeof XMLHttpRequest === 'undefined') {
      convertFile(file, token).then(resolve, () => fail('NETWORK'))
      return
    }
    const body = new FormData()
    body.append('file', file, uploadName(file.name))
    const xhr = new XMLHttpRequest()
    xhr.open('POST', CONVERT_URL)
    xhr.responseType = 'arraybuffer'
    if (token.trim()) xhr.setRequestHeader('Authorization', 'Bearer ' + token.trim())
    let uploaded = false
    const markUploaded = (): void => { if (!uploaded) { uploaded = true; hooks.onUploaded?.() } }
    xhr.upload.addEventListener('load', markUploaded)
    xhr.addEventListener('readystatechange', () => { if (xhr.readyState >= 2) markUploaded() })
    xhr.addEventListener('load', () => {
      markUploaded()
      const bytes = new Uint8Array((xhr.response as ArrayBuffer | null) ?? new ArrayBuffer(0))
      interpretResponse(xhr.status, { get: (name: string) => xhr.getResponseHeader(name) }, bytes).then(resolve, () => fail('BAD_ANSWER'))
    })
    xhr.addEventListener('error', () => fail('NETWORK'))
    xhr.addEventListener('timeout', () => fail('NETWORK'))
    xhr.addEventListener('abort', () => fail(CANCELLED))
    if (hooks.signal) {
      if (hooks.signal.aborted) { fail(CANCELLED); return }
      hooks.signal.addEventListener('abort', () => xhr.abort())
    }
    xhr.send(body)
  })
}

export const STATUS_URL = '../status'

/** GET /status as parsed JSON, or null on any failure (no network, not JSON, not 2xx). Never throws. */
export async function fetchStatus(fetcher: Fetcher = (u, i) => fetch(u, i)): Promise<unknown> {
  try {
    const res = await fetcher(STATUS_URL, { method: 'GET', headers: { Accept: 'application/json' } })
    if (!res.ok) return null
    return (await res.json()) as unknown
  } catch {
    return null
  }
}

export const PREVIEW_URL = '../v1/forms/preview?images=1&dpi=150'

/** POST /v1/forms/preview (wave 10, FP-contract.md): page pictures and the places of the finder's candidates for
 * the same file. A read-only side call: any failure (no route, BUSY, a refusal, no network) is null, and the rest
 * of the page works without it. */
export async function previewFile(file: File, token: string, fetcher: Fetcher = (u, i) => fetch(u, i)): Promise<unknown> {
  try {
    const body = new FormData()
    body.append('file', file, uploadName(file.name))
    const headers: Record<string, string> = {}
    if (token.trim()) headers['Authorization'] = 'Bearer ' + token.trim()
    const res = await fetcher(PREVIEW_URL, { method: 'POST', body, headers })
    if (res.status !== 200) return null
    return (await res.json()) as unknown
  } catch {
    return null
  }
}

// ---- W11 FLOW: jobs (POST /v1/jobs, GET /v1/jobs/{id}, GET /v1/jobs/{id}/result) -----------------------------------
// The file is taken at once, waits its turn in the service's bounded queue, and the service tells where it is: the
// place in the queue, the stage, and the finished parts of the work. The page shows exactly that and adds nothing.

export interface JobStage { name: string; step: string | null; page: number | null; pages: number | null }

export interface JobStatus {
  id: string
  state: 'queued' | 'running' | 'done' | 'error' | 'cancelled'
  /** place among the waiting jobs, 1 = the next to start; null when not waiting */
  position: number | null
  queue: { running: number; waiting: number; waitingMax: number } | null
  stage: JobStage | null
  /** finished parts of the work and all parts, as the conversion reported them; never a clock */
  units: { done: number; total: number } | null
  /** seconds since the conversion last reported something (the service's own clock) */
  stageS: number | null
}

const num = (x: unknown): number | null => (typeof x === 'number' && Number.isFinite(x) ? x : null)
const JOB_STATES: readonly string[] = ['queued', 'running', 'done', 'error', 'cancelled']

/** The body of a job answer, or null when it is not one. Unknown keys are ignored, missing ones are null. */
export function parseJobStatus(raw: unknown): JobStatus | null {
  if (!raw || typeof raw !== 'object') return null
  const o = raw as Record<string, unknown>
  if (typeof o.id !== 'string' || !o.id || typeof o.state !== 'string' || !JOB_STATES.includes(o.state)) return null
  const q = o.queue as Record<string, unknown> | undefined
  const s = o.stage as Record<string, unknown> | undefined
  const u = o.units as Record<string, unknown> | undefined
  const done = u ? num(u.done) : null
  const total = u ? num(u.total) : null
  return {
    id: o.id,
    state: o.state as JobStatus['state'],
    position: num(o.position),
    queue: q && num(q.running) !== null && num(q.waiting) !== null
      ? { running: num(q.running)!, waiting: num(q.waiting)!, waitingMax: num(q.waiting_max) ?? 0 } : null,
    stage: s && typeof s.name === 'string'
      ? { name: s.name, step: typeof s.step === 'string' ? s.step : null, page: num(s.page), pages: num(s.pages) } : null,
    units: done !== null && total !== null && total > 0 ? { done: Math.max(0, Math.min(done, total)), total } : null,
    stageS: num(o.stage_s)
  }
}

export const JOBS_URL = '../v1/jobs'
/** How often the page asks for the state of a job. */
export const POLL_MS = 1000
/** After this many state questions in a row without an answer the page stops waiting (NETWORK). */
export const POLL_FAILS_MAX = 20
/** A full queue: the page waits and offers the file again, at most this many times. */
export const FULL_TRIES_MAX = 90
/** The job is unknown to the service (it restarted, or the result expired). */
export const JOB_LOST = 'JOB_LOST'

export interface Answer { status: number; headers: Pick<Headers, 'get'>; bytes: Uint8Array }

/** What convertQueued needs from the outside; tests replace it. */
export interface JobIo {
  /** POST the file to JOBS_URL; `onSent` gets the bytes that left the browser. Rejects on a network failure. */
  submit: (file: File, token: string, onSent: (loaded: number, total: number) => void, signal?: AbortSignal) => Promise<Answer>
  fetcher: Fetcher
  /** Resolves after `ms`, or at once when the signal aborts. */
  sleep: (ms: number, signal?: AbortSignal) => Promise<void>
  /** The request the page made before jobs existed; used when the service has no /v1/jobs (an older build). */
  direct: (file: File, token: string, hooks: ConvertHooks) => Promise<Outcome>
}

function authHeaders(token: string): Record<string, string> {
  return token.trim() ? { Authorization: 'Bearer ' + token.trim() } : {}
}

function xhrSubmit(file: File, token: string, onSent: (loaded: number, total: number) => void, signal?: AbortSignal): Promise<Answer> {
  return new Promise<Answer>((resolve, reject) => {
    const body = new FormData()
    body.append('file', file, uploadName(file.name))
    const xhr = new XMLHttpRequest()
    xhr.open('POST', JOBS_URL)
    xhr.responseType = 'arraybuffer'
    if (token.trim()) xhr.setRequestHeader('Authorization', 'Bearer ' + token.trim())
    xhr.upload.addEventListener('progress', (e) => { if (e.lengthComputable) onSent(e.loaded, e.total) })
    xhr.addEventListener('load', () => resolve({
      status: xhr.status,
      headers: { get: (name: string) => xhr.getResponseHeader(name) },
      bytes: new Uint8Array((xhr.response as ArrayBuffer | null) ?? new ArrayBuffer(0))
    }))
    xhr.addEventListener('error', () => reject(new Error('network')))
    xhr.addEventListener('timeout', () => reject(new Error('network')))
    xhr.addEventListener('abort', () => reject(new Error(CANCELLED)))
    if (signal) {
      if (signal.aborted) { reject(new Error(CANCELLED)); return }
      signal.addEventListener('abort', () => xhr.abort())
    }
    xhr.send(body)
  })
}

function sleepFor(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise<void>((resolve) => {
    if (signal?.aborted) { resolve(); return }
    const timer = setTimeout(done, ms)
    function done(): void { clearTimeout(timer); signal?.removeEventListener('abort', done); resolve() }
    signal?.addEventListener('abort', done)
  })
}

export const defaultJobIo: JobIo = {
  submit: xhrSubmit,
  fetcher: (u, i) => fetch(u, i),
  sleep: sleepFor,
  direct: (file, token, hooks) => convertWithProgress(file, token, hooks)
}

function jsonOf(bytes: Uint8Array): unknown {
  try { return JSON.parse(new TextDecoder().decode(bytes)) as unknown } catch { return null }
}

/** One file through the service's queue. Resolves with the same Outcome as convertWithProgress; on the way the
 * hooks are told what the service said (never a guess of the page):
 *  - onSent: bytes of the file that left the browser;
 *  - onUploaded: the service has taken the file (202);
 *  - onFull: the queue had no room (429 QUEUE_FULL); the page waits `retryS` seconds and offers the file again;
 *  - onStatus: every answer about the job; onSilent: questions in a row that got no answer.
 * A service without /v1/jobs (404 or 405) gets the old single request instead. */
export async function convertQueued(file: File, token: string, hooks: ConvertHooks = {}, io: JobIo = defaultJobIo): Promise<Outcome> {
  const fail = (code: string, status = 0): Problem => ({ kind: 'error', code, status, detail: null, title: null })
  const signal = hooks.signal
  let taken: JobStatus | null = null
  for (let tries = 0; taken === null; tries++) {
    if (signal?.aborted) return fail(CANCELLED)
    let res: Answer
    try {
      res = await io.submit(file, token, (loaded, total) => hooks.onSent?.(loaded, total), signal)
    } catch (e) {
      return fail(signal?.aborted || (e instanceof Error && e.message === CANCELLED) ? CANCELLED : 'NETWORK')
    }
    if (res.status === 404 || res.status === 405) return io.direct(file, token, hooks)
    if (res.status === 202) {
      taken = parseJobStatus(jsonOf(res.bytes))
      if (taken === null) return fail('BAD_ANSWER', res.status)
      break
    }
    const problem = problemFrom(res.status, res.headers.get('content-type'), new TextDecoder().decode(res.bytes))
    if (problem.code !== 'QUEUE_FULL' || tries + 1 >= FULL_TRIES_MAX) return problem
    const asked = Number(res.headers.get('retry-after'))
    const retryS = Number.isFinite(asked) && asked > 0 ? Math.min(asked, 60) : 10
    hooks.onFull?.(retryS)
    await io.sleep(retryS * 1000, signal)
  }
  hooks.onUploaded?.()
  hooks.onStatus?.(taken)
  const url = `${JOBS_URL}/${encodeURIComponent(taken.id)}`
  const headers = authHeaders(token)
  const giveUp = (): void => { void io.fetcher(url, { method: 'DELETE', headers }).catch(() => undefined) }
  let silent = 0
  let state: JobStatus = taken
  while (state.state === 'queued' || state.state === 'running') {
    await io.sleep(POLL_MS, signal)
    if (signal?.aborted) { giveUp(); return fail(CANCELLED) }
    let next: JobStatus | null = null
    let status = 0
    try {
      const res = await io.fetcher(url, { method: 'GET', headers: { ...headers, Accept: 'application/json' } })
      status = res.status
      next = res.ok ? parseJobStatus(await res.json()) : null
    } catch {
      next = null
    }
    if (status === 404) return fail(JOB_LOST, 404)
    if (next === null) {
      silent += 1
      hooks.onSilent?.(silent)
      if (silent >= POLL_FAILS_MAX) return fail('NETWORK')
      continue
    }
    silent = 0
    state = next
    hooks.onStatus?.(state)
  }
  if (state.state === 'cancelled') return fail(CANCELLED)
  try {
    const res = await io.fetcher(`${url}/result?report=1`, { method: 'GET', headers })
    if (res.status === 404) return fail(JOB_LOST, 404)
    if (res.status === 202) return fail('BAD_ANSWER', 202)
    return await interpretResponse(res.status, res.headers, new Uint8Array(await res.arrayBuffer()))
  } catch {
    return fail('NETWORK')
  }
}
