"""Scoring rules.

Each rule looks at a company + its contacts + the ICP and returns a short reason
string when it applies (None when it doesn't). Points live in the strategies, so
the same rule can be worth +10 for sales and -5 for acquisition.
"""

from collections.abc import Callable, Sequence
from datetime import date
from typing import Any

Rule = Callable[[Any, Sequence[Any], dict], str | None]

STALE_SITE_YEARS = 3
DEFAULT_MIN_YEARS = 10
# owner-operated sweet spot for searchers when the icp doesn't say otherwise
ACQ_EMPLOYEE_RANGE = (5, 100)


def _signals(company) -> dict:
    return getattr(company, "signals", None) or {}


def _lower_list(values) -> list[str]:
    return [str(v).strip().lower() for v in (values or []) if str(v).strip()]


def industry_match(company, contacts, icp) -> str | None:
    targets = _lower_list(icp.get("industries"))
    industry = (company.industry or "").strip()
    if not targets or not industry:
        return None
    ind = industry.lower()
    if any(t in ind or ind in t for t in targets):
        return f"Industry '{industry}' is in your ICP"
    return None


def location_match(company, contacts, icp) -> str | None:
    targets = _lower_list(icp.get("countries")) + _lower_list(icp.get("states"))
    if not targets:
        return None
    for value in (company.country, company.state):
        if value and value.strip().lower() in targets:
            return f"Located in {value.strip()}"
    return None


def size_fit(company, contacts, icp) -> str | None:
    n = company.employee_count
    if n is None:
        return None
    lo, hi = icp.get("employee_min"), icp.get("employee_max")
    if lo is None and hi is None:
        if icp.get("mode") != "acquisition":
            return None
        lo, hi = ACQ_EMPLOYEE_RANGE
    if (lo is None or n >= lo) and (hi is None or n <= hi):
        return f"{n} employees fits the {lo or 0}-{hi or '∞'} range"
    return None


def personal_email_valid(company, contacts, icp) -> str | None:
    for c in contacts:
        if c.email and c.email_type == "personal" and c.email_status == "valid_mx":
            return f"Verified personal email ({c.email})"
    return None


def decision_maker(company, contacts, icp) -> str | None:
    for c in contacts:
        if c.is_decision_maker and c.full_name:
            title = f" ({c.title})" if c.title else ""
            return f"Found decision maker: {c.full_name}{title}"
    return None


def valid_phone(company, contacts, icp) -> str | None:
    for c in contacts:
        if c.phone_valid and c.phone_e164:
            return f"Valid phone {c.phone_e164}"
    return None


def site_healthy(company, contacts, icp) -> str | None:
    if company.website_status == "alive" and _signals(company).get("has_ssl"):
        return "Website is up with SSL"
    return None


def hiring(company, contacts, icp) -> str | None:
    if _signals(company).get("hiring"):
        evidence = _signals(company).get("hiring_evidence") or []
        return "Hiring right now" + (f" ({evidence[0]})" if evidence else "")
    return None


def modern_stack(company, contacts, icp) -> str | None:
    if _signals(company).get("modern_stack"):
        return "Uses modern sales/marketing tools"
    return None


def years_in_business(company, contacts, icp) -> str | None:
    if not company.founded_year:
        return None
    years = date.today().year - company.founded_year
    if years >= (icp.get("min_years_in_business") or DEFAULT_MIN_YEARS):
        return f"Operating since {company.founded_year} ({years} yrs)"
    return None


def stale_website(company, contacts, icp) -> str | None:
    year = company.copyright_year
    if year and date.today().year - year >= STALE_SITE_YEARS:
        return f"Website not updated since {year}"
    return None


def family_owned(company, contacts, icp) -> str | None:
    if _signals(company).get("family_owned"):
        hint = _signals(company).get("family_owned_hint")
        return f"Says it's '{hint}'" if hint else "Family / owner operated"
    return None


def low_confidence_merge(company, contacts, icp) -> str | None:
    if _signals(company).get("low_confidence_merge"):
        return "Merged from fuzzy-matched duplicates"
    return None


def role_only_emails(company, contacts, icp) -> str | None:
    emails = [c for c in contacts if c.email and c.email_status != "invalid_syntax"]
    if emails and all(c.email_type == "role" for c in emails):
        return "Only generic inboxes (info@, sales@...)"
    return None


def site_dead(company, contacts, icp) -> str | None:
    if company.website_status in ("dead", "timeout"):
        return f"Website is {company.website_status}"
    return None


RULES: dict[str, Rule] = {
    "industry_match": industry_match,
    "location_match": location_match,
    "size_fit": size_fit,
    "personal_email_valid": personal_email_valid,
    "decision_maker": decision_maker,
    "valid_phone": valid_phone,
    "site_healthy": site_healthy,
    "hiring": hiring,
    "modern_stack": modern_stack,
    "years_in_business": years_in_business,
    "stale_website": stale_website,
    "family_owned": family_owned,
    "low_confidence_merge": low_confidence_merge,
    "role_only_emails": role_only_emails,
    "site_dead": site_dead,
}
