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
    hash
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
