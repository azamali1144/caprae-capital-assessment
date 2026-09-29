from datetime import date
from types import SimpleNamespace

from app.services.scoring import rules

THIS_YEAR = date.today().year


def company(**kw):
    base = dict(
        industry=None,
        country=None,
        state=None,
        employee_count=None,
        founded_year=None,
        copyright_year=None,
        website_status="alive",
        signals={},
    )
    return SimpleNamespace(**{**base, **kw})


def contact(**kw):
    base = dict(
        full_name=None,
        title=None,
        email=None,
        email_status="unknown",
        email_type=None,
        phone_e164=None,
        phone_valid=False,
        is_decision_maker=False,
    )
    return SimpleNamespace(**{**base, **kw})


def test_industry_match_is_loose():
    icp = {"industries": ["HVAC", "plumbing"]}
    assert rules.industry_match(company(industry="HVAC Services"), [], icp)
    assert rules.industry_match(company(industry="plumbing"), [], icp)
    assert rules.industry_match(company(industry="Bakery"), [], icp) is None
    assert rules.industry_match(company(industry="HVAC"), [], {}) is None


def test_location_match_country_or_state():
    icp = {"countries": ["US"], "states": ["TX"]}
    assert rules.location_match(company(country="us"), [], icp)
    assert rules.location_match(company(country="CA", state="TX"), [], icp)
    assert rules.location_match(company(country="CA"), [], icp) is None


def test_size_fit_uses_icp_range_then_acq_default():
    assert rules.size_fit(company(employee_count=30), [], {"employee_min": 10, "employee_max": 50})
    assert rules.size_fit(company(employee_count=300), [], {"employee_max": 50}) is None
    assert rules.size_fit(company(employee_count=30), [], {"mode": "acquisition"})
    assert rules.size_fit(company(employee_count=30), [], {"mode": "sales"}) is None


def test_contact_rules():
    people = [
        contact(email="info@acme.com", email_type="role", email_status="valid_mx"),
        contact(
            full_name="John Smith",
            title="Owner",
            is_decision_maker=True,
            email="john@acme.com",
            email_type="personal",
            email_status="valid_mx",
            phone_e164="+15125550100",
            phone_valid=True,
        ),
    ]
    assert "john@acme.com" in rules.personal_email_valid(company(), people, {})
    assert rules.decision_maker(company(), people, {}) == "Found decision maker: John Smith (Owner)"
    assert rules.valid_phone(company(), people, {})
    assert rules.role_only_emails(company(), people, {}) is None
    assert rules.role_only_emails(company(), people[:1], {})


def test_years_and_stale_site():
    old = company(founded_year=1998, copyright_year=THIS_YEAR - 5)
    assert f"({THIS_YEAR - 1998} yrs)" in rules.years_in_business(old, [], {})
    assert rules.stale_website(old, [], {})
    young = company(founded_year=THIS_YEAR - 2, copyright_year=THIS_YEAR)
    assert rules.years_in_business(young, [], {}) is None
    assert rules.stale_website(young, [], {}) is None
    # icp can raise the bar
    assert rules.years_in_business(old, [], {"min_years_in_business": 40}) is None


def test_signal_rules():
    c = company(
        signals={
            "has_ssl": True,
            "hiring": True,
            "hiring_evidence": ["careers page"],
            "modern_stack": True,
            "family_owned": True,
            "family_owned_hint": "family-owned",
        }
    )
    assert rules.site_healthy(c, [], {})
    assert rules.hiring(c, [], {}) == "Hiring right now (careers page)"
    assert rules.modern_stack(c, [], {})
    assert "family-owned" in rules.family_owned(c, [], {})
    assert rules.site_dead(c, [], {}) is None
    assert rules.site_dead(company(website_status="timeout"), [], {}) == "Website is timeout"
