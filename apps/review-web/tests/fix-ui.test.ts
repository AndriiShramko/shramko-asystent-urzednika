import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { nameOf, type ENode } from '../src/lib/fp/form'
import { FP } from '../src/lib/fp/text'

describe('FIX-UI', () => {
  it('Polish plural of the missing-fields sentence', () => {
    expect(FP.missing(1, 'A')).toBe('Brakuje 1 wymaganego pola: A.')
    expect(FP.missing(2, 'A, B')).toBe('Brakuje 2 wymaganych pól: A, B.')
    expect(FP.missing(5, 'x')).toContain('5 wymaganych pól')
  })
  it('the partner dictionary id is not shown as a label', () => {
    const n = { title: 'TERYT_4G_DOWODOWY', dictionaryName: 'TERYT_4G_DOWODOWY', type: 'SELECT', techName: 'x' } as unknown as ENode
    expect(nameOf(n)).toBe('Miejscowość z rejestru TERYT (gmina, powiat, województwo)')
    expect(nameOf({ ...n, title: 'Województwo' } as ENode)).toBe('Województwo')
  })
  it('the page has a relative favicon the CSP allows', () => {
    const html = readFileSync('index.html', 'utf8')
    expect(html).toContain('<link rel="icon" href="./favicon.svg" type="image/svg+xml"')
    expect(html).toMatch(/img-src 'self'/)
  })
})
