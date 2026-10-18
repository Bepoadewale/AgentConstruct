from davdeploy.product_readiness import security_headers
from davdeploy.rate_limit import SlidingWindowRateLimiter


def test_optional_rate_limit_and_security_headers_are_explicit():
    limiter = SlidingWindowRateLimiter(limit=2)
    assert limiter.allow("tenant-a") is True
    assert limiter.allow("tenant-a") is True
    assert limiter.allow("tenant-a") is False
    headers = security_headers()
    assert "Content-Security-Policy" in headers
    assert headers["X-Frame-Options"] == "DENY"
