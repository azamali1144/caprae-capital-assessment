from app.schemas.raw_lead import RawLead
from app.services.normalization.dedup import dedupe_leads


def test_same_domain_different_case_and_url_merges():
    leads = [
        RawLead(name="Acme HVAC", domain="https://www.AcmeHVAC.com/about"),
        RawLead(name="Acme Heating", domain="acmehvac.com", city="Austin"),
    ]
    unique, removed = dedupe_leads(leads)
    assert removed == 1
    assert len(unique) == 1
    assert unique[0].domain == "acmehvac.com"
    assert unique[0].city == "Austin"  # filled from the dupe
    assert unique[0].merged_count == 1


def test_fuzzy_name_match_without_domain():
    leads = [
        RawLead(name="Acme Inc", domain="acme.com", city="Austin"),
        RawLead(name="ACME, Inc.", city="Austin", email="jane@gmail.com", owner="Jane Doe"),
    ]
    unique, removed = dedupe_leads(leads)
    assert removed == 1
    assert len(unique) == 1
    assert {c.full_name for c in unique[0].contacts} == {"Jane Doe"}


def test_same_name_different_cities_not_merged():
    leads = [
        RawLead(name="Joe's Plumbing", city="Austin"),
        RawLead(name="Joes Plumbing LLC", city="Denver"),
    ]
    unique, removed = dedupe_leads(leads)
    assert removed == 0
    assert len(unique) == 2


def test_contacts_are_unioned_without_repeats():
    leads = [
        RawLead(domain="acme.com", owner="John Smith", email="john@acme.com"),
        RawLead(domain="acme.com", owner="John Smith", email="john@acme.com"),
        RawLead(domain="acme.com", owner="Sara Lee", email="sara@acme.com"),
    ]
    unique, removed = dedupe_leads(leads)
    assert removed == 2
    assert sorted(c.email for c in unique[0].contacts) == ["john@acme.com", "sara@acme.com"]


def test_existing_domains_are_dropped():
    leads = [RawLead(domain="acme.com"), RawLead(domain="new.com")]
    unique, removed = dedupe_leads(leads, existing_domains={"acme.com"})
    assert [u.domain for u in unique] == ["new.com"]
    assert removed == 1


def test_domain_falls_back_to_company_email():
    unique, _ = dedupe_leads([RawLead(name="Bright Books", email="amy@brightbooks.io")])
    assert unique[0].domain == "brightbooks.io"


def test_name_defaults_to_domain():
    unique, _ = dedupe_leads([RawLead(domain="coolair.com")])
    assert unique[0].name == "coolair.com"


def test_apostrophes_dont_break_fuzzy_match():
    leads = [
        RawLead(name="Joe's Plumbing", city="Denver"),
        RawLead(name="Joes Plumbing LLC", city="Denver"),
    ]
    unique, removed = dedupe_leads(leads)
    assert removed == 1
    assert len(unique) == 1
