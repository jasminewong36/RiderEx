# RiderEx 

**AV Customer Experience Multi-Agent Pipeline — powered by Band.ai**

RiderEx is a full-stack autonomous vehicle customer support platform. When a passenger submits feedback, 5 AI agents collaborate through Band to automatically classify the issue, triage safety, draft a response, quality review it, create an engineering ticket, and render a Go/No-Go software release decision.

Live demo: **https://riderex.vercel.app**

---

## Features

### 🚀 Pipeline Tab
Submit passenger feedback and run it through the 5-agent pipeline. Auto-generates Vehicle IDs (WM-0001 to WM-2000) and Ride IDs. Results shown across 6 tabs:
- **Ticket** — intake classification, priority, sentiment, churn risk
- **Safety** — NHTSA reportability, vehicle action, AV failure mode
- **Response** — drafted customer response + action items
- **🚦 Release Report** — Go / No-Go / Conditional Go decision with criteria checklist, issue investigation list, and quality review summary
- **JIRA** — engineering ticket with acceptance criteria
- **Band Log** — live agent collaboration thread

### 📊 Dashboard Tab
Metrics aggregated from all pipeline runs + 200-vehicle seed dataset:
- 10 KPIs: total rides, safety incidents, NHTSA flags, avg rating, churn risk, refund totals, quality score, engineering tickets, go/no-go rate
- 8 bar charts across categories, priorities, safety levels, sentiment, and more
- Filter bar: category, priority, safety level, time range
- Recent rides table
- Backed by Supabase for persistence; falls back to localStorage

### 🚗 Fleet Tab
HUD-style registry of all 200 RiderEx vehicles (WM-001 to WM-200):
- Each vehicle card shows model, city, safety score bar, open tickets, resolved tickets, and avg rating
- **Smart ticket tracking**: `netOpen = original tickets + new incidents surfaced - resolved via pipeline`
  - Pipeline run with LOW/NONE result → ticket resolved (OPEN count drops)
  - Pipeline run with HIGH/CRITICAL result → new incident added (OPEN count rises)
  - Vehicles are never permanently "cleared" — new issues always come in
- Click any card to open a detail modal with pipeline run history (✓ resolved / ! new issue per run)
- **Run Pipeline** button pre-fills the vehicle ID on the pipeline form
- Live sync: every pipeline run instantly updates the vehicle's fleet card (status, score, tickets)

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
[Band] Resolution → RESOLUTION_DRAFT
        ↓
[Band] Quality Review → REVIEW_COMPLETE
        ↓
[Band] Engineering Handoff → CASE_CLOSED
        ↓
Customer gets response + Go/No-Go release decision + Engineering JIRA ticket
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Agent Framework** | Band.ai (`band-sdk`) |
| **AI Model** | `claude-sonnet-4-5` via AI/ML API (OpenAI-compatible) |
| **AI Client** | `openai` Python SDK with custom `base_url` |
| **Backend** | FastAPI + Uvicorn |
| **Database** | Supabase (PostgreSQL) — gracefully optional |
| **Frontend** | Vanilla HTML/CSS/JS — dark teal HUD aesthetic |
| **Deployment** | Vercel (serverless Python) |
| **Fleet Dataset** | 200-vehicle seed data (`riderex_vehicles.json`) |

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
# AI/ML API (OpenAI-compatible, runs Claude models)
AIML_API_KEY=your_key
AIML_BASE_URL=https://api.aimlapi.com/v1

# Supabase (optional — app works without it, but you can set this up if you want your data stored)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key

# Band.ai
BAND_API_KEY=your_band_api_key
THENVOI_WS_URL=wss://app.band.ai/api/v1/socket/websocket
THENVOI_REST_URL=https://app.band.ai/
```

> **Security**: `.env` and `agent_config.yaml` are in `.gitignore` — never commit them.

### 3. Configure Band agents

Go to [app.band.ai/agents](https://app.band.ai/agents) → New Agent → Remote Agent × 5:
- `intake_agent`, `safety_agent`, `resolution_agent`, `review_agent`, `engineering_agent`

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
- Vehicle ID, model, city, state, fleet zone
- Software version, sensor config
- Total mileage, total rides, avg passenger rating
- Safety score, open support tickets, last incident type
- Service dates, in-service date

The dashboard seeds 200 records from this dataset on first load (incident type → category, safety score → safety level, status → priority).

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/run-pipeline` | Run the 5-agent pipeline on feedback |
| `GET` | `/vehicles` | Return the 200-vehicle fleet dataset |
| `GET` | `/metrics` | Query ride records from Supabase (filterable) |
| `GET` | `/health` | Service status + integration flags |
| `GET` | `/` | Serve the frontend |

---

## Security

- API keys stored only in `.env` locally and Vercel encrypted environment variables in production
- `.env` and `agent_config.yaml` are gitignored and never committed
- Supabase uses service role key server-side only; frontend never touches it directly
