import re
from urllib.parse import unquote

from app.services.enrichment.base import EnrichmentContext

EMAIL_RE = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,24}", re.I)

# "john [at] acme [dot] com", "john(at)acme.com" etc
_AT_RE = re.compile(r"\s*[\[\(\{]\s*at\s*[\]\)\}]\s*|\s+at\s+(?=[a-z0-9-]+\s*[\[\(\{]\s*dot)", re.I)
_DOT_RE = re.compile(r"\s*[\[\(\{]\s*dot\s*[\]\)\}]\s*", re.I)

_JUNK_TLDS = ("png", "jpg", "jpeg", "gif", "svg", "webp", "css", "js")
_JUNK_DOMAINS = (
    "sentry.io",
    "sentry-next.wixpress.com",
    "wixpress.com",
    "example.com",
    "domain.com",
    "email.com",
    "yourdomain.com",
    "godaddy.com",
)
_JUNK_LOCAL = ("noreply", "no-reply", "donotreply", "user", "name", "email", "yourname")

# personal addresses on these are fine - small shops use gmail all the time
FREE_PROVIDERS = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "aol.com",
    "icloud.com",
    "live.com",
    "msn.com",
    "comcast.net",
    "att.net",
    "verizon.net",
    "protonmail.com",
}


def deobfuscate(text: str) -> str:
    return _DOT_RE.sub(".", _AT_RE.sub("@", text))


def _looks_real(email: str, company_domain: str) -> bool:
    local, _, host = email.partition("@")
    if host.rsplit(".", 1)[-1] in _JUNK_TLDS:  # logo@2x.png
        return False
    if any(host == d or host.endswith("." + d) for d in _JUNK_DOMAINS):
        return False
    if local in _JUNK_LOCAL or len(local) > 40:
        return False
    if re.fullmatch(r"[0-9a-f]{16,}", local):  # tracking hashes
        return False
    on_company = host == company_domain or host.endswith("." + company_domain)
    return on_company or host in FREE_PROVIDERS


def find_emails(html: str, text: str, company_domain: str) -> list[str]:
    found: list[str] = []

    for m in re.finditer(r'mailto:([^"\'?>\s]+)', html, re.I):
        found.append(unquote(m.group(1)))
    found.extend(EMAIL_RE.findall(deobfuscate(text)))

    out: list[str] = []
    for e in found:
        e = e.strip().strip(".").lower()
        if EMAIL_RE.fullmatch(e) and _looks_real(e, company_domain) and e not in out:
            out.append(e)
    return out


class EmailExtractor:
    name = "emails"

    async def extract(self, ctx: EnrichmentContext) -> None:
        emails: list[str] = []
        for page in ctx.iter_pages():
            for e in find_emails(page.html, page.text, ctx.domain):
                if e not in emails:
                    emails.append(e)
        ctx.result["emails"] = emails[:20]
