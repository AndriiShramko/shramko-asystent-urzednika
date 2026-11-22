// Wave 11 KEY: the block "Model AI (opcjonalnie)". It says in plain words whether the optional model step is on,
// off or broken, shows where the key comes from (dots; the service never sends a key, at most its last four
// characters), lets a person type an address, a model name and a key for this session, and checks the connection
// with one small real call. A key typed here is kept in a variable of this tab only (no storage, no cookie), so
// "Pokaż" can show it in full in this tab and nowhere else.
import { checkModel, fetchAiState, forgetSession, isTyped, masked, typedOf, useInSession, type AiState, type Changed,
  type CheckResult, type Typed } from '../lib/aimodel'
import { t } from '../lib/i18n'
import { h } from './dom'

export interface ModelKeyDeps {
  state: (token: string) => Promise<AiState | null>
  check: (typed: Typed, token: string) => Promise<CheckResult>
  use: (typed: Typed, token: string) => Promise<Changed>
  forget: (token: string) => Promise<Changed>
  /** the access token of THIS service, from the upload panel (not the model key) */
  token: () => string
}

export interface ModelKeyBlock {
  el: HTMLElement
  /** texts again, after a change of language */
  refresh(): void
  /** ask the service again (after a conversion the state may have changed) */
  reload(): Promise<void>
}

function i18nEl<K extends keyof HTMLElementTagNameMap>(tag: K, key: string, attrs: Record<string, string> = {}): HTMLElementTagNameMap[K] {
  const el = h(tag, { 'data-i18n': key, ...attrs })
  el.textContent = t(key)
  return el
}

export function mountModelKey(deps: Partial<ModelKeyDeps> = {}): ModelKeyBlock {
  const token = deps.token ?? (() => (document.getElementById('token') as HTMLInputElement | null)?.value ?? '')
  const getState = deps.state ?? ((tok) => fetchAiState(tok))
  const check = deps.check ?? ((typed, tok) => checkModel(typed, tok))
  const use = deps.use ?? ((typed, tok) => useInSession(typed, tok))
  const forget = deps.forget ?? ((tok) => forgetSession(tok))

  let state: AiState | null = null
  let loaded = false
  let busy = false
  let revealed = false
  let touched = false            // has the person edited the address or the model name since the last answer
  let call = 0
  /** the last result line: a key of the dictionaries with its parameters, so a change of language repaints it */
  let result: { key: string; params: Record<string, string | number>; bad: boolean; still: boolean; lead?: string } | null = null

  const badge = h('span', { id: 'ai-badge', class: 'ai-badge' })
  const stateLine = h('p', { id: 'ai-state', class: 'ai-state' })
  const sourceLine = h('p', { id: 'ai-source', class: 'muted' })
  const url = h('input', { type: 'text', id: 'ai-url', name: 'ai-url', autocomplete: 'off', spellcheck: 'false', inputmode: 'url',
    'aria-describedby': 'ai-url-hint' })
  const model = h('input', { type: 'text', id: 'ai-model', name: 'ai-model', autocomplete: 'off', spellcheck: 'false' })
  const key = h('input', { type: 'password', id: 'ai-key', name: 'ai-key', autocomplete: 'off', spellcheck: 'false',
    'aria-describedby': 'ai-key-hint' })
  const reveal = h('button', { type: 'button', class: 'btn', id: 'ai-reveal', 'aria-controls': 'ai-key', 'aria-pressed': 'false' })
  const keyHint = h('p', { id: 'ai-key-hint', class: 'muted' })
  const checkBtn = i18nEl('button', 'ai.check', { type: 'button', class: 'btn', id: 'ai-check' })
  const useBtn = i18nEl('button', 'ai.use', { type: 'button', class: 'btn btn-main', id: 'ai-use' })
  const resetBtn = i18nEl('button', 'ai.reset', { type: 'button', class: 'btn', id: 'ai-reset' })
  const resultLine = h('p', { id: 'ai-result', class: 'ai-result', role: 'status', 'aria-live': 'polite' })
  const form = h('div', { id: 'ai-form' },
    h('div', { class: 'field-row' }, i18nEl('label', 'ai.url.label', { for: 'ai-url' }), url,
      i18nEl('p', 'ai.url.hint', { id: 'ai-url-hint', class: 'muted' })),
    h('div', { class: 'field-row' }, i18nEl('label', 'ai.model.label', { for: 'ai-model' }), model),
    h('div', { class: 'field-row' }, i18nEl('label', 'ai.key.label', { for: 'ai-key' }),
      h('div', { class: 'ai-keyrow' }, key, reveal), keyHint),
    h('div', { class: 'actions' }, checkBtn, useBtn, resetBtn),
    resultLine,
    i18nEl('p', 'ai.session.note', { class: 'muted' }))
  const details = h('details', { id: 'ai-details', class: 'ai-details' },
    h('summary', {}, i18nEl('span', 'ai.heading', { id: 'h-ai' }), ' ', badge),
    i18nEl('p', 'ai.intro', { class: 'muted' }),
    stateLine, sourceLine, form)
  const el = h('section', { class: 'panel ai', id: 'ai', 'aria-labelledby': 'h-ai', hidden: true }, details)

  const typed = (): Typed => typedOf(state, url.value, model.value, key.value)

  function paint(): void {
    el.hidden = !loaded || state === null   // a service without this block (an older build): nothing is shown
    if (state === null) return
    const s = state
    badge.textContent = t('ai.badge.' + s.state)
    badge.className = 'ai-badge ai-' + s.state
    el.setAttribute('data-state', s.state)
    el.setAttribute('data-source', s.source)
    const why = s.state === 'fallback' ? t('ai.check.' + (s.problem || 'server_error')) : ''
    stateLine.textContent = s.state === 'on'
      ? t(s.used ? 'ai.state.on' : 'ai.state.on.unused', { model: s.model })
      : s.state === 'fallback' ? t('ai.state.fallback', { why }) : t('ai.state.' + s.state)
    stateLine.className = 'ai-state ai-state-' + s.state
    sourceLine.textContent = s.source === 'none' ? '' : t('ai.source.' + s.source)
    sourceLine.hidden = s.source === 'none'

    const editable = s.pageConfig && !busy
    for (const input of [url, model, key]) input.disabled = !editable
    form.hidden = s.state === 'disabled'
    // The key field: what the person typed, or dots for a key that only the service knows.
    const serverKey = s.keySet && !key.value
    key.type = revealed && key.value ? 'text' : 'password'
    key.placeholder = serverKey ? masked(revealed ? s.keyTail : '') : ''
    key.classList.toggle('ai-key-server', serverKey)
    reveal.textContent = t(revealed ? 'ai.hide' : 'ai.show')
    reveal.setAttribute('aria-pressed', revealed ? 'true' : 'false')
    reveal.disabled = !key.value && !s.keySet
    keyHint.textContent = key.value ? t('ai.key.hint.typed')
      : !s.keySet ? t('ai.key.hint.none')
        : revealed ? t(s.keyTail ? 'ai.key.hint.tail' : 'ai.key.hint.notail', { tail: s.keyTail })
          : t('ai.key.hint.' + (s.keyOrigin || 'environment-variable'))
    const dirty = isTyped(typed())
    checkBtn.disabled = busy
    useBtn.disabled = busy || !dirty || !s.pageConfig
    useBtn.hidden = !s.pageConfig
    resetBtn.hidden = s.source !== 'session' || !s.pageConfig
    resetBtn.disabled = busy
    if (busy) {
      resultLine.textContent = t('ai.checking')
      resultLine.className = 'ai-result'
    } else if (result) {
      const text = (result.lead ? t(result.lead) + ' ' : '') + t(result.key, result.params) + (result.still ? ' ' + t('ai.stillWorks') : '') +
        (result.bad && result.params.http !== '' ? ' ' + t('ai.http', result.params) : '')
      resultLine.textContent = text
      resultLine.className = 'ai-result ' + (result.bad ? 'ai-bad' : 'ai-good')
    } else {
      resultLine.textContent = ''
      resultLine.className = 'ai-result'
    }
    resultLine.setAttribute('data-code', busy ? 'busy' : result ? result.key.replace('ai.check.', '') : '')
  }

  /** The fields follow the service unless the person is in the middle of typing. */
  function fill(): void {
    if (!state || touched) return
    url.value = state.address
    model.value = state.model
  }

  function show(res: { ok: boolean; code: string; http?: number | null; ms?: number }, lead?: string): void {
    const seconds = new Intl.NumberFormat(document.documentElement.lang || 'pl', { maximumFractionDigits: 1 }).format((res.ms ?? 0) / 1000)
    result = { key: 'ai.check.' + res.code, params: { http: res.http ?? '', s: seconds }, bad: !res.ok,
      still: !res.ok && !['token', 'no_service', 'busy'].includes(res.code), lead }
  }

  async function reload(): Promise<void> {
    const mine = ++call
    const next = await getState(token())
    if (mine !== call) return
    const first = !loaded
    loaded = true
    state = next
    fill()
    // Open by itself when there is something to see: a model that is on or broken. Off stays one quiet line.
    if (first && state && (state.state === 'on' || state.state === 'fallback')) details.open = true
    paint()
  }

  async function during(work: () => Promise<void>): Promise<void> {
    if (busy) return
    busy = true
    paint()
    try { await work() } finally { busy = false; paint() }
  }

  checkBtn.addEventListener('click', () => void during(async () => {
    show(await check(typed(), token()))
    if (!isTyped(typed())) { call++; state = (await getState(token())) ?? state }   // a good check ends a fallback
  }))

  useBtn.addEventListener('click', () => void during(async () => {
    const sent = typed()
    const res = await use(sent, token())
    if (!res.ok) { show({ ok: false, code: res.code }); return }
    // The key stays in the field (this tab's memory), so it can be looked at; the service got it once, just now.
    touched = false
    call++
    state = res.state ?? (await getState(token())) ?? state
    fill()
    show(await check({}, token()), 'ai.used')
    state = (await getState(token())) ?? state
  }))

  resetBtn.addEventListener('click', () => void during(async () => {
    const res = await forget(token())
    if (!res.ok) { show({ ok: false, code: res.code }); return }
    key.value = ''
    revealed = false
    touched = false
    call++
    state = res.state ?? (await getState(token())) ?? state
    fill()
    result = { key: 'ai.reset.done', params: {}, bad: false, still: false }
  }))

  reveal.addEventListener('click', () => { revealed = !revealed; paint() })
  for (const input of [url, model]) input.addEventListener('input', () => { touched = true; result = null; paint() })
  key.addEventListener('input', () => { result = null; paint() })

  void reload()
  return { el, refresh: paint, reload }
}

/** Put the block on a mounted page, after the upload panel, and keep it in step with the page: the language
 * switch repaints it, a change of the mode badge (a finished conversion, a new /status) asks the service again. */
export function attachModelKey(root: HTMLElement, deps: Partial<ModelKeyDeps> = {}): ModelKeyBlock {
  const block = mountModelKey(deps)
  const main = root.querySelector('#main')
  const upload = main?.querySelector('section.panel')
  if (upload) upload.after(block.el)
  else (main ?? root).append(block.el)
  root.querySelector('#lang')?.addEventListener('change', () => block.refresh())
  const mode = root.querySelector('#mode')
  if (mode && typeof MutationObserver !== 'undefined') {
    let timer: ReturnType<typeof setTimeout> | null = null
    new MutationObserver(() => {
      if (timer !== null) clearTimeout(timer)
      timer = setTimeout(() => { timer = null; void block.reload() }, 300)
    }).observe(mode, { attributes: true, attributeFilter: ['data-mode', 'data-engine'] })
  }
  return block
}
