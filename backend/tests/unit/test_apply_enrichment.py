import pytest

from app.models import Company, Contact
from app.services.enrichment.apply import (
    _email_matches_person,
    apply_company_fields,
    merge_contacts,
)

ENRICHMENT = {
    "website_status": "alive",
    "has_ssl": True,
    "http_status": 200,
    "final_url": "https://www.acmehvac.com/",
    "pages_crawled": ["/", "/about"],
    "data": {
        "description": "Family-owned HVAC in Austin since 1998.",
        "founded_year": 1998,
        "copyright_year": 2019,
        "tech_stack": ["WordPress"],
        "socials": {"facebook": "https://facebook.com/acmehvac"},
        "hiring": False,
        "family_owned": True,
        "family_owned_hint": "family-owned",
        "emails": ["john@acmehvac.com", "office@acmehvac.com"],
        "phones": ["+15125550100"],
        "people": [
            {"full_name": "John Smith", "title": "Owner", "is_decision_maker": True},
            {"full_name": "Maria Garcia", "title": "Office Manager", "is_decision_maker": False},
        ],
    },
}


def make_company(contacts=None) -> Company:
    c = Company(name="Acme HVAC", name_normalized="acme hvac", domain="acmehvac.com")
    c.contacts = contacts or []
    c.signals = {}
    return c


@pytest.mark.parametrize(
    "email, name, expected",
    [
        ("john@acme.com", "John Smith", True),
        ("jsmith@acme.com", "John Smith", True),
        ("john.smith@acme.com", "John Smith", True),
        ("smithj@acme.com", "John Smith", True),
        ("office@acme.com", "John Smith", False),
        ("john@acme.com", "John", False),
    ],
)
def test_email_matches_person(email, name, expected):
    assert _email_matches_person(email, name) is expected


def test_company_fields_are_filled():
    company = make_company()
    apply_company_fields(company, ENRICHMENT)
    assert company.website_status == "alive"
    assert company.founded_year == 1998
    assert company.copyright_year == 2019
    assert company.signals["family_owned"] is True
    assert company.signals["has_ssl"] is True
    assert company.website_url == "https://www.acmehvac.com/"
    assert company.last_enriched_at is not None


def test_merge_attaches_email_and_phone_to_owner():
    company = make_company()
    merge_contacts(company, ENRICHMENT)

    by_name = {c.full_name: c for c in company.contacts if c.full_name}
    john = by_name["John Smith"]
    assert john.email == "john@acmehvac.com"
    assert john.phone_e164 == "+15125550100"
    assert john.is_decision_maker
    # generic inbox becomes its own contact
    assert any(c.email == "office@acmehvac.com" and not c.full_name for c in company.contacts)
    assert len(company.contacts) == 3


def test_merge_does_not_duplicate_csv_contacts():
    existing = Contact(full_name="John Smith", email="john@acmehvac.com", source="csv")
    company = make_company([existing])
    merge_contacts(company, ENRICHMENT)

    emails = [c.email for c in company.contacts if c.email]
    assert emails.count("john@acmehvac.com") == 1
    assert existing.title == "Owner"  # filled in from the website
    assert existing.is_decision_maker
