"""Token-bucket behaviour, tested with a fake clock so no test ever sleeps."""
from app.ratelimit import RateLimiter, TokenBucket
from tests.helpers import FakeClock


def test_a_burst_up_to_capacity_is_allowed_then_blocked():
    clock = FakeClock()
    bucket = TokenBucket(capacity=3, refill_seconds=10, clock=clock)
    assert [bucket.take()[0] for _ in range(3)] == [True, True, True]
    allowed, wait = bucket.take()
    assert allowed is False
    assert wait == 10  # a full empty bucket needs one whole refill period


def test_tokens_refill_with_time():
    clock = FakeClock()
    bucket = TokenBucket(capacity=2, refill_seconds=10, clock=clock)
    bucket.take(), bucket.take()
    assert bucket.take()[0] is False
    clock.advance(9)
    assert bucket.take()[0] is False  # 0.9 of a token is not enough
    clock.advance(1)
    assert bucket.take()[0] is True


def test_idle_time_never_banks_more_than_capacity():
    clock = FakeClock()
    bucket = TokenBucket(capacity=2, refill_seconds=1, clock=clock)
    clock.advance(10_000)
    assert [bucket.take()[0] for _ in range(3)] == [True, True, False]


def test_wait_time_shrinks_as_the_bucket_refills():
    clock = FakeClock()
    bucket = TokenBucket(capacity=1, refill_seconds=10, clock=clock)
    bucket.take()
    clock.advance(4)
    allowed, wait = bucket.take()
    assert allowed is False
    assert round(wait) == 6


def test_identities_have_independent_buckets():
    limiter = RateLimiter(capacity=1, refill_seconds=60, clock=FakeClock())
    assert limiter.check("ip:1.1.1.1") == (True, 0)
    assert limiter.check("ip:1.1.1.1")[0] is False
    assert limiter.check("ip:2.2.2.2") == (True, 0)


def test_retry_after_is_a_whole_number_of_seconds_of_at_least_one():
    limiter = RateLimiter(capacity=1, refill_seconds=0.2, clock=FakeClock())
    limiter.check("a")
    allowed, retry_after = limiter.check("a")
    assert allowed is False
    assert isinstance(retry_after, int) and retry_after >= 1


def test_memory_is_bounded_by_evicting_the_least_recently_used_identity():
    limiter = RateLimiter(capacity=1, refill_seconds=3600, clock=FakeClock(), max_identities=2)
    limiter.check("a")
    limiter.check("b")
    limiter.check("c")  # evicts "a"
    assert limiter.check("a") == (True, 0)  # "a" was forgotten, so it gets a fresh bucket
    assert limiter.check("c")[0] is False   # "c" is still remembered and still empty
