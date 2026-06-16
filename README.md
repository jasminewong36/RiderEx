# RiderEx

**AV Customer Experience Multi-Agent Pipeline — powered by Band.ai**

RiderEx is a full-stack autonomous vehicle customer support platform. When a passenger submits feedback, 5 AI agents collaborate through Band to automatically classify the issue, triage safety, draft a response, quality review it, create an engineering ticket, and render a Go/No-Go software release decision — all in one pipeline run.

Live demo: **https://riderex.vercel.app**

---

## What RiderEx Does

A passenger reports a problem with their autonomous vehicle ride. RiderEx:

1. Classifies the feedback (safety, comfort, route, software, or compliment)
2. Triages safety risk and NHTSA reportability
3. Drafts a warm, policy-compliant customer response with refund/credit
4. Quality reviews the response for tone, legal exposure, and recurring patterns
5. Creates a JIRA engineering ticket and assigns it to the right team
6. Renders a Go / Conditional / No-Go release decision for the vehicle's software branch
7. Saves the full record to Supabase and updates every tab in real time

---

## Tab Walkthrough

### 🚀 Pipeline Tab

The core of the platform. Submit real passenger feedback and watch 5 agents process it live.

**Inputs:**
- **Customer Feedback** — free-text complaint or compliment (e.g. "The car slammed on the brakes for no reason at 65mph")
- **Vehicle ID** — auto-generated (WM-001 to WM-200), or type any valid ID
- **Star Rating** — 1–5 stars from the passenger

**What happens when you submit:**
- The form POSTs to `/run-pipeline`, which runs all 5 Band agents sequentially
- Results appear across 6 sub-tabs:

| Sub-tab | What it shows |
|---------|--------------|
| 📋 **Ticket** | Category, priority (P1–P4), sentiment, churn risk, key phrases, summary |
| 🚨 **Safety** | Safety level (CRITICAL → NONE), NHTSA reportability, AV failure mode, vehicle action |
| 💬 **Response** | Full customer-facing response, refund/credit amounts, action item list |
| 🚦 **Release Report** | Go / Conditional / No-Go decision with checklist of release criteria |
| 🔧 **JIRA** | Engineering ticket title, priority, labels, description, acceptance criteria, telemetry request |
| 📡 **Band Log** | Live agent collaboration thread showing every message exchanged through Band |

**After submission**, the run is saved to both `localStorage` and Supabase, and the Dashboard, Fleet, and Software tabs all update to reflect the new data.

**Atmosphere:** The tab has a moving perspective road animation — lane markings scroll toward the viewer with a scan line and HUD corner brackets — scoped only to this tab.

---

### 📊 Dashboard Tab

A full operations dashboard aggregating data from 250,400 seeded rides (200 vehicles × 1,252 rides each) plus every real pipeline submission.

**KPIs (10 cards):**

| KPI | What it measures |
|-----|-----------------|
| Total Rides | All rides processed; badge shows real submission count |
| Avg CSAT | Mean passenger rating across all rides |
| Good Ride Rate | % of rides with no incident and P4 priority |
| Safety Rate | % of rides flagged as a SAFETY category incident |
| NHTSA Flags | Count of rides requiring federal reportability |
| Avg Quality Score | Mean AI response quality score (0–100) |
| Escalation Rate | % of rides requiring engineering involvement |
| Avg Refund/Credit | Mean monetary resolution per ride |
| Band Messages | Mean agent messages exchanged per pipeline run |
| P1 Incidents | Count of top-priority safety-critical tickets |

**Filters:** Category · Priority · Safety Level · Time Range · Software Version — all combinable. The counter updates to show `N of M total` when filters are active.

**All Rides table:** Every ride sorted by most recent. Clicking any row opens a ticket modal with the full breakdown: vehicle info, classification, resolution details, key phrases, and the original customer feedback text.

**Scroll-reveal animation:** As you scroll down the Dashboard, three autonomous vehicle images (Pod, SUV, Shuttle) swoosh in from alternating sides of the screen — Pod and Shuttle from the right, SUV from the left.

**Data source:** `getMetrics()` merges the in-memory seeded dataset with localStorage real runs. The Supabase endpoint (`/metrics`) supplements with any runs submitted from other devices.

---

### 🚗 Fleet Tab

A real-time HUD-style registry of all 200 RiderEx vehicles (WM-001 to WM-200).

**Vehicle cards (front face):**
- Vehicle ID and status dot (ACTIVE / MAINTENANCE / GROUNDED)
- Model image (Pod Gen2 · Shuttle Gen3 · SUV Gen4)
- Safety score bar (0–100, color-coded green/amber/red)
- Open tickets vs resolved tickets
- Avg passenger rating

**Vehicle cards (back face — flip to reveal):**
- Fleet zone
- Software version
- Total mileage
- Rides processed (synced with Dashboard and Software tab)
- Last incident type
- Pipeline run count
- Open ticket count

**Click VIEW DETAILS** to open the full vehicle modal:
- All card metrics at a glance
- Pipeline run history (last 20 runs) — each showing ticket ID, category, safety level, and whether it was resolved or a new incident

**Smart ticket tracking:**
```
netOpen = original_open_tickets + new_incidents_surfaced − resolved_via_pipeline
```
- Pipeline run with LOW/NONE/MEDIUM safety → ticket resolved (OPEN drops)
- Pipeline run with HIGH/CRITICAL safety → new incident added (OPEN rises)

**Run Pipeline button** on each card pre-fills the vehicle ID on the Pipeline tab so you can submit feedback for that specific vehicle.

**Live sync:** Every pipeline submission instantly updates the relevant vehicle card without a page reload — score, status, ticket counts, and ride total all adjust in memory.

---

### 🔀 Software Tab

Tracks all software branches across the fleet and renders release readiness for each.

**Branches tracked:**

| Branch | Status | Notes |
|--------|--------|-------|
| `weimo-av-4.2.1` | Released · Mar 15, 2024 | Initial stable release |
| `weimo-av-4.3.0` | Released · Sep 1, 2024 | Route optimization & comfort improvements |
| `weimo-av-4.3.1` | Released · Jan 20, 2025 | Safety patch — AEB false trigger fix |
| `weimo-av-4.4.0-beta` | Beta · Pending | Next-gen perception stack — pre-release |

**Per-branch metrics card:**

| Metric | Description |
|--------|-------------|
| Rides | Total ride count on this branch |
| Safety Rate | % of rides in the SAFETY category |
| NHTSA Flags | Count of federally reportable incidents |
| Avg Quality | Mean response quality score |
| Vehicles | Number of fleet vehicles running this branch |
| Pipeline Runs | Real feedback submissions on this branch |

**Readiness badges:**
- ✅ **Go** — no critical/high safety incidents, no NHTSA flags, quality scores healthy
- ⚠️ **Conditional** — elevated severity or quality concerns; needs review before release
- 🚫 **No-Go** — critical safety incidents or NHTSA flags present; release blocked

Released branches (4.2.1, 4.3.0, 4.3.1) always show **Go** — they've already passed signoff, so their seeded data reflects clean, post-certification metrics. The beta branch reflects pre-release data with its full incident distribution.

**Pipeline Release Reports:** Inside each branch card, every real pipeline submission on that branch appears as a checklist — showing which release criteria passed and which are still pending (safety level, NHTSA flag, vehicle clearance, priority, quality score, response approval, engineering tickets).

**Filter pills:** All Branches · Pending Release · Released

---

## Architecture

### 5 Agents via Band.ai

| Agent | Role | Band Message |
|-------|------|-------------|
| **Intake & Classification** | Categorize feedback, assign priority, sentiment, churn risk | `TICKET_CREATED` |
| **Safety Triage** | NHTSA check, AV failure mode, vehicle action recommendation | `SAFETY_ASSESSMENT` |
| **Resolution** | Draft customer response, compute refund/credit, action items | `RESOLUTION_DRAFT` |
| **Quality Review** | Score tone/empathy/policy compliance, approve or revise | `REVIEW_COMPLETE` |
| **Engineering Handoff** | Create JIRA ticket, assign team, set SLA | `CASE_CLOSED` |

### Pipeline Flow

```
Passenger submits feedback
        ↓
[Band] Intake Agent → TICKET_CREATED
        ↓
[Band] Safety Triage → SAFETY_ASSESSMENT
        ↓
[Band] Resolution Agent → RESOLUTION_DRAFT
        ↓
[Band] Quality Review Agent → REVIEW_COMPLETE
        ↓
[Band] Engineering Handoff → CASE_CLOSED
        ↓
Result saved to localStorage + Supabase
        ↓
Dashboard, Fleet, and Software tabs update with new data
```

### Data Flow

```
seededRecords (250,400 in-memory)  ─┐
localStorage real runs              ├── getMetrics() ── Dashboard · Fleet · Software
Supabase real runs (other devices)  ┘
```

All three tabs read from the same `getMetrics()` function. A single pipeline submission increments the ride count identically everywhere, and the vehicle's Fleet card updates in real time without a page reload.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Agent Framework** | Band.ai (`band-sdk`) |
| **AI Model** | `claude-sonnet-4-5` via AI/ML API (OpenAI-compatible) |
| **AI Client** | `openai` Python SDK with custom `base_url` |
| **Backend** | FastAPI + Uvicorn |
| **Database** | Supabase (PostgreSQL) — gracefully optional |
| **Frontend** | Vanilla HTML/CSS/JS — dark space aesthetic with teal HUD accents |
| **Deployment** | Vercel (serverless Python) |
| **Fleet Dataset** | 200-vehicle registry (`riderex_vehicles.json` / `.csv`) |

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/your-username/riderex
cd riderex
uv venv && uv pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in `.env`:

```env
# AI/ML API (OpenAI-compatible, routes to Claude)
AIML_API_KEY=your_key
AIML_BASE_URL=https://api.aimlapi.com/v1

# Supabase (optional — app works without it, but real runs won't persist across devices)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key

# Band.ai
BAND_API_KEY=your_band_api_key
THENVOI_WS_URL=wss://app.band.ai/api/v1/socket/websocket
THENVOI_REST_URL=https://app.band.ai/
```

> **Security**: `.env` and `agent_config.yaml` are gitignored and never committed. API keys live only in your local `.env` or Vercel's encrypted environment variables.

### 3. Configure Band agents

Go to [app.band.ai/agents](https://app.band.ai/agents) → New Agent → Remote Agent × 5:
`intake_agent` · `safety_agent` · `resolution_agent` · `review_agent` · `engineering_agent`

Copy each UUID and API key into `agent_config.yaml` (gitignored).

### 4. Set up Supabase (optional)

Run `supabase_schema.sql` in the Supabase SQL Editor to create the `rides` table with all required columns and indexes.

### 5. Run locally

```bash
uv run python app.py
# Open http://localhost:7860
```

---

## Dataset

`riderex_vehicles.json` / `riderex_vehicles.csv` — 200 vehicles with:

- Vehicle ID, model (Pod Gen2 · Shuttle Gen3 · SUV Gen4), city, state, fleet zone
- Software version (`weimo-av-4.2.1` through `weimo-av-4.4.0-beta`)
- Total mileage, total rides, avg passenger rating, safety score
- Open support tickets, last incident type, last service date

The frontend generates 1,252 seeded ride records per vehicle (250,400 total) on page load using the registry as source data. Released branches generate clean metrics; the beta branch uses the full incident distribution.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/run-pipeline` | Run the 5-agent pipeline; saves result to Supabase |
| `GET` | `/vehicles` | Return the 200-vehicle fleet registry |
| `GET` | `/metrics` | Query ride records from Supabase (filterable by category, priority, safety level, days) |
| `POST` | `/seed-supabase` | Bulk-insert seeded ride records into Supabase (runs once per browser session) |
| `GET` | `/health` | Service status + integration flags (Band, AI/ML, Supabase) |
| `GET` | `/` | Serve the frontend |

---

## Security

- API keys stored only in `.env` locally and Vercel encrypted environment variables in production
- `.env` and `agent_config.yaml` are gitignored and never committed
- Supabase uses the service role key server-side only; the frontend never touches Supabase directly
