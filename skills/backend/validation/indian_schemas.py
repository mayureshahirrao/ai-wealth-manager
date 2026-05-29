"""
indian_schemas.py — Pydantic base schemas for Indian financial data.

All API request/response schemas for Indian financial data should
inherit from or reference these base schemas for consistent validation.

Dependencies: pan_validator.py, indian_constants.py (Tier 4)
Consumed by: All API route schemas
"""

from datetime import date
from typing import Optional, Annotated
from pydantic import BaseModel, Field, field_validator, model_validator

from skills.backend.validation.pan_validator import validate_pan, mask_pan
from skills.backend.database.base_model import RiskProfile, TaxRegime, AssetClass, GoalType
from skills.backend.financial.indian_constants import (
    RETAIL_SEGMENT_MAX, MASS_AFFLUENT_MAX, HNW_MAX,
)


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_name: str
    client_id: Optional[str] = None  # Set for investor role


# ─── Client Profile Schemas ───────────────────────────────────────────────────

class ClientSummarySchema(BaseModel):
    """Brief client profile for list views."""
    id: str
    name: str
    age: int
    city: str
    segment: str           # "Retail" | "Mass Affluent" | "HNW"
    portfolio_value_lakhs: float
    risk_profile: RiskProfile
    tax_regime: TaxRegime
    xirr_pct: Optional[float] = None
    last_reviewed_days_ago: Optional[int] = None
    active_sips_count: int = 0
    alert_count: int = 0

    @classmethod
    def get_segment(cls, portfolio_value: float) -> str:
        if portfolio_value < RETAIL_SEGMENT_MAX:
            return "Retail"
        elif portfolio_value < MASS_AFFLUENT_MAX:
            return "Mass Affluent"
        elif portfolio_value < HNW_MAX:
            return "HNW"
        return "UHNW"


class ClientDetailSchema(ClientSummarySchema):
    """Full client profile for detail views."""
    pan_masked: Optional[str] = None
    annual_income: Optional[float] = None
    employer_type: Optional[str] = None  # "salaried" | "self_employed" | "business"
    has_will: bool = False
    has_nominee_all_assets: bool = False
    kyc_status: str = "verified"
    goals_count: int = 0


# ─── Portfolio Schemas ────────────────────────────────────────────────────────

class HoldingSchema(BaseModel):
    """Single holding (MF scheme or stock)."""
    symbol: str
    scheme_name: str
    asset_class: AssetClass
    units: float
    current_nav: float
    current_value: float
    invested_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    allocation_pct: float
    holding_period_months: Optional[int] = None
    is_ltcg_eligible: bool = False  # Held > 12 months
    has_sip_active: bool = False


class PortfolioSummarySchema(BaseModel):
    """Complete portfolio summary."""
    client_id: str
    total_value: float
    total_value_lakhs: float
    invested_value: float
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float
    xirr_pct: Optional[float] = None
    holdings: list[HoldingSchema]
    allocation_by_asset_class: dict[str, float]  # {"equity": 0.55, "debt": 0.30, ...}
    active_sips_monthly_total: float
    as_of_date: date
    benchmark_xirr_pct: Optional[float] = None   # Nifty 50 XIRR for same period


# ─── Goal Schemas ─────────────────────────────────────────────────────────────

class GoalSchema(BaseModel):
    """A single financial goal."""
    id: str
    goal_type: GoalType
    goal_name: str
    target_amount: float
    target_date: date
    current_corpus: float
    monthly_sip: float
    feasibility_score: int
    status: str
    progress_pct: float


# ─── Chat / AI Schemas ────────────────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
    """Incoming chat message from investor."""
    client_id: str
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: Optional[str] = None  # For continuing a conversation


class AuditLogEntrySchema(BaseModel):
    """SEBI audit log entry for AI interactions."""
    id: str
    client_id: str
    client_name: str
    query: str
    response_preview: str
    tools_used: list[str]
    confidence_score: float
    query_type: str
    sebi_compliant: bool
    created_at: str


# ─── Compliance Schemas ───────────────────────────────────────────────────────

class RiskAlertSchema(BaseModel):
    """A compliance risk alert for a client."""
    id: str
    client_id: str
    client_name: str
    alert_type: str
    priority: str
    description: str
    regulation_reference: Optional[str] = None
    created_at: str
    is_resolved: bool = False


class ComplianceDocRequest(BaseModel):
    """Request to generate a compliance document."""
    client_id: str
    doc_type: str  # "sebi_disclosure" | "risk_profile" | "suitability_attestation"


# ─── Market Data Schemas ──────────────────────────────────────────────────────

class MarketDataPoint(BaseModel):
    """Single NAV/price data point."""
    symbol: str
    date: date
    nav: float
    change_pct: float


class NAVHistorySchema(BaseModel):
    """Historical NAV data for charts."""
    symbol: str
    scheme_name: str
    data_points: list[dict]  # [{"date": "2024-01-01", "nav": 45.23}, ...]
