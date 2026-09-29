import re

from app.services.enrichment.base import EnrichmentContext

HIRING_RE = re.compile(
    r"\b(we'?re hiring|we are hiring|now hiring|join our team|open positions|"
    r"current openings|job openings|apply now|career opportunities)\b",
    re.I,
)
CAREERS_PATH_RE = re.compile(r"(careers?|jobs|join|employment|work-with-us)", re.I)
# hosted job boards linked from the site
ATS_RE = re.compile(r"(greenhouse\.io|lever\.co|workable\.com|bamboohr\.com|indeed\.com/cmp)", re.I)


class HiringExtractor:
    name = "hiring"

    async def extract(self, ctx: EnrichmentContext) -> None:
        reasons = []
        if any(CAREERS_PATH_RE.search(p.path) for p in ctx.iter_pages() if p.path != "/"):
            reasons.append("careers page")
        m = HIRING_RE.search(ctx.all_text())
        if m:
            reasons.append(f'"{m.group(0)}"')
        if any(ATS_RE.search(p.html) for p in ctx.iter_pages()):
            reasons.append("job board link")

        ctx.result["hiring"] = bool(reasons)
        ctx.result["hiring_evidence"] = reasons
