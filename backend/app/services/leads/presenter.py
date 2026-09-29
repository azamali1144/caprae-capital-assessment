from app.models import Company, Contact
from app.schemas.company import ContactOut, LeadDetail, LeadOut


def best_contact(contacts: list[Contact]) -> Contact | None:
    """Who a rep should reach out to first."""
    if not contacts:
        return None

    def rank(c: Contact) -> tuple:
        return (
            c.is_decision_maker and c.email_status == "valid_mx",
            c.email_status == "valid_mx" and c.email_type == "personal",
            c.is_decision_maker,
            c.email_status == "valid_mx",
            bool(c.email),
            c.phone_valid,
        )

    return max(contacts, key=rank)


def top_reasons(company: Company, n: int = 2) -> list[str]:
    items = [b for b in (company.score_breakdown or []) if b.get("points", 0) > 0]
    items.sort(key=lambda b: -b["points"])
    return [b["reason"] for b in items[:n]]


def to_lead_out(company: Company) -> LeadOut:
    contact = best_contact(company.contacts)
    return LeadOut.model_validate(company).model_copy(
        update={
            "best_contact": ContactOut.model_validate(contact) if contact else None,
            "contacts_count": len(company.contacts),
            "top_reasons": top_reasons(company),
        }
    )


def to_lead_detail(company: Company) -> LeadDetail:
    contacts = sorted(
        company.contacts,
        key=lambda c: (not c.is_decision_maker, c.email_status != "valid_mx", c.full_name or "~"),
    )
    base = to_lead_out(company)
    return LeadDetail.model_validate(company).model_copy(
        update={
            "best_contact": base.best_contact,
            "contacts_count": base.contacts_count,
            "top_reasons": top_reasons(company, n=3),
            "contacts": [ContactOut.model_validate(c) for c in contacts],
        }
    )
