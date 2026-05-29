"""
compliance_injector.py — SEBI compliance layer for AI responses.

Classifies user queries, injects mandatory disclaimers, validates that
AI responses are compliant with SEBI (Investment Advisers) Regulations, 2013.

Dependencies: indian_constants.py (Tier 3)
"""

import re
from enum import Enum
from typing import Optional

from app.financial.indian_constants import SEBI_DISCLAIMER, SEBI_MIN_CONFIDENCE_FOR_RECOMMENDATION
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class QueryType(str, Enum):
    PORTFOLIO = "portfolio"
    TAX = "tax"
    RETIREMENT = "retirement"
    INVESTMENT_ADVICE = "investment_advice"
    BEHAVIORAL = "behavioral"
    MARKET = "market"
    GENERAL = "general"


# Phrases that require a compliance disclaimer even if classified as GENERAL
DISCLAIMER_TRIGGER_PHRASES = [
    "invest", "buy", "sell", "redeem", "switch", "portfolio",
    "mutual fund", "sip", "lumpsum", "returns", "tax", "gains",
    "ltcg", "stcg", "retirement", "pension", "goal", "corpus",
    "xirr", "nps", "ppf", "elss", "nifty", "sensex", "market",
    "equity", "debt", "gold", "allocation", "rebalance",
]

# Phrases that indicate investment advice (triggering stricter validation)
INVESTMENT_ADVICE_PHRASES = [
    "should i", "should i invest", "recommend", "what should", "best fund",
    "which fund", "buy or sell", "when to", "should i buy", "should i sell",
    "is it good", "is it safe", "is it worth", "good time to",
]

# Phrases that indicate Clause 19 rationale is required
RATIONALE_INDICATORS = [
    "recommend", "suggest", "advise", "should invest", "best option",
    "better to", "consider", "switch to", "move to", "reallocate",
    "rebalance into",
]

# Prohibited phrases Claude must never use
PROHIBITED_PHRASES = [
    "guaranteed returns",
    "risk-free",
    "certain profit",
    "definitely will",
    "100% sure",
    "will definitely",
    "assured return",
    "no risk",
    "zero risk",
]


def classify_query(query: str) -> QueryType:
    """
    Classify the user's query to determine compliance requirements.

    Returns:
        QueryType enum value
    """
    q = query.lower()

    # Order matters — check most specific first
    if any(p in q for p in ["retire", "retirement", "pension", "corpus at 60", "nps"]):
        return QueryType.RETIREMENT

    if any(p in q for p in ["tax", "ltcg", "stcg", "80c", "80d", "deduction", "itr", "regime"]):
        return QueryType.TAX

    if any(p in q for p in ["portfolio", "holding", "xirr", "nav", "aum", "allocation"]):
        return QueryType.PORTFOLIO

    if any(p in q for p in INVESTMENT_ADVICE_PHRASES):
        return QueryType.INVESTMENT_ADVICE

    if any(p in q for p in ["nifty", "sensex", "market", "index", "bull", "bear", "rally", "crash"]):
        return QueryType.MARKET

    if any(p in q for p in ["feeling", "worried", "panic", "fear", "excited", "emotion", "sleep"]):
        return QueryType.BEHAVIORAL

    return QueryType.GENERAL


def inject_disclaimer(response: str, query_type: QueryType) -> str:
    """
    Append SEBI disclaimer to AI response if required.

    Disclaimer is always injected for INVESTMENT_ADVICE, TAX, and RETIREMENT.
    Also injected for PORTFOLIO if the response contains investment keywords.

    Returns:
        Response string with disclaimer appended (or unchanged if not needed).
    """
    requires_disclaimer = query_type in (
        QueryType.INVESTMENT_ADVICE,
        QueryType.TAX,
        QueryType.RETIREMENT,
        QueryType.PORTFOLIO,
    )

    # Also inject for GENERAL/MARKET if response mentions investing
    if not requires_disclaimer:
        resp_lower = response.lower()
        if any(phrase in resp_lower for phrase in DISCLAIMER_TRIGGER_PHRASES[:8]):
            requires_disclaimer = True

    if requires_disclaimer and SEBI_DISCLAIMER.strip() not in response:
        return response + SEBI_DISCLAIMER

    return response


def validate_response_compliance(
    response: str,
    query_type: QueryType,
) -> dict:
    """
    Check if AI response complies with SEBI regulations.

    Checks:
    1. No prohibited phrases (guaranteed returns, risk-free, etc.)
    2. Investment advice responses have rationale
    3. No specific fund name buy/sell recommendations without disclaimer

    Returns:
        {
            "is_compliant": bool,
            "violations": list[str],
            "warnings": list[str],
        }
    """
    violations = []
    warnings = []
    resp_lower = response.lower()

    # Check prohibited phrases
    for phrase in PROHIBITED_PHRASES:
        if phrase in resp_lower:
            violations.append(f"Prohibited phrase detected: '{phrase}'")

    # Investment advice requires explicit rationale
    if query_type == QueryType.INVESTMENT_ADVICE:
        has_rationale = any(indicator in resp_lower for indicator in RATIONALE_INDICATORS)
        if not has_rationale:
            warnings.append("Investment advice response lacks explicit rationale (SEBI IA Reg. Clause 19)")

    # Check for specific fund names + buy recommendations without caveats
    buy_patterns = [r"buy\s+\w+\s+fund", r"invest in\s+\w+\s+fund", r"purchase\s+\w+"]
    for pattern in buy_patterns:
        if re.search(pattern, resp_lower):
            if "past performance" not in resp_lower and "consult" not in resp_lower:
                warnings.append("Specific buy recommendation without standard caveat")
            break

    is_compliant = len(violations) == 0
    if not is_compliant:
        logger.warning(
            "compliance_violation_detected",
            query_type=query_type,
            violations=violations,
        )

    return {
        "is_compliant": is_compliant,
        "violations": violations,
        "warnings": warnings,
    }


def estimate_confidence(
    response: str,
    tools_used: list[str],
    rag_sources_found: int = 0,
) -> float:
    """
    Estimate confidence score (0.0–1.0) for an AI response.

    Higher confidence when:
    - More tools were used (live data)
    - RAG sources found
    - Response is detailed (length proxy)
    - Response doesn't express uncertainty

    Returns:
        float confidence score, capped at 0.95
    """
    score = 0.40  # Base score

    # Tools add confidence (live data)
    score += min(len(tools_used) * 0.12, 0.36)  # max +0.36 for 3+ tools

    # RAG sources add confidence
    if rag_sources_found > 0:
        score += min(rag_sources_found * 0.05, 0.10)

    # Response length proxy (more detail = more confidence)
    if len(response) > 500:
        score += 0.05
    if len(response) > 1500:
        score += 0.05

    # Uncertainty phrases reduce confidence
    uncertainty_phrases = [
        "i'm not sure", "i don't know", "unclear", "might be", "possibly",
        "i cannot", "unable to", "no data available", "couldn't find",
    ]
    resp_lower = response.lower()
    uncertainty_count = sum(1 for p in uncertainty_phrases if p in resp_lower)
    score -= uncertainty_count * 0.08

    # Clamp between 0.3 and 0.95
    return round(min(0.95, max(0.30, score)), 2)
