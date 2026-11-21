// Synthetic fixtures: a small form in the partner's shape and a sidecar in the shape the service sends today.
// No value here is a real one; the labels are invented.
const enc = new TextEncoder()

export function field(id: string, type: string, title: string, extra: Record<string, unknown> = {}) {
  return { id, type, techName: title.toLowerCase().replace(/[^a-z]+/g, '_'), title, description: '', options: [],
    validation: [], readOnly: false, repeatingSectionGrid: [], states: [], tooltipMessage: '', ...extra }
}

export function cell(f: unknown, y = 0) {
  return { x: 0, y, rows: 1, cols: 3, field: f }
}

export function syntheticForm() {
  const matterSection = field('s-1', 'SECTION', 'Sprawa', {
    repeatingSectionGrid: [
      cell(field('f-1', 'TEXT_FIELD', 'Nazwa ulicy', { validation: ['REQUIRED'] })),
      cell(field('f-2', 'RADIO', 'Rodzaj sprawy', { options: [{ id: 'a', name: 'Pierwszy', techName: 'a' }, { id: 'b', name: 'Drugi', techName: 'b' }] }), 1),
      cell(field('f-3', 'TEXT_BLOCK', 'Tekst stały'), 2)
    ]
  })
  const standardSection = field('s-2', 'SECTION', 'Dane wnioskodawcy', {
    repeatingSectionGrid: [cell(field('f-4', 'TEXT_FIELD', 'Imię')), cell(field('f-5', 'TEXT_FIELD', 'Nazwisko'), 1)]
  })
  return {
    title: 'Wniosek próbny',
    tabs: [
      { id: 't-1', title: 'Dane', type: 'MAIN', questions: [cell(standardSection)] },
      { id: 't-2', title: 'Szczegóły sprawy', type: 'MAIN', questions: [cell(matterSection)] }
    ],
    flow: { links: [] }
  }
}

export function syntheticSidecar() {
  return {
    version: 1,
    converter: { version: '0.1.0', pipeline: 'brief', reader: 'pdf.native' },
    counts: { pages: 2, fields: 4, source_pages: 1 },
    warnings: [
      { code: 'LABEL_NOT_FOUND', page: 1, box: [1, 2, 3, 4], candidate: 'c1', evidence: [], detail: 'a box without words beside it' },
      { code: 'LABEL_NOT_FOUND', page: 1, candidate: 'c2', evidence: [], detail: 'another box' },
      { code: 'SOMETHING_NEW', detail: 'a code the page does not know' }
    ],
    checks: [],
    meta: {
      origins: { 's-2': 'standard', 'f-4': 'standard', 'f-5': 'standard', 's-1': 'paper', 'f-1': 'paper', 'f-2': 'paper' },
      evidence: {
        'f-1': { page: 2, quote: 'Nazwa ulicy ………', candidate: 'c1' },
        'f-2': [{ page: 2, anchor: 'p[3]' }, { quote: 'Rodzaj sprawy' }]
      }
    }
  }
}

export async function sha256(bytes: Uint8Array): Promise<string> {
  const d = await crypto.subtle.digest('SHA-256', bytes as BufferSource)
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, '0')).join('')
}

/** The body the service builds for ?report=1: form.json and meta.json as multipart/mixed (app/main.py). */
export function multipartBody(form: Uint8Array, meta: Uint8Array | null, boundary = 'formularze-abc123'): Uint8Array {
  const chunks: Uint8Array[] = []
  const add = (name: string, payload: Uint8Array) => {
    chunks.push(enc.encode(`--${boundary}\r\nContent-Type: application/json\r\nContent-Disposition: attachment; filename="${name}"\r\n\r\n`), payload, enc.encode('\r\n'))
  }
  add('form.json', form)
  if (meta) add('meta.json', meta)
  chunks.push(enc.encode(`--${boundary}--\r\n`))
  const out = new Uint8Array(chunks.reduce((n, c) => n + c.length, 0))
  let o = 0
  for (const c of chunks) { out.set(c, o); o += c.length }
  return out
}

export function canonical(obj: unknown): Uint8Array {
  return enc.encode(JSON.stringify(obj))
}
