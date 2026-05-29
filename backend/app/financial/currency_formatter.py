"""
currency_formatter.py — Indian currency formatting utilities.

Indian convention: lakhs and crores, not millions and billions.
₹10,00,000 = ₹10 Lakh; ₹1,00,00,000 = ₹1 Crore

Dependencies: None (Tier 0)
Consumed by: All financial tool outputs, AI responses, frontend formatters
"""


def format_inr(amount: float, decimal_places: int = 2) -> str:
    """
    Format amount in INR using Indian convention (Lakh/Crore).

    Examples:
        format_inr(500000)       → "₹5.00 L"
        format_inr(10000000)     → "₹1.00 Cr"
        format_inr(25000000)     → "₹2.50 Cr"
        format_inr(95000)        → "₹95,000"
        format_inr(1250, 0)      → "₹1,250"

    Args:
        amount: Amount in INR (can be negative)
        decimal_places: Decimal places for lakh/crore display

    Returns:
        Formatted string with ₹ symbol
    """
    sign = "-" if amount < 0 else ""
    abs_amount = abs(amount)

    if abs_amount >= 10_000_000:  # 1 crore = 10,000,000
        value = abs_amount / 10_000_000
        return f"{sign}₹{value:.{decimal_places}f} Cr"
    elif abs_amount >= 100_000:   # 1 lakh = 100,000
        value = abs_amount / 100_000
        return f"{sign}₹{value:.{decimal_places}f} L"
    else:
        return f"{sign}₹{abs_amount:,.{0 if decimal_places == 0 else decimal_places}f}"


def format_inr_indian_numbering(amount: float) -> str:
    """
    Format amount using Indian numbering system (commas at 2-2-3).

    Examples:
        1000000    → "₹10,00,000"
        10000000   → "₹1,00,00,000"
        250000     → "₹2,50,000"
    """
    sign = "-" if amount < 0 else ""
    abs_amount = int(abs(amount))
    s = str(abs_amount)

    if len(s) <= 3:
        return f"{sign}₹{s}"

    # Indian number grouping: last 3 digits, then groups of 2
    last_three = s[-3:]
    rest = s[:-3]

    groups = []
    while rest:
        groups.append(rest[-2:])
        rest = rest[:-2]

    groups.reverse()
    formatted = ",".join(groups) + "," + last_three
    return f"{sign}₹{formatted}"


def amount_to_words(amount: float) -> str:
    """
    Convert amount to Indian-style words.

    Examples:
        42_00_000  → "42 Lakh"
        1_50_00_000 → "1 Crore 50 Lakh"
        500         → "500"
    """
    abs_amount = abs(amount)
    prefix = "minus " if amount < 0 else ""

    crores = int(abs_amount // 10_000_000)
    remaining = abs_amount % 10_000_000
    lakhs = int(remaining // 100_000)
    remainder = int(remaining % 100_000)

    parts = []
    if crores:
        parts.append(f"{crores} Crore")
    if lakhs:
        parts.append(f"{lakhs} Lakh")
    if remainder and not crores:
        parts.append(f"{remainder:,}")

    if not parts:
        return f"{prefix}₹0"

    return f"{prefix}₹" + " ".join(parts)


def lakhs(amount: float) -> float:
    """Convert rupees to lakhs (for calculations)."""
    return amount / 100_000


def crores(amount: float) -> float:
    """Convert rupees to crores (for calculations)."""
    return amount / 10_000_000


def from_lakhs(amount_in_lakhs: float) -> float:
    """Convert lakh value to rupees."""
    return amount_in_lakhs * 100_000


def from_crores(amount_in_crores: float) -> float:
    """Convert crore value to rupees."""
    return amount_in_crores * 10_000_000
