// W11 ADDR step 2: address hints from the registers the page serves itself (public/teryt/: GUS TERYT, GeoNames).
// The tests read the real files of the repository; names of localities and streets are public register data.
import { beforeEach, describe, expect, it } from 'vitest'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { codeFits, codesOf, describe as describeLoc, fold, parseLocalities, parseStreets, searchStreets, terytPath, terytSource, type FetchText } from '../src/lib/fp/teryt'
import { addressGroups, roleOf } from '../src/ui/address'
import { mountFill } from '../src/ui/fill'
import { readForm } from '../src/lib/fp/form'
import { renderEForm } from '../src/ui/eform'
import { interpretResponse, type Converted } from '../src/lib/api'
import { canonical, cell, field, multipartBody } from './helpers'

const DIR = join(__dirname, '..', 'public', 'teryt')
const read = (name: string): string => readFileSync(join(DIR, name), 'utf8')
const asked: string[] = []
const fromDisk: FetchText = async (path) => { asked.push(path); return read(path.replace('./teryt/', '')) }
const tick = async (n = 6): Promise<void> => { for (let i = 0; i < n; i++) await new Promise((r) => setTimeout(r, 0)) }

function paperForm() {
  const f = (id: string, type: string, title: string, techName: string, extra: Record<string, unknown> = {}) => field(id, type, title, { techName, ...extra })
  const adres = f('s-adres', 'SECTION', 'Adres wnioskodawcy', 'adres_wnioskodawcy', { repeatingSectionGrid: [
    cell(f('f-miejsc', 'TEXT_FIELD', 'Miejscowość', 'miejscowosc')),
    cell(f('f-ulica', 'TEXT_FIELD', 'Ulica', 'ulica'), 1),
    cell(f('f-nr', 'TEXT_FIELD', 'Nr domu', 'nr_domu'), 2),
    cell(f('f-kod', 'TEXT_FIELD', 'Kod pocztowy', 'kod_pocztowy', { validation: ['ZIP_CODE'] }), 3),
    cell(f('f-gmina', 'TEXT_FIELD', 'Gmina', 'gmina'), 4),
    cell(f('f-powiat', 'TEXT_FIELD', 'Powiat', 'powiat'), 5),
    cell(f('f-woj', 'SELECT', 'Województwo', 'wojewodztwo', { dictionaryName: 'TERYT_4G_DOWODOWY' }), 6),
    cell(f('f-data', 'TEXT_FIELD', 'Miejscowość, data', 'miejscowosc_data'), 7)
  ] })
  const std = f('s-std', 'SECTION', 'Adres zamieszkania', 'adres_zamieszkania', { repeatingSectionGrid: [
    cell(f('g-kraj', 'SELECT', 'Kraj', 'kraj', { dictionaryName: 'Kraje', defaultValue: ['Polska'] })),
    cell(f('g-mz', 'TEXT_FIELD', 'Miejscowość', 'miejscowosc_zagranica'), 1),
    cell(f('g-teryt', 'SELECT', 'TERYT_4G_DOWODOWY', 'wojewodztwo', { dictionaryName: 'TERYT_4G_DOWODOWY' }), 2),
    cell(f('g-kod', 'TEXT_FIELD', 'Kod pocztowy', 'kod_pocztowy', { validation: ['ZIP_CODE'] }), 3),
    cell(f('g-ulica', 'TEXT_FIELD', 'Ulica', 'ulica'), 4)
  ] })
  return { title: 'Wniosek', tabs: [{ id: 't-1', title: 'Dane', type: 'MAIN', questions: [cell(adres), cell(std, 1)] }], flow: { links: [] } }
}

async function converted(): Promise<Converted> {
  const res = await interpretResponse(200, new Headers({ 'content-type': 'multipart/mixed; boundary=formularze-abc123' }),
    multipartBody(canonical(paperForm()), null))
  if (res.kind !== 'ok') throw new Error('fixture failed')
  return res
}
const input = (root: HTMLElement, id: string): HTMLInputElement => root.querySelector<HTMLInputElement>(`[id="fpf-${id}"]`)!
function type(el: HTMLInputElement, text: string): void { el.dispatchEvent(new Event('focus')); el.value = text; el.dispatchEvent(new Event('input')) }
const options = (root: HTMLElement, id: string): string[] => [...root.querySelectorAll(`[id="fph-${id}"] [role="option"]`)].map((o) => o.textContent ?? '')
const clickOption = (root: HTMLElement, id: string, i: number): void => { root.querySelectorAll(`[id="fph-${id}"] [role="option"]`)[i].dispatchEvent(new Event('mousedown', { cancelable: true })) }

beforeEach(() => { document.body.innerHTML = '<div id="app"></div>'; asked.length = 0 })

describe('W11 ADDR: the registers the page carries', () => {
  const t0 = performance.now()
  const reg = parseLocalities(read('miejscowosci.txt'))
  const parseMs = performance.now() - t0

  it('holds the localities of the SIMC register with gmina, powiat and województwo', () => {
    expect(reg.size).toBeGreaterThan(50000)
    expect(reg.stan).toMatch(/TERC \d{4}-\d\d-\d\d, SIMC \d{4}-\d\d-\d\d, ULIC \d{4}-\d\d-\d\d/)
    const b = reg.search('byd')[0]
    expect(b).toMatchObject({ name: 'Bydgoszcz', kind: 'miasto', gmina: 'Bydgoszcz', powiat: 'Bydgoszcz', woj: 'kujawsko-pomorskie', wojCode: '04' })
    expect(describeLoc(b)).toBe('miasto, gm. Bydgoszcz, pow. Bydgoszcz, woj. kujawsko-pomorskie')
    expect(terytPath(b)).toBe('kujawsko-pomorskie / Bydgoszcz / Bydgoszcz / Bydgoszcz')
    // typed without Polish letters, any case
    expect(reg.search('LODZ')[0].name).toBe('Łódź')
    expect(reg.search('zolw').every((l) => fold(l.name).startsWith('zolw'))).toBe(true)
    expect(reg.search('b')).toEqual([])
    // a name many villages share: every hint says which gmina and powiat it is
    const lipa = reg.named('Lipa')
    expect(lipa.length).toBeGreaterThan(5)
    expect(new Set(lipa.map((l) => `${l.gmina}|${l.powiat}`)).size).toBe(lipa.length)
    // a district of a city is not a separate locality: its streets belong to the city
    expect(reg.named('Warszawa')[0].streets).toBeGreaterThan(4000)
    expect(reg.named('Mokotów').filter((l) => l.powiat === 'Warszawa')).toEqual([])
  })

  it('answers a search in a few milliseconds (measured here, printed)', () => {
    const t = performance.now()
    for (const q of ['by', 'war', 'kra', 'nowa w', 'zzz', 'sta', 'os', 'lip', 'gd', 'sz']) reg.search(q)
    const perSearch = (performance.now() - t) / 10
    console.log(`TERYT: parse ${parseMs.toFixed(0)} ms for ${reg.size} localities; search ${perSearch.toFixed(2)} ms on average`)
    expect(perSearch).toBeLessThan(50)
    expect(parseMs).toBeLessThan(3000)
  })

  it('offers the streets of the chosen locality from the ULIC register', () => {
    const b = reg.search('bydgoszcz')[0]
    const streets = parseStreets(read(`ulice-${b.wojCode}.txt`)).of(b.sym)
    expect(streets.length).toBe(b.streets)
    expect(searchStreets(streets, 'gda')[0].name).toBe('Gdańska')
    expect(searchStreets(streets, 'ul. gdanska')[0].name).toBe('Gdańska')
    expect(searchStreets(streets, 'jana pawla').map((s) => s.name)).toContain('Aleje Jana Pawła II')
    expect(searchStreets(streets, 'zzzz')).toEqual([])
    // a village without street names: an address without a street
    const village = reg.search('lipa').find((l) => l.streets === 0)!
    expect(parseStreets(read(`ulice-${village.wojCode}.txt`)).of(village.sym)).toEqual([])
  })

  it('knows the postal codes of a locality from the open set, and says nothing where the set has none', () => {
    const b = reg.search('bydgoszcz')[0]
    expect(codeFits(b, '85-001')).toBe(true)
    expect(codeFits(b, '00-001')).toBe(false)
    expect(codeFits(b, '85001')).toBeNull()
    expect(codesOf(b, 3)).toEqual(['85-000', '85-001', '85-002'])
    expect(codeFits({ ...b, codes: '' }, '00-001')).toBeNull()
  })

  it('carries its source and state in every file and stays small enough for the image', () => {
    const files = readdirSync(DIR).filter((f) => f.endsWith('.txt'))
    expect(files.length).toBe(17)
    let bytes = 0
    for (const f of files) {
      bytes += statSync(join(DIR, f)).size
      expect(read(f).split('\n')[0]).toMatch(/^#(TERYT|ULIC)\|.*GUS eteryt\.stat\.gov\.pl/)
    }
    console.log(`TERYT: ${files.length} files, ${(bytes / 1048576).toFixed(2)} MB`)
    expect(bytes).toBeLessThan(8 * 1048576)
    expect(readFileSync(join(DIR, 'SOURCE.md'), 'utf8')).toMatch(/GeoNames[\s\S]*CC BY 4\.0/)
  })
})

describe('W11 ADDR: hints in the trial fill', () => {
  it('finds the address fields of a form and ties them to the locality of their section', () => {
    const ef = renderEForm(readForm(paperForm()))
    const roles = Object.fromEntries(ef.model.all.filter((n) => roleOf(n)).map((n) => [n.id, roleOf(n)]))
    expect(roles).toEqual({ 'f-miejsc': 'locality', 'f-ulica': 'street', 'f-kod': 'postal', 'f-gmina': 'gmina', 'f-powiat': 'powiat', 'f-woj': 'woj',
      'g-teryt': 'teryt', 'g-kod': 'postal', 'g-ulica': 'street' })
    const groups = addressGroups(ef)
    expect(groups.map((g) => [g.locality.id, Object.keys(g.parts).sort().join(',')])).toEqual([
      ['f-miejsc', 'gmina,postal,powiat,street,woj'], ['g-teryt', 'postal,street']])
  })

  it('typing letters offers localities; a click fills locality, gmina, powiat, województwo; the street field offers its streets', async () => {
    const fill = mountFill(await converted(), Promise.resolve(null), terytSource(fromDisk))
    const app = document.getElementById('app')!
    app.append(fill.el)
    expect(asked).toEqual([])                       // nothing is read before an address field gets focus
    const loc = input(app, 'f-miejsc')
    type(loc, 'Byd')
    await tick()
    expect(asked).toEqual(['./teryt/miejscowosci.txt'])
    const opts = options(app, 'f-miejsc')
    expect(opts[0]).toBe('Bydgoszczmiasto, gm. Bydgoszcz, pow. Bydgoszcz, woj. kujawsko-pomorskie')
    expect(loc.getAttribute('aria-expanded')).toBe('true')
    clickOption(app, 'f-miejsc', 0)
    expect(fill.eform.textOf('f-miejsc')).toBe('Bydgoszcz')
    expect(fill.eform.textOf('f-gmina')).toBe('Bydgoszcz')
    expect(fill.eform.textOf('f-powiat')).toBe('Bydgoszcz')
    expect(fill.eform.textOf('f-woj')).toBe('kujawsko-pomorskie')
    expect(fill.eform.textOf('f-kod')).toBe('')    // a city has many codes: none is guessed
    expect(app.querySelector('[id="fph-f-miejsc-note"]')?.textContent).toBe('Uzupełniono z rejestru TERYT: gmina Bydgoszcz, powiat Bydgoszcz, województwo kujawsko-pomorskie.')
    expect(fill.eform.textOf('f-data')).toBe('')   // "Miejscowość, data" is not an address field

    const street = input(app, 'f-ulica')
    type(street, 'gda')
    await tick()
    expect(asked).toEqual(['./teryt/miejscowosci.txt', './teryt/ulice-04.txt'])
    expect(options(app, 'f-ulica')[0]).toBe('Gdańska')
    clickOption(app, 'f-ulica', 0)
    expect(fill.eform.textOf('f-ulica')).toBe('Gdańska')

    // keyboard: arrows and Enter choose a hint too
    type(street, 'dwor')
    await tick()
    street.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }))
    street.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }))
    expect(fill.eform.textOf('f-ulica').toLowerCase()).toContain('dwor')

    // the postal code: wrong for this locality is a remark in plain Polish, with the range the set knows
    const kod = input(app, 'f-kod')
    type(kod, '00-001')
    await tick()
    expect(app.querySelector('[id="fph-f-kod-note"]')?.textContent).toMatch(/^Kod pocztowy 00-001 nie występuje w zbiorze kodów miejscowości Bydgoszcz \(od 85-000 do 85-950\)\. Sprawdź kod albo miejscowość\.$/)
    fill.check.run()
    await tick()
    expect(app.querySelector('#fp-check-address')?.textContent).toContain('Kod pocztowy 00-001 nie występuje')
    type(kod, '85-0')
    await tick()
    type(kod, '85-001')
    await tick()
    expect(app.querySelector('[id="fph-f-kod-note"]')?.textContent).toBe('')
    fill.check.run()
    await tick()
    expect(app.querySelector('#fp-check-address')).toBeNull()
  })

  it('a village with one postal code gets it filled; the partner TERYT drop-down takes the four levels', async () => {
    const reg = parseLocalities(read('miejscowosci.txt'))
    const one = reg.search('zolw').find((l) => codesOf(l, 2).length === 1 && l.streets === 0)!
    const fill = mountFill(await converted(), Promise.resolve(null), terytSource(fromDisk))
    const app = document.getElementById('app')!
    app.append(fill.el)
    const t = input(app, 'g-teryt')
    expect(t.hasAttribute('list')).toBe(false)
    type(t, one.name)
    await tick()
    const i = options(app, 'g-teryt').findIndex((o) => o === one.name + describeLoc(one))
    expect(i).toBeGreaterThanOrEqual(0)
    clickOption(app, 'g-teryt', i)
    expect(fill.eform.textOf('g-teryt')).toBe(terytPath(one))
    expect(fill.eform.textOf('g-kod')).toBe(codesOf(one, 1)[0])
    const street = input(app, 'g-ulica')
    type(street, '')
    await tick()
    expect(options(app, 'g-ulica')).toEqual([])
    expect(app.querySelector('[id="fph-g-ulica-note"]')?.textContent).toBe(`W miejscowości ${one.name} rejestr ULIC nie ma ulic: adres bez ulicy (pole może zostać puste).`)
  })

  it('without the register files the fields still take typed text and say why there are no hints', async () => {
    const fill = mountFill(await converted(), Promise.resolve(null), terytSource(async () => { throw new Error('404') }))
    const app = document.getElementById('app')!
    app.append(fill.el)
    const loc = input(app, 'f-miejsc')
    type(loc, 'Byd')
    await tick()
    expect(options(app, 'f-miejsc')).toEqual([])
    expect(app.querySelector('[id="fph-f-miejsc-note"]')?.textContent).toMatch(/^Podpowiedzi adresowe są niedostępne/)
    expect(fill.eform.textOf('f-miejsc')).toBe('Byd')
  })
})
