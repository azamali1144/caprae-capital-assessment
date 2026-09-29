from app.core.cache import cached
from app.core.config import get_settings
from app.services.enrichment.extractors import default_extractors
from app.services.enrichment.fetcher import Fetcher
from app.services.enrichment.pipeline import EnrichmentPipeline

_pipeline: EnrichmentPipeline | None = None


def get_pipeline() -> EnrichmentPipeline:
    # one fetcher for the whole process so connections get reused
    global _pipeline
    if _pipeline is None:
        _pipeline = EnrichmentPipeline(Fetcher(), default_extractors())
    return _pipeline


async def close_pipeline() -> None:
    global _pipeline
    if _pipeline is not None:
        await _pipeline.fetcher.aclose()
        _pipeline = None


@cached("enrich", ttl=get_settings().enrich_cache_ttl_seconds)
async def enrich_domain(domain: str, country: str | None = None) -> dict:
    """Crawl + extract for one domain. Cached a week per domain; pass force=True to redo it."""
    return await get_pipeline().run(domain, country)
