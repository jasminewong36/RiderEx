---
title: RiderEx
emoji: 🚗
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
short_description: AV Customer Experience Multi-Agent Pipeline via Band.ai
---

# RiderEx 🚗

**AV Customer Experience Multi-Agent Pipeline — powered by Band.ai**

When a Waymo passenger submits feedback, 5 agents collaborate through Band to automatically classify the issue, triage safety, draft a response, quality review it, and create an engineering ticket.

## Band SDK Integration

Uses `band-sdk[anthropic]` — each agent connects to Band via `AnthropicAdapter` and `thenvoi`:

```python
from thenvoi import Agent
from thenvoi.adapters import AnthropicAdapter
from thenvoi.config import load_agent_config

agent_id, api_key = load_agent_config("intake_agent")
adapter = AnthropicAdapter(model="claude-sonnet-4-5-20250929", system_prompt=INTAKE_SYSTEM)
agent = Agent.create(adapter=adapter, agent_id=agent_id, api_key=api_key,
    ws_url=os.getenv("THENVOI_WS_URL"), rest_url=os.getenv("THENVOI_REST_URL"))
await agent.run()
```

## 5 Agents via Band

| Agent | Band Message Posted | Reads From Band |
|-------|-------------------|-----------------|
| **Intake & Classification** | `TICKET_CREATED` | — |
| **Safety Triage** | `SAFETY_ASSESSMENT` | `TICKET_CREATED` |
| **Resolution** | `RESOLUTION_DRAFT` | `TICKET_CREATED` + `SAFETY_ASSESSMENT` |
| **Quality Review** | `REVIEW_COMPLETE` | All 3 prior messages |
| **Engineering Handoff** | `CASE_CLOSED` | Entire Band thread |

## Band Collaboration Flow

```
Customer submits feedback
        ↓
[Band] Intake Agent → TICKET_CREATED
        ↓
[Band] Safety Triage reads TICKET_CREATED → SAFETY_ASSESSMENT
        ↓
[Band] Resolution reads TICKET_CREATED + SAFETY_ASSESSMENT → RESOLUTION_DRAFT
        ↓
[Band] Quality Review reads all 3 → REVIEW_COMPLETE
        ↓
[Band] Engineering Handoff reads entire thread → CASE_CLOSED
        ↓
Customer gets response + Engineering team gets JIRA ticket
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
# or with uv:
uv add "band-sdk[anthropic]"
```

### 2. Configure environment

```bash
cp .env.example .env
# Add ANTHROPIC_API_KEY and BAND_API_KEY
```

### 3. Create agents on Band

Go to https://app.band.ai/agents → New Agent → Remote Agent × 5:
- `intake_agent`
- `safety_agent`
- `resolution_agent`
- `review_agent`
- `engineering_agent`

Copy each agent's UUID and API key into `agent_config.yaml`.

### 4. Run

```bash
python app.py
# Open http://localhost:7860
```

> **Note:** `agent_config.yaml` and `.env` are in `.gitignore` — never commit them.

## Sample Scenarios

- 🔴 **Safety** — AEB false trigger at highway speed → P1, NHTSA flag, full refund + $25 credit, AEB team JIRA
- 🟡 **Comfort** — Rough ride, AC issues → P3, empathetic response, $10 credit
- 🟠 **Route** — Wrong destination → P2, full refund, UX team action item
- 🟢 **Compliment** — Great ride → P4, thank you + $5 appreciation credit

## Tech Stack

- **Agent Framework**: Band.ai (`band-sdk[anthropic]`, `thenvoi`)
- **AI Model**: Claude via Anthropic SDK
- **Backend**: FastAPI
- **Frontend**: Vanilla HTML/CSS/JS
- **Deployment**: HuggingFace Spaces (Docker)

## Built For

Band of Agents Hackathon — Track 1: Internal Enterprise Workflows
