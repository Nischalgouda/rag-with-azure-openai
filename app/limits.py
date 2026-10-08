"""Demo-mode guards: who may call what, how often, and the global cost ceiling.

In normal (dev) mode nothing here restricts anything, so a fork runs with zero friction.
With DEMO_MODE=true:
  * /ask is open to anonymous visitors on a small allowance (burst + daily cap per IP),
    and to API-key holders on a larger one.
  * /ingest and /usage are admin-only.
  * A global daily token budget and a kill switch protect the Azure bill.
"""
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request

from app import auth, db
from app.config import settings
from app.ratelimit import RateLimiter


@dataclass(frozen=True)
class Caller:
    identity: str            # "key:<owner>" or "ip:<address>"
    owner: str | None        # API-key owner, None for anonymous
    daily_cap: int           # questions allowed per UTC day
    used_today: int          # questions already asked today (before this one)

    @property
    def remaining_after_this(self) -> int:
        return max(0, self.daily_cap - self.used_today - 1)


def _build_limiters() -> tuple[RateLimiter, RateLimiter]:
    return (
        RateLimiter(settings.anon_burst, settings.anon_refill_seconds),
        RateLimiter(settings.keyed_burst, settings.keyed_refill_seconds),
    )


anon_limiter, keyed_limiter = _build_limiters()


def _too_many(detail: str, retry_after: int) -> HTTPException:
    return HTTPException(status_code=429, detail=detail, headers={"Retry-After": str(retry_after)})


def client_ip(request: Request) -> str:
    """The visitor's address, resilient to spoofed X-Forwarded-For.

    Each proxy APPENDS the address it saw to the right of the header, while everything to the left may
    have been written by the client. So with N trusted proxies the real visitor is the Nth entry from the
    right. With 0 trusted proxies the header is ignored entirely."""
    hops = settings.trusted_proxy_hops
    forwarded = request.headers.get("x-forwarded-for")
    if hops > 0 and forwarded:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if len(parts) >= hops:
            return parts[-hops]
    return request.client.host if request.client else "unknown"


def guard_ask(request: Request, owner: str | None = Depends(auth.optional_api_key)) -> Caller:
    """Dependency for POST /ask. Raises 503 / 429 when the caller must not proceed."""
    identity = f"key:{owner}" if owner else f"ip:{client_ip(request)}"
    cap = settings.keyed_daily_questions if owner else settings.anon_daily_questions

    if not settings.demo_mode:
        return Caller(identity, owner, cap, used_today=0)

    if not settings.demo_enabled:
        raise HTTPException(status_code=503, detail="The demo is switched off right now. Please check back later.")

    allowed, retry_after = (keyed_limiter if owner else anon_limiter).check(identity)
    if not allowed:
        raise _too_many("You're asking quickly. Give it a few seconds.", retry_after)

    used = db.questions_today(identity)
    reset_in = db.seconds_until_utc_midnight()
    if used >= cap:
        raise _too_many(f"Daily limit of {cap} questions reached for this demo. It resets at 00:00 UTC.", reset_in)
    if db.tokens_today() >= settings.daily_token_budget:
        raise _too_many("Today's shared demo budget is used up. It resets at 00:00 UTC.", reset_in)

    return Caller(identity, owner, cap, used)


def require_admin(owner: str | None = Depends(auth.optional_api_key)) -> str | None:
    """Dependency for admin endpoints. Open in dev mode; in demo mode needs an admin key."""
    if not settings.demo_mode:
        return owner
    if owner is None:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    admins = {n.strip() for n in settings.admin_key_names.split(",") if n.strip()}
    if owner not in admins:
        raise HTTPException(status_code=403, detail="This endpoint is restricted to administrators")
    return owner
