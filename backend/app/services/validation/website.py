from dataclasses import dataclass


@dataclass
class WebsiteHealth:
    status: str  # alive | dead | blocked | timeout
    has_ssl: bool
    http_status: int | None
    reason: str

    @property
    def healthy(self) -> bool:
        return self.status == "alive" and self.has_ssl


def classify_website(enrichment: dict) -> WebsiteHealth:
    """Turns the pipeline's fetch info into something the ui/scoring can use."""
    status = enrichment.get("website_status") or "dead"
    has_ssl = bool(enrichment.get("has_ssl"))
    http_status = enrichment.get("http_status")
    errors = enrichment.get("errors") or []

    if status == "alive":
        reason = "Site is up" + (" over HTTPS" if has_ssl else " but has no SSL")
    elif status == "blocked":
        reason = "Site blocked our crawler (robots.txt or 403) - we backed off"
    elif status == "timeout":
        reason = "Site didn't respond in time"
    else:
        home_err = next((e for e in errors if e.startswith("home:")), "")
        reason = (
            f"Site looks down ({home_err.removeprefix('home: ') or http_status or 'no response'})"
        )

    return WebsiteHealth(status=status, has_ssl=has_ssl, http_status=http_status, reason=reason)
