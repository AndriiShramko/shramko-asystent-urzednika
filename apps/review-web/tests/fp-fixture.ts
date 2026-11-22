// A synthetic form in the shape our composer writes (sections, SHOW conditions as in the judged results, partner
// initial-data defaults, dictionaries, validators). Labels are invented; no value is a real one.
import { cell, field } from './helpers'

const ref = (tab: string, sec: string, f: string): string =>
  `tabs['${tab}' in title].questions['${sec}' in field.techName].field.repeatingSectionGrid['${f}' in field.techName].field.__userAnswer`

export function fpForm() {
  const f = (id: string, type: string, title: string, techName: string, extra: Record<string, unknown> = {}) =>
    field(id, type, title, { techName, ...extra })
  const podmiot = f('s-podmiot', 'SECTION', 'Podmiot wniosku', 'podmiot_wniosku', {
    repeatingSectionGrid: [
      cell(f('r-kto', 'RADIO', 'Wybierz, w czyim imieniu wnioskujesz', 'wybierz_w_czyim_imieniu_wnioskujesz', {
        options: [{ id: 'Swoim', name: 'Swoim', techName: 'swoim' }, { id: 'Innej osoby', name: 'Innej osoby', techName: 'innej_osoby' }]
      }))
    ]
  })
  const twoje = f('s-twoje', 'SECTION', 'Twoje dane', 'twoje_dane', {
    repeatingSectionGrid: [
      cell(f('f-imie', 'TEXT_FIELD', 'Imię', 'imie', { readOnly: true, defaultValue: 'PESEL.name', defaultValueType: 'EXTERNAL_SYSTEM' })),
      cell(f('f-nazwisko', 'TEXT_FIELD', 'Nazwisko', 'nazwisko', { readOnly: true, defaultValue: 'PESEL.surname', defaultValueType: 'EXTERNAL_SYSTEM' }), 1),
      cell(f('f-pesel', 'TEXT_FIELD', 'Numer PESEL', 'numer_pesel', { readOnly: true, validation: ['PESEL'], defaultValue: 'PESEL.pesel', defaultValueType: 'EXTERNAL_SYSTEM' }), 2)
    ]
  })
  const adres = f('s-adres', 'SECTION', 'Adres zamieszkania', 'adres_zamieszkania', {
    repeatingSectionGrid: [
      cell(f('f-kraj', 'SELECT', 'Kraj', 'kraj', { dictionaryName: 'Kraje', defaultValue: ['Polska'] })),
      cell(f('f-ulica-z', 'TEXT_FIELD', 'Ulica', 'ulica_zagranica', {
        states: [{ type: 'SHOW', query: `$not("Polska" in ${ref('Dane', 'adres_zamieszkania', 'kraj')})` }]
      }), 1),
      cell(f('f-kod', 'TEXT_FIELD', 'Kod pocztowy', 'kod_pocztowy', {
        validation: ['ZIP_CODE'], defaultValue: 'MLPZ.postCode', defaultValueType: 'EXTERNAL_SYSTEM',
        states: [{ type: 'SHOW', query: `("Polska" in ${ref('Dane', 'adres_zamieszkania', 'kraj')})` }]
      }), 2),
      cell(f('f-ulica', 'TEXT_FIELD', 'Ulica', 'ulica', { defaultValue: 'MLPZ.street', defaultValueType: 'EXTERNAL_SYSTEM' }), 3),
      cell(f('f-bud', 'TEXT_FIELD', 'Numer budynku', 'numer_budynku', { defaultValue: 'MLPZ.building', defaultValueType: 'EXTERNAL_SYSTEM' }), 4)
    ]
  })
  const inna = f('s-inna', 'SECTION', 'Dane innej osoby', 'dane_innej_osoby', {
    states: [{ type: 'SHOW', query: `("Innej osoby" in ${ref('Dane', 'podmiot_wniosku', 'wybierz_w_czyim_imieniu_wnioskujesz')})` }],
    repeatingSectionGrid: [cell(f('f-imie-inna', 'TEXT_FIELD', 'Imię', 'imie_inna_osoba'))]
  })
  const sprawa = f('s-sprawa', 'SECTION', 'Szczegóły sprawy', 'szczegoly_sprawy', {
    repeatingSectionGrid: [
      cell(f('f-nip', 'TEXT_FIELD', 'NIP', 'nip', { validation: ['NIP'] })),
      cell(f('f-data', 'DATEPICKER', 'Data urodzenia', 'data_urodzenia', { validation: ['REQUIRED'] }), 1),
      cell(f('f-cel', 'TEXTAREA', 'Cel wydania', 'cel_wydania', { validation: ['REQUIRED'] }), 2),
      cell(f('f-info', 'TEXT_BLOCK', '', 'info', { description: '<html><body><p>Opłata <strong>17 zł</strong>.</p><script>x()</script></body></html>' }), 3),
      cell(f('f-dziwny', 'TEXT_FIELD', 'Pole z obcym warunkiem', 'dziwny', { states: [{ type: 'SHOW', query: '$count(x) > 1' }] }), 4),
      cell(f('f-zgoda', 'CONSENT_SECTION', '', 'zgoda', {
        consentSectionConfig: { consents: [{ description: '<p>Wyrażam zgodę.</p>', required: true }] }
      }), 5)
    ]
  })
  const kontakt = f('s-kontakt', 'SECTION', 'Dane do kontaktu', 'dane_do_kontaktu', {
    repeatingSectionGrid: [
      cell(f('f-tel', 'TEXT_FIELD', 'Numer telefonu', 'numer_telefonu', { defaultValue: 'MLPZ.phoneNumber', defaultValueType: 'EXTERNAL_SYSTEM' })),
      cell(f('f-mail', 'TEXT_FIELD', 'Adres e-mail', 'adres_e_mail', { validation: ['EMAIL'], defaultValue: 'MLPZ.email', defaultValueType: 'EXTERNAL_SYSTEM' }), 1)
    ]
  })
  return {
    title: 'Wniosek próbny o zaświadczenie',
    tabs: [
      { id: 't-1', title: 'Dane', type: 'MAIN', questions: [cell(podmiot), cell(twoje, 1), cell(adres, 2), cell(inna, 3)] },
      { id: 't-2', title: 'Szczegóły sprawy', type: 'MAIN', questions: [cell(sprawa)] },
      { id: 't-3', title: 'Kontakt', type: 'MAIN', questions: [cell(kontakt)] }
    ],
    flow: {}
  }
}

/** Form ids of the fixture that are matter fields (origin paper) vs standard. */
export function fpSidecar() {
  return {
    version: '1', converter: 'test', counts: { pages: 3, fields: 14 }, warnings: [],
    meta: {
      origins: { 's-sprawa': 'paper', 'f-nip': 'paper', 'f-data': 'paper', 'f-cel': 'paper', 's-twoje': 'standard', 's-adres': 'standard' },
      ledger: { rows: [] }
    }
  }
}

export function fpLedgerSidecar() {
  const s = fpSidecar() as ReturnType<typeof fpSidecar> & { converter: unknown }
  s.converter = { pipeline: 'brief' }
  s.meta.ledger = { rows: [
    { candidate: 'c1', fate: 'LEFT_OUT', reason: 'OFFICE_USE' },
    { candidate: 'c2', fate: 'STANDARD', section: 'standard/twoje_dane' },
    { candidate: 'c3', fate: 'STANDARD', section: 'standard/adres' },
    { candidate: 'c4', fate: 'FIELD', field: 'f-nip' },
    { candidate: 'c5', fate: 'FIELD', field: 'r-kto' },
    { candidate: 'c8', fate: 'FIELD', field: 'f-data' }
  ] } as never
  return s
}

export function fpPreview(geometry = true) {
  const page = { n: 1, w: 595.32, h: 842.04, source: 'native', img: { media_type: 'image/png', dpi: 150, width_px: 1241, height_px: 1755, data: 'AAAA' } }
  const place = (o: Record<string, unknown>) => geometry ? o : { ...o, box: undefined, anchor: 'p[3]' }
  return {
    version: 1, format: geometry ? 'pdf' : 'docx', units: 'pt', origin: 'top-left',
    page_images: geometry ? 'OK' : 'NO_PAGE_IMAGE',
    pages: geometry ? [page] : [],
    places: {
      c1: place({ page: 1, kind: 'office_use', box: [384, 30, 544, 38], label: 'Nr sprawy' }),
      c2: place({ page: 1, kind: 'cell', box: [55, 198, 539, 224], label: 'Imię i nazwisko', section: 's1' }),
      c3: place({ page: 1, kind: 'cell', box: [55, 224, 346, 245], label: 'Nr domu', section: 's1' }),
      c4: place({ page: 1, kind: 'leader', box: [258, 430, 365, 438], label: 'NIP', section: 's2' }),
      c5: place({ page: 1, kind: 'choice_group', box: [255, 489, 409, 499], label: 'W czyim imieniu', options: [{ text: 'Swoim', mark: 'c6' }, { text: 'Innej osoby', mark: 'c7' }] }),
      c6: place({ page: 1, kind: 'box', box: [255, 489, 261, 499], group: 'c5' }),
      c7: place({ page: 1, kind: 'box', box: [404, 489, 409, 499], group: 'c5' }),
      c8: { page: 1, kind: 'leader', anchor: 'p[9]', label: 'Data urodzenia' }
    },
    counts: { pages: 1, places: 8, boxed: 7, anchored: 1 }
  }
}
