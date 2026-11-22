// The one call the page makes: POST /v1/forms/convert?report=1 with the file and an optional bearer token.
// The address is relative to the page (served under /ui/), so nothing leaves the origin it came from.
import { boundaryOf, parseMultipart } from './multipart'
import { parseWarningsHeader, type HeaderWarnings } from './warnings'
import type { Sidecar } from './model'

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
  body.append('file', file, file.name)
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
    body.append('file', file, file.name)
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
