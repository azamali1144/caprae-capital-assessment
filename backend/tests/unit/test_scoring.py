from datetime import date
from types import SimpleNamespace

import pytest

from app.services.scoring.engine import grade_for, score_company
from app.services.scoring.strategies import get_strategy

THIS_YEAR = date.today().year

ICP = {"industries": ["HVAC"], "countries": ["US"], "employee_min": 5, "employee_max": 100}


def make_company(**kw):
    base = dict(
        industry="HVAC",
        country="US",
        state="TX",
        employee_count=25,
        founded_year=None,
        copyright_year=None,
        website_status="alive",
        signals={"has_ssl": True},
    )
    return SimpleNamespace(**{**base, **kw})


OWNER = SimpleNamespace(
    full_name="John Smith",
    title="Owner",
    email="john@acme.com",
    email_status="valid_mx",
    email_type="personal",
    phone_e164="+15125550100",
    phone_valid=True,
    is_decision_maker=True,
)


def test_same_company_scores_differently_per_mode():
    # an old, sleepy, owner-run shop
    sleepy = make_company(
        founded_year=1995,
        copyright_year=THIS_YEAR - 6,
        signals={"has_ssl": True, "family_owned": True},
    )
    sales = score_company(sleepy, [OWNER], {**ICP, "mode": "sales"})
    acq = score_company(sleepy, [OWNER], {**ICP, "mode": "acquisition"})

    assert acq.score > sales.score
    assert acq.grade == "A"
    rules_hit = {b["rule"] for b in acq.breakdown}
    assert {"years_in_business", "stale_website", "family_owned"} <= rules_hit


def test_growing_company_is_better_for_sales():
    growing = make_company(signals={"has_ssl": True, "hiring": True, "modern_stack": True})
    sales = score_company(growing, [OWNER], {**ICP, "mode": "sales"})
    acq = score_company(growing, [OWNER], {**ICP, "mode": "acquisition"})
    assert sales.score > acq.score
    hiring = next(b for b in acq.breakdown if b["rule"] == "hiring")
    assert hiring["points"] < 0


def test_score_is_clamped():
    dead = make_company(
        industry="Bakery", country="FR", employee_count=None, website_status="dead", signals={}
    )
    role = SimpleNamespace(**{**vars(OWNER), "email_type": "role", "is_decision_maker": False})
    res = score_company(dead, [role], {**ICP, "mode": "sales"})
    assert res.score == 0
    assert res.grade == "D"
    assert any(b["points"] < 0 for b in res.breakdown)


@pytest.mark.parametrize(
    "score, grade",
    [(100, "A"), (80, "A"), (79, "B"), (60, "B"), (59, "C"), (40, "C"), (39, "D"), (0, "D")],
)
def test_grade_thresholds(score, grade):
    assert grade_for(score) == grade


def test_icp_weight_overrides():
    strat = get_strategy("sales", {"hiring": 25, "made_up_rule": 99})
    assert strat.weights["hiring"] == 25
    assert "made_up_rule" not in strat.weights
    # base strategy untouched
    assert get_strategy("sales").weights["hiring"] == 10


def test_breakdown_has_reasons_and_top_reasons():
    res = score_company(make_company(), [OWNER], {**ICP, "mode": "sales"})
    assert all(b["reason"] for b in res.breakdown)
    assert res.top_reasons[0] == "Industry 'HVAC' is in your ICP"
    assert res.breakdown == sorted(res.breakdown, key=lambda b: -b["points"])


def test_unknown_mode_falls_back_to_sales():
    assert get_strategy("whatever").mode == "sales"
