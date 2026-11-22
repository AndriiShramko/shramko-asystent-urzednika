// Two views of one result (wave 11). "Widok urzędnika" is the default: the original next to the ready e-form, only
// what the software could not settle, one final action. "Widok dla jury" keeps everything technical the page showed
// before. The choice lives in the module (it survives a rebuild of the result on a language change) and is written
// on the result root as data-view; the style sheet shows and hides `.clerk-only` / `.jury-only` by it.
import { t } from '../lib/i18n'
import { h } from './dom'

export type View = 'clerk' | 'jury'

let current: View = 'clerk'

export function getView(): View { return current }
export function setView(v: View): void { current = v }

/** Whether an element sits in a result shown in the clerk view (an element outside any result is not). */
export function inClerkView(el: Element): boolean {
  return el.closest('.result')?.getAttribute('data-view') === 'clerk'
}

function i18n<K extends keyof HTMLElementTagNameMap>(tag: K, key: string, attrs: Record<string, string | boolean | undefined> = {}): HTMLElementTagNameMap[K] {
  return h(tag, { 'data-i18n': key, ...attrs }, t(key))
}

/** The switch: two buttons, the pressed one is the view. It writes data-view on `root` and nothing else. */
export function viewSwitch(root: HTMLElement): HTMLElement {
  const buttons = (['clerk', 'jury'] as const).map((v) => i18n('button', 'view.' + v, { type: 'button', class: 'view-btn', 'data-set-view': v }))
  const paint = (): void => {
    root.setAttribute('data-view', current)
    for (const b of buttons) b.setAttribute('aria-pressed', String(b.getAttribute('data-set-view') === current))
  }
  for (const b of buttons) {
    b.addEventListener('click', () => {
      current = b.getAttribute('data-set-view') as View
      paint()
    })
  }
  paint()
  const box = h('div', { class: 'view-switch', id: 'view-switch', role: 'group' }, ...buttons)
  box.setAttribute('aria-label', t('view.label'))
  return box
}

/** A static text of ours inside a block that is built once: the page refreshes [data-i18n] on a language change. */
export const clerkText = i18n
