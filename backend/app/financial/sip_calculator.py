"""
sip_calculator.py — SIP and investment math for Indian investors.

Provides standard financial planning calculations used by the AI tools
and planning agents.

Dependencies: indian_constants.py (Tier 1)
Consumed by: GoalEngine, RetirementProjectionTool, FinancialPlanAgent
"""

import math
from typing import Optional
from app.financial.indian_constants import (
    DEFAULT_EQUITY_RETURN,
    DEFAULT_INFLATION_RATE,
    DEFAULT_STEP_UP_RATE,
)


def sip_future_value(
    monthly_sip: float,
    years: int,
    annual_return: float = DEFAULT_EQUITY_RETURN,
) -> float:
    """
    Calculate the future value of a regular monthly SIP.

    Formula: FV = P × [((1 + r)^n - 1) / r] × (1 + r)
    where r = monthly_rate, n = number_of_months

    Args:
        monthly_sip: Monthly investment amount (₹)
        years: Investment duration in years
        annual_return: Expected annual return (e.g., 0.12 for 12%)

    Returns:
        Future value in ₹

    Example:
        # ₹10,000/month for 20 years at 12% = ~₹98 Lakh
        fv = sip_future_value(10000, 20, 0.12)
    """
    if years <= 0 or monthly_sip <= 0:
        return 0.0
    monthly_rate = annual_return / 12
    n = years * 12
    if monthly_rate == 0:
        return monthly_sip * n
    return monthly_sip * (((1 + monthly_rate) ** n - 1) / monthly_rate) * (1 + monthly_rate)


def required_monthly_sip(
    target_corpus: float,
    years: int,
    annual_return: float = DEFAULT_EQUITY_RETURN,
) -> float:
    """
    Calculate the monthly SIP required to reach a target corpus.
    Reverse of sip_future_value.

    Args:
        target_corpus: Target amount in ₹
        years: Time horizon in years
        annual_return: Expected annual return

    Returns:
        Required monthly SIP amount in ₹

    Example:
        # To build ₹1 crore in 15 years at 12%
        sip = required_monthly_sip(10_000_000, 15, 0.12)  # ≈ ₹18,000/month
    """
    if years <= 0 or target_corpus <= 0:
        return 0.0
    monthly_rate = annual_return / 12
    n = years * 12
    if monthly_rate == 0:
        return target_corpus / n
    denominator = (((1 + monthly_rate) ** n - 1) / monthly_rate) * (1 + monthly_rate)
    return target_corpus / denominator


def stepup_sip_future_value(
    initial_monthly_sip: float,
    annual_stepup_pct: float,
    years: int,
    annual_return: float = DEFAULT_EQUITY_RETURN,
) -> float:
    """
    Calculate future value of a step-up SIP (SIP increased annually).

    Step-up SIP is highly recommended in India — increases SIP by a fixed %
    each year, aligned with salary increments.

    Args:
        initial_monthly_sip: Starting SIP amount (₹)
        annual_stepup_pct: Annual increase in SIP (e.g., 0.10 for 10%)
        years: Total investment duration in years
        annual_return: Expected annual return

    Returns:
        Future value in ₹
    """
    total_fv = 0.0
    current_sip = initial_monthly_sip

    for year in range(years):
        # Remaining years from this year's SIP
        remaining_years = years - year
        year_fv = sip_future_value(current_sip, remaining_years, annual_return)
        total_fv += year_fv
        current_sip *= (1 + annual_stepup_pct)

    return total_fv


def lumpsum_future_value(
    principal: float,
    years: int,
    annual_return: float = DEFAULT_EQUITY_RETURN,
) -> float:
    """
    Calculate the future value of a lumpsum investment.

    Args:
        principal: Initial investment amount (₹)
        years: Investment duration in years
        annual_return: Expected annual return

    Returns:
        Future value in ₹
    """
    return principal * (1 + annual_return) ** years


def inflation_adjusted_value(
    nominal_amount: float,
    years: int,
    inflation_rate: float = DEFAULT_INFLATION_RATE,
) -> float:
    """
    Calculate the inflation-adjusted (real) value of an amount in today's ₹.

    Used to show clients what their future corpus is worth in today's money.

    Args:
        nominal_amount: Future nominal amount (₹)
        years: Number of years in the future
        inflation_rate: Annual inflation rate (6% for India)

    Returns:
        Real value in today's ₹
    """
    return nominal_amount / (1 + inflation_rate) ** years


def required_corpus_for_monthly_income(
    monthly_income_needed: float,
    years_of_income: int,
    post_retirement_return: float = 0.07,
) -> float:
    """
    Calculate corpus needed to generate a desired monthly income.
    Uses Present Value of Annuity formula.

    Args:
        monthly_income_needed: Desired monthly withdrawal (₹, today's value)
        years_of_income: Expected retirement duration (years)
        post_retirement_return: Conservative return post-retirement

    Returns:
        Required corpus in ₹ (today's value)
    """
    monthly_rate = post_retirement_return / 12
    n = years_of_income * 12
    if monthly_rate == 0:
        return monthly_income_needed * n
    pv = monthly_income_needed * (1 - (1 + monthly_rate) ** (-n)) / monthly_rate
    return pv


def monthly_withdrawal_from_corpus(
    corpus: float,
    years: int,
    post_retirement_return: float = 0.07,
) -> float:
    """
    Calculate maximum monthly withdrawal from a corpus over a given period.

    Args:
        corpus: Total retirement corpus (₹)
        years: Expected retirement duration
        post_retirement_return: Expected return during retirement phase

    Returns:
        Maximum monthly withdrawal amount (₹)
    """
    monthly_rate = post_retirement_return / 12
    n = years * 12
    if monthly_rate == 0:
        return corpus / n
    return corpus * monthly_rate / (1 - (1 + monthly_rate) ** (-n))


def years_to_double(annual_return: float) -> float:
    """Rule of 72 — years to double investment at given return."""
    if annual_return <= 0:
        return float("inf")
    return 72 / (annual_return * 100)
