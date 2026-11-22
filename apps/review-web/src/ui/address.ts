// Address hints of the trial fill (W11 ADDR). Typing the first letters of a locality offers real Polish localities
// from the TERYT register; a click fills the locality and, where the form has them, gmina, powiat, województwo and
// the postal code when the locality has exactly one. The street field offers the streets of that locality (ULIC).
// The registers are files of this page's own folder, read on the first focus of an address field: no other host.
import { h, clear } from './dom'
import type { ENode } from '../lib/fp/form'
import { codeFits, codesOf, describe, fold, searchStreets, terytPath, terytSource, type Locality, type TerytSource } from '../lib/fp/teryt'
import type { EForm } from './eform'

export type Role = 'locality' | 'teryt' | 'street' | 'postal' | 'gmina' | 'powiat' | 'woj'

const TXT = {
  loading: 'Wczytywanie rejestru TERYT…',
  start: 'Wpisz pierwsze litery miejscowości: podpowiemy ją razem z gminą, powiatem i województwem (rejestr TERYT GUS).',
  example: 'np. Bydgoszcz',
  chosen: (loc: Locality): string => `Wybrano: ${loc.name} (${loc.kind}), gmina ${loc.gmina}, powiat ${loc.powiat}, województwo ${loc.woj}.`,
  unavailable: 'Podpowiedzi adresowe są niedostępne (brak plików rejestru TERYT w tej instalacji). Adres można wpisać ręcznie.',
  source: (stan: string): string => `Źródło: rejestr TERYT GUS (${stan}). Wybierz z listy albo wpisz własną wartość.`,
  none: 'Brak takiej miejscowości w rejestrze TERYT. Sprawdź pisownię albo wpisz nazwę ręcznie.',
  filled: (what: string): string => `Uzupełniono z rejestru TERYT: ${what}.`,
  pickFirst: 'Najpierw wybierz miejscowość z listy, wtedy podpowiemy jej ulice.',
  noStreets: (name: string): string => `W miejscowości ${name} rejestr ULIC nie ma ulic: adres bez ulicy (pole może zostać puste).`,
  streetsOf: (loc: Locality, n: number): string => `Ulice miejscowości ${loc.name} (pow. ${loc.powiat}): ${n} w rejestrze ULIC GUS.`,
  noStreet: (name: string): string => `Takiej ulicy nie ma w rejestrze ULIC dla miejscowości ${name}. Sprawdź pisownię.`,
  codeOff: (code: string, name: string, some: string): string =>
    `Kod pocztowy ${code} nie występuje w zbiorze kodów miejscowości ${name} (${some}). Sprawdź kod albo miejscowość.`,
  codesOf: (name: string): string => `Kody pocztowe miejscowości ${name} (zbiór GeoNames):`
}

/** Which address part a field asks for, by its type, dictionary, techName and label; null: not an address field. */
export function roleOf(n: ENode): Role | null {
  if (n.readOnly || !['TEXT_FIELD', 'SELECT'].includes(n.type) || (n.type === 'SELECT' && n.options.length)) return null
  const t = fold(n.title)
  const tech = n.techName.toLowerCase()
  if (/zagranic/.test(tech) || /zagranic/.test(t)) return null
  const teryt = n.type === 'SELECT' && /^TERYT/i.test(n.dictionaryName ?? '')
  if (/^wojewodztwo$/.test(t)) return 'woj'
  if (/^powiat$/.test(t)) return 'powiat'
  if (/^gmina$/.test(t)) return 'gmina'
  if (teryt) return 'teryt'
  if (n.type !== 'TEXT_FIELD') return null
  if (n.validation.includes('ZIP_CODE') || /^kod pocztowy$/.test(t)) return 'postal'
  if (/\b(data|dnia|podpis|numer|nr)\b|[,;/]/.test(t)) return null
  if (/^(miejscowosc|miasto)( zamieszkania| zameldowania)?$/.test(t)) return 'locality'
  if (/^ulica$/.test(t)) return 'street'
  return null
}

interface Group { locality: ENode; parts: Partial<Record<Role, ENode>> }

/** Address fields of one section, each tied to the nearest locality field of that section. */
export function addressGroups(ef: EForm): Group[] {
  const bySection = new Map<ENode | null, { n: ENode; role: Role; at: number }[]>()
  ef.model.all.forEach((n, at) => {
    const role = roleOf(n)
    if (!role) return
    const list = bySection.get(n.parent) ?? []
    list.push({ n, role, at })
    bySection.set(n.parent, list)
  })
  const groups: Group[] = []
  for (const list of bySection.values()) {
    const heads = list.filter((x) => x.role === 'locality' || x.role === 'teryt')
    const mine = heads.map((x) => ({ locality: x.n, parts: {} } as Group))
    for (const x of list) {
      if (x.role === 'locality' || x.role === 'teryt') continue
      let best = -1
      heads.forEach((hd, i) => { if (best < 0 || Math.abs(hd.at - x.at) < Math.abs(heads[best].at - x.at)) best = i })
      if (best >= 0 && !mine[best].parts[x.role]) mine[best].parts[x.role] = x.n
    }
    groups.push(...mine)
  }
  return groups
}

interface Item { main: string; sub?: string; pick(): void }

/** A list of hints under one text input: arrows and Enter, Escape, or a click. The input stays free text. */
function hintBox(input: HTMLInputElement, id: string, items: () => Promise<{ items: Item[]; note?: string }>): { refresh(): void; close(): void } {
  const list = h('ul', { class: 'fp-hints', id, role: 'listbox', hidden: true })
  const note = h('p', { class: 'fp-hint-note muted small', id: id + '-note', 'aria-live': 'polite' })
  input.setAttribute('role', 'combobox')
  input.setAttribute('aria-autocomplete', 'list')
  input.setAttribute('aria-controls', id)
  input.setAttribute('aria-expanded', 'false')
  input.removeAttribute('list')
  input.setAttribute('spellcheck', 'false')
  input.after(list, note)
  let shown: Item[] = []
  let active = -1
  let turn = 0

  const close = (): void => { list.hidden = true; input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); active = -1 }
  const mark = (): void => {
    [...list.children].forEach((li, i) => li.setAttribute('aria-selected', String(i === active)))
    if (active >= 0) input.setAttribute('aria-activedescendant', `${id}-${active}`); else input.removeAttribute('aria-activedescendant')
  }
  const choose = (i: number): void => { const it = shown[i]; if (!it) return; close(); it.pick() }

  async function refresh(): Promise<void> {
    const my = ++turn
    let got: { items: Item[]; note?: string }
    try { got = await items() } catch { got = { items: [], note: TXT.unavailable } }
    if (my !== turn) return
    shown = got.items
    clear(list)
    shown.forEach((it, i) => {
      const li = h('li', { role: 'option', id: `${id}-${i}`, class: 'fp-hint', 'aria-selected': 'false' },
        h('span', { class: 'fp-hint-main' }, it.main), it.sub ? h('span', { class: 'fp-hint-sub' }, it.sub) : null)
      // mousedown: before the input loses focus
      li.addEventListener('mousedown', (e) => { e.preventDefault(); choose(i) })
      list.append(li)
    })
    note.textContent = got.note ?? ''
    active = -1
    list.hidden = !shown.length || input.readOnly
    input.setAttribute('aria-expanded', String(!list.hidden))
  }

  input.addEventListener('focus', () => { void refresh() })
  input.addEventListener('input', () => { void refresh() })
  input.addEventListener('blur', () => { turn++; close() })
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { close(); return }
    if (list.hidden || !shown.length) return
    if (e.key === 'ArrowDown') { active = (active + 1) % shown.length; mark(); e.preventDefault() }
    else if (e.key === 'ArrowUp') { active = (active - 1 + shown.length) % shown.length; mark(); e.preventDefault() }
    else if (e.key === 'Enter' && active >= 0) { e.preventDefault(); choose(active) }
  })
  return { refresh: () => { void refresh() }, close }
}

export interface AddressHints {
  /** The locality chosen (or recognised by its exact name) for the group this field belongs to. */
  localityFor(id: string): Locality | null
  /** Remarks for postal codes that are not among the codes of their locality (reads the register when it is not read yet). */
  postalRemarks(): Promise<{ node: ENode; msg: string }[]>
  groups: Group[]
}

/** Wire the hints to an electronic form already on the page. `source` is replaced in tests. */
export function attachAddressHints(ef: EForm, source: TerytSource = terytSource()): AddressHints {
  const groups = addressGroups(ef)
  const picked = new Map<string, Locality>()        // locality field id -> chosen locality
  const auto = new Map<string, string>()            // field id -> the value this module wrote there
  const inputOf = (n: ENode): HTMLInputElement | null => {
    const el = ef.el.querySelector(`[id="fpf-${n.id}"]`)
    return el instanceof HTMLInputElement ? el : null
  }
  const locked = (n: ENode): boolean => n.readOnly || ef.tagOf(n.id) === 'pesel' || ef.tagOf(n.id) === 'mlpz'
  const mayWrite = (n: ENode | undefined): n is ENode => !!n && !locked(n) && (!ef.textOf(n.id).trim() || ef.textOf(n.id) === auto.get(n.id))
  const write = (n: ENode, v: string): void => { ef.set(n.id, v); auto.set(n.id, v) }
  let known: Awaited<ReturnType<TerytSource['localities']>> | null = null

  /** The locality of a group: the one clicked, else the one its text names (the largest place of that name that fits the filled parts). */
  function resolve(g: Group): Locality | null {
    const text = ef.textOf(g.locality.id).trim()
    const hit = picked.get(g.locality.id)
    if (hit && (text === hit.name || text === terytPath(hit))) return hit
    if (!known || !text) return null
    const name = text.includes(' / ') ? text.split(' / ').pop() ?? '' : text
    const all = known.named(name)
    const want = (role: Role, of: (l: Locality) => string) => {
      const n = g.parts[role]
      const v = n ? fold(ef.textOf(n.id)) : ''
      return (l: Locality): boolean => !v || fold(of(l)) === v || v.includes(fold(of(l)))
    }
    const fits = all.filter(want('woj', (l) => l.woj)).filter(want('powiat', (l) => l.powiat)).filter(want('gmina', (l) => l.gmina))
    return fits[0] ?? all[0] ?? null
  }

  function pick(g: Group, loc: Locality, note: HTMLElement | null): void {
    picked.set(g.locality.id, loc)
    ef.set(g.locality.id, roleOf(g.locality) === 'teryt' ? terytPath(loc) : loc.name)
    const done: string[] = []
    const put = (role: Role, v: string, label: string): void => {
      const n = g.parts[role]
      if (v && mayWrite(n)) { write(n, v); done.push(`${label} ${v}`) }
    }
    put('gmina', loc.gmina, 'gmina')
    put('powiat', loc.powiat, 'powiat')
    put('woj', loc.woj, 'województwo')
    const codes = codesOf(loc, 2)
    if (codes.length === 1) put('postal', codes[0], 'kod pocztowy')
    const street = g.parts.street
    if (street && ef.textOf(street.id) === auto.get(street.id)) write(street, '')
    if (note) note.textContent = [TXT.chosen(loc), done.length ? TXT.filled(done.join(', ')) : ''].filter(Boolean).join(' ')
  }

  for (const g of groups) {
    const locInput = inputOf(g.locality)
    if (locInput) {
      locInput.setAttribute('placeholder', TXT.example)
      hintBox(locInput, `fph-${g.locality.id}`, async () => {
        const noteEl = ef.el.querySelector<HTMLElement>(`[id="fph-${g.locality.id}-note"]`)
        if (!known) { if (noteEl) noteEl.textContent = TXT.loading; known = await source.localities() }
        const typed = locInput.value.includes(' / ') ? '' : locInput.value
        const found = known.search(typed, 8)
        const items = found.map((loc) => ({ main: loc.name, sub: describe(loc), pick: () => pick(g, loc, noteEl) }))
        const settled = resolve(g)
        const note = found.length ? TXT.source(known.stan) : fold(typed).length >= 2 && !settled ? TXT.none : settled ? TXT.chosen(settled) : TXT.start
        return { items: settled && found.length === 1 && found[0] === settled ? [] : items, note }
      })
      const start = ef.el.querySelector(`[id="fph-${g.locality.id}-note"]`)
      if (start && !ef.textOf(g.locality.id)) start.textContent = TXT.start
    }
    const street = g.parts.street
    const streetInput = street ? inputOf(street) : null
    if (street && streetInput) {
      hintBox(streetInput, `fph-${street.id}`, async () => {
        known ??= await source.localities()
        const loc = resolve(g)
        if (!loc) return { items: [], note: TXT.pickFirst }
        if (!loc.streets) return { items: [], note: TXT.noStreets(loc.name) }
        const all = (await source.streets(loc.wojCode)).of(loc.sym)
        const typed = streetInput.value
        const found = searchStreets(all, typed, 8)
        const exact = all.some((s) => fold(s.name) === fold(typed))
        return {
          items: exact ? [] : found.map((s) => ({ main: s.name, pick: () => { write(street, s.name); auto.delete(street.id) } })),
          note: found.length || exact || !typed.trim() ? TXT.streetsOf(loc, all.length) : TXT.noStreet(loc.name)
        }
      })
    }
    // a territorial drop-down keeps the list of województwa only where it asks for a województwo
    for (const role of ['powiat', 'gmina'] as const) { const n = g.parts[role]; if (n) inputOf(n)?.removeAttribute('list') }
    const postal = g.parts.postal
    const postalInput = postal ? inputOf(postal) : null
    if (postal && postalInput) {
      hintBox(postalInput, `fph-${postal.id}`, async () => {
        known ??= await source.localities()
        const loc = resolve(g)
        if (!loc || !loc.codes) return { items: [] }
        const typed = postalInput.value.trim()
        if (codeFits(loc, typed) === true) return { items: [] }
        const codes = codesOf(loc, 400).filter((c) => c.startsWith(typed) || c.replace('-', '').startsWith(typed))
        const few = codes.length <= 8
        const off = codeFits(loc, typed) === false
        return {
          items: few ? codes.map((c) => ({ main: c, pick: () => write(postal, c) })) : [],
          note: off ? postalMessage(loc, typed) : few ? (codes.length ? TXT.codesOf(loc.name) : '') : `${TXT.codesOf(loc.name)} ${span(loc)}. Wpisz kolejne cyfry.`
        }
      })
    }
  }

  function span(loc: Locality): string {
    const few = codesOf(loc, 4)
    if (few.length <= 3) return few.join(', ')
    const runs = loc.codes.split(',')
    const last = runs[runs.length - 1].split(':').pop() ?? ''
    return `od ${few[0]} do ${last.slice(0, 2)}-${last.slice(2)}`
  }
  function postalMessage(loc: Locality, code: string): string { return TXT.codeOff(code, loc.name, span(loc)) }

  return {
    groups,
    localityFor(id) {
      const g = groups.find((x) => x.locality.id === id || Object.values(x.parts).some((n) => n?.id === id))
      return g ? resolve(g) : null
    },
    async postalRemarks() {
      const out: { node: ENode; msg: string }[] = []
      if (!groups.some((g) => g.parts.postal && ef.textOf(g.parts.postal.id).trim())) return out
      try { known ??= await source.localities() } catch { return out }
      for (const g of groups) {
        const postal = g.parts.postal
        if (!postal || !ef.isVisible(postal)) continue
        const loc = resolve(g)
        const code = ef.textOf(postal.id).trim()
        if (loc && codeFits(loc, code) === false) out.push({ node: postal, msg: postalMessage(loc, code) })
      }
      return out
    }
  }
}
