"""
goal_engine.py — Goal feasibility scoring and corpus gap analysis.

Used by the Financial Plan Generator and Next Best Action engine to evaluate
whether a client's current savings trajectory meets their stated goals.

Dependencies: indian_constants.py, sip_calculator.py (Tier 1)
Consumed by: GetGoalProgressTool, FinancialPlanAgent, NextBestActionEngine
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from skills.backend.financial.sip_calculator import (
    sip_future_value,
    lumpsum_future_value,
    required_monthly_sip,
    stepup_sip_future_value,
    inflation_adjusted_value,
)
from skills.backend.financial.indian_constants import (
    DEFAULT_EQUITY_RETURN,
    DEFAULT_DEBT_RETURN,
    DEFAULT_INFLATION_RATE,
    DEFAULT_STEP_UP_RATE,
)


@dataclass
class GoalAssessment:
    """Assessment of a single financial goal."""
    goal_type: str
    target_amount: float           # Goal corpus in today's ₹
    target_date: date
    current_corpus: float          # Money already saved for this goal
    monthly_sip: float             # Current monthly SIP towards this goal
    years_remaining: int

    # Calculated fields
    inflation_adjusted_target: float = 0.0
    projected_corpus: float = 0.0
    shortfall: float = 0.0
    additional_sip_needed: float = 0.0
    feasibility_score: int = 0     # 0-100
    status: str = ""               # "on_track" | "slightly_off" | "needs_action" | "at_risk"
    recommendation: str = ""

    def __post_init__(self):
        self._calculate()

    def _calculate(self):
        # Inflate target amount to future value
        self.inflation_adjusted_target = inflation_adjusted_value(
            self.target_amount, self.years_remaining, DEFAULT_INFLATION_RATE
        ) if self.years_remaining > 0 else self.target_amount

        # Use nominal target amount for projection (inflation is in target)
        nominal_target = self.target_amount * (1 + DEFAULT_INFLATION_RATE) ** self.years_remaining

        # Project current corpus growth
        existing_corpus_growth = lumpsum_future_value(
            self.current_corpus, self.years_remaining, DEFAULT_EQUITY_RETURN
        ) if self.current_corpus > 0 else 0.0

        # Project SIP growth
        sip_growth = sip_future_value(
            self.monthly_sip, self.years_remaining, DEFAULT_EQUITY_RETURN
        ) if self.monthly_sip > 0 else 0.0

        self.projected_corpus = existing_corpus_growth + sip_growth
        self.shortfall = max(0, nominal_target - self.projected_corpus)

        # Calculate additional SIP needed
        if self.shortfall > 0 and self.years_remaining > 0:
            self.additional_sip_needed = required_monthly_sip(
                self.shortfall, self.years_remaining, DEFAULT_EQUITY_RETURN
            )

        # Score: 100 = meets goal, 0 = no savings at all
        if nominal_target > 0:
            ratio = self.projected_corpus / nominal_target
            self.feasibility_score = min(100, int(ratio * 100))

        # Status classification
        if self.feasibility_score >= 90:
            self.status = "on_track"
            self.recommendation = f"You are on track for your {self.goal_type} goal! ✓"
        elif self.feasibility_score >= 70:
            self.status = "slightly_off"
            self.recommendation = (
                f"Slightly behind on {self.goal_type}. "
                f"Increase SIP by ₹{self.additional_sip_needed:,.0f}/month to close the gap."
            )
        elif self.feasibility_score >= 40:
            self.status = "needs_action"
            self.recommendation = (
                f"Action needed for {self.goal_type} goal. "
                f"Shortfall of ₹{self.shortfall/100_000:.1f}L. "
                f"Need ₹{self.additional_sip_needed:,.0f} more/month."
            )
        else:
            self.status = "at_risk"
            self.recommendation = (
                f"Goal {self.goal_type} is at risk. "
                f"Current savings cover only {self.feasibility_score}% of target. "
                f"Consider extending timeline or reducing target."
            )

    def to_dict(self) -> dict:
        return {
            "goal_type": self.goal_type,
            "target_amount": round(self.target_amount),
            "target_amount_lakhs": round(self.target_amount / 100_000, 2),
            "years_remaining": self.years_remaining,
            "current_corpus": round(self.current_corpus),
            "monthly_sip": round(self.monthly_sip),
            "projected_corpus": round(self.projected_corpus),
            "projected_corpus_lakhs": round(self.projected_corpus / 100_000, 2),
            "shortfall": round(self.shortfall),
            "additional_sip_needed": round(self.additional_sip_needed),
            "feasibility_score": self.feasibility_score,
            "status": self.status,
            "recommendation": self.recommendation,
        }


def assess_retirement_readiness(
    current_age: int,
    target_retirement_age: int,
    current_retirement_corpus: float,
    monthly_retirement_sip: float,
    desired_monthly_income: float,
    expected_retirement_years: int = 25,
    annual_return: float = DEFAULT_EQUITY_RETURN,
) -> dict:
    """
    Comprehensive retirement readiness assessment.

    Args:
        current_age: Client's current age
        target_retirement_age: Desired retirement age
        current_retirement_corpus: Existing EPF + NPS + retirement MF corpus (₹)
        monthly_retirement_sip: Monthly SIP towards retirement (₹)
        desired_monthly_income: Monthly income needed in retirement (today's ₹)
        expected_retirement_years: How long retirement phase lasts
        annual_return: Expected return on accumulation

    Returns:
        Comprehensive retirement assessment dict
    """
    years_to_retirement = target_retirement_age - current_age

    if years_to_retirement <= 0:
        return {"error": "Already at or past retirement age"}

    # Inflate desired income to retirement date
    inflated_monthly_income = desired_monthly_income * (1 + DEFAULT_INFLATION_RATE) ** years_to_retirement

    # Required corpus at retirement (using 4% withdrawal rule adjusted for India)
    # India: use 6% post-retirement return, 25-year retirement
    post_retirement_monthly_rate = 0.06 / 12
    n = expected_retirement_years * 12
    required_corpus = inflated_monthly_income * (1 - (1 + post_retirement_monthly_rate) ** (-n)) / post_retirement_monthly_rate

    # Projected corpus
    existing_growth = lumpsum_future_value(current_retirement_corpus, years_to_retirement, annual_return)
    sip_growth = sip_future_value(monthly_retirement_sip, years_to_retirement, annual_return)
    projected_corpus = existing_growth + sip_growth

    # Gap analysis
    shortfall = max(0, required_corpus - projected_corpus)
    additional_sip = required_monthly_sip(shortfall, years_to_retirement, annual_return) if shortfall > 0 else 0

    # Feasibility
    coverage = projected_corpus / required_corpus if required_corpus > 0 else 0
    feasibility_score = min(100, int(coverage * 100))

    return {
        "years_to_retirement": years_to_retirement,
        "required_corpus_lakhs": round(required_corpus / 100_000, 2),
        "projected_corpus_lakhs": round(projected_corpus / 100_000, 2),
        "shortfall_lakhs": round(shortfall / 100_000, 2),
        "monthly_income_at_retirement": round(inflated_monthly_income),
        "feasibility_score": feasibility_score,
        "additional_monthly_sip_needed": round(additional_sip),
        "stepup_sip_alternative": round(
            monthly_retirement_sip * 0.3  # 30% step-up over 3 years as alternative
        ),
        "on_track": feasibility_score >= 80,
        "recommendation": (
            "On track for retirement ✓" if feasibility_score >= 80
            else f"Shortfall of ₹{shortfall/100_000:.1f}L — add ₹{additional_sip:,.0f}/month SIP or step up existing SIPs by 10% annually"
        ),
    }
