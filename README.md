# AP Digital Operations Manager

A full-stack **Accounts Payable automation platform** that streamlines invoice processing, PO matching, exception handling, and approval workflows — powered by AI intelligence via Claude.

## Architecture

```
frontend/          Next.js 15 + TypeScript + shadcn/ui + React Query
backend/           FastAPI + SQLAlchemy 2.0 + PostgreSQL
docker-compose.yml PostgreSQL, Redis, MinIO (S3), Backend, Frontend
```

### AI-Powered Processing Pipeline

```mermaid
flowchart TB
    subgraph Ingestion["Ingestion"]
        Upload["PDF / Image Upload"]
        CSV["CSV / Excel Import"]
        Email["Email Attachments"]
    end

    subgraph Extraction["AI Extraction - 3 Tier OCR"]
        direction TB
        Tier1["pdfplumber - Digital PDFs"]
        Tier2["Tesseract OCR - Scanned PDFs"]
        Tier3["Claude Vision - Structured JSON"]
        Tier1 -->|"fallback"| Tier2 -->|"fallback"| Tier3
    end

    subgraph Classification["AI Classification"]
        Classify["Document Type + Quality Score"]
        GLPredict["GL Account Prediction"]
        Confidence["Confidence Scoring"]
    end

    subgraph CorePipeline["Core Pipeline"]
        direction TB
        VendorRes["Vendor Resolution"]
        DupCheck["Duplicate Detection"]
        AutoLink["Auto-Link PO Lines"]
        MatchEng["Match Engine"]
        VendorRes --> DupCheck --> AutoLink --> MatchEng
    end

    MatchResult{"Match Result"}

    subgraph MatchDetail["Match Engine"]
        TwoWay["2-Way: Invoice vs PO"]
        ThreeWay["3-Way: Invoice vs PO vs GRN"]
        ToleranceEval["Tolerance Evaluation"]
    end

    subgraph ExceptionQueue["Exception Queue"]
        direction TB
        ExTypes["12 Exception Types"]
        AIAnalysis["AI Severity Analysis"]
        ExTypes --> AIAnalysis
    end

    subgraph ResolutionEngine["AI Resolution Engine"]
        direction TB
        Playbook["13 Playbooks"]
        ResPlan["Resolution Plan"]
        AutoExec["100+ Action Handlers"]
        HumanGate{"Needs Human?"}
        Playbook --> ResPlan --> AutoExec --> HumanGate
    end

    subgraph AutoResolution["Auto-Resolution"]
        TolCheck["Within Tolerance"]
        AutoResolve["Auto-Resolve"]
        TolCheck --> AutoResolve
    end

    subgraph ApprovalWF["Approval Workflow"]
        direction TB
        AIRisk["AI Risk Assessment"]
        Matrix["Approval Matrix"]
        Decision{"Decision"}
        AIRisk --> Matrix --> Decision
    end

    subgraph Output["Output"]
        Posted["Posted to ERP"]
        Dashboard["KPI Dashboard"]
        Analytics["Analytics + Reports"]
        Audit["Audit Trail"]
    end

    subgraph BGTasks["Background Tasks - Celery"]
        BatchMatch["Batch Matching"]
        AutoResScan["Auto-Resolution Scan"]
        DupScan["Duplicate Scan"]
    end

    ChatPanel["AI Chat Assistant"]

    Ingestion --> Extraction --> Classification --> CorePipeline
    MatchEng --> MatchResult
    MatchEng -.-> MatchDetail

    MatchResult -->|"Matched"| ApprovalWF
    MatchResult -->|"Variance"| ExceptionQueue
    MatchResult -->|"Near Tolerance"| AutoResolution

    AutoResolution -->|"Resolved"| ApprovalWF
    AutoResolution -->|"Exceeds"| ExceptionQueue

    ExceptionQueue --> ResolutionEngine
    HumanGate -->|"Yes"| ExceptionQueue
    HumanGate -->|"No"| ApprovalWF

    Decision -->|"Approved"| Output
    Decision -->|"Rejected"| ExceptionQueue

    BGTasks -.-> CorePipeline
    ChatPanel -.-> Output

    style Ingestion fill:#e8f4fd,stroke:#2196F3,color:#0d47a1
    style Extraction fill:#fff3e0,stroke:#ff9800,color:#e65100
    style Classification fill:#fff3e0,stroke:#ff9800,color:#e65100
    style CorePipeline fill:#f3e5f5,stroke:#9c27b0,color:#4a148c
    style MatchDetail fill:#f3e5f5,stroke:#9c27b0,color:#4a148c
    style ExceptionQueue fill:#ffebee,stroke:#f44336,color:#b71c1c
    style ResolutionEngine fill:#ffebee,stroke:#f44336,color:#b71c1c
    style AutoResolution fill:#fff8e1,stroke:#ffc107,color:#f57f17
    style ApprovalWF fill:#e8f5e9,stroke:#4caf50,color:#1b5e20
    style Output fill:#e0f2f1,stroke:#009688,color:#004d40
    style BGTasks fill:#eceff1,stroke:#607d8b,color:#263238
```

## Key Features

### Invoice Processing
- Upload and manage invoices with full lifecycle tracking (draft → extracted → matched → approved → posted)
- **AI-powered OCR extraction** via Claude Vision — extracts invoice numbers, dates, amounts, line items, and GL account predictions from PDFs/images
- Real-time confidence scoring based on extraction completeness

### PO Matching
- Two-way matching engine (invoice ↔ purchase order)
- Configurable tolerance thresholds
- Automatic exception creation for variances

### Exception Management
- 12 exception types (missing PO, amount variance, duplicate invoice, vendor on hold, etc.)
- **AI-powered exception analysis** — Claude suggests severity levels and resolution approaches
- Assignment, escalation, and resolution workflows with full comment threads

### Approval Workflows
- Configurable approval matrix with role-based routing
- **AI-powered approval recommendations** — Claude analyzes invoice risk considering match results, vendor history, and exception patterns
- Batch approval for high-volume processing

### AI Chat Assistant
- Slide-out chat panel with conversational AI
- Real-time access to system statistics (pending invoices, open exceptions, approval queues)
- AP domain expertise — workflow guidance, exception resolution advice, best practices

### Dashboard & Analytics
- Real-time KPI dashboard (match rates, processing times, straight-through rates)
- Invoice processing funnel visualization
- Trend analysis and top vendor performance
- Dedicated Analytics page: aging analysis, exception breakdown, vendor risk distribution, monthly comparison, approval turnaround
- Export PDF analytics report with one click

### Data Import
- Bulk import for purchase orders, goods receipts, and vendors via CSV/Excel
- Job tracking with progress and error reporting

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS 4, shadcn/ui |
| State | React Query (TanStack Query) |
| Charts | Recharts |
| Backend | FastAPI, Python 3.12+, Pydantic v2 |
| ORM | SQLAlchemy 2.0 with Alembic migrations |
| Database | PostgreSQL 16 |
| AI | Anthropic Claude API (Haiku for cost-efficiency) |
| Storage | MinIO (S3-compatible) for invoice files |
| Queue | Redis + Celery for async tasks |
| Auth | JWT tokens with role-based access control |

## API

39 REST endpoints across 8 modules:

| Module | Endpoints | Description |
|--------|-----------|-------------|
| Auth | 3 | Login, register, current user |
| Invoices | 6 | CRUD, OCR extract, PO match, audit trail |
| Exceptions | 4 | List, update, batch assign, comments |
| Approvals | 4 | Pending queue, approve/reject, batch, history |
| Vendors | 4 | CRUD with risk level management |
| Import | 4 | PO, GRN, vendor bulk import + job status |
| Analytics | 10 | Dashboard KPIs, funnel, trends, top vendors, aging, exception breakdown, vendor risk, monthly comparison, approval turnaround, PDF export |
| AI Chat | 1 | Conversational assistant |

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.12+ (for local backend dev)

### Quick Start (Docker)

```bash
# Start all services (auto-runs migrations + seeds demo data)
docker compose up --build

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
# MinIO Console: http://localhost:9001
# Login: admin@apops.dev / admin123
```

### Local Development

**Backend:**

```bash
cd backend

# Create virtual environment
python -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start services (PostgreSQL, Redis, MinIO)
docker compose up -d postgres redis minio

# Run migrations
alembic upgrade head

# Seed demo data
python -m app.seed

# Start server
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://ap_user:ap_password_dev@localhost:5432/ap_operations` |
| `SECRET_KEY` | JWT signing key | (change in production) |
| `LLM_API_KEY` | Anthropic API key | (empty = AI features disabled) |
| `LLM_MODEL` | Claude model ID | `claude-haiku-4-5-20251001` |
| `S3_ENDPOINT` | MinIO/S3 endpoint | `http://localhost:9000` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |

> AI features gracefully degrade when `LLM_API_KEY` is not set — the app works fully with rule-based fallbacks.

### E2E Testing

```bash
cd frontend
npx playwright install chromium   # first time only
npm run test:e2e                   # run all tests
npm run test:e2e:ui                # interactive UI mode
```

Covers 8 test suites: authentication, dashboard, invoices, vendors, exceptions, approvals, audit trail, and data import.

## CI/CD & AI Workflow

![CI](https://github.com/jl3443/AP-Operation-Manager/actions/workflows/ci.yml/badge.svg)
![Deploy](https://github.com/jl3443/AP-Operation-Manager/actions/workflows/deploy.yml/badge.svg)

Three GitHub Actions workflows automate quality, review, and deployment:

```mermaid
flowchart TB
    subgraph trigger["🔀 Triggers"]
        PR["Pull Request"]
        Push["Push to main"]
    end

    PR --> CI
    PR --> AIReview
    Push --> CI
    Push --> Deploy

    subgraph CI["⚙️ CI Pipeline"]
        direction TB

        subgraph backend_jobs["Backend"]
            BL["🔍 Lint<br/><small>ruff check + format</small>"]
            BT["🧪 Test<br/><small>pytest + PostgreSQL + Redis</small>"]
            BM["🗃️ Migrations<br/><small>alembic upgrade head<br/>alembic check</small>"]
        end

        subgraph frontend_jobs["Frontend"]
            FL["📝 Lint & Build<br/><small>tsc --noEmit<br/>ESLint<br/>next build</small>"]
        end

        BT --> E2E
        FL --> E2E

        E2E["🎭 E2E Tests<br/><small>docker-compose full stack<br/>Playwright · Chromium</small>"]
    end

    subgraph AIReview["🤖 AI Code Review"]
        direction TB
        Diff["Get PR Diff"]
        Claude["Claude API<br/><small>haiku · structured review</small>"]
        Comment["Post PR Comment<br/><small>Summary · Risk · Issues<br/>Suggestions · Security</small>"]
        Diff --> Claude --> Comment
    end

    subgraph Deploy["🚀 Deploy"]
        direction TB
        BuildBE["Build Backend<br/><small>Docker · python:3.12</small>"]
        BuildFE["Build Frontend<br/><small>Docker · node:20</small>"]
        GHCR["Push to GHCR<br/><small>ghcr.io · sha + latest tags</small>"]
        BuildBE --> GHCR
        BuildFE --> GHCR
    end

    style trigger fill:#f0f4ff,stroke:#4a6cf7,color:#1a1a2e
    style CI fill:#f0fdf4,stroke:#22c55e,color:#1a1a2e
    style AIReview fill:#fef3f2,stroke:#ef4444,color:#1a1a2e
    style Deploy fill:#fdf4ff,stroke:#a855f7,color:#1a1a2e
    style E2E fill:#dbeafe,stroke:#3b82f6,color:#1a1a2e
```

### Workflow Details

| Workflow | Trigger | Jobs | Key Features |
|----------|---------|------|-------------|
| **CI** | Push / PR to `main` | Backend Lint, Test, Migrations + Frontend Lint & Build + E2E | PostgreSQL & Redis service containers, Playwright with artifact upload, Alembic migration check |
| **AI Review** | PR opened / updated | Claude Code Review | Structured review (risk, issues, suggestions, security), auto-updates comment on re-push, skips drafts & dependabot |
| **Deploy** | Push to `main` | Build & Push (matrix) | Parallel backend + frontend Docker builds, GHCR with `sha-<commit>` + `latest` tags, GHA layer caching |

### Setup Required

1. **GitHub Secret**: Add `ANTHROPIC_API_KEY` in repo Settings → Secrets → Actions
2. **Branch Protection** (recommended): Require `Backend · Lint`, `Backend · Test`, `Frontend · Lint & Build` to pass before merge

## User Roles

| Role | Capabilities |
|------|-------------|
| `ap_clerk` | Upload invoices, view exceptions, import data |
| `ap_analyst` | Manage exceptions, run matching, view analytics |
| `approver` | Approve/reject invoices, view approval queue |
| `admin` | Full access including user and vendor management |
| `auditor` | Read-only access to all data and audit trails |

## Project Structure

```
backend/
  app/
    api/v1/endpoints/    # Route handlers (8 modules)
    core/                # Config, database, security
    models/              # SQLAlchemy ORM models
    schemas/             # Pydantic request/response schemas
    services/            # Business logic layer
  alembic/               # Database migrations
  tests/

frontend/
  app/
    (dashboard)/         # Dashboard pages (8 sections)
    login/               # Auth pages
  components/            # Reusable UI components
  hooks/                 # React Query hooks
  lib/                   # API client, types, utilities
```

## License

Private — internal use only.
