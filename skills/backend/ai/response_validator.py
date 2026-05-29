"""
response_validator.py — Validate AI response completeness and safety.

Checks that responses don't hallucinate financial figures, contain required
elements for tax/retirement queries, and meet SEBI Clause 19 standards.

Dependencies: indian_constants.py, exceptions.py (Tier 4)
Consumed by: compliance_injector.py, streaming.py, audit log writer
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from skills.backend.financial.indian_constants import (
    SEBI_MIN_CONFIDENCE_FOR_RECOMMENDATION,
    EQUITY_LTCG_RATE,
    EQUITY_STCG_RATE,
    SEC_80C_LIMIT,
)
from skills.backend.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of a response validation check."""
    passed: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confidence_penalty: float = 0.0

    def add_issue(self, msg: str, penalty: float = 0.05):
        self.issues.append(msg)
        self.confidence_penalty += penalty
        self.passed = False

    def add_warning(self, msg: str):
        self.warnings.append(msg)


def validate_tax_response(response: str) -> ValidationResult:
    """
    Validate that a tax-related response contains all required elements.

    Required elements per SEBI guidance:
    - Tax liability figures must not contradict current law
    - LTCG rate must be cited as 12.5% (not old 10%)
    - Must mention CA/tax consultant for specific advice
    """
    result = ValidationResult(passed=True)
    response_lower = response.lower()

    # Check for outdated LTCG rate (old 10% rate pre-Budget 2024)
    if re.search(r"10%.*long.?term|ltcg.*10%|long.?term.*10%", response_lower):
        result.add_issue(
            "Response may cite outdated LTCG rate of 10% — current rate is 12.5% (Budget 2024)",
            penalty=0.15,
        )

    # Check if CA consultation is recommended for tax advice
    ca_mentioned = any(kw in response_lower for kw in [
        "chartered accountant", "ca ", "tax consultant", "tax advisor", "consult"
    ])
    if not ca_mentioned:
        result.add_warning(
            "Tax response should recommend consulting a CA/tax advisor for personal advice"
        )

    # Check 80C limit accuracy
    if "1.5 lakh" in response_lower or "150,000" in response_lower or "1,50,000" in response_lower:
        pass  # Correct limit cited
    elif "80c" in response_lower and "lakh" in response_lower:
        result.add_warning("80C deduction limit should be cited as ₹1.5 lakh")

    return result


def validate_retirement_response(response: str) -> ValidationResult:
    """
    Validate retirement planning response contains required elements.
    """
    result = ValidationResult(passed=True)
    response_lower = response.lower()

    # Must mention inflation
    if "inflation" not in response_lower:
        result.add_warning("Retirement projection should account for inflation (6% India CPI)")

    # Must not claim specific guaranteed NPS returns
    if re.search(r"nps.*guarantee|guarantee.*nps", response_lower):
        result.add_issue("NPS returns are market-linked and cannot be guaranteed", penalty=0.2)

    return result


def validate_investment_advice_response(response: str) -> ValidationResult:
    """
    Validate investment recommendation contains rationale and risk disclosure.
    SEBI IA Regulations 2013, Clause 19: Rationale required for all advice.
    """
    result = ValidationResult(passed=True)
    response_lower = response.lower()

    # Rationale must be present
    rationale_found = any(kw in response_lower for kw in [
        "because", "since", "given", "based on", "considering", "reason", "rationale"
    ])
    if not rationale_found:
        result.add_issue(
            "Investment advice must include rationale per SEBI Clause 19",
            penalty=0.2,
        )

    # Risk must be mentioned
    risk_found = any(kw in response_lower for kw in [
        "risk", "volatility", "market risk", "loss", "no guarantee"
    ])
    if not risk_found:
        result.add_warning(
            "Investment recommendation should include risk disclosure"
        )

    return result


def validate_figure_plausibility(response: str) -> ValidationResult:
    """
    Basic sanity check on monetary figures mentioned in response.
    Catches obvious hallucinations (e.g., ₹100 crore for a ₹5L portfolio).
    """
    result = ValidationResult(passed=True)

    # Find all crore/lakh figures
    crore_figures = re.findall(r"₹?\s*(\d+(?:\.\d+)?)\s*(?:crore|cr)", response.lower())
    lakh_figures = re.findall(r"₹?\s*(\d+(?:\.\d+)?)\s*(?:lakh|l\b)", response.lower())

    # Flag implausibly large figures (>500 crore is unusual for individual investors)
    for fig in crore_figures:
        try:
            if float(fig) > 500:
                result.add_warning(f"Unusually large figure: ₹{fig} crore — verify this is correct")
        except ValueError:
            pass

    return result


def run_full_validation(
    response: str,
    query_type: str,
    tools_used: Optional[list[str]] = None,
) -> dict:
    """
    Run all applicable validation checks for a given query type.

    Args:
        response: The AI response text
        query_type: "tax" | "retirement" | "investment_advice" | "portfolio" | "general"
        tools_used: List of tool names called during response generation

    Returns:
        Dict with overall pass/fail, issues list, confidence adjustment
    """
    all_issues = []
    all_warnings = []
    total_confidence_penalty = 0.0

    validators = {
        "tax": validate_tax_response,
        "retirement": validate_retirement_response,
        "investment_advice": validate_investment_advice_response,
    }

    # Run query-type specific validation
    if query_type in validators:
        result = validators[query_type](response)
        all_issues.extend(result.issues)
        all_warnings.extend(result.warnings)
        total_confidence_penalty += result.confidence_penalty

    # Always run figure plausibility check
    plausibility = validate_figure_plausibility(response)
    all_warnings.extend(plausibility.warnings)

    # Bonus confidence if tools were used (grounded response)
    data_grounded = bool(tools_used)

    return {
        "validation_passed": len(all_issues) == 0,
        "issues": all_issues,
        "warnings": all_warnings,
        "confidence_penalty": total_confidence_penalty,
        "data_grounded": data_grounded,
        "tools_used": tools_used or [],
        "requires_human_review": total_confidence_penalty > 0.3,
    }
