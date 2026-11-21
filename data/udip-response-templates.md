# UDIP response templates (Polish skeletons)

Status: 2026-11-21. Skeletons for AI-assisted drafting at a Polish city office. They contain **placeholders only**: no invented facts, no real persons. Every document is a DRAFT until a named clerk approves it; decisions (T10, T11) additionally need a lawyer and an authorised signatory.

Legal base: ustawa z dnia 6 września 2001 r. o dostępie do informacji publicznej (Dz. U. z 2022 r. poz. 902 oraz z 2025 r. poz. 1844), "UDIP"; Kodeks postępowania administracyjnego (t.j. Dz. U. z 2025 r. poz. 1691), "KPA". Check current Dz.U. references before use. Evidence of each rule is in `research/02-udip-law-process-taxonomy.md` (labels V verified, S secondary, U unverified).

Placeholder convention: `{{NAZWA}}` is filled by the system from the case record; `{{?NAZWA}}` is optional; `[[DO ZATWIERDZENIA: ...]]` marks text a human must write or confirm. Do not auto-fill reasons: they must come from the department and the clerk.

Common header block (all letters and decisions):

```
{{NAZWA_URZĘDU}}                                   {{MIEJSCOWOŚĆ}}, dnia {{DATA_PISMA}}
{{JEDNOSTKA_PROWADZĄCA}}
Znak sprawy: {{ZNAK_SPRAWY}}

{{WNIOSKODAWCA_IMIĘ_NAZWISKO_LUB_NAZWA}}
{{ADRES_DORĘCZENIA_LUB_E_MAIL}}
```

Common blocks:

- `BLOK_ART_12` (mandatory on every disclosure, UDIP art. 12): "Podmiot udostępniający informację: {{NAZWA_URZĘDU}}. Autor informacji lub osoba odpowiedzialna za jej treść: {{AUTOR_LUB_ODPOWIEDZIALNY}}. Osoba udostępniająca informację: {{IMIĘ_NAZWISKO_STANOWISKO_UDOSTĘPNIAJĄCEGO}}. Data udostępnienia: {{DATA_UDOSTĘPNIENIA}}."
- `STOPKA_RODO`: take the current wording from the office's own UDIP page. Review with the IOD whether the sentence on automated processing and profiling is still true once an AI assistant is used.
- `PODPIS`: "{{IMIĘ_NAZWISKO}}, {{STANOWISKO}}" plus signature or qualified electronic signature as the office rules require.

---

## T1. Udostępnienie informacji publicznej

- Nature: czynność materialno-techniczna (no decision, no appeal instruction).
- Legal basis: UDIP art. 10 ust. 1-2, art. 12, art. 13 ust. 1, art. 14 ust. 1.
- Deadline: bez zbędnej zwłoki, najpóźniej 14 dni od złożenia wniosku (D14), or the date announced in T5 (max 2 months from filing).
- Approvals: clerk, department head.

Mandatory elements checklist:

- [ ] Case number and reference to the request (date, channel)
- [ ] The information itself or attachments, in the **form and manner requested** (art. 14 ust. 1)
- [ ] Art. 12 block: disclosing entity, author or person responsible, person releasing, date
- [ ] Each numbered question answered or explicitly routed (multi-item request)
- [ ] No question about the applicant's purpose (art. 2 ust. 2)
- [ ] Redactions listed with the ground for each (art. 5 ust. 2) and, if any, a note that a decision T10 follows for that part

Pitfalls: an evasive or incomplete answer equals inaction; do not condition release on prior payment; send to the address and in the format requested.

Skeleton:

```
Dotyczy: Państwa wniosku z dnia {{DATA_WNIOSKU}} o udostępnienie informacji publicznej

W odpowiedzi na wniosek z dnia {{DATA_WNIOSKU}}, który wpłynął do {{NAZWA_URZĘDU}} dnia {{DATA_WPŁYWU}},
na podstawie art. 10 ust. 1 w związku z art. 14 ust. 1 ustawy z dnia 6 września 2001 r. o dostępie do informacji publicznej
udostępniam informację w zakresie:

{{NUMER_PYTANIA_1}}. {{TREŚĆ_PYTANIA_1}}
   Odpowiedź: {{ODPOWIEDŹ_1_LUB_WSKAZANIE_ZAŁĄCZNIKA}}
{{NUMER_PYTANIA_2}}. {{TREŚĆ_PYTANIA_2}}
   Odpowiedź: {{ODPOWIEDŹ_2_LUB_WSKAZANIE_ZAŁĄCZNIKA}}

Załączniki: {{LISTA_ZAŁĄCZNIKÓW}}
{{?UWAGA_O_ZANONIMIZOWANIU: W dokumentach zanonimizowano dane {{ZAKRES_DANYCH}} ze względu na {{PODSTAWA_PRAWNA_ART_5}}. W tym zakresie zostanie wydana decyzja o odmowie udostępnienia informacji.}}

[[BLOK_ART_12]]
PODPIS
```

---

## T2. Pismo: informacja nie stanowi informacji publicznej

- Nature: ordinary letter (not a decision). Bydgoszcz BIP card confirms the letter form.
- Legal basis: UDIP art. 1 ust. 1, art. 6 (test of "sprawa publiczna").
- Deadline: D14.
- Approvals: clerk, lawyer (mandatory; high inaction-complaint risk, especially for "dokument wewnętrzny").

Checklist:

- [ ] Which question or part is not public information
- [ ] Reason in terms of the content (private matter; request for opinion, legal advice or explanation; internal working document), not just the label
- [ ] Remaining parts answered (T1) or routed
- [ ] Information on other possible regime if relevant (see T12)
- [ ] Signature

Pitfalls: overuse of "dokument wewnętrzny" (NSA I OSK 2130/11 shows the narrow reading); documents that were a basis of a decision or paid with public money are public; a decision here is a defect.

Skeleton:

```
Dotyczy: Państwa wniosku z dnia {{DATA_WNIOSKU}}

W odpowiedzi na wniosek z dnia {{DATA_WNIOSKU}} informuję, że w zakresie {{NUMER_I_TREŚĆ_PYTANIA}}
żądana informacja nie stanowi informacji publicznej w rozumieniu art. 1 ust. 1 ustawy z dnia 6 września 2001 r.
o dostępie do informacji publicznej.

Uzasadnienie: [[DO ZATWIERDZENIA: konkretne uzasadnienie z uwzględnieniem treści żądania; odwołanie do art. 1 i art. 6 ustawy;
ewentualnie orzecznictwo {{SYGNATURA_ORZECZENIA}}]]

{{?W pozostałym zakresie informacje zostały udostępnione w piśmie znak {{ZNAK_PISMA_T1}}.}}
{{?Pouczenie: Pismo nie jest decyzją administracyjną. Przysługuje skarga do sądu administracyjnego na podstawie przepisów ustawy Prawo o postępowaniu przed sądami administracyjnymi w zakresie określonym w tych przepisach. [[DO ZATWIERDZENIA przez radcę prawnego]]}}

PODPIS
```

---

## T3. Pismo: urząd nie posiada informacji

- Nature: ordinary letter.
- Legal basis: UDIP art. 4 ust. 3 (obliged only if the information is held).
- Deadline: D14.
- Approvals: clerk, department head (confirm that every competent department searched).

Checklist:

- [ ] Clear statement that the office does not hold the information (or the part)
- [ ] Which departments and registers were checked (internal record, not necessarily in the letter)
- [ ] Remaining parts answered
- [ ] Optional: who may hold it, if known (courtesy, no duty to forward)

Pitfalls: statement must be true and checked; a partly held item must be released for the held part; a fact that "will be created" later is also "not held".

Skeleton:

```
Dotyczy: Państwa wniosku z dnia {{DATA_WNIOSKU}}

W odpowiedzi na wniosek z dnia {{DATA_WNIOSKU}} informuję, że {{NAZWA_URZĘDU}} nie posiada informacji
w zakresie {{NUMER_I_TREŚĆ_PYTANIA}}.
{{?Informacja może znajdować się w posiadaniu: {{PODMIOT_MOŻLIWIE_POSIADAJĄCY}}.}}
{{?W pozostałym zakresie informacje udostępniono w piśmie znak {{ZNAK_PISMA_T1}}.}}

PODPIS
```

---

## T4. Pismo: wskazanie BIP, portalu danych lub CRU JSFP

- Nature: ordinary letter.
- Legal basis: UDIP art. 10 ust. 1 (wording in force from 1.07.2026: BIP, portal danych, Centralny Rejestr Umów Jednostek Sektora Finansów Publicznych).
- Deadline: D14.
- Approvals: clerk.

Checklist:

- [ ] Exact URL (deep link) and navigation path to the specific information
- [ ] Verified that the page really holds the requested content, complete and current
- [ ] For CRU JSFP: contract concluded from 1.07.2026, requested fields are among the register fields
- [ ] Offer to release unpublished remainder by T1

Pitfalls: a general "see BIP" is treated as inaction; the office's ordinary website is not BIP.

Skeleton:

```
Dotyczy: Państwa wniosku z dnia {{DATA_WNIOSKU}}

Informacje, o które Państwo wnoszą w zakresie {{NUMER_I_TREŚĆ_PYTANIA}}, zostały udostępnione
w {{NAZWA_ŹRÓDŁA: Biuletynie Informacji Publicznej | portalu dane.gov.pl | Centralnym Rejestrze Umów Jednostek Sektora Finansów Publicznych}}
pod adresem: {{DOKŁADNY_ADRES_URL}}
Ścieżka dostępu: {{ŚCIEŻKA_NAWIGACJI}}
(art. 10 ust. 1 ustawy z dnia 6 września 2001 r. o dostępie do informacji publicznej).

{{?Informacje w zakresie {{POZOSTAŁY_ZAKRES}} zostały udostępnione w piśmie znak {{ZNAK_PISMA_T1}}.}}

PODPIS
```

---

## T5. Zawiadomienie o przedłużeniu terminu udostępnienia informacji

- Nature: written notice.
- Legal basis: UDIP art. 13 ust. 2.
- Deadline: must be **sent inside D14**; the new date is not later than 2 months from filing (D60). One extension only.
- Approvals: department head.

Checklist:

- [ ] Sent within 14 days from filing
- [ ] **Concrete** reasons why the information cannot be given in 14 days
- [ ] A specific calendar date, not later than D60
- [ ] Which items the extension concerns (the rest is answered now)

Pitfalls: generic reasons ("duża liczba spraw") are criticised; a late notice does not cure inaction; no second extension.

Skeleton:

```
Dotyczy: Państwa wniosku z dnia {{DATA_WNIOSKU}}

Na podstawie art. 13 ust. 2 ustawy z dnia 6 września 2001 r. o dostępie do informacji publicznej zawiadamiam,
że udostępnienie informacji w zakresie {{NUMER_I_TREŚĆ_PYTANIA}} nie jest możliwe w terminie 14 dni od złożenia wniosku.

Przyczyny: [[DO ZATWIERDZENIA: konkretne przyczyny podane przez komórkę merytoryczną]]
Nowy termin udostępnienia informacji: {{NOWA_DATA_NIE_PÓŹNIEJ_NIŻ_D60}}.

{{?Informacje w zakresie {{POZOSTAŁY_ZAKRES}} udostępniono w piśmie znak {{ZNAK_PISMA_T1}}.}}

PODPIS
```

---

## T6. Wezwanie do wykazania szczególnie istotnego interesu publicznego

- Nature: call (wezwanie), not a formal-defect call: no "pozostawienie bez rozpoznania".
- Legal basis: UDIP art. 3 ust. 1 pkt 1 (informacja przetworzona released only to the extent particularly important for the public interest); pattern in NSA I OSK 977/11, I OSK 1347/05.
- Deadline: within D14, usually sent together with T5. The time limit for the applicant is not set by statute (practice 7-14 days).
- Approvals: department head, lawyer.

Checklist:

- [ ] Explanation **why** the information is processed: operations, sources, scale, effort (from the department estimate)
- [ ] A reasonable time limit for the reply
- [ ] Information that, without the interest being shown, a refusal decision (T10) may be issued, and that the office itself will also assess the interest
- [ ] Combined with T5 so the clock does not run out
- [ ] Applicant identification state checked before a decision is on the horizon (T9)

Skeleton:

```
Dotyczy: Państwa wniosku z dnia {{DATA_WNIOSKU}}

Z analizy wniosku wynika, że żądane informacje w zakresie {{NUMER_I_TREŚĆ_PYTANIA}} mają charakter informacji przetworzonej,
ponieważ ich udostępnienie wymaga {{OPIS_CZYNNOŚCI_I_NAKŁADU}} [[DO ZATWIERDZENIA: opis z komórki merytorycznej]].
Zgodnie z art. 3 ust. 1 pkt 1 ustawy z dnia 6 września 2001 r. o dostępie do informacji publicznej udostępnienie
informacji przetworzonej jest możliwe w takim zakresie, w jakim jest to szczególnie istotne dla interesu publicznego.

Wzywam do wskazania, na czym polega szczególnie istotny interes publiczny w uzyskaniu informacji w tym zakresie,
w terminie {{LICZBA}} dni od otrzymania niniejszego pisma.
Informuję, że w przypadku niewykazania szczególnej istotności dla interesu publicznego może zostać wydana decyzja
o odmowie udostępnienia informacji przetworzonej.

{{?Jednocześnie, na podstawie art. 13 ust. 2 ustawy, zawiadamiam o przedłużeniu terminu do dnia {{NOWA_DATA}}. Przyczyny: {{PRZYCZYNY}}.}}

PODPIS
```

---

## T7. Zawiadomienie o wysokości opłaty

- Nature: notice.
- Legal basis: UDIP art. 15.
- Deadline: notify the amount **within 14 days from filing**; release after 14 days from the notice unless the applicant changes or withdraws the request.
- Approvals: clerk, finance.

Checklist:

- [ ] Amount and calculation of **real additional costs** caused by the requested manner or conversion (media, copies, postage)
- [ ] Statement that release follows after 14 days from the notice, unless the applicant changes the manner or form or withdraws
- [ ] Bank account or payment instruction
- [ ] No fee for staff time or for searching

Skeleton:

```
Dotyczy: Państwa wniosku z dnia {{DATA_WNIOSKU}}

Na podstawie art. 15 ustawy z dnia 6 września 2001 r. o dostępie do informacji publicznej zawiadamiam, że udostępnienie
informacji w sposób lub formie wskazanej we wniosku ({{SPOSÓB_I_FORMA}}) wiąże się z dodatkowymi kosztami w wysokości {{KWOTA}} zł,
na które składają się: {{SKŁADNIKI_KOSZTU_Z_KALKULACJI}}.

Informację udostępnię po upływie 14 dni od dnia powiadomienia o wysokości opłaty, chyba że w tym terminie
zmienią Państwo wniosek w zakresie sposobu lub formy udostępnienia informacji albo wycofają wniosek.
Dane do wpłaty: {{DANE_DO_WPŁATY}}.

PODPIS
```

---

## T8. Zawiadomienie na podstawie art. 14 ust. 2

- Nature: written notice with reasons.
- Legal basis: UDIP art. 14 ust. 2.
- Deadline: inside D14; the applicant has 14 days to file a new request; silence leads to T11.
- Approvals: clerk.

Checklist:

- [ ] Reasons why the requested form or manner is impossible (technical means only)
- [ ] The form or manner in which the information can be released **immediately**
- [ ] Instruction: new request within 14 days from the notice, otherwise the proceeding is discontinued by decision
- [ ] Proof of delivery recorded (date of receipt)

Skeleton:

```
Dotyczy: Państwa wniosku z dnia {{DATA_WNIOSKU}}

Na podstawie art. 14 ust. 2 ustawy z dnia 6 września 2001 r. o dostępie do informacji publicznej zawiadamiam,
że udostępnienie informacji w sposób lub formie wskazanej we wniosku ({{SPOSÓB_I_FORMA}}) nie jest możliwe,
ponieważ {{PRZYCZYNY_TECHNICZNE}} [[DO ZATWIERDZENIA]].
Informacja może zostać niezwłocznie udostępniona w następujący sposób lub formie: {{DOSTĘPNY_SPOSÓB_I_FORMA}}.

Jeżeli w terminie 14 dni od dnia powiadomienia nie złożą Państwo wniosku o udostępnienie informacji w sposób lub formie
wskazanej w niniejszym piśmie, postępowanie zostanie umorzone.

PODPIS
```

---

## T9. Wezwanie do uzupełnienia braków przed decyzją

- Nature: call under KPA art. 64 § 2.
- Legal basis: KPA art. 64 § 2; UDIP art. 16 ust. 2 (KPA applies to decisions); NSA III OSK 2396/25, I OSK 692/18 (missing personal data and signature as a curable formal defect at the decision stage); the office's identification policy after III OSK 1602/24.
- Deadline: at least 7 days for the applicant; sent as early as possible. Consequence: request left without consideration.
- Approvals: clerk, lawyer.

Checklist:

- [ ] What exactly is missing: name and surname (or company name), address for service, signature (or qualified channel)
- [ ] Time limit not shorter than 7 days
- [ ] Consequence stated: pozostawienie podania bez rozpoznania
- [ ] Used only when a decision is planned or under a documented office policy; not a tool to delay simple answers
- [ ] The data are mandatory only for the decision; the plain letter does not need them in the classic line

Skeleton:

```
Dotyczy: Państwa wniosku z dnia {{DATA_WNIOSKU}}

Na podstawie art. 64 § 2 Kodeksu postępowania administracyjnego wzywam do uzupełnienia braków formalnych wniosku
poprzez: {{BRAKUJĄCE_ELEMENTY: imię i nazwisko lub nazwa wnioskodawcy | adres do doręczeń | podpis}},
w terminie {{LICZBA_DNI_MIN_7}} dni od otrzymania wezwania.

Wezwanie jest związane z zamiarem wydania decyzji administracyjnej w sprawie wniosku z dnia {{DATA_WNIOSKU}}
{{?albo: {{KRÓTKI_OPIS_POLITYKI_URZĘDU_DOT_IDENTYFIKACJI}}}}.
Nieuzupełnienie braków w tym terminie spowoduje pozostawienie wniosku bez rozpoznania.

{{STOPKA_RODO}}
PODPIS
```

---

## T10. Decyzja o odmowie udostępnienia informacji publicznej

- Nature: administrative decision (KPA applies, UDIP art. 16 ust. 2).
- Legal basis: UDIP art. 5 (and art. 3 ust. 1 pkt 1 for processed information), art. 16 ust. 1-2; KPA art. 107 § 1.
- Deadline: D14 or the extended date (max D60).
- Approvals: lawyer (mandatory), IOD on request (privacy), signatory (upoważnienie).
- Precondition: applicant identified and signature on file (T9 first if not).

Checklist (KPA art. 107 § 1 plus UDIP art. 16 ust. 2):

- [ ] Heading "DECYZJA", case number, date
- [ ] Name of the authority and legal basis of competence
- [ ] Identification of the party (applicant)
- [ ] Ruling with **precise scope** of the refusal ("odmawiam udostępnienia informacji w zakresie ...")
- [ ] Factual reasoning (what was requested, what the office holds, which ground)
- [ ] Legal reasoning with articles (and case law if used)
- [ ] For processed information: reasons why it is processed **and** why a special public interest was not shown
- [ ] Art. 16 ust. 2 pkt 2: names, surnames and functions of persons who took a position, and the entities whose interests under art. 5 ust. 2 are protected
- [ ] Instruction on appeal: to {{ORGAN_ODWOŁAWCZY: Samorządowe Kolegium Odwoławcze w {{MIASTO}}}}, within 14 days from service, through the issuing authority; right to waive the appeal (KPA art. 127a)
- [ ] Signature with name and position (or qualified electronic signature)

Pitfalls: refusing something that is not public information is a defect (use T2); do not refuse more than the ground covers; partial restriction pairs with an anonymised release (T1).

Skeleton:

```
DECYZJA
Znak sprawy: {{ZNAK_SPRAWY}}

Na podstawie art. 16 ust. 1 w związku z art. 5 ust. {{USTĘP_ART_5}} {{?oraz art. 3 ust. 1 pkt 1}} ustawy z dnia 6 września 2001 r.
o dostępie do informacji publicznej (Dz. U. z 2022 r. poz. 902 oraz z 2025 r. poz. 1844) oraz art. 104 Kodeksu postępowania
administracyjnego,
po rozpatrzeniu wniosku {{WNIOSKODAWCA}} z dnia {{DATA_WNIOSKU}} o udostępnienie informacji publicznej w zakresie:
{{PRECYZYJNY_ZAKRES_WNIOSKU}},

orzekam
odmówić udostępnienia informacji publicznej w zakresie: {{PRECYZYJNY_ZAKRES_ODMOWY}}.

UZASADNIENIE
1. Stan faktyczny: {{PRZEBIEG_SPRAWY_I_TREŚĆ_WNIOSKU}} [[DO ZATWIERDZENIA]]
2. Podstawa prawna odmowy: {{OPIS_PODSTAWY_ART_5_ALBO_BRAK_SZCZEGÓLNEJ_ISTOTNOŚCI_DLA_INTERESU_PUBLICZNEGO}} [[DO ZATWIERDZENIA przez radcę prawnego]]
3. Osoby, które zajęły stanowisko w sprawie (art. 16 ust. 2 pkt 2): {{LISTA_IMIĘ_NAZWISKO_FUNKCJA}}
4. Podmioty, których interes prawnie chroniony uzasadnia odmowę (art. 5 ust. 2): {{LISTA_PODMIOTÓW_LUB_NIE_DOTYCZY}}

POUCZENIE
Od niniejszej decyzji przysługuje odwołanie do {{ORGAN_ODWOŁAWCZY}} za pośrednictwem {{ORGAN_WYDAJĄCY}} w terminie 14 dni od dnia
doręczenia decyzji. W trakcie biegu terminu do wniesienia odwołania strona może zrzec się prawa do wniesienia odwołania
wobec organu, który wydał decyzję. Z dniem doręczenia organowi oświadczenia o zrzeczeniu się prawa do wniesienia odwołania
decyzja staje się ostateczna i prawomocna.

{{STOPKA_RODO}}
PODPIS {{UPOWAŻNIENIE_NUMER}}
```

---

## T11. Decyzja o umorzeniu postępowania

- Nature: administrative decision.
- Legal basis: UDIP art. 14 ust. 2 zd. 2, art. 16 ust. 1; KPA art. 105 § 1 (adapted), art. 107.
- Deadline: after 14 days from the delivery of T8 passed without a new request.
- Approvals: clerk, signatory.
- Precondition: delivery of T8 proven; applicant identified (T9 if needed).

Checklist:

- [ ] Date of the T8 notice and date of its delivery
- [ ] Statement that 14 days passed without a new request
- [ ] KPA art. 107 § 1 elements and appeal instruction as in T10 (without the art. 16 ust. 2 pkt 2 additions)

Pitfalls: only for the art. 14 ust. 2 situation; withdrawal of a request needs no decision; no proof of delivery means no discontinuance.

Skeleton:

```
DECYZJA
Znak sprawy: {{ZNAK_SPRAWY}}

Na podstawie art. 14 ust. 2 i art. 16 ust. 1 ustawy z dnia 6 września 2001 r. o dostępie do informacji publicznej
oraz art. 105 § 1 Kodeksu postępowania administracyjnego, w sprawie wniosku {{WNIOSKODAWCA}} z dnia {{DATA_WNIOSKU}},

orzekam
umorzyć postępowanie w sprawie udostępnienia informacji publicznej.

UZASADNIENIE
Pismem z dnia {{DATA_T8}}, doręczonym dnia {{DATA_DORĘCZENIA_T8}}, zawiadomiono wnioskodawcę o niemożności udostępnienia informacji
w sposób lub formie wskazanej we wniosku oraz o możliwości złożenia w terminie 14 dni wniosku o udostępnienie informacji w sposób
lub formie wskazanej w zawiadomieniu. W tym terminie wniosek nie został złożony. W związku z tym postępowanie podlega umorzeniu.

POUCZENIE: [[jak w T10]]
PODPIS {{UPOWAŻNIENIE_NUMER}}
```

---

## T12. Pismo o innym trybie dostępu

- Nature: ordinary letter.
- Legal basis: UDIP art. 1 ust. 2 (special acts regulating access); the regime-specific act.
- Deadline: D14.
- Approvals: clerk.

Checklist:

- [ ] Which regime applies (KPA art. 73 files, petycje, skargi, informacja o środowisku, archives, akty stanu cywilnego, ewidencja ludności, zaświadczenie, prawo prasowe)
- [ ] Legal basis of that regime
- [ ] Where and how to file, or statement that the letter was passed on internally to {{KOMÓRKA}}
- [ ] For KPA art. 73: the applicant is a party of the case; otherwise the letter is T2

Pitfalls: check that the other act truly regulates access comprehensively; do not send a letter instead of a decision where the sector act requires a postanowienie.

Skeleton:

```
Dotyczy: Państwa wniosku z dnia {{DATA_WNIOSKU}}

Zgodnie z art. 1 ust. 2 ustawy z dnia 6 września 2001 r. o dostępie do informacji publicznej ustawa nie narusza przepisów
innych ustaw określających odmienne zasady i tryb dostępu do informacji będących informacjami publicznymi.
Dostęp do informacji w zakresie {{NUMER_I_TREŚĆ_PYTANIA}} jest uregulowany w {{AKT_PRAWNY_I_PRZEPIS}}.
{{?Wniosek został przekazany do {{KOMÓRKA_LUB_ORGAN}} celem rozpatrzenia w tym trybie.}}
{{?W tym trybie wniosek można złożyć: {{SPOSÓB_ZŁOŻENIA}}.}}

PODPIS
```

---

## Placeholder inventory (for the generator)

| Placeholder | Source in case record |
|---|---|
| `{{NAZWA_URZĘDU}}`, `{{JEDNOSTKA_PROWADZĄCA}}` | Office configuration |
| `{{ZNAK_SPRAWY}}`, `{{DATA_WPŁYWU}}` | EZD registration |
| `{{DATA_WNIOSKU}}`, `{{TREŚĆ_PYTANIA_n}}`, `{{NUMER_PYTANIA_n}}` | Request text split into items (S3) |
| `{{WNIOSKODAWCA_*}}`, `{{ADRES_DORĘCZENIA_LUB_E_MAIL}}` | Applicant record and `applicant_identification` state |
| `{{NOWA_DATA_NIE_PÓŹNIEJ_NIŻ_D60}}` | Computed: filing date + 2 months, then reduced by department estimate |
| `{{AUTOR_LUB_ODPOWIEDZIALNY}}`, `{{IMIĘ_NAZWISKO_STANOWISKO_UDOSTĘPNIAJĄCEGO}}` | Department reply and logged clerk |
| `{{ORGAN_ODWOŁAWCZY}}` | Office configuration (SKO) |
| `[[DO ZATWIERDZENIA]]` | Human author; the assistant may only propose text with citations |

## Gate rules for the generator

1. No document may be generated without a classification record (taxonomy id) and a computed D14 and D60.
2. T10 and T11 are generated only when `applicant_identification = identified` and the lawyer and signatory approvals are open tasks.
3. T5 and T6 are blocked after D14 and trigger a deadline-risk flag instead.
4. Every `[[DO ZATWIERDZENIA]]` marker must be resolved by a human before export; export fails otherwise.
5. Judgments cited in reasons must come from the verified list in the research report (orzeczenia.nsa.gov.pl links).
