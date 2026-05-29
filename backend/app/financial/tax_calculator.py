"""
tax_calculator.py — Indian income tax and capital gains calculator.

Implements Budget 2024 tax rules for Old and New regimes.
Always import from indian_constants.py for rates — never hardcode.

Dependencies: indian_constants.py (Tier 1)
Consumed by: CalculateTaxLiabilityTool, TaxRegimeComparisonTool, FinancialPlanAgent
"""

from dataclasses import dataclass, field
from typing import Optional

from app.financial.indian_constants import (
    NEW_REGIME_SLABS, OLD_REGIME_SLABS,
    NEW_REGIME_STANDARD_DEDUCTION, OLD_REGIME_STANDARD_DEDUCTION,
    NEW_REGIME_87A_REBATE_LIMIT, NEW_REGIME_87A_REBATE_AMOUNT,
    OLD_REGIME_87A_REBATE_LIMIT, OLD_REGIME_87A_REBATE_AMOUNT,
    HEALTH_EDUCATION_CESS,
    SEC_80C_LIMIT, SEC_80D_SELF_BELOW_60, SEC_80D_SELF_ABOVE_60,
    SEC_80D_PARENTS_ABOVE_60, SEC_80CCD_1B_NPS,
    EQUITY_LTCG_RATE, EQUITY_LTCG_EXEMPTION,
    EQUITY_STCG_RATE, CRYPTO_VDA_RATE,
    SENIOR_CITIZEN_BASIC_EXEMPTION, SUPER_SENIOR_CITIZEN_AGE,
    SUPER_SENIOR_BASIC_EXEMPTION,
)


@dataclass
class Deductions:
    """Deduction inputs for Old Regime tax calculation."""
    sec_80c: float = 0.0          # ELSS, PPF, EPF, etc.
    sec_80d_self: float = 0.0     # Health insurance self
    sec_80d_parents: float = 0.0  # Health insurance parents
    sec_80ccd_nps: float = 0.0    # NPS 80CCD(1B)
    hra_exemption: float = 0.0    # HRA
    home_loan_interest: float = 0.0  # 24B
    other_deductions: float = 0.0


@dataclass
class TaxResult:
    """Result of a tax calculation."""
    gross_income: float
    taxable_income: float
    total_deductions: float
    tax_before_cess: float
    cess: float
    total_tax: float
    effective_rate: float
    regime: str
    rebate_applied: float = 0.0
    notes: list[str] = field(default_factory=list)


def _calculate_slab_tax(
    taxable_income: float,
    slabs: list[tuple[int, float, float]],
) -> float:
    """Calculate tax from given slabs."""
    tax = 0.0
    for lower, upper, rate in slabs:
        if taxable_income <= lower:
            break
        slab_income = min(taxable_income, upper) - lower
        tax += slab_income * rate
    return tax


def calculate_new_regime_tax(
    gross_income: float,
    age: int = 35,
) -> TaxResult:
    """
    Calculate income tax under the New Tax Regime (FY 2024-25).

    Args:
        gross_income: Total annual income (₹)
        age: Taxpayer age (affects senior citizen exemption)

    Returns:
        TaxResult dataclass
    """
    notes = []
    standard_deduction = NEW_REGIME_STANDARD_DEDUCTION
    taxable_income = max(0, gross_income - standard_deduction)
    total_deductions = standard_deduction

    # Calculate slab tax
    tax = _calculate_slab_tax(taxable_income, NEW_REGIME_SLABS)

    # 87A rebate (no tax if taxable income ≤ ₹7L)
    rebate = 0.0
    if taxable_income <= NEW_REGIME_87A_REBATE_LIMIT:
        rebate = min(tax, NEW_REGIME_87A_REBATE_AMOUNT)
        tax = max(0, tax - rebate)
        if rebate > 0:
            notes.append(f"Section 87A rebate of ₹{rebate:,.0f} applied")

    # Health & Education Cess
    cess = tax * HEALTH_EDUCATION_CESS

    total_tax = tax + cess
    effective_rate = total_tax / gross_income if gross_income > 0 else 0.0

    return TaxResult(
        gross_income=gross_income,
        taxable_income=taxable_income,
        total_deductions=total_deductions,
        tax_before_cess=tax,
        cess=cess,
        total_tax=total_tax,
        effective_rate=round(effective_rate, 4),
        regime="New Regime",
        rebate_applied=rebate,
        notes=notes,
    )


def calculate_old_regime_tax(
    gross_income: float,
    deductions: Optional[Deductions] = None,
    age: int = 35,
    parents_senior: bool = False,
) -> TaxResult:
    """
    Calculate income tax under the Old Tax Regime.

    Args:
        gross_income: Total annual income (₹)
        deductions: Deductions dataclass with 80C, 80D, NPS etc.
        age: Taxpayer age
        parents_senior: If True, parents' 80D limit is ₹50K

    Returns:
        TaxResult dataclass
    """
    if deductions is None:
        deductions = Deductions()

    notes = []

    # Standard deduction
    std_deduction = OLD_REGIME_STANDARD_DEDUCTION

    # Section 80C (capped at ₹1.5L)
    actual_80c = min(deductions.sec_80c, SEC_80C_LIMIT)

    # Section 80D
    self_80d_limit = SEC_80D_SELF_ABOVE_60 if age >= 60 else SEC_80D_SELF_BELOW_60
    parents_80d_limit = SEC_80D_PARENTS_ABOVE_60 if parents_senior else 25_000
    actual_80d = min(deductions.sec_80d_self, self_80d_limit) + min(deductions.sec_80d_parents, parents_80d_limit)

    # Section 80CCD(1B) NPS
    actual_nps = min(deductions.sec_80ccd_nps, SEC_80CCD_1B_NPS)

    # HRA (simplified — just take claimed amount)
    hra = deductions.hra_exemption

    # 24B home loan interest
    home_loan = min(deductions.home_loan_interest, 200_000)

    total_deductions = std_deduction + actual_80c + actual_80d + actual_nps + hra + home_loan + deductions.other_deductions

    # Taxable income (never below basic exemption)
    basic_exemption = 250_000
    if age >= SUPER_SENIOR_CITIZEN_AGE:
        basic_exemption = SUPER_SENIOR_BASIC_EXEMPTION
    elif age >= 60:
        basic_exemption = SENIOR_CITIZEN_BASIC_EXEMPTION

    taxable_income = max(0, gross_income - total_deductions)

    tax = _calculate_slab_tax(taxable_income, OLD_REGIME_SLABS)

    # 87A rebate
    rebate = 0.0
    if taxable_income <= OLD_REGIME_87A_REBATE_LIMIT:
        rebate = min(tax, OLD_REGIME_87A_REBATE_AMOUNT)
        tax = max(0, tax - rebate)

    cess = tax * HEALTH_EDUCATION_CESS
    total_tax = tax + cess
    effective_rate = total_tax / gross_income if gross_income > 0 else 0.0

    if actual_80c < deductions.sec_80c:
        notes.append(f"80C capped at ₹1.5L (you claimed ₹{deductions.sec_80c:,.0f})")

    return TaxResult(
        gross_income=gross_income,
        taxable_income=taxable_income,
        total_deductions=total_deductions,
        tax_before_cess=tax,
        cess=cess,
        total_tax=total_tax,
        effective_rate=round(effective_rate, 4),
        regime="Old Regime",
        rebate_applied=rebate,
        notes=notes,
    )


def compare_tax_regimes(
    gross_income: float,
    deductions: Optional[Deductions] = None,
    age: int = 35,
) -> dict:
    """
    Compare Old vs New regime and recommend the better option.

    Returns:
        Dict with both regime results and recommendation
    """
    new_result = calculate_new_regime_tax(gross_income, age)
    old_result = calculate_old_regime_tax(gross_income, deductions, age)

    savings = old_result.total_tax - new_result.total_tax
    recommended = "New Regime" if new_result.total_tax <= old_result.total_tax else "Old Regime"
    saving_regime = "New Regime" if savings > 0 else "Old Regime"

    return {
        "new_regime": {
            "taxable_income": new_result.taxable_income,
            "total_tax": round(new_result.total_tax),
            "effective_rate_pct": round(new_result.effective_rate * 100, 2),
            "notes": new_result.notes,
        },
        "old_regime": {
            "taxable_income": old_result.taxable_income,
            "total_deductions": round(old_result.total_deductions),
            "total_tax": round(old_result.total_tax),
            "effective_rate_pct": round(old_result.effective_rate * 100, 2),
            "notes": old_result.notes,
        },
        "recommended_regime": recommended,
        "tax_savings_if_switching": round(abs(savings)),
        "better_by": saving_regime,
        "recommendation_note": (
            f"{recommended} saves ₹{abs(savings):,.0f} per year for your income and deduction profile."
        ),
    }


def calculate_ltcg_tax(gains: float) -> dict:
    """
    Calculate LTCG tax on equity gains (Budget 2024: 12.5% above ₹1.25L).

    Args:
        gains: Total long-term capital gains on equity (₹)

    Returns:
        Dict with taxable gains, tax payable, effective rate
    """
    taxable_gains = max(0, gains - EQUITY_LTCG_EXEMPTION)
    tax = taxable_gains * EQUITY_LTCG_RATE
    cess = tax * HEALTH_EDUCATION_CESS

    return {
        "total_ltcg": round(gains),
        "exemption_applied": round(min(gains, EQUITY_LTCG_EXEMPTION)),
        "taxable_ltcg": round(taxable_gains),
        "ltcg_tax": round(tax),
        "cess": round(cess),
        "total_tax": round(tax + cess),
        "effective_rate_pct": round((tax + cess) / gains * 100, 2) if gains > 0 else 0,
        "note": "LTCG on equity at 12.5% (Budget 2024) after ₹1.25L annual exemption",
    }


def calculate_stcg_tax(gains: float) -> dict:
    """
    Calculate STCG tax on equity gains (Budget 2024: 20%).

    Args:
        gains: Short-term capital gains on equity (₹)
    """
    tax = gains * EQUITY_STCG_RATE
    cess = tax * HEALTH_EDUCATION_CESS
    return {
        "total_stcg": round(gains),
        "stcg_tax": round(tax),
        "cess": round(cess),
        "total_tax": round(tax + cess),
        "effective_rate_pct": round(EQUITY_STCG_RATE * 100 + EQUITY_STCG_RATE * HEALTH_EDUCATION_CESS * 100, 2),
        "note": "STCG on equity at 20% (Budget 2024)",
    }


def ltcg_harvesting_opportunity(
    unrealized_gains: float,
    current_fy_realized_gains: float = 0.0,
) -> dict:
    """
    Check if LTCG tax harvesting opportunity exists before March 31.

    Harvest up to ₹1.25L LTCG annually (tax-free) — book gains and reinvest.

    Args:
        unrealized_gains: Current unrealized LTCG in portfolio
        current_fy_realized_gains: Already realized LTCG this FY

    Returns:
        Dict with harvesting recommendation
    """
    remaining_exemption = max(0, EQUITY_LTCG_EXEMPTION - current_fy_realized_gains)
    can_harvest = min(unrealized_gains, remaining_exemption)
    tax_saved = can_harvest * EQUITY_LTCG_RATE

    return {
        "unrealized_gains": round(unrealized_gains),
        "already_realized_this_fy": round(current_fy_realized_gains),
        "remaining_exemption": round(remaining_exemption),
        "harvestable_amount": round(can_harvest),
        "tax_saved_by_harvesting": round(tax_saved),
        "recommendation": (
            f"You can harvest ₹{can_harvest:,.0f} of LTCG tax-free before March 31. "
            f"This saves ₹{tax_saved:,.0f} in taxes."
        ) if can_harvest > 0 else "No LTCG harvesting opportunity available this FY.",
    }
