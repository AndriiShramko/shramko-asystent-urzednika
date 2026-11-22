// W11 FLOW: what the person sees of the files in work. A bar that is filled only as far as the service reported
// (and moves without a number while nothing is known), and for several files a list: one row per file with its own
// state, bar, sign of life and buttons. Rows are built once and updated in place, so focus and reading position stay.
import { t } from '../lib/i18n'
import { h } from './dom'
import { aliveText, isEnded, percentOf, stageText, tally, type QueueItem } from './queue-model'

export interface Bar { el: HTMLElement; set(percent: number | null, label: string): void }

/** role=progressbar. With a percent: aria-valuenow and a filled part of that width. Without: no value (so nothing
 * is claimed) and the moving stripe that only says "working". */
export function createBar(id?: string): Bar {
  const run = h('div', { class: 'bar-run' })
  const fill = h('div', { class: 'bar-fill', hidden: true })
  const el = h('div', { class: 'bar', role: 'progressbar', ...(id ? { id } : {}) }, run, fill)
  return {
    el,
    set(percent, label) {
      el.setAttribute('aria-label', label)
      if (percent === null) {
        el.removeAttribute('aria-valuenow'); el.removeAttribute('aria-valuemin'); el.removeAttribute('aria-valuemax')
        run.hidden = false
        fill.hidden = true
        return
      }
      el.setAttribute('aria-valuemin', '0'); el.setAttribute('aria-valuemax', '100')
      el.setAttribute('aria-valuenow', String(percent))
      run.hidden = true
      fill.hidden = false
      fill.style.width = percent + '%'
    }
  }
}

/** A dot that beats once for every answer of the service: the visible sign that the service is alive. */
export function beat(dot: HTMLElement): void {
  dot.classList.remove('beat')
  void dot.offsetWidth // restart the animation
  dot.classList.add('beat')
}

export interface QueueHandlers {
  open: (item: QueueItem) => void
  cancel: (item: QueueItem) => void
  cancelAll: () => void
}

export interface QueueList {
  el: HTMLElement
  /** Replace the rows (a new set of files). */
  reset(items: readonly QueueItem[]): void
  /** Bring every row up to date. `selected` = the file whose result is shown below. */
  paint(items: readonly QueueItem[], selected: QueueItem | null, now: number, size: (bytes: number) => string): void
  /** The service answered about this file. */
  answered(item: QueueItem): void
}

interface Row {
  li: HTMLElement; name: HTMLElement; pct: HTMLElement; bar: Bar; stage: HTMLElement; alive: HTMLElement
  dot: HTMLElement; open: HTMLButtonElement; cancel: HTMLButtonElement
}

export function createQueueList(handlers: QueueHandlers): QueueList {
  const heading = h('h2', { id: 'h-queue', tabindex: -1 })
  const hint = h('p', { class: 'muted', id: 'queue-hint' })
  const list = h('ol', { class: 'q-list', id: 'queue-list' })
  const cancelAll = h('button', { type: 'button', class: 'btn', id: 'queue-cancel-all', 'data-i18n': 'flow.queue.cancelAll' }, t('flow.queue.cancelAll'))
  cancelAll.addEventListener('click', () => handlers.cancelAll())
  const el = h('section', { class: 'panel queue', id: 'queue', 'aria-labelledby': 'h-queue', hidden: true },
    heading, hint, list, cancelAll)
  const rows = new Map<number, Row>()

  function build(item: QueueItem): Row {
    const name = h('span', { class: 'q-name' })
    const pct = h('span', { class: 'q-pct' })
    const bar = createBar()
    const dot = h('span', { class: 'q-dot', 'aria-hidden': 'true' })
    const stage = h('p', { class: 'q-stage' })
    const alive = h('p', { class: 'q-alive muted' })
    const open = h('button', { type: 'button', class: 'btn q-open' })
    const cancel = h('button', { type: 'button', class: 'btn q-cancel' })
    open.addEventListener('click', () => handlers.open(item))
    cancel.addEventListener('click', () => handlers.cancel(item))
    const li = h('li', { class: 'q-row', 'data-id': String(item.id) },
      h('div', { class: 'q-head' }, name, pct),
      bar.el,
      h('div', { class: 'q-state' }, dot, stage),
      alive,
      h('div', { class: 'q-actions' }, open, cancel))
    return { li, name, pct, bar, stage, alive, dot, open, cancel }
  }

  return {
    el,
    reset(items) {
      rows.clear()
      while (list.firstChild) list.removeChild(list.firstChild)
      for (const item of items) {
        const row = build(item)
        rows.set(item.id, row)
        list.append(row.li)
      }
      el.hidden = items.length === 0
    },
    paint(items, selected, now, size) {
      const sum = tally(items)
      heading.textContent = t('flow.queue.heading', { all: sum.all, done: sum.done })
      hint.textContent = sum.active > 0 ? t('flow.queue.hint.working') : t('flow.queue.hint.ended', { done: sum.done, failed: sum.failed, all: sum.all })
      cancelAll.textContent = t('flow.queue.cancelAll')
      cancelAll.hidden = sum.active === 0
      for (const item of items) {
        const row = rows.get(item.id)
        if (!row) continue
        const percent = percentOf(item)
        const ended = isEnded(item)
        row.li.setAttribute('data-phase', item.phase)
        row.li.classList.toggle('selected', selected === item)
        row.name.textContent = t('flow.row.name', { name: item.file.name, size: size(item.file.size) })
        row.pct.textContent = percent === null || ended ? '' : t('flow.percent', { pct: percent })
        row.bar.el.hidden = ended || item.phase === 'pending'
        row.bar.set(percent, t('flow.row.barLabel', { name: item.file.name }))
        const text = stageText(item, now)
        if (row.stage.textContent !== text) row.stage.textContent = text
        row.alive.textContent = aliveText(item, now)
        row.alive.hidden = !row.alive.textContent
        row.dot.hidden = item.phase !== 'taken'
        const shown = selected === item
        row.open.hidden = !(item.phase === 'done' || item.phase === 'failed')
        row.open.textContent = shown ? t('flow.row.shown') : item.phase === 'failed' ? t('flow.row.why') : t('flow.row.open')
        row.open.setAttribute('aria-pressed', shown ? 'true' : 'false')
        row.cancel.hidden = ended
        row.cancel.textContent = t('progress.cancel')
        row.cancel.setAttribute('aria-label', t('flow.row.cancelLabel', { name: item.file.name }))
      }
    },
    answered(item) {
      const row = rows.get(item.id)
      if (row) beat(row.dot)
    }
  }
}
