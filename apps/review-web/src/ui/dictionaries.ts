// Wave 10 DICT: the block "Słowniki" of the result. (1) a proposed NEW dictionary: name, what it is for, entries
// (the first ENTRIES_SHOWN, the rest behind "pokaż wszystkie"), the field it would serve; (2) the partner's
// dictionaries linked to fields of the paper. One calm line when the report has neither. The names, entries and
// labels come from the paper through the service: they are shown as text, in elements marked lang="pl".
import { t, tn } from '../lib/i18n'
import type { Dictionaries, DictLink, ProposedDict } from '../lib/dictionaries'
import type { FieldRow } from '../lib/model'
import { h } from './dom'

export const ENTRIES_SHOWN = 8
const PL = { lang: 'pl' }

function fieldNames(ids: string[], rows: readonly FieldRow[]): string[] {
  const names: string[] = []
  for (const id of ids) {
    const row = rows.find((r) => r.id === id)
    const name = row && row.title.trim() ? row.title.trim() : null
    if (name && !names.includes(name)) names.push(name)
  }
  return names
}

function proposalBlock(p: ProposedDict, rows: readonly FieldRow[]): HTMLElement {
  const shown = p.entries.slice(0, ENTRIES_SHOWN)
  const rest = p.entries.slice(ENTRIES_SHOWN)
  const names = fieldNames(p.fields, rows)
  return h('div', { class: 'dict-proposal' },
    h('h4', {}, t('dict.name') + ' ', h('span', PL, p.name)),
    p.why || p.use
      ? h('p', {}, h('strong', {}, t('dict.purpose') + ' '), [p.why, p.use].filter(Boolean).join(' '))
      : null,
    names.length
      ? h('p', {}, h('strong', {}, tn('dict.fields', names.length) + ' '), h('span', PL, names.map((n) => '„' + n + '”').join(', ')))
      : null,
    p.pages.length ? h('p', { class: 'muted' }, tn('dict.pages', p.pages.length, { list: p.pages.join(', ') })) : null,
    h('p', {}, h('strong', {}, t('dict.entries', { n: p.entries.length }))),
    h('ul', { class: 'dict-entries', ...PL }, ...shown.map((e) => h('li', {}, e))),
    rest.length
      ? h('details', { class: 'dict-more' },
        h('summary', {}, t('dict.showAll', { n: p.entries.length })),
        h('ul', { class: 'dict-entries', ...PL }, ...rest.map((e) => h('li', {}, e))))
      : null)
}

function linkItem(l: DictLink): HTMLElement {
  return h('li', { class: 'dict-link' },
    h('span', PL, l.label ? '„' + l.label + '”' : t('dict.noLabel')),
    ' → ',
    h('strong', PL, l.dictionary),
    ' ',
    h('span', { class: 'chip' }, t(l.written ? 'dict.written' : 'dict.notWritten')))
}

/** The section, or null without a report (the page then cannot know which dictionaries apply). */
export function dictionariesSection(d: Dictionaries, rows: readonly FieldRow[], hasSidecar: boolean): HTMLElement | null {
  if (!hasSidecar) return null
  const section = h('section', { class: 'dictionaries', 'aria-labelledby': 'h-dict' },
    h('h2', { id: 'h-dict' }, t('dict.heading')))
  if (!d.proposals.length && !d.links.length) {
    section.append(h('p', { class: 'muted', id: 'dict-none' }, t('dict.none')))
    return section
  }
  if (d.proposals.length) {
    section.append(h('h3', { id: 'h-dict-new' }, tn('dict.proposalHeading', d.proposals.length)),
      h('p', { class: 'muted' }, t('dict.proposalIntro')),
      ...d.proposals.map((p) => proposalBlock(p, rows)))
  }
  if (d.links.length) {
    section.append(h('h3', { id: 'h-dict-links' }, t('dict.linksHeading')),
      h('p', { class: 'muted' }, t('dict.linksIntro')),
      h('ul', { class: 'plain dict-links' }, ...d.links.map(linkItem)))
  }
  return section
}
