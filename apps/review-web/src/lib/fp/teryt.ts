// The address registers the page serves from its own origin (public/teryt/, built by scripts/teryt-build.mjs from
// the official GUS TERYT files TERC, SIMC, ULIC; postal codes from GeoNames, CC BY 4.0). Read only when an address
// field gets focus; nothing here calls any other host. Every text of the files is data: it is shown as text.

export interface Locality {
  name: string
  /** SIMC identifier of the locality (7 digits). */
  sym: string
  /** wieś, miasto, osada… (SIMC "rodzaj miejscowości"). */
  kind: string
  gmina: string
  powiat: string
  woj: string
  /** TERC code of the województwo (2 digits): the street file to read. */
  wojCode: string
  /** How many streets the ULIC register lists here (0: an address without a street). */
  streets: number
  /** Postal codes as packed runs ("85001:85018,85021"); '' when the open set has none for this place. */
  codes: string
}

export interface Register {
  /** "TERC 2026-01-01, SIMC …, ULIC …": the state of the registers as the files say. */
  stan: string
  size: number
  /** Localities whose name starts with the typed letters (accents and case aside): exact names first, then larger places. */
  search(typed: string, limit?: number): Locality[]
  /** Localities with exactly this name. */
  named(name: string): Locality[]
}

export interface Street { name: string; key: string }
export interface StreetBook { of(sym: string): Street[] }

const KINDS: Record<string, string> = { '01': 'wieś', '02': 'kolonia', '03': 'przysiółek', '04': 'osada', '05': 'osada leśna',
  '06': 'osiedle', '07': 'schronisko turystyczne', '96': 'miasto' }

/** Lower case, no accents, ł as l: what a person types without Polish letters still finds the name. */
export function fold(s: string): string {
  return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ł/g, 'l').replace(/\s+/g, ' ').trim()
}

export function parseLocalities(text: string): Register {
  const woj = new Map<string, string>()
  const pow = new Map<string, string>()
  const gmi: [string, string][] = []
  const rows: Locality[] = []
  const keys: string[] = []
  let stan = ''
  for (const line of text.split('\n')) {
    const c = line.split('|')
    switch (c[0]) {
      case 'W': woj.set(c[1], c[2]); break
      case 'P': pow.set(c[1], c[2]); break
      case 'G': gmi.push([c[1], c[2]]); break
      case 'M': {
        const g = gmi[Number(c[2])]
        if (!g || !c[1]) break
        rows.push({ name: c[1], sym: c[3], kind: KINDS[c[4]] ?? 'miejscowość', gmina: g[1], powiat: pow.get(g[0].slice(0, 4)) ?? '',
          woj: woj.get(g[0].slice(0, 2)) ?? '', wojCode: g[0].slice(0, 2), streets: Number(c[5]) || 0, codes: c[6] ?? '' })
        keys.push(fold(c[1]))
        break
      }
      default:
        if (line.startsWith('#TERYT')) stan = c.slice(1, 4).join(', ')
    }
  }
  return {
    stan,
    size: rows.length,
    search(typed, limit = 8) {
      const q = fold(typed)
      if (q.length < 2) return []
      const exact: Locality[] = []
      const starts: Locality[] = []
      for (let i = 0; i < keys.length; i++) {
        const k = keys[i]
        if (!k.startsWith(q)) continue
        if (k.length === q.length) { if (exact.length < limit) exact.push(rows[i]) } else if (starts.length < limit) starts.push(rows[i])
      }
      return [...exact, ...starts].slice(0, limit)
    },
    named(name) {
      const q = fold(name)
      const out: Locality[] = []
      if (!q) return out
      for (let i = 0; i < keys.length; i++) if (keys[i] === q) out.push(rows[i])
      return out
    }
  }
}

/** What goes into a street field: "Kujawska", "al. Jana Pawła II", "pl. Wolności" (the plain "ul." is not written). */
function streetName(cecha: string, first: string, main: string): string {
  const body = [first, main].filter(Boolean).join(' ')
  return cecha && cecha !== 'ul.' ? `${cecha} ${body}` : body
}

export function parseStreets(text: string): StreetBook {
  const names: Street[] = []
  const lists = new Map<string, string>()
  for (const line of text.split('\n')) {
    if (line.startsWith('N|')) {
      const [cecha, first, main] = line.slice(2).split(';')
      const name = streetName(cecha ?? '', first ?? '', main ?? '')
      names.push({ name, key: fold(`${main ?? ''} ${first ?? ''}`) })
    } else if (line.startsWith('L|')) {
      const bar = line.indexOf('|', 2)
      lists.set(line.slice(2, bar), line.slice(bar + 1))
    }
  }
  const cache = new Map<string, Street[]>()
  return {
    of(sym) {
      const hit = cache.get(sym)
      if (hit) return hit
      const out: Street[] = []
      let at = 0
      for (const part of (lists.get(sym) ?? '').split(',')) {
        if (!part) continue
        at += parseInt(part, 36)
        const s = names[at]
        if (s) out.push(s)
      }
      cache.set(sym, out)
      return out
    }
  }
}

/** Streets of one locality that have a word starting with the typed letters; names that start with them come first. */
export function searchStreets(streets: Street[], typed: string, limit = 8): Street[] {
  const q = fold(typed.replace(/^\s*(ul\.?|ulica)\s+/i, ''))
  if (!q) return streets.slice(0, limit)
  const first: Street[] = []
  const inside: Street[] = []
  for (const s of streets) {
    if (s.key.startsWith(q) || fold(s.name).startsWith(q)) first.push(s)
    else if (s.key.includes(' ' + q)) inside.push(s)
    if (first.length >= limit) break
  }
  return [...first, ...inside].slice(0, limit)
}

const show = (n: number): string => { const s = String(n).padStart(5, '0'); return `${s.slice(0, 2)}-${s.slice(2)}` }

/** The postal codes of a locality, written out (at most `limit`, in order); [] when the set has none. */
export function codesOf(loc: Locality, limit = 2000): string[] {
  const out: string[] = []
  for (const run of loc.codes.split(',')) {
    if (!run) continue
    const [a, b] = run.split(':').map(Number)
    for (let n = a; n <= (b ?? a) && out.length < limit; n++) out.push(show(n))
    if (out.length >= limit) break
  }
  return out
}

/** true: the code is one of the locality's; false: it is not; null: the set knows no code here, or the value is not a code. */
export function codeFits(loc: Locality, code: string): boolean | null {
  const m = /^(\d{2})-(\d{3})$/.exec(code.trim())
  if (!m || !loc.codes) return null
  const n = Number(m[1] + m[2])
  for (const run of loc.codes.split(',')) {
    const [a, b] = run.split(':').map(Number)
    if (n >= a && n <= (b ?? a)) return true
  }
  return false
}

/** One line under a hint: "miasto, gm. Bydgoszcz, pow. Bydgoszcz, woj. kujawsko-pomorskie". */
export function describe(loc: Locality): string {
  return `${loc.kind}, gm. ${loc.gmina}, pow. ${loc.powiat}, woj. ${loc.woj}`
}

/** The four levels of the partner's multi-level TERYT dictionary, from the top. */
export function terytPath(loc: Locality): string {
  return `${loc.woj} / ${loc.powiat} / ${loc.gmina} / ${loc.name}`
}

// ---- loading: once, from the page's own folder --------------------------------------------------------------------
export type FetchText = (path: string) => Promise<string>

const viaFetch: FetchText = async (path) => {
  const res = await fetch(path)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.text()
}

export interface TerytSource { localities(): Promise<Register>; streets(wojCode: string): Promise<StreetBook> }

export function terytSource(fetchText: FetchText = viaFetch, base = './teryt/'): TerytSource {
  let reg: Promise<Register> | null = null
  const books = new Map<string, Promise<StreetBook>>()
  return {
    localities() {
      reg ??= fetchText(base + 'miejscowosci.txt').then(parseLocalities)
      reg.catch(() => { reg = null })
      return reg
    },
    streets(wojCode) {
      if (!/^\d{2}$/.test(wojCode)) return Promise.reject(new Error('bad code'))
      let b = books.get(wojCode)
      if (!b) {
        b = fetchText(`${base}ulice-${wojCode}.txt`).then(parseStreets)
        books.set(wojCode, b)
        b.catch(() => books.delete(wojCode))
      }
      return b
    }
  }
}
