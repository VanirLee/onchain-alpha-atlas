from onchain_alpha.rate_limit import TokenBucket


def test_bucket_can_acquire_without_sleep():
    bucket = TokenBucket(100, capacity=2)
    bucket.acquire(); bucket.acquire()
    assert bucket.tokens >= 0


def test_bucket_penalizes_429():
    bucket = TokenBucket(10, capacity=2)
    before = bucket.rate
    bucket.penalize()
    assert bucket.rate < before
