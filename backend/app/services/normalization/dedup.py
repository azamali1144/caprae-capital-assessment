from dataclasses import dataclass, field

from rapidfuzz import fuzz

from app.schemas.raw_lead import RawLead
from app.services.normalization.company_name import clean_display_name, normalize_company_name
from app.services.normalization.domain import canonical_domain

FUZZY_THRESHOLD = 92

# a gmail address tells us nothing about the company's website
FREE_MAIL = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "aol.com",
    "icloud.com",
    "live.com",
    "msn.com",
    "protonmail.com",
    "comcast.net",
    "att.net",
    "verizon.net",
}

# fields we fill from a duplicate when the kept row is missing them
_FILLABLE = ("name", "industry", "city", "state", "country", "employees", "revenue")


@dataclass
class ContactSeed:
    full_name: str | None = None
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None

    def key(self) -> tuple:
        return ((self.email or "").lower(), (self.full_name or "").lower(), self.phone or "")

    def is_empty(self) -> bool:
        return not (self.full_name or self.email or self.phone or self.linkedin)


@dataclass
class LeadCandidate:
    name: str
    name_normalized: str
    domain: str | None = None
    industry: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    employees: int | None = None
    revenue: int | None = None
    contacts: list[ContactSeed] = field(default_factory=list)
    merged_count: int = 0  # how many dupes got folded into this one

    def add_contact(self, contact: ContactSeed) -> None:
        if contact.is_empty():
            return
        if any(c.key() == contact.key() for c in self.contacts):
            return
        self.contacts.append(contact)


def _to_candidate(lead: RawLead) -> LeadCandidate:
    domain = canonical_domain(lead.domain)
    if not domain:
        email_domain = canonical_domain(lead.email)
        if email_domain and email_domain not in FREE_MAIL:
            domain = email_domain
    name = clean_display_name(lead.name) or (domain or "")
    cand = LeadCandidate(
        name=name,
        name_normalized=normalize_company_name(name),
        domain=domain,
        industry=lead.industry,
        city=lead.city,
        state=lead.state,
        country=lead.country,
        employees=lead.employees,
        revenue=lead.revenue,
    )
    cand.add_contact(
        ContactSeed(
            full_name=lead.owner,
            title=lead.title,
            email=lead.email,
            phone=lead.phone,
            linkedin=lead.linkedin,
        )
    )
    return cand


def _merge(keep: LeadCandidate, dupe: LeadCandidate) -> None:
    for attr in _FILLABLE:
        if getattr(keep, attr) in (None, "") and getattr(dupe, attr) not in (None, ""):
            setattr(keep, attr, getattr(dupe, attr))
    if not keep.domain and dupe.domain:
        keep.domain = dupe.domain
    for c in dupe.contacts:
        keep.add_contact(c)
    keep.merged_count += 1 + dupe.merged_count


def _same_place(a: LeadCandidate, b: LeadCandidate) -> bool:
    # no city on either side -> can't tell, treat as same place
    if not a.city or not b.city:
        return True
    return a.city.strip().lower() == b.city.strip().lower()


def dedupe_leads(
    leads: list[RawLead], existing_domains: set[str] | None = None
) -> tuple[list[LeadCandidate], int]:
    """Exact dedup on domain, fuzzy on name+city for rows without one.

    Rows whose domain is already in the db (existing_domains) are dropped too.
    Returns (unique candidates, number of rows removed).
    """
    existing = existing_domains or set()
    by_domain: dict[str, LeadCandidate] = {}
    no_domain: list[LeadCandidate] = []
    removed = 0

    for lead in leads:
        cand = _to_candidate(lead)
        if not cand.name_normalized and not cand.domain:
            removed += 1
            continue

        if cand.domain:
            if cand.domain in existing:
                removed += 1
                continue
            if cand.domain in by_domain:
                _merge(by_domain[cand.domain], cand)
                removed += 1
                continue
            by_domain[cand.domain] = cand
        else:
            no_domain.append(cand)

    kept = list(by_domain.values())

    # fuzzy pass: rows without a domain vs everything we've kept so far
    for cand in no_domain:
        match = next(
            (
                k
                for k in kept
                if k.name_normalized
                and _same_place(k, cand)
                and fuzz.token_sort_ratio(k.name_normalized, cand.name_normalized)
                >= FUZZY_THRESHOLD
            ),
            None,
        )
        if match:
            _merge(match, cand)
            removed += 1
        else:
            kept.append(cand)

    return kept, removed
