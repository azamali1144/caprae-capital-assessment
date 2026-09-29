import pytest

from app.services.validation.phone import check_phone
from app.services.validation.website import classify_website


@pytest.mark.parametrize(
    "raw, country, e164, valid",
    [
        ("(512) 555-0100", "US", "+15125550100", True),
        ("512.555.0199", None, "+15125550199", True),
        ("+44 20 7123 4567", "US", "+442071234567", True),
        ("020 7123 4567", "UK", "+442071234567", True),
        ("555-0100", "US", None, False),
        ("call us", "US", None, False),
        ("", "US", None, False),
        (None, None, None, False),
    ],
)
def test_check_phone(raw, country, e164, valid):
    res = check_phone(raw, country)
    assert res.e164 == e164
    assert res.valid is valid


def test_toll_free_kind():
    assert check_phone("1-800-555-0199", "US").kind in ("toll_free", None)


@pytest.mark.parametrize(
    "enrichment, status, healthy",
    [
        ({"website_status": "alive", "has_ssl": True, "http_status": 200}, "alive", True),
        ({"website_status": "alive", "has_ssl": False, "http_status": 200}, "alive", False),
        ({"website_status": "blocked", "http_status": 403}, "blocked", False),
        ({"website_status": "timeout"}, "timeout", False),
        ({"website_status": "dead", "errors": ["home: connect_error"]}, "dead", False),
        ({}, "dead", False),
    ],
)
def test_classify_website(enrichment, status, healthy):
    res = classify_website(enrichment)
    assert res.status == status
    assert res.healthy is healthy
    assert res.reason


def test_dead_reason_mentions_error():
    res = classify_website({"website_status": "dead", "errors": ["home: connect_error"]})
    assert "connect_error" in res.reason
