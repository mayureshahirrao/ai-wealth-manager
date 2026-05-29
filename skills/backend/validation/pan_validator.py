"""
pan_validator.py — Indian PAN card format validation.

PAN format: AAAAA9999A
- Characters 1-3: Any letter (A-Z)
- Character 4: Taxpayer type (P=Person, C=Company, H=HUF, F=Firm, etc.)
- Character 5: First letter of surname (for individuals)
- Characters 6-9: Digits (0-9)
- Character 10: Any letter (A-Z)

Dependencies: None (Tier 0)
Consumed by: Client onboarding, KYC validation
"""

import re


PAN_REGEX = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")

TAXPAYER_CODES = {
    "P": "Individual Person",
    "C": "Company",
    "H": "Hindu Undivided Family (HUF)",
    "F": "Firm",
    "A": "Association of Persons (AOP)",
    "T": "Trust",
    "B": "Body of Individuals (BOI)",
    "L": "Local Authority",
    "J": "Artificial Juridical Person",
    "G": "Government",
}


def validate_pan(pan: str) -> bool:
    """
    Validate Indian PAN card format.

    Args:
        pan: PAN string (will be uppercased before validation)

    Returns:
        True if valid format, False otherwise

    Examples:
        validate_pan("ABCDE1234F")  → True
        validate_pan("abcde1234f")  → True (normalized)
        validate_pan("1234ABCDE5") → False
        validate_pan("ABCDE12345") → False (last char must be letter)
    """
    if not pan or not isinstance(pan, str):
        return False
    return bool(PAN_REGEX.match(pan.upper().strip()))


def get_taxpayer_type(pan: str) -> str:
    """
    Extract taxpayer type from PAN's 4th character.

    Args:
        pan: Valid PAN string

    Returns:
        Human-readable taxpayer type or "Unknown"
    """
    if not validate_pan(pan):
        return "Invalid PAN"
    return TAXPAYER_CODES.get(pan[3].upper(), "Unknown")


def mask_pan(pan: str) -> str:
    """
    Mask PAN for display (show only last 4 characters).

    Example: "ABCDE1234F" → "XXXXXX234F"
    """
    if not pan or len(pan) < 4:
        return "XXXXXXXXXX"
    return "X" * (len(pan) - 4) + pan[-4:].upper()
