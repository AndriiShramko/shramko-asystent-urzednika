// BL13 CLERK-T: what a box of the original stands for in the e-form. Every place the finder drew a box for gets a
// target: the field it became, the fields of the standard section that took it over (name -> "Twoje dane" Imię and
// Nazwisko, address -> the address section, phone / e-mail -> the contact section), the field a merged blank joined,
// or a short plain note when the place on purpose did not become a field (signature and date, office use…). The
// rule is testable: the ledger row of the candidate and the section titles of the form, nothing guessed from text
// beyond the paper's own label of the box (attrOfLabel).
import type { ENode, FormModel } from './form'
import { CONTAINER_TYPES } from './form'
import { attrOfLabel, type Attr, type LedgerRow, type Place, type Preview } from './places'

export type TargetKind = 'field' | 'standard' | 'merged' | 'out' | 'wait' | 'none'

export interface BoxTarget {
  cid: string
  place: Place
  kind: TargetKind
  /** e-form node ids to scroll to (the first) and light (all) */
  fields: string[]
  /** LEFT_OUT reason, when the place on purpose has no field */
  reason: string | null
  /** the server's own plain sentence for a paper-only place (sidecar INPUT_NOTE, rule paper_only.*), Polish */
  text?: string
}

export interface PaperOnly { reason: string; text: string }

/** Paper-only places the converter reports in the sidecar (INPUT_NOTE with an applied fix of rule paper_only.*). */
export function paperOnlyNotes(warnings: unknown): Map<string, PaperOnly> {
  const m = new Map<string, PaperOnly>()
  for (const w of Array.isArray(warnings) ? warnings as Record<string, unknown>[] : []) {
    const fix = (w?.fix ?? {}) as Record<string, unknown>
    const rule = typeof fix.rule === 'string' ? fix.rule : ''
    if (typeof w?.candidate !== 'string' || fix.kind !== 'applied' || !rule.startsWith('paper_only.')) continue
    const reason = rule === 'paper_only.signature_and_date' ? 'SIGNATURE_AND_DATE' : rule === 'paper_only.office_use' ? 'OFFICE_USE' : 'OTHER'
    m.set(w.candidate, { reason, text: typeof fix.text === 'string' ? fix.text.trim() : '' })
  }
  return m
}

/** Without a ledger row: a place the finder itself calls a signature, a date or office use is on purpose no field. */
function ownRule(place: Place): string | null {
  const label = norm(place.label ?? '')
  if (place.kind === 'signature' || /^(podpis|czytelny podpis)/.test(label)) return 'SIGNATURE_AND_DATE'
  if (/^data( zlozenia| wypelnienia)?/.test(label) && !/urodzenia/.test(label)) return 'SIGNATURE_AND_DATE'
  if (place.kind === 'office_use') return 'OFFICE_USE'
  return null
}

const norm = (s: string): string => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ł/g, 'l').replace(/\s+/g, ' ').trim()

/** The top section of the form a ledger section key (`standard/twoje_dane`, `standard/adres`…) stands for. */
export function sectionNode(model: FormModel, section: string): ENode | null {
  const key = section.replace(/^standard\//, '')
  const tops = model.all.filter((n) => n.parent === null && CONTAINER_TYPES.has(n.type))
  const words = norm(key.replace(/_/g, ' '))
  const exact = tops.find((n) => norm(n.title) === words) ?? tops.find((n) => norm(n.title).startsWith(words))
  if (exact) return exact
  const test: RegExp | null = key === 'twoje_dane' ? /^twoje dane|^dane wnioskodawcy/
    : key === 'dane_do_kontaktu' || key.includes('kontakt') ? /kontakt/
      : /korespond/.test(key) ? /^adres.*korespond/
        : /siedzib/.test(key) ? /^adres.*siedzib/
          : key.startsWith('adres') ? /^adres zamieszkania$|^adres$/
            : null
  return test ? tops.find((n) => test.test(norm(n.title))) ?? null : null
}

const CHILD: Partial<Record<Attr, RegExp>> = {
  name: /^imie/, surname: /^nazwisko/, pesel: /pesel/, postCode: /kod pocztowy/, street: /^ulica/,
  building: /(numer|nr) (budynku|domu)/, apartment: /(numer|nr) (lokalu|mieszkania)/, place: /^miejscowosc/,
  phone: /telefon/, email: /e-?mail/
}

function walk(n: ENode, out: ENode[]): void { for (const c of n.children) { out.push(c); walk(c, out) } }

/** The fields of a standard section a place with this label stands for; the section itself when the label names
 * the whole of it (an address in one line) or names nothing we know. */
export function standardFields(sec: ENode, attr: Attr | null): string[] {
  const kids: ENode[] = []
  walk(sec, kids)
  const pick = (a: Attr): string | null => { const re = CHILD[a]; const k = re ? kids.find((c) => re.test(norm(c.title))) : undefined; return k?.id ?? null }
  if (attr === 'fullname' || attr === 'fullname_rev') {
    const ids = [pick('name'), pick('surname')].filter((x): x is string => !!x)
    if (attr === 'fullname_rev') ids.reverse()
    return ids.length ? ids : [sec.id]
  }
  if (attr && attr !== 'address') { const id = pick(attr); if (id) return [id] }
  return [sec.id]
}

/** One label may name two things ("nr telefonu/adres e-mail"): every attribute it names, in its order. */
export function attrsOfLabel(label: string): Attr[] {
  const parts = label.split(/\s*[/;]\s*|\s+lub\s+|\s+albo\s+/).filter(Boolean)
  const whole = attrOfLabel(label)
  const out: Attr[] = []
  for (const p of parts) { const a = attrOfLabel(p); if (a && !out.includes(a)) out.push(a) }
  // a label that names one thing as a whole ("imię i nazwisko/nazwa") keeps that thing
  if (whole && (out.length <= 1 || out.includes(whole) === false)) return [whole]
  return out.length ? out : whole ? [whole] : []
}

/** candidate id -> its target, for every ledger row whose place the preview knows. */
export function boxTargets(rows: LedgerRow[], pv: Preview, model: FormModel, notes: Map<string, PaperOnly> = new Map()): Map<string, BoxTarget> {
  const out = new Map<string, BoxTarget>()
  const byCid = new Map(rows.map((r) => [r.candidate, r]))
  const fieldsOf = (r: LedgerRow, depth: number): { kind: TargetKind; fields: string[]; reason: string | null } => {
    if (r.fate === 'FIELD' && r.field && model.byId.has(r.field)) return { kind: 'field', fields: [r.field], reason: null }
    if (r.fate === 'STANDARD' && r.section) {
      const sec = sectionNode(model, r.section)
      const label = pv.places[r.candidate]?.label
      if (sec) {
        const attrs = label ? attrsOfLabel(label) : []
        const ids = attrs.length ? [...new Set(attrs.flatMap((a) => standardFields(sec, a)))] : [sec.id]
        // two named things of which one is not in the section: the section's own match only
        const exact = ids.filter((id) => id !== sec.id)
        return { kind: 'standard', fields: exact.length ? exact : [sec.id], reason: null }
      }
    }
    if (r.fate === 'MERGED' && r.into && depth < 8) {
      const into = byCid.get(r.into)
      if (into) { const t = fieldsOf(into, depth + 1); if (t.fields.length) return { kind: 'merged', fields: t.fields, reason: null } }
    }
    if (r.fate === 'LEFT_OUT') return { kind: 'out', fields: [], reason: r.reason ?? 'OTHER' }
    if (r.fate === 'AWAITING_DECISION') return { kind: 'wait', fields: [], reason: null }
    return { kind: 'none', fields: [], reason: null }
  }
  for (const r of rows) {
    const place = pv.places[r.candidate]
    if (!place) continue
    const t = fieldsOf(r, 0)
    out.set(r.candidate, { cid: r.candidate, place, ...t })
    // the marks of a choice group lead to the group's field
    for (const o of place.options ?? []) {
      const m = o.mark ? pv.places[o.mark] : undefined
      if (o.mark && m && !out.has(o.mark)) out.set(o.mark, { cid: o.mark, place: m, ...t })
    }
  }
  // the server's paper-only notes win over our own wording; a place that became a field keeps its field
  for (const [cid, n] of notes) {
    const place = pv.places[cid]
    const had = out.get(cid)
    if (!place || (had && had.fields.length)) continue
    out.set(cid, { cid, place, kind: 'out', fields: [], reason: n.reason, text: n.text || undefined })
  }
  // no ledger row and no note: the finder's own kind or label of a signature, date or office place
  for (const [cid, place] of Object.entries(pv.places)) {
    if (out.has(cid) || !place.box) continue
    const reason = ownRule(place)
    if (reason) out.set(cid, { cid, place, kind: 'out', fields: [], reason })
  }
  return out
}

/** e-form node id -> the candidate whose box stands for it (the first one in ledger order). */
export function fieldBoxes(targets: Map<string, BoxTarget>): Map<string, string> {
  const m = new Map<string, string>()
  for (const t of targets.values()) for (const f of t.fields) if (!m.has(f) && t.place.box) m.set(f, t.cid)
  return m
}

/** Does a click on this box answer with something: a field to show or a note. */
export const answers = (t: BoxTarget | undefined): boolean => !!t && (t.fields.length > 0 || t.kind === 'out' || t.kind === 'wait')
