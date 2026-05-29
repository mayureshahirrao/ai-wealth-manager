"""
models.py — All SQLAlchemy ORM table definitions.

Every table in the system is defined here. Import WealthBase into alembic/env.py
so autogenerate can detect all models.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey,
    Integer, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base_model import (
    WealthBase, UserRole, RiskProfile, TaxRegime,
    AssetClass, GoalType, TransactionType, AlertType, AlertPriority, ComplianceDocType
)
from sqlalchemy import Enum as SAEnum


def _enum(enum_class):
    """SQLAlchemy 2.x uses enum .name by default; force it to use .value instead."""
    return SAEnum(enum_class, values_callable=lambda x: [e.value for e in x])


# ─── Users ────────────────────────────────────────────────────────────────────

class User(WealthBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(_enum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Only set for investor role
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True
    )

    client: Mapped[Optional["Client"]] = relationship("Client", back_populates="user")


# ─── Clients ──────────────────────────────────────────────────────────────────

class Client(WealthBase):
    __tablename__ = "clients"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    pan: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    risk_profile: Mapped[RiskProfile] = mapped_column(
        _enum(RiskProfile), default=RiskProfile.MODERATE, nullable=False
    )
    tax_regime: Mapped[TaxRegime] = mapped_column(
        _enum(TaxRegime), default=TaxRegime.NEW, nullable=False
    )
    annual_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rm_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_review_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    kyc_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="client")
    portfolio: Mapped[Optional["Portfolio"]] = relationship("Portfolio", back_populates="client", uselist=False)
    goals: Mapped[list["Goal"]] = relationship("Goal", back_populates="client")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="client")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="client")
    chat_messages: Mapped[list["ChatMessage"]] = relationship("ChatMessage", back_populates="client")
    ai_audit_logs: Mapped[list["AIAuditLog"]] = relationship("AIAuditLog", back_populates="client")


# ─── Portfolio + Holdings ─────────────────────────────────────────────────────

class Portfolio(WealthBase):
    __tablename__ = "portfolios"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, unique=True, index=True
    )
    total_invested: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    current_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    xirr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    benchmark_xirr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_calculated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    client: Mapped["Client"] = relationship("Client", back_populates="portfolio")
    holdings: Mapped[list["Holding"]] = relationship("Holding", back_populates="portfolio")
    nav_history: Mapped[list["NAVHistory"]] = relationship("NAVHistory", back_populates="portfolio")


class Holding(WealthBase):
    __tablename__ = "holdings"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True
    )
    scheme_name: Mapped[str] = mapped_column(String(200), nullable=False)
    isin: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    folio_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    asset_class: Mapped[AssetClass] = mapped_column(_enum(AssetClass), nullable=False)
    units: Mapped[float] = mapped_column(Float, nullable=False)
    nav: Mapped[float] = mapped_column(Float, nullable=False)
    invested_amount: Mapped[float] = mapped_column(Float, nullable=False)
    current_value: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sip_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    has_sip_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="holdings")


class NAVHistory(WealthBase):
    __tablename__ = "nav_history"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True
    )
    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    portfolio_value: Mapped[float] = mapped_column(Float, nullable=False)
    benchmark_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="nav_history")


# ─── Goals ────────────────────────────────────────────────────────────────────

class Goal(WealthBase):
    __tablename__ = "goals"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    goal_name: Mapped[str] = mapped_column(String(100), nullable=False)
    goal_type: Mapped[GoalType] = mapped_column(_enum(GoalType), nullable=False)
    target_amount: Mapped[float] = mapped_column(Float, nullable=False)
    current_corpus: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    monthly_sip: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    target_year: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    client: Mapped["Client"] = relationship("Client", back_populates="goals")


# ─── Transactions ─────────────────────────────────────────────────────────────

class Transaction(WealthBase):
    __tablename__ = "transactions"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    scheme_name: Mapped[str] = mapped_column(String(200), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(_enum(TransactionType), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    units: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nav: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    client: Mapped["Client"] = relationship("Client", back_populates="transactions")


# ─── Alerts ───────────────────────────────────────────────────────────────────

class Alert(WealthBase):
    __tablename__ = "alerts"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    alert_type: Mapped[AlertType] = mapped_column(_enum(AlertType), nullable=False)
    priority: Mapped[AlertPriority] = mapped_column(_enum(AlertPriority), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    client: Mapped["Client"] = relationship("Client", back_populates="alerts")


# ─── Chat Messages ────────────────────────────────────────────────────────────

class ChatMessage(WealthBase):
    __tablename__ = "chat_messages"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tools_used: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    client: Mapped["Client"] = relationship("Client", back_populates="chat_messages")


# ─── AI Audit Log (SEBI Requirement) ─────────────────────────────────────────

class AIAuditLog(WealthBase):
    __tablename__ = "ai_audit_logs"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    ai_response_summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    disclaimer_injected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sebi_compliant: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    client: Mapped["Client"] = relationship("Client", back_populates="ai_audit_logs")


# ─── Compliance Documents ─────────────────────────────────────────────────────

class ComplianceDocument(WealthBase):
    __tablename__ = "compliance_documents"

    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True, index=True
    )
    doc_type: Mapped[ComplianceDocType] = mapped_column(_enum(ComplianceDocType), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    generated_by: Mapped[str] = mapped_column(String(50), default="ai", nullable=False)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
