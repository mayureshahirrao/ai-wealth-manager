"""initial_schema

Revision ID: 001
Revises:
Create Date: 2026-05-29

Full schema for AI Wealth Manager — all 11 tables + 9 PostgreSQL enum types.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enum types are created automatically by SQLAlchemy when create_table runs.

    # ── clients (create before users — users FK → clients) ────────────────────
    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("pan", sa.String(10), nullable=True),
        sa.Column("phone", sa.String(15), nullable=True),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("age", sa.Integer, nullable=True),
        sa.Column("risk_profile", sa.Enum("conservative", "moderate", "moderately_aggressive", "aggressive", name="riskprofile"), nullable=False, server_default="moderate"),
        sa.Column("tax_regime", sa.Enum("old", "new", name="taxregime"), nullable=False, server_default="new"),
        sa.Column("annual_income", sa.Float, nullable=True),
        sa.Column("rm_notes", sa.Text, nullable=True),
        sa.Column("last_review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("kyc_verified", sa.Boolean, default=False, nullable=False, server_default=sa.false()),
    )

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("investor", "rm", "compliance", name="userrole"), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=True),
    )

    # ── portfolios ────────────────────────────────────────────────────────────
    op.create_table(
        "portfolios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False, unique=True, index=True),
        sa.Column("total_invested", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("current_value", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("xirr", sa.Float, nullable=True),
        sa.Column("benchmark_xirr", sa.Float, nullable=True),
        sa.Column("last_calculated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── holdings ──────────────────────────────────────────────────────────────
    op.create_table(
        "holdings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portfolios.id"), nullable=False, index=True),
        sa.Column("scheme_name", sa.String(200), nullable=False),
        sa.Column("isin", sa.String(20), nullable=True),
        sa.Column("folio_number", sa.String(50), nullable=True),
        sa.Column("asset_class", sa.Enum("equity", "debt", "gold", "international", "cash", "real_estate", "crypto", name="assetclass"), nullable=False),
        sa.Column("units", sa.Float, nullable=False),
        sa.Column("nav", sa.Float, nullable=False),
        sa.Column("invested_amount", sa.Float, nullable=False),
        sa.Column("current_value", sa.Float, nullable=False),
        sa.Column("purchase_date", sa.Date, nullable=True),
        sa.Column("sip_amount", sa.Float, nullable=True),
        sa.Column("has_sip_active", sa.Boolean, nullable=False, server_default=sa.false()),
    )

    # ── nav_history ───────────────────────────────────────────────────────────
    op.create_table(
        "nav_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portfolios.id"), nullable=False, index=True),
        sa.Column("record_date", sa.Date, nullable=False, index=True),
        sa.Column("portfolio_value", sa.Float, nullable=False),
        sa.Column("benchmark_value", sa.Float, nullable=True),
    )

    # ── goals ─────────────────────────────────────────────────────────────────
    op.create_table(
        "goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False, index=True),
        sa.Column("goal_name", sa.String(100), nullable=False),
        sa.Column("goal_type", sa.Enum("retirement", "home_purchase", "child_education", "emergency_fund", "vacation", "wealth_creation", "other", name="goaltype"), nullable=False),
        sa.Column("target_amount", sa.Float, nullable=False),
        sa.Column("current_corpus", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("monthly_sip", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("target_year", sa.Integer, nullable=False),
        sa.Column("priority", sa.Integer, nullable=False, server_default="1"),
    )

    # ── transactions ──────────────────────────────────────────────────────────
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False, index=True),
        sa.Column("scheme_name", sa.String(200), nullable=False),
        sa.Column("transaction_type", sa.Enum("sip", "lumpsum_buy", "redemption", "switch_in", "switch_out", "dividend", name="transactiontype"), nullable=False),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("units", sa.Float, nullable=True),
        sa.Column("nav", sa.Float, nullable=True),
        sa.Column("transaction_date", sa.Date, nullable=False, index=True),
    )

    # ── alerts ────────────────────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False, index=True),
        sa.Column("alert_type", sa.Enum("CONCENTRATION_RISK", "CRYPTO_OVERWEIGHT", "NO_NOMINEE", "KYC_EXPIRED", "ESTATE_GAP", "REVIEW_OVERDUE", "NPS_NOT_OPENED", "FD_OVERWEIGHT", "AI_LOW_CONFIDENCE", name="alerttype"), nullable=False),
        sa.Column("priority", sa.Enum("critical", "high", "medium", "low", name="alertpriority"), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("is_resolved", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── chat_messages ─────────────────────────────────────────────────────────
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False, index=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("tools_used", postgresql.JSONB, nullable=True),
    )

    # ── ai_audit_logs ─────────────────────────────────────────────────────────
    op.create_table(
        "ai_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False, index=True),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("user_query", sa.Text, nullable=False),
        sa.Column("ai_response_summary", sa.Text, nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("disclaimer_injected", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("sebi_compliant", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("duration_ms", sa.Integer, nullable=True),
    )

    # ── compliance_documents ──────────────────────────────────────────────────
    op.create_table(
        "compliance_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=True, index=True),
        sa.Column("doc_type", sa.Enum("sebi_disclosure", "risk_profile", "suitability_attestation", "kyc_record", "meeting_summary", name="compliancedoctype"), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("generated_by", sa.String(50), nullable=False, server_default="'ai'"),
        sa.Column("reviewed_by", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("compliance_documents")
    op.drop_table("ai_audit_logs")
    op.drop_table("chat_messages")
    op.drop_table("alerts")
    op.drop_table("transactions")
    op.drop_table("goals")
    op.drop_table("nav_history")
    op.drop_table("holdings")
    op.drop_table("portfolios")
    op.drop_table("users")
    op.drop_table("clients")

    op.execute("DROP TYPE IF EXISTS compliancedoctype")
    op.execute("DROP TYPE IF EXISTS alertpriority")
    op.execute("DROP TYPE IF EXISTS alerttype")
    op.execute("DROP TYPE IF EXISTS transactiontype")
    op.execute("DROP TYPE IF EXISTS goaltype")
    op.execute("DROP TYPE IF EXISTS assetclass")
    op.execute("DROP TYPE IF EXISTS taxregime")
    op.execute("DROP TYPE IF EXISTS riskprofile")
    op.execute("DROP TYPE IF EXISTS userrole")
