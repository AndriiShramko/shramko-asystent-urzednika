// Integration check: real task-set files through the page against a service that checks the bearer (AUTH_MODE=jwt).
//   node scripts/integration.mjs --base http://127.0.0.1:PORT/ui/ --secret-file secret.key --files a.pdf,b.docx [--engines chromium,firefox]
// The files are read in place (found through tools/coi_paths.py by the caller); nothing is copied or written
// except one line per file on stdout. Also checks: no token -> the page shows a refusal, wrong token -> a refusal,
// right token -> the form, SHA-256 line "agrees", and the downloaded text is byte-equal to the response's form part.
import { readFileSync } from 'node:fs'
import { createHmac, createHash } from 'node:crypto'
import { basename } from 'node:path'

const args = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, all) => (x.startsWith('--') ? [...a, [x.slice(2), all[i + 1]]] : a), []))
const base = args.base
const files = (args.files ?? '').split(',').filter(Boolean)
if (!base || !args['secret-file'] || !files.length) { console.error('--base, --secret-file, --files required'); process.exit(2) }
const secret = readFileSync(args['secret-file'])
const b64 = (x) => Buffer.from(x).toString('base64url')
function mint(extra = {}, key = secret) {
  const head = b64(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const body = b64(JSON.stringify({ sub: 'synthetic-tester', scope: 'convert', exp: Math.floor(Date.now() / 1000) + 600, ...extra }))
  return `${head}.${body}.${createHmac('sha256', key).update(`${head}.${body}`).digest('base64url')}`
}
const pw = await import('playwright')
let failed = 0
const say = (ok, msg) => { if (!ok) failed++; console.log(`${ok ? 'PASS' : 'FAIL'} ${msg}`) }

for (const name of (args.engines ?? 'chromium,firefox').split(',')) {
  let browser
  try { browser = await pw[name].launch() } catch (e) { console.log(`SKIP ${name}: ${String(e.message).split('\n')[0]}`); continue }
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, acceptDownloads: true })
  const page = await ctx.newPage()
  const first = files[0]
  const tries = [['no token', ''], ['wrong key', mint({}, Buffer.from('another synthetic key of at least 32 chars'))], ['expired', mint({ exp: 1 })]]
  for (const [label, tok] of tries) {
    await page.goto(base)
    if (tok) await page.fill('#token', tok)
    await page.setInputFiles('#file', first)
    await page.waitForSelector('#h-error, #h-done', { timeout: 60000 })
    say(await page.locator('#h-error').count() === 1 && await page.locator('#h-done').count() === 0, `${name}: ${label} -> refusal shown, no form`)
  }
  for (const f of files) {
    await page.goto(base)
    await page.fill('#token', mint())
    // The convert response is awaited as a promise (not a fire-and-forget listener), so its header is known
    // before the comparison. Every missing input below is a FAIL, never a pass by default.
    const answer = page.waitForResponse((r) => r.url().includes('/v1/forms/convert'), { timeout: 120000 }).catch(() => null)
    await page.setInputFiles('#file', f)
    await page.waitForSelector('#h-error, #h-done', { timeout: 120000 })
    const resp = await answer
    const hdr = resp ? resp.headers()['x-form-sha256'] ?? null : null
    const raw = resp ? await resp.body().catch(() => null) : null
    const done = await page.locator('#h-done').count() === 1
    const hashOk = done && /zgadza się/.test(await page.locator('#json-status').locator('xpath=preceding-sibling::p | following-sibling::p').allInnerTexts().then((a) => a.join(' ')).catch(() => ''))
    let equal = false
    let why = ''
    if (done) {
      // The shown text must be the raw answer: the pretty switch must exist and start unchecked.
      const pretty = page.locator('#json-pretty')
      const hasPretty = await pretty.count() === 1
      const prettyOff = hasPretty && !(await pretty.isChecked())
      const text = await page.locator('#json-text').innerText()
      const digest = createHash('sha256').update(Buffer.from(text.replace(/\r\n/g, '\n'))).digest('hex')
      const rawDigest = raw ? createHash('sha256').update(raw).digest('hex') : null
      if (!hdr) why = 'no X-Form-SHA256 header'
      else if (!raw) why = 'response body not readable'
      else if (!hasPretty) why = 'no #json-pretty switch'
      else if (!prettyOff) why = 'pretty view on by default'
      else if (rawDigest !== hdr) why = 'header differs from the body'
      else if (digest !== hdr) why = 'shown text differs from the body'
      equal = why === ''
    }
    if (!done) console.log('  page says: ' + (await page.locator('#result').innerText()).replace(/\s+/g, ' ').slice(0, 300))
    const fields = done ? await page.locator('#h-matter').count() : 0
    say(done && hashOk && equal, `${name}: ${basename(f).slice(0, 4)}***.${f.split('.').pop()} -> form shown=${done}, sha agrees=${hashOk}, bytes equal=${equal}${why ? ' (' + why + ')' : ''}, matter section=${fields === 1}`)
  }
  await browser.close()
}
console.log(failed ? `${failed} failing` : 'all passing')
process.exit(failed ? 1 : 0)
