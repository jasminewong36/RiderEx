"""RiderEx — FastAPI backend"""
import os
import json
import logging
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from agents import run_riderex_pipeline
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="RiderEx")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Supabase client (optional — gracefully disabled if not configured) ──
def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as e:
        logger.warning(f"Supabase unavailable: {e}")
        return None

def save_to_supabase(result: dict):
    sb = get_supabase()
    if not sb:
        return
    try:
        intake     = result.get("intake", {})
        safety     = result.get("safety", {})
        resolution = result.get("resolution", {})
        review     = result.get("quality_review", {})
        handoff    = result.get("engineering_handoff", {})
        sb.table("rides").insert({
            "ticket_id":            intake.get("ticket_id"),
            "ride_id":              result.get("ride_id"),
            "vehicle_id":           result.get("vehicle_id"),
            "category":             intake.get("category"),
            "priority":             intake.get("priority"),
            "safety_level":         safety.get("safety_level"),
            "nhtsa":                bool(safety.get("nhtsa_reportable")),
            "rating":               result.get("rating"),
            "churn_risk":           intake.get("churn_risk"),
            "refund_amount":        resolution.get("refund_amount", 0),
            "credit_amount":        resolution.get("credit_amount", 0),
            "good_ride":            intake.get("category") == "COMPLIMENT" or (
                                        safety.get("safety_level") == "NONE" and
                                        intake.get("priority") == "P4"
                                    ),
            "sentiment":            intake.get("sentiment"),
            "quality_score":        review.get("quality_score"),
            "review_decision":      review.get("review_decision"),
            "requires_engineering": bool(handoff.get("requires_engineering")),
            "engineering_team":     handoff.get("engineering_team", "NONE"),
            "vehicle_action":       safety.get("recommended_vehicle_action", "NONE"),
            "action_items":         len(resolution.get("action_items", [])),
            "band_messages":        result.get("band_messages", 0),
            "key_phrases":          intake.get("key_phrases", []),
            "intake_data":          intake,
            "safety_data":          safety,
            "resolution_data":      resolution,
            "review_data":          review,
            "engineering_data":     handoff,
        }).execute()
        logger.info(f"[Supabase] Saved ride {intake.get('ticket_id')}")
    except Exception as e:
        logger.warning(f"[Supabase] Save failed: {e}")


class FeedbackRequest(BaseModel):
    feedback_text: str
    ride_id: Optional[str] = "RIDE-0000000000000001"
    vehicle_id: Optional[str] = "WM-0001"
    rating: Optional[int] = None


@app.post("/run-pipeline")
async def run_pipeline(request: FeedbackRequest):
    try:
        result = run_riderex_pipeline(
            feedback_text=request.feedback_text,
            ride_id=request.ride_id,
            vehicle_id=request.vehicle_id,
            rating=request.rating
        )
        save_to_supabase(result)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/metrics")
async def get_metrics(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    safety_level: Optional[str] = None,
    days: Optional[int] = None,
    limit: int = 500,
):
    """Return ride records from Supabase for the dashboard."""
    sb = get_supabase()
    if not sb:
        return JSONResponse(status_code=503, content={"error": "Supabase not configured"})
    try:
        query = sb.table("rides").select(
            "id,ticket_id,ride_id,vehicle_id,category,priority,safety_level,"
            "nhtsa,rating,churn_risk,refund_amount,credit_amount,good_ride,"
            "sentiment,quality_score,review_decision,requires_engineering,"
            "engineering_team,vehicle_action,action_items,band_messages,"
            "key_phrases,created_at"
        ).order("created_at", desc=True).limit(limit)

        if category:   query = query.eq("category", category)
        if priority:   query = query.eq("priority", priority)
        if safety_level: query = query.eq("safety_level", safety_level)
        if days:
            from datetime import datetime, timedelta, timezone
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            query = query.gte("created_at", cutoff)

        res = query.execute()
        return JSONResponse(content={"rides": res.data, "total": len(res.data)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "RiderEx",
        "agents": 5,
        "band_configured": bool(os.getenv("BAND_API_KEY")),
        "aiml_configured": bool(os.getenv("AIML_API_KEY")),
        "supabase_configured": bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY")),
    }


@app.get("/vehicles")
async def get_vehicles():
    try:
        with open("riderex_vehicles.json") as f:
            return JSONResponse(content=json.load(f))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/", response_class=HTMLResponse)
async def index():
    return open("index.html").read()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
