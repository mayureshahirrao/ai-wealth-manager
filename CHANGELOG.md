# Changelog

All notable changes to AI Wealth Manager are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.

> **Version policy:**
> - `MAJOR` — breaking API/schema changes
> - `MINOR` — new phase / significant feature set
> - `PATCH` — bug fixes, dependency pins, config corrections

---

## [0.9.0] — 2026-06-10

### Added — Phase 11: Production Hardening

#### `backend/app/ai/market_data.py` [NEW]
- Live Indian market data module via Yahoo Finance (yfinance)
- Fetches: Nifty 50, Sensex, Midcap 100, Smallcap 100, India VIX, GOLDBEES (gold ETF), USD/INR
- 15-minute in-memory TTL cache — prevents hammering Yahoo Finance on every AI call
- Runs fetch in executor so async event loop is never blocked
- Graceful fallback: on yfinance error, returns stale cache or hardcoded demo values
- Market sentiment heuristic based on daily return + VIX level

#### `backend/app/ai/tools/get_market_data.py`
- Replaced static demo dict with `await get_market_data()` call to live module
- Tool description updated to mention live data + 15-min cache

#### `backend/app/main.py`
- Added `slowapi` rate limiter (default 300/min) with `SlowAPIMiddleware`
- Shared `limiter` instance exported for use in routers

#### `backend/app/api/chat.py`
- `POST /api/chat/message` — `@limiter.limit("10/minute")` guard added

#### `backend/app/api/rm.py`
- `GET /api/rm/meeting-prep/{id}` — `@limiter.limit("5/minute")` guard added

#### `backend/app/api/compliance.py`
- `POST /api/compliance/generate-doc` — `@limiter.limit("5/minute")` guard added

#### `backend/app/api/financial_plan.py`
- `POST /api/financial-plan/generate` — `@limiter.limit("3/minute")` guard added

#### `backend/tests/` [NEW] — pytest test suite (30 tests, all passing)
- `tests/conftest.py` — pytest-asyncio fixtures: in-memory SQLite engine, per-test session, httpx AsyncClient, JWT auth headers for all 3 roles; JSONB→JSON SQLite patch
- `tests/api/test_health.py` — 4 tests: /health OK, version format, /docs accessible, 404
- `tests/api/test_auth.py` — 8 tests: login success/fail/missing, /api/auth/me for all 3 roles, auth required
- `tests/api/test_portfolio.py` — 6 tests: portfolio data, auth required, RM forbidden from /me, goals, tax summary
- `tests/api/test_compliance.py` — 6 tests: audit log access (investor forbidden, RM allowed, compliance allowed), risk alerts, AI governance
- `tests/api/test_market_data.py` — 6 tests: module keys, NIFTY_50 present, index filter, fallback on error, cache TTL, debt rates
- `backend/pytest.ini` — asyncio_mode=auto, asyncio_default_fixture_loop_scope=function

#### `frontend/src/components/ErrorBoundary.jsx`
- Added `fullPage` prop — full-viewport centered error UI for top-level boundary
- Added `errorInfo` state to capture component stack
- Dev-only stack trace `<details>` block (collapsed)
- Added "Reload Page" button alongside "Try Again"

#### `frontend/src/App.jsx`
- Root `<ErrorBoundary>` upgraded to `fullPage`
- Per-dashboard `<ErrorBoundary fullPage>` added around InvestorDashboard, RMDashboard, ComplianceDashboard — crash in one role's dashboard doesn't crash others

### Added — Dependencies
- `backend/requirements.txt`: `yfinance==1.4.1`, `slowapi==0.1.9`, `aiosqlite==0.20.0`

### Verified Working ✅
- 30 pytest tests pass (health, auth, portfolio, compliance, market data)
- Live market data: Nifty 50 23,215, Sensex 73,983, India VIX 15.6 (2026-06-10)
- Rate limiting: slowapi middleware wired, AI endpoints protected
- Error boundaries: fullPage boundaries on root + all 3 role dashboards

---

## [0.8.0] — 2026-06-10

### Added — Phase 10: Polish, Demo Prep & Developer Documentation

#### `docs/DEVELOPER_GUIDE.docx`
- New: full developer reference — architecture, all modules, code examples, DB models, AI layer, RAG pipeline, frontend hooks, auth roles, tool extension guide, known issues, versioning

#### `docs/DEMO_SCRIPT.docx`
- New: 10-minute demo walkthrough script — 3 acts (Investor/RM/Compliance), pre-demo checklist, talking points, Q&A, timing guide, fallback troubleshooting

#### `docs/RUNNING_THE_PROJECT.docx`
- New: step-by-step ops guide — prerequisites, env setup, Docker, migrations, seed, RAG index, backend/frontend startup, service verification commands

#### `README.md`
- Added "Verify Services Are Running" section with PostgreSQL + ChromaDB + backend health check commands
- Fixed ChromaDB collection name in verify commands (`indian_financial_knowledge`)
- Version badge updated to 0.8.0

### Fixed

#### `backend/app/api/compliance.py`
- `_risk_profile_prompt`: invalid Python f-string format spec `{client.annual_income:,.0f if client.annual_income else 0}` → fixed to `{client.annual_income or 0:,.0f}` — was causing 500 on all compliance doc generation
- `doc_type` max_tokens reduced 1500→800 — prevents 30s axios timeout on doc generation

#### `backend/app/api/rm.py`
- Meeting prep `max_tokens` reduced 1500→800 — prevents 30s axios timeout

#### `frontend/src/api/endpoints.js`
- Added `RESOLVE_ALERT: (alertId) => /api/compliance/resolve-alert/${alertId}` — was missing entirely

#### `frontend/src/hooks/useApi.js`
- Added `useResolveAlert()` mutation — wires PATCH /api/compliance/resolve-alert/{id} with cache invalidation
- `useGenerateMeetingPrep`: timeout increased 30s→120s — was silently timing out
- `useGenerateComplianceDoc`: timeout increased 30s→120s — was silently timing out

#### `frontend/src/pages/compliance/DocGeneratorView.jsx`
- All 5 `DOC_TYPES` values fixed to match backend `ComplianceDocType` enum: `DISCLOSURE_DOC`→`sebi_disclosure`, `RISK_PROFILE`→`risk_profile`, etc. — mismatch was causing 400 on every doc generation attempt

#### `frontend/src/pages/rm/ClientDetail.jsx`
- Added `error: briefError` destructuring from `useGenerateMeetingPrep` — errors were silently swallowed; now shows red error card with message

#### `frontend/src/pages/rm/NextActions.jsx`
- Added `useResolveAlert` import and hook
- Added `dismissedIds` local state for optimistic UI
- Added `handleResolve()` — calls PATCH for alert-backed items, local-only dismiss for auto-detected items (no alert_id)
- Added "✓ Dismiss" button on every action card

### Verified Working ✅
- Investor portal: portfolio loads, AI chat streams, goals and tax views correct
- RM: client list, next actions display, dismiss button resolves alerts, meeting prep generates brief
- Compliance: audit log, risk alerts, AI governance all load; doc generator produces SEBI documents for all 5 doc types
- 31 API endpoints documented in Swagger UI at /docs

---

## [0.7.1] — 2026-06-01

### Fixed — Phase 10: Critical Bug Fixes (Demo Prep)

#### `backend/app/core/config.py`
- Added `env_ignore_empty=True` to `SettingsConfigDict` — pydantic-settings now ignores
  empty system env vars (e.g. `ANTHROPIC_API_KEY=''` set by Claude Code process) and falls
  through to `.env` file value. Previously the empty system env overrode `.env`, causing
  `ANTHROPIC_API_KEY` to be blank in all backend processes.

#### `backend/app/ai/base_tool.py`
- `log_ai_call()` input/output summaries now ASCII-encoded (`encode('ascii','replace')`) before
  logging. Tool results contain `₹` (U+20B9 Rupee sign) which crashed structlog on Windows
  cp1252 console, raising `AIToolExecutionError` and surfacing as generic SSE error.

#### `frontend/src/pages/investor/GoalsView.jsx`
- Fixed: `data?.data` was object `{goals:[], retirement_readiness:{}}` not array —
  changed to `data?.data?.goals || []`
- Fixed: `goal.progress_pct` (field missing in API response) — replaced with `goal.feasibility_score`
- Fixed: `goal.target_year` (field missing in API response) — derived as
  `new Date().getFullYear() + goal.years_remaining`

### Verified Working
- AI chat SSE stream ✅ — tool called → data fetched → response streamed → SEBI disclaimer → done event (confidence=0.72)
- Goals view renders ✅ — feasibility scores, target years, progress bars all correct
- All 31 API endpoints documented in Swagger ✅
- All 3 role login flows ✅ — investor, RM, compliance
- RAG index ✅ — 162 chunks, 5 docs

---

## [0.7.0] — 2026-06-01

### Added — Phase 8: Compliance Module Full Implementation

#### `backend/app/api/compliance.py` (full rewrite of stub)
- `GET /api/compliance/audit-log` — paginated AI audit log with filters:
  - Filters: `client_id`, `tool_name`, `sebi_compliant`, `days` (look-back window)
  - Enriched with client names; distinct tool list returned for filter UI
  - Pagination metadata: page, page_size, total, total_pages
- `GET /api/compliance/risk-alerts` — all unresolved alerts across all clients:
  - Filter by `priority` (critical/high/medium/low)
  - Enriched with `client_name` via join
- `PATCH /api/compliance/resolve-alert/{id}` — mark alert resolved:
  - Sets `is_resolved=True`, stores `resolution_note`, records `resolved_by` email and timestamp
- `POST /api/compliance/generate-doc` — SEBI document generator via Claude:
  - 5 doc types: `DISCLOSURE_DOC`, `RISK_PROFILE`, `SUITABILITY_ATTESTATION`, `KYC_RECORD`, `MEETING_SUMMARY`
  - Each type has a dedicated Claude prompt builder with client data context
  - Saves to `compliance_documents` table for audit trail
- `GET /api/compliance/ai-governance` — AI governance metrics dashboard:
  - SEBI compliance rate %, disclaimer injection rate %, average confidence, average duration
  - Confidence distribution: high/medium/low/unknown buckets with counts + pct
  - Tool usage breakdown sorted by frequency
  - Low-confidence interactions (score < 0.50) enriched with client names
  - Daily interaction trend (last 7 days of look-back window)
  - Flags: non-compliant count, below-threshold count, missing disclaimer count
- 5 prompt builder helpers: `_sebi_disclosure_prompt`, `_risk_profile_prompt`,
  `_suitability_prompt`, `_kyc_record_prompt`, `_meeting_summary_prompt`

#### `frontend/src/pages/compliance/AIGovernanceView.jsx` (full rewrite of stub)
- Period selector (7 / 30 / 90 / 365 days) wired to `GET /api/compliance/ai-governance`
- 4 stat cards: total interactions, SEBI compliance rate, avg confidence, disclaimer injection rate
- Colour-coded compliance/confidence status (green ≥95%/75%, amber ≥80%/50%, red below)
- Flag banners: non-compliant count, low-confidence count, missing disclaimer count
- Confidence distribution: horizontal progress bars for high/medium/low/unknown
- Tool usage: horizontal progress bars per tool name
- Daily trend: mini bar chart (last 7 days)
- Low-confidence table: client name, tool, query preview, ConfidenceBadge, timestamp

#### `frontend/src/pages/compliance/DocGeneratorView.jsx` (new file)
- Client selector populated from `/api/clients`
- Doc type selector with 5 options and description per type
- Optional context/notes textarea
- "Generate Document" button wired to `POST /api/compliance/generate-doc`
- Document rendered in bg-gray-50 pre block with download button
- Shows doc_id + "saved to audit trail" confirmation

#### `frontend/src/pages/compliance/ComplianceDashboard.jsx`
- Added 4th nav item: "Doc Generator" → `/compliance/doc-generator`
- Route added for `DocGeneratorView`

#### `frontend/src/pages/compliance/RiskAlertsView.jsx`
- Fixed: shows `client_name` (returned by API) instead of truncated `client_id` UUID

### Fixed
- RiskAlertsView showed `client_id.slice(0,8)...` — now shows `client_name` from API response

### Verified Working
- Frontend compiles with zero console errors ✅
- Login page renders, all 3 role quick-fill buttons visible ✅
- Network error on login expected (backend Docker not started during UI verification) ✅

---

## [0.6.0] — 2026-05-31

### Added — Phase 6: RM Copilot Full Implementation

#### `backend/app/api/rm.py` (full rewrite of stub)
- `GET /api/rm/next-actions` — prioritised action queue across ALL clients:
  - Sources: active compliance alerts, auto-detected overdue reviews (90+ days),
    at-risk goals (feasibility score < 40)
  - Sorted by priority (critical → high → medium → low), then client name
  - Each action includes `recommended_action` string mapped from alert type
  - Returns `total_actions`, `generated_at` timestamp
- `GET /api/rm/meeting-prep/{client_id}` — AI-generated meeting brief:
  - Gathers: client profile, portfolio (XIRR, allocation, holdings), goals (GoalAssessment),
    active alerts
  - Calls `claude.complete()` with structured 7-section prompt
  - Returns: brief text, context_summary (AUM, alert count, goal count), generated_at
- `GET /api/rm/alerts/{client_id}` — enriched (adds `recommended_action` per alert)
- Helper `_get_recommended_action()` — maps AlertType → actionable recommendation string
- Helper `_build_meeting_context()` — formats client data into Claude-readable brief
- `require_rm_or_compliance` guard on all RM endpoints (compliance can view too)

#### `backend/app/api/financial_plan.py` (full rewrite of stub)
- `POST /api/financial-plan/generate` — AI comprehensive financial plan:
  - Request body: `{client_id, advisor_notes?, target_retirement_age, desired_monthly_income}`
  - Gathers full client data: portfolio, holdings, goals (GoalAssessment for each),
    tax regime comparison, active alerts
  - Calls `claude.complete()` with 8-section structured prompt (system prompt as SEBI RA)
  - Saves to `compliance_documents` table (SUITABILITY_ATTESTATION type) for audit trail
  - Returns: plan text, plan_id, tokens_used, generated_by
- `GET /api/financial-plan/{client_id}` — retrieves most recent saved plan from DB
- Helper `_build_plan_context()` — comprehensive context with portfolio, goals, tax analysis
- `GeneratePlanRequest` Pydantic model with validation

#### `frontend/src/pages/rm/NextActions.jsx` (full rewrite)
- Priority filter chips (All, Critical, High, Medium, Low) with counts
- Action cards with emoji icons per action type, priority colour coding
- "View Client →" navigation to ClientDetail
- Refresh button, empty state ("All clients in good standing")

#### `frontend/src/pages/rm/FinancialPlanView.jsx` (full rewrite)
- Client selector dropdown populated from `/api/clients`
- Parameters: retirement age, desired monthly income, advisor notes
- "Generate Financial Plan" button with loading state (~30-60s warning)
- Plan rendered as pre-formatted text with download button
- Shows existing saved plan on load

#### `frontend/src/pages/rm/ClientDetail.jsx` (major update)
- Added tab navigation: Overview | Portfolio | Goals | Meeting Prep
- **Overview tab**: client details + portfolio snapshot
- **Portfolio tab**: holdings table with gain/loss %, asset allocation
- **Goals tab**: feasibility progress bars with colour coding
- **Meeting Prep tab**: "Generate Meeting Brief" button → streaming Claude response
- Alerts banner with `recommended_action` shown below each alert

#### `frontend/src/hooks/useApi.js`
- `useMeetingPrep()` — `enabled` param (only fetches on demand)
- `useGenerateMeetingPrep()` — mutation for triggering meeting brief generation

---

## [0.5.0] — 2026-05-31

### Added — Phase 5: ChromaDB RAG Pipeline

#### Knowledge Documents (`backend/app/rag/knowledge_docs/`)
- `sebi_ia_regulations.txt` — SEBI IA Regulations 2013: registration, conduct obligations
  (Clauses 17–24), AI advisory rules, prohibited activities, record retention requirements
- `indian_tax_guide.txt` — Complete FY 2024-25 tax guide: Old/New regime slabs, Budget 2024
  LTCG/STCG rates (12.5%/20%), NPS/PPF/EPF benefits, LTCG harvesting strategy, filing dates
- `mutual_funds_guide.txt` — AMFI MF categories, SIP vs lumpsum, expense ratio impact,
  Direct vs Regular plans, portfolio construction, XIRR explained
- `retirement_planning_guide.txt` — Three-pillar framework, corpus calculation methodology,
  timeline strategy by age, SWP post-retirement, healthcare planning, FIRE in India
- `goal_based_investing.txt` — Goal types (emergency fund, child education, home, retirement,
  wedding), feasibility scoring, SIP amounts for common goals, asset allocation by timeline

#### RAG Engine (`backend/app/rag/`)
- `embedder.py` — Loads .txt knowledge docs, chunks them (500-char chunks, 100 overlap) at
  paragraph/sentence boundaries, embeds with sentence-transformers (all-MiniLM-L6-v2),
  upserts into ChromaDB collection; idempotent (clears before re-indexing)
- `retriever.py` — Semantic search using cosine similarity; query-type-aware source filtering
  (e.g., TAX queries search only tax + SEBI docs); formats top-k chunks into system prompt
  context string (max 3000 chars); `get_rag_context()` async convenience wrapper
- `index.py` — CLI entry point: `python -m app.rag.index`
- `__init__.py` — Public API: `retrieve`, `format_context_for_prompt`, `get_rag_context`,
  `index_knowledge_docs`

#### Streaming Integration (`backend/app/ai/streaming.py`)
- RAG retrieval now runs before every Claude API call
- `_is_rag_available()` — lazy singleton check; graceful degradation if ChromaDB unreachable
- Retrieved context injected into enriched system prompt
- `rag_sources` count included in `done` SSE event
- `estimate_confidence()` now receives `rag_sources_found` for better scoring
- **Bug fix**: `client_id` now always force-overridden in tool inputs (prevents Claude
  hallucinating placeholder UUIDs like "priya-sharma-uuid")

#### Chat Endpoint (`backend/app/api/chat.py`)
- `build_investor_system_prompt()` now receives `client_id` parameter
- Real UUID embedded in system prompt with explicit instruction to Claude

#### System Prompt (`backend/app/ai/streaming.py`)
- `build_investor_system_prompt()` signature updated: added `client_id: str = ""`
- Client UUID and instruction injected into prompt: "use the client_id provided above"

#### Infrastructure
- `docker-compose.yml` — ChromaDB image: `0.5.0` → `0.5.23` (fixes API v1/v2 mismatch)
- `Makefile` — added `rag-index` target
- `requirements.txt` — uncommented `chromadb==0.5.23` and `sentence-transformers==3.3.1`

### Verified Working
- RAG retrieval test: scores 0.786 and 0.763 for LTCG tax query ✅
- 162 chunks indexed from 5 documents ✅
- Full chat pipeline: SSE streaming, 2 tools called, 3 RAG sources, confidence 0.79 ✅
- SEBI disclaimer auto-injected ✅

---

## [0.4.0] — 2026-05-29

### Fixed — Windows compatibility & dependency stabilisation
- **Migration idempotency** — removed explicit `CREATE TYPE` DDL from `001_initial_schema.py`; SQLAlchemy now owns enum creation via `create_table`, eliminating `DuplicateObjectError` on re-runs
- **SQLAlchemy enum values** — added `_enum()` helper with `values_callable=lambda x: [e.value for e in x]` to all `SAEnum()` columns in `models.py`; fixes `InvalidTextRepresentationError: invalid input value for enum userrole: "RM"` caused by SQLAlchemy 2.x defaulting to `.name` over `.value`
- **Port conflict** — changed Docker PostgreSQL host port from `5432` → `5433` in `docker-compose.yml` and `config.py` default to avoid collision with locally-installed PostgreSQL
- **Dependency conflicts** — resolved `anthropic==0.39.0` vs `langchain-anthropic==0.3.3` incompatibility by relaxing to `anthropic>=0.41.0`; pinned `bcrypt==4.0.1` for `passlib==1.7.4` compatibility; added `email-validator==2.2.0` for Pydantic `EmailStr`; commented out `chromadb` and `sentence-transformers` (require C++ Build Tools, deferred to Phase 5)
- **`.env` location** — documented that `backend/.env` is required (pydantic-settings resolves relative to CWD, not package root); config default updated to port 5433 as safe fallback

### Changed
- `backend/requirements.txt` — pinned `bcrypt==4.0.1`, added `email-validator==2.2.0`, relaxed `anthropic` pin, commented out ChromaDB/sentence-transformers
- `backend/app/core/config.py` — `APP_VERSION` → `"0.4.0"`, `DATABASE_URL` default → port `5433`
- `frontend/package.json` — `version` → `"0.4.0"`

---

## [0.3.0] — 2026-05-29

### Added — Phase 3+4: Claude Integration, 5 AI Tools, SSE Streaming

#### AI Infrastructure (`backend/app/ai/`)
- `claude_client.py` — Singleton `AsyncAnthropic` wrapper with tenacity retry (3 attempts, exponential backoff on rate limit / API errors)
- `base_tool.py` — Abstract `BaseTool` with automatic timing, SEBI audit logging (`log_ai_call`), and error wrapping to `AIToolExecutionError`
- `tool_registry.py` — Per-request `ToolRegistry` with `dispatch()` + `get_schemas()`; `ToolNames` constants defining `INVESTOR_TOOLS` and `RM_TOOLS` subsets
- `compliance_injector.py` — `QueryType` enum (PORTFOLIO / TAX / RETIREMENT / INVESTMENT_ADVICE / BEHAVIORAL / MARKET / GENERAL); `classify_query()`, `inject_disclaimer()` (appends SEBI disclaimer), `validate_response_compliance()` (prohibited phrase detection), `estimate_confidence()` (heuristic 0.0–0.95)
- `langsmith_tracer.py` — `setup_langsmith()` configures env vars at startup; no-op when `LANGCHAIN_API_KEY` not set
- `response_validator.py` — `ValidationResult` dataclass; plausibility checks for tax rates, XIRR bounds, retirement corpus range; `run_full_validation()` dispatcher
- `streaming.py` — Agentic tool-use loop (max 5 iterations); SSE event protocol (`delta`, `tool_call`, `tool_result`, `done`, `error`); `build_investor_system_prompt()` and `build_rm_system_prompt()`

#### 5 AI Tools (`backend/app/ai/tools/`)
All tools are DB-injected per-request via `build_tool_registry(db)`:
- `get_portfolio_summary` — AUM, XIRR vs benchmark, asset allocation %, top 5 holdings, active SIPs
- `get_goal_progress` — `GoalAssessment` feasibility scores (0–100), shortfall analysis, recommendations per goal
- `calculate_tax_liability` — Old/New regime comparison (Budget 2024), LTCG harvesting opportunity (₹1.25L annual exemption)
- `get_market_data` — Nifty 50, Sensex, midcap/smallcap indices, RBI repo rate, G-Sec yield, MCX gold, USD/INR (demo data; Phase 5 → live NSE/BSE API)
- `run_retirement_projection` — `assess_retirement_readiness()` with 6% inflation-adjusted targets, corpus gap analysis, additional SIP needed

#### Chat Endpoint (`backend/app/api/chat.py`)
- Full agentic SSE streaming replacing Phase 1 stub
- Role-based tool selection: investors get 5 tools, RM gets 4 (no market data)
- Investor access control: 403 if querying another client's `client_id`
- Post-stream `finally` block persists `ChatMessage` (user + assistant) and `AIAuditLog` to DB even on client disconnect

#### Other Backend
- `main.py` — calls `setup_langsmith()` at startup
- `auth/router.py GET /api/auth/me` — now returns `name` and `client_id`

#### Frontend
- `endpoints.js` — added `ME` namespace for all `/api/me/*` investor endpoints
- `useApi.js` — `useMyPortfolio`, `useMyGoals`, `useMyTaxSummary`, `useMyNavHistory`, `useMyPerformance`, `useMyAlerts`, `useMyProfile` all call `/api/me/*` (no clientId required)

---

## [0.2.0] — 2026-05-28

### Added — Phase 2: Financial Engine & Data Layer

#### Financial Calculation Engine (`backend/app/financial/`)
- `indian_constants.py` — Single source of truth: Budget 2024 tax rates, SEBI limits, SIP defaults, MF categories, LTCG/STCG rates, SEBI disclaimer text
- `xirr.py` — Newton-Raphson XIRR with bisection fallback; handles irregular SIP cashflows
- `currency_formatter.py` — `format_inr()` → "₹2.50 Cr", "₹45.00 L", "₹9,500"
- `sip_calculator.py` — SIP future value, step-up SIP, lumpsum FV, required monthly SIP, inflation-adjusted value
- `tax_calculator.py` — Old/New regime tax calculation, LTCG/STCG, `compare_tax_regimes()`, `ltcg_harvesting_opportunity()`
- `goal_engine.py` — `GoalAssessment` dataclass (feasibility 0–100, status, recommendation); `assess_retirement_readiness()`

#### Database & Migrations
- `alembic/versions/001_initial_schema.py` — hand-written DDL: 11 tables, 9 PostgreSQL enum types
- `seed_data.py` — 5 Indian demo personas; 24-month SIP history + lumpsum transactions for XIRR; 2 compliance alerts; 3 investor login accounts

#### API Endpoints (enriched)
- `GET /api/clients` — AUM, XIRR, active alerts count, days since last review
- `GET /api/clients/{id}/goals` — with `GoalAssessment` feasibility scores
- `GET /api/clients/{id}/tax-summary` — regime comparison + LTCG harvesting opportunity
- `GET /api/me/*` — 7 investor self-service endpoints (portfolio, goals, tax-summary, nav-history, performance, profile, alerts)

#### Auth
- JWT payload now carries `client_id` for investor role
- `CurrentUser` dataclass includes `client_id: Optional[uuid.UUID]`

---

## [0.1.0] — 2026-05-27

### Added — Phase 1: Foundation Scaffold

- `docker-compose.yml` — PostgreSQL 16, ChromaDB 0.5, FastAPI backend, React frontend services
- Full FastAPI application skeleton: core config, exceptions, logging, error handlers
- SQLAlchemy 2.0 async ORM models: User, Client, Portfolio, Holding, Goal, Transaction, Alert, ChatMessage, AIAuditLog, ComplianceDocument, NAVHistory
- Alembic migration environment (async)
- JWT auth: login endpoint, role-based access guard (investor / rm / compliance)
- Stub API routers: clients, chat, rm, compliance, financial-plan, market
- React 18 + Vite + Tailwind CSS frontend scaffold
- Role-based page structure: investor dashboard, RM dashboard, compliance dashboard
- Login page with demo account quick-fill buttons
- `Makefile` — `make up`, `make migrate-seed`, `make backend`, `make frontend`, `make dev`
