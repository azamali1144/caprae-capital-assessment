import asyncio
import logging
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from urllib.parse import urljoin, urlsplit

from app.services.enrichment.base import EnrichmentContext, Extractor, Page
from app.services.enrichment.fetcher import Fetcher, FetchResult
from app.services.normalization.domain import canonical_domain

log = logging.getLogger(__name__)

MAX_SUBPAGES = 4
SUBPAGE_RE = re.compile(
    r"(about|contact|team|staff|people|leadership|careers|jobs|join|our-story|who-we-are|history)",
    re.I,
)


def discover_links(page: Page, domain: str) -> list[str]:
    """Internal links that look like about/contact/team/careers pages, best first."""
    found: dict[str, int] = {}
    for a in page.tree.css("a[href]"):
        href = (a.attributes.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        url = urljoin(page.url, href).split("#")[0]
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or canonical_domain(parts.netloc) != domain:
            continue
        path = parts.path.rstrip("/") or "/"
        if path == "/" or path.lower().endswith((".pdf", ".jpg", ".png", ".zip")):
            continue
        m = SUBPAGE_RE.search(path) or SUBPAGE_RE.search(a.text(strip=True))
        if m and url not in found:
            # shorter paths are usually the "real" page (/about vs /blog/about-our-new-van)
            found[url] = path.count("/")
    return sorted(found, key=found.get)[:MAX_SUBPAGES]


def _site_status(res: FetchResult) -> str:
    if res.ok:
        return "alive"
    if res.error == "timeout":
        return "timeout"
    if res.error == "blocked_robots" or res.status in (401, 403, 429):
        return "blocked"
    return "dead"


class EnrichmentPipeline:
    """fetch homepage -> find a few subpages -> fetch them -> run extractors in order."""

    def __init__(self, fetcher: Fetcher, extractors: Sequence[Extractor]):
        self.fetcher = fetcher
        self.extractors = list(extractors)

    async def _fetch_home(self, domain: str) -> FetchResult:
        res = None
        for url in (f"https://{domain}/", f"https://www.{domain}/", f"http://{domain}/"):
            res = await self.fetcher.fetch(url)
            if res.ok or res.error in ("blocked_robots",) or res.status:
                return res
        return res

    async def run(self, domain: str, country: str | None = None) -> dict:
        ctx = EnrichmentContext(domain=domain, country=country)

        home = await self._fetch_home(domain)
        ctx.site_status = _site_status(home)
        ctx.http_status = home.status
        ctx.has_ssl = home.ok and home.is_https

        if home.ok:
            ctx.base_url = home.final_url or home.url
            ctx.pages["/"] = Page(path="/", url=ctx.base_url, html=home.html)

            links = discover_links(ctx.pages["/"], domain)
            subs = await asyncio.gather(*(self.fetcher.fetch(u) for u in links))
            for url, res in zip(links, subs, strict=True):
                if res.ok:
                    path = urlsplit(url).path.rstrip("/") or "/"
                    ctx.pages[path] = Page(path=path, url=res.final_url or url, html=res.html)
                elif res.error:
                    ctx.errors.append(f"{url}: {res.error}")

            for ex in self.extractors:
                try:
                    await ex.extract(ctx)
                except Exception as exc:  # one bad extractor shouldn't sink the lead
                    log.warning("extractor %s failed on %s: %s", ex.name, domain, exc)
                    ctx.errors.append(f"{ex.name}: {exc}")
        elif home.error:
            ctx.errors.append(f"home: {home.error}")

        return {
            "domain": domain,
            "website_status": ctx.site_status,
            "has_ssl": ctx.has_ssl,
            "http_status": ctx.http_status,
            "final_url": ctx.base_url,
            "pages_crawled": sorted(ctx.pages),
            "data": ctx.result,
            "errors": ctx.errors,
            "enriched_at": datetime.now(UTC).isoformat(),
        }
