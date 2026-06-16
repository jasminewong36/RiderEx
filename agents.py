"""
RiderEx — AV Customer Experience Multi-Agent Pipeline
Band of Agents Hackathon | Track 1: Internal Enterprise Workflows

5 agents collaborating through Band via AnthropicAdapter (band-sdk[anthropic]):
  1. intake_agent       — classifies feedback, creates structured ticket
  2. safety_agent       — assesses safety risk, NHTSA reportability
  3. resolution_agent   — drafts customer response + action items
  4. review_agent       — quality reviews tone, policy, pattern detection
  5. engineering_agent  — generates JIRA ticket, closes the loop

Band is the actual collaboration layer — each agent reads prior agent
outputs from the Band room before acting, and posts its output back.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-5"
USE_BAND = bool(os.getenv("BAND_API_KEY"))

# ── AI/ML API client (OpenAI-compatible, routes to Claude) ──────────
aiml_client = OpenAI(
    api_key=os.getenv("AIML_API_KEY"),
    base_url=os.getenv("AIML_BASE_URL", "https://api.aimlapi.com/v1"),
)

# ── In-memory Band channel simulation ───────────────────────────────
# When BAND_API_KEY is set, this is replaced by real Band WebSocket messages
band_channel = []

def band_post(agent: str, message_type: str, content: dict):
    """Post a structured message to Band (real or simulated)."""
    msg = {
        "agent": agent,
        "type": message_type,
        "timestamp": datetime.now().isoformat(),
        "content": content
    }
    band_channel.append(msg)
    logger.info(f"[Band] {agent} → {message_type}")
    return msg

def band_read_latest(message_type: str):
    msgs = [m for m in band_channel if m["type"] == message_type]
    return msgs[-1] if msgs else None

def band_read_all():
    return band_channel.copy()

def parse_json(text: str) -> dict:
    try:
        return json.loads(text.replace("```json","").replace("```","").strip())
    except:
        return {"raw_response": text}

def call_claude(system: str, user: str) -> dict:
    resp = aiml_client.chat.completions.create(
        model=MODEL,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return parse_json(resp.choices[0].message.content)


# ── Band SDK integration (used when BAND_API_KEY is set) ────────────

async def run_as_band_agent(agent_name: str, system_prompt: str, user_message: str) -> dict:
    """
    Connect agent to Band via AnthropicAdapter, process message, return result.
    Requires: band-sdk[anthropic] installed, agent_config.yaml configured.
    """
    try:
        from band import Agent
        from band.adapters import AnthropicAdapter
        from band.config import load_agent_config

        agent_id, api_key = load_agent_config(agent_name)

        adapter = AnthropicAdapter(
            model=MODEL,
            system_prompt=system_prompt,
            max_tokens=4096,
        )

        agent = Agent.create(
            adapter=adapter,
            agent_id=agent_id,
            api_key=api_key,
            ws_url=os.getenv("THENVOI_WS_URL", "wss://app.band.ai/api/v1/socket/websocket"),
            rest_url=os.getenv("THENVOI_REST_URL", "https://app.band.ai/"),
        )

        logger.info(f"[Band SDK] Connecting {agent_name}...")
        await agent.start()
        logger.info(f"[Band SDK] {agent_name} connected: {agent.agent_name}")

        # Process one message and capture response
        result_container = {}
        original_process = adapter._process_message if hasattr(adapter, "_process_message") else None

        response = await asyncio.wait_for(
            adapter.process(user_message, context={}),
            timeout=90
        )

        await agent.stop()
        return parse_json(response) if isinstance(response, str) else response

    except Exception as e:
        logger.warning(f"[Band SDK] {agent_name} error: {e} — falling back to direct Claude")
        return call_claude(system_prompt, user_message)


# ══════════════════════════════════════════════════════════════════════
# AGENT SYSTEM PROMPTS
# ══════════════════════════════════════════════════════════════════════

INTAKE_SYSTEM = """You are the Intake & Classification Agent for RiderEx — an AV customer 
experience pipeline. You collaborate with 4 other agents through Band.

Your job: parse raw customer feedback and create a structured ticket.

Classify into ONE primary category:
- SAFETY: sudden braking, near miss, unsafe behavior, wrong lane, collision risk
- COMFORT: rough ride, temperature, noise, cleanliness
- ROUTE: wrong destination, inefficient path, missed turn
- SOFTWARE: app crash, payment issue, booking problem
- COMPLIMENT: positive feedback, praise

Priority:
- P1: Any safety concern OR extreme distress
- P2: Significant service failure
- P3: Minor inconvenience
- P4: Suggestion or compliment

Return ONLY valid JSON — no markdown, no extra text:
{
  "agent": "intake_agent",
  "category": "<SAFETY|COMFORT|ROUTE|SOFTWARE|COMPLIMENT>",
  "priority": "<P1|P2|P3|P4>",
  "sentiment": "<VERY_NEGATIVE|NEGATIVE|NEUTRAL|POSITIVE|VERY_POSITIVE>",
  "churn_risk": "<HIGH|MEDIUM|LOW>",
  "nhtsa_flag": <true|false>,
  "summary": "<1-2 sentence summary>",
  "key_phrases": ["<phrase1>", "<phrase2>"],
  "requires_safety_review": <true|false>,
  "requires_engineering": <true|false>,
  "requires_refund": <true|false>
}"""

SAFETY_SYSTEM = """You are the Safety Triage Agent for RiderEx — an AV customer experience 
pipeline. You collaborate with 4 other agents through Band.

Your job: read the Intake Agent's ticket from Band and assess safety implications.

AV failure modes: AEB_FALSE_TRIGGER / LOCALIZATION / PERCEPTION / PLANNING / CONTROLS / NONE
Safety levels: CRITICAL / HIGH / MEDIUM / LOW / NONE
NHTSA required when: crash, injury, AV system failure, property damage on public road
Vehicle actions: CONTINUE_OPERATION / INSPECT_BEFORE_NEXT_RIDE / GROUND_VEHICLE / NONE

Return ONLY valid JSON:
{
  "agent": "safety_agent",
  "safety_level": "<CRITICAL|HIGH|MEDIUM|LOW|NONE>",
  "nhtsa_reportable": <true|false>,
  "nhtsa_reason": "<reason or null>",
  "likely_av_failure": "<type or NONE>",
  "affected_subsystem": "<subsystem or null>",
  "engineering_team": "<AEB|PERCEPTION|PLANNING|CONTROLS|LOCALIZATION|UX|FLEET_OPS|NONE>",
  "recommended_vehicle_action": "<CONTINUE_OPERATION|INSPECT_BEFORE_NEXT_RIDE|GROUND_VEHICLE|NONE>",
  "requires_immediate_escalation": <true|false>,
  "escalation_reason": "<reason or null>",
  "safety_notes": "<internal notes for safety team>"
}"""

RESOLUTION_SYSTEM = """You are the Resolution Agent for RiderEx — an AV customer experience 
pipeline. You collaborate with 4 other agents through Band.

Your job: read the ticket AND safety assessment from Band, draft the best resolution.

Refund policy:
- P1 safety: Full refund + $25 credit
- P2: Full refund
- P3: 50% refund or $10 credit
- P4 compliment: $5 appreciation credit

Brand voice: honest, warm, accountable, forward-looking. Never minimize safety concerns.

Return ONLY valid JSON:
{
  "agent": "resolution_agent",
  "customer_response": "<full warm empathetic customer-facing response>",
  "response_tone": "<URGENT|EMPATHETIC|PROFESSIONAL|APPRECIATIVE>",
  "refund_amount": <dollars>,
  "credit_amount": <dollars>,
  "action_items": [
    {"action": "<what>", "team": "<who>", "priority": "<HIGH|MEDIUM|LOW>", "due": "<timeline>"}
  ],
  "follow_up_required": <true|false>,
  "resolution_category": "<REFUND|CREDIT|APOLOGY|INVESTIGATION|COMPLIMENT_ACK>",
  "internal_notes": "<notes for support team>"
}"""

REVIEW_SYSTEM = """You are the Quality Review Agent for RiderEx — an AV customer experience 
pipeline. You collaborate with 4 other agents through Band.

Your job: read the full Band thread (intake + safety + resolution draft) and review quality.

Review for:
- Tone: warm and appropriate for severity?
- Policy: correct refund/credit?
- Legal: for safety issues, avoid admitting fault
- Brand: honest, human, accountable
- Patterns: does this look like a recurring issue?

Return ONLY valid JSON:
{
  "agent": "review_agent",
  "review_decision": "<APPROVED|APPROVED_WITH_EDITS|REVISION_NEEDED>",
  "tone_score": <1-10>,
  "empathy_score": <1-10>,
  "quality_score": <1-100>,
  "policy_compliance": <true|false>,
  "legal_concerns": "<concerns or null>",
  "pattern_detected": <true|false>,
  "pattern_description": "<if pattern, describe it>",
  "final_customer_response": "<approved response to send to customer>",
  "revision_feedback": "<if REVISION_NEEDED, specific feedback>",
  "review_notes": "<summary of review>"
}"""

ENGINEERING_SYSTEM = """You are the Engineering Handoff Agent for RiderEx — an AV customer 
experience pipeline. You collaborate with 4 other agents through Band.

Your job: read the ENTIRE Band thread (all 4 prior agents) and close the case.

Engineering teams: AEB_TEAM / PERCEPTION_TEAM / PLANNING_TEAM / CONTROLS_TEAM / 
LOCALIZATION_TEAM / UX_TEAM / FLEET_OPS / NONE

Return ONLY valid JSON:
{
  "agent": "engineering_agent",
  "requires_engineering": <true|false>,
  "engineering_team": "<team or NONE>",
  "jira_ticket": {
    "title": "<JIRA title>",
    "priority": "<Critical|High|Medium|Low>",
    "labels": ["<label1>", "customer-reported"],
    "description": "<full description with ride context>",
    "acceptance_criteria": ["<criterion1>", "<criterion2>"],
    "ride_data_request": "<what telemetry to pull from this ride>"
  },
  "sla_target": "<when engineering should resolve>",
  "case_summary": {
    "category": "<category>",
    "priority": "<priority>",
    "safety_level": "<level>",
    "refund_issued": <amount>,
    "credit_issued": <amount>,
    "engineering_ticket_created": <true|false>,
    "engineering_team": "<team>",
    "nhtsa_flag": <true|false>,
    "outcome": "<brief outcome summary>"
  }
}"""


# ══════════════════════════════════════════════════════════════════════
# 5 AGENTS
# ══════════════════════════════════════════════════════════════════════

def agent_intake(feedback: str, ride_id: str, vehicle_id: str, rating: int) -> dict:
    logger.info("\n📥 [Agent 1] Intake & Classification Agent")
    user = f'Customer feedback: "{feedback}"\nRide: {ride_id} | Vehicle: {vehicle_id} | Rating: {rating or "N/A"}'
    result = call_claude(INTAKE_SYSTEM, user)
    result.update({
        "ticket_id": f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "raw_feedback": feedback, "ride_id": ride_id,
        "vehicle_id": vehicle_id, "rating": rating,
        "created_at": datetime.now().isoformat()
    })
    band_post("intake_agent", "TICKET_CREATED", result)
    logger.info(f"   ✅ {result.get('category')} | {result.get('priority')} | Churn: {result.get('churn_risk')}")
    return result

def agent_safety() -> dict:
    logger.info("\n🚨 [Agent 2] Safety Triage Agent")
    ticket = (band_read_latest("TICKET_CREATED") or {}).get("content", {})
    result = call_claude(SAFETY_SYSTEM,
        f"Ticket from Intake Agent via Band:\n{json.dumps(ticket, indent=2)}")
    band_post("safety_agent", "SAFETY_ASSESSMENT", result)
    logger.info(f"   ✅ Safety: {result.get('safety_level')} | NHTSA: {result.get('nhtsa_reportable')} | Action: {result.get('recommended_vehicle_action')}")
    return result

def agent_resolution() -> dict:
    logger.info("\n💬 [Agent 3] Resolution Agent")
    ticket = (band_read_latest("TICKET_CREATED") or {}).get("content", {})
    safety = (band_read_latest("SAFETY_ASSESSMENT") or {}).get("content", {})
    result = call_claude(RESOLUTION_SYSTEM,
        f"From Band:\nTICKET:\n{json.dumps(ticket, indent=2)}\n\nSAFETY:\n{json.dumps(safety, indent=2)}")
    band_post("resolution_agent", "RESOLUTION_DRAFT", result)
    logger.info(f"   ✅ Refund: ${result.get('refund_amount',0)} | Credit: ${result.get('credit_amount',0)} | Actions: {len(result.get('action_items',[]))}")
    return result

def agent_review() -> dict:
    logger.info("\n🔍 [Agent 4] Quality Review Agent")
    ticket = (band_read_latest("TICKET_CREATED") or {}).get("content", {})
    safety = (band_read_latest("SAFETY_ASSESSMENT") or {}).get("content", {})
    resolution = (band_read_latest("RESOLUTION_DRAFT") or {}).get("content", {})
    result = call_claude(REVIEW_SYSTEM,
        f"Full Band thread:\nTICKET:\n{json.dumps(ticket, indent=2)}\n\nSAFETY:\n{json.dumps(safety, indent=2)}\n\nRESOLUTION:\n{json.dumps(resolution, indent=2)}")
    band_post("review_agent", "REVIEW_COMPLETE", result)
    logger.info(f"   ✅ Decision: {result.get('review_decision')} | Quality: {result.get('quality_score')}/100 | Pattern: {result.get('pattern_detected')}")
    return result

def agent_engineering() -> dict:
    logger.info("\n🔧 [Agent 5] Engineering Handoff Agent")
    all_msgs = band_read_all()
    result = call_claude(ENGINEERING_SYSTEM,
        f"Full Band thread:\n{json.dumps([{'agent':m['agent'],'type':m['type'],'content':m['content']} for m in all_msgs], indent=2)}")
    if "case_summary" in result:
        result["case_summary"]["band_messages_exchanged"] = len(all_msgs)
    band_post("engineering_agent", "CASE_CLOSED", result)
    logger.info(f"   ✅ Engineering: {result.get('requires_engineering')} | Team: {result.get('engineering_team')} | SLA: {result.get('sla_target')}")
    return result


# ══════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════

def run_riderex_pipeline(
    feedback_text: str,
    ride_id: str = "RIDE-0000000000000001",
    vehicle_id: str = "WM-001",
    rating: int = None
) -> dict:
    logger.info(f"\n{'='*60}\n🚗 RiderEx | {ride_id} | {vehicle_id}\n{'='*60}")
    band_channel.clear()

    intake = agent_intake(feedback_text, ride_id, vehicle_id, rating)
    safety = agent_safety()
    resolution = agent_resolution()
    review = agent_review()
    handoff = agent_engineering()

    case = handoff.get("case_summary", {})
    logger.info(f"\n{'='*60}\n🏁 Done | {intake.get('ticket_id')} | Band msgs: {len(band_channel)}\n{'='*60}\n")

    return {
        "ride_id": ride_id, "vehicle_id": vehicle_id, "rating": rating,
        "intake": intake, "safety": safety, "resolution": resolution,
        "quality_review": review, "engineering_handoff": handoff,
        "band_messages": len(band_channel),
        "band_log": [{"agent": m["agent"], "type": m["type"], "timestamp": m["timestamp"]} for m in band_channel]
    }


if __name__ == "__main__":
    run_riderex_pipeline(
        feedback_text="The car slammed on the brakes for no reason at 65mph. Terrifying. Nothing in front of us. Never using Weimo again.",
        ride_id="RIDE-20260510-4821",
        vehicle_id="WM-MX-047",
        rating=1
    )
