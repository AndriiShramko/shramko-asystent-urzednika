// The page: header with the mode badge and the language switch, the upload panel, a progress panel, a live status
// line, the result. The upload panel is built once (so a typed token and the focus survive a change of language);
// its texts are refreshed through data-i18n attributes. The result is rebuilt from the kept outcome.
import { CANCELLED, convertWithProgress, fetchStatus, type ConvertHooks, type Engine, type Outcome } from '../lib/api'
import { LANGS, getLang, initialLang, setLang, t, type Lang } from '../lib/i18n'
import { badgeMode, modeOf, type Mode } from '../lib/verdict'
import { h, clear } from './dom'
import { doneStatus, renderConverted, renderProblem } from './result'

const STORE_KEY = 'review.lang'
/** After this long the page says the wait is unusual and offers to stop. */
export const LONG_MS = 90_000

export interface AppDeps {
  convert: (file: File, token: string, hooks?: ConvertHooks) => Promise<Outcome>
  store: Pick<Storage, 'getItem' | 'setItem'> | null
  /** GET /status as JSON, or null when it failed. */
  status: () => Promise<unknown>
}

function i18nEl<K extends keyof HTMLElementTagNameMap>(tag: K, key: string, attrs: Record<string, string> = {}): HTMLElementTagNameMap[K] {
  const el = h(tag, { 'data-i18n': key, ...attrs })
  el.textContent = t(key)
  return el
}

/** File size for people: KB under one megabyte, else MB with one decimal, in the page's language. */
export function formatSize(bytes: number): string {
  const nf = (n: number, digits: number): string =>
    new Intl.NumberFormat(getLang(), { maximumFractionDigits: digits, minimumFractionDigits: 0 }).format(n)
  if (bytes < 1024 * 1024) return t('size.kb', { n: nf(Math.max(1, Math.round(bytes / 1024)), 0) })
  return t('size.mb', { n: nf(bytes / (1024 * 1024), 1) })
}

export function mountApp(root: HTMLElement, deps: Partial<AppDeps> = {}): { refresh(): void } {
  const convert = deps.convert ?? ((f, tok, hooks) => convertWithProgress(f, tok, hooks))
  const store = deps.store === undefined ? safeStorage() : deps.store
  const getStatus = deps.status ?? (() => fetchStatus())
  setLang(initialLang(store?.getItem(STORE_KEY)))
  document.documentElement.lang = getLang()

  let outcome: Outcome | null = null
  let fileName = ''
  let lastFile: File | null = null
  let busy = false
  let stage: 'sending' | 'processing' = 'sending'
  let started = 0
  let ticker: ReturnType<typeof setInterval> | null = null
  let abort: AbortController | null = null
  let cancelled = false
  let several = false
  // The badge has two sources (see badgeMode): what /status said last, and the engine of the last conversion.
  let statusMode: Mode | null = null
  let lastEngine: Engine | null = null
  let statusCall = 0

  const status = h('p', { id: 'status', role: 'status', 'aria-live': 'polite', class: 'status' })
  // The result itself is not a live region (it is long); the status line above announces it, an error is role=alert.
  const resultBox = h('div', { id: 'result', class: 'result-box' })

  // ---- header: the mode badge (from GET /status and from the engine of the last conversion), the language switch
  const modeBadge = h('span', { id: 'mode', class: 'mode', hidden: true })
  const select = h('select', { id: 'lang', name: 'lang' },
    ...LANGS.map((l) => h('option', { value: l, lang: l }, t('lang.' + l))))
  select.value = getLang()
  select.addEventListener('change', () => {
    setLang(select.value as Lang)
    try { store?.setItem(STORE_KEY, select.value) } catch { /* private mode: the choice just is not kept */ }
    refresh()
  })
  const header = h('header', { class: 'top' },
    h('div', { class: 'brand' }, i18nEl('h1', 'app.title'), i18nEl('p', 'app.subtitle', { class: 'muted' })),
    h('div', { class: 'top-right' }, modeBadge,
      h('div', { class: 'lang' }, i18nEl('label', 'lang.label', { for: 'lang' }), select)))

  // ---- upload panel
  const fileInput = h('input', { type: 'file', id: 'file', class: 'sr-only', tabindex: -1, 'aria-hidden': 'true',
    accept: '.pdf,.doc,.docx,.ods,.xlsx,.jpg,.jpeg,.png' })
  const pick = i18nEl('button', 'upload.button', { type: 'button', class: 'btn btn-main', id: 'pick' })
  const chosen = h('p', { class: 'muted', id: 'chosen' })
  const token = h('input', { type: 'password', id: 'token', name: 'token', autocomplete: 'off', spellcheck: 'false',
    'aria-describedby': 'token-hint' })
  const zone = h('div', { class: 'drop', id: 'drop' },
    i18nEl('p', 'upload.drop'), pick, fileInput, chosen)
  const upload = h('section', { 'aria-labelledby': 'h-upload', class: 'panel' },
    i18nEl('h2', 'upload.heading', { id: 'h-upload' }),
    zone,
    i18nEl('p', 'upload.formats', { class: 'muted' }),
    h('div', { class: 'field-row' },
      i18nEl('label', 'upload.token.label', { for: 'token' }), token,
      i18nEl('p', 'upload.token.hint', { id: 'token-hint', class: 'muted' })))

  // ---- progress panel: file name and size, a moving bar without a percentage, elapsed seconds, the long state
  const progFile = h('p', { id: 'progress-file', class: 'progress-file' })
  const bar = h('div', { class: 'bar', role: 'progressbar', id: 'progress-bar' }, h('div', { class: 'bar-run' }))
  const elapsed = h('p', { id: 'progress-elapsed', class: 'muted', role: 'timer' })
  // its own polite live text: the sentence is set only when the wait becomes long, so it is announced once
  const longText = h('p', { id: 'progress-long', class: 'progress-long', 'aria-live': 'polite' })
  const cancelBtn = h('button', { type: 'button', class: 'btn', id: 'progress-cancel' })
  const longBox = h('div', { id: 'progress-longbox', hidden: true }, longText, cancelBtn)
  const progress = h('div', { id: 'progress', class: 'progress', hidden: true }, progFile, bar, elapsed, longBox)
  cancelBtn.addEventListener('click', () => { cancelled = true; abort?.abort() })

  pick.addEventListener('click', () => { if (!busy) fileInput.click() })
  fileInput.addEventListener('change', () => {
    const files = [...(fileInput.files ?? [])]
    fileInput.value = ''
    void run(files)
  })
  for (const ev of ['dragenter', 'dragover'] as const) {
    zone.addEventListener(ev, (e) => {
      e.preventDefault()
      if (busy) return
      zone.classList.add('active'); setChosen(t('upload.dropActive'))
    })
  }
  for (const ev of ['dragleave', 'drop'] as const) {
    zone.addEventListener(ev, () => { zone.classList.remove('active'); setChosen(fileName ? t('upload.chosen', { name: fileName }) : '') })
  }
  zone.addEventListener('drop', (e) => {
    e.preventDefault()
    if (busy) return
    void run([...(e.dataTransfer?.files ?? [])])
  })

  function setChosen(text: string): void { chosen.textContent = text }

  function setBusy(on: boolean): void {
    busy = on
    pick.disabled = on
    fileInput.disabled = on
    zone.classList.toggle('busy', on)
    if (on) zone.setAttribute('aria-disabled', 'true')
    else zone.removeAttribute('aria-disabled')
    progress.hidden = !on
    if (on) resultBox.setAttribute('aria-busy', 'true')
    else resultBox.removeAttribute('aria-busy')
  }

  function paintProgress(): void {
    if (!busy || !lastFile) return
    const secs = Math.floor((Date.now() - started) / 1000)
    progFile.textContent = t('progress.file', { name: lastFile.name, size: formatSize(lastFile.size) })
    bar.setAttribute('aria-label', t('progress.label'))
    elapsed.textContent = t('progress.elapsed', { s: secs })
    const long = Date.now() - started >= LONG_MS
    longText.textContent = long ? t('progress.long') : ''
    cancelBtn.textContent = t('progress.cancel')
    longBox.hidden = !long
    // The live line changes only with the stage, never every second: the seconds sit in the role=timer line,
    // which screen readers do not announce by themselves; the long state has its own live text above.
    const parts = [
      several ? t('upload.multiple') : '',
      t(stage === 'sending' ? 'progress.sending' : 'progress.processing', { name: lastFile.name })
    ]
    const line = parts.filter(Boolean).join(' ')
    if (status.textContent !== line) status.textContent = line
  }

  async function run(files: File[]): Promise<void> {
    if (!files.length || busy) return
    const file = files[0]
    lastFile = file
    fileName = file.name
    setChosen(t('upload.chosen', { name: fileName }))
    outcome = null
    cancelled = false
    clear(resultBox)
    stage = 'sending'
    started = Date.now()
    longBox.hidden = true
    several = files.length > 1
    setBusy(true)
    paintProgress()
    ticker = setInterval(paintProgress, 1000)
    abort = new AbortController()
    try {
      outcome = await convert(file, token.value, {
        signal: abort.signal,
        onUploaded: () => { stage = 'processing'; paintProgress() }
      })
    } catch {
      outcome = { kind: 'error', code: 'NETWORK', status: 0, detail: null, title: null }
    } finally {
      if (ticker !== null) clearInterval(ticker)
      ticker = null
      abort = null
      setBusy(false)
    }
    if (cancelled || (outcome.kind === 'error' && outcome.code === CANCELLED)) {
      outcome = null
      renderOutcome(false)
      status.textContent = t('progress.cancelled')
      pick.focus()
      return
    }
    // The badge follows this conversion at once. Its stated engine is newer than the kept answer of /status, so
    // that answer is dropped; a conversion that did not state an engine (a refusal, no header) tells nothing and
    // leaves the badge to /status.
    lastEngine = outcome.kind === 'ok' ? outcome.engine : null
    if (lastEngine !== null) statusMode = null
    paintMode()
    renderOutcome(true)
    void loadMode() // the service may have changed since (a model that stopped answering)
  }

  function renderOutcome(moveFocus: boolean): void {
    clear(resultBox)
    if (!outcome) { status.textContent = ''; return }
    if (outcome.kind === 'ok') {
      resultBox.append(renderConverted(outcome))
      status.textContent = doneStatus(outcome)
      if (moveFocus) resultBox.querySelector<HTMLElement>('#h-done')?.focus()
    } else {
      resultBox.append(renderProblem(outcome, {
        retry: () => { if (lastFile) void run([lastFile]) },
        pickOther: () => { if (!busy) fileInput.click() }
      }))
      status.textContent = t('status.refused')
      if (moveFocus) resultBox.querySelector<HTMLElement>('#h-error')?.focus()
    }
  }

  function paintMode(): void {
    const mode = badgeMode(lastEngine, statusMode)
    // For tests and scripts: data-mode is what the badge says, data-engine the raw token of the last conversion.
    if (lastEngine === null) modeBadge.removeAttribute('data-engine')
    else modeBadge.setAttribute('data-engine', lastEngine)
    if (mode === null) {
      modeBadge.hidden = true
      modeBadge.textContent = ''
      modeBadge.className = 'mode'
      modeBadge.removeAttribute('data-mode')
      modeBadge.removeAttribute('title')
      return
    }
    modeBadge.hidden = false
    modeBadge.className = `mode mode-${mode}`
    modeBadge.setAttribute('data-mode', mode)
    modeBadge.textContent = t('mode.' + mode)
    // "Nothing leaves this service" is a claim about the service, so it needs the service's own word: /status.
    // One conversion that ran on rules alone does not prove it.
    if (mode === 'rules' && statusMode === 'rules') modeBadge.setAttribute('title', t('mode.local'))
    else modeBadge.removeAttribute('title')
  }

  async function loadMode(): Promise<void> {
    const call = ++statusCall
    let answer: unknown = null
    try { answer = await getStatus() } catch { answer = null }
    if (call !== statusCall) return // a later request is on its way: this answer is the older one
    statusMode = modeOf(answer)
    paintMode()
  }

  function refresh(): void {
    document.documentElement.lang = getLang()
    document.title = t('app.title')
    for (const el of root.querySelectorAll<HTMLElement>('[data-i18n]')) el.textContent = t(el.dataset.i18n ?? '')
    for (const opt of select.options) opt.textContent = t('lang.' + opt.value)
    setChosen(fileName ? t('upload.chosen', { name: fileName }) : '')
    paintMode()
    if (busy) paintProgress()
    else renderOutcome(false)
  }

  const main = h('main', { id: 'main', tabindex: -1 }, upload, progress, status, resultBox)
  clear(root)
  root.append(i18nEl('a', 'app.skip', { href: '#main', class: 'skip' }), header, main)
  refresh()
  void loadMode()
  return { refresh }
}

function safeStorage(): Pick<Storage, 'getItem' | 'setItem'> | null {
  try { return window.localStorage } catch { return null }
}
