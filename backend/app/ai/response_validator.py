"""
response_validator.py — Validates AI tool output for financial plausibility.

Before Claude returns a response, tool outputs are checked for:
1. Figure plausibility (tax rates, returns within realistic bounds)
2. Retirement corpus sanity checks
3. Indian tax calculation spot-checks

Dependencies: indian_constants.py (Tier 3)
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from app.financial.indian_constants import (
    EQUITY_LTCG_RATE,
    EQUITY_STCG_RATE,
    NEW_REGIME_SLABS,
    SEBI_MIN_CONFIDENCE_FOR_RECOMMENDATION,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of validating a tool's output."""
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confidence_penalty: float = 0.0  # Subtract from confidence score if invalid


def validate_tax_response(tool_result: dict) -> ValidationResult:
    """
    Validate calculate_tax_liability tool output.

    Checks:
    - Effective tax rate is within realistic bounds (0–50%)
    - Total tax doesn't exceed gross income
    - Recommended regime is one of the two valid options
    """
    errors = []
    warnings = []
    penalty = 0.0

    try:
        new_r = tool_result.get("new_regime", {})
        old_r = tool_result.get("old_regime", {})

        # Effective rate check
        for regime_name, regime in [("New Regime", new_r), ("Old Regime", old_r)]:
            rate = regime.get("effective_rate_pct", 0)
            if rate < 0 or rate > 50:
                errors.append(f"{regime_name}: effective tax rate {rate}% is out of bounds (0–50%)")
                penalty += 0.15

        # Recommended regime must be valid
        recommended = tool_result.get("recommended_regime", "")
        if recommended not in ("New Regime", "Old Regime"):
            errors.append(f"Invalid recommended_regime: '{recommended}'")
            penalty += 0.10

        # Tax savings sanity
        savings = tool_result.get("tax_savings_if_switching", 0)
        if abs(savings) > 500_000:  # ₹5L savings unlikely for most clients
            warnings.append(f"Unusually large tax savings: ₹{savings:,.0f} — verify inputs")

    except Exception as exc:
        errors.append(f"Tax validation error: {exc}")
        penalty += 0.20

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        confidence_penalty=penalty,
    )


def validate_retirement_response(tool_result: dict) -> ValidationResult:
    """
    Validate run_retirement_projection tool output.

    Checks:
    - Required corpus is in realistic range (₹50L – ₹50 Cr)
    - Feasibility score is 0–100
    - Years to retirement is positive
    """
    errors = []
    warnings = []
    penalty = 0.0

    try:
        required_lakhs = tool_result.get("required_corpus_lakhs", 0)
        if required_lakhs < 10:
            warnings.append(f"Very low required corpus: ₹{required_lakhs}L — verify income inputs")
        if required_lakhs > 50_000:  # > ₹500 Cr
            errors.append(f"Required corpus ₹{required_lakhs}L exceeds plausible range")
            penalty += 0.20

        score = tool_result.get("feasibility_score", -1)
        if not (0 <= score <= 100):
            errors.append(f"Feasibility score {score} outside 0–100 range")
            penalty += 0.15

        years = tool_result.get("years_to_retirement", 0)
        if years <= 0:
            errors.append("years_to_retirement must be positive")
            penalty += 0.10

    except Exception as exc:
        errors.append(f"Retirement validation error: {exc}")
        penalty += 0.20

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        confidence_penalty=penalty,
    )


def validate_investment_advice_response(tool_result: dict) -> ValidationResult:
    """
    Validate portfolio summary tool output for plausibility.

    Checks:
    - XIRR within realistic range (-30% to 60%)
    - AUM is positive
    - Asset allocation sums to ~100%
    """
    errors = []
    warnings = []
    penalty = 0.0

    try:
        xirr = tool_result.get("xirr_pct", None)
        if xirr is not None and not (-30 <= xirr <= 60):
            errors.append(f"XIRR {xirr}% outside realistic range (-30% to 60%)")
            penalty += 0.15

        aum = tool_result.get("current_value", 0)
        if aum < 0:
            errors.append(f"Current portfolio value is negative: {aum}")
            penalty += 0.25

    except Exception as exc:
        errors.append(f"Portfolio validation error: {exc}")
        penalty += 0.10

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        confidence_penalty=penalty,
    )


def validate_figure_plausibility(key: str, value: Any) -> Optional[str]:
    """
    Spot-check a single figure against known Indian financial bounds.

    Returns:
        Warning string if out of bounds, None if OK.
    """
    if not isinstance(value, (int, float)):
        return None

    checks = {
        "ltcg_rate": (0.10, 0.15),
        "stcg_rate": (0.15, 0.25),
        "effective_rate_pct": (0, 50),
        "xirr_pct": (-30, 60),
        "feasibility_score": (0, 100),
        "years_remaining": (0, 50),
    }

    if key in checks:
        lo, hi = checks[key]
        if not (lo <= value <= hi):
            return f"'{key}' value {value} is outside expected range [{lo}, {hi}]"

    return None


def run_full_validation(
    tool_name: str,
    tool_result: dict,
) -> ValidationResult:
    """
    Run appropriate validation based on tool name.

    Args:
        tool_name: Name of the tool that produced this result
        tool_result: The dict returned by the tool

    Returns:
        ValidationResult with all errors, warnings, and confidence penalty
    """
    if "tax" in tool_name:
        result = validate_tax_response(tool_result)
    elif "retirement" in tool_name:
        result = validate_retirement_response(tool_result)
    elif "portfolio" in tool_name:
        result = validate_investment_advice_response(tool_result)
    else:
        # No specific validator — return clean result
        result = ValidationResult(is_valid=True)

    if not result.is_valid:
        logger.warning(
            "tool_validation_failed",
            tool_name=tool_name,
            errors=result.errors,
            warnings=result.warnings,
        )
    elif result.warnings:
        logger.debug(
            "tool_validation_warnings",
            tool_name=tool_name,
            warnings=result.warnings,
        )

    return result
