"""import -> enrich (faked) -> list -> patch -> export, against a real postgres.

Needs the docker compose db (or the CI service). Uses its own database so it
never touches your dev data. Redis isn't needed - the cache fails open.
"""

import csv
import io
import os
import uuid

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

BASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://leadlens:leadlens@localhost:5432")
TEST_DB = f"leadlens_test_{uuid.uuid4().hex[:8]}"

FAKE_SITES = {
    "acmehvac.com": {
        "website_status": "alive",
        "has_ssl": True,
        "http_status": 200,
        "final_url": "https://acmehvac.com/",
        "pages_crawled": ["/", "/about"],
        "errors": [],
        "data": {
            "description": "Family-owned HVAC in Austin since 1998.",
            "founded_year": 1998,
            "copyright_year": 2018,
            "family_owned": True,
            "emails": ["john@acmehvac.com", "info@acmehvac.com"],
            "phones": ["+15125550100"],
            "people": [{"full_name": "John Smith", "title": "Owner", "is_decision_maker": True}],
            "tech_stack": ["WordPress"],
            "socials": {},
        },
    },
    "deadco.com": {
        "website_status": "dead",
        "has_ssl": False,
        "errors": ["home: connect_error"],
        "data": {},
    },
}

CSV = (
    b"Company Name,Website,Industry,Country,Employees\n"
    b"Acme HVAC,https://www.acmehvac.com,HVAC,US,25\n"
    b"Acme HVAC LLC,acmehvac.com,HVAC,US,25\n"
    b"Dead Co,deadco.com,HVAC,US,10\n"
    b"Bakery,bakery.com,Bakery,FR,300\n"
)


async def _admin(sql: str) -> None:
    conn = await asyncpg.connect(BASE_URL.replace("+asyncpg", "") + "/postgres")
    try:
        await conn.execute(sql)
    finally:
        await conn.close()


@pytest.fixture
async def client():
    try:
        await _admin(f"CREATE DATABASE {TEST_DB}")
    except OSError:
        pytest.skip("postgres isn't running - start it with docker compose up -d")

    from app.core import db as db_mod
    from app.main import app
    from app.models import Base
    from app.services.jobs import enrich_job

    engine = create_async_engine(f"{BASE_URL}/{TEST_DB}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # point the app + background jobs at the throwaway db
    session_local = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    db_mod.SessionLocal = session_local
    enrich_job.SessionLocal = session_local

    async def override_session():
        async with session_local() as s:
            yield s

    app.dependency_overrides[db_mod.get_session] = override_session

    # no real crawling or dns in tests
    async def fake_enrich(domain, country=None, force=False):
        return FAKE_SITES.get(domain, {"website_status": "dead", "has_ssl": False, "data": {}})

    async def fake_mx(domain):
        return domain != "deadco.com"

    mp = pytest.MonkeyPatch()
    mp.setattr(enrich_job, "enrich_domain", fake_enrich)
    mp.setattr("app.services.validation.email.has_mx", fake_mx)
    mp.setattr("app.services.export.csv_exporter.SessionLocal", session_local)

    # stats caches in redis - skip that so numbers are always fresh here
    async def no_cache(*_args, **_kw):
        return None

    mp.setattr("app.api.v1.stats.cache_get_json", no_cache)
    mp.setattr("app.api.v1.stats.cache_set_json", no_cache)

    from app.services.scoring.service import seed_default_profiles

    async with session_local() as s:
        await seed_default_profiles(s)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    mp.undo()
    app.dependency_overrides.clear()
    await engine.dispose()
    await _admin(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)")


async def test_import_to_export_flow(client: AsyncClient):
    # 1. import - the two acme rows are the same company
    r = await client.post("/api/v1/imports/csv", files={"file": ("leads.csv", CSV, "text/csv")})
    assert r.status_code == 201, r.text
    job_id = r.json()["job_id"]

    # background task has run by the time the response is done (asgi transport)
    job = (await client.get(f"/api/v1/imports/{job_id}")).json()
    assert job["status"] == "completed"
    assert job["duplicates_removed"] == 1
    assert job["processed"] == 3

    # 2. list - acme should be on top with an owner + verified email
    leads = (await client.get("/api/v1/leads")).json()
    assert leads["total"] == 3
    top = leads["items"][0]
    assert top["domain"] == "acmehvac.com"
    assert top["best_contact"]["full_name"] == "John Smith"
    assert top["best_contact"]["email_status"] == "valid_mx"
    assert top["top_reasons"]

    # dead site gets penalised
    dead = next(i for i in leads["items"] if i["domain"] == "deadco.com")
    assert dead["website_status"] == "dead"
    assert dead["score"] < top["score"]

    # 3. filters
    only_a_b = (await client.get("/api/v1/leads", params={"grade": ["A", "B"]})).json()
    assert all(i["grade"] in ("A", "B") for i in only_a_b["items"])
    verified = (await client.get("/api/v1/leads", params={"email_status": "valid_mx"})).json()
    assert {i["domain"] for i in verified["items"]} == {"acmehvac.com"}

    # 4. detail + patch
    detail = (await client.get(f"/api/v1/leads/{top['id']}")).json()
    assert any(b["rule"] == "decision_maker" for b in detail["score_breakdown"])
    r = await client.patch(
        f"/api/v1/leads/{top['id']}", json={"stage": "qualified", "notes": "hot"}
    )
    assert r.json()["stage"] == "qualified"

    # 5. switching to the acquisition lens re-scores everything
    profiles = (await client.get("/api/v1/icp-profiles")).json()
    acq = next(p for p in profiles if p["mode"] == "acquisition")
    r = await client.post(f"/api/v1/icp-profiles/{acq['id']}/activate")
    assert r.json()["rescored"] == 3
    acme = (await client.get(f"/api/v1/leads/{top['id']}")).json()
    assert {"years_in_business", "stale_website", "family_owned"} <= {
        b["rule"] for b in acme["score_breakdown"]
    }

    # 6. export matches the filters
    r = await client.get("/api/v1/exports/csv", params={"stage": "qualified"})
    assert r.status_code == 200
    rows = list(csv.DictReader(io.StringIO(r.text.lstrip("﻿"))))
    assert len(rows) == 1
    assert rows[0]["Domain"] == "acmehvac.com"
    assert rows[0]["Contact Name"] == "John Smith"

    # 7. stats add up
    stats = (await client.get("/api/v1/stats")).json()
    assert stats["total_leads"] == 3
    assert stats["duplicates_removed_total"] == 1
