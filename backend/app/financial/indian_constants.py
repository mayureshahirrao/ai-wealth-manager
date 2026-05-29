"""
indian_constants.py — Single source of truth for all Indian financial parameters.

Update this file when SEBI/RBI/Budget regulations change. Never hardcode financial
rates, limits, or thresholds in business logic — always import from here.

Dependencies: None (Tier 0)
Consumed by: tax_calculator, sip_calculator, goal_engine, compliance_injector,
             all AI tools, risk alert engine, response_validator
"""

from typing import List, Tuple

# ─── Capital Gains Tax (Budget 2024) ────────────────────────────────────────
EQUITY_LTCG_RATE = 0.125           # 12.5% on equity gains held > 12 months
EQUITY_LTCG_HOLDING_MONTHS = 12    # Qualifying holding period
EQUITY_LTCG_EXEMPTION = 125_000    # ₹1.25 lakh annual exemption (Budget 2024)

EQUITY_STCG_RATE = 0.20            # 20% on equity gains held ≤ 12 months
DEBT_MF_TAX_AS_INCOME = True       # Post Apr 2023: debt MF gains taxed as income

CRYPTO_VDA_RATE = 0.30             # 30% flat on Virtual Digital Assets
CRYPTO_VDA_NO_LOSS_OFFSET = True   # VDA losses cannot offset other income

STT_EQUITY_DELIVERY = 0.001        # 0.1% Securities Transaction Tax
STT_EQUITY_INTRADAY = 0.00025      # 0.025% for intraday

HEALTH_EDUCATION_CESS = 0.04       # 4% on income tax + surcharge

# ─── Income Tax Slabs ────────────────────────────────────────────────────────
# Format: (lower_bound, upper_bound, rate)
# New Regime (FY 2024-25, Budget 2023 onwards — DEFAULT regime)
NEW_REGIME_SLABS: List[Tuple[int, float, float]] = [
    (0,         300_000,        0.00),
    (300_000,   700_000,        0.05),
    (700_000,   1_000_000,      0.10),
    (1_000_000, 1_200_000,      0.15),
    (1_200_000, 1_500_000,      0.20),
    (1_500_000, float("inf"),   0.30),
]
NEW_REGIME_STANDARD_DEDUCTION = 75_000  # ₹75K for salaried (Budget 2024)
NEW_REGIME_87A_REBATE_LIMIT = 700_000   # No tax if income ≤ ₹7L (after deductions)
NEW_REGIME_87A_REBATE_AMOUNT = 25_000   # Max rebate ₹25K

# Old Regime
OLD_REGIME_SLABS: List[Tuple[int, float, float]] = [
    (0,         250_000,        0.00),
    (250_000,   500_000,        0.05),
    (500_000,   1_000_000,      0.20),
    (1_000_000, float("inf"),   0.30),
]
OLD_REGIME_STANDARD_DEDUCTION = 50_000  # ₹50K for salaried
OLD_REGIME_87A_REBATE_LIMIT = 500_000   # No tax if income ≤ ₹5L (after deductions)
OLD_REGIME_87A_REBATE_AMOUNT = 12_500   # Max rebate ₹12.5K

# Senior Citizen (>60 years) — Old Regime only
SENIOR_CITIZEN_BASIC_EXEMPTION = 300_000   # ₹3L
SUPER_SENIOR_CITIZEN_AGE = 80              # 80+ = super senior
SUPER_SENIOR_BASIC_EXEMPTION = 500_000     # ₹5L

# Surcharge rates
SURCHARGE_SLABS: List[Tuple[int, float]] = [
    (5_000_000,    0.10),   # 10% if income > ₹50L
    (10_000_000,   0.15),   # 15% if income > ₹1Cr
    (20_000_000,   0.25),   # 25% if income > ₹2Cr (New Regime capped at 25%)
    (50_000_000,   0.37),   # 37% if income > ₹5Cr (Old Regime only)
]
NEW_REGIME_MAX_SURCHARGE = 0.25  # Capped at 25% in new regime

# ─── Deductions (Old Regime) ─────────────────────────────────────────────────
SEC_80C_LIMIT = 150_000            # ₹1.5L — ELSS, PPF, EPF, LIC, NSC, ULIP, etc.
SEC_80D_SELF_BELOW_60 = 25_000     # Health insurance for self (< 60 yrs)
SEC_80D_SELF_ABOVE_60 = 50_000     # Health insurance for self (≥ 60 yrs)
SEC_80D_PARENTS_BELOW_60 = 25_000  # Parents below 60
SEC_80D_PARENTS_ABOVE_60 = 50_000  # Senior citizen parents
SEC_80CCD_1B_NPS = 50_000          # Additional NPS deduction (over 80C)
SEC_80CCD_2_EMPLOYER_NPS = 0.10    # Employer NPS: 10% of basic (no upper limit for old regime)
SEC_80TTA_SAVINGS_INTEREST = 10_000  # Savings bank interest deduction
SEC_80TTB_SENIOR_INTEREST = 50_000   # Senior citizen bank interest deduction
SEC_24B_HOME_LOAN_INTEREST = 200_000  # Self-occupied property interest deduction
SEC_80GG_HRA_NO_EMPLOYER = 60_000    # HRA deduction if no HRA from employer

# ─── NPS (National Pension System) ──────────────────────────────────────────
NPS_TIER1_MIN_ANNUAL = 1_000       # ₹1,000 minimum per year
NPS_EQUITY_MAX_ACTIVE_CHOICE = 0.75  # Max 75% equity in active choice
NPS_ANNUITY_MIN_PERCENT = 0.40     # 40% corpus must buy annuity at retirement
NPS_LUMP_SUM_TAX_FREE = 0.60       # 60% lump sum is tax-free at withdrawal
NPS_RETIREMENT_AGE = 60            # Normal retirement age

# ─── PPF (Public Provident Fund) ─────────────────────────────────────────────
PPF_ANNUAL_RATE = 0.071            # 7.1% p.a. (current, subject to quarterly revision)
PPF_MIN_ANNUAL = 500               # ₹500 minimum per year
PPF_MAX_ANNUAL = 150_000           # ₹1.5L maximum per year (also 80C eligible)
PPF_LOCK_IN_YEARS = 15             # 15-year lock-in (extendable in 5-year blocks)
PPF_PARTIAL_WITHDRAWAL_FROM_YEAR = 7  # Allowed from year 7

# ─── EPF (Employee Provident Fund) ───────────────────────────────────────────
EPF_EMPLOYEE_CONTRIBUTION = 0.12   # 12% of basic salary
EPF_EMPLOYER_CONTRIBUTION = 0.12   # 12% (8.33% EPS + 3.67% EPF)
EPF_INTEREST_RATE = 0.0815         # 8.15% p.a. (FY 2023-24)
EPF_TAX_FREE_INTEREST_THRESHOLD = 250_000  # Interest tax-free up to ₹2.5L contribution/yr

# ─── SCSS (Senior Citizen Savings Scheme) ────────────────────────────────────
SCSS_RATE = 0.0820                 # 8.2% p.a.
SCSS_MAX_INVESTMENT = 3_000_000    # ₹30L maximum
SCSS_TENURE_YEARS = 5              # 5 years (extendable by 3 years)
SCSS_ELIGIBILITY_AGE = 60         # 60+ or 55+ if VRS/superannuation

# ─── Sovereign Gold Bonds ────────────────────────────────────────────────────
SGB_COUPON_RATE = 0.025            # 2.5% annual interest
SGB_MATURITY_YEARS = 8             # 8-year maturity
SGB_PREMATURE_EXIT_YEAR = 5        # Can exit after 5 years (on coupon dates)
SGB_LTCG_ON_MATURITY = False       # Capital gains on maturity are tax-free

# ─── Mutual Fund Categories (AMFI classification) ─────────────────────────────
MF_CATEGORIES = {
    "large_cap": {"equity_pct": 0.80, "min_holding_months": 12, "typical_return": 0.12},
    "mid_cap": {"equity_pct": 0.65, "min_holding_months": 12, "typical_return": 0.15},
    "small_cap": {"equity_pct": 0.65, "min_holding_months": 12, "typical_return": 0.18},
    "flexi_cap": {"equity_pct": 0.65, "min_holding_months": 12, "typical_return": 0.13},
    "elss": {"equity_pct": 0.80, "min_holding_months": 36, "typical_return": 0.14},  # 3yr lock
    "hybrid_balanced": {"equity_pct": 0.60, "min_holding_months": 12, "typical_return": 0.10},
    "balanced_advantage": {"equity_pct": 0.50, "min_holding_months": 12, "typical_return": 0.09},
    "liquid": {"equity_pct": 0.00, "min_holding_months": 0, "typical_return": 0.07},
    "debt_corporate_bond": {"equity_pct": 0.00, "min_holding_months": 36, "typical_return": 0.07},
    "gilt": {"equity_pct": 0.00, "min_holding_months": 36, "typical_return": 0.065},
    "international": {"equity_pct": 1.00, "min_holding_months": 24, "typical_return": 0.10},
}

ELSS_LOCK_IN_MONTHS = 36           # 3-year lock-in from each SIP installment

# ─── Wealth Segments (Indian context) ────────────────────────────────────────
RETAIL_SEGMENT_MAX = 2_500_000             # < ₹25 Lakh
MASS_AFFLUENT_MAX = 10_000_000             # ₹25L – ₹1 Crore
HNW_MAX = 250_000_000                      # ₹1 Cr – ₹25 Crore
UHNW_THRESHOLD = 250_000_000               # > ₹25 Crore

# ─── SIP Defaults ────────────────────────────────────────────────────────────
DEFAULT_EQUITY_RETURN = 0.12       # 12% long-term Nifty 50 CAGR assumption
DEFAULT_DEBT_RETURN = 0.07         # 7% debt fund return
DEFAULT_INFLATION_RATE = 0.06      # 6% India CPI average
DEFAULT_STEP_UP_RATE = 0.10        # 10% annual SIP step-up recommendation

# ─── Risk Profile Thresholds ─────────────────────────────────────────────────
MAX_SINGLE_ASSET_CONCENTRATION = 0.20   # >20% = concentration flag
MAX_CRYPTO_ALLOCATION = 0.20            # >20% = crypto risk flag
MIN_EMERGENCY_FUND_MONTHS = 6           # 6 months expense buffer recommended
EQUITY_MAX_FOR_CONSERVATIVE = 0.30      # >30% equity for conservative profile
EQUITY_MIN_FOR_AGGRESSIVE = 0.70        # <70% equity for aggressive profile

# ─── SEBI Compliance ─────────────────────────────────────────────────────────
SEBI_IA_REGULATION_YEAR = 2013
SEBI_RECORD_RETENTION_YEARS = 5        # IA Regulations: 5-year record keeping
SEBI_KYC_REFRESH_MONTHS = 24           # KYC must be refreshed every 2 years
SEBI_MIN_CONFIDENCE_FOR_RECOMMENDATION = 0.75  # Below this → escalate to human

SEBI_DISCLAIMER = (
    "\n\n---\n"
    "*Disclaimer: This information is generated by an AI assistant for educational "
    "and informational purposes only. It does not constitute investment advice under "
    "SEBI (Investment Advisers) Regulations, 2013. Past performance is not indicative "
    "of future results. Please consult your SEBI-registered investment adviser before "
    "making any investment decisions.*"
)

# ─── Compliance Alert Types ───────────────────────────────────────────────────
ALERT_TYPES = {
    "CONCENTRATION_RISK": "Single asset exceeds 20% of portfolio",
    "CRYPTO_OVERWEIGHT": "Crypto/VDA allocation exceeds 20%",
    "NO_NOMINEE": "Assets without nominee registration",
    "KYC_EXPIRED": "KYC not refreshed in >24 months",
    "ESTATE_GAP": "No Will or trust on record",
    "REVIEW_OVERDUE": "Client not reviewed in >12 months",
    "NPS_NOT_OPENED": "80CCD(1B) deduction unused — NPS not started",
    "FD_OVERWEIGHT": "Fixed deposits >40% — inflation-adjusted return negative",
    "AI_LOW_CONFIDENCE": "AI recommendation confidence below threshold",
    "ELSS_LOCK_IN": "ELSS redemption attempted before 3-year lock-in",
}

# ─── LRS (Liberalized Remittance Scheme) for international investing ──────────
LRS_ANNUAL_LIMIT_USD = 250_000     # $250,000 per financial year
LRS_TCS_RATE = 0.20                # 20% TCS on LRS > ₹7L (from Oct 2023)
LRS_TCS_THRESHOLD = 700_000        # TCS applies above ₹7L
