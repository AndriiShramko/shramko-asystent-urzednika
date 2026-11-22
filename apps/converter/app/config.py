"""Configuration of the converter (design section 4).

Every value comes from the environment or from a file the environment names. The set is validated as a whole
when the service starts; an inconsistent set raises ConfigError listing every problem, and the process refuses
to start. Nothing secret is stored here: keys are read from files by the auth module.
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Mapping

SYMMETRIC = ("HS256", "HS384", "HS512")
ASYMMETRIC = ("RS256", "ES256", "EdDSA")
ALGORITHMS = SYMMETRIC + ASYMMETRIC
MAX_LEEWAY_S = 120
MIN_HMAC_SECRET_BYTES = 32
# Scan preparation steps of the image path (audit 8 SL1). A token joins SCAN_PREP_ACCEPTED (what SCAN_PREP=on turns
# on) only after the scan lab accepted it.
SCAN_PREP_TOKENS = frozenset({"glyph", "leader", "thick", "deskew", "scale", "rules", "orient"})
# lab 22.11 (image sl1:s5, 145 files): the six together with orient +13.0 points recall per file; orient alone +0.4
# ([-1.2, +2.5]), sideways pages not fixed, slower: left out
SCAN_PREP_ACCEPTED: frozenset[str] = frozenset({"scale", "glyph", "leader", "thick", "deskew", "rules"})


class ConfigError(Exception):
    """The set of settings is inconsistent. `problems` lists every one, so the operator fixes them in one go."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class Settings:
    max_upload_bytes: int = 20971520
    max_pages: int = 60
    max_cells: int = 200_000
    max_pixels: int = 80000000
    job_timeout_s: int = 600   # fits the page budget: 60 scanned pages at about 6 s each (review D19, B2)
    worker_memory_mb: int = 1024
    concurrency: int = 2
    rate_limit_per_min: int = 60
    auth_mode: str = "auto"   # auto: jwt when a key file is named, otherwise off (with a warning in the log)
    jwt_alg: str = "HS256"
    jwt_secret_file: str = ""
    jwt_public_key_file: str = ""
    jwt_jwks_file: str = ""
    jwt_issuer: str = ""
    jwt_audience: str = ""
    jwt_required_claims: tuple[str, ...] = ("exp",)
    jwt_leeway_s: int = 30
    finish_style: str = "export"
    validators: str = "on"
    # "paper": REQUIRED only where the paper or the standard says so (completeness decision R-1, the partner's exports
    # carry none); "inferred": also where our rule calls a field the substance of the request (design 6.4.3).
    required_policy: str = "paper"
    repeating_style: str = "native"
    statutory_representative: bool = True
    poa_exemption: bool = False
    ocr_min_chars: int = 20
    strict_extensions: bool = False
    doc_reader: str = "native"
    ocr_langs: str = "pol+eng"
    ocr_dpi: int = 300
    ocr_second_engine: str = "off"
    active_content: str = "warn"
    filled_form: str = "warn"
    form_key: str = ""
    id_namespace: str = ""
    sign_output: str = "off"
    signing_key_file: str = ""
    # The model step (WP-H4 names, WP-H1 behaviour). `auto`: the step runs when a model is configured and answers,
    # otherwise the rules; `off`: rules only. This build has no model step: the names are read and reported by
    # `app.engine`, nothing is called. The URL and the key file path are kept out of `repr`; the key itself is
    # never stored: `model_api_key_set` only says that the variable MODEL_API_KEY holds something.
    model_step: str = "auto"
    model_base_url: str = field(default="", repr=False)
    model_name: str = ""
    model_api_key_file: str = field(default="", repr=False)
    model_api_key_set: bool = False
    # scan preparation of the image path: "off" (the image path of before), "on" (= SCAN_PREP_ACCEPTED) or a comma
    # list of SCAN_PREP_TOKENS
    scan_prep: str = "off"
    ui_enabled: bool = True
    ui_dir: str = ""
    log_level: str = "info"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        """Build and validate settings from `env` (default: the process environment)."""
        env = os.environ if env is None else env
        problems: list[str] = []
        values: dict[str, object] = {}
        defaults = cls()

        choices = {
            "auth_mode": ("auto", "jwt", "off"),
            "jwt_alg": ALGORITHMS,
            "finish_style": ("export", "info_section"),
            "validators": ("on", "off"),
            "required_policy": ("paper", "inferred"),
            "repeating_style": ("native", "flat"),
            "doc_reader": ("native", "libreoffice", "off"),
            "ocr_second_engine": ("on", "off"),
            "active_content": ("warn", "strict"),
            "filled_form": ("warn", "reject"),
            "sign_output": ("off", "jws"),
            "model_step": ("auto", "off"),
            "log_level": ("debug", "info", "warning", "error"),
        }
        for f in fields(cls):
            if f.name == "model_api_key_set":   # presence of MODEL_API_KEY only: the value never enters the settings
                values[f.name] = bool((env.get("MODEL_API_KEY") or "").strip())
                continue
            name = f.name.upper()
            raw = env.get(name)
            default = getattr(defaults, f.name)
            if raw is None or raw.strip() == "":
                values[f.name] = default
                continue
            raw = raw.strip()
            if isinstance(default, bool):
                if raw.lower() not in ("true", "false"):
                    problems.append(f"{name} must be true or false")
                    continue
                values[f.name] = raw.lower() == "true"
            elif isinstance(default, int):
                try:
                    number = int(raw)
                except ValueError:
                    problems.append(f"{name} must be a whole number")
                    continue
                if number < 0 or (number == 0 and f.name != "jwt_leeway_s"):
                    problems.append(f"{name} must be positive")
                    continue
                values[f.name] = number
            elif isinstance(default, tuple):
                values[f.name] = tuple(p.strip() for p in raw.split(",") if p.strip())
            else:
                if f.name in choices and raw not in choices[f.name] and not (f.name == "jwt_alg" and raw.lower() == "none"):
                    problems.append(f"{name} must be one of {', '.join(choices[f.name])}")
                    continue
                if f.name == "jwt_alg" and raw.lower() == "none":
                    problems.append("JWT_ALG must not be none")
                    continue
                values[f.name] = raw

        s = cls(**{k: v for k, v in values.items() if v is not None})  # type: ignore[arg-type]
        problems += s._consistency()
        if problems:
            raise ConfigError(problems)
        return s

    def _consistency(self) -> list[str]:
        out: list[str] = []
        if self.jwt_leeway_s > MAX_LEEWAY_S:
            out.append(f"JWT_LEEWAY_S is at most {MAX_LEEWAY_S}")
        if "exp" not in self.jwt_required_claims:
            out.append("JWT_REQUIRED_CLAIMS must contain exp: it cannot be removed")
        if self.auth_enabled:   # explicit jwt with no key is refused here (fail closed); auto with no key is off
            keys =[k for k in (self.jwt_secret_file, self.jwt_public_key_file, self.jwt_jwks_file) if k]
            if not keys:
                out.append("AUTH_MODE=jwt needs a key file: JWT_SECRET_FILE, JWT_PUBLIC_KEY_FILE or JWT_JWKS_FILE")
            if self.jwt_alg in SYMMETRIC:
                if self.jwt_public_key_file or self.jwt_jwks_file:
                    out.append(f"{self.jwt_alg} takes JWT_SECRET_FILE only: a public key or a JWKS belongs to an asymmetric algorithm")
                if not self.jwt_secret_file:
                    out.append(f"{self.jwt_alg} needs JWT_SECRET_FILE")
            else:
                if self.jwt_secret_file:
                    out.append(f"{self.jwt_alg} takes JWT_PUBLIC_KEY_FILE or JWT_JWKS_FILE: a shared secret belongs to HS256, HS384 or HS512")
                if self.jwt_public_key_file and self.jwt_jwks_file:
                    out.append("give JWT_PUBLIC_KEY_FILE or JWT_JWKS_FILE, not both")
            for label, path in (("JWT_SECRET_FILE", self.jwt_secret_file), ("JWT_PUBLIC_KEY_FILE", self.jwt_public_key_file),
                                ("JWT_JWKS_FILE", self.jwt_jwks_file)):
                if path and "://" in path:
                    out.append(f"{label} is a file path: the service calls nothing, a URL is not supported")
                elif path and not Path(path).is_file():
                    out.append(f"{label} names a file that does not exist")
        if self.id_namespace:
            try:
                uuid.UUID(self.id_namespace)
            except ValueError:
                out.append("ID_NAMESPACE must be a UUID")
        if self.sign_output == "jws" and not self.signing_key_file:
            out.append("SIGN_OUTPUT=jws needs SIGNING_KEY_FILE")
        if self.scan_prep not in ("off", "on"):
            bad = [t for t in self.scan_prep.split(",") if t.strip() not in SCAN_PREP_TOKENS]
            if bad:
                out.append(f"SCAN_PREP must be off, on or a comma list of {', '.join(sorted(SCAN_PREP_TOKENS))}")
        return out

    def _has_key(self) -> bool:
        return any((self.jwt_secret_file, self.jwt_public_key_file, self.jwt_jwks_file))

    @property
    def auth_enabled(self) -> bool:
        """Tokens are checked: AUTH_MODE=jwt, or AUTH_MODE=auto (the default) with a key file named."""
        return self.auth_mode == "jwt" or (self.auth_mode == "auto" and self._has_key())


def scan_prep_steps(value: str) -> frozenset[str]:
    """SCAN_PREP -> the set of scan preparation steps: off = none, on = the accepted set, else the named tokens."""
    if value == "off":
        return frozenset()
    if value == "on":
        return SCAN_PREP_ACCEPTED
    return frozenset(t.strip() for t in value.split(",") if t.strip() in SCAN_PREP_TOKENS)


def read_options(s: Settings):
    """Settings -> the limits and thresholds of the readers."""
    from app.readers import ReadOptions

    return ReadOptions(ocr_min_chars=s.ocr_min_chars, max_pages=s.max_pages, max_cells=s.max_cells,
                       max_pixels=s.max_pixels, ocr_lang=s.ocr_langs,  # no timeout setting exists: ocr_timeout keeps its default
                       scan_prep=scan_prep_steps(s.scan_prep))


def compose_options(s: Settings):
    """Settings -> the switches of the composer. `flat` repeating style is the composer's one plain section."""
    from app.compose import ComposeOptions
    from app.compose.names import ID_NAMESPACE

    return ComposeOptions(
        finish_style=s.finish_style,
        validators=s.validators == "on",
        required_policy=s.required_policy,
        repeating_style="section" if s.repeating_style == "flat" else "native",
        statutory_representative=s.statutory_representative,
        poa_exemption=s.poa_exemption,
        form_key=s.form_key or None,
        id_namespace=uuid.UUID(s.id_namespace) if s.id_namespace else ID_NAMESPACE,
    )
