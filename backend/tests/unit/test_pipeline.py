import httpx
import pytest
import respx

from app.services.enrichment import fetcher as fetcher_mod
from app.services.enrichment.base import EnrichmentContext, Page
from app.services.enrichment.fetcher import Fetcher
from app.services.enrichment.pipeline import EnrichmentPipeline, discover_links

HOME = """
<html><body>
  <a href="/about-us">About</a>
  <a href="https://www.acme.com/contact/">Contact</a>
  <a href="/services">Services</a>
  <a href="/team">Meet the team</a>
  <a href="/careers">Careers</a>
  <a href="/blog/about-our-new-van">blog</a>
  <a href="https://facebook.com/acme">fb</a>
  <a href="mailto:hi@acme.com">mail</a>
  <a href="/brochure-about.pdf">pdf</a>
</body></html>
"""


@pytest.fixture(autouse=True)
def no_redis(monkeypatch):
    async def fake_get(key):
        return None

    async def fake_set(key, value, ttl):
        return None

    monkeypatch.setattr(fetcher_mod, "cache_get_json", fake_get)
    monkeypatch.setattr(fetcher_mod, "cache_set_json", fake_set)


class Recorder:
    name = "recorder"

    async def extract(self, ctx: EnrichmentContext) -> None:
        ctx.result["paths"] = sorted(ctx.pages)


class Broken:
    name = "broken"

    async def extract(self, ctx: EnrichmentContext) -> None:
        raise RuntimeError("boom")


def test_discover_links_keeps_internal_about_pages_only():
    page = Page(path="/", url="https://acme.com/", html=HOME)
    links = discover_links(page, "acme.com")
    assert len(links) == 4
    assert "https://acme.com/about-us" in links
    assert "https://www.acme.com/contact/" in links
    assert not any("facebook" in u or u.endswith(".pdf") for u in links)
    # the deep blog link loses out to the short real pages
    assert "https://acme.com/blog/about-our-new-van" not in links


@respx.mock
async def test_pipeline_crawls_subpages_and_survives_broken_extractor():
    respx.get(url__regex=r".*/robots\.txt").respond(404)
    respx.get("https://acme.com/").respond(200, html=HOME)
    for path in ("/about-us", "/team", "/careers"):
        respx.get(f"https://acme.com{path}").respond(200, html=f"<p>{path}</p>")
    respx.get("https://www.acme.com/contact/").respond(500)

    async with Fetcher(host_delay=0) as f:
        out = await EnrichmentPipeline(f, [Broken(), Recorder()]).run("acme.com")

    assert out["website_status"] == "alive"
    assert out["has_ssl"] is True
    assert out["data"]["paths"] == ["/", "/about-us", "/careers", "/team"]
    assert any(e.startswith("broken:") for e in out["errors"])
    assert any("contact" in e for e in out["errors"])


@respx.mock
async def test_dead_site():
    respx.get(url__regex=r".*/robots\.txt").mock(side_effect=httpx.ConnectError("nope"))
    respx.get(url__regex=r".*deadco\.com/$").mock(side_effect=httpx.ConnectError("nope"))

    async with Fetcher(host_delay=0) as f:
        out = await EnrichmentPipeline(f, [Recorder()]).run("deadco.com")

    assert out["website_status"] == "dead"
    assert out["data"] == {}
    assert out["pages_crawled"] == []
