// Wave 10 DICT: the dictionaries of the report (task card points I and II, the partner's "Słowniki"). The service
// writes them into the sidecar's `meta` only when it has something to say (converter `compose/dictionaries.py`):
//   meta.proposals.dictionaries[]: a proposed NEW dictionary (contract `ProposedDictionary`): name, entries, field,
//     fields, why, use, pages, evidence;
//   meta.dictionary_links[]: a field of the paper that takes a dictionary of the partner (`DictionaryLink`): field,
//     label, dictionary, written, why.
// Everything here is data from the service: a missing or malformed key is left out, never guessed.
import type { Sidecar } from './model'

export interface ProposedDict {
  name: string
  entries: string[]
  why: string | null
  use: string | null
  /** form ids of the fields that would take the dictionary (`fields`, else `field`) */
  fields: string[]
  pages: number[]
}

export interface DictLink {
  field: string
  label: string
  dictionary: string
  written: boolean
  why: string | null
}

export interface Dictionaries {
  proposals: ProposedDict[]
  links: DictLink[]
}

const str = (x: unknown): string | null => (typeof x === 'string' && x.trim() ? x.trim() : null)
const rec = (x: unknown): Record<string, unknown> | null =>
  x && typeof x === 'object' && !Array.isArray(x) ? (x as Record<string, unknown>) : null

function proposal(raw: unknown): ProposedDict | null {
  const r = rec(raw)
  const name = r ? str(r.name) : null
  if (!r || !name) return null
  const entries = Array.isArray(r.entries) ? r.entries.map(str).filter((e): e is string => e !== null) : []
  const fields = Array.isArray(r.fields) ? r.fields.map(str).filter((e): e is string => e !== null) : []
  const one = str(r.field)
  if (!fields.length && one) fields.push(one)
  const pages = Array.isArray(r.pages) ? r.pages.filter((p): p is number => typeof p === 'number') : []
  return { name, entries, why: str(r.why), use: str(r.use), fields, pages }
}

function link(raw: unknown): DictLink | null {
  const r = rec(raw)
  const dictionary = r ? str(r.dictionary) : null
  if (!r || !dictionary) return null
  return { field: str(r.field) ?? '', label: str(r.label) ?? '', dictionary, written: r.written === true, why: str(r.why) }
}

/** The dictionaries of one report; both lists empty when the sidecar has none (or there is no sidecar). */
export function readDictionaries(sidecar: Sidecar | null): Dictionaries {
  const meta = rec(sidecar?.meta) ?? {}
  const props = rec(meta.proposals)
  const rawProps = props && Array.isArray(props.dictionaries) ? props.dictionaries : []
  const rawLinks = Array.isArray(meta.dictionary_links) ? meta.dictionary_links : []
  return {
    proposals: rawProps.map(proposal).filter((p): p is ProposedDict => p !== null),
    links: rawLinks.map(link).filter((l): l is DictLink => l !== null)
  }
}
