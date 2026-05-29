"""
base_model.py — SQLAlchemy declarative base with common fields.

All ORM models must inherit from WealthBase. This provides:
- UUID primary key (auto-generated)
- created_at / updated_at timestamps (auto-managed by DB)
- __repr__ for clean debugging output

Dependencies: config.py (Tier 2)
Consumed by: All ORM model definitions
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class WealthBase(DeclarativeBase):
    """
    Declarative base class for all SQLAlchemy models.

    Usage:
        from skills.backend.database.base_model import WealthBase

        class Client(WealthBase):
            __tablename__ = "clients"
            name: Mapped[str] = mapped_column(String(100))
            # id, created_at, updated_at are inherited
    """

    # Shared columns on every table
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary (excludes SQLAlchemy internals)."""
        return {
            col.name: getattr(self, col.name)
            for col in self.__table__.columns
        }


# ─── Enum Values (shared across models) ──────────────────────────────────────
from enum import Enum


class UserRole(str, Enum):
    INVESTOR = "investor"
    RM = "rm"                   # Relationship Manager
    COMPLIANCE = "compliance"


class RiskProfile(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    MODERATELY_AGGRESSIVE = "moderately_aggressive"
    AGGRESSIVE = "aggressive"


class TaxRegime(str, Enum):
    OLD = "old"
    NEW = "new"


class AssetClass(str, Enum):
    EQUITY = "equity"
    DEBT = "debt"
    GOLD = "gold"
    INTERNATIONAL = "international"
    CASH = "cash"
    REAL_ESTATE = "real_estate"
    CRYPTO = "crypto"


class GoalType(str, Enum):
    RETIREMENT = "retirement"
    HOME_PURCHASE = "home_purchase"
    CHILD_EDUCATION = "child_education"
    EMERGENCY_FUND = "emergency_fund"
    VACATION = "vacation"
    WEALTH_CREATION = "wealth_creation"
    OTHER = "other"


class TransactionType(str, Enum):
    SIP = "sip"
    LUMPSUM_BUY = "lumpsum_buy"
    REDEMPTION = "redemption"
    SWITCH_IN = "switch_in"
    SWITCH_OUT = "switch_out"
    DIVIDEND = "dividend"


class AlertType(str, Enum):
    CONCENTRATION_RISK = "CONCENTRATION_RISK"
    CRYPTO_OVERWEIGHT = "CRYPTO_OVERWEIGHT"
    NO_NOMINEE = "NO_NOMINEE"
    KYC_EXPIRED = "KYC_EXPIRED"
    ESTATE_GAP = "ESTATE_GAP"
    REVIEW_OVERDUE = "REVIEW_OVERDUE"
    NPS_NOT_OPENED = "NPS_NOT_OPENED"
    FD_OVERWEIGHT = "FD_OVERWEIGHT"
    AI_LOW_CONFIDENCE = "AI_LOW_CONFIDENCE"


class AlertPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComplianceDocType(str, Enum):
    SEBI_DISCLOSURE = "sebi_disclosure"
    RISK_PROFILE = "risk_profile"
    SUITABILITY_ATTESTATION = "suitability_attestation"
    KYC_RECORD = "kyc_record"
    MEETING_SUMMARY = "meeting_summary"
