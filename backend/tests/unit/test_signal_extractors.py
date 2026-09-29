from pathlib import Path

import pytest

from app.services.enrichment.base import EnrichmentContext, Page
from app.services.enrichment.extractors.founded import (
    FoundedExtractor,
    find_copyright_year,
    find_founded_year,
)
from app.services.enrichment.extractors.hiring import HiringExtractor
from app.services.enrichment.extractors.meta import MetaExtractor
from app.services.enrichment.extractors.people import PeopleExtractor, find_people
from app.services.enrichment.extractors.tech_stack import TechStackExtractor, detect_tech

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def about_ctx() -> EnrichmentContext:
    html = (FIXTURES / "about_page.html").read_text(encoding="utf-8")
    ctx = EnrichmentContext(domain="acmehvac.com")
    ctx.pages["/"] = Page(path="/", url="https://acmehvac.com/", html=html)
    ctx.pages["/about"] = Page(path="/about", url="https://acmehvac.com/about", html=html)
    return ctx


async def test_meta(about_ctx):
    await MetaExtractor().extract(about_ctx)
    assert about_ctx.result["title"].startswith("About Us - Acme HVAC")
    assert "since 1998" in about_ctx.result["description"]
    assert about_ctx.result["site_name"] == "Acme HVAC"


async def test_founded_copyright_and_family(about_ctx):
    await FoundedExtractor().extract(about_ctx)
    assert about_ctx.result["founded_year"] == 1998
    assert about_ctx.result["copyright_year"] == 2019
    assert about_ctx.result["family_owned"] is True


@pytest.mark.parametrize(
    "text, year",
    [
        ("Established in 1987", 1987),
        ("Proudly serving the Denver area since 1975.", 1975),
        ("Est. 2004", 2004),
        ("We opened our doors to 3000 customers", None),
        ("Founded in 2999", None),
    ],
)
def test_find_founded_year(text, year):
    assert find_founded_year(text) == year


def test_copyright_takes_latest_year():
    assert find_copyright_year("© 2012 - 2023 Acme") == 2023
    assert find_copyright_year("Copyright 2016 Acme") == 2016
    assert find_copyright_year("no footer here") is None


async def test_hiring(about_ctx):
    await HiringExtractor().extract(about_ctx)
    assert about_ctx.result["hiring"] is True
    assert about_ctx.result["hiring_evidence"]


async def test_not_hiring():
    ctx = EnrichmentContext(domain="quiet.com")
    ctx.pages["/"] = Page(path="/", url="https://quiet.com/", html="<p>We fix boilers.</p>")
    await HiringExtractor().extract(ctx)
    assert ctx.result["hiring"] is False


async def test_tech_stack(about_ctx):
    await TechStackExtractor().extract(about_ctx)
    assert about_ctx.result["tech_stack"] == ["WordPress", "Google Analytics"]
    assert about_ctx.result["modern_stack"] is False


def test_modern_tech_detected():
    html = '<script src="//js.hs-scripts.com/123.js"></script><div id="__NEXT_DATA__">'
    assert set(detect_tech(html)) == {"HubSpot", "Next.js"}


async def test_people(about_ctx):
    await PeopleExtractor().extract(about_ctx)
    people = {p["full_name"]: p for p in about_ctx.result["people"]}
    assert people["John Smith"]["title"] == "Owner"
    assert people["John Smith"]["is_decision_maker"] is True
    assert people["Robert Brown"]["title"] == "Founder & CEO"
    assert people["Maria Garcia"]["is_decision_maker"] is False
    # decision makers come first
    assert about_ctx.result["people"][0]["is_decision_maker"] is True


def test_people_ignores_nav_words():
    assert find_people("Contact Us, Owner") == []


def test_people_ignores_ui_labels():
    # seen on a real site: a search widget label sitting next to a title
    assert find_people("Search Extended - Executive Director") == []
    assert find_people("Executive Director: Search Extended") == []


@pytest.mark.parametrize(
    "text",
    [
        "Dale Smith, LEED AP - Principal",
        "With Akron - Partner",
        "You Can Rely - Partner",
        "Estimating Manager - President",
    ],
)
def test_people_rejects_marketing_copy(text):
    names = [p["full_name"] for p in find_people(text)]
    assert not any(
        n in ("LEED AP", "With Akron", "You Can Rely", "Estimating Manager") for n in names
    )


def test_real_names_still_work():
    people = find_people("John H. Langer - President")
    assert people[0]["full_name"] == "John H. Langer"
    assert people[0]["is_decision_maker"]
