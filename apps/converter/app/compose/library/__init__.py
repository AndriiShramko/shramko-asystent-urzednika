"""Library of the partner's standard sections, cut from their two reference exports (design 6.5.1).

One builder per section. Wording, techNames, suffixes (`_siedziba`, `_inna_osoba`, `_zagranica`, D7), dictionaries,
initial data (D6) and conditions are those of the exports. Where the two exports differ the builder takes a
parameter; `Standard` holds them, `EXPORT_1` and `EXPORT_5` are the values measured on each export
(contracts/coi/standard-sections-diff.md). Markup is ours (D11): the exports' spans, styles and inline images are
not copied, the visible text is.

Deliberate departures from both exports, each checked by the comparison test as a named tolerance:
- the title "Opłata skarbowa za pełnomonictwo" is written "... pełnomocnictwo" (a typing slip in both exports);
- `searchEnabled` and `multiLevelTree` of the country and territorial selects are written one way everywhere
  (the exports set them on some addresses only);
- `defaultValue: ""` of `ulica_siedziba` is not written.

Extensions behind switches (P18 "wolno rozszerzać"): the statutory representative (D16), the reason of exemption
from stamp duty (D17). With both off, the sections are the exports' sections.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..html import doc, link, p, strong
from ..query import Is, Not, Pred, all_of, any_of
from ..spec import Comp, Sec

KRAJE, TERYT, TERYT_4G = "Kraje", "TERYT_DOWODOWY", "TERYT_4G_DOWODOWY"
EXTERNAL = "EXTERNAL_SYSTEM"

SELF, OTHER, ENTITY = "Swoim", "Innej osoby", "Osoby prawnej lub jednostki organizacyjnej"
POA, REPRESENTATIVE, STATUTORY = "Pełnomocnik", "Reprezentant", "Przedstawiciel ustawowy"
YES, NO = "Tak", "Nie"

R_PARTY, R_CAPACITY, R_CAPACITY_OTHER, R_FEE = "std:w_czyim_imieniu", "std:jako_kto", "std:jako_kto_inna_osoba", "std:czy_oplata"

FINISH_SEND = "Zanim wyślesz wniosek, sprawdź uzupełnione dane na podglądzie. Jeśli zobaczysz błędy, wróć do edycji."
FINISH_SIGN = "Zanim przejdziesz do wyboru sposobu podpisu, sprawdź dane na podglądzie. Jeśli zobaczysz błędy, wróć do edycji."

URL_FEE_FAMILY = "https://www.biznes.gov.pl/pl/portal/0089#8"
URL_FEE_ENTITY = "https://www.biznes.gov.pl/pl/portal/0089#9"
URL_FEE_ABROAD = "https://warszawa19115.pl/-/oplata-skarbowa"


@dataclass(frozen=True)
class Standard:
    """Where the two exports differ. The defaults are our choice; the brief switches the first four."""

    identity_source: str = "MLPZ"            # export 1: MLPZ; export 5: PESEL (with the PESEL number shown)
    pesel: bool = False                      # "Numer PESEL" in "Twoje dane": when the paper asks for PESEL
    entity_regon: bool = False               # export 1 has REGON and KRS in "Dane podmiotu": when the paper names them
    entity_krs: bool = False
    other_pesel: bool = False                # ours: PESEL of the other person, typed, when the paper asks for it
    teryt_self: str = TERYT_4G               # the exports disagree (design 6.6): four of six uses are TERYT_4G
    teryt_entity: str = TERYT_4G
    teryt_other: str = TERYT_4G
    upload_wording: str = "file"             # "file": export 5 ("Plik z ..."); "document": export 1
    contact_page_title: str = "Kontakt i zgody"                    # export 5; export 1: "Kontakt z urzędem"
    consent_section: tuple[str, str] = ("zgoda_wyrazenie", "Zgoda")  # export 5; export 1: zgoda_sekcja / Zgoda_sekcja
    finish_text: str = FINISH_SIGN           # export 5; export 1: FINISH_SEND
    transfer_title: str | None = None        # None: the title of the form (export 5); export 1 names another form


EXPORT_1 = Standard(entity_regon=True, entity_krs=True, teryt_self=TERYT, upload_wording="document",
                    contact_page_title="Kontakt z urzędem", consent_section=("zgoda_sekcja", "Zgoda_sekcja"),
                    finish_text=FINISH_SEND, transfer_title="Wniosek o zwrot opłaty skarbowej")
EXPORT_5 = Standard(identity_source="PESEL", pesel=True, teryt_other=TERYT)


@dataclass(frozen=True)
class Who:
    """Which parties the form offers, and the conditions that follow (design 6.4.2). None means "always"."""

    self_: bool
    other: bool
    entity: bool
    statutory: bool = False                  # D16: the other person may be represented by a statutory representative

    @property
    def parties(self) -> tuple[str, ...]:
        return tuple(label for on, label in ((self.self_, SELF), (self.other, OTHER), (self.entity, ENTITY)) if on)

    @property
    def asks_party(self) -> bool:
        return len(self.parties) > 1

    def party(self, label: str) -> Pred | None:
        return Is(R_PARTY, label) if self.asks_party else None

    def entity_as(self, capacity: str) -> Pred | None:
        return all_of(self.party(ENTITY), Is(R_CAPACITY, capacity))

    def other_as(self, capacity: str) -> Pred | None:
        return all_of(self.party(OTHER), Is(R_CAPACITY_OTHER, capacity) if self.statutory else None)

    def power_of_attorney(self) -> Pred | None:
        branches = ([self.other_as(POA)] if self.other else []) + ([self.entity_as(POA)] if self.entity else [])
        return any_of(*branches)


# -- page "Dane" ---------------------------------------------------------------------------------------------

def addressee(kind: str, name: str | None) -> Sec:
    """Office or body the application goes to. Without a name the field stays empty and editable."""
    office = kind != "body"
    word, tech, label, field_tech = (("Urząd", "urzad_do_ktorego_jest_skladany_wniosek", "Nazwa urzędu", "nazwa_urzedu") if office
                                     else ("Organ", "organ_do_ktorego_jest_skladany_wniosek", "Nazwa organu", "nazwa_organu"))
    return Sec("dane/adresat", f"{word}, do którego jest składany wniosek", tech,
               [Comp("nazwa", "TEXT_FIELD", label, field_tech, read_only=name is not None, default=name)])


def party(who: Who) -> Sec | None:
    """"Podmiot wniosku": on whose behalf, and in which capacity. Left out when there is nothing to choose."""
    comps = []
    if who.asks_party:
        comps.append(Comp("w_czyim_imieniu", "RADIO", "Wybierz, w czyim imieniu wnioskujesz", "wybierz_w_czyim_imieniu_wnioskujesz",
                          options=who.parties, ref=R_PARTY, validation=("REQUIRED",)))
    if who.entity:
        comps.append(Comp("jako_kto", "RADIO", "Wybierz, jako kto wnioskujesz", "wybierz_jako_kto_wnioskujesz",
                          options=(POA, REPRESENTATIVE), show=who.party(ENTITY), ref=R_CAPACITY, validation=("REQUIRED",)))
    if who.other and who.statutory:
        comps.append(Comp("jako_kto_inna_osoba", "RADIO", "Wybierz, jako kto wnioskujesz w imieniu innej osoby",
                          "wybierz_jako_kto_wnioskujesz_inna_osoba", options=(POA, STATUTORY), show=who.party(OTHER),
                          ref=R_CAPACITY_OTHER, validation=("REQUIRED",)))
    return Sec("dane/podmiot_wniosku", "Podmiot wniosku", "podmiot_wniosku", comps) if comps else None


def your_data(source: str, pesel: bool) -> Sec:
    """The person at the keyboard: identity from the register, read-only (D6)."""
    comps = [Comp("imie", "TEXT_FIELD", "Imię", "imie", read_only=True, default=f"{source}.name", default_type=EXTERNAL, validation=("REQUIRED",)),
             Comp("nazwisko", "TEXT_FIELD", "Nazwisko", "nazwisko", read_only=True, default=f"{source}.surname", default_type=EXTERNAL, validation=("REQUIRED",))]
    if pesel:
        # D8: the field states PESEL, so it names the validator like every other PESEL of the form; the value comes
        # from the register and is read-only, the validator documents the kind of the value (VALIDATORS=off clears it).
        comps.append(Comp("numer_pesel", "TEXT_FIELD", "Numer PESEL", "numer_pesel", read_only=True, default="PESEL.pesel",
                          default_type=EXTERNAL, validation=("REQUIRED", "PESEL")))
    return Sec("dane/twoje_dane", "Twoje dane", "twoje_dane", comps)


_ADDRESS = {
    "self": ("dane/adres_zamieszkania", "adres_zamieszkania", "Adres zamieszkania", "", "std:kraj"),
    "entity": ("dane/adres_siedziby", "adres_siedziby", "Adres siedziby", "_siedziba", "std:kraj_siedziba"),
    "other": ("dane/adres_zamieszkania_innej_osoby", "adres_zamieszkania_osoby_ktorej_jestes_pelnomocnikiem",
              "Adres zamieszkania innej osoby", "_inna_osoba", "std:kraj_inna_osoba"),
}


def address(block: str, teryt: str, show: Pred | None = None) -> Sec:
    """Address with the Poland and abroad branches. Only the person at the keyboard gets initial data, editable (D6)."""
    role, tech, title, sfx, ref = _ADDRESS[block]
    poland, abroad = Is(ref, "Polska"), Not(Is(ref, "Polska"))

    def pre(attribute: str) -> dict:
        return {"default": f"MLPZ.{attribute}", "default_type": EXTERNAL} if block == "self" else {}

    return Sec(role, title, tech, [
        Comp("kraj", "SELECT", "Kraj", f"kraj{sfx}", dictionary=KRAJE, multi_level=False, search=True, default=["Polska"], ref=ref, validation=("REQUIRED",)),
        Comp("miejscowosc_zagranica", "TEXT_FIELD", "Miejscowość", f"miejscowosc{sfx}_zagranica", show=abroad, validation=("REQUIRED",)),
        Comp("kod_pocztowy_zagranica", "TEXT_FIELD", "Kod pocztowy", f"kod_pocztowy{sfx}_zagranica", show=abroad),
        Comp("ulica_zagranica", "TEXT_FIELD", "Ulica", f"ulica{sfx}_zagranica", show=abroad),
        # As in all six uses of the exports: the title of the territorial select is the name of its dictionary.
        Comp("wojewodztwo", "SELECT", teryt, f"wojewodztwo{sfx}", dictionary=teryt, multi_level=True, search=True, default=[], show=poland),
        Comp("kod_pocztowy", "TEXT_FIELD", "Kod pocztowy", f"kod_pocztowy{sfx}", show=poland, validation=("REQUIRED", "ZIP_CODE"), **pre("postCode")),
        Comp("ulica", "TEXT_FIELD", "Ulica", f"ulica{sfx}", show=poland, **pre("street")),
        Comp("numer_budynku", "TEXT_FIELD", "Numer budynku", f"numer_budynku{sfx}", validation=("REQUIRED",), **pre("building")),
        Comp("numer_lokalu", "TEXT_FIELD", "Numer lokalu", f"numer_lokalu{sfx}", **pre("apartment")),
    ], show=show)


def entity_data(regon: bool, krs: bool, show: Pred | None = None) -> Sec:
    comps = [Comp("nazwa", "TEXT_FIELD", "Nazwa", "nazwa", validation=("REQUIRED",)),
             Comp("nip", "TEXT_FIELD", "NIP", "nip", validation=("REQUIRED", "NIP"))]
    if regon:
        comps.append(Comp("regon", "TEXT_FIELD", "REGON", "regon", validation=("REGON",)))
    if krs:
        comps.append(Comp("numer_krs", "TEXT_FIELD", "Numer KRS", "numer_krs"))
    return Sec("dane/dane_podmiotu", "Dane podmiotu", "dane_podmiotu", comps, show=show)


def representative_proof(show: Pred | None = None) -> Sec:
    return Sec("dane/potwierdzenie_reprezentanta", "Potwierdzenie, że jesteś reprezentantem", "potwierdzenie_ze_jestes_reprezentantem",
               [Comp("plik", "FILE_UPLOADER", "Plik z odpisem danych", "plik_z_odpisem_danych")],
               html=doc(p("Dołącz aktualny odpis danych z Krajowego Rejestru Sądowego lub innego rejestru. Odpis powinien "
                          "potwierdzać, że jesteś reprezentantem podmiotu lub instytucji.")), show=show)


def other_person(pesel: bool, show: Pred | None = None) -> Sec:
    comps = [Comp("imie", "TEXT_FIELD", "Imię", "imie_inna_osoba", validation=("REQUIRED",)),
             Comp("nazwisko", "TEXT_FIELD", "Nazwisko", "nazwisko_inna_osoba", validation=("REQUIRED",))]
    if pesel:
        comps.append(Comp("numer_pesel", "TEXT_FIELD", "Numer PESEL", "numer_pesel_inna_osoba", validation=("REQUIRED", "PESEL")))
    return Sec("dane/dane_innej_osoby", "Dane innej osoby", "dane_innej_osoby", comps, show=show)


def statutory_proof(show: Pred | None = None) -> Sec:
    """D16: the statutory representative (parent, guardian, curator) proves the capacity with its own document.
    The stamp-duty sections are not shown on this path."""
    return Sec("dane/potwierdzenie_przedstawiciela_ustawowego", "Potwierdzenie, że jesteś przedstawicielem ustawowym",
               "potwierdzenie_ze_jestes_przedstawicielem_ustawowym",
               [Comp("plik", "FILE_UPLOADER", "Plik z dokumentem potwierdzającym", "plik_z_dokumentem_przedstawiciela_ustawowego")],
               html=doc(p("Dołącz dokument potwierdzający, że jesteś przedstawicielem ustawowym tej osoby: rodzicem, opiekunem "
                          "lub kuratorem. Może to być na przykład odpis aktu urodzenia dziecka albo postanowienie sądu.")), show=show)


def _upload(wording: str, what: str, sfx: str = "") -> tuple[str, str]:
    """(title, techName) of an upload, in the wording of export 5 ("file") or of export 1 ("document")."""
    table = {
        ("file", "power"): ("Plik dokumentu z pełnomocnictwem", "plik_dokumentu_z_pelnomocnictwem"),
        ("document", "power"): ("Dokument z potwierdzeniem, podpisany elektronicznie", "dokument_z_potwierdzeniem_podpisany_elektronicznie"),
        ("file", "transfer"): ("Plik z potwierdzeniem przelewu", "plik_z_potwierdzeniem_przelewu"),
        ("document", "transfer"): ("Potwierdzenie przelewu", "potwierdzenie_przelewu"),
    }
    title, tech = table[(wording, what)]
    return title, f"{tech}{sfx}"


def power_of_attorney(wording: str, show: Pred | None = None) -> Sec:
    title, tech = _upload(wording, "power")
    return Sec("dane/pelnomocnictwo", "Pełnomocnictwo", "pelnomocnictwo", [Comp("plik", "FILE_UPLOADER", title, tech)],
               html=doc(p("Dodaj dokument potwierdzający, że jesteś pełnomocnikiem.")), show=show)


def _fee_text(transfer_title: str, whose_address: str, more: bool) -> str:
    blocks = [
        p("Opłata skarbowa za pełnomocnictwo wynosi ", strong("17 zł"), "."),
        p(f"Przelej ją na konto urzędu miasta lub gminy właściwego dla adresu {whose_address} pełnomocnictwa. "
          "Jeśli adres nie jest w Polsce, opłatę przelej na konto ",
          link(URL_FEE_ABROAD, "Urzędu Miasta Stołecznego Warszawy – Centrum Obsługi Podatnika")),
        p(f"W tytule przelewu wpisz „{transfer_title} – opłata skarbowa za pełnomocnictwo”."),
    ]
    if more:
        blocks.append(p("Więcej informacji o opłacie skarbowej za pełnomocnictwo znajdziesz na stronie ", link(URL_FEE_ENTITY, "biznes.gov.pl")))
    return doc(*blocks)


def stamp_duty_person(transfer_title: str, wording: str, exemption: bool, show: Pred | None = None) -> Sec:
    """Stamp duty of a power of attorney given by a person: asked, because close family is exempt."""
    title, tech = _upload(wording, "transfer")
    due, free = Is(R_FEE, YES), Is(R_FEE, NO)
    comps = [Comp("czy_oplata", "RADIO", "Czy złożenie pełnomocnictwa wymaga opłaty skarbowej?",
                  "czy_zlozenie_pelnomocnictwa_wymaga_oplaty_skarbowej", options=(YES, NO), ref=R_FEE)]
    if exemption:  # D17, off by default: the reason of the exemption, in the four groups of the act
        comps.append(Comp("powod_zwolnienia", "RADIO", "Wybierz powód zwolnienia z opłaty skarbowej",
                          "wybierz_powod_zwolnienia_z_oplaty_skarbowej", show=free,
                          options=("Pełnomocnictwa udzielił małżonek", "Pełnomocnictwa udzielił rodzic, dziadek lub babcia",
                                   "Pełnomocnictwa udzieliło dziecko lub wnuk", "Pełnomocnictwa udzielił brat lub siostra", "Inny powód")))
    comps += [Comp("informacja", "TEXT_BLOCK", "", "oplata_info_1", show=due,
                   html=_fee_text(transfer_title, "zamieszkania osoby, która udzieliła", more=False)),
              Comp("potwierdzenie", "FILE_UPLOADER", title, tech, show=due)]
    return Sec("dane/oplata_skarbowa_osoba", "Opłata skarbowa", "oplata_skarbowa_pelnomocnictwo_1", comps, show=show,
               html=doc(p("Nie musisz płacić za złożenie pełnomocnictwa wystawionego przez najbliższą rodzinę: małżonka, dzieci, "
                          "rodziców, dziadków, wnuków, rodzeństwo. Więcej informacji na stronie ", link(URL_FEE_FAMILY, "biznes.gov.pl"))))


def stamp_duty_entity(transfer_title: str, wording: str, show: Pred | None = None) -> Sec:
    """Stamp duty of a power of attorney given by an entity: always due."""
    title, tech = _upload(wording, "transfer", "_2")
    return Sec("dane/oplata_skarbowa_podmiot", "Opłata skarbowa za pełnomocnictwo", "oplata_skarbowa_pelnomocnictwo_2", [
        Comp("informacja", "TEXT_BLOCK", "", "oplata_info", html=_fee_text(transfer_title, "siedziby podmiotu, który udzielił", more=True)),
        Comp("potwierdzenie", "FILE_UPLOADER", title, tech)], show=show)


# -- pages "Kontakt i zgody" and "Strona końcowa" ---------------------------------------------------------------

def contact() -> Sec:
    return Sec("kontakt/dane_do_kontaktu", "Dane do kontaktu", "dane_do_kontaktu", [
        Comp("numer_telefonu", "TEXT_FIELD", "Numer telefonu", "numer_telefonu", default="MLPZ.phoneNumber", default_type=EXTERNAL),
        Comp("adres_e_mail", "TEXT_FIELD", "Adres e-mail", "adres_e_mail", default="MLPZ.email", default_type=EXTERNAL, validation=("EMAIL",)),
    ], html=doc(p("Wpisanie danych do kontaktu może przyspieszyć załatwienie sprawy. Urzędnik będzie mógł skontaktować się z Tobą "
                  "w przypadku pytań lub wątpliwości."),
                p("Jeśli widzisz uzupełnione dane, sprawdź, czy są poprawne. Możesz je zmienić lub usunąć.")))


def consent(section: tuple[str, str], clause_url: str | None) -> Sec:
    """Consent to the processing of personal data, with a link to the clause when the brief knows an https address."""
    tech, title = section
    clause = link(clause_url, "klauzulą informacyjną") if clause_url else "klauzulą informacyjną"
    text = doc(p("Wyrażam zgodę na przetwarzanie moich danych osobowych zgodnie z ", clause))
    return Sec("kontakt/zgoda", title, tech, [Comp("zgoda", "CONSENT_SECTION", "", "zgoda", consents=((text, True),))])


def finish(text: str, style: str) -> Sec:
    """D5: a SECTION with one TEXT_BLOCK as in both exports; `info_section` is the reading of the rules document."""
    kind = "INFO_SECTION" if style == "info_section" else "TEXT_BLOCK"
    return Sec("koniec/podglad", "Podgląd uzupełnionego wniosku", "podglad_uzupelnionego_wniosku",
               [Comp("podglad", kind, "", "podglad_1", html=doc(p(text)))])
