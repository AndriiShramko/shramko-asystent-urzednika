"""Token check (design 8, "token abuse"). The algorithm comes from configuration, never from the token; `none` is
never accepted; `exp` is required; issuer and audience must equal the configured ones; leeway is capped; the key
is read from a file; nothing is fetched. The answer to a bad token is never more specific than three codes."""
from .token import RateLimiter, TokenVerifier, scopes_of

__all__ = ["RateLimiter", "TokenVerifier", "scopes_of"]
