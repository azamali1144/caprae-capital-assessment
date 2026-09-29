import logging
from dataclasses import dataclass

import dns.asyncresolver
import dns.exception
import dns.resolver
from email_validator import EmailNotValidError, validate_email

from app.core.cache import cache_get_json, cache_set_json

log = logging.getLogger(__name__)

MX_TTL = 60 * 60 * 24
DNS_TIMEOUT = 3.0

ROLE_PREFIXES = {
    "info",
    "sales",
    "contact",
    "admin",
    "support",
    "hello",
    "office",
    "billing",
    "careers",
    "jobs",
    "hr",
    "noreply",
    "no-reply",
    "service",
    "help",
    "team",
    "marketing",
    "accounts",
    "enquiries",
    "inquiries",
    "mail",
    "webmaster",
    "reception",
    "orders",
}

# small list on purpose - the big ones cover most junk signups
DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "guerrillamail.com",
    "10minutemail.com",
    "tempmail.com",
    "temp-mail.org",
    "trashmail.com",
    "yopmail.com",
    "getnada.com",
    "sharklasers.com",
    "throwawaymail.com",
    "maildrop.cc",
    "dispostable.com",
}


@dataclass
class EmailCheck:
    email: str
    status: str  # valid_mx | no_mx | invalid_syntax | disposable | unknown
    type: str | None  # personal | role

    @property
    def deliverable(self) -> bool:
        return self.status == "valid_mx"


def email_type(local_part: str) -> str:
    base = local_part.lower().split("+")[0]
    return "role" if base in ROLE_PREFIXES else "personal"


async def has_mx(domain: str) -> bool | None:
    """True/False when we got an answer, None if dns itself flaked (so we don't lie)."""
    key = f"mx:{domain}"
    cached = await cache_get_json(key)
    if cached is not None:
        return cached["mx"]

    resolver = dns.asyncresolver.Resolver()
    resolver.lifetime = DNS_TIMEOUT
    try:
        answer = await resolver.resolve(domain, "MX")
        ok = any(str(r.exchange).strip(".") for r in answer)
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        ok = False
    except (dns.exception.Timeout, dns.exception.DNSException) as exc:
        log.debug("mx lookup failed for %s: %s", domain, exc)
        return None

    await cache_set_json(key, {"mx": ok}, MX_TTL)
    return ok


async def check_email(email: str) -> EmailCheck:
    """Syntax -> disposable -> MX. No SMTP probing on purpose (see README)."""
    raw = (email or "").strip()
    try:
        parsed = validate_email(raw, check_deliverability=False)
    except EmailNotValidError:
        return EmailCheck(email=raw.lower(), status="invalid_syntax", type=None)

    normalized = parsed.normalized.lower()
    domain = parsed.domain.lower()
    kind = email_type(parsed.local_part)

    if domain in DISPOSABLE_DOMAINS:
        return EmailCheck(email=normalized, status="disposable", type=kind)

    mx = await has_mx(domain)
    status = "unknown" if mx is None else ("valid_mx" if mx else "no_mx")
    return EmailCheck(email=normalized, status=status, type=kind)
