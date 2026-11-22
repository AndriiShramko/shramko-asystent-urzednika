// Builds the compact address registers the page serves from its own origin (public/teryt/), so address hints
// work with no network: localities with their gmina, powiat and województwo (GUS TERYT: TERC, SIMC), the streets of
// each locality (GUS TERYT: ULIC, one file per województwo), and the postal codes of a locality (GeoNames, CC BY 4.0).
//
//   node scripts/teryt-build.mjs <TERC.csv> <SIMC.csv> <ULIC.csv> [<GeoNames PL.txt>]
//
// The inputs are the full "urzędowy" CSV files from eteryt.stat.gov.pl (Baza TERYT, Pobieranie, Pliki pełne) and
// PL.txt from download.geonames.org/export/zip/PL.zip. Nothing is fetched here; see public/teryt/SOURCE.md.
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const [tercPath, simcPath, ulicPath, geoPath] = process.argv.slice(2)
if (!tercPath || !simcPath || !ulicPath) {
  console.error('usage: node scripts/teryt-build.mjs <TERC.csv> <SIMC.csv> <ULIC.csv> [<GeoNames PL.txt>]')
  process.exit(2)
}
const out = join(dirname(fileURLToPath(import.meta.url)), '..', 'public', 'teryt')
mkdirSync(out, { recursive: true })

function csv(path) {
  const lines = readFileSync(path, 'utf8').replace(/^﻿/, '').split(/\r?\n/).filter(Boolean)
  const head = lines[0].split(';')
  return lines.slice(1).map((l) => { const c = l.split(';'); return Object.fromEntries(head.map((h, i) => [h, c[i] ?? ''])) })
}
const clean = (s) => s.replace(/[|\t\r\n]/g, ' ').trim()
const pl = (a, b) => a.localeCompare(b, 'pl')

// ---- TERC: województwa, powiaty, gminy ---------------------------------------------------------------------------
const terc = csv(tercPath)
const stan = terc[0].STAN_NA
const woj = new Map(), pow = new Map(), gmi = new Map()
for (const r of terc) {
  if (!r.POW) woj.set(r.WOJ, r.NAZWA.toLowerCase())
  else if (!r.GMI) pow.set(r.WOJ + r.POW, r.NAZWA)
  else gmi.set(r.WOJ + r.POW + r.GMI + r.RODZ, r.NAZWA)
}

// ---- SIMC: base localities; a part of a locality and a city district fold into their locality --------------------
const simc = csv(simcPath)
const bySym = new Map(simc.map((r) => [r.SYM, r]))
const cityOfPowiat = new Map()
for (const r of simc) if (r.RM === '96' && r.SYM === r.SYMPOD && r.RODZ_GMI === '1') cityOfPowiat.set(r.WOJ + r.POW, r.SYM)
const DISTRICT = new Set(['95', '98'])
function rootOf(sym) {
  let r = bySym.get(sym)
  for (let i = 0; r && r.SYM !== r.SYMPOD && i < 4; i++) r = bySym.get(r.SYMPOD)
  if (r && DISTRICT.has(r.RM)) return cityOfPowiat.get(r.WOJ + r.POW) ?? r.SYM
  return r ? r.SYM : null
}
const base = simc.filter((r) => r.SYM === r.SYMPOD && !DISTRICT.has(r.RM))

// ---- ULIC: streets per locality ---------------------------------------------------------------------------------
const ulic = csv(ulicPath)
const stanUlic = ulic[0].STAN_NA
const streetsOf = new Map()   // root sym -> Set of "cecha|n2|n1"
for (const r of ulic) {
  const root = rootOf(r.SYM)
  if (!root) continue
  const key = [r.CECHA === 'inne' ? '' : clean(r.CECHA), clean(r.NAZWA_2), clean(r.NAZWA_1)].join(';')
  if (!streetsOf.has(root)) streetsOf.set(root, new Set())
  streetsOf.get(root).add(key)
}

// ---- GeoNames: postal codes per locality (name and gmina, else name and powiat) -----------------------------------
const codesOf = new Map()
let geoRows = 0, geoMatched = 0
if (geoPath) {
  const norm = (s) => s.toLowerCase().normalize('NFC').trim()
  const byGmina = new Map(), byPowiat = new Map()
  for (const r of simc) {
    const root = rootOf(r.SYM)
    if (!root) continue
    const add = (m, k) => { if (!m.has(k)) m.set(k, new Set()); m.get(k).add(root) }
    add(byGmina, norm(r.NAZWA) + '|' + r.WOJ + r.POW + r.GMI)
    add(byPowiat, norm(r.NAZWA) + '|' + r.WOJ + r.POW)
  }
  for (const line of readFileSync(geoPath, 'utf8').split(/\r?\n/)) {
    const c = line.split('\t')
    if (c.length < 9 || !/^\d{2}-\d{3}$/.test(c[1])) continue
    geoRows++
    const name = norm(c[2].replace(/\s*\(.*\)\s*$/, ''))
    const hit = byGmina.get(name + '|' + c[8].slice(0, 6)) ?? byPowiat.get(name + '|' + c[6])
    if (!hit || hit.size !== 1) continue      // an ambiguous name is left out: a wrong code is worse than none
    geoMatched++
    const sym = [...hit][0]
    if (!codesOf.has(sym)) codesOf.set(sym, new Set())
    codesOf.get(sym).add(c[1])
  }
}
/** Sorted codes as "00-001,00-002" for a few, or as ranges "00-001:00-950" runs when there are many. */
function packCodes(set) {
  if (!set) return ''
  const n = [...set].map((c) => Number(c.replace('-', ''))).sort((a, b) => a - b)
  const f = (x) => String(x).padStart(5, '0')
  const runs = []
  for (let i = 0; i < n.length;) {
    let j = i
    while (j + 1 < n.length && n[j + 1] === n[j] + 1) j++
    runs.push(j > i ? f(n[i]) + ':' + f(n[j]) : f(n[i]))
    i = j + 1
  }
  return runs.join(',')
}

// ---- write: localities --------------------------------------------------------------------------------------------
const gKeys = [...gmi.keys()].sort()
const gIndex = new Map(gKeys.map((k, i) => [k, i]))
const rows = base.map((r) => ({ r, n: streetsOf.get(r.SYM)?.size ?? 0 }))
  .sort((a, b) => b.n - a.n || pl(a.r.NAZWA, b.r.NAZWA) || a.r.SYM.localeCompare(b.r.SYM))
const L = [`#TERYT|TERC ${stan}|SIMC ${simc[0].STAN_NA}|ULIC ${stanUlic}|GUS eteryt.stat.gov.pl${geoPath ? '|kody: GeoNames CC BY 4.0' : ''}`]
for (const [k, v] of [...woj].sort()) L.push(`W|${k}|${v}`)
for (const [k, v] of [...pow].sort()) L.push(`P|${k}|${clean(v)}`)
for (const k of gKeys) L.push(`G|${k}|${clean(gmi.get(k))}`)
let withCodes = 0
for (const { r, n } of rows) {
  const g = gIndex.get(r.WOJ + r.POW + r.GMI + r.RODZ_GMI)
  if (g === undefined) continue
  const codes = packCodes(codesOf.get(r.SYM))
  if (codes) withCodes++
  L.push(`M|${clean(r.NAZWA)}|${g}|${r.SYM}|${r.RM}|${n}|${codes}`)
}
writeFileSync(join(out, 'miejscowosci.txt'), L.join('\n') + '\n')

// ---- write: streets, one file per województwo ---------------------------------------------------------------------
let streetRows = 0
for (const w of [...woj.keys()].sort()) {
  const syms = base.filter((r) => r.WOJ === w && streetsOf.has(r.SYM)).map((r) => r.SYM).sort()
  const names = [...new Set(syms.flatMap((s) => [...streetsOf.get(s)]))]
    .sort((a, b) => { const x = a.split(';'), y = b.split(';'); return pl(x[2], y[2]) || pl(x[1], y[1]) || pl(x[0], y[0]) })
  const idx = new Map(names.map((n, i) => [n, i]))
  const S = [`#ULIC|${w}|${stanUlic}|GUS eteryt.stat.gov.pl`, ...names.map((n) => 'N|' + n)]
  for (const s of syms) {
    const ids = [...streetsOf.get(s)].map((n) => idx.get(n)).sort((a, b) => a - b)
    streetRows += ids.length
    S.push(`L|${s}|${ids.map((v, i) => (i ? v - ids[i - 1] : v).toString(36)).join(',')}`)
  }
  writeFileSync(join(out, `ulice-${w}.txt`), S.join('\n') + '\n')
}
console.log(JSON.stringify({ stan, localities: rows.length, gminy: gKeys.length, localitiesWithStreets: streetsOf.size,
  streetRows, geoRows, geoMatched, localitiesWithCodes: withCodes }))
