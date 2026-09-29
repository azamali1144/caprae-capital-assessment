import pytest

from app.services.normalization.company_name import normalize_company_name
from app.services.normalization.domain import canonical_domain


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("https://www.Acme-HVAC.com/about?x=1", "acme-hvac.com"),
        ("acme.com", "acme.com"),
        ("www.acme.com", "acme.com"),
        ("http://shop.acme.com/cart", "acme.com"),
        ("  ACME.COM  ", "acme.com"),
        ("mailto:john@acme.com", "acme.com"),
        ("john@acme.com", "acme.com"),
        ("https://blog.acme.co.uk", "acme.co.uk"),
        ("acme.com:8080/path", "acme.com"),
        ("http://acme.com.", "acme.com"),
    ],
)
def test_canonical_domain(raw, expected):
    assert canonical_domain(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "   ", "not a domain", "localhost", "http://", "com"])
def test_canonical_domain_rejects_junk(raw):
    assert canonical_domain(raw) is None


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("ACME, Inc.", "acme"),
        ("Acme Inc", "acme"),
        ("Acme HVAC LLC", "acme hvac"),
        ("Smith & Sons Co.", "smith and sons"),
        ("The Plumbing Company", "plumbing"),
        ("Müller GmbH", "muller"),
        ("  Big   Air   Corp ", "big air"),
        ("Inc", "inc"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalize_company_name(raw, expected):
    assert normalize_company_name(raw) == expected
