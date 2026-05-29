"""
compliance_injector.py — SEBI compliance disclaimer injection and Clause 19 validation.

SEBI (Investment Advisers) Regulations 2013, Clause 19 requires:
- Every recommendation must have a rationale
- Investment advice must include risk disclosure
- Guaranteed returns must never be stated

This module ensures all AI responses meet these requirements before delivery.

Dependencies: indian_constants.py, logging_config.py (Tier 4)
Consumed by: streaming.py, chat endpoint, compliance doc generator
"""

import re
from enum import Enum
from typing import Optional

from skills.backend.financial.indian_constants import SEBI_DISCLAIMER
from skills.backend.core.logging_config import get_logger

logger = get_logger(__name__)


class QueryType(str, Enum):
    """Classification of user query for appropriate disclaimer selection."""
    PORTFOLIO = "portfolio"
    TAX = "tax"
    RETIREMENT = "retirement"
    INVESTMENT_ADVICE = "investment_advice"
    BEHAVIORAL = "behavioral"
    MARKET = "market"
    GENERAL = "general"


# ─── Prohibited phrases Claude must never use ──────────────────────────────────
PROHIBITED_PHRASES = [
    r"guaranteed return",
    r"guaranteed profit",
    r"risk.?free return",
    r"will definitely",
    r"certain to (grow|increase|rise)",
    r"100% safe",
    r"no risk",
]

# ─── Phrases that indicate Clause 19 rationale is present ──────────────────────
RATIONALE_INDICATORS = [
    "because",
    "since",
    "given that",
    "based on",
    "considering",
    "reason",
    "rationale",
    "due to",
    "as a result of",
]


def classify_query(query: str) -> QueryType:
    """
    Classify an investor query to determine appropriate compliance handling.

    Args:
        query: Raw user message text

    Returns:
        QueryType enum value
    """
    query_lower = query.lower()

    if any(kw in query_lower for kw in ["tax", "80c", "ltcg", "stcg", "regime", "tds", "deduction"]):
        return QueryType.TAX
    if any(kw in query_lower for kw in ["retire", "retirement", "nps", "pension", "corpus"]):
        return QueryType.RETIREMENT
    if any(kw in query_lower for kw in ["portfolio", "holdings", "allocation", "performance", "xirr"]):
        return QueryType.PORTFOLIO
    if any(kw in query_lower for kw in ["buy", "invest", "recommend", "should i", "which fund", "best fund"]):
        return QueryType.INVESTMENT_ADVICE
    if any(kw in query_lower for kw in ["market", "nifty", "sensex", "crash", "fall", "rally"]):
        return QueryType.MARKET
    if any(kw in query_lower for kw in ["panic", "worried", "scared", "should i sell", "exit"]):
        return QueryType.BEHAVIORAL

    return QueryType.GENERAL


def inject_disclaimer(response: str, query_type: QueryType = QueryType.GENERAL) -> str:
    """
    Append SEBI-mandated disclaimer to AI response.

    Always appended. Query type may influence disclaimer variant in future.

    Args:
        response: Raw AI response text
        query_type: Type of query (for logging/audit purposes)

    Returns:
        Response with disclaimer appended
    """
    logger.debug("disclaimer_injected", query_type=query_type.value)
    return response + SEBI_DISCLAIMER


def validate_response_compliance(response: str, query_type: QueryType) -> dict:
    """
    Validate that an AI response meets SEBI Clause 19 requirements.

    Returns a compliance report dict with:
    - sebi_compliant: bool
    - has_disclaimer: bool
    - no_guaranteed_returns: bool
    - has_rationale: bool (for investment advice queries)
    - flags: list of issues found

    Usage:
        report = validate_response_compliance(ai_response, QueryType.INVESTMENT_ADVICE)
        if not report["sebi_compliant"]:
            log_compliance_issue(report)
    """
    flags = []
    response_lower = response.lower()

    # Check for prohibited phrases
    for pattern in PROHIBITED_PHRASES:
        if re.search(pattern, response_lower):
            flags.append(f"Prohibited phrase found: '{pattern}'")

    # Check for disclaimer presence
    has_disclaimer = "sebi" in response_lower or "investment adviser" in response_lower

    # Check for rationale in advice queries
    has_rationale = True  # Default to True for non-advice queries
    if query_type == QueryType.INVESTMENT_ADVICE:
        has_rationale = any(ind in response_lower for ind in RATIONALE_INDICATORS)
        if not has_rationale:
            flags.append("Investment advice without explicit rationale (Clause 19 requirement)")

    # Check for tax-specific completeness
    if query_type == QueryType.TAX:
        tax_completeness_checks = [
            ("income tax mention", "tax" in response_lower),
            ("consult advisor mention", any(kw in response_lower for kw in ["tax adviser", "ca", "chartered accountant", "consult"])),
        ]
        for check_name, passed in tax_completeness_checks:
            if not passed:
                flags.append(f"Tax response missing: {check_name}")

    no_prohibited = len([f for f in flags if "Prohibited" in f]) == 0

    return {
        "sebi_compliant": has_disclaimer and no_prohibited and has_rationale,
        "has_disclaimer": has_disclaimer,
        "no_guaranteed_returns": no_prohibited,
        "has_rationale": has_rationale,
        "query_type": query_type.value,
        "flags": flags,
        "clause_19_satisfied": has_rationale and no_prohibited,
    }


def estimate_confidence(
    response: str,
    tools_used: list[str],
    rag_sources_found: int,
) -> float:
    """
    Estimate AI response confidence score for governance dashboard.

    Heuristic scoring:
    - Tool calls used: +0.3 (grounded in data)
    - RAG sources found: +0.2 (grounded in knowledge)
    - Response length (adequate): +0.2
    - Hedging language present: -0.1

    Returns:
        Float between 0.0 and 1.0
    """
    score = 0.5  # Base score

    if tools_used:
        score += min(0.3, len(tools_used) * 0.1)  # Max +0.3 for tool usage

    if rag_sources_found > 0:
        score += min(0.2, rag_sources_found * 0.05)  # Max +0.2

    if len(response) > 200:
        score += 0.1  # Adequate length

    # Hedging language reduces confidence
    hedging_phrases = ["i'm not sure", "i cannot", "unclear", "might", "possibly", "uncertain"]
    hedge_count = sum(1 for phrase in hedging_phrases if phrase in response.lower())
    score -= hedge_count * 0.05

    return round(max(0.0, min(1.0, score)), 2)
