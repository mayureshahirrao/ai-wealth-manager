# Suggested Implementation Order

Build the project in exactly this sequence. Each step is unblocked once the previous is complete.
Steps within the same phase can be built in parallel.

---

## Phase 1: Foundation (Days 1–2)
**Goal:** Single `docker-compose up` starts all services with a health check passing.

| Step | What to build | Skills used |
|---|---|---|
| 1.1 | `docker-compose.yml` + `.env.example` | — |
| 1.2 | Backend `Dockerfile` + `requirements.txt` | — |
| 1.3 | Frontend `Dockerfile` + `package.json` | — |
| 1.4 | `config.py` → load all env vars | `core/config.py` |
| 1.5 | `exceptions.py` + `base_response.py` | `core/exceptions.py`, `core/base_response.py` |
| 1.6 | `logging_config.py` + `error_handler.py` | `core/logging_config.py`, `core/error_handler.py` |
| 1.7 | FastAPI `main.py` with `/health` endpoint | All `core/` skills |
| 1.8 | PostgreSQL service + Alembic init | `database/base_model.py` |

**Milestone:** `curl http://localhost:8000/health` returns `{"status": "ok"}`

---

## Phase 2: Data Layer (Days 3–4)
**Goal:** All 5 Indian client personas + market data queryable via API.

| Step | What to build | Skills used |
|---|---|---|
| 2.1 | All SQLAlchemy models (users, clients, portfolios, holdings, etc.) | `database/base_model.py` |
| 2.2 | Alembic migrations for all models | `database/base_model.py` |
| 2.3 | `repository.py` + specific repositories per model | `database/repository.py` |
| 2.4 | `transaction.py` + `pagination.py` | `database/transaction.py`, `database/pagination.py` |
| 2.5 | Seed data: 5 personas, 15 assets, 24-month NAV | `financial/indian_constants.py`, `testing/mock_data.py` |
| 2.6 | CRUD endpoints: GET /api/clients, GET /api/clients/{id}/portfolio | `core/`, `database/`, `validation/indian_schemas.py` |
| 2.7 | `pan_validator.py` + `indian_schemas.py` + `financial_validators.py` | `validation/` |

**Milestone:** `GET /api/clients/priya-sharma/portfolio` returns portfolio JSON

---

## Phase 3: Auth (Days 3–4, parallel with 2)
**Goal:** Three roles log in, JWT issued, role-guarded endpoints enforce access.

| Step | What to build | Skills used |
|---|---|---|
| 3.1 | `password_utils.py` | `auth/password_utils.py` |
| 3.2 | `jwt_handler.py` | `auth/jwt_handler.py` |
| 3.3 | `role_guard.py` | `auth/role_guard.py` |
| 3.4 | `POST /api/auth/login` endpoint | All `auth/` skills |
| 3.5 | Apply `role_guard` to all data endpoints | `auth/role_guard.py` |

**Milestone:** Login as `priya@demo.com` (investor) gets JWT; login as `rm@demo.com` gets RM token; investor cannot access RM endpoints.

---

## Phase 4: AI Core (Days 5–7)
**Goal:** Claude responds to a portfolio question using real tool data, response streamed.

| Step | What to build | Skills used |
|---|---|---|
| 4.1 | `claude_client.py` with retry logic | `ai/claude_client.py` |
| 4.2 | `langsmith_tracer.py` — configure tracing | `ai/langsmith_tracer.py` |
| 4.3 | `base_tool.py` abstract class | `ai/base_tool.py` |
| 4.4 | `compliance_injector.py` + `response_validator.py` | `ai/compliance_injector.py`, `ai/response_validator.py` |
| 4.5 | `streaming.py` — SSE response helper | `ai/streaming.py` |
| 4.6 | First tool: `GetPortfolioSummaryTool` (inherits BaseTool) | `ai/base_tool.py`, `database/repository.py` |
| 4.7 | `tool_registry.py` — register GetPortfolioSummaryTool | `ai/tool_registry.py` |
| 4.8 | `base_agent.py` — LangGraph single-node agent | `ai/base_agent.py` |
| 4.9 | `POST /api/chat/message` — streaming chat endpoint | All `ai/` skills |

**Milestone:** Priya asks "What's my portfolio allocation?" → Claude calls GetPortfolioSummaryTool → streams back answer with SEBI disclaimer → visible in LangSmith.

---

## Phase 5: RAG (Days 7–8)
**Goal:** AI answers questions from the financial knowledge base.

| Step | What to build | Skills used |
|---|---|---|
| 5.1 | Write 7 knowledge markdown documents | — |
| 5.2 | `chroma_client.py` | `rag/chroma_client.py` |
| 5.3 | `document_loader.py` + `chunker.py` | `rag/document_loader.py`, `rag/chunker.py` |
| 5.4 | `embedder.py` | `rag/embedder.py` |
| 5.5 | Index all 7 documents into ChromaDB | All `rag/` skills |
| 5.6 | `retriever.py` — hybrid retrieval | `rag/retriever.py` |
| 5.7 | `QueryFinancialKnowledgeTool` (new BaseTool) | `ai/base_tool.py`, `rag/retriever.py` |
| 5.8 | Register in ToolRegistry, test with NPS/80C queries | `ai/tool_registry.py` |

**Milestone:** "What is the 80C deduction limit?" → retrieves from ChromaDB → Claude answers with citation.

---

## Phase 6: All Portfolio + Tax Tools (Days 8–9)
**Goal:** Full suite of Indian financial tools callable by Claude.

| Step | Tool | Skills used |
|---|---|---|
| 6.1 | `GetGoalProgressTool` | `financial/goal_engine.py`, `database/repository.py` |
| 6.2 | `RunRetirementProjectionTool` | `financial/sip_calculator.py`, `financial/xirr.py` |
| 6.3 | `RunScenarioAnalysisTool` | `financial/indian_constants.py`, `database/repository.py` |
| 6.4 | `CalculateTaxLiabilityTool` | `financial/tax_calculator.py` |
| 6.5 | Register all in ToolRegistry | `ai/tool_registry.py` |

**Milestone:** Full multi-tool conversation works: Priya asks about retirement → Claude chains projection + tax + goal tools.

---

## Phase 7: RM Copilot (Days 9–10)
**Goal:** RM dashboard with Next Best Action and Meeting Prep working.

| Step | What to build | Skills used |
|---|---|---|
| 7.1 | `GetNextBestActionsTool` (scans all clients) | All `financial/` + `database/` |
| 7.2 | `GET /api/rm/next-actions` endpoint | `ai/` + `database/repository.py` |
| 7.3 | `GenerateMeetingPrepTool` | `ai/claude_client.py`, `database/`, `rag/retriever.py` |
| 7.4 | `POST /api/rm/meeting-prep/{client_id}` | Above |
| 7.5 | Financial Plan Generator: LangGraph 5-node graph | `ai/base_agent.py`, all financial tools |
| 7.6 | `POST /api/financial-plan/generate` | Above |

**Milestone:** RM generates meeting prep for Rajesh Gupta → structured agenda with SEBI-compliant talking points.

---

## Phase 8: Compliance Module (Days 11–12)
**Goal:** Compliance officer can see audit log, risk alerts, and generate SEBI docs.

| Step | What to build | Skills used |
|---|---|---|
| 8.1 | Audit logging middleware (auto-log every AI call) | `ai/compliance_injector.py`, `database/repository.py` |
| 8.2 | `GET /api/compliance/audit-log` | `database/repository.py`, `validation/indian_schemas.py` |
| 8.3 | Risk alert engine (concentration, KYC, crypto, estate) | `financial/indian_constants.py`, `database/repository.py` |
| 8.4 | `GET /api/compliance/risk-alerts` | Above |
| 8.5 | SEBI doc generator (Disclosure Doc, Suitability, Risk Profile) | `ai/claude_client.py`, `ai/compliance_injector.py` |
| 8.6 | `POST /api/compliance/generate-doc` | Above |

**Milestone:** Compliance officer sees Aarav flagged for crypto concentration; generates suitability attestation.

---

## Phase 9: Frontend Build (Days 5–13, parallel with backend)
**Goal:** All three dashboards polished and connected to real API.

| Step | What to build | Skills used |
|---|---|---|
| 9.1 | React app scaffold, Tailwind config, React Router | `frontend/utils/constants.js` |
| 9.2 | `apiClient.js` + `endpoints.js` + `errorHandler.js` | `frontend/api/` |
| 9.3 | AuthContext + `useAuth.js` hook | `frontend/hooks/useAuth.js` |
| 9.4 | Login page with three role cards | `useAuth.js` |
| 9.5 | `useApi.js` (React Query) | `frontend/hooks/useApi.js` |
| 9.6 | Shared components: `INRAmount`, `PercentBadge`, `LoadingSpinner`, `ErrorBoundary` | `frontend/components/` |
| 9.7 | `formatters.js` + `chartHelpers.js` | `frontend/utils/` |
| 9.8 | Investor Portal: Portfolio dashboard with charts | All frontend skills |
| 9.9 | `useSSE.js` + Chat interface with streaming | `frontend/hooks/useSSE.js` |
| 9.10 | RM Dashboard: client list, Next Best Action, meeting prep | All frontend skills |
| 9.11 | RM: Financial Plan Generator with live agent steps | `useSSE.js` |
| 9.12 | Compliance Dashboard: audit log, risk alerts, doc generator | All frontend skills |
| 9.13 | `ConfidenceBadge.jsx` in compliance view | `frontend/components/ConfidenceBadge.jsx` |

---

## Phase 10: Polish + Demo Prep (Days 13–14)
| Step | Activity |
|---|---|
| 10.1 | End-to-end test all 3 role flows |
| 10.2 | Seed data verification — all personas load correctly |
| 10.3 | Docker build clean test: fresh `docker-compose up` |
| 10.4 | LangSmith trace review — verify all agent steps visible |
| 10.5 | Demo script rehearsal (10-minute walkthrough) |
| 10.6 | Swagger UI check at `/docs` — all endpoints documented |

---

## What to Build If Time Runs Out

If you hit Day 12 and haven't finished everything, prioritize in this order:
1. ✅ Investor Portal (chat + portfolio) — most impressive
2. ✅ RM Next Best Action — quick win, very visible value
3. ✅ Financial Plan Generator — most technically impressive
4. ⚠️ Compliance dashboard — deprioritize if time is tight
5. ⚠️ Full chart polish — basic charts are fine for demo
