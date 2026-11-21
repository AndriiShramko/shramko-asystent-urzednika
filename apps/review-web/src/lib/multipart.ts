// A reader for the `multipart/mixed` answer of POST /v1/forms/convert?report=1. It works on bytes and never
// decodes the payload: the form part must stay byte-equal to what the service sent (decision D1).

export interface Part {
  headers: Record<string, string>
  filename: string | null
  body: Uint8Array
}

const enc = new TextEncoder()
const dec = new TextDecoder('utf-8')

export function boundaryOf(contentType: string | null): string | null {
  if (!contentType) return null
  const m = /boundary=(?:"([^"]+)"|([^;\s]+))/i.exec(contentType)
  return m ? (m[1] ?? m[2] ?? null) : null
}

function indexOf(hay: Uint8Array, needle: Uint8Array, from: number): number {
  outer: for (let i = from; i <= hay.length - needle.length; i++) {
    for (let j = 0; j < needle.length; j++) if (hay[i + j] !== needle[j]) continue outer
    return i
  }
  return -1
}

export function parseMultipart(bytes: Uint8Array, boundary: string): Part[] {
  const delim = enc.encode('--' + boundary)
  const crlf2 = enc.encode('\r\n\r\n')
  const parts: Part[] = []
  let pos = indexOf(bytes, delim, 0)
  while (pos >= 0) {
    let start = pos + delim.length
    if (bytes[start] === 0x2d && bytes[start + 1] === 0x2d) break // closing delimiter
    if (bytes[start] === 0x0d && bytes[start + 1] === 0x0a) start += 2
    const next = indexOf(bytes, delim, start)
    if (next < 0) break
    let end = next
    if (bytes[end - 2] === 0x0d && bytes[end - 1] === 0x0a) end -= 2 // the CRLF belongs to the delimiter
    const headEnd = indexOf(bytes.subarray(0, end), crlf2, start)
    const headText = headEnd >= 0 ? dec.decode(bytes.subarray(start, headEnd)) : ''
    const bodyStart = headEnd >= 0 ? headEnd + 4 : start
    const headers: Record<string, string> = {}
    for (const line of headText.split('\r\n')) {
      const i = line.indexOf(':')
      if (i > 0) headers[line.slice(0, i).trim().toLowerCase()] = line.slice(i + 1).trim()
    }
    const fm = /filename="([^"]*)"/i.exec(headers['content-disposition'] ?? '')
    parts.push({ headers, filename: fm ? fm[1] : null, body: bytes.slice(bodyStart, Math.max(bodyStart, end)) })
    pos = next
  }
  return parts
}
