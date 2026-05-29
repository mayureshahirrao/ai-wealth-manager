"""
mock_data.py — Canonical mock data for all 5 Indian client personas.

Use this data in:
- pytest fixtures (consistent test baseline)
- Database seed scripts (demo data)
- Agent test cases (predictable tool outputs)

Dependencies: indian_constants.py, currency_formatter.py (Tier 5)
Consumed by: fixtures.py, seed_data.py, agent_tester.py
"""

from datetime import date
from typing import Any


# ─── Demo Credentials ──────────────────────────────────────────────────────────
DEMO_CREDENTIALS = {
    "investor": [
        {"email": "priya.sharma@demo.com", "password": "demo1234", "client_id": "cli-001"},
        {"email": "rajesh.gupta@demo.com", "password": "demo1234", "client_id": "cli-002"},
        {"email": "neha.khanna@demo.com", "password": "demo1234", "client_id": "cli-003"},
        {"email": "aarav.singh@demo.com", "password": "demo1234", "client_id": "cli-004"},
        {"email": "sushma.reddy@demo.com", "password": "demo1234", "client_id": "cli-005"},
    ],
    "rm": [
        {"email": "rm@demo.com", "password": "demo1234"},
    ],
    "compliance": [
        {"email": "compliance@demo.com", "password": "demo1234"},
    ],
}

# ─── Client Personas ─────────────────────────────────────────────────────────

MOCK_CLIENTS: list[dict[str, Any]] = [
    {
        "id": "cli-001",
        "name": "Priya Sharma",
        "age": 32,
        "city": "Bengaluru",
        "state": "Karnataka",
        "occupation": "Software Engineer",
        "employer": "MNC Tech Company",
        "employer_type": "salaried",
        "annual_income": 1_800_000,      # ₹18 LPA
        "tax_regime": "old",
        "risk_profile": "moderately_aggressive",
        "pan": "ABCPS1234P",
        "kyc_status": "verified",
        "has_will": False,
        "has_nominee_all_assets": True,
        "last_reviewed_days_ago": 45,
        "segment": "Mass Affluent",
        "total_portfolio_value": 4_200_000,    # ₹42 Lakh
        "monthly_savings_capacity": 35_000,
    },
    {
        "id": "cli-002",
        "name": "Rajesh Gupta",
        "age": 47,
        "city": "Mumbai",
        "state": "Maharashtra",
        "occupation": "VP, PSU Bank",
        "employer": "State Bank of India",
        "employer_type": "salaried",
        "annual_income": 2_400_000,      # ₹24 LPA
        "tax_regime": "old",
        "risk_profile": "conservative",
        "pan": "ABRPG5678Q",
        "kyc_status": "verified",
        "has_will": False,
        "has_nominee_all_assets": False,  # Alert: incomplete nominees
        "last_reviewed_days_ago": 420,    # Alert: overdue review
        "segment": "Mass Affluent",
        "total_portfolio_value": 8_800_000,   # ₹88 Lakh
        "monthly_savings_capacity": 60_000,
    },
    {
        "id": "cli-003",
        "name": "Neha Khanna",
        "age": 35,
        "city": "Pune",
        "state": "Maharashtra",
        "occupation": "Product Manager",
        "employer": "Fintech Startup",
        "employer_type": "salaried",
        "annual_income": 3_200_000,      # ₹32 LPA
        "tax_regime": "new",
        "risk_profile": "aggressive",
        "pan": "ACPNK9012R",
        "kyc_status": "verified",
        "has_will": False,
        "has_nominee_all_assets": True,
        "last_reviewed_days_ago": 90,
        "segment": "HNW",
        "total_portfolio_value": 13_500_000,  # ₹1.35 Crore
        "monthly_savings_capacity": 80_000,
    },
    {
        "id": "cli-004",
        "name": "Aarav Singh",
        "age": 24,
        "city": "Delhi",
        "state": "Delhi",
        "occupation": "Data Analyst",
        "employer": "Analytics Startup",
        "employer_type": "salaried",
        "annual_income": 800_000,        # ₹8 LPA
        "tax_regime": "new",
        "risk_profile": "aggressive",
        "pan": "ADPAS3456S",
        "kyc_status": "verified",
        "has_will": False,
        "has_nominee_all_assets": False,  # Alert: no nominees
        "last_reviewed_days_ago": 30,
        "segment": "Retail",
        "total_portfolio_value": 720_000,     # ₹7.2 Lakh
        "monthly_savings_capacity": 12_000,
    },
    {
        "id": "cli-005",
        "name": "Sushma Reddy",
        "age": 63,
        "city": "Hyderabad",
        "state": "Telangana",
        "occupation": "Retired",
        "employer": "Government School",
        "employer_type": "retired",
        "annual_income": 756_000,        # ₹63K/month pension + SCSS interest
        "tax_regime": "old",
        "risk_profile": "conservative",
        "pan": "AEPSR7890T",
        "kyc_status": "refresh_required",  # Alert: KYC due
        "has_will": False,                  # Alert: estate gap
        "has_nominee_all_assets": False,    # Alert: missing nominees
        "last_reviewed_days_ago": 180,
        "segment": "HNW",
        "total_portfolio_value": 23_000_000,  # ₹2.3 Crore
        "monthly_savings_capacity": 0,
    },
]


# ─── Mock Portfolios ──────────────────────────────────────────────────────────

MOCK_PORTFOLIOS: dict[str, list[dict]] = {
    "cli-001": [
        {"symbol": "NIFTY50_IDX", "scheme_name": "Nippon India Nifty 50 BeES",
         "asset_class": "equity", "units": 350.5, "current_nav": 240.20,
         "invested_value": 700_000, "allocation_pct": 0.40},
        {"symbol": "AXIS_ELSS", "scheme_name": "Axis Long Term Equity Fund",
         "asset_class": "equity", "units": 1200.0, "current_nav": 70.15,
         "invested_value": 700_000, "allocation_pct": 0.20},
        {"symbol": "PPF", "scheme_name": "Public Provident Fund",
         "asset_class": "debt", "units": 1, "current_nav": 630_000,
         "invested_value": 630_000, "allocation_pct": 0.15},
        {"symbol": "HDFC_FD", "scheme_name": "HDFC Bank Fixed Deposit",
         "asset_class": "debt", "units": 1, "current_nav": 630_000,
         "invested_value": 630_000, "allocation_pct": 0.15},
        {"symbol": "SGB_2028", "scheme_name": "Sovereign Gold Bond 2028",
         "asset_class": "gold", "units": 5.0, "current_nav": 84_000,
         "invested_value": 350_000, "allocation_pct": 0.10},
    ],
    "cli-002": [
        {"symbol": "HDFC_FD", "scheme_name": "HDFC Bank Fixed Deposit",
         "asset_class": "debt", "units": 1, "current_nav": 4_840_000,
         "invested_value": 4_000_000, "allocation_pct": 0.55},
        {"symbol": "LIC_ENDOW", "scheme_name": "LIC Endowment Policy",
         "asset_class": "debt", "units": 1, "current_nav": 1_760_000,
         "invested_value": 2_200_000, "allocation_pct": 0.20},
        {"symbol": "PPF", "scheme_name": "Public Provident Fund",
         "asset_class": "debt", "units": 1, "current_nav": 1_320_000,
         "invested_value": 1_200_000, "allocation_pct": 0.15},
        {"symbol": "NIFTY50_IDX", "scheme_name": "Nippon India Nifty 50 BeES",
         "asset_class": "equity", "units": 370.0, "current_nav": 240.20,
         "invested_value": 800_000, "allocation_pct": 0.10},
    ],
    "cli-004": [
        {"symbol": "CRYPTO_BTC", "scheme_name": "Bitcoin (via CoinDCX)",
         "asset_class": "crypto", "units": 0.005, "current_nav": 5_800_000,
         "invested_value": 250_000, "allocation_pct": 0.40},
        {"symbol": "ZOMATO", "scheme_name": "Zomato Ltd",
         "asset_class": "equity", "units": 500.0, "current_nav": 280.00,
         "invested_value": 120_000, "allocation_pct": 0.20},
        {"symbol": "NIFTY_SMALLCAP", "scheme_name": "SBI Small Cap Fund",
         "asset_class": "equity", "units": 200.0, "current_nav": 120.00,
         "invested_value": 200_000, "allocation_pct": 0.28},
        {"symbol": "LIQUID_FUND", "scheme_name": "SBI Liquid Fund",
         "asset_class": "cash", "units": 10.0, "current_nav": 3_800.00,
         "invested_value": 35_000, "allocation_pct": 0.05},
    ],
}


# ─── Mock Goals ───────────────────────────────────────────────────────────────

MOCK_GOALS: dict[str, list[dict]] = {
    "cli-001": [
        {
            "id": "goal-001-01",
            "goal_type": "home_purchase",
            "goal_name": "2BHK in Bengaluru",
            "target_amount": 8_000_000,     # ₹80L
            "target_date": date(2029, 6, 1),  # 5 years
            "current_corpus": 500_000,
            "monthly_sip": 15_000,
        },
        {
            "id": "goal-001-02",
            "goal_type": "retirement",
            "goal_name": "Retire at 55",
            "target_amount": 30_000_000,    # ₹3 Crore
            "target_date": date(2047, 3, 1),  # 23 years
            "current_corpus": 1_200_000,
            "monthly_sip": 10_000,
        },
    ],
    "cli-004": [
        {
            "id": "goal-004-01",
            "goal_type": "wealth_creation",
            "goal_name": "₹1 Crore before 35",
            "target_amount": 10_000_000,   # ₹1 Crore
            "target_date": date(2035, 12, 1),
            "current_corpus": 720_000,
            "monthly_sip": 8_000,
        },
    ],
}


# ─── Expected AI Tool Responses (for agent testing) ──────────────────────────

EXPECTED_TOOL_OUTPUTS = {
    "get_portfolio_summary_cli-001": {
        "client_id": "cli-001",
        "total_value_lakhs": 42.0,
        "total_value": 4_200_000,
        "xirr_pct": 13.4,
        "holdings_count": 5,
        "top_asset_class": "equity",
    },
    "calculate_tax_liability_cli-001": {
        "recommended_regime": "Old Regime",
        "recommended_regime_tax_lakhs": 2.1,
        "new_regime_tax_lakhs": 2.4,
        "savings_by_old_regime": 30_000,
    },
}
