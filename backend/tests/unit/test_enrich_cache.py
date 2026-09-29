import asyncio
import time

import pytest

from app.core import cache as cache_mod
from app.services.enrichment import service


class SlowPipeline:
    def __init__(self):
        self.calls = 0

    async def run(self, domain, country=None):
        self.calls += 1
        await asyncio.sleep(0.2)
        return {"domain": domain, "data": {"emails": ["hi@" + domain]}}


@pytest.fixture
def fake_pipeline(monkeypatch):
    store = {}

    async def fake_get(key):
        return store.get(key)

    async def fake_set(key, value, ttl):
        store[key] = value

    monkeypatch.setattr(cache_mod, "cache_get_json", fake_get)
    monkeypatch.setattr(cache_mod, "cache_set_json", fake_set)

    pipe = SlowPipeline()
    monkeypatch.setattr(service, "get_pipeline", lambda: pipe)
    return pipe, store


async def test_second_run_comes_from_cache(fake_pipeline):
    pipe, store = fake_pipeline

    first = await service.enrich_domain("acme.com")
    started = time.perf_counter()
    second = await service.enrich_domain("acme.com")
    elapsed_ms = (time.perf_counter() - started) * 1000

    assert first == second
    assert pipe.calls == 1
    assert elapsed_ms < 20
    assert "enrich:acme.com" in store


async def test_force_bypasses_cache(fake_pipeline):
    pipe, _ = fake_pipeline

    await service.enrich_domain("acme.com")
    await service.enrich_domain("acme.com", force=True)
    assert pipe.calls == 2
