import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

// WCAG 2.1 AA for the colour tokens added by ORDER UI (a8 UX): headline, remarks, small grey codes, progress bar.
const css = readFileSync(resolve(process.cwd(), 'src/style.css'), 'utf8')
const tokens: Record<string, string> = {}
for (const m of css.matchAll(/--c-([a-z-]+):\s*(#[0-9a-fA-F]{6})/g)) tokens[m[1]] = m[2]

function lum(hex: string): number {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4))
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
}
function ratio(a: string, b: string): number {
  const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p)
  return (x + 0.05) / (y + 0.05)
}

const TEXT: [string, string][] = [
  ['ok-text', 'ok-bg'], ['partial-text', 'partial-bg'], ['text', 'remark-bg'], ['muted', 'remark-bg'],
  ['code', 'bg'], ['code', 'remark-bg'], ['code', 'surface'], ['error-text', 'error-bg'], ['accent', 'remark-bg']
]
const UI: [string, string][] = [['ok-edge', 'ok-bg'], ['partial-edge', 'partial-bg'], ['remark-edge', 'remark-bg'], ['remark-edge', 'bg'],
  ['bar', 'bar-track'], ['bar', 'surface']]

describe('contrast tokens of ORDER UI', () => {
  for (const [fg, bg] of TEXT) {
    it(`text ${fg} on ${bg} is at least 4.5:1`, () => {
      expect(tokens[fg], fg).toBeTruthy(); expect(tokens[bg], bg).toBeTruthy()
      expect(ratio(tokens[fg], tokens[bg])).toBeGreaterThanOrEqual(4.5)
    })
  }
  for (const [fg, bg] of UI) {
    it(`component ${fg} against ${bg} is at least 3:1`, () => expect(ratio(tokens[fg], tokens[bg])).toBeGreaterThanOrEqual(3))
  }
})
