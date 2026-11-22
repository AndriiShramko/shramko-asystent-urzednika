import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

// Our own accessibility rule for colour (WCAG 2.1 AA): the tokens of src/style.css are checked as pairs.
const css = readFileSync(resolve(process.cwd(), 'src/style.css'), 'utf8')
const tokens: Record<string, string> = {}
for (const m of css.matchAll(/--c-([a-z-]+):\s*(#[0-9a-fA-F]{6})/g)) tokens[m[1]] = m[2]

function lum(hex: string): number {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4))
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
}
export function ratio(a: string, b: string): number {
  const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p)
  return (x + 0.05) / (y + 0.05)
}

const TEXT_PAIRS: [string, string][] = [
  ['text', 'bg'], ['text', 'surface'], ['muted', 'bg'], ['muted', 'surface'], ['accent', 'bg'], ['on-accent', 'accent'],
  ['chip-text', 'chip-bg'], ['req-text', 'req-bg'], ['bad', 'bg'], ['notice-text', 'notice-bg'], ['error-text', 'error-bg'],
  ['text', 'chip-bg'], ['accent', 'chip-bg'],
  // the mode badge of the header (#mode, the one engine indicator): grey rules, green model on, amber fallback
  ['engine-rules-text', 'engine-rules-bg'], ['engine-model-text', 'engine-model-bg'], ['engine-fallback-text', 'engine-fallback-bg']
]
const UI_PAIRS: [string, string][] = [['border', 'bg'], ['border', 'surface'], ['focus', 'bg'], ['accent', 'surface'], ['bad', 'error-bg'],
  ['engine-rules-edge', 'engine-rules-bg'], ['engine-model-edge', 'engine-model-bg'], ['engine-fallback-edge', 'engine-fallback-bg'],
  ['engine-rules-edge', 'bg'], ['engine-model-edge', 'bg'], ['engine-fallback-edge', 'bg']]

describe('contrast tokens', () => {
  it('finds the tokens', () => expect(Object.keys(tokens).length).toBeGreaterThanOrEqual(17))
  for (const [fg, bg] of TEXT_PAIRS) {
    it(`text ${fg} on ${bg} is at least 4.5:1`, () => expect(ratio(tokens[fg], tokens[bg])).toBeGreaterThanOrEqual(4.5))
  }
  for (const [fg, bg] of UI_PAIRS) {
    it(`component ${fg} against ${bg} is at least 3:1`, () => expect(ratio(tokens[fg], tokens[bg])).toBeGreaterThanOrEqual(3))
  }
  it('negative control: a pair that fails is measured as failing', () => expect(ratio('#999999', '#ffffff')).toBeLessThan(4.5))
  it('the mode badge is painted with the checked tokens, and no rule of the removed engine band is left', () => {
    for (const [cls, kind] of [['mode-rules', 'rules'], ['mode-model-on', 'model'], ['mode-model-fallback', 'fallback']]) {
      const rule = css.match(new RegExp(`\\.${cls} \\{([^}]*)\\}`))?.[1] ?? ''
      for (const part of ['bg', 'text', 'edge']) expect(rule, cls).toContain(`var(--c-engine-${kind}-${part})`)
    }
    expect(css).not.toMatch(/\.engine\b|\.engine-/)
  })
})
