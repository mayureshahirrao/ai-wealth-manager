# AI Wealth Manager — India 🇮🇳

> **Version 0.7.0** · [Changelog](CHANGELOG.md)

An AI-powered robo-advisor platform for the Indian market, built with **Claude Sonnet** as the reasoning engine. Covers portfolio analysis, goal planning, tax optimisation (Budget 2024), and retirement projections — all within SEBI (Investment Advisers) Regulations, 2013 compliance.

---

## Features

### For Investors
- **Portfolio Overview** — AUM, XIRR vs Nifty 50 benchmark, asset allocation (equity / debt / gold)
- **Goal Tracking** — feasibility scores (0–100) for retirement, education, and other goals with SIP gap analysis
- **Tax Summary** — Old vs New regime comparison, LTCG harvesting opportunity (₹1.25L annual exemption, Budget 2024)
- **AI Chat** — conversational assistant powered by Claude with live portfolio data via tool calls

### For Relationship Managers
- **Client Dashboard** — AUM, XIRR, active alerts, days since last review across all clients
- **AI Copilot** — query any client's portfolio, goals, and tax position through natural language
- **Next Best Actions** — prioritised action queue based on alerts and review schedules

### For Compliance Officers
- **SEBI Audit Trail** — every AI response logged to `ai_audit_logs` with confidence score and disclaimer flag
- **Risk Alerts** — concentration risk, overdue reviews, KYC expiry
- **AI Governance** — tool usage stats, confidence distribution, SEBI compliance rate, daily trend, low-confidence escalation table
- **SEBI Doc Generator** — AI-generated compliance docs: Disclosure, Risk Profile, Suitability, KYC, Meeting Summary

### AI Capabilities
- 5 Claude tools: `get_portfolio_summary`, `get_goal_progress`, `calculate_tax_liability`, `get_market_data`, `run_retirement_projection`
- SEBI compliance layer: query classification, mandatory disclaimer injection, prohibited phrase detection
- Agentic streaming loop (up to 5 tool-use iterations per query)
- LangSmith tracing support for observability

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Claude Sonnet (`claude-sonnet-4-6`) via Anthropic SDK |
| Backend | Python 3.11 · FastAPI 0.115 · SQLAlchemy 2.0 async |
| Database | PostgreSQL 16 (Docker) · asyncpg |
| Migrations | Alembic |
| Auth | JWT (python-jose) · bcrypt · Role-based access |
| Frontend | React 18 · Vite · Tailwind CSS · TanStack Query · Recharts |
| Observability | LangSmith (optional) · structlog |
| Infrastructure | Docker Compose |

---

## Project Status

| Phase | Description | Status |
|---|---|---|
| 1 | Foundation scaffold — DB models, auth, stub APIs, React shell | ✅ Done |
| 2 | Financial engine — XIRR, tax calc, goal engine, data layer | ✅ Done |
| 3+4 | Claude integration — 5 tools, SSE streaming, SEBI compliance | ✅ Done |
| 5 | ChromaDB RAG — Indian financial knowledge retrieval | ✅ Done |
| 6 | RM Copilot — next actions, meeting prep, financial plan | ✅ Done |
| 7+8 | Compliance dashboard — audit log, risk alerts, SEBI docs, AI governance | ✅ Done |
| 9 | Frontend polish — all dashboards fully wired | 🔜 Next |
| 10 | Demo prep — end-to-end test, Docker clean build, LangSmith review | 🔜 Next |

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker Desktop** (for PostgreSQL)
- **Anthropic API key** (for AI chat; get one at [console.anthropic.com](https://console.anthropic.com))

> **Windows note:** Docker Desktop must be running before starting the backend. If you have PostgreSQL installed locally, Docker uses port **5433** to avoid conflicts.

---

## Quick Start

### 1. Clone & configure

```bash
git clone https://github.com/mayureshahirrao/ai-wealth-manager.git
cd ai-wealth-manager
```

Copy the example env file and fill in your API key:

```bash
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY=sk-ant-...
```

Also copy `.env` into the backend directory (required for local development):

```bash
cp .env backend/.env
```

### 2. Start infrastructure

```bash
docker compose up -d postgres chromadb
```

### 3. Set up backend

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m app.seed.seed_data

# macOS/Linux:
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m app.seed.seed_data
```

### 4. Index knowledge docs into ChromaDB (one-time)

```bash
# Windows:
.venv\Scripts\python -m app.rag.index

# macOS/Linux:
.venv/bin/python -m app.rag.index
```

Expected: `✅ Indexed 162 chunks from 5 documents into ChromaDB.`

### 5. Start backend server

```bash
# Windows:
.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# macOS/Linux:
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Start frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**

---

## Demo Accounts

All accounts use password: **`demo1234`**

| Role | Email | Access |
|---|---|---|
| Investor | `priya.sharma@demo.com` | Own portfolio, goals, chat |
| Investor | `arjun.kapoor@demo.com` | Own portfolio, goals, chat |
| Investor | `sunita.rao@demo.com` | Own portfolio, goals, chat |
| RM | `rm@wealthmanager.com` | All 5 clients, AI copilot |
| Compliance | `compliance@wealthmanager.com` | Audit logs, risk alerts |

---

## API Reference

Interactive docs available at **http://localhost:8000/docs** (Swagger UI) and **http://localhost:8000/redoc**.

### Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Login → JWT token |
| `GET` | `/api/auth/me` | Current user info |
| `GET` | `/api/me/portfolio` | Investor's own portfolio |
| `GET` | `/api/me/goals` | Goals with feasibility scores |
| `GET` | `/api/me/tax-summary` | Tax regime comparison + LTCG |
| `GET` | `/api/me/nav-history` | 24-month portfolio vs benchmark |
| `GET` | `/api/clients` | All clients (RM only) |
| `GET` | `/api/clients/{id}/portfolio` | Client portfolio (RM only) |
| `POST` | `/api/chat/message` | AI chat — returns SSE stream |
| `GET` | `/api/chat/history/{clientId}` | Chat history |
| `GET` | `/api/rm/next-actions` | Prioritised RM action queue |
| `GET` | `/api/rm/meeting-prep/{id}` | AI-generated meeting brief |
| `POST` | `/api/financial-plan/generate` | AI comprehensive financial plan |
| `GET` | `/api/compliance/audit-log` | Paginated AI audit log (filters: client, tool, days) |
| `GET` | `/api/compliance/risk-alerts` | All unresolved alerts with client names |
| `PATCH` | `/api/compliance/resolve-alert/{id}` | Mark alert resolved |
| `POST` | `/api/compliance/generate-doc` | SEBI document generator (5 doc types) |
| `GET` | `/api/compliance/ai-governance` | AI governance metrics |
| `GET` | `/health` | Health check |

### Chat SSE Protocol

`POST /api/chat/message` streams Server-Sent Events:

```
data: {"type": "tool_call", "tool": "get_portfolio_summary", "input": {...}}
data: {"type": "tool_result", "tool": "get_portfolio_summary", "result": {...}}
data: {"type": "delta", "text": "Your portfolio is currently valued at..."}
data: {"type": "done", "confidence": 0.87, "tools_used": ["get_portfolio_summary"], "duration_ms": 1823}
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ for chat | — | Anthropic API key |
| `DATABASE_URL` | ✅ | `...localhost:5433/wealth_manager` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | ✅ prod | `local-dev-secret-...` | JWT signing secret |
| `LANGCHAIN_API_KEY` | Optional | — | LangSmith tracing key |
| `LANGCHAIN_TRACING_V2` | Optional | `false` | Enable LangSmith tracing |
| `APP_ENV` | Optional | `development` | `development` or `production` |
| `LOG_FORMAT` | Optional | `text` | `text` or `json` |

---

## Project Structure

```
ai-wealth-manager/
├── backend/
│   ├── app/
│   │   ├── ai/                    # Claude client, tools, streaming
│   │   │   ├── tools/             # 5 AI tools (portfolio, goals, tax, market, retirement)
│   │   │   ├── claude_client.py
│   │   │   ├── streaming.py       # Agentic SSE loop
│   │   │   └── compliance_injector.py
│   │   ├── api/                   # FastAPI routers
│   │   ├── auth/                  # JWT, role guards
│   │   ├── core/                  # Config, exceptions, logging
│   │   ├── database/              # SQLAlchemy models, transactions
│   │   ├── financial/             # XIRR, tax calc, goal engine, SIP
│   │   ├── rag/                   # ChromaDB retrieval (Phase 5)
│   │   └── seed/                  # Demo data seeder
│   ├── alembic/                   # DB migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                   # Axios client, endpoint constants
│   │   ├── components/            # Shared UI components
│   │   ├── hooks/                 # React Query hooks (useApi, useAuth)
│   │   ├── pages/
│   │   │   ├── investor/          # Portfolio, goals, chat, tax
│   │   │   ├── rm/                # Client list, detail, copilot
│   │   │   └── compliance/        # Audit log, risk alerts
│   │   └── utils/                 # Constants, formatters
│   └── package.json
├── docker-compose.yml
├── .env.example
├── VERSION                        # Single source of version truth
├── CHANGELOG.md
└── Makefile
```

---

## Indian Financial Context

This platform is built specifically for Indian investors and advisors:

- **Tax rules**: Budget 2024 — LTCG 12.5% (above ₹1.25L exemption), STCG 20%, new regime standard deduction ₹75K
- **Instruments**: Mutual funds (AMFI categories), SIP, NPS, PPF, ELSS, SGB, SCSS
- **Compliance**: SEBI (Investment Advisers) Regulations, 2013 — mandatory disclaimers, 5-year audit retention, Clause 19 rationale
- **Currency**: All amounts in Indian Rupee (₹), formatted as Lakhs / Crores
- **Benchmarks**: Nifty 50 as default equity benchmark; XIRR for return calculation

---

## Known Limitations (Current Version)

- Market data (`get_market_data` tool) uses static demo values — live NSE/BSE API integration planned
- ChromaDB RAG pipeline active with 162 chunks across 5 Indian financial knowledge documents
- Market data (`get_market_data` tool) uses static demo values — live NSE/BSE API integration planned
- `chromadb` and `sentence-transformers` may require C++ Build Tools on Windows (see setup notes)

---

## Versioning

The project version is maintained in three places (always kept in sync):
- `VERSION` — canonical single-line version file
- `backend/app/core/config.py` — `APP_VERSION` (returned in `/health` endpoint)
- `frontend/package.json` — `version`

| Version | Phase | Description |
|---|---|---|
| 0.1.0 | Phase 1 | Foundation scaffold |
| 0.2.0 | Phase 2 | Financial engine + data layer |
| 0.3.0 | Phase 3+4 | Claude integration + 5 AI tools + SSE streaming |
| 0.4.0 | Bugfix | Windows compatibility, dependency fixes, migration stability |
| 0.5.0 | Phase 5 | ChromaDB RAG pipeline — 162 chunks, 5 knowledge docs |
| 0.6.0 | Phase 7 | RM Copilot — next actions, meeting prep, financial plan |
| 0.7.0 | Phase 8 | Compliance dashboard — audit log, risk alerts, SEBI docs, AI governance |
| 0.8.0 | Phase 9 | Frontend polish *(planned)* |
| 1.0.0 | Phase 10 | Demo-ready release *(planned)* |

---

## License

Private project — all rights reserved.
