# ── AI Wealth Manager — Dev Commands ────────────────────────────────────────
# Usage: make <target>
#
# Prerequisites:
#   - Docker Desktop running
#   - .env file filled (ANTHROPIC_API_KEY required for chat)
#   - Python 3.11+ with venv at backend/.venv
#   - Node 18+ at frontend/

.PHONY: up down restart seed migrate logs shell-db help

# ── Infrastructure ────────────────────────────────────────────────────────────

up:
	@echo "Starting Docker services (PostgreSQL + ChromaDB)..."
	docker compose up -d postgres chromadb
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 3
	@echo "Services up. Run 'make migrate' then 'make seed' to initialise data."

down:
	docker compose down

restart:
	docker compose restart

# ── Database ──────────────────────────────────────────────────────────────────

migrate:
	@echo "Running Alembic migrations..."
	cd backend && .venv/Scripts/python -m alembic upgrade head

seed:
	@echo "Seeding 5 Indian demo personas..."
	cd backend && .venv/Scripts/python -m app.seed.seed_data

migrate-seed: migrate seed

# ── Backend ───────────────────────────────────────────────────────────────────

backend:
	@echo "Starting FastAPI backend on http://localhost:8000"
	cd backend && .venv/Scripts/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-install:
	cd backend && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt

# ── Frontend ─────────────────────────────────────────────────────────────────

frontend:
	@echo "Starting Vite dev server on http://localhost:3000"
	cd frontend && npm run dev

frontend-install:
	cd frontend && npm install

# ── Full Stack Dev ────────────────────────────────────────────────────────────

dev: up
	@echo ""
	@echo "Infrastructure is up. Open two more terminals:"
	@echo "  Terminal 2: make backend"
	@echo "  Terminal 3: make frontend"
	@echo ""
	@echo "Demo logins (password: demo1234):"
	@echo "  Investor:   priya.sharma@demo.com"
	@echo "  RM:         rm@wealthmanager.com"
	@echo "  Compliance: compliance@wealthmanager.com"

# ── Logs ─────────────────────────────────────────────────────────────────────

logs:
	docker compose logs -f postgres chromadb

logs-backend:
	docker compose logs -f backend

shell-db:
	docker compose exec postgres psql -U wm_user -d wealth_manager

# ── Utilities ─────────────────────────────────────────────────────────────────

clean:
	docker compose down -v
	@echo "Volumes deleted. Run 'make up migrate seed' to start fresh."

help:
	@echo ""
	@echo "AI Wealth Manager — Dev Commands"
	@echo "================================="
	@echo "  make up              Start PostgreSQL + ChromaDB"
	@echo "  make migrate         Run Alembic migrations"
	@echo "  make seed            Seed 5 demo clients"
	@echo "  make migrate-seed    Migrate + seed in one step"
	@echo "  make backend         Start FastAPI dev server (port 8000)"
	@echo "  make frontend        Start Vite dev server (port 3000)"
	@echo "  make dev             Start infra + show instructions"
	@echo "  make logs            Tail Docker logs"
	@echo "  make shell-db        psql shell into PostgreSQL"
	@echo "  make clean           Destroy volumes (fresh start)"
	@echo ""
