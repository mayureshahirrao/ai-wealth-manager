# AI Wealth Manager — Skill Architecture

## What Is This Directory?

The `skills/` directory contains all **reusable foundation components** for the project — utilities, base classes, patterns, interfaces, and helpers that every module will consume. Nothing here is a product feature. Everything here is infrastructure that makes building features fast, consistent, and safe.

---

## Skill Domains (12 total)

| # | Domain | Location | Description |
|---|---|---|---|
| 1 | Core | `backend/core/` | API response shapes, exceptions, logging, config |
| 2 | Database | `backend/database/` | SQLAlchemy base, generic repository, pagination, transactions |
| 3 | Auth | `backend/auth/` | JWT handling, role guards, password utilities |
| 4 | AI | `backend/ai/` | Claude client, base tool, base agent, compliance injector, streaming |
| 5 | RAG | `backend/rag/` | ChromaDB client, document loading, chunking, embedding, retrieval |
| 6 | Financial | `backend/financial/` | Indian tax constants, XIRR, SIP math, tax calculator, goal engine |
| 7 | Validation | `backend/validation/` | PAN validator, Indian Pydantic schemas, financial validators |
| 8 | Testing (BE) | `backend/testing/` | pytest fixtures, mock data, test client, agent tester |
| 9 | API Client | `frontend/api/` | Axios instance, endpoint constants, error handler |
| 10 | Hooks | `frontend/hooks/` | useAuth, useApi (React Query), useSSE, useINRFormatter |
| 11 | Components | `frontend/components/` | Shared UI atoms: INRAmount, PercentBadge, ConfidenceBadge, etc. |
| 12 | FE Utils | `frontend/utils/` | INR formatters, Recharts helpers, frontend constants |

---

## How These Skills Are Used

Every product module (Auth API, Portfolio API, Chat Agent, Compliance Dashboard, etc.) imports from `skills/` rather than rewriting common logic. The workflow is:

```
Product Module
    └── imports from skills/backend/core/     (response shapes, exceptions)
    └── imports from skills/backend/database/ (repository, transactions)
    └── imports from skills/backend/ai/       (Claude client, base tool)
    └── imports from skills/backend/financial/(XIRR, tax, SIP math)
    └── imports from skills/backend/rag/      (retriever for knowledge queries)
```

---

## Module-Wise Skill Inventory

### Module 1: Infrastructure (Docker, DB setup, env)
| Skill | File | Purpose |
|---|---|---|
| App Config | `core/config.py` | Central settings via pydantic-settings |
| Structured Logging | `core/logging_config.py` | JSON logs, request ID, LangSmith correlation |
| Exception Hierarchy | `core/exceptions.py` | Typed errors for every failure mode |
| Error Handler | `core/error_handler.py` | FastAPI exception → structured JSON response |

### Module 2: Authentication
| Skill | File | Purpose |
|---|---|---|
| JWT Handler | `auth/jwt_handler.py` | Encode/decode/verify JWT tokens |
| Role Guard | `auth/role_guard.py` | Decorator for role-based endpoint protection |
| Password Utils | `auth/password_utils.py` | bcrypt hashing and verification |

### Module 3: Database Layer
| Skill | File | Purpose |
|---|---|---|
| Base Model | `database/base_model.py` | SQLAlchemy base with UUID PK, timestamps |
| Generic Repository | `database/repository.py` | CRUD pattern for all models |
| Pagination | `database/pagination.py` | Offset + cursor pagination |
| Transaction Context | `database/transaction.py` | Unit-of-work pattern |

### Module 4: AI Core (Chat + Agents)
| Skill | File | Purpose |
|---|---|---|
| Claude Client | `ai/claude_client.py` | Singleton Anthropic client with retry |
| Base Tool | `ai/base_tool.py` | Abstract class all portfolio/tax/planning tools inherit |
| Base Agent | `ai/base_agent.py` | LangGraph agent template with standard hooks |
| Tool Registry | `ai/tool_registry.py` | Register/discover tools dynamically |
| Response Validator | `ai/response_validator.py` | Validate AI output completeness + SEBI compliance |
| Compliance Injector | `ai/compliance_injector.py` | SEBI disclaimer injection and Clause 19 check |
| LangSmith Tracer | `ai/langsmith_tracer.py` | Setup tracing context for every agent run |
| Streaming Helper | `ai/streaming.py` | SSE streaming response for chat interface |

### Module 5: RAG (Knowledge Base)
| Skill | File | Purpose |
|---|---|---|
| ChromaDB Client | `rag/chroma_client.py` | Singleton ChromaDB connection |
| Document Loader | `rag/document_loader.py` | Load .md/.txt docs from knowledge_docs/ |
| Chunker | `rag/chunker.py` | Semantic chunking strategies |
| Embedder | `rag/embedder.py` | Generate embeddings via Claude/HuggingFace |
| Retriever | `rag/retriever.py` | Hybrid retrieval (dense + keyword) |

### Module 6: Financial Domain (Indian)
| Skill | File | Purpose |
|---|---|---|
| Indian Constants | `financial/indian_constants.py` | LTCG, STCG, 80C, 80D, NPS limits, slabs |
| XIRR Calculator | `financial/xirr.py` | Extended IRR for SIP portfolios |
| SIP Calculator | `financial/sip_calculator.py` | SIP FV, required SIP, step-up SIP |
| Tax Calculator | `financial/tax_calculator.py` | Old/New regime, LTCG/STCG, 80C optimizer |
| Goal Engine | `financial/goal_engine.py` | Goal feasibility scoring, corpus gap analysis |
| Currency Formatter | `financial/currency_formatter.py` | ₹ in lakhs/crores, Indian numbering |

### Module 7: Validation
| Skill | File | Purpose |
|---|---|---|
| PAN Validator | `validation/pan_validator.py` | Validate Indian PAN card format |
| Indian Schemas | `validation/indian_schemas.py` | Pydantic base schemas for Indian financial data |
| Financial Validators | `validation/financial_validators.py` | Portfolio, SIP, goal, tax input validators |

### Module 8: Testing Foundation
| Skill | File | Purpose |
|---|---|---|
| Fixtures | `testing/fixtures.py` | pytest fixtures for DB, client, auth |
| Mock Data | `testing/mock_data.py` | Standard mock personas, portfolios, goals |
| Test API Client | `testing/api_client.py` | FastAPI TestClient wrapper |
| Agent Tester | `testing/agent_tester.py` | LangGraph agent test utilities |

### Module 9–12: Frontend Skills
| Skill | File | Purpose |
|---|---|---|
| API Client | `frontend/api/apiClient.js` | Axios with JWT interceptors |
| Endpoints | `frontend/api/endpoints.js` | All API URL constants |
| useAuth | `frontend/hooks/useAuth.js` | Auth context + role helpers |
| useApi | `frontend/hooks/useApi.js` | React Query wrapper |
| useSSE | `frontend/hooks/useSSE.js` | Server-sent events for chat streaming |
| INRAmount | `frontend/components/INRAmount.jsx` | Render ₹ values in lakhs/crores |
| PercentBadge | `frontend/components/PercentBadge.jsx` | Green/red % change indicator |
| ConfidenceBadge | `frontend/components/ConfidenceBadge.jsx` | AI confidence visual |
| formatters | `frontend/utils/formatters.js` | INR, date, XIRR formatters |
| chartHelpers | `frontend/utils/chartHelpers.js` | Transform portfolio data for Recharts |
| constants | `frontend/utils/constants.js` | Asset class colors, segment labels, URLs |

---

## Conventions Enforced by Skills

### Backend Conventions
1. All API responses use `APIResponse[T]` wrapper from `core/base_response.py`
2. All errors are `WealthManagerException` subclasses — never raise raw `Exception`
3. All DB access goes through `BaseRepository` — no raw SQL in routes
4. All AI tool functions inherit `BaseTool` — schema auto-registered
5. All amounts are stored in **paisa (integer)** internally, formatted on output
6. All financial calculations import constants from `indian_constants.py` — never hardcode rates
7. All AI responses run through `compliance_injector.inject_disclaimer()` before returning

### Frontend Conventions
1. All API calls go through `apiClient.js` — never raw `fetch`
2. All INR values rendered via `<INRAmount value={...} />` — never format inline
3. All server data fetched via `useApi(endpoint)` — never `useEffect + fetch`
4. All Recharts data transformed via `chartHelpers.js` — never in components
5. Role checks via `useAuth().isInvestor` — never read localStorage directly

---

## Scalability & Extensibility Notes

- `BaseTool` is designed so adding a new tool = new class + register in `ToolRegistry`. No other changes.
- `BaseRepository` supports any SQLAlchemy model — adding a new model = new repository class with 2 lines.
- `indian_constants.py` is the single source of truth for all financial parameters. Budget changes = update one file.
- `compliance_injector.py` is the centralized SEBI compliance gate — modify disclaimer in one place.
- `chunker.py` supports swappable strategies — change chunking without touching RAG pipeline.
