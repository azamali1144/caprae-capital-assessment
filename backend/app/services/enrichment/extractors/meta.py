from app.services.enrichment.base import EnrichmentContext


def _meta(tree, *selectors: str) -> str | None:
    for sel in selectors:
        node = tree.css_first(sel)
        if node:
            val = (node.attributes.get("content") or "").strip()
            if val:
                return val
    return None


class MetaExtractor:
    name = "meta"

    async def extract(self, ctx: EnrichmentContext) -> None:
        home = ctx.home
        if not home:
            return
        tree = home.tree
        title_node = tree.css_first("title")
        title = title_node.text(strip=True) if title_node else None
        desc = _meta(
            tree,
            'meta[name="description"]',
            'meta[property="og:description"]',
            'meta[name="twitter:description"]',
        )
        ctx.result["title"] = title[:200] if title else None
        ctx.result["description"] = desc[:500] if desc else None
        ctx.result["site_name"] = _meta(tree, 'meta[property="og:site_name"]')
