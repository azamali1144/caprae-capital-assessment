import dns.exception
import dns.resolver
import pytest

from app.services.validation import email as email_mod
from app.services.validation.email import check_email, email_type, has_mx


class FakeMx:
    def __init__(self, exchange):
        self.exchange = exchange


class FakeResolver:
    # domain -> list of mx hosts, or an exception to raise
    answers: dict = {}
    calls = 0

    def __init__(self):
        self.lifetime = None

    async def resolve(self, domain, rtype):
        FakeResolver.calls += 1
        ans = self.answers.get(domain, dns.resolver.NXDOMAIN())
        if isinstance(ans, Exception):
            raise ans
        return [FakeMx(h) for h in ans]


@pytest.fixture(autouse=True)
def fake_dns(monkeypatch):
    store = {}

    async def fake_get(key):
        return store.get(key)

    async def fake_set(key, value, ttl):
        store[key] = value

    monkeypatch.setattr(email_mod, "cache_get_json", fake_get)
    monkeypatch.setattr(email_mod, "cache_set_json", fake_set)
    FakeResolver.answers = {
        "acme.com": ["mx1.acme.com."],
        "nomail.com": dns.resolver.NoAnswer(),
        "slow.com": dns.exception.Timeout(),
    }
    FakeResolver.calls = 0
    monkeypatch.setattr(email_mod.dns.asyncresolver, "Resolver", FakeResolver)
    return store


@pytest.mark.parametrize(
    "email, status, kind",
    [
        ("john@acme.com", "valid_mx", "personal"),
        ("Info@ACME.com", "valid_mx", "role"),
        ("sales+leads@acme.com", "valid_mx", "role"),
        ("john@nomail.com", "no_mx", "personal"),
        ("john@doesnotexist-xyz.com", "no_mx", "personal"),
        ("john@slow.com", "unknown", "personal"),
        ("temp@mailinator.com", "disposable", "personal"),
        ("not-an-email", "invalid_syntax", None),
        ("john@@acme.com", "invalid_syntax", None),
        ("", "invalid_syntax", None),
    ],
)
async def test_check_email(email, status, kind):
    res = await check_email(email)
    assert (res.status, res.type) == (status, kind)


async def test_email_is_normalized():
    res = await check_email("  John.Smith@ACME.com ")
    assert res.email == "john.smith@acme.com"
    assert res.deliverable


async def test_mx_result_is_cached(fake_dns):
    await has_mx("acme.com")
    await has_mx("acme.com")
    assert FakeResolver.calls == 1
    assert fake_dns["mx:acme.com"] == {"mx": True}


async def test_dns_timeout_is_not_cached(fake_dns):
    assert await has_mx("slow.com") is None
    assert "mx:slow.com" not in fake_dns


def test_email_type():
    assert email_type("hello") == "role"
    assert email_type("jane.doe") == "personal"
