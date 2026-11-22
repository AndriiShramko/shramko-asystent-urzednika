// W11 FLOW: the files the person gave the page, each with its own state, and the words for that state.
// Nothing here draws and nothing here counts time into the progress: the percent comes from the parts of the work
// the service reported as finished (`units`), the texts from the stage it named.
import type { JobStatus, Outcome } from '../lib/api'
import { hasKey, t } from '../lib/i18n'

/** pending: not sent yet; sending: on its way; full: the service's queue had no room, the page will offer the file
 * again; taken: the service has it (waiting or working: see `status`); done, failed, cancelled: ended;
 * skipped: over the number of files the page takes at once. */
export type Phase = 'pending' | 'sending' | 'full' | 'taken' | 'done' | 'failed' | 'cancelled' | 'skipped'

export interface QueueItem {
  id: number
  file: File
  phase: Phase
  sent: { loaded: number; total: number } | null
  status: JobStatus | null
  outcome: Outcome | null
  /** page clock: when the item began to be sent, when it ended */
  startedAt: number | null
  endedAt: number | null
  /** page clock of the service's last answer about this job */
  answeredAt: number | null
  /** questions in a row without an answer */
  silent: number
  /** page clock: when a file refused by a full queue is offered again */
  retryAt: number | null
  abort: AbortController | null
}

export function newItem(id: number, file: File, phase: Phase = 'pending'): QueueItem {
  return { id, file, phase, sent: null, status: null, outcome: null, startedAt: null, endedAt: null, answeredAt: null,
    silent: 0, retryAt: null, abort: null }
}

/** The page takes at most this many files at once; the waiting room of the service holds as many. */
export const MAX_FILES = 20

export const ENDED: readonly Phase[] = ['done', 'failed', 'cancelled', 'skipped']
export const isEnded = (item: QueueItem): boolean => ENDED.includes(item.phase)

/** Percent of the work that is finished, from the service's units and nothing else. null = the service has not
 * told (the file is still being sent, or the service has no job state): the page then shows no number. */
export function percentOf(item: QueueItem): number | null {
  if (item.phase === 'done') return 100
  const u = item.status?.units
  if (item.phase !== 'taken' || !u) return null
  return Math.max(0, Math.min(100, Math.floor((100 * u.done) / u.total)))
}

function pageWords(form: 'acc' | 'loc', page: number, pages: number | null): string {
  return pages ? t(`flow.page.${form}.of`, { page, pages }) : t(`flow.page.${form}.one`, { page })
}

/** The stage the service named, in plain words. */
export function runningText(status: JobStatus): string {
  const stage = status.stage
  if (!stage) return t('flow.processing')
  if (stage.name === 'reading' && stage.page && stage.step) {
    const key = 'flow.stage.reading.' + stage.step
    if (hasKey('pl', key)) {
      return t(key, { acc: pageWords('acc', stage.page, stage.pages), loc: pageWords('loc', stage.page, stage.pages) })
    }
  }
  const key = 'flow.stage.' + stage.name
  return hasKey('pl', key) ? t(key) : t('flow.processing')
}

/** One sentence: what is happening with this file now. */
export function stageText(item: QueueItem, now: number): string {
  switch (item.phase) {
    case 'pending': return t('flow.pending')
    case 'sending':
      return item.sent && item.sent.total > 0
        ? t('flow.sending.pct', { pct: Math.floor((100 * item.sent.loaded) / item.sent.total) }) : t('flow.sending')
    case 'full':
      return t('flow.full', { s: Math.max(0, Math.ceil(((item.retryAt ?? now) - now) / 1000)) })
    case 'taken': {
      const s = item.status
      if (!s) return t('flow.processing')
      if (s.state === 'queued') {
        const ahead = Math.max(0, (s.position ?? 1) - 1)
        return ahead === 0 ? t('flow.queued.next') : t('flow.queued', { pos: s.position ?? 1, ahead })
      }
      return runningText(s)
    }
    case 'done': return t('flow.done')
    case 'failed': return t('flow.failed', { reason: reasonOf(item) })
    case 'cancelled': return t('flow.cancelled')
    case 'skipped': return t('flow.skipped', { max: MAX_FILES })
  }
}

/** Why a file failed, in the words the result view uses for the same code. */
export function reasonOf(item: QueueItem): string {
  const o = item.outcome
  if (!o || o.kind !== 'error') return t('problem.UNKNOWN')
  if (item.file.size === 0) return t('problem.EMPTY_FILE')
  const key = 'problem.' + o.code
  return hasKey('pl', key) ? t(key) : o.code === 'HTTP' ? t('problem.HTTP') : t('problem.UNKNOWN')
}

/** The sign of life while the service works on the file: how long the current stage has lasted by the service's
 * own clock, and when the service last answered. Empty when there is nothing true to say. */
export function aliveText(item: QueueItem, now: number): string {
  if (item.phase !== 'taken' || !item.status || item.answeredAt === null) return ''
  const ago = Math.max(0, Math.round((now - item.answeredAt) / 1000))
  if (item.silent > 0) return t('flow.silent', { s: ago })
  if (item.status.state !== 'running' || item.status.stageS === null) return ''
  return t('flow.alive', { s: Math.floor(item.status.stageS), ago })
}

export interface Tally { all: number; done: number; failed: number; active: number; other: number }

export function tally(items: readonly QueueItem[]): Tally {
  const done = items.filter((i) => i.phase === 'done').length
  const failed = items.filter((i) => i.phase === 'failed').length
  const active = items.filter((i) => !isEnded(i)).length
  return { all: items.length, done, failed, active, other: items.length - done - failed - active }
}
