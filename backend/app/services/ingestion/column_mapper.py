import re

# our field -> header names we've seen in the wild (saasquatch exports + generic crm dumps)
SYNONYMS: dict[str, list[str]] = {
    "domain": ["domain", "website", "url", "company website", "website url", "web", "site"],
    "name": ["company", "company name", "name", "business name", "organization", "account name"],
    "industry": ["industry", "category", "sector", "vertical", "business type"],
    "email": ["email", "email address", "contact email", "owner email", "e-mail"],
    "phone": ["phone", "phone number", "telephone", "contact phone", "mobile", "tel"],
    "city": ["city", "town", "locality"],
    "state": ["state", "region", "province", "state/province"],
    "country": ["country", "country code", "nation"],
    "employees": ["employees", "employee count", "headcount", "company size", "size", "staff"],
    "revenue": ["revenue", "annual revenue", "revenue estimate", "est revenue", "sales volume"],
    "owner": ["owner", "owner name", "contact name", "contact", "full name", "decision maker"],
    "title": ["title", "job title", "owner title", "position", "role"],
    "linkedin": ["linkedin", "linkedin url", "company linkedin", "linkedin profile"],
}

_CLEAN_RE = re.compile(r"[^a-z0-9/]+")


def _clean(header: str) -> str:
    return _CLEAN_RE.sub(" ", header.lower()).strip()


_LOOKUP = {_clean(s): field for field, names in SYNONYMS.items() for s in names}


def map_columns(headers: list[str]) -> tuple[dict[str, str], list[str]]:
    """Returns ({header: field}, unmapped_headers). First header wins per field."""
    mapping: dict[str, str] = {}
    taken: set[str] = set()
    unmapped: list[str] = []

    for header in headers:
        field = _LOOKUP.get(_clean(header))
        if field and field not in taken:
            mapping[header] = field
            taken.add(field)
        else:
            unmapped.append(header)
    return mapping, unmapped
