import re
from urllib.parse import urlsplit

import tldextract

# use the bundled suffix list, no network calls at runtime
_extract = tldextract.TLDExtract(suffix_list_urls=())

_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.I)


def canonical_domain(value: str | None) -> str | None:
    """'https://www.Acme-HVAC.com/about?x=1' -> 'acme-hvac.com'.

    Also handles bare hosts, emails / mailto:, and strips subdomains.
    Returns None when there's no usable registrable domain.
    """
    if not value:
        return None
    raw = value.strip().lower()
    if not raw:
        return None

    if raw.startswith("mailto:"):
        raw = raw[len("mailto:") :]
    if "@" in raw and "/" not in raw:
        raw = raw.rsplit("@", 1)[1]

    if not _SCHEME_RE.match(raw):
        raw = "http://" + raw

    try:
        host = urlsplit(raw).hostname or ""
    except ValueError:
        return None

    host = host.strip(".")
    if not host or " " in host:
        return None

    parts = _extract(host)
    if not parts.domain or not parts.suffix:
        return None
    return f"{parts.domain}.{parts.suffix}"


def website_url(domain: str | None) -> str | None:
    return f"https://{domain}" if domain else None
