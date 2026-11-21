"""JWT verification with PyJWT, locked down. See the package docstring for the rules."""
from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import jwt

from app.config import ASYMMETRIC, Settings
from app.guard.problems import ProblemError

MAX_TOKEN_CHARS = 8192


def scopes_of(claims: dict[str, Any]) -> set[str]:
    """`scope` as a space-separated string (RFC 8693) or `scp` as a list."""
    out: set[str] = set()
    scope = claims.get("scope")
    if isinstance(scope, str):
        out |= set(scope.split())
    scp = claims.get("scp")
    if isinstance(scp, list):
        out |= {s for s in scp if isinstance(s, str)}
    return out


class TokenVerifier:
    """Built once at start; `verify` returns the claims or raises ProblemError(401)."""

    def __init__(self, settings: Settings) -> None:
        self.s = settings
        self._secret: bytes | None = None
        self._public: bytes | None = None
        self._jwks: list[dict] = []
        if settings.jwt_secret_file:
            self._secret = Path(settings.jwt_secret_file).read_bytes().strip()
            if len(self._secret) < 32:
                raise ValueError("the shared secret is shorter than 32 bytes")
        elif settings.jwt_public_key_file:
            self._public = Path(settings.jwt_public_key_file).read_bytes()
        elif settings.jwt_jwks_file:
            self._jwks = list(json.loads(Path(settings.jwt_jwks_file).read_text(encoding="utf-8")).get("keys", []))

    def _key_for(self, token: str) -> Any:
        if self._secret is not None:
            return self._secret
        if self._public is not None:
            return self._public
        kid = jwt.get_unverified_header(token).get("kid")
        hits = [k for k in self._jwks if kid is not None and k.get("kid") == kid]
        if not hits and kid is None and len(self._jwks) == 1:
            hits = self._jwks
        if len(hits) != 1:
            raise jwt.InvalidTokenError("no single key for kid")
        return jwt.PyJWK(hits[0]).key

    def verify(self, token: str | None) -> dict[str, Any]:
        if not token:
            raise ProblemError("TOKEN_MISSING", "Brak nagłówka Authorization: Bearer.")
        if len(token) > MAX_TOKEN_CHARS:
            raise ProblemError("TOKEN_INVALID")
        s = self.s
        try:
            header = jwt.get_unverified_header(token)
            # The token may only name the algorithm we already chose; anything else, `none` included, is refused
            # here and again by PyJWT through the `algorithms` list.
            if header.get("alg") != s.jwt_alg:
                raise jwt.InvalidAlgorithmError("algorithm differs from configuration")
            options: dict[str, Any] = {"require": list(s.jwt_required_claims), "verify_exp": True,
                                       "verify_signature": True}
            kwargs: dict[str, Any] = {}
            if s.jwt_issuer:
                kwargs["issuer"] = s.jwt_issuer
                options["require"] = sorted(set(options["require"]) | {"iss"})
            if s.jwt_audience:
                kwargs["audience"] = s.jwt_audience
                options["require"] = sorted(set(options["require"]) | {"aud"})
            else:
                options["verify_aud"] = False
            claims = jwt.decode(token, self._key_for(token), algorithms=[s.jwt_alg], leeway=s.jwt_leeway_s,
                                options=options, **kwargs)
        except jwt.ExpiredSignatureError as exc:
            raise ProblemError("TOKEN_EXPIRED") from exc
        except (jwt.PyJWTError, ValueError, TypeError, KeyError) as exc:
            raise ProblemError("TOKEN_INVALID") from exc
        return claims

    @staticmethod
    def asymmetric(alg: str) -> bool:
        return alg in ASYMMETRIC


class RateLimiter:
    """Sliding window per token subject, in memory. 429 BUSY with Retry-After when the minute is used up."""

    def __init__(self, per_minute: int, clock=time.monotonic) -> None:
        self.per_minute = per_minute
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, subject: str) -> None:
        now = self._clock()
        with self._lock:
            q = self._hits[subject]
            while q and now - q[0] >= 60:
                q.popleft()
            if len(q) >= self.per_minute:
                wait = max(1, int(60 - (now - q[0])) + 1)
                raise ProblemError("BUSY", "Przekroczono limit żądań na minutę.", headers={"Retry-After": str(wait)})
            q.append(now)
