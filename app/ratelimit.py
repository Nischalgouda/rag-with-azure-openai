"""Token-bucket rate limiting.

A bucket holds up to `capacity` tokens and earns one token every `refill_seconds`.
Each request spends one token. A burst of up to `capacity` requests is allowed, after that
requests are admitted at the steady refill rate. Compared with a fixed "N per minute" window it
has no boundary spikes (N requests at 0:59 and N more at 1:01).

The clock is injectable so tests can move time instantly instead of sleeping.

Limitation (by design, documented): buckets live in this process's memory. With several replicas
each would keep its own counts; a shared store such as Redis would be the next step.
"""
import math
import threading
import time
from collections import OrderedDict
from collections.abc import Callable

Clock = Callable[[], float]


class TokenBucket:
    def __init__(self, capacity: int, refill_seconds: float, clock: Clock = time.monotonic):
        self.capacity = capacity
        self.refill_seconds = refill_seconds
        self._clock = clock
        self._tokens = float(capacity)
        self._last = clock()

    def take(self) -> tuple[bool, float]:
        """Try to spend one token. Returns (allowed, seconds_until_a_token_is_available)."""
        now = self._clock()
        self._tokens = min(self.capacity, self._tokens + (now - self._last) / self.refill_seconds)
        self._last = now
        if self._tokens >= 1:
            self._tokens -= 1
            return True, 0.0
        return False, (1 - self._tokens) * self.refill_seconds


class RateLimiter:
    """One bucket per identity (API key owner or client IP), with a bounded memory footprint."""

    def __init__(self, capacity: int, refill_seconds: float, clock: Clock = time.monotonic,
                 max_identities: int = 10_000):
        self._capacity = capacity
        self._refill_seconds = refill_seconds
        self._clock = clock
        self._max = max_identities
        self._buckets: OrderedDict[str, TokenBucket] = OrderedDict()
        self._lock = threading.Lock()

    def check(self, identity: str) -> tuple[bool, int]:
        """Returns (allowed, retry_after_seconds). retry_after is 0 when allowed, otherwise >= 1."""
        with self._lock:
            bucket = self._buckets.get(identity)
            if bucket is None:
                bucket = TokenBucket(self._capacity, self._refill_seconds, self._clock)
                self._buckets[identity] = bucket
                if len(self._buckets) > self._max:
                    self._buckets.popitem(last=False)  # evict the least recently used identity
            else:
                self._buckets.move_to_end(identity)
            allowed, wait = bucket.take()
        return allowed, 0 if allowed else max(1, math.ceil(wait))
