import re
from datetime import date

from app.services.enrichment.base import EnrichmentContext

FOUNDED_RE = re.compile(
    r"\b(?:founded|established|est\.?|since|serving[\w\s,]{0,40}?since|in business since)"
    r"\s+(?:in\s+)?((?:19|20)\d{2})\b",
    re.I,
)
COPYRIGHT_RE = re.compile(
    r"(?:©|&copy;|\(c\)|copyright)\s*(?:\d{4}\s*[-–]\s*)?((?:19|20)\d{2})", re.I
)

FAMILY_RE = re.compile(
    r"\b(family[- ]owned|family[- ]run|family business|locally owned|owner[- ]operated|"
    r"second[- ]generation|third[- ]generation|husband and wife|father and son|mom and pop)\b",
    re.I,
)


def find_founded_year(text: str) -> int | None:
    this_year = date.today().year
    years = [int(y) for y in FOUNDED_RE.findall(text) if 1850 <= int(y) <= this_year]
    return min(years) if years else None


def find_copyright_year(text: str) -> int | None:
    this_year = date.today().year
    years = [int(y) for y in COPYRIGHT_RE.findall(text) if 1990 <= int(y) <= this_year + 1]
    # latest one wins - "© 2009-2024" means they touched the site in 2024
    return max(years) if years else None


class FoundedExtractor:
    """Founding year, copyright year (a proxy for how stale the site is) and family-owned vibes."""

    name = "founded"

    async def extract(self, ctx: EnrichmentContext) -> None:
        text = ctx.all_text()
        raw = "\n".join(p.html for p in ctx.iter_pages())

        ctx.result["founded_year"] = find_founded_year(text)
        ctx.result["copyright_year"] = find_copyright_year(text) or find_copyright_year(raw)

        m = FAMILY_RE.search(text)
        ctx.result["family_owned"] = bool(m)
        if m:
            ctx.result["family_owned_hint"] = m.group(0)
