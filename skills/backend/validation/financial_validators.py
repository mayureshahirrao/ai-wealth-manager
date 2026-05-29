"""
financial_validators.py — Business-rule validators for financial inputs.

These validators enforce Indian financial constraints (SEBI rules, AMFI limits,
tax thresholds) at the API boundary before any business logic runs.

Dependencies: indian_constants.py, indian_schemas.py, exceptions.py (Tier 4)
Consumed by: All route handlers that accept financial inputs
"""

from skills.backend.financial.indian_constants import (
    SEC_80C_LIMIT, SEC_80CCD_1B_NPS,
    PPF_MIN_ANNUAL, PPF_MAX_ANNUAL,
    SCSS_MAX_INVESTMENT,
    MAX_SINGLE_ASSET_CONCENTRATION,
    MAX_CRYPTO_ALLOCATION,
)
from skills.backend.core.exceptions import ValidationException


def validate_sip_amount(amount: float, scheme_name: str = "fund") -> float:
    """
    Validate SIP amount meets AMFI minimum requirements.

    Most MF schemes require minimum ₹500/month SIP.
    Returns validated amount or raises ValidationException.
    """
    MIN_SIP = 500
    MAX_SIP = 10_000_000  # ₹1 Crore/month (practical upper limit)

    if amount < MIN_SIP:
        raise ValidationException(
            field="sip_amount",
            reason=f"Minimum SIP for {scheme_name} is ₹{MIN_SIP}. You entered ₹{amount}."
        )
    if amount > MAX_SIP:
        raise ValidationException(
            field="sip_amount",
            reason=f"SIP amount ₹{amount} exceeds practical maximum ₹{MAX_SIP:,}"
        )
    return amount


def validate_80c_claim(amount: float) -> float:
    """
    Validate Section 80C deduction claim doesn't exceed ₹1.5 lakh limit.
    Returns the capped amount (not an error if exceeded — just capped).
    """
    if amount > SEC_80C_LIMIT:
        return SEC_80C_LIMIT  # Cap silently — caller should inform user
    return amount


def validate_ppf_contribution(annual_contribution: float) -> float:
    """Validate PPF annual contribution is within ₹500–₹1.5L range."""
    if annual_contribution < PPF_MIN_ANNUAL:
        raise ValidationException(
            field="ppf_contribution",
            reason=f"PPF minimum annual contribution is ₹{PPF_MIN_ANNUAL}."
        )
    if annual_contribution > PPF_MAX_ANNUAL:
        raise ValidationException(
            field="ppf_contribution",
            reason=f"PPF maximum annual contribution is ₹{PPF_MAX_ANNUAL:,} (₹1.5 lakh)."
        )
    return annual_contribution


def validate_portfolio_concentration(
    asset_value: float,
    total_portfolio_value: float,
    asset_name: str,
) -> dict:
    """
    Check if a single asset exceeds concentration threshold (20%).

    Returns:
        Dict with is_concentrated flag and concentration percentage
    """
    if total_portfolio_value <= 0:
        return {"is_concentrated": False, "concentration_pct": 0.0}

    concentration = asset_value / total_portfolio_value
    is_concentrated = concentration > MAX_SINGLE_ASSET_CONCENTRATION

    return {
        "asset_name": asset_name,
        "concentration_pct": round(concentration * 100, 2),
        "is_concentrated": is_concentrated,
        "threshold_pct": MAX_SINGLE_ASSET_CONCENTRATION * 100,
        "sebi_alert": is_concentrated,
    }


def validate_crypto_allocation(
    crypto_value: float,
    total_portfolio_value: float,
) -> dict:
    """
    Check if crypto/VDA allocation exceeds 20% (SEBI risk threshold).
    Note: Crypto >20% triggers compliance alert, not a hard block.
    """
    if total_portfolio_value <= 0:
        return {"is_overweight": False, "allocation_pct": 0.0}

    allocation = crypto_value / total_portfolio_value

    return {
        "allocation_pct": round(allocation * 100, 2),
        "is_overweight": allocation > MAX_CRYPTO_ALLOCATION,
        "threshold_pct": MAX_CRYPTO_ALLOCATION * 100,
        "tax_note": "Crypto gains taxed at 30% flat (VDA rules) — no loss offset allowed",
        "compliance_flag": allocation > MAX_CRYPTO_ALLOCATION,
    }


def validate_investment_amount(amount: float, min_amount: float = 1000) -> float:
    """Validate a one-time investment (lumpsum) is within sensible range."""
    if amount < min_amount:
        raise ValidationException(
            field="investment_amount",
            reason=f"Minimum investment amount is ₹{min_amount:,}."
        )
    return amount


def validate_goal_target(target_amount: float, goal_type: str) -> float:
    """
    Validate goal target amount is realistic for the goal type.
    Soft check — just warns if unrealistic.
    """
    MINIMUMS = {
        "retirement": 1_000_000,       # ₹10L minimum retirement corpus
        "home_purchase": 500_000,       # ₹5L minimum (down payment)
        "child_education": 200_000,     # ₹2L minimum
        "emergency_fund": 50_000,       # ₹50K minimum
    }
    minimum = MINIMUMS.get(goal_type, 10_000)
    if target_amount < minimum:
        raise ValidationException(
            field="target_amount",
            reason=f"Target amount ₹{target_amount:,.0f} seems too low for a {goal_type} goal. "
                   f"Minimum recommended: ₹{minimum:,}."
        )
    return target_amount
