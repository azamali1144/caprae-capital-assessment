import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from app.services.scoring.rules import RULES
from app.services.scoring.strategies import get_strategy

log = logging.getLogger(__name__)

GRADES = ((80, "A"), (60, "B"), (40, "C"))


def grade_for(score: int) -> str:
    return next((g for cutoff, g in GRADES if score >= cutoff), "D")


@dataclass
class ScoreResult:
    score: int
    grade: str
    mode: str
    breakdown: list[dict] = field(default_factory=list)

    @property
    def top_reasons(self) -> list[str]:
        positives = sorted(
            (b for b in self.breakdown if b["points"] > 0), key=lambda b: -b["points"]
        )
        return [b["reason"] for b in positives[:3]]


def score_company(
    company: Any, contacts: Sequence[Any], icp_rules: dict | None = None
) -> ScoreResult:
    """Run every rule the active strategy cares about and add up the points.

    icp_rules is the IcpProfile.rules dict plus "mode"; weights in it override the defaults.
    """
    icp = icp_rules or {}
    strategy = get_strategy(icp.get("mode"), icp.get("weights"))

    breakdown: list[dict] = []
    for name, points in strategy.weights.items():
        if not points:
            continue
        try:
            reason = RULES[name](company, contacts, icp)
        except Exception as exc:  # a broken rule shouldn't zero the whole score
            log.warning("rule %s failed: %s", name, exc)
            continue
        if reason:
            breakdown.append({"rule": name, "points": points, "reason": reason})

    total = max(0, min(100, sum(b["points"] for b in breakdown)))
    breakdown.sort(key=lambda b: -b["points"])
    return ScoreResult(score=total, grade=grade_for(total), mode=strategy.mode, breakdown=breakdown)
