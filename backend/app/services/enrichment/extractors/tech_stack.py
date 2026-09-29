from app.services.enrichment.base import EnrichmentContext

# name -> (html fingerprints, is it a "modern" sales/marketing tool)
FINGERPRINTS: dict[str, tuple[tuple[str, ...], bool]] = {
    "WordPress": (("wp-content/", "wp-includes/"), False),
    "Wix": (("static.wixstatic.com", "wix.com"), False),
    "Squarespace": (("static1.squarespace.com", "squarespace.com"), False),
    "GoDaddy Builder": (("img1.wsimg.com",), False),
    "Weebly": (("weebly.com",), False),
    "Shopify": (("cdn.shopify.com",), True),
    "Webflow": (("webflow.com", "data-wf-page"), True),
    "Next.js": (("__NEXT_DATA__", "/_next/static"), True),
    "React": (("data-reactroot", "react-dom"), True),
    "HubSpot": (("js.hs-scripts.com", "js.hsforms.net"), True),
    "Salesforce Pardot": (("pi.pardot.com", "pardot.com/pd.js"), True),
    "Marketo": (("munchkin.marketo.net",), True),
    "Intercom": (("widget.intercom.io",), True),
    "Drift": (("js.driftt.com",), True),
    "Zendesk": (("static.zdassets.com",), True),
    "Calendly": (("assets.calendly.com",), True),
    "Google Analytics": (("gtag(", "google-analytics.com", "googletagmanager.com"), False),
    "Facebook Pixel": (("connect.facebook.net", "fbq("), False),
    "ServiceTitan": (("servicetitan.com",), True),
    "Housecall Pro": (("housecallpro.com",), True),
}


def detect_tech(html: str) -> list[str]:
    return [name for name, (needles, _) in FINGERPRINTS.items() if any(n in html for n in needles)]


class TechStackExtractor:
    name = "tech_stack"

    async def extract(self, ctx: EnrichmentContext) -> None:
        found: list[str] = []
        for page in ctx.iter_pages():
            for t in detect_tech(page.html):
                if t not in found:
                    found.append(t)
        ctx.result["tech_stack"] = found
        ctx.result["modern_stack"] = any(FINGERPRINTS[t][1] for t in found)
