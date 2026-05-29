"""
app.financial — Indian financial calculation engine.

Public API — import from here in tools and endpoints:
    from app.financial import xirr, format_inr, compare_tax_regimes, GoalAssessment
"""

from app.financial.xirr import xirr, xirr_from_sip_history, xirr_to_display
from app.financial.sip_calculator import (
    sip_future_value,
    required_monthly_sip,
    stepup_sip_future_value,
    lumpsum_future_value,
    inflation_adjusted_value,
    monthly_withdrawal_from_corpus,
    years_to_double,
)
from app.financial.tax_calculator import (
    calculate_new_regime_tax,
    calculate_old_regime_tax,
    compare_tax_regimes,
    calculate_ltcg_tax,
    calculate_stcg_tax,
    ltcg_harvesting_opportunity,
    Deductions,
    TaxResult,
)
from app.financial.goal_engine import (
    GoalAssessment,
    assess_retirement_readiness,
)
from app.financial.currency_formatter import (
    format_inr,
    format_inr_indian_numbering,
    amount_to_words,
    lakhs,
    crores,
)

__all__ = [
    # XIRR
    "xirr", "xirr_from_sip_history", "xirr_to_display",
    # SIP math
    "sip_future_value", "required_monthly_sip", "stepup_sip_future_value",
    "lumpsum_future_value", "inflation_adjusted_value",
    "monthly_withdrawal_from_corpus", "years_to_double",
    # Tax
    "calculate_new_regime_tax", "calculate_old_regime_tax", "compare_tax_regimes",
    "calculate_ltcg_tax", "calculate_stcg_tax", "ltcg_harvesting_opportunity",
    "Deductions", "TaxResult",
    # Goals
    "GoalAssessment", "assess_retirement_readiness",
    # Formatting
    "format_inr", "format_inr_indian_numbering", "amount_to_words",
    "lakhs", "crores",
]
