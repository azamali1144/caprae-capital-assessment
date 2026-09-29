from pathlib import Path

import pytest

from app.services.enrichment.base import EnrichmentContext, Page
from app.services.enrichment.extractors.emails import EmailExtractor, deobfuscate, find_emails
from app.services.enrichment.extractors.phones import PhoneExtractor, region_for
from app.services.enrichment.extractors.socials import SocialExtractor, find_socials

FIXTURES = Path(__file__).parent.parent / "fixtures"


def load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture
def contact_ctx() -> EnrichmentContext:
    ctx = EnrichmentContext(domain="acmehvac.com", country="US")
    ctx.pages["/contact"] = Page(
        path="/contact", url="https://acmehvac.com/contact", html=load("contact_page.html")
    )
    return ctx


# --- emails ---------------------------------------------------------------


async def test_emails_from_contact_page(contact_ctx):
    await EmailExtractor().extract(contact_ctx)
    emails = contact_ctx.result["emails"]
    assert emails[0] == "john@acmehvac.com"  # mailto first
    assert set(emails) == {
        "john@acmehvac.com",
        "office@acmehvac.com",
        "billing@acmehvac.com",
        "mike.acmehvac@gmail.com",
    }


def test_deobfuscate():
    assert deobfuscate("jane [at] acme [dot] com") == "jane@acme.com"
    assert deobfuscate("jane(at)acme(dot)co(dot)uk") == "jane@acme.co.uk"


@pytest.mark.parametrize(
    "junk",
    [
        "logo@2x.png",
        "abc123@o12345.ingest.sentry.io",
        "noreply@acme.com",
        "you@example.com",
        "someone@otherbusiness.com",
        "test@gmail.com",
        "john.doe@acme.com",
        "youremail@acme.com",
    ],
)
def test_junk_emails_filtered(junk):
    assert find_emails("", f"contact {junk} today", "acme.com") == []


# --- phones ---------------------------------------------------------------


async def test_phones_from_contact_page(contact_ctx):
    await PhoneExtractor().extract(contact_ctx)
    assert contact_ctx.result["phones"] == ["+15125550100", "+15125550199"]


@pytest.mark.parametrize(
    "country, region",
    [
        (None, "US"),
        ("US", "US"),
        ("gb", "GB"),
        ("UK", "GB"),
        ("United Kingdom", "GB"),
        ("Narnia", "US"),
    ],
)
def test_region_for(country, region):
    assert region_for(country) == region


async def test_uk_number_uses_country_hint():
    ctx = EnrichmentContext(domain="acme.co.uk", country="UK")
    ctx.pages["/"] = Page(path="/", url="https://acme.co.uk/", html="<p>Ring 020 7123 4567</p>")
    await PhoneExtractor().extract(ctx)
    assert ctx.result["phones"] == ["+442071234567"]


# --- socials --------------------------------------------------------------


async def test_socials_from_contact_page(contact_ctx):
    await SocialExtractor().extract(contact_ctx)
    assert contact_ctx.result["socials"] == {
        "linkedin": "https://www.linkedin.com/company/acme-hvac",
        "facebook": "https://www.facebook.com/AcmeHVACAustin",
        "instagram": "https://instagram.com/acmehvac",
        "x": "https://x.com/acmehvac",
        "youtube": "https://www.youtube.com/@acmehvac",
    }


def test_personal_linkedin_is_ignored():
    assert find_socials(["https://www.linkedin.com/in/john-smith"]) == {}
