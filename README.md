# VASP-Trace (SIH26182)

> **Automated Attribution of Unknown Cryptocurrency Wallets to Nearest VASPs**  
> Smart India Hackathon 2026 · Problem Statement SIH26182

---

## 1. Overview

**VASP-Trace** is an investigator-facing intelligence and attribution platform designed to identify Virtual Asset Service Providers (VASPs)—such as centralized exchanges or custodial services—that received funds from unknown target cryptocurrency wallets.

Key capabilities:
- **Bounded Transaction Graph Expansion:** Reconstructs chronologically ordered fund flows across hops with strict anti-explosion guards (hop caps, call budgets, degree thresholds).
- **Multi-Factor Attribution Engine:** Evaluates candidates across 10 distinct features (funds reached, percentage of traced flow, recency, cluster association, etc.) rather than simplistic shortest paths.
- **Risk & Attribution Decoupling:** Risk assessment (mixer usage, peel chains, rapid hops) never distorts VASP attribution.
- **Evidence Ledger & Audit Trail:** Immutable hash-chained audit logging and evidentiary provenance (`OBSERVED`, `THIRD-PARTY INTELLIGENCE`, `DERIVED`, `INFERENCE`).
- **Deterministic Demo & Live Public Modes:** Built-in fixture provider for 5 deterministic demo cases running in under 5 minutes, alongside live-mode adapters for EVM and Tron.

---

## 2. Architecture & Monorepo Structure

```text
DhanRashi/
├── apps/
│   └── web/                   # Next.js 14 (App Router, TypeScript, Tailwind CSS)
├── services/
│   └── api/                   # FastAPI backend, SQLAlchemy 2, Celery, Alembic
│       ├── app/
│       │   ├── core/          # Settings, security, error envelope, logging redaction
│       │   ├── routers/       # Health, auth, cases, investigations, vasps, reports, sahyog, audit
│       │   ├── db/            # SQLAlchemy 2 base, session engines
│       │   ├── workers/       # Celery app with queues (fetch, trace, analyze, report) & beat
│       │   └── scripts/       # Seeding and registry import CLI utilities
│       ├── alembic/           # Database migration scripts
│       └── tests/             # Pytest test suite (health, worker, secrets, etc.)
├── data/
│   └── demo/                  # Synthetic registry, chain fixtures, expected outputs
├── .github/
│   ├── workflows/ci.yml       # GitHub Actions CI (linting, type checking, tests, compose config)
│   └── hooks/pre-commit       # Git pre-commit secret hygiene hook
├── docker-compose.yml         # Compose configuration (web, api, worker, beat, postgres, redis)
├── Makefile                   # Developer productivity commands
└── README.md
```

---

## 3. Quickstart (Under 10 Minutes)

### Option A: Using Docker Compose (Full Stack)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/shadwalsr/DhanRashi-SIH26182.git
   cd DhanRashi-SIH26182
   ```

2. **Copy environment variables:**
   ```bash
   cp .env.example .env
   ```

3. **Start all services:**
   ```bash
   docker compose up -d
   ```

4. **Verify running services:**
   - Web UI: [http://localhost:3000](http://localhost:3000)
   - API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Liveness Probe: [http://localhost:8000/health/live](http://localhost:8000/health/live)

---

### Option B: Local Development (Without Docker)

#### 1. Backend Service (`services/api`)

Requires Python 3.11+.

```bash
cd services/api

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run test suite
pytest

# Start development API server
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Application (`apps/web`)

Requires Node.js 18+ or 20+.

```bash
cd apps/web

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000).

---

## 4. Testing & Verification

Run the verification suite across backend and frontend:

```bash
# Backend tests
cd services/api
pytest

# Backend lint & type check
ruff check .
mypy app

# Frontend lint & type check
cd ../../apps/web
npm run lint
npx tsc --noEmit
npm run build
```

---

## 5. Secret Hygiene & Security

- **Log Redaction:** `app/core/logging.py` automatically scrubs private keys (`0x...64`), API keys, passwords, and Bearer tokens before emitting log entries.
- **Git Pre-commit Hook:** Located in `.github/hooks/pre-commit`, prevents committing `.env` secret files.
- **Synthetic Data Ribbon:** UI prominently displays the `SYNTHETIC DATA` banner when `DEMO_MODE=true` to ensure demo operations are transparently distinguished from live data.
