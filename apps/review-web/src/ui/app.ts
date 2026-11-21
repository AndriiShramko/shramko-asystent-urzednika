// The page: header with the language switch, the upload panel, a live status line, the result. The upload panel
// is built once (so a typed token and the focus survive a change of language); its texts are refreshed through
// data-i18n attributes. The result is rebuilt from the kept outcome.
import { convertFile, type Outcome } from '../lib/api'
import { LANGS, getLang, initialLang, setLang, t, type Lang } from '../lib/i18n'
import { buildView } from '../lib/model'
import { h, clear } from './dom'
import { renderConverted, renderProblem } from './result'

const STORE_KEY = 'review.lang'

export interface AppDeps {
  convert: (file: File, token: string) => Promise<Outcome>
  store: Pick<Storage, 'getItem' | 'setItem'> | null
}

function i18nEl<K extends keyof HTMLElementTagNameMap>(tag: K, key: string, attrs: Record<string, string> = {}): HTMLElementTagNameMap[K] {
  const el = h(tag, { 'data-i18n': key, ...attrs })
  el.textContent = t(key)
  return el
}

export function mountApp(root: HTMLElement, deps: Partial<AppDeps> = {}): { refresh(): void } {
  const convert = deps.convert ?? ((f, tok) => convertFile(f, tok))
  const store = deps.store === undefined ? safeStorage() : deps.store
  setLang(initialLang(store?.getItem(STORE_KEY)))
  document.documentElement.lang = getLang()

  let outcome: Outcome | null = null
  let fileName = ''

  const status = h('p', { id: 'status', role: 'status', 'aria-live': 'polite', class: 'status' })
  const resultBox = h('div', { id: 'result', class: 'result-box' })

  // ---- header and language switch
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
    h('div', { class: 'lang' }, i18nEl('label', 'lang.label', { for: 'lang' }), select))

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

  pick.addEventListener('click', () => fileInput.click())
  fileInput.addEventListener('change', () => {
    const files = [...(fileInput.files ?? [])]
    fileInput.value = ''
    void run(files)
  })
  for (const ev of ['dragenter', 'dragover'] as const) {
    zone.addEventListener(ev, (e) => { e.preventDefault(); zone.classList.add('active'); setChosen(t('upload.dropActive')) })
  }
  for (const ev of ['dragleave', 'drop'] as const) {
    zone.addEventListener(ev, () => { zone.classList.remove('active'); setChosen(fileName ? t('upload.chosen', { name: fileName }) : '') })
  }
  zone.addEventListener('drop', (e) => {
    e.preventDefault()
    void run([...(e.dataTransfer?.files ?? [])])
  })

  function setChosen(text: string): void { chosen.textContent = text }

  async function run(files: File[]): Promise<void> {
    if (!files.length) return
    const file = files[0]
    fileName = file.name
    setChosen(t('upload.chosen', { name: fileName }))
    outcome = null
    clear(resultBox)
    status.textContent = (files.length > 1 ? t('upload.multiple') + ' ' : '') + t('upload.busy', { name: fileName })
    resultBox.setAttribute('aria-busy', 'true')
    pick.disabled = true
    try {
      outcome = await convert(file, token.value)
    } finally {
      pick.disabled = false
      resultBox.removeAttribute('aria-busy')
    }
    renderOutcome(true)
  }

  function renderOutcome(moveFocus: boolean): void {
    clear(resultBox)
    if (!outcome) { status.textContent = ''; return }
    if (outcome.kind === 'ok') {
      resultBox.append(renderConverted(outcome))
      status.textContent = t('status.done', { title: buildView(outcome.form, outcome.sidecar).title })
      if (moveFocus) resultBox.querySelector<HTMLElement>('#h-done')?.focus()
    } else {
      resultBox.append(renderProblem(outcome))
      status.textContent = t('status.refused')
      if (moveFocus) resultBox.querySelector<HTMLElement>('#h-error')?.focus()
    }
  }

  function refresh(): void {
    document.documentElement.lang = getLang()
    document.title = t('app.title')
    for (const el of root.querySelectorAll<HTMLElement>('[data-i18n]')) el.textContent = t(el.dataset.i18n ?? '')
    for (const opt of select.options) opt.textContent = t('lang.' + opt.value)
    setChosen(fileName ? t('upload.chosen', { name: fileName }) : '')
    renderOutcome(false)
  }

  const main = h('main', { id: 'main', tabindex: -1 }, upload, status, resultBox)
  clear(root)
  root.append(i18nEl('a', 'app.skip', { href: '#main', class: 'skip' }), header, main)
  refresh()
  return { refresh }
}

function safeStorage(): Pick<Storage, 'getItem' | 'setItem'> | null {
  try { return window.localStorage } catch { return null }
}
