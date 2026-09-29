from dataclasses import dataclass, field


@dataclass
class ScoringStrategy:
    mode: str
    label: str
    weights: dict[str, int] = field(default_factory=dict)

    def with_overrides(self, overrides: dict | None) -> "ScoringStrategy":
        if not overrides:
            return self
        merged = {**self.weights}
        for rule, pts in overrides.items():
            if rule in merged or rule in ALL_RULES:
                merged[rule] = int(pts)
        return ScoringStrategy(mode=self.mode, label=self.label, weights=merged)


# selling *to* the company: reachable, growing, spending on tools
SALES = ScoringStrategy(
    mode="sales",
    label="Sales",
    weights={
        "industry_match": 20,
        "location_match": 10,
        "size_fit": 10,
        "personal_email_valid": 15,
        "decision_maker": 10,
        "valid_phone": 5,
        "site_healthy": 5,
        "hiring": 10,
        "modern_stack": 5,
        "years_in_business": 0,
        "stale_website": -5,
        "family_owned": 0,
        "low_confidence_merge": -5,
        "role_only_emails": -5,
        "site_dead": -20,
    },
)

# buying the company: established, owner-run, under-invested (= upside after the deal)
ACQUISITION = ScoringStrategy(
    mode="acquisition",
    label="Acquisition fit",
    weights={
        "industry_match": 20,
        "location_match": 10,
        "size_fit": 15,
        "personal_email_valid": 10,
        "decision_maker": 15,
        "valid_phone": 5,
        "site_healthy": 5,
        "hiring": -5,
        "modern_stack": 0,
        "years_in_business": 10,
        "stale_website": 5,
        "family_owned": 5,
        "low_confidence_merge": -5,
        "role_only_emails": -5,
        "site_dead": -20,
    },
)

STRATEGIES = {s.mode: s for s in (SALES, ACQUISITION)}
ALL_RULES = set(SALES.weights) | set(ACQUISITION.weights)


def get_strategy(mode: str | None, overrides: dict | None = None) -> ScoringStrategy:
    base = STRATEGIES.get((mode or "sales").lower(), SALES)
    return base.with_overrides(overrides)
