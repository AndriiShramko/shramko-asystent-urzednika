// The page: header with the mode badge and the language switch, the upload panel, a progress panel, a live status
// line, the result. The upload panel is built once (so a typed token and the focus survive a change of language);
// its texts are refreshed through data-i18n attributes. The result is rebuilt from the kept outcome.
import { CANCELLED, convertQueued, fetchStatus, previewFile, type ConvertHooks, type Engine, type Outcome } from '../lib/api'
import { LANGS, getLang, initialLang, setLang, t, type Lang } from '../lib/i18n'
import { badgeMode, modeOf, type Mode } from '../lib/verdict'
import { h, clear } from './dom'
import { doneStatus, renderConverted, renderProblem } from './result'
import { mountFill, type FillBlock } from './fill'

const STORE_KEY = 'review.lang'
/** After this long the page says the wait is unusual and offers to stop. */
export const LONG_MS = 90_000
// UX2: a separate import line, so the import block above stays as the fill-and-print patches (FP-2..FP-6) expect it.
import { acceptOf, formatsOf, formatsText } from '../lib/verdict'
// W11 FLOW: progress by the stages the service reports, and several files at once (queue-model.ts, queue-view.ts).
import { MAX_FILES, aliveText, newItem, percentOf, stageText, tally, type QueueItem } from './queue-model'
import { beat, createBar, createQueueList } from './queue-view'

export interface AppDeps {
  convert: (file: File, token: string, hooks?: ConvertHooks) => Promise<Outcome>
  store: Pick<Storage, 'getItem' | 'setItem'> | null
  /** GET /status as JSON, or null when it failed. */
  status: () => Promise<unknown>
  /** POST /v1/forms/preview for the same file (wave 10); any failure resolves to null. */
  preview: (file: File, token: string) => Promise<unknown>
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
  const convert = deps.convert ?? ((f, tok, hooks) => convertQueued(f, tok, hooks))
  const store = deps.store === undefined ? safeStorage() : deps.store
  const getStatus = deps.status ?? (() => fetchStatus())
  // A page with an injected convert (tests, scripts) calls no real preview unless one is injected too.
  const getPreview = deps.preview ?? (deps.convert ? async () => null : (f: File, tok: string) => previewFile(f, tok))
  setLang(initialLang(store?.getItem(STORE_KEY)))
  document.documentElement.lang = getLang()

  // W11 FLOW: every file of the last choice with its own state; `current` is the one whose result is shown.
  let items: QueueItem[] = []
  let current: QueueItem | null = null
  let fileName = ''
  let busy = false
  let started = 0
  let ticker: ReturnType<typeof setInterval> | null = null
  let cancelled = false
  let several = false
  // The fill-and-print block of each result: built once per conversion, kept across a language change.
  const fills = new Map<number, FillBlock>()
  let whenIdle: Array<() => void> = []
  // The badge has two sources (see badgeMode): what /status said last, and the engine of the last conversion.
  let statusMode: Mode | null = null
  let lastEngine: Engine | null = null
  let statusCall = 0
  // What /status said about the service besides the mode: accepted formats, the job time limit in seconds.
  let formats: string[] = []
  let jobLimitS: number | null = null

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
  // No `accept` until /status names the formats: the page does not invent the list, the service decides.
  const fileInput = h('input', { type: 'file', id: 'file', class: 'sr-only', tabindex: -1, 'aria-hidden': 'true', multiple: true })
  const pick = i18nEl('button', 'upload.button', { type: 'button', class: 'btn btn-main', id: 'pick' })
  const chosen = h('p', { class: 'muted', id: 'chosen' })
  const token = h('input', { type: 'password', id: 'token', name: 'token', autocomplete: 'off', spellcheck: 'false',
    'aria-describedby': 'token-hint' })
  // The formats line comes from GET /status (`formats`); hidden while the page does not know them.
  const formatsLine = h('p', { class: 'muted', id: 'formats', hidden: true })
  const manyHint = h('p', { class: 'muted', id: 'many-hint' })
  const zone = h('div', { class: 'drop', id: 'drop' },
    i18nEl('p', 'upload.drop'), pick, fileInput, manyHint, chosen)
  const upload = h('section', { 'aria-labelledby': 'h-upload', class: 'panel' },
    i18nEl('h2', 'upload.heading', { id: 'h-upload' }),
    zone,
    formatsLine,
    h('div', { class: 'field-row' },
      i18nEl('label', 'upload.token.label', { for: 'token' }), token,
      i18nEl('p', 'upload.token.hint', { id: 'token-hint', class: 'muted' })))

  // ---- progress panel: file name and size, a moving bar without a percentage, elapsed seconds, the long state
  const progFile = h('p', { id: 'progress-file', class: 'progress-file' })
  // W11 FLOW: the bar is filled as far as the service reported finished work; no number while nothing is known.
  const progressBar = createBar('progress-bar')
  const bar = progressBar.el
  const stageDot = h('span', { class: 'q-dot', 'aria-hidden': 'true', hidden: true })
  const stageLine = h('span', { id: 'progress-stage' })
  const stageBox = h('p', { class: 'q-state progress-stage', hidden: true }, stageDot, stageLine)
  const aliveLine = h('p', { id: 'progress-alive', class: 'muted', hidden: true })
  const elapsed = h('p', { id: 'progress-elapsed', class: 'muted', role: 'timer' })
  // its own polite live text: the sentence is set only when the wait becomes long, so it is announced once
  const longText = h('p', { id: 'progress-long', class: 'progress-long', 'aria-live': 'polite' })
  const cancelBtn = h('button', { type: 'button', class: 'btn', id: 'progress-cancel' })
  const longBox = h('div', { id: 'progress-longbox', hidden: true }, longText, cancelBtn)
  const progress = h('div', { id: 'progress', class: 'progress', hidden: true }, progFile, bar, stageBox, aliveLine, elapsed, longBox)
  cancelBtn.addEventListener('click', () => { cancelled = true; items[0]?.abort?.abort() })
  const giveUp = (item: QueueItem): void => { if (item.phase === 'pending') item.phase = 'cancelled'; else item.abort?.abort() }
  const queue = createQueueList({
    open: (item) => show(item, true),
    cancel: (item) => { giveUp(item); paintProgress() },
    cancelAll: () => { items.forEach(giveUp); paintProgress() }
  })

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
    zone.addEventListener(ev, () => { zone.classList.remove('active'); setChosen(chosenText()) })
  }
  zone.addEventListener('drop', (e) => {
    e.preventDefault()
    if (busy) return
    void run([...(e.dataTransfer?.files ?? [])])
  })

  function setChosen(text: string): void { chosen.textContent = text }
  function chosenText(): string {
    return several ? t('flow.chosen.many', { n: items.length }) : fileName ? t('upload.chosen', { name: fileName }) : ''
  }

  function setBusy(on: boolean): void {
    busy = on
    pick.disabled = on
    fileInput.disabled = on
    zone.classList.toggle('busy', on)
    if (on) zone.setAttribute('aria-disabled', 'true')
    else zone.removeAttribute('aria-disabled')
    progress.hidden = !on || several
    if (on) resultBox.setAttribute('aria-busy', 'true')
    else resultBox.removeAttribute('aria-busy')
  }

  function paintQueue(): void { queue.paint(items, current, Date.now(), formatSize) }

  /** The live line for several files: the counts, said again only when they change. */
  function paintBatchStatus(): void {
    const sum = tally(items)
    const line = sum.active > 0
      ? t('flow.status.batch', { all: sum.all, done: sum.done, failed: sum.failed })
      : t('flow.status.batchDone', { all: sum.all, done: sum.done, failed: sum.failed })
    if (status.textContent !== line) status.textContent = line
  }

  function paintProgress(): void {
    if (!busy) return
    if (several) { paintQueue(); paintBatchStatus(); return }
    const item = items[0]
    if (!item) return
    const now = Date.now()
    const secs = Math.floor((now - started) / 1000)
    progFile.textContent = t('progress.file', { name: item.file.name, size: formatSize(item.file.size) })
    // The percent comes from the parts of the work the service reported finished; null = nothing reported yet.
    const percent = percentOf(item)
    progressBar.set(percent, t('progress.label'))
    // What the service said it is doing. Shown only when it said something (or the bytes sent are known).
    const told = item.status !== null || item.phase === 'full' || (item.phase === 'sending' && item.sent !== null)
    const words = told ? stageText(item, now) : ''
    stageLine.textContent = words && percent !== null ? t('flow.stage.withPercent', { text: words, pct: percent }) : words
    stageBox.hidden = !words
    stageDot.hidden = item.phase !== 'taken' || item.status === null
    aliveLine.textContent = aliveText(item, now)
    aliveLine.hidden = !aliveLine.textContent
    elapsed.textContent = t('progress.elapsed', { s: secs })
    const long = now - started >= LONG_MS
    longText.textContent = !long ? ''
      : jobLimitS ? t('progress.long.limit', { min: Math.max(1, Math.round(jobLimitS / 60)) }) : t('progress.long')
    cancelBtn.textContent = t('progress.cancel')
    longBox.hidden = !long
    // The live line changes only with the stage, never every second: the seconds sit in the role=timer line,
    // which screen readers do not announce by themselves; the long state has its own live text above.
    const line = item.status !== null ? words
      : t(item.phase === 'sending' || item.phase === 'pending' ? 'progress.sending' : 'progress.processing', { name: item.file.name })
    if (status.textContent !== line) status.textContent = line
  }

  /** One file from the first byte sent to its end. `accepted` is called when the service has taken the file (or
   * the file has ended): the next file is sent only then, so the page never pushes twenty uploads at once. */
  async function work(item: QueueItem, accepted: () => void): Promise<void> {
    item.phase = 'sending'
    item.startedAt = Date.now()
    item.abort = new AbortController()
    paintProgress()
    let out: Outcome
    try {
      out = await convert(item.file, token.value, {
        signal: item.abort.signal,
        onSent: (loaded, total) => {
          item.sent = { loaded, total }
          if (item.phase === 'full' && Date.now() >= (item.retryAt ?? 0)) item.phase = 'sending'
          paintProgress()
        },
        onUploaded: () => { item.phase = 'taken'; item.retryAt = null; accepted(); paintProgress() },
        onFull: (retryS) => { item.phase = 'full'; item.sent = null; item.retryAt = Date.now() + retryS * 1000; paintProgress() },
        onStatus: (s) => {
          item.status = s
          item.answeredAt = Date.now()
          item.silent = 0
          if (several) queue.answered(item)
          else beat(stageDot)
          paintProgress()
        },
        onSilent: (n) => { item.silent = n; paintProgress() }
      })
    } catch {
      out = { kind: 'error', code: 'NETWORK', status: 0, detail: null, title: null }
    }
    item.abort = null
    item.endedAt = Date.now()
    item.outcome = out
    item.phase = out.kind === 'ok' ? 'done' : out.code === CANCELLED ? 'cancelled' : 'failed'
    accepted()
    if (!several) return
    // The badge follows the newest finished conversion; the first finished file is shown without being asked for.
    if (out.kind === 'ok' && out.engine !== null) { lastEngine = out.engine; statusMode = null; paintMode() }
    if (current === null && item.phase === 'done') show(item, false)
    paintProgress()
  }

  /** Send every waiting file, one after the other, and wait for all of them. One failure stops nothing. */
  async function processPending(): Promise<void> {
    setBusy(true)
    paintProgress()
    ticker = setInterval(paintProgress, 1000)
    const waits: Promise<void>[] = []
    try {
      for (const item of items) {
        if (item.phase !== 'pending') continue   // given up while it waited, or over the limit
        let accepted: () => void = () => undefined
        const taken = new Promise<void>((resolve) => { accepted = resolve })
        const done = work(item, accepted)
        waits.push(done)
        await Promise.race([taken, done])
      }
      await Promise.all(waits)
    } finally {
      if (ticker !== null) clearInterval(ticker)
      ticker = null
      setBusy(false)
      for (const go of whenIdle) go()
      whenIdle = []
    }
  }

  async function run(files: File[]): Promise<void> {
    if (!files.length || busy) return
    items = files.map((f, i) => newItem(i + 1, f, i < MAX_FILES ? 'pending' : 'skipped'))
    several = items.length > 1
    current = null
    fills.clear()
    cancelled = false
    fileName = several ? '' : files[0].name
    setChosen(chosenText())
    clear(resultBox)
    started = Date.now()
    longBox.hidden = true
    queue.reset(several ? items : [])
    await processPending()
    if (several) {
      paintQueue()
      paintBatchStatus()
      void loadMode()
      return
    }
    const item = items[0]
    if (cancelled || item.phase === 'cancelled') {
      current = null
      renderOutcome(false)
      status.textContent = t('progress.cancelled')
      pick.focus()
      return
    }
    current = item
    // The badge follows this conversion at once. Its stated engine is newer than the kept answer of /status, so
    // that answer is dropped; a conversion that did not state an engine (a refusal, no header) tells nothing and
    // leaves the badge to /status.
    lastEngine = item.outcome?.kind === 'ok' ? item.outcome.engine : null
    if (lastEngine !== null) statusMode = null
    paintMode()
    renderOutcome(true)
    void loadMode() // the service may have changed since (a model that stopped answering)
  }

  /** Several files: show the result (or the reason of the failure) of one of them below the list. */
  function show(item: QueueItem, moveFocus: boolean): void {
    if (!item.outcome) return
    current = item
    renderOutcome(moveFocus)
    paintQueue()
  }

  /** Several files: one failed file is sent again in its own row; the others keep their results. */
  async function again(item: QueueItem): Promise<void> {
    if (busy) return
    Object.assign(item, newItem(item.id, item.file))
    fills.delete(item.id)
    if (current === item) { current = null; clear(resultBox) }
    await processPending()
    paintQueue()
    paintBatchStatus()
  }

  /** The page pictures for the fill-and-print block. While other files of the set are in work the service answers
   * BUSY to this side call, so it is asked once more when the set has ended. */
  function previewFor(file: File): Promise<unknown> {
    const ask = (): Promise<unknown> => getPreview(file, token.value).catch(() => null)
    return ask().then((got) => {
      if (got !== null || !busy) return got
      return new Promise<void>((resolve) => { whenIdle.push(resolve) }).then(ask)
    })
  }

  function renderOutcome(moveFocus: boolean): void {
    clear(resultBox)
    const outcome = current?.outcome ?? null
    if (!current || !outcome) { if (!several) status.textContent = ''; return }
    const item = current
    if (outcome.kind === 'ok') {
      const view = renderConverted(outcome)
      resultBox.append(view)
      let fill = fills.get(item.id)
      if (!fill) {
        fill = mountFill(outcome, previewFor(item.file))
        fills.set(item.id, fill)
      }
      // Steps 3 to 6 sit between the review and the form JSON (the JSON stays last, as before).
      const json = view.querySelector('section[aria-labelledby="h-json"]')
      if (json) view.insertBefore(fill.el, json)
      else view.append(fill.el)
      if (!several) status.textContent = doneStatus(outcome)
      if (moveFocus) resultBox.querySelector<HTMLElement>('#h-done')?.focus()
    } else {
      resultBox.append(renderProblem(outcome, {
        retry: () => { if (several) void again(item); else void run([item.file]) },
        pickOther: () => { if (!busy) fileInput.click() }
      }, { fileSize: item.file.size, formats }))
      if (!several) status.textContent = t('status.refused')
      if (moveFocus) resultBox.querySelector<HTMLElement>('#h-error')?.focus()
    }
    if (several) resultBox.prepend(h('p', { class: 'q-which', id: 'result-which' }, t('flow.result.which', { name: item.file.name })))
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
    const known = formatsOf(answer)
    if (known.length) formats = known // a failed /status later does not erase what the service said before
    const limit = (answer as { limits?: { job_timeout_s?: unknown } } | null)?.limits?.job_timeout_s
    if (typeof limit === 'number' && limit > 0 && Number.isFinite(limit)) jobLimitS = limit
    paintMode()
    paintFormats()
  }

  function paintFormats(): void {
    formatsLine.hidden = formats.length === 0
    formatsLine.textContent = formats.length ? t('upload.formats', { list: formatsText(formats) }) : ''
    const accept = acceptOf(formats)
    if (accept) fileInput.setAttribute('accept', accept)
    else fileInput.removeAttribute('accept')
  }

  function refresh(): void {
    document.documentElement.lang = getLang()
    document.title = t('app.title')
    for (const el of root.querySelectorAll<HTMLElement>('[data-i18n]')) el.textContent = t(el.dataset.i18n ?? '')
    for (const opt of select.options) opt.textContent = t('lang.' + opt.value)
    setChosen(chosenText())
    manyHint.textContent = t('flow.drop.many', { max: MAX_FILES })
    paintMode()
    paintFormats()
    if (busy) paintProgress()
    if (several) { paintQueue(); paintBatchStatus() }
    if (!busy || several) renderOutcome(false)
  }

  const main = h('main', { id: 'main', tabindex: -1 }, upload, progress, queue.el, status, resultBox)
  clear(root)
  root.append(i18nEl('a', 'app.skip', { href: '#main', class: 'skip' }), header, main)
  refresh()
  void loadMode()
  return { refresh }
}

function safeStorage(): Pick<Storage, 'getItem' | 'setItem'> | null {
  try { return window.localStorage } catch { return null }
}
