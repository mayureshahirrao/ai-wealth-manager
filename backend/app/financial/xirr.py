"""
xirr.py — XIRR (Extended Internal Rate of Return) calculator.

XIRR is the standard performance metric for SIP portfolios in India.
Unlike CAGR, XIRR accounts for irregular cash flow timing (each SIP installment
is a separate cash flow with its own date).

Dependencies: None (Tier 0)
Consumed by: Portfolio tools, performance calculator
"""

from datetime import date
from typing import Optional
import math


def xirr(
    cash_flows: list[tuple[date, float]],
    guess: float = 0.1,
    max_iterations: int = 100,
    tolerance: float = 1e-6,
) -> Optional[float]:
    """
    Calculate XIRR for a series of dated cash flows.

    Convention:
    - Investments (SIP, lumpsum) are NEGATIVE values
    - Redemptions and current portfolio value are POSITIVE values

    Args:
        cash_flows: List of (date, amount) tuples
                    Example: [(2022-01-01, -5000), (2022-02-01, -5000), (2024-01-01, +120000)]
        guess: Initial guess for the rate (default 10%)
        max_iterations: Newton-Raphson iteration limit
        tolerance: Convergence tolerance

    Returns:
        Annualized XIRR as a decimal (e.g., 0.142 = 14.2%)
        Returns None if calculation fails to converge

    Example:
        flows = [
            (date(2022, 1, 1), -10000),   # Jan SIP
            (date(2022, 2, 1), -10000),   # Feb SIP
            (date(2024, 1, 1), +25000),   # Current value
        ]
        rate = xirr(flows)  # e.g., 0.138 (13.8% XIRR)
    """
    if len(cash_flows) < 2:
        return None

    dates = [cf[0] for cf in cash_flows]
    amounts = [cf[1] for cf in cash_flows]
    base_date = dates[0]

    def _npv(rate: float) -> float:
        """Net Present Value at given rate."""
        return sum(
            amount / (1 + rate) ** ((d - base_date).days / 365.0)
            for d, amount in zip(dates, amounts)
        )

    def _npv_derivative(rate: float) -> float:
        """Derivative of NPV for Newton-Raphson."""
        return sum(
            -((d - base_date).days / 365.0) * amount / (1 + rate) ** ((d - base_date).days / 365.0 + 1)
            for d, amount in zip(dates, amounts)
        )

    # Newton-Raphson iteration
    rate = guess
    for _ in range(max_iterations):
        npv = _npv(rate)
        npv_deriv = _npv_derivative(rate)

        if abs(npv_deriv) < 1e-10:
            break

        new_rate = rate - npv / npv_deriv

        if abs(new_rate - rate) < tolerance:
            return round(new_rate, 6)

        rate = new_rate

        # Guard against divergence
        if rate < -0.99 or rate > 100 or math.isnan(rate):
            break

    # Fallback: try bisection if Newton-Raphson failed
    return _xirr_bisection(dates, amounts, base_date)


def _xirr_bisection(
    dates: list[date],
    amounts: list[float],
    base_date: date,
    low: float = -0.99,
    high: float = 10.0,
    tolerance: float = 1e-6,
    max_iterations: int = 200,
) -> Optional[float]:
    """Bisection fallback for XIRR convergence."""

    def npv(r):
        return sum(
            a / (1 + r) ** ((d - base_date).days / 365.0)
            for d, a in zip(dates, amounts)
        )

    try:
        f_low, f_high = npv(low), npv(high)
        if f_low * f_high > 0:
            return None

        for _ in range(max_iterations):
            mid = (low + high) / 2
            f_mid = npv(mid)
            if abs(f_mid) < tolerance or (high - low) / 2 < tolerance:
                return round(mid, 6)
            if f_low * f_mid < 0:
                high = mid
            else:
                low, f_low = mid, f_mid
        return round((low + high) / 2, 6)
    except Exception:
        return None


def xirr_from_sip_history(
    sip_amount: float,
    sip_start_date: date,
    sip_frequency_months: int,
    current_value: float,
    current_date: date,
) -> Optional[float]:
    """
    Calculate XIRR for a regular SIP investment.

    Convenience function for the common case of monthly SIP.

    Args:
        sip_amount: Monthly SIP amount (positive, e.g. 5000)
        sip_start_date: Date of first SIP
        sip_frequency_months: 1 for monthly, 3 for quarterly
        current_value: Current portfolio value (positive)
        current_date: Today's date

    Returns:
        XIRR as decimal or None
    """
    from dateutil.relativedelta import relativedelta

    cash_flows = []
    d = sip_start_date
    while d <= current_date:
        cash_flows.append((d, -sip_amount))
        d += relativedelta(months=sip_frequency_months)

    # Add current portfolio value as final positive cash flow
    cash_flows.append((current_date, current_value))

    return xirr(cash_flows)


def xirr_to_display(rate: Optional[float]) -> str:
    """Format XIRR for display (e.g., 0.142 → '14.20%')."""
    if rate is None:
        return "N/A"
    return f"{rate * 100:.2f}%"
