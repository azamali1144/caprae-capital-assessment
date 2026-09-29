"""Turn a cached enrichment result into rows on the company + its contacts."""

from datetime import UTC, datetime

from app.models import Company, Contact
from app.services.enrichment.extractors.people import is_decision_maker
from app.services.validation.email import check_email
from app.services.validation.phone import check_phone


def _email_matches_person(email: str, full_name: str) -> bool:
    # john@, jsmith@, john.smith@, smithj@ all count as John Smith
    local = email.split("@", 1)[0].lower().replace(".", "").replace("_", "")
    parts = [p.lower() for p in full_name.split() if p.isalpha()]
    if len(parts) < 2:
        return False
    first, last = parts[0], parts[-1]
    return local in {first, first + last, first[0] + last, last + first[0], last}


def apply_company_fields(company: Company, enrichment: dict) -> None:
    data = enrichment.get("data") or {}

    company.website_status = enrichment.get("website_status")
    if enrichment.get("final_url"):
        company.website_url = enrichment["final_url"]
    if data.get("description") and not company.description:
        company.description = data["description"]
    company.founded_year = data.get("founded_year") or company.founded_year
    company.copyright_year = data.get("copyright_year")
    company.tech_stack = data.get("tech_stack") or []
    company.socials = data.get("socials") or {}
    company.signals = {
        **(company.signals or {}),
        "has_ssl": bool(enrichment.get("has_ssl")),
        "http_status": enrichment.get("http_status"),
        "hiring": bool(data.get("hiring")),
        "hiring_evidence": data.get("hiring_evidence") or [],
        "modern_stack": bool(data.get("modern_stack")),
        "family_owned": bool(data.get("family_owned")),
        "family_owned_hint": data.get("family_owned_hint"),
        "pages_crawled": enrichment.get("pages_crawled") or [],
    }
    company.last_enriched_at = datetime.now(UTC)


def merge_contacts(company: Company, enrichment: dict) -> None:
    """Add people/emails/phones found on the site without duplicating what the csv gave us."""
    data = enrichment.get("data") or {}
    contacts: list[Contact] = company.contacts
    by_email = {c.email.lower(): c for c in contacts if c.email}
    by_name = {c.full_name.lower(): c for c in contacts if c.full_name}

    for person in data.get("people") or []:
        existing = by_name.get(person["full_name"].lower())
        if existing:
            existing.title = existing.title or person.get("title")
            existing.is_decision_maker = existing.is_decision_maker or person["is_decision_maker"]
            continue
        c = Contact(
            full_name=person["full_name"],
            title=person.get("title"),
            is_decision_maker=person["is_decision_maker"],
            source="website",
        )
        contacts.append(c)
        by_name[c.full_name.lower()] = c

    for email in data.get("emails") or []:
        if email in by_email:
            continue
        owner = next(
            (
                c
                for c in contacts
                if c.full_name and not c.email and _email_matches_person(email, c.full_name)
            ),
            None,
        )
        if owner:
            owner.email = email
        else:
            owner = Contact(email=email, source="website")
            contacts.append(owner)
        by_email[email] = owner

    phones = data.get("phones") or []
    if phones:
        # main line goes to the decision maker if we have one, else the first contact w/o phone
        target = next((c for c in contacts if c.is_decision_maker and not c.phone_e164), None)
        target = target or next((c for c in contacts if not c.phone_e164), None)
        if target:
            target.phone_e164 = phones[0]
        elif not contacts:
            contacts.append(Contact(phone_e164=phones[0], source="website"))


async def validate_contacts(company: Company) -> None:
    for c in company.contacts:
        # csv rows often have "Owner"/"CEO" in the title column but no flag
        if c.title and not c.is_decision_maker:
            c.is_decision_maker = is_decision_maker(c.title)
        if c.email:
            res = await check_email(c.email)
            c.email = res.email
            c.email_status = res.status
            c.email_type = res.type
        if c.phone_e164:
            res = check_phone(c.phone_e164, company.country)
            c.phone_e164 = res.e164 or c.phone_e164
            c.phone_valid = res.valid
