"""Problem answers (RFC 9457, `application/problem+json`) with a Polish title and a stable code (design section 3)."""
from __future__ import annotations

PROBLEM_BASE = "https://formularze.flyreelstudio.eu/problems/"

# code -> (status, Polish title). The code is the contract; the title is for people.
CODES: dict[str, tuple[int, str]] = {
    "BAD_REQUEST": (400, "Nieprawidłowe żądanie"),
    "BAD_NAME": (400, "Nieprawidłowa nazwa pliku"),
    "TOKEN_MISSING": (401, "Brak tokenu dostępu"),
    "TOKEN_INVALID": (401, "Token dostępu jest nieprawidłowy"),
    "TOKEN_EXPIRED": (401, "Token dostępu wygasł"),
    "SCOPE": (403, "Token nie ma wymaganego zakresu"),
    "NOT_FOUND": (404, "Nie ma takiego adresu"),
    "METHOD_NOT_ALLOWED": (405, "Ta metoda nie jest obsługiwana pod tym adresem"),
    "TOO_LARGE": (413, "Plik jest za duży"),
    "TOO_MANY_PAGES": (413, "Dokument ma za dużo stron"),
    "TOO_MANY_PIXELS": (413, "Obraz ma za dużo pikseli"),
    "ARCHIVE_LIMIT": (413, "Archiwum przekracza dopuszczalne limity"),
    "EXTENSION": (415, "Nieobsługiwane rozszerzenie pliku"),
    "TYPE_MISMATCH": (415, "Zawartość pliku nie zgadza się z rozszerzeniem"),
    "DOC_READER_OFF": (415, "Czytnik plików DOC jest wyłączony"),
    "UNREADABLE": (422, "Nie udało się odczytać pliku"),
    "NOT_A_FORM": (422, "Nie znaleziono miejsc do wypełnienia"),
    "ACTIVE_CONTENT": (422, "Plik zawiera makra lub treść aktywną"),
    "BUSY": (429, "Usługa jest zajęta, spróbuj za chwilę"),
    "GATE_FAILED": (500, "Wynik nie przeszedł kontroli wewnętrznej"),
    "TIMEOUT": (504, "Przekroczono czas przetwarzania"),
}


class ProblemError(Exception):
    """Raised anywhere in the shell; the app turns it into a problem answer. The detail never holds file content."""

    def __init__(self, code: str, detail: str = "", *, limits: dict | None = None,
                 headers: dict[str, str] | None = None) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status, self.title = CODES[code]
        self.detail = detail
        self.limits = limits
        self.headers = headers or {}

    def body(self) -> dict:
        out: dict = {
            "type": PROBLEM_BASE + self.code.lower().replace("_", "-"),
            "title": self.title,
            "status": self.status,
            "code": self.code,
        }
        if self.detail:
            out["detail"] = self.detail
        if self.limits:
            out["limits"] = self.limits
        return out
