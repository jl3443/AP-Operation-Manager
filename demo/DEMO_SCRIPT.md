# AP Digital Operations Manager — Demo Script

## Quick Start

```bash
cd /path/to/project
docker compose up --build -d
# Wait ~2 minutes for all services
# Open: http://localhost:3000
# Login: admin@apops.dev / admin123
```

**Services:**
| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 (minioadmin/minioadmin123) |

---

## ACT 3 — "AI Builds the App"

### Story
> "AI designed and built a complete AP automation system from scratch — frontend, backend, database, integrations — 40+ APIs, 13 data models, 11 pages."

### Demo Route (5-8 min)

**Step 1: Login**
- Open http://localhost:3000
- Enter: `admin@apops.dev` / `admin123`
- Click Sign In

**Step 2: Dashboard** (`/dashboard`)
- Point out 6 KPI cards:
  - Total Invoices: 15
  - Pending Approval: 2
  - Open Exceptions: 4
  - Match Rate: 62.5%
  - **Touchless Rate: 20%** (highlight this)
  - **Avg Cycle Time** (highlight this)
- Show Invoice Processing Funnel chart
- Show Invoice Volume Trend
- Show Top Vendors chart

**Step 3: Quick tour of pages**
- Click **Invoices** — show list with status filters
- Click **Exceptions** — show status cards (Open/Assigned/In Progress/Resolved)
- Click **Approvals** — show pending approval queue
- Click **Vendors** — show 8+ vendors with risk levels
- Click **Analytics** — show 5 charts, mention PDF export
- Click **Audit Trail** — show complete action log
- Click **Compliance** — show 4-tab compliance dashboard (preview for ACT 5-6)

### Talking Points
- "13 SQLAlchemy data models covering the full AP lifecycle"
- "40+ REST API endpoints with pagination, filtering, sorting"
- "Role-based access: AP Clerk, Analyst, Approver, Admin, Auditor"
- "AI-powered: OCR extraction, document classification, exception analysis, approval recommendations"

---

## ACT 4 — "AI Runs Operations"

### Story
> "Now the AI operates the system — importing data, processing invoices, detecting exceptions, routing approvals — all automatically."

### Demo Route (8-10 min)

**Step 1: Import Master Data** (`/import`)
- Click **Import Data** in sidebar
- Select tab: **Vendors**
- Upload file: `demo/demo_vendors.csv`
- Wait for success — "5 records imported"
- Select tab: **Purchase Orders**
- Upload file: `demo/demo_po_data.csv`
- Wait for success — "12 records imported"
- Select tab: **Goods Receipts**
- Upload file: `demo/demo_grn_data.csv`
- Wait for success — "12 records imported"

> "In production, this connects to SAP/Oracle via API. For the demo, we import CSVs that mirror real ERP exports."

**Step 2: Upload an Invoice** (`/invoices/upload`)
- Click **Invoices** > **Upload Invoice**
- Select vendor from dropdown (pick SteelCore or any vendor)
- Upload file: `demo/SC-INV-2025-0089_SteelCore_45000.pdf`
- Click Upload

> "The system stores the document in S3-compatible storage and creates a draft invoice record."

**Step 3: OCR Extraction**
- On the invoice detail page, click **Extract** (or the extract button)
- Watch the AI extract:
  - Invoice number, dates, amounts
  - Line items with quantities and prices
  - Document classification (invoice vs credit memo vs debit memo)
  - Confidence score

> "AI Vision reads the PDF, extracts structured data, then a classification agent validates consistency — checking math, dates, vendor match, and flagging issues."

**Step 4: Matching**
- Click **Match** on the invoice
- System runs 2-way match (Invoice vs PO) or 3-way match (Invoice vs PO vs GRN)
- Shows match score and any variances

> "The engine automatically detects whether GRN data exists and selects 2-way or 3-way matching. Tolerances are configurable globally and per-vendor."

**Step 5: Show Exceptions** (`/exceptions`)
- Navigate to Exceptions page
- Show auto-detected exceptions:
  - Amount variance
  - Missing PO
  - Quantity variance
  - Vendor on-hold
- Click into an exception — show AI-suggested resolution

> "Every exception includes AI analysis: severity assessment, root cause hypothesis, and recommended resolution."

**Step 6: Approve/Reject** (`/approvals`)
- Navigate to Approvals page
- Show pending items with AI recommendation (Approve/Reject/Review)
- Click Approve on one
- Show the reasoning

> "AI analyzes the full context — invoice amount, vendor history, exception patterns — and recommends approve, reject, or send for review."

**Step 7: Show Dashboard Impact**
- Go back to Dashboard
- Show updated KPIs reflecting the processing

### Key Files to Demo Upload

| File | Scenario |
|------|----------|
| `SC-INV-2025-0089_SteelCore_45000.pdf` | Normal invoice, should match PO-2025-001 |
| `TP-2025-INV-00341_TechParts_12500_DUPLICATE.pdf` | Duplicate invoice detection |
| `MP-INV-2025-00231_MachPrecision_78000.pdf` | Partial delivery (PO partially received) |
| `MP-INV-2025-00245_MachPrecision_215000.pdf` | Amount exceeds PO — amount variance exception |
| `LT-25-INV-00567_LogiTrans_8364.pdf` | Service invoice (freight) |
| `ACI-2025-00001_ApexChemicals_15025.pdf` | Unknown vendor — missing PO exception |

---

## ACT 5 — "AI Handles Audit & Compliance"

### Story
> "AI doesn't just process invoices — it maintains a complete audit trail and maps every control to policy sections, identifying compliance gaps in real-time."

### Demo Route (5 min)

**Step 1: Audit Trail** (`/audit`)
- Show the full action log
- Filter by entity type: "invoice"
- Show individual entries:
  - Timestamp, action, actor (user/system/AI)
  - Changes and evidence attached to each entry

> "Every action in the system — creation, update, OCR extraction, matching, approval — is logged with the actor, timestamp, and evidence. This is tamper-proof and query-ready for any auditor."

**Step 2: Compliance Dashboard** (`/compliance`)
- Click **Compliance** in sidebar
- Show 4 summary cards:
  - **Controls Active: 7/10**
  - **Open Gaps: 2**
  - **Root Causes: 4**
  - **Optimization Ideas: 3 high priority**

**Step 3: Control Mapping tab**
- Show 10 AP controls mapped to policy sections:
  - CTL-001: Three-Way Matching → Section 4.1
  - CTL-002: Duplicate Detection → Section 3.3
  - CTL-003: Approval Matrix → Section 5
  - etc.
- Point out status: Active/Partial/Planned
- Point out automated vs manual
- Point out test results: Pass/Fail

> "When an auditor asks 'How do you ensure three-way matching?', AI shows: Control CTL-001, mapped to Policy Section 4.1, status Active, automated, last tested today, result: Pass."

**Step 4: Gap Analysis tab**
- Switch to Gap Analysis tab
- Show dynamically detected gaps:
  - SLA breach risk (open exceptions exceeding 48h)
  - Unmatched invoices
  - On-hold vendor invoices processed
  - Missing audit trails
  - Payment term monitoring not automated

> "These gaps are computed in real-time from actual system data — not a static checklist."

---

## ACT 6 — "AI Improves Itself"

### Story
> "AI analyzes its own operational data to find root causes, identify patterns, and propose rule optimizations — moving from reactive to proactive."

### Demo Route (5 min)

**Step 1: Root Causes tab** (on `/compliance`)
- Switch to Root Causes tab
- Show exception patterns grouped by type + vendor:
  - e.g., "Amount Variance — SteelCore: 3 occurrences, $12,500 impact"
  - e.g., "Missing PO — new vendor invoices: 2 occurrences"
- Each root cause shows:
  - Category and specific issue
  - Occurrence count
  - Affected invoice count
  - Dollar impact
  - Suggested fix

> "AI identifies that SteelCore has repeated amount variances — the root cause is outdated contract prices in the PO system. Suggested fix: update PO pricing from latest contract."

**Step 2: Optimization tab**
- Switch to Optimization tab
- Show AI-generated improvement proposals:
  - **Increase Amount Tolerance Threshold** — High priority, Low effort
    - "Reduce low-value exceptions by adjusting tolerance from 5% to 8%"
  - **Vendor On-Hold Auto-Block** — High priority, Medium effort
    - "Auto-reject invoices from on-hold vendors before matching"
  - **PO Creation SOP Update** — Medium priority, Low effort
    - "Reduce missing PO exceptions by enforcing PO creation before delivery"

- Each proposal shows:
  - Priority (High/Medium/Low)
  - Category tag
  - Effort level
  - Projected impact

> "AI doesn't just flag problems — it proposes specific, actionable improvements with priority and effort estimates. This is the difference between RPA and true intelligent automation."

**Step 3: Close the Loop**
- Go back to Dashboard
- Show the Touchless Rate: 20%

> "Today touchless rate is 20%. With the proposed optimizations — increasing tolerance, blocking on-hold vendors, improving PO compliance — AI projects this can reach 60-70%. That's the continuous improvement loop."

---

## Closing Statement

> "In 6 ACTs, you've seen AI perform 6 different roles:
> - **Analyst** — understood the business from raw documents
> - **Architect** — designed the complete system
> - **Developer** — built the full-stack application
> - **Operator** — processed invoices end-to-end automatically
> - **Auditor** — maintained compliance with real-time gap detection
> - **Optimizer** — identified root causes and proposed improvements
>
> This isn't 6 separate tools. It's one AI agent that understands the complete lifecycle — from understanding to building to operating to improving. That's an AI Digital Operations Manager."

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Can't login | Check backend is running: `docker ps` |
| Import fails | Ensure CSV column names match exactly (lowercase) |
| OCR returns mock data | Set `ANTHROPIC_API_KEY` in backend env for real AI |
| No data on dashboard | Run `python -m app.seed` in backend container |
| Compliance page empty | Backend needs to be running on port 8000 |

## Reset Demo Data

```bash
# Stop everything
docker compose down -v

# Rebuild fresh (deletes all data)
docker compose up --build -d

# Data auto-seeds on startup
```
