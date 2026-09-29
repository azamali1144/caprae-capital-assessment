import re
from urllib.parse import unquote

import phonenumbers

from app.services.enrichment.base import EnrichmentContext

_COUNTRY_ALIASES = {
    "usa": "US",
    "united states": "US",
    "united states of america": "US",
    "uk": "GB",
    "united kingdom": "GB",
    "england": "GB",
    "canada": "CA",
    "australia": "AU",
    "pakistan": "PK",
    "india": "IN",
    "germany": "DE",
}


def region_for(country: str | None) -> str:
    if not country:
        return "US"  # most saasquatch leads are US
    c = country.strip()
    if c.lower() in _COUNTRY_ALIASES:  # check first - "UK" isn't a real iso code
        return _COUNTRY_ALIASES[c.lower()]
    if len(c) == 2 and c.isalpha():
        return c.upper()
    return "US"


def _to_e164(num: phonenumbers.PhoneNumber) -> str:
    return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)


def find_phones(html: str, text: str, region: str) -> list[str]:
    out: list[str] = []

    # tel: links are the most reliable, check those first
    for m in re.finditer(r'tel:([^"\'>]+)', html, re.I):
        try:
            num = phonenumbers.parse(unquote(m.group(1)), region)
        except phonenumbers.NumberParseException:
            continue
        if phonenumbers.is_valid_number(num) and _to_e164(num) not in out:
            out.append(_to_e164(num))

    for match in phonenumbers.PhoneNumberMatcher(
        text, region, leniency=phonenumbers.Leniency.VALID
    ):
        e164 = _to_e164(match.number)
        if e164 not in out:
            out.append(e164)
    return out


class PhoneExtractor:
    name = "phones"

    async def extract(self, ctx: EnrichmentContext) -> None:
        region = region_for(ctx.country)
        phones: list[str] = []
        for page in ctx.iter_pages():
            for p in find_phones(page.html, page.text, region):
                if p not in phones:
                    phones.append(p)
        ctx.result["phones"] = phones[:10]
