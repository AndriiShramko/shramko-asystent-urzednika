// Fixes found in the live check on task set 07 (wave 10): a hidden field is not filled; a consent block is named
// by its section. Synthetic data only.
import { describe, expect, it } from 'vitest'
import { HOUSEHOLD } from '../src/lib/fp/family'
import { planFill } from '../src/lib/fp/fill'
import { nameOf, readForm } from '../src/lib/fp/form'
import { renderEForm } from '../src/ui/eform'
import { renderCitizen } from '../src/ui/citizen'
import { fpForm } from './fp-fixture'
import { layoutText } from '../src/lib/fp/places'

describe('FP live fixes', () => {
  it('the one-click fill skips hidden fields (the foreign address while the country is Polska)', () => {
    const ef = renderEForm(readForm(fpForm()))
    const ids = planFill(ef.model, HOUSEHOLD[0], (id) => !ef.textOf(id).trim(), (n) => ef.isVisible(n)).map((p) => p.id)
    expect(ids).not.toContain('f-ulica-z')
    expect(ids).toContain('f-ulica')
  })

  it('a consent block without a title is named by its section', () => {
    const m = readForm(fpForm())
    expect(nameOf(m.byId.get('f-zgoda')!)).toBe('Szczegóły sprawy')
  })

  it('a low table cell writes after its own label; a tall one under it (set 07: Telefon)', () => {
    const low = layoutText({ page: 1, kind: 'cell', box: [55, 370, 750, 388], label: 'Telefon:' }, '+48 000 000 105')
    expect(low.glyphs[0].left).toBeGreaterThan(55 + 'Telefon:'.length * 4)
    const tall = layoutText({ page: 1, kind: 'cell', box: [55, 198, 539, 224], label: 'Imię i nazwisko' }, 'Helena Przykładowska')
    expect(tall.glyphs[0].left).toBe(57)
  })

  it('a line block of two 10 pt lines writes at 9 pt, not the 7 pt minimum (set 07: dog address)', () => {
    const r = layoutText({ page: 1, kind: 'line_block', box: [50, 600, 520, 620], lines: 2 }, 'ul. Przykładowa 14, 85-999 Bydgoszcz')
    expect(r.glyphs[0].size).toBe(9)
  })

  it('a choice that reveals a field gets that field filled in the same click (set 07: chip number)', () => {
    const f = fpForm()
    const sprawa = f.tabs[1].questions[0].field as { repeatingSectionGrid: unknown[] }
    sprawa.repeatingSectionGrid.push(
      { x: 0, y: 9, rows: 1, cols: 3, field: { id: 'r-oz', type: 'RADIO', techName: 'oznakowanie', title: 'Sposób oznakowania psa / nr ident.', options: [{ id: 'm', name: 'mikroprocesor', techName: 'm' }, { id: 'b', name: 'brak', techName: 'b' }], validation: [], states: [], repeatingSectionGrid: [] } },
      { x: 0, y: 10, rows: 1, cols: 3, field: { id: 'f-chip', type: 'TEXT_FIELD', techName: 'oznakowanie_m', title: 'Sposób oznakowania psa / nr ident.: mikroprocesor', validation: [], repeatingSectionGrid: [],
        states: [{ type: 'SHOW', query: `("mikroprocesor" in tabs['Szczegóły sprawy' in title].questions['szczegoly_sprawy' in field.techName].field.repeatingSectionGrid['oznakowanie' in field.techName].field.__userAnswer)` }] } })
    const ef = renderEForm(readForm(f))
    const c = renderCitizen(ef)
    document.body.innerHTML = ''
    document.body.append(ef.el, c.el)
    const helena = HOUSEHOLD.findIndex((p) => p.extra.dog)
    ;(document.querySelector('#fp-scan') as HTMLElement).click()
    ;(document.querySelector(`[data-person="${helena}"]`) as HTMLElement).click()
    ;(document.querySelector('#fp-fill') as HTMLElement).click()
    expect(ef.get('r-oz')).toBe('mikroprocesor')
    expect(ef.textOf('f-chip')).toMatch(/^616 /)
  })
})
