import httpx
import pytest
import respx

from app.services.enrichment import fetcher as fetcher_mod
from app.services.enrichment.fetcher import Fetcher

HTML = "<html><body><h1>Acme HVAC</h1></body></html>"


@pytest.fixture(autouse=True)
def no_redis(monkeypatch):
    # keep these tests off the real redis
    store = {}

    async def fake_get(key):
        return store.get(key)

    async def fake_set(key, value, ttl):
        store[key] = value

    monkeypatch.setattr(fetcher_mod, "cache_get_json", fake_get)
    monkeypatch.setattr(fetcher_mod, "cache_set_json", fake_set)


@pytest.fixture
async def fetcher():
    f = Fetcher(host_delay=0)
    yield f
    await f.aclose()


@respx.mock
async def test_fetch_ok(fetcher):
    respx.get("https://acme.com/robots.txt").respond(404)
    respx.get("https://acme.com/").respond(200, html=HTML)

    res = await fetcher.fetch("https://acme.com/")
    assert res.ok
    assert res.status == 200
    assert "Acme HVAC" in res.html
    assert res.is_https


@respx.mock
async def test_fetch_404(fetcher):
    respx.get("https://acme.com/robots.txt").respond(404)
    respx.get("https://acme.com/missing").respond(404, html="nope")

    res = await fetcher.fetch("https://acme.com/missing")
    assert not res.ok
    assert res.error == "http_404"


@respx.mock
async def test_timeout_is_retried_then_reported(fetcher):
    respx.get("https://slow.com/robots.txt").respond(404)
    route = respx.get("https://slow.com/").mock(side_effect=httpx.ReadTimeout("slow"))

    res = await fetcher.fetch("https://slow.com/")
    assert res.error == "timeout"
    assert route.call_count == 2


@respx.mock
async def test_5xx_retry_recovers(fetcher):
    respx.get("https://flaky.com/robots.txt").respond(404)
    respx.get("https://flaky.com/").mock(
        side_effect=[httpx.Response(503), httpx.Response(200, html=HTML)]
    )

    res = await fetcher.fetch("https://flaky.com/")
    assert res.ok


@respx.mock
async def test_robots_disallow(fetcher):
    respx.get("https://private.com/robots.txt").respond(200, text="User-agent: *\nDisallow: /")
    page = respx.get("https://private.com/").respond(200, html=HTML)

    res = await fetcher.fetch("https://private.com/")
    assert res.error == "blocked_robots"
    assert not page.called


@respx.mock
async def test_non_html_is_skipped(fetcher):
    respx.get("https://acme.com/robots.txt").respond(404)
    respx.get("https://acme.com/brochure.pdf").respond(
        200, content=b"%PDF", headers={"content-type": "application/pdf"}
    )

    res = await fetcher.fetch("https://acme.com/brochure.pdf")
    assert res.error == "not_html"
