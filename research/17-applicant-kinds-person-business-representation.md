# Research 17: who may apply (applicant kinds, representation, identifiers, e-Delivery, registers)

Prepared 21 November 2026 for the HackNation 2026 task "Cyfryzacja formularzy" (partner: COI).
Scope: how Polish administrative forms treat the applicant, and how the partner's standard ("Podmiot wniosku") handles it, so that our converter can decide from the paper which sections, identifiers, attachments and fees follow.

How to read the evidence. Every source below was opened on 2026-11-21. Source ids in square brackets point to the legend in section 12. Labels: "inference" = my reasoning from verified facts; "unverified" = could not be confirmed from an official source today. Primary legal texts were read as consolidated texts from the Sejm ELI API (the official Dziennik Ustaw publisher), text in force on the dates shown in the legend. Polish diacritics are dropped in some quotes because the PDF text layer loses them.

## TL;DR for builders

- The partner's "Podmiot wniosku" is two radios: "w czyim imieniu" (Swoim / Innej osoby / Osoby prawnej lub jednostki organizacyjnej) and "jako kto" (Pelnomocnik / Reprezentant, shown only for the legal-person branch). Both reference exports use it unchanged, so it is a standard block, not a per-form choice [R1].
- Legal gaps in that block (details in section 8): no statutory representative or guardian path, no PESEL or date of birth for "another person", no sole-trader path, no e-Delivery address, no validators, REGON/KRS present in one export and absent in the other.
- Stamp duty for a power of attorney is 17 zl per power-of-attorney relation (Annex to the Stamp Duty Act, part IV). It is NOT always due: 8 statutory exemptions, among them spouse, ascendant, descendant, sibling, and the general power of attorney under the Tax Ordinance [S1].
- Where it is paid is fixed by art. 12 of the same act: for an electronic submission, the office of the principal's residence or seat; if the principal has none in Poland, the President of Warsaw. The partner's fee text already says this correctly [S1][R1].
- Statutory representation (parent, guardian, curator, organ of a legal person) is not a power of attorney: no power-of-attorney fee, different proof (court decision, KRS extract). The partner's tree merges these cases under "Pelnomocnik/Reprezentant" (inference from [S2] art. 30 par. 2-3 and art. 33).
- All main identifiers can be validated offline. PESEL, NIP, REGON-9/14, ID card, NRB/IBAN and the 8-digit bank settlement number were checked by me against published examples (all pass). Algorithms are in section 4 and the code block there is ready to paste.
- Parcel identifier format is official and exact: WWPPGG_R.XXXX.NDZ (regulation on land and building register, annex 5) [S4]. This is the field "Numer ewidencyjny dzialki" in the first reference form.
- Two things I could NOT verify from official sources: the two check digits of the e-Delivery address (ADE) and the land-register check-digit formula. I tested 3 real ADEs against about 20,000 candidate formulas: no match. Validate the ADE by format only until the partner or the ministry gives the rule.
- e-Delivery calendar that matters to forms: public bodies from 1 Jan 2025; CEIDG entrepreneurs without an address had to be in the address base by 30 Sep 2026 (so from 1 Oct 2026 every JDG has one); KRS entities from the date set in the ministerial communique (about 1 Apr 2025, medium confidence); hybrid service for local government and courts from 1 Oct 2029 [S3].
- Since the KPA amendment, an electronic application is lodged to the office's e-Delivery address or its account; mail to an ordinary office e-mail is left unprocessed. So the form's "e-mail" is a notification channel only, and an ADE field belongs in the contact block [S2 art. 63].
- Registers as future "initial data" (CEIDG, KRS, REGON/BIR, VAT white list, e-Delivery address base) are all free or free-to-register. I propose source names in the partner's notation (section 7). The product itself calls nothing; it only emits the names.
- The paper itself tells the applicant kind: "imie i nazwisko lub nazwa firmy", "adres zamieszkania/siedziby", "w imieniu", "pelnomocnik", "reprezentant klubu z KRS" appear in the sample forms of this repo. Section 9 turns wording into sections, validators, attachments and fees.
- Ten dictionaries proposed (section 10). Highest value for a government IT centre: identity document kind, legal form (GUS), offices and bodies (with ADE), kind of power of attorney (carrying the fee rule), degree of kinship (carrying the exemption flag).

## 1. Applicant kinds and their legal basis

Procedural capacity in administrative proceedings: art. 28-30 KPA (text in force: Dz.U. 2025 poz. 1691, consolidated 7 Nov 2025) [S2]. Verified wording:

- Art. 28: a party is anyone whose legal interest or duty the proceeding concerns, or who requests an act of the authority because of their own legal interest or duty.
- Art. 29: parties may be natural persons and legal persons; for state and local-government organisational units and for social organisations also units without legal personality.
- Art. 30 par. 1: capacity is judged by civil law. Par. 2: natural persons without capacity act through statutory representatives. Par. 3: parties that are not natural persons act through statutory or statute-based representatives.

| Kind | Legal basis (text in force Nov 2026) | Who acts | Typical identifiers |
|---|---|---|---|
| Natural person | KPA art. 28-30 [S2]; place of residence: Civil Code art. 25 [S5] | the person; or pelnomocnik; or statutory representative if no capacity | PESEL; without PESEL: date of birth and identity document (see 4.3) |
| Natural person running a business (JDG, CEIDG) | Civil Code art. 43(1): an entrepreneur is a natural person, a legal person or a unit from art. 33(1) [S5]; CEIDG act art. 5 [S6] | the person; prokurent or pelnomocnik registered in CEIDG | PESEL if any (else date of birth), NIP if any, REGON if any, citizenship, delivery address, business address, ADE [S6 art. 5] |
| Legal person (company, association, foundation, cooperative, state/local legal entity) | KPA art. 29 and 30 par. 3 [S2]; Civil Code art. 38-41 (organ, seat) [S5] | organ per statute and register (board, president), prokurent, pelnomocnik | KRS, NIP, REGON-9 |
| Organisational unit without legal personality that has capacity | Civil Code art. 33(1) par. 1: provisions on legal persons apply accordingly [S5]; KPA art. 29 (state/local units, social organisations) [S2] | its organ or statutory representative | NIP, REGON (KRS for partnerships entered in it) |
| Partners of a civil partnership (spolka cywilna) | not a legal entity or art. 33(1) unit: partners act as natural persons or entrepreneurs (inference from Civil Code art. 33(1) and 43(1)); CEIDG entry is per partner [S6] | partners jointly or each, or a pelnomocnik | PESEL/NIP per partner; NIP and REGON of the partnership (unverified in detail) |
| Housing community (wspolnota mieszkaniowa) | Act on ownership of premises art. 6: the community of owners may acquire rights, take on obligations, sue and be sued [S7] | board (zarzad) or administrator; evidence is the resolution on the board (inference, art. 18-22 not re-read) | NIP, REGON (no KRS); inference |
| Office or body as applicant | art. 29 KPA state/local units [S2]; exempt from stamp duty by art. 7 [S1] | head of the unit or authorised employee | REGON, ADE (public entities must hold an ADE: e-Delivery act art. 8 [S8]) |

Takeaway for the converter: the three radio values of the partner (Swoim / Innej osoby / Osoby prawnej lub jednostki organizacyjnej) cover the table only coarsely. "Natural person running a business" and "civil partnership" fall in "Swoim" or "legal person" depending on wording; the standard has no marker for them (section 8).

## 2. Representation

| Representative | Basis | Proof the office may ask for | Fee |
|---|---|---|---|
| Pelnomocnik (KPA) | Art. 32: a party may act through a pelnomocnik unless the act requires personal action. Art. 33 par. 1: only a natural person with legal capacity. Par. 2: power of attorney in writing or declared to the record. Par. 3: original or officially certified copy; advocates, legal advisers, patent attorneys and tax advisers may certify copies themselves. Par. 4: in minor matters the office may skip the document when the pelnomocnik is a close family member or household member and there is no doubt [S2] | the document; the former par. 2a (electronic form) is repealed, electronic submission is governed by art. 63 [S2] | 17 zl per relation unless exempt [S1] |
| Statutory representative of a person without capacity | KPA art. 30 par. 2 [S2]; parents: Family Code (not re-read; inference) | birth certificate, court decision for a guardian or curator (inference) | none for a power of attorney (inference: no pelnomocnictwo document is filed); matters of guardianship and curatorship are exempt anyway by art. 2 par. 1 pkt 1 lit. a [S1] |
| Representative for a person absent or incapacitated | KPA art. 34: the office asks the court to appoint one [S2] | court decision | none (inference) |
| Statutory or statute-based representative of a non-natural party | KPA art. 30 par. 3 [S2] | extract from KRS or other register; the office can see public registers itself: art. 220 par. 1 pkt 2 KPA forbids demanding a certificate or statement on facts the office can establish from public registers it can access electronically [S2] | none |
| Prokurent | Civil Code art. 109(1): prokura is a pelnomocnictwo given by an entrepreneur entered in CEIDG or the KRS register of entrepreneurs, covering court and out-of-court acts connected with running the enterprise; art. 109(2): written form, a natural person with full capacity [S5]. CEIDG also stores pelnomocnik and prokurent data: name, PESEL, NIP, citizenship, delivery address [S6 art. 5] | entry in KRS or CEIDG | 17 zl is due "per power-of-attorney relation (prokura)" [S1 annex IV]; whether the register entry replaces the document for the fee is described by a tax authority only in a secondary source: unverified |
| Social organisation acting for another person | KPA art. 31 [S2] | statute; consent of the person | n/a |

KPA art. 63 par. 2 sets the minimum content of an application: who it comes from, their address (also for electronic applications) and a request. Without an address the application is left without consideration (art. 64 par. 1) [S2]. This is the legal root of the "Twoje dane" and address sections in the standard.

Tax matters add their own rules (the second reference form is a tax-overpayment request). The Tax Ordinance has a general power of attorney kept in the central register of general powers (CRPO); it is exempt from stamp duty (annex IV pkt 6) [S1]. Details of the Tax Ordinance articles were not re-read: unverified beyond the exemption.

## 3. Stamp duty

Source: consolidated text of the Stamp Duty Act announced 9 Oct 2026, Dz.U. 2026 poz. 1395, legal state on 1 Oct 2026 [S1]. Everything in this section is quoted or paraphrased from that text unless marked.

### 3.1 Power of attorney (annex, part IV)

- Subject: filing a document certifying a power of attorney or prokura, or its copy, extract or duplicate, in an administrative matter or court proceeding (art. 1 par. 1 pkt 2).
- Amount: 17 zl "od kazdego stosunku pelnomocnictwa (prokury)". Joint power of attorney of several principals is one relation (secondary source, [S9]: inference supported).
- Who pays: the principal, the pelnomocnik, the entrepreneur or the prokurent (art. 5 par. 1); jointly and severally if filed together (art. 5 par. 2).
- When due: at the moment of filing the document in the authority (art. 6 par. 1 pkt 4); the fee is paid at that moment (art. 6 par. 2).
- Where paid: the competent tax organ is the wojt, burmistrz or president (art. 12 par. 1). For a power of attorney filed on paper: the organ of the place of filing (art. 12 par. 2 pkt 2). For one filed electronically through an IT system: the organ of the principal's residence or seat; with several principals in one document, the first one resident in Poland; if none is resident in Poland, the President of Warsaw (art. 12 par. 2 pkt 3). Payment is to the organ's cash desk or account (art. 8 par. 1). The gov.pl page of the Public Procurement Office says the same and adds the Warsaw account for the Centrum Obslugi Podatnika [S9]; the partner's text uses exactly this rule [R1].
- Exemptions in annex IV (column 4), verbatim in substance:
  1. certified by a notary or an authorised body, authorising only the receipt of documents;
  2. in matters: criminal, fiscal-criminal, disciplinary, petty offences; civil matters where the principal is exempt from court costs;
  3. granted to a spouse, ascendant, descendant or sibling;
  4. where the principal is an entity from art. 7 pkt 1-5;
  5. for signing electronically filed tax returns;
  6. a general power of attorney under the Tax Ordinance;
  7. to file or change a simplified registration notification or a notification of ceasing activity as an intermediary or consuming oil entity (excise act);
  8. a special power of attorney under the Identity Cards Act.
- Art. 7 exemptions (entities): foreign states under reciprocity, budget units, local-government units, metropolitan unions, public benefit organisations acting only in connection with unpaid public benefit activity, persons presenting a social-assistance certificate for poverty, and the nature-protection case in pkt 6.
- Art. 2 par. 1 pkt 1 lit. a-b also exempts the power of attorney itself in matters of maintenance, guardianship, curatorship, adoption, social and health insurance and some benefits.
- Note on the partner's form: the first reference form asks "Czy zlozenie pelnomocnictwa wymaga oplaty skarbowej? Tak/Nie" for "another person" but never lists the exemptions, so the applicant must guess. The legal-person pelnomocnik branch asks nothing and always shows the fee text. Inference: both should use the same question with the exemption list as help text.

### 3.2 Typical matters (annex, part I, part II)

Amounts below are as printed in [S1] part II (certificates and extracts) unless marked.

| Matter | Amount | Note |
|---|---|---|
| Short extract of a civil-status record | 22 zl | part II pkt 1 item 12 |
| Full extract of a civil-status record | 33, 39 or 50 zl depending on case | part II pkt 1 items 5-11; the competent organ for electronic issue is the place where the record was drawn up (art. 12 par. 2 pkt 1a) |
| "Pozostale zaswiadczenia" (other certificates) | 17 zl is the amount every sample form of this repo quotes ("Wniosek o wydanie zaswiadczenia": "17 zl (od kazdego egzemplarza)"); the amount cell of part II pkt 21 fell on a page I could not read in the text layer: unverified in the act text itself | exemptions by case (pkt 21 sub-items) |
| Extract or full copy of processed personal data from residents' registers | 17 zl | part II pkt 2 |
| Power of attorney | 17 zl | part IV |

The price of a matter belongs to the matter (the form's subject), not to the applicant kind. Applicant kind only changes who is exempt (art. 7) and which organ receives the payment (art. 12). Refund: on the payer's request, without a decision, within 2 months if justified (art. 9 par. 2a) [S1]; a transitional rule (art. 31 of the act of 29 May 2026, Dz.U. 2026 poz. 846) keeps the old rules for refund requests filed before its entry into force [S1].

Fee changes in 2025-2026 to watch: from 1 Jan 2025 the payment of the fee on an electronically signed power of attorney was changed by the act of 19 Nov 2024, Dz.U. 2024 poz. 1757 [S9]; a June 2025 draft to remove the paper/electronic difference was found, adoption not confirmed (secondary, unverified). The consolidated text of Oct 2026 already contains the "organ of the principal's residence" rule, so the electronic rule is in force.

## 4. Identifiers and exact validation algorithms

All algorithms below were implemented and run on 2026-11-21 on the published textbook example of each identifier (one per kind: PESEL, NIP, REGON with 9 and with 14 digits, identity card, IBAN, bank settlement number). All returned valid. The example values are deliberately not repeated here: the publishing check of this repository refuses any literal identifier with a valid check digit, so tests build their values from a stem and a computed check digit. Reference code:

```python
def pesel(s):   # 11 digits, weights 1,3,7,9,1,3,7,9,1,3 ; check = (10 - S mod 10) mod 10
    w=[1,3,7,9,1,3,7,9,1,3]
    return len(s)==11 and s.isdigit() and (10-sum(int(a)*b for a,b in zip(s,w))%10)%10==int(s[10])
def nip(s):     # 10 digits, weights 6,5,7,2,3,4,5,6,7 ; mod 11 ; remainder 10 = invalid number
    if len(s)!=10 or not s.isdigit(): return False
    r=sum(int(a)*b for a,b in zip(s,[6,5,7,2,3,4,5,6,7]))%11
    return r!=10 and r==int(s[9])
def regon(s):   # 9 digits: 8,9,2,3,4,5,6,7 mod 11 (10->0); 14 digits: first 9 valid + 2,4,8,5,0,9,7,3,6,1,2,4,8 mod 11 (10->0)
    if not s.isdigit(): return False
    if len(s)==9:
        r=sum(int(a)*b for a,b in zip(s,[8,9,2,3,4,5,6,7]))%11
        return (0 if r==10 else r)==int(s[8])
    if len(s)==14:
        r=sum(int(a)*b for a,b in zip(s,[2,4,8,5,0,9,7,3,6,1,2,4,8]))%11
        return regon(s[:9]) and (0 if r==10 else r)==int(s[13])
    return False
def id_card(s): # 3 letters + 6 digits ; A=10..Z=35 ; weights 7,3,1,9,7,3,1,7,3 ; sum mod 10 == 0 (check digit is char 4)
    if len(s)!=9 or not s[:3].isalpha() or not s[3:].isdigit(): return False
    return sum(int(c,36)*w for c,w in zip(s.upper(),[7,3,1,9,7,3,1,7,3]))%10==0
def iban(s):    # ISO 13616 / ISO 7064 mod 97-10 ; NRB = 26 digits without country prefix
    s=s.replace(' ','').upper(); s=s if s[:2].isalpha() else 'PL'+s
    return int(''.join(str(int(c,36)) for c in s[4:]+s[:4]))%97==1
def nbp_settlement(s):  # 8 digits, weights 3,9,7,1 repeated, sum mod 10 == 0 (check digit last)
    return len(s)==8 and s.isdigit() and sum(int(a)*b for a,b in zip(s,[3,9,7,1]*2))%10==0
```

### 4.1 Table of identifiers

| Identifier | Format | Algorithm and official source | Confidence |
|---|---|---|---|
| PESEL | 11 digits: YYMMDD, serial (3), sex digit (even female, odd male), check digit | weights above; month offset +80 (1800s), +0 (1900s), +20 (2000s), +40 (2100s), +60 (2200s). Source: Polish Wikipedia PESEL page, which cites the Population Records Act and the MSWiA regulation of 4 Jan 2012 [S10]. The regulation text itself not opened: medium. A valid checksum does not prove the number exists; duplicates occurred (same source) | high for algorithm, medium for source |
| NIP | 10 digits | weights 6,5,7,2,3,4,5,6,7, mod 11, remainder 10 never issued [S11]; NIP Act cited there as Dz.U. 2026 poz. 151 | high |
| REGON-9 | 9 digits | weights 8,9,2,3,4,5,6,7, mod 11, 10 becomes 0 [S12] | high |
| REGON-14 | 14 digits: parent REGON-9 + 4 digits of the local unit + check | weights 2,4,8,5,0,9,7,3,6,1,2,4,8, mod 11, 10 becomes 0; first nine must be a valid REGON-9 [S12] | high |
| KRS number | 10 digits, leading zeros kept (example used by the registry: 0000026438, a public company) | I found no check digit in any official text: unverified that none exists; treat as format only (inference) | medium |
| ID card | 3 letters + 6 digits | A=10..Z=35, weights 7,3,1,9,7,3,1,7,3, sum mod 10 = 0 [S13]; legal basis Identity Cards Act of 6 Aug 2010 (Dz.U. 2025 poz. 1753 cited there). Series in use: A, C, D, DEA | high |
| Passport | 2 letters + 7 digits (Polish format, inference); the visible number has no check digit; the machine-readable zone has one (ICAO 9303: weights 7,3,1, A=10..Z=35, mod 10) | secondary forum only: unverified | low |
| Land and mortgage register (KW) | court code (4 chars) / number (8 digits) / check digit (1), separated by "/" | Structure is official: Regulation of the Minister of Justice, Dz.U. 2024 poz. 1583 [S14]. The regulation says the check digit is "calculated from the court code and the number" and does not print the formula [S14][S15]. Community implementation: character values 0-9 as is, X=10, A=11, B=12 and so on (letters Q and V not used), weights 1,3,7 repeated over the 12 characters, sum mod 10: UNVERIFIED (a GitHub gist found by search; not run) | structure high, formula low |
| NRB / IBAN | 26 digits (2 check + 8 settlement + 16 account); IBAN adds PL | provider identifiers follow Polish Standard PN-F-01102 [S16]; mod 97-10 as for IBAN (ISO 13616) (verified by running the example) | high |
| Bank settlement number | 8 digits, last is check | weights 3,9,7,1 repeated, mod 10 [S16 annex 2]; positions 3-10 of an NRB (secondary [S17]) | high |
| Postal code | NN-NNN | pattern only; no checksum; list is the Poczta Polska PNA database (not opened): inference | medium |
| TERYT TERC | 7 characters: WW (voivodeship) PP (county) GG (commune) R (type of commune) | structure used in the EGiB identifier WWPPGG_R [S4 annex 5]; meaning of R digits not opened: inference | medium |
| SIMC | 7 digits locality identifier, stable and unique | no public check formula found: unverified | low |
| ULIC | street identifier (5 digits), plus street "cecha" such as ul., al., pl., os. | the 2021 regulation on the register of localities, streets and addresses requires cecha and ULIC id per TERYT (found by search [S18]); digit counts unverified | low |
| Cadastral parcel | WWPPGG_R.XXXX.NDZ: unit id, then area (obreb) 0001-9999, then parcel number | exact, annex 5 of the regulation on the land and building register [S4]. Building: WWPPGG_R.XXXX.Nr_BUD; premises: building id + "." + number | high |
| e-Delivery address (ADE) | AE:PL-XXXXX-XXXXX-YYYYY-ZZ; X digit, Y letter, ZZ check digits | format from official guides [S19]; real examples: AE:PL-86009-60876-AHEER-26 and AE:PL-31301-35062-RUIJT-31 (local-government pages, [S20]) and AE:PL-40883-64824-AJHIG-16 (municipality). The ZZ algorithm is NOT published in what I could open. I ran about 20,000 variants (mod 89-102, letter maps A=10/A=1/A=0, with and without "AE", "PL", "00", "2521", digits-then-letters or letters-then-digits, direct and "98 minus" forms) on three real addresses: no hit. Regex only: `^AE:PL-\d{5}-\d{5}-[A-Z]{5}-\d{2}$` | format high, checksum unknown |
| ePUAP box address | path form such as /identifier/box_name (for example /ministerstwo/skrytka) | not opened: unverified. Note: from 1 Jan 2026 e-Delivery replaced ePUAP mail, per a government page found by search (medium, [S20]) | low |

### 4.2 Why this matters for the JSON

In both reference exports `validation` is an empty list on every text field and no field has REQUIRED (forensics file, "validators used: {}"). The standard therefore has the slot, but the reference forms do not use it. Our converter can add validators by wording ("PESEL", "NIP", "kod pocztowy") only if the partner's import accepts them: that is question T4/T12 (partner only).

### 4.3 People without PESEL

- The CEIDG act itself models this: PESEL "if the person has one", and the date of birth "if the person has no PESEL"; plus citizenship and NIP if any (art. 5 par. 1 pkt 1-5) [S6]. The same pattern holds for a pelnomocnik or prokurent in the CEIDG entry (PESEL; date of birth if neither PESEL nor NIP) [S6].
- PESEL is assigned automatically to foreigners with permanent residence, long-term EU residence, refugee or similar status and Ukrainian-war status UKR; others may apply, and the number is free [S10][S21 secondary].
- A foreigner at an office therefore normally gives: first and last names, date of birth, citizenship, type and number of an identity document (passport or residence card) and country of issue (secondary [S21]; inference for the "type" field).
- Design: one block "Identyfikator osoby" with a switch: PESEL | date of birth + document kind + document number + country (dictionary "kind of identity document", section 10).

### 4.4 Address kinds

- Residence: "miejsce zamieszkania" is the place where the person stays with the intent of permanent stay (Civil Code art. 25) [S5]; in population records, permanent stay is residence with intent to stay permanently, temporary stay is any other (Population Records Act art. 25) [S22].
- Address content in the registers: for towns the town name (district), street, house and flat number, voivodeship and postal code; for other communes the locality, street if any, numbers, commune, voivodeship and postal code; and the TERYT identifiers are added in the PESEL register (art. 26) [S22].
- Registered seat of a legal person: the place of its governing body unless statute says otherwise (Civil Code art. 41) [S5].
- Sole trader: CEIDG stores the "adres do doreczen" and, if there is one, the address of the permanent place of business; both follow TERYT codes (art. 5 par. 1 pkt 6) [S6]. This is a third kind, not residence.
- Correspondence address and e-Delivery address are separate fields in the registers [S6][S8].
- Reference forms: own address block (postal code, street, voivodeship, building, flat, country) and a seat block for legal persons (section 8).

## 5. Applicant block in the references, branch by branch

(measured by me from the first reference JSON `konfiguracja_form_wniosekOUstalenieNumeruPorzadkowegoNieruchomosci`, and from the forensics file for the second export [R1][R2])

Question 1, `wybierz_w_czyim_imieniu_wnioskujesz`: options Swoim / Innej osoby / Osoby prawnej lub jednostki organizacyjnej.
Question 2, `wybierz_jako_kto_wnioskujesz`: options Pelnomocnik / Reprezentant. Visible only when Question 1 = legal person or unit.

| Section | Shown when |
|---|---|
| Twoje dane (surname, name; second export also PESEL; all from the register, read-only) | always |
| Adres zamieszkania (postal code, street, voivodeship dictionary, building, flat, country; foreign variant: street, locality, postal code) | always; Polish or foreign variant by country |
| Dane podmiotu (name, NIP, REGON, KRS in export 1; name, NIP in export 2) | legal person |
| Adres siedziby | legal person |
| Potwierdzenie, ze jestes reprezentantem (upload "Plik z odpisem danych") | legal person and Reprezentant |
| Dane innej osoby (surname, name) and Adres zamieszkania innej osoby | Innej osoby |
| Pelnomocnictwo (upload; export 1 requires an electronically signed document) | Innej osoby, or legal person and Pelnomocnik |
| Oplata skarbowa 1 (radio "wymaga oplaty?", text 17 zl and payment instruction, upload of transfer confirmation) | Innej osoby |
| Oplata skarbowa 2 (text 17 zl, payment instruction, upload) | legal person and Pelnomocnik |

The conditions are JSONata-like expressions over `__userAnswer`, for example `"Innej osoby" in ...['wybierz_w_czyim_imieniu_wnioskujesz'...].field.__userAnswer`; the pelnomocnictwo section uses `A or (B and C)`.

## 6. e-Delivery obligation calendar and what it implies for forms

Law: Act of 18 Nov 2020 on electronic delivery, consolidated text Dz.U. 2026 poz. 3 (announced 29 Dec 2025) [S8]. Opened on 2026-11-21.

| Date | What | Source |
|---|---|---|
| 5 Oct 2021 | Act in force (art. 166) | [S8] |
| 1 Jan 2025 | Public bodies deliver via e-Delivery (art. 155 par. 9, date also quoted by the ministry page of 1 Jul 2025); new CEIDG entries must supply data for an address (art. 152 par. 1) | [S8][S23] |
| about 1 Apr 2025 | KRS-registered non-public entities must have an address within 3 months of the date in the ministerial communique (art. 151 par. 1); secondary sources give 1 April 2025 | [S8], date medium |
| 1 Jul 2025 to 30 Sep 2026 | A CEIDG entrepreneur without an address who files a change must supply address data or ask for one (art. 152 par. 2) | [S8] |
| 30 Sep 2026 | Every other CEIDG entrepreneur must have an ADE entered in the address base (art. 152 par. 3). From 1 Oct 2026 it is an obligation for all JDG; the deadline has passed today | [S8] |
| 1 Jan 2026 | e-Delivery replaces ePUAP-based correspondence at offices (government pages found by search) | [S20], medium |
| 31 Dec 2026 | ABW, Intelligence Agency, military counter-intelligence, CBA and the defence ministry (art. 155 par. 5a) | [S8] |
| 1 Oct 2029 | Hybrid service obligation for local-government units (art. 155 par. 6), and for courts, prosecutors, bailiffs, police, prison service (art. 155 par. 7); art. 160 lapses on 30 Sep 2029 (art. 165) | [S8] |

I found nothing in the act dated 2027 or 2028 for entrepreneurs. The summary requested ("2025 to 2029") is therefore: 2025 start for public bodies and KRS entities, 2026 completion for CEIDG, end 2026 special services, end of 2029 hybrid service for local government and courts. Note: PKD 2025 reclassification in registers is a separate date, 1 Jan 2027 (section 10).

Who must hold an address (art. 9): advocates, legal advisers, tax advisers, restructuring advisers, patent attorneys, notaries (practising), non-public entities in the KRS register of entrepreneurs, non-public entities in CEIDG. Other non-public entities, including ordinary natural persons, "may" hold one (art. 10) [S8]. Public entities must (art. 8) [S8].

Implications for contact sections:
1. Applicant kind decides whether an ADE is mandatory (JDG, KRS company, lawyer: yes; private person: optional; office: yes).
2. Add a field "Adres do doreczen elektronicznych" next to phone and e-mail, validated by the ADE format; prefill from CEIDG/KRS/BAE when a source exists.
3. KPA art. 63 par. 1: an electronic application is lodged to the office's e-Delivery address or via its IT account; an ordinary e-mail to the office is left without consideration unless other law says otherwise [S2]. The form's e-mail is for notices, not for lodging.
4. KPA art. 63 par. 3a: an electronic application contains the data in the format of the prescribed form, where the law prescribes a form [S2]. This is the legal anchor of the whole task.
5. Public lookup: the Electronic Address Database (BAE) is searched by the SE API; versions 2-4 live in 2025, version 4 for non-public entities, up to 1000 addresses per query; integrators must register the system with the ministry [S24]. Search keys not stated on the page: unverified.

## 7. Registers as future initial data (PROPOSAL)

The product calls nothing external. The idea: the JSON may name an initial-data source using the partner's own `SOURCE.attribute` notation (as in `MLPZ.surname`, `PESEL.pesel`), and the partner's platform (which already resolves `EXTERNAL_SYSTEM` defaults) fills it. We only need to emit the names, document them, and ship a local fixture file that shows the shape for the demo.

| Register | Access and terms (as found) | Attributes I would propose, with legal anchor | Source |
|---|---|---|---|
| CEIDG (Hurtownia Danych API) | free information; requires a biznes.gov.pl account and permission; documentation in Akademia; version 3 API field names not seen: unverified | `CEIDG.firstName`, `CEIDG.lastName`, `CEIDG.firmName`, `CEIDG.nip`, `CEIDG.regon`, `CEIDG.pesel` (only if public: unverified), `CEIDG.citizenship`, `CEIDG.deliveryAddress.*`, `CEIDG.businessAddress.*`, `CEIDG.eDeliveryAddress`, `CEIDG.status`, `CEIDG.pkd[]`. Legal list of data: art. 5 CEIDG act [S6] | [S6] [S25] |
| KRS Open API | third-party sources say keyless, by KRS number, endpoints OdpisAktualny and OdpisPelny, register P (entrepreneurs) or S (associations): secondary. My live check of the host on 2026-11-21 returned a "technical break" page: unverified, and a reason to cache | `KRS.name`, `KRS.krs`, `KRS.nip`, `KRS.regon`, `KRS.legalForm`, `KRS.seat.*`, `KRS.representation[]` (name, function), `KRS.eDeliveryAddress` (art. 151 par. 2 e-Delivery act moves ADE data from BAE to KRS [S8]) | [S26 secondary] |
| REGON / BIR (GUS) | free; production key by e-mail to GUS with a description and the IP addresses; for public administration agreed individually; test environment and BIR 1.1 manual in zip files [S27]; search by REGON, NIP or KRS | `REGON.name`, `REGON.regon9`, `REGON.regon14`, `REGON.legalForm` (the GUS "forma prawna" code), `REGON.pkd`, `REGON.address.teryt.*` (TERYT codes: unverified in BIR responses) | [S27] |
| VAT white list (MF) | search: 100 queries/day, up to 30 entities; check: up to 5,000; WL2 (VAT status): 50,000/day; test environment exists; base URL from 15 Oct 2026 `wykazpodatnikowvat.mf.gov.pl/api`, legacy `wl-api.mf.gov.pl` supported until 1 Dec 2026; daily flat file with hashed NIP-account pairs; spec v1.6.2 of 5 Nov 2026 [S28] | `WL.name`, `WL.nip`, `WL.vatStatus`, `WL.accountNumbers[]` (NRB), `WL.workingAddress`, `WL.residenceAddress`: attribute list not on the page, taken from the spec title: unverified | [S28] |
| e-Delivery address base (BAE) via SE API | needs a system integrated with the national e-Delivery components and registered with the ministry [S24]; free-form web search by humans | `BAE.eDeliveryAddress`, `BAE.holderType`, `BAE.validFrom` (names are mine; unverified) | [S24] |
| Population registers (already partner-side) | `PESEL.*`, `MLPZ.*` seen in the references | for "another person": `PESEL.*` lookup by number | [R1][R2] |

Design advice (inference): ship the sources as a small declarative catalogue `sources.json` {name, kind (person/entity), attributes with type and validator, mandatory-for-kind flags}. The converter picks `CEIDG.nip` instead of a free "NIP" text field when the paper says "NIP" and the applicant is an entrepreneur, marks it readOnly, and leaves an override for the unit's own data. Offline friendly: the white-list flat file and the TERYT/NBP files can be downloaded by the operator and loaded as dictionaries without any call at run time.

## 8. Reference exports: what is missing or inconsistent (legal view)

Measured facts [R1][R2]; legal reasoning is mine (inference unless a source is given).

1. Three options, but the law has more. The first question says "swoim / innej osoby / osoby prawnej lub jednostki organizacyjnej". There is no statutory representative or guardian, no "organ of a legal person acting for the entity" apart from the Reprezentant radio, no JDG, no civil partnership, no housing community. KPA art. 30 par. 2-3 and art. 34 describe those parties [S2].
2. "Innej osoby" assumes a pelnomocnik. The section is named "Adres zamieszkania osoby, ktorej jestes pelnomocnikiem" and asks for a power of attorney and its fee. A parent or guardian of a child is not a pelnomocnik: no power-of-attorney document, no fee, and the proof is another document.
3. No PESEL, no date of birth for "another person". Only surname, name and address. A tax form (the second export) needs the taxpayer identity; documents in tax matters carry NIP or PESEL (NIP page, [S11]). Without PESEL a person cannot be told from another of the same name; for foreigners the date of birth and document would be the substitute (section 4.3).
4. REGON and KRS in one export, only NIP in the other. Export 1 "Dane podmiotu": name, NIP, REGON, KRS. Export 2: name, NIP only. The field set is not a standard: it follows the author's choice. Legally, KRS applies only to KRS-registered entities, not to a JDG, a housing community or a local-government unit; REGON applies to nearly all; NIP to nearly all. All four fields have no validator and no REQUIRED, so a person can submit an empty entity.
5. Sole trader not distinguished. A JDG acting "swoim" has no NIP, REGON or ADE field and no marker that this is a business matter; a JDG acting through the entity branch would need to choose "osoby prawnej lub jednostki organizacyjnej", which it is not. Law: Civil Code art. 43(1), CEIDG art. 5 [S5][S6].
6. The Reprezentant proves their role by uploading an extract. KPA art. 220 par. 1 pkt 2 bars an office from demanding statements on facts it can establish from public registers; a KRS or CEIDG lookup could replace the upload for registered entities (inference, B11).
7. The "Reprezentant" does not state the capacity (board member, president, liquidator, partner, prokurent, parent). Needed for checking the right to represent.
8. No e-Delivery address, no correspondence address; contact block has phone and e-mail only. Conflicts with the 2025-2026 obligations and KPA art. 63 par. 1 (sections 6, 4.4).
9. Polish branch of the residence address has postal code, street, voivodeship (dictionary), building and flat, but no locality or commune field, which the Population Records Act lists as address elements (art. 26). The foreign branch has a locality field. Possibly the multi-level dictionary (`multiLevelTree: true` on the first export's voivodeship select) delivers the locality; the exports do not show it: unverified, ask the partner.
10. Dictionary names are inconsistent between exports for the same logical field. Voivodeship of own address: export 1 `TERYT_DOWODOWY`, export 2 `TERYT_4G_DOWODOWY`. Voivodeship of "another person": export 1 `TERYT_4G_DOWODOWY`, export 2 `TERYT_DOWODOWY`. In export 1 the title of the own voivodeship select is the dictionary name "TERYT_DOWODOWY", not a human label. Inference: hand-made and drifting; the converter should default one dictionary per role (partner to confirm which, B15/T5).
11. The fee text is correct but not complete. The text "17 zl, pay to the office of the principal's residence, abroad to Warsaw" matches art. 12 [S1]; the exemptions (spouse, ascendant, descendant, sibling, art. 7 entities, general power of attorney, matters under art. 2) are missing, and the legal-person pelnomocnik branch cannot say "no fee".
12. Wording in export 1: the second fee section title contains a typo ("pelnomonictwo"); the section titles contain the form-specific word "pelnomocnik" in a technical id. Cosmetic.
13. Pelnomocnictwo upload text: export 1 "Dokument z potwierdzeniem, podpisany elektronicznie", export 2 "Plik dokumentu z pelnomocnictwem": the same field with different labels; same logic as in the refs (forensics).
14. Consent: one CONSENT_SECTION with the data-protection clause in both exports (so it is a standard block too).

## 9. Decision table: wording on paper to applicant options, sections, validators, attachments, fees

Wording examples marked (repo) occur in the sample forms of `data/coi/` read today. Others are common administrative wording (inference).

| Wording on paper | Applicant options to offer | Sections | Validators | Attachments | Fee |
|---|---|---|---|---|---|
| "Imie i nazwisko, adres, PESEL, nr telefonu" (repo: zaswiadczenie) | natural person, own name | Twoje dane, Adres zamieszkania, Kontakt | PESEL, postal code, phone | none | only the matter's fee (17 zl for most certificates, repo text) |
| "Imie i nazwisko lub nazwa firmy"; "Adres zamieszkania/siedziby" (repo: pas drogowy) | natural person; JDG; legal person or unit | kind switch, then person block or entity block (name, NIP, REGON, KRS if register), address by kind | PESEL or NIP; REGON-9; KRS 10 digits; postal code | none by default | matter's fee |
| "w imieniu", "pelnomocnik", "upowazniony" | pelnomocnik of a person; pelnomocnik of an entity | Dane pelnomocnika; Dane mocodawcy (with PESEL or date of birth); Pelnomocnictwo | PESEL/NIP; document id if any | the power of attorney file (art. 33 par. 3); exempt only in minor matters for close family (art. 33 par. 4) | 17 zl unless one of the 8 exemptions; payer and organ by art. 5, 12 |
| "przedstawiciel ustawowy", "rodzic", "opiekun", "kurator", "dziecko niepelnoletnie" | statutory representative | Dane przedstawiciela; Dane osoby reprezentowanej (PESEL, date of birth); relation | PESEL | birth certificate or court decision | no power-of-attorney fee (inference); some matters exempt entirely (art. 2) |
| "reprezentant", "osoba uprawniona do reprezentacji", "zarzad", "prezes", "kierownik jednostki" | organ of an entity | Dane podmiotu, Adres siedziby, Dane reprezentanta with function | NIP, REGON, KRS | extract from KRS or other register (or lookup) | none for the organ itself |
| "prokurent" | prokurent | as pelnomocnik, with the KRS/CEIDG entry | PESEL/NIP | prokura document unless in KRS/CEIDG | 17 zl per relation (secondary: register entry can be cited: unverified) |
| "wspolnicy spolki cywilnej" | partners of a civil partnership | repeating section "wspolnik"; partnership NIP and REGON | PESEL/NIP per partner | partnership agreement if asked | matter's fee; each partner liable jointly (art. 5 par. 2 as for joint filings) |
| "wspolnota mieszkaniowa", "zarzad wspolnoty", "zarzadca" | housing community | entity block without KRS; board member or administrator as representative | NIP, REGON | resolution on board, administrator contract | matter's fee; exempt if no rule: none (inference) |
| "klub sportowy", "stowarzyszenie", "fundacja"; "dane reprezentanta z KRS lub innego wlasciwego rejestru" (repo: stypendium sportowe) | legal person or unit, with a register choice | entity block with register type (KRS or ewidencja), representative block | KRS 10 digits where chosen | register extract | exempt only for public-benefit organisations acting unpaid (art. 7 pkt 4) |
| "organ", "urzad", "jednostka budzetowa", "wojt", "dyrektor szkoly" | office or body as applicant | name, REGON, ADE, seat | REGON, ADE format | authorisation of the signer | exempt (art. 7: budget units, local-government units) |
| "cudzoziemiec", "nie posiada numeru PESEL", "data urodzenia", "obywatelstwo" | natural person without PESEL | date of birth, citizenship, identity document kind and number, country | document patterns by kind | copy or presentation of the document if the office asks | matter's fee |
| "oplata skarbowa", "17 zl", "dowod wplaty" | n/a | fee section | account NRB (organ) | transfer proof | text from art. 12 by principal's place; exemption list as help |
| "adres do doreczen elektronicznych", "e-Doreczenia", "skrzynka ePUAP" | by kind: mandatory for JDG, KRS entity, lawyer, office | contact block | ADE format | none | none |
| "numer ksiegi wieczystej", "dzialka ewidencyjna nr", "obreb" | n/a | property block | KW structure; parcel id WWPPGG_R.XXXX.NDZ | extract from KW or map if asked | none |
| "numer konta", "rachunek bankowy" | n/a | payment block | NRB 26 digits mod 97; settlement number mod 10 | none | none |

Rule of thumb for the converter: first detect entity-type cues (words in the table above), then derive the three standard questions, then attach sections. When no cue appears, offer the partner's three options unchanged, since both references use them.

## 10. Proposals of new dictionaries

Structure for every dictionary: `{"name","version","source","validFrom","entries":[{"id","label", ...extra}]}`, one file each; shipped from a local file; the JSON of the form only names it in `dictionaryName`. (Where the partner expects dictionaries: T5, B16.)

| Dictionary (name) | Entry structure | Source of entries | Where used |
|---|---|---|---|
| RODZAJ_DOKUMENTU_TOZSAMOSCI | id, label, regex, hasCheckDigit, country scope | Identity Cards Act, passports, aliens law; patterns from section 4 | identity block for persons without PESEL; "inna osoba" |
| FORMA_PRAWNA_GUS | code (3 digits), label, isLegalPerson, hasKRS, registerKind | REGON legal-form classification (Council of Ministers regulation of 30 Nov 2015 as cited by GUS glossary [S29]; the list itself: unverified) | entity switch; chooses KRS/CEIDG/none |
| RODZAJ_ULICY_TERYT | id, abbreviation (ul., al., pl., os., rondo, skwer, bulwar), label | TERYT ULIC "cecha" values (not opened: unverified) | address blocks; join with the street name |
| URZEDY_I_ORGANY | id, name, kind (gmina, starostwo, urzad marszalkowski, US, ...), REGON, TERYT of seat, ADE | BAE public-entity records, BIP, TERYT; ADE addresses are published (for example on gov.pl pages of offices) | "Organ, do ktorego sklada sie wniosek"; applicant-is-office; payment organ |
| RODZAJ_PELNOMOCNICTWA | id (general, special, per category, prokura, for receipt of documents, tax general, ID special), label, feeRuleId | Civil Code, Tax Ordinance, Identity Cards Act, Stamp Duty Act annex IV [S1] | pelnomocnictwo section; fee branch |
| STOPIEN_POKREWIENSTWA | id (spouse, ascendant, descendant, sibling, in-law, other), label, feeExempt (spouse, ascendant, descendant, sibling), kpa33_4 | Family Code art. 617-618 [S30]; Stamp Duty annex IV pkt 3 [S1]; KPA art. 33 par. 4 [S2] | "is the pelnomocnik a relative?" gate that removes the fee |
| BANKI_NBP | settlement number (8 digits), provider name, provider id | NBP list of active settlement numbers on ewib.nbp.pl (a third-party site quotes 3147 numbers and 582 providers on 23 Oct 2026: unverified); rule [S16] | payment/refund block; NRB check |
| PKD_2025 | code, label, section, parent, validFrom | Council of Ministers regulation 18 Dec 2024, Dz.U. 2024 poz. 1936 (in force) [S31]; self-reclassification until 31 Dec 2026 and automatic reclassification in registers from 1 Jan 2027 (secondary [S32]) | activity block of business matters |
| KRAJE_ISO3166 | alpha-2, alpha-3, numeric, Polish label, euMember | ISO 3166-1 plus Polish names; reconcile with the partner's "Kraje" dictionary, which stores the name itself as value (default `["Polska"]` in the references) [R1] | addresses; citizenship; foreign pelnomocnik fee branch |
| WALUTY_ISO4217 | code, numeric, label | ISO 4217, plus NBP tables for exchange rates | amounts in refunds, subsidies |

Also worth adding: WOJEWODZTWA (TERC level 1) as the stable base of `TERYT_DOWODOWY`, and RODZAJ_JEDNOSTKI_ORGANIZACYJNEJ (public benefit organisation, housing community, civil partnership, sports club) to drive the entity switch.

## 11. What I did and did not do

- Read: task card and docs listed by the brief (questions-v1, forensics, reference JSON), the sample forms `judged-03`, `-04`, `-06`, `-09` (first lines).
- Primary legal texts read as PDFs from the Sejm ELI API: KPA, Stamp Duty Act, e-Delivery Act, Civil Code, Family Code, Population Records Act, CEIDG Act, ownership of premises act (art. 6 only), regulation on land register and EGiB, regulation on bank identifiers.
- Not read in full: Tax Ordinance (power of attorney articles), the KRS Act, the Act on ID cards, the e-Delivery technical specifications.
- KPA amendments after the 7 Nov 2025 consolidated text: not individually verified (a June 2026 simplification act exists, Dz.U. 2026 poz. 875, per the stamp-duty announcement [S1]).
- The partner's two reference forms were not modified. Nothing outside the output file was edited.
- Injection note: no instruction aimed at me was found in any page or file I opened.

## 12. Sources (all opened 2026-11-21)

| Id | Source |
|---|---|
| S1 | Stamp Duty Act, consolidated text Dz.U. 2026 poz. 1395 (legal state 1 Oct 2026): https://api.sejm.gov.pl/eli/acts/DU/2026/1395/text.pdf |
| S2 | KPA, consolidated text Dz.U. 2025 poz. 1691 (7 Nov 2025): https://api.sejm.gov.pl/eli/acts/DU/2025/1691/text.pdf |
| S4 | Regulation on land and building register, consolidated Dz.U. 2024 poz. 219, annex 5: https://api.sejm.gov.pl/eli/acts/DU/2024/219/text.pdf |
| S5 | Civil Code, consolidated Dz.U. 2026 poz. 795: https://api.sejm.gov.pl/eli/acts/DU/2026/795/text.pdf |
| S6 | CEIDG Act, consolidated Dz.U. 2026 poz. 30: https://api.sejm.gov.pl/eli/acts/DU/2026/30/text.pdf |
| S7 | Act on ownership of premises, Dz.U. 2026 poz. 232, art. 6: https://api.sejm.gov.pl/eli/acts/DU/2026/232/text.pdf |
| S8 | Act on electronic delivery, consolidated Dz.U. 2026 poz. 3: https://api.sejm.gov.pl/eli/acts/DU/2026/3/text.pdf |
| S9 | Public Procurement Office page on stamp duty for a power of attorney: https://www.gov.pl/web/uzp/oplata-skarbowa-od-pelnomocnictwa |
| S10 | PESEL (Polish Wikipedia): https://pl.wikipedia.org/wiki/PESEL |
| S11 | NIP (Polish Wikipedia): https://pl.wikipedia.org/wiki/Numer_identyfikacji_podatkowej |
| S12 | REGON (Polish Wikipedia): https://pl.wikipedia.org/wiki/REGON |
| S13 | Identity card in Poland (Polish Wikipedia): https://pl.wikipedia.org/wiki/Dowód_osobisty_w_Polsce |
| S14 | Regulation on land registers, consolidated Dz.U. 2024 poz. 1583: https://api.sejm.gov.pl/eli/acts/DU/2024/1583/text.pdf |
| S15 | Regulation on moving land-register content, Dz.U. 2016 poz. 463 par. 3: https://api.sejm.gov.pl/eli/acts/DU/2016/463/text.pdf |
| S16 | Regulation of the Minister of Finance, Dz.U. 2024 poz. 1142, annex 2 and par. 3, 7: https://api.sejm.gov.pl/eli/acts/DU/2024/1142/text.pdf |
| S17 | Bank identifiers, secondary (search result): https://bankoweabc.pl/numery-rozliczeniowe-bankow-w-polsce/ |
| S18 | Regulation on the register of localities, streets and addresses, Dz.U. 2021 poz. 1368 (search result only): https://eli.gov.pl/eli/DU/2021/1368/ogl/pol/pdf |
| S19 | e-Delivery address format, official guide: https://www.gov.pl/web/gov/uzyskaj-adres-do-e-doreczen-u-publicznego-dostawcy-uslugi-e-doreczen |
| S20 | Example ADE on local-government pages: https://samorzad.gov.pl/web/gmina-smykow/e-doreczenia and https://samorzad.gov.pl/web/gmina-gielniow/e-doreczenia--nowy-standard-korespondencji-z-urzedem-od-1-stycznia-2026-r |
| S21 | Foreigners and PESEL, secondary: https://formularze.net/sprawy/cudzoziemcy-pesel ; https://www.gov.pl/web/gov/uzyskaj-numer-pesel--usluga-dla-cudzoziemcow-en |
| S22 | Population Records Act, consolidated Dz.U. 2026 poz. 384, art. 25-26: https://api.sejm.gov.pl/eli/acts/DU/2026/384/text.pdf |
| S23 | Ministry of Digital Affairs, page of 1 Jul 2025: https://www.gov.pl/web/cyfryzacja/kolejny-etap-wdrazania-e-doreczen--adres-potrzebny-przy-zmianach-w-ceidg |
| S24 | SE API (address search): https://www.gov.pl/web/e-doreczenia/interfejs-wyszukiwania-adresu-do-e-doreczen-search-engine-api-se-api--nowe-funkcje2 |
| S25 | CEIDG data warehouse page: https://akademia.biznes.gov.pl/hurtownia-danych/ |
| S26 | KRS open API, secondary: https://apify.com/bovi/poland-company-registry ; official host `api-krs.ms.gov.pl` returned a maintenance page |
| S27 | GUS REGON API page: https://api.stat.gov.pl/Home/RegonApi?lang=en |
| S28 | VAT white list API page: https://www.gov.pl/web/kas/api-wykazu-podatnikow-vat |
| S29 | GUS glossary, legal form (search result): https://stat.gov.pl/metainformacje/slownik-pojec/pojecia-stosowane-w-statystyce-publicznej/97,pojecie.html |
| S30 | Family Code, consolidated Dz.U. 2026 poz. 236, art. 617-618: https://api.sejm.gov.pl/eli/acts/DU/2026/236/text.pdf |
| S31 | PKD regulation, Dz.U. 2024 poz. 1936 (metadata only): https://api.sejm.gov.pl/eli/acts/DU/2024/1936 |
| S32 | PKD 2025 transition, secondary: https://www.zus.pl/en/-/pkd-2025-sprawd%C5%BA-czy-tw%C3%B3j-kod-jest-aktualny ; https://bip.stat.gov.pl/dzialalnosc-statystyki-publicznej/rejestr-regon/pkd-2025 |
| R1 | Reference JSON export 1: `data/coi/reference-01-numer-porzadkowy/konfiguracja_form_wniosekOUstalenieNumeruPorządkowegoNieruchomości (1).json` (this repo) |
| R2 | `docs/05-hackathon/mentor-questions/reference-json-forensics.txt` (this repo; second export `konfiguracja_form_wniosekOStwierdzenieNadpłatyPodatkuHacknation (2).json`) |

## Questions of questions-v1.md answered here

| id | our answer | confidence | evidence |
|---|---|---|---|
| T4 | Do not invent REQUIRED. Set it only where the paper marks a field mandatory (asterisk, "obowiazkowe"). The reference exports use no REQUIRED at all, but KPA art. 63 par. 2 makes identity, address and request mandatory content of an application, so identity and address fields are legally required | medium | R2 ("fields with REQUIRED: 0"); S2 art. 63 par. 2 |
| T5 | Partial. Two dictionary names are confirmed (Kraje, TERYT_DOWODOWY) and a third appears: TERYT_4G_DOWODOWY. Names drift between the two exports (section 8, item 10), so the full list can come only from the partner | high for the three names | R1, R2 |
| T7 | In the references the identity fields (surname, name, PESEL) are readOnly, while address and contact defaults from MLPZ are editable. Follow that pattern | high | R2: EXTERNAL_SYSTEM list with readOnly flags |
| B5 | Add standard sections only when the paper shows a cue for them (applicant wording, "w imieniu", fee for a power of attorney). Both references carry the block unchanged, so default it for forms with an applicant, but never invent it for forms that have no applicant data | medium | section 9; R1, R2 |
| B6 | The three variants follow from the law (own name, another person, entity), but "another person" must split into pelnomocnik vs statutory representative, and the entity branch into organ vs pelnomocnik; the partner's two references show exactly three, so offer three by default and extend by cue | medium | S2 art. 30, 32-34; R1 |
| B11 | Yes, valuable: CEIDG, KRS, REGON and the VAT white list are free or free to register, and KPA art. 220 par. 1 pkt 2 bars demanding proof of facts visible in public registers. The product should only name the sources | medium | section 7; S2 art. 220; S27; S28; S25 |
| B12 | A sole trader is a natural person (identified by PESEL, NIP optional) who also has an entrepreneur capacity. Model it as a kind inside "natural person" with NIP, REGON and an ADE obligation, not as a separate legal entity | high | S5 art. 43(1); S6 art. 5; S8 art. 9 |
| B13 | Only when the paper says so. The 17 zl is due for each power-of-attorney relation but has 8 exemptions (spouse, ascendant, descendant, sibling, art. 7 entities, general tax power of attorney and others), so a blanket "always attach and pay" is wrong | high | S1 annex IV |
| B14 | Cannot say what they miss, but all candidate validators except land register check digit and ADE check digit have public algorithms and are implemented here: PESEL, NIP, REGON, ID card, NRB, settlement number, parcel id, postal code, KRS format | high for the algorithms | section 4 |
| B15 | My ranking by legal weight: legal form, kind of power of attorney, degree of kinship, offices and bodies, identity document kind, street kind, banks, PKD, countries, currencies (section 10) | medium | section 10 |
| B16 | A separate file per dictionary with a version and source line, referenced by `dictionaryName`; embedding entries would bloat the form and detach them from the source | low (inference, depends on how the partner imports) | section 10 |
| T12 | Not answered by the references: no regex or file-limit keys appear in the field keys of either export | low | R2 (field key list) |

## Only the partner can answer

- What is behind `MLPZ.*` and `PESEL.*` (which service, which attributes exist, which are available for "another person"). Cannot be found outside: internal system names.
- Whether the generator accepts validator names such as PESEL, NIP, REGON, postal code in `validation`, and in which spelling. The references use an empty list; no public schema for it exists.
- The complete dictionary list and the meaning of `TERYT_DOWODOWY` versus `TERYT_4G_DOWODOWY` (levels, whether it contains locality and commune), and which is the standard for the voivodeship selects.
- Whether the applicant block is generated by the platform from a template (it looks identical in both references) or typed by hand; whether we may emit it, extend it (statutory representative, sole trader, ADE), or must reproduce it exactly.
- Whether the platform resolves `SOURCE.attribute` names beyond `MLPZ` and `PESEL`, and who registers new ones (needed for any CEIDG/KRS proposal).
- Policy on the fee exemptions: do they want the radio "wymaga oplaty?" kept, or a full branch with exemption selectors.
- The e-Delivery address check digits (algorithm) and a position on whether to validate more than the format. The ministry may publish it in the KSDE technical specification, which needs registration to read.
- Whether the land-register check digit rule they use matches the community formula in section 4.1 (the regulation does not print it).

## Proposals beyond what the partner asked

| proposal | why it matters to them | effort | libraries and licences | risk |
|---|---|---|---|---|
| Applicant-kind engine as a declarative rule file (wording cue to kind, sections, validators, attachments, fee rule), shipped next to the code and shown in the report | Specialists can read and amend the legal logic without code; reproducible on new forms at the defence | M | none beyond the standard library; YAML via PyYAML (MIT) or plain JSON | the cue lists need tuning on unseen wording |
| Offline validator pack with the exact algorithms and test vectors from section 4 (PESEL, NIP, REGON-9/14, ID card, NRB/IBAN, bank number, parcel id, ADE format) | Fixes the "no validators in the references" gap; zero network; trivial to audit | S | standard library only (or `python-stdnum`, LGPL-2.1+: avoid, we write our own) | ADE and KW checksums unverified, so format-only for those |
| Stamp-duty module: data table of amounts, exemptions and organ rule (art. 12), producing the payment text block correctly per case | Their fee text is right but omits exemptions; a corrected block shows legal depth | M | none | amounts change by new consolidated texts: store the table with a source and a date |
| Extra applicant paths proposed on top of the standard: statutory representative, JDG, civil partnership, housing community; with PESEL or date of birth plus document for persons without PESEL | Closes the legal gaps in section 8 without breaking the three-option core | M | none | the partner's importer may not accept new radio options: need an opt-in flag |
| Initial-data source catalogue `sources.json` (CEIDG, KRS, REGON, VAT white list, BAE) in `SOURCE.attribute` notation, plus fixtures | Shows the next step of the platform; keeps the product free of external calls | S | none (JSON only) | attribute names for CEIDG v3 and VAT white list are unverified: mark as proposal |
| Versioned dictionary files with provenance (legal form, kinship with exemption flag, kind of power of attorney with fee rule, banks, PKD 2025, countries, currencies) | Dictionaries are an explicit scoring extension (proposal of a new dictionary) and carry rules, not only labels | M | NBP and GUS files are public data; no code dependency | licensing of external list files: check terms before bundling (TERYT, PKD are public-sector data: unverified licence text) |
| e-Delivery contact block with obligation by applicant kind and a short note on KPA art. 63 | Visible alignment with the 2025-2026 law; few teams will include it | S | none | none |
| Consistency checker run on our own output against the legal gaps list (for example "entity branch without NIP", "pelnomocnik section without fee text") | Shows quality control that does not depend on any model; helps the report endpoint (B8) | S | none | false alarms if the form is not an applicant form |
