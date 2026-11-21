// Every-device check (owner, 21 November): the review page at 375, 768 and 1280 px in Chromium, Firefox and (where
// present) WebKit, against a RUNNING service that serves the built page under /ui/.
//   node scripts/devices.mjs --base http://127.0.0.1:8099/ui/ --file path/to/form.pdf --bad path/to/refused.png --out evidence
// Playwright is not a dependency of the package: `npm install --no-save playwright` and
// `PLAYWRIGHT_BROWSERS_PATH=.playwright npx playwright install chromium firefox` first (both are git-ignored).
// Checks per engine, width, language and state: no horizontal scroll of the page, no element sticking out of the
// viewport, no clipped text, every control inside the viewport and at least 24 px high, no two controls
// overlapping, every control reachable with Tab. One screenshot per width and engine (state "result") is kept.
import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

const args = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, all) => (x.startsWith('--') ? [...a, [x.slice(2), all[i + 1]]] : a), []))
const base = args.base ?? 'http://127.0.0.1:8099/ui/'
const good = args.file
const bad = args.bad
const out = args.out ?? 'evidence'
if (!good || !bad) { console.error('--file and --bad are required'); process.exit(2) }
mkdirSync(out, { recursive: true })

const pw = await import('playwright')
const engines = (args.engines ?? 'chromium,firefox,webkit').split(',')
const widths = [375, 768, 1280]
const langs = ['pl', 'en', 'es']

/** Runs inside the page. Returns a list of findings; an empty list is a pass. */
function audit() {
  const findings = []
  const vw = document.documentElement.clientWidth
  if (document.documentElement.scrollWidth > vw + 1) findings.push(`page scrolls horizontally: ${document.documentElement.scrollWidth} > ${vw}`)
  const visible = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' }
  const label = (el) => `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}${el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : ''}`
  for (const el of document.body.querySelectorAll('*')) {
    if (!visible(el) || el.closest('.sr-only') || el.classList.contains('skip')) continue
    const r = el.getBoundingClientRect()
    if (r.right > vw + 1 || r.left < -1) findings.push(`sticks out of the viewport: ${label(el)} [${Math.round(r.left)}..${Math.round(r.right)}]`)
    const s = getComputedStyle(el)
    const clips = ['hidden', 'clip'].includes(s.overflowX) && el.scrollWidth > el.clientWidth + 1
    if (clips && el.children.length === 0) findings.push(`text clipped: ${label(el)}`)
    if (el.tagName === 'PRE' && el.scrollWidth > el.clientWidth + 1) findings.push(`pre scrolls sideways: ${label(el)}`)
  }
  const controls = [...document.querySelectorAll('button, a[href], select, input:not([type=hidden]):not(.sr-only), summary, textarea, [tabindex="0"]')].filter((e) => visible(e) && !e.closest('.sr-only') && !e.classList.contains('skip'))
  for (const c of controls) {
    const r = c.getBoundingClientRect()
    if (r.height < 24 || r.width < 24) findings.push(`control smaller than 24 px: ${label(c)} ${Math.round(r.width)}x${Math.round(r.height)}`)
  }
  const boxes = controls.map((c) => [c, c.getBoundingClientRect()])
  for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
    const [a, ra] = boxes[i], [b, rb] = boxes[j]
    if (a.contains(b) || b.contains(a)) continue
    const w = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left)
    const hgt = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top)
    if (w > 2 && hgt > 2) findings.push(`controls overlap: ${label(a)} and ${label(b)}`)
  }
  return { findings, controls: controls.length }
}

async function tabReach(page, expected) {
  // Tab through the page once; every visible control must receive focus at some point.
  await page.evaluate(() => { document.activeElement?.blur(); window.scrollTo(0, 0) })
  const seen = new Set()
  for (let i = 0; i < expected + 12; i++) {
    await page.keyboard.press('Tab')
    const id = await page.evaluate(() => {
      const a = document.activeElement
      if (!a || a === document.body) return null
      a.setAttribute('data-tabseen', '1')
      return 1
    })
    if (id) seen.add(i)
  }
  return page.evaluate(() => {
    const need = [...document.querySelectorAll('button, a[href], select, input:not([type=hidden]), summary, textarea, [tabindex="0"]')]
      .filter((e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && !e.closest('.sr-only') && e.tabIndex >= 0 && !e.classList.contains('skip') })
    return need.filter((e) => !e.hasAttribute('data-tabseen')).map((e) => e.tagName.toLowerCase() + (e.id ? '#' + e.id : ''))
  })
}

const results = []
let failed = 0
for (const name of engines) {
  const type = pw[name]
  let browser
  try { browser = await type.launch() } catch (e) { console.log(`SKIP ${name}: ${String(e.message).split('\n')[0]}`); continue }
  for (const width of widths) {
    const ctx = await browser.newContext({ viewport: { width, height: 800 }, deviceScaleFactor: 1 })
    const page = await ctx.newPage()
    const problems = []
    page.on('request', (r) => { if (!r.url().startsWith(new URL(base).origin) && !r.url().startsWith('data:') && !r.url().startsWith('blob:')) problems.push('outside request: ' + r.url()) })
    for (const lang of langs) {
      await page.goto(base)
      await page.selectOption('#lang', lang)
      const steps = [['idle', null], ['result', good], ['error', bad]]
      for (const [state, file] of steps) {
        if (file) {
          await page.setInputFiles('#file', file)
          await page.waitForSelector(state === 'result' ? '#h-done' : '#h-error', { timeout: 60000 })
        }
        const { findings, controls } = await page.evaluate(audit)
        const unreached = await tabReach(page, controls)
        for (const u of unreached) findings.push(`not reachable with Tab: ${u}`)
        if (lang === 'pl' && state === 'result') await page.screenshot({ path: join(out, `${name}-${width}.png`), fullPage: true })
        const row = { engine: name, width, lang, state, controls, findings }
        results.push(row)
        if (findings.length) { failed++; console.log(`FAIL ${name} ${width} ${lang} ${state}: ${findings.slice(0, 6).join(' | ')}`) }
      }
    }
    for (const p of problems) { failed++; console.log(`FAIL ${name} ${width}: ${p}`) }
    await ctx.close()
  }
  await browser.close()
}
writeFileSync(join(out, 'devices-report.json'), JSON.stringify(results, null, 1))
console.log(`${results.length} page states checked, ${failed} failing`)
process.exit(failed ? 1 : 0)
