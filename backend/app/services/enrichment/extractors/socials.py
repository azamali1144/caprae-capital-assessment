import re

from app.services.enrichment.base import EnrichmentContext

# only company pages - not share buttons or someone's personal profile
PATTERNS = {
    "linkedin": re.compile(r"https?://([a-z]{2,3}\.)?linkedin\.com/company/[\w\-%.]+", re.I),
    "facebook": re.compile(
        r"https?://(www\.|m\.)?facebook\.com/(?!sharer|share|dialog|plugins|tr\b)[\w\-.]+", re.I
    ),
    "instagram": re.compile(r"https?://(www\.)?instagram\.com/(?!p/|explore)[\w\-.]+", re.I),
    "x": re.compile(r"https?://(www\.)?(twitter|x)\.com/(?!intent|share|home)[\w]+", re.I),
    "youtube": re.compile(r"https?://(www\.)?youtube\.com/(channel/|c/|user/|@)[\w\-.]+", re.I),
}


def find_socials(hrefs: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for href in hrefs:
        for net, pattern in PATTERNS.items():
            if net in out:
                continue
            m = pattern.match(href.strip())
            if m:
                out[net] = m.group(0).rstrip("/.")
    return out


class SocialExtractor:
    name = "socials"

    async def extract(self, ctx: EnrichmentContext) -> None:
        hrefs = [
            a.attributes.get("href") or ""
            for page in ctx.iter_pages()
            for a in page.tree.css("a[href]")
        ]
        ctx.result["socials"] = find_socials(hrefs)
