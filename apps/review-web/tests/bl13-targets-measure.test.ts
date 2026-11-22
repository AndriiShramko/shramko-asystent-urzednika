// BL13 CLERK-T measurement: over saved answers of the real converter (convert?report=1 multipart + preview JSON),
// how many boxes of the original answer a click, before (only a ledger FIELD row and its choice marks led anywhere;
// standard, merged, waiting and left-out places were silent or not drawn) and after (lib/fp/targets.ts).
// Runs only when MEASURE_DIR names a folder of `<name>.r.txt` + `<name>.p.json`; the answers stay outside git.
// @vitest-environment node
import { describe, expect, it } from 'vitest'
import { existsSync, readdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { ledgerRows, parsePreview } from '../src/lib/fp/places'
import { readForm } from '../src/lib/fp/form'
import { answers, boxTargets } from '../src/lib/fp/targets'
import type { Sidecar } from '../src/lib/model'

const dir = process.env.MEASURE_DIR ?? ''

function parts(text: string): unknown[] {
  const out: unknown[] = []
  for (const p of text.split(/--formularze-[0-9a-f]+/)) {
    const i = p.indexOf('{')
    if (i < 0) continue
    try { out.push(JSON.parse(p.slice(i).trim())) } catch { /* the closing boundary */ }
  }
  return out
}

describe.skipIf(!dir || !existsSync(dir))('BL13 box targets over the real answers', () => {
  it('counts boxes without a target before and after', () => {
    const lines: Record<string, unknown>[] = []
    for (const f of readdirSync(dir).filter((x) => x.endsWith('.r.txt')).sort()) {
      const name = f.slice(0, -'.r.txt'.length)
      const pf = join(dir, name + '.p.json')
      if (!existsSync(pf)) continue
      const ps = parts(readFileSync(join(dir, f), 'utf-8'))
      const form = ps.find((x) => !!x && typeof x === 'object' && 'tabs' in (x as object))
      const sidecar = ps.find((x) => !!x && typeof x === 'object' && 'warnings' in (x as object)) as Sidecar | undefined
      const pv = parsePreview(JSON.parse(readFileSync(pf, 'utf-8')))
      if (!form || !sidecar || !pv) { lines.push({ name, error: 'unreadable' }); continue }
      const model = readForm(form)
      const rows = ledgerRows(sidecar)
      const tg = boxTargets(rows, pv, model)
      const boxed = [...tg.values()].filter((t) => !!t.place.box)
      // before: a FIELD row whose field is in the form, and the marks of its options
      const before = boxed.filter((t) => t.kind === 'field').length
      const after = boxed.filter((t) => answers(t)).length
      const toField = boxed.filter((t) => t.fields.length > 0).length
      const kinds: Record<string, number> = {}
      for (const t of boxed) kinds[t.kind] = (kinds[t.kind] ?? 0) + 1
      if (process.env.MEASURE_DETAIL) for (const t of boxed) if (t.kind === 'standard' || t.kind === 'merged') console.log(`DETAIL ${name} ${t.cid} ${t.kind} «${t.place.label ?? ''}» -> ${t.fields.map((id) => model.byId.get(id)?.title).join(' + ')}`)
      lines.push({ name, boxes: boxed.length, noTargetBefore: boxed.length - before, noTargetAfter: boxed.length - after, toField, note: after - toField, kinds })
    }
    if (process.env.MEASURE_OUT) writeFileSync(process.env.MEASURE_OUT, JSON.stringify(lines, null, 1))
    for (const l of lines) console.log(JSON.stringify(l))
    expect(lines.length).toBeGreaterThan(0)
  })
})
